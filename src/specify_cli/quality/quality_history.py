"""
Quality History Tracking

Tracks quality runs over time to identify trends, measure improvement,
and provide data-driven insights for quality optimization.

Key features:
- Save and load quality run records
- Calculate trends and statistics
- Compare runs over time
- Export history for external analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
import json
import re


@dataclass
class QualityRunRecord:
    """Record of a single quality run"""
    run_id: str
    task_alias: str
    timestamp: str
    score: float
    passed: bool
    phase: str
    stop_reason: str
    iteration: int
    max_iterations: int
    priority_profile: Optional[str] = None
    cascade_strategy: Optional[str] = None
    criteria_name: Optional[str] = None
    category_scores: Optional[Dict[str, float]] = None
    severity_counts: Optional[Dict[str, int]] = None
    gate_policy: Optional[str] = None
    gate_passed: Optional[bool] = None
    failed_categories: Optional[List[str]] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "task_alias": self.task_alias,
            "timestamp": self.timestamp,
            "score": self.score,
            "passed": self.passed,
            "phase": self.phase,
            "stop_reason": self.stop_reason,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "priority_profile": self.priority_profile,
            "cascade_strategy": self.cascade_strategy,
            "criteria_name": self.criteria_name,
            "category_scores": self.category_scores,
            "severity_counts": self.severity_counts,
            "gate_policy": self.gate_policy,
            "gate_passed": self.gate_passed,
            "failed_categories": self.failed_categories,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityRunRecord":
        """Create from dictionary"""
        return cls(
            run_id=data["run_id"],
            task_alias=data["task_alias"],
            timestamp=data["timestamp"],
            score=data["score"],
            passed=data["passed"],
            phase=data["phase"],
            stop_reason=data["stop_reason"],
            iteration=data["iteration"],
            max_iterations=data["max_iterations"],
            priority_profile=data.get("priority_profile"),
            cascade_strategy=data.get("cascade_strategy"),
            criteria_name=data.get("criteria_name"),
            category_scores=data.get("category_scores"),
            severity_counts=data.get("severity_counts"),
            gate_policy=data.get("gate_policy"),
            gate_passed=data.get("gate_passed"),
            failed_categories=data.get("failed_categories"),
            duration_seconds=data.get("duration_seconds"),
        )

    @classmethod
    def from_loop_result(cls, result: Dict[str, Any], criteria_name: str, duration_seconds: Optional[float] = None) -> "QualityRunRecord":
        """Create record from loop result"""
        state = result.get("state", {})

        # Extract category scores
        category_scores = None
        if state.get("evaluation", {}).get("category_scores"):
            category_scores = {
                cat: data.get("score", 0.0)
                for cat, data in state["evaluation"]["category_scores"].items()
            }

        # Extract severity counts
        severity_counts = None
        if state.get("evaluation", {}).get("severity_counts"):
            severity_counts = state["evaluation"]["severity_counts"]

        # Extract failed categories
        failed_categories = None
        if state.get("evaluation", {}).get("failed_rules"):
            failed_categories = list(set(
                r.get("category", "general")
                for r in state["evaluation"]["failed_rules"]
            ))

        # Extract gate policy info
        gate_policy = None
        gate_passed = None
        if result.get("gate_result"):
            gate_policy = result["gate_result"].get("policy_name")
            gate_passed = result["gate_result"].get("passed")

        return cls(
            run_id=state.get("run_id", ""),
            task_alias=state.get("task_alias", result.get("task_alias", "")),
            timestamp=state.get("started_at", datetime.now().isoformat()),
            score=result.get("score", 0.0),
            passed=result.get("passed", False),
            phase=state.get("phase", "A"),
            stop_reason=result.get("stop_reason", ""),
            iteration=state.get("iteration", 1),
            max_iterations=state.get("max_iterations", 4),
            priority_profile=result.get("priority_profile"),
            cascade_strategy=result.get("cascade_strategy"),
            criteria_name=criteria_name,
            category_scores=category_scores,
            severity_counts=severity_counts,
            gate_policy=gate_policy,
            gate_passed=gate_passed,
            failed_categories=failed_categories,
            duration_seconds=duration_seconds,
        )


@dataclass
class QualityStatistics:
    """Statistics for quality runs"""
    total_runs: int
    passed_runs: int
    failed_runs: int
    pass_rate: float
    avg_score: float
    min_score: float
    max_score: float
    avg_iterations: float
    most_failed_category: Optional[str] = None
    most_used_profile: Optional[str] = None
    most_used_criteria: Optional[str] = None


@dataclass
class QualityTrend:
    """Trend analysis for quality runs"""
    direction: str  # "improving", "declining", "stable"
    score_change: float  # Change in score from first to last
    score_change_percent: float  # Percentage change
    trend_description: str
    recent_avg: float  # Average of last 5 runs
    overall_avg: float  # Average of all runs
    category_trends: Optional[Dict[str, str]] = None  # Category -> trend direction


@dataclass
class RunComparison:
    """Comparison between two runs"""
    run1_id: str
    run2_id: str
    score_delta: float
    score_delta_percent: float
    score_improved: bool
    iteration_delta: int
    iteration_improved: bool
    category_deltas: Optional[Dict[str, float]] = None
    passed_comparison: Optional[str] = None  # "both_passed", "both_failed", "now_passed", "now_failed"
    gate_comparison: Optional[str] = None


class QualityHistoryManager:
    """Manages quality run history"""

    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize history manager

        Args:
            history_dir: Directory to store history files (default: .speckit/quality-history)
        """
        if history_dir is None:
            history_dir = Path.cwd() / ".speckit" / "quality-history"

        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Master history index file
        self.index_file = self.history_dir / "index.jsonl"

    def save_run(self, record: QualityRunRecord) -> str:
        """Save a quality run record

        Args:
            record: Quality run record to save

        Returns:
            Path to saved file
        """
        # Append to index (JSONL format - one JSON per line)
        with open(self.index_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

        # Also save individual run file for easy access
        run_file = self.history_dir / f"{record.run_id}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

        return str(run_file)

    def load_history(self, task_alias: Optional[str] = None, limit: Optional[int] = None) -> List[QualityRunRecord]:
        """Load quality run history

        Args:
            task_alias: Optional task alias to filter by
            limit: Maximum number of records to load (most recent first)

        Returns:
            List of quality run records (sorted by timestamp descending)
        """
        if not self.index_file.exists():
            return []

        records = []
        with open(self.index_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    record = QualityRunRecord.from_dict(data)

                    # Filter by task alias if specified
                    if task_alias is None or record.task_alias == task_alias:
                        records.append(record)
                except (json.JSONDecodeError, KeyError):
                    continue

        # Sort by timestamp (most recent first)
        records.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply limit
        if limit is not None:
            records = records[:limit]

        return records

    def get_statistics(self, task_alias: Optional[str] = None) -> Optional[QualityStatistics]:
        """Calculate statistics for quality runs

        Args:
            task_alias: Optional task alias to filter by

        Returns:
            QualityStatistics or None if no history
        """
        records = self.load_history(task_alias=task_alias)

        if not records:
            return None

        total_runs = len(records)
        passed_runs = sum(1 for r in records if r.passed)
        failed_runs = total_runs - passed_runs
        pass_rate = passed_runs / total_runs if total_runs > 0 else 0.0

        scores = [r.score for r in records]
        avg_score = sum(scores) / total_runs
        min_score = min(scores)
        max_score = max(scores)

        avg_iterations = sum(r.iteration for r in records) / total_runs

        # Find most failed category
        category_fail_counts: Dict[str, int] = {}
        for r in records:
            if r.failed_categories:
                for cat in r.failed_categories:
                    category_fail_counts[cat] = category_fail_counts.get(cat, 0) + 1

        most_failed_category = max(category_fail_counts, key=category_fail_counts.get) if category_fail_counts else None

        # Find most used profile
        profile_counts: Dict[str, int] = {}
        for r in records:
            if r.priority_profile:
                profile_counts[r.priority_profile] = profile_counts.get(r.priority_profile, 0) + 1

        most_used_profile = max(profile_counts, key=profile_counts.get) if profile_counts else None

        # Find most used criteria
        criteria_counts: Dict[str, int] = {}
        for r in records:
            if r.criteria_name:
                criteria_counts[r.criteria_name] = criteria_counts.get(r.criteria_name, 0) + 1

        most_used_criteria = max(criteria_counts, key=criteria_counts.get) if criteria_counts else None

        return QualityStatistics(
            total_runs=total_runs,
            passed_runs=passed_runs,
            failed_runs=failed_runs,
            pass_rate=pass_rate,
            avg_score=avg_score,
            min_score=min_score,
            max_score=max_score,
            avg_iterations=avg_iterations,
            most_failed_category=most_failed_category,
            most_used_profile=most_used_profile,
            most_used_criteria=most_used_criteria,
        )

    def get_trends(self, task_alias: Optional[str] = None, min_runs: int = 3) -> Optional[QualityTrend]:
        """Calculate trends for quality runs

        Args:
            task_alias: Optional task alias to filter by
            min_runs: Minimum number of runs required for trend analysis

        Returns:
            QualityTrend or None if not enough data
        """
        records = self.load_history(task_alias=task_alias)

        if len(records) < min_runs:
            return None

        # Sort by timestamp (oldest first for trend calculation)
        records_sorted = sorted(records, key=lambda r: r.timestamp)

        first_score = records_sorted[0].score
        last_score = records_sorted[-1].score
        score_change = last_score - first_score
        score_change_percent = (score_change / first_score * 100) if first_score > 0 else 0.0

        # Determine trend direction
        if abs(score_change) < 0.02:
            direction = "stable"
        elif score_change > 0:
            direction = "improving"
        else:
            direction = "declining"

        # Trend description
        if direction == "stable":
            trend_description = "Quality scores have remained stable"
        elif direction == "improving":
            if score_change_percent > 10:
                trend_description = f"Strong improvement (+{score_change_percent:.1f}%)"
            elif score_change_percent > 5:
                trend_description = f"Moderate improvement (+{score_change_percent:.1f}%)"
            else:
                trend_description = f"Slight improvement (+{score_change_percent:.1f}%)"
        else:  # declining
            if abs(score_change_percent) > 10:
                trend_description = f"Significant decline ({score_change_percent:.1f}%)"
            elif abs(score_change_percent) > 5:
                trend_description = f"Moderate decline ({score_change_percent:.1f}%)"
            else:
                trend_description = f"Slight decline ({score_change_percent:.1f}%)"

        # Calculate averages
        overall_avg = sum(r.score for r in records_sorted) / len(records_sorted)
        recent_runs = records_sorted[-5:] if len(records_sorted) >= 5 else records_sorted
        recent_avg = sum(r.score for r in recent_runs) / len(recent_runs)

        # Category trends
        category_trends = {}
        category_scores_history: Dict[str, List[float]] = {}

        for r in records_sorted:
            if r.category_scores:
                for cat, score in r.category_scores.items():
                    if cat not in category_scores_history:
                        category_scores_history[cat] = []
                    category_scores_history[cat].append(score)

        for cat, scores in category_scores_history.items():
            if len(scores) >= 2:
                cat_change = scores[-1] - scores[0]
                if abs(cat_change) < 0.02:
                    category_trends[cat] = "stable"
                elif cat_change > 0:
                    category_trends[cat] = "improving"
                else:
                    category_trends[cat] = "declining"

        return QualityTrend(
            direction=direction,
            score_change=score_change,
            score_change_percent=score_change_percent,
            trend_description=trend_description,
            recent_avg=recent_avg,
            overall_avg=overall_avg,
            category_trends=category_trends if category_trends else None,
        )

    def compare_runs(self, run_id1: str, run_id2: str) -> Optional[RunComparison]:
        """Compare two quality runs

        Args:
            run_id1: First run ID
            run_id2: Second run ID

        Returns:
            RunComparison or None if runs not found
        """
        # Load all runs and find the two we need
        records = self.load_history()
        run1 = next((r for r in records if r.run_id == run_id1), None)
        run2 = next((r for r in records if r.run_id == run_id2), None)

        if not run1 or not run2:
            return None

        score_delta = run2.score - run1.score
        score_delta_percent = (score_delta / run1.score * 100) if run1.score > 0 else 0.0
        score_improved = score_delta > 0

        iteration_delta = run2.iteration - run1.iteration
        iteration_improved = iteration_delta < 0  # Fewer iterations is better

        # Category deltas
        category_deltas = None
        if run1.category_scores and run2.category_scores:
            category_deltas = {}
            all_categories = set(run1.category_scores.keys()) | set(run2.category_scores.keys())
            for cat in all_categories:
                score1 = run1.category_scores.get(cat, 0.0)
                score2 = run2.category_scores.get(cat, 0.0)
                category_deltas[cat] = score2 - score1

        # Passed comparison
        if run1.passed and run2.passed:
            passed_comparison = "both_passed"
        elif not run1.passed and not run2.passed:
            passed_comparison = "both_failed"
        elif not run1.passed and run2.passed:
            passed_comparison = "now_passed"
        else:
            passed_comparison = "now_failed"

        # Gate comparison
        gate_comparison = None
        if run1.gate_passed is not None and run2.gate_passed is not None:
            if run1.gate_passed and run2.gate_passed:
                gate_comparison = "both_passed"
            elif not run1.gate_passed and not run2.gate_passed:
                gate_comparison = "both_failed"
            elif not run1.gate_passed and run2.gate_passed:
                gate_comparison = "now_passed"
            else:
                gate_comparison = "now_failed"

        return RunComparison(
            run1_id=run_id1,
            run2_id=run_id2,
            score_delta=score_delta,
            score_delta_percent=score_delta_percent,
            score_improved=score_improved,
            iteration_delta=iteration_delta,
            iteration_improved=iteration_improved,
            category_deltas=category_deltas,
            passed_comparison=passed_comparison,
            gate_comparison=gate_comparison,
        )

    def get_recent_runs(self, limit: int = 10, task_alias: Optional[str] = None) -> List[QualityRunRecord]:
        """Get recent quality runs

        Args:
            limit: Maximum number of runs to return
            task_alias: Optional task alias to filter by

        Returns:
            List of recent quality run records
        """
        return self.load_history(task_alias=task_alias, limit=limit)

    def clear_history(self, task_alias: Optional[str] = None) -> int:
        """Clear quality run history

        Args:
            task_alias: Optional task alias to filter by (if None, clears all)

        Returns:
            Number of records cleared
        """
        records = self.load_history(task_alias=task_alias)

        if task_alias:
            # Filter out records for this task
            other_records = [r for r in records if r.task_alias != task_alias]
            cleared_count = len(records) - len(other_records)

            # Rewrite index with remaining records
            with open(self.index_file, "w", encoding="utf-8") as f:
                for record in other_records:
                    f.write(json.dumps(record.to_dict()) + "\n")
        else:
            # Clear all
            cleared_count = len(records)
            self.index_file.unlink(missing_ok=True)

        return cleared_count


# Convenience functions

def save_quality_run(
    result: Dict[str, Any],
    criteria_name: str,
    history_dir: Optional[Path] = None,
    duration_seconds: Optional[float] = None,
) -> Optional[str]:
    """Save a quality run result to history

    Args:
        result: Quality loop result
        criteria_name: Criteria template name used
        history_dir: Optional custom history directory
        duration_seconds: Optional duration of the run in seconds

    Returns:
        Path to saved file or None if failed
    """
    try:
        manager = QualityHistoryManager(history_dir=history_dir)
        record = QualityRunRecord.from_loop_result(result, criteria_name, duration_seconds)
        return manager.save_run(record)
    except Exception:
        return None


def get_quality_statistics(
    task_alias: Optional[str] = None,
    history_dir: Optional[Path] = None,
) -> Optional[QualityStatistics]:
    """Get statistics for quality runs

    Args:
        task_alias: Optional task alias to filter by
        history_dir: Optional custom history directory

    Returns:
        QualityStatistics or None if no history
    """
    manager = QualityHistoryManager(history_dir=history_dir)
    return manager.get_statistics(task_alias=task_alias)


def get_quality_trends(
    task_alias: Optional[str] = None,
    min_runs: int = 3,
    history_dir: Optional[Path] = None,
) -> Optional[QualityTrend]:
    """Get trends for quality runs

    Args:
        task_alias: Optional task alias to filter by
        min_runs: Minimum number of runs required for trend analysis
        history_dir: Optional custom history directory

    Returns:
        QualityTrend or None if not enough data
    """
    manager = QualityHistoryManager(history_dir=history_dir)
    return manager.get_trends(task_alias=task_alias, min_runs=min_runs)


def format_statistics_report(stats: QualityStatistics, task_alias: Optional[str] = None) -> str:
    """Format statistics report as text

    Args:
        stats: QualityStatistics to format
        task_alias: Optional task alias for title

    Returns:
        Formatted report string
    """
    lines = []
    title = f"Quality Statistics for '{task_alias}'" if task_alias else "Quality Statistics"
    lines.append(f"## {title}")
    lines.append("")

    lines.append(f"**Total Runs:** {stats.total_runs}")
    lines.append(f"**Passed:** {stats.passed_runs} | **Failed:** {stats.failed_runs}")
    lines.append(f"**Pass Rate:** {stats.pass_rate:.1%}")
    lines.append("")

    lines.append("### Score Statistics")
    lines.append(f"**Average:** {stats.avg_score:.3f}")
    lines.append(f"**Min:** {stats.min_score:.3f} | **Max:** {stats.max_score:.3f}")
    lines.append(f"**Range:** {stats.max_score - stats.min_score:.3f}")
    lines.append("")

    lines.append(f"**Average Iterations:** {stats.avg_iterations:.1f}")
    lines.append("")

    if stats.most_failed_category:
        lines.append(f"**Most Failed Category:** {stats.most_failed_category}")
    if stats.most_used_profile:
        lines.append(f"**Most Used Profile:** {stats.most_used_profile}")
    if stats.most_used_criteria:
        lines.append(f"**Most Used Criteria:** {stats.most_used_criteria}")

    return "\n".join(lines)


def format_trends_report(trend: QualityTrend, task_alias: Optional[str] = None) -> str:
    """Format trends report as text

    Args:
        trend: QualityTrend to format
        task_alias: Optional task alias for title

    Returns:
        Formatted report string
    """
    lines = []
    title = f"Quality Trends for '{task_alias}'" if task_alias else "Quality Trends"
    lines.append(f"## {title}")
    lines.append("")

    # Direction indicator
    direction_emoji = {
        "improving": "📈",
        "declining": "📉",
        "stable": "➡️",
    }
    emoji = direction_emoji.get(trend.direction, "")

    lines.append(f"**Trend:** {emoji} {trend.direction.upper()}")
    lines.append(f"**Description:** {trend.trend_description}")
    lines.append("")

    lines.append("### Score Changes")
    lines.append(f"**Change:** {trend.score_change:+.3f} ({trend.score_change_percent:+.1f}%)")
    lines.append(f"**Overall Avg:** {trend.overall_avg:.3f}")
    lines.append(f"**Recent Avg:** {trend.recent_avg:.3f}")
    lines.append("")

    if trend.category_trends:
        lines.append("### Category Trends")
        for cat, cat_trend in sorted(trend.category_trends.items()):
            cat_emoji = direction_emoji.get(cat_trend, "")
            lines.append(f"- **{cat}:** {cat_emoji} {cat_trend}")
        lines.append("")

    return "\n".join(lines)


def format_history_json(
    statistics: Optional[QualityStatistics] = None,
    trends: Optional[QualityTrend] = None,
    recent_runs: Optional[List[QualityRunRecord]] = None,
    task_alias: Optional[str] = None,
) -> str:
    """Format history data as JSON

    Args:
        statistics: Optional QualityStatistics
        trends: Optional QualityTrend
        recent_runs: Optional list of recent runs
        task_alias: Optional task alias

    Returns:
        JSON string
    """
    data = {}

    if task_alias:
        data["task_alias"] = task_alias

    if statistics:
        data["statistics"] = {
            "total_runs": statistics.total_runs,
            "passed_runs": statistics.passed_runs,
            "failed_runs": statistics.failed_runs,
            "pass_rate": statistics.pass_rate,
            "avg_score": statistics.avg_score,
            "min_score": statistics.min_score,
            "max_score": statistics.max_score,
            "avg_iterations": statistics.avg_iterations,
            "most_failed_category": statistics.most_failed_category,
            "most_used_profile": statistics.most_used_profile,
            "most_used_criteria": statistics.most_used_criteria,
        }

    if trends:
        data["trends"] = {
            "direction": trends.direction,
            "score_change": trends.score_change,
            "score_change_percent": trends.score_change_percent,
            "trend_description": trends.trend_description,
            "recent_avg": trends.recent_avg,
            "overall_avg": trends.overall_avg,
            "category_trends": trends.category_trends,
        }

    if recent_runs:
        data["recent_runs"] = [r.to_dict() for r in recent_runs]

    return json.dumps(data, indent=2)
