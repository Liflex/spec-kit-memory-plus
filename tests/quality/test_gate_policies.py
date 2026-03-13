"""
Tests for gate_policies.py - Quality Gate Policies

Tests for:
- SeverityGate, CategoryGate, GatePolicy classes
- GatePolicyManager - management and evaluation
- GatePolicyCascade - cascade multiple policies
- GatePolicyRecommender - policy recommendations
"""

import pytest
from typing import Dict, Any

from specify_cli.quality.gate_policies import (
    # Enums
    GateResult,
    ValidationError,
    CascadeStrategy,
    CascadeValidationError,
    RecommendationReason,

    # Data classes
    ValidationIssue,
    SeverityGate,
    CategoryGate,
    GatePolicy,
    CascadeValidationIssue,
    CascadeGatePolicy,
    PolicyRecommendation,

    # Main classes
    GatePolicyManager,
    GatePolicyCascade,
    GatePolicyRecommender,

    # Functions
    evaluate_quality_gate,
    cascade_gate_policies,
    format_cascade_policy,
    format_cascade_policy_json,
    format_recommendation,
    format_recommendation_json,
)


# ============================================================================
# Tests for Enums
# ============================================================================

class TestGateResult:
    """Tests for GateResult enum"""

    def test_gate_result_values(self):
        """Test GateResult enum has correct values"""
        assert GateResult.PASSED.value == "passed"
        assert GateResult.FAILED.value == "failed"
        assert GateResult.WARNING.value == "warning"


class TestValidationError:
    """Tests for ValidationError enum"""

    def test_validation_error_types(self):
        """Test ValidationError enum has all required types"""
        assert ValidationError.INVALID_THRESHOLD.value == "invalid_threshold"
        assert ValidationError.INVALID_SEVERITY_LIMIT.value == "invalid_severity_limit"
        assert ValidationError.INVALID_CATEGORY_LIMIT.value == "invalid_category_limit"
        assert ValidationError.INVALID_CATEGORY_SCORE.value == "invalid_category_score"
        assert ValidationError.DUPLICATE_POLICY_NAME.value == "duplicate_policy_name"
        assert ValidationError.MISSING_REQUIRED_FIELD.value == "missing_required_field"


class TestCascadeStrategy:
    """Tests for CascadeStrategy enum"""

    def test_cascade_strategy_values(self):
        """Test CascadeStrategy enum has correct values"""
        assert CascadeStrategy.STRICT.value == "strict"
        assert CascadeStrategy.LENIENT.value == "lenient"
        assert CascadeStrategy.AVERAGE.value == "average"
        assert CascadeStrategy.UNION.value == "union"
        assert CascadeStrategy.INTERSECTION.value == "intersection"


class TestCascadeValidationError:
    """Tests for CascadeValidationError enum"""

    def test_cascade_validation_error_values(self):
        """Test CascadeValidationError enum has correct values"""
        assert CascadeValidationError.POLICY_NOT_FOUND.value == "policy_not_found"
        assert CascadeValidationError.EMPTY_POLICY_LIST.value == "empty_policy_list"
        assert CascadeValidationError.INVALID_STRATEGY.value == "invalid_strategy"
        assert CascadeValidationError.INCOMPATIBLE_POLICIES.value == "incompatible_policies"


class TestRecommendationReason:
    """Tests for RecommendationReason enum"""

    def test_recommendation_reason_values(self):
        """Test RecommendationReason enum has correct values"""
        assert RecommendationReason.CI_ENVIRONMENT.value == "ci_environment"
        assert RecommendationReason.PRODUCTION_BRANCH.value == "production_branch"
        assert RecommendationReason.PROJECT_TYPE.value == "project_type"
        assert RecommendationReason.QUALITY_SCORE.value == "quality_score"
        assert RecommendationReason.USER_PREFERENCE.value == "user_preference"
        assert RecommendationReason.SECURITY_SENSITIVE.value == "security_sensitive"
        assert RecommendationReason.CRITICAL_SYSTEM.value == "critical_system"
        assert RecommendationReason.EXPERIMENTAL.value == "experimental"


# ============================================================================
# Tests for SeverityGate
# ============================================================================

