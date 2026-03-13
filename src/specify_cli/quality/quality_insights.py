"""
Quality Insights System (Exp 73)

Provides intelligent analytics and proactive quality improvement recommendations:
- Pattern Recognition: Identify recurring quality patterns and trends
- Predictive Analytics: Forecast future quality scores and potential issues
- Smart Recommendations: Data-driven optimization suggestions
- Action Items: Generate concrete improvement actions
- Root Cause Analysis: Identify underlying causes of quality issues
- Optimization Opportunities: Find areas with highest improvement potential

This transforms quality monitoring from reactive to proactive by providing
actionable insights based on historical data analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import statistics
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from .quality_history import QualityRunRecord, QualityHistoryManager
from .quality_anomaly import AnomalyReport, AnomalySeverity, AnomalyType
from .quality_goals import QualityGoal, GoalStatus, QualityGoalsManager
from .priority_profiles import PriorityProfilesManager, CATEGORY_TAGS


class InsightType(Enum):
    """Types of insights that can be generated"""
    PATTERN = "pattern"  # Recurring pattern identified
    TREND = "trend"  # Trend direction and significance
    PREDICTION = "prediction"  # Future quality forecast
    OPTIMIZATION = "optimization"  # Optimization opportunity
    ROOT_CAUSE = "root_cause"  # Root cause analysis
    ACTION_ITEM = "action_item"  # Specific action to take
    BENCHMARK = "benchmark"  # Comparison to baseline/target


class InsightPriority(Enum):
    """Priority level for insights"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class QualityInsight:
    """Represents a single quality insight"""
    insight_type: InsightType
    priority: InsightPriority
    title: str
    description: str
    category: Optional[str] = None  # Quality category affected
    confidence: float = 0.0  # 0-1 confidence score
    evidence: List[str] = field(default_factory=list)  # Supporting data
    recommendation: Optional[str] = None  # Actionable recommendation
    predicted_impact: Optional[str] = None  # Expected outcome
    related_insights: List[str] = field(default_factory=list)  # IDs of related insights

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "insight_type": self.insight_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "predicted_impact": self.predicted_impact,
            "related_insights": self.related_insights,
        }


@dataclass
class PatternInsight:
    """Insight about a recurring quality pattern"""
    pattern_name: str
    frequency: int  # How often pattern occurs
    pattern_type: str  # "cyclical", "degradation", "improvement", "spike"
    description: str
    triggers: List[str] = field(default_factory=list)
    mitigation: Optional[str] = None


@dataclass
class TrendInsight:
    """Insight about quality trends"""
    trend_direction: str  # "improving", "declining", "stable", "volatile"
    strength: float  # 0-1 how strong the trend is
    time_window: int  # Number of runs analyzed
    forecast: Optional[str] = None  # Predicted future state
    change_rate: Optional[float] = None  # Score change per run


@dataclass
class OptimizationInsight:
    """Insight about optimization opportunities"""
    area: str  # Category or rule area
    current_value: float
    potential_value: float  # Expected if optimized
    improvement_potential: float  # Potential score increase
    effort: str  # "low", "medium", "high"
    actions: List[str] = field(default_factory=list)


@dataclass
class ActionItem:
    """Concrete action item for quality improvement"""
    action_id: str
    title: str
    description: str
    priority: InsightPriority
    effort: str  # "low", "medium", "high"
    category: Optional[str] = None
    expected_impact: str = ""
    steps: List[str] = field(default_factory=list)


@dataclass
class InsightsReport:
    """Complete insights report"""
    insights_generated: int
    insights_by_priority: Dict[str, int]
    insights_by_type: Dict[str, int]
    insights: List[QualityInsight]
    pattern_insights: List[PatternInsight]
    trend_insights: List[TrendInsight]
    optimization_insights: List[OptimizationInsight]
    action_items: List[ActionItem]
    total_runs_analyzed: int
    analysis_timestamp: str
    task_alias: Optional[str] = None
    overall_quality_assessment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "insights_generated": self.insights_generated,
            "insights_by_priority": self.insights_by_priority,
            "insights_by_type": self.insights_by_type,
            "insights": [i.to_dict() for i in self.insights],
            "pattern_insights": [
                {
                    "pattern_name": p.pattern_name,
                    "frequency": p.frequency,
                    "pattern_type": p.pattern_type,
                    "description": p.description,
                    "triggers": p.triggers,
                    "mitigation": p.mitigation,
                }
                for p in self.pattern_insights
            ],
            "trend_insights": [
                {
                    "trend_direction": t.trend_direction,
                    "strength": t.strength,
                    "time_window": t.time_window,
                    "forecast": t.forecast,
                    "change_rate": t.change_rate,
                }
                for t in self.trend_insights
            ],
            "optimization_insights": [
                {
                    "area": o.area,
                    "current_value": o.current_value,
                    "potential_value": o.potential_value,
                    "improvement_potential": o.improvement_potential,
                    "effort": o.effort,
                    "actions": o.actions,
                }
                for o in self.optimization_insights
            ],
            "action_items": [
                {
                    "action_id": a.action_id,
                    "title": a.title,
                    "description": a.description,
                    "priority": a.priority.value,
                    "effort": a.effort,
                    "category": a.category,
                    "expected_impact": a.expected_impact,
                    "steps": a.steps,
                }
                for a in self.action_items
            ],
            "total_runs_analyzed": self.total_runs_analyzed,
            "analysis_timestamp": self.analysis_timestamp,
            "task_alias": self.task_alias,
            "overall_quality_assessment": self.overall_quality_assessment,
        }


