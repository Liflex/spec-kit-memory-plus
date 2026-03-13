"""
Quality Template Registry CLI (Exp 126)

Provides CLI commands for template discovery, metadata extraction,
and template combination recommendations.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from specify_cli.quality.template_registry import (
    TemplateRegistry,
    TemplateCategory,
    TemplateMetadata,
    TemplateCombination,
    BlendPreset,
    BlendedTemplate,
    get_registry,
    print_template_table,
    print_combination_table,
    compare_templates,
    format_template_diff,
    blend_templates,
    save_blended_template,
    format_blended_template,
)

console = Console()

# Create templates app
templates_app = typer.Typer(
    name="templates",
    help="Quality Template Registry - Discovery and recommendations for quality templates",
    add_completion=False,
)


@templates_app.command("list")
def list_templates_command(
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category (core, infrastructure, architecture, domain)",
    ),
    builtin: bool = typer.Option(
        False,
        "--builtin",
        "-b",
        help="Show only built-in templates",
    ),
    details: bool = typer.Option(
        False,
        "--details",
        "-d",
        help="Show detailed information",
    ),
):
    """List all available quality templates."""
    registry = get_registry()

    # Parse category if provided
    cat_enum = None
    if category:
        try:
            cat_enum = TemplateCategory(category.lower())
        except ValueError:
            console.print(f"[red]Invalid category: {category}[/red]")
            console.print(
                f"Valid categories: [cyan]{', '.join([c.value for c in TemplateCategory])}[/cyan]"
            )
            raise typer.Exit(1)

    # Get templates
    templates = registry.list_templates(category=cat_enum, builtin_only=builtin)

    if not templates:
        console.print("[yellow]No templates found matching the criteria.[/yellow]")
        return

    # Display using the print function or detailed view
    if details:
        _print_detailed_templates(templates)
    else:
        console.print(print_template_table(templates))

    # Show summary
    stats = registry.get_template_stats()
    console.print(
        f"\n[dim]Total: {stats['total_templates']} templates | "
        f"Built-in: {stats['builtin_templates']} | "
        f"Custom: {stats['custom_templates']}[/dim]"
    )


@templates_app.command("info")
def template_info_command(
    template_name: str = typer.Argument(
        ...,
        help="Template name (e.g., api-gateway, frontend, security)",
    )
):
    """Show detailed information about a specific template."""
    registry = get_registry()
    template = registry.get_template(template_name)

    if not template:
        console.print(f"[red]Template not found: {template_name}[/red]")
        console.print(
            f"\n[dim]Use [cyan]'speckit templates list'[/cyan] to see available templates.[/dim]"
        )
        raise typer.Exit(1)

    # Create detailed info panel
    info_lines = [
        f"[bold cyan]Template:[/bold cyan] {template.display_name}",
        f"[bold]Version:[/bold] {template.version}",
        f"[bold]Category:[/bold] {template.category.value}",
        f"[bold]File:[/bold] {template.file_path}",
        "",
        f"[bold]Description:[/bold]",
        f"  {template.description}",
        "",
        f"[bold]Statistics:[/bold]",
        f"  Rules: {template.rule_count}",
    ]

    # Severity breakdown
    if template.severity_breakdown:
        info_lines.append("  Severity Breakdown:")
        for severity, count in sorted(
            template.severity_breakdown.items(), key=lambda x: x[0], reverse=True
        ):
            color = {"fail": "red", "warn": "yellow", "info": "blue"}.get(severity, "white")
            info_lines.append(f"    [{color}]{severity}[/{color}]: {count}")

    # Domain tags
    if template.domain_tags:
        info_lines.append("")
        info_lines.append("[bold]Domain Tags:[/bold]")
        info_lines.append(f"  {', '.join(sorted(template.domain_tags))}")

    # Priority profiles
    if template.priority_profile_names:
        info_lines.append("")
        info_lines.append("[bold]Priority Profiles:[/bold]")
        for profile in template.priority_profile_names:
            info_lines.append(f"  - {profile}")

    # Phases
    if template.phases:
        info_lines.append("")
        info_lines.append("[bold]Phases:[/bold]")
        for phase in template.phases:
            info_lines.append(f"  - {phase}")

    # Compatible templates
    compatible = registry.get_compatible_templates(template_name)
    if compatible:
        info_lines.append("")
        info_lines.append("[bold]Compatible Templates:[/bold]")
        info_lines.append(f"  {', '.join(compatible)}")

    # Display in panel
    info_text = "\n".join(info_lines)
    console.print(Panel(info_text, title=f"[bold]{template_name}[/bold]", border_style="cyan"))

    # Show usage example
    console.print(
        f"\n[dim]Usage: speckit loop --criteria {template_name}[/dim]"
    )


@templates_app.command("search")
def search_templates_command(
    query: str = typer.Argument(
        ...,
        help="Search query (keyword in name, description, or domain tags)",
    )
):
    """Search templates by keyword."""
    registry = get_registry()
    results = registry.search_templates(query)

    if not results:
        console.print(f"[yellow]No templates found matching '{query}'[/yellow]")
        console.print(
            "\n[dim]Try searching for: security, api, performance, graphql, mobile[/dim]"
        )
        return

    console.print(f"\n[bold]Found {len(results)} template(s) matching '{query}':[/bold]\n")
    console.print(print_template_table(results))


@templates_app.command("recommend")
def recommend_templates_command(
    project_type: str = typer.Argument(
        ...,
        help="Project type (e.g., web-app, microservice, ml-service, mobile-app, serverless, graphql-api)",
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all matching recommendations",
    ),
):
    """Get template recommendations for a project type."""
    registry = get_registry()
    recommendations = registry.get_recommendations(project_type)

    if not recommendations:
        console.print(
            f"[yellow]No recommendations found for project type: {project_type}[/yellow]"
        )
        console.print(
            "\n[dim]Available project types: web-app, microservice, ml-service, "
            "mobile-app, graphql-api, serverless, desktop, infrastructure[/dim]"
        )
        return

    # Show all or just the best match
    if show_all:
        console.print(
            f"\n[bold]{len(recommendations)} recommendation(s) for '{project_type}':[/bold]\n"
        )
        console.print(print_combination_table(recommendations))
    else:
        # Show the best match (first one)
        best = recommendations[0]
        console.print(
            f"\n[bold cyan]Recommended for '{project_type}':[/bold cyan] {best.name.replace('_', ' ').title()}\n"
        )
        console.print(f"[dim]{best.description}[/dim]\n")
        console.print(f"[bold]Templates:[/bold] {', '.join(best.templates)}")

    # Show usage example
    recommended_templates = recommendations[0].templates
    console.print(
        f"\n[dim]Usage: speckit loop --criteria {','.join(recommended_templates)}[/dim]"
    )


@templates_app.command("stats")
def template_stats_command():
    """Show template registry statistics."""
    registry = get_registry()
    stats = registry.get_template_stats()

    console.print("\n[bold cyan]Quality Template Registry Statistics[/bold cyan]\n")

    # Template counts
    console.print("[bold]Templates:[/bold]")
    console.print(f"  Total: {stats['total_templates']}")
    console.print(f"  Built-in: {stats['builtin_templates']}")
    console.print(f"  Custom: {stats['custom_templates']}")

    # By category
    if stats["by_category"]:
        console.print("\n[bold]By Category:[/bold]")
        for category, count in sorted(stats["by_category"].items()):
            console.print(f"  {category}: {count}")

    # Rules
    console.print("\n[bold]Rules:[/bold]")
    console.print(f"  Total Rules: {stats['total_rules']}")
    if stats["total_templates"] > 0:
        avg = stats["total_rules"] / stats["total_templates"]
        console.print(f"  Average Rules per Template: {avg:.1f}")

    # Available combinations
    console.print(f"\n[bold]Recommended Combinations:[/bold]")
    console.print(f"  Total: {len(TemplateRegistry.RECOMMENDED_COMBINATIONS)}")
    for combo in TemplateRegistry.RECOMMENDED_COMBINATIONS:
        console.print(f"  - {combo.name.replace('_', ' ').title()}: {len(combo.templates)} templates")


@templates_app.command("combinations")
def list_combinations_command():
    """List all recommended template combinations."""
    console.print("\n[bold cyan]Recommended Template Combinations[/bold cyan]\n")
    console.print(print_combination_table(TemplateRegistry.RECOMMENDED_COMBINATIONS))

    console.print("\n[dim]Usage: speckit templates recommend <project-type>[/dim]")


@templates_app.command("compare")
def compare_templates_command(
    templates: list[str] = typer.Argument(
        ...,
        help="Template names to compare (2-4 templates)",
    ),
    diff: bool = typer.Option(
        False,
        "--diff",
        "-d",
        help="Show diff-style comparison (only for 2 templates)",
    ),
):
    """Compare multiple templates side-by-side."""
    if len(templates) < 2:
        console.print("[red]Error: Need at least 2 templates to compare.[/red]")
        raise typer.Exit(1)

    if len(templates) > 4:
        console.print("[yellow]Warning: Comparing more than 4 templates may be hard to read.[/yellow]")

    registry = get_registry()

    # Get template metadata
    template_list = []
    missing = []
    for name in templates:
        template = registry.get_template(name)
        if template:
            template_list.append(template)
        else:
            missing.append(name)

    if missing:
        console.print(f"[red]Error: Template(s) not found: {', '.join(missing)}[/red]")
        console.print("\n[dim]Use 'speckit templates list' to see available templates.[/dim]")
        raise typer.Exit(1)

    # Use diff format if requested and exactly 2 templates
    if diff and len(template_list) == 2:
        console.print(format_template_diff(template_list[0], template_list[1]))
    else:
        if diff and len(template_list) != 2:
            console.print("[yellow]Note: --diff only works with 2 templates. Using table format.[/yellow]")
        console.print(compare_templates(template_list))


@templates_app.command("diff")
def diff_templates_command(
    template1: str = typer.Argument(..., help="First template name"),
    template2: str = typer.Argument(..., help="Second template name"),
):
    """Show detailed diff between two templates."""
    registry = get_registry()

    t1 = registry.get_template(template1)
    t2 = registry.get_template(template2)

    if not t1:
        console.print(f"[red]Error: Template not found: {template1}[/red]")
        raise typer.Exit(1)

    if not t2:
        console.print(f"[red]Error: Template not found: {template2}[/red]")
        raise typer.Exit(1)

    console.print(format_template_diff(t1, t2))


@templates_app.command("blend")
def blend_templates_command(
    templates: list[str] = typer.Argument(
        ...,
        help="Template names to blend (2-8 templates)",
    ),
    mode: str = typer.Option(
        "union",
        "--mode",
        "-m",
        help="Blend mode: 'union' (all rules), 'consensus' (majority rules), 'weighted' (weighted selection)",
    ),
    weights: Optional[str] = typer.Option(
        None,
        "--weights",
        "-w",
        help="Weights for weighted mode (format: template1:0.5,template2:0.5)",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Name for the blended template",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Description for the blended template",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path to save blended template (YAML format)",
    ),
    version: str = typer.Option(
        "1.0",
        "--version",
        "-v",
        help="Version for the blended template",
    ),
):
    """Blend multiple templates into a single configuration."""
    if len(templates) < 2:
        console.print("[red]Error: Need at least 2 templates to blend.[/red]")
        raise typer.Exit(1)

    if len(templates) > 8:
        console.print("[yellow]Warning: Blending more than 8 templates may be slow.[/yellow]")

    registry = get_registry()

    # Get template metadata
    template_list = []
    missing = []
    for template_name in templates:
        template = registry.get_template(template_name)
        if template:
            template_list.append(template)
        else:
            missing.append(template_name)

    if missing:
        console.print(f"[red]Error: Template(s) not found: {', '.join(missing)}[/red]")
        console.print("\n[dim]Use 'speckit templates list' to see available templates.[/dim]")
        raise typer.Exit(1)

    # Parse weights if provided
    weight_dict = None
    if mode == "weighted":
        if not weights:
            console.print("[red]Error: --weights required for weighted mode.[/red]")
            console.print("\n[dim]Format: --weights template1:0.5,template2:0.5[/dim]")
            raise typer.Exit(1)

        try:
            weight_dict = {}
            for pair in weights.split(","):
                template_name, weight = pair.strip().split(":")
                weight_dict[template_name] = float(weight)

            # Validate all templates have weights
            for template_name in templates:
                if template_name not in weight_dict:
                    console.print(f"[red]Error: Missing weight for template: {template_name}[/red]")
                    raise typer.Exit(1)

        except ValueError as e:
            console.print(f"[red]Error: Invalid weights format. Use: template1:0.5,template2:0.5[/red]")
            raise typer.Exit(1)

    # Create blended template
    try:
        from pathlib import Path

        blended = blend_templates(
            templates=template_list,
            mode=mode,
            weights=weight_dict,
            name=name or "",
            description=description or ""
        )

        console.print(format_blended_template(blended))

        # Show rule breakdown
        severity_counts = {}
        category_counts = {}
        for rule in blended.rules:
            severity = rule.get("severity", "info")
            category = rule.get("category", "general")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

        console.print("\n[bold]Rule Breakdown:[/bold]")
        console.print("  By Severity:")
        for severity, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
            color = {"fail": "red", "warn": "yellow", "info": "blue"}.get(severity, "white")
            console.print(f"    [{color}]{severity}[/{color}]: {count}")

        console.print("  By Category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            console.print(f"    {category}: {count}")

        # Save to file if requested
        if output:
            output_path = Path(output)
            save_blended_template(blended, output_path, version=version)
            console.print(f"\n[green]✓ Blended template saved to: {output_path}[/green]")
            console.print(f"\n[dim]Usage: speckit loop --criteria {output_path.stem}[/dim]")
        else:
            console.print(f"\n[dim]Usage: speckit loop --criteria {blended.name}[/dim]")
            console.print("[dim]Use --output to save the blended template to a file.[/dim]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error blending templates: {e}[/red]")
        raise typer.Exit(1)


def _print_detailed_templates(templates: list[TemplateMetadata]) -> None:
    """Print detailed template information."""
    for template in templates:
        compatible = get_registry().get_compatible_templates(template.name)

        console.print(
            Panel(
                f"""[bold cyan]{template.display_name}[/bold cyan] [dim]({template.name})[/dim]

