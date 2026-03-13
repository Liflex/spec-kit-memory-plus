"""
QA Dashboard System (Exp 71)

Provides a unified interface for all quality assurance features:
- Quality Overview: Quick summary of quality status
- Quality Check: Fast assessment with recommendations
- Run Comparison: Compare metrics across quality runs
- Quality Trends: View trends and forecasts
- Interactive Mode: Guided workflows for all QA features

This creates a single entry point for discovering and using all quality features.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, timedelta

from .quality_history import QualityHistoryManager, QualityRunRecord, QualityStatistics
from .quality_anomaly import AnomalyReport, AnomalySeverity
from .quality_goals import QualityGoalsManager, GoalStatus, GoalProgress
from .quality_insights import InsightsReport, InsightPriority
from .gate_policies import GatePolicyManager, GATE_PRESETS


class TrendDirection(Enum):
    """Quality trend direction"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class QualityOverview:
    """Quality status overview"""
    quality_score: float
    pass_rate: float
    total_rules: int
    passed_rules: int
    failed_rules: int
    trend_direction: TrendDirection
    trend_change: float  # Change over recent runs
    goals_summary: Dict[str, int]  # active, achieved, at_risk, failed
    anomalies_count: int
    anomalies_by_severity: Dict[str, int]
    top_insights: List[str]
    last_run: Optional[datetime] = None
    task_alias: str = "default"


@dataclass
class QualityCheckResult:
    """Result of quality check"""
    assessment: str  # GOOD, NEEDS_IMPROVEMENT, CRITICAL
    quality_score: float
    pass_rate: float
    trend: str
    priority_actions: List[Dict[str, str]]
    recommendations: List[str]
    detected_issues: List[str]


@dataclass
class RunComparison:
    """Comparison of quality runs"""
    runs: List[Dict[str, Any]]
    trend_direction: TrendDirection
    average_change: float
    best_run: Optional[int]
    worst_run: Optional[int]
    anomaly_runs: List[int]
    category_changes: Dict[str, Tuple[float, float]]  # category: (old, new)


@dataclass
class QualityTrend:
    """Quality trend over time"""
    direction: TrendDirection
    strength: float  # 0-1, how strong the trend is
    moving_average: float
    forecast: Optional[float]
    confidence: float  # 0-1
    seasonality: Optional[str]  # Detected pattern if any


def get_quality_overview(
    task_alias: str = "default",
    max_runs: int = 10,
    history_dir: Optional[Path] = None
) -> QualityOverview:
    """
    Generate a comprehensive quality overview.

    Args:
        task_alias: Task to analyze
        max_runs: Number of recent runs to consider
        history_dir: Custom history directory

    Returns:
        QualityOverview with current quality status
    """
    history_mgr = QualityHistoryManager(history_dir=history_dir)

    # Get recent runs
    runs = history_mgr.get_recent_runs(task_alias, limit=max_runs)

    if not runs:
        return QualityOverview(
            quality_score=0.0,
            pass_rate=0.0,
            total_rules=0,
            passed_rules=0,
            failed_rules=0,
            trend_direction=TrendDirection.STABLE,
            trend_change=0.0,
            goals_summary={"active": 0, "achieved": 0, "at_risk": 0, "failed": 0},
            anomalies_count=0,
            anomalies_by_severity={},
            top_insights=["No quality history found. Run quality loop first."],
            task_alias=task_alias
        )

    # Get latest run
    latest = runs[0]

    # Calculate trend
    trend_direction, trend_change = _calculate_trend(runs)

    # Get goals summary
    goals_mgr = QualityGoalsManager()
    goal_summaries = goals_mgr.get_all_goal_progress(task_alias)

    goals_summary = {
        "active": len([g for g in goal_summaries if g.status != GoalStatus.ACHIEVED]),
        "achieved": len([g for g in goal_summaries if g.status == GoalStatus.ACHIEVED]),
        "at_risk": len([g for g in goal_summaries if g.status == GoalStatus.AT_RISK]),
        "failed": len([g for g in goal_summaries if g.status == GoalStatus.FAILED])
    }

    # Get anomalies
    from .quality_anomaly import detect_anomalies
    anomaly_report = detect_anomalies(task_alias, max_runs=max_runs)

    anomalies_by_severity = {}
    for anomaly in anomaly_report.anomalies:
        severity_name = anomaly.severity.value
        anomalies_by_severity[severity_name] = anomalies_by_severity.get(severity_name, 0) + 1

    # Get top insights
    top_insights = _get_top_insights(task_alias, max_runs=max_runs)

    return QualityOverview(
        quality_score=latest.score,
        pass_rate=latest.pass_rate,
        total_rules=latest.total_rules,
        passed_rules=latest.passed_rules,
        failed_rules=latest.failed_rules,
        trend_direction=trend_direction,
        trend_change=trend_change,
        goals_summary=goals_summary,
        anomalies_count=len(anomaly_report.anomalies),
        anomalies_by_severity=anomalies_by_severity,
        top_insights=top_insights,
        last_run=latest.timestamp,
        task_alias=task_alias
    )


