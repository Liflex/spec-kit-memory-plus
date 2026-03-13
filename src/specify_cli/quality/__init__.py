"""
Spec Kit Quality Module

Provides quality evaluation, scoring, and refinement capabilities.
"""

# === Core Engine ===
from specify_cli.quality.models import (
    CriteriaTemplate,
    QualityRule,
    EvaluationResult,
    LoopState,
    PriorityProfile,
    RuleSeverity,
    Phase,
)
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.critique import Critique
from specify_cli.quality.refiner import Refiner
from specify_cli.quality.state import LoopStateManager
from specify_cli.quality.loop import QualityLoop

# === Reports ===
from specify_cli.quality.html_report import HTMLReportGenerator, generate_html_report
from specify_cli.quality.report_exporter import MarkdownReportGenerator, generate_markdown_report
from specify_cli.quality.json_report import (
    JSONReportGenerator,
    generate_json_report,
    get_schema,
    validate_schema,
    get_schema_json,
    export_schema,
    get_schema_info,
    print_schema_info,
    calculate_distribution_stats,
    get_severity_distribution,
)
from specify_cli.quality.report_exporter import (
    ReportFormat,
    ALL_FORMATS,
    ExportConfig,
    ExportedReport,
    ExportResult,
    ReportExporter,
    export_quality_reports,
    export_result_card_json,
    format_export_summary,
)
from specify_cli.quality.result_card import (
    ResultStatus,
    CategorySummary,
    ActionItem,
    ResultCardData,
    ResultCardFormatter,
    create_result_card_data,
    format_result_card,
    print_result_card,
)

# === Gates ===
from specify_cli.quality.gate_policies import (
    GatePolicy,
    GateResult,
    SeverityGate,
    CategoryGate,
    GatePolicyManager,
    GATE_PRESETS,
    evaluate_quality_gate,
    ValidationError,
    ValidationIssue,
)
from specify_cli.quality.gate_policies import (
    GatePolicyRecommender,
    PolicyRecommendation,
    recommend_gate_policy,
    format_recommendation,
    format_recommendation_json,
)
from specify_cli.quality.gate_policies import (
    GatePolicyCascade,
    CascadeGatePolicy,
    CascadeStrategy,
    CascadeValidationError,
    CascadeValidationIssue,
    cascade_gate_policies,
    format_cascade_policy,
    format_cascade_policy_json,
)
from specify_cli.quality.goal_gates import (
    GoalGateMode,
    GoalGateConfig,
    GoalGateResult,
    GoalGatePolicy,
    GoalAwareGatePolicy,
    GOAL_GATE_PRESETS,
    create_goal_gate,
    evaluate_goal_gate,
    format_goal_gate_result,
    format_goal_gate_result_json,
    list_goal_gate_presets,
    get_goal_gate_preset_info,
    recommend_goal_gate,
    create_aware_gate,
)

# === History & Analytics ===
from specify_cli.quality.quality_history import (
    QualityRunRecord,
    QualityStatistics,
    QualityTrend,
    RunComparison,
    QualityHistoryManager,
    save_quality_run,
    get_quality_statistics,
    get_quality_trends,
    format_statistics_report,
    format_trends_report,
    format_history_json,
)
from specify_cli.quality.quality_anomaly import (
    QualityAnomalyDetector,
    QualityAnomaly,
    AnomalyReport,
    AnomalySeverity,
    AnomalyType,
    AnomalyDetectionConfig,
    detect_anomalies,
    format_anomaly_report,
    format_anomalies_json,
    get_anomaly_summary,
    list_anomaly_types,
    format_config,
    get_anomaly_recommendations,
    get_anomaly_statistics,
    filter_anomalies,
    export_anomalies_csv,
    AnomalyRiskScore,
    AnomalyRiskScorer,
    enrich_anomalies_with_risk,
    format_risk_scores_text,
    export_risk_scores_csv,
)
from specify_cli.quality.quality_benchmarking import (
    BenchmarkType,
    BenchmarkComparison,
    PercentileMetrics,
    BenchmarkResult,
    CategoryBenchmark,
    BenchmarkProfile,
    BenchmarkReport,
    QualityBenchmarkingEngine,
    create_benchmark,
    compare_quality,
    generate_benchmark_report,
    format_benchmark_report,
    format_benchmark_json,
    get_benchmark_summary,
)

# === Goals ===
from specify_cli.quality.quality_goals import (
    GoalStatus,
    GoalType,
    QualityGoal,
    GoalProgress,
    GoalSummary,
    QualityGoalsManager,
    create_target_score_goal,
    create_pass_rate_goal,
    create_category_goal,
    create_streak_goal,
    create_improvement_goal,
    create_stability_goal,
    format_goal_progress,
    format_goals_summary,
    GoalPreset,
    GOAL_PRESETS,
    apply_preset,
    list_presets,
    get_preset_info,
    recommend_preset,
    export_goals,
    import_goals,
    export_goals_as_dict,
    export_progress_as_dict,
    CATEGORY_GOAL_TEMPLATES,
    apply_category_template,
    list_category_templates,
    get_category_template_info,
    recommend_category_template,
)
from specify_cli.quality.goal_suggester import (
    GoalSuggester,
    GoalSuggestion,
    SuggestionReason,
    SuggestionConfidence,
    SuggestionReport,
    suggest_goals,
    format_suggestions_report,
    format_suggestions_json,
    get_suggestions_summary,
)
from specify_cli.quality.quality_insights import (
    QualityInsightsEngine,
    QualityInsight,
    InsightType,
    InsightPriority,
    PatternInsight,
    TrendInsight,
    OptimizationInsight,
    InsightsReport,
    InsightsConfig,
    generate_insights,
    format_insights_report,
    format_insights_json,
    get_insights_summary,
    export_action_items,
)