[bold]Version:[/bold] {template.version}
[bold]Category:[/bold] {template.category.value}
[bold]Rules:[/bold] {template.rule_count}

[bold]Description:[/bold]
{template.description}

[bold]Domain Tags:[/bold] {', '.join(sorted(template.domain_tags)) if template.domain_tags else 'none'}

[bold]Compatible With:[/bold] {', '.join(compatible) if compatible else 'none'}""",
                border_style="cyan" if template.is_builtin else "blue",
            )
        )


# Create presets app for blend preset commands
presets_app = typer.Typer(
    name="presets",
    help="Blend Presets - Pre-configured template blends for common use cases",
    add_completion=False,
)


@presets_app.command("list")
def list_presets_command(
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Filter by tag (e.g., web, mobile, api)",
    ),
    project_type: Optional[str] = typer.Option(
        None,
        "--project-type",
        "-p",
        help="Filter by project type (e.g., web-app, microservice)",
    ),
):
    """List all available blend presets."""
    registry = get_registry()
    presets = registry.list_blend_presets(tag=tag, project_type=project_type)

    if not presets:
        console.print("[yellow]No blend presets found matching the criteria.[/yellow]")
        return

    console.print("\n[bold cyan]Blend Presets[/bold cyan]\n")

    for preset in presets:
        tags_str = ', '.join(sorted(preset.tags)) if preset.tags else 'none'
        project_types_str = ', '.join(preset.project_types) if preset.project_types else 'none'

        console.print(
            Panel(
                f"""[bold green]{preset.name}[/bold green]

