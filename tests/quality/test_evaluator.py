"""
Comprehensive unit tests for Evaluator (Exp 149)

Tests cover:
- Core evaluation functionality
- Rule-specific check methods
- Priority profile integration
- Cascade profile handling
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.models import (
    QualityRule,
    RuleSeverity,
    Phase,
    PhaseConfig,
    RuleCheckType,
    CriteriaTemplate,
    PriorityProfile,
    EvaluationResult,
    FailedRule,
)


class TestEvaluatorBasic:
    """Test basic Evaluator functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_evaluate_simple_artifact(self):
        """Test evaluating a simple artifact"""
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
        assert isinstance(result.passed_rules, list)
        assert isinstance(result.failed_rules, list)

    def test_evaluate_empty_artifact(self):
        """Test evaluating an empty artifact"""
        artifact = ""

        criteria = self.rule_manager.load_criteria("code-gen")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        # Empty artifact should have low score
        assert result.score < 0.5
        assert result.passed is False

    def test_evaluate_phase_a_vs_b(self):
        """Test that Phase B has same or lower score than Phase A"""
        artifact = """
def hello():
    print("Hello")
"""

        criteria = self.rule_manager.load_criteria("code-gen")
        result_a = self.evaluator.evaluate(artifact, criteria, "A")
        result_b = self.evaluator.evaluate(artifact, criteria, "B")

        assert 0.0 <= result_a.score <= 1.0
        assert 0.0 <= result_b.score <= 1.0
        # Phase B should have same or lower score (stricter)
        assert result_b.score <= result_a.score or result_b.score == result_a.score

    def test_evaluate_returns_evaluation_result(self):
        """Test that evaluate returns proper EvaluationResult"""
        artifact = "# Test"
        criteria = self.rule_manager.load_criteria("docs")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert isinstance(result, EvaluationResult)
        assert hasattr(result, "score")
        assert hasattr(result, "passed")
        assert hasattr(result, "threshold")
        assert hasattr(result, "phase")
        assert hasattr(result, "passed_rules")
        assert hasattr(result, "failed_rules")
        assert hasattr(result, "warnings")
        assert hasattr(result, "category_breakdown")
        assert hasattr(result, "category_scores")
        assert hasattr(result, "severity_counts")

    def test_evaluate_with_priority_profile(self):
        """Test evaluation with priority profile"""
        artifact = """
# API

## GET /users
## POST /users
## PUT /users
## DELETE /users
"""

        criteria = self.rule_manager.load_criteria("api-spec")

        # Get available profiles
        profiles = list(criteria.priority_profiles.keys()) if criteria.priority_profiles else []
        if profiles:
            result = self.evaluator.evaluate(
                artifact, criteria, "A", priority_profile=profiles[0]
            )
            assert result is not None
            assert result.priority_profile == profiles[0]
        else:
            # No profiles available - should use default
            result = self.evaluator.evaluate(artifact, criteria, "A")
            assert result is not None


class TestEvaluatorRuleChecking:
    """Test rule-specific check methods"""

    def setup_method(self):
        """Setup test fixtures"""
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_check_rule_content_passed(self):
        """Test _check_rule with content-based rule (pass)"""
        rule = QualityRule(
            id="test.keyword",
            description="Test keyword check",
            severity=RuleSeverity.fail,
            weight=1,
            phase=Phase.A,
            check="api endpoint users",
            check_type=RuleCheckType.content,
        )

        artifact = "This is an API endpoint for users"
        passed, reason = self.evaluator._check_rule(rule, artifact)

        # Should pass with keyword matching
        assert isinstance(passed, bool)
        assert isinstance(reason, str)

    def test_check_rule_content_failed(self):
        """Test _check_rule with content-based rule (fail)"""
        rule = QualityRule(
            id="test.keyword",
            description="Test keyword check",
            severity=RuleSeverity.fail,
            weight=1,
            phase=Phase.A,
            check="nonexistent impossible keyword",
            check_type=RuleCheckType.content,
        )

        artifact = "This has nothing relevant"
        passed, reason = self.evaluator._check_rule(rule, artifact)

        assert passed is False
        assert "0/" in reason  # Found 0 keywords

    def test_check_rule_executable(self):
        """Test _check_rule with executable rule"""
        rule = QualityRule(
            id="test.executable",
            description="Test executable check",
            severity=RuleSeverity.fail,
            weight=1,
            phase=Phase.A,
            check="some command",
            check_type=RuleCheckType.executable,
        )

        artifact = "some content"
        passed, reason = self.evaluator._check_rule(rule, artifact)

        # Executable checks not fully implemented
        assert isinstance(passed, bool)
        assert isinstance(reason, str)

    def test_check_rule_hybrid(self):
        """Test _check_rule with hybrid rule"""
        rule = QualityRule(
            id="test.hybrid",
            description="Test hybrid check",
            severity=RuleSeverity.fail,
            weight=1,
            phase=Phase.A,
            check="test keyword",
            check_type=RuleCheckType.hybrid,
        )

        artifact = "test keyword content"
        passed, reason = self.evaluator._check_rule(rule, artifact)

        assert isinstance(passed, bool)
        assert isinstance(reason, str)


