"""
Quality Loop Configuration Persistence (Exp 65)

Allows saving and loading quality loop configurations for consistent,
repeatable quality checks across runs and teams.

Key features:
- Save configurations with name, description, and all loop parameters
- Load configurations by name
- List available configurations
- Validate configurations
- Export/import configurations for team sharing
- Preset configurations for common scenarios
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import json

from rich.console import Console

console = Console()
import yaml


@dataclass
class LoopConfig:
    """Configuration for a quality loop run"""
    name: str
    description: str

    # Exp 127: Project type for automatic template recommendations
    project_type: Optional[str] = None  # e.g., web-app, microservice, ml-service

    # Core parameters
    criteria: List[str] = field(default_factory=list)  # Multiple criteria supported
    max_iterations: int = 4
    threshold_a: float = 0.8
    threshold_b: float = 0.9

    # Exp 127: Template integration settings
    auto_expand_templates: bool = True  # Auto-include template dependencies
    validate_templates: bool = True  # Validate template compatibility

    # Priority and cascade settings
    priority_profile: Optional[str] = None
    cascade_strategy: Optional[str] = None  # avg, max, min, wgt

    # Quality modes
    strict_mode: bool = False
    lenient_mode: bool = False

    # Output formats
    html_output: Optional[str] = None
    markdown_output: Optional[str] = None
    json_output: Optional[str] = None

    # Category filtering
    include_categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None

    # Gate policies
    gate_preset: Optional[str] = None
    gate_policy: Optional[str] = None
    gate_policy_auto: bool = False
    gate_goal_mode: Optional[str] = None
    auto_update_goals: bool = False

    # Exp 78: Goal suggestion settings
    suggest_goals: bool = False
    auto_apply_goals: bool = False
    goal_suggestion_strategy: Optional[str] = None  # optimistic, conservative, balanced, maintenance

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Handle None values for lists
        if self.include_categories is None:
            data["include_categories"] = []
        if self.exclude_categories is None:
            data["exclude_categories"] = []
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopConfig":
        """Create from dictionary"""
        # Handle list conversion
        include_categories = data.get("include_categories")
        if include_categories is not None and len(include_categories) == 0:
            include_categories = None

        exclude_categories = data.get("exclude_categories")
        if exclude_categories is not None and len(exclude_categories) == 0:
            exclude_categories = None

        return cls(
            name=data["name"],
            description=data["description"],
            # Exp 127: Project type for template recommendations
            project_type=data.get("project_type"),
            criteria=data.get("criteria", []),
            max_iterations=data.get("max_iterations", 4),
            threshold_a=data.get("threshold_a", 0.8),
            threshold_b=data.get("threshold_b", 0.9),
            # Exp 127: Template integration settings
            auto_expand_templates=data.get("auto_expand_templates", True),
            validate_templates=data.get("validate_templates", True),
            priority_profile=data.get("priority_profile"),
            cascade_strategy=data.get("cascade_strategy"),
            strict_mode=data.get("strict_mode", False),
            lenient_mode=data.get("lenient_mode", False),
            html_output=data.get("html_output"),
            markdown_output=data.get("markdown_output"),
            json_output=data.get("json_output"),
            include_categories=include_categories,
            exclude_categories=exclude_categories,
            gate_preset=data.get("gate_preset"),
            gate_policy=data.get("gate_policy"),
            gate_policy_auto=data.get("gate_policy_auto", False),
            gate_goal_mode=data.get("gate_goal_mode"),
            auto_update_goals=data.get("auto_update_goals", False),
            # Exp 78: Goal suggestion settings
            suggest_goals=data.get("suggest_goals", False),
            auto_apply_goals=data.get("auto_apply_goals", False),
            goal_suggestion_strategy=data.get("goal_suggestion_strategy"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            author=data.get("author"),
            tags=data.get("tags", []),
        )

    def validate(self) -> List[str]:
        """Validate configuration, return list of errors (empty if valid)"""
        errors = []

        if not self.name:
            errors.append("Configuration name is required")

        if not self.description:
            errors.append("Description is required")

        if self.max_iterations < 1 or self.max_iterations > 20:
            errors.append("max_iterations must be between 1 and 20")

        if self.threshold_a < 0 or self.threshold_a > 1:
            errors.append("threshold_a must be between 0 and 1")

        if self.threshold_b < 0 or self.threshold_b > 1:
            errors.append("threshold_b must be between 0 and 1")

        if self.threshold_a >= self.threshold_b:
            errors.append("threshold_a must be less than threshold_b")

        if self.strict_mode and self.lenient_mode:
            errors.append("Cannot enable both strict_mode and lenient_mode")

        if self.include_categories and self.exclude_categories:
            errors.append("Cannot specify both include_categories and exclude_categories")

        if self.gate_preset and self.gate_policy:
            errors.append("Cannot specify both gate_preset and gate_policy")

        # Validate cascade strategy
        if self.cascade_strategy:
            valid_strategies = {"avg", "mean", "bal", "max", "strict", "min", "lenient", "wgt", "weighted", "custom"}
            if self.cascade_strategy not in valid_strategies:
                errors.append(f"Invalid cascade_strategy: {self.cascade_strategy}. Must be one of {valid_strategies}")

        # Validate gate goal mode
        if self.gate_goal_mode:
            valid_modes = {"strict", "moderate", "lenient", "conservative", "balanced"}
            if self.gate_goal_mode not in valid_modes:
                errors.append(f"Invalid gate_goal_mode: {self.gate_goal_mode}. Must be one of {valid_modes}")

        # Exp 78: Validate goal suggestion strategy
        if self.goal_suggestion_strategy:
            valid_strategies = {"optimistic", "conservative", "balanced", "maintenance", "stabilizing", "catch-up"}
            if self.goal_suggestion_strategy not in valid_strategies:
                errors.append(f"Invalid goal_suggestion_strategy: {self.goal_suggestion_strategy}. Must be one of {valid_strategies}")

        # Validate auto_apply_goals requires suggest_goals
        if self.auto_apply_goals and not self.suggest_goals:
            errors.append("auto_apply_goals requires suggest_goals to be enabled")

        return errors

    def to_command_args(self) -> List[str]:
        """Convert configuration to command line arguments"""
        args = []

        # Exp 127: Project type (takes precedence over criteria for recommendations)
        if self.project_type:
            args.extend(["--project-type", self.project_type])

        # Criteria
        if self.criteria:
            args.extend(["--criteria", ",".join(self.criteria)])

        # Exp 127: Template integration options
        if not self.auto_expand_templates:
            args.append("--no-expand-templates")
        if not self.validate_templates:
            args.append("--no-validate-templates")

        # Iterations and thresholds
        if self.max_iterations != 4:
            args.extend(["--max-iterations", str(self.max_iterations)])
        if self.threshold_a != 0.8:
            args.extend(["--threshold-a", str(self.threshold_a)])
        if self.threshold_b != 0.9:
            args.extend(["--threshold-b", str(self.threshold_b)])

        # Priority profile
        if self.priority_profile:
            args.extend(["--priority-profile", self.priority_profile])
        if self.cascade_strategy:
            args.extend(["--strategy", self.cascade_strategy])

        # Quality modes
        if self.strict_mode:
            args.append("--strict")
        if self.lenient_mode:
            args.append("--lenient")

        # Output formats
        if self.html_output:
            args.extend(["--html-output", self.html_output])
        if self.markdown_output:
            args.extend(["--markdown-output", self.markdown_output])
        if self.json_output:
            args.extend(["--json-output", self.json_output])

        # Category filtering
        if self.include_categories:
            args.extend(["--include-categories", ",".join(self.include_categories)])
        if self.exclude_categories:
            args.extend(["--exclude-categories", ",".join(self.exclude_categories)])

        # Gate policies
        if self.gate_preset:
            args.extend(["--gate-preset", self.gate_preset])
        if self.gate_policy:
            args.extend(["--gate-policy", self.gate_policy])
        if self.gate_policy_auto:
            args.append("--gate-policy-auto")
        if self.gate_goal_mode:
            args.extend(["--gate-goal-mode", self.gate_goal_mode])
        if self.auto_update_goals:
            args.append("--auto-update-goals")

        # Exp 78: Goal suggestion settings
        if self.suggest_goals:
            args.append("--suggest-goals")
        if self.auto_apply_goals:
            args.append("--auto-apply-goals")
        if self.goal_suggestion_strategy:
            args.extend(["--goal-strategy", self.goal_suggestion_strategy])

        return args


# Preset configurations for common scenarios

LOOP_CONFIG_PRESETS: Dict[str, LoopConfig] = {
    "production-strict": LoopConfig(
        name="production-strict",
        description="Strict quality checks for production deployment with comprehensive reporting",
        criteria=["backend", "security", "performance", "testing"],
        max_iterations=6,
        threshold_a=0.85,
        threshold_b=0.95,
        priority_profile="web-app+mobile-app",
        cascade_strategy="max",
        strict_mode=True,
        lenient_mode=False,
        html_output=".speckit/quality-report.html",
        markdown_output=".speckit/quality-report.md",
        json_output=".speckit/quality-report.json",
        gate_preset="production",
        tags=["production", "strict", "comprehensive"],
    ),
    "ci-standard": LoopConfig(
        name="ci-standard",
        description="Standard CI/CD quality gate with JSON output for automation",
        criteria=["backend", "testing"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="web-app",
        json_output=".speckit/quality-report.json",
        gate_preset="ci",
        tags=["ci", "automation", "standard"],
    ),
    "development-quick": LoopConfig(
        name="development-quick",
        description="Quick quality check for development iterations",
        criteria=["backend"],
        max_iterations=2,
        threshold_a=0.7,
        threshold_b=0.8,
        priority_profile="default",
        lenient_mode=True,
        gate_preset="development",
        tags=["development", "quick", "lenient"],
    ),
    "security-focused": LoopConfig(
        name="security-focused",
        description="Security-focused quality checks with high severity thresholds",
        criteria=["backend", "security"],
        max_iterations=5,
        threshold_a=0.85,
        threshold_b=0.9,
        priority_profile="microservice",
        cascade_strategy="max",
        gate_preset="strict",
        tags=["security", "strict", "backend"],
    ),
    "frontend-qa": LoopConfig(
        name="frontend-qa",
        description="Comprehensive frontend quality assurance",
        criteria=["frontend", "ui-ux", "performance"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="web-app",
        html_output=".speckit/frontend-report.html",
        markdown_output=".speckit/frontend-report.md",
        gate_preset="staging",
        tags=["frontend", "ui", "ux"],
    ),
    "fullstack-comprehensive": LoopConfig(
        name="fullstack-comprehensive",
        description="Comprehensive quality check for full-stack applications",
        criteria=["backend", "frontend", "security", "performance", "testing"],
        max_iterations=6,
        threshold_a=0.85,
        threshold_b=0.92,
        priority_profile="web-app+mobile-app",
        cascade_strategy="max",
        html_output=".speckit/fullstack-report.html",
        markdown_output=".speckit/fullstack-report.md",
        json_output=".speckit/fullstack-report.json",
        gate_preset="production",
        tags=["fullstack", "comprehensive", "production"],
    ),
    "api-focused": LoopConfig(
        name="api-focused",
        description="Quality checks focused on API correctness and security",
        criteria=["api-spec", "backend", "security"],
        max_iterations=4,
        threshold_a=0.85,
        threshold_b=0.9,
        priority_profile="graphql-api",
        html_output=".speckit/api-report.html",
        json_output=".speckit/api-report.json",
        gate_preset="staging",
        tags=["api", "backend", "security"],
    ),
    "mobile-app-qa": LoopConfig(
        name="mobile-app-qa",
        description="Quality assurance for mobile applications",
        criteria=["mobile", "frontend", "performance"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="mobile-app",
        html_output=".speckit/mobile-report.html",
        markdown_output=".speckit/mobile-report.md",
        gate_preset="staging",
        tags=["mobile", "ios", "android"],
    ),
    "data-pipeline": LoopConfig(
        name="data-pipeline",
        description="Quality checks for data processing pipelines",
        criteria=["backend", "performance", "testing"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="data-pipeline",
        json_output=".speckit/pipeline-report.json",
        gate_preset="ci",
        tags=["data", "pipeline", "performance"],
    ),
    "ml-service": LoopConfig(
        name="ml-service",
        description="Quality checks for ML/AI services",
        criteria=["backend", "api-spec", "performance"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="ml-service",
        html_output=".speckit/ml-report.html",
        json_output=".speckit/ml-report.json",
        gate_preset="staging",
        tags=["ml", "ai", "service"],
    ),
    # Exp 78: Goal-Aware Presets
    "goal-driven-development": LoopConfig(
        name="goal-driven-development",
        description="Quality loop with automatic goal suggestions and application for continuous improvement",
        criteria=["backend", "security", "performance", "testing"],
        max_iterations=5,
        threshold_a=0.82,
        threshold_b=0.9,
        priority_profile="web-app",
        html_output=".speckit/quality-report.html",
        json_output=".speckit/quality-report.json",
        gate_preset="staging",
        suggest_goals=True,
        auto_apply_goals=True,
        goal_suggestion_strategy="balanced",
        tags=["goals", "continuous-improvement", "automation"],
    ),
    "quality-improvement-focus": LoopConfig(
        name="quality-improvement-focus",
        description="Focus on quality improvement with conservative goal suggestions for steady progress",
        criteria=["backend", "frontend", "testing"],
        max_iterations=6,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="web-app",
        html_output=".speckit/improvement-report.html",
        markdown_output=".speckit/improvement-report.md",
        gate_preset="production",
        suggest_goals=True,
        auto_apply_goals=False,
        goal_suggestion_strategy="conservative",
        tags=["goals", "improvement", "conservative"],
    ),
    "aggressive-quality-targets": LoopConfig(
        name="aggressive-quality-targets",
        description="Ambitious quality targets with optimistic goal suggestions for rapid improvement",
        criteria=["backend", "security", "performance", "testing", "docs"],
        max_iterations=6,
        threshold_a=0.85,
        threshold_b=0.95,
        priority_profile="web-app+mobile-app",
        cascade_strategy="max",
        strict_mode=True,
        html_output=".speckit/aggressive-report.html",
        json_output=".speckit/aggressive-report.json",
        gate_preset="production",
        suggest_goals=True,
        auto_apply_goals=True,
        goal_suggestion_strategy="optimistic",
        tags=["goals", "aggressive", "optimistic"],
    ),
    "stability-focused": LoopConfig(
        name="stability-focused",
        description="Maintain quality stability with stabilizing goal suggestions",
        criteria=["backend", "testing"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="default",
        json_output=".speckit/stability-report.json",
        gate_preset="ci",
        suggest_goals=True,
        auto_apply_goals=False,
        goal_suggestion_strategy="stabilizing",
        tags=["goals", "stability", "maintenance"],
    ),
    "goal-aware-ci": LoopConfig(
        name="goal-aware-ci",
        description="CI/CD pipeline with goal tracking and automatic goal suggestions",
        criteria=["backend", "testing", "security"],
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="web-app",
        json_output=".speckit/ci-report.json",
        gate_preset="ci",
        gate_goal_mode="balanced",
        suggest_goals=True,
        auto_apply_goals=False,
        goal_suggestion_strategy="maintenance",
        tags=["goals", "ci", "automation"],
    ),
    # Exp 127: Project-type-based presets
    "smart-web-app": LoopConfig(
        name="smart-web-app",
        description="Automatic template selection for web applications based on project type",
        project_type="web-app",
        criteria=[],  # Auto-populated from template registry
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="web-app",
        html_output=".speckit/quality-report.html",
        json_output=".speckit/quality-report.json",
        gate_preset="staging",
        auto_expand_templates=True,
        validate_templates=True,
        tags=["smart", "web-app", "auto-templates"],
    ),
    "smart-microservice": LoopConfig(
        name="smart-microservice",
        description="Automatic template selection for microservices based on project type",
        project_type="microservice",
        criteria=[],  # Auto-populated from template registry
        max_iterations=5,
        threshold_a=0.85,
        threshold_b=0.9,
        priority_profile="microservice",
        cascade_strategy="max",
        html_output=".speckit/quality-report.html",
        json_output=".speckit/quality-report.json",
        gate_preset="staging",
        auto_expand_templates=True,
        validate_templates=True,
        tags=["smart", "microservice", "auto-templates"],
    ),
    "smart-ml-service": LoopConfig(
        name="smart-ml-service",
        description="Automatic template selection for ML/AI services based on project type",
        project_type="ml-service",
        criteria=[],  # Auto-populated from template registry
        max_iterations=4,
        threshold_a=0.8,
        threshold_b=0.9,
        priority_profile="ml-service",
        html_output=".speckit/quality-report.html",
        json_output=".speckit/quality-report.json",
        gate_preset="staging",
        auto_expand_templates=True,
        validate_templates=True,
        tags=["smart", "ml", "ai", "auto-templates"],
    ),
}


class LoopConfigManager:
    """Manages quality loop configurations"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager

        Args:
            config_dir: Directory to store configurations (default: .speckit/loop-configs)
        """
        if config_dir is None:
            config_dir = Path.cwd() / ".speckit" / "loop-configs"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Index file for all configurations
        self.index_file = self.config_dir / "index.json"

    def save(self, config: LoopConfig) -> str:
        """Save a configuration

        Args:
            config: LoopConfig to save

        Returns:
            Path to saved file
        """
        # Update timestamp
        config.updated_at = datetime.now().isoformat()

        # Save individual config file
        config_file = self.config_dir / f"{config.name}.yml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

        # Update index
        self._update_index(config)

        return str(config_file)

    def load(self, name: str) -> Optional[LoopConfig]:
        """Load a configuration by name

        Args:
            name: Configuration name

        Returns:
            LoopConfig or None if not found
        """
        # Check presets first
        if name in LOOP_CONFIG_PRESETS:
            return LOOP_CONFIG_PRESETS[name]

        # Check custom configs
        config_file = self.config_dir / f"{name}.yml"
        if not config_file.exists():
            return None

        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return LoopConfig.from_dict(data)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all available configurations

        Returns:
            List of config summaries
        """
        configs = []

        # Add presets
        for name, config in LOOP_CONFIG_PRESETS.items():
            configs.append({
                "name": name,
                "description": config.description,
                "is_preset": True,
                "tags": config.tags,
                "criteria": config.criteria,
            })

        # Add custom configs
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)

            for name, data in index_data.get("configs", {}).items():
                # Check if file still exists
                config_file = self.config_dir / f"{name}.yml"
                if config_file.exists():
                    configs.append({
                        "name": name,
                        "description": data.get("description", ""),
                        "is_preset": False,
                        "tags": data.get("tags", []),
                        "criteria": data.get("criteria", []),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "author": data.get("author"),
                    })

        return configs

    def delete(self, name: str) -> bool:
        """Delete a configuration

        Args:
            name: Configuration name

        Returns:
            True if deleted, False if not found or is preset
        """
        # Cannot delete presets
        if name in LOOP_CONFIG_PRESETS:
            return False

        config_file = self.config_dir / f"{name}.yml"
        if not config_file.exists():
            return False

        config_file.unlink()

        # Update index
        self._remove_from_index(name)

        return True

    def export(self, name: str, output_path: Path) -> bool:
        """Export a configuration to a file for sharing

        Args:
            name: Configuration name
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        config = self.load(name)
        if config is None:
            return False

        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

        return True

    def import_config(self, config_path: Path, new_name: Optional[str] = None) -> Optional[LoopConfig]:
        """Import a configuration from a file

        Args:
            config_path: Path to config file
            new_name: Optional new name for the config

        Returns:
            Imported LoopConfig or None if failed
        """
        config_path = Path(config_path)
        if not config_path.exists():
            return None

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        config = LoopConfig.from_dict(data)

        if new_name:
            config.name = new_name

        # Validate
        errors = config.validate()
        if errors:
            return None

        self.save(config)
        return config

    def _update_index(self, config: LoopConfig):
        """Update the configuration index"""
        index_data = {}
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)

        if "configs" not in index_data:
            index_data["configs"] = {}

        index_data["configs"][config.name] = {
            "description": config.description,
            "tags": config.tags,
            "criteria": config.criteria,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "author": config.author,
        }

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

    def _remove_from_index(self, name: str):
        """Remove a configuration from the index"""
        if not self.index_file.exists():
            return

        with open(self.index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        if "configs" in index_data and name in index_data["configs"]:
            del index_data["configs"][name]

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)


# Convenience functions

def save_loop_config(
    name: str,
    description: str,
    project_type: Optional[str] = None,  # Exp 127: Project type for template recommendations
    criteria: Optional[List[str]] = None,
    max_iterations: int = 4,
    threshold_a: float = 0.8,
    threshold_b: float = 0.9,
    priority_profile: Optional[str] = None,
    # Exp 127: Template integration settings
    auto_expand_templates: bool = True,
    validate_templates: bool = True,
    cascade_strategy: Optional[str] = None,
    strict_mode: bool = False,
    lenient_mode: bool = False,
    html_output: Optional[str] = None,
    markdown_output: Optional[str] = None,
    json_output: Optional[str] = None,
    include_categories: Optional[List[str]] = None,
    exclude_categories: Optional[List[str]] = None,
    gate_preset: Optional[str] = None,
    gate_policy: Optional[str] = None,
    gate_policy_auto: bool = False,
    gate_goal_mode: Optional[str] = None,
    auto_update_goals: bool = False,
    # Exp 78: Goal suggestion settings
    suggest_goals: bool = False,
    auto_apply_goals: bool = False,
    goal_suggestion_strategy: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    config_dir: Optional[Path] = None,
) -> Optional[LoopConfig]:
    """Save a loop configuration

    Args:
        name: Configuration name
        description: Configuration description
        ... (other parameters)

    Returns:
        Saved LoopConfig or None if validation failed
    """
    config = LoopConfig(
        name=name,
        description=description,
        # Exp 127: Project type for template recommendations
        project_type=project_type,
        criteria=criteria or [],
        max_iterations=max_iterations,
        threshold_a=threshold_a,
        threshold_b=threshold_b,
        # Exp 127: Template integration settings
        auto_expand_templates=auto_expand_templates,
        validate_templates=validate_templates,
        priority_profile=priority_profile,
        cascade_strategy=cascade_strategy,
        strict_mode=strict_mode,
        lenient_mode=lenient_mode,
        html_output=html_output,
        markdown_output=markdown_output,
        json_output=json_output,
        include_categories=include_categories,
        exclude_categories=exclude_categories,
        gate_preset=gate_preset,
        gate_policy=gate_policy,
        gate_policy_auto=gate_policy_auto,
        gate_goal_mode=gate_goal_mode,
        auto_update_goals=auto_update_goals,
        # Exp 78: Goal suggestion settings
        suggest_goals=suggest_goals,
        auto_apply_goals=auto_apply_goals,
        goal_suggestion_strategy=goal_suggestion_strategy,
        author=author,
        tags=tags or [],
    )

    # Validate
    errors = config.validate()
    if errors:
        return None

    manager = LoopConfigManager(config_dir=config_dir)
    manager.save(config)
    return config


def load_loop_config(name: str, config_dir: Optional[Path] = None) -> Optional[LoopConfig]:
    """Load a loop configuration by name

    Args:
        name: Configuration name
        config_dir: Optional custom config directory

    Returns:
        LoopConfig or None if not found
    """
    manager = LoopConfigManager(config_dir=config_dir)
    return manager.load(name)


def list_loop_configs(config_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List all available loop configurations

    Args:
        config_dir: Optional custom config directory

    Returns:
        List of configuration summaries
    """
    manager = LoopConfigManager(config_dir=config_dir)
    return manager.list_all()


