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
