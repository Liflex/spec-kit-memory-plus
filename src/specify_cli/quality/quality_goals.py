"""
Quality Goals System

Define, track, and achieve quality goals for your project.

Key features:
- Define quality goals (target scores, pass rates, category targets)
- Track progress towards goals over time
- Generate goal achievement reports
- Integrate with quality loop to validate goals
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from pathlib import Path
from enum import Enum
import json
import re

from .quality_history import QualityHistoryManager, QualityRunRecord, QualityStatistics


class GoalStatus(Enum):
    """Status of a quality goal"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"
    AT_RISK = "at_risk"


class GoalType(Enum):
    """Type of quality goal"""
    TARGET_SCORE = "target_score"  # Achieve minimum average score
    PASS_RATE = "pass_rate"  # Achieve minimum pass rate
    CATEGORY_TARGET = "category_target"  # Achieve minimum score in specific category
    STREAK = "streak"  # Maintain consecutive passed runs
    IMPROVEMENT = "improvement"  # Improve score by percentage
    STABILITY = "stability"  # Keep score variance below threshold


@dataclass
class QualityGoal:
    """Definition of a quality goal"""
    goal_id: str
    name: str
    description: str
    goal_type: GoalType
    target_value: float
    current_value: float
    status: GoalStatus
    created_at: str
    achieved_at: Optional[str] = None
    category: Optional[str] = None  # For category_target goals
    window_size: int = 10  # Number of runs to consider
    threshold_a: Optional[float] = None  # Warning threshold (75% of target)
    deadline: Optional[str] = None  # Optional deadline
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "goal_id": self.goal_id,
            "name": self.name,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "status": self.status.value,
            "created_at": self.created_at,
            "achieved_at": self.achieved_at,
            "category": self.category,
            "window_size": self.window_size,
            "threshold_a": self.threshold_a,
            "deadline": self.deadline,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityGoal":
        """Create from dictionary"""
        return cls(
            goal_id=data["goal_id"],
            name=data["name"],
            description=data["description"],
            goal_type=GoalType(data["goal_type"]),
            target_value=data["target_value"],
            current_value=data["current_value"],
            status=GoalStatus(data["status"]),
            created_at=data["created_at"],
            achieved_at=data.get("achieved_at"),
            category=data.get("category"),
            window_size=data.get("window_size", 10),
            threshold_a=data.get("threshold_a"),
            deadline=data.get("deadline"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GoalProgress:
    """Progress report for a quality goal"""
    goal_id: str
    goal_name: str
    current_value: float
    target_value: float
    progress_percent: float
    status: GoalStatus
    trend: str  # "improving", "declining", "stable"
    recent_values: List[float]
    message: str
    actions: List[str]  # Recommended actions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "goal_id": self.goal_id,
            "goal_name": self.goal_name,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "progress_percent": self.progress_percent,
            "status": self.status.value,
            "trend": self.trend,
            "recent_values": self.recent_values,
            "message": self.message,
            "actions": self.actions,
        }


@dataclass
class GoalSummary:
    """Summary of all quality goals"""
    total_goals: int
    achieved_goals: int
    in_progress_goals: int
    at_risk_goals: int
    failed_goals: int
    overall_progress: float
    top_priority_goal: Optional[str] = None
    most_achieved_goal: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_goals": self.total_goals,
            "achieved_goals": self.achieved_goals,
            "in_progress_goals": self.in_progress_goals,
            "at_risk_goals": self.at_risk_goals,
            "failed_goals": self.failed_goals,
            "overall_progress": self.overall_progress,
            "top_priority_goal": self.top_priority_goal,
            "most_achieved_goal": self.most_achieved_goal,
        }