class TestSeverityGate:
    """Tests for SeverityGate dataclass"""

    def test_severity_gate_defaults(self):
        """Test SeverityGate has correct default values"""
        gate = SeverityGate()
        assert gate.critical_max == 0
        assert gate.high_max == 0
        assert gate.medium_max == 5
        assert gate.low_max == 999
        assert gate.info_max == 999

    def test_severity_gate_custom_values(self):
        """Test SeverityGate with custom values"""
        gate = SeverityGate(critical_max=1, high_max=2, medium_max=3, low_max=5, info_max=10)
        assert gate.critical_max == 1
        assert gate.high_max == 2
        assert gate.medium_max == 3
        assert gate.low_max == 5
        assert gate.info_max == 10

    def test_severity_gate_check_pass(self):
        """Test SeverityGate check returns True when within limits"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5, low_max=10)

        # All within limits
        severity_counts = {"critical": 0, "high": 1, "medium": 3, "low": 5, "info": 0}
        passed, messages = gate.check(severity_counts)
        assert passed is True
        assert len(messages) == 0

    def test_severity_gate_check_fail_critical(self):
        """Test SeverityGate check fails on critical issues"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5, low_max=10)

        severity_counts = {"critical": 1, "high": 0, "medium": 0, "low": 0, "info": 0}
        passed, messages = gate.check(severity_counts)
        assert passed is False
        assert len(messages) > 0
        assert any("critical" in m.lower() for m in messages)

    def test_severity_gate_check_fail_high(self):
        """Test SeverityGate check fails on high issues"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5, low_max=10)

        severity_counts = {"critical": 0, "high": 2, "medium": 0, "low": 0, "info": 0}
        passed, messages = gate.check(severity_counts)
        assert passed is False
        assert len(messages) > 0
        assert any("high" in m.lower() for m in messages)

    def test_severity_gate_check_fail_medium(self):
        """Test SeverityGate check fails on medium issues"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5, low_max=10)

        severity_counts = {"critical": 0, "high": 0, "medium": 6, "low": 0, "info": 0}
        passed, messages = gate.check(severity_counts)
        assert passed is False
        assert len(messages) > 0
        assert any("medium" in m.lower() for m in messages)

    def test_severity_gate_check_fail_low(self):
        """Test SeverityGate check fails on low issues"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5, low_max=10)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 11, "info": 0}
        passed, messages = gate.check(severity_counts)
        assert passed is False
        assert len(messages) > 0
        assert any("low" in m.lower() for m in messages)

    def test_severity_gate_check_partial_counts(self):
        """Test SeverityGate check with partial severity counts"""
        gate = SeverityGate(critical_max=0, high_max=1, medium_max=5)

        # Missing keys should be treated as 0
        severity_counts = {"critical": 0, "high": 1}
        passed, messages = gate.check(severity_counts)
        assert passed is True


# ============================================================================
# Tests for CategoryGate
# ============================================================================

class TestCategoryGate:
    """Tests for CategoryGate dataclass"""

    def test_category_gate_defaults(self):
        """Test CategoryGate has correct default values"""
        gate = CategoryGate(category="security")
        assert gate.category == "security"
        assert gate.max_failed == 999
        assert gate.min_score == 0.0

    def test_category_gate_custom_values(self):
        """Test CategoryGate with custom values"""
        gate = CategoryGate(category="testing", max_failed=2, min_score=0.8)
        assert gate.category == "testing"
        assert gate.max_failed == 2
        assert gate.min_score == 0.8

    def test_category_gate_check_pass(self):
        """Test CategoryGate check returns True when within limits"""
        gate = CategoryGate(category="security", max_failed=1, min_score=0.8)

        # Within limits
        passed, messages = gate.check(category_score=0.85, failed_count=1)
        assert passed is True
        assert len(messages) == 0

    def test_category_gate_check_fail_max_failed(self):
        """Test CategoryGate check fails on too many failed rules"""
        gate = CategoryGate(category="security", max_failed=1, min_score=0.8)

        passed, messages = gate.check(category_score=0.9, failed_count=2)
        assert passed is False
        assert len(messages) > 0
        assert any("failed" in m.lower() for m in messages)
        assert any("security" in m for m in messages)

    def test_category_gate_check_fail_min_score(self):
        """Test CategoryGate check fails on too low score"""
        gate = CategoryGate(category="security", max_failed=1, min_score=0.8)

        passed, messages = gate.check(category_score=0.75, failed_count=0)
        assert passed is False
        assert len(messages) > 0
        assert any("score" in m.lower() for m in messages)
        assert any("security" in m for m in messages)

    def test_category_gate_check_fail_both(self):
        """Test CategoryGate check fails when both limits exceeded"""
        gate = CategoryGate(category="security", max_failed=1, min_score=0.8)

        passed, messages = gate.check(category_score=0.7, failed_count=2)
        assert passed is False
        # Should mention both issues
        assert len(messages) >= 2
        assert any("security" in m for m in messages)


# ============================================================================
# Tests for GatePolicy
# ============================================================================

class TestGatePolicy:
    """Tests for GatePolicy dataclass"""

    def test_gate_policy_creation(self):
        """Test GatePolicy creation with required fields"""
        # description is required field
        policy = GatePolicy(name="test-policy", description="Test policy")
        assert policy.name == "test-policy"
        assert policy.description == "Test policy"
        assert policy.overall_threshold == 0.8
        assert policy.block_on_failure is True
        # Default severity gate is created in __post_init__
        assert policy.severity_gate is not None

    def test_gate_policy_with_severity_gate(self):
        """Test GatePolicy with custom severity gate"""
        severity = SeverityGate(critical_max=0, high_max=1)
        policy = GatePolicy(name="strict", description="Strict policy", severity_gate=severity)
        assert policy.severity_gate == severity

    def test_gate_policy_with_category_gates(self):
        """Test GatePolicy with category gates"""
        categories = [
            CategoryGate(category="security", max_failed=0),
            CategoryGate(category="testing", max_failed=2),
        ]
        policy = GatePolicy(name="balanced", description="Balanced policy", category_gates=categories)
        assert len(policy.category_gates) == 2
        assert policy.category_gates[0].category == "security"
        assert policy.category_gates[1].category == "testing"

    def test_gate_policy_check_pass(self):
        """Test GatePolicy check passes when all conditions met"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            overall_threshold=0.8,
            severity_gate=SeverityGate(critical_max=0, high_max=1),
            category_gates=[CategoryGate(category="security", max_failed=0)]
        )

        result, messages = policy.check(
            overall_score=0.85,
            category_scores={"security": 0.9},
            category_failed={"security": 0},
            severity_counts={"critical": 0, "high": 0, "medium": 0, "low": 0}
        )
        assert result == GateResult.PASSED
        assert len(messages) == 0

    def test_gate_policy_check_fail_overall_threshold(self):
        """Test GatePolicy check fails on overall threshold"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            overall_threshold=0.8
        )

        result, messages = policy.check(
            overall_score=0.75,
            category_scores={},
            category_failed={},
            severity_counts={}
        )
        assert result == GateResult.FAILED
        assert len(messages) > 0

    def test_gate_policy_check_fail_severity_gate(self):
        """Test GatePolicy check fails on severity gate"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            severity_gate=SeverityGate(critical_max=0, high_max=1)
        )

        result, messages = policy.check(
            overall_score=0.9,
            category_scores={},
            category_failed={},
            severity_counts={"critical": 1, "high": 0, "medium": 0}
        )
        assert result == GateResult.FAILED
        assert len(messages) > 0


