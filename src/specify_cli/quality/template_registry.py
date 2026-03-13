"""
Quality Template Registry and Discovery System (Exp 125)

Provides a central registry for all quality templates with:
- Template discovery and listing
- Template metadata extraction
- Template combination recommendations
- Search and filter capabilities
"""

from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class TemplateCategory(Enum):
    """Template categories for organization"""
    CORE = "core"  # Original 13 built-in templates
    INFRASTRUCTURE = "infrastructure"  # Infra-related templates
    ARCHITECTURE = "architecture"  # Architecture patterns
    DOMAIN = "domain"  # Domain-specific templates


@dataclass
class TemplateMetadata:
    """Metadata about a quality template"""
    name: str
    version: str
    description: str
    file_path: str
    category: TemplateCategory
    rule_count: int = 0
    domain_tags: Set[str] = field(default_factory=set)
    has_priority_profiles: bool = False
    priority_profile_names: List[str] = field(default_factory=list)
    phases: List[str] = field(default_factory=list)
    severity_breakdown: Dict[str, int] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        """Human-readable display name"""
        return self.name.replace("-", " ").replace("_", " ").title()

    @property
    def is_builtin(self) -> bool:
        """Whether this is a built-in template"""
        return self.category == TemplateCategory.CORE


@dataclass
class TemplateCombination:
    """Recommended template combination for specific use cases"""
    name: str
    description: str
    templates: List[str]
    use_case: str
    project_types: List[str]




@dataclass
class BlendPreset:
    """Pre-configured blend preset for common use cases"""
    name: str
    description: str
    templates: List[str]
    mode: str  # "union", "consensus", "weighted"
    weights: Optional[Dict[str, float]] = None  # For weighted mode
    project_types: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class BlendedTemplate:
    """Result of blending multiple templates"""
    name: str
    description: str
    source_templates: List[str]  # Names of source templates
    blend_mode: str  # "union", "consensus", "weighted"
    rules: List[dict]  # Blended rules
    metadata: Dict[str, any]  # Additional metadata