class QualityGoalsManager:
    """Manages quality goals and tracking"""

    def __init__(self, goals_dir: Optional[Path] = None, history_dir: Optional[Path] = None):
        """Initialize goals manager

        Args:
            goals_dir: Directory to store goal files (default: .speckit/quality-goals)
            history_dir: Directory for quality history (default: .speckit/quality-history)
        """
        if goals_dir is None:
            goals_dir = Path.cwd() / ".speckit" / "quality-goals"

        self.goals_dir = Path(goals_dir)
        self.goals_dir.mkdir(parents=True, exist_ok=True)

        self.history_manager = QualityHistoryManager(history_dir=history_dir)

        # Goals index file
        self.goals_file = self.goals_dir / "goals.json"

    def create_goal(
        self,
        name: str,
        description: str,
        goal_type: GoalType,
        target_value: float,
        category: Optional[str] = None,
        window_size: int = 10,
        threshold_a: Optional[float] = None,
        deadline: Optional[str] = None,
    ) -> QualityGoal:
        """Create a new quality goal

        Args:
            name: Goal name
            description: Goal description
            goal_type: Type of goal
            target_value: Target value to achieve
            category: Category for category_target goals
            window_size: Number of runs to consider
            threshold_a: Warning threshold (default: 75% of target)
            deadline: Optional deadline ISO string

        Returns:
            Created QualityGoal
        """
        goal_id = self._generate_goal_id(name)

        if threshold_a is None:
            threshold_a = target_value * 0.75

        goal = QualityGoal(
            goal_id=goal_id,
            name=name,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            current_value=0.0,
            status=GoalStatus.NOT_STARTED,
            created_at=datetime.now().isoformat(),
            category=category,
            window_size=window_size,
            threshold_a=threshold_a,
            deadline=deadline,
        )

        self._save_goal(goal)
        return goal

    def update_goal_progress(self, goal: QualityGoal) -> GoalProgress:
        """Update goal progress based on current history

        Args:
            goal: Goal to update

        Returns:
            GoalProgress with current status
        """
        records = self.history_manager.load_history(limit=goal.window_size)

        if not records:
            return self._create_empty_progress(goal)

        # Calculate current value based on goal type
        current_value = self._calculate_goal_value(goal, records)

        # Determine status
        status = self._determine_goal_status(goal, current_value, records)

        # Update goal
        goal.current_value = current_value
        goal.status = status

        if status == GoalStatus.ACHIEVED and not goal.achieved_at:
            goal.achieved_at = datetime.now().isoformat()

        self._save_goal(goal)

        # Calculate trend
        recent_values = self._get_recent_values(goal, records)
        trend = self._calculate_trend(recent_values)

        # Generate message and actions
        message, actions = self._generate_goal_message(goal, current_value, trend, records)

        # Calculate progress percent
        progress_percent = min(100, (current_value / goal.target_value) * 100) if goal.target_value > 0 else 0

        return GoalProgress(
            goal_id=goal.goal_id,
            goal_name=goal.name,
            current_value=current_value,
            target_value=goal.target_value,
            progress_percent=progress_percent,
            status=status,
            trend=trend,
            recent_values=recent_values,
            message=message,
            actions=actions,
        )

    def get_all_goals(self) -> List[QualityGoal]:
        """Get all quality goals

        Returns:
            List of all goals
        """
        if not self.goals_file.exists():
            return []

        try:
            data = json.loads(self.goals_file.read_text(encoding="utf-8"))
            return [QualityGoal.from_dict(g) for g in data.get("goals", [])]
        except (json.JSONDecodeError, KeyError):
            return []

    def get_goal(self, goal_id: str) -> Optional[QualityGoal]:
        """Get a specific goal by ID

        Args:
            goal_id: Goal ID

        Returns:
            QualityGoal or None
        """
        goals = self.get_all_goals()
        return next((g for g in goals if g.goal_id == goal_id), None)

    def update_goal(
        self,
        goal_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        target_value: Optional[float] = None,
        category: Optional[str] = None,
        window_size: Optional[int] = None,
        threshold_a: Optional[float] = None,
        deadline: Optional[str] = None,
    ) -> Optional[QualityGoal]:
        """Update an existing goal

        Args:
            goal_id: Goal ID to update
            name: New name
            description: New description
            target_value: New target value
            category: New category
            window_size: New window size
            threshold_a: New warning threshold
            deadline: New deadline

        Returns:
            Updated goal or None if not found
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return None

        if name is not None:
            goal.name = name
        if description is not None:
            goal.description = description
        if target_value is not None:
            goal.target_value = target_value
        if category is not None:
            goal.category = category
        if window_size is not None:
            goal.window_size = window_size
        if threshold_a is not None:
            goal.threshold_a = threshold_a
        if deadline is not None:
            goal.deadline = deadline

        self._save_goal(goal)
        return goal

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal

        Args:
            goal_id: Goal ID to delete

        Returns:
            True if deleted, False if not found
        """
        goals = self.get_all_goals()
        filtered_goals = [g for g in goals if g.goal_id != goal_id]

        if len(filtered_goals) == len(goals):
            return False

        self._save_all_goals(filtered_goals)
        return True

    def get_goal_summary(self) -> Optional[GoalSummary]:
        """Get summary of all goals

        Returns:
            GoalSummary or None if no goals
        """
        goals = self.get_all_goals()
        if not goals:
            return None

        achieved = sum(1 for g in goals if g.status == GoalStatus.ACHIEVED)
        in_progress = sum(1 for g in goals if g.status == GoalStatus.IN_PROGRESS)
        at_risk = sum(1 for g in goals if g.status == GoalStatus.AT_RISK)
        failed = sum(1 for g in goals if g.status == GoalStatus.FAILED)

        total_progress = sum(
            (g.current_value / g.target_value) * 100
            for g in goals
            if g.target_value > 0
        ) / len(goals) if goals else 0

        # Find top priority goal (lowest progress among active goals)
        active_goals = [g for g in goals if g.status not in [GoalStatus.ACHIEVED, GoalStatus.FAILED]]
        top_priority = min(active_goals, key=lambda g: g.progress_ratio()) if active_goals else None

        # Find most achieved goal (highest progress)
        most_achieved = max(goals, key=lambda g: g.progress_ratio()) if goals else None

        return GoalSummary(
            total_goals=len(goals),
            achieved_goals=achieved,
            in_progress_goals=in_progress,
            at_risk_goals=at_risk,
            failed_goals=failed,
            overall_progress=total_progress,
            top_priority_goal=top_priority.name if top_priority else None,
            most_achieved_goal=most_achieved.name if most_achieved else None,
        )

    def check_goals_after_run(self, result: Dict[str, Any], criteria_name: str) -> List[GoalProgress]:
        """Check all goals after a quality run

        Args:
            result: Quality loop result
            criteria_name: Criteria template name used

        Returns:
            List of goal progress updates
        """
        # First save the run to history
        from .quality_history import save_quality_run
        save_quality_run(result, criteria_name)

        # Then update all goals
        goals = self.get_all_goals()
        progress_updates = []

        for goal in goals:
            progress = self.update_goal_progress(goal)
            progress_updates.append(progress)

        return progress_updates

    def _generate_goal_id(self, name: str) -> str:
        """Generate a unique goal ID from name"""
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        counter = 1
        goal_id = base

        while self.get_goal(goal_id):
            goal_id = f"{base}-{counter}"
            counter += 1

        return goal_id

    def _save_goal(self, goal: QualityGoal) -> None:
        """Save a single goal to the goals file"""
        goals = self.get_all_goals()

        # Update or add
        existing_index = next((i for i, g in enumerate(goals) if g.goal_id == goal.goal_id), None)
        if existing_index is not None:
            goals[existing_index] = goal
        else:
            goals.append(goal)

        self._save_all_goals(goals)

    def _save_all_goals(self, goals: List[QualityGoal]) -> None:
        """Save all goals to the goals file"""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "goals": [g.to_dict() for g in goals],
        }

        self.goals_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _calculate_goal_value(self, goal: QualityGoal, records: List[QualityRunRecord]) -> float:
        """Calculate current value for a goal based on records"""
        if not records:
            return 0.0

        records_window = records[:goal.window_size]

        if goal.goal_type == GoalType.TARGET_SCORE:
            # Average score over window
            return sum(r.score for r in records_window) / len(records_window)

        elif goal.goal_type == GoalType.PASS_RATE:
            # Pass rate over window
            passed = sum(1 for r in records_window if r.passed)
            return (passed / len(records_window)) * 100

        elif goal.goal_type == GoalType.CATEGORY_TARGET:
            # Average score in specific category
            if not goal.category:
                return 0.0

            category_scores = []
            for r in records_window:
                if r.category_scores and goal.category in r.category_scores:
                    category_scores.append(r.category_scores[goal.category])

            return sum(category_scores) / len(category_scores) if category_scores else 0.0

        elif goal.goal_type == GoalType.STREAK:
            # Current streak of passed runs
            streak = 0
            for r in records_window:
                if r.passed:
                    streak += 1
                else:
                    break
            return float(streak)

        elif goal.goal_type == GoalType.IMPROVEMENT:
            # Improvement from oldest to newest in window
            if len(records_window) < 2:
                return 0.0

            oldest = records_window[-1].score
            newest = records_window[0].score

            if oldest == 0:
                return 0.0

            improvement = ((newest - oldest) / oldest) * 100
            return max(0, improvement)  # Only positive improvement

        elif goal.goal_type == GoalType.STABILITY:
            # Score variance (lower is more stable)
            scores = [r.score for r in records_window]
            avg = sum(scores) / len(scores)
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)
            return 100 - min(100, variance * 100)  # Convert to stability percentage

        return 0.0

    def _determine_goal_status(
        self,
        goal: QualityGoal,
        current_value: float,
        records: List[QualityRunRecord],
    ) -> GoalStatus:
        """Determine the status of a goal"""
        # Check deadline
        if goal.deadline:
            deadline = datetime.fromisoformat(goal.deadline)
            if datetime.now() > deadline and current_value < goal.target_value:
                return GoalStatus.FAILED

        # Check if achieved
        if current_value >= goal.target_value:
            return GoalStatus.ACHIEVED

        # Check if at risk
        if goal.threshold_a and current_value < goal.threshold_a:
            return GoalStatus.AT_RISK

        # Check if in progress (have some history)
        if records:
            return GoalStatus.IN_PROGRESS

        return GoalStatus.NOT_STARTED

    def _get_recent_values(self, goal: QualityGoal, records: List[QualityRunRecord]) -> List[float]:
        """Get recent values for trend calculation"""
        values = []
        for record in records[:goal.window_size]:
            value = 0.0

            if goal.goal_type == GoalType.TARGET_SCORE:
                value = record.score
            elif goal.goal_type == GoalType.PASS_RATE:
                value = 100.0 if record.passed else 0.0
            elif goal.goal_type == GoalType.CATEGORY_TARGET and goal.category:
                value = record.category_scores.get(goal.category, 0.0) if record.category_scores else 0.0
            elif goal.goal_type == GoalType.STREAK:
                # Streak is cumulative, not per-run
                continue
            elif goal.goal_type == GoalType.IMPROVEMENT:
                # Improvement needs baseline
                continue
            elif goal.goal_type == GoalType.STABILITY:
                value = record.score

            values.append(value)

        return values[-5:]  # Last 5 values

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return "stable"

        if len(values) < 3:
            change = values[0] - values[-1]
            if abs(change) < 0.02:
                return "stable"
            return "improving" if change > 0 else "declining"

        # Use simple linear regression for trend
        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0

        avg_y = sum_y / n
        if abs(slope) < avg_y * 0.01:  # Less than 1% change per step
            return "stable"
        return "improving" if slope > 0 else "declining"

    def _generate_goal_message(
        self,
        goal: QualityGoal,
        current_value: float,
        trend: str,
        records: List[QualityRunRecord],
    ) -> tuple[str, List[str]]:
        """Generate status message and recommended actions"""
        progress = (current_value / goal.target_value) * 100 if goal.target_value > 0 else 0

        # Status message
        if goal.status == GoalStatus.ACHIEVED:
            message = f"Goal achieved! Current: {current_value:.2f}, Target: {goal.target_value:.2f}"
        elif goal.status == GoalStatus.FAILED:
            message = f"Goal failed. Current: {current_value:.2f}, Target: {goal.target_value:.2f}"
        elif goal.status == GoalStatus.AT_RISK:
            message = f"Goal at risk! Current: {current_value:.2f} ({progress:.0f}% of target {goal.target_value:.2f})"
        elif goal.status == GoalStatus.IN_PROGRESS:
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(trend, "")
            message = f"Goal in progress {trend_emoji}. Current: {current_value:.2f} ({progress:.0f}% of target {goal.target_value:.2f})"
        else:
            message = f"Goal not started. Need {goal.target_value:.2f}"

        # Recommended actions
        actions = []

        if goal.status == GoalStatus.FAILED:
            actions.append("Review and adjust goal target")
            actions.append("Analyze failure root causes")

        elif goal.status == GoalStatus.AT_RISK:
            if trend == "declining":
                actions.append("Urgent: Quality is declining - investigate recent changes")
            actions.append("Focus on failing categories")
            actions.append("Review quality gate policies")

        elif goal.status == GoalStatus.IN_PROGRESS:
            if trend == "improving":
                actions.append("Continue current practices")
            elif trend == "declining":
                actions.append("Investigate cause of decline")
            else:
                actions.append("Maintain current approach")

            # Category-specific actions
            if goal.goal_type == GoalType.CATEGORY_TARGET and records:
                latest = records[0]
                if latest.failed_categories and goal.category in latest.failed_categories:
                    actions.append(f"Address failing rules in {goal.category} category")

        elif goal.status == GoalStatus.NOT_STARTED:
            actions.append("Run quality loop to establish baseline")
            actions.append("Review current quality status")

        elif goal.status == GoalStatus.ACHIEVED:
            actions.append("Consider raising the target")
            actions.append("Document practices that led to success")

        return message, actions

    def _create_empty_progress(self, goal: QualityGoal) -> GoalProgress:
        """Create progress for goal with no history"""
        return GoalProgress(
            goal_id=goal.goal_id,
            goal_name=goal.name,
            current_value=0.0,
            target_value=goal.target_value,
            progress_percent=0.0,
            status=GoalStatus.NOT_STARTED,
            trend="stable",
            recent_values=[],
            message="No quality history available. Run quality loop to start tracking.",
            actions=["Run quality loop to establish baseline"],
        )