class TestEvaluatorCRUDEndpoints:
    """Test _check_crud_endpoints method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_all_crud_endpoints_present(self):
        """Test when all CRUD endpoints are present"""
        artifact = """
# API
GET /users - list users
POST /users - create user
PUT /users - update user
DELETE /users - delete user
"""
        passed, reason = self.evaluator._check_crud_endpoints(
            artifact, artifact.lower()
        )

        assert passed is True
        assert "All CRUD" in reason

    def test_missing_crud_endpoints(self):
        """Test when some CRUD endpoints are missing"""
        artifact = """
# API
GET /users - list users
POST /users - create user
"""
        passed, reason = self.evaluator._check_crud_endpoints(
            artifact, artifact.lower()
        )

        assert passed is False
        assert "Missing" in reason

    def test_alternative_http_verbs(self):
        """Test alternative HTTP verb names (fetch, create, update, remove)"""
        artifact = """
# API
fetch users list
create new user
update existing user
remove deleted user
"""
        passed, reason = self.evaluator._check_crud_endpoints(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_no_http_verbs(self):
        """Test artifact with no HTTP verbs"""
        artifact = "This is just plain text with no API endpoints."

        passed, reason = self.evaluator._check_crud_endpoints(
            artifact, artifact.lower()
        )

        assert passed is False
        assert "Missing" in reason


class TestEvaluatorStatusCodes:
    """Test _check_status_codes method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_all_status_codes_present(self):
        """Test when all required status codes are documented"""
        artifact = """
200 - OK
201 - Created
204 - No Content
400 - Bad Request
404 - Not Found
500 - Internal Error
"""
        passed, reason = self.evaluator._check_status_codes(artifact, artifact.lower())

        assert passed is True
        assert "6/6" in reason

    def test_some_status_codes_present(self):
        """Test when only some status codes are documented"""
        artifact = """
200 - OK
201 - Created
"""
        passed, reason = self.evaluator._check_status_codes(artifact, artifact.lower())

        assert passed is False
        assert "2/6" in reason

    def test_no_status_codes(self):
        """Test artifact with no status codes"""
        artifact = "No status codes here"

        passed, reason = self.evaluator._check_status_codes(artifact, artifact.lower())

        assert passed is False
        assert "0/6" in reason


class TestEvaluatorAuthDocumentation:
    """Test _check_auth_documentation method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_auth_with_bearer_token(self):
        """Test auth documentation with bearer token"""
        artifact = "Authorization: Bearer token123"

        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_auth_with_oauth(self):
        """Test auth documentation with OAuth"""
        artifact = "Uses OAuth 2.0 for authentication"

        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_auth_with_api_key(self):
        """Test auth documentation with API key (single keyword match)"""
        # Note: "api key" (with space) won't match "x-api-key", but "api" will
        artifact = "Authentication: api key header"

        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )

        assert passed is True  # "auth" and "api" keywords found

    def test_no_auth_documentation(self):
        """Test artifact without auth documentation"""
        # Note: Must avoid all auth keywords: auth, token, bearer, api key, oauth, jwt, login
        artifact = "This documentation describes endpoints and schemas"

        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )

        assert passed is False


class TestEvaluatorTests:
    """Test _check_tests method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_pytest_present(self):
        """Test artifact with pytest references"""
        artifact = "import pytest\n\ndef test_something():\n    pass"

        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())

        assert passed is True
        assert "pytest" in reason.lower() or "test" in reason.lower()

    def test_jest_present(self):
        """Test artifact with Jest references"""
        artifact = "describe('test', () => { it('should work', () => {}); });"

        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())

        assert passed is True

    def test_no_tests(self):
        """Test artifact without test references"""
        artifact = "def hello():\n    print('hello')"

        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())

        assert passed is False


class TestEvaluatorTypeHints:
    """Test _check_type_hints method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_type_hints_present(self):
        """Test code with type hints"""
        artifact = """
def greet(name: str) -> str:
    return f"Hello, {name}"

