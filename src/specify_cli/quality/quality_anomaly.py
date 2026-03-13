"""
Quality Anomaly Detection with Risk Scoring (Exp 66/67/111)

Provides statistical anomaly detection for quality runs over time:
- Regression Detection: Identifies significant score drops compared to rolling baseline
- Outlier Detection: Z-score statistical analysis to find unusual runs
- Pass Rate Monitoring: Tracks declining pass rates over time
- Stagnation Detection: Identifies when quality has plateaued
- Category-Specific Anomalies: Detects issues in specific categories
- Iteration Spike Detection: Identifies sudden increases in iteration counts
- Risk Scoring: Multi-factor risk assessment for prioritization (Exp 111)

This transforms quality monitoring from passive to active by alerting
when unusual patterns emerge in quality metrics, with risk-based prioritization.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import statistics
from datetime import datetime


class AnomalySeverity(Enum):
    """Severity levels for anomalies"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    REGRESSION = "regression"  # Score drop compared to baseline
    OUTLIER = "outlier"  # Statistical outlier using z-score
    PASS_RATE_DROP = "pass_rate_drop"  # Declining pass rate
    STAGNATION = "stagnation"  # Quality plateaued
    CATEGORY_DROP = "category_drop"  # Specific category score drop
    ITERATION_SPIKE = "iteration_spike"  # Sudden increase in iterations


@dataclass
class QualityAnomaly:
    """Represents a single detected anomaly"""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    title: str
    description: str
    run_id: Optional[str] = None
    timestamp: Optional[str] = None
    affected_category: Optional[str] = None
    baseline_value: Optional[float] = None
    actual_value: Optional[float] = None
    delta: Optional[float] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "affected_category": self.affected_category,
            "baseline_value": self.baseline_value,
            "actual_value": self.actual_value,
            "delta": self.delta,
            "recommendation": self.recommendation,
        }


@dataclass
class AnomalyDetectionConfig:
    """Configuration for anomaly detection thresholds"""
    regression_threshold: float = 0.05  # 5% score drop triggers alert
    regression_critical: float = 0.15  # 15% drop = critical
    z_score_threshold: float = 2.5  # Statistical outlier threshold
    pass_rate_drop_threshold: float = 0.10  # 10% pass rate drop
    stagnation_window: int = 10  # Number of runs to check for stagnation
    stagnation_variance: float = 0.01  # Max variance for stagnation
    iteration_spike_multiplier: float = 2.0  # Iteration count must be X times average
    category_drop_threshold: float = 0.10  # 10% category score drop


@dataclass
class AnomalyReport:
    """Complete anomaly detection report"""
    anomalies_detected: int
    anomalies_by_severity: Dict[str, int]
    anomalies: List[QualityAnomaly]
    total_runs_analyzed: int
    analysis_timestamp: str
    task_alias: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "anomalies_detected": self.anomalies_detected,
            "anomalies_by_severity": self.anomalies_by_severity,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "total_runs_analyzed": self.total_runs_analyzed,
            "analysis_timestamp": self.analysis_timestamp,
            "task_alias": self.task_alias,
        }


