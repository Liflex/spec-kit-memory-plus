"""
Rule Manager

Manages quality rules and criteria templates.
Loads built-in and user-defined criteria templates.
"""

import yaml
from pathlib import Path
from typing import List, Optional

from specify_cli.quality.models import CriteriaTemplate, QualityRule, Phase, PhaseConfig


class CriteriaNotFound(Exception):
    """Raised when criteria template is not found"""
    def __init__(self, name: str, available: List[str]):
        self.name = name
        self.available = available
        super().__init__(
            f"Criteria template '{name}' not found. "
            f"Available: {', '.join(available)}"
        )


class InvalidCriteriaSpec(Exception):
    """Raised when criteria spec string is malformed"""
    pass


class RuleManager:
    """Manage quality rules and criteria templates"""

    # Built-in criteria directory
    BUILTIN_CRITERIA_DIR = Path(__file__).parent / "templates"

    # Auto-detect keyword mapping
    AUTO_DETECT_MAPPING = {
        "api": "api-spec",
        "endpoint": "api-spec",
        "openapi": "api-spec",
        "rest": "api-spec",
        "graphql": "api-spec",
        "code": "code-gen",
        "implementation": "code-gen",
        "function": "code-gen",
        "class": "code-gen",
        "docs": "docs",
        "readme": "docs",
        "documentation": "docs",
        "config": "config",
        "settings": "config",
        "configuration": "config",
        "database": "database",
        "db": "database",
        "sql": "database",
        "schema": "database",
        "migration": "database",
        "frontend": "frontend",
        "ui": "frontend",
        "react": "frontend",
        "vue": "frontend",
        "angular": "frontend",
        "component": "frontend",
        "backend": "backend",
        "service": "backend",
        "controller": "backend",
        "middleware": "backend",
        "infrastructure": "infrastructure",
        "devops": "infrastructure",
        "docker": "infrastructure",
        "kubernetes": "infrastructure",
        "deploy": "infrastructure",
        "test": "testing",
        "testing": "testing",
        "unit": "testing",
        "integration": "testing",
        "e2e": "testing",
        "security": "security",
        "auth": "security",
        "authentication": "security",
        "authorization": "security",
        "performance": "performance",
        "optimization": "performance",
        "cache": "performance",
        "scalability": "performance",
        "ux": "ui-ux",
        "accessibility": "ui-ux",
        "responsive": "ui-ux",
        "design": "ui-ux",
        "live": "live-test",
        "physical": "live-test",
        "runtime": "live-test",
        "smoke": "live-test",
        "real-test": "live-test",
        "e2e-run": "live-test",
    }

    def __init__(self, criteria_root: Optional[Path] = None):
        """Initialize rule manager

        Args:
            criteria_root: Root directory for user-defined criteria templates
                          (default: .speckit/criteria/ in current project)
        """
        if criteria_root is None:
            # Use current working directory for project-specific criteria
            project_dir = Path.cwd()
            criteria_root = project_dir / ".speckit" / "criteria"

        self.criteria_root = Path(criteria_root)
        self.criteria_root.mkdir(parents=True, exist_ok=True)

    def _get_template_path(self, name: str) -> Optional[Path]:
        """Get path to criteria template

        Args:
            name: Template name (e.g., "code-gen")

        Returns:
            Path to template file, or None if not found
        """
        # Check user override first
        user_path = self.criteria_root / f"{name}.yml"
        if user_path.exists():
            return user_path

        # Fallback to built-in
        builtin_path = self.BUILTIN_CRITERIA_DIR / f"{name}.yml"
        if builtin_path.exists():
            return builtin_path

        return None

    def load_criteria(self, name: str) -> CriteriaTemplate:
        """Load criteria template by name

        Args:
            name: Template name (e.g., "code-gen", "api-spec")

        Returns:
            CriteriaTemplate object

        Raises:
            CriteriaNotFound: If template not found
        """
        path = self._get_template_path(name)

        if path is None:
            available = self.list_criteria()
            raise CriteriaNotFound(name, available)

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return CriteriaTemplate.from_dict(data)

    def load_merged_criteria(self, criteria_spec: str) -> CriteriaTemplate:
        """Load one or more criteria templates, merging rules if multiple specified.

        Accepts comma-separated names: "backend,security,live-test"
        Rules are merged with deduplication by rule id (last wins).

        Args:
            criteria_spec: Single name or comma-separated names

        Returns:
            CriteriaTemplate (merged if multiple)

        Raises:
            CriteriaNotFound: If any template not found
            InvalidCriteriaSpec: If spec is empty
        """
        names = [n.strip() for n in criteria_spec.split(",") if n.strip()]

        if not names:
            raise InvalidCriteriaSpec("Criteria spec is empty")

        if len(names) == 1:
            return self.load_criteria(names[0])

        # Load all templates
        templates = [self.load_criteria(name) for name in names]

        # Merge: use first template as base, add rules from others
        merged_rules: dict = {}  # rule_id -> QualityRule (last wins)
        for tpl in templates:
            for rule in tpl.rules:
                merged_rules[rule.id] = rule

        # Use the strictest thresholds across all templates
        threshold_a = max(
            tpl.phases.get("a", PhaseConfig(threshold=0.8)).threshold
            for tpl in templates
        )
        threshold_b = max(
            tpl.phases.get("b", PhaseConfig(threshold=0.9)).threshold
            for tpl in templates
        )

        merged_name = " + ".join(tpl.name for tpl in templates)
        merged_desc = f"Merged criteria: {', '.join(names)}"

        return CriteriaTemplate(
            name=merged_name,
            version=1.0,
            description=merged_desc,
            phases={
                "a": PhaseConfig(threshold=threshold_a, active_levels=["A"]),
                "b": PhaseConfig(threshold=threshold_b, active_levels=["A", "B"]),
            },
            rules=list(merged_rules.values()),
        )

    def list_criteria(self) -> List[str]:
        """List available criteria templates

        Returns:
            List of template names
        """
        names = set()

        # Add built-in templates
        if self.BUILTIN_CRITERIA_DIR.exists():
            for file in self.BUILTIN_CRITERIA_DIR.glob("*.yml"):
                names.add(file.stem)

        # Add user-defined templates (override built-in)
        if self.criteria_root.exists():
            for file in self.criteria_root.glob("*.yml"):
                names.add(file.stem)

        return sorted(list(names))

    def get_rules_for_phase(
        self,
        criteria: CriteriaTemplate,
        phase: Phase
    ) -> List[QualityRule]:
        """Get active rules for a phase

        Args:
            criteria: Criteria template
            phase: "A" or "B"

        Returns:
            List of rules active in this phase
        """
        return criteria.get_active_rules(phase)

    def auto_detect_criteria(self, task_description: str) -> str:
        """Auto-detect criteria template from task description

        Args:
            task_description: Task description text

        Returns:
            Criteria template name
        """
        if not task_description:
            return "code-gen"  # Default

        words = task_description.lower().split()

        for word in words:
            # Clean word from punctuation
            clean_word = word.strip(",.!?;:'\"()[]{}")

            if clean_word in self.AUTO_DETECT_MAPPING:
                return self.AUTO_DETECT_MAPPING[clean_word]

        return "code-gen"  # Default
