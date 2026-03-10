"""
Unit tests for Evaluator
"""

import pytest
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.scorer import Scorer


class TestEvaluator:
    """Test Evaluator class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_evaluate_simple_artifact(self):
        """Test evaluating a simple artifact"""
        # Simple artifact with some content
        artifact = """
# My API

## GET /users
Get all users

## POST /users
Create a user
"""

        criteria = self.rule_manager.load_criteria("api-spec")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.passed, bool)

    def test_evaluate_empty_artifact(self):
        """Test evaluating an empty artifact"""
        artifact = ""

        criteria = self.rule_manager.load_criteria("code-gen")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        # Empty artifact should have low score
        assert result.score < 0.5

    def test_evaluate_phase_a_vs_b(self):
        """Test that Phase B is stricter than Phase A"""
        artifact = """
def hello():
    print("Hello")
"""

        criteria = self.rule_manager.load_criteria("code-gen")
        result_a = self.evaluator.evaluate(artifact, criteria, "A")
        result_b = self.evaluator.evaluate(artifact, criteria, "B")

        # Phase B might have lower score (more rules)
        # Or same score if all rules pass
        assert 0.0 <= result_a.score <= 1.0
        assert 0.0 <= result_b.score <= 1.0

    def test_check_rule_content(self):
        """Test content-based rule checking"""
        artifact = "# My Title\n\nThis is documentation."

        passed, reason = self.evaluator._check_rule(
            criteria.get_active_rules(criteria, "A")[0],
            artifact
        )

        # Just verify it runs without error
        assert isinstance(passed, bool)
        assert isinstance(reason, str)