def get_items() -> List[int]:
    return [1, 2, 3]
"""
        passed, reason = self.evaluator._check_type_hints(artifact, artifact.lower())

        assert passed is True

    def test_no_type_hints(self):
        """Test code without type hints"""
        artifact = """
def greet(name):
    return f"Hello, {name}"
"""
        passed, reason = self.evaluator._check_type_hints(artifact, artifact.lower())

        assert passed is False

    def test_partial_type_hints(self):
        """Test code with only one type hint pattern"""
        artifact = "x: int = 5"

        passed, reason = self.evaluator._check_type_hints(artifact, artifact.lower())

        # Only 1 pattern found, need 2
        assert passed is False


class TestEvaluatorSecrets:
    """Test _check_secrets method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_no_hardcoded_secrets(self):
        """Test clean code without hardcoded secrets"""
        artifact = """
password = os.environ.get('PASSWORD')
api_key = settings.API_KEY
"""

        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())

        assert passed is True
        assert "No hardcoded secrets" in reason

    def test_hardcoded_password(self):
        """Test code with hardcoded password"""
        artifact = 'password = "supersecret123"'

        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())

        assert passed is False
        assert "secret" in reason.lower()

    def test_hardcoded_api_key(self):
        """Test code with hardcoded API key"""
        artifact = "api_key = 'sk-1234567890abcdef'"

        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())

        assert passed is False

    def test_hardcoded_token(self):
        """Test code with hardcoded token"""
        artifact = 'token = "bearer_token_xyz"'

        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())

        assert passed is False

    # Exp 13: False positive exclusions

    def test_env_var_reference_not_flagged(self):
        """Env var references like ${VAR} should not be flagged"""
        artifact = 'password = "${DB_PASSWORD}"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_env_var_subshell_not_flagged(self):
        """Env var subshell like $(VAR) should not be flagged"""
        artifact = "api_key = '$(get_api_key)'"
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_placeholder_your_x_here_not_flagged(self):
        """YOUR_X_HERE placeholders should not be flagged"""
        artifact = 'api_key = "YOUR_API_KEY_HERE"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_placeholder_angle_brackets_not_flagged(self):
        """<your-secret> placeholders should not be flagged"""
        artifact = 'token = "<your-token>"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_redacted_stars_not_flagged(self):
        """***REDACTED*** should not be flagged"""
        artifact = 'secret = "***REDACTED***"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_changeme_not_flagged(self):
        """CHANGEME placeholder should not be flagged"""
        artifact = 'password = "CHANGEME"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_xxx_placeholder_not_flagged(self):
        """xxx placeholders should not be flagged"""
        artifact = 'token = "xxxx"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_dummy_value_not_flagged(self):
        """dummy_xxx values should not be flagged"""
        artifact = 'api_key = "dummy_key_for_testing"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    def test_real_secret_still_detected(self):
        """Real secrets should still be caught"""
        artifact = 'password = "P@ssw0rd!2024"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False

    def test_real_api_key_still_detected(self):
        """Real API keys should still be caught"""
        artifact = "secret = 'ghp_1234567890abcdefABCDEF'"
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False

    def test_is_placeholder_helper(self):
        """Test _is_placeholder directly"""
        assert self.evaluator._is_placeholder("${DB_PASSWORD}") is True
        assert self.evaluator._is_placeholder("YOUR_API_KEY_HERE") is True
        assert self.evaluator._is_placeholder("<your-secret>") is True
        assert self.evaluator._is_placeholder("***") is True
        assert self.evaluator._is_placeholder("CHANGEME") is True
        assert self.evaluator._is_placeholder("real_password_123") is False
        assert self.evaluator._is_placeholder("sk-abc123def456") is False


class TestEvaluatorDocumentation:
    """Test documentation-related check methods"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_check_title_present(self):
        """Test artifact with title"""
        artifact = "# My Project\n\nSome content"

        passed, reason = self.evaluator._check_title(artifact, artifact.lower())

        assert passed is True

    def test_check_title_missing(self):
        """Test artifact without title"""
        artifact = "No title here\n\nJust content"

        passed, reason = self.evaluator._check_title(artifact, artifact.lower())

        assert passed is False

    def test_check_purpose_present(self):
        """Test artifact with purpose section"""
        artifact = "# My Project\n\n## Purpose\nThis project does X."

        passed, reason = self.evaluator._check_purpose(artifact, artifact.lower())

        assert passed is True

    def test_check_installation_present(self):
        """Test artifact with installation instructions"""
        artifact = "## Installation\n\n```\nnpm install my-package\n```"

        passed, reason = self.evaluator._check_installation(artifact, artifact.lower())

        assert passed is True

    def test_check_usage_present(self):
        """Test artifact with usage examples"""
        artifact = """
