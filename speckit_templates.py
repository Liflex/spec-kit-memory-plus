#!/usr/bin/env python3
"""
Spec Kit Templates CLI (Exp 126)

Standalone entry point for template registry commands.
Run directly: python speckit_templates.py list
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import typer
from rich.console import Console

# Import template registry directly without going through quality package
import importlib.util

def load_template_registry():
    """Load template_registry module directly to avoid circular imports."""
    tr_path = src_path / "specify_cli" / "quality" / "template_registry.py"
    spec = importlib.util.spec_from_file_location("template_registry", tr_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["template_registry"] = module
    spec.loader.exec_module(module)
    return module

tr_module = load_template_registry()
TemplateRegistry = tr_module.TemplateRegistry
TemplateCategory = tr_module.TemplateCategory
get_registry = tr_module.get_registry
print_template_table = tr_module.print_template_table
print_combination_table = tr_module.print_combination_table

console = Console()
app = typer.Typer(
    name="speckit-templates",
    help="Quality Template Registry - Discovery and recommendations",
)

@app.command()
def list(
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    builtin: bool = typer.Option(False, "--builtin", "-b", help="Only built-in templates"),
):
    """List all available quality templates."""
    registry = get_registry()
    cat_enum = None
    if category:
        try:
            cat_enum = TemplateCategory(category.lower())
        except ValueError:
            console.print(f"[red]Invalid category: {category}[/red]")
            raise typer.Exit(1)
    templates = registry.list_templates(category=cat_enum, builtin_only=builtin)
    console.print(print_template_table(templates))

@app.command()
def info(template_name: str = typer.Argument(..., help="Template name")):
    """Show detailed information about a template."""
    registry = get_registry()
    template = registry.get_template(template_name)
    if not template:
        console.print(f"[red]Template not found: {template_name}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold cyan]{template.display_name}[/bold cyan]")
    console.print(f"Version: {template.version}")
    console.print(f"Category: {template.category.value}")
    console.print(f"Rules: {template.rule_count}")
    console.print(f"\n{template.description}")

@app.command()
def search(query: str = typer.Argument(..., help="Search query")):
    """Search templates by keyword."""
    registry = get_registry()
    results = registry.search_templates(query)
    if not results:
        console.print(f"[yellow]No templates found matching '{query}'[/yellow]")
        return
    console.print(print_template_table(results))

@app.command()
def recommend(project_type: str = typer.Argument(..., help="Project type")):
    """Get template recommendations for a project type."""
    registry = get_registry()
    recommendations = registry.get_recommendations(project_type)
    if not recommendations:
        console.print(f"[yellow]No recommendations for: {project_type}[/yellow]")
        return
    best = recommendations[0]
    console.print(f"[bold cyan]Recommended: {best.name.replace('_', ' ').title()}[/bold cyan]")
    console.print(f"{best.description}")
    console.print(f"\nTemplates: {', '.join(best.templates)}")

@app.command()
def stats():
    """Show template registry statistics."""
    registry = get_registry()
    stats = registry.get_template_stats()
    console.print("[bold cyan]Template Registry Statistics[/bold cyan]")
    console.print(f"Total Templates: {stats['total_templates']}")
    console.print(f"Built-in: {stats['builtin_templates']}")
    console.print(f"Custom: {stats['custom_templates']}")
    console.print(f"Total Rules: {stats['total_rules']}")

@app.command()
def combinations():
    """List all recommended template combinations."""
    console.print("[bold cyan]Recommended Template Combinations[/bold cyan]")
    console.print(print_combination_table(TemplateRegistry.RECOMMENDED_COMBINATIONS))

if __name__ == "__main__":
    app()