def run_quality_check(
    task_alias: str = "default",
    detailed: bool = False,
    recommend: bool = True,
    history_dir: Optional[Path] = None
) -> QualityCheckResult:
    """
    Run a quick quality check with recommendations.

    Args:
        task_alias: Task to check
        detailed: Include detailed breakdown
        recommend: Include specific recommendations
        history_dir: Custom history directory

    Returns:
        QualityCheckResult with assessment and recommendations
    """
    overview = get_quality_overview(task_alias=task_alias, history_dir=history_dir)

    # Determine assessment
    if overview.quality_score >= 0.90 and overview.anomalies_count == 0:
        assessment = "EXCELLENT"
    elif overview.quality_score >= 0.80 and overview.anomalies_count <= 2:
        assessment = "GOOD"
    elif overview.quality_score >= 0.70:
        assessment = "NEEDS_IMPROVEMENT"
    else:
        assessment = "CRITICAL"

    # Generate priority actions
    priority_actions = _generate_priority_actions(overview)

    # Generate recommendations
    recommendations = []
    if recommend:
        recommendations = _generate_recommendations(overview)

    # Detect issues
    detected_issues = []
    if detailed:
        detected_issues = _detect_issues(overview)

    return QualityCheckResult(
        assessment=assessment,
        quality_score=overview.quality_score,
        pass_rate=overview.pass_rate,
        trend=f"{overview.trend_direction.value} ({overview.trend_change:+.2f})",
        priority_actions=priority_actions,
        recommendations=recommendations,
        detected_issues=detected_issues
    )


def compare_quality_runs(
    task_alias: str = "default",
    n_runs: int = 5,
    history_dir: Optional[Path] = None
) -> RunComparison:
    """
    Compare quality metrics across recent runs.

    Args:
        task_alias: Task to analyze
        n_runs: Number of runs to compare
        history_dir: Custom history directory

    Returns:
        RunComparison with metrics and changes
    """
    history_mgr = QualityHistoryManager(history_dir=history_dir)
    runs = history_mgr.get_recent_runs(task_alias, limit=n_runs)

    if len(runs) < 2:
        return RunComparison(
            runs=[],
            trend_direction=TrendDirection.STABLE,
            average_change=0.0,
            best_run=None,
            worst_run=None,
            anomaly_runs=[],
            category_changes={}
        )

    # Build run data
    run_data = []
    for i, run in enumerate(runs):
        run_data.append({
            "run_number": i + 1,
            "score": run.score,
            "pass_rate": run.pass_rate,
            "iterations": run.iteration,
            "timestamp": run.timestamp.isoformat() if run.timestamp else None
        })

    # Calculate trend
    trend_direction, avg_change = _calculate_trend(runs)

    # Find best and worst runs
    scores = [r.score for r in runs]
    best_idx = scores.index(max(scores))
    worst_idx = scores.index(min(scores))

    # Detect anomaly runs (significant drops)
    anomaly_runs = []
    for i in range(1, len(runs)):
        change = runs[i].score - runs[i-1].score
        if change < -0.05:  # More than 5% drop
            anomaly_runs.append(i)

    # Calculate category changes
    category_changes = {}
    if len(runs) >= 2:
        latest = runs[0]
        previous = runs[1]
        for cat in latest.category_scores:
            old_score = previous.category_scores.get(cat, 0.0)
            new_score = latest.category_scores.get(cat, 0.0)
            if old_score != new_score:
                category_changes[cat] = (old_score, new_score)

    return RunComparison(
        runs=run_data,
        trend_direction=trend_direction,
        average_change=avg_change,
        best_run=best_idx + 1,
        worst_run=worst_idx + 1,
        anomaly_runs=anomaly_runs,
        category_changes=category_changes
    )


