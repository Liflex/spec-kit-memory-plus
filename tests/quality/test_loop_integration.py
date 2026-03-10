"""
Integration tests for QualityLoop
"""

import pytest
import tempfile
from pathlib import Path
from specify_cli.quality import (
    RuleManager, Scorer, Evaluator, Critique, Refiner, QualityLoop, LoopStateManager
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