# Helper to extend QualityGoal with progress_ratio method
def _progress_ratio(goal: QualityGoal) -> float:
    """Calculate progress ratio for a goal"""
    if goal.target_value == 0:
        return 0.0
    return min(1.0, goal.current_value / goal.target_value)


# Monkey patch the method onto QualityGoal
QualityGoal.progress_ratio = _progress_ratio


# Convenience functions for goal creation presets

def create_target_score_goal(
    name: str,
    target_score: float,
    window_size: int = 10,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create a target score goal preset

    Args:
        name: Goal name
        target_score: Target average score (0-1)
        window_size: Number of runs to average
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Achieve an average quality score of {target_score:.2f} over {window_size} runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.TARGET_SCORE,
        target_value=target_score,
        window_size=window_size,
    )


def create_pass_rate_goal(
    name: str,
    target_pass_rate: float,
    window_size: int = 10,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create a pass rate goal preset

    Args:
        name: Goal name
        target_pass_rate: Target pass rate percentage (0-100)
        window_size: Number of runs to consider
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Achieve a {target_pass_rate:.0f}% pass rate over {window_size} runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.PASS_RATE,
        target_value=target_pass_rate,
        window_size=window_size,
    )


def create_category_goal(
    name: str,
    category: str,
    target_score: float,
    window_size: int = 10,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create a category target goal preset

    Args:
        name: Goal name
        category: Category name
        target_score: Target score for category (0-1)
        window_size: Number of runs to average
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Achieve {target_score:.2f} average score in {category} over {window_size} runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.CATEGORY_TARGET,
        target_value=target_score,
        category=category,
        window_size=window_size,
    )