def get_quality_trends(
    task_alias: str = "default",
    forecast: bool = False,
    history_dir: Optional[Path] = None
) -> QualityTrend:
    """
    Analyze quality trends over time.

    Args:
        task_alias: Task to analyze
        forecast: Include predictive forecast
        history_dir: Custom history directory

    Returns:
        QualityTrend with trend analysis
    """
    history_mgr = QualityHistoryManager(history_dir=history_dir)
    runs = history_mgr.get_recent_runs(task_alias, limit=20)

    if len(runs) < 3:
        return QualityTrend(
            direction=TrendDirection.STABLE,
            strength=0.0,
            moving_average=0.0,
            forecast=None,
            confidence=0.0,
            seasonality=None
        )

    scores = [r.score for r in runs]
    direction, change = _calculate_trend(runs)

    # Calculate trend strength (0-1)
    strength = min(abs(change) * 10, 1.0)

    # Moving average
    moving_average = sum(scores[:min(5, len(scores))]) / min(5, len(scores))

    # Forecast if requested
    forecast_score = None
    confidence = 0.5
    if forecast and len(runs) >= 5:
        # Simple linear forecast
        recent_changes = [runs[i].score - runs[i+1].score for i in range(len(runs)-1)]
        avg_change = sum(recent_changes) / len(recent_changes)
        forecast_score = runs[0].score + avg_change

        # Confidence based on stability
        variance = sum((c - avg_change)**2 for c in recent_changes) / len(recent_changes)
        confidence = max(0, 1.0 - variance * 10)

    # Detect seasonality (simple pattern detection)
    seasonality = None
    if len(runs) >= 6:
        # Check for alternating pattern
        up_down = [1 if i < len(runs)-1 and runs[i].score < runs[i+1].score else 0
                   for i in range(len(runs)-1)]
        if sum(up_down) / len(up_down) > 0.7:
            seasonality = "generally_improving"
        elif sum(up_down) / len(up_down) < 0.3:
            seasonality = "generally_declining"

    return QualityTrend(
        direction=direction,
        strength=strength,
        moving_average=moving_average,
        forecast=forecast_score,
        confidence=confidence,
        seasonality=seasonality
    )


def format_overview_report(overview: QualityOverview, detailed: bool = False) -> str:
    """Format quality overview as readable text."""
    lines = [
        "=== Spec Kit Quality Overview ===",
        "",
        f"Quality Score: {overview.quality_score:.2f} ({_trend_arrow(overview.trend_direction)} {overview.trend_direction.value})",
        f"Pass Rate: {overview.pass_rate*100:.0f}% ({overview.passed_rules}/{overview.total_rules} rules)",
        "",
    ]

    # Goals section
    if overview.goals_summary["active"] > 0:
        lines.append("Quality Goals: {} active".format(overview.goals_summary["active"]))
        goals = [
            f"  ✅ Achieved: {overview.goals_summary['achieved']}",
            f"  ⚠️ At-Risk: {overview.goals_summary['at_risk']}",
            f"  ❌ Failed: {overview.goals_summary['failed']}"
        ]
        lines.extend(goals)
        lines.append("")

    # Anomalies section
    if overview.anomalies_count > 0:
        lines.append(f"Recent Anomalies: {overview.anomalies_count} detected")
        for severity, count in overview.anomalies_by_severity.items():
            if count > 0:
                lines.append(f"  {_severity_emoji(severity)} {severity.title()}: {count}")
        lines.append("")

    # Top insights
    if overview.top_insights:
        lines.append("Top Insights:")
        for insight in overview.top_insights[:5]:
            lines.append(f"  - {insight}")
        lines.append("")

    # Next steps
    lines.extend([
        "Next Steps:",
        "  - /speckit.qa interactive for guided workflow",
        "  - /speckit.goals suggest for goal recommendations",
        "  - /speckit.loop --suggest-goals for smart goal suggestions"
    ])

    return "\n".join(lines)