# === Configuration ===
from specify_cli.quality.loop_config import (
    LoopConfig,
    LoopConfigManager,
    LOOP_CONFIG_PRESETS,
    save_loop_config,
    load_loop_config,
    list_loop_configs,
    delete_loop_config,
    format_config_summary,
    format_config_details,
    recommend_config,
    resolve_criteria_from_config,
    get_available_project_types,
)
from specify_cli.quality.quality_plans import (
    QualityPlan,
    PlanType,
    PlanCategory,
    QualityPlanManager,
    QualityPlanWizard,
    get_builtin_plans,
    list_available_plans,
    recommend_quality_plan,
    get_plan_details,
    create_plan_interactive,
    create_plan_from_quick_setup,
)

# === Priority Profiles ===
from specify_cli.quality.priority_profiles import (
    PriorityProfilesManager,
    print_profile_summary,
    print_all_profiles,
    print_custom_profiles_info,
    BUILTIN_PRIORITY_PROFILES,
    DOMAIN_TAGS,
    CATEGORY_TAGS,
    CUSTOM_PROFILES_PATH,
    interactive_profile_wizard,
    print_profile_analysis,
    print_strategy_comparison,
    print_strategy_comparison_json,
    print_all_profiles_json,
    print_profile_summary_json,
    print_domain_tags_json,
    print_profile_comparison_json,
    print_profile_diff_json,
    print_cascade_profile_info_json,
    print_profile_recommendation_json,
    print_cascade_recommendation_json,
    print_custom_profiles_json,
)
from specify_cli.quality import autodetect
from specify_cli.quality.autodetect import (
    ProfileDetector,
    detect_priority_profile,
    get_detection_details,
    print_detection_details,
    print_detection_details_json,
)

# === Feedback ===
from specify_cli.quality.feedback_loop import (
    TrendDirection as FeedbackTrendDirection,
    AdjustmentType,
    InsightPriority as FeedbackInsightPriority,
    QualityResult,
    TrendAnalysis,
    ConfigurationAdjustment,
    FeedbackReport,
    FeedbackAnalyzer,
    create_quality_result,
    analyze_feedback,
    get_improvement_suggestions,
    export_feedback_report,
)

# === Display ===
from specify_cli.quality.live_progress import (
    ProgressPhase,
    AnimationStyle,
    ProgressState,
    ProgressConfig,
    ProgressTracker,
    LiveProgressContext,
    track_quality_progress,
    create_progress_config,
    ProgressCallback,
    create_progress_callback,
)
from specify_cli.quality.terminal_colors import (
    ColorScheme,
    ANSI,
    ColorTheme,
    TerminalInfo,
    detect_terminal_capabilities,
    get_terminal_info,
    reset_terminal_cache,
)

# === QA Dashboard ===
from specify_cli.quality.qa_dashboard import (
    TrendDirection,
    QualityOverview,
    QualityCheckResult,
    RunComparison,
    QualityTrend,
    BenchmarkAwareQualityOverview,
    get_quality_overview,
    run_quality_check,
    compare_quality_runs,
    get_quality_trends,
    format_overview_report,
    format_check_result,
    format_comparison_report,
    format_trends_report,
    format_overview_json,
    format_check_json,
    get_benchmark_aware_overview,
    format_benchmark_aware_overview_report,
)

# === Templates ===
from specify_cli.quality.template_registry import (
    TemplateCategory,
    TemplateMetadata,
    TemplateCombination,
    BlendPreset,
    BlendedTemplate,
    TemplateRegistry,
    get_registry,
    print_template_table,
    print_combination_table,
    compare_templates,
    format_template_diff,
    blend_templates,
    save_blended_template,
    format_blended_template,
)
from specify_cli.quality.templates_cli import (
    templates_app,
    list_templates_command,
    template_info_command,
    search_templates_command,
    recommend_templates_command,
    template_stats_command,
)
from specify_cli.quality.template_registry import (
    TemplateIntegration,
    get_recommended_templates,
    validate_templates,
    expand_templates,
)

# === Profile helpers ===
_profile_manager = PriorityProfilesManager
get_profile_json = _profile_manager.get_profile_json
get_all_profiles_json = _profile_manager.get_all_profiles_json
diff_profiles = _profile_manager.diff_profiles
print_profile_diff = _profile_manager.print_profile_diff
merge_profiles = _profile_manager.merge_profiles
print_cascade_profile_info = _profile_manager.print_cascade_profile_info
list_available_cascades = _profile_manager.list_available_cascades
print_profile_wizard = interactive_profile_wizard
analyze_profile_rules = _profile_manager.analyze_profile_rules

__version__ = "0.90.0"
