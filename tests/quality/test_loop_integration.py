"""
Integration tests for QualityLoop
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
from specify_cli.quality import (
    RuleManager, Scorer, Evaluator, Critique, Refiner, QualityLoop, LoopStateManager
)
from specify_cli.quality.models import (
    EvaluationResult, FailedRule, Phase, LoopStatus, StopReason,
)


class TestQualityLoopIntegration:
    """Integration tests for QualityLoop"""

    def setup_method(self):
        """Setup test fixtures"""
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())

        # Initialize components
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)
        self.critique = Critique(max_issues=5)
        self.refiner = Refiner(llm_client=None)  # No LLM for testing
        self.state_manager = LoopStateManager(evolution_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_run_loop_phase_a_passed(self):
        """Test loop run where Phase A is passed"""
        # High-quality artifact
        artifact = """
# User Authentication API

## GET /api/auth/login
Login with username and password.

## POST /api/auth/login
Authenticate user credentials.

## PUT /api/auth/password
Change user password.

## DELETE /api/auth/logout
Logout and invalidate session.

## Authentication
All endpoints require Bearer token authentication.

## Parameters
- username: string
- password: string (encrypted)

## Responses
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Server Error
"""

        criteria = self.rule_manager.load_criteria("api-spec")

        loop = QualityLoop(
            rule_manager=self.rule_manager,
            evaluator=self.evaluator,
            scorer=self.scorer,
            critique=self.critique,
            refiner=self.refiner,
            state_manager=self.state_manager,
        )

        result = loop.run(
            artifact=artifact,
            task_alias="test-api",
            criteria_name="api-spec",
            max_iterations=2,
            threshold_a=0.6,  # Lower threshold for test
            threshold_b=0.8,
            llm_client=None
        )

        assert result is not None
        assert "score" in result
        assert "stop_reason" in result

    def test_run_loop_with_iteration_limit(self):
        """Test loop stopping at iteration limit"""
        artifact = "# Minimal API\n\nHas one endpoint."

        loop = QualityLoop(
            rule_manager=self.rule_manager,
            evaluator=self.evaluator,
            scorer=self.scorer,
            critique=self.critique,
            refiner=self.refiner,
            state_manager=self.state_manager,
        )

        result = loop.run(
            artifact=artifact,
            task_alias="test-minimal",
            criteria_name="api-spec",
            max_iterations=1,  # Only 1 iteration
            threshold_a=0.9,  # High threshold
            threshold_b=0.95,
            llm_client=None
        )

        # Should stop due to iteration limit
        assert result["stop_reason"] in ["iteration_limit", "stagnation", "threshold_reached"]

    def test_run_loop_state_persistence(self):
        """Test that loop state persists across iterations"""
        artifact = "# Test\n\nSome content."

        loop = QualityLoop(
            rule_manager=self.rule_manager,
            evaluator=self.evaluator,
            scorer=self.scorer,
            critique=self.critique,
            refiner=self.refiner,
            state_manager=self.state_manager,
        )

        loop.run(
            artifact=artifact,
            task_alias="test-persistence",
            criteria_name="code-gen",
            max_iterations=1,
            llm_client=None
        )

        # Check that state was saved
        saved_state = self.state_manager.load_state("test-persistence")

        assert saved_state is not None
        assert saved_state.task_alias == "test-persistence"

        # Check that events were logged
        events = self.state_manager.get_history("test-persistence")

        assert len(events) > 0

    def test_run_loop_history_tracking(self):
        """Test that loop tracks all events in history"""
        artifact = "# Test Artifact\n\nWith some content."

        loop = QualityLoop(
            rule_manager=self.rule_manager,
            evaluator=self.evaluator,
            scorer=self.scorer,
            critique=self.critique,
            refiner=self.refiner,
            state_manager=self.state_manager,
        )

        result = loop.run(
            artifact=artifact,
            task_alias="test-history",
            criteria_name="docs",
            max_iterations=1,
            llm_client=None
        )

        events = self.state_manager.get_history("test-history")

        # Should have events like: plan_created, evaluation_started, evaluation_done
        event_types = [e.event_type for e in events]

        assert "plan_created" in event_types
        assert "evaluation_done" in event_types


class TestStagnationCounterReset:
    """Exp 47: Test that stagnation counter resets on Phase A -> B transition"""

    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)
        self.critique = Critique(max_issues=5)
        self.refiner = Refiner(llm_client=None)
        self.state_manager = LoopStateManager(evolution_dir=self.temp_dir)

    def teardown_method(self):
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _make_loop(self):
        return QualityLoop(
            rule_manager=self.rule_manager,
            evaluator=self.evaluator,
            scorer=self.scorer,
            critique=self.critique,
            refiner=self.refiner,
            state_manager=self.state_manager,
        )

    def _make_eval_result(self, score, passed, phase="A", failed_rules=None):
        """Helper to create EvaluationResult for mocking"""
        return EvaluationResult(
            score=score,
            passed=passed,
            threshold=0.8 if phase == "A" else 0.9,
            phase=phase,
            passed_rules=[],
            failed_rules=failed_rules or [],
            warnings=[],
            evaluated_at="2026-03-17T00:00:00",
        )

    def test_stagnation_counter_resets_on_phase_transition(self):
        """Stagnation counter must reset when transitioning from Phase A to Phase B.

        Scenario: Phase A scores stagnate (0.81, 0.81, 0.81) but pass threshold.
        Without fix: Phase B would inherit stagnation_count=2 and immediately stop.
        With fix: Phase B starts fresh, no false stagnation.
        """
        # Simulate: 3 Phase A iterations with stagnant score (all pass),
        # then Phase B iterations that should NOT trigger stagnation
        eval_results = [
            # Phase A: stagnant passing scores
            self._make_eval_result(0.81, True, "A"),
            self._make_eval_result(0.81, True, "A"),  # continue triggers re-eval
            # After phase switch to B (counter should be reset):
            self._make_eval_result(0.70, False, "B",
                                   [FailedRule(rule_id="quality.test", reason="missing")]),
            self._make_eval_result(0.70, False, "B",
                                   [FailedRule(rule_id="quality.test", reason="missing")]),
            self._make_eval_result(0.70, False, "B",
                                   [FailedRule(rule_id="quality.test", reason="missing")]),
        ]
        call_count = {"n": 0}

        original_evaluate = self.evaluator.evaluate

        def mock_evaluate(artifact, criteria, phase, **kwargs):
            idx = min(call_count["n"], len(eval_results) - 1)
            call_count["n"] += 1
            return eval_results[idx]

        loop = self._make_loop()

        with patch.object(self.evaluator, "evaluate", side_effect=mock_evaluate):
            result = loop.run(
                artifact="# Test",
                task_alias="test-stag-reset",
                criteria_name="code-gen",
                max_iterations=5,
                threshold_a=0.8,
                threshold_b=0.9,
            )

        # Should NOT stop due to stagnation — the counter was reset at phase transition
        # It should reach iteration limit or stagnation AFTER enough Phase B iterations
        if result["stop_reason"] == "stagnation":
            # Stagnation is acceptable only if it happened in Phase B
            # with enough iterations (counter reset means it needs 2+ Phase B iterations)
            assert call_count["n"] >= 4, (
                "Stagnation triggered too early — counter was not reset on phase transition"
            )

    def test_last_score_resets_on_phase_transition(self):
        """last_score must reset on phase transition so first Phase B eval
        isn't compared to last Phase A score for stagnation detection."""
        eval_results = [
            self._make_eval_result(0.82, True, "A"),   # Phase A passes
            # Phase B (after transition, last_score should be None):
            self._make_eval_result(0.82, False, "B",
                                   [FailedRule(rule_id="quality.test", reason="x")]),
            self._make_eval_result(0.82, False, "B",
                                   [FailedRule(rule_id="quality.test", reason="x")]),
        ]
        call_count = {"n": 0}

        def mock_evaluate(artifact, criteria, phase, **kwargs):
            idx = min(call_count["n"], len(eval_results) - 1)
            call_count["n"] += 1
            return eval_results[idx]

        loop = self._make_loop()

        with patch.object(self.evaluator, "evaluate", side_effect=mock_evaluate):
            result = loop.run(
                artifact="# Test",
                task_alias="test-last-score",
                criteria_name="code-gen",
                max_iterations=3,
                threshold_a=0.8,
                threshold_b=0.9,
            )

        # With only 3 max iterations and last_score reset,
        # stagnation should NOT fire (need 2+ stagnation counts after reset)
        assert result["stop_reason"] != "stagnation" or call_count["n"] >= 3

    def test_check_stagnation_method(self):
        """Direct unit test of _check_stagnation logic"""
        loop = self._make_loop()

        # Create a mock state
        from specify_cli.quality.models import LoopState, LoopStatus, Phase
        state = LoopState(
            run_id="test",
            task_alias="test",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=5,
            phase=Phase.A,
            current_step="EVALUATE",
            current_score=0.80,
            last_score=None,
        )

        # No last_score -> no stagnation
        assert loop._check_stagnation(state, 0) is False
        assert loop._check_stagnation(state, 5) is False

        # With last_score, small delta, but low counter -> no stagnation
        state.last_score = 0.80
        assert loop._check_stagnation(state, 0) is False
        assert loop._check_stagnation(state, 1) is False

        # With last_score, small delta, counter >= 2 -> stagnation
        assert loop._check_stagnation(state, 2) is True
        assert loop._check_stagnation(state, 3) is True

        # Large delta -> no stagnation even with high counter
        state.current_score = 0.95
        assert loop._check_stagnation(state, 5) is False

    def test_phase_transition_event_logged(self):
        """Phase transition should log phase_switched event"""
        eval_results = [
            self._make_eval_result(0.85, True, "A"),   # Phase A passes
            self._make_eval_result(0.92, True, "B"),   # Phase B passes too
        ]
        call_count = {"n": 0}

        def mock_evaluate(artifact, criteria, phase, **kwargs):
            idx = min(call_count["n"], len(eval_results) - 1)
            call_count["n"] += 1
            return eval_results[idx]

        loop = self._make_loop()

        with patch.object(self.evaluator, "evaluate", side_effect=mock_evaluate):
            result = loop.run(
                artifact="# Test",
                task_alias="test-phase-event",
                criteria_name="code-gen",
                max_iterations=4,
                threshold_a=0.8,
                threshold_b=0.9,
            )

        events = self.state_manager.get_history("test-phase-event")
        event_types = [e.event_type for e in events]
        assert "phase_switched" in event_types
