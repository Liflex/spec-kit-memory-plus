"""
Unit tests for Scorer (Exp 139: Extended coverage)
"""

import pytest
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.models import QualityRule, RuleSeverity, Phase, FailedRule, PriorityProfile, CriteriaTemplate, PhaseConfig


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

    def test_check_passed_with_blocking_failure(self):
        """Test pass check with blocking failure (weight >= 2)"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules
        failed_rules = [
            FailedRule(rule_id="security.rule1", reason="Failed", weight=2)
        ]

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # High score but has blocking failure (weight=2)
        assert not passed

    def test_check_passed_no_failures(self):
        """Test pass check without any failures"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules
        failed_rules = []  # No failures

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # High score, no failures
        assert passed

    def test_check_passed_non_blocking_failure(self):
        """Test pass check with non-blocking failure (weight < 2)"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules
        failed_rules = [
            FailedRule(rule_id="quality.readability", reason="Low readability", weight=1)
        ]

        score = self.scorer.calculate_score(passed_rules, all_rules)
        passed = self.scorer.check_passed(score, 0.8, failed_rules)

        # High score, only non-blocking failure (weight=1) — should pass
        assert passed

    def test_check_passed_mixed_weights(self):
        """Test pass check with mixed blocking and non-blocking failures"""
        failed_rules = [
            FailedRule(rule_id="quality.readability", reason="Low readability", weight=1),
            FailedRule(rule_id="security.auth", reason="No auth", weight=2),
        ]

        passed = self.scorer.check_passed(0.9, 0.8, failed_rules)

        # Has at least one blocking failure (weight=2) — should not pass
        assert not passed

    def test_check_passed_weight_zero_not_blocking(self):
        """Test that weight=0 failures do not block"""
        failed_rules = [
            FailedRule(rule_id="docs.readme", reason="Missing readme", weight=0),
        ]

        passed = self.scorer.check_passed(0.9, 0.8, failed_rules)

        # weight=0 is info-level, should not block
        assert passed

    def test_check_passed_default_weight_not_blocking(self):
        """Test that default weight (1) does not block"""
        failed_rules = [
            FailedRule(rule_id="correctness.tests", reason="No tests"),  # default weight=1
        ]

        passed = self.scorer.check_passed(0.9, 0.8, failed_rules)

        # Default weight=1, not blocking
        assert passed

    def test_calculate_distance_to_success_passed(self):
        """Test distance calculation when already passed"""
        distance = self.scorer.calculate_distance_to_success(0.9, 0.8)

        assert distance == 0.0  # Already passed

    def test_calculate_distance_to_success_failed(self):
        """Test distance calculation when not passed"""
        distance = self.scorer.calculate_distance_to_success(0.7, 0.9)

        assert abs(distance - 0.2) < 0.01


class TestScorerSimple:
    """Test Scorer.calculate_score_simple (backward compatibility)"""

    def setup_method(self):
        self.scorer = Scorer()
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

    def test_calculate_score_simple_partial(self):
        """Test simple score calculation without priority weighting"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = [self.rule1]

        score = self.scorer.calculate_score_simple(passed_rules, all_rules)

        # score = 2 / (2 + 1) = 2/3 ≈ 0.67
        assert abs(score - 0.67) < 0.01

    def test_calculate_score_simple_all_passed(self):
        """Test simple score with all rules passed"""
        all_rules = [self.rule1, self.rule2]
        passed_rules = all_rules

        score = self.scorer.calculate_score_simple(passed_rules, all_rules)

        assert score == 1.0

    def test_calculate_score_simple_no_rules(self):
        """Test simple score with no rules"""
        score = self.scorer.calculate_score_simple([], [])

        assert score == 1.0