def create_streak_goal(
    name: str,
    target_streak: int,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create a streak goal preset

    Args:
        name: Goal name
        target_streak: Target consecutive passed runs
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Maintain {target_streak} consecutive passed quality runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.STREAK,
        target_value=float(target_streak),
        window_size=target_streak * 2,  # Look back enough for the streak
    )


def create_improvement_goal(
    name: str,
    target_improvement: float,
    window_size: int = 10,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create an improvement goal preset

    Args:
        name: Goal name
        target_improvement: Target improvement percentage (0-100)
        window_size: Number of runs to measure improvement over
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Improve quality score by {target_improvement:.0f}% over {window_size} runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.IMPROVEMENT,
        target_value=target_improvement,
        window_size=window_size,
    )


def create_stability_goal(
    name: str,
    target_stability: float,
    window_size: int = 10,
    description: Optional[str] = None,
) -> QualityGoal:
    """Create a stability goal preset

    Args:
        name: Goal name
        target_stability: Target stability score (0-100, higher is more stable)
        window_size: Number of runs to measure variance
        description: Optional description

    Returns:
        Created QualityGoal
    """
    manager = QualityGoalsManager()
    if description is None:
        description = f"Maintain {target_stability:.0f}% score stability over {window_size} runs"

    return manager.create_goal(
        name=name,
        description=description,
        goal_type=GoalType.STABILITY,
        target_value=target_stability,
        window_size=window_size,
    )


# Goal Presets System

class GoalPreset(Enum):
    """Pre-configured goal sets for common scenarios"""
    PRODUCTION_READY = "production_ready"
    CI_GATE = "ci_gate"
    SECURITY_FOCUSED = "security_focused"
    QUICK_START = "quick_start"
    STABILITY = "stability"
    COMPREHENSIVE = "comprehensive"


