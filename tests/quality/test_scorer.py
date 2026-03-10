"""
Unit tests for Scorer
"""

import pytest
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.models import QualityRule, RuleSeverity, Phase, FailedRule


class TestScorer:
    """Test Scorer class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = Scorer()

        # Create test rules
        self.rule1 = QualityRule(
            id="test.rule1",
            description="Test rule 1",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="check something",
        )

        self.rule2 = QualityRule(
            id="test.rule2",
            description="Test rule 2",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.A,
            check="check something else",
        )

        self.rule3 = QualityRule(
            id="test.rule3",
            description="Test rule 3",
            severity=RuleSeverity.info,
            weight=0,
            phase=Phase.A,
            check="check another thing",
        )

    def test_calculate_score_all_passed(self):
        """Test score calculation when all rules pass"""
        all_rules = [self.rule1, self.rule2, self.rule3]
        passed_rules = all_rules

        score = self.scorer.calculate_score(passed_rules, all_rules)

        assert score == 1.0

    def test_calculate_score_partial(self):
        """Test score calculation with partial passes"""
        all_rules = [self.rule1, self.rule2, self.rule3]
        passed_rules = [self.rule1]  # Only rule1 (weight=2) passed

        score = self.scorer.calculate_score(passed_rules, all_rules)

        # score = 2 / (2 + 1 + 0) = 2/3 ≈ 0.67
        assert abs(score - 0.67) < 0.01

    def test_calculate_score_no_rules(self):
        """Test score calculation with no rules"""
        score = self.scorer.calculate_score([], [])

        assert score == 1.0  # No rules means perfect score

    def test_check_passed_with_threshold(self):
        """Test pass check with threshold"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = [self.rule1]
        failed_rules = []

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # score = 2/3 = 0.67 < 0.8, should fail
        assert not passed

    def test_check_passed_with_fail_severity(self):
        """Test pass check with fail-severity failures"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules
        failed_rules = [
            FailedRule(rule_id="test.rule1", reason="Failed")
        ]

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # High score but has fail-severity failure
        assert not passed

    def test_check_passed_no_fail_severity(self):
        """Test pass check without fail-severity failures"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules
        failed_rules = []  # No failures

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # High score, no failures
        assert passed

    def test_calculate_distance_to_success_passed(self):
        """Test distance calculation when already passed"""
        distance = self.scorer.calculate_distance_to_success(0.9, 0.8)

        assert distance == 0.0  # Already passed

    def test_calculate_distance_to_success_failed(self):
        """Test distance calculation when not passed"""
        distance = self.scorer.calculate_distance_to_success(0.7, 0.9)

        assert abs(distance - 0.2) < 0.01
