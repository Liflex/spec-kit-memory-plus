"""
Quality Loop

Main quality loop coordinator that runs iterative quality improvement.
Supports priority-aware scoring with domain multipliers.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from specify_cli.quality.models import (
    LoopState,
    LoopStatus,
    Phase,
    LoopEvent,
    StopReason,
    CriteriaTemplate,
)
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.critique import Critique
from specify_cli.quality.refiner import Refiner
from specify_cli.quality.state import LoopStateManager
from specify_cli.quality.priority_profiles import PriorityProfilesManager
from specify_cli.quality.html_report import generate_html_report
from specify_cli.quality.report_exporter import generate_markdown_report
from specify_cli.quality.json_report import generate_json_report
from specify_cli.quality.gate_policies import evaluate_quality_gate, GatePolicyManager
from specify_cli.quality.gate_policies import recommend_gate_policy, format_recommendation
# Exp 101: Real-time Quality Progress Updates
from specify_cli.quality.live_progress import (
    ProgressState,
    ProgressPhase,
    ProgressCallback,
    LiveProgressContext,
    track_quality_progress,
)
# Exp 102: Final Result Card with Actionable Summary
from specify_cli.quality.result_card import (
    format_result_card,
    print_result_card,
    create_result_card_data,
    ResultCardFormatter,
    ColorTheme,
)
# Exp 104: Multi-Format Report Export Integration
from specify_cli.quality.report_exporter import (
    export_quality_reports,
    ExportConfig,
    ReportFormat,
)
from typing import List, Optional, Set
from pathlib import Path

# Exp 128: Template registry for automatic template selection based on project type
from specify_cli.quality.template_registry import get_registry


class QualityLoop:
    """Main quality loop coordinator with priority-aware scoring"""

    def __init__(
        self,
        rule_manager: RuleManager,
        evaluator: Evaluator,
        scorer: Scorer,
        critique: Critique,
        refiner: Refiner,
        state_manager: LoopStateManager,
    ):
        """Initialize quality loop

        Args:
            rule_manager: Rule manager instance
            evaluator: Evaluator instance
            scorer: Scorer instance
            critique: Critique instance
            refiner: Refiner instance
            state_manager: Loop state manager instance
        """
        self.rule_manager = rule_manager
        self.evaluator = evaluator
        self.scorer = scorer
        self.critique = critique
        self.refiner = refiner
        self.state_manager = state_manager

    def run(
        self,
        artifact: str,
        task_alias: str,
        criteria_name: str,
        max_iterations: int = 4,
        threshold_a: float = 0.8,
        threshold_b: float = 0.9,
        # Exp 128: Project type for automatic template selection
        project_type: Optional[str] = None,
        # Exp 132: Blend preset for automatic template blending
        blend_preset: Optional[str] = None,
        # Exp 133: Auto-detect blend preset from project analysis
        auto_detect: bool = False,
        priority_profile: Optional[str] = None,
        cascade_strategy: Optional[str] = None,
        strict_mode: bool = False,
        lenient_mode: bool = False,
        llm_client=None,
        html_output: Optional[str] = None,
        markdown_output: Optional[str] = None,
        json_output: Optional[str] = None,
        include_categories: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
        # Exp 55: Quality gate policy parameters
        gate_preset: Optional[str] = None,
        gate_policy_name: Optional[str] = None,
        gate_policy_auto: bool = False,
        # Exp 101: Real-time progress updates
        progress_callback: Optional[ProgressCallback] = None,
        show_progress: bool = False,
        progress_animation: str = "spinner",
        progress_compact: bool = False,
        # Exp 102: Final result card display
        show_result_card: bool = False,
        result_card_compact: bool = False,
        result_card_theme: str = "default",
        # Exp 104: Multi-format report export (unified interface)
        export_reports: Optional[List[str]] = None,
        export_dir: Optional[str] = None,
        export_prefix: str = "quality_report",
    ) -> Dict:
        """Run quality loop

        Args:
            artifact: Initial artifact content
            task_alias: Task alias for the loop
            criteria_name: Criteria template name (supports comma-separated: "backend,live-test")
            max_iterations: Maximum iterations
            threshold_a: Phase A threshold
            threshold_b: Phase B threshold
            priority_profile: Optional priority profile name for domain-based weighting
            project_type: Optional project type for automatic template selection (Exp 128).
                          Options: web-app, microservice, ml-service, mobile-app, graphql-api,
                          serverless, desktop, infrastructure. If specified, overrides criteria_name.
            blend_preset: Optional blend preset name for automatic template blending (Exp 132).
                          Options: full_stack_secure, microservices_robust, api_first, mobile_backend,
                          data_pipeline, cloud_native, quality_rigorous, startup_mvp, iot_platform,
                          devsecops. Takes precedence over project_type if both specified.
            auto_detect: If True, automatically detect project type and select appropriate blend preset (Exp 133).
                         Analyzes the codebase to determine the best blend preset. Takes precedence over
                         criteria_name, but is overridden by blend_preset or project_type if specified.
                         Recommended for zero-config experience on new projects.
            cascade_strategy: Optional cascade merge strategy (avg/max/min/wgt/weighted)
            strict_mode: If True, use strict mode (web-app+mobile-app with max strategy)
            lenient_mode: If True, use lenient mode (default profile with min strategy)
            llm_client: Optional LLM client for refinements
            html_output: Optional path to save HTML report (e.g., "quality-report.html")
            markdown_output: Optional path to save Markdown report (e.g., "quality-report.md")
            json_output: Optional path to save JSON report with category breakdown (e.g., "quality-report.json")
            include_categories: Only include these categories in JSON report (e.g., ["security", "performance"])
            exclude_categories: Exclude these categories from JSON report (e.g., ["docs"])
            gate_preset: Optional quality gate preset name (production, staging, development, ci, strict, lenient) or custom policy name from .speckit/gate-policies.yml
            gate_policy_name: Optional custom gate policy name from project config (alias for gate_preset)
            gate_policy_auto: If True, automatically recommend and apply gate policy based on CI environment, branch, project type (Exp 60)
            progress_callback: Optional callback function for real-time progress updates (Exp 101)
            show_progress: If True, show animated progress bar during quality loop (Exp 101)
            progress_animation: Animation style for progress display (spinner, dots, bar, pulse, none) (Exp 101)
            progress_compact: If True, use compact single-line progress display (Exp 101)
            show_result_card: If True, display final result card after quality loop completes (Exp 102)
            result_card_compact: If True, use compact single-line result card format (Exp 102)
            result_card_theme: Color theme for result card (default, dark, high-contrast, minimal) (Exp 102)
            export_reports: List of report formats to export (Exp 104). Options: "console", "json", "html", "markdown", "csv"
                          If specified, overrides html_output, markdown_output, json_output parameters
            export_dir: Directory to save exported reports (Exp 104)
            export_prefix: Filename prefix for exported reports (Exp 104)

        Returns:
            Final result with score, status, changes, and gate evaluation

        Note on project_type (Exp 128):
            If project_type is specified (e.g., "web-app", "microservice", "ml-service"),
            it will automatically select the best template combination for that project type.
            This takes precedence over criteria_name if both are provided.
            Available project types: web-app, microservice, ml-service, mobile-app,
            graphql-api, serverless, desktop, infrastructure.

        Note on blend_preset (Exp 132):
            If blend_preset is specified (e.g., "full_stack_secure", "microservices_robust"),
            it will automatically apply a pre-configured blend of templates optimized for
            specific use cases. This takes precedence over both project_type and criteria_name.
            Available presets: full_stack_secure, microservices_robust, api_first, mobile_backend,
            data_pipeline, cloud_native, quality_rigorous, startup_mvp, iot_platform, devsecops.

        Note on auto_detect (Exp 133):
            If auto_detect is True, the system will analyze the project codebase and automatically
            select the most appropriate blend preset. This provides a zero-config experience for
            typical projects. Precedence order: blend_preset > project_type > auto_detect > criteria_name.
        """
        # Get project root for custom profiles
        project_root = str(Path.cwd())

        # Exp 132: Apply blend preset if specified (takes precedence over project_type)
        if blend_preset:
            registry = get_registry()
            preset = registry.get_blend_preset(blend_preset)
            if preset:
                # Apply blend preset to create merged criteria
                resolved_templates = ",".join(preset.templates)
                criteria_name = resolved_templates
            else:
                # Blend preset not found - fall back to criteria_name
                pass

        # Exp 128: Auto-select templates based on project type (only if blend_preset not used)
        elif project_type:
            registry = get_registry()
            # First, try to get a blend preset recommendation for this project type
            blend_preset = registry.recommend_blend_preset(project_type)
            if blend_preset:
                # Use blend preset if available
                resolved_templates = ",".join(blend_preset.templates)
                criteria_name = resolved_templates
            else:
                # Fall back to regular template recommendations
                recommendations = registry.get_recommendations(project_type)
                if recommendations:
                    # Use the best matching recommendation (first one)
                    best_match = recommendations[0]
                    resolved_templates = ",".join(best_match.templates)

                    # If criteria_name is provided, project_type overrides it
                    if criteria_name and criteria_name != "default":
                        # User specified both - use resolved templates but log the override
                        criteria_name = resolved_templates
                    else:
                        # Use project_type-based templates
                        criteria_name = resolved_templates
                else:
                    # No recommendations found for this project type
                    # Fall back to criteria_name if provided, otherwise use default
                    if not criteria_name or criteria_name == "default":
                        criteria_name = "backend"  # Sensible default

        # Exp 133: Auto-detect blend preset if requested (only if blend_preset and project_type not used)
        elif auto_detect:
            registry = get_registry()
            detected_preset = registry.auto_detect_blend_preset(project_root=Path(project_root))
            if detected_preset:
                # Use detected preset
                resolved_templates = ",".join(detected_preset.templates)
                criteria_name = resolved_templates
            # If detection fails, fall back to original criteria_name

        # Load criteria (supports comma-separated merge)
        if "," in criteria_name:
            criteria = self.rule_manager.load_merged_criteria(criteria_name)
        else:
            criteria = self.rule_manager.load_criteria(criteria_name)

        # Update thresholds if custom
        if threshold_a != 0.8:
            criteria.phases["a"].threshold = threshold_a
        if threshold_b != 0.9:
            criteria.phases["b"].threshold = threshold_b

        # Handle shortcuts: strict_mode and lenient_mode override priority_profile and cascade_strategy
        # These shortcuts provide convenient presets for common quality scenarios
        if strict_mode:
            # Strict mode: most demanding quality checks for fullstack apps
            # Uses cascade profile web-app+mobile-app with max strategy (highest multipliers per domain)
            if priority_profile is None:
                priority_profile = "web-app+mobile-app"
            if cascade_strategy is None:
                cascade_strategy = "max"
        elif lenient_mode:
            # Lenient mode: relaxed requirements for faster iteration
            # Uses default profile (all 1.0x multipliers) with min strategy (lowest multipliers)
            if priority_profile is None:
                priority_profile = "default"
            if cascade_strategy is None:
                cascade_strategy = "min"

        # Validate priority profile if specified
        if priority_profile:
            # Handle "auto" - detect from project files
            if priority_profile == "auto":
                detected_profile = PriorityProfilesManager.detect_profile(Path(project_root))
                priority_profile = detected_profile
            else:
                # Check for cascade profile syntax (e.g., "web-app+mobile-app")
                is_cascade, profile_names, cascade_error = PriorityProfilesManager.parse_cascade_profile(priority_profile)

                if cascade_error:
                    # Invalid cascade syntax - fall back to default
                    priority_profile = "default"
                elif not is_cascade:
                    # Single profile - validate it exists
                    available_profiles = criteria.list_priority_profiles(project_root)
                    if priority_profile not in available_profiles and priority_profile != "default":
                        # Fall back to default if specified profile not found
                        priority_profile = "default"
                # else: cascade profile - validation will happen in evaluator

        # Set refiner LLM client
        self.refiner.llm_client = llm_client

        # Exp 101: Setup progress tracking
        progress_context = None
        if show_progress:
            progress_context = track_quality_progress(
                enabled=True,
                animation=progress_animation,
                compact=progress_compact,
            )
            progress_context.__enter__()

        def _update_progress(phase: ProgressPhase, message: str = "", **kwargs):
            """Helper to update progress display"""
            if progress_callback:
                state = ProgressState(
                    phase=phase,
                    iteration=state.iteration,
                    max_iterations=state.max_iterations,
                    current_phase_letter=state.phase.value if hasattr(state, 'phase') else "A",
                    score=state.current_score,
                    message=message,
                    details=kwargs,
                )
                progress_callback(state)
            if progress_context:
                progress_context.update(phase=phase, message=message, **kwargs)

        # Initialize state
        run_id = f"{task_alias}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        state = LoopState(
            run_id=run_id,
            task_alias=task_alias,
            status=LoopStatus.running,
            iteration=1,
            max_iterations=max_iterations,
            phase=Phase.A,
            current_step="PLAN",
            started_at=datetime.now().isoformat(),
            priority_profile=priority_profile,
        )
        self.state_manager.save_state(state)
        self.state_manager.save_artifact(artifact, task_alias)

        # Log plan created event
        self._log_event(
            task_alias=task_alias,
            event_type="plan_created",
            iteration=1,
            phase="A",
            details={
                "criteria": criteria_name,
                "max_iterations": max_iterations,
                "priority_profile": priority_profile,
            }
        )

        # Run iterations
        stagnation_count = 0
        while state.iteration <= state.max_iterations:
            # EVALUATE
            state.current_step = "EVALUATE"
            self._log_event(
                task_alias=task_alias,
                event_type="evaluation_started",
                iteration=state.iteration,
                phase=state.phase.value,
            )

            # Exp 101: Update progress for evaluation
            _update_progress(
                ProgressPhase.EVALUATE,
                f"Evaluating iteration {state.iteration} Phase {state.phase.value}",
                iteration=state.iteration,
            )

            result = self.evaluator.evaluate(
                artifact,
                criteria,
                state.phase.value,
                priority_profile=priority_profile,
                cascade_strategy=cascade_strategy,
                project_root=project_root,
            )
            state.evaluation = result
            state.current_score = result.score

            self._log_event(
                task_alias=task_alias,
                event_type="evaluation_done",
                iteration=state.iteration,
                phase=state.phase.value,
                details={
                    "score": result.score,
                    "passed": result.passed,
                    "priority_profile": priority_profile,
                }
            )

            # Exp 101: Update progress with score
            _update_progress(
                ProgressPhase.EVALUATE,
                f"Score: {result.score:.2f} ({'PASS' if result.passed else 'FAIL'})",
                score=result.score,
                failed_rules_count=len(result.failed_rules) if hasattr(result, 'failed_rules') else 0,
            )

            # Check if passed Phase B
            if result.passed and state.phase == Phase.B:
                state.status = LoopStatus.completed
                state.stop = {"passed": True, "reason": StopReason.threshold_reached.value}
                self.state_manager.save_state(state)
                break

            # Check stagnation
            if self._check_stagnation(state, stagnation_count):
                state.status = LoopStatus.stopped
                state.stop = {"passed": False, "reason": StopReason.stagnation.value}
                self.state_manager.save_state(state)
                break

            # Switch to Phase B if Phase A passed
            if result.passed and state.phase == Phase.A:
                state.phase = Phase.B
                self.state_manager.save_state(state)

                # Exp 101: Update progress for phase transition
                _update_progress(
                    ProgressPhase.EVALUATE,
                    "Phase A complete! Switching to Phase B...",
                )

                self._log_event(
                    task_alias=task_alias,
                    event_type="phase_switched",
                    iteration=state.iteration,
                    phase="A",
                    details={"new_phase": "B"}
                )
                continue  # Re-evaluate with Phase B rules

            # CRITIQUE + REFINE (only if failed)
            if not result.passed:
                state.current_step = "CRITIQUE"

                # Exp 101: Update progress for critique
                _update_progress(
                    ProgressPhase.CRITIQUE,
                    f"Analyzing {len(result.failed_rules)} failed rules",
                )

                failed_rules_list = [fr.to_dict() for fr in result.failed_rules]
                critique_result = self.critique.generate(failed_rules_list, artifact)
                state.critique = critique_result

                self._log_event(
                    task_alias=task_alias,
                    event_type="critique_done",
                    iteration=state.iteration,
                    phase=state.phase.value,
                    details={"issues": critique_result["addressed"]}
                )

                state.current_step = "REFINE"

                # Exp 101: Update progress for refinement
                _update_progress(
                    ProgressPhase.REFINE,
                    f"Refining artifact ({critique_result.get('addressed', 0)} issues to fix)",
                )

                artifact = self.refiner.apply(artifact, critique_result)
                self.state_manager.save_artifact(artifact, task_alias)

                self._log_event(
                    task_alias=task_alias,
                    event_type="refinement_done",
                    iteration=state.iteration,
                    phase=state.phase.value,
                )

            # Update stagnation counter
            if state.last_score is not None:
                delta = abs(state.current_score - state.last_score)
                if delta < 0.02:
                    stagnation_count += 1
                else:
                    stagnation_count = 0

            # Next iteration
            state.iteration += 1
            state.last_score = state.current_score
            state.current_step = "PLAN"
            self.state_manager.save_state(state)

        # Check iteration limit
        if state.iteration > state.max_iterations and state.status != LoopStatus.completed:
            state.status = LoopStatus.stopped
            state.stop = {"passed": False, "reason": StopReason.iteration_limit.value}
            self.state_manager.save_state(state)

        # Clear active loop
        self.state_manager.clear_active_loop()

        # Exp 101: Final progress update
        if progress_context:
            final_message = "Quality check complete!" if state.status == LoopStatus.completed else "Quality check stopped"
            progress_context.update(
                phase=ProgressPhase.COMPLETE,
                message=final_message,
                score=state.current_score,
            )

        result = {
            "state": state.to_dict(),
            "artifact": artifact,
            "score": state.current_score,
            "passed": state.stop.get("passed", False) if state.stop else False,
            "stop_reason": state.stop.get("reason", "") if state.stop else "",
            "priority_profile": priority_profile,
            # Exp 105: Additional metadata for enhanced CSV export (trend analysis, BI integration)
            "run_id": state.run_id,
            "timestamp": state.started_at,
            "criteria": criteria_name,
            "iterations": state.iteration - 1,  # Actual iterations used
            "max_iterations": state.max_iterations,
        }

        # Exp 55: Evaluate quality gate if specified
        # Exp 56: Support custom gate policies from project config
        # Exp 60: Auto-recommend gate policy if requested
        if gate_policy_auto and not (gate_preset or gate_policy_name):
            # Auto-recommend gate policy based on context
            # Get failed categories for recommendation
            failed_categories = []
            if result.get("state", {}).get("evaluation", {}).get("failed_rules"):
                failed_categories = list(set(
                    r.get("category", "general")
                    for r in result["state"]["evaluation"]["failed_rules"]
                ))

            # Get recommendation
            recommendation = recommend_gate_policy(
                project_root=Path(project_root),
                current_score=state.current_score,
                failed_categories=failed_categories,
            )

            # Use recommended policy
            policy_name = recommendation.policy_name
            gate_result = evaluate_quality_gate(
                evaluation_result=result,
                gate_preset=policy_name,
                project_root=project_root,
            )
            gate_result["recommendation"] = recommendation.to_dict()
            result["gate_result"] = gate_result
        elif gate_preset or gate_policy_name:
            # Use gate_policy_name if provided, otherwise use gate_preset
            policy_name = gate_policy_name or gate_preset
            gate_result = evaluate_quality_gate(
                evaluation_result=result,
                gate_preset=policy_name,
                project_root=project_root,
            )
            result["gate_result"] = gate_result

        # Exp 104: Multi-format report export (unified interface)
        # If export_reports is specified, use unified ReportExporter
        if export_reports is not None:
            try:
                # Normalize formats: handle comma-separated string and convert to set
                if isinstance(export_reports, str):
                    export_reports = [f.strip() for f in export_reports.split(",")]
                export_formats: Set[ReportFormat] = set(export_reports) & {"console", "json", "html", "markdown", "csv"}

                # Use export_dir if specified, otherwise use legacy parameters for backward compatibility
                output_directory = export_dir
                if not output_directory:
                    # Extract directory from legacy parameters for backward compatibility
                    if html_output:
                        output_directory = str(Path(html_output).parent)
                    elif markdown_output:
                        output_directory = str(Path(markdown_output).parent)
                    elif json_output:
                        output_directory = str(Path(json_output).parent)

                # Export reports using unified interface
                export_result = export_quality_reports(
                    result=result,
                    previous_score=None,  # Could be fetched from history
                    formats=list(export_formats) if export_formats else None,
                    output_dir=output_directory,
                    filename_prefix=export_prefix,
                    include_timeline=True,
                    include_details=True,
                    compact_console=result_card_compact,
                    console_theme=result_card_theme,
                    json_pretty=True,
                )

                # Add export results to output
                result["export_result"] = {
                    "formats_generated": list(export_result.reports.keys()),
                    "output_dir": output_directory,
                    "total_size_bytes": export_result.total_size_bytes,
                }

                # Add individual file paths for backward compatibility
                if "json" in export_result.reports and export_result.reports["json"].path:
                    result["json_report_path"] = export_result.reports["json"].path
                if "html" in export_result.reports and export_result.reports["html"].path:
                    result["html_report_path"] = export_result.reports["html"].path
                if "markdown" in export_result.reports and export_result.reports["markdown"].path:
                    result["markdown_report_path"] = export_result.reports["markdown"].path
                if "csv" in export_result.reports and export_result.reports["csv"].path:
                    result["csv_report_path"] = export_result.reports["csv"].path

                # Store console output for later display
                if "console" in export_result.reports:
                    result["console_output"] = export_result.get_console_output()

            except Exception as e:
                # Export failure should not break the loop
                result["export_error"] = str(e)
        else:
            # Legacy mode: use individual report generators for backward compatibility
            # Generate HTML report if requested
            if html_output:
                try:
                    generate_html_report(result, output_path=html_output)
                    result["html_report_path"] = html_output
                except Exception as e:
                    # HTML generation failure should not break the loop
                    result["html_report_error"] = str(e)

            # Generate Markdown report if requested
            if markdown_output:
                try:
                    generate_markdown_report(result, output_path=markdown_output)
                    result["markdown_report_path"] = markdown_output
                except Exception as e:
                    # Markdown generation failure should not break the loop
                    result["markdown_report_error"] = str(e)

            # Generate JSON report if requested (Exp 51: JSON Export for CI/CD, Exp 52: Schema validation and category filtering)
            if json_output:
                try:
                    generate_json_report(
                        result,
                        output_path=json_output,
                        pretty=True,
                        validate=True,
                        include_categories=include_categories,
                        exclude_categories=exclude_categories,
                    )
                    result["json_report_path"] = json_output
                except Exception as e:
                    # JSON generation failure should not break the loop
                    result["json_report_error"] = str(e)

        # Exp 101: Close progress context
        if progress_context:
            progress_context.__exit__(None, None, None)

        # Exp 102: Display final result card if requested
        if show_result_card:
            try:
                # Display result card
                print_result_card(
                    result=result,
                    previous_score=None,
                    compact=result_card_compact,
                    theme=result_card_theme,
                )
            except Exception as e:
                # Result card display failure should not break the loop
                result["result_card_error"] = str(e)

        return result

    def _check_stagnation(self, state: LoopState, stagnation_count: int) -> bool:
        """Check if score is stagnating

        Args:
            state: Current loop state
            stagnation_count: Current stagnation iteration count

        Returns:
            True if stagnating (2+ iterations with <0.02 improvement)
        """
        if state.last_score is None:
            return False

        delta = abs(state.current_score - state.last_score)

        # Stagnate if delta < 0.02 for 2+ iterations
        if delta < 0.02 and stagnation_count >= 2:
            return True

        return False

    def _log_event(
        self,
        task_alias: str,
        event_type: str,
        iteration: Optional[int] = None,
        phase: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log event to history

        Args:
            task_alias: Task alias
            event_type: Event type
            iteration: Iteration number
            phase: Phase
            details: Additional details
        """
        event = LoopEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            iteration=iteration,
            phase=phase,
            details=details,
        )
        self.state_manager.append_event(event, task_alias)
