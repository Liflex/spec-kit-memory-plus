"""
Quality Benchmarking System (Exp 75)

Provides quality benchmarking capabilities for comparing quality metrics:
- Percentile Ranking: Determine where current quality stands vs historical data
- Benchmark Baselines: Establish project-specific quality baselines
- Industry Standards: Compare against industry quality standards
- Trend Validation: Validate quality improvements against benchmarks
- Performance Targets: Set realistic quality targets based on benchmarks

This transforms quality monitoring from absolute scores to relative positioning,
enabling better decision-making through context-aware quality assessment.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import statistics
from datetime import datetime
from collections import defaultdict
import math

from .quality_history import QualityRunRecord, QualityHistoryManager, QualityStatistics
from .priority_profiles import CATEGORY_TAGS


class BenchmarkType(Enum):
    """Types of benchmarks"""
    HISTORICAL = "historical"  # Based on project's historical data
    INDUSTRY = "industry"  # Industry-wide standards
    CUSTOM = "custom"  # User-defined benchmarks
    PEER = "peer"  # Peer project comparisons


class BenchmarkComparison(Enum):
    """Comparison result vs benchmark"""
    EXCELLENT = "excellent"  # Top 10%
    ABOVE_AVERAGE = "above_average"  # Top 25%
    AVERAGE = "average"  # Middle 50%
    BELOW_AVERAGE = "below_average"  # Bottom 25%
    POOR = "poor"  # Bottom 10%


@dataclass
class PercentileMetrics:
    """Percentile-based metrics for a quality measure"""
    p0: float  # Minimum
    p10: float  # 10th percentile
    p25: float  # 25th percentile (Q1)
    p50: float  # 50th percentile (median)
    p75: float  # 75th percentile (Q3)
    p90: float  # 90th percentile
    p95: float  # 95th percentile
    p99: float  # 99th percentile
    p100: float  # Maximum
    mean: float
    std_dev: float
    sample_size: int

    def get_percentile_rank(self, value: float) -> float:
        """Get percentile rank of a value (0-100)"""
        if self.sample_size == 0:
            return 50.0

        # Simple percentile calculation using interpolation
        if value <= self.p0:
            return 0.0
        if value >= self.p100:
            return 100.0

        # Find which percentile range the value falls into
        percentiles = [0, 10, 25, 50, 75, 90, 95, 99, 100]
        values = [self.p0, self.p10, self.p25, self.p50, self.p75, self.p90, self.p95, self.p99, self.p100]

        for i in range(len(percentiles) - 1):
            if values[i] <= value <= values[i + 1]:
                # Linear interpolation within the range
                lower_pct = percentiles[i]
                upper_pct = percentiles[i + 1]
                lower_val = values[i]
                upper_val = values[i + 1]

                if upper_val == lower_val:
                    return lower_pct

                fraction = (value - lower_val) / (upper_val - lower_val)
                return lower_pct + fraction * (upper_pct - lower_pct)

        return 50.0

    def get_comparison(self, value: float) -> BenchmarkComparison:
        """Get comparison category for a value"""
        rank = self.get_percentile_rank(value)

        if rank >= 90:
            return BenchmarkComparison.EXCELLENT
        elif rank >= 75:
            return BenchmarkComparison.ABOVE_AVERAGE
        elif rank >= 25:
            return BenchmarkComparison.AVERAGE
        elif rank >= 10:
            return BenchmarkComparison.BELOW_AVERAGE
        else:
            return BenchmarkComparison.POOR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "p0": self.p0,
            "p10": self.p10,
            "p25": self.p25,
            "p50": self.p50,
            "p75": self.p75,
            "p90": self.p90,
            "p95": self.p95,
            "p99": self.p99,
            "p100": self.p100,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "sample_size": self.sample_size,
        }


@dataclass
class BenchmarkResult:
    """Result of benchmark comparison"""
    metric_name: str  # Name of the metric being benchmarked
    current_value: float  # Current value
    benchmark_type: BenchmarkType
    percentile_rank: float  # 0-100
    comparison: BenchmarkComparison
    percentile_metrics: PercentileMetrics
    difference_from_mean: float  # Current value - mean
    difference_from_median: float  # Current value - median
    z_score: float  # Standard score
    percentile_label: str  # Human-readable percentile label
    comparison_label: str  # Human-readable comparison label

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "benchmark_type": self.benchmark_type.value,
            "percentile_rank": round(self.percentile_rank, 2),
            "comparison": self.comparison.value,
            "percentile_metrics": self.percentile_metrics.to_dict(),
            "difference_from_mean": round(self.difference_from_mean, 3),
            "difference_from_median": round(self.difference_from_median, 3),
            "z_score": round(self.z_score, 2),
            "percentile_label": self.percentile_label,
            "comparison_label": self.comparison_label,
        }


@dataclass
class CategoryBenchmark:
    """Benchmark for a specific quality category"""
    category: str
    current_score: float
    percentile_rank: float
    comparison: BenchmarkComparison
    percentile_metrics: PercentileMetrics
    trend: str  # "improving", "declining", "stable"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "category": self.category,
            "current_score": round(self.current_score, 3),
            "percentile_rank": round(self.percentile_rank, 2),
            "comparison": self.comparison.value,
            "percentile_metrics": self.percentile_metrics.to_dict(),
            "trend": self.trend,
        }


@dataclass
class BenchmarkProfile:
    """A benchmark profile for a specific context"""
    name: str
    description: str
    benchmark_type: BenchmarkType
    project_type: Optional[str] = None  # "web-app", "api", etc.
    criteria_template: Optional[str] = None  # "backend", "frontend", etc.
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    min_sample_size: int = 10  # Minimum samples for reliable benchmark

    # Benchmark data
    overall_metrics: Optional[PercentileMetrics] = None
    category_metrics: Dict[str, PercentileMetrics] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "benchmark_type": self.benchmark_type.value,
            "project_type": self.project_type,
            "criteria_template": self.criteria_template,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "min_sample_size": self.min_sample_size,
            "overall_metrics": self.overall_metrics.to_dict() if self.overall_metrics else None,
            "category_metrics": {
                cat: metrics.to_dict()
                for cat, metrics in self.category_metrics.items()
            },
        }


@dataclass
class BenchmarkReport:
    """Complete benchmarking report"""
    profile_name: str
    task_alias: str
    generated_at: datetime
    sample_size: int
    reliability: str  # "high", "medium", "low" based on sample size

    # Overall benchmark
    overall_benchmark: Optional[BenchmarkResult] = None

    # Category benchmarks
    category_benchmarks: Dict[str, CategoryBenchmark] = field(default_factory=dict)

    # Summary statistics
    total_categories: int = 0
    excellent_count: int = 0
    above_average_count: int = 0
    average_count: int = 0
    below_average_count: int = 0
    poor_count: int = 0

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    priority_improvements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "profile_name": self.profile_name,
            "task_alias": self.task_alias,
            "generated_at": self.generated_at.isoformat(),
            "sample_size": self.sample_size,
            "reliability": self.reliability,
            "overall_benchmark": self.overall_benchmark.to_dict() if self.overall_benchmark else None,
            "category_benchmarks": {
                cat: bench.to_dict()
                for cat, bench in self.category_benchmarks.items()
            },
            "summary": {
                "total_categories": self.total_categories,
                "excellent_count": self.excellent_count,
                "above_average_count": self.above_average_count,
                "average_count": self.average_count,
                "below_average_count": self.below_average_count,
                "poor_count": self.poor_count,
            },
            "recommendations": self.recommendations,
            "priority_improvements": self.priority_improvements,
        }


class QualityBenchmarkingEngine:
    """
    Engine for quality benchmarking analysis.

    Computes percentile-based benchmarks and comparisons to provide
    context-aware quality assessment.
    """

    # Industry-standard quality baselines (based on typical quality scores)
    INDUSTRY_BASELINES = {
        "overall": {
            "excellent": 0.90,
            "good": 0.80,
            "average": 0.70,
            "below_average": 0.60,
        },
        "security": {
            "excellent": 0.95,
            "good": 0.85,
            "average": 0.75,
            "below_average": 0.65,
        },
        "correctness": {
            "excellent": 0.92,
            "good": 0.82,
            "average": 0.72,
            "below_average": 0.62,
        },
        "performance": {
            "excellent": 0.88,
            "good": 0.78,
            "average": 0.68,
            "below_average": 0.58,
        },
        "testing": {
            "excellent": 0.85,
            "good": 0.75,
            "average": 0.65,
            "below_average": 0.55,
        },
    }

    def __init__(
        self,
        history_dir: Optional[Path] = None,
        min_sample_size: int = 10
    ):
        """
        Initialize the benchmarking engine.

        Args:
            history_dir: Directory for quality history data
            min_sample_size: Minimum samples required for reliable benchmarks
        """
        self.history_manager = QualityHistoryManager(history_dir=history_dir)
        self.min_sample_size = min_sample_size

    def _calculate_percentiles(
        self,
        values: List[float]
    ) -> PercentileMetrics:
        """
        Calculate percentile metrics from a list of values.

        Args:
            values: List of numeric values

        Returns:
            PercentileMetrics object with calculated percentiles
        """
        if not values:
            return PercentileMetrics(
                p0=0.0, p10=0.0, p25=0.0, p50=0.0, p75=0.0,
                p90=0.0, p95=0.0, p99=0.0, p100=0.0,
                mean=0.0, std_dev=0.0, sample_size=0
            )

        sorted_values = sorted(values)
        n = len(sorted_values)

        def get_percentile(p: float) -> float:
            """Get value at percentile p (0-100)"""
            if n == 0:
                return 0.0
            idx = (p / 100) * (n - 1)
            lower = int(math.floor(idx))
            upper = int(math.ceil(idx))
            if lower == upper:
                return sorted_values[lower]
            # Linear interpolation
            weight = idx - lower
            return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight

        return PercentileMetrics(
            p0=get_percentile(0),
            p10=get_percentile(10),
            p25=get_percentile(25),
            p50=get_percentile(50),
            p75=get_percentile(75),
            p90=get_percentile(90),
            p95=get_percentile(95),
            p99=get_percentile(99),
            p100=get_percentile(100),
            mean=statistics.mean(values),
            std_dev=statistics.stdev(values) if n > 1 else 0.0,
            sample_size=n,
        )

    def create_historical_benchmark(
        self,
        task_alias: str = "default",
        max_runs: int = 100,
        profile_name: Optional[str] = None
    ) -> BenchmarkProfile:
        """
        Create a benchmark profile from historical quality data.

        Args:
            task_alias: Task to analyze
            max_runs: Maximum number of historical runs to include
            profile_name: Name for the benchmark profile

        Returns:
            BenchmarkProfile with calculated percentile metrics
        """
        # Get historical runs
        history = self.history_manager.get_history(task_alias)
        runs = history[:max_runs]

        if not runs:
            # Return empty profile if no history
            return BenchmarkProfile(
                name=profile_name or f"{task_alias}-benchmark",
                description=f"Historical benchmark for {task_alias}",
                benchmark_type=BenchmarkType.HISTORICAL,
                project_type=task_alias,
            )

        # Extract overall scores
        overall_scores = [run.final_score for run in runs if run.final_score is not None]

        # Calculate overall percentiles
        overall_metrics = self._calculate_percentiles(overall_scores) if overall_scores else None

        # Extract category scores
        category_scores = defaultdict(list)
        for run in runs:
            if run.category_scores:
                for category, score in run.category_scores.items():
                    category_scores[category].append(score)

        # Calculate category percentiles
        category_metrics = {}
        for category, scores in category_scores.items():
            category_metrics[category] = self._calculate_percentiles(scores)

        return BenchmarkProfile(
            name=profile_name or f"{task_alias}-benchmark",
            description=f"Historical benchmark for {task_alias} based on {len(runs)} runs",
            benchmark_type=BenchmarkType.HISTORICAL,
            project_type=task_alias,
            overall_metrics=overall_metrics,
            category_metrics=category_metrics,
            min_sample_size=self.min_sample_size,
        )

    def compare_to_benchmark(
        self,
        current_score: float,
        benchmark: BenchmarkProfile,
        category: Optional[str] = None
    ) -> BenchmarkResult:
        """
        Compare a current score to a benchmark.

        Args:
            current_score: Current quality score
            benchmark: Benchmark profile to compare against
            category: Optional category for category-specific comparison

        Returns:
            BenchmarkResult with comparison details
        """
        # Get appropriate percentile metrics
        if category and category in benchmark.category_metrics:
            percentile_metrics = benchmark.category_metrics[category]
            metric_name = f"category_{category}"
        elif benchmark.overall_metrics:
            percentile_metrics = benchmark.overall_metrics
            metric_name = "overall_quality"
        else:
            # No benchmark data available
            raise ValueError(f"No benchmark data available for {category or 'overall'}")

        # Calculate percentile rank
        percentile_rank = percentile_metrics.get_percentile_rank(current_score)

        # Get comparison category
        comparison = percentile_metrics.get_comparison(current_score)

        # Calculate differences
        diff_from_mean = current_score - percentile_metrics.mean
        diff_from_median = current_score - percentile_metrics.p50

        # Calculate z-score
        z_score = (
            (current_score - percentile_metrics.mean) / percentile_metrics.std_dev
            if percentile_metrics.std_dev > 0
            else 0.0
        )

        # Generate labels
        percentile_label = f"{percentile_rank:.1f}th percentile"
        comparison_label = comparison.value.replace("_", " ").title()

        return BenchmarkResult(
            metric_name=metric_name,
            current_value=current_score,
            benchmark_type=benchmark.benchmark_type,
            percentile_rank=percentile_rank,
            comparison=comparison,
            percentile_metrics=percentile_metrics,
            difference_from_mean=diff_from_mean,
            difference_from_median=diff_from_median,
            z_score=z_score,
            percentile_label=percentile_label,
            comparison_label=comparison_label,
        )

    def generate_benchmark_report(
        self,
        task_alias: str = "default",
        profile: Optional[BenchmarkProfile] = None,
        current_scores: Optional[Dict[str, float]] = None,
        max_runs: int = 100
    ) -> BenchmarkReport:
        """
        Generate a comprehensive benchmark report.

        Args:
            task_alias: Task to analyze
            profile: Benchmark profile (created from history if not provided)
            current_scores: Current scores dict with 'overall' and category scores
            max_runs: Maximum historical runs for benchmark creation

        Returns:
            BenchmarkReport with comprehensive comparison
        """
        # Create benchmark profile if not provided
        if profile is None:
            profile = self.create_historical_benchmark(
                task_alias=task_alias,
                max_runs=max_runs
            )

        # Get current scores
        if current_scores is None:
            # Get most recent run
            history = self.history_manager.get_history(task_alias)
            if history:
                latest = history[0]
                current_scores = {"overall": latest.final_score}
                if latest.category_scores:
                    current_scores.update(latest.category_scores)
            else:
                current_scores = {}

        # Determine reliability
        sample_size = (
            profile.overall_metrics.sample_size if profile.overall_metrics else 0
        )
        if sample_size >= 30:
            reliability = "high"
        elif sample_size >= 10:
            reliability = "medium"
        else:
            reliability = "low"

        # Initialize report
        report = BenchmarkReport(
            profile_name=profile.name,
            task_alias=task_alias,
            generated_at=datetime.now(),
            sample_size=sample_size,
            reliability=reliability,
        )

        # Compare overall score
        overall_score = current_scores.get("overall")
        if overall_score and profile.overall_metrics:
            report.overall_benchmark = self.compare_to_benchmark(
                overall_score, profile
            )

        # Compare category scores
        for category, score in current_scores.items():
            if category == "overall":
                continue

            if category in profile.category_metrics:
                percentile_metrics = profile.category_metrics[category]
                percentile_rank = percentile_metrics.get_percentile_rank(score)
                comparison = percentile_metrics.get_comparison(score)

                # Determine trend (placeholder - would need historical trend data)
                trend = "stable"

                report.category_benchmarks[category] = CategoryBenchmark(
                    category=category,
                    current_score=score,
                    percentile_rank=percentile_rank,
                    comparison=comparison,
                    percentile_metrics=percentile_metrics,
                    trend=trend,
                )

        # Calculate summary statistics
        report.total_categories = len(report.category_benchmarks)
        for bench in report.category_benchmarks.values():
            if bench.comparison == BenchmarkComparison.EXCELLENT:
                report.excellent_count += 1
            elif bench.comparison == BenchmarkComparison.ABOVE_AVERAGE:
                report.above_average_count += 1
            elif bench.comparison == BenchmarkComparison.AVERAGE:
                report.average_count += 1
            elif bench.comparison == BenchmarkComparison.BELOW_AVERAGE:
                report.below_average_count += 1
            elif bench.comparison == BenchmarkComparison.POOR:
                report.poor_count += 1

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        # Generate priority improvements
        report.priority_improvements = self._generate_priority_improvements(report)

        return report

    def _generate_recommendations(
        self,
        report: BenchmarkReport
    ) -> List[str]:
        """Generate recommendations based on benchmark results"""
        recommendations = []

        if report.reliability == "low":
            recommendations.append(
                "Benchmark reliability is low due to limited historical data. "
                "Continue running quality checks to improve accuracy."
            )

        if report.overall_benchmark:
            comp = report.overall_benchmark.comparison
            if comp == BenchmarkComparison.POOR:
                recommendations.append(
                    "Overall quality is in bottom 10% compared to historical data. "
                    "Immediate attention required."
                )
            elif comp == BenchmarkComparison.BELOW_AVERAGE:
                recommendations.append(
                    "Overall quality is below average. Review and prioritize improvements."
                )
            elif comp == BenchmarkComparison.EXCELLENT:
                recommendations.append(
                    "Excellent quality performance! Consider raising quality targets."
                )

        # Category-specific recommendations
        for category, bench in report.category_benchmarks.items():
            if bench.comparison == BenchmarkComparison.POOR:
                recommendations.append(
                    f"Category '{category}' is critically low (bottom 10%). "
                    f"Focus improvement efforts here."
                )
            elif bench.comparison == BenchmarkComparison.EXCELLENT:
                recommendations.append(
                    f"Category '{category}' is excellent (top 10%). "
                    f"Could serve as best practice reference."
                )

        return recommendations

    def _generate_priority_improvements(
        self,
        report: BenchmarkReport
    ) -> List[str]:
        """Generate prioritized improvement actions"""
        improvements = []

        # Sort categories by percentile rank (lowest first)
        sorted_categories = sorted(
            report.category_benchmarks.items(),
            key=lambda x: x[1].percentile_rank
        )

        for category, bench in sorted_categories:
            if bench.percentile_rank < 25:
                improvements.append(
                    f"[HIGH PRIORITY] {category}: Currently at {bench.percentile_rank:.1f}th percentile"
                )
            elif bench.percentile_rank < 50:
                improvements.append(
                    f"[MEDIUM PRIORITY] {category}: Currently at {bench.percentile_rank:.1f}th percentile"
                )

        return improvements

    def get_industry_benchmark(
        self,
        category: str = "overall"
    ) -> Optional[PercentileMetrics]:
        """
        Get industry-standard benchmark for a category.

        Args:
            category: Category to get benchmark for

        Returns:
            PercentileMetrics with industry baseline or None
        """
        baselines = self.INDUSTRY_BASELINES.get(category)
        if not baselines:
            return None

        # Convert baseline dict to percentile metrics
        return PercentileMetrics(
            p0=0.0,
            p10=baselines.get("below_average", 0.5),
            p25=baselines.get("average", 0.6),
            p50=baselines.get("average", 0.7),
            p75=baselines.get("good", 0.8),
            p90=baselines.get("good", 0.85),
            p95=baselines.get("excellent", 0.9),
            p99=1.0,
            p100=1.0,
            mean=baselines.get("average", 0.7),
            std_dev=0.15,  # Estimated
            sample_size=1000,  # Industry baseline
        )


# Module-level convenience functions

def create_benchmark(
    task_alias: str = "default",
    max_runs: int = 100,
    history_dir: Optional[Path] = None
) -> BenchmarkProfile:
    """
    Create a benchmark profile from historical data.

    Args:
        task_alias: Task to analyze
        max_runs: Maximum historical runs to include
        history_dir: Custom history directory

    Returns:
        BenchmarkProfile with calculated percentiles
    """
    engine = QualityBenchmarkingEngine(history_dir=history_dir)
    return engine.create_historical_benchmark(
        task_alias=task_alias,
        max_runs=max_runs
    )


def compare_quality(
    current_score: float,
    benchmark: BenchmarkProfile,
    category: Optional[str] = None
) -> BenchmarkResult:
    """
    Compare current quality to benchmark.

    Args:
        current_score: Current quality score (0-1)
        benchmark: Benchmark profile
        category: Optional category for comparison

    Returns:
        BenchmarkResult with comparison details
    """
    engine = QualityBenchmarkingEngine()
    return engine.compare_to_benchmark(current_score, benchmark, category)


def generate_benchmark_report(
    task_alias: str = "default",
    current_scores: Optional[Dict[str, float]] = None,
    max_runs: int = 100,
    history_dir: Optional[Path] = None
) -> BenchmarkReport:
    """
    Generate a comprehensive benchmark report.

    Args:
        task_alias: Task to analyze
        current_scores: Current scores dict (uses latest if None)
        max_runs: Maximum historical runs for benchmark
        history_dir: Custom history directory

    Returns:
        BenchmarkReport with comprehensive comparison
    """
    engine = QualityBenchmarkingEngine(history_dir=history_dir)
    return engine.generate_benchmark_report(
        task_alias=task_alias,
        current_scores=current_scores,
        max_runs=max_runs
    )


def format_benchmark_report(
    report: BenchmarkReport,
    detailed: bool = True
) -> str:
    """
    Format benchmark report as human-readable text.

    Args:
        report: Benchmark report to format
        detailed: Include detailed category breakdown

    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"QUALITY BENCHMARK REPORT: {report.profile_name}")
    lines.append(f"Task: {report.task_alias}")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Sample Size: {report.sample_size} runs")
    lines.append(f"Reliability: {report.reliability.upper()}")
    lines.append("=" * 60)
    lines.append("")

    # Overall benchmark
    if report.overall_benchmark:
        b = report.overall_benchmark
        lines.append("OVERALL QUALITY")
        lines.append("-" * 40)
        lines.append(f"Current Score: {b.current_value:.3f}")
        lines.append(f"Percentile Rank: {b.percentile_label}")
        lines.append(f"Comparison: {b.comparison_label}")
        lines.append(f"Difference from Mean: {b.difference_from_mean:+.3f}")
        lines.append(f"Z-Score: {b.z_score:+.2f}")
        lines.append("")

    # Summary
    lines.append("CATEGORY SUMMARY")
    lines.append("-" * 40)
    summary = {
        BenchmarkComparison.EXCELLENT: report.excellent_count,
        BenchmarkComparison.ABOVE_AVERAGE: report.above_average_count,
        BenchmarkComparison.AVERAGE: report.average_count,
        BenchmarkComparison.BELOW_AVERAGE: report.below_average_count,
        BenchmarkComparison.POOR: report.poor_count,
    }
    for comp, count in summary.items():
        if count > 0:
            lines.append(f"  {comp.value.replace('_', ' ').title()}: {count}")
    lines.append("")

    # Category benchmarks
    if detailed and report.category_benchmarks:
        lines.append("CATEGORY BREAKDOWN")
        lines.append("-" * 40)
        for category, bench in sorted(
            report.category_benchmarks.items(),
            key=lambda x: x[1].percentile_rank,
            reverse=True
        ):
            lines.append(f"\n{category.upper()}")
            lines.append(f"  Score: {bench.current_score:.3f}")
            lines.append(f"  Percentile: {bench.percentile_rank:.1f}th")
            lines.append(f"  Comparison: {bench.comparison.value}")
            lines.append(f"  Trend: {bench.trend}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 40)
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    # Priority improvements
    if report.priority_improvements:
        lines.append("PRIORITY IMPROVEMENTS")
        lines.append("-" * 40)
        for imp in report.priority_improvements:
            lines.append(f"  {imp}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_benchmark_json(
    report: BenchmarkReport
) -> str:
    """
    Format benchmark report as JSON.

    Args:
        report: Benchmark report to format

    Returns:
        JSON string
    """
    return json.dumps(report.to_dict(), indent=2)


def get_benchmark_summary(
    report: BenchmarkReport
) -> Dict[str, Any]:
    """
    Get summary of benchmark report.

    Args:
        report: Benchmark report

    Returns:
        Summary dictionary
    """
    return {
        "profile_name": report.profile_name,
        "task_alias": report.task_alias,
        "reliability": report.reliability,
        "sample_size": report.sample_size,
        "overall_percentile": (
            report.overall_benchmark.percentile_rank
            if report.overall_benchmark else None
        ),
        "overall_comparison": (
            report.overall_benchmark.comparison.value
            if report.overall_benchmark else None
        ),
        "category_count": {
            "excellent": report.excellent_count,
            "above_average": report.above_average_count,
            "average": report.average_count,
            "below_average": report.below_average_count,
            "poor": report.poor_count,
        },
        "recommendation_count": len(report.recommendations),
        "priority_count": len(report.priority_improvements),
    }