def format_check_result(check: QualityCheckResult, detailed: bool = False) -> str:
    """Format quality check result as readable text."""
    lines = [
        "=== Quick Quality Check ===",
        "",
        f"Assessment: {check.assessment}",
        "",
        "Current Status:",
        f"  Score: {check.quality_score:.2f}",
        f"  Pass Rate: {check.pass_rate*100:.0f}%",
        f"  Trend: {check.trend}",
        ""
    ]

    if check.priority_actions:
        lines.append("Priority Actions:")
        for i, action in enumerate(check.priority_actions, 1):
            lines.append(f"  {i}. {action['title']}")
            if 'command' in action:
                lines.append(f"     → {action['command']}")
        lines.append("")

    if check.recommendations:
        lines.append("Recommendations:")
        for rec in check.recommendations:
            lines.append(f"  - {rec}")
        lines.append("")

    if detailed and check.detected_issues:
        lines.append("Detected Issues:")
        for issue in check.detected_issues:
            lines.append(f"  ⚠️ {issue}")

    return "\n".join(lines)


def format_comparison_report(comparison: RunComparison) -> str:
    """Format run comparison as readable text."""
    if not comparison.runs:
        return "=== Quality Comparison ===\n\nNo quality runs found."

    lines = [
        f"=== Quality Comparison (Last {len(comparison.runs)} Runs) ===",
        "",
        "Run | Score | Change | Pass Rate | Iterations | Anomalies",
        "----|-------|--------|-----------|------------|----------"
    ]

    prev_score = None
    for run in comparison.runs:
        score = run["score"]
        change = ""
        if prev_score is not None:
            change = f"{score - prev_score:+.2f}"
        prev_score = score

        anomaly_mark = " 🚨" if run["run_number"] in comparison.anomaly_runs else ""
        lines.append(
            f"R{run['run_number']}  | {score:.2f}  | {change:>6}  | {run['pass_rate']*100:.0f}%       "
            f"| {run['iterations']}          |{anomaly_mark}"
        )

    lines.extend([
        "",
        f"Trend: {comparison.trend_direction.value} (average {comparison.average_change:+.3f} per run)"
    ])

    if comparison.best_run:
        lines.append(f"Best Run: R{comparison.best_run} (current)" if comparison.best_run == 1 else f"Best Run: R{comparison.best_run}")

    if comparison.worst_run and comparison.worst_run != comparison.best_run:
        lines.append(f"Worst Run: R{comparison.worst_run}")

    if comparison.anomaly_runs:
        lines.append(f"Anomaly Detected: Runs {', '.join(f'R{r}' for r in comparison.anomaly_runs)} had significant changes")

    # Category changes
    if comparison.category_changes:
        lines.extend(["", "Category Breakdown (previous → current):"])
        for cat, (old, new) in comparison.category_changes.items():
            change = new - old
            lines.append(f"  {cat}: {old:.2f} → {new:.2f} ({change:+.2f})")

    return "\n".join(lines)


def format_trends_report(trend: QualityTrend) -> str:
    """Format quality trends as readable text."""
    lines = [
        "=== Quality Trends ===",
        "",
        f"Direction: {trend.direction.value}",
        f"Strength: {trend.strength:.2f} (0-1 scale)",
        f"Moving Average (5 runs): {trend.moving_average:.2f}",
        ""
    ]

    if trend.forecast is not None:
        lines.extend([
            f"Forecast: {trend.forecast:.2f}",
            f"Confidence: {trend.confidence*100:.0f}%",
            ""
        ])

    if trend.seasonality:
        lines.append(f"Pattern: {trend.seasonality}")

    return "\n".join(lines)