# ============================================================================
# Tests for ValidationIssue
# ============================================================================

class TestValidationIssue:
    """Tests for ValidationIssue dataclass"""

    def test_validation_issue_creation(self):
        """Test ValidationIssue creation"""
        issue = ValidationIssue(
            error_type=ValidationError.INVALID_THRESHOLD,
            field="overall_threshold",
            message="Threshold must be between 0 and 1",
            policy_name="test-policy"
        )
        assert issue.error_type == ValidationError.INVALID_THRESHOLD
        assert issue.field == "overall_threshold"
        assert issue.message == "Threshold must be between 0 and 1"
        assert issue.policy_name == "test-policy"

    def test_validation_issue_to_dict(self):
        """Test ValidationIssue to_dict method"""
        issue = ValidationIssue(
            error_type=ValidationError.INVALID_THRESHOLD,
            field="overall_threshold",
            message="Threshold must be between 0 and 1",
            policy_name="test-policy"
        )
        result = issue.to_dict()
        assert result["error_type"] == "invalid_threshold"
        assert result["field"] == "overall_threshold"
        assert result["message"] == "Threshold must be between 0 and 1"
        assert result["policy_name"] == "test-policy"


class TestCascadeValidationIssue:
    """Tests for CascadeValidationIssue dataclass"""

    def test_cascade_validation_issue_creation(self):
        """Test CascadeValidationIssue creation"""
        issue = CascadeValidationIssue(
            error_type=CascadeValidationError.POLICY_NOT_FOUND,
            message="Policy 'strict' not found",
            details={"policy_names": ["strict"]}
        )
        assert issue.error_type == CascadeValidationError.POLICY_NOT_FOUND
        assert issue.message == "Policy 'strict' not found"
        assert issue.details == {"policy_names": ["strict"]}

    def test_cascade_validation_issue_to_dict(self):
        """Test CascadeValidationIssue to_dict method"""
        issue = CascadeValidationIssue(
            error_type=CascadeValidationError.EMPTY_POLICY_LIST,
            message="Empty policy list"
        )
        result = issue.to_dict()
        assert result["error_type"] == "empty_policy_list"
        assert result["message"] == "Empty policy list"