# Preset definitions with goal configurations
GOAL_PRESETS: Dict[GoalPreset, Dict[str, Any]] = {
    GoalPreset.PRODUCTION_READY: {
        "name": "Production Ready",
        "description": "High quality standards for production deployment",
        "goals": [
            {
                "name": "Production Score Target",
                "description": "Maintain 0.9+ average quality score for production",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.9,
                "window_size": 10,
            },
            {
                "name": "Production Pass Rate",
                "description": "Achieve 95% pass rate across all quality runs",
                "goal_type": GoalType.PASS_RATE,
                "target_value": 95.0,
                "window_size": 20,
            },
            {
                "name": "Production Stability",
                "description": "Maintain consistent quality scores",
                "goal_type": GoalType.STABILITY,
                "target_value": 85.0,
                "window_size": 15,
            },
        ],
    },

    GoalPreset.CI_GATE: {
        "name": "CI Gate",
        "description": "Quality gates for CI/CD pipeline",
        "goals": [
            {
                "name": "CI Pass Rate",
                "description": "Minimum pass rate for CI acceptance",
                "goal_type": GoalType.PASS_RATE,
                "target_value": 80.0,
                "window_size": 10,
            },
            {
                "name": "CI Quality Baseline",
                "description": "Minimum acceptable quality score",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.75,
                "window_size": 5,
            },
            {
                "name": "CI Build Streak",
                "description": "Consecutive passing CI builds",
                "goal_type": GoalType.STREAK,
                "target_value": 5.0,
                "window_size": 10,
            },
        ],
    },

    GoalPreset.SECURITY_FOCUSED: {
        "name": "Security Focused",
        "description": "Security quality targets for security-critical projects",
        "goals": [
            {
                "name": "Security Excellence",
                "description": "High security category scores",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.95,
                "category": "security",
                "window_size": 10,
            },
            {
                "name": "Security Consistency",
                "description": "Stable security quality over time",
                "goal_type": GoalType.STABILITY,
                "target_value": 90.0,
                "window_size": 15,
            },
            {
                "name": "Quality Standard",
                "description": "Overall quality baseline for security projects",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.8,
                "window_size": 10,
            },
        ],
    },

    GoalPreset.QUICK_START: {
        "name": "Quick Start",
        "description": "Easy-to-achieve goals for getting started",
        "goals": [
            {
                "name": "Initial Quality Target",
                "description": "Achieve baseline quality score",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.75,
                "window_size": 5,
            },
            {
                "name": "Initial Pass Rate",
                "description": "Establish consistent passing runs",
                "goal_type": GoalType.PASS_RATE,
                "target_value": 70.0,
                "window_size": 10,
            },
        ],
    },

    GoalPreset.STABILITY: {
        "name": "Stability",
        "description": "Focus on score consistency and predictability",
        "goals": [
            {
                "name": "Score Stability",
                "description": "Maintain consistent quality scores",
                "goal_type": GoalType.STABILITY,
                "target_value": 90.0,
                "window_size": 20,
            },
            {
                "name": "Passing Streak",
                "description": "Maintain consecutive passed runs",
                "goal_type": GoalType.STREAK,
                "target_value": 10.0,
                "window_size": 20,
            },
            {
                "name": "Baseline Quality",
                "description": "Minimum acceptable score",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.8,
                "window_size": 15,
            },
        ],
    },

    GoalPreset.COMPREHENSIVE: {
        "name": "Comprehensive",
        "description": "Complete quality coverage across all dimensions",
        "goals": [
            {
                "name": "Overall Score Target",
                "description": "High overall quality score",
                "goal_type": GoalType.TARGET_SCORE,
                "target_value": 0.85,
                "window_size": 10,
            },
            {
                "name": "High Pass Rate",
                "description": "Consistent passing quality runs",
                "goal_type": GoalType.PASS_RATE,
                "target_value": 90.0,
                "window_size": 20,
            },
            {
                "name": "Quality Stability",
                "description": "Stable quality over time",
                "goal_type": GoalType.STABILITY,
                "target_value": 85.0,
                "window_size": 15,
            },
            {
                "name": "Consecutive Passing",
                "description": "Maintain passing streak",
                "goal_type": GoalType.STREAK,
                "target_value": 7.0,
                "window_size": 15,
            },
            {
                "name": "Security Standard",
                "description": "Security category target",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "security",
                "window_size": 10,
            },
            {
                "name": "Continuous Improvement",
                "description": "Improve quality over time",
                "goal_type": GoalType.IMPROVEMENT,
                "target_value": 10.0,
                "window_size": 20,
            },
        ],
    },
}


def apply_preset(preset: GoalPreset, manager: Optional[QualityGoalsManager] = None) -> List[QualityGoal]:
    """Apply a goal preset, creating all goals in the preset

    Args:
        preset: Preset to apply
        manager: GoalsManager instance (creates new if None)

    Returns:
        List of created QualityGoal objects
    """
    if manager is None:
        manager = QualityGoalsManager()

    preset_config = GOAL_PRESETS.get(preset)
    if not preset_config:
        raise ValueError(f"Unknown preset: {preset}")

    created_goals = []
    for goal_config in preset_config["goals"]:
        goal = manager.create_goal(
            name=goal_config["name"],
            description=goal_config["description"],
            goal_type=goal_config["goal_type"],
            target_value=goal_config["target_value"],
            category=goal_config.get("category"),
            window_size=goal_config.get("window_size", 10),
        )
        created_goals.append(goal)

    return created_goals


def list_presets() -> Dict[str, Dict[str, Any]]:
    """List all available goal presets with their configurations

    Returns:
        Dict mapping preset names to their configurations
    """
    return {
        preset.value: {
            "name": config["name"],
            "description": config["description"],
            "goal_count": len(config["goals"]),
            "goals": [
                {
                    "type": g["goal_type"].value,
                    "target": g["target_value"],
                    "category": g.get("category"),
                }
                for g in config["goals"]
            ],
        }
        for preset, config in GOAL_PRESETS.items()
    }


def get_preset_info(preset: GoalPreset) -> Dict[str, Any]:
    """Get detailed information about a specific preset

    Args:
        preset: Preset to get info for

    Returns:
        Dict with preset details
    """
    config = GOAL_PRESETS.get(preset)
    if not config:
        raise ValueError(f"Unknown preset: {preset}")

    return {
        "id": preset.value,
        "name": config["name"],
        "description": config["description"],
        "goals": config["goals"],
    }


def recommend_preset(
    current_score: Optional[float] = None,
    current_pass_rate: Optional[float] = None,
    project_type: str = "general",
    strictness: str = "standard",  # strict, standard, relaxed
) -> GoalPreset:
    """Recommend a goal preset based on current state and preferences

    Args:
        current_score: Current quality score (0-1)
        current_pass_rate: Current pass rate (0-100)
        project_type: Type of project (general, security, ci, production)
        strictness: Quality strictness level

    Returns:
        Recommended GoalPreset
    """
    # Security-focused projects
    if project_type == "security":
        return GoalPreset.SECURITY_FOCUSED

    # CI/CD focus
    if project_type == "ci":
        return GoalPreset.CI_GATE

    # Production requirements
    if project_type == "production":
        return GoalPreset.PRODUCTION_READY

    # Based on current quality state
    if current_score is not None and current_score < 0.7:
        return GoalPreset.QUICK_START

    if current_pass_rate is not None and current_pass_rate < 70:
        return GoalPreset.QUICK_START

    # Based on strictness
    if strictness == "strict":
        return GoalPreset.COMPREHENSIVE
    elif strictness == "relaxed":
        return GoalPreset.QUICK_START

    # Default recommendation
    return GoalPreset.STABILITY