def format_overview_json(overview: QualityOverview) -> str:
    """Format quality overview as JSON."""
    return json.dumps({
        "quality_score": overview.quality_score,
        "pass_rate": overview.pass_rate,
        "total_rules": overview.total_rules,
        "passed_rules": overview.passed_rules,
        "failed_rules": overview.failed_rules,
        "trend": overview.trend_direction.value,
        "trend_change": overview.trend_change,
        "goals": overview.goals_summary,
        "anomalies": {
            "detected": overview.anomalies_count,
            "by_severity": overview.anomalies_by_severity
        },
        "top_insights": overview.top_insights,
        "last_run": overview.last_run.isoformat() if overview.last_run else None,
        "task_alias": overview.task_alias
    }, indent=2)


def format_check_json(check: QualityCheckResult) -> str:
    """Format quality check result as JSON."""
    return json.dumps({
        "assessment": check.assessment,
        "quality_score": check.quality_score,
        "pass_rate": check.pass_rate,
        "trend": check.trend,
        "priority_actions": check.priority_actions,
        "recommendations": check.recommendations,
        "detected_issues": check.detected_issues
    }, indent=2)


# Helper functions

def _calculate_trend(runs: List[QualityRunRecord]) -> Tuple[TrendDirection, float]:
    """Calculate trend direction and average change."""
    if len(runs) < 2:
        return TrendDirection.STABLE, 0.0

    # Calculate changes between consecutive runs
    changes = []
    for i in range(len(runs) - 1):
        change = runs[i].score - runs[i + 1].score
        changes.append(change)

    avg_change = sum(changes) / len(changes) if changes else 0.0

    # Determine direction
    if avg_change > 0.02:
        direction = TrendDirection.IMPROVING
    elif avg_change < -0.02:
        direction = TrendDirection.DECLINING
    else:
        # Check volatility
        variance = sum((c - avg_change)**2 for c in changes) / len(changes) if changes else 0
        if variance > 0.01:
            direction = TrendDirection.VOLATILE
        else:
            direction = TrendDirection.STABLE

    return direction, avg_change


def _get_top_insights(task_alias: str, max_runs: int = 10) -> List[str]:
    """Get top quality insights."""
    try:
        from .quality_insights import generate_insights
        report = generate_insights(task_alias=task_alias, max_runs=max_runs)

        insights = []
        for insight in report.insights[:5]:
            if insight.priority in [InsightPriority.CRITICAL, InsightPriority.HIGH]:
                insights.append(f"[{insight.priority.value.upper()}] {insight.title}")

        return insights if insights else ["No critical insights. Quality is stable."]
    except Exception:
        return ["Unable to generate insights. Run quality loop first."]


def _generate_priority_actions(overview: QualityOverview) -> List[Dict[str, str]]:
    """Generate priority actions based on overview."""
    actions = []

    # Failed goals
    if overview.goals_summary["failed"] > 0:
        actions.append({
            "title": f"Fix {overview.goals_summary['failed']} failed goal(s)",
            "command": "/speckit.goals check"
        })

    # At-risk goals
    if overview.goals_summary["at_risk"] > 0:
        actions.append({
            "title": f"Address {overview.goals_summary['at_risk']} at-risk goal(s)",
            "command": "/speckit.goals suggest"
        })

    # Anomalies
    if overview.anomalies_count > 0:
        actions.append({
            "title": f"Investigate {overview.anomalies_count} detected anomaly/ies",
            "command": "/speckit.anomalies list"
        })

    # Score improvement
    if overview.quality_score < 0.90:
        actions.append({
            "title": f"Improve quality score ({overview.quality_score:.2f} → 0.90)",
            "command": "/speckit.loop --suggest-goals"
        })

    return actions


