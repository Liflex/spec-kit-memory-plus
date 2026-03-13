"""
Quality Feedback Loop System (Exp 87)

Adaptive configuration system that learns from quality loop results
and continuously improves configuration recommendations.

Key features:
- Collects and analyzes quality loop results
- Detects performance patterns and trends
- Recommends configuration adjustments
- Provides actionable improvement insights
- Integrates with SmartConfigRecommender (Exp 84)

Usage:
    analyzer = FeedbackAnalyzer()
    insights = analyzer.analyze_results(results)
    adjustments = analyzer.recommend_adjustments(insights)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
import json
from statistics import mean, median, stdev
from collections import defaultdict, Counter


class TrendDirection(Enum):
    """Trend direction for metrics"""
    IMPROVING = "improving"     # Getting better
    DECLINING = "declining"     # Getting worse
    STABLE = "stable"           # No significant change
    VOLATILE = "volatile"       # Too much variation


class AdjustmentType(Enum):
    """Types of configuration adjustments"""
    INCREASE_THRESHOLD = "increase_threshold"    # Raise quality bar
    DECREASE_THRESHOLD = "decrease_threshold"    # Lower for faster iteration
    ADD_CRITERION = "add_criterion"              # Add quality check
    REMOVE_CRITERION = "remove_criterion"        # Remove quality check
    ADJUST_ITERATIONS = "adjust_iterations"      # Change loop iterations
    CHANGE_PROFILE = "change_profile"            # Switch priority profile
    ADJUST_GOALS = "adjust_goals"                # Modify quality targets
    ADD_CATEGORY_FOCUS = "add_category_focus"    # Focus on weak area


class InsightPriority(Enum):
    """Priority level for insights"""
    CRITICAL = "critical"     # Immediate action needed
    HIGH = "high"            # Important improvement
    MEDIUM = "medium"        # Worth considering
    LOW = "low"              # Minor optimization


@dataclass
class QualityResult:
    """Single quality loop result for analysis"""
    timestamp: datetime
    score: float
    passed: bool
    iteration_count: int
    criteria: List[str]
    category_scores: Dict[str, float]
    failed_rules: List[str]
    warnings: List[str]
    config_id: Optional[str] = None
    task_alias: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "score": self.score,
            "passed": self.passed,
            "iteration_count": self.iteration_count,
            "criteria": self.criteria,
            "category_scores": self.category_scores,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "config_id": self.config_id,
            "task_alias": self.task_alias,
            "metadata": self.metadata,
        }


@dataclass
class TrendAnalysis:
    """Analysis of metric trends over time"""
    metric_name: str
    direction: TrendDirection
    current_value: float
    baseline_value: float
    change_percent: float
    change_abs: float
    confidence: float
    velocity: float  # Rate of change per run
    sample_size: int
    is_significant: bool


@dataclass
class QualityInsight:
    """Insight about quality performance"""
    category: str
    title: str
    description: str
    priority: InsightPriority
    evidence: List[str]
    impact_score: float  # 0-1, potential impact
    effort_estimate: str  # "low", "medium", "high"
    suggested_actions: List[str]


@dataclass
class ConfigurationAdjustment:
    """Suggested configuration adjustment"""
    adjustment_type: AdjustmentType
    description: str
    current_value: Any
    suggested_value: Any
    reason: str
    expected_impact: str
    confidence: float
    rollback_plan: str


@dataclass
class FeedbackReport:
    """Complete feedback analysis report"""
    analysis_period: Tuple[datetime, datetime]
    total_runs: int
    overall_trend: TrendAnalysis
    category_trends: Dict[str, TrendAnalysis]
    insights: List[QualityInsight]
    adjustments: List[ConfigurationAdjustment]
    weak_areas: List[str]
    strong_areas: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "analysis_period": {
                "start": self.analysis_period[0].isoformat(),
                "end": self.analysis_period[1].isoformat(),
            },
            "total_runs": self.total_runs,
            "overall_trend": {
                "metric_name": self.overall_trend.metric_name,
                "direction": self.overall_trend.direction.value,
                "current_value": self.overall_trend.current_value,
                "baseline_value": self.overall_trend.baseline_value,
                "change_percent": round(self.overall_trend.change_percent, 2),
                "velocity": round(self.overall_trend.velocity, 3),
                "is_significant": self.overall_trend.is_significant,
            },
            "category_trends": {
                cat: {
                    "direction": trend.direction.value,
                    "current": trend.current_value,
                    "change_percent": round(trend.change_percent, 2),
                }
                for cat, trend in self.category_trends.items()
            },
            "insights": [
                {
                    "category": ins.category,
                    "title": ins.title,
                    "priority": ins.priority.value,
                    "impact_score": round(ins.impact_score, 2),
                    "suggested_actions": ins.suggested_actions,
                }
                for ins in self.insights
            ],
            "adjustments": [
                {
                    "type": adj.adjustment_type.value,
                    "description": adj.description,
                    "confidence": round(adj.confidence, 2),
                }
                for adj in self.adjustments
            ],
            "weak_areas": self.weak_areas,
            "strong_areas": self.strong_areas,
            "recommendations": self.recommendations,
        }


class FeedbackAnalyzer:
    """
    Analyzes quality loop results and provides actionable insights.
    """

    # Minimum runs needed for meaningful analysis
    MIN_RUNS_FOR_TREND = 3
    MIN_RUNS_FOR_CONFIDENCE = 10

    # Significance thresholds
    SIGNIFICANT_CHANGE_THRESHOLD = 0.05  # 5% change
    HIGH_VELOCITY_THRESHOLD = 0.02  # 2% per run
    VOLATILITY_THRESHOLD = 0.15  # Std dev > 15%

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize feedback analyzer

        Args:
            storage_path: Path to store/load results. Defaults to .speckit/feedback/
        """
        if storage_path is None:
            storage_path = Path.cwd() / ".speckit" / "feedback"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._results_cache: List[QualityResult] = []

    def collect_result(self, result: QualityResult) -> None:
        """Collect a quality loop result for analysis

        Args:
            result: QualityResult to store
        """
        self._results_cache.append(result)
        self._save_result(result)

    def analyze_results(
        self,
        task_alias: Optional[str] = None,
        lookback_runs: int = 20,
    ) -> FeedbackReport:
        """Analyze collected quality results

        Args:
            task_alias: Filter results by task alias (optional)
            lookback_runs: Number of recent results to analyze

        Returns:
            FeedbackReport with insights and recommendations
        """
        # Load results
        results = self._load_results(task_alias=task_alias)

        if len(results) < self.MIN_RUNS_FOR_TREND:
            return self._insufficient_data_report(results)

        # Limit to lookback_runs
        results = results[-lookback_runs:]

        # Analyze trends
        overall_trend = self._analyze_score_trend(results)
        category_trends = self._analyze_category_trends(results)

        # Generate insights
        insights = self._generate_insights(results, overall_trend, category_trends)

        # Recommend adjustments
        adjustments = self._recommend_adjustments(
            results, overall_trend, category_trends, insights
        )

        # Identify weak/strong areas
        weak_areas, strong_areas = self._identify_areas(results, category_trends)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            insights, adjustments, weak_areas, strong_areas
        )

        # Determine analysis period
        if results:
            analysis_period = (results[0].timestamp, results[-1].timestamp)
        else:
            now = datetime.now()
            analysis_period = (now, now)

        return FeedbackReport(
            analysis_period=analysis_period,
            total_runs=len(results),
            overall_trend=overall_trend,
            category_trends=category_trends,
            insights=insights,
            adjustments=adjustments,
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            recommendations=recommendations,
        )

    def _analyze_score_trend(self, results: List[QualityResult]) -> TrendAnalysis:
        """Analyze overall score trend"""
        scores = [r.score for r in results]
        current = scores[-1]
        baseline = scores[0]

        change_abs = current - baseline
        change_percent = (change_abs / baseline * 100) if baseline > 0 else 0

        # Calculate velocity (average change per run)
        velocity = change_abs / len(results) if len(results) > 1 else 0

        # Determine direction
        if change_percent > self.SIGNIFICANT_CHANGE_THRESHOLD * 100:
            direction = TrendDirection.IMPROVING
        elif change_percent < -self.SIGNIFICANT_CHANGE_THRESHOLD * 100:
            direction = TrendDirection.DECLINING
        else:
            direction = TrendDirection.STABLE

        # Check for volatility
        if len(scores) >= self.MIN_RUNS_FOR_CONFIDENCE:
            try:
                volatility = stdev(scores) / mean(scores) if mean(scores) > 0 else 0
                if volatility > self.VOLATILITY_THRESHOLD:
                    direction = TrendDirection.VOLATILE
            except:
                pass

        # Confidence based on sample size
        confidence = min(1.0, len(results) / self.MIN_RUNS_FOR_CONFIDENCE)

        return TrendAnalysis(
            metric_name="overall_score",
            direction=direction,
            current_value=current,
            baseline_value=baseline,
            change_percent=change_percent,
            change_abs=change_abs,
            confidence=confidence,
            velocity=velocity,
            sample_size=len(results),
            is_significant=abs(change_percent) >= self.SIGNIFICANT_CHANGE_THRESHOLD * 100,
        )

    def _analyze_category_trends(
        self, results: List[QualityResult]
    ) -> Dict[str, TrendAnalysis]:
        """Analyze trends for each quality category"""
        category_trends = {}

        # Collect category scores across all results
        category_scores = defaultdict(list)
        for result in results:
            for cat, score in result.category_scores.items():
                category_scores[cat].append(score)

        # Analyze each category
        for cat, scores in category_scores.items():
            if len(scores) < self.MIN_RUNS_FOR_TREND:
                continue

            current = scores[-1]
            baseline = scores[0]

            change_abs = current - baseline
            change_percent = (change_abs / baseline * 100) if baseline > 0 else 0
            velocity = change_abs / len(scores)

            # Determine direction
            if change_percent > self.SIGNIFICANT_CHANGE_THRESHOLD * 100:
                direction = TrendDirection.IMPROVING
            elif change_percent < -self.SIGNIFICANT_CHANGE_THRESHOLD * 100:
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.STABLE

            confidence = min(1.0, len(scores) / self.MIN_RUNS_FOR_CONFIDENCE)

            category_trends[cat] = TrendAnalysis(
                metric_name=f"{cat}_score",
                direction=direction,
                current_value=current,
                baseline_value=baseline,
                change_percent=change_percent,
                change_abs=change_abs,
                confidence=confidence,
                velocity=velocity,
                sample_size=len(scores),
                is_significant=abs(change_percent) >= self.SIGNIFICANT_CHANGE_THRESHOLD * 100,
            )

        return category_trends

    def _generate_insights(
        self,
        results: List[QualityResult],
        overall_trend: TrendAnalysis,
        category_trends: Dict[str, TrendAnalysis],
    ) -> List[QualityInsight]:
        """Generate actionable insights from analysis"""
        insights = []

        # Overall trend insight
        if overall_trend.direction == TrendDirection.IMPROVING:
            insights.append(QualityInsight(
                category="overall",
                title="Quality Improving",
                description=f"Quality score has improved by {overall_trend.change_percent:.1f}% over {overall_trend.sample_size} runs.",
                priority=InsightPriority.MEDIUM,
                evidence=[
                    f"Current score: {overall_trend.current_value:.2f}",
                    f"Baseline: {overall_trend.baseline_value:.2f}",
                    f"Velocity: {overall_trend.velocity:.3f} per run",
                ],
                impact_score=0.5,
                effort_estimate="low",
                suggested_actions=[
                    "Continue current quality practices",
                    "Consider increasing quality targets for further improvement",
                ],
            ))
        elif overall_trend.direction == TrendDirection.DECLINING:
            insights.append(QualityInsight(
                category="overall",
                title="Quality Declining",
                description=f"Quality score has declined by {abs(overall_trend.change_percent):.1f}% over {overall_trend.sample_size} runs.",
                priority=InsightPriority.CRITICAL,
                evidence=[
                    f"Current score: {overall_trend.current_value:.2f}",
                    f"Baseline: {overall_trend.baseline_value:.2f}",
                    f"Decline rate: {abs(overall_trend.velocity):.3f} per run",
                ],
                impact_score=0.9,
                effort_estimate="medium",
                suggested_actions=[
                    "Review recent specification changes",
                    "Check for failing quality rules",
                    "Consider increasing iteration count",
                    "Verify quality criteria alignment",
                ],
            ))
        elif overall_trend.direction == TrendDirection.VOLATILE:
            insights.append(QualityInsight(
                category="overall",
                title="Quality Volatile",
                description="Quality scores are showing high volatility. Results are inconsistent.",
                priority=InsightPriority.HIGH,
                evidence=[
                    f"Score variation detected across {overall_trend.sample_size} runs",
                    f"Consider standardizing specification process",
                ],
                impact_score=0.7,
                effort_estimate="medium",
                suggested_actions=[
                    "Review specification process consistency",
                    "Check for varying input quality",
                    "Consider stricter quality gates",
                ],
            ))

        # Category-specific insights
        for cat, trend in category_trends.items():
            if trend.direction == TrendDirection.DECLINING and trend.is_significant:
                insights.append(QualityInsight(
                    category=cat,
                    title=f"{cat.title()} Quality Declining",
                    description=f"{cat.title()} quality has declined by {abs(trend.change_percent):.1f}%. This area needs attention.",
                    priority=InsightPriority.HIGH,
                    evidence=[
                        f"Current: {trend.current_value:.2f}",
                        f"Baseline: {trend.baseline_value:.2f}",
                        f"Decline: {abs(trend.change_percent):.1f}%",
                    ],
                    impact_score=0.8,
                    effort_estimate="medium",
                    suggested_actions=[
                        f"Review {cat}-specific quality rules",
                        f"Add more iterations for {cat} refinement",
                        f"Consider increasing {cat} category weight in priority profile",
                    ],
                ))

        # Iteration efficiency insight
        avg_iterations = mean(r.iteration_count for r in results)
        max_iterations = max(r.iteration_count for r in results)

        if avg_iterations >= max_iterations * 0.9:
            insights.append(QualityInsight(
                category="efficiency",
                title="Max Iterations Frequently Reached",
                description=f"Quality loop is using {avg_iterations:.1f} iterations on average (max: {max_iterations}). Consider increasing max_iterations.",
                priority=InsightPriority.MEDIUM,
                evidence=[
                    f"Average iterations: {avg_iterations:.1f}",
                    f"Max configured: {max_iterations}",
                ],
                impact_score=0.6,
                effort_estimate="low",
                suggested_actions=[
                    "Increase max_iterations to allow more refinement",
                    "Review if criteria are too strict",
                    "Consider adjusting threshold_a/threshold_b",
                ],
            ))

        return insights

    def _recommend_adjustments(
        self,
        results: List[QualityResult],
        overall_trend: TrendAnalysis,
        category_trends: Dict[str, TrendAnalysis],
        insights: List[QualityInsight],
    ) -> List[ConfigurationAdjustment]:
        """Recommend configuration adjustments"""
        adjustments = []

        # Get current config from most recent result
        if not results:
            return adjustments

        latest = results[-1]
        current_threshold_a = 0.8
        current_threshold_b = 0.9
        current_iterations = 4

        # Threshold adjustments based on trend
        if overall_trend.direction == TrendDirection.IMPROVING:
            # Quality is good, can raise the bar
            if overall_trend.current_value > 0.85:
                adjustments.append(ConfigurationAdjustment(
                    adjustment_type=AdjustmentType.INCREASE_THRESHOLD,
                    description="Increase quality thresholds to drive further improvement",
                    current_value=f"Threshold A: {current_threshold_a}, B: {current_threshold_b}",
                    suggested_value=f"Threshold A: {current_threshold_a + 0.05}, B: {current_threshold_b + 0.05}",
                    reason=f"Quality is consistently high ({overall_trend.current_value:.2f}). Raise thresholds for continuous improvement.",
                    expected_impact="Higher quality specifications, may require more iterations",
                    confidence=0.7,
                    rollback_plan="Reduce thresholds if iteration count increases significantly",
                ))

        elif overall_trend.direction == TrendDirection.DECLINING:
            # Quality is dropping, might need to lower threshold or add iterations
            adjustments.append(ConfigurationAdjustment(
                adjustment_type=AdjustmentType.ADJUST_ITERATIONS,
                description="Increase iterations to allow more refinement time",
                current_value=f"Iterations: {current_iterations}",
                suggested_value=f"Iterations: {current_iterations + 2}",
                reason=f"Quality is declining. More iterations may help achieve target quality.",
                expected_impact="Better quality results, longer evaluation time",
                confidence=0.6,
                rollback_plan="Reduce iterations if quality doesn't improve",
            ))

        # Category focus adjustments
        weak_cats = [
            cat for cat, trend in category_trends.items()
            if trend.direction == TrendDirection.DECLINING
        ]
        if weak_cats:
            adjustments.append(ConfigurationAdjustment(
                adjustment_type=AdjustmentType.ADD_CATEGORY_FOCUS,
                description=f"Increase focus on weak areas: {', '.join(weak_cats)}",
                current_value="Balanced profile",
                suggested_value=f"{' + '.join(weak_cats)}-focused profile",
                reason=f"These categories show declining trends and need attention.",
                expected_impact=f"Improved {', '.join(weak_cats)} quality",
                confidence=0.7,
                rollback_plan="Revert to balanced profile after improvement",
            ))

        # Criteria adjustments based on failures
        failure_counts = Counter()
        for result in results:
            for rule in result.failed_rules:
                failure_counts[rule] += 1

        common_failures = [
            (rule, count) for rule, count in failure_counts.most_common(5)
            if count >= len(results) * 0.3  # Fails in 30%+ of runs
        ]

        if common_failures:
            failing_rules = [rule for rule, _ in common_failures]
            adjustments.append(ConfigurationAdjustment(
                adjustment_type=AdjustmentType.ADD_CRITERION,
                description=f"Add focus on commonly failing rules: {', '.join(failing_rules[:3])}",
                current_value="Standard criteria evaluation",
                suggested_value="Enhanced evaluation with failing-rule focus",
                reason=f"These rules consistently fail and need targeted attention.",
                expected_impact="Higher pass rate for currently failing rules",
                confidence=0.6,
                rollback_plan="Remove enhanced focus if pass rate doesn't improve",
            ))

        return adjustments

    def _identify_areas(
        self,
        results: List[QualityResult],
        category_trends: Dict[str, TrendAnalysis],
    ) -> Tuple[List[str], List[str]]:
        """Identify weak and strong areas"""
        # Get latest category scores
        if not results:
            return [], []

        latest = results[-1]
        cat_scores = latest.category_scores

        # Sort by score
        sorted_cats = sorted(cat_scores.items(), key=lambda x: x[1])

        # Weak areas: bottom 25% or declining
        weak = [cat for cat, score in sorted_cats[:max(1, len(sorted_cats) // 4)]]

        # Add declining areas
        for cat, trend in category_trends.items():
            if trend.direction == TrendDirection.DECLINING and cat not in weak:
                weak.append(cat)

        # Strong areas: top 25% and improving
        strong = [cat for cat, score in sorted_cats[-max(1, len(sorted_cats) // 4):]]

        return list(set(weak)), list(set(strong))

    def _generate_recommendations(
        self,
        insights: List[QualityInsight],
        adjustments: List[ConfigurationAdjustment],
        weak_areas: List[str],
        strong_areas: List[str],
    ) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []

        # Priority-based recommendations
        critical_insights = [i for i in insights if i.priority == InsightPriority.CRITICAL]
        if critical_insights:
            recommendations.append(
                f"🚨 CRITICAL: Address {len(critical_insights)} critical issue(s) immediately"
            )

        # Weak area recommendations
        if weak_areas:
            recommendations.append(
                f"📉 Focus on improving weak areas: {', '.join(weak_areas)}"
            )

        # Strong area recommendations
        if strong_areas:
            recommendations.append(
                f"📈 Leverage strong areas: {', '.join(strong_areas)}"
            )

        # Adjustment recommendations
        high_confidence_adjustments = [
            a for a in adjustments if a.confidence >= 0.7
        ]
        if high_confidence_adjustments:
            recommendations.append(
                f"⚙️  Consider {len(high_confidence_adjustments)} high-confidence configuration adjustment(s)"
            )

        # General recommendations
        if not weak_areas and not strong_areas:
            recommendations.append(
                "✅ Quality is stable. Continue current practices."
            )

        return recommendations

    def _insufficient_data_report(self, results: List[QualityResult]) -> FeedbackReport:
        """Generate report when insufficient data available"""
        now = datetime.now()

        return FeedbackReport(
            analysis_period=(now, now),
            total_runs=len(results),
            overall_trend=TrendAnalysis(
                metric_name="overall_score",
                direction=TrendDirection.STABLE,
                current_value=0.0,
                baseline_value=0.0,
                change_percent=0.0,
                change_abs=0.0,
                confidence=0.0,
                velocity=0.0,
                sample_size=len(results),
                is_significant=False,
            ),
            category_trends={},
            insights=[
                QualityInsight(
                    category="data",
                    title="Insufficient Data",
                    description=f"Need at least {self.MIN_RUNS_FOR_TREND} quality runs for trend analysis. Currently have {len(results)}.",
                    priority=InsightPriority.LOW,
                    evidence=[f"Current runs: {len(results)}"],
                    impact_score=0.0,
                    effort_estimate="low",
                    suggested_actions=[
                        f"Run {self.MIN_RUNS_FOR_TREND - len(results)} more quality evaluations",
                        "Use consistent criteria for better analysis",
                    ],
                )
            ],
            adjustments=[],
            weak_areas=[],
            strong_areas=[],
            recommendations=[
                f"Run more quality evaluations to enable trend analysis",
            ],
        )

    def _save_result(self, result: QualityResult) -> None:
        """Save result to storage"""
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"result_{timestamp}.json"
        filepath = self.storage_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_results(self, task_alias: Optional[str] = None) -> List[QualityResult]:
        """Load results from storage"""
        results = []

        # Load from cache first
        results.extend(self._results_cache)

        # Load from storage
        if self.storage_path.exists():
            for filepath in self.storage_path.glob("result_*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Filter by task_alias if specified
                    if task_alias and data.get("task_alias") != task_alias:
                        continue

                    result = QualityResult(
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        score=data["score"],
                        passed=data["passed"],
                        iteration_count=data["iteration_count"],
                        criteria=data["criteria"],
                        category_scores=data.get("category_scores", {}),
                        failed_rules=data.get("failed_rules", []),
                        warnings=data.get("warnings", []),
                        config_id=data.get("config_id"),
                        task_alias=data.get("task_alias"),
                        metadata=data.get("metadata", {}),
                    )
                    results.append(result)
                except Exception:
                    continue

        # Sort by timestamp
        results.sort(key=lambda r: r.timestamp)

        return results


# Convenience functions for integration
def create_quality_result(
    score: float,
    passed: bool,
    iteration_count: int,
    criteria: List[str],
    category_scores: Dict[str, float],
    failed_rules: List[str],
    warnings: List[str],
    config_id: Optional[str] = None,
    task_alias: Optional[str] = None,
) -> QualityResult:
    """Create a QualityResult from loop output"""
    return QualityResult(
        timestamp=datetime.now(),
        score=score,
        passed=passed,
        iteration_count=iteration_count,
        criteria=criteria,
        category_scores=category_scores,
        failed_rules=failed_rules,
        warnings=warnings,
        config_id=config_id,
        task_alias=task_alias,
    )


def analyze_feedback(
    task_alias: Optional[str] = None,
    lookback_runs: int = 20,
    storage_path: Optional[Path] = None,
) -> FeedbackReport:
    """Analyze quality feedback and generate report"""
    analyzer = FeedbackAnalyzer(storage_path)
    return analyzer.analyze_results(task_alias=task_alias, lookback_runs=lookback_runs)


def get_improvement_suggestions(
    task_alias: Optional[str] = None,
    storage_path: Optional[Path] = None,
) -> List[str]:
    """Get actionable improvement suggestions"""
    report = analyze_feedback(task_alias=task_alias, storage_path=storage_path)
    return report.recommendations


def export_feedback_report(
    output_path: Path,
    task_alias: Optional[str] = None,
    lookback_runs: int = 20,
    format: str = "json",
) -> None:
    """Export feedback report to file"""
    report = analyze_feedback(task_alias=task_alias, lookback_runs=lookback_runs)

    if format == "json":
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    elif format == "markdown":
        # Simple markdown export (feedback_report module was removed during cleanup)
        lines = [f"# Quality Feedback Report\n"]
        if hasattr(report, 'overall_trend'):
            lines.append(f"**Overall Trend:** {report.overall_trend}\n")
        if hasattr(report, 'recommendations'):
            lines.append("## Recommendations\n")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
