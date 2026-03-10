"""
Rule Manager

Manages quality rules and criteria templates.
Loads built-in and user-defined criteria templates.
"""

import yaml
from pathlib import Path
from typing import List, Optional

from specify_cli.quality.models import CriteriaTemplate, QualityRule, Phase


class CriteriaNotFound(Exception):
    """Raised when criteria template is not found"""
    def __init__(self, name: str, available: List[str]):
        self.name = name
        self.available = available
        super().__init__(
            f"Criteria template '{name}' not found. "
            f"Available: {', '.join(available)}"
        )


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