def delete_loop_config(name: str, config_dir: Optional[Path] = None) -> bool:
    """Delete a loop configuration

    Args:
        name: Configuration name
        config_dir: Optional custom config directory

    Returns:
        True if deleted, False otherwise
    """
    manager = LoopConfigManager(config_dir=config_dir)
    return manager.delete(name)


def format_config_summary(configs: List[Dict[str, Any]]) -> str:
    """Format configuration list for display

    Args:
        configs: List of configuration summaries

    Returns:
        Formatted string
    """
    lines = []
    lines.append("## Loop Configurations")
    lines.append("")

    presets = [c for c in configs if c.get("is_preset")]
    custom = [c for c in configs if not c.get("is_preset")]

    if presets:
        lines.append("### Presets")
        lines.append("")
        for config in presets:
            preset_indicator = "🔹" if config.get("is_preset") else ""
            tags_str = " ".join(f"`{tag}`" for tag in config.get("tags", []))
            criteria_str = ", ".join(config.get("criteria", []))

            lines.append(f"{preset_indicator} **{config['name']}**")
            lines.append(f"   {config['description']}")
            if criteria_str:
                lines.append(f"   Criteria: {criteria_str}")
            if tags_str:
                lines.append(f"   Tags: {tags_str}")
            lines.append("")

    if custom:
        lines.append("### Custom Configurations")
        lines.append("")
        for config in custom:
            tags_str = " ".join(f"`{tag}`" for tag in config.get("tags", []))
            criteria_str = ", ".join(config.get("criteria", []))
            author = config.get("author", "Unknown")
            updated = config.get("updated_at", "Unknown")

            lines.append(f"**{config['name']}** (by {author}, updated {updated})")
            lines.append(f"   {config['description']}")
            if criteria_str:
                lines.append(f"   Criteria: {criteria_str}")
            if tags_str:
                lines.append(f"   Tags: {tags_str}")
            lines.append("")

    if not presets and not custom:
        lines.append("No configurations found.")

    return "\n".join(lines)