class QualityAnomalyDetector:
    """Detects anomalies in quality run history"""

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        """Initialize anomaly detector

        Args:
            config: Detection configuration (uses defaults if None)
        """
        self.config = config or AnomalyDetectionConfig()

    def detect_all(
        self,
        runs: List[Any],
        task_alias: Optional[str] = None,
    ) -> AnomalyReport:
        """Run all anomaly detection algorithms

        Args:
            runs: List of quality run records (oldest first for trends)
            task_alias: Optional task alias for reporting

        Returns:
            AnomalyReport with all detected anomalies
        """
        if len(runs) < 3:
            return AnomalyReport(
                anomalies_detected=0,
                anomalies_by_severity={},
                anomalies=[],
                total_runs_analyzed=len(runs),
                analysis_timestamp=datetime.now().isoformat(),
                task_alias=task_alias,
            )

        anomalies: List[QualityAnomaly] = []

        # Run detection algorithms
        anomalies.extend(self._detect_regressions(runs))
        anomalies.extend(self._detect_outliers(runs))
        anomalies.extend(self._detect_pass_rate_drops(runs))
        anomalies.extend(self._detect_stagnation(runs))
        anomalies.extend(self._detect_category_drops(runs))
        anomalies.extend(self._detect_iteration_spikes(runs))

        # Count by severity
        severity_counts: Dict[str, int] = {}
        for anomaly in anomalies:
            sev = anomaly.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Sort by severity (critical first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3,
            AnomalySeverity.INFO: 4,
        }
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 5))

        return AnomalyReport(
            anomalies_detected=len(anomalies),
            anomalies_by_severity=severity_counts,
            anomalies=anomalies,
            total_runs_analyzed=len(runs),
            analysis_timestamp=datetime.now().isoformat(),
            task_alias=task_alias,
        )

    def _detect_regressions(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect score regressions using rolling baseline

        Compares recent scores to a rolling baseline (5-run window).
        A regression is detected when score drops significantly below baseline.
        """
        anomalies = []
        window_size = 5

        # Sort oldest to newest for trend analysis
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)

        for i in range(window_size, len(sorted_runs)):
            current_run = sorted_runs[i]
            baseline_runs = sorted_runs[i - window_size:i]

            # Calculate rolling baseline
            baseline_scores = [r.score for r in baseline_runs]
            rolling_baseline = statistics.mean(baseline_scores)

            # Check for regression
            score_drop = rolling_baseline - current_run.score
            drop_pct = score_drop / rolling_baseline if rolling_baseline > 0 else 0

            if drop_pct >= self.config.regression_critical:
                severity = AnomalySeverity.CRITICAL
                recommendation = (
                    f"Critical quality regression detected! Score dropped by {drop_pct*100:.1f}%. "
                    "Investigate immediately - this may indicate a serious code issue."
                )
            elif drop_pct >= self.config.regression_threshold:
                severity = AnomalySeverity.HIGH
                recommendation = (
                    f"Quality regression of {drop_pct*100:.1f}% detected. "
                    "Review recent changes that may have affected quality."
                )
            else:
                continue

            anomalies.append(QualityAnomaly(
                anomaly_type=AnomalyType.REGRESSION,
                severity=severity,
                title=f"Quality Regression: {drop_pct*100:.1f}% drop",
                description=(
                    f"Score dropped from {rolling_baseline:.3f} (baseline) to "
                    f"{current_run.score:.3f} (current)"
                ),
                run_id=current_run.run_id,
                timestamp=current_run.timestamp,
                baseline_value=rolling_baseline,
                actual_value=current_run.score,
                delta=-score_drop,
                recommendation=recommendation,
            ))

        return anomalies

    def _detect_outliers(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect statistical outliers using z-score

        A run is an outlier if its score deviates significantly from the mean
        (measured in standard deviations).
        """
        anomalies = []

        if len(runs) < 3:
            return anomalies

        scores = [r.score for r in runs]
        mean_score = statistics.mean(scores)

        try:
            stdev_score = statistics.stdev(scores)
        except statistics.StatisticsError:
            return anomalies  # Need more samples for stdev

        if stdev_score == 0:
            return anomalies  # No variance

        for run in runs:
            z_score = abs((run.score - mean_score) / stdev_score)

            if z_score >= self.config.z_score_threshold:
                severity = AnomalySeverity.CRITICAL if z_score > 3.5 else AnomalySeverity.MEDIUM

                anomalies.append(QualityAnomaly(
                    anomaly_type=AnomalyType.OUTLIER,
                    severity=severity,
                    title=f"Statistical Outlier: z-score {z_score:.1f}",
                    description=(
                        f"This run's score ({run.score:.3f}) is a statistical outlier. "
                        f"Mean score: {mean_score:.3f}, Std dev: {stdev_score:.3f}"
                    ),
                    run_id=run.run_id,
                    timestamp=run.timestamp,
                    baseline_value=mean_score,
                    actual_value=run.score,
                    delta=run.score - mean_score,
                    recommendation=(
                        "Investigate this run for unusual circumstances. "
                        "It may represent a unique scenario or measurement error."
                    ),
                ))

        return anomalies

    def _detect_pass_rate_drops(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect declining pass rates over time

        Compares pass rate in recent window to earlier window.
        """
        anomalies = []
        min_runs = 10

        if len(runs) < min_runs:
            return anomalies

        # Split runs: early half vs recent half
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        mid_point = len(sorted_runs) // 2

        early_runs = sorted_runs[:mid_point]
        recent_runs = sorted_runs[mid_point:]

        early_pass_rate = sum(1 for r in early_runs if r.passed) / len(early_runs)
        recent_pass_rate = sum(1 for r in recent_runs if r.passed) / len(recent_runs)

        pass_rate_drop = early_pass_rate - recent_pass_rate

        if pass_rate_drop >= self.config.pass_rate_drop_threshold:
            severity = AnomalySeverity.HIGH if pass_rate_drop > 0.2 else AnomalySeverity.MEDIUM

            anomalies.append(QualityAnomaly(
                anomaly_type=AnomalyType.PASS_RATE_DROP,
                severity=severity,
                title=f"Pass Rate Decline: {pass_rate_drop*100:.1f}%",
                description=(
                    f"Pass rate dropped from {early_pass_rate*100:.1f}% to "
                    f"{recent_pass_rate*100:.1f}% over time"
                ),
                timestamp=datetime.now().isoformat(),
                baseline_value=early_pass_rate,
                actual_value=recent_pass_rate,
                delta=-pass_rate_drop,
                recommendation=(
                    "Pass rate is declining. Review recent changes and "
                    "consider if quality standards are too strict or if quality is actually degrading."
                ),
            ))

        return anomalies

    def _detect_stagnation(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect when quality has plateaued

        Stagnation is detected when scores show very little variance
        over a window of runs.
        """
        anomalies = []

        if len(runs) < self.config.stagnation_window:
            return anomalies

        # Check most recent runs
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        recent_runs = sorted_runs[-self.config.stagnation_window:]

        scores = [r.score for r in recent_runs]

        try:
            score_variance = statistics.variance(scores)
            score_stdev = statistics.stdev(scores)
        except statistics.StatisticsError:
            return anomalies

        if score_variance < self.config.stagnation_variance:
            avg_score = statistics.mean(scores)
            min_score = min(scores)
            max_score = max(scores)

            anomalies.append(QualityAnomaly(
                anomaly_type=AnomalyType.STAGNATION,
                severity=AnomalySeverity.LOW,
                title=f"Quality Stagnation Detected",
                description=(
                    f"Quality scores have plateaued over the last {len(recent_runs)} runs. "
                    f"Range: [{min_score:.3f}, {max_score:.3f}], Stdev: {score_stdev:.4f}"
                ),
                timestamp=datetime.now().isoformat(),
                baseline_value=avg_score,
                actual_value=avg_score,
                delta=0,
                recommendation=(
                    "Quality has stabilized. This may indicate the system has reached "
                    "its optimal state, or that improvements are needed to break through the plateau."
                ),
            ))

        return anomalies

    def _detect_category_drops(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect drops in specific category scores

        Compares recent category scores to historical baseline for each category.
        """
        anomalies = []

        # Get runs with category scores
        runs_with_categories = [r for r in runs if r.category_scores]

        if len(runs_with_categories) < 6:
            return anomalies

        # Sort by timestamp
        sorted_runs = sorted(runs_with_categories, key=lambda r: r.timestamp)
        split_point = len(sorted_runs) // 2

        baseline_runs = sorted_runs[:split_point]
        recent_runs = sorted_runs[split_point:]

        # Calculate baseline scores per category
        category_baseline: Dict[str, float] = {}
        category_counts: Dict[str, int] = {}

        for run in baseline_runs:
            if run.category_scores:
                for cat, score in run.category_scores.items():
                    if cat not in category_baseline:
                        category_baseline[cat] = 0
                        category_counts[cat] = 0
                    category_baseline[cat] += score
                    category_counts[cat] += 1

        for cat in category_baseline:
            category_baseline[cat] /= category_counts[cat]

        # Check recent runs for drops
        for run in recent_runs[-3:]:  # Check last 3 runs
            if not run.category_scores:
                continue

            for cat, baseline_score in category_baseline.items():
                current_score = run.category_scores.get(cat, baseline_score)

                score_drop = baseline_score - current_score
                drop_pct = score_drop / baseline_score if baseline_score > 0 else 0

                if drop_pct >= self.config.category_drop_threshold:
                    anomalies.append(QualityAnomaly(
                        anomaly_type=AnomalyType.CATEGORY_DROP,
                        severity=AnomalySeverity.MEDIUM,
                        title=f"Category Drop: {cat}",
                        description=(
                            f"{cat} score dropped by {drop_pct*100:.1f}% "
                            f"(from {baseline_score:.3f} to {current_score:.3f})"
                        ),
                        run_id=run.run_id,
                        timestamp=run.timestamp,
                        affected_category=cat,
                        baseline_value=baseline_score,
                        actual_value=current_score,
                        delta=-score_drop,
                        recommendation=(
                            f"Review recent changes affecting {cat} quality. "
                            "This category may need focused attention."
                        ),
                    ))

        return anomalies

    def _detect_iteration_spikes(self, runs: List[Any]) -> List[QualityAnomaly]:
        """Detect sudden increases in iteration counts

        A spike is detected when a run requires significantly more iterations
        than the historical average.
        """
        anomalies = []

        if len(runs) < 5:
            return anomalies

        # Calculate average iterations (excluding extreme outliers)
        iterations = [r.iteration for r in runs]
        mean_iterations = statistics.mean(iterations)

        try:
            stdev_iterations = statistics.stdev(iterations)
        except statistics.StatisticsError:
            stdev_iterations = 0

        for run in runs:
            iteration_ratio = run.iteration / mean_iterations if mean_iterations > 0 else 1

            if iteration_ratio >= self.config.iteration_spike_multiplier:
                severity = AnomalySeverity.MEDIUM

                anomalies.append(QualityAnomaly(
                    anomaly_type=AnomalyType.ITERATION_SPIKE,
                    severity=severity,
                    title=f"Iteration Spike: {run.iteration} iterations",
                    description=(
                        f"This run required {run.iteration} iterations, "
                        f"{iteration_ratio:.1f}x the average ({mean_iterations:.1f})"
                    ),
                    run_id=run.run_id,
                    timestamp=run.timestamp,
                    baseline_value=mean_iterations,
                    actual_value=float(run.iteration),
                    delta=run.iteration - mean_iterations,
                    recommendation=(
                        "High iteration count may indicate quality issues or "
                        "inefficient refinement. Consider adjusting quality thresholds."
                    ),
                ))

        return anomalies


# Convenience functions

def detect_anomalies(
    runs: List[Any],
    config: Optional[AnomalyDetectionConfig] = None,
    task_alias: Optional[str] = None,
) -> AnomalyReport:
    """Detect anomalies in quality run history

    Args:
        runs: List of quality run records
        config: Optional detection configuration
        task_alias: Optional task alias for reporting

    Returns:
        AnomalyReport with detected anomalies
    """
    detector = QualityAnomalyDetector(config)
    return detector.detect_all(runs, task_alias)


def format_anomaly_report(
    report: AnomalyReport,
    task_alias: Optional[str] = None,
) -> str:
    """Format anomaly report for display

    Args:
        report: AnomalyReport to format
        task_alias: Optional task alias for title

    Returns:
        Formatted report string
    """
    lines = []
    title = f"Anomaly Report for '{task_alias}'" if task_alias else "Quality Anomaly Report"
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"**Analyzed:** {report.total_runs_analyzed} runs")
    lines.append(f"**Detected:** {report.anomalies_detected} anomalies")
    lines.append(f"**Timestamp:** {report.analysis_timestamp}")
    lines.append("")

    if report.anomalies_by_severity:
        lines.append("**Severity Breakdown:**")
        for sev, count in sorted(report.anomalies_by_severity.items(), key=lambda x: -len(x[0])):
            lines.append(f"  - {sev.upper()}: {count}")
        lines.append("")

    if not report.anomalies:
        lines.append("*No anomalies detected. Quality metrics look healthy!*")
    else:
        lines.append("### Detected Anomalies")
        lines.append("")

        for anomaly in report.anomalies:
            severity_emoji = {
                AnomalySeverity.CRITICAL: "🚨",
                AnomalySeverity.HIGH: "⚠️",
                AnomalySeverity.MEDIUM: "⚡",
                AnomalySeverity.LOW: "💡",
                AnomalySeverity.INFO: "ℹ️",
            }
            emoji = severity_emoji.get(anomaly.severity, "")

            lines.append(f"{emoji} **{anomaly.title}** [{anomaly.severity.value.upper()}]")
            lines.append(f"   {anomaly.description}")

            if anomaly.run_id:
                lines.append(f"   Run ID: `{anomaly.run_id}`")
            if anomaly.recommendation:
                lines.append(f"   💡 {anomaly.recommendation}")

            lines.append("")

    return "\n".join(lines)


def format_anomalies_json(report: AnomalyReport, indent: int = 2) -> str:
    """Format anomaly report as JSON for CI/CD integration

    Args:
        report: AnomalyReport to format
        indent: JSON indentation

    Returns:
        JSON string
    """
    return json.dumps(report.to_dict(), indent=indent)


def get_anomaly_summary(report: AnomalyReport) -> str:
    """Get a one-line summary of anomalies

    Args:
        report: AnomalyReport

    Returns:
        Summary string
    """
    critical = report.anomalies_by_severity.get("critical", 0)
    high = report.anomalies_by_severity.get("high", 0)

    if critical > 0:
        return f"CRITICAL: {critical} critical, {high} high severity anomalies detected"
    elif high > 0:
        return f"WARNING: {high} high severity anomalies detected"
    elif report.anomalies_detected > 0:
        return f"INFO: {report.anomalies_detected} anomalies detected"
    else:
        return "OK: No anomalies detected"


def list_anomaly_types() -> str:
    """List all available anomaly types with descriptions

    Returns:
        Formatted string of anomaly types
    """
    descriptions = {
        AnomalyType.REGRESSION: "Score drop compared to rolling baseline",
        AnomalyType.OUTLIER: "Statistical outlier using z-score analysis",
        AnomalyType.PASS_RATE_DROP: "Declining pass rate over time",
        AnomalyType.STAGNATION: "Quality plateaued (no improvement)",
        AnomalyType.CATEGORY_DROP: "Specific category score drop",
        AnomalyType.ITERATION_SPIKE: "Sudden increase in iteration count",
    }

    lines = ["Available Anomaly Types:", ""]
    for anomaly_type in AnomalyType:
        desc = descriptions.get(anomaly_type, "")
        lines.append(f"  {anomaly_type.value:20s} - {desc}")

    return "\n".join(lines)


def format_config(config: AnomalyDetectionConfig) -> str:
    """Format anomaly detection configuration for display

    Args:
        config: AnomalyDetectionConfig to format

    Returns:
        Formatted configuration string
    """
    lines = ["Anomaly Detection Configuration:", ""]
    lines.append(f"  Regression threshold: {config.regression_threshold*100:.1f}% (critical: {config.regression_critical*100:.1f}%)")
    lines.append(f"  Z-score threshold: {config.z_score_threshold}")
    lines.append(f"  Pass rate drop threshold: {config.pass_rate_drop_threshold*100:.1f}%")
    lines.append(f"  Stagnation window: {config.stagnation_window} runs (variance: {config.stagnation_variance*100:.1f}%)")
    lines.append(f"  Iteration spike multiplier: {config.iteration_spike_multiplier}x")
    lines.append(f"  Category drop threshold: {config.category_drop_threshold*100:.1f}%")

    return "\n".join(lines)


def get_anomaly_recommendations(
    report: AnomalyReport,
    min_severity: Optional[AnomalySeverity] = None,
    anomaly_type: Optional[AnomalyType] = None,
    category: Optional[str] = None,
) -> str:
    """Get actionable recommendations for detected anomalies

    Args:
        report: AnomalyReport with detected anomalies
        min_severity: Minimum severity to include (None = all)
        anomaly_type: Filter by anomaly type (None = all)
        category: Filter by category (None = all)

    Returns:
        Formatted recommendations string
    """
    # Filter anomalies
    filtered = []
    for anomaly in report.anomalies:
        if min_severity:
            severity_order = {
                AnomalySeverity.CRITICAL: 5,
                AnomalySeverity.HIGH: 4,
                AnomalySeverity.MEDIUM: 3,
                AnomalySeverity.LOW: 2,
                AnomalySeverity.INFO: 1,
            }
            if severity_order.get(anomaly.severity, 0) < severity_order.get(min_severity, 0):
                continue

        if anomaly_type and anomaly.anomaly_type != anomaly_type:
            continue

        if category and anomaly.affected_category != category:
            continue

        filtered.append(anomaly)

    if not filtered:
        return "No anomalies match the specified filters."

    # Group recommendations by type
    by_type: Dict[str, List[QualityAnomaly]] = {}
    for anomaly in filtered:
        type_name = anomaly.anomaly_type.value.replace("_", " ").title()
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(anomaly)

    lines = ["Anomaly Recommendations:", ""]

    for type_name, anomalies in by_type.items():
        lines.append(f"### {type_name}")
        lines.append("")

        for anomaly in anomalies:
            lines.append(f"**{anomaly.title}** [{anomaly.severity.value.upper()}]")
            if anomaly.recommendation:
                lines.append(f"  → {anomaly.recommendation}")
            lines.append("")

    return "\n".join(lines)


def get_anomaly_statistics(
    report: AnomalyReport,
    group_by: str = "severity",  # "severity", "type", "category"
) -> str:
    """Get statistics about detected anomalies

    Args:
        report: AnomalyReport with detected anomalies
        group_by: How to group statistics

    Returns:
        Formatted statistics string
    """
    if report.anomalies_detected == 0:
        return "No anomalies detected."

    lines = ["Anomaly Statistics:", ""]

    if group_by == "severity":
        lines.append("**By Severity:**")
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = report.anomalies_by_severity.get(sev, 0)
            if count > 0:
                percentage = (count / report.anomalies_detected) * 100
                lines.append(f"  {sev.upper():10s}: {count:3d} ({percentage:5.1f}%)")

    elif group_by == "type":
        type_counts: Dict[str, int] = {}
        for anomaly in report.anomalies:
            type_name = anomaly.anomaly_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        lines.append("**By Type:**")
        for type_name, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            percentage = (count / report.anomalies_detected) * 100
            display_name = type_name.replace("_", " ").title()
            lines.append(f"  {display_name:20s}: {count:3d} ({percentage:5.1f}%)")

    elif group_by == "category":
        category_counts: Dict[str, int] = {}
        for anomaly in report.anomalies:
            if anomaly.affected_category:
                cat = anomaly.affected_category
                category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            lines.append("**By Category:**")
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
                percentage = (count / report.anomalies_detected) * 100
                lines.append(f"  {cat:20s}: {count:3d} ({percentage:5.1f}%)")
        else:
            lines.append("No category-specific anomalies detected.")

    lines.append("")
    lines.append(f"Total anomalies: {report.anomalies_detected}")
    lines.append(f"Total runs analyzed: {report.total_runs_analyzed}")

    return "\n".join(lines)


def filter_anomalies(
    report: AnomalyReport,
    min_severity: Optional[AnomalySeverity] = None,
    anomaly_type: Optional[AnomalyType] = None,
    category: Optional[str] = None,
) -> AnomalyReport:
    """Filter anomalies by severity, type, or category

    Args:
        report: Original AnomalyReport
        min_severity: Minimum severity to include
        anomaly_type: Filter by anomaly type
        category: Filter by category

    Returns:
        Filtered AnomalyReport
    """
    filtered = []
    for anomaly in report.anomalies:
        if min_severity:
            severity_order = {
                AnomalySeverity.CRITICAL: 5,
                AnomalySeverity.HIGH: 4,
                AnomalySeverity.MEDIUM: 3,
                AnomalySeverity.LOW: 2,
                AnomalySeverity.INFO: 1,
            }
            if severity_order.get(anomaly.severity, 0) < severity_order.get(min_severity, 0):
                continue

        if anomaly_type and anomaly.anomaly_type != anomaly_type:
            continue

        if category and anomaly.affected_category != category:
            continue

        filtered.append(anomaly)

    # Recalculate severity counts
    severity_counts: Dict[str, int] = {}
    for anomaly in filtered:
        sev = anomaly.severity.value
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return AnomalyReport(
        anomalies_detected=len(filtered),
        anomalies_by_severity=severity_counts,
        anomalies=filtered,
        total_runs_analyzed=report.total_runs_analyzed,
        analysis_timestamp=report.analysis_timestamp,
        task_alias=report.task_alias,
    )


def export_anomalies_csv(report: AnomalyReport) -> str:
    """Export anomalies as CSV format

    Args:
        report: AnomalyReport to export

    Returns:
        CSV string
    """
    lines = ["type,severity,title,description,run_id,category,baseline,actual,delta,recommendation"]

    for anomaly in report.anomalies:
        run_id = anomaly.run_id or ""
        category = anomaly.affected_category or ""
        baseline = str(anomaly.baseline_value) if anomaly.baseline_value is not None else ""
        actual = str(anomaly.actual_value) if anomaly.actual_value is not None else ""
        delta = str(anomaly.delta) if anomaly.delta is not None else ""
        recommendation = (anomaly.recommendation or "").replace(",", ";").replace("\n", " ")

        lines.append(
            f"{anomaly.anomaly_type.value},"
            f"{anomaly.severity.value},"
            f'"{anomaly.title}",'
            f'"{anomaly.description}",'
            f'"{run_id}",'
            f'"{category}",'
            f"{baseline},"
            f"{actual},"
            f"{delta},"
            f'"{recommendation}"'
        )

    return "\n".join(lines)


# ============================================================================
# Anomaly Risk Scoring System (Exp 111)
# ============================================================================

@dataclass
class AnomalyRiskScore:
    """Risk score for a single anomaly

    Combines multiple factors into a single 0-100 risk score:
    - Severity weight: Critical=100, High=75, Medium=50, Low=25, Info=10
    - Type impact: Regression=1.5, Outlier=1.3, Category Drop=1.2, others=1.0
    - Delta magnitude: Larger score drops increase risk
    - Frequency: Recurring anomalies get higher risk

    Risk Level: Critical (80-100), High (60-79), Medium (40-59), Low (20-39), Info (0-19)
    """
    score: float  # 0-100
    risk_level: str  # critical, high, medium, low, info
    severity_weight: float
    type_multiplier: float
    delta_impact: float
    frequency_boost: float
    factors: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "score": round(self.score, 2),
            "risk_level": self.risk_level,
            "severity_weight": round(self.severity_weight, 2),
            "type_multiplier": round(self.type_multiplier, 2),
            "delta_impact": round(self.delta_impact, 2),
            "frequency_boost": round(self.frequency_boost, 2),
            "factors": self.factors,
        }


class AnomalyRiskScorer:
    """Calculates risk scores for anomalies based on multiple factors

    Risk Score Formula:
        score = (severity_weight * type_multiplier) + delta_impact + frequency_boost

    Where:
    - severity_weight: Base score from severity level
    - type_multiplier: Adjusts based on anomaly type impact
    - delta_impact: Additional risk from magnitude of change
    - frequency_boost: Increased risk for recurring patterns

    This enables prioritization of anomalies for remediation efforts.
    """

    # Severity base weights (0-100 scale)
    SEVERITY_WEIGHTS = {
        AnomalySeverity.CRITICAL: 100.0,
        AnomalySeverity.HIGH: 75.0,
        AnomalySeverity.MEDIUM: 50.0,
        AnomalySeverity.LOW: 25.0,
        AnomalySeverity.INFO: 10.0,
    }

    # Type multipliers based on business impact
    TYPE_MULTIPLIERS = {
        AnomalyType.REGRESSION: 1.5,  # Quality regression is most impactful
        AnomalyType.OUTLIER: 1.3,     # Statistical outliers need investigation
        AnomalyType.CATEGORY_DROP: 1.2,  # Category-specific issues
        AnomalyType.PASS_RATE_DROP: 1.2,
        AnomalyType.ITERATION_SPIKE: 1.1,
        AnomalyType.STAGNATION: 1.0,  # Lower urgency
    }

    def __init__(
        self,
        severity_weights: Optional[Dict[AnomalySeverity, float]] = None,
        type_multipliers: Optional[Dict[AnomalyType, float]] = None,
        delta_scale: float = 50.0,  # How much delta impacts score
        frequency_scale: float = 10.0,  # How much frequency impacts score
    ):
        """Initialize risk scorer

        Args:
            severity_weights: Custom severity weights (uses defaults if None)
            type_multipliers: Custom type multipliers (uses defaults if None)
            delta_scale: Scaling factor for delta impact
            frequency_scale: Scaling factor for frequency boost
        """
        self.severity_weights = severity_weights or self.SEVERITY_WEIGHTS
        self.type_multipliers = type_multipliers or self.TYPE_MULTIPLIERS
        self.delta_scale = delta_scale
        self.frequency_scale = frequency_scale

    def score_anomaly(
        self,
        anomaly: QualityAnomaly,
        historical_count: int = 0,
    ) -> AnomalyRiskScore:
        """Calculate risk score for a single anomaly

        Args:
            anomaly: Anomaly to score
            historical_count: How many times this anomaly type occurred recently

        Returns:
            AnomalyRiskScore with calculated risk
        """
        # Base score from severity
        severity_weight = self.severity_weights.get(anomaly.severity, 50.0)

        # Type multiplier
        type_multiplier = self.type_multipliers.get(anomaly.anomaly_type, 1.0)

        # Delta impact (magnitude of change)
        delta_impact = 0.0
        if anomaly.delta is not None:
            # Normalize delta to 0-1 range, then scale
            delta_abs = abs(anomaly.delta)
            delta_impact = min(delta_abs * 10, self.delta_scale)

        # Frequency boost (recurring anomalies get higher risk)
        frequency_boost = min(historical_count * self.frequency_scale, 20.0)

        # Calculate final score
        # Formula combines weighted severity with impacts
        base_score = severity_weight * type_multiplier
        score = min(base_score + delta_impact + frequency_boost, 100.0)

        # Determine risk level
        risk_level = self._get_risk_level(score)

        # Build factors dict for transparency
        factors = {
            "base_severity": severity_weight,
            "type_adjustment": (type_multiplier - 1.0) * severity_weight,
            "delta_contribution": delta_impact,
            "frequency_contribution": frequency_boost,
        }

        return AnomalyRiskScore(
            score=score,
            risk_level=risk_level,
            severity_weight=severity_weight,
            type_multiplier=type_multiplier,
            delta_impact=delta_impact,
            frequency_boost=frequency_boost,
            factors=factors,
        )

    def score_report(
        self,
        report: AnomalyReport,
        historical_counts: Optional[Dict[str, int]] = None,
    ) -> Dict[str, AnomalyRiskScore]:
        """Calculate risk scores for all anomalies in a report

        Args:
            report: AnomalyReport with anomalies to score
            historical_counts: Optional historical occurrence counts by anomaly type

        Returns:
            Dict mapping anomaly title to risk score
        """
        risk_scores = {}

        for anomaly in report.anomalies:
            # Get historical count for this anomaly type
            hist_count = 0
            if historical_counts:
                type_key = anomaly.anomaly_type.value
                hist_count = historical_counts.get(type_key, 0)

            risk_score = self.score_anomaly(anomaly, hist_count)
            risk_scores[anomaly.title] = risk_score

        return risk_scores

    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "info"

    def get_top_risks(
        self,
        risk_scores: Dict[str, AnomalyRiskScore],
        limit: int = 5,
    ) -> List[Tuple[str, AnomalyRiskScore]]:
        """Get top N riskiest anomalies

        Args:
            risk_scores: Dict of anomaly titles to risk scores
            limit: Maximum number to return

        Returns:
            List of (title, risk_score) tuples sorted by risk (descending)
        """
        sorted_items = sorted(
            risk_scores.items(),
            key=lambda x: x[1].score,
            reverse=True,
        )
        return sorted_items[:limit]

    def get_risk_summary(
        self,
        risk_scores: Dict[str, AnomalyRiskScore],
    ) -> Dict[str, int]:
        """Get count of anomalies by risk level

        Args:
            risk_scores: Dict of anomaly titles to risk scores

        Returns:
            Dict with counts by risk level
        """
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for risk_score in risk_scores.values():
            summary[risk_score.risk_level] += 1

        return summary


# Enhanced QualityAnomaly with risk scoring support

def enrich_anomalies_with_risk(
    report: AnomalyReport,
    scorer: Optional[AnomalyRiskScorer] = None,
    historical_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, AnomalyRiskScore]:
    """Enrich anomaly report with risk scores

    Args:
        report: AnomalyReport to enrich
        scorer: Custom scorer (uses default if None)
        historical_counts: Optional historical occurrence counts

    Returns:
        Dict mapping anomaly titles to risk scores
    """
    if scorer is None:
        scorer = AnomalyRiskScorer()

    return scorer.score_report(report, historical_counts)


def format_risk_scores_text(
    risk_scores: Dict[str, AnomalyRiskScore],
    top_n: int = 10,
) -> str:
    """Format risk scores as readable text

    Args:
        risk_scores: Dict of anomaly titles to risk scores
        top_n: Number of top risks to show

    Returns:
        Formatted text report
    """
    scorer = AnomalyRiskScorer()
    top_risks = scorer.get_top_risks(risk_scores, limit=top_n)
    summary = scorer.get_risk_summary(risk_scores)

    lines = [
        "## Anomaly Risk Assessment",
        "",
        f"**Total Anomalies:** {len(risk_scores)}",
        "",
        "**Risk Distribution:**",
    ]

    for level in ["critical", "high", "medium", "low", "info"]:
        count = summary.get(level, 0)
        if count > 0:
            emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "💡", "info": "ℹ️"}
            lines.append(f"  {emoji.get(level, '')} {level.upper()}: {count}")

    lines.extend(["", "### Top Priority Risks", ""])

    for i, (title, risk) in enumerate(top_risks, 1):
        lines.append(
            f"{i}. **{title}** - Risk: {risk.score:.1f}/100 [{risk.risk_level.upper()}]"
        )
        lines.append(f"   - Severity weight: {risk.severity_weight:.1f}")
        lines.append(f"   - Type multiplier: {risk.type_multiplier:.2f}x")
        if risk.delta_impact > 0:
            lines.append(f"   - Delta impact: +{risk.delta_impact:.1f}")
        if risk.frequency_boost > 0:
            lines.append(f"   - Frequency boost: +{risk.frequency_boost:.1f}")
        lines.append("")

    return "\n".join(lines)


def export_risk_scores_csv(
    report: AnomalyReport,
    risk_scores: Dict[str, AnomalyRiskScore],
) -> str:
    """Export anomaly risk scores as CSV

    Args:
        report: AnomalyReport with anomalies
        risk_scores: Risk scores for anomalies

    Returns:
        CSV string
    """
    lines = [
        "title,type,severity,risk_score,risk_level,"
        "severity_weight,type_multiplier,delta_impact,frequency_boost"
    ]

    for anomaly in report.anomalies:
        risk = risk_scores.get(anomaly.title)
        if not risk:
            continue

        lines.append(
            f'"{anomaly.title}",'
            f"{anomaly.anomaly_type.value},"
            f"{anomaly.severity.value},"
            f"{risk.score:.2f},"
            f"{risk.risk_level},"
            f"{risk.severity_weight:.2f},"
            f"{risk.type_multiplier:.2f},"
            f"{risk.delta_impact:.2f},"
            f"{risk.frequency_boost:.2f}"
        )

    return "\n".join(lines)
