"""
Quality Plans (Exp 79)

Unified quality improvement plans that combine loop configurations,
quality goals, gate policies, and priority profiles into a single,
cohesive improvement strategy.

Key features:
- Pre-configured quality plan presets for common scenarios
- Custom quality plans for project-specific needs
- Plan validation and recommendation
- Integration with loop, goals, gates, and profiles
- Plan export/import for team sharing
- Plan comparison and diff visualization
- Interactive wizard for custom plan creation (Exp 80)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple, Callable
from enum import Enum
import json
import yaml

from .loop_config import LoopConfig


# Available categories for quality plans
AVAILABLE_CATEGORIES = [
    "general", "production", "security", "performance",
    "stability", "improvement", "ci_cd"
]

# Available gate presets
AVAILABLE_GATE_PRESETS = [
    "development", "ci", "staging", "production", "strict"
]

# Available priority profiles
AVAILABLE_PRIORITY_PROFILES = [
    "default", "balanced", "web-app", "mobile-app", "api",
    "microservice", "security-first", "performance-focused",
    "quality-first", "criticality-focused"
]

# Available cascade strategies
AVAILABLE_CASCADE_STRATEGIES = [
    "avg", "max", "min", "wgt", "bal"
]

# Quality criteria options
AVAILABLE_CRITERIA = [
    "api-spec", "backend", "code-gen", "config", "database",
    "docs", "frontend", "infrastructure", "live-test",
    "performance", "security", "testing", "ui-ux"
]

# Goal suggestion strategies
AVAILABLE_GOAL_STRATEGIES = [
    "optimistic", "conservative", "balanced", "maintenance"
]


class PlanType(Enum):
    """Type of quality plan"""
    PRESET = "preset"  # Built-in preset
    CUSTOM = "custom"  # User-defined
    TEAM = "team"  # Team-shared plan


class PlanCategory(Enum):
    """Category of quality plan"""
    GENERAL = "general"
    PRODUCTION = "production"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STABILITY = "stability"
    IMPROVEMENT = "improvement"
    CI_CD = "ci_cd"


@dataclass
class QualityPlan:
    """Unified quality improvement plan combining all quality systems"""

    # Basic info
    plan_id: str
    name: str
    description: str
    plan_type: PlanType
    category: PlanCategory

    # Loop configuration
    loop_config: LoopConfig

    # Quality goals (optional, can be empty)
    goals: List[Dict[str, Any]] = field(default_factory=list)

    # Gate policy reference
    gate_preset: Optional[str] = None
    gate_policy: Optional[str] = None

    # Priority profile reference
    priority_profile: Optional[str] = None
    cascade_strategy: Optional[str] = None

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    estimated_duration: Optional[str] = None  # e.g., "2 weeks", "1 sprint"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "plan_type": self.plan_type.value,
            "category": self.category.value,
            "loop_config": self.loop_config.to_dict(),
            "goals": self.goals,
            "gate_preset": self.gate_preset,
            "gate_policy": self.gate_policy,
            "priority_profile": self.priority_profile,
            "cascade_strategy": self.cascade_strategy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "estimated_duration": self.estimated_duration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityPlan":
        """Create from dictionary"""
        loop_config_data = data.get("loop_config", {})
        loop_config = LoopConfig.from_dict(loop_config_data)

        return cls(
            plan_id=data["plan_id"],
            name=data["name"],
            description=data["description"],
            plan_type=PlanType(data.get("plan_type", "custom")),
            category=PlanCategory(data.get("category", "general")),
            loop_config=loop_config,
            goals=data.get("goals", []),
            gate_preset=data.get("gate_preset"),
            gate_policy=data.get("gate_policy"),
            priority_profile=data.get("priority_profile"),
            cascade_strategy=data.get("cascade_strategy"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            author=data.get("author"),
            version=data.get("version", "1.0"),
            tags=data.get("tags", []),
            estimated_duration=data.get("estimated_duration"),
        )

    def validate(self) -> List[str]:
        """Validate quality plan, return list of errors (empty if valid)"""
        errors = []

        if not self.plan_id:
            errors.append("Plan ID is required")

        if not self.name:
            errors.append("Plan name is required")

        if not self.description:
            errors.append("Description is required")

        # Validate loop config
        loop_errors = self.loop_config.validate()
        errors.extend([f"Loop config: {e}" for e in loop_errors])

        # Validate goals
        for i, goal_data in enumerate(self.goals):
            if "name" not in goal_data:
                errors.append(f"Goal {i}: missing 'name'")
            if "target_value" not in goal_data:
                errors.append(f"Goal {i}: missing 'target_value'")

        return errors

    def get_summary(self) -> str:
        """Get a human-readable summary of the plan"""
        lines = [
            f"# {self.name}",
            f"**{self.description}**",
            "",
            "## Configuration",
            f"- **Iterations**: {self.loop_config.max_iterations}",
            f"- **Thresholds**: A={self.loop_config.threshold_a}, B={self.loop_config.threshold_b}",
            f"- **Criteria**: {', '.join(self.loop_config.criteria) if self.loop_config.criteria else 'All'}",
        ]

        if self.priority_profile:
            lines.append(f"- **Priority Profile**: {self.priority_profile}")

        if self.gate_preset:
            lines.append(f"- **Gate Preset**: {self.gate_preset}")

        if self.goals:
            lines.append("")
            lines.append("## Goals")
            for i, goal in enumerate(self.goals, 1):
                target = goal.get("target_value", "N/A")
                lines.append(f"{i}. {goal.get('name', 'Unnamed')} (target: {target})")

        if self.estimated_duration:
            lines.append("")
            lines.append(f"**Estimated Duration**: {self.estimated_duration}")

        return "\n".join(lines)

    def to_yaml(self) -> str:
        """Export to YAML format"""
        data = self.to_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "QualityPlan":
        """Import from YAML format"""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)


class QualityPlanManager:
    """Manager for quality plans"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize manager with optional custom config directory"""
        self.config_dir = config_dir or Path.home() / ".speckit" / "quality" / "plans"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._presets: Optional[Dict[str, QualityPlan]] = None

    @property
    def presets(self) -> Dict[str, QualityPlan]:
        """Get built-in presets (lazy loaded)"""
        if self._presets is None:
            self._presets = self._load_builtin_presets()
        return self._presets

    def _load_builtin_presets(self) -> Dict[str, QualityPlan]:
        """Load built-in preset quality plans"""
        presets = {}

        # 1. Quick Start Plan
        presets["quick-start"] = QualityPlan(
            plan_id="quick-start",
            name="Quick Start",
            description="Basic quality checks for new projects. Get started with quality assurance quickly.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.GENERAL,
            loop_config=LoopConfig(
                name="quick-start-loop",
                description="Quick start quality loop configuration",
                criteria=["backend", "frontend"],
                max_iterations=2,
                threshold_a=0.7,
                threshold_b=0.8,
            ),
            goals=[
                {
                    "name": "Initial Quality Baseline",
                    "description": "Establish initial quality baseline",
                    "goal_type": "target_score",
                    "target_value": 0.75,
                    "category": None,
                }
            ],
            gate_preset="development",
            priority_profile="balanced",
            estimated_duration="1-2 days",
            tags=["beginner", "quick-start", "onboarding"],
        )

        # 2. Production Ready Plan
        presets["production-ready"] = QualityPlan(
            plan_id="production-ready",
            name="Production Ready",
            description="Comprehensive quality checks for production deployment readiness.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.PRODUCTION,
            loop_config=LoopConfig(
                name="production-loop",
                description="Production-ready quality loop configuration",
                criteria=["backend", "frontend", "security", "testing", "performance"],
                max_iterations=5,
                threshold_a=0.85,
                threshold_b=0.9,
                strict_mode=True,
            ),
            goals=[
                {
                    "name": "Production Quality Score",
                    "description": "Achieve production-ready quality score",
                    "goal_type": "target_score",
                    "target_value": 0.9,
                },
                {
                    "name": "Zero Critical Issues",
                    "description": "No critical issues allowed",
                    "goal_type": "target_score",
                    "target_value": 1.0,
                    "category": "security",
                },
                {
                    "name": "High Test Coverage",
                    "description": "Maintain high test coverage",
                    "goal_type": "category_target",
                    "target_value": 0.85,
                    "category": "testing",
                },
            ],
            gate_preset="production",
            priority_profile="criticality-focused",
            estimated_duration="1-2 weeks",
            tags=["production", "comprehensive", "deployment"],
        )

        # 3. Continuous Improvement Plan
        presets["continuous-improvement"] = QualityPlan(
            plan_id="continuous-improvement",
            name="Continuous Improvement",
            description="Ongoing quality enhancement with progressive targets and auto-suggestions.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.IMPROVEMENT,
            loop_config=LoopConfig(
                name="improvement-loop",
                description="Continuous improvement quality loop",
                criteria=["backend", "frontend", "testing", "docs"],
                max_iterations=4,
                threshold_a=0.8,
                threshold_b=0.85,
            ),
            goals=[
                {
                    "name": "Steady Quality Growth",
                    "description": "Consistently improve quality over time",
                    "goal_type": "improvement",
                    "target_value": 0.05,  # 5% improvement
                },
                {
                    "name": "Documentation Coverage",
                    "description": "Improve documentation quality",
                    "goal_type": "category_target",
                    "target_value": 0.8,
                    "category": "docs",
                },
            ],
            gate_preset="staging",
            priority_profile="balanced",
            estimated_duration="Ongoing",
            tags=["continuous", "improvement", "agile"],
        )

        # 4. Security Focus Plan
        presets["security-focus"] = QualityPlan(
            plan_id="security-focus",
            name="Security Focus",
            description="Security-first quality plan for applications handling sensitive data.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.SECURITY,
            loop_config=LoopConfig(
                name="security-loop",
                description="Security-focused quality loop",
                criteria=["security", "backend", "infrastructure"],
                max_iterations=6,
                threshold_a=0.9,
                threshold_b=0.95,
                strict_mode=True,
            ),
            goals=[
                {
                    "name": "Zero Security Vulnerabilities",
                    "description": "No critical or high security issues",
                    "goal_type": "target_score",
                    "target_value": 1.0,
                    "category": "security",
                },
                {
                    "name": "Secure Infrastructure",
                    "description": "Infrastructure follows security best practices",
                    "goal_type": "category_target",
                    "target_value": 0.95,
                    "category": "infrastructure",
                },
            ],
            gate_preset="production",
            priority_profile="security-first",
            estimated_duration="1-2 weeks",
            tags=["security", "compliance", "sensitive-data"],
        )

        # 5. Performance Focus Plan
        presets["performance-focus"] = QualityPlan(
            plan_id="performance-focus",
            name="Performance Focus",
            description="Performance-optimized quality plan for high-traffic applications.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.PERFORMANCE,
            loop_config=LoopConfig(
                name="performance-loop",
                description="Performance-focused quality loop",
                criteria=["performance", "backend", "database", "infrastructure"],
                max_iterations=5,
                threshold_a=0.8,
                threshold_b=0.85,
            ),
            goals=[
                {
                    "name": "Optimal Performance",
                    "description": "Achieve optimal performance scores",
                    "goal_type": "target_score",
                    "target_value": 0.85,
                    "category": "performance",
                },
                {
                    "name": "Database Efficiency",
                    "description": "Database queries optimized",
                    "goal_type": "category_target",
                    "target_value": 0.85,
                    "category": "database",
                },
            ],
            gate_preset="staging",
            priority_profile="performance-focused",
            estimated_duration="1 week",
            tags=["performance", "optimization", "scalability"],
        )

        # 6. Stability Plan
        presets["stability"] = QualityPlan(
            plan_id="stability",
            name="Stability",
            description="Maintain quality standards with focus on consistency and reliability.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.STABILITY,
            loop_config=LoopConfig(
                name="stability-loop",
                description="Stability-focused quality loop",
                criteria=["backend", "frontend", "testing"],
                max_iterations=3,
                threshold_a=0.85,
                threshold_b=0.85,
                strict_mode=True,
            ),
            goals=[
                {
                    "name": "Consistent Quality",
                    "description": "Maintain consistent quality across runs",
                    "goal_type": "stability",
                    "target_value": 0.05,  # Max 5% variance
                },
                {
                    "name": "High Reliability",
                    "description": "Maintain high reliability score",
                    "goal_type": "target_score",
                    "target_value": 0.88,
                },
            ],
            gate_preset="staging",
            priority_profile="balanced",
            estimated_duration="Ongoing",
            tags=["stability", "maintenance", "reliability"],
        )

        # 7. Aggressive Improvement Plan
        presets["aggressive"] = QualityPlan(
            plan_id="aggressive",
            name="Aggressive Improvement",
            description="Rapid quality improvement plan with high targets and intensive iterations.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.IMPROVEMENT,
            loop_config=LoopConfig(
                name="aggressive-loop",
                description="Aggressive improvement quality loop",
                criteria=["backend", "frontend", "security", "testing", "performance", "docs"],
                max_iterations=7,
                threshold_a=0.9,
                threshold_b=0.92,
                strict_mode=True,
                # Exp 78: Enable goal suggestions
                suggest_goals=True,
                auto_apply_goals=True,
                goal_suggestion_strategy="optimistic",
            ),
            goals=[
                {
                    "name": "Excellence Target",
                    "description": "Achieve excellent quality score",
                    "goal_type": "target_score",
                    "target_value": 0.92,
                },
                {
                    "name": "All Categories Strong",
                    "description": "All categories above 0.85",
                    "goal_type": "pass_rate",
                    "target_value": 1.0,
                },
                {
                    "name": "Rapid Improvement",
                    "description": "10% improvement per sprint",
                    "goal_type": "improvement",
                    "target_value": 0.10,
                },
            ],
            gate_preset="production",
            priority_profile="quality-first",
            estimated_duration="2-3 weeks",
            tags=["aggressive", "excellence", "intensive"],
        )

        # 8. CI/CD Integration Plan
        presets["ci-cd"] = QualityPlan(
            plan_id="ci-cd",
            name="CI/CD Integration",
            description="Quality plan optimized for continuous integration and deployment pipelines.",
            plan_type=PlanType.PRESET,
            category=PlanCategory.CI_CD,
            loop_config=LoopConfig(
                name="ci-cd-loop",
                description="CI/CD quality loop",
                criteria=["backend", "frontend", "testing"],
                max_iterations=2,
                threshold_a=0.8,
                threshold_b=0.85,
                json_output="quality-report.json",
            ),
            goals=[
                {
                    "name": "Gate Passing",
                    "description": "Pass quality gates for deployment",
                    "goal_type": "target_score",
                    "target_value": 0.85,
                },
            ],
            gate_preset="ci",
            priority_profile="balanced",
            estimated_duration="Per pipeline",
            tags=["ci-cd", "automation", "deployment"],
        )

        return presets

    def list_presets(self, category: Optional[PlanCategory] = None) -> List[QualityPlan]:
        """List available presets, optionally filtered by category"""
        presets = list(self.presets.values())
        if category:
            presets = [p for p in presets if p.category == category]
        return sorted(presets, key=lambda p: p.name)

    def get_plan(self, plan_id: str) -> Optional[QualityPlan]:
        """Get a plan by ID (preset or custom)"""
        # Check presets first
        if plan_id in self.presets:
            return self.presets[plan_id]

        # Check custom plans
        plan_file = self.config_dir / f"{plan_id}.yml"
        if plan_file.exists():
            return QualityPlan.from_yaml(plan_file.read_text())

        return None

    def save_plan(self, plan: QualityPlan) -> None:
        """Save a custom plan to disk"""
        plan.plan_type = PlanType.CUSTOM
        plan.updated_at = datetime.now().isoformat()

        plan_file = self.config_dir / f"{plan.plan_id}.yml"
        plan_file.write_text(plan.to_yaml())

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a custom plan (cannot delete presets)"""
        if plan_id in self.presets:
            return False  # Cannot delete presets

        plan_file = self.config_dir / f"{plan_id}.yml"
        if plan_file.exists():
            plan_file.unlink()
            return True
        return False

    def list_custom_plans(self) -> List[QualityPlan]:
        """List all custom plans saved by user"""
        plans = []
        for plan_file in self.config_dir.glob("*.yml"):
            try:
                plan = QualityPlan.from_yaml(plan_file.read_text())
                plans.append(plan)
            except Exception:
                continue  # Skip invalid files
        return sorted(plans, key=lambda p: p.name)

    def recommend_plan(
        self,
        keywords: List[str],
        category: Optional[PlanCategory] = None,
    ) -> List[Tuple[QualityPlan, float]]:
        """Recommend plans based on keywords and category

        Returns list of (plan, score) tuples sorted by relevance.
        """
        keywords_lower = [k.lower() for k in keywords]
        results = []

        all_plans = list(self.presets.values()) + self.list_custom_plans()

        for plan in all_plans:
            if category and plan.category != category:
                continue

            score = 0.0

            # Check name match
            for keyword in keywords_lower:
                if keyword in plan.name.lower():
                    score += 1.0

            # Check description match
            for keyword in keywords_lower:
                if keyword in plan.description.lower():
                    score += 0.5

            # Check tag match
            for keyword in keywords_lower:
                for tag in plan.tags:
                    if keyword in tag.lower():
                        score += 0.8

            # Check category match
            for keyword in keywords_lower:
                if keyword in plan.category.value:
                    score += 0.3

            if score > 0:
                results.append((plan, score))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def compare_plans(self, plan_id1: str, plan_id2: str) -> Dict[str, Any]:
        """Compare two plans and return differences"""
        plan1 = self.get_plan(plan_id1)
        plan2 = self.get_plan(plan_id2)

        if not plan1 or not plan2:
            return {"error": "One or both plans not found"}

        differences = {
            "plan1": plan1.name,
            "plan2": plan2.name,
            "loop_config": self._compare_loop_config(plan1.loop_config, plan2.loop_config),
            "goals": {
                "plan1_count": len(plan1.goals),
                "plan2_count": len(plan2.goals),
            },
            "gate_preset": {
                "plan1": plan1.gate_preset,
                "plan2": plan2.gate_preset,
            },
            "priority_profile": {
                "plan1": plan1.priority_profile,
                "plan2": plan2.priority_profile,
            },
            "estimated_duration": {
                "plan1": plan1.estimated_duration,
                "plan2": plan2.estimated_duration,
            },
        }

        return differences

    def _compare_loop_config(self, config1: LoopConfig, config2: LoopConfig) -> Dict[str, Any]:
        """Compare two loop configurations"""
        return {
            "max_iterations": {"plan1": config1.max_iterations, "plan2": config2.max_iterations},
            "threshold_a": {"plan1": config1.threshold_a, "plan2": config2.threshold_a},
            "threshold_b": {"plan1": config1.threshold_b, "plan2": config2.threshold_b},
            "criteria": {"plan1": config1.criteria, "plan2": config2.criteria},
            "strict_mode": {"plan1": config1.strict_mode, "plan2": config2.strict_mode},
        }

    def export_plan(self, plan_id: str, output_path: Path) -> None:
        """Export a plan to a file for sharing"""
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan '{plan_id}' not found")

        output_path.write_text(plan.to_yaml())

    def import_plan(self, input_path: Path, new_id: Optional[str] = None) -> QualityPlan:
        """Import a plan from a file"""
        content = input_path.read_text()
        plan = QualityPlan.from_yaml(content)

        if new_id:
            plan.plan_id = new_id

        plan.plan_type = PlanType.CUSTOM
        return plan

    def get_plan_for_apply(self, plan_id: str) -> Dict[str, Any]:
        """Get plan data formatted for applying to quality loop"""
        plan = self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan '{plan_id}' not found")

        return {
            "loop_config": plan.loop_config,
            "goals": plan.goals,
            "gate_preset": plan.gate_preset,
            "gate_policy": plan.gate_policy,
            "priority_profile": plan.priority_profile,
            "cascade_strategy": plan.cascade_strategy,
        }


class QualityPlanWizard:
    """Interactive wizard for creating custom quality plans (Exp 80)"""

    def __init__(
        self,
        input_func: Optional[Callable[[str], str]] = None,
        output_func: Optional[Callable[[str], None]] = None,
    ):
        """Initialize wizard with optional I/O functions (for testing)"""
        self.input_func = input_func or input
        self.output_func = output_func or print
        self.manager = QualityPlanManager()
        self.responses: Dict[str, Any] = {}

    def create_plan_interactive(
        self,
        plan_id: Optional[str] = None,
        skip_prompts: bool = False,
    ) -> Optional[QualityPlan]:
        """Run interactive wizard to create a custom quality plan

        Args:
            plan_id: Optional plan ID (will prompt if not provided)
            skip_prompts: If True, use smart defaults without prompting

        Returns:
            Created QualityPlan or None if cancelled
        """
        self.output_func("\n" + "="*60)
        self.output_func("🎯 Quality Plan Wizard")
        self.output_func("="*60)
        self.output_func("This wizard will guide you through creating a custom quality plan.")
        self.output_func("Press Enter at any time to use the [default] value.\n")

        # Step 1: Basic Info
        if not self._step_basic_info(plan_id, skip_prompts):
            return None

        # Step 2: Category Selection
        if not self._step_category(skip_prompts):
            return None

        # Step 3: Loop Configuration
        if not self._step_loop_config(skip_prompts):
            return None

        # Step 4: Goals Configuration
        if not self._step_goals(skip_prompts):
            return None

        # Step 5: Gate Policy
        if not self._step_gate_policy(skip_prompts):
            return None

        # Step 6: Priority Profile
        if not self._step_priority_profile(skip_prompts):
            return None

        # Step 7: Final Review
        if not self._step_review(skip_prompts):
            return None

        # Create and return the plan
        return self._build_plan()

    def _step_basic_info(self, plan_id: Optional[str], skip_prompts: bool) -> bool:
        """Step 1: Basic plan information"""
        self.output_func("\n📝 Step 1: Basic Information")
        self.output_func("-" * 40)

        # Plan ID
        if not plan_id:
            plan_id = self._prompt(
                "Enter a unique ID for this plan (lowercase, hyphens allowed)",
                default="custom-plan"
            )
        if not plan_id or plan_id.lower() in ["cancel", "exit", "quit"]:
            return False

        self.responses["plan_id"] = plan_id.lower().replace(" ", "-")

        # Plan name
        name = self._prompt(
            "Enter a descriptive name for this plan",
            default=self._format_name_from_id(self.responses["plan_id"])
        )
        if not name:
            return False
        self.responses["name"] = name

        # Description
        description = self._prompt(
            "Enter a description for this plan",
            default=f"Custom quality plan: {name}"
        )
        if description is None:
            return False
        self.responses["description"] = description

        # Author
        author = self._prompt(
            "Enter your name (optional, for attribution)",
            default=""
        )
        if author is None:
            return False
        self.responses["author"] = author or None

        # Estimated duration
        duration = self._prompt(
            "Enter estimated duration (e.g., '1 week', '2-3 days', 'Ongoing')",
            default="1 week"
        )
        if duration is None:
            return False
        self.responses["estimated_duration"] = duration

        return True

    def _step_category(self, skip_prompts: bool) -> bool:
        """Step 2: Category selection"""
        self.output_func("\n📂 Step 2: Plan Category")
        self.output_func("-" * 40)

        self.output_func("Available categories:")
        for i, cat in enumerate(AVAILABLE_CATEGORIES, 1):
            self.output_func(f"  {i}. {cat}")

        category = self._prompt_choice(
            "Select a category",
            choices=AVAILABLE_CATEGORIES,
            default="general"
        )
        if category is None:
            return False

        self.responses["category"] = category

        # Suggest tags based on category
        suggested_tags = self._suggest_tags_for_category(category)
        tags_input = self._prompt(
            "Enter tags (comma-separated, optional)",
            default=", ".join(suggested_tags)
        )
        if tags_input is None:
            return False

        self.responses["tags"] = [
            tag.strip() for tag in tags_input.split(",")
            if tag.strip()
        ]

        return True

    def _step_loop_config(self, skip_prompts: bool) -> bool:
        """Step 3: Loop configuration"""
        self.output_func("\n⚙️  Step 3: Loop Configuration")
        self.output_func("-" * 40)

        # Criteria selection
        self.output_func("\nAvailable quality criteria:")
        for i, crit in enumerate(AVAILABLE_CRITERIA, 1):
            self.output_func(f"  {i}. {crit}")

        criteria_input = self._prompt(
            "Enter criteria to include (comma-separated, or 'all')",
            default="backend,frontend"
        )
        if criteria_input is None:
            return False

        if criteria_input.lower().strip() == "all":
            criteria = AVAILABLE_CRITERIA.copy()
        else:
            criteria = [
                c.strip() for c in criteria_input.split(",")
                if c.strip() in AVAILABLE_CRITERIA
            ]

        self.responses["criteria"] = criteria

        # Iterations
        iterations = self._prompt_int(
            "Maximum number of refinement iterations",
            default=4,
            min_val=1,
            max_val=20
        )
        if iterations is None:
            return False
        self.responses["max_iterations"] = iterations

        # Thresholds
        threshold_a = self._prompt_float(
            "Quality threshold A (minimum acceptable, 0-1)",
            default=0.8,
            min_val=0.0,
            max_val=1.0
        )
        if threshold_a is None:
            return False
        self.responses["threshold_a"] = threshold_a

        threshold_b = self._prompt_float(
            "Quality threshold B (target threshold, 0-1)",
            default=0.9,
            min_val=threshold_a + 0.01,
            max_val=1.0
        )
        if threshold_b is None:
            return False
        self.responses["threshold_b"] = threshold_b

        # Strict mode
        strict_mode = self._prompt_yes_no(
            "Enable strict mode (stricter rule evaluation)",
            default=False
        )
        if strict_mode is None:
            return False
        self.responses["strict_mode"] = strict_mode

        # Goal suggestions
        suggest_goals = self._prompt_yes_no(
            "Enable automatic goal suggestions",
            default=True
        )
        if suggest_goals is None:
            return False
        self.responses["suggest_goals"] = suggest_goals

        if suggest_goals:
            auto_apply = self._prompt_yes_no(
                "Auto-apply suggested goals",
                default=False
            )
            if auto_apply is None:
                return False
            self.responses["auto_apply_goals"] = auto_apply

            strategy = self._prompt_choice(
                "Goal suggestion strategy",
                choices=AVAILABLE_GOAL_STRATEGIES,
                default="balanced"
            )
            if strategy is None:
                return False
            self.responses["goal_suggestion_strategy"] = strategy

        return True

    def _step_goals(self, skip_prompts: bool) -> bool:
        """Step 4: Goals configuration"""
        self.output_func("\n🎯 Step 4: Quality Goals")
        self.output_func("-" * 40)

        add_goals = self._prompt_yes_no(
            "Do you want to add specific quality goals?",
            default=False
        )
        if add_goals is None:
            return False

        if not add_goals:
            self.responses["goals"] = []
            return True

        goals = []
        while True:
            self.output_func(f"\n--- Goal {len(goals) + 1} ---")

            goal_name = self._prompt(
                "Goal name (or press Enter to finish)",
                default=""
            )
            if not goal_name:
                break

            goal_target = self._prompt_float(
                "Target value (0-1)",
                default=0.85,
                min_val=0.0,
                max_val=1.0
            )
            if goal_target is None:
                break

            goal_category = self._prompt_choice(
                "Category (optional, press Enter for overall)",
                choices=[""] + AVAILABLE_CRITERIA,
                default=""
            )
            if goal_category is None:
                break

            goals.append({
                "name": goal_name,
                "description": f"Target: {goal_target:.2f}",
                "goal_type": "target_score",
                "target_value": goal_target,
                "category": goal_category or None,
            })

            self.output_func(f"✓ Added goal: {goal_name}")

            more = self._prompt_yes_no("Add another goal?", default=False)
            if more is None or not more:
                break

        self.responses["goals"] = goals
        return True

    def _step_gate_policy(self, skip_prompts: bool) -> bool:
        """Step 5: Gate policy configuration"""
        self.output_func("\n🚪 Step 5: Gate Policy")
        self.output_func("-" * 40)

        use_gate = self._prompt_yes_no(
            "Do you want to configure quality gates?",
            default=True
        )
        if use_gate is None:
            return False

        if not use_gate:
            self.responses["gate_preset"] = None
            self.responses["gate_policy"] = None
            return True

        gate_preset = self._prompt_choice(
            "Select gate preset",
            choices=AVAILABLE_GATE_PRESETS,
            default="staging"
        )
        if gate_preset is None:
            return False

        self.responses["gate_preset"] = gate_preset
        self.responses["gate_policy"] = None

        return True

    def _step_priority_profile(self, skip_prompts: bool) -> bool:
        """Step 6: Priority profile configuration"""
        self.output_func("\n⚖️  Step 6: Priority Profile")
        self.output_func("-" * 40)

        use_profile = self._prompt_yes_no(
            "Do you want to configure priority profile?",
            default=True
        )
        if use_profile is None:
            return False

        if not use_profile:
            self.responses["priority_profile"] = None
            self.responses["cascade_strategy"] = None
            return True

        priority_profile = self._prompt_choice(
            "Select priority profile",
            choices=AVAILABLE_PRIORITY_PROFILES,
            default="balanced"
        )
        if priority_profile is None:
            return False

        self.responses["priority_profile"] = priority_profile

        # Cascade strategy (only if relevant)
        use_cascade = self._prompt_yes_no(
            "Use cascade strategy for hybrid profiles?",
            default=False
        )
        if use_cascade is None:
            return False

        if use_cascade:
            cascade_strategy = self._prompt_choice(
                "Select cascade strategy",
                choices=AVAILABLE_CASCADE_STRATEGIES,
                default="bal"
            )
            if cascade_strategy is None:
                return False
            self.responses["cascade_strategy"] = cascade_strategy
        else:
            self.responses["cascade_strategy"] = None

        return True

    def _step_review(self, skip_prompts: bool) -> bool:
        """Step 7: Final review and confirmation"""
        self.output_func("\n✅ Step 7: Review and Confirm")
        self.output_func("-" * 40)

        self._print_summary()

        confirm = self._prompt_yes_no(
            "\nCreate this quality plan?",
            default=True
        )
        if confirm is None:
            return False

        return confirm

    def _build_plan(self) -> QualityPlan:
        """Build QualityPlan from collected responses"""
        # Create loop config
        loop_config = LoopConfig(
            name=f"{self.responses['plan_id']}-loop",
            description=f"Loop config for {self.responses['name']}",
            criteria=self.responses.get("criteria", ["backend", "frontend"]),
            max_iterations=self.responses.get("max_iterations", 4),
            threshold_a=self.responses.get("threshold_a", 0.8),
            threshold_b=self.responses.get("threshold_b", 0.9),
            strict_mode=self.responses.get("strict_mode", False),
            suggest_goals=self.responses.get("suggest_goals", False),
            auto_apply_goals=self.responses.get("auto_apply_goals", False),
            goal_suggestion_strategy=self.responses.get("goal_suggestion_strategy"),
        )

        # Map category string to PlanCategory enum
        category_map = {
            "general": PlanCategory.GENERAL,
            "production": PlanCategory.PRODUCTION,
            "security": PlanCategory.SECURITY,
            "performance": PlanCategory.PERFORMANCE,
            "stability": PlanCategory.STABILITY,
            "improvement": PlanCategory.IMPROVEMENT,
            "ci_cd": PlanCategory.CI_CD,
        }
        category = category_map.get(
            self.responses.get("category", "general"),
            PlanCategory.GENERAL
        )

        return QualityPlan(
            plan_id=self.responses["plan_id"],
            name=self.responses["name"],
            description=self.responses["description"],
            plan_type=PlanType.CUSTOM,
            category=category,
            loop_config=loop_config,
            goals=self.responses.get("goals", []),
            gate_preset=self.responses.get("gate_preset"),
            priority_profile=self.responses.get("priority_profile"),
            cascade_strategy=self.responses.get("cascade_strategy"),
            author=self.responses.get("author"),
            tags=self.responses.get("tags", []),
            estimated_duration=self.responses.get("estimated_duration"),
        )

    def _print_summary(self) -> None:
        """Print summary of collected responses"""
        self.output_func("\n" + "="*60)
        self.output_func("📋 Plan Summary")
        self.output_func("="*60)

        self.output_func(f"\nName: {self.responses.get('name')}")
        self.output_func(f"ID: {self.responses.get('plan_id')}")
        self.output_func(f"Category: {self.responses.get('category')}")
        self.output_func(f"Description: {self.responses.get('description')}")

        self.output_func(f"\nLoop Config:")
        self.output_func(f"  Criteria: {', '.join(self.responses.get('criteria', []))}")
        self.output_func(f"  Iterations: {self.responses.get('max_iterations')}")
        self.output_func(f"  Thresholds: A={self.responses.get('threshold_a')}, B={self.responses.get('threshold_b')}")
        self.output_func(f"  Strict Mode: {self.responses.get('strict_mode')}")

        if self.responses.get('goals'):
            self.output_func(f"\nGoals: {len(self.responses['goals'])} goal(s)")
            for goal in self.responses['goals']:
                self.output_func(f"  - {goal['name']}: {goal['target_value']}")

        self.output_func(f"\nGate: {self.responses.get('gate_preset', 'None')}")
        self.output_func(f"Profile: {self.responses.get('priority_profile', 'None')}")
        if self.responses.get('cascade_strategy'):
            self.output_func(f"Cascade: {self.responses['cascade_strategy']}")

        self.output_func(f"\nDuration: {self.responses.get('estimated_duration')}")
        self.output_func(f"Tags: {', '.join(self.responses.get('tags', []))}")

        self.output_func("="*60)

    def _format_name_from_id(self, plan_id: str) -> str:
        """Generate a readable name from plan ID"""
        return " ".join(
            word.capitalize() for word in plan_id.replace("-", " ").split()
        )

    def _suggest_tags_for_category(self, category: str) -> List[str]:
        """Suggest tags based on category"""
        tag_suggestions = {
            "general": ["custom", "quality"],
            "production": ["production", "deployment"],
            "security": ["security", "compliance"],
            "performance": ["performance", "optimization"],
            "stability": ["stability", "maintenance"],
            "improvement": ["improvement", "enhancement"],
            "ci_cd": ["ci-cd", "automation"],
        }
        return tag_suggestions.get(category, ["custom"])

    def _prompt(self, message: str, default: str = "") -> Optional[str]:
        """Prompt user for input with default value"""
        prompt = f"{message}"
        if default:
            prompt += f" [{default}]"
        prompt += ": "

        try:
            response = self.input_func(prompt).strip()
            if response.lower() in ["cancel", "exit", "quit"]:
                return None
            return response or default
        except (EOFError, KeyboardInterrupt):
            return None

    def _prompt_choice(
        self,
        message: str,
        choices: List[str],
        default: str = ""
    ) -> Optional[str]:
        """Prompt user to select from choices"""
        prompt = f"{message}"
        if default:
            prompt += f" [{default}]"
        prompt += f"\nChoices: {', '.join(choices)}\n> "

        try:
            response = self.input_func(prompt).strip().lower()
            if response.lower() in ["cancel", "exit", "quit"]:
                return None
            if not response:
                return default

            # Find matching choice
            for choice in choices:
                if choice.lower() == response or choice.lower().startswith(response):
                    return choice

            # Invalid choice, return default
            self.output_func(f"Invalid choice, using default: {default}")
            return default
        except (EOFError, KeyboardInterrupt):
            return None

    def _prompt_int(
        self,
        message: str,
        default: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
    ) -> Optional[int]:
        """Prompt user for integer input"""
        while True:
            prompt = f"{message}"
            prompt += f" [{default}]"
            if min_val is not None and max_val is not None:
                prompt += f" (range: {min_val}-{max_val})"
            prompt += ": "

            try:
                response = self.input_func(prompt).strip()
                if response.lower() in ["cancel", "exit", "quit"]:
                    return None
                if not response:
                    return default

                value = int(response)
                if min_val is not None and value < min_val:
                    self.output_func(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    self.output_func(f"Value must be at most {max_val}")
                    continue
                return value
            except ValueError:
                self.output_func("Please enter a valid integer")
            except (EOFError, KeyboardInterrupt):
                return None

    def _prompt_float(
        self,
        message: str,
        default: float,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> Optional[float]:
        """Prompt user for float input"""
        while True:
            prompt = f"{message}"
            prompt += f" [{default}]"
            if min_val is not None and max_val is not None:
                prompt += f" (range: {min_val}-{max_val})"
            prompt += ": "

            try:
                response = self.input_func(prompt).strip()
                if response.lower() in ["cancel", "exit", "quit"]:
                    return None
                if not response:
                    return default

                value = float(response)
                if min_val is not None and value < min_val:
                    self.output_func(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    self.output_func(f"Value must be at most {max_val}")
                    continue
                return value
            except ValueError:
                self.output_func("Please enter a valid number")
            except (EOFError, KeyboardInterrupt):
                return None

    def _prompt_yes_no(self, message: str, default: bool = False) -> Optional[bool]:
        """Prompt user for yes/no input"""
        default_str = "Y/n" if default else "y/N"
        prompt = f"{message} [{default_str}]: "

        try:
            response = self.input_func(prompt).strip().lower()
            if response in ["cancel", "exit", "quit"]:
                return None
            if not response:
                return default
            return response in ["y", "yes", "true", "1"]
        except (EOFError, KeyboardInterrupt):
            return None


# Convenience functions for CLI
def get_builtin_plans() -> Dict[str, QualityPlan]:
    """Get all built-in quality plan presets"""
    manager = QualityPlanManager()
    return manager.presets


def list_available_plans(category: Optional[str] = None) -> List[QualityPlan]:
    """List all available plans (presets + custom)"""
    manager = QualityPlanManager()
    if category:
        try:
            cat = PlanCategory(category)
            return manager.list_presets(cat)
        except ValueError:
            return manager.list_presets()
    return manager.list_presets() + manager.list_custom_plans()


def recommend_quality_plan(keywords: List[str]) -> List[QualityPlan]:
    """Get recommended plans based on keywords"""
    manager = QualityPlanManager()
    results = manager.recommend_plan(keywords)
    return [plan for plan, score in results if score > 0]


def get_plan_details(plan_id: str) -> Optional[str]:
    """Get detailed summary of a plan"""
    manager = QualityPlanManager()
    plan = manager.get_plan(plan_id)
    return plan.get_summary() if plan else None


# Wizard convenience functions (Exp 80)
def create_plan_interactive(
    plan_id: Optional[str] = None,
    input_func: Optional[Callable[[str], str]] = None,
    output_func: Optional[Callable[[str], None]] = None,
) -> Optional[QualityPlan]:
    """Create a quality plan using interactive wizard

    Args:
        plan_id: Optional plan ID (will prompt if not provided)
        input_func: Optional input function for testing
        output_func: Optional output function for testing

    Returns:
        Created QualityPlan or None if cancelled
    """
    wizard = QualityPlanWizard(input_func, output_func)
    return wizard.create_plan_interactive(plan_id)


def create_plan_from_quick_setup(
    name: str,
    category: str = "general",
    strict_mode: bool = False,
    iterations: int = 4,
) -> Optional[QualityPlan]:
    """Create a quality plan with quick setup (non-interactive)

    Args:
        name: Plan name
        category: Plan category
        strict_mode: Enable strict mode
        iterations: Max iterations

    Returns:
        Created QualityPlan or None if validation failed
    """
    plan_id = name.lower().replace(" ", "-")

    # Map category string to PlanCategory enum
    category_map = {
        "general": PlanCategory.GENERAL,
        "production": PlanCategory.PRODUCTION,
        "security": PlanCategory.SECURITY,
        "performance": PlanCategory.PERFORMANCE,
        "stability": PlanCategory.STABILITY,
        "improvement": PlanCategory.IMPROVEMENT,
        "ci_cd": PlanCategory.CI_CD,
    }
    category_enum = category_map.get(category, PlanCategory.GENERAL)

    # Suggest criteria based on category
    criteria_map = {
        PlanCategory.GENERAL: ["backend", "frontend"],
        PlanCategory.PRODUCTION: ["backend", "frontend", "security", "testing", "performance"],
        PlanCategory.SECURITY: ["security", "backend", "infrastructure"],
        PlanCategory.PERFORMANCE: ["performance", "backend", "database", "infrastructure"],
        PlanCategory.STABILITY: ["backend", "frontend", "testing"],
        PlanCategory.IMPROVEMENT: ["backend", "frontend", "testing", "docs"],
        PlanCategory.CI_CD: ["backend", "frontend", "testing"],
    }

    # Create loop config
    loop_config = LoopConfig(
        name=f"{plan_id}-loop",
        description=f"Loop config for {name}",
        criteria=criteria_map.get(category_enum, ["backend", "frontend"]),
        max_iterations=iterations,
        threshold_a=0.8 if not strict_mode else 0.85,
        threshold_b=0.9 if not strict_mode else 0.95,
        strict_mode=strict_mode,
    )

    plan = QualityPlan(
        plan_id=plan_id,
        name=name,
        description=f"Quality plan for {name}",
        plan_type=PlanType.CUSTOM,
        category=category_enum,
        loop_config=loop_config,
        gate_preset="staging" if category != "ci_cd" else "ci",
        priority_profile="balanced",
        estimated_duration="1 week",
        tags=[category],
    )

    # Validate
    errors = plan.validate()
    if errors:
        return None

    return plan