def format_config_details(config: LoopConfig) -> str:
    """Format configuration details for display

    Args:
        config: LoopConfig to format

    Returns:
        Formatted string
    """
    lines = []
    lines.append(f"## Configuration: {config.name}")
    lines.append("")
    lines.append(f"**Description:** {config.description}")
    lines.append("")

    lines.append("### Core Parameters")
    # Exp 127: Show project type if set
    if config.project_type:
        lines.append(f"- **Project Type:** {config.project_type}")
    lines.append(f"- **Criteria:** {', '.join(config.criteria) or 'auto-detect'}")
    lines.append(f"- **Max Iterations:** {config.max_iterations}")
    lines.append(f"- **Threshold A:** {config.threshold_a}")
    lines.append(f"- **Threshold B:** {config.threshold_b}")
    lines.append("")

    if config.priority_profile:
        lines.append("### Priority Profile")
        lines.append(f"- **Profile:** {config.priority_profile}")
        if config.cascade_strategy:
            lines.append(f"- **Strategy:** {config.cascade_strategy}")
        lines.append("")

    if config.strict_mode or config.lenient_mode:
        lines.append("### Quality Mode")
        if config.strict_mode:
            lines.append("- **Strict Mode:** Enabled")
        if config.lenient_mode:
            lines.append("- **Lenient Mode:** Enabled")
        lines.append("")

    outputs = []
    if config.html_output:
        outputs.append(f"HTML: {config.html_output}")
    if config.markdown_output:
        outputs.append(f"Markdown: {config.markdown_output}")
    if config.json_output:
        outputs.append(f"JSON: {config.json_output}")

    if outputs:
        lines.append("### Output Formats")
        for output in outputs:
            lines.append(f"- {output}")
        lines.append("")

    if config.include_categories or config.exclude_categories:
        lines.append("### Category Filtering")
        if config.include_categories:
            lines.append(f"- **Include:** {', '.join(config.include_categories)}")
        if config.exclude_categories:
            lines.append(f"- **Exclude:** {', '.join(config.exclude_categories)}")
        lines.append("")

    # Exp 127: Template integration settings
    if not config.auto_expand_templates or not config.validate_templates:
        lines.append("### Template Integration")
        if not config.auto_expand_templates:
            lines.append("- **Auto-Expand Templates:** Disabled")
        if not config.validate_templates:
            lines.append("- **Validate Templates:** Disabled")
        lines.append("")

    if config.gate_preset or config.gate_policy or config.gate_policy_auto:
        lines.append("### Gate Policy")
        if config.gate_preset:
            lines.append(f"- **Preset:** {config.gate_preset}")
        if config.gate_policy:
            lines.append(f"- **Policy:** {config.gate_policy}")
        if config.gate_policy_auto:
            lines.append(f"- **Auto:** Enabled")
        if config.gate_goal_mode:
            lines.append(f"- **Goal Mode:** {config.gate_goal_mode}")
        if config.auto_update_goals:
            lines.append(f"- **Auto Update Goals:** Enabled")
        lines.append("")

    # Exp 78: Goal suggestion settings
    if config.suggest_goals or config.auto_apply_goals or config.goal_suggestion_strategy:
        lines.append("### Goal Suggestions")
        if config.suggest_goals:
            lines.append(f"- **Suggest Goals:** Enabled")
        if config.auto_apply_goals:
            lines.append(f"- **Auto Apply Goals:** Enabled")
        if config.goal_suggestion_strategy:
            lines.append(f"- **Strategy:** {config.goal_suggestion_strategy}")
        lines.append("")

    if config.tags:
        lines.append(f"**Tags:** {', '.join(config.tags)})")
        lines.append("")

    lines.append("### Command Equivalent")
    args = config.to_command_args()
    if args:
        cmd_args = " ".join(args)
        lines.append(f"```bash")
        lines.append(f"/speckit.loop {cmd_args}")
        lines.append(f"```")
    else:
        lines.append("```bash")
        lines.append(f"/speckit.loop")
        lines.append(f"```")

    return "\n".join(lines)