## Usage

```python
from mypackage import hello
hello()
```
"""
        passed, reason = self.evaluator._check_usage(artifact, artifact.lower())

        assert passed is True


class TestEvaluatorErrorHandling:
    """Test error handling-related check methods"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_error_handling_present(self):
        """Test code with error handling"""
        artifact = """
try:
    do_something()
except Exception as e:
    raise ValueError(f"Error: {e}")
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_no_error_handling(self):
        """Test code without error handling"""
        artifact = """
def hello():
    print("hello")
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )

        assert passed is False


class TestEvaluatorInputValidation:
    """Test input validation check method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_input_validation_present(self):
        """Test code with input validation"""
        artifact = """
def process(data):
    validate(data)
    return sanitize(data)
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_no_input_validation(self):
        """Test code without input validation"""
        artifact = """
def process(data):
    return data
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )

        assert passed is False


class TestEvaluatorReadability:
    """Test readability check method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_has_python_comments(self):
        """Test code with Python comments"""
        artifact = "# This is a comment\nx = 5"

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is True

    def test_has_docstrings(self):
        """Test code with docstrings"""
        artifact = '''
def hello():
    """Say hello."""
    print("hello")
'''
        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is True

    def test_has_js_comments(self):
        """Test code with JavaScript comments"""
        artifact = "// This is a comment\nconst x = 5;"

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is True

    def test_no_comments(self):
        """Test code without comments"""
        artifact = "x = 5\ny = 10"

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is False


class TestEvaluatorStructure:
    """Test structure check method"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_has_class_definition(self):
        """Test code with class definition"""
        artifact = "class MyClass:\n    pass"

        passed, reason = self.evaluator._check_structure(artifact, artifact.lower())

        assert passed is True

    def test_has_function_definition(self):
        """Test code with function definition"""
        artifact = "def my_function():\n    pass"

        passed, reason = self.evaluator._check_structure(artifact, artifact.lower())

        assert passed is True

    def test_no_structure(self):
        """Test code without structure definitions"""
        artifact = "x = 5\nprint(x)"

        passed, reason = self.evaluator._check_structure(artifact, artifact.lower())

        assert passed is False


class TestEvaluatorCategoryBreakdown:
    """Test category breakdown generation"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_category_breakdown_populated(self):
        """Test that category breakdown is populated"""
        artifact = """
# API Documentation

## GET /users
## POST /users
## PUT /users
## DELETE /users
"""

        criteria = self.rule_manager.load_criteria("api-spec")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result.category_breakdown is not None
        assert "categories" in result.category_breakdown
        assert "total_issues" in result.category_breakdown

    def test_category_scores_populated(self):
        """Test that category scores are populated"""
        artifact = "# Test Document\n\n## Purpose\nThis is a test."

        criteria = self.rule_manager.load_criteria("docs")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result.category_scores is not None
        assert isinstance(result.category_scores, dict)


class TestEvaluatorSeverityCounts:
    """Test severity count generation"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_severity_counts_populated(self):
        """Test that severity counts are populated"""
        artifact = "# Test"

        criteria = self.rule_manager.load_criteria("docs")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result.severity_counts is not None
        assert "critical" in result.severity_counts
        assert "high" in result.severity_counts
        assert "medium" in result.severity_counts
        assert "low" in result.severity_counts
        assert "info" in result.severity_counts


class TestEvaluatorCascadeProfiles:
    """Test cascade profile handling"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_cascade_profile_syntax_recognized(self):
        """Test that cascade profile syntax is recognized"""
        artifact = "# Test"
        criteria = self.rule_manager.load_criteria("api-spec")

        # Test with cascade syntax - should not crash
        result = self.evaluator.evaluate(
            artifact,
            criteria,
            "A",
            priority_profile="web+mobile",  # Cascade syntax
        )

        assert result is not None
        # Should fall back to default if cascade doesn't exist
        assert isinstance(result, EvaluationResult)

    def test_cascade_profile_basic(self):
        """Test cascade profile evaluation"""
        artifact = "# Test"
        criteria = self.rule_manager.load_criteria("api-spec")

        result = self.evaluator.evaluate(
            artifact,
            criteria,
            "A",
            priority_profile="web+mobile",
        )

        assert result is not None


