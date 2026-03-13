"""
Goal-Based Quality Gates

Integrates Quality Goals with Quality Gate Policies to enable
goal-based quality control for CI/CD pipelines.

Key features:
- Gate policies based on goal achievement status
- Automatic goal validation in quality gates
- Goal-aware blocking for at-risk/failed goals
- Integration with existing gate policy system
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .quality_goals import (
    QualityGoal,
    GoalStatus,
    QualityGoalsManager,
    format_goal_progress,
    format_goals_summary,
)
from .gate_policies import (
    GatePolicy,
    GateResult,
    GatePolicyManager,
    GATE_PRESETS,
)


class GoalGateMode(Enum):
    """How goals affect gate decision"""
    ALL_MUST_PASS = "all_must_pass"  # All goals must be achieved
    NONE_FAILED = "none_failed"  # No goals can be failed
    NONE_AT_RISK = "none_at_risk"  # No goals can be at_risk or failed
    PERCENTAGE_ACHIEVED = "percentage_achieved"  # Minimum % of goals achieved
    CUSTOM = "custom"  # Custom logic via callback


@dataclass
class GoalGateConfig:
    """Configuration for goal-based gate"""
    mode: GoalGateMode
    min_percentage: float = 0.0  # For PERCENTAGE_ACHIEVED mode
    allow_at_risk: bool = True  # For ALL_MUST_PASS mode
    goal_categories: Optional[List[str]] = None  # Filter goals by category
    goal_types: Optional[List[str]] = None  # Filter goals by type
    description: str = ""


@dataclass
class GoalGateResult:
    """Result of goal-based gate evaluation"""
    passed: bool
    total_goals: int
    achieved_goals: int
    at_risk_goals: int
    failed_goals: int
    not_started_goals: int
    in_progress_goals: int
    blocked_goals: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


class GoalGatePolicy:
    """
    Gate policy that validates quality goals.

    Combines Quality Goals system with Quality Gate Policies
    to enable goal-based quality control.
    """

    def __init__(
        self,
        name: str,
        config: GoalGateConfig,
        goals_file: Optional[str] = None,
    ):
        self.name = name
        self.config = config
        self.goals_file = goals_file
        self.goals_manager = QualityGoalsManager(goals_file)

    def evaluate(self, evaluation_result: Any) -> GateResult:
        """
        Evaluate gate against quality goals.

        Args:
            evaluation_result: Current evaluation result

        Returns:
            GateResult with goal validation outcome
        """
        # Get current goals
        goals = self.goals_manager.get_all_goals()

        # Filter goals if specified
        if self.config.goal_categories:
            goals = [g for g in goals if g.category in self.config.goal_categories]
        if self.config.goal_types:
            goal_type_names = [t.value for t in self.config.goal_types]
            goals = [g for g in goals if g.goal_type.value in goal_type_names]

        # Evaluate against mode
        result = self._evaluate_goals(goals)

        return GateResult(
            policy_name=self.name,
            passed=result.passed,
            message=result.message,
            details={
                "total_goals": result.total_goals,
                "achieved_goals": result.achieved_goals,
                "at_risk_goals": result.at_risk_goals,
                "failed_goals": result.failed_goals,
                "blocked_goals": result.blocked_goals,
            },
        )

    def _evaluate_goals(self, goals: List[QualityGoal]) -> GoalGateResult:
        """Evaluate goals based on configured mode"""
        total = len(goals)
        achieved = sum(1 for g in goals if g.status == GoalStatus.ACHIEVED)
        at_risk = sum(1 for g in goals if g.status == GoalStatus.AT_RISK)
        failed = sum(1 for g in goals if g.status == GoalStatus.FAILED)
        not_started = sum(1 for g in goals if g.status == GoalStatus.NOT_STARTED)
        in_progress = sum(1 for g in goals if g.status == GoalStatus.IN_PROGRESS)

        blocked = []
        passed = False
        message = ""

        if self.config.mode == GoalGateMode.ALL_MUST_PASS:
            # All goals must be achieved (at_risk allowed based on config)
            failed_goals = [g for g in goals if g.status == GoalStatus.FAILED]
            if self.config.allow_at_risk:
                passed = len(failed_goals) == 0 and achieved + at_risk == total
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in failed_goals
                ]
            else:
                passed = achieved == total
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in goals
                    if g.status != GoalStatus.ACHIEVED
                ]

            if not passed:
                message = f"Gate failed: {len(blocked)} goal(s) not achieved"

        elif self.config.mode == GoalGateMode.NONE_FAILED:
            # No goals can be failed
            passed = failed == 0
            blocked = [
                {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                for g in goals
                if g.status == GoalStatus.FAILED
            ]
            if not passed:
                message = f"Gate failed: {failed} goal(s) failed"

        elif self.config.mode == GoalGateMode.NONE_AT_RISK:
            # No goals can be at_risk or failed
            blocked = [
                {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                for g in goals
                if g.status in [GoalStatus.AT_RISK, GoalStatus.FAILED]
            ]
            passed = len(blocked) == 0
            if not passed:
                message = f"Gate failed: {len(blocked)} goal(s) at risk or failed"

        elif self.config.mode == GoalGateMode.PERCENTAGE_ACHIEVED:
            # Minimum percentage of goals must be achieved
            percentage = (achieved / total * 100) if total > 0 else 0
            passed = percentage >= self.config.min_percentage
            if not passed:
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in goals
                    if g.status != GoalStatus.ACHIEVED
                ]
                message = f"Gate failed: {percentage:.1f}% goals achieved, required {self.config.min_percentage}%"
            else:
                message = f"Gate passed: {percentage:.1f}% goals achieved"

        if passed and not message:
            message = f"Gate passed: {achieved}/{total} goals achieved"

        return GoalGateResult(
            passed=passed,
            total_goals=total,
            achieved_goals=achieved,
            at_risk_goals=at_risk,
            failed_goals=failed,
            not_started_goals=not_started,
            in_progress_goals=in_progress,
            blocked_goals=blocked,
            message=message,
        )


# Pre-configured goal gate presets
GOAL_GATE_PRESETS: Dict[str, GoalGateConfig] = {
    "strict": GoalGateConfig(
        mode=GoalGateMode.ALL_MUST_PASS,
        allow_at_risk=False,
        description="All goals must be achieved, at-risk goals block gate",
    ),
    "moderate": GoalGateConfig(
        mode=GoalGateMode.ALL_MUST_PASS,
        allow_at_risk=True,
        description="All goals must be achieved or at-risk, failed goals block gate",
    ),
    "lenient": GoalGateConfig(
        mode=GoalGateMode.NONE_FAILED,
        description="Only failed goals block gate, at-risk allowed",
    ),
    "conservative": GoalGateConfig(
        mode=GoalGateMode.NONE_AT_RISK,
        description="At-risk or failed goals block gate",
    ),
    "balanced": GoalGateConfig(
        mode=GoalGateMode.PERCENTAGE_ACHIEVED,
        min_percentage=80.0,
        description="At least 80% of goals must be achieved",
    ),
}


def create_goal_gate(
    name: str,
    mode: str = "moderate",
    goals_file: Optional[str] = None,
    **kwargs
) -> GoalGatePolicy:
    """
    Create a goal-based gate policy.

    Args:
        name: Name of the gate policy
        mode: Gate mode (strict, moderate, lenient, conservative, balanced, or custom)
        goals_file: Path to goals file
        **kwargs: Additional config options

    Returns:
        GoalGatePolicy instance
    """
    if mode in GOAL_GATE_PRESETS:
        config = GOAL_GATE_PRESETS[mode]
    else:
        # Custom mode
        mode_enum = GoalGateMode(mode)
        config = GoalGateConfig(
            mode=mode_enum,
            min_percentage=kwargs.get("min_percentage", 0.0),
            allow_at_risk=kwargs.get("allow_at_risk", True),
            goal_categories=kwargs.get("goal_categories"),
            goal_types=kwargs.get("goal_types"),
        )

    return GoalGatePolicy(name, config, goals_file)


def evaluate_goal_gate(
    name: str,
    mode: str = "moderate",
    goals_file: Optional[str] = None,
    evaluation_result: Optional[Any] = None,
    **kwargs
) -> GateResult:
    """
    Evaluate a goal-based gate policy.

    Args:
        name: Name of the gate policy
        mode: Gate mode (strict, moderate, lenient, conservative, balanced)
        goals_file: Path to goals file
        evaluation_result: Current evaluation result
        **kwargs: Additional config options

    Returns:
        GateResult with evaluation outcome
    """
    gate = create_goal_gate(name, mode, goals_file, **kwargs)
    return gate.evaluate(evaluation_result)


def format_goal_gate_result(result: GateResult) -> str:
    """Format goal gate result for display"""
    lines = [
        f"Goal Gate: {result.policy_name}",
        f"Status: {'PASSED' if result.passed else 'FAILED'}",
        f"Message: {result.message}",
        "",
        "Goal Summary:",
    ]

    details = result.details or {}
    total = details.get("total_goals", 0)
    achieved = details.get("achieved_goals", 0)
    at_risk = details.get("at_risk_goals", 0)
    failed = details.get("failed_goals", 0)

    lines.append(f"  Total: {total}")
    lines.append(f"  Achieved: {achieved}")
    lines.append(f"  At Risk: {at_risk}")
    lines.append(f"  Failed: {failed}")

    blocked = details.get("blocked_goals", [])
    if blocked:
        lines.append("")
        lines.append("Blocked Goals:")
        for goal in blocked:
            lines.append(f"  - {goal['name']} [{goal['status']}]")

    return "\n".join(lines)


def format_goal_gate_result_json(result: GateResult) -> Dict[str, Any]:
    """Format goal gate result as JSON"""
    return {
        "policy_name": result.policy_name,
        "passed": result.passed,
        "message": result.message,
        "details": result.details,
    }


def list_goal_gate_presets() -> Dict[str, str]:
    """List available goal gate presets"""
    return {
        name: config.description
        for name, config in GOAL_GATE_PRESETS.items()
    }


def get_goal_gate_preset_info(preset_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a goal gate preset"""
    if preset_name not in GOAL_GATE_PRESETS:
        return None

    config = GOAL_GATE_PRESETS[preset_name]
    return {
        "name": preset_name,
        "mode": config.mode.value,
        "description": config.description,
        "allow_at_risk": config.allow_at_risk,
        "min_percentage": config.min_percentage,
    }