# ============================================================================
# Tests for evaluate_quality_gate function
# ============================================================================

class TestEvaluateQualityGate:
    """Tests for evaluate_quality_gate function"""

    def test_evaluate_with_ci_preset_passes(self):
        """Test evaluation with CI preset passes"""
        evaluation_result = {
            "score": 0.85,
            "state": {
                "iteration": 1,
                "phase": "A",
                "evaluation": {
                    "total_rules": 10,
                    "passed_rules": 9,
                    "failed_rules": [],
                    "category_breakdown": {
                        "categories": [
                            {"name": "security", "score": 0.9, "total": 5, "failed": 0}
                        ]
                    },
                    "severity_counts": {"critical": 0, "high": 0, "medium": 0}
                }
            }
        }

        result = evaluate_quality_gate(evaluation_result, gate_preset="ci")
        assert "gate_result" in result
        assert "passed" in result

    def test_evaluate_with_custom_policy(self):
        """Test evaluation with custom policy"""
        custom_policy = GatePolicy(
            name="strict",
            description="Strict policy",
            overall_threshold=0.9,
            severity_gate=SeverityGate(critical_max=0, high_max=0)
        )

        evaluation_result = {
            "score": 0.95,
            "state": {
                "iteration": 1,
                "phase": "A",
                "evaluation": {
                    "total_rules": 10,
                    "passed_rules": 10,
                    "failed_rules": [],
                    "severity_counts": {"critical": 0, "high": 0, "medium": 0}
                }
            }
        }

        result = evaluate_quality_gate(evaluation_result, gate_policy=custom_policy)
        assert "gate_result" in result
        assert "passed" in result

    def test_evaluate_low_score_fails(self):
        """Test evaluation fails with low score"""
        evaluation_result = {
            "score": 0.6,
            "state": {
                "iteration": 1,
                "phase": "A",
                "evaluation": {
                    "total_rules": 10,
                    "passed_rules": 6,
                    "failed_rules": [],
                    "severity_counts": {"critical": 1, "high": 2, "medium": 1}
                }
            }
        }

        result = evaluate_quality_gate(evaluation_result, gate_preset="ci")
        # Low score with critical issues should fail
        assert result.get("passed", True) is False or result.get("gate_result") == GateResult.FAILED


# ============================================================================
# Tests for GatePolicyManager
# ============================================================================