def recommend_config(
    task_description: str,
    config_dir: Optional[Path] = None,
) -> Optional[LoopConfig]:
    """Recommend a configuration based on task description

    Args:
        task_description: Description of the task
        config_dir: Optional custom config directory

    Returns:
        Recommended LoopConfig or None
    """
    description_lower = task_description.lower()

    # Keyword matching for presets
    keywords_map = {
        "production-strict": ["production", "deploy", "release", "strict", "critical"],
        "ci-standard": ["ci", "cd", "pipeline", "automation", "github actions"],
        "development-quick": ["dev", "quick", "fast", "iteration", "prototype"],
        "security-focused": ["security", "vulnerability", "auth", "injection", "xss"],
        "frontend-qa": ["frontend", "ui", "ux", "react", "vue", "angular", "svelte"],
        "fullstack-comprehensive": ["fullstack", "full-stack", "complete", "comprehensive"],
        "api-focused": ["api", "rest", "graphql", "endpoint", "backend"],
        "mobile-app-qa": ["mobile", "ios", "android", "react native", "flutter"],
        "data-pipeline": ["data", "etl", "pipeline", "batch", "stream"],
        "ml-service": ["ml", "ai", "machine learning", "model", "prediction"],
        # Exp 78: Goal-aware presets
        "goal-driven-development": ["goal", "goals", "improvement", "continuous", "target"],
        "quality-improvement-focus": ["improve", "improvement", "better", "enhance"],
        "aggressive-quality-targets": ["aggressive", "ambitious", "rapid", "fast-track"],
        "stability-focused": ["stable", "stability", "maintain", "consistency"],
        "goal-aware-ci": ["ci goals", "pipeline goals", "automation goals"],
    }

    # Score each preset
    scores = {}
    for preset_name, keywords in keywords_map.items():
        score = sum(1 for keyword in keywords if keyword in description_lower)
        if score > 0:
            scores[preset_name] = score

    if scores:
        # Return highest scoring preset
        best_match = max(scores, key=scores.get)
        return LOOP_CONFIG_PRESETS[best_match]

    # Default fallback
    return LOOP_CONFIG_PRESETS["ci-standard"]