def recommend_goal_gate(
    project_type: str,
    strictness: str = "moderate",
) -> Optional[str]:
    """
    Recommend a goal gate preset based on project context.

    Args:
        project_type: Type of project (production, staging, development, etc.)
        strictness: Desired strictness level (strict, moderate, lenient)

    Returns:
        Recommended preset name
    """
    if strictness == "strict":
        return "strict"
    elif strictness == "lenient":
        return "lenient"
    elif project_type == "production":
        return "conservative"
    else:
        return "moderate"


class GoalAwareGatePolicy:
    """
    Enhanced gate policy that automatically updates goals based on evaluation results.

    This class combines gate evaluation with automatic goal tracking:
    1. Evaluates gate against current goals
    2. Updates goal progress based on evaluation result
    3. Saves updated goals for tracking
    """

    def __init__(
        self,
        name: str,
        config: GoalGateConfig,
        goals_file: Optional[str] = None,
        auto_update: bool = True,
    ):
        self.name = name
        self.config = config
        self.goals_file = goals_file
        self.auto_update = auto_update
        self.goals_manager = QualityGoalsManager(goals_file)

    def evaluate_and_update(
        self,
        evaluation_result: Any,
        score: float,
        category_scores: Optional[Dict[str, float]] = None,
    ) -> GateResult:
        """
        Evaluate gate and update goal progress.

        Args:
            evaluation_result: Current evaluation result
            score: Overall quality score
            category_scores: Category-specific scores

        Returns:
            GateResult with evaluation outcome
        """
        # First, update goals with new evaluation data
        if self.auto_update:
            self._update_goals(evaluation_result, score, category_scores)

        # Then evaluate gate against updated goals
        return self.evaluate(evaluation_result)

    def _update_goals(
        self,
        evaluation_result: Any,
        score: float,
        category_scores: Optional[Dict[str, float]] = None,
    ):
        """Update goal progress based on evaluation result"""
        goals = self.goals_manager.get_all_goals()

        for goal in goals:
            try:
                # Update goal based on type
                if goal.goal_type.value == "target_score":
                    self.goals_manager.update_goal_progress(
                        goal.goal_id,
                        score,
                        category_scores,
                    )
                elif goal.goal_type.value == "category_target" and goal.category:
                    cat_score = category_scores.get(goal.category, 0.0) if category_scores else 0.0
                    self.goals_manager.update_goal_progress(
                        goal.goal_id,
                        cat_score,
                        category_scores,
                    )
                elif goal.goal_type.value == "pass_rate":
                    # Calculate pass rate from evaluation result
                    pass_rate = self._calculate_pass_rate(evaluation_result)
                    self.goals_manager.update_goal_progress(
                        goal.goal_id,
                        pass_rate,
                        category_scores,
                    )
            except Exception:
                # Skip goal if update fails
                continue

        # Save updated goals
        self.goals_manager.save_goals()

    def _calculate_pass_rate(self, evaluation_result: Any) -> float:
        """Calculate pass rate from evaluation result"""
        try:
            # Try to get pass rate from result
            if hasattr(evaluation_result, "pass_rate"):
                return evaluation_result.pass_rate
            elif isinstance(evaluation_result, dict):
                return evaluation_result.get("pass_rate", 0.0)
            else:
                # Default to checking rule results
                return 0.0
        except Exception:
            return 0.0

    def evaluate(self, evaluation_result: Any) -> GateResult:
        """Evaluate gate against quality goals"""
        # Reuse GoalGatePolicy evaluation logic
        goals = self.goals_manager.get_all_goals()

        # Filter goals if specified
        if self.config.goal_categories:
            goals = [g for g in goals if g.category in self.config.goal_categories]
        if self.config.goal_types:
            goal_type_names = [t.value for t in self.config.goal_types]
            goals = [g for g in goals if g.goal_type.value in goal_type_names]

        # Evaluate against mode
        result = self._evaluate_goals(goals)

        return GateResult(
            policy_name=self.name,
            passed=result.passed,
            message=result.message,
            details={
                "total_goals": result.total_goals,
                "achieved_goals": result.achieved_goals,
                "at_risk_goals": result.at_risk_goals,
                "failed_goals": result.failed_goals,
                "blocked_goals": result.blocked_goals,
            },
        )

    def _evaluate_goals(self, goals: List[QualityGoal]) -> GoalGateResult:
        """Evaluate goals based on configured mode"""
        total = len(goals)
        achieved = sum(1 for g in goals if g.status == GoalStatus.ACHIEVED)
        at_risk = sum(1 for g in goals if g.status == GoalStatus.AT_RISK)
        failed = sum(1 for g in goals if g.status == GoalStatus.FAILED)
        not_started = sum(1 for g in goals if g.status == GoalStatus.NOT_STARTED)
        in_progress = sum(1 for g in goals if g.status == GoalStatus.IN_PROGRESS)

        blocked = []
        passed = False
        message = ""

        if self.config.mode == GoalGateMode.ALL_MUST_PASS:
            failed_goals = [g for g in goals if g.status == GoalStatus.FAILED]
            if self.config.allow_at_risk:
                passed = len(failed_goals) == 0 and achieved + at_risk == total
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in failed_goals
                ]
            else:
                passed = achieved == total
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in goals
                    if g.status != GoalStatus.ACHIEVED
                ]

            if not passed:
                message = f"Gate failed: {len(blocked)} goal(s) not achieved"

        elif self.config.mode == GoalGateMode.NONE_FAILED:
            passed = failed == 0
            blocked = [
                {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                for g in goals
                if g.status == GoalStatus.FAILED
            ]
            if not passed:
                message = f"Gate failed: {failed} goal(s) failed"

        elif self.config.mode == GoalGateMode.NONE_AT_RISK:
            blocked = [
                {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                for g in goals
                if g.status in [GoalStatus.AT_RISK, GoalStatus.FAILED]
            ]
            passed = len(blocked) == 0
            if not passed:
                message = f"Gate failed: {len(blocked)} goal(s) at risk or failed"

        elif self.config.mode == GoalGateMode.PERCENTAGE_ACHIEVED:
            percentage = (achieved / total * 100) if total > 0 else 0
            passed = percentage >= self.config.min_percentage
            if not passed:
                blocked = [
                    {"goal_id": g.goal_id, "name": g.name, "status": g.status.value}
                    for g in goals
                    if g.status != GoalStatus.ACHIEVED
                ]
                message = f"Gate failed: {percentage:.1f}% goals achieved, required {self.config.min_percentage}%"
            else:
                message = f"Gate passed: {percentage:.1f}% goals achieved"

        if passed and not message:
            message = f"Gate passed: {achieved}/{total} goals achieved"

        return GoalGateResult(
            passed=passed,
            total_goals=total,
            achieved_goals=achieved,
            at_risk_goals=at_risk,
            failed_goals=failed,
            not_started_goals=not_started,
            in_progress_goals=in_progress,
            blocked_goals=blocked,
            message=message,
        )


def create_aware_gate(
    name: str,
    mode: str = "moderate",
    goals_file: Optional[str] = None,
    auto_update: bool = True,
    **kwargs
) -> GoalAwareGatePolicy:
    """
    Create a goal-aware gate policy with automatic goal updates.

    Args:
        name: Name of the gate policy
        mode: Gate mode (strict, moderate, lenient, conservative, balanced)
        goals_file: Path to goals file
        auto_update: Automatically update goals on evaluation
        **kwargs: Additional config options

    Returns:
        GoalAwareGatePolicy instance
    """
    if mode in GOAL_GATE_PRESETS:
        config = GOAL_GATE_PRESETS[mode]
    else:
        mode_enum = GoalGateMode(mode)
        config = GoalGateConfig(
            mode=mode_enum,
            min_percentage=kwargs.get("min_percentage", 0.0),
            allow_at_risk=kwargs.get("allow_at_risk", True),
            goal_categories=kwargs.get("goal_categories"),
            goal_types=kwargs.get("goal_types"),
        )

    return GoalAwareGatePolicy(name, config, goals_file, auto_update)
