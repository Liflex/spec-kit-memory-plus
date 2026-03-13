"""
Smart Goal Suggestions System (Exp 74, Exp 75)

Integrates Quality Insights with Quality Goals to provide intelligent,
data-driven goal recommendations based on historical quality data.

Key features:
- Suggest optimal goal targets based on historical performance
- Recommend achievable goals using statistical analysis
- Prioritize suggestions by improvement potential and effort
- Generate personalized goal presets based on project patterns
- Provide rationale and confidence scores for each suggestion
- Correlation-aware suggestions for high-impact goals (Exp 75)
- Quality Loop integration for auto-suggest workflows (Exp 75)

This bridges the gap between Quality Insights (what's happening)
and Quality Goals (what to aim for).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import statistics
from datetime import datetime
from pathlib import Path

from .quality_history import QualityHistoryManager, QualityRunRecord
from .quality_insights import (
    QualityInsightsEngine,
    InsightsReport,
    OptimizationInsight,
    TrendInsight,
    InsightPriority,
)
from .quality_goals import QualityGoal, GoalType, GoalStatus, QualityGoalsManager
from .priority_profiles import CATEGORY_TAGS


class SuggestionReason(Enum):
    """Reason for goal suggestion"""
    ACHIEVABLE_TARGET = "achievable_target"  # Based on recent performance
    IMPROVEMENT_AREA = "improvement_area"  # Low category needs focus
    TREND_ALIGNMENT = "trend_alignment"  # Align with positive trend
    STABILITY_FOCUS = "stability_focus"  # Reduce volatility
    PASS_RATE_BOOST = "pass_rate_boost"  # Improve consistency
    QUICK_WIN = "quick_win"  # Easy achievable goal
    STRETCH_GOAL = "stretch_goal"  # Ambitious but possible


class SuggestionConfidence(Enum):
    """Confidence level in suggestion"""
    HIGH = "high"  # Strong statistical evidence
    MEDIUM = "medium"  # Moderate evidence
    LOW = "low"  # Limited data, speculative


@dataclass
class GoalSuggestion:
    """Suggested quality goal with rationale"""
    goal_type: GoalType
    name: str
    description: str
    suggested_target: float
    confidence: SuggestionConfidence
    reason: SuggestionReason
    rationale: str  # Why this goal is suggested
    current_baseline: float  # Current actual value
    expected_effort: str  # "low", "medium", "high"
    estimated_achievable: bool  # Whether goal is realistically achievable
    category: Optional[str] = None  # For category-specific goals
    alternative_targets: Dict[str, float] = field(default_factory=dict)  # Conservative/Aggressive options
    supporting_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "goal_type": self.goal_type.value,
            "name": self.name,
            "description": self.description,
            "suggested_target": self.suggested_target,
            "confidence": self.confidence.value,
            "reason": self.reason.value,
            "rationale": self.rationale,
            "current_baseline": self.current_baseline,
            "expected_effort": self.expected_effort,
            "estimated_achievable": self.estimated_achievable,
            "category": self.category,
            "alternative_targets": self.alternative_targets,
            "supporting_evidence": self.supporting_evidence,
        }


@dataclass
class GoalPreset:
    """Pre-configured set of goals for specific scenarios"""
    preset_id: str
    name: str
    description: str
    scenario: str  # "new_project", "improvement", "maintenance", "release_prep"
    goals: List[GoalSuggestion]
    estimated_total_effort: str
    expected_outcomes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "scenario": self.scenario,
            "goals": [g.to_dict() for g in self.goals],
            "estimated_total_effort": self.estimated_total_effort,
            "expected_outcomes": self.expected_outcomes,
        }


@dataclass
class SuggestionReport:
    """Complete goal suggestion report"""
    suggestions_generated: int
    suggestions_by_priority: Dict[str, int]
    suggestions_by_confidence: Dict[str, int]
    suggestions: List[GoalSuggestion]
    presets: List[GoalPreset]
    top_recommendations: List[str]  # IDs of top suggestions
    analysis_summary: str
    project_context: Dict[str, Any]
    generated_at: str
    task_alias: Optional[str] = None
    # Exp 75: Correlation-aware suggestions
    correlation_insights: Optional[List[Dict[str, Any]]] = None
    leading_indicators: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "suggestions_generated": self.suggestions_generated,
            "suggestions_by_priority": self.suggestions_by_priority,
            "suggestions_by_confidence": self.suggestions_by_confidence,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "presets": [p.to_dict() for p in self.presets],
            "top_recommendations": self.top_recommendations,
            "analysis_summary": self.analysis_summary,
            "project_context": self.project_context,
            "generated_at": self.generated_at,
            "task_alias": self.task_alias,
            "correlation_insights": self.correlation_insights,
            "leading_indicators": self.leading_indicators,
        }


class GoalSuggester:
    """Generates smart goal suggestions based on quality insights

    Exp 75: Enhanced with correlation-aware suggestions for high-impact goals
    """

    def __init__(
        self,
        history_dir: Optional[Path] = None,
        goals_dir: Optional[Path] = None,
    ):
        """Initialize goal suggester

        Args:
            history_dir: Directory for quality history
            goals_dir: Directory for quality goals
        """
        self.history_manager = QualityHistoryManager(history_dir=history_dir)
        self.goals_manager = QualityGoalsManager(goals_dir=goals_dir)
        self.insights_engine = QualityInsightsEngine(history_dir=history_dir)

        # Statistical thresholds
        self.min_runs_for_suggestions = 3
        self.confident_runs_threshold = 10

        # Exp 75: Correlation analysis
        self._correlation_analyzer = None
        self._correlation_cache = {}

    def _get_correlation_analyzer(self):
        """Lazy load correlation analyzer (Exp 75)"""
        if self._correlation_analyzer is None:
            try:
                from .correlation_analysis import QualityCorrelationAnalyzer
                self._correlation_analyzer = QualityCorrelationAnalyzer(
                    history_dir=self.history_manager.history_dir
                )
            except Exception:
                # Correlation analysis not available
                self._correlation_analyzer = False
        return self._correlation_analyzer if self._correlation_analyzer is not False else None

    def generate_suggestions(
        self,
        max_suggestions: int = 10,
        include_presets: bool = True,
        task_alias: Optional[str] = None,
        use_correlations: bool = True,  # Exp 75
    ) -> SuggestionReport:
        """Generate goal suggestions based on quality history

        Args:
            max_suggestions: Maximum number of suggestions to generate
            include_presets: Whether to include goal presets
            task_alias: Optional task alias for filtering
            use_correlations: Whether to use correlation analysis (Exp 75)

        Returns:
            SuggestionReport with all suggestions
        """
        runs = self.history_manager.get_runs(limit=50, task_alias=task_alias)

        if len(runs) < self.min_runs_for_suggestions:
            # Not enough data - provide beginner presets
            return self._generate_beginner_suggestions(
                runs=runs,
                include_presets=include_presets,
                task_alias=task_alias,
            )

        # Generate insights
        insights_report = self.insights_engine.generate_insights(
            task_alias=task_alias
        )

        # Analyze current state
        current_state = self._analyze_current_state(runs)

        # Exp 75: Get correlation insights if enabled
        correlation_insights = []
        leading_indicators = []
        correlation_data = {}
        if use_correlations:
            correlation_insights, leading_indicators, correlation_data = self._get_correlation_data(task_alias)

        # Generate suggestions
        suggestions = []

        # 1. Target score suggestions
        suggestions.extend(self._suggest_target_scores(current_state, insights_report))

        # 2. Pass rate suggestions
        suggestions.extend(self._suggest_pass_rates(current_state, insights_report))

        # 3. Category-specific suggestions (Exp 75: enhanced with correlations)
        suggestions.extend(self._suggest_category_goals(current_state, insights_report, correlation_data))

        # 4. Improvement suggestions
        suggestions.extend(self._suggest_improvement_goals(current_state, insights_report))

        # 5. Stability suggestions
        suggestions.extend(self._suggest_stability_goals(current_state, insights_report))

        # Exp 75: Correlation-aware suggestions
        if correlation_data:
            suggestions.extend(self._suggest_correlation_goals(current_state, correlation_data))

        # Rank and limit
        suggestions = self._rank_suggestions(suggestions, correlation_data)[:max_suggestions]

        # Generate presets
        presets = []
        if include_presets:
            presets = self._generate_presets(current_state, insights_report, suggestions, correlation_data)

        # Build report
        report = SuggestionReport(
            suggestions_generated=len(suggestions),
            suggestions_by_priority=self._count_by_priority(suggestions),
            suggestions_by_confidence=self._count_by_confidence(suggestions),
            suggestions=suggestions,
            presets=presets,
            top_recommendations=[s.name for s in suggestions[:3]],
            analysis_summary=self._generate_summary(current_state, insights_report, correlation_data),
            project_context=current_state,
            generated_at=datetime.now().isoformat(),
            task_alias=task_alias,
            correlation_insights=correlation_insights,
            leading_indicators=leading_indicators,
        )

        return report

    def _analyze_current_state(self, runs: List[QualityRunRecord]) -> Dict[str, Any]:
        """Analyze current quality state"""
        if not runs:
            return {
                "has_data": False,
                "total_runs": 0,
            }

        recent_runs = runs[:10]  # Most recent 10

        scores = [r.final_score for r in runs if r.final_score is not None]
        recent_scores = [r.final_score for r in recent_runs if r.final_score is not None]

        pass_count = sum(1 for r in runs if r.passed)
        recent_pass_count = sum(1 for r in recent_runs if r.passed)

        # Category analysis
        category_scores: Dict[str, List[float]] = {}
        for run in runs:
            if run.category_scores:
                for cat, score in run.category_scores.items():
                    if cat not in category_scores:
                        category_scores[cat] = []
                    category_scores[cat].append(score)

        category_stats = {}
        for cat, scores in category_scores.items():
            category_stats[cat] = {
                "mean": statistics.mean(scores),
                "min": min(scores),
                "max": max(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "count": len(scores),
            }

        # Iteration analysis
        iterations = [r.iteration for r in runs]
        avg_iterations = statistics.mean(iterations) if iterations else 0

        return {
            "has_data": True,
            "total_runs": len(runs),
            "avg_score": statistics.mean(scores) if scores else 0.0,
            "recent_avg_score": statistics.mean(recent_scores) if recent_scores else 0.0,
            "overall_pass_rate": pass_count / len(runs) if runs else 0.0,
            "recent_pass_rate": recent_pass_count / len(recent_runs) if recent_runs else 0.0,
            "score_std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
            "avg_iterations": avg_iterations,
            "category_stats": category_stats,
            "best_score": max(scores) if scores else 0.0,
            "worst_score": min(scores) if scores else 0.0,
        }

    def _suggest_target_scores(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> List[GoalSuggestion]:
        """Suggest target score goals"""
        suggestions = []
        current_avg = state.get("recent_avg_score", 0.0)
        best_score = state.get("best_score", 0.0)
        score_std = state.get("score_std", 0.1)

        # Calculate achievable targets
        conservative_target = current_avg + (score_std * 0.5)
        moderate_target = current_avg + (score_std * 1.0)
        aggressive_target = min(current_avg + (score_std * 1.5), best_score)

        # Primary suggestion
        suggestions.append(
            GoalSuggestion(
                goal_type=GoalType.TARGET_SCORE,
                name="Achieve Consistent Quality",
                description=f"Maintain average score above {moderate_target:.2f}",
                suggested_target=round(moderate_target, 2),
                confidence=SuggestionConfidence.MEDIUM if state["total_runs"] < self.confident_runs_threshold else SuggestionConfidence.HIGH,
                reason=SuggestionReason.ACHIEVABLE_TARGET,
                rationale=f"Based on recent performance (avg: {current_avg:.2f}), this target is achievable with focused effort. Best score: {best_score:.2f}",
                current_baseline=round(current_avg, 2),
                expected_effort="medium" if moderate_target > current_avg * 1.05 else "low",
                estimated_achievable=True,
                alternative_targets={
                    "conservative": round(conservative_target, 2),
                    "moderate": round(moderate_target, 2),
                    "aggressive": round(aggressive_target, 2),
                },
                supporting_evidence=[
                    f"Current average: {current_avg:.2f}",
                    f"Standard deviation: {score_std:.2f}",
                    f"Best historical score: {best_score:.2f}",
                ],
            )
        )

        return suggestions

    def _suggest_pass_rates(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> List[GoalSuggestion]:
        """Suggest pass rate goals"""
        suggestions = []
        current_pass_rate = state.get("recent_pass_rate", 0.0)

        # Target improvements
        if current_pass_rate < 0.5:
            # Low pass rate - focus on consistency
            target = 0.7
            effort = "high"
        elif current_pass_rate < 0.8:
            target = 0.85
            effort = "medium"
        else:
            target = min(current_pass_rate + 0.1, 0.95)
            effort = "low"

        suggestions.append(
            GoalSuggestion(
                goal_type=GoalType.PASS_RATE,
                name="Improve Quality Consistency",
                description=f"Achieve {target*100:.0f}% pass rate over 10 runs",
                suggested_target=round(target, 2),
                confidence=SuggestionConfidence.MEDIUM,
                reason=SuggestionReason.PASS_RATE_BOOST,
                rationale=f"Current pass rate is {current_pass_rate*100:.0f}%. Focused effort can improve consistency and reduce failed iterations.",
                current_baseline=round(current_pass_rate, 2),
                expected_effort=effort,
                estimated_achievable=target <= current_pass_rate + 0.2,
                alternative_targets={
                    "conservative": round(current_pass_rate + 0.1, 2),
                    "moderate": round(target, 2),
                    "aggressive": round(min(target + 0.1, 0.98), 2),
                },
                supporting_evidence=[
                    f"Current pass rate: {current_pass_rate*100:.0f}%",
                    f"Avg iterations per run: {state.get('avg_iterations', 0):.1f}",
                ],
            )
        )

        return suggestions

    def _suggest_category_goals(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
        correlation_data: Optional[Dict] = None,
    ) -> List[GoalSuggestion]:
        """Suggest category-specific goals based on weak areas

        Exp 75: Enhanced with correlation-aware prioritization
        """
        suggestions = []
        category_stats = state.get("category_stats", {})

        # Exp 75: Get correlation boost factors
        correlation_boost = {}
        if correlation_data:
            opportunities = correlation_data.get("optimization_opportunities", [])
            for opp in opportunities:
                if opp.roi > 0.1:
                    correlation_boost[opp.category] = opp.roi

        # Sort categories by performance (worst first)
        sorted_categories = sorted(
            category_stats.items(),
            key=lambda x: (x[1]["mean"], -correlation_boost.get(x[0], 0))
        )

        # Suggest improvements for bottom 3 categories
        for category, stats in sorted_categories[:4]:
            current = stats["mean"]
            best = stats["max"]

            # Skip if already performing well
            if current >= 0.85:
                continue

            # Calculate target
            improvement = min((best - current) * 0.5, 0.2)
            target = current + improvement

            # Exp 75: Check correlation boost
            roi_boost = correlation_boost.get(category, 0)
            rationale = f"{category} is underperforming (current: {current:.2f}, best: {best:.2f}). Focused improvement here will have high impact."

            if roi_boost > 0.15:
                rationale = f"{category} is underperforming AND has high correlation with overall quality (ROI: {roi_boost:.2f}). Improving here will have maximum impact."
                # Increase target for high-ROI categories
                target = min(target + 0.05, 0.95)

            suggestions.append(
                GoalSuggestion(
                    goal_type=GoalType.CATEGORY_TARGET,
                    name=f"Improve {category} Quality",
                    description=f"Achieve {target:.2f} average score in {category}",
                    suggested_target=round(target, 2),
                    confidence=SuggestionConfidence.HIGH if stats["count"] >= 5 else SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.IMPROVEMENT_AREA,
                    rationale=rationale,
                    current_baseline=round(current, 2),
                    expected_effort="medium",
                    estimated_achievable=True,
                    category=category,
                    alternative_targets={
                        "conservative": round(current + (improvement * 0.5), 2),
                        "moderate": round(target, 2),
                        "aggressive": round(current + improvement * 1.5, 2),
                    },
                    supporting_evidence=[
                        f"Category average: {current:.2f}",
                        f"Category best: {best:.2f}",
                        f"Variance: {stats['std']:.2f}",
                        f"Correlation ROI: {roi_boost:.2f}" if roi_boost > 0 else "No strong correlation data",
                    ],
                )
            )

        return suggestions

    def _suggest_improvement_goals(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> List[GoalSuggestion]:
        """Suggest improvement goals"""
        suggestions = []
        current_avg = state.get("recent_avg_score", 0.0)

        # Look for positive trends to align with
        positive_trends = [
            t for t in insights.trend_insights
            if t.trend_direction == "improving"
        ]

        if positive_trends:
            # Suggest amplifying positive trend
            improvement_pct = 0.1  # 10% improvement
            target = min(current_avg * (1 + improvement_pct), 0.95)

            suggestions.append(
                GoalSuggestion(
                    goal_type=GoalType.IMPROVEMENT,
                    name="Accelerate Quality Improvement",
                    description=f"Improve average score by {improvement_pct*100:.0f}%",
                    suggested_target=round(target, 2),
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.TREND_ALIGNMENT,
                    rationale=f"Positive trend detected. Building on this momentum can accelerate improvement.",
                    current_baseline=round(current_avg, 2),
                    expected_effort="medium",
                    estimated_achievable=True,
                    alternative_targets={
                        "conservative": round(current_avg * 1.05, 2),
                        "moderate": round(target, 2),
                        "aggressive": round(current_avg * 1.15, 2),
                    },
                    supporting_evidence=[
                        f"Positive trends: {len(positive_trends)}",
                        f"Current trajectory: {positive_trends[0].trend_direction if positive_trends else 'stable'}",
                    ],
                )
            )

        return suggestions

    def _suggest_stability_goals(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> List[GoalSuggestion]:
        """Suggest stability goals to reduce volatility"""
        suggestions = []
        score_std = state.get("score_std", 0.0)

        # Only suggest if volatility is high
        if score_std > 0.1:
            target_std = max(score_std * 0.5, 0.05)

            suggestions.append(
                GoalSuggestion(
                    goal_type=GoalType.STABILITY,
                    name="Reduce Quality Volatility",
                    description=f"Keep score variance below {target_std:.2f} over 10 runs",
                    suggested_target=round(target_std, 2),
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.STABILITY_FOCUS,
                    rationale=f"High volatility detected (std: {score_std:.2f}). Reducing variance improves predictability and reliability.",
                    current_baseline=round(score_std, 2),
                    expected_effort="medium",
                    estimated_achievable=True,
                    alternative_targets={
                        "conservative": round(score_std * 0.7, 2),
                        "moderate": round(target_std, 2),
                        "aggressive": round(score_std * 0.3, 2),
                    },
                    supporting_evidence=[
                        f"Current std: {score_std:.2f}",
                        "High variance causes unpredictable quality",
                    ],
                )
            )

        return suggestions

    def _rank_suggestions(self, suggestions: List[GoalSuggestion]) -> List[GoalSuggestion]:
        """Rank suggestions by priority (achievable, high impact)"""
        def score_suggestion(s: GoalSuggestion) -> float:
            score = 0.0

            # Confidence bonus
            if s.confidence == SuggestionConfidence.HIGH:
                score += 3
            elif s.confidence == SuggestionConfidence.MEDIUM:
                score += 2

            # Achievability is key
            if s.estimated_achievable:
                score += 2

            # Reason priority
            if s.reason == SuggestionReason.IMPROVEMENT_AREA:
                score += 3
            elif s.reason == SuggestionReason.ACHIEVABLE_TARGET:
                score += 2
            elif s.reason == SuggestionReason.QUICK_WIN:
                score += 1

            # Effort penalty (prefer easier goals)
            if s.expected_effort == "low":
                score += 2
            elif s.expected_effort == "medium":
                score += 1

            return score

        return sorted(suggestions, key=score_suggestion, reverse=True)

    def _count_by_priority(self, suggestions: List[GoalSuggestion]) -> Dict[str, int]:
        """Count suggestions by effort level (as proxy for priority)"""
        counts = {"low": 0, "medium": 0, "high": 0}
        for s in suggestions:
            if s.expected_effort in counts:
                counts[s.expected_effort] += 1
        return counts

    def _count_by_confidence(self, suggestions: List[GoalSuggestion]) -> Dict[str, int]:
        """Count suggestions by confidence level"""
        counts = {"high": 0, "medium": 0, "low": 0}
        for s in suggestions:
            counts[s.confidence.value] += 1
        return counts

    def _generate_presets(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
        suggestions: List[GoalSuggestion],
        correlation_data: Optional[Dict] = None,
    ) -> List[GoalPreset]:
        """Generate goal presets for different scenarios

        Exp 75: Enhanced with correlation-based high-impact preset
        """
        presets = []

        # Determine project maturity
        runs_count = state.get("total_runs", 0)
        avg_score = state.get("avg_score", 0.0)

        if runs_count < 5:
            # New project preset
            presets.append(self._create_new_project_preset(state))
        elif avg_score < 0.6:
            # Improvement preset
            presets.append(self._create_improvement_preset(state, insights, correlation_data))
        elif avg_score < 0.85:
            # Refinement preset
            presets.append(self._create_refinement_preset(state, insights, correlation_data))
        else:
            # Excellence preset
            presets.append(self._create_excellence_preset(state, insights))

        # Exp 75: High-impact preset based on correlations
        if correlation_data:
            high_impact_preset = self._create_high_impact_preset(state, correlation_data)
            if high_impact_preset:
                presets.append(high_impact_preset)

        # Quick wins preset (always available)
        quick_wins = [s for s in suggestions if s.expected_effort == "low"]
        if quick_wins:
            presets.append(
                GoalPreset(
                    preset_id="quick_wins",
                    name="Quick Wins",
                    description="Low-effort goals for immediate improvement",
                    scenario="quick_wins",
                    goals=quick_wins[:3],
                    estimated_total_effort="low",
                    expected_outcomes=[
                        "Rapid quality improvements",
                        "Build momentum",
                        "Easy first goal achievements",
                    ],
                )
            )

        return presets

    def _create_new_project_preset(self, state: Dict[str, Any]) -> GoalPreset:
        """Create preset for new projects"""
        return GoalPreset(
            preset_id="new_project",
            name="New Project Foundation",
            description="Establish quality baseline and initial standards",
            scenario="new_project",
            goals=[
                GoalSuggestion(
                    goal_type=GoalType.PASS_RATE,
                    name="Establish Quality Baseline",
                    description="Achieve 60% pass rate over first 10 runs",
                    suggested_target=0.6,
                    confidence=SuggestionConfidence.HIGH,
                    reason=SuggestionReason.ACHIEVABLE_TARGET,
                    rationale="Starting with achievable goals builds quality culture",
                    current_baseline=0.0,
                    expected_effort="medium",
                    estimated_achievable=True,
                    supporting_evidence=["New project - establishing baseline"],
                ),
                GoalSuggestion(
                    goal_type=GoalType.STABILITY,
                    name="Consistent Quality Process",
                    description="Maintain consistent quality checks",
                    suggested_target=0.15,
                    confidence=SuggestionConfidence.HIGH,
                    reason=SuggestionReason.STABILITY_FOCUS,
                    rationale="Process consistency is key early",
                    current_baseline=0.0,
                    expected_effort="low",
                    estimated_achievable=True,
                    supporting_evidence=["Focus on process over scores initially"],
                ),
            ],
            estimated_total_effort="medium",
            expected_outcomes=[
                "Established quality baseline",
                "Consistent quality process",
                "Foundation for future improvements",
            ],
        )

    def _create_improvement_preset(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
        correlation_data: Optional[Dict] = None,
    ) -> GoalPreset:
        """Create preset for projects needing improvement

        Exp 75: Enhanced with correlation-based focus areas
        """
        current_score = state.get("recent_avg_score", 0.5)
        target_score = min(current_score + 0.15, 0.8)

        # Exp 75: Get high-impact categories from correlations
        focus_area = "all areas"
        if correlation_data:
            opportunities = correlation_data.get("optimization_opportunities", [])
            if opportunities:
                top_category = opportunities[0].category
                if opportunities[0].roi > 0.15:
                    focus_area = f"{top_category} (high-impact)"

        return GoalPreset(
            preset_id="improvement",
            name="Quality Improvement Focus",
            description=f"Comprehensive improvement with focus on {focus_area}",
            scenario="improvement",
            goals=[
                GoalSuggestion(
                    goal_type=GoalType.TARGET_SCORE,
                    name="Raise Quality Bar",
                    description=f"Increase average score to {target_score:.2f}",
                    suggested_target=round(target_score, 2),
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.IMPROVEMENT_AREA,
                    rationale=f"Current quality ({current_score:.2f}) needs focused improvement",
                    current_baseline=round(current_score, 2),
                    expected_effort="high",
                    estimated_achievable=True,
                    supporting_evidence=[f"Focus area: {focus_area}"],
                ),
                GoalSuggestion(
                    goal_type=GoalType.PASS_RATE,
                    name="Improve Consistency",
                    description="Achieve 75% pass rate",
                    suggested_target=0.75,
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.PASS_RATE_BOOST,
                    rationale="Better consistency reduces rework",
                    current_baseline=state.get("recent_pass_rate", 0.5),
                    expected_effort="medium",
                    estimated_achievable=True,
                ),
            ],
            estimated_total_effort="high",
            expected_outcomes=[
                "Significantly improved quality",
                "Better process reliability",
                "Reduced technical debt",
            ],
        )

    def _create_refinement_preset(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
        correlation_data: Optional[Dict] = None,
    ) -> GoalPreset:
        """Create preset for projects with good baseline

        Exp 75: Enhanced with correlation-based optimization
        """
        current_score = state.get("recent_avg_score", 0.7)

        return GoalPreset(
            preset_id="refinement",
            name="Quality Refinement",
            description="Polish and optimize quality processes",
            scenario="refinement",
            goals=[
                GoalSuggestion(
                    goal_type=GoalType.TARGET_SCORE,
                    name="Achieve Quality Excellence",
                    description="Maintain 0.85+ average score",
                    suggested_target=0.85,
                    confidence=SuggestionConfidence.HIGH,
                    reason=SuggestionReason.ACHIEVABLE_TARGET,
                    rationale="Good foundation - aim for excellence",
                    current_baseline=round(current_score, 2),
                    expected_effort="medium",
                    estimated_achievable=True,
                ),
                GoalSuggestion(
                    goal_type=GoalType.STABILITY,
                    name="Predictable Quality",
                    description="Keep variance below 0.08",
                    suggested_target=0.08,
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.STABILITY_FOCUS,
                    rationale="High quality needs consistency",
                    current_baseline=state.get("score_std", 0.1),
                    expected_effort="medium",
                    estimated_achievable=True,
                ),
            ],
            estimated_total_effort="medium",
            expected_outcomes=[
                "High-quality, consistent output",
                "Predictable quality process",
                "Excellence culture",
            ],
        )

    def _create_high_impact_preset(
        self,
        state: Dict[str, Any],
        correlation_data: Dict,
    ) -> Optional[GoalPreset]:
        """Create preset based on correlation analysis (Exp 75)

        Returns preset focused on high-ROI categories
        """
        opportunities = correlation_data.get("optimization_opportunities", [])
        high_roi = [o for o in opportunities if o.roi > 0.15]

        if not high_roi:
            return None

        # Create goals for top 2 high-ROI categories
        goals = []
        for opp in high_roi[:2]:
            current = opp.current_score
            target = min(current + opp.potential_impact, 0.95)

            goals.append(
                GoalSuggestion(
                    goal_type=GoalType.CATEGORY_TARGET,
                    name=f"High-Impact {opp.category} Boost",
                    description=f"Improve {opp.category} for +{opp.potential_impact:.3f} overall impact",
                    suggested_target=round(target, 2),
                    confidence=SuggestionConfidence.HIGH,
                    reason=SuggestionReason.IMPROVEMENT_AREA,
                    rationale=f"High ROI category (score: {opp.roi:.2f}). Maximum impact on overall quality.",
                    current_baseline=round(current, 2),
                    expected_effort=opp.effort,
                    estimated_achievable=True,
                    category=opp.category,
                    supporting_evidence=[
                        f"ROI: {opp.roi:.2f}",
                        f"Potential impact: +{opp.potential_impact:.3f}",
                        f"Related: {', '.join(opp.related_categories[:3])}",
                    ],
                )
            )

        return GoalPreset(
            preset_id="high_impact",
            name="High-Impact Optimization",
            description=f"Focus on {len(high_roi)} high-ROI categories for maximum impact",
            scenario="high_impact",
            goals=goals,
            estimated_total_effort="medium",
            expected_outcomes=[
                "Maximum overall quality improvement",
                "Efficient use of improvement effort",
                "Compound benefits from related categories",
            ],
        )

    def _create_excellence_preset(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> GoalPreset:
        """Create preset for high-performing projects"""
        return GoalPreset(
            preset_id="excellence",
            name="Sustained Excellence",
            description="Maintain and optimize high-quality standards",
            scenario="excellence",
            goals=[
                GoalSuggestion(
                    goal_type=GoalType.TARGET_SCORE,
                    name="Maintain Excellence",
                    description="Sustain 0.90+ average score",
                    suggested_target=0.90,
                    confidence=SuggestionConfidence.HIGH,
                    reason=SuggestionReason.ACHIEVABLE_TARGET,
                    rationale="Already excellent - maintain standards",
                    current_baseline=state.get("recent_avg_score", 0.85),
                    expected_effort="low",
                    estimated_achievable=True,
                ),
                GoalSuggestion(
                    goal_type=GoalType.STREAK,
                    name="Quality Streak",
                    description="Achieve 10 consecutive passed runs",
                    suggested_target=10.0,
                    confidence=SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.STRETCH_GOAL,
                    rationale="Demonstrate sustained excellence",
                    current_baseline=0.0,
                    expected_effort="low",
                    estimated_achievable=True,
                ),
            ],
            estimated_total_effort="low",
            expected_outcomes=[
                "Sustained excellence",
                "Quality consistency",
                "Best practices showcase",
            ],
        )

    def _generate_beginner_suggestions(
        self,
        runs: List[QualityRunRecord],
        include_presets: bool,
        task_alias: Optional[str],
    ) -> SuggestionReport:
        """Generate suggestions for projects with limited data"""
        suggestions = [
            GoalSuggestion(
                goal_type=GoalType.PASS_RATE,
                name="Establish Quality Baseline",
                description="Start with achievable 50% pass rate",
                suggested_target=0.5,
                confidence=SuggestionConfidence.MEDIUM,
                reason=SuggestionReason.QUICK_WIN,
                rationale="Build quality culture gradually",
                current_baseline=0.0,
                expected_effort="low",
                estimated_achievable=True,
                supporting_evidence=["New project - start simple"],
            ),
            GoalSuggestion(
                goal_type=GoalType.TARGET_SCORE,
                name="Initial Quality Target",
                description="Achieve 0.6 average score",
                suggested_target=0.6,
                confidence=SuggestionConfidence.MEDIUM,
                reason=SuggestionReason.ACHIEVABLE_TARGET,
                rationale="Reasonable initial target",
                current_baseline=0.0,
                expected_effort="low",
                estimated_achievable=True,
            ),
        ]

        presets = [self._create_new_project_preset({"total_runs": len(runs)})] if include_presets else []

        return SuggestionReport(
            suggestions_generated=len(suggestions),
            suggestions_by_priority={"low": 2, "medium": 0, "high": 0},
            suggestions_by_confidence={"medium": 2, "high": 0, "low": 0},
            suggestions=suggestions,
            presets=presets,
            top_recommendations=[s.name for s in suggestions],
            analysis_summary="Limited data available. Starting with beginner-friendly goals to establish quality baseline.",
            project_context={"has_data": False, "total_runs": len(runs)},
            generated_at=datetime.now().isoformat(),
            task_alias=task_alias,
        )

    def _generate_summary(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
    ) -> str:
        """Generate analysis summary"""
        if not state.get("has_data"):
            return "No quality history available. Start with basic goals to establish baseline."

        total_runs = state["total_runs"]
        avg_score = state.get("avg_score", 0.0)
        pass_rate = state.get("overall_pass_rate", 0.0)

        summary_parts = [
            f"Based on {total_runs} quality runs with average score of {avg_score:.2f} ",
            f"and {pass_rate*100:.0f}% pass rate.",
        ]

        if insights.action_items:
            summary_parts.append(
                f" Identified {len(insights.action_items)} actionable optimization opportunities."
            )

        if insights.trend_insights:
            positive = sum(1 for t in insights.trend_insights if t.trend_direction == "improving")
            if positive > 0:
                summary_parts.append(f" {positive} positive trends detected.")

        return "".join(summary_parts)

    def apply_suggestion(self, suggestion: GoalSuggestion) -> QualityGoal:
        """Apply a suggestion and create the actual goal

        Args:
            suggestion: The suggestion to apply

        Returns:
            Created QualityGoal
        """
        goal = self.goals_manager.create_goal(
            name=suggestion.name,
            description=suggestion.description,
            goal_type=suggestion.goal_type,
            target_value=suggestion.suggested_target,
            category=suggestion.category,
            window_size=10,
        )

        return goal

    # Exp 75: Correlation-aware suggestion methods

    def _get_correlation_data(
        self, task_alias: Optional[str]
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """Get correlation analysis data for goal suggestions (Exp 75)

        Returns:
            Tuple of (correlation_insights, leading_indicators, correlation_data)
        """
        analyzer = self._get_correlation_analyzer()
        if analyzer is None:
            return [], {}, {}

        try:
            # Get correlation report
            report = analyzer.analyze_correlations(task_alias=task_alias or "default")

            if report.analyzed_runs == 0:
                return [], {}, {}

            # Extract correlation insights
            correlation_insights = []
            for opp in report.optimization_opportunities[:5]:
                if opp.potential_impact > 0.05:
                    correlation_insights.append({
                        "category": opp.category,
                        "current_score": opp.current_score,
                        "potential_impact": opp.potential_impact,
                        "roi": opp.roi,
                        "effort": opp.effort,
                    })

            # Extract leading indicators
            leading_indicators = []
            for indicator in report.leading_indicators[:5]:
                if indicator.indicator_type.value == "leading":
                    leading_indicators.append({
                        "category": indicator.category,
                        "correlation": indicator.correlation,
                        "predictive_power": indicator.predictive_power,
                        "lag_periods": indicator.lag_periods,
                    })

            # Build correlation data dictionary
            correlation_data = {
                "optimization_opportunities": report.optimization_opportunities,
                "leading_indicators": report.leading_indicators,
                "category_correlations": report.category_correlations,
            }

            return correlation_insights, leading_indicators, correlation_data

        except Exception:
            return [], {}, {}

    def _suggest_correlation_goals(
        self,
        state: Dict[str, Any],
        correlation_data: Dict,
    ) -> List[GoalSuggestion]:
        """Generate suggestions based on correlation analysis (Exp 75)

        Args:
            state: Current quality state
            correlation_data: Correlation analysis data

        Returns:
            List of correlation-based suggestions
        """
        suggestions = []

        opportunities = correlation_data.get("optimization_opportunities", [])

        # Get top 2 high-ROI opportunities
        for opp in opportunities[:2]:
            if opp.potential_impact < 0.05:
                continue

            category = opp.category
            current = opp.current_score
            impact = opp.potential_impact

            # Calculate target based on potential impact
            target = min(current + impact, 0.95)

            suggestions.append(
                GoalSuggestion(
                    goal_type=GoalType.CATEGORY_TARGET,
                    name=f"High-Impact {category} Improvement",
                    description=f"Improve {category} to boost overall quality by +{impact:.3f}",
                    suggested_target=round(target, 2),
                    confidence=SuggestionConfidence.HIGH if opp.roi > 0.15 else SuggestionConfidence.MEDIUM,
                    reason=SuggestionReason.IMPROVEMENT_AREA,
                    rationale=f"High-ROI opportunity: {opp.roi:.2f}. {opp.recommendation}",
                    current_baseline=round(current, 2),
                    expected_effort=opp.effort,
                    estimated_achievable=True,
                    category=category,
                    alternative_targets={
                        "conservative": round(current + (impact * 0.5), 2),
                        "moderate": round(target, 2),
                        "aggressive": round(min(target + 0.1, 0.98), 2),
                    },
                    supporting_evidence=[
                        f"Potential impact: +{impact:.3f} on overall quality",
                        f"ROI score: {opp.roi:.2f}",
                        f"Related categories: {', '.join(opp.related_categories[:3])}",
                    ],
                )
            )

        return suggestions

    def _rank_suggestions(
        self,
        suggestions: List[GoalSuggestion],
        correlation_data: Optional[Dict] = None,
    ) -> List[GoalSuggestion]:
        """Rank suggestions by priority (achievable, high impact)

        Exp 75: Enhanced with correlation-based boosting
        """
        def score_suggestion(s: GoalSuggestion) -> float:
            score = 0.0

            # Confidence bonus
            if s.confidence == SuggestionConfidence.HIGH:
                score += 3
            elif s.confidence == SuggestionConfidence.MEDIUM:
                score += 2

            # Achievability is key
            if s.estimated_achievable:
                score += 2

            # Reason priority
            if s.reason == SuggestionReason.IMPROVEMENT_AREA:
                score += 3
            elif s.reason == SuggestionReason.ACHIEVABLE_TARGET:
                score += 2
            elif s.reason == SuggestionReason.QUICK_WIN:
                score += 1

            # Effort penalty (prefer easier goals)
            if s.expected_effort == "low":
                score += 2
            elif s.expected_effort == "medium":
                score += 1

            # Exp 75: Correlation boost
            if correlation_data and s.category:
                opportunities = correlation_data.get("optimization_opportunities", [])
                for opp in opportunities:
                    if opp.category == s.category and opp.roi > 0.15:
                        score += 2  # Boost high-ROI category goals
                        break

            return score

        return sorted(suggestions, key=score_suggestion, reverse=True)

    def _generate_summary(
        self,
        state: Dict[str, Any],
        insights: InsightsReport,
        correlation_data: Optional[Dict] = None,
    ) -> str:
        """Generate analysis summary

        Exp 75: Enhanced with correlation information
        """
        if not state.get("has_data"):
            return "No quality history available. Start with basic goals to establish baseline."

        total_runs = state["total_runs"]
        avg_score = state.get("avg_score", 0.0)
        pass_rate = state.get("overall_pass_rate", 0.0)

        summary_parts = [
            f"Based on {total_runs} quality runs with average score of {avg_score:.2f} ",
            f"and {pass_rate*100:.0f}% pass rate.",
        ]

        if insights.action_items:
            summary_parts.append(
                f" Identified {len(insights.action_items)} actionable optimization opportunities."
            )

        if insights.trend_insights:
            positive = sum(1 for t in insights.trend_insights if t.trend_direction == "improving")
            if positive > 0:
                summary_parts.append(f" {positive} positive trends detected.")

        # Exp 75: Add correlation insights
        if correlation_data:
            opportunities = correlation_data.get("optimization_opportunities", [])
            high_roi = [o for o in opportunities if o.roi > 0.15]
            if high_roi:
                summary_parts.append(f" {len(high_roi)} high-ROI improvement opportunities identified.")

            leading = correlation_data.get("leading_indicators", [])
            leading_count = sum(1 for i in leading if i.indicator_type.value == "leading")
            if leading_count > 0:
                summary_parts.append(f" {leading_count} leading quality indicator(s) found.")

        return "".join(summary_parts)


# Convenience functions for easy integration

def suggest_goals(
    history_dir: Optional[Path] = None,
    goals_dir: Optional[Path] = None,
    max_suggestions: int = 10,
    include_presets: bool = True,
    task_alias: Optional[str] = None,
    use_correlations: bool = True,  # Exp 75
) -> SuggestionReport:
    """Generate goal suggestions

    Args:
        history_dir: Directory for quality history
        goals_dir: Directory for quality goals
        max_suggestions: Maximum suggestions to generate
        include_presets: Whether to include goal presets
        task_alias: Optional task alias
        use_correlations: Whether to use correlation analysis (Exp 75)

    Returns:
        SuggestionReport with suggestions
    """
    suggester = GoalSuggester(history_dir=history_dir, goals_dir=goals_dir)
    return suggester.generate_suggestions(
        max_suggestions=max_suggestions,
        include_presets=include_presets,
        task_alias=task_alias,
        use_correlations=use_correlations,
    )


def format_suggestions_report(report: SuggestionReport) -> str:
    """Format suggestions report as text

    Args:
        report: SuggestionReport to format

    Returns:
        Formatted text report
    """
    lines = [
        "# Quality Goal Suggestions",
        "",
        f"**Generated:** {report.generated_at}",
        f"**Suggestions:** {report.suggestions_generated}",
        "",
        "## Summary",
        "",
        report.analysis_summary,
        "",
    ]

    if report.top_recommendations:
        lines.extend([
            "### Top Recommendations",
            "",
        ])
        for i, rec in enumerate(report.top_recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    if report.suggestions:
        lines.extend([
            "## Suggested Goals",
            "",
        ])

        for i, suggestion in enumerate(report.suggestions, 1):
            confidence_emoji = {
                "high": "🔒",
                "medium": "🔐",
                "low": "🔓",
            }.get(suggestion.confidence.value, "•")

            lines.extend([
                f"### {i}. {suggestion.name} {confidence_emoji}",
                "",
                f"**Type:** {suggestion.goal_type.value}",
                f"**Target:** {suggestion.suggested_target}",
                f"**Current:** {suggestion.current_baseline}",
                f"**Confidence:** {suggestion.confidence.value}",
                f"**Effort:** {suggestion.expected_effort}",
                "",
                f"{suggestion.description}",
                "",
                f"**Why:** {suggestion.rationale}",
                "",
            ])

            if suggestion.alternative_targets:
                lines.append("**Alternatives:**")
                for alt_name, alt_value in suggestion.alternative_targets.items():
                    lines.append(f"  - {alt_name}: {alt_value}")
                lines.append("")

            if suggestion.supporting_evidence:
                lines.append("**Evidence:**")
                for evidence in suggestion.supporting_evidence:
                    lines.append(f"  - {evidence}")
                lines.append("")

    if report.presets:
        lines.extend([
            "## Goal Presets",
            "",
        ])

        for preset in report.presets:
            lines.extend([
                f"### {preset.name}",
                "",
                f"{preset.description}",
                "",
                f"**Scenario:** {preset.scenario}",
                f"**Effort:** {preset.estimated_total_effort}",
                "",
                "**Goals:**",
            ])
            for goal in preset.goals:
                lines.append(f"  - {goal.name}")
            lines.append("")

            if preset.expected_outcomes:
                lines.append("**Expected Outcomes:**")
                for outcome in preset.expected_outcomes:
                    lines.append(f"  - {outcome}")
                lines.append("")

    return "\n".join(lines)


def format_suggestions_json(report: SuggestionReport) -> str:
    """Format suggestions report as JSON

    Args:
        report: SuggestionReport to format

    Returns:
        JSON string
    """
    import json
    return json.dumps(report.to_dict(), indent=2)


def get_suggestions_summary(report: SuggestionReport) -> str:
    """Get quick one-line summary of suggestions

    Args:
        report: SuggestionReport to summarize

    Returns:
        One-line summary string
    """
    top = report.top_recommendations[0] if report.top_recommendations else "No suggestions"
    return f"{report.suggestions_generated} suggestions generated. Top: {top}"