# ============================================================================
# Category-Specific Goal Templates (Exp 66)
# ============================================================================

CATEGORY_GOAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "security": {
        "name": "Security Quality Goals",
        "description": "Goals for maintaining high security standards",
        "goals": [
            {
                "name": "Security Score Target",
                "description": "Maintain 0.85+ security category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "security",
                "window_size": 10,
            },
            {
                "name": "Security Consistency",
                "description": "Keep security quality stable (85%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 85.0,
                "category": "security",
                "window_size": 15,
            },
            {
                "name": "Zero Security Failures",
                "description": "Maintain streak of passed security checks",
                "goal_type": GoalType.STREAK,
                "target_value": 10.0,
                "category": "security",
                "window_size": 10,
            },
        ],
    },

    "performance": {
        "name": "Performance Quality Goals",
        "description": "Goals for maintaining high performance standards",
        "goals": [
            {
                "name": "Performance Score Target",
                "description": "Maintain 0.80+ performance category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.80,
                "category": "performance",
                "window_size": 10,
            },
            {
                "name": "Performance Consistency",
                "description": "Keep performance quality stable (80%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 80.0,
                "category": "performance",
                "window_size": 15,
            },
            {
                "name": "Performance Improvement",
                "description": "Improve performance by 10% over time",
                "goal_type": GoalType.IMPROVEMENT,
                "target_value": 10.0,
                "category": "performance",
                "window_size": 20,
            },
        ],
    },

    "testing": {
        "name": "Testing Quality Goals",
        "description": "Goals for comprehensive test coverage and quality",
        "goals": [
            {
                "name": "Test Coverage Target",
                "description": "Maintain 0.85+ testing category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "testing",
                "window_size": 10,
            },
            {
                "name": "Test Consistency",
                "description": "Keep testing quality stable (80%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 80.0,
                "category": "testing",
                "window_size": 15,
            },
            {
                "name": "Passing Test Streak",
                "description": "Maintain consecutive passing test runs",
                "goal_type": GoalType.STREAK,
                "target_value": 7.0,
                "category": "testing",
                "window_size": 15,
            },
        ],
    },

    "documentation": {
        "name": "Documentation Quality Goals",
        "description": "Goals for maintaining high documentation standards",
        "goals": [
            {
                "name": "Documentation Score Target",
                "description": "Maintain 0.80+ documentation category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.80,
                "category": "documentation",
                "window_size": 10,
            },
            {
                "name": "Documentation Consistency",
                "description": "Keep documentation quality stable (75%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 75.0,
                "category": "documentation",
                "window_size": 15,
            },
        ],
    },

    "code_quality": {
        "name": "Code Quality Goals",
        "description": "Goals for maintaining high code quality standards",
        "goals": [
            {
                "name": "Code Quality Target",
                "description": "Maintain 0.85+ code quality score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "code_quality",
                "window_size": 10,
            },
            {
                "name": "Code Quality Consistency",
                "description": "Keep code quality stable (80%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 80.0,
                "category": "code_quality",
                "window_size": 15,
            },
            {
                "name": "Code Improvement",
                "description": "Improve code quality by 5% over time",
                "goal_type": GoalType.IMPROVEMENT,
                "target_value": 5.0,
                "category": "code_quality",
                "window_size": 20,
            },
        ],
    },

    "infrastructure": {
        "name": "Infrastructure Quality Goals",
        "description": "Goals for maintaining high infrastructure standards",
        "goals": [
            {
                "name": "Infrastructure Score Target",
                "description": "Maintain 0.80+ infrastructure category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.80,
                "category": "infrastructure",
                "window_size": 10,
            },
            {
                "name": "Infrastructure Consistency",
                "description": "Keep infrastructure quality stable (80%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 80.0,
                "category": "infrastructure",
                "window_size": 15,
            },
        ],
    },

    "observability": {
        "name": "Observability Quality Goals",
        "description": "Goals for maintaining high observability standards",
        "goals": [
            {
                "name": "Observability Score Target",
                "description": "Maintain 0.80+ observability category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.80,
                "category": "observability",
                "window_size": 10,
            },
            {
                "name": "Monitoring Coverage",
                "description": "Keep observability quality stable (75%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 75.0,
                "category": "observability",
                "window_size": 15,
            },
        ],
    },

    "reliability": {
        "name": "Reliability Quality Goals",
        "description": "Goals for maintaining high reliability standards",
        "goals": [
            {
                "name": "Reliability Score Target",
                "description": "Maintain 0.85+ reliability category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "reliability",
                "window_size": 10,
            },
            {
                "name": "Reliability Consistency",
                "description": "Keep reliability quality stable (85%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 85.0,
                "category": "reliability",
                "window_size": 15,
            },
            {
                "name": "Reliable Operations Streak",
                "description": "Maintain consecutive passed reliability checks",
                "goal_type": GoalType.STREAK,
                "target_value": 10.0,
                "category": "reliability",
                "window_size": 10,
            },
        ],
    },

    "cicd": {
        "name": "CI/CD Quality Goals",
        "description": "Goals for maintaining high CI/CD pipeline quality",
        "goals": [
            {
                "name": "CI/CD Score Target",
                "description": "Maintain 0.85+ CI/CD category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "cicd",
                "window_size": 10,
            },
            {
                "name": "Pipeline Consistency",
                "description": "Keep CI/CD quality stable (85%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 85.0,
                "category": "cicd",
                "window_size": 15,
            },
            {
                "name": "Passing Pipeline Streak",
                "description": "Maintain consecutive passed pipeline runs",
                "goal_type": GoalType.STREAK,
                "target_value": 5.0,
                "category": "cicd",
                "window_size": 10,
            },
        ],
    },

    "correctness": {
        "name": "Correctness Quality Goals",
        "description": "Goals for maintaining high correctness standards",
        "goals": [
            {
                "name": "Correctness Score Target",
                "description": "Maintain 0.90+ correctness category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.90,
                "category": "correctness",
                "window_size": 10,
            },
            {
                "name": "Correctness Consistency",
                "description": "Keep correctness quality stable (90%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 90.0,
                "category": "correctness",
                "window_size": 15,
            },
        ],
    },

    "accessibility": {
        "name": "Accessibility Quality Goals",
        "description": "Goals for maintaining high accessibility standards",
        "goals": [
            {
                "name": "Accessibility Score Target",
                "description": "Maintain 0.85+ accessibility category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.85,
                "category": "accessibility",
                "window_size": 10,
            },
            {
                "name": "Accessibility Consistency",
                "description": "Keep accessibility quality stable (80%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 80.0,
                "category": "accessibility",
                "window_size": 15,
            },
        ],
    },

    "ux_quality": {
        "name": "UX Quality Goals",
        "description": "Goals for maintaining high UX quality standards",
        "goals": [
            {
                "name": "UX Score Target",
                "description": "Maintain 0.80+ UX quality category score",
                "goal_type": GoalType.CATEGORY_TARGET,
                "target_value": 0.80,
                "category": "ux_quality",
                "window_size": 10,
            },
            {
                "name": "UX Consistency",
                "description": "Keep UX quality stable (75%+)",
                "goal_type": GoalType.STABILITY,
                "target_value": 75.0,
                "category": "ux_quality",
                "window_size": 15,
            },
        ],
    },
}


