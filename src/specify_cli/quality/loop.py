"""
Quality Loop

Main quality loop coordinator that runs iterative quality improvement.
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


class QualityLoop:
    """Main quality loop coordinator"""

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
        llm_client=None
    ) -> Dict:
        """Run quality loop

        Args:
            artifact: Initial artifact content
            task_alias: Task alias for the loop
            criteria_name: Criteria template name (supports comma-separated: "backend,live-test")
            max_iterations: Maximum iterations
            threshold_a: Phase A threshold
            threshold_b: Phase B threshold
            llm_client: Optional LLM client for refinements

        Returns:
            Final result with score, status, changes
        """
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

        # Set refiner LLM client
        self.refiner.llm_client = llm_client

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
        )
        self.state_manager.save_state(state)
        self.state_manager.save_artifact(artifact, task_alias)

        # Log plan created event
        self._log_event(
            task_alias=task_alias,
            event_type="plan_created",
            iteration=1,
            phase="A",
            details={"criteria": criteria_name, "max_iterations": max_iterations}
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

            result = self.evaluator.evaluate(artifact, criteria, state.phase.value)
            state.evaluation = result
            state.current_score = result.score

            self._log_event(
                task_alias=task_alias,
                event_type="evaluation_done",
                iteration=state.iteration,
                phase=state.phase.value,
                details={"score": result.score, "passed": result.passed}
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

        return {
            "state": state.to_dict(),
            "artifact": artifact,
            "score": state.current_score,
            "passed": state.stop.get("passed", False) if state.stop else False,
            "stop_reason": state.stop.get("reason", "") if state.stop else "",
        }

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