[bold]Description:[/bold] {preset.description}
[bold]Mode:[/bold] {preset.mode}
[bold]Templates:[/bold] {', '.join(preset.templates)}
[bold]Tags:[/bold] {tags_str}
[bold]Project Types:[/bold] {project_types_str}""",
                border_style="green",
            )
        )

    console.print(f"\n[dim]Total: {len(presets)} preset(s)[/dim]")
    console.print("\n[dim]Usage: speckit templates presets apply <preset-name>[/dim]")


@presets_app.command("info")
def preset_info_command(
    preset_name: str = typer.Argument(
        ...,
        help="Preset name (e.g., full_stack_secure, microservices_robust)",
    )
):
    """Show detailed information about a specific blend preset."""
    registry = get_registry()
    preset = registry.get_blend_preset(preset_name)

    if not preset:
        console.print(f"[red]Blend preset not found: {preset_name}[/red]")
        console.print("\n[dim]Use 'speckit templates presets list' to see available presets.[/dim]")
        raise typer.Exit(1)

    tags_str = ', '.join(sorted(preset.tags)) if preset.tags else 'none'
    project_types_str = ', '.join(preset.project_types) if preset.project_types else 'none'

    console.print(
        Panel(
            f"""[bold cyan]Preset:[/bold cyan] {preset.name}