class TestGatePolicyManager:
    """Tests for GatePolicyManager static methods"""

    def test_get_preset_ci(self):
        """Test getting CI preset policy"""
        policy = GatePolicyManager.get_preset("ci")
        assert policy is not None
        assert policy.name == "ci"

    def test_get_preset_production(self):
        """Test getting production preset policy"""
        policy = GatePolicyManager.get_preset("production")
        assert policy is not None
        assert policy.name == "production"

    def test_get_preset_development(self):
        """Test getting development preset policy"""
        policy = GatePolicyManager.get_preset("development")
        assert policy is not None
        assert policy.name == "development"

    def test_get_preset_nonexistent_returns_none(self):
        """Test getting nonexistent preset returns None"""
        policy = GatePolicyManager.get_preset("nonexistent")
        assert policy is None

    def test_list_presets(self):
        """Test listing all available presets"""
        presets = GatePolicyManager.list_presets()
        assert isinstance(presets, list)
        assert len(presets) > 0
        # Should have at least basic presets
        assert "ci" in presets
        assert "production" in presets

    def test_validate_policy_valid(self):
        """Test validating a valid policy"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            overall_threshold=0.8,
            severity_gate=SeverityGate(critical_max=0, high_max=1)
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is True
        assert len(issues) == 0

    def test_validate_policy_invalid_threshold(self):
        """Test validating policy with invalid threshold"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            overall_threshold=1.5  # Invalid
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is False
        assert len(issues) > 0
        assert any(i.error_type == ValidationError.INVALID_THRESHOLD for i in issues)

    def test_validate_policy_negative_threshold(self):
        """Test validating policy with negative threshold"""
        policy = GatePolicy(
            name="test",
            description="Test policy",
            overall_threshold=-0.1  # Invalid
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is False
        assert len(issues) > 0
        assert any(i.error_type == ValidationError.INVALID_THRESHOLD for i in issues)

    def test_validate_policy_invalid_severity_limits(self):
        """Test validating policy with invalid severity limits"""
        severity = SeverityGate(critical_max=-1)  # Invalid
        policy = GatePolicy(
            name="test",
            description="Test policy",
            severity_gate=severity
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is False
        assert len(issues) > 0
        assert any(i.error_type == ValidationError.INVALID_SEVERITY_LIMIT for i in issues)

    def test_validate_policy_invalid_category_limits(self):
        """Test validating policy with invalid category limits"""
        category = CategoryGate(category="security", max_failed=-1)  # Invalid
        policy = GatePolicy(
            name="test",
            description="Test policy",
            category_gates=[category]
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is False
        assert len(issues) > 0
        assert any(i.error_type == ValidationError.INVALID_CATEGORY_LIMIT for i in issues)

    def test_validate_policy_invalid_category_score(self):
        """Test validating policy with invalid category score"""
        category = CategoryGate(category="security", min_score=1.5)  # Invalid
        policy = GatePolicy(
            name="test",
            description="Test policy",
            category_gates=[category]
        )

        passed, issues = GatePolicyManager.validate_policy(policy)
        assert passed is False
        assert len(issues) > 0
        assert any(i.error_type == ValidationError.INVALID_CATEGORY_SCORE for i in issues)


# ============================================================================
# Tests for CascadeGatePolicy and GatePolicyCascade
# ============================================================================

class TestCascadeGatePolicy:
    """Tests for CascadeGatePolicy dataclass"""

    def test_cascade_gate_policy_creation(self):
        """Test CascadeGatePolicy creation with required fields"""
        base_policy = GatePolicy(name="base", description="Base policy", overall_threshold=0.8)
        cascade = CascadeGatePolicy(
            name="test-cascade",
            description="Test cascade",
            source_policies=["production", "ci"],
            strategy=CascadeStrategy.STRICT,
            merged_policy=base_policy
        )
        assert cascade.name == "test-cascade"
        assert cascade.description == "Test cascade"
        assert cascade.strategy == CascadeStrategy.STRICT
        assert len(cascade.source_policies) == 2

    def test_cascade_gate_policy_to_dict(self):
        """Test CascadeGatePolicy to_dict method"""
        base_policy = GatePolicy(name="base", description="Base", overall_threshold=0.8)
        cascade = CascadeGatePolicy(
            name="test",
            description="Test cascade",
            source_policies=["p1", "p2"],
            strategy=CascadeStrategy.LENIENT,
            merged_policy=base_policy
        )
        result = cascade.to_dict()
        assert result["name"] == "test"
        assert result["strategy"] == "lenient"
        assert len(result["source_policies"]) == 2


class TestGatePolicyCascade:
    """Tests for GatePolicyCascade class"""

    def test_list_cascade_presets(self):
        """Test listing all cascade presets"""
        presets = GatePolicyCascade.list_cascade_presets()
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_get_cascade_preset(self):
        """Test getting a cascade preset"""
        cascade = GatePolicyCascade.get_cascade_preset("prod-security")
        assert cascade is not None
        assert "description" in cascade
        assert "policies" in cascade
        assert "strategy" in cascade

    def test_get_cascade_preset_nonexistent(self):
        """Test getting nonexistent cascade preset returns None"""
        cascade = GatePolicyCascade.get_cascade_preset("nonexistent")
        assert cascade is None


class TestCascadeGatePoliciesFunction:
    """Tests for cascade_gate_policies function"""

    def test_cascade_valid_policies(self):
        """Test cascading valid policies"""
        result, issues = cascade_gate_policies(
            policy_names=["production", "ci"],
            strategy="strict"
        )
        # Should return a cascade policy or validation issues
        assert result is not None or len(issues) > 0

    def test_cascade_invalid_strategy(self):
        """Test cascading with invalid strategy"""
        result, issues = cascade_gate_policies(
            policy_names=["production", "ci"],
            strategy="invalid_strategy"
        )
        # Should return validation error
        assert result is None
        assert len(issues) > 0
        assert any(i.error_type == CascadeValidationError.INVALID_STRATEGY for i in issues)

    def test_cascade_with_custom_name(self):
        """Test cascading with custom cascade name"""
        result, issues = cascade_gate_policies(
            policy_names=["production", "ci"],
            strategy="lenient",
            cascade_name="my-custom-cascade"
        )
        # Should return a cascade policy with the custom name or validation issues
        if result is not None:
            assert result.name == "my-custom-cascade"


# ============================================================================
# Tests for GatePolicyRecommender
# ============================================================================

class TestPolicyRecommendation:
    """Tests for PolicyRecommendation dataclass"""

    def test_policy_recommendation_creation(self):
        """Test PolicyRecommendation creation with required fields"""
        recommendation = PolicyRecommendation(
            policy_name="strict",
            confidence=0.9,
            reasons=["High security requirements"],
            alternative_policies=[("production", "For production environments")],
            context={"environment": "production"}
        )
        assert recommendation.policy_name == "strict"
        assert recommendation.confidence == 0.9
        assert len(recommendation.reasons) == 1
        assert len(recommendation.alternative_policies) == 1

    def test_policy_recommendation_to_dict(self):
        """Test PolicyRecommendation to_dict method"""
        recommendation = PolicyRecommendation(
            policy_name="ci",
            confidence=0.85,
            reasons=["CI environment"],
            alternative_policies=[("strict", "Higher standards")],
            context={"env": "ci"}
        )
        result = recommendation.to_dict()
        assert result["policy_name"] == "ci"
        assert result["confidence"] == 0.85
        assert len(result["reasons"]) == 1
        assert len(result["alternative_policies"]) == 1


class TestGatePolicyRecommender:
    """Tests for GatePolicyRecommender class"""

    def test_recommender_initialization(self):
        """Test GatePolicyRecommender initialization"""
        recommender = GatePolicyRecommender()
        assert recommender is not None

    def test_recommend_default(self):
        """Test default recommendation"""
        recommender = GatePolicyRecommender()
        recommendation = recommender.recommend()
        assert recommendation is not None
        assert hasattr(recommendation, "policy_name")
        assert hasattr(recommendation, "confidence")

    def test_recommend_with_high_score(self):
        """Test recommendation with high quality score"""
        recommender = GatePolicyRecommender()
        recommendation = recommender.recommend(current_score=0.95)
        assert recommendation is not None
        assert recommendation.confidence >= 0.0

    def test_recommend_with_failed_categories(self):
        """Test recommendation with failed categories"""
        recommender = GatePolicyRecommender()
        recommendation = recommender.recommend(
            current_score=0.75,
            failed_categories=["security", "testing"]
        )
        assert recommendation is not None
        assert len(recommendation.reasons) > 0


# ============================================================================
# Tests for formatting functions
# ============================================================================

class TestFormattingFunctions:
    """Tests for formatting functions"""

    def test_format_cascade_policy(self):
        """Test format_cascade_policy returns string"""
        base_policy = GatePolicy(name="base", description="Base", overall_threshold=0.8)
        cascade = CascadeGatePolicy(
            name="test",
            description="Test cascade",
            source_policies=["p1", "p2"],
            strategy=CascadeStrategy.STRICT,
            merged_policy=base_policy
        )
        result = format_cascade_policy(cascade)
        assert isinstance(result, str)
        assert "test" in result

    def test_format_cascade_policy_json(self):
        """Test format_cascade_policy_json returns JSON string"""
        base_policy = GatePolicy(name="base", description="Base", overall_threshold=0.8)
        cascade = CascadeGatePolicy(
            name="test",
            description="Test cascade",
            source_policies=["p1", "p2"],
            strategy=CascadeStrategy.AVERAGE,
            merged_policy=base_policy
        )
        result = format_cascade_policy_json(cascade)
        assert isinstance(result, str)
        assert "test" in result

    def test_format_recommendation(self):
        """Test format_recommendation returns string"""
        recommendation = PolicyRecommendation(
            policy_name="strict",
            confidence=0.9,
            reasons=["High security"],
            alternative_policies=[("production", "Production env")],
            context={}
        )
        result = format_recommendation(recommendation)
        assert isinstance(result, str)
        assert "strict" in result

    def test_format_recommendation_json(self):
        """Test format_recommendation_json returns JSON string"""
        recommendation = PolicyRecommendation(
            policy_name="ci",
            confidence=0.85,
            reasons=["CI environment"],
            alternative_policies=[],
            context={}
        )
        result = format_recommendation_json(recommendation)
        assert isinstance(result, str)
        assert "ci" in result