def _generate_recommendations(overview: QualityOverview) -> List[str]:
    """Generate recommendations based on overview."""
    recommendations = []

    if overview.quality_score < 0.80:
        recommendations.append("Use --strict mode for production checks")

    if overview.goals_summary["active"] == 0:
        recommendations.append("Set quality goals to track progress: /speckit.goals suggest")

    if overview.pass_rate < 0.90:
        recommendations.append("Focus on failed rules for quick wins")

    if overview.trend_direction == TrendDirection.DECLINING:
        recommendations.append("Investigate recent changes causing quality decline")

    if overview.anomalies_count > 2:
        recommendations.append("Review anomaly patterns: /speckit.insights patterns")

    recommendations.append("Run quality loop with insights: /speckit.loop --suggest-goals")

    return recommendations


def _detect_issues(overview: QualityOverview) -> List[str]:
    """Detect specific issues from overview."""
    issues = []

    if overview.anomalies_count > 0:
        critical_anomalies = overview.anomalies_by_severity.get("critical", 0)
        if critical_anomalies > 0:
            issues.append(f"{critical_anomalies} critical anomaly/ies detected")

    if overview.quality_score < 0.70:
        issues.append("Quality score below 0.70 threshold")

    if overview.pass_rate < 0.80:
        issues.append("Pass rate below 80%")

    failed_goals = overview.goals_summary["failed"]
    if failed_goals > 0:
        issues.append(f"{failed_goals} goal(s) failed")

    return issues


def _trend_arrow(direction: TrendDirection) -> str:
    """Get arrow emoji for trend direction."""
    arrows = {
        TrendDirection.IMPROVING: "↑",
        TrendDirection.DECLINING: "↓",
        TrendDirection.STABLE: "→",
        TrendDirection.VOLATILE: "↝"
    }
    return arrows.get(direction, "→")


def _severity_emoji(severity: str) -> str:
    """Get emoji for severity level."""
    emojis = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "⚡",
        "low": "💡"
    }
    return emojis.get(severity, "•")


# Exp 75: Quality Benchmarking Integration - Benchmark-aware quality overview

@dataclass
class BenchmarkAwareQualityOverview(QualityOverview):
    """Extended quality overview with benchmark comparison"""
    benchmark_percentile: float = 0.0  # Percentile rank vs historical data
    benchmark_comparison: str = ""  # excellent, above_average, etc.
    benchmark_reliability: str = ""  # high, medium, low
    historical_mean: float = 0.0
    historical_median: float = 0.0
    z_score: float = 0.0


def get_benchmark_aware_overview(
    task_alias: str = "default",
    max_runs: int = 50,
    history_dir: Optional[Path] = None
) -> BenchmarkAwareQualityOverview:
    """
    Get quality overview with benchmark comparison (Exp 75).

    Combines standard quality overview with percentile ranking against
    historical baselines for context-aware quality assessment.

    Args:
        task_alias: Task to analyze
        max_runs: Maximum historical runs for benchmark
        history_dir: Custom history directory

    Returns:
        BenchmarkAwareQualityOverview with extended metrics
    """
    from .quality_benchmarking import QualityBenchmarkingEngine

    # Get standard overview
    base_overview = get_quality_overview(task_alias, max_runs, history_dir)

    # Create benchmark from historical data
    benchmark_engine = QualityBenchmarkingEngine(history_dir=history_dir)
    benchmark_profile = benchmark_engine.create_historical_benchmark(
        task_alias=task_alias,
        max_runs=max_runs
    )

    # Calculate benchmark metrics
    benchmark_percentile = 0.0
    benchmark_comparison = ""
    benchmark_reliability = "low"
    historical_mean = 0.0
    historical_median = 0.0
    z_score = 0.0

    if benchmark_profile.overall_metrics:
        metrics = benchmark_profile.overall_metrics
        benchmark_percentile = metrics.get_percentile_rank(base_overview.quality_score)
        benchmark_comparison = metrics.get_comparison(base_overview.quality_score).value
        historical_mean = metrics.mean
        historical_median = metrics.p50
        benchmark_reliability = (
            "high" if metrics.sample_size >= 30 else
            "medium" if metrics.sample_size >= 10 else "low"
        )
        z_score = (
            (base_overview.quality_score - metrics.mean) / metrics.std_dev
            if metrics.std_dev > 0 else 0.0
        )

    # Create benchmark-aware overview
    return BenchmarkAwareQualityOverview(
        # Base fields
        quality_score=base_overview.quality_score,
        pass_rate=base_overview.pass_rate,
        total_rules=base_overview.total_rules,
        passed_rules=base_overview.passed_rules,
        failed_rules=base_overview.failed_rules,
        trend_direction=base_overview.trend_direction,
        trend_change=base_overview.trend_change,
        goals_summary=base_overview.goals_summary,
        anomalies_count=base_overview.anomalies_count,
        anomalies_by_severity=base_overview.anomalies_by_severity,
        top_insights=base_overview.top_insights,
        last_run=base_overview.last_run,
        task_alias=base_overview.task_alias,
        # Benchmark fields
        benchmark_percentile=benchmark_percentile,
        benchmark_comparison=benchmark_comparison,
        benchmark_reliability=benchmark_reliability,
        historical_mean=historical_mean,
        historical_median=historical_median,
        z_score=z_score,
    )