class QualityInsightsEngine:
    """Generates quality insights from historical data"""

    def __init__(
        self,
        history_file: Optional[str] = None,
        goals_file: Optional[str] = None,
    ):
        """Initialize insights engine

        Args:
            history_file: Path to quality history file
            goals_file: Path to quality goals file
        """
        self.history_manager = QualityHistoryManager(history_file)
        self.goals_manager = QualityGoalsManager(goals_file) if goals_file else None

    def generate_insights(
        self,
        task_alias: Optional[str] = None,
        max_runs: int = 50,
    ) -> InsightsReport:
        """Generate comprehensive quality insights

        Args:
            task_alias: Task alias to analyze (None = all tasks)
            max_runs: Maximum number of historical runs to analyze

        Returns:
            InsightsReport with all generated insights
        """
        # Load quality history
        runs = self.history_manager.get_runs(task_alias, limit=max_runs)

        if len(runs) < 3:
            return InsightsReport(
                insights_generated=0,
                insights_by_priority={},
                insights_by_type={},
                insights=[],
                pattern_insights=[],
                trend_insights=[],
                optimization_insights=[],
                action_items=[],
                total_runs_analyzed=len(runs),
                analysis_timestamp=datetime.now().isoformat(),
                task_alias=task_alias,
                overall_quality_assessment="Insufficient data for analysis",
            )

        insights: List[QualityInsight] = []
        pattern_insights: List[PatternInsight] = []
        trend_insights: List[TrendInsight] = []
        optimization_insights: List[OptimizationInsight] = []
        action_items: List[ActionItem] = []

        # Generate pattern insights
        pattern_insights.extend(self._detect_patterns(runs))

        # Generate trend insights
        trend_insights.extend(self._analyze_trends(runs))

        # Generate optimization insights
        optimization_insights.extend(self._find_optimization_opportunities(runs))

        # Convert pattern/trend/optimization insights to general insights
        for p in pattern_insights:
            insights.append(self._pattern_to_insight(p))
        for t in trend_insights:
            insights.append(self._trend_to_insight(t))
        for o in optimization_insights:
            insights.append(self._optimization_to_insight(o))

        # Generate action items
        action_items.extend(self._generate_action_items(runs, insights))

        # Generate root cause insights
        insights.extend(self._analyze_root_causes(runs))

        # Generate prediction insights
        insights.extend(self._generate_predictions(runs))

        # Generate benchmark insights
        if self.goals_manager:
            insights.extend(self._benchmark_vs_goals(runs))

        # Count by priority and type
        priority_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for insight in insights:
            priority_counts[insight.priority.value] = priority_counts.get(insight.priority.value, 0) + 1
            type_counts[insight.insight_type.value] = type_counts.get(insight.insight_type.value, 0) + 1

        # Overall quality assessment
        overall_assessment = self._assess_overall_quality(runs, insights)

        # Sort insights by priority (critical first)
        priority_order = {
            InsightPriority.CRITICAL: 0,
            InsightPriority.HIGH: 1,
            InsightPriority.MEDIUM: 2,
            InsightPriority.LOW: 3,
        }
        insights.sort(key=lambda i: priority_order.get(i.priority, 4))

        return InsightsReport(
            insights_generated=len(insights),
            insights_by_priority=priority_counts,
            insights_by_type=type_counts,
            insights=insights,
            pattern_insights=pattern_insights,
            trend_insights=trend_insights,
            optimization_insights=optimization_insights,
            action_items=action_items,
            total_runs_analyzed=len(runs),
            analysis_timestamp=datetime.now().isoformat(),
            task_alias=task_alias,
            overall_quality_assessment=overall_assessment,
        )

    def _detect_patterns(self, runs: List[QualityRunRecord]) -> List[PatternInsight]:
        """Detect recurring quality patterns"""
        patterns = []

        if len(runs) < 5:
            return patterns

        # Sort by timestamp
        sorted_runs = sorted(runs, key=lambda r: r.timestamp)

        # Pattern 1: Cyclical patterns (score oscillation)
        scores = [r.score for r in sorted_runs]
        if len(scores) >= 6:
            # Check for oscillation
            up_down_transitions = 0
            for i in range(1, len(scores)):
                if (scores[i] - scores[i-1]) * (scores[i-1] - scores[i-2] if i >= 2 else 0) < 0:
                    up_down_transitions += 1

            if up_down_transitions >= len(scores) / 2:
                patterns.append(PatternInsight(
                    pattern_name="Score Oscillation",
                    frequency=up_down_transitions,
                    pattern_type="cyclical",
                    description="Quality scores show cyclical oscillation pattern, indicating instability",
                    triggers=["Frequent code changes", "Inconsistent review process", "Variable team capacity"],
                    mitigation="Establish consistent quality gates and review processes",
                ))

        # Pattern 2: Gradual degradation
        recent_scores = scores[-5:]
        if len(recent_scores) >= 4:
            degrading = all(recent_scores[i] <= recent_scores[i-1] for i in range(1, len(recent_scores)))
            if degrading and (recent_scores[0] - recent_scores[-1]) > 0.05:
                patterns.append(PatternInsight(
                    pattern_name="Gradual Degradation",
                    frequency=5,
                    pattern_type="degradation",
                    description=f"Quality degrading by {(recent_scores[0] - recent_scores[-1])*100:.1f}% over recent runs",
                    triggers=["Technical debt accumulation", "Rushed features", "Resource constraints"],
                    mitigation="Schedule dedicated quality improvement sprints",
                ))

        # Pattern 3: Iteration spikes
        iterations = [r.iteration for r in sorted_runs]
        mean_iter = statistics.mean(iterations)
        spike_count = sum(1 for i in iterations if i > mean_iter * 1.5)

        if spike_count >= 2:
            patterns.append(PatternInsight(
                pattern_name="Iteration Spikes",
                frequency=spike_count,
                pattern_type="spike",
                description=f"{spike_count} runs required unusually high iteration counts",
                triggers=["Complex quality requirements", "Misconfigured criteria", "Ambiguous specifications"],
                mitigation="Review and simplify quality criteria, clarify specifications",
            ))

        # Pattern 4: Category-specific patterns
        for run in sorted_runs[-3:]:
            if run.category_scores:
                low_categories = [cat for cat, score in run.category_scores.items() if score < 0.6]
                if len(low_categories) >= 2:
                    patterns.append(PatternInsight(
                        pattern_name=f"Persistent Low Categories: {', '.join(low_categories[:2])}",
                        frequency=3,
                        pattern_type="persistent_issue",
                        description=f"Categories consistently scoring below 0.6: {', '.join(low_categories)}",
                        triggers=["Lack of focus areas", "Missing expertise", "Tooling gaps"],
                        mitigation=f"Assign focused improvement efforts to: {', '.join(low_categories)}",
                    ))
                    break

        return patterns

    def _analyze_trends(self, runs: List[QualityRunRecord]) -> List[TrendInsight]:
        """Analyze quality trends over time"""
        insights = []

        if len(runs) < 4:
            return insights

        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        scores = [r.score for r in sorted_runs]

        # Calculate trend using linear regression approximation
        n = len(scores)
        x = list(range(n))
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(scores)

        # Simple linear regression: y = mx + b
        numerator = sum((x[i] - mean_x) * (scores[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            return insights

        slope = numerator / denominator

        # Determine trend direction and strength
        change_rate = abs(slope)
        if slope > 0.01:
            direction = "improving"
            forecast = f"Continued improvement expected (~+{slope*100:.2f} per run)"
        elif slope < -0.01:
            direction = "declining"
            forecast = f"Continued decline expected ({slope*100:.2f} per run) - intervention needed"
        else:
            direction = "stable"
            forecast = "Quality expected to remain stable"

        # Calculate strength (R² approximation)
        ss_res = sum((scores[i] - (slope * x[i] + mean_y - slope * mean_x)) ** 2 for i in range(n))
        ss_tot = sum((scores[i] - mean_y) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        strength = max(0, min(1, r_squared))

        # Check for volatility
        if len(scores) >= 4:
            stdev = statistics.stdev(scores)
            if stdev > 0.1:
                direction = "volatile"
                forecast = f"High volatility detected (stdev: {stdev:.3f}) - stability needed"

        insights.append(TrendInsight(
            trend_direction=direction,
            strength=strength,
            time_window=n,
            forecast=forecast,
            change_rate=slope,
        ))

        # Category-specific trends
        all_categories = set()
        for run in sorted_runs:
            if run.category_scores:
                all_categories.update(run.category_scores.keys())

        for category in all_categories:
            cat_scores = []
            for run in sorted_runs:
                if run.category_scores and category in run.category_scores:
                    cat_scores.append(run.category_scores[category])

            if len(cat_scores) >= 4:
                cat_slope = self._calculate_slope(cat_scores)
                if abs(cat_slope) > 0.02:
                    cat_direction = "improving" if cat_slope > 0 else "declining"
                    insights.append(TrendInsight(
                        trend_direction=cat_direction,
                        strength=0.7,
                        time_window=len(cat_scores),
                        forecast=f"{category}: {'improving' if cat_slope > 0 else 'declining'} trend",
                        change_rate=cat_slope,
                    ))

        return insights

    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear trend slope"""
        n = len(values)
        x = list(range(n))
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(values)

        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0

    def _find_optimization_opportunities(self, runs: List[QualityRunRecord]) -> List[OptimizationInsight]:
        """Find areas with high improvement potential"""
        opportunities = []

        if len(runs) < 3:
            return opportunities

        # Analyze category scores
        category_scores: Dict[str, List[float]] = defaultdict(list)
        for run in runs[-10:]:
            if run.category_scores:
                for cat, score in run.category_scores.items():
                    category_scores[cat].append(score)

        for category, scores in category_scores.items():
            if len(scores) < 2:
                continue

            avg_score = statistics.mean(scores)
            max_score = max(scores)

            # Categories with low average scores have high potential
            if avg_score < 0.7:
                potential = min(1.0, avg_score + 0.2)  # Realistic improvement
                improvement = potential - avg_score

                effort = "low" if avg_score > 0.5 else "medium"

                opportunities.append(OptimizationInsight(
                    area=category,
                    current_value=avg_score,
                    potential_value=potential,
                    improvement_potential=improvement,
                    effort=effort,
                    actions=[
                        f"Review {category} criteria templates",
                        f"Add {category}-focused quality rules",
                        f"Run dedicated {category} improvement loop",
                    ],
                ))

        # Check for pass rate optimization
        if len(runs) >= 5:
            pass_rate = sum(1 for r in runs if r.passed) / len(runs)
            if pass_rate < 0.8:
                opportunities.append(OptimizationInsight(
                    area="Pass Rate",
                    current_value=pass_rate,
                    potential_value=0.9,
                    improvement_potential=0.9 - pass_rate,
                    effort="medium",
                    actions=[
                        "Review quality gate thresholds",
                        "Adjust iteration limits",
                        "Check for overly strict criteria",
                    ],
                ))

        # Check for iteration optimization
        iterations = [r.iteration for r in runs]
        avg_iterations = statistics.mean(iterations)
        if avg_iterations > 3:
            opportunities.append(OptimizationInsight(
                area="Iteration Efficiency",
                current_value=avg_iterations,
                potential_value=2.5,
                improvement_potential=avg_iterations - 2.5,
                effort="low",
                actions=[
                    "Refine criteria for clarity",
                    "Improve artifact quality before loop",
                    "Adjust quality thresholds",
                ],
            ))

        # Sort by improvement potential
        opportunities.sort(key=lambda o: o.improvement_potential, reverse=True)

        return opportunities[:5]  # Top 5 opportunities

    def _analyze_root_causes(self, runs: List[QualityRunRecord]) -> List[QualityInsight]:
        """Analyze root causes of quality issues"""
        insights = []

        if len(runs) < 3:
            return insights

        # Find failed runs
        failed_runs = [r for r in runs if not r.passed]

        if len(failed_runs) >= 2:
            # Analyze common failure patterns
            low_categories: Dict[str, int] = Counter()
            for run in failed_runs:
                if run.category_scores:
                    for cat, score in run.category_scores.items():
                        if score < 0.5:
                            low_categories[cat] += 1

            if low_categories:
                top_issue = low_categories.most_common(1)[0]
                insights.append(QualityInsight(
                    insight_type=InsightType.ROOT_CAUSE,
                    priority=InsightPriority.HIGH,
                    title=f"Primary Failure Category: {top_issue[0]}",
                    description=f"{top_issue[0]} is the most common failure point ({top_issue[1]} failed runs)",
                    category=top_issue[0],
                    confidence=0.8,
                    evidence=[
                        f"{top_issue[1]} of {len(failed_runs)} failed runs had low {top_issue[0]} scores",
                        f"Average {top_issue[0]} score in failed runs: {statistics.mean([r.category_scores.get(top_issue[0], 0) for r in failed_runs if r.category_scores and top_issue[0] in r.category_scores]):.2f}",
                    ],
                    recommendation=f"Focus improvement efforts on {top_issue[0]} - review criteria, add rules, run dedicated loop",
                    predicted_impact=f"+{min(0.15, top_issue[1] * 0.03):.2f} expected score increase",
                ))

        # Analyze high iteration runs
        high_iter_runs = [r for r in runs if r.iteration > statistics.mean([r.iteration for r in runs]) * 1.5]
        if len(high_iter_runs) >= 2:
            insights.append(QualityInsight(
                insight_type=InsightType.ROOT_CAUSE,
                priority=InsightPriority.MEDIUM,
                title="High Iteration Count Pattern",
                description=f"{len(high_iter_runs)} runs required excessive iterations to converge",
                confidence=0.7,
                evidence=[
                    f"Avg iterations: {statistics.mean([r.iteration for r in high_iter_runs]):.1f}",
                    f"Overall avg: {statistics.mean([r.iteration for r in runs]):.1f}",
                ],
                recommendation="Refine criteria clarity, adjust thresholds, improve initial artifact quality",
                predicted_impact="30-50% reduction in iteration time",
            ))

        return insights

    def _generate_predictions(self, runs: List[QualityRunRecord]) -> List[QualityInsight]:
        """Generate predictive insights"""
        insights = []

        if len(runs) < 5:
            return insights

        sorted_runs = sorted(runs, key=lambda r: r.timestamp)
        scores = [r.score for r in sorted_runs]

        # Predict next score using linear trend
        n = len(scores)
        slope = self._calculate_slope(scores)

        next_score = scores[-1] + slope

        if slope > 0.005:
            insights.append(QualityInsight(
                insight_type=InsightType.PREDICTION,
                priority=InsightPriority.LOW,
                title="Score Improvement Prediction",
                description=f"Based on current trend, next run expected to score: {next_score:.3f}",
                confidence=min(0.9, len(scores) / 20),
                evidence=[
                    f"Current trend: +{slope*100:.2f} per run",
                    f"Recent scores: {scores[-3:]}",
                ],
                recommendation="Maintain current practices to continue improvement",
                predicted_impact=f"+{(slope*100):.2f}% per run",
            ))
        elif slope < -0.005:
            insights.append(QualityInsight(
                insight_type=InsightType.PREDICTION,
                priority=InsightPriority.HIGH,
                title="Score Decline Warning",
                description=f"Based on current trend, next run expected to score: {next_score:.3f}",
                confidence=min(0.9, len(scores) / 20),
                evidence=[
                    f"Current trend: {slope*100:.2f} per run",
                    f"Recent scores: {scores[-3:]}",
                ],
                recommendation="Intervention needed: review recent changes, adjust quality gates",
                predicted_impact=f"{slope*100:.2f}% per run (declining)",
            ))

        # Predict pass rate
        recent_passed = sum(1 for r in sorted_runs[-10:] if r.passed)
        recent_pass_rate = recent_passed / min(len(sorted_runs), 10)

        if recent_pass_rate < 0.7 and len(sorted_runs) >= 10:
            insights.append(QualityInsight(
                insight_type=InsightType.PREDICTION,
                priority=InsightPriority.HIGH,
                title="Pass Rate At Risk",
                description=f"Current pass rate ({recent_pass_rate*100:.0f}%) risks falling below acceptable threshold",
                confidence=0.75,
                evidence=[
                    f"Recent pass rate: {recent_pass_rate*100:.0f}%",
                    f"Passed runs: {recent_passed}/{min(len(sorted_runs), 10)}",
                ],
                recommendation="Review quality gate configuration, consider threshold adjustments",
                predicted_impact="10-20% pass rate improvement with adjustment",
            ))

        return insights

    def _benchmark_vs_goals(self, runs: List[QualityRunRecord]) -> List[QualityInsight]:
        """Benchmark current quality against goals"""
        insights = []

        if not self.goals_manager:
            return insights

        goals = self.goals_manager.get_all_goals()
        if not goals or len(runs) < 3:
            return insights

        # Get current stats
        recent_runs = runs[-10:]
        avg_score = statistics.mean([r.score for r in recent_runs])
        pass_rate = sum(1 for r in recent_runs if r.passed) / len(recent_runs)

        for goal in goals:
            if goal.status == GoalStatus.ACHIEVED:
                continue

            gap = goal.target_value - goal.current_value
            urgency = (goal.target_value - avg_score) if goal.goal_type.value == "target_score" else gap

            priority = InsightPriority.CRITICAL if urgency > 0.2 else InsightPriority.HIGH if urgency > 0.1 else InsightPriority.MEDIUM

            insights.append(QualityInsight(
                insight_type=InsightType.BENCHMARK,
                priority=priority,
                title=f"Goal Gap: {goal.name}",
                description=f"Gap of {urgency:.2f} to goal target ({goal.target_value:.2f})",
                category=goal.category,
                confidence=0.8,
                evidence=[
                    f"Current value: {goal.current_value:.2f}",
                    f"Target: {goal.target_value:.2f}",
                    f"Status: {goal.status.value}",
                ],
                recommendation=f"Focus efforts on {goal.name} - consider dedicated quality loop",
                predicted_impact=f"+{urgency:.2f} to achieve goal",
            ))

        return insights

    def _generate_action_items(
        self,
        runs: List[QualityRunRecord],
        insights: List[QualityInsight],
    ) -> List[ActionItem]:
        """Generate concrete action items from insights"""
        actions = []

        action_id = 1

        # High priority insights -> action items
        for insight in insights[:5]:  # Top 5 insights
            if insight.priority in [InsightPriority.CRITICAL, InsightPriority.HIGH]:
                if insight.category:
                    actions.append(ActionItem(
                        action_id=f"A{action_id:03d}",
                        title=f"Improve {insight.category} Quality",
                        description=insight.recommendation or f"Address {insight.title}",
                        priority=insight.priority,
                        effort="medium",
                        category=insight.category,
                        expected_impact=insight.predicted_impact or "Improved quality scores",
                        steps=[
                            f"Review {insight.category} criteria template",
                            f"Run quality loop with focus on {insight.category}",
                            f"Add specific {insight.category} quality rules",
                            "Monitor progress in next 3 runs",
                        ],
                    ))
                    action_id += 1

        # Generic improvement actions based on overall trends
        if len(runs) >= 5:
            avg_score = statistics.mean([r.score for r in runs])
            if avg_score < 0.7:
                actions.append(ActionItem(
                    action_id=f"A{action_id:03d}",
                    title="Overall Quality Improvement Initiative",
                    description="Launch comprehensive quality improvement program",
                    priority=InsightPriority.HIGH,
                    effort="high",
                    expected_impact="+0.1 to +0.2 overall score increase",
                    steps=[
                        "Run quality loop with production-strict config",
                        "Address all critical and high priority insights",
                        "Establish quality gates for CI/CD",
                        "Schedule weekly quality reviews",
                    ],
                ))
                action_id += 1

        return actions

    def _assess_overall_quality(
        self,
        runs: List[QualityRunRecord],
        insights: List[QualityInsight],
    ) -> str:
        """Generate overall quality assessment"""
        if len(runs) < 3:
            return "Insufficient data"

        avg_score = statistics.mean([r.score for r in runs])
        pass_rate = sum(1 for r in runs if r.passed) / len(runs)
        critical_count = sum(1 for i in insights if i.priority == InsightPriority.CRITICAL)
        high_count = sum(1 for i in insights if i.priority == InsightPriority.HIGH)

        # Quality tier assessment
        if avg_score >= 0.9 and pass_rate >= 0.9:
            tier = "Excellent"
            status = "Quality is excellent. Maintain current practices."
        elif avg_score >= 0.8 and pass_rate >= 0.8:
            tier = "Good"
            status = f"Quality is good. {high_count} high-priority improvements identified."
        elif avg_score >= 0.7 and pass_rate >= 0.7:
            tier = "Fair"
            status = f"Quality is fair. {critical_count} critical and {high_count} high-priority issues need attention."
        else:
            tier = "Needs Improvement"
            status = f"Quality needs improvement. {critical_count} critical issues require immediate attention."

        return f"[{tier}] {status}"

    def _pattern_to_insight(self, pattern: PatternInsight) -> QualityInsight:
        """Convert pattern insight to general insight"""
        return QualityInsight(
            insight_type=InsightType.PATTERN,
            priority=InsightPriority.MEDIUM,
            title=f"Pattern: {pattern.pattern_name}",
            description=pattern.description,
            evidence=pattern.triggers,
            recommendation=pattern.mitigation,
            confidence=0.7,
        )

    def _trend_to_insight(self, trend: TrendInsight) -> QualityInsight:
        """Convert trend insight to general insight"""
        priority = InsightPriority.HIGH if trend.trend_direction == "declining" else InsightPriority.LOW
        return QualityInsight(
            insight_type=InsightType.TREND,
            priority=priority,
            title=f"Trend: {trend.trend_direction.upper()} Quality Trend",
            description=f"Quality is {trend.trend_direction} with strength {trend.strength:.2f}",
            confidence=trend.strength,
            evidence=[f"Forecast: {trend.forecast}"],
            recommendation=trend.forecast,
        )

    def _optimization_to_insight(self, opt: OptimizationInsight) -> QualityInsight:
        """Convert optimization insight to general insight"""
        priority = InsightPriority.HIGH if opt.improvement_potential > 0.15 else InsightPriority.MEDIUM
        return QualityInsight(
            insight_type=InsightType.OPTIMIZATION,
            priority=priority,
            title=f"Optimization: {opt.area}",
            description=f"+{opt.improvement_potential*100:.1f}% improvement potential in {opt.area}",
            category=opt.area,
            confidence=0.75,
            evidence=[f"Current: {opt.current_value:.2f}, Potential: {opt.potential_value:.2f}"],
            recommendation=f"Focus on {opt.area}: {', '.join(opt.actions[:2])}",
            predicted_impact=f"+{opt.improvement_potential*100:.1f}% in {opt.area}",
        )


# Convenience functions

def generate_insights(
    task_alias: Optional[str] = None,
    max_runs: int = 50,
    history_file: Optional[str] = None,
    goals_file: Optional[str] = None,
) -> InsightsReport:
    """Generate quality insights report

    Args:
        task_alias: Task alias to analyze
        max_runs: Maximum runs to analyze
        history_file: Path to history file
        goals_file: Path to goals file

    Returns:
        InsightsReport
    """
    engine = QualityInsightsEngine(history_file, goals_file)
    return engine.generate_insights(task_alias, max_runs)


def format_insights_report(
    report: InsightsReport,
    detailed: bool = True,
) -> str:
    """Format insights report for display

    Args:
        report: InsightsReport to format
        detailed: Show detailed insights

    Returns:
        Formatted report string
    """
    lines = []

    title = f"Quality Insights for '{report.task_alias}'" if report.task_alias else "Quality Insights Report"
    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"**Overall Assessment:** {report.overall_quality_assessment}")
    lines.append(f"**Analyzed:** {report.total_runs_analyzed} runs")
    lines.append(f"**Insights Generated:** {report.insights_generated}")
    lines.append(f"**Timestamp:** {report.analysis_timestamp}")
    lines.append("")

    # Priority breakdown
    if report.insights_by_priority:
        lines.append("**Priority Breakdown:**")
        for priority, count in sorted(report.insights_by_priority.items(), key=lambda x: -len(x[0])):
            icon = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "💡"}.get(priority, "")
            lines.append(f"  {icon} {priority.upper()}: {count}")
        lines.append("")

    # Pattern insights
    if report.pattern_insights:
        lines.append("### Patterns Detected")
        lines.append("")
        for pattern in report.pattern_insights:
            lines.append(f"🔁 **{pattern.pattern_name}** [{pattern.pattern_type}]")
            lines.append(f"   {pattern.description}")
            if pattern.triggers:
                lines.append(f"   Triggers: {', '.join(pattern.triggers[:2])}")
            if pattern.mitigation:
                lines.append(f"   💡 {pattern.mitigation}")
            lines.append("")

    # Trend insights
    if report.trend_insights:
        lines.append("### Trends Analysis")
        lines.append("")
        for trend in report.trend_insights:
            direction_icon = {
                "improving": "📈",
                "declining": "📉",
                "stable": "➡️",
                "volatile": "🌊",
            }.get(trend.trend_direction, "📊")
            lines.append(f"{direction_icon} **Trend: {trend.trend_direction.upper()}** (strength: {trend.strength:.2f})")
            lines.append(f"   {trend.forecast}")
            if trend.change_rate is not None:
                lines.append(f"   Rate: {trend.change_rate*100:+.2f} per run")
            lines.append("")

    # Optimization opportunities
    if report.optimization_insights:
        lines.append("### Optimization Opportunities")
        lines.append("")
        for opt in report.optimization_insights:
            lines.append(f"🎯 **{opt.area}** (+{opt.improvement_potential*100:.1f}% potential)")
            lines.append(f"   Current: {opt.current_value:.2f} → Potential: {opt.potential_value:.2f}")
            lines.append(f"   Effort: {opt.effort.upper()}")
            if opt.actions:
                lines.append(f"   Actions: {opt.actions[0]}")
            lines.append("")

    # Action items
    if report.action_items:
        lines.append("### Recommended Actions")
        lines.append("")
        for action in report.action_items[:5]:  # Top 5
            priority_icon = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "💡",
            }.get(action.priority.value, "")
            lines.append(f"{priority_icon} **{action.action_id}: {action.title}** [{action.priority.value.upper()}]")
            lines.append(f"   {action.description}")
            if action.expected_impact:
                lines.append(f"   Impact: {action.expected_impact}")
            lines.append("")

    if not detailed:
        return "\n".join(lines)

    # All insights (detailed)
    lines.append("### All Insights (Detailed)")
    lines.append("")

    for insight in report.insights[:10]:  # Top 10
        type_icon = {
            InsightType.PATTERN: "🔁",
            InsightType.TREND: "📊",
            InsightType.PREDICTION: "🔮",
            InsightType.OPTIMIZATION: "🎯",
            InsightType.ROOT_CAUSE: "🔍",
            InsightType.ACTION_ITEM: "⚡",
            InsightType.BENCHMARK: "📏",
        }.get(insight.insight_type, "💡")

        lines.append(f"{type_icon} **{insight.title}** [{insight.insight_type.value}]")
        lines.append(f"   {insight.description}")
        if insight.category:
            lines.append(f"   Category: {insight.category}")
        if insight.recommendation:
            lines.append(f"   💡 {insight.recommendation}")
        if insight.predicted_impact:
            lines.append(f"   Impact: {insight.predicted_impact}")
        lines.append("")

    return "\n".join(lines)


def format_insights_json(report: InsightsReport, indent: int = 2) -> str:
    """Format insights report as JSON

    Args:
        report: InsightsReport to format
        indent: JSON indentation

    Returns:
        JSON string
    """
    return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)


def get_insights_summary(report: InsightsReport) -> str:
    """Get one-line summary of insights

    Args:
        report: InsightsReport

    Returns:
        Summary string
    """
    critical = report.insights_by_priority.get("critical", 0)
    high = report.insights_by_priority.get("high", 0)

    if critical > 0:
        return f"CRITICAL: {critical} critical, {high} high priority insights"
    elif high > 0:
        return f"ATTENTION: {high} high priority insights"
    elif report.insights_generated > 0:
        return f"INFO: {report.insights_generated} insights generated"
    else:
        return "OK: Quality is healthy, no major concerns"


def export_action_items(report: InsightsReport, output_path: str) -> None:
    """Export action items to markdown file

    Args:
        report: InsightsReport with action items
        output_path: Path to output file
    """
    lines = ["# Quality Improvement Action Items\n"]
    lines.append(f"Generated: {report.analysis_timestamp}\n")
    lines.append(f"Task: {report.task_alias or 'All'}\n")
    lines.append("\n## Summary\n")
    lines.append(f"- Total actions: {len(report.action_items)}")
    lines.append(f"- Critical: {sum(1 for a in report.action_items if a.priority.value == 'critical')}")
    lines.append(f"- High: {sum(1 for a in report.action_items if a.priority.value == 'high')}")
    lines.append("\n## Action Items\n")

    for action in report.action_items:
        lines.append(f"### {action.action_id}: {action.title}")
        lines.append(f"**Priority:** {action.priority.value.upper()}  ")
        lines.append(f"**Effort:** {action.effort.upper()}  ")
        lines.append(f"**Impact:** {action.expected_impact}\n")
        lines.append(f"{action.description}\n")
        if action.category:
            lines.append(f"**Category:** {action.category}\n")
        lines.append("**Steps:**\n")
        for i, step in enumerate(action.steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("\n---\n")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


class InsightsConfig:
    """Configuration for insights generation"""

    def __init__(
        self,
        min_runs: int = 3,
        max_runs: int = 50,
        include_predictions: bool = True,
        include_benchmarks: bool = True,
        include_action_items: bool = True,
        max_action_items: int = 10,
    ):
        self.min_runs = min_runs
        self.max_runs = max_runs
        self.include_predictions = include_predictions
        self.include_benchmarks = include_benchmarks
        self.include_action_items = include_action_items
        self.max_action_items = max_action_items