def apply_category_template(
    category: str,
    manager: Optional[QualityGoalsManager] = None,
) -> List[QualityGoal]:
    """Apply a category-specific goal template, creating all goals in the template

    Args:
        category: Category to apply goals for (e.g., 'security', 'performance', 'testing')
        manager: GoalsManager instance (creates new if None)

    Returns:
        List of created QualityGoal objects

    Raises:
        ValueError: If category is not found in templates
    """
    if manager is None:
        manager = QualityGoalsManager()

    category_lower = category.lower()
    template_config = CATEGORY_GOAL_TEMPLATES.get(category_lower)

    if not template_config:
        available = ", ".join(CATEGORY_GOAL_TEMPLATES.keys())
        raise ValueError(
            f"Unknown category: {category}. Available categories: {available}"
        )

    created_goals = []
    for goal_config in template_config["goals"]:
        goal = manager.create_goal(
            name=goal_config["name"],
            description=goal_config["description"],
            goal_type=goal_config["goal_type"],
            target_value=goal_config["target_value"],
            category=goal_config.get("category"),
            window_size=goal_config.get("window_size", 10),
        )
        created_goals.append(goal)

    return created_goals


def list_category_templates() -> Dict[str, Dict[str, Any]]:
    """List all available category goal templates with their configurations

    Returns:
        Dict mapping category names to their template configurations
    """
    return {
        category: {
            "name": config["name"],
            "description": config["description"],
            "goal_count": len(config["goals"]),
            "goals": [
                {
                    "type": g["goal_type"].value,
                    "target": g["target_value"],
                    "category": g.get("category"),
                }
                for g in config["goals"]
            ],
        }
        for category, config in CATEGORY_GOAL_TEMPLATES.items()
    }


def get_category_template_info(category: str) -> Dict[str, Any]:
    """Get detailed information about a specific category template

    Args:
        category: Category to get info for

    Returns:
        Dict with category template details

    Raises:
        ValueError: If category is not found
    """
    category_lower = category.lower()
    config = CATEGORY_GOAL_TEMPLATES.get(category_lower)

    if not config:
        available = ", ".join(CATEGORY_GOAL_TEMPLATES.keys())
        raise ValueError(
            f"Unknown category: {category}. Available categories: {available}"
        )

    return {
        "id": category_lower,
        "name": config["name"],
        "description": config["description"],
        "goals": config["goals"],
    }


def recommend_category_template(
    current_scores: Optional[Dict[str, float]] = None,
    project_type: str = "general",
    focus_area: Optional[str] = None,
) -> str:
    """Recommend a category goal template based on current state and preferences

    Args:
        current_scores: Dict mapping categories to their current scores (0-1)
        project_type: Type of project (general, security, performance, testing)
        focus_area: Specific category to focus on (overrides recommendation)

    Returns:
        Recommended category name

    Examples:
        >>> recommend_category_template(project_type="security")
        'security'

        >>> recommend_category_template(
        ...     current_scores={"security": 0.6, "performance": 0.9}
        ... )
        'security'  # Recommends improving the weakest area

        >>> recommend_category_template(focus_area="testing")
        'testing'  # User explicitly chose focus area
    """
    # Explicit focus area takes precedence
    if focus_area:
        focus_lower = focus_area.lower()
        if focus_lower in CATEGORY_GOAL_TEMPLATES:
            return focus_lower

    # Project type recommendations
    project_type_lower = project_type.lower()

    project_type_mapping = {
        "security": "security",
        "performance": "performance",
        "testing": "testing",
        "docs": "documentation",
        "documentation": "documentation",
        "infra": "infrastructure",
        "infrastructure": "infrastructure",
        "observability": "observability",
        "reliability": "reliability",
        "cicd": "cicd",
        "ci/cd": "cicd",
        "correctness": "correctness",
        "accessibility": "accessibility",
        "ux": "ux_quality",
        "ui": "ux_quality",
    }

    if project_type_lower in project_type_mapping:
        return project_type_mapping[project_type_lower]

    # Analyze current scores to find weakest area
    if current_scores:
        # Filter to categories that have templates
        valid_scores = {
            cat: score
            for cat, score in current_scores.items()
            if cat.lower() in CATEGORY_GOAL_TEMPLATES
        }

        if valid_scores:
            # Find category with lowest score (most room for improvement)
            weakest_category = min(valid_scores, key=valid_scores.get)
            weakest_score = valid_scores[weakest_category]

            # Only recommend if score is below threshold
            if weakest_score < 0.8:
                return weakest_category

    # Default to code quality for general projects
    return "code_quality"