class TemplateRegistry:
    """
    Central registry for quality templates.

    Provides discovery, metadata extraction, and recommendation
    capabilities for all quality templates.
    """

    # Built-in criteria from prepare.py (DO NOT modify during experiments)
    BUILTIN_CRITERIA = [
        "api-spec", "code-gen", "docs", "config",
        "database", "frontend", "backend", "infrastructure",
        "testing", "security", "performance", "ui-ux", "live-test"
    ]

    # Blend presets for common use cases
    BLEND_PRESETS = [
        BlendPreset(
            name="full_stack_secure",
            description="Full-stack web application with enhanced security focus",
            templates=["frontend", "backend", "api-spec", "security", "performance", "testing"],
            mode="union",
            project_types=["web-app", "full-stack"],
            tags={"web", "security", "full-stack"}
        ),
        BlendPreset(
            name="microservices_robust",
            description="Microservices with robust communication and testing",
            templates=["api-gateway", "service-mesh", "backend", "security", "testing", "infrastructure"],
            mode="consensus",
            project_types=["microservice", "distributed-system"],
            tags={"microservice", "distributed", "robust"}
        ),
        BlendPreset(
            name="api_first",
            description="API-first development with comprehensive specification",
            templates=["api-spec", "backend", "security", "docs", "testing"],
            mode="union",
            project_types=["api", "graphql-api", "rest-api"],
            tags={"api", "documentation"}
        ),
        BlendPreset(
            name="mobile_backend",
            description="Mobile app backend with security and performance",
            templates=["mobile", "api-spec", "backend", "security", "performance"],
            mode="union",
            project_types=["mobile-app", "api"],
            tags={"mobile", "backend"}
        ),
        BlendPreset(
            name="data_pipeline",
            description="Data pipeline with performance and testing focus",
            templates=["database", "backend", "performance", "testing", "docs"],
            mode="consensus",
            project_types=["ml-service", "data-pipeline", "etl"],
            tags={"data", "ml", "pipeline"}
        ),
        BlendPreset(
            name="cloud_native",
            description="Cloud-native application with infrastructure focus",
            templates=["serverless", "api-gateway", "security", "performance", "infrastructure"],
            mode="union",
            project_types=["serverless", "cloud-native"],
            tags={"cloud", "serverless"}
        ),
        BlendPreset(
            name="quality_rigorous",
            description="Rigorous quality standards with comprehensive testing",
            templates=["testing", "security", "performance", "docs", "code-gen"],
            mode="union",
            project_types=["enterprise", "production"],
            tags={"quality", "testing", "enterprise"}
        ),
        BlendPreset(
            name="startup_mvp",
            description="Balanced quality for MVP development",
            templates=["frontend", "backend", "api-spec", "testing"],
            mode="consensus",
            project_types=["startup", "mvp"],
            tags={"startup", "mvp", "lean"}
        ),
        BlendPreset(
            name="iot_platform",
            description="IoT platform with device and infrastructure focus",
            templates=["backend", "security", "infrastructure", "performance", "testing"],
            mode="union",
            project_types=["iot", "embedded"],
            tags={"iot", "embedded"}
        ),
        BlendPreset(
            name="devsecops",
            description="DevSecOps with security and infrastructure integration",
            templates=["security", "infrastructure", "terraform", "testing", "config"],
            mode="union",
            project_types=["devops", "platform"],
            tags={"devsecops", "infrastructure", "security"}
        ),
    ]

    # Recommended template combinations
    RECOMMENDED_COMBINATIONS = [
        TemplateCombination(
            name="full_stack_web_app",
            description="Complete quality coverage for full-stack web applications",
            templates=["frontend", "backend", "api-spec", "security", "performance", "testing", "docs"],
            use_case="Web application with frontend and backend",
            project_types=["web-app", "full-stack"]
        ),
        TemplateCombination(
            name="microservices_platform",
            description="Quality rules for microservices architecture",
            templates=["api-gateway", "service-mesh", "backend", "security", "performance", "testing", "infrastructure"],
            use_case="Microservices-based architecture",
            project_types=["microservice", "distributed-system"]
        ),
        TemplateCombination(
            name="ml_pipeline",
            description="Quality rules for ML/data pipelines",
            templates=["database", "backend", "performance", "testing", "docs", "config"],
            use_case="Machine learning or data processing pipeline",
            project_types=["ml-service", "data-pipeline"]
        ),
        TemplateCombination(
            name="mobile_app_api",
            description="Quality rules for mobile app with API backend",
            templates=["mobile", "api-spec", "backend", "security", "performance", "testing"],
            use_case="Mobile application with backend API",
            project_types=["mobile-app", "api"]
        ),
        TemplateCombination(
            name="graphql_api",
            description="Quality rules for GraphQL API services",
            templates=["api-spec", "backend", "security", "performance", "testing", "docs"],
            use_case="GraphQL API service",
            project_types=["graphql-api", "api"]
        ),
        TemplateCombination(
            name="serverless_app",
            description="Quality rules for serverless applications",
            templates=["serverless", "api-gateway", "security", "performance", "testing", "docs"],
            use_case="Serverless/FaaS application",
            project_types=["serverless", "cloud-native"]
        ),
        TemplateCombination(
            name="desktop_application",
            description="Quality rules for desktop applications",
            templates=["desktop", "backend", "security", "testing", "docs"],
            use_case="Desktop application (Electron, Tauri, native)",
            project_types=["desktop", "client-app"]
        ),
        TemplateCombination(
            name="infrastructure_as_code",
            description="Quality rules for IaC and infrastructure",
            templates=["terraform", "infrastructure", "container", "config", "security"],
            use_case="Infrastructure as Code projects",
            project_types=["infrastructure", "devops", "platform"]
        ),
    ]

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the template registry.

        Args:
            templates_dir: Path to templates directory. If None, uses default.
        """
        if templates_dir is None:
            # Default to src/specify_cli/quality/templates
            current_dir = Path(__file__).parent
            templates_dir = current_dir / "templates"

        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, TemplateMetadata] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from the templates directory"""
        if not self.templates_dir.exists():
            return

        for template_file in self.templates_dir.glob("*.yml"):
            metadata = self._extract_metadata(template_file)
            if metadata:
                self._templates[metadata.name] = metadata

    def _extract_metadata(self, template_path: Path) -> Optional[TemplateMetadata]:
        """
        Extract metadata from a template file.

        Args:
            template_path: Path to template YAML file

        Returns:
            TemplateMetadata or None if extraction fails
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            if not content:
                return None

            name = template_path.stem
            version = content.get('version', '1.0')
            description = content.get('description', '')
            rules = content.get('rules', [])

            # Determine category
            category = self._determine_category(name)

            # Extract domain tags from rules
            domain_tags = set()
            severity_breakdown = {}

            for rule in rules:
                for tag in rule.get('domain_tags', []):
                    domain_tags.add(tag)
                severity = rule.get('severity', 'info')
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1

            # Extract priority profiles
            priority_profiles = content.get('priority_profiles', {})
            profile_names = list(priority_profiles.keys()) if priority_profiles else []

            # Extract phases
            phases_config = content.get('phases', {})
            phases = list(phases_config.keys()) if phases_config else []

            return TemplateMetadata(
                name=name,
                version=version,
                description=description,
                file_path=str(template_path),
                category=category,
                rule_count=len(rules),
                domain_tags=domain_tags,
                has_priority_profiles=bool(priority_profiles),
                priority_profile_names=profile_names,
                phases=phases,
                severity_breakdown=severity_breakdown
            )

        except Exception as e:
            # Silently skip invalid templates
            return None

    def _determine_category(self, name: str) -> TemplateCategory:
        """Determine template category based on name"""
        if name in self.BUILTIN_CRITERIA:
            return TemplateCategory.CORE

        infrastructure_templates = {
            "api-gateway", "cache", "container", "database-migration",
            "serverless", "service-mesh", "terraform", "message-queue", "websocket"
        }

        architecture_templates = {
            "grpc", "desktop"
        }

        domain_templates = {
            "mobile"
        }

        if name in infrastructure_templates:
            return TemplateCategory.INFRASTRUCTURE
        elif name in architecture_templates:
            return TemplateCategory.ARCHITECTURE
        elif name in domain_templates:
            return TemplateCategory.DOMAIN
        else:
            return TemplateCategory.CORE  # Default to core

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        builtin_only: bool = False
    ) -> List[TemplateMetadata]:
        """
        List all templates, optionally filtered by category.

        Args:
            category: Filter by category
            builtin_only: Only show built-in templates

        Returns:
            List of template metadata
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if builtin_only:
            templates = [t for t in templates if t.is_builtin]

        return sorted(templates, key=lambda t: t.name)

    def get_template(self, name: str) -> Optional[TemplateMetadata]:
        """
        Get metadata for a specific template.

        Args:
            name: Template name

        Returns:
            TemplateMetadata or None if not found
        """
        return self._templates.get(name)

    def search_templates(self, query: str) -> List[TemplateMetadata]:
        """
        Search templates by name, description, or domain tags.

        Args:
            query: Search query

        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        results = []

        for template in self._templates.values():
            # Search in name
            if query_lower in template.name.lower():
                results.append(template)
                continue

            # Search in description
            if query_lower in template.description.lower():
                results.append(template)
                continue

            # Search in domain tags
            if any(query_lower in tag.lower() for tag in template.domain_tags):
                results.append(template)
                continue

        return results

    def get_recommendations(
        self,
        project_type: str,
        domain_tags: Optional[Set[str]] = None
    ) -> List[TemplateCombination]:
        """
        Get recommended template combinations for a project type.

        Args:
            project_type: Type of project (e.g., "web-app", "microservice")
            domain_tags: Optional domain tags for more specific recommendations

        Returns:
            List of recommended template combinations
        """
        recommendations = []

        for combination in self.RECOMMENDED_COMBINATIONS:
            # Match by project type
            if project_type.lower() in [pt.lower() for pt in combination.project_types]:
                recommendations.append(combination)

            # Match by domain tags if provided
            if domain_tags:
                for template_name in combination.templates:
                    template = self.get_template(template_name)
                    if template and domain_tags.intersection(template.domain_tags):
                        if combination not in recommendations:
                            recommendations.append(combination)
                        break

        return recommendations

    def get_template_stats(self) -> Dict[str, any]:
        """
        Get statistics about all templates.

        Returns:
            Dictionary with template statistics
        """
        total = len(self._templates)
        by_category = {}
        total_rules = 0

        for template in self._templates.values():
            cat = template.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            total_rules += template.rule_count

        return {
            "total_templates": total,
            "builtin_templates": len(self.BUILTIN_CRITERIA),
            "custom_templates": total - len(self.BUILTIN_CRITERIA),
            "by_category": by_category,
            "total_rules": total_rules,
        }

    def get_compatible_templates(self, template_name: str) -> List[str]:
        """
        Get templates that are commonly used together with the given template.

        Args:
            template_name: Name of the template

        Returns:
            List of compatible template names
        """
        compatible = set()

        # Find combinations that include this template
        for combination in self.RECOMMENDED_COMBINATIONS:
            if template_name in combination.templates:
                compatible.update(combination.templates)

        # Remove the template itself
        compatible.discard(template_name)

        return sorted(list(compatible))

    def list_blend_presets(
        self,
        tag: Optional[str] = None,
        project_type: Optional[str] = None
    ) -> List[BlendPreset]:
        """
        List all blend presets, optionally filtered by tag or project type.

        Args:
            tag: Filter by tag
            project_type: Filter by project type

        Returns:
            List of blend presets
        """
        presets = self.BLEND_PRESETS

        if tag:
            presets = [p for p in presets if tag.lower() in {t.lower() for t in p.tags}]

        if project_type:
            presets = [p for p in presets if project_type.lower() in {pt.lower() for pt in p.project_types}]

        return presets

    def get_blend_preset(self, name: str) -> Optional[BlendPreset]:
        """
        Get a specific blend preset by name.

        Args:
            name: Preset name

        Returns:
            BlendPreset or None if not found
        """
        for preset in self.BLEND_PRESETS:
            if preset.name == name:
                return preset
        return None

    def search_blend_presets(self, query: str) -> List[BlendPreset]:
        """
        Search blend presets by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching presets
        """
        query_lower = query.lower()
        results = []

        for preset in self.BLEND_PRESETS:
            # Search in name
            if query_lower in preset.name.lower():
                results.append(preset)
                continue

            # Search in description
            if query_lower in preset.description.lower():
                results.append(preset)
                continue

            # Search in tags
            if any(query_lower in tag.lower() for tag in preset.tags):
                results.append(preset)
                continue

            # Search in template names
            if any(query_lower in t.lower() for t in preset.templates):
                results.append(preset)
                continue

        return results

    def recommend_blend_preset(self, project_type: str) -> Optional[BlendPreset]:
        """
        Recommend a blend preset for a given project type.

        Uses intelligent mapping between project types and blend presets,
        with fallback to keyword matching.

        Args:
            project_type: Type of project

        Returns:
            Recommended BlendPreset or None
        """
        # Direct mapping for common project types
        preset_mapping = {
            "web-app": "full_stack_secure",
            "full-stack": "full_stack_secure",
            "microservice": "microservices_robust",
            "microservices": "microservices_robust",
            "distributed-system": "microservices_robust",
            "api": "api_first",
            "rest-api": "api_first",
            "graphql-api": "api_first",
            "mobile-app": "mobile_backend",
            "mobile": "mobile_backend",
            "ml-service": "data_pipeline",
            "data-pipeline": "data_pipeline",
            "etl": "data_pipeline",
            "serverless": "cloud_native",
            "cloud-native": "cloud_native",
            "enterprise": "quality_rigorous",
            "production": "quality_rigorous",
            "startup": "startup_mvp",
            "mvp": "startup_mvp",
            "iot": "iot_platform",
            "embedded": "iot_platform",
            "devops": "devsecops",
            "platform": "devsecops",
        }

        # Try direct mapping first
        mapped_preset_name = preset_mapping.get(project_type.lower())
        if mapped_preset_name:
            return self.get_blend_preset(mapped_preset_name)

        # Fallback to tag-based matching
        presets = self.list_blend_presets(project_type=project_type)
        return presets[0] if presets else None

    def apply_blend_preset(
        self,
        preset_name: str,
        custom_name: Optional[str] = None,
        custom_description: Optional[str] = None
    ) -> Optional[BlendedTemplate]:
        """
        Apply a blend preset to create a blended template.

        Args:
            preset_name: Name of the preset to apply
            custom_name: Optional custom name for the result
            custom_description: Optional custom description

        Returns:
            BlendedTemplate or None if preset not found
        """
        preset = self.get_blend_preset(preset_name)
        if not preset:
            return None

        # Get template metadata for the preset
        templates = []
        for template_name in preset.templates:
            template = self.get_template(template_name)
            if template:
                templates.append(template)

        if not templates:
            return None

        # Create blended template
        return blend_templates(
            templates=templates,
            mode=preset.mode,
            weights=preset.weights,
            name=custom_name or preset.name,
            description=custom_description or preset.description
        )

    def get_all_blend_presets_info(self) -> List[Dict[str, any]]:
        """
        Get information about all blend presets for display.

        Returns:
            List of dictionaries with preset information
        """
        return [
            {
                "name": preset.name,
                "description": preset.description,
                "templates": preset.templates,
                "mode": preset.mode,
                "project_types": preset.project_types,
                "tags": list(preset.tags),
            }
            for preset in self.BLEND_PRESETS
        ]


# Singleton instance for easy access
_registry_instance: Optional[TemplateRegistry] = None


def get_registry(templates_dir: Optional[Path] = None) -> TemplateRegistry:
    """
    Get the singleton template registry instance.

    Args:
        templates_dir: Optional custom templates directory

    Returns:
        TemplateRegistry instance
    """
    global _registry_instance

    if _registry_instance is None or templates_dir is not None:
        _registry_instance = TemplateRegistry(templates_dir)

    return _registry_instance


def print_template_table(templates: List[TemplateMetadata], show_details: bool = False) -> str:
    """
    Format templates as a table for CLI display.

    Args:
        templates: List of templates to format
        show_details: Whether to show detailed information

    Returns:
        Formatted table string
    """
    if not templates:
        return "No templates found."

    lines = []
    lines.append("=" * 100)
    lines.append(f"{'Name':<25} {'Version':<10} {'Category':<15} {'Rules':<8} {'Description'}")
    lines.append("=" * 100)

    for template in templates:
        name_display = template.display_name
        version = template.version
        category = template.category.value
        rules = str(template.rule_count)
        description = template.description[:40] + "..." if len(template.description) > 40 else template.description

        lines.append(f"{name_display:<25} {version:<10} {category:<15} {rules:<8} {description}")

    lines.append("=" * 100)

    return "\n".join(lines)


def print_combination_table(combinations: List[TemplateCombination]) -> str:
    """
    Format template combinations as a table for CLI display.

    Args:
        combinations: List of combinations to format

    Returns:
        Formatted table string
    """
    if not combinations:
        return "No recommendations found."

    lines = []
    lines.append("=" * 100)
    lines.append(f"{'Combination':<25} {'Use Case':<30} {'Templates'}")
    lines.append("=" * 100)

    for combo in combinations:
        name = combo.name.replace("_", " ").title()
        use_case = combo.use_case[:28] + "..." if len(combo.use_case) > 28 else combo.use_case
        templates = ", ".join(combo.templates[:5])
        if len(combo.templates) > 5:
            templates += f" +{len(combo.templates) - 5} more"

        lines.append(f"{name:<25} {use_case:<30} {templates}")

    lines.append("=" * 100)

    return "\n".join(lines)


def compare_templates(templates: List[TemplateMetadata]) -> str:
    """
    Compare multiple templates side-by-side.

    Args:
        templates: List of templates to compare (2-4 recommended)

    Returns:
        Formatted comparison table string
    """
    if not templates:
        return "No templates to compare."
    if len(templates) < 2:
        return "Need at least 2 templates to compare."

    # Limit to 4 templates for readability
    templates = templates[:4]

    lines = []
    lines.append("=" * 120)
    lines.append("TEMPLATE COMPARISON")
    lines.append("=" * 120)

    # Header with template names
    header = f"{'Attribute':<30}"
    for template in templates:
        name = template.display_name[:20]
        header += f" | {name:<20}"
    lines.append(header)
    lines.append("-" * 120)

    # Row: Category
    row = f"{'Category':<30}"
    for template in templates:
        row += f" | {template.category.value:<20}"
    lines.append(row)

    # Row: Rules count
    row = f"{'Rules':<30}"
    for template in templates:
        row += f" | {str(template.rule_count):<20}"
    lines.append(row)

    # Row: Version
    row = f"{'Version':<30}"
    for template in templates:
        row += f" | {template.version:<20}"
    lines.append(row)

    # Row: Domain tags
    lines.append("-" * 120)
    lines.append("Domain Tags:")
    all_tags = set()
    for template in templates:
        all_tags.update(template.domain_tags)

    for tag in sorted(all_tags):
        row = f"  {tag:<28}"
        for template in templates:
            has_tag = tag in template.domain_tags
            row += f" | {'✓' if has_tag else '✗':<20}"
        lines.append(row)

    # Row: Severity breakdown
    lines.append("-" * 120)
    lines.append("Severity Breakdown:")
    all_severities = set()
    for template in templates:
        all_severities.update(template.severity_breakdown.keys())

    for severity in sorted(all_severities, reverse=True):
        row = f"  {severity:<28}"
        for template in templates:
            count = template.severity_breakdown.get(severity, 0)
            row += f" | {str(count):<20}"
        lines.append(row)

    # Row: Priority profiles
    lines.append("-" * 120)
    lines.append("Priority Profiles:")
    has_profiles = any(template.priority_profile_names for template in templates)
    if has_profiles:
        max_profiles = max(len(template.priority_profile_names) for template in templates)
        for i in range(max_profiles):
            row = f"  Profile {i + 1:<22}"
            for template in templates:
                profile = template.priority_profile_names[i] if i < len(template.priority_profile_names) else "-"
                row += f" | {profile:<20}"
            lines.append(row)
    else:
        lines.append("  No profiles defined")

    # Row: Phases
    lines.append("-" * 120)
    lines.append("Phases:")
    all_phases = set()
    for template in templates:
        all_phases.update(template.phases)

    if all_phases:
        for phase in sorted(all_phases):
            row = f"  {phase:<28}"
            for template in templates:
                has_phase = phase in template.phases
                row += f" | {'✓' if has_phase else '✗':<20}"
            lines.append(row)
    else:
        lines.append("  No phases defined")

    lines.append("=" * 120)

    return "\n".join(lines)


def format_template_diff(template1: TemplateMetadata, template2: TemplateMetadata) -> str:
    """
    Format a diff-style comparison between two templates.

    Args:
        template1: First template
        template2: Second template

    Returns:
        Formatted diff string
    """
    lines = []
    lines.append("=" * 100)
    lines.append(f"TEMPLATE DIFF: {template1.display_name} vs {template2.display_name}")
    lines.append("=" * 100)

    # Category difference
    if template1.category != template2.category:
        lines.append(f"[DIFF] Category: {template1.category.value} → {template2.category.value}")

    # Rules count difference
    rules_diff = template2.rule_count - template1.rule_count
    if rules_diff != 0:
        sign = "+" if rules_diff > 0 else ""
        lines.append(f"[DIFF] Rules: {template1.rule_count} → {template2.rule_count} ({sign}{rules_diff})")

    # Domain tags differences
    tags_only_1 = template1.domain_tags - template2.domain_tags
    tags_only_2 = template2.domain_tags - template1.domain_tags

    if tags_only_1 or tags_only_2:
        lines.append("[DIFF] Domain Tags:")
        if tags_only_1:
            lines.append(f"  Only in {template1.name}: {', '.join(sorted(tags_only_1))}")
        if tags_only_2:
            lines.append(f"  Only in {template2.name}: {', '.join(sorted(tags_only_2))}")

    # Severity differences
    all_severities = set(template1.severity_breakdown.keys()) | set(template2.severity_breakdown.keys())
    severity_diffs = []
    for severity in all_severities:
        count1 = template1.severity_breakdown.get(severity, 0)
        count2 = template2.severity_breakdown.get(severity, 0)
        if count1 != count2:
            severity_diffs.append(f"{severity}: {count1}→{count2}")

    if severity_diffs:
        lines.append("[DIFF] Severity Breakdown:")
        for diff in severity_diffs:
            lines.append(f"  {diff}")

    lines.append("=" * 100)

    return "\n".join(lines)


def blend_templates(
    templates: List[TemplateMetadata],
    mode: str = "union",
    weights: Optional[Dict[str, float]] = None,
    name: str = "blended",
    description: str = ""
) -> BlendedTemplate:
    """
    Blend multiple templates into a single configuration.

    Args:
        templates: List of templates to blend (2-8 recommended)
        mode: Blend mode - "union" (all rules), "consensus" (majority rules), "weighted" (weighted selection)
        weights: Optional weights for each template (only for weighted mode)
        name: Name for the blended template
        description: Description for the blended template

    Returns:
        BlendedTemplate with combined rules

    Raises:
        ValueError: If invalid parameters provided
    """
    if len(templates) < 2:
        raise ValueError("Need at least 2 templates to blend")

    if len(templates) > 8:
        raise ValueError("Cannot blend more than 8 templates at once")

    if mode not in ("union", "consensus", "weighted"):
        raise ValueError(f"Invalid blend mode: {mode}. Must be 'union', 'consensus', or 'weighted'")

    if mode == "weighted" and not weights:
        raise ValueError("Weights must be provided for weighted mode")

    # Load full template content
    template_contents = []
    for template in templates:
        try:
            with open(template.file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if content:
                    template_contents.append(content)
        except Exception:
            continue

    if not template_contents:
        raise ValueError("No valid template contents found")

    # Generate name and description if not provided
    if not name:
        template_names = [t.name for t in templates]
        name = f"blend-{'-'.join(template_names[:3])}"

    if not description:
        source_names = ", ".join([t.display_name for t in templates])
        description = f"Blended template from {source_names}"

    # Blend rules based on mode
    if mode == "union":
        blended_rules = _blend_union(template_contents)
    elif mode == "consensus":
        blended_rules = _blend_consensus(template_contents)
    else:  # weighted
        blended_rules = _blend_weighted(template_contents, weights, templates)

    # Blend priority profiles (union of all profiles)
    priority_profiles = {}
    profiles_count = {}  # Track which templates have which profiles

    for i, content in enumerate(template_contents):
        template_name = templates[i].name
        for profile_name, profile_config in content.get('priority_profiles', {}).items():
            key = f"{template_name}:{profile_name}"
            if key not in profiles_count:
                profiles_count[key] = []
            profiles_count[key].append(template_name)

            # Store profile with template prefix to avoid conflicts
            new_profile_name = f"{template_name}_{profile_name}"
            priority_profiles[new_profile_name] = profile_config

    # Blend phases (union of all phases)
    phases = {}
    for content in template_contents:
        for phase_name, phase_config in content.get('phases', {}).items():
            if phase_name not in phases:
                phases[phase_name] = phase_config

    # Create metadata
    metadata = {
        "source_templates": [t.name for t in templates],
        "source_count": len(templates),
        "total_rules": len(blended_rules),
        "blend_mode": mode,
    }

    if mode == "weighted":
        metadata["weights"] = weights

    return BlendedTemplate(
        name=name,
        description=description,
        source_templates=[t.name for t in templates],
        blend_mode=mode,
        rules=blended_rules,
        metadata={
            "priority_profiles": priority_profiles,
            "phases": phases,
            **metadata
        }
    )


def _blend_union(template_contents: List[dict]) -> List[dict]:
    """Blend rules using union mode (all unique rules)"""
    seen_rules = set()
    blended_rules = []

    for content in template_contents:
        for rule in content.get('rules', []):
            # Create a unique key for the rule
            rule_key = (
                rule.get('category', ''),
                rule.get('name', ''),
                rule.get('check', '')
            )
            if rule_key not in seen_rules:
                seen_rules.add(rule_key)
                blended_rules.append(rule)

    return blended_rules


def _blend_consensus(template_contents: List[dict]) -> List[dict]:
    """Blend rules using consensus mode (rules in majority of templates)"""
    from collections import defaultdict

    rule_votes = defaultdict(lambda: {"count": 0, "rule": None, "severities": []})

    for content in template_contents:
        for rule in content.get('rules', []):
            rule_key = (
                rule.get('category', ''),
                rule.get('name', ''),
                rule.get('check', '')
            )
            rule_votes[rule_key]["count"] += 1
            rule_votes[rule_key]["severities"].append(rule.get('severity', 'info'))
            # Keep the first seen rule as reference
            if rule_votes[rule_key]["rule"] is None:
                rule_votes[rule_key]["rule"] = rule

    threshold = len(template_contents) / 2  # Majority threshold
    blended_rules = []

    for key, data in rule_votes.items():
        if data["count"] >= threshold:
            rule = data["rule"].copy()
            # Use highest severity among votes
            severity_order = {"fail": 3, "warn": 2, "info": 1}
            highest_severity = max(
                data["severities"],
                key=lambda s: severity_order.get(s, 0)
            )
            rule["severity"] = highest_severity
            blended_rules.append(rule)

    return blended_rules


def _blend_weighted(
    template_contents: List[dict],
    weights: Dict[str, float],
    templates: List[TemplateMetadata]
) -> List[dict]:
    """Blend rules using weighted selection"""
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight == 0:
        total_weight = 1

    # Map template names to weights
    template_weights = {}
    for template in templates:
        template_weights[template.name] = weights.get(template.name, 1.0) / total_weight

    # Track rules with their cumulative weight
    from collections import defaultdict

    rule_scores = defaultdict(lambda: {"score": 0, "rule": None, "severities": []})

    for i, content in enumerate(template_contents):
        template_name = templates[i].name
        weight = template_weights.get(template_name, 0)

        for rule in content.get('rules', []):
            rule_key = (
                rule.get('category', ''),
                rule.get('name', ''),
                rule.get('check', '')
            )
            rule_scores[rule_key]["score"] += weight
            rule_scores[rule_key]["severities"].append(rule.get('severity', 'info'))
            if rule_scores[rule_key]["rule"] is None:
                rule_scores[rule_key]["rule"] = rule

    # Sort by score and take top rules
    sorted_rules = sorted(
        rule_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    # Take rules with score >= average
    avg_score = 1.0 / len(template_contents)
    blended_rules = []

    for key, data in sorted_rules:
        if data["score"] >= avg_score * 0.5:  # At least 50% of average
            rule = data["rule"].copy()
            # Use highest severity
            severity_order = {"fail": 3, "warn": 2, "info": 1}
            highest_severity = max(
                data["severities"],
                key=lambda s: severity_order.get(s, 0)
            )
            rule["severity"] = highest_severity
            blended_rules.append(rule)

    return blended_rules


def save_blended_template(
    blended: BlendedTemplate,
    output_path: Path,
    version: str = "1.0"
) -> None:
    """
    Save a blended template to a YAML file.

    Args:
        blended: BlendedTemplate to save
        output_path: Path to save the template
        version: Version string for the template
    """
    output = {
        "version": version,
        "description": blended.description,
        "source_templates": blended.source_templates,
        "blend_mode": blended.blend_mode,
        "rules": blended.rules
    }

    # Add priority profiles if present
    if "priority_profiles" in blended.metadata:
        output["priority_profiles"] = blended.metadata["priority_profiles"]

    # Add phases if present
    if "phases" in blended.metadata:
        output["phases"] = blended.metadata["phases"]

    # Ensure parent directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(output, f, default_flow_style=False, sort_keys=False)


def format_blended_template(blended: BlendedTemplate) -> str:
    """
    Format a blended template for display.

    Args:
        blended: BlendedTemplate to format

    Returns:
        Formatted string representation
    """
    lines = []
    lines.append("=" * 100)
    lines.append(f"BLENDED TEMPLATE: {blended.name}")
    lines.append("=" * 100)
    lines.append(f"")
    lines.append(f"[bold]Description:[/bold] {blended.description}")
    lines.append(f"[bold]Mode:[/bold] {blended.blend_mode}")
    lines.append(f"[bold]Source Templates:[/bold] {', '.join(blended.source_templates)}")
    lines.append(f"[bold]Total Rules:[/bold] {len(blended.rules)}")

    # Show weights if weighted mode
    if blended.blend_mode == "weighted" and "weights" in blended.metadata:
        lines.append(f"[bold]Weights:[/bold]")
        for template, weight in blended.metadata["weights"].items():
            lines.append(f"  {template}: {weight:.2f}")

    lines.append("")
    lines.append("=" * 100)

    return "\n".join(lines)


# ============================================================
# Template Integration (formerly template_integration.py)
# ============================================================

_integration_console = None

def _get_integration_console():
    global _integration_console
    if _integration_console is None:
        from rich.console import Console
        _integration_console = Console()
    return _integration_console


class TemplateIntegration:
    """
    Integration layer for template registry with quality loop.

    Provides methods to get recommended templates, validate combinations,
    and expand templates based on dependencies.
    """

    DEFAULT_TEMPLATES = ["backend", "security", "testing", "docs"]

    PROJECT_TYPE_ALIASES = {
        "web": "web-app",
        "webapp": "web-app",
        "web-app": "web-app",
        "fullstack": "full-stack",
        "full-stack": "full-stack",
        "microservice": "microservice",
        "microservices": "microservice",
        "ml": "ml-service",
        "ml-service": "ml-service",
        "ai": "ml-service",
        "mobile": "mobile-app",
        "mobile-app": "mobile-app",
        "serverless": "serverless",
        "graphql": "graphql-api",
        "graphql-api": "graphql-api",
        "desktop": "desktop",
        "infra": "infrastructure",
        "infrastructure": "infrastructure",
    }

    COMPATIBILITY_GROUPS = {
        "web-stack": {"frontend", "backend", "api-spec", "security", "performance", "testing"},
        "api-stack": {"api-spec", "backend", "security", "performance", "testing"},
        "data-stack": {"database", "backend", "performance", "testing"},
        "infra-stack": {"infrastructure", "security", "config", "testing"},
        "mobile-stack": {"mobile", "backend", "security", "testing"},
    }

    @classmethod
    def get_recommended_templates(
        cls,
        project_type: str,
        fallback_to_default: bool = True,
    ) -> List[str]:
        """Get recommended templates for a given project type."""
        normalized_type = cls.PROJECT_TYPE_ALIASES.get(
            project_type.lower(),
            project_type.lower()
        )

        registry = get_registry()
        recommendations = registry.get_recommendations(normalized_type)

        if recommendations and recommendations[0].templates:
            return recommendations[0].templates

        if fallback_to_default:
            _get_integration_console().print(
                f"[yellow]No specific recommendations for '{project_type}'. "
                f"Using default templates: {', '.join(cls.DEFAULT_TEMPLATES)}[/yellow]"
            )
            return cls.DEFAULT_TEMPLATES.copy()

        return []

    @classmethod
    def validate_template_combination(
        cls,
        templates: List[str],
    ) -> Tuple[bool, List[str], Optional[str]]:
        """Validate a template combination for compatibility."""
        registry = get_registry()
        valid_templates = []
        invalid_templates = []

        for template_name in templates:
            template = registry.get_template(template_name)
            if template:
                valid_templates.append(template_name)
            else:
                invalid_templates.append(template_name)

        warning = None
        if invalid_templates:
            warning = (
                f"Unknown templates: {', '.join(invalid_templates)}. "
                f"Use 'speckit templates list' to see available templates."
            )

        if len(valid_templates) > 1:
            conflicts = cls._detect_conflicts(valid_templates)
            if conflicts:
                conflict_msg = (
                    f"Possible template conflicts detected: {', '.join(conflicts)}. "
                    f"You may want to separate these into different quality loops."
                )
                if warning:
                    warning += " " + conflict_msg
                else:
                    warning = conflict_msg

        return len(invalid_templates) == 0, valid_templates, warning

    @classmethod
    def _detect_conflicts(cls, templates: List[str]) -> List[str]:
        """Detect potential conflicts in template combinations."""
        conflicts = []
        registry = get_registry()

        frontend_templates = [t for t in templates if registry.get_template(t)]
        for template in frontend_templates:
            metadata = registry.get_template(template)
            if metadata and "react" in metadata.domain_tags and "vue" in metadata.domain_tags:
                conflicts.append("React and Vue templates in same run")

        return conflicts

    @classmethod
    def expand_templates(
        cls,
        templates: List[str],
        include_dependencies: bool = True,
    ) -> List[str]:
        """Expand templates to include dependencies."""
        if not include_dependencies:
            return templates.copy()

        registry = get_registry()
        expanded = set(templates)

        DEPENDENCY_RULES: Dict[str, List[str]] = {
            "frontend": ["testing"],
            "backend": ["testing", "security"],
            "api-spec": ["testing", "docs"],
            "mobile": ["testing", "security"],
            "serverless": ["security", "performance"],
            "database": ["testing"],
            "cache": ["testing"],
            "message-queue": ["testing"],
            "websocket": ["security"],
            "grpc": ["testing", "docs"],
            "graphql": ["testing", "docs"],
        }

        for template in templates:
            dependencies = DEPENDENCY_RULES.get(template, [])
            for dep in dependencies:
                if registry.get_template(dep):
                    expanded.add(dep)

        return sorted(expanded)

    @classmethod
    def format_template_summary(
        cls,
        templates: List[str],
        show_compatibility: bool = True,
    ) -> str:
        """Format a summary of the selected templates."""
        if not templates:
            return "[dim]No templates selected[/dim]"

        from rich.table import Table

        registry = get_registry()
        console = _get_integration_console()

        table = Table(title="Quality Templates", show_header=True, header_style="bold cyan")
        table.add_column("Template", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Rules", style="green")
        table.add_column("Description", style="dim")

        for template_name in templates:
            template = registry.get_template(template_name)
            if template:
                table.add_row(
                    template.display_name,
                    template.category.value,
                    str(template.rule_count),
                    template.description[:50] + "..." if len(template.description) > 50 else template.description,
                )
            else:
                table.add_row(
                    template_name,
                    "[red]Unknown[/red]",
                    "[red]N/A[/red]",
                    "[red]Template not found in registry[/red]",
                )

        with console.capture() as capture:
            console.print(table)
        return capture.get()

    @classmethod
    def suggest_from_codebase(
        cls,
        project_path: Optional[Path] = None,
    ) -> List[str]:
        """Suggest templates based on codebase analysis."""
        if project_path is None:
            project_path = Path.cwd()

        suggested = set()

        INDICATORS: Dict[str, List[str]] = {
            "frontend": ["package.json", "src/components", "src/App.jsx", "src/App.tsx"],
            "backend": ["requirements.txt", "go.mod", "pom.xml", "build.gradle"],
            "api-spec": ["openapi.yaml", "swagger.yaml", "api/openapi.yaml"],
            "database": ["migrations", "schema.sql", "prisma/schema.prisma"],
            "mobile": ["ios/", "android/", "lib/"],
            "serverless": ["serverless.yml", "terraform/", "lambda/"],
            "infrastructure": ["docker/", "kubernetes/", "helm/", "terraform/"],
            "testing": ["tests/", "__tests__", "test/"],
            "docs": ["docs/", "README.md", "CHANGELOG.md"],
        }

        for template_name, patterns in INDICATORS.items():
            for pattern in patterns:
                path = project_path / pattern
                if path.exists():
                    suggested.add(template_name)
                    break

        suggested.add("security")
        return sorted(suggested)


def get_recommended_templates(
    project_type: str,
    fallback_to_default: bool = True,
) -> List[str]:
    """Convenience function to get recommended templates for a project type."""
    return TemplateIntegration.get_recommended_templates(
        project_type=project_type,
        fallback_to_default=fallback_to_default,
    )


def validate_templates(
    templates: List[str],
) -> Tuple[bool, List[str], Optional[str]]:
    """Convenience function to validate a template combination."""
    return TemplateIntegration.validate_template_combination(templates)


def expand_templates(
    templates: List[str],
    include_dependencies: bool = True,
) -> List[str]:
    """Convenience function to expand templates with dependencies."""
    return TemplateIntegration.expand_templates(
        templates=templates,
        include_dependencies=include_dependencies,
    )