# Exp 127: Template integration helper functions


def resolve_criteria_from_config(
    config: LoopConfig,
    project_path: Optional[Path] = None,
) -> List[str]:
    """
    Resolve the final list of criteria/templates to use from a LoopConfig.

    This function implements the following logic:
    1. If project_type is set and criteria is empty, use template registry recommendations
    2. If criteria is provided, use those (optionally validated and expanded)
    3. If both are empty, auto-detect from codebase

    Args:
        config: LoopConfig to resolve criteria from
        project_path: Optional path to project for auto-detection

    Returns:
        List of template/criteria names to use
    """
    # Import here to avoid circular imports
    try:
        from specify_cli.quality.template_registry import (
            TemplateIntegration,
            get_recommended_templates,
            validate_templates,
            expand_templates,
        )
        _template_integration_available = True
    except ImportError:
        _template_integration_available = False

    # If project_type is set and no explicit criteria, use recommendations
    if config.project_type and not config.criteria:
        if _template_integration_available:
            templates = get_recommended_templates(
                project_type=config.project_type,
                fallback_to_default=True,
            )
            console.print(
                f"[cyan]Using recommended templates for '{config.project_type}': "
                f"{', '.join(templates)}[/cyan]"
            )
            return templates
        else:
            console.print("[yellow]Template integration not available. Using default criteria.[/yellow]")
            return TemplateIntegration.DEFAULT_TEMPLATES

    # If criteria are provided
    if config.criteria:
        final_criteria = config.criteria.copy()

        # Validate if enabled
        if config.validate_templates and _template_integration_available:
            is_valid, valid_templates, warning = validate_templates(final_criteria)
            if warning:
                console.print(f"[yellow]{warning}[/yellow]")
            if not is_valid:
                # Filter out invalid templates
                final_criteria = valid_templates
                if final_criteria:
                    console.print(
                        f"[yellow]Using only valid templates: {', '.join(final_criteria)}[/yellow]"
                    )
                else:
                    console.print("[red]No valid templates found. Using defaults.[/red]")
                    return TemplateIntegration.DEFAULT_TEMPLATES.copy()

        # Expand dependencies if enabled
        if config.auto_expand_templates and _template_integration_available:
            final_criteria = expand_templates(
                templates=final_criteria,
                include_dependencies=True,
            )
            if len(final_criteria) > len(config.criteria):
                added = set(final_criteria) - set(config.criteria)
                console.print(
                    f"[dim]Auto-added dependencies: {', '.join(added)}[/dim]"
                )

        return final_criteria

    # If both are empty, try auto-detection from codebase
    if _template_integration_available:
        suggested = TemplateIntegration.suggest_from_codebase(project_path)
        if suggested:
            console.print(
                f"[cyan]Auto-detected templates from codebase: {', '.join(suggested)}[/cyan]"
            )
            return suggested

    # Final fallback
    return ["backend", "security", "testing"]


def get_available_project_types() -> List[str]:
    """
    Get list of available project types for template recommendations.

    Returns:
        List of project type names
    """
    try:
        from specify_cli.quality.template_registry import TemplateIntegration
        return sorted(TemplateIntegration.PROJECT_TYPE_ALIASES.values())
    except ImportError:
        return [
            "web-app", "microservice", "ml-service", "mobile-app",
            "serverless", "graphql-api", "desktop", "infrastructure",
        ]