[bold]Description:[/bold]
{preset.description}

[bold]Configuration:[/bold]
  Mode: {preset.mode}
  Templates: {', '.join(preset.templates)}

[bold]Metadata:[/bold]
  Tags: {tags_str}
  Project Types: {project_types_str}

[bold]Weights:[/bold]
  {'Yes' if preset.weights else 'No (uniform)'}""",
            title=f"[bold]{preset_name}[/bold]",
            border_style="green",
        )
    )

    console.print(f"\n[dim]Usage: speckit templates presets apply {preset_name}[/dim]")


@presets_app.command("search")
def search_presets_command(
    query: str = typer.Argument(
        ...,
        help="Search query (keyword in name, description, tags, or template names)",
    )
):
    """Search blend presets by keyword."""
    registry = get_registry()
    results = registry.search_blend_presets(query)

    if not results:
        console.print(f"[yellow]No blend presets found matching '{query}'[/yellow]")
        console.print("\n[dim]Try searching for: web, api, mobile, security, testing[/dim]")
        return

    console.print(f"\n[bold]Found {len(results)} preset(s) matching '{query}':[/bold]\n")

    for preset in results:
        tags_str = ', '.join(sorted(preset.tags)) if preset.tags else 'none'
        console.print(f"[bold green]{preset.name}[/bold green]: {preset.description}")
        console.print(f"  Templates: {', '.join(preset.templates)}")
        console.print(f"  Tags: {tags_str}")
        console.print("")

    console.print(f"\n[dim]Usage: speckit templates presets apply <preset-name>[/dim]")


@presets_app.command("recommend")
def recommend_preset_command(
    project_type: str = typer.Argument(
        ...,
        help="Project type (e.g., web-app, microservice, api, mobile-app)",
    )
):
    """Recommend a blend preset for a project type."""
    registry = get_registry()
    preset = registry.recommend_blend_preset(project_type)

    if not preset:
        console.print(f"[yellow]No preset recommendation for project type: {project_type}[/yellow]")
        console.print("\n[dim]Use 'speckit templates presets list' to see all available presets.[/dim]")
        return

    tags_str = ', '.join(sorted(preset.tags)) if preset.tags else 'none'

    console.print(
        f"\n[bold cyan]Recommended for '{project_type}':[/bold cyan] {preset.name}\n"
    )
    console.print(f"[dim]{preset.description}[/dim]\n")
    console.print(f"[bold]Mode:[/bold] {preset.mode}")
    console.print(f"[bold]Templates:[/bold] {', '.join(preset.templates)}")
    console.print(f"[bold]Tags:[/bold] {tags_str}")

    console.print(f"\n[dim]Usage: speckit templates presets apply {preset.name}[/dim]")


@presets_app.command("apply")
def apply_preset_command(
    preset_name: str = typer.Argument(
        ...,
        help="Preset name to apply",
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Custom name for the blended result",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Custom description for the blended result",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path to save blended template (YAML format)",
    ),
    version: str = typer.Option(
        "1.0",
        "--version",
        "-v",
        help="Version for the blended template",
    ),
):
    """Apply a blend preset to create a blended template."""
    registry = get_registry()

    preset = registry.get_blend_preset(preset_name)
    if not preset:
        console.print(f"[red]Blend preset not found: {preset_name}[/red]")
        console.print("\n[dim]Use 'speckit templates presets list' to see available presets.[/dim]")
        raise typer.Exit(1)

    console.print(f"[bold]Applying preset:[/bold] {preset_name}")
    console.print(f"[dim]Templates: {', '.join(preset.templates)}[/dim]")
    console.print(f"[dim]Mode: {preset.mode}[/dim]\n")

    # Apply preset
    blended = registry.apply_blend_preset(
        preset_name=preset_name,
        custom_name=name,
        custom_description=description
    )

    if not blended:
        console.print(f"[red]Error: Could not apply preset. Some templates may not exist.[/red]")
        raise typer.Exit(1)

    console.print(format_blended_template(blended))

    # Show rule breakdown
    severity_counts = {}
    category_counts = {}
    for rule in blended.rules:
        severity = rule.get("severity", "info")
        category = rule.get("category", "general")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    console.print("\n[bold]Rule Breakdown:[/bold]")
    console.print("  By Severity:")
    for severity, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
        color = {"fail": "red", "warn": "yellow", "info": "blue"}.get(severity, "white")
        console.print(f"    [{color}]{severity}[/{color}]: {count}")

    console.print("  By Category:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        console.print(f"    {category}: {count}")

    # Save to file if requested
    if output:
        output_path = Path(output)
        save_blended_template(blended, output_path, version=version)
        console.print(f"\n[green]✓ Blended template saved to: {output_path}[/green]")
        console.print(f"\n[dim]Usage: speckit loop --criteria {output_path.stem}[/dim]")
    else:
        console.print(f"\n[dim]Usage: speckit loop --criteria {blended.name}[/dim]")
        console.print("[dim]Use --output to save the blended template to a file.[/dim]")


def main():
    """Entry point for templates CLI."""
    templates_app()


def main():
    """Entry point for templates CLI."""
    templates_app()


if __name__ == "__main__":
    main()