class TestScorerPriorityScore:
    """Test Scorer priority profile scoring (Exp 139)"""

    def setup_method(self):
        self.scorer = Scorer()

        # Create rules with domain tags and categories
        self.rule_security = QualityRule(
            id="security.auth",
            description="Auth rule",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="check auth",
            domain_tags=["auth", "web"],
            category="security",
        )

        self.rule_performance = QualityRule(
            id="performance.caching",
            description="Caching rule",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.A,
            check="check caching",
            domain_tags=["api"],
            category="performance",
        )

        # Create priority profile with multipliers
        self.profile = PriorityProfile(
            name="security-focused",
            multipliers={"auth": 2.0, "web": 1.5, "api": 1.0},
            category_multipliers={"security": 1.5, "performance": 0.8},
            description="Security-focused profile",
        )

    def test_get_rule_priority_score_no_profile(self):
        """Test priority score without profile (base weight)"""
        score = self.scorer.get_rule_priority_score(self.rule_security, None)

        # Base weight * 1.0 (no multipliers)
        assert score == 2.0

    def test_get_rule_priority_score_with_domain_multiplier(self):
        """Test priority score with domain multipliers"""
        score = self.scorer.get_rule_priority_score(self.rule_security, self.profile)

        # weight 2 * auth multiplier 2.0 * security category 1.5 = 6.0
        assert score == 6.0

    def test_get_rule_priority_score_with_category_multiplier(self):
        """Test priority score with category multipliers"""
        score = self.scorer.get_rule_priority_score(self.rule_performance, self.profile)

        # weight 1 * api multiplier 1.0 * performance category 0.8 = 0.8
        assert abs(score - 0.8) < 0.01

    def test_calculate_score_with_priority_profile(self):
        """Test score calculation with priority profile"""
        all_rules = [self.rule_security, self.rule_performance]
        passed_rules = [self.rule_security]

        score = self.scorer.calculate_score(passed_rules, all_rules, self.profile)

        # Security rule: weight 2 * auth 2.0 * security 1.5 = 6.0
        # Performance rule: weight 1 * api 1.0 * performance 0.8 = 0.8
        # Score = 6.0 / (6.0 + 0.8) = 6.0 / 6.8 ≈ 0.88
        assert abs(score - 0.88) < 0.02

    def test_calculate_score_both_passed_with_profile(self):
        """Test score when both rules pass with profile"""
        all_rules = [self.rule_security, self.rule_performance]
        passed_rules = all_rules

        score = self.scorer.calculate_score(passed_rules, all_rules, self.profile)

        # Both passed = perfect score
        assert score == 1.0