def format_benchmark_aware_overview_report(
    overview: BenchmarkAwareQualityOverview
) -> str:
    """
    Format benchmark-aware quality overview as text report (Exp 75).

    Args:
        overview: Benchmark-aware quality overview

    Returns:
        Formatted text report with benchmark context
    """
    lines = []
    lines.append("=" * 60)
    lines.append("QUALITY OVERVIEW (WITH BENCHMARKS)")
    lines.append("=" * 60)
    lines.append("")

    # Basic quality metrics
    lines.append(f"Quality Score: {overview.quality_score:.3f}")
    lines.append(f"Pass Rate: {overview.pass_rate:.1%}")
    lines.append(f"Rules: {overview.passed_rules}/{overview.total_rules} passed")

    # Trend
    arrow = _trend_arrow(overview.trend_direction)
    lines.append(f"Trend: {arrow} {overview.trend_direction.value} ({overview.trend_change:+.3f})")
    lines.append("")

    # Benchmark comparison
    lines.append("BENCHMARK COMPARISON")
    lines.append("-" * 40)
    lines.append(f"Percentile Rank: {overview.benchmark_percentile:.1f}th percentile")
    lines.append(f"Comparison: {overview.benchmark_comparison.replace('_', ' ').title()}")
    lines.append(f"Reliability: {overview.benchmark_reliability.upper()}")
    lines.append(f"vs Historical Mean: {overview.quality_score - overview.historical_mean:+.3f}")
    lines.append(f"Z-Score: {overview.z_score:+.2f}")
    lines.append("")

    # Interpretation
    if overview.benchmark_comparison == "excellent":
        lines.append("✨ Excellent performance! Top 10% of historical quality.")
    elif overview.benchmark_comparison == "above_average":
        lines.append("👍 Above average. Top 25% of historical quality.")
    elif overview.benchmark_comparison == "average":
        lines.append("📊 Average performance. Middle 50% of historical quality.")
    elif overview.benchmark_comparison == "below_average":
        lines.append("⚠️ Below average. Bottom 25% of historical quality.")
    elif overview.benchmark_comparison == "poor":
        lines.append("🚨 Poor performance. Bottom 10% of historical quality.")
    lines.append("")

    # Goals summary
    if overview.goals_summary:
        lines.append("GOALS STATUS")
        lines.append("-" * 40)
        for status, count in overview.goals_summary.items():
            if count > 0:
                lines.append(f"  {status.title()}: {count}")
        lines.append("")

    # Anomalies
    if overview.anomalies_count > 0:
        lines.append("ANOMALIES")
        lines.append("-" * 40)
        lines.append(f"  Total: {overview.anomalies_count}")
        for severity, count in overview.anomalies_by_severity.items():
            if count > 0:
                emoji = _severity_emoji(severity)
                lines.append(f"  {emoji} {severity.title()}: {count}")
        lines.append("")

    # Top insights
    if overview.top_insights:
        lines.append("TOP INSIGHTS")
        lines.append("-" * 40)
        for insight in overview.top_insights[:3]:
            lines.append(f"  • {insight}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