# Formatting functions

def format_goal_progress(progress: GoalProgress) -> str:
    """Format goal progress as text report

    Args:
        progress: GoalProgress to format

    Returns:
        Formatted report string
    """
    status_emoji = {
        GoalStatus.NOT_STARTED: "⏳",
        GoalStatus.IN_PROGRESS: "🔄",
        GoalStatus.ACHIEVED: "✅",
        GoalStatus.FAILED: "❌",
        GoalStatus.AT_RISK: "⚠️",
    }

    trend_emoji = {
        "improving": "📈",
        "declining": "📉",
        "stable": "➡️",
    }

    lines = []
    lines.append(f"## {progress.goal_name}")
    lines.append("")
    lines.append(f"**Status:** {status_emoji.get(progress.status, '')} {progress.status.value.upper().replace('_', ' ')}")
    lines.append(f"**Trend:** {trend_emoji.get(progress.trend, '')} {progress.trend.upper()}")
    lines.append("")
    lines.append(f"**Progress:** {progress.current_value:.2f} / {progress.target_value:.2f} ({progress.progress_percent:.0f}%)")
    lines.append("")
    lines.append(f"**Message:** {progress.message}")
    lines.append("")

    if progress.recent_values:
        lines.append(f"**Recent Values:** {', '.join(f'{v:.2f}' for v in progress.recent_values)}")
        lines.append("")

    if progress.actions:
        lines.append("**Recommended Actions:**")
        for action in progress.actions:
            lines.append(f"- {action}")
        lines.append("")

    return "\n".join(lines)


def format_goals_summary(summary: GoalSummary) -> str:
    """Format goals summary as text report

    Args:
        summary: GoalSummary to format

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("## Quality Goals Summary")
    lines.append("")

    lines.append(f"**Total Goals:** {summary.total_goals}")
    lines.append(f"**Achieved:** ✅ {summary.achieved_goals}")
    lines.append(f"**In Progress:** 🔄 {summary.in_progress_goals}")
    lines.append(f"**At Risk:** ⚠️ {summary.at_risk_goals}")
    lines.append(f"**Failed:** ❌ {summary.failed_goals}")
    lines.append("")

    lines.append(f"**Overall Progress:** {summary.overall_progress:.0f}%")
    lines.append("")

    if summary.top_priority_goal:
        lines.append(f"**Top Priority:** {summary.top_priority_goal}")
    if summary.most_achieved_goal:
        lines.append(f"**Best Progress:** {summary.most_achieved_goal}")

    return "\n".join(lines)


# Export/Import functions

def export_goals(
    manager: Optional[QualityGoalsManager] = None,
    format: str = "json",
    output_file: Optional[Path] = None,
) -> str:
    """Export all goals to a portable format

    Args:
        manager: GoalsManager instance (creates new if None)
        format: Export format ('json' or 'yaml')
        output_file: Optional file to write to (returns string if None)

    Returns:
        Exported data as string
    """
    if manager is None:
        manager = QualityGoalsManager()

    goals = manager.get_all_goals()

    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "goals": [g.to_dict() for g in goals],
    }

    if format.lower() == "yaml":
        try:
            import yaml
            output = yaml.dump(data, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback to JSON if yaml not available
            output = json.dumps(data, indent=2)
    else:
        output = json.dumps(data, indent=2)

    if output_file:
        output_file = Path(output_file)
        output_file.write_text(output, encoding="utf-8")

    return output


def import_goals(
    input_data: str,
    manager: Optional[QualityGoalsManager] = None,
    merge: bool = False,
) -> List[QualityGoal]:
    """Import goals from exported data

    Args:
        input_data: JSON or YAML string with goal data
        manager: GoalsManager instance (creates new if None)
        merge: If True, merge with existing goals; if False, replace all

    Returns:
        List of imported QualityGoal objects
    """
    if manager is None:
        manager = QualityGoalsManager()

    # Try parsing as JSON first
    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        # Try YAML
        try:
            import yaml
            data = yaml.safe_load(input_data)
        except ImportError:
            raise ValueError("Input is not valid JSON and YAML library not available")
        except yaml.YAMLError:
            raise ValueError("Input is not valid JSON or YAML")

    if "goals" not in data:
        raise ValueError("Invalid goal data: missing 'goals' field")

    if not merge:
        # Clear existing goals
        manager._save_all_goals([])

    imported_goals = []
    for goal_data in data["goals"]:
        goal = QualityGoal.from_dict(goal_data)
        manager._save_goal(goal)
        imported_goals.append(goal)

    return imported_goals


def export_goals_as_dict(
    manager: Optional[QualityGoalsManager] = None,
) -> Dict[str, Any]:
    """Export goals as a dictionary for JSON output

    Args:
        manager: GoalsManager instance

    Returns:
        Dict with goal data
    """
    if manager is None:
        manager = QualityGoalsManager()

    goals = manager.get_all_goals()
    summary = manager.get_goal_summary()

    return {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "summary": summary.to_dict() if summary else None,
        "goals": [g.to_dict() for g in goals],
    }


def export_progress_as_dict(
    manager: Optional[QualityGoalsManager] = None,
) -> Dict[str, Any]:
    """Export goal progress as a dictionary for JSON output

    Args:
        manager: GoalsManager instance

    Returns:
        Dict with progress data
    """
    if manager is None:
        manager = QualityGoalsManager()

    goals = manager.get_all_goals()

    progress_list = []
    for goal in goals:
        progress = manager.update_goal_progress(goal)
        progress_list.append(progress.to_dict())

    summary = manager.get_goal_summary()

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": summary.to_dict() if summary else None,
        "progress": progress_list,
    }