class TestScorerSeverityCounts:
    """Test Scorer severity counting (Exp 139, updated Exp 43)"""

    def setup_method(self):
        self.scorer = Scorer()

    def test_get_severity_counts_empty(self):
        """Test severity counts with no failures"""
        counts = self.scorer.get_severity_counts([], [])

        assert counts["critical"] == 0
        assert counts["high"] == 0
        assert counts["medium"] == 0
        assert counts["low"] == 0
        assert counts["info"] == 0

    def test_get_severity_counts_security_blocking(self):
        """Test severity counts for security blocking rules (weight>=2 -> critical)"""
        failed_rules = [
            FailedRule(rule_id="security.sql_injection", reason="SQL injection", category="security", weight=2, severity="fail"),
            FailedRule(rule_id="security.xss_attack", reason="XSS vulnerability", category="security", weight=2, severity="fail"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # security + weight>=2 -> critical
        assert counts["critical"] == 2

    def test_get_severity_counts_security_warning(self):
        """Exp 43: Security warning (weight=1) maps to high, not critical"""
        warnings = [
            FailedRule(rule_id="security.cors_config", reason="CORS not strict", category="security", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts([], warnings)

        # security + weight<2 -> high (not critical!)
        assert counts["high"] == 1
        assert counts["critical"] == 0

    def test_get_severity_counts_correctness_blocking(self):
        """Test correctness blocking rules (weight>=2 -> high)"""
        failed_rules = [
            FailedRule(rule_id="correctness.tests", reason="No tests", category="correctness", weight=2, severity="fail"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # correctness + weight>=2 -> high
        assert counts["high"] == 1

    def test_get_severity_counts_correctness_warning(self):
        """Exp 43: Correctness warning (weight=1) maps to medium, not high"""
        failed_rules = [
            FailedRule(rule_id="correctness.type_hints", reason="Missing types", category="correctness", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # correctness + weight<2 -> medium
        assert counts["medium"] == 1
        assert counts["high"] == 0

    def test_get_severity_counts_performance(self):
        """Test severity counts for performance rules (always medium)"""
        warnings = [
            FailedRule(rule_id="performance.caching", reason="No caching", category="performance", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts([], warnings)

        # performance.* -> medium
        assert counts["medium"] == 1

    def test_get_severity_counts_quality_blocking(self):
        """Exp 43: Quality blocking rule (weight>=2) maps to medium, not low"""
        failed_rules = [
            FailedRule(rule_id="quality.error_handling", reason="No error handling", category="quality", weight=2, severity="fail"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # quality + weight>=2 -> medium
        assert counts["medium"] == 1
        assert counts["low"] == 0

    def test_get_severity_counts_quality_warning(self):
        """Test quality warning maps to low"""
        failed_rules = [
            FailedRule(rule_id="quality.readability", reason="Low readability", category="quality", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # quality + weight<2 -> low
        assert counts["low"] == 1

    def test_get_severity_counts_info_always_info(self):
        """Exp 43: Info rules (weight=0) always map to info regardless of prefix"""
        failed_rules = [
            FailedRule(rule_id="security.advisory", reason="Advisory", category="security", weight=0, severity="info"),
            FailedRule(rule_id="correctness.hint", reason="Hint", category="correctness", weight=0, severity="info"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # weight=0 / severity=info -> always info
        assert counts["info"] == 2
        assert counts["critical"] == 0
        assert counts["high"] == 0

    def test_get_severity_counts_mixed(self):
        """Test severity counts with mixed severities and weights"""
        failed_rules = [
            FailedRule(rule_id="security.auth", reason="No auth", category="security", weight=2, severity="fail"),
            FailedRule(rule_id="correctness.type_hints", reason="No types", category="correctness", weight=1, severity="warn"),
            FailedRule(rule_id="performance.complexity", reason="Complex", category="performance", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        assert counts["critical"] == 1  # security + blocking
        assert counts["medium"] == 2  # correctness warning + performance
        assert counts["high"] == 0

    def test_get_severity_counts_unknown_prefix(self):
        """Test severity counts for unknown rule prefix (defaults to medium)"""
        failed_rules = [
            FailedRule(rule_id="unknown.rule", reason="Unknown rule", category="general", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        # Unknown prefix -> medium (default)
        assert counts["medium"] == 1

    def test_get_severity_counts_docs_always_info(self):
        """Test docs rules always map to info"""
        failed_rules = [
            FailedRule(rule_id="docs.readme", reason="Missing readme", category="docs", weight=1, severity="warn"),
        ]

        counts = self.scorer.get_severity_counts(failed_rules, [])

        assert counts["info"] == 1


class TestScorerCategoryScores:
    """Test Scorer category scoring (Exp 139)"""

    def setup_method(self):
        self.scorer = Scorer()

        self.security_rule = QualityRule(
            id="security.auth",
            description="Auth rule",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="check auth",
            category="security",
        )

        self.performance_rule = QualityRule(
            id="performance.caching",
            description="Caching rule",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.A,
            check="check caching",
            category="performance",
        )

        self.docs_rule = QualityRule(
            id="docs.readme",
            description="Readme rule",
            severity=RuleSeverity.info,
            weight=0,
            phase=Phase.A,
            check="check readme",
            category="docs",
        )

    def test_get_category_scores_all_passed(self):
        """Test category scores when all rules pass"""
        all_rules = [self.security_rule, self.performance_rule, self.docs_rule]
        passed_rules = all_rules
        failed_rules = []

        scores = self.scorer.get_category_scores(passed_rules, failed_rules, all_rules)

        assert scores["security"]["score"] == 1.0
        assert scores["security"]["passed"] == 1
        assert scores["security"]["total"] == 1
        assert scores["security"]["failed"] == 0

        assert scores["performance"]["score"] == 1.0
        assert scores["docs"]["score"] == 1.0

    def test_get_category_scores_partial_failure(self):
        """Test category scores with some failures"""
        all_rules = [self.security_rule, self.performance_rule, self.docs_rule]
        passed_rules = [self.security_rule]
        failed_rules = [
            FailedRule(rule_id="performance.caching", reason="No caching", category="performance"),
            FailedRule(rule_id="docs.readme", reason="No readme", category="docs"),
        ]

        scores = self.scorer.get_category_scores(passed_rules, failed_rules, all_rules)

        assert scores["security"]["score"] == 1.0
        assert scores["security"]["passed"] == 1
        assert scores["security"]["failed"] == 0

        assert scores["performance"]["score"] == 0.0
        assert scores["performance"]["passed"] == 0
        assert scores["performance"]["failed"] == 1
        assert scores["performance"]["total"] == 1

        assert scores["docs"]["score"] == 0.0
        assert scores["docs"]["passed"] == 0
        assert scores["docs"]["failed"] == 1

    def test_get_category_scores_empty(self):
        """Test category scores with no rules"""
        scores = self.scorer.get_category_scores([], [], [])

        assert scores == {}


class TestScorerGateConditions:
    """Test Scorer gate condition checking (Exp 139)"""

    def setup_method(self):
        self.scorer = Scorer()

    def test_check_gate_conditions_passed(self):
        """Test gate conditions when passed"""
        result = self.scorer.check_gate_conditions(
            score=0.9,
            threshold=0.8,
            failed_rules=[],
            category_scores={},
            severity_counts={},
        )

        assert result["passed"] is True
        assert result["score"] == 0.9
        assert result["threshold"] == 0.8
        assert result["has_critical_issues"] is False
        assert result["has_high_issues"] is False
        assert result["failing_categories"] == []

    def test_check_gate_conditions_low_score(self):
        """Test gate conditions with low score"""
        result = self.scorer.check_gate_conditions(
            score=0.7,
            threshold=0.8,
            failed_rules=[],
            category_scores={},
            severity_counts={},
        )

        assert result["passed"] is False
        assert result["score"] == 0.7

    def test_check_gate_conditions_with_critical(self):
        """Test gate conditions with critical severity"""
        result = self.scorer.check_gate_conditions(
            score=0.9,
            threshold=0.8,
            failed_rules=[],
            category_scores={},
            severity_counts={"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0},
        )

        # Critical issues should fail even with high score
        assert result["passed"] is False
        assert result["has_critical_issues"] is True

    def test_check_gate_conditions_with_high(self):
        """Test gate conditions with high severity (but not critical)"""
        result = self.scorer.check_gate_conditions(
            score=0.9,
            threshold=0.8,
            failed_rules=[],
            category_scores={},
            severity_counts={"critical": 0, "high": 2, "medium": 0, "low": 0, "info": 0},
        )

        # High score with high severity issues (but no critical) still passes
        assert result["passed"] is True
        assert result["has_high_issues"] is True
        assert result["has_critical_issues"] is False

    def test_check_gate_conditions_with_failing_categories(self):
        """Test gate conditions reports failing categories"""
        result = self.scorer.check_gate_conditions(
            score=0.9,
            threshold=0.8,
            failed_rules=[],
            category_scores={
                "security": {"score": 0.5, "passed": 1, "failed": 1, "total": 2},
                "performance": {"score": 1.0, "passed": 2, "failed": 0, "total": 2},
            },
            severity_counts={},
        )

        assert result["passed"] is True
        assert result["failing_categories"] == ["security"]

    def test_check_gate_conditions_complete(self):
        """Test gate conditions with all data populated"""
        result = self.scorer.check_gate_conditions(
            score=0.85,
            threshold=0.8,
            failed_rules=[
                FailedRule(rule_id="performance.cache", reason="No cache", category="performance"),
            ],
            category_scores={
                "security": {"score": 1.0, "passed": 2, "failed": 0, "total": 2},
                "performance": {"score": 0.5, "passed": 1, "failed": 1, "total": 2},
            },
            severity_counts={"critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0},
        )

        assert result["passed"] is True
        assert result["score"] == 0.85
        assert result["failing_categories"] == ["performance"]
        assert result["severity_counts"]["medium"] == 1


class TestScorerPriorityProfiles:
    """Test Scorer priority profile helpers (Exp 139)"""

    def setup_method(self):
        self.scorer = Scorer()

        # Create a criteria template with priority profiles
        self.criteria = CriteriaTemplate(
            name="test-template",
            version=1.0,
            description="Test template",
            phases={
                "a": PhaseConfig(threshold=0.8),
            },
            rules=[],
            priority_profiles={
                "default": PriorityProfile(
                    name="default",
                    multipliers={"web": 1.0, "api": 1.0},
                    description="Default profile",
                ),
                "security-focused": PriorityProfile(
                    name="security-focused",
                    multipliers={"auth": 2.0, "web": 1.5},
                    description="Security focused",
                ),
            },
        )

    def test_list_priority_profiles(self):
        """Test listing priority profiles from criteria"""
        profiles = self.scorer.list_priority_profiles(self.criteria)

        assert "default" in profiles
        assert "security-focused" in profiles
        assert len(profiles) == 2

    def test_get_default_priority_profile(self):
        """Test getting default priority profile"""
        profile = self.scorer.get_default_priority_profile(self.criteria)

        assert profile.name == "default"
        assert profile.multipliers == {"web": 1.0, "api": 1.0}

    def test_get_default_priority_profile_creates_if_missing(self):
        """Test that default profile is created if missing"""
        criteria_no_default = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles={},  # No default
        )

        profile = self.scorer.get_default_priority_profile(criteria_no_default)

        assert profile.name == "default"
        # Should have been created with default multipliers
        assert "web" in profile.multipliers
        assert "api" in profile.multipliers

    def test_validate_priority_profile_exists(self):
        """Test validating existing priority profile"""
        result = self.scorer.validate_priority_profile(self.criteria, "security-focused")

        assert result is True

    def test_validate_priority_profile_not_exists(self):
        """Test validating non-existing priority profile"""
        result = self.scorer.validate_priority_profile(self.criteria, "nonexistent")

        assert result is False