class TestEvaluatorEdgeCases:
    """Test edge cases and error handling"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_empty_artifact(self):
        """Test evaluation of empty artifact"""
        artifact = ""
        criteria = self.rule_manager.load_criteria("docs")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None
        assert result.score < 1.0

    def test_whitespace_only_artifact(self):
        """Test evaluation of whitespace-only artifact"""
        artifact = "   \n\n   \t\t   \n   "
        criteria = self.rule_manager.load_criteria("docs")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None

    def test_very_long_artifact(self):
        """Test evaluation of very long artifact"""
        artifact = "# Test\n\n" + "Content line.\n" * 1000
        criteria = self.rule_manager.load_criteria("docs")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None
        assert 0.0 <= result.score <= 1.0

    def test_unicode_artifact(self):
        """Test evaluation of artifact with unicode characters"""
        artifact = "# Тест документ\n\nЭто тест с unicode символами: émojis 🎉"
        criteria = self.rule_manager.load_criteria("docs")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None

    def test_special_characters_in_artifact(self):
        """Test artifact with special characters"""
        artifact = """
# API

## GET /users?filter=name eq 'test'
Response: {"data": "<script>alert('xss')</script>"}
"""
        criteria = self.rule_manager.load_criteria("api-spec")

        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert result is not None

    def test_nonexistent_priority_profile(self):
        """Test with non-existent priority profile"""
        artifact = "# Test"
        criteria = self.rule_manager.load_criteria("docs")

        # Should fall back to default profile
        result = self.evaluator.evaluate(
            artifact,
            criteria,
            "A",
            priority_profile="nonexistent_profile_xyz",
        )

        assert result is not None

    def test_invalid_phase(self):
        """Test with invalid phase (should raise ValueError)"""
        artifact = "# Test"
        criteria = self.rule_manager.load_criteria("docs")

        with pytest.raises(ValueError):
            self.evaluator.evaluate(artifact, criteria, "C")

    def test_content_type_detection(self):
        """Test content type detection"""
        artifact = """
# API
Content-Type: application/json
Accept: text/html
"""
        passed, reason = self.evaluator._check_content_types(
            artifact, artifact.lower()
        )

        assert passed is True

    def test_parameters_detection(self):
        """Test parameters detection"""
        artifact = """
# API
## GET /users
Query params: page, limit
Body: user object
"""
        passed, reason = self.evaluator._check_parameters(artifact, artifact.lower())

        assert passed is True

    def test_responses_detection(self):
        """Test response schema detection"""
        artifact = """
# API
Response schema:
{
  "result": "success"
}
"""
        passed, reason = self.evaluator._check_responses(artifact, artifact.lower())

        assert passed is True


class TestEvaluatorIntegration:
    """Integration tests for Evaluator"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow"""
        artifact = """
# User API Documentation

## Overview
This API provides user management functionality.

## Authentication
Uses Bearer token authentication.

## Endpoints

### GET /users
List all users
Response: 200 OK

### POST /users
Create a new user
Response: 201 Created

### PUT /users/{id}
Update a user
Response: 200 OK

### DELETE /users/{id}
Delete a user
Response: 204 No Content

## Error Handling
400 Bad Request
404 Not Found
500 Internal Server Error
"""

        criteria = self.rule_manager.load_criteria("api-spec")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        # Verify result structure
        assert isinstance(result, EvaluationResult)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.passed, bool)
        assert result.phase == "A"
        assert isinstance(result.passed_rules, list)
        assert isinstance(result.failed_rules, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.category_breakdown, dict)
        assert isinstance(result.category_scores, dict)
        assert isinstance(result.severity_counts, dict)

    def test_docs_template_evaluation(self):
        """Test evaluation with docs template"""
        artifact = """
# My Project

## Purpose
This project demonstrates the quality evaluation system.

## Installation
```
pip install my-project
```

## Usage
```python
from my_project import main
main.run()
```
"""

        criteria = self.rule_manager.load_criteria("docs")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert isinstance(result, EvaluationResult)
        assert result.score > 0.5  # Should have reasonable score

    def test_code_gen_template_evaluation(self):
        """Test evaluation with code-gen template"""
        artifact = """
def calculate_sum(numbers: list[int]) -> int:
    \"\"\"Calculate the sum of numbers.\"\"\"
    total = 0
    try:
        for n in numbers:
            total += n
        return total
    except TypeError:
        raise ValueError("Invalid input")

# Tests
def test_calculate_sum():
    assert calculate_sum([1, 2, 3]) == 6
"""

        criteria = self.rule_manager.load_criteria("code-gen")
        result = self.evaluator.evaluate(artifact, criteria, "A")

        assert isinstance(result, EvaluationResult)
        # Should pass several checks
        assert len(result.passed_rules) > 0
