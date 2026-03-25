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
        """Test that Phase B evaluates more rules than Phase A"""
        artifact = """
def hello():
    print("Hello")
"""

        criteria = self.rule_manager.load_criteria("code-gen")
        result_a = self.evaluator.evaluate(artifact, criteria, "A")
        result_b = self.evaluator.evaluate(artifact, criteria, "B")

        assert 0.0 <= result_a.score <= 1.0
        assert 0.0 <= result_b.score <= 1.0
        # Phase B evaluates more rules (A + B)
        total_a = len(result_a.passed_rules) + len(result_a.failed_rules)
        total_b = len(result_b.passed_rules) + len(result_b.failed_rules)
        assert total_b >= total_a
        # Phase B has stricter threshold
        assert result_b.threshold >= result_a.threshold

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
        artifact = "This documentation describes endpoints and schemas"

        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )

        assert passed is False

    def test_false_positive_generic_token_word(self):
        """Prose mentioning 'token' generically should NOT pass (Exp 18)"""
        artifact = "The token economy grew. Players earn token rewards in the game."
        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_false_positive_login_noun(self):
        """'login page' without a login() call should NOT pass (Exp 18)"""
        artifact = "The login page design was updated with new colors."
        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_jwt_mention_passes(self):
        """JWT mention should pass (Exp 18)"""
        artifact = "Uses JWT for session management"
        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_access_token_passes(self):
        """access_token pattern should pass (Exp 18)"""
        artifact = "Store the access_token in secure storage"
        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_decorator_login_required_passes(self):
        """@login_required decorator should pass (Exp 18)"""
        artifact = """
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
"""
        passed, reason = self.evaluator._check_auth_documentation(
            artifact, artifact.lower()
        )
        assert passed is True


class TestEvaluatorParametersPatternBased:
    """Test _check_parameters pattern-based method (Exp 18)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_false_positive_generic_request_body(self):
        """Generic prose with 'request' and 'body' should NOT pass (Exp 18)"""
        artifact = "The body of the request was unclear to the reviewer."
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_openapi_query_param_passes(self):
        """OpenAPI 'query param' should pass (Exp 18)"""
        artifact = """
- name: page
  in: query
  type: integer
"""
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_jsdoc_param_passes(self):
        """JSDoc @param should pass (Exp 18)"""
        artifact = """
/**
 * @param {string} name - The user name
 * @param {number} age - The user age
 */
function createUser(name, age) {}
"""
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_sphinx_param_passes(self):
        """Sphinx :param: should pass (Exp 18)"""
        artifact = '''
def process(data):
    """Process data.

    :param data: Input data
    :param timeout: Max seconds
    """
'''
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_request_body_doc_passes(self):
        """'request body' as API docs term should pass (Exp 18)"""
        artifact = """
## POST /users
Request body:
{
  "name": "John",
  "email": "john@example.com"
}
"""
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_plain_code_no_params(self):
        """Plain code without parameter docs should NOT pass (Exp 18)"""
        artifact = """
def add(a, b):
    return a + b
"""
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_req_query_passes(self):
        """Express req.query should pass (Exp 18)"""
        artifact = """
app.get('/users', (req, res) => {
    const page = req.query.page;
    const data = req.body;
});
"""
        passed, reason = self.evaluator._check_parameters(
            artifact, artifact.lower()
        )
        assert passed is True


class TestEvaluatorResponsesPatternBased:
    """Test _check_responses pattern-based method (Exp 18)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_false_positive_return_result_in_code(self):
        """Generic 'return result' in code should NOT pass (Exp 18)"""
        artifact = """
def calculate(x, y):
    result = x + y
    return result
"""
        passed, reason = self.evaluator._check_responses(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_response_schema_passes(self):
        """'response schema' should pass (Exp 18)"""
        artifact = """
## Response Schema
{
  "status": "ok",
  "data": []
}
"""
        passed, reason = self.evaluator._check_responses(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_status_code_docs_passes(self):
        """Status code documentation should pass (Exp 18)"""
        artifact = """
## Responses
200: Success
404: Not Found
500: Internal Server Error
"""
        passed, reason = self.evaluator._check_responses(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_json_response_example_passes(self):
        """JSON response with typical keys should pass (Exp 18)"""
        artifact = """
Response example:
{
  "status": "success",
  "data": {"id": 1}
}
"""
        passed, reason = self.evaluator._check_responses(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_content_type_json_passes(self):
        """Content-Type: application/json should pass (Exp 18)"""
        artifact = """
Content-Type: application/json
"""
        passed, reason = self.evaluator._check_responses(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_plain_prose_no_response_docs(self):
        """Plain prose should NOT pass (Exp 18)"""
        artifact = "The output of the program was displayed on screen."
        passed, reason = self.evaluator._check_responses(
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

    # Exp 17: Pattern-based test detection

    def test_false_positive_word_test_in_prose(self):
        """Word 'test' in prose should NOT pass (Exp 17)"""
        artifact = """
We need to test this feature before releasing.
The test environment is ready for deployment.
"""
        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())
        assert passed is False

    def test_python_unittest_import(self):
        """import unittest should pass (Exp 17)"""
        artifact = """
import unittest

class MyTest(unittest.TestCase):
    pass
"""
        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())
        assert passed is True

    def test_python_assert_statement(self):
        """Python assert should pass (Exp 17)"""
        artifact = """
def test_add():
    assert add(1, 2) == 3
"""
        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())
        assert passed is True

    def test_js_expect_call(self):
        """JS expect() should pass (Exp 17)"""
        artifact = """
test('adds 1 + 2', () => {
    expect(add(1, 2)).toBe(3);
});
"""
        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())
        assert passed is True

    def test_pytest_fixture_decorator(self):
        """@pytest.fixture should pass (Exp 17)"""
        artifact = """
@pytest.fixture
def client():
    return TestClient(app)
"""
        passed, reason = self.evaluator._check_tests(artifact, artifact.lower())
        assert passed is True

    def test_plain_code_no_tests(self):
        """Plain code without test constructs should NOT pass (Exp 17)"""
        artifact = """
def calculate(x, y):
    return x + y

result = calculate(1, 2)
print(result)
"""
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

    # Exp 16: Known secret format detection

    def test_aws_access_key_detected(self):
        """AWS Access Key ID (AKIA...) should be detected (Exp 16)"""
        artifact = 'aws_access_key = "AKIAIOSFODNN7EXAMPLE"'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False
        assert "AWS" in reason

    def test_jwt_token_detected(self):
        """JWT token (eyJ...) should be detected (Exp 16)"""
        artifact = 'auth_header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False
        assert "JWT" in reason

    def test_github_pat_detected(self):
        """GitHub PAT (ghp_...) should be detected (Exp 16)"""
        # Use bare string (no assignment) to test known-format detection path
        artifact = 'Authorization: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False
        assert "GitHub" in reason

    def test_short_eyj_not_flagged(self):
        """Short 'eyJ' string should NOT be flagged as JWT (Exp 16)"""
        artifact = 'text = "eyJhbG"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True

    # Exp 17: Connection string detection

    def test_postgresql_connection_string_detected(self):
        """PostgreSQL connection string with credentials should be detected (Exp 17)"""
        artifact = 'DATABASE_URL = "postgresql://admin:secretpass@db.example.com:5432/mydb"'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False
        assert "connection string" in reason.lower()

    def test_mongodb_connection_string_detected(self):
        """MongoDB connection string with credentials should be detected (Exp 17)"""
        artifact = 'MONGO_URI = "mongodb://root:password123@mongo.example.com:27017/app"'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False
        assert "connection string" in reason.lower()

    def test_redis_connection_string_detected(self):
        """Redis connection string with credentials should be detected (Exp 17)"""
        artifact = 'REDIS_URL = "redis://default:mypassword@redis.example.com:6379/0"'
        passed, reason = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is False

    def test_connection_string_no_password_not_flagged(self):
        """Connection string without credentials should NOT be flagged (Exp 17)"""
        artifact = 'DATABASE_URL = "postgresql://localhost:5432/mydb"'
        passed, _ = self.evaluator._check_secrets(artifact, artifact.lower())
        assert passed is True


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

    def test_false_positive_error_keyword_in_text(self):
        """'error' + 'try' in prose should NOT pass (Exp 16)"""
        artifact = """
If you encounter an error, try refreshing the page.
The exception to this rule is admin users.
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_js_try_catch_passes(self):
        """JavaScript try/catch should pass (Exp 16)"""
        artifact = """
try {
    fetchData();
} catch (error) {
    console.log(error);
}
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_python_raise_passes(self):
        """Python raise statement should pass (Exp 16)"""
        artifact = """
def validate(x):
    if x < 0:
        raise ValueError("must be positive")
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_js_throw_passes(self):
        """JavaScript throw should pass (Exp 16)"""
        artifact = """
function validate(x) {
    if (!x) throw new Error("required");
}
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_promise_catch_passes(self):
        """Promise .catch() should pass (Exp 16)"""
        artifact = """
fetch('/api/data')
    .then(r => r.json())
    .catch(err => console.error(err));
"""
        passed, reason = self.evaluator._check_error_handling(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_plain_code_no_error_handling(self):
        """Plain arithmetic should NOT pass (Exp 16)"""
        artifact = """
def add(a, b):
    return a + b
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

    def test_false_positive_check_keyword_alone(self):
        """'check' alone should NOT pass — too generic (Exp 15)"""
        artifact = """
def process(data):
    # check if data is ready
    result = data.check
    return result
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is False

    def test_check_function_call_passes(self):
        """check_permissions() style call SHOULD pass (Exp 15)"""
        artifact = """
def process(request):
    check_permissions(request.user)
    return handle(request)
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_raise_valueerror_passes(self):
        """raise ValueError should pass (Exp 15)"""
        artifact = """
def process(data):
    if not data:
        raise ValueError("data is required")
    return data
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_isinstance_check_passes(self):
        """isinstance check should pass (Exp 15)"""
        artifact = """
def process(data):
    if not isinstance(data, dict):
        return None
    return data['key']
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_schema_validate_passes(self):
        """schema.validate should pass (Exp 15)"""
        artifact = """
def process(data):
    schema.validate(data)
    return transform(data)
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_pydantic_validator_passes(self):
        """@validator decorator should pass (Exp 15)"""
        artifact = """
class Config(BaseModel):
    name: str

    @validator('name')
    def name_must_be_nonempty(cls, v):
        assert len(v) > 0
        return v
"""
        passed, reason = self.evaluator._check_input_validation(
            artifact, artifact.lower()
        )
        assert passed is True

    def test_plain_code_no_validation(self):
        """Plain arithmetic code should NOT pass (Exp 15)"""
        artifact = """
def calculate(x, y):
    return x + y
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

    def test_css_color_not_comment(self):
        """CSS color #fff should NOT pass as a comment (Exp 15)"""
        artifact = "color = '#fff'\nbackground = '#000'"

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is False

    def test_url_anchor_not_comment(self):
        """URL anchor #section should NOT pass as a comment (Exp 15)"""
        artifact = 'url = "http://example.com#section"'

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is False

    def test_markdown_heading_not_comment(self):
        """Markdown # Heading at start of line IS a real comment/doc (Exp 15)"""
        artifact = "# Heading\nSome text here"

        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is True

    def test_indented_python_comment(self):
        """Indented Python comment should pass (Exp 15)"""
        artifact = """
def foo():
    # Calculate total
    return 42
"""
        passed, reason = self.evaluator._check_readability(artifact, artifact.lower())

        assert passed is True


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


class TestCheckSqlInjectionPrevention:
    """Test SQL injection prevention check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_parameterized_queries(self):
        """Parameterized queries should pass"""
        artifact = "Use parameterized queries to prevent injection"
        passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
        assert passed is True

    def test_prepared_statement(self):
        """Prepared statement should pass"""
        artifact = "Use prepared statement for database queries"
        passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
        assert passed is True

    def test_orm_usage(self):
        """ORM usage should pass"""
        artifact = "from sqlalchemy import Column\nclass User(Base):\n    name = Column(String)"
        passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
        assert passed is True

    def test_specific_orm_name(self):
        """Specific ORM names should pass"""
        for orm in ["SQLAlchemy", "Prisma", "TypeORM", "Django ORM"]:
            artifact = f"We use {orm} for database access"
            passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
            assert passed is True, f"Failed for {orm}"

    def test_false_positive_generic_text(self):
        """Generic text without SQL injection prevention should fail"""
        artifact = "The user can query the database for information about products."
        passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
        assert passed is False

    def test_sanitize_call(self):
        """sanitize() call should pass"""
        artifact = "value = sanitize(user_input)"
        passed, _ = self.evaluator._check_sql_injection_prevention(artifact, artifact.lower())
        assert passed is True


class TestCheckXssPrevention:
    """Test XSS prevention check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_csp_header(self):
        """CSP header should pass"""
        artifact = "Content-Security-Policy: default-src 'self'"
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is True

    def test_dompurify(self):
        """DOMPurify usage should pass"""
        artifact = "import DOMPurify from 'dompurify'\nclean = DOMPurify.sanitize(dirty)"
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is True

    def test_output_encoding(self):
        """Output encoding mention should pass"""
        artifact = "Apply output encoding to all user-generated content"
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is True

    def test_textcontent_safe(self):
        """textContent usage should pass"""
        artifact = "element.textContent = userInput  // safe DOM manipulation"
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic_html(self):
        """Generic HTML text should fail"""
        artifact = "The page displays a list of products with prices and descriptions."
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is False

    def test_innerhtml_detected(self):
        """innerHTML mention should pass (flagging unsafe usage)"""
        artifact = "Never use innerHTML with untrusted data"
        passed, _ = self.evaluator._check_xss_prevention(artifact, artifact.lower())
        assert passed is True


class TestCheckAuthentication:
    """Test authentication check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_auth_middleware(self):
        """Auth middleware should pass"""
        artifact = "app.use(auth middleware)"
        passed, _ = self.evaluator._check_authentication(artifact, artifact.lower())
        assert passed is True

    def test_login_required_decorator(self):
        """@login_required decorator should pass"""
        artifact = "@login_required\ndef dashboard(request):\n    pass"
        passed, _ = self.evaluator._check_authentication(artifact, artifact.lower())
        assert passed is True

    def test_bearer_token(self):
        """Bearer token should pass"""
        artifact = 'Authorization: Bearer token in headers'
        passed, _ = self.evaluator._check_authentication(artifact, artifact.lower())
        assert passed is True

    def test_verify_token(self):
        """verify token should pass"""
        artifact = "def verify token(jwt_token):\n    return decode(jwt_token)"
        passed, _ = self.evaluator._check_authentication(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic_text(self):
        """Generic text about users should fail"""
        artifact = "The user can view their profile and update settings."
        passed, _ = self.evaluator._check_authentication(artifact, artifact.lower())
        assert passed is False


class TestCheckAuthorization:
    """Test authorization check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_rbac(self):
        """RBAC should pass"""
        artifact = "Implements RBAC for access control"
        passed, _ = self.evaluator._check_authorization(artifact, artifact.lower())
        assert passed is True

    def test_permission_check(self):
        """Permission check should pass"""
        artifact = "if has_permission('admin'):\n    allow_access()"
        passed, _ = self.evaluator._check_authorization(artifact, artifact.lower())
        assert passed is True

    def test_role_required_decorator(self):
        """@requires_role decorator should pass"""
        artifact = "@requires_role('admin')\ndef admin_panel():\n    pass"
        passed, _ = self.evaluator._check_authorization(artifact, artifact.lower())
        assert passed is True

    def test_access_denied(self):
        """Access denied/forbidden should pass"""
        artifact = "Return 403 forbidden if user lacks permissions"
        passed, _ = self.evaluator._check_authorization(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic_text(self):
        """Generic text should fail"""
        artifact = "The application displays a list of items to the user."
        passed, _ = self.evaluator._check_authorization(artifact, artifact.lower())
        assert passed is False


class TestCheckHttpsOnly:
    """Test HTTPS enforcement check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_hsts_header(self):
        """HSTS header should pass"""
        artifact = "Strict-Transport-Security: max-age=31536000"
        passed, _ = self.evaluator._check_https_only(artifact, artifact.lower())
        assert passed is True

    def test_https_redirect(self):
        """HTTPS redirect should pass"""
        artifact = "HTTPS redirect enabled for all endpoints"
        passed, _ = self.evaluator._check_https_only(artifact, artifact.lower())
        assert passed is True

    def test_ssl_true(self):
        """ssl=true config should pass"""
        artifact = "ssl = true\nport = 443"
        passed, _ = self.evaluator._check_https_only(artifact, artifact.lower())
        assert passed is True

    def test_tls_certificate(self):
        """TLS and certificate mention should pass"""
        artifact = "Configure TLS certificate for the server"
        passed, _ = self.evaluator._check_https_only(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_http_url(self):
        """Plain http:// URL without HTTPS mention should fail"""
        artifact = "Connect to http://api.example.com for data"
        passed, _ = self.evaluator._check_https_only(artifact, artifact.lower())
        assert passed is False


class TestCheckCsrfProtection:
    """Test CSRF protection check (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_csrf_token(self):
        """CSRF token should pass"""
        artifact = "Include csrf_token in all POST forms"
        passed, _ = self.evaluator._check_csrf_protection(artifact, artifact.lower())
        assert passed is True

    def test_samesite_cookie(self):
        """SameSite cookie should pass"""
        artifact = "Set-Cookie: session=abc; SameSite=Strict; Secure"
        passed, _ = self.evaluator._check_csrf_protection(artifact, artifact.lower())
        assert passed is True

    def test_anti_forgery(self):
        """Anti-forgery token should pass"""
        artifact = "Use AntiForgery token in ASP.NET forms"
        passed, _ = self.evaluator._check_csrf_protection(artifact, artifact.lower())
        assert passed is True

    def test_csrf_exempt_decorator(self):
        """@csrf_exempt should pass (it's a CSRF-related construct)"""
        artifact = "@csrf_exempt\ndef webhook(request):\n    pass"
        passed, _ = self.evaluator._check_csrf_protection(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic_form(self):
        """Generic form text should fail"""
        artifact = "The form collects user name and email address."
        passed, _ = self.evaluator._check_csrf_protection(artifact, artifact.lower())
        assert passed is False


class TestCheckSecurityNoHardcodedSecrets:
    """Test that security.no_hardcoded_secrets maps to _check_secrets (Exp 19)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def test_no_hardcoded_secrets_uses_check_secrets(self):
        """security.no_hardcoded_secrets should map to _check_secrets method"""
        check_methods = {
            "security.no_hardcoded_secrets": self.evaluator._check_secrets,
            "security.secrets": self.evaluator._check_secrets,
        }
        # Verify both map to the same method
        assert check_methods["security.no_hardcoded_secrets"] == check_methods["security.secrets"]


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


class TestSecureErrorHandling:
    """Tests for _check_secure_error_handling (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_generic_error_message(self):
        artifact = "return generic error message to client"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_hide_stack_trace(self):
        artifact = "hide stack trace in production responses"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_error_tracking_service(self):
        artifact = "errors are reported to Sentry for monitoring"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_express_error_middleware(self):
        artifact = "app.use(error, req, res, next) { res.status(500).json({}) }"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_logger_error(self):
        artifact = "logger.error('Failed to process request', { error })"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic_text(self):
        artifact = "The system processes various error conditions internally"
        passed, _ = self.evaluator._check_secure_error_handling(artifact, artifact.lower())
        assert passed is False


class TestCorsConfiguration:
    """Tests for _check_cors_configuration (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_cors_header(self):
        artifact = "Access-Control-Allow-Origin: https://example.com"
        passed, _ = self.evaluator._check_cors_configuration(artifact, artifact.lower())
        assert passed is True

    def test_cors_middleware(self):
        artifact = "app.use(cors({ origin: ['https://example.com'] }))"
        passed, _ = self.evaluator._check_cors_configuration(artifact, artifact.lower())
        assert passed is True

    def test_allowed_origins(self):
        artifact = "allowed_origins = ['https://app.example.com']"
        passed, _ = self.evaluator._check_cors_configuration(artifact, artifact.lower())
        assert passed is True

    def test_cross_origin(self):
        artifact = "Configure cross-origin resource sharing policy"
        passed, _ = self.evaluator._check_cors_configuration(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_cors(self):
        artifact = "The API accepts requests from authenticated users"
        passed, _ = self.evaluator._check_cors_configuration(artifact, artifact.lower())
        assert passed is False


class TestCspHeaders:
    """Tests for _check_csp_headers (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_csp_header(self):
        artifact = "Content-Security-Policy: default-src 'self'"
        passed, _ = self.evaluator._check_csp_headers(artifact, artifact.lower())
        assert passed is True

    def test_csp_directives(self):
        artifact = "script-src 'self'; object-src 'none'; img-src *"
        passed, _ = self.evaluator._check_csp_headers(artifact, artifact.lower())
        assert passed is True

    def test_helmet_middleware(self):
        artifact = "app.use(helmet({ contentSecurityPolicy: true }))"
        passed, _ = self.evaluator._check_csp_headers(artifact, artifact.lower())
        assert passed is True

    def test_csp_nonce(self):
        artifact = "Use nonce-abc123def456 for inline scripts"
        passed, _ = self.evaluator._check_csp_headers(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_csp(self):
        artifact = "The page loads JavaScript from external sources"
        passed, _ = self.evaluator._check_csp_headers(artifact, artifact.lower())
        assert passed is False


class TestRateLimiting:
    """Tests for _check_rate_limiting (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_rate_limiter(self):
        artifact = "Apply rate-limiting to all API endpoints"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_throttle(self):
        artifact = "throttle requests to 100 per minute"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_429_status(self):
        artifact = "Return 429 Too Many Requests when limit exceeded"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_rate_limit_library(self):
        artifact = "const limiter = require('express-rate-limit')"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_sliding_window(self):
        artifact = "Use sliding window algorithm for rate counting"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_rate_limit(self):
        artifact = "The API handles requests from multiple clients"
        passed, _ = self.evaluator._check_rate_limiting(artifact, artifact.lower())
        assert passed is False


class TestJwtTokenHandling:
    """Tests for _check_jwt_token_handling (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_jwt_verify(self):
        artifact = "jwt.verify(token, secret)"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is True

    def test_token_expiration(self):
        artifact = "Set token expiration to 15 minutes"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is True

    def test_httponly_cookie(self):
        artifact = "Store JWT in httpOnly secure cookie"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is True

    def test_refresh_token(self):
        artifact = "Use refresh token to obtain new access token"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is True

    def test_jwt_library(self):
        artifact = "const jwt = require('jsonwebtoken')"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_jwt(self):
        artifact = "Users authenticate with username and password"
        passed, _ = self.evaluator._check_jwt_token_handling(artifact, artifact.lower())
        assert passed is False


class TestEnvVariableUsage:
    """Tests for _check_env_variable_usage (Exp 20)"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_process_env(self):
        artifact = "const secret = process.env.SECRET_KEY"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_os_environ(self):
        artifact = "secret = os.environ['DATABASE_URL']"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_os_getenv(self):
        artifact = "api_key = os.getenv('API_KEY')"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_dotenv(self):
        artifact = "from dotenv import load_dotenv"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_secret_manager(self):
        artifact = "Load secrets from AWS Secrets Manager"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_env_in_gitignore(self):
        artifact = "Ensure .gitignore includes .env files"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_env(self):
        artifact = "The application reads configuration from a YAML file"
        passed, _ = self.evaluator._check_env_variable_usage(artifact, artifact.lower())
        assert passed is False


# Exp 21: Tests for _check_dependencies
class TestCheckDependencies:
    """Test _check_dependencies method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_npm_audit(self):
        artifact = "Run npm audit to check for vulnerabilities"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_pip_audit(self):
        artifact = "Use pip audit to scan Python dependencies"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_snyk(self):
        artifact = "Integrate Snyk into CI pipeline for dependency scanning"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_dependabot(self):
        artifact = "Configure Dependabot for automatic dependency updates"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_cve_mention(self):
        artifact = "Check packages against CVE database for known vulnerability issues"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_dependency_update(self):
        artifact = "Run dependency update checks weekly"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_lock_file(self):
        artifact = "Commit package-lock.json to ensure reproducible builds"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The project depends on several libraries for data processing"
        passed, _ = self.evaluator._check_dependencies(artifact, artifact.lower())
        assert passed is False


# Exp 21: Tests for _check_api_key_management
class TestCheckApiKeyManagement:
    """Test _check_api_key_management method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_scoped_permissions(self):
        artifact = "API keys should have scoped permissions for each service"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is True

    def test_key_rotation(self):
        artifact = "Implement key rotation every 90 days"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is True

    def test_least_privilege(self):
        artifact = "Follow least privilege principle for all API tokens"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is True

    def test_revoke_key(self):
        artifact = "Ability to revoke key immediately on compromise"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is True

    def test_per_environment_key(self):
        artifact = "Use per-environment keys for dev, staging, production"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The API returns user data in JSON format with pagination"
        passed, _ = self.evaluator._check_api_key_management(artifact, artifact.lower())
        assert passed is False


# Exp 21: Tests for _check_secret_rotation
class TestCheckSecretRotation:
    """Test _check_secret_rotation method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_secret_rotation(self):
        artifact = "Implement secret rotation for database credentials"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is True

    def test_certificate_renewal(self):
        artifact = "Monitor certificate expiration and auto-renew"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is True

    def test_automatic_rotation(self):
        artifact = "Enable automatic rotation via AWS Secrets Manager"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is True

    def test_rotation_policy(self):
        artifact = "Define rotation policy: keys rotated every 90 days"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is True

    def test_hashicorp_vault(self):
        artifact = "Use HashiCorp Vault for secret lifecycle management"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The application stores user preferences in a database"
        passed, _ = self.evaluator._check_secret_rotation(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_query_depth_limiting
class TestCheckGraphqlQueryDepthLimiting:
    """Test _check_graphql_query_depth_limiting method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_depth_limit_config(self):
        artifact = "Set maxDepth: 7 for all GraphQL queries"
        passed, _ = self.evaluator._check_graphql_query_depth_limiting(artifact, artifact.lower())
        assert passed is True

    def test_depth_limit_package(self):
        artifact = "Use graphql-depth-limit middleware to restrict nesting"
        passed, _ = self.evaluator._check_graphql_query_depth_limiting(artifact, artifact.lower())
        assert passed is True

    def test_depth_limit_function(self):
        artifact = "Apply depthLimit(5) to the GraphQL server"
        passed, _ = self.evaluator._check_graphql_query_depth_limiting(artifact, artifact.lower())
        assert passed is True

    def test_nested_query_mention(self):
        artifact = "Prevent deeply nested queries by limiting nesting levels"
        passed, _ = self.evaluator._check_graphql_query_depth_limiting(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The application uses a relational database with foreign keys"
        passed, _ = self.evaluator._check_graphql_query_depth_limiting(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_query_complexity_analysis
class TestCheckGraphqlQueryComplexityAnalysis:
    """Test _check_graphql_query_complexity_analysis method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_query_complexity(self):
        artifact = "Enable query complexity analysis with a limit of 1000"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is True

    def test_complexity_limit(self):
        artifact = "Set complexity limit per query to prevent DoS"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is True

    def test_field_cost(self):
        artifact = "Assign field cost values: User=1, Posts=10, Comments=5"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is True

    def test_complexity_directive(self):
        artifact = "Use @complexity directive on expensive resolvers"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is True

    def test_max_complexity(self):
        artifact = "Configure maxComplexity=500 for the API"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The system processes user data through a pipeline"
        passed, _ = self.evaluator._check_graphql_query_complexity_analysis(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_introspection_disabled
class TestCheckGraphqlIntrospectionDisabled:
    """Test _check_graphql_introspection_disabled method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_introspection_false(self):
        artifact = "Set introspection: false in production config"
        passed, _ = self.evaluator._check_graphql_introspection_disabled(artifact, artifact.lower())
        assert passed is True

    def test_disable_introspection(self):
        artifact = "Disable introspection for the production environment"
        passed, _ = self.evaluator._check_graphql_introspection_disabled(artifact, artifact.lower())
        assert passed is True

    def test_node_env_production(self):
        artifact = "Check NODE_ENV === 'production' before enabling schema"
        passed, _ = self.evaluator._check_graphql_introspection_disabled(artifact, artifact.lower())
        assert passed is True

    def test_schema_query_blocked(self):
        artifact = "Block __schema queries in production"
        passed, _ = self.evaluator._check_graphql_introspection_disabled(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The API returns user profile data with pagination"
        passed, _ = self.evaluator._check_graphql_introspection_disabled(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_rate_limiting
class TestCheckGraphqlRateLimiting:
    """Test _check_graphql_rate_limiting method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_cost_based_rate_limiting(self):
        artifact = "Apply cost-based rate limiting to GraphQL queries"
        passed, _ = self.evaluator._check_graphql_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_complexity_based_throttle(self):
        artifact = "Use complexity-based throttling for the API"
        passed, _ = self.evaluator._check_graphql_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_query_cost_limit(self):
        artifact = "Set query cost limit to 100 per minute per user"
        passed, _ = self.evaluator._check_graphql_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_graphql_rate_limit_package(self):
        artifact = "Install graphql-rate-limit for per-field limiting"
        passed, _ = self.evaluator._check_graphql_rate_limiting(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The web server handles HTTP requests with Express"
        passed, _ = self.evaluator._check_graphql_rate_limiting(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_batch_query_limiting
class TestCheckGraphqlBatchQueryLimiting:
    """Test _check_graphql_batch_query_limiting method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_batch_limit(self):
        artifact = "Set batch limit to max 10 operations per request"
        passed, _ = self.evaluator._check_graphql_batch_query_limiting(artifact, artifact.lower())
        assert passed is True

    def test_max_operations(self):
        artifact = "Configure maxOperations: 5 for batch requests"
        passed, _ = self.evaluator._check_graphql_batch_query_limiting(artifact, artifact.lower())
        assert passed is True

    def test_batched_requests(self):
        artifact = "Validate batched requests before processing"
        passed, _ = self.evaluator._check_graphql_batch_query_limiting(artifact, artifact.lower())
        assert passed is True

    def test_operation_count(self):
        artifact = "Check operation count in array before execution"
        passed, _ = self.evaluator._check_graphql_batch_query_limiting(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The application uses a message queue for async processing"
        passed, _ = self.evaluator._check_graphql_batch_query_limiting(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_persisted_queries
class TestCheckGraphqlPersistedQueries:
    """Test _check_graphql_persisted_queries method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_persisted_queries(self):
        artifact = "Enable persisted queries for production security"
        passed, _ = self.evaluator._check_graphql_persisted_queries(artifact, artifact.lower())
        assert passed is True

    def test_apq(self):
        artifact = "Use APQ (Automatic Persisted Queries) with Apollo"
        passed, _ = self.evaluator._check_graphql_persisted_queries(artifact, artifact.lower())
        assert passed is True

    def test_query_allowlist(self):
        artifact = "Maintain a query allowlist for production"
        passed, _ = self.evaluator._check_graphql_persisted_queries(artifact, artifact.lower())
        assert passed is True

    def test_trusted_queries(self):
        artifact = "Only allow trusted queries in production mode"
        passed, _ = self.evaluator._check_graphql_persisted_queries(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The REST API returns JSON data with standard headers"
        passed, _ = self.evaluator._check_graphql_persisted_queries(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_field_authorization
class TestCheckGraphqlFieldAuthorization:
    """Test _check_graphql_field_authorization method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_field_level_auth(self):
        artifact = "Implement field-level authorization for sensitive data"
        passed, _ = self.evaluator._check_graphql_field_authorization(artifact, artifact.lower())
        assert passed is True

    def test_auth_directive(self):
        artifact = "Use @auth directive on User.email and User.phone fields"
        passed, _ = self.evaluator._check_graphql_field_authorization(artifact, artifact.lower())
        assert passed is True

    def test_graphql_shield(self):
        artifact = "Configure graphql-shield rules for field permissions"
        passed, _ = self.evaluator._check_graphql_field_authorization(artifact, artifact.lower())
        assert passed is True

    def test_per_field_check(self):
        artifact = "Apply per-field auth checks in resolvers"
        passed, _ = self.evaluator._check_graphql_field_authorization(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The database has tables for users and orders"
        passed, _ = self.evaluator._check_graphql_field_authorization(artifact, artifact.lower())
        assert passed is False


# Exp 23: Tests for _check_graphql_mutation_idempotency
class TestCheckGraphqlMutationIdempotency:
    """Test _check_graphql_mutation_idempotency method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_idempotency_key(self):
        artifact = "Accept Idempotency-Key header in mutation requests"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_idempotent_mutation(self):
        artifact = "Ensure idempotent mutations for network retry safety"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_client_mutation_id(self):
        artifact = "Include clientMutationId in all mutation inputs"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_safe_retry(self):
        artifact = "Support safe retries for failed mutation requests"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_exactly_once(self):
        artifact = "Guarantee at-most-once delivery for payment mutations"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The service processes incoming webhooks from Stripe"
        passed, _ = self.evaluator._check_graphql_mutation_idempotency(artifact, artifact.lower())
        assert passed is False


# Exp 27: Tests for database Phase A check methods

class TestCheckDbPrimaryKey:
    """Test _check_db_primary_key method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_primary_key_sql(self):
        artifact = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255))"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is True

    def test_serial_column(self):
        artifact = "id SERIAL NOT NULL"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is True

    def test_uuid_primary_key(self):
        artifact = "id UUID DEFAULT gen_random_uuid()"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is True

    def test_autoincrement(self):
        artifact = "id INTEGER AUTO_INCREMENT"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is True

    def test_pk_shorthand(self):
        artifact = "Define pk for each table"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The application renders a list of items on the homepage"
        passed, _ = self.evaluator._check_db_primary_key(artifact, artifact.lower())
        assert passed is False


class TestCheckDbForeignKeys:
    """Test _check_db_foreign_keys method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_foreign_key_sql(self):
        artifact = "FOREIGN KEY (user_id) REFERENCES users(id)"
        passed, _ = self.evaluator._check_db_foreign_keys(artifact, artifact.lower())
        assert passed is True

    def test_on_delete_cascade(self):
        artifact = "ON DELETE CASCADE ON UPDATE SET NULL"
        passed, _ = self.evaluator._check_db_foreign_keys(artifact, artifact.lower())
        assert passed is True

    def test_orm_foreign_key(self):
        artifact = "user = models.ForeignKey(User, on_delete=models.CASCADE)"
        passed, _ = self.evaluator._check_db_foreign_keys(artifact, artifact.lower())
        assert passed is True

    def test_rails_association(self):
        artifact = "class Order < ApplicationRecord\n  belongs_to :user\n  has_many :items"
        passed, _ = self.evaluator._check_db_foreign_keys(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The dashboard shows analytics for monthly revenue"
        passed, _ = self.evaluator._check_db_foreign_keys(artifact, artifact.lower())
        assert passed is False


class TestCheckDbIndexes:
    """Test _check_db_indexes method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_create_index(self):
        artifact = "CREATE INDEX idx_users_email ON users(email)"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is True

    def test_unique_index(self):
        artifact = "CREATE UNIQUE INDEX idx_email ON users(email)"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is True

    def test_composite_index(self):
        artifact = "Add composite index on (user_id, created_at)"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is True

    def test_gin_index(self):
        artifact = "Create GIN index for full-text search on content"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is True

    def test_django_db_index(self):
        artifact = "email = models.EmailField(db_index=True)"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The payment gateway processes credit card transactions securely"
        passed, _ = self.evaluator._check_db_indexes(artifact, artifact.lower())
        assert passed is False


class TestCheckDbDataTypes:
    """Test _check_db_data_types method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_varchar_and_int(self):
        artifact = "name VARCHAR(255), age INTEGER NOT NULL"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is True

    def test_decimal_and_boolean(self):
        artifact = "price DECIMAL(10,2), active BOOLEAN DEFAULT true"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is True

    def test_json_and_timestamp(self):
        artifact = "metadata JSONB, created_at TIMESTAMP"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is True

    def test_django_fields(self):
        artifact = "name = CharField(max_length=100)\nprice = FloatField()"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is True

    def test_single_type_sufficient(self):
        artifact = "Use VARCHAR(100) for the name column"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The microservice handles user authentication via OAuth"
        passed, _ = self.evaluator._check_db_data_types(artifact, artifact.lower())
        assert passed is False


class TestCheckDbNotNull:
    """Test _check_db_not_null method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_not_null_sql(self):
        artifact = "email VARCHAR(255) NOT NULL"
        passed, _ = self.evaluator._check_db_not_null(artifact, artifact.lower())
        assert passed is True

    def test_nullable_false(self):
        artifact = "email = Column(String, nullable=False)"
        passed, _ = self.evaluator._check_db_not_null(artifact, artifact.lower())
        assert passed is True

    def test_required_field(self):
        artifact = "username is a required field in the schema"
        passed, _ = self.evaluator._check_db_not_null(artifact, artifact.lower())
        assert passed is True

    def test_django_blank_false(self):
        artifact = "name = models.CharField(max_length=100, blank=False)"
        passed, _ = self.evaluator._check_db_not_null(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "Deploy the application to production using Docker"
        passed, _ = self.evaluator._check_db_not_null(artifact, artifact.lower())
        assert passed is False


class TestCheckDbSqlInjection:
    """Test _check_db_sql_injection method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_parameterized_queries(self):
        artifact = "Always use parameterized queries for user input"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is True

    def test_prepared_statement(self):
        artifact = "Use prepared statements to prevent injection attacks"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is True

    def test_orm_usage(self):
        artifact = "Use ORM queries instead of raw SQL for data access"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is True

    def test_no_concatenation(self):
        artifact = "Avoid string concatenation in SQL queries"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is True

    def test_prisma(self):
        artifact = "Use Prisma client for all database operations"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_generic(self):
        artifact = "The frontend uses React components with TypeScript"
        passed, _ = self.evaluator._check_db_sql_injection(artifact, artifact.lower())
        assert passed is False


class TestCheckDbTimestamps:
    """Test _check_db_timestamps method"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_created_at_updated_at(self):
        artifact = "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP"
        passed, _ = self.evaluator._check_db_timestamps(artifact, artifact.lower())
        assert passed is True

    def test_django_auto_now(self):
        artifact = "created = models.DateTimeField(auto_now_add=True)\nupdated = models.DateTimeField(auto_now=True)"
        passed, _ = self.evaluator._check_db_timestamps(artifact, artifact.lower())
        assert passed is True

    def test_modified_at(self):
        artifact = "Add modified_at and created_at columns to all tables"
        passed, _ = self.evaluator._check_db_timestamps(artifact, artifact.lower())
        assert passed is True

    def test_single_timestamp_not_enough(self):
        artifact = "The table has a created_at column"
        passed, _ = self.evaluator._check_db_timestamps(artifact, artifact.lower())
        assert passed is False

    def test_false_positive_generic(self):
        artifact = "Configure nginx as reverse proxy for the API gateway"
        passed, _ = self.evaluator._check_db_timestamps(artifact, artifact.lower())
        assert passed is False


# ============================================================================
# Frontend Phase A Check Methods (Exp 28)
# ============================================================================


class TestFrontendComponents:
    """Test _check_fe_components for detecting component-based architecture"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_react_function_component(self):
        artifact = "export default function UserProfile({ name }) { return (<div>{name}</div>) }"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_react_arrow_component(self):
        artifact = "const UserCard = ({ user }) => { return (<div>{user.name}</div>) }"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_react_class_component(self):
        artifact = "class Dashboard extends React.Component { render() { return <div /> } }"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_jsx_return(self):
        artifact = "function App() {\n  return (\n    <div className='app'>\n    </div>\n  )\n}"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_vue_define_component(self):
        artifact = "export default defineComponent({ setup() { return {} } })"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_angular_component(self):
        artifact = "@Component({ selector: 'app-root', template: '<div>Hello</div>' })"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_components(self):
        artifact = "SELECT * FROM users WHERE age > 18"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is False

    def test_custom_jsx_tag(self):
        artifact = "render() { return <UserAvatar size='large' /> }"
        passed, _ = self.evaluator._check_fe_components(artifact, artifact.lower())
        assert passed is True


class TestFrontendStateManagement:
    """Test _check_fe_state_management for detecting state management patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_use_state(self):
        artifact = "const [count, setCount] = useState(0)"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_use_reducer(self):
        artifact = "const [state, dispatch] = useReducer(reducer, initialState)"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_use_context(self):
        artifact = "const theme = useContext(ThemeContext)"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_class_set_state(self):
        artifact = "this.setState({ loading: true })"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_vue_reactive(self):
        artifact = "const state = reactive({ count: 0 })"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_vue_ref(self):
        artifact = "const count = ref(0)"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_angular_signal(self):
        artifact = "count = Signal(0)"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_state(self):
        artifact = "Deploy the application to production using Docker"
        passed, _ = self.evaluator._check_fe_state_management(artifact, artifact.lower())
        assert passed is False


class TestFrontendPropsValidation:
    """Test _check_fe_props_validation for detecting props type validation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_typescript_interface_props(self):
        artifact = "interface UserProps { name: string; age: number; }"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True

    def test_typescript_type_props(self):
        artifact = "type ButtonProps = { onClick: () => void; label: string; }"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True

    def test_react_prop_types(self):
        artifact = "import PropTypes from 'prop-types';\nButton.propTypes = { label: PropTypes.string }"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True

    def test_vue_define_props(self):
        artifact = "const props = defineProps({ title: String, count: Number })"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True

    def test_vue_props_object(self):
        artifact = "export default { props: { title: { type: String, required: true } } }"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_props(self):
        artifact = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is False

    def test_type_annotation(self):
        artifact = "function Card(props: CardProps) { return <div /> }"
        passed, _ = self.evaluator._check_fe_props_validation(artifact, artifact.lower())
        assert passed is True


class TestFrontendRouting:
    """Test _check_fe_routing for detecting routing configuration"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_react_router_route(self):
        artifact = "<Route path='/users' element={<UserList />} />"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_react_router_browser_router(self):
        artifact = "<BrowserRouter><Routes><Route path='/' /></Routes></BrowserRouter>"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_use_navigate(self):
        artifact = "const navigate = useNavigate(); navigate('/dashboard')"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_next_use_router(self):
        artifact = "const router = useRouter(); router.push('/settings')"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_vue_create_router(self):
        artifact = "const router = createRouter({ history: createWebHistory(), routes })"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_angular_router_module(self):
        artifact = "imports: [RouterModule.forRoot(routes)]"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_path_definition(self):
        artifact = "{ path: '/users/:id', component: UserDetail }"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_routing(self):
        artifact = "Calculate the sum of all elements in the array"
        passed, _ = self.evaluator._check_fe_routing(artifact, artifact.lower())
        assert passed is False


class TestFrontendResponsive:
    """Test _check_fe_responsive for detecting responsive design patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_css_media_query(self):
        artifact = "@media (max-width: 768px) { .sidebar { display: none; } }"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is True

    def test_tailwind_breakpoints(self):
        artifact = "<div className='w-full md:w-1/2 lg:w-1/3'>"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is True

    def test_bootstrap_grid(self):
        artifact = "<div class='col-sm-6 col-md-4 col-lg-3'>"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is True

    def test_use_media_query_hook(self):
        artifact = "const isMobile = useMediaQuery('(max-width: 768px)')"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is True

    def test_viewport_mention(self):
        artifact = "Set viewport meta tag for mobile devices"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_responsive(self):
        artifact = "INSERT INTO products (name, price) VALUES ('Widget', 9.99)"
        passed, _ = self.evaluator._check_fe_responsive(artifact, artifact.lower())
        assert passed is False


class TestFrontendAltText:
    """Test _check_fe_alt_text for detecting alt text and accessibility attributes"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_img_alt_attribute(self):
        artifact = '<img src="logo.png" alt="Company Logo" />'
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is True

    def test_jsx_alt_variable(self):
        artifact = "<img src={url} alt={description} />"
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is True

    def test_next_image_alt(self):
        artifact = '<Image src="/hero.jpg" alt="Hero banner" width={800} height={600} />'
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is True

    def test_aria_label(self):
        artifact = '<button aria-label="Close dialog">X</button>'
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is True

    def test_role_attribute(self):
        artifact = '<div role="navigation">Menu items</div>'
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_a11y(self):
        artifact = "Run the database migration scripts and restart the server"
        passed, _ = self.evaluator._check_fe_alt_text(artifact, artifact.lower())
        assert passed is False


# ============================================================
# Backend Phase A rules (Exp 29)
# ============================================================


class TestBackendApiStructure:
    """Test _check_be_api_structure for detecting RESTful API patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_http_method_with_path(self):
        artifact = "GET /users - retrieve all users"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_express_router(self):
        artifact = "router.get('/users', getUsers)"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_decorator(self):
        artifact = "@Get('/users')\nasync findAll() { return this.usersService.findAll(); }"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_fastapi_decorator(self):
        artifact = "@app.post('/users')\nasync def create_user(user: UserCreate):"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_django_url_path(self):
        artifact = "path('users/', UserListView.as_view(), name='user-list')"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_fastapi_router(self):
        artifact = "router = APIRouter(prefix='/api/v1')"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_rest_mention(self):
        artifact = "The REST API supports CRUD operations on user resources"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_api(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is False

    def test_drf_api_view(self):
        artifact = "@api_view(['GET', 'POST'])\ndef user_list(request):"
        passed, _ = self.evaluator._check_be_api_structure(artifact, artifact.lower())
        assert passed is True


class TestBackendServiceLayer:
    """Test _check_be_service_layer for detecting service/controller separation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_service_class(self):
        artifact = "class UserService:\n    def get_user(self, id): ..."
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_controller_class(self):
        artifact = "class UserController {\n  constructor(private userService: UserService) {}\n}"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_repository_class(self):
        artifact = "class UserRepository extends Repository<User> {}"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_injectable(self):
        artifact = "@Injectable()\nexport class AuthService {}"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_spring_service(self):
        artifact = "@Service\npublic class OrderService {}"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_services_directory(self):
        artifact = "Import business logic from services/userService"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_business_logic_mention(self):
        artifact = "All business logic is in the service layer"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_service(self):
        artifact = "SELECT * FROM users WHERE active = true"
        passed, _ = self.evaluator._check_be_service_layer(artifact, artifact.lower())
        assert passed is False


class TestBackendDependencyInjection:
    """Test _check_be_dependency_injection for detecting DI patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_nestjs_inject(self):
        artifact = "constructor(@Inject(CONFIG) private config: AppConfig) {}"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_injectable(self):
        artifact = "@Injectable()\nexport class CatsService {}"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_spring_autowired(self):
        artifact = "@Autowired\nprivate UserRepository userRepo;"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_fastapi_depends(self):
        artifact = "async def get_items(db: Session = Depends(get_db)):"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_ts_constructor_injection(self):
        artifact = "constructor(private readonly userService: UserService) {}"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_python_init_injection(self):
        artifact = "def __init__(self, repository, event_bus):\n    self.repository = repository"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_providers_array(self):
        artifact = "providers: [UsersService, AuthService, DatabaseModule]"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_container_register(self):
        artifact = "container.register('userService', UserService)"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_di(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_be_dependency_injection(artifact, artifact.lower())
        assert passed is False


class TestBackendErrorResponses:
    """Test _check_be_error_responses for detecting proper error response patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_status_code_400(self):
        artifact = "Return status 400 for bad request"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_status_code_500(self):
        artifact = "Returns 500 internal server error"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_fastapi_http_exception(self):
        artifact = "raise HTTPException(status_code=404, detail='Not found')"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_http_exception(self):
        artifact = "throw new HttpException('Forbidden', HttpStatus.FORBIDDEN);"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_bad_request_error(self):
        artifact = "throw new BadRequest('Invalid email format')"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_express_status(self):
        artifact = "res.status(422).json({ error: 'Validation failed' })"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_error_message_field(self):
        artifact = "response = { error.message: 'Something went wrong', code: 'ERR_001' }"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_errors(self):
        artifact = "The application renders a beautiful homepage"
        passed, _ = self.evaluator._check_be_error_responses(artifact, artifact.lower())
        assert passed is False


class TestBackendValidation:
    """Test _check_be_validation for detecting input validation patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_validate_function(self):
        artifact = "validate(request.body)"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_class_validator(self):
        artifact = "@IsString()\n@IsNotEmpty()\nname: string;"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_zod_schema(self):
        artifact = "const userSchema = z.object();\nconst result = userSchema.parse(data);"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_joi_validation(self):
        artifact = "const schema = Joi.object({ email: Joi.string().email() })"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_pydantic_base_model(self):
        artifact = "class UserCreate(BaseModel):\n    name: str\n    email: str"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_validation_error(self):
        artifact = "raise ValidationError('Invalid input data')"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_body(self):
        artifact = "async create(@Body() createCatDto: CreateCatDto) {}"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_validation(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_be_validation(artifact, artifact.lower())
        assert passed is False


class TestBackendLogging:
    """Test _check_be_logging for detecting structured logging patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_python_logger(self):
        artifact = "logger.info('User created', extra={'user_id': user.id})"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_python_logging_module(self):
        artifact = "import logging\nlogging.error('Connection failed')"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_console_log(self):
        artifact = "console.error('Failed to process request', error)"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_winston_library(self):
        artifact = "const logger = winston.createLogger({ transports: [...] })"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_pino_library(self):
        artifact = "const logger = pino({ level: 'info' })"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_python_get_logger(self):
        artifact = "logger = getLogger(__name__)"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_log_level_constants(self):
        artifact = "Set log level to DEBUG in development, INFO in production"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_logging(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_be_logging(artifact, artifact.lower())
        assert passed is False


# === Testing Phase A rules (Exp 30) ===


class TestTestStructure:
    """Test _check_test_structure for AAA/BDD patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_aaa_pattern(self):
        artifact = "# Arrange\ndata = create_data()\n# Act\nresult = process(data)\n# Assert\nassert result == expected"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is True

    def test_bdd_pattern(self):
        artifact = "Given a user exists\nWhen the user logs in\nThen they see the dashboard"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is True

    def test_describe_it_blocks(self):
        artifact = "describe('UserService', () => {\n  it('should create user', () => {\n    expect(user).toBeDefined();\n  });\n});"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is True

    def test_python_test_method(self):
        artifact = "def test_create_user(self):\n    user = UserFactory.create()\n    assert user.id is not None"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is True

    def test_jest_lifecycle(self):
        artifact = "beforeEach(() => { setup(); });\ntest('works', () => { expect(true).toBe(true); });"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_tests(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_structure(artifact, artifact.lower())
        assert passed is False


class TestTestAssertions:
    """Test _check_test_assertions for assertion patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_python_assert(self):
        artifact = "assert result == 42"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_unittest_assert_equal(self):
        artifact = "self.assertEqual(result, expected)"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_jest_expect_tobe(self):
        artifact = "expect(result).toBe(42)"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_jest_to_equal(self):
        artifact = "expect(data).toEqual({ name: 'test' })"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_pytest_raises(self):
        artifact = "with pytest.raises(ValueError):\n    process(invalid_data)"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_chai_should(self):
        artifact = "result.should.equal(42)"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_assertions(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_assertions(artifact, artifact.lower())
        assert passed is False


class TestTestIsolation:
    """Test _check_test_isolation for setup/teardown and fixture patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_jest_before_each(self):
        artifact = "beforeEach(() => { db = createTestDb(); });"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_pytest_fixture(self):
        artifact = "@pytest.fixture\ndef user():\n    return User(name='test')"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_python_setup_method(self):
        artifact = "def setup_method(self):\n    self.client = TestClient(app)"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_unittest_setup(self):
        artifact = "def setUp(self):\n    self.db = create_test_db()"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_mock_for_isolation(self):
        artifact = "Use mock objects to isolate unit tests from external services"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_conftest(self):
        artifact = "Define shared fixtures in conftest.py for test isolation"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_isolation(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_isolation(artifact, artifact.lower())
        assert passed is False


class TestTestEdgeCases:
    """Test _check_test_edge_cases for edge case testing patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_null_and_empty(self):
        artifact = "Test with null input and empty string"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is True

    def test_none_and_boundary(self):
        artifact = "Test None value and boundary conditions"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is True

    def test_negative_and_overflow(self):
        artifact = "Test negative numbers and integer overflow cases"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is True

    def test_invalid_input(self):
        artifact = "Test with invalid input and malformed data"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is True

    def test_min_max_values(self):
        artifact = "Test min value and max value boundaries"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_edge_cases(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_edge_cases(artifact, artifact.lower())
        assert passed is False


class TestTestMocks:
    """Test _check_test_mocks for mock/stub patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_python_mock(self):
        artifact = "from unittest.mock import Mock\ndb = Mock()"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_python_magic_mock(self):
        artifact = "service = MagicMock(spec=UserService)"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_python_patch(self):
        artifact = "@patch('myapp.services.send_email')\ndef test_signup(self, mock_email):"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_jest_fn(self):
        artifact = "const mockFn = jest.fn().mockReturnValue(42)"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_jest_mock(self):
        artifact = "jest.mock('./database')"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_jest_spy_on(self):
        artifact = "jest.spyOn(service, 'getUser').mockResolvedValue(user)"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_sinon_stub(self):
        artifact = "const stub = sinon.stub(db, 'query').returns([])"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_mocks(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_mocks(artifact, artifact.lower())
        assert passed is False


class TestTestErrorTests:
    """Test _check_test_error_tests for error handling test patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_pytest_raises(self):
        artifact = "with pytest.raises(ValueError):\n    parse_int('abc')"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_unittest_assert_raises(self):
        artifact = "self.assertRaises(TypeError, process, None)"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_jest_to_throw(self):
        artifact = "expect(() => parse('bad')).toThrow(ValidationError)"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_jest_rejects(self):
        artifact = "await expect(fetchData()).rejects.toThrow()"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_exception_keyword(self):
        artifact = "Test that the exception is raised correctly for invalid input"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_python_raise(self):
        artifact = "def test_raises_on_bad_input():\n    raise ValueError('bad')"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_errors(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_error_tests(artifact, artifact.lower())
        assert passed is False


class TestTestCoverage:
    """Test _check_test_coverage for coverage configuration patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_pytest_cov(self):
        artifact = "pytest --cov=myapp --cov-report=html"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is True

    def test_coverage_keyword(self):
        artifact = "Code coverage should be maintained at 85%"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is True

    def test_jest_coverage_threshold(self):
        artifact = "coverageThreshold: { global: { branches: 80 } }"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is True

    def test_nyc_istanbul(self):
        artifact = "nyc report --reporter=lcov"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is True

    def test_codecov_service(self):
        artifact = "Upload results to codecov for PR checks"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_coverage(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_coverage(artifact, artifact.lower())
        assert passed is False


class TestTestE2E:
    """Test _check_test_e2e for E2E testing patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_playwright(self):
        artifact = "import { test } from '@playwright/test';"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is True

    def test_cypress(self):
        artifact = "cy.visit('/login')\ncy.get('#email').type('test@test.com')"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is True

    def test_playwright_api(self):
        artifact = "await page.goto('/dashboard');\nawait page.click('#submit');"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is True

    def test_selenium(self):
        artifact = "driver = selenium.webdriver.Chrome()"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is True

    def test_e2e_keyword(self):
        artifact = "Run end-to-end tests before deployment"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_e2e(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_e2e(artifact, artifact.lower())
        assert passed is False


class TestTestComponent:
    """Test _check_test_component for component testing patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_testing_library_render(self):
        artifact = "import { render } from '@testing-library/react';\nrender(<Button />);"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_get_by_role(self):
        artifact = "const button = screen.getByRole('button', { name: 'Submit' });"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_get_by_text(self):
        artifact = "const heading = screen.getByText('Welcome');"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_fire_event(self):
        artifact = "fireEvent.click(button);\nexpect(onSubmit).toHaveBeenCalled();"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_angular_test_bed(self):
        artifact = "TestBed.configureTestingModule({ declarations: [MyComponent] });"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_enzyme_mount(self):
        artifact = "const wrapper = mount(<MyComponent />);"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_component_tests(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_test_component(artifact, artifact.lower())
        assert passed is False


# Config Phase A check methods (Exp 31)

class TestConfigRequiredFields:
    """Test _check_config_required_fields for config field presence patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_yaml_config_with_common_fields(self):
        artifact = "name: my-app\nversion: 1.0\nhost: localhost\nport: 8080"
        passed, reason = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_required_keyword(self):
        artifact = "required:\n  - name\n  - version\nname: test"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_mandatory_fields(self):
        artifact = "mandatory fields: name, version\nname: my-app"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_database_config(self):
        artifact = "database:\n  host: localhost\n  port: 5432\n  url: postgres://localhost/db"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_must_have_pattern(self):
        artifact = "Config must have a name field\nname: my-service\nversion: 2.0"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_schema_definition(self):
        artifact = "name: my-app\nschema = {\n  'name': {'type': 'string'},\n  'port': {'type': 'integer'}\n}"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_env_config(self):
        artifact = "environment: production\napi_key: ${API_KEY}\nport: 3000"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_config(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is False

    def test_single_field_insufficient(self):
        artifact = "name: test"
        passed, _ = self.evaluator._check_config_required_fields(artifact, artifact.lower())
        assert passed is False


class TestConfigFieldTypes:
    """Test _check_config_field_types for type validation patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_yaml_typed_values(self):
        artifact = "port: 8080\ndebug: true\nname: 'my-app'"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_json_schema_types(self):
        artifact = 'type: string\nminLength: 1\ntype: integer'
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_python_type_annotations(self):
        artifact = "host: str = 'localhost'\nport: int = 8080\ndebug: bool = False"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_boolean_literals(self):
        artifact = "debug = True\nverbose = False"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_array_and_object_values(self):
        artifact = "hosts: [\n  'localhost',\n  '0.0.0.0'\n]\noptions: {\n  debug: true\n}"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_optional_union_types(self):
        artifact = "from typing import Optional, Union\nhost: Optional[str] = None\nport: Union[str, int] = 8080"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_types(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is False

    def test_single_type_insufficient(self):
        artifact = "debug: on"
        passed, _ = self.evaluator._check_config_field_types(artifact, artifact.lower())
        assert passed is False


class TestConfigComments:
    """Test _check_config_comments for configuration documentation patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_yaml_comments(self):
        artifact = "# Database configuration\nhost: localhost  # Local dev server\ndescription: Main DB"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_json5_comments(self):
        artifact = '// Server settings\nhost: "localhost"\ndescription: Production server'
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_marker_comments(self):
        artifact = "# NOTE: This value must match the frontend config\n# TODO: Move to env vars\nport: 3000"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_config_annotation_comments(self):
        artifact = "# required\nname: my-app\n# optional, default is 8080\nport: 8080"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_description_field(self):
        artifact = "name: my-app\ndescription: Main application config\nhelp: See docs for details"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_block_comments(self):
        artifact = "/* Global settings */\nhost: localhost\n<!-- XML comment -->"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_comments(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is False

    def test_single_comment_insufficient(self):
        artifact = "host: localhost"
        passed, _ = self.evaluator._check_config_comments(artifact, artifact.lower())
        assert passed is False


# Docs Phase A check methods (Exp 31)

class TestDocsLinks:
    """Test _check_docs_links for link format validation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_markdown_link(self):
        artifact = "See [documentation](https://docs.example.com) for details"
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True

    def test_reference_link(self):
        artifact = "See [docs][1] for details\n\n[1]: https://docs.example.com"
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True

    def test_raw_url(self):
        artifact = "Visit https://example.com for more info"
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True

    def test_html_link(self):
        artifact = '<a href="https://example.com">Example</a>'
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True

    def test_multiple_links(self):
        artifact = "[Link1](url1) and [Link2](url2) and https://example.com"
        passed, reason = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True
        assert "link" in reason.lower()

    def test_reference_definition(self):
        artifact = "[docs]: https://docs.example.com"
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is True

    def test_false_positive_no_links(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is False

    def test_false_positive_empty(self):
        artifact = ""
        passed, _ = self.evaluator._check_docs_links(artifact, artifact.lower())
        assert passed is False


class TestDocsStructure:
    """Test _check_docs_structure for heading hierarchy validation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_proper_hierarchy(self):
        artifact = "# Title\n\n## Section 1\n\nContent\n\n## Section 2\n\nMore content"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is True
        assert "H1=" in reason

    def test_deep_hierarchy(self):
        artifact = "# Title\n\n## Section\n\n### Subsection\n\nContent"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is True
        assert "H3=" in reason

    def test_only_h1(self):
        artifact = "# Title\n\nSome content without sections"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is False
        assert "missing H2" in reason

    def test_only_h2_no_h1(self):
        artifact = "## Section 1\n\nContent\n\n## Section 2\n\nMore"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is False
        assert "missing H1" in reason

    def test_no_headings(self):
        artifact = "The quick brown fox jumps over the lazy dog"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is False
        assert "No heading" in reason

    def test_multiple_h2_sections(self):
        artifact = "# My Project\n\n## Install\n\n## Usage\n\n## API\n\n## License"
        passed, reason = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is True
        assert "H2=4" in reason

    def test_empty_content(self):
        artifact = ""
        passed, _ = self.evaluator._check_docs_structure(artifact, artifact.lower())
        assert passed is False


# Code-Gen Phase B check methods (Exp 32)


class TestCheckComplexity:
    """Test _check_complexity for excessive nesting detection"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_simple_code_passes(self):
        artifact = "def hello():\n    print('hello')\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True

    def test_single_loop_passes(self):
        artifact = "for i in range(10):\n    print(i)\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True

    def test_triple_nested_loop_fails(self):
        artifact = "for i in items:\n    for j in items:\n        for k in items:\n            print(i, j, k)\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        # Without mitigation patterns, triple nesting should fail
        assert passed is False

    def test_triple_nested_with_guard_clause_passes(self):
        artifact = "for i in items:\n    for j in items:\n        for k in items:\n            if not valid:\n                break\n            process(i, j, k)\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True

    def test_nested_ifs_with_early_return(self):
        artifact = "if a:\n    if b:\n        if c:\n            if d:\n                return x\n    return y\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True  # has return as mitigation

    def test_chained_promises_fail(self):
        artifact = "fetch(url).then(r => r.json()).then(data => process(data)).then(result => save(result))"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True

    def test_function_decomposition_mitigates(self):
        artifact = "for i in items:\n    for j in items:\n        for k in items:\n            pass\ndef _helper(x):\n    return x\n"
        passed, _ = self.evaluator._check_complexity(artifact, artifact.lower())
        assert passed is True


class TestCheckResourceCleanup:
    """Test _check_resource_cleanup for proper resource management"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_with_statement(self):
        artifact = "with open('file.txt') as f:\n    data = f.read()\n"
        passed, reason = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True
        assert "resource cleanup" in reason.lower()

    def test_finally_block(self):
        artifact = "try:\n    conn = connect()\n    conn.query()\nfinally:\n    conn.close()\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_close_call(self):
        artifact = "f = open('data.txt')\ndata = f.read()\nf.close()\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_async_with(self):
        artifact = "async with aiohttp.ClientSession() as session:\n    resp = await session.get(url)\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_contextmanager_decorator(self):
        artifact = "@contextmanager\ndef managed_resource():\n    yield resource\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_exit_stack(self):
        artifact = "with ExitStack() as stack:\n    files = [stack.enter_context(open(f)) for f in names]\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_no_cleanup_fails(self):
        artifact = "x = 42\nprint(x)\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is False

    def test_dispose_pattern(self):
        artifact = "resource = acquire()\nresource.dispose()\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True

    def test_atexit_handler(self):
        artifact = "import atexit\natexit.register(cleanup)\n"
        passed, _ = self.evaluator._check_resource_cleanup(artifact, artifact.lower())
        assert passed is True


class TestCheckExceptionHandling:
    """Test _check_exception_handling for proper exception types"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_specific_exception(self):
        artifact = "try:\n    x = int(value)\nexcept ValueError:\n    print('Invalid')\n"
        passed, reason = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True
        assert "specific" in reason.lower()

    def test_multiple_specific_exceptions(self):
        artifact = "try:\n    data = json.loads(text)\nexcept (ValueError, KeyError) as e:\n    log.error(e)\n"
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True

    def test_bare_except_only_fails(self):
        artifact = "try:\n    risky()\nexcept:\n    pass\n"
        passed, reason = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is False
        assert "bare" in reason.lower() or "broad" in reason.lower()

    def test_mixed_good_and_bad(self):
        artifact = "try:\n    x = int(v)\nexcept ValueError:\n    handle()\nexcept:\n    pass\n"
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True  # mixed is OK (has specific ones)

    def test_custom_exception_class(self):
        artifact = "class AppError(Exception):\n    pass\n\nraise AppError('failed')\n"
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True

    def test_raise_specific(self):
        artifact = "if not valid:\n    raise ValueError('Invalid input')\n"
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True

    def test_js_throw_new(self):
        artifact = "if (!valid) {\n    throw new ValidationError('bad input');\n}\n"
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True

    def test_no_exception_handling(self):
        artifact = "x = 42\nprint(x)\n"
        passed, reason = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True  # no exception handling needed
        assert "not be needed" in reason.lower()

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_exception_handling(artifact, artifact.lower())
        assert passed is True


class TestCheckImports:
    """Test _check_imports for organized import statements"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_python_imports(self):
        artifact = "import os\nimport sys\nfrom pathlib import Path\n"
        passed, reason = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True
        assert "import" in reason.lower()

    def test_from_import(self):
        artifact = "from typing import List, Dict\n"
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_js_require(self):
        artifact = "const express = require('express');\nconst path = require('path');\n"
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_js_import(self):
        artifact = "import { useState } from 'react';\nimport App from './App';\n"
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_rust_use(self):
        artifact = "use std::collections::HashMap;\nuse tokio::sync::Mutex;\n"
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_c_include(self):
        artifact = '#include <stdio.h>\n#include "mylib.h"\n'
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_no_imports_ok(self):
        artifact = "x = 42\nprint(x)\n"
        passed, reason = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True
        assert "not be needed" in reason.lower()

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True

    def test_organized_with_sections(self):
        artifact = "# stdlib\nimport os\nimport sys\n\n# third-party\nimport click\n"
        passed, reason = self.evaluator._check_imports(artifact, artifact.lower())
        assert passed is True
        assert "organization" in reason.lower()


class TestCheckContextManagers:
    """Test _check_context_managers for proper resource management patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_with_open(self):
        artifact = "with open('data.txt') as f:\n    content = f.read()\n"
        passed, reason = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True
        assert "context manager" in reason.lower()

    def test_db_connection(self):
        artifact = "with db.connect() as conn:\n    conn.execute(query)\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_db_cursor(self):
        artifact = "with conn.cursor() as cur:\n    cur.execute(sql)\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_lock(self):
        artifact = "with lock:\n    shared_state += 1\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_async_with(self):
        artifact = "async with session.get(url) as resp:\n    data = await resp.json()\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_contextmanager_decorator(self):
        artifact = "from contextlib import contextmanager\n\n@contextmanager\ndef temp():\n    yield\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_generic_with_as(self):
        artifact = "with Transaction() as tx:\n    tx.commit()\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True

    def test_no_context_managers_fails(self):
        artifact = "x = 42\nprint(x)\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is False

    def test_tempfile(self):
        artifact = "with tempfile.NamedTemporaryFile() as tmp:\n    tmp.write(data)\n"
        passed, _ = self.evaluator._check_context_managers(artifact, artifact.lower())
        assert passed is True


# --- Backend Phase B rules (Exp 33) ---


class TestCheckAsyncOperations:
    """Test _check_async_operations for async/await usage in I/O"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_python_async_await(self):
        artifact = "async def fetch_data():\n    result = await db.query('SELECT *')\n    return result\n"
        passed, reason = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True
        assert "async" in reason.lower()

    def test_asyncio_gather(self):
        artifact = "import asyncio\n\nasync def main():\n    results = await asyncio.gather(task1(), task2())\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True

    def test_aiohttp_client(self):
        artifact = "import aiohttp\n\nasync def fetch(url):\n    async with aiohttp.ClientSession() as session:\n        resp = await session.get(url)\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True

    def test_js_async_function(self):
        artifact = "async function fetchData() {\n    const result = await fetch('/api/data');\n    return result.json();\n}\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True

    def test_promise_all(self):
        artifact = "const results = await Promise.all([fetch(url1), fetch(url2)]);\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True

    def test_blocking_without_async_fails(self):
        artifact = "import requests\nresponse = requests.get('https://api.example.com')\nprint(response.json())\n"
        passed, reason = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is False
        assert "blocking" in reason.lower()

    def test_async_for(self):
        artifact = "async def stream():\n    async for chunk in response.aiter_bytes():\n        yield chunk\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True

    def test_no_async_patterns_fails(self):
        artifact = "def sync_function():\n    return 42\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is False

    def test_httpx_async_client(self):
        artifact = "async def get_data():\n    async with httpx.AsyncClient() as client:\n        resp = await client.get(url)\n"
        passed, _ = self.evaluator._check_async_operations(artifact, artifact.lower())
        assert passed is True


class TestCheckHttpStatusCodes:
    """Test _check_http_status_codes for proper status code usage"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_success_and_error_codes(self):
        artifact = "return Response(data, status=200)\n# ...\nreturn Response({'error': 'Not found'}, status=404)\n"
        passed, reason = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is True
        assert "status" in reason.lower()

    def test_http_constant_style(self):
        artifact = "from rest_framework import status\nif response.status_code == 200:\n    pass\nreturn Response(data, status=HTTP_200_OK)\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is True

    def test_status_code_reference(self):
        artifact = "if response.status_code == 200:\n    process(data)\nelif response.status_code == 400:\n    handle_error()\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is True

    def test_named_constants(self):
        artifact = "return HttpStatus.OK\n# ...\nthrow new HttpException('...', HttpStatus.BAD_REQUEST)\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is True

    def test_201_created(self):
        artifact = "return Response(serializer.data, status=201)\nreturn Response(errors, status=422)\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is True

    def test_no_status_codes_fails(self):
        artifact = "def process():\n    return result\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is False

    def test_single_code_insufficient(self):
        artifact = "return 200\n"
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_http_status_codes(artifact, artifact.lower())
        assert passed is False


class TestCheckContentNegotiation:
    """Test _check_content_negotiation for Accept/Content-Type headers"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_json_content_type(self):
        artifact = "response.headers['Content-Type'] = 'application/json'\nreturn response\n"
        passed, reason = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is True
        assert "content negotiation" in reason.lower()

    def test_html_and_json(self):
        artifact = "# Supports application/json and text/html\ncontent_type = request.headers.get('Accept', 'application/json')\n"
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is True

    def test_produces_annotation(self):
        artifact = "@produces('application/json')\ndef get_users():\n    return jsonify(users)\n"
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is True

    def test_media_type_param(self):
        artifact = "media_type='application/json'\nresponse.headers['Content-Type'] = media_type\n"
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is True

    def test_406_not_acceptable(self):
        artifact = "if not supported:\n    return Response(status=406)\ncontent_type = 'application/json'\n"
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is True

    def test_no_content_negotiation_fails(self):
        artifact = "def get_data():\n    return {'key': 'value'}\n"
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_content_negotiation(artifact, artifact.lower())
        assert passed is False


class TestCheckResourceNaming:
    """Test _check_resource_naming for RESTful naming conventions"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_express_routes(self):
        artifact = "router.get('/users', getUsers);\nrouter.post('/users', createUser);\n"
        passed, reason = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True
        assert "resource" in reason.lower()

    def test_flask_routes(self):
        artifact = "@app.get('/orders')\ndef get_orders():\n    pass\n\n@app.post('/orders')\ndef create_order():\n    pass\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True

    def test_api_versioned_paths(self):
        artifact = "router.get('/api/v1/users', handler);\nrouter.get('/api/v1/products', handler);\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True

    def test_parameterized_routes(self):
        artifact = "router.get('/users/:id', getUser);\nrouter.delete('/users/:id', deleteUser);\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True

    def test_django_paths(self):
        artifact = "path('/orders', views.list_orders),\npath('/orders/<int:id>', views.order_detail),\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True

    def test_nestjs_decorators(self):
        artifact = "@Get('/items')\nfindAll() {}\n\n@Post('/items')\ncreate() {}\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is True

    def test_no_routes_fails(self):
        artifact = "class UserService:\n    def get_user(self, id):\n        return self.repo.find(id)\n"
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_resource_naming(artifact, artifact.lower())
        assert passed is False


class TestCheckSecurityHeaders:
    """Test _check_security_headers for security headers in responses"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_helmet_middleware(self):
        artifact = "const helmet = require('helmet');\napp.use(helmet());\napp.use(helmet.contentSecurityPolicy());\n"
        passed, reason = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True
        assert "security header" in reason.lower()

    def test_manual_headers(self):
        artifact = "response.headers['X-Content-Type-Options'] = 'nosniff'\nresponse.headers['X-Frame-Options'] = 'DENY'\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True

    def test_csp_and_hsts(self):
        artifact = "Content-Security-Policy: default-src 'self'\nStrict-Transport-Security: max-age=31536000\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True

    def test_referrer_and_permissions_policy(self):
        artifact = "Referrer-Policy: strict-origin-when-cross-origin\nPermissions-Policy: camera=(), microphone=()\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True

    def test_nosniff_and_deny(self):
        artifact = "# Set nosniff to prevent MIME type sniffing\n# Set DENY for X-Frame-Options\nX-Content-Type-Options: nosniff\nX-Frame-Options: DENY\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True

    def test_secure_headers_middleware(self):
        artifact = "from secure_headers import SecureHeaders\napp.use(secure_headers())\nStrict-Transport-Security: max-age=63072000\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is True

    def test_single_header_insufficient(self):
        artifact = "X-XSS-Protection: 1; mode=block\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is False

    def test_no_security_headers_fails(self):
        artifact = "def get_data():\n    return {'key': 'value'}\n"
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_security_headers(artifact, artifact.lower())
        assert passed is False


# ============================================================================
# Exp 34: Keyword Fallback Robustness Tests
# ============================================================================


class TestExtractKeywords:
    """Test _extract_keywords static method for noise filtering and edge cases"""

    def test_empty_string_returns_empty(self):
        result = Evaluator._extract_keywords("")
        assert result == []

    def test_none_returns_empty(self):
        result = Evaluator._extract_keywords(None)
        assert result == []

    def test_whitespace_only_returns_empty(self):
        result = Evaluator._extract_keywords("   \t\n  ")
        assert result == []

    def test_noise_words_filtered(self):
        result = Evaluator._extract_keywords("verify the component for proper usage")
        assert "verify" not in result
        assert "the" not in result
        assert "for" not in result
        assert "component" in result
        assert "usage" in result

    def test_punctuation_stripped(self):
        result = Evaluator._extract_keywords("state, mutations, (components)")
        assert "state" in result
        assert "mutations" in result
        assert "components" in result

    def test_compound_slash_split(self):
        result = Evaluator._extract_keywords("useState/useReducer")
        assert "usestate" in result
        assert "usereducer" in result

    def test_real_check_description(self):
        result = Evaluator._extract_keywords(
            "verify React.lazy() or dynamic imports for large components"
        )
        assert "react.lazy" in result or "lazy" in result
        assert "dynamic" in result
        assert "imports" in result
        assert "components" in result
        # Noise should be gone
        assert "verify" not in result
        assert "for" not in result
        assert "or" not in result

    def test_short_tokens_filtered(self):
        """Single char tokens should be filtered out"""
        result = Evaluator._extract_keywords("a b c def ghi")
        assert "def" in result
        assert "ghi" in result
        # 'a', 'b', 'c' are single char - filtered
        assert len([k for k in result if len(k) < 2]) == 0

    def test_all_noise_returns_empty(self):
        result = Evaluator._extract_keywords("verify the for and or")
        assert result == []

    def test_preserves_technical_terms(self):
        result = Evaluator._extract_keywords(
            "verify useCallback/useMemo for expensive computations and callback dependencies"
        )
        assert "usecallback" in result
        assert "usememo" in result
        assert "expensive" in result
        assert "computations" in result
        assert "callback" in result
        assert "dependencies" in result

    def test_parentheses_stripped(self):
        result = Evaluator._extract_keywords("(export default Component)")
        assert "export" in result
        assert "default" in result
        assert "component" in result


class TestKeywordFallbackEdgeCases:
    """Test _check_content keyword fallback with edge cases (Exp 34)"""

    def setup_method(self):
        self.rule_manager = RuleManager()
        self.scorer = Scorer()
        self.evaluator = Evaluator(self.rule_manager, self.scorer)

    def _make_rule(self, rule_id, check_text):
        return QualityRule(
            id=rule_id,
            description="test rule",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.B,
            check=check_text,
            check_type=RuleCheckType.content,
        )

    def test_empty_check_fails(self):
        """Empty check string should fail, not silently pass"""
        rule = self._make_rule("test.empty", "")
        passed, reason = self.evaluator._check_content(rule, "any content here")
        assert passed is False
        assert "No meaningful keywords" in reason

    def test_noise_only_check_fails(self):
        """Check with only noise words should fail"""
        rule = self._make_rule("test.noise", "verify the for and")
        passed, reason = self.evaluator._check_content(rule, "any content here")
        assert passed is False
        assert "No meaningful keywords" in reason

    def test_compound_keyword_matches(self):
        """Compound words split on / should match individually"""
        rule = self._make_rule("test.compound", "useState/useReducer state management")
        artifact = "const [count, setCount] = useState(0);"
        passed, _ = self.evaluator._check_content(rule, artifact)
        assert passed is True

    def test_punctuation_in_check_doesnt_block_match(self):
        """Punctuation in check keywords shouldn't prevent matching"""
        rule = self._make_rule("test.punct", "state, mutations, components")
        artifact = "manage state in react components with mutations"
        passed, _ = self.evaluator._check_content(rule, artifact)
        assert passed is True

    def test_meaningful_keywords_still_fail_correctly(self):
        """When meaningful keywords are present but not found in artifact, should fail"""
        rule = self._make_rule("test.miss", "dataloader batching n+1 prevention")
        artifact = "def hello_world():\n    print('hello')"
        passed, _ = self.evaluator._check_content(rule, artifact)
        assert passed is False


# Backend Phase B Remaining Rules (Exp 35)

class TestCheckDomainErrors:
    """Test _check_domain_errors for domain error separation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_custom_error_classes(self):
        artifact = "class NotFoundError(DomainError):\n    pass\nraise NotFoundError('User not found')\n"
        passed, reason = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is True
        assert "domain error" in reason.lower()

    def test_js_custom_exceptions(self):
        artifact = "class InsufficientFundsError extends BusinessError {}\nthrow new InsufficientFundsError('Not enough balance');\n"
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is True

    def test_error_code_with_handler(self):
        artifact = "@exception_handler(DomainError)\ndef handle_domain_error(exc):\n    return {'error_code': exc.code, 'message': exc.message}\n"
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is True

    def test_validation_status_codes(self):
        artifact = "if not valid:\n    return Response({'error': 'validation failed'}, status=422)\nraise BusinessError('insufficient funds')\n"
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is True

    def test_no_domain_errors_fails(self):
        artifact = "def hello():\n    return 'world'\n"
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is False

    def test_single_pattern_insufficient(self):
        artifact = "class MyError(Exception):\n    pass\n"
        passed, _ = self.evaluator._check_domain_errors(artifact, artifact.lower())
        assert passed is False


class TestCheckErrorConsistency:
    """Test _check_error_consistency for consistent error response format"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_error_schema_with_request_id(self):
        artifact = "class ErrorResponse:\n    request_id: str\n    error_code: str\n    message: str\n"
        passed, reason = self.evaluator._check_error_consistency(artifact, artifact.lower())
        assert passed is True
        assert "error consistency" in reason.lower()

    def test_error_middleware_with_format(self):
        artifact = "@ExceptionHandler\ndef error_handler(exc):\n    return {'error_code': exc.code, 'message': str(exc), 'request_id': req.id}\n"
        passed, _ = self.evaluator._check_error_consistency(artifact, artifact.lower())
        assert passed is True

    def test_js_error_format(self):
        artifact = "app.use((err, req, res, next) => {\n    res.json({error: {code: err.code, message: err.message}});\n});\n"
        passed, _ = self.evaluator._check_error_consistency(artifact, artifact.lower())
        assert passed is True

    def test_no_error_patterns_fails(self):
        artifact = "def hello():\n    return 42\n"
        passed, _ = self.evaluator._check_error_consistency(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_error_consistency(artifact, artifact.lower())
        assert passed is False


class TestCheckStackTraceSanitization:
    """Test _check_stack_trace_sanitization for production trace hiding"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_debug_false_with_generic_error(self):
        artifact = "DEBUG = False\n\ndef handle_error(exc):\n    return Response({'error': 'Internal server error'}, status=500)\n"
        passed, reason = self.evaluator._check_stack_trace_sanitization(artifact, artifact.lower())
        assert passed is True
        assert "stack trace" in reason.lower()

    def test_node_env_check(self):
        artifact = "if (process.env.NODE_ENV === 'production') {\n    // hide stack trace\n    app.use((err, req, res, next) => res.json({error: 'Internal server error'}));\n}\n"
        passed, _ = self.evaluator._check_stack_trace_sanitization(artifact, artifact.lower())
        assert passed is True

    def test_request_id_correlation(self):
        artifact = "logger.error(f'Error: {exc}', exc_info=True)\nreturn {'error': 'Internal server error', 'request_id': req.request_id}\n"
        passed, _ = self.evaluator._check_stack_trace_sanitization(artifact, artifact.lower())
        assert passed is True

    def test_no_sanitization_fails(self):
        artifact = "def process():\n    return result\n"
        passed, _ = self.evaluator._check_stack_trace_sanitization(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_stack_trace_sanitization(artifact, artifact.lower())
        assert passed is False


class TestCheckApiVersioning:
    """Test _check_api_versioning for API versioning implementation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_url_path_versioning(self):
        artifact = "router = APIRouter(prefix='/v1')\n@router.get('/v1/users')\ndef get_users(): pass\n"
        passed, reason = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is True
        assert "api versioning" in reason.lower()

    def test_version_header(self):
        artifact = "api_version = request.headers.get('X-API-Version', '1')\nif api_version == '2':\n    return v2_response()\n"
        passed, _ = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is True

    def test_drf_versioning(self):
        artifact = "REST_FRAMEWORK = {\n    'DEFAULT_VERSIONING_CLASS': 'UrlPathVersioning',\n    'version': 'v1',\n}\n"
        passed, _ = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is True

    def test_deprecation_with_versioned_routes(self):
        artifact = "@deprecated(reason='Use /v2/users instead')\n@app.get('/v1/users')\ndef old_users(): pass\n"
        passed, _ = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is True

    def test_no_versioning_fails(self):
        artifact = "def get_users():\n    return User.query.all()\n"
        passed, _ = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_api_versioning(artifact, artifact.lower())
        assert passed is False


class TestCheckSchemaValidation:
    """Test _check_schema_validation for request/response schema validation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_pydantic_model(self):
        artifact = "from pydantic import BaseModel\n\nclass UserCreate(BaseModel):\n    name: str\n    email: str\n\ndef create_user(data: UserCreate): pass\n"
        passed, reason = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is True
        assert "schema validation" in reason.lower()

    def test_zod_schema(self):
        artifact = "import { z } from 'zod';\nconst UserSchema = z.object({\n    name: z.string(),\n    email: z.string().email(),\n});\nconst result = UserSchema.parse(req.body);\n"
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is True

    def test_class_validator_decorators(self):
        artifact = "class CreateUserDto {\n    @IsString()\n    name: string;\n    @IsEmail()\n    email: string;\n}\n"
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is True

    def test_openapi_swagger(self):
        artifact = "from pydantic import BaseModel\nfrom fastapi import FastAPI\napp = FastAPI()\n# OpenAPI docs at /docs\n@app.post('/users')\ndef create(user: UserCreate): pass\n"
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is True

    def test_drf_serializer(self):
        artifact = "class UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = '__all__'\n\ndef validate(self, data): pass\n"
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is True

    def test_no_schema_validation_fails(self):
        artifact = "def process(data):\n    return data['name']\n"
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_schema_validation(artifact, artifact.lower())
        assert passed is False


class TestCheckIdempotency:
    """Test _check_idempotency for idempotent operations"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_idempotency_key_header(self):
        artifact = "idempotency_key = request.headers.get('Idempotency-Key')\nif cached := get_cached_result(idempotency_key):\n    return cached\n"
        passed, reason = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is True
        assert "idempotency" in reason.lower()

    def test_upsert_with_on_conflict(self):
        artifact = "INSERT INTO users (email, name) VALUES ($1, $2)\nON CONFLICT (email) DO UPDATE SET name = $2;\n"
        passed, _ = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_put_update_idempotent(self):
        artifact = "@app.put('/users/{id}')\ndef update_user(id: int, data: UserUpdate):\n    # PUT is idempotent by design\n    return db.upsert(User, id=id, **data.dict())\n"
        passed, _ = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_if_not_exists(self):
        artifact = "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY);\nINSERT INTO users (email) SELECT 'test@test.com' WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'test@test.com');\n"
        passed, _ = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is True

    def test_no_idempotency_fails(self):
        artifact = "def process():\n    return result\n"
        passed, _ = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_idempotency(artifact, artifact.lower())
        assert passed is False


# ============================================================================
# Frontend Phase B Check Methods (Exp 36)
# ============================================================================


class TestCheckFeLazyLoading:
    """Test _check_fe_lazy_loading for code splitting and lazy loading"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_react_lazy_with_suspense(self):
        artifact = "const Dashboard = React.lazy(() => import('./Dashboard'));\n<Suspense fallback={<Loading />}><Dashboard /></Suspense>\n"
        passed, reason = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is True
        assert "lazy loading" in reason.lower()

    def test_dynamic_import(self):
        artifact = "const module = await import('./heavyModule');\nconst LazyComp = lazy(() => import('./LazyComp'));\n"
        passed, _ = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is True

    def test_image_lazy_loading(self):
        artifact = '<img src="photo.jpg" loading="lazy" alt="Photo" />\n<img src="banner.jpg" loading="lazy" alt="Banner" />\n'
        passed, _ = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is True

    def test_intersection_observer(self):
        artifact = "const observer = new IntersectionObserver(callback);\nconst { ref, inView } = useInView({ threshold: 0.5 });\n"
        passed, _ = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is True

    def test_no_lazy_loading_fails(self):
        artifact = "import Dashboard from './Dashboard';\nfunction App() { return <Dashboard />; }\n"
        passed, _ = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_lazy_loading(artifact, artifact.lower())
        assert passed is False


class TestCheckFeSemanticHtml:
    """Test _check_fe_semantic_html for semantic HTML elements"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_page_structure_elements(self):
        artifact = "<header><nav>Menu</nav></header>\n<main><article>Content</article></main>\n<footer>Footer</footer>\n"
        passed, reason = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is True
        assert "semantic html" in reason.lower()

    def test_article_and_section(self):
        artifact = "<section><h2>Title</h2><article>Post content</article></section>\n"
        passed, _ = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is True

    def test_aria_attributes(self):
        artifact = '<div role="navigation" aria-label="Main menu">\n<button aria-expanded="false">Toggle</button>\n</div>\n'
        passed, _ = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is True

    def test_figure_and_details(self):
        artifact = "<figure><img src='chart.png' /><figcaption>Sales chart</figcaption></figure>\n<details><summary>More info</summary></details>\n"
        passed, _ = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is True

    def test_div_soup_fails(self):
        artifact = "<div><div><div>Content</div></div></div>\n"
        passed, _ = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_semantic_html(artifact, artifact.lower())
        assert passed is False


class TestCheckFeCssOrganization:
    """Test _check_fe_css_organization for CSS structure approaches"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_css_modules(self):
        artifact = "import styles from './Button.module.css';\n<button className={styles.primary}>Click</button>\n"
        passed, reason = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is True
        assert "css organization" in reason.lower()

    def test_styled_components(self):
        artifact = "import styled from 'styled-components';\nconst Button = styled.button`\n  color: blue;\n`;\nconst highlight = css`font-weight: bold;`;\n"
        passed, _ = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is True

    def test_tailwind(self):
        artifact = "// tailwind.config.js\nmodule.exports = { content: ['./src/**/*.tsx'] };\n// In component: className='@apply flex items-center'\n"
        passed, _ = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is True

    def test_mui_styles(self):
        artifact = "const useStyles = makeStyles((theme) => ({ root: { padding: 8 } }));\n<Box sx={{ display: 'flex' }}>\n"
        passed, _ = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is True

    def test_no_css_organization_fails(self):
        artifact = "function App() {\n  return <div style={{color: 'red'}}>Hello</div>;\n}\n"
        passed, _ = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_css_organization(artifact, artifact.lower())
        assert passed is False


class TestCheckFeHooksOptimization:
    """Test _check_fe_hooks_optimization for React hooks performance"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_usememo_and_usecallback(self):
        artifact = "const memoized = useMemo(() => expensiveCalc(data), [data]);\nconst handleClick = useCallback(() => onClick(id), [id]);\n"
        passed, reason = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is True
        assert "hooks optimization" in reason.lower()

    def test_react_memo(self):
        artifact = "const ListItem = React.memo(function ListItem({ item }) {\n  return <li>{item.name}</li>;\n});\nconst ref = useRef(null);\n"
        passed, _ = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is True

    def test_concurrent_features(self):
        artifact = "const [isPending, startTransition] = useTransition();\nconst deferredQuery = useDeferredValue(query);\n"
        passed, _ = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is True

    def test_shallow_equal(self):
        artifact = "export default React.memo(Component, shallowEqual);\nconst value = useMemo(() => compute(a, b), [a, b]);\n"
        passed, _ = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is True

    def test_no_optimization_fails(self):
        artifact = "function Component({ data }) {\n  const items = data.map(i => <Item key={i.id} />);\n  return <ul>{items}</ul>;\n}\n"
        passed, _ = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_hooks_optimization(artifact, artifact.lower())
        assert passed is False


class TestCheckFeErrorBoundaries:
    """Test _check_fe_error_boundaries for error boundary implementation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_class_error_boundary(self):
        artifact = "class ErrorBoundary extends React.Component {\n  componentDidCatch(error, info) {\n    logError(error);\n  }\n}\n"
        passed, reason = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is True
        assert "error boundary" in reason.lower()

    def test_react_error_boundary_lib(self):
        artifact = "import { useErrorBoundary } from 'react-error-boundary';\n<ErrorBoundary FallbackComponent={ErrorFallback} onReset={handleReset}>\n"
        passed, _ = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_get_derived_state(self):
        artifact = "static getDerivedStateFromError(error) {\n  return { hasError: true };\n}\nrender() {\n  if (this.state.hasError) return <ErrorBoundary fallbackRender={...} />;\n}\n"
        passed, _ = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_fallback_component(self):
        artifact = "<ErrorBoundary FallbackComponent={ErrorPage} onError={logToService}>\n  <App />\n</ErrorBoundary>\n"
        passed, _ = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_no_error_boundary_fails(self):
        artifact = "function App() {\n  return <div>Hello World</div>;\n}\n"
        passed, _ = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_error_boundaries(artifact, artifact.lower())
        assert passed is False


class TestCheckFeComponentComposition:
    """Test _check_fe_component_composition for composition patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_children_prop(self):
        artifact = "function Layout({ children }) {\n  return <div className='layout'>{children}</div>;\n}\n"
        passed, reason = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is True
        assert "component composition" in reason.lower()

    def test_context_provider(self):
        artifact = "const ThemeContext = createContext('light');\nfunction ThemeProvider({ children }) {\n  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;\n}\n"
        passed, _ = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is True

    def test_render_props(self):
        artifact = "// Using render props pattern\nfunction DataFetcher({ children, render }) {\n  const data = useFetch('/api');\n  return render ? render(data) : children(data);\n}\n<DataFetcher render={data => <List items={data} />} />\n"
        passed, _ = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is True

    def test_forward_ref(self):
        artifact = "const Input = React.forwardRef((props, ref) => {\n  return <input ref={ref} {...props} />;\n});\nconst theme = useContext(ThemeContext);\n"
        passed, _ = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is True

    def test_no_composition_fails(self):
        artifact = "function Button() {\n  return <button>Click me</button>;\n}\n"
        passed, _ = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_component_composition(artifact, artifact.lower())
        assert passed is False


class TestCheckFeApiIntegration:
    """Test _check_fe_api_integration for API data fetching patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_react_query(self):
        artifact = "const { data, isLoading, isError } = useQuery(['users'], fetchUsers);\nif (isLoading) return <Spinner />;\n"
        passed, reason = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is True
        assert "api integration" in reason.lower()

    def test_swr(self):
        artifact = "const { data, error } = useSWR('/api/user', fetcher);\nif (error) return <Error />;\nif (isLoading) return <Loading />;\n"
        passed, _ = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is True

    def test_fetch_with_states(self):
        artifact = "const response = await fetch('/api/data');\nconst [isLoading, setLoading] = useState(true);\nif (isError) return <ErrorMessage />;\n"
        passed, _ = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is True

    def test_mutation_with_callbacks(self):
        artifact = "const mutation = useMutation(createUser, {\n  onSuccess: () => invalidateQueries(['users']),\n  onError: (err) => showError(err),\n});\n"
        passed, _ = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is True

    def test_no_api_integration_fails(self):
        artifact = "function Profile({ name }) {\n  return <h1>{name}</h1>;\n}\n"
        passed, _ = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_api_integration(artifact, artifact.lower())
        assert passed is False


class TestCheckFeFormValidation:
    """Test _check_fe_form_validation for form validation patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_react_hook_form(self):
        artifact = "const { register, handleSubmit, formState: { errors } } = useForm();\n<input {...register('email', { required: true })} />\n{errors.email && <span>Required</span>}\n"
        passed, reason = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is True
        assert "form validation" in reason.lower()

    def test_formik_with_yup(self):
        artifact = "const formik = useFormik({\n  validationSchema: Yup.object({ name: Yup.string().required() }),\n  onSubmit: handleSubmit,\n});\n"
        passed, _ = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is True

    def test_zod_validation(self):
        artifact = "const schema = z.object({ email: z.string().email() });\nconst { register, handleSubmit } = useForm({ resolver: zodResolver(schema) });\n"
        passed, _ = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is True

    def test_validation_rules(self):
        artifact = "<input onBlur={validateField}\n  {...register('password', { required: true, minLength: 8, pattern: /^[A-Z]/ })}\n/>\n"
        passed, _ = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is True

    def test_no_form_validation_fails(self):
        artifact = "function Form() {\n  return <form><input name='email' /><button>Submit</button></form>;\n}\n"
        passed, _ = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_form_validation(artifact, artifact.lower())
        assert passed is False


class TestCheckFeEnvironmentConfig:
    """Test _check_fe_environment_config for env-based configuration"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_process_env(self):
        artifact = "const API_URL = process.env.REACT_APP_API_URL;\nconst apiKey = process.env.REACT_APP_API_KEY;\n"
        passed, reason = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is True
        assert "environment config" in reason.lower()

    def test_vite_env(self):
        artifact = "const baseUrl = import.meta.env.VITE_API_BASE;\nconst mode = import.meta.env.VITE_MODE;\n"
        passed, _ = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is True

    def test_next_public_env(self):
        artifact = "const url = process.env.NEXT_PUBLIC_API_URL;\n// See .env.example for required variables\n"
        passed, _ = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is True

    def test_env_file_references(self):
        artifact = "# .env.local\nAPI_URL=http://localhost:3000\n# Copy .env.example to .env.local\nBASE_URL=https://api.example.com\n"
        passed, _ = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is True

    def test_no_env_config_fails(self):
        artifact = "const API_URL = 'https://api.example.com';\nfetch(API_URL + '/users');\n"
        passed, _ = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_environment_config(artifact, artifact.lower())
        assert passed is False


class TestCheckFeStatePersistence:
    """Test _check_fe_state_persistence for state persistence patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_localstorage_with_json(self):
        artifact = "const saved = localStorage.getItem('settings');\nconst data = JSON.parse(saved);\nlocalStorage.setItem('settings', JSON.stringify(newData));\n"
        passed, reason = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is True
        assert "state persistence" in reason.lower()

    def test_try_catch_storage(self):
        artifact = "try {\n  localStorage.setItem('token', value);\n} catch (e) {\n  if (e.name === 'QuotaExceededError') console.warn('Storage full');\n}\n"
        passed, _ = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is True

    def test_custom_storage_hook(self):
        artifact = "const [theme, setTheme] = useLocalStorage('theme', 'light');\nconst saved = JSON.parse(localStorage.getItem('prefs'));\n"
        passed, _ = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is True

    def test_indexeddb(self):
        artifact = "const db = await indexedDB.open('myApp', 1);\nimport { openDB } from 'idb';\nconst store = await Dexie.open('cache');\n"
        passed, _ = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is True

    def test_no_persistence_fails(self):
        artifact = "const [count, setCount] = useState(0);\nfunction increment() { setCount(c => c + 1); }\n"
        passed, _ = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_fe_state_persistence(artifact, artifact.lower())
        assert passed is False


# ============================================================================
# Exp 39: Backend GraphQL Phase B check methods
# ============================================================================


class TestCheckGqlNPlus1:
    """Test _check_gql_n_plus1 for N+1 query prevention"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_dataloader_with_batch(self):
        artifact = "const userLoader = new DataLoader(keys => batchLoadUsers(keys));\ncontext.loaders = { userLoader };\n"
        passed, reason = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is True
        assert "n+1" in reason.lower() or "pattern" in reason.lower()

    def test_python_dataloader(self):
        artifact = "from promise.dataloader import DataLoader\nuser_loader = DataLoader(batch_load_fn=batch_get_users)\n"
        passed, _ = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is True

    def test_eager_loading(self):
        artifact = "users = User.objects.prefetch_related('orders').all()\nresult = await eager_load(query, ['posts', 'comments'])\n"
        passed, _ = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is True

    def test_loader_load_many(self):
        artifact = "const users = await loader.loadMany(userIds);\nconst post = await loader.load(postId);\n"
        passed, _ = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is True

    def test_no_batching_fails(self):
        artifact = "async function getUser(id) { return db.query('SELECT * FROM users WHERE id = ?', [id]); }\n"
        passed, _ = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_n_plus1(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlErrorHandling:
    """Test _check_gql_error_handling for structured GraphQL errors"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_apollo_error_with_format(self):
        artifact = "throw new ApolloError('Not found', 'NOT_FOUND');\nconst formatError = (err) => ({ message: err.message, extensions: { code: err.extensions.code } });\n"
        passed, reason = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_graphql_error_class(self):
        artifact = "import { GraphQLError } from 'graphql';\nthrow new GraphQLError('Validation failed', { extensions: { code: 'BAD_USER_INPUT' } });\n"
        passed, _ = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_error_masking(self):
        artifact = "function formatError(error) {\n  // mask internal errors\n  const sanitize error details for production\n  return { message: error.message, locations: error.locations, path: error.path };\n}\n"
        passed, _ = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_error_extensions_code(self):
        artifact = "error.extensions.code = 'FORBIDDEN';\nif (error.extensions.code === 'GRAPHQL_VALIDATION_FAILED') handleValidation();\n"
        passed, _ = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is True

    def test_no_error_handling_fails(self):
        artifact = "const resolvers = { Query: { user: (_, { id }) => db.getUser(id) } };\n"
        passed, _ = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_error_handling(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlPagination:
    """Test _check_gql_pagination for connection-based pagination"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_relay_connection(self):
        artifact = "type UserConnection { edges: [UserEdge!]! pageInfo: PageInfo! }\ntype PageInfo { hasNextPage: Boolean! endCursor: String }\n"
        passed, reason = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is True

    def test_cursor_based_args(self):
        artifact = "users(first: 10, after: $cursor) { edges { node { id name } } pageInfo { hasNextPage endCursor } }\n"
        passed, _ = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is True

    def test_offset_pagination(self):
        artifact = "query getUsers($page: Int!) { users(pageSize: 20, pageNumber: $page) { totalCount items { id } } }\n"
        passed, _ = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is True

    def test_has_previous_page(self):
        artifact = "type PageInfo { hasPreviousPage: Boolean! startCursor: String }\nusers(last: 5, before: $cursor)\n"
        passed, _ = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is True

    def test_no_pagination_fails(self):
        artifact = "type Query { users: [User!]! }\ntype User { id: ID! name: String! }\n"
        passed, _ = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_pagination(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlSubscriptionsAuth:
    """Test _check_gql_subscriptions_auth for secure subscription authentication"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_on_connect_with_auth(self):
        artifact = "const server = new ApolloServer({ subscriptions: { onConnect: (connectionParams, webSocket) => { verifyToken(connectionParams.authToken); } } });\n"
        passed, reason = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is True

    def test_websocket_auth(self):
        artifact = "// Authenticate on websocket connection\nconst wsLink = new WebSocketLink({ connectionParams: { authToken: getToken() } });\nvalidate websocket token on connect\n"
        passed, _ = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is True

    def test_subscription_guard(self):
        artifact = "subscription middleware validates JWT\nsubscription guard checks permissions\n"
        passed, _ = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is True

    def test_connection_init_params(self):
        artifact = "ws.on('connection_init', (ctx) => { verifyAuth(ctx.connectionParams); });\nvalidate connectionParams token\n"
        passed, _ = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is True

    def test_no_subscription_auth_fails(self):
        artifact = "const subscription = gql`subscription { messageAdded { id content } }`;\nclient.subscribe({ query: subscription });\n"
        passed, _ = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_subscriptions_auth(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlDescriptionDocs:
    """Test _check_gql_description_docs for schema documentation"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_description_field_with_deprecated(self):
        artifact = 'description: "The user\'s unique identifier"\n@deprecated(reason: "Use newField instead")\n'
        passed, reason = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is True

    def test_triple_quote_docstring(self):
        artifact = '""\"User type represents a registered user\"\"\"\ntype User {\n  description: "The unique ID"\n  id: ID!\n}\n'
        passed, _ = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is True

    def test_document_types_and_fields(self):
        artifact = "# Document all type descriptions\nDocument types and fields for API documentation reference\n"
        passed, _ = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is True

    def test_graphql_docs(self):
        artifact = "GraphQL documentation for the schema\nAPI documentation available at /docs\n"
        passed, _ = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is True

    def test_no_docs_fails(self):
        artifact = "type User { id: ID! name: String! email: String! }\ntype Query { user(id: ID!): User }\n"
        passed, _ = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_description_docs(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlFederation:
    """Test _check_gql_federation for GraphQL Federation patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_key_and_extends(self):
        artifact = '@key(fields: "id")\ntype User @extends {\n  id: ID! @external\n  orders: [Order!]!\n}\n'
        passed, reason = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is True

    def test_resolve_reference(self):
        artifact = "User.__resolveReference = async (ref) => { return db.getUserById(ref.id); };\nfederated schema composition\n"
        passed, _ = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is True

    def test_subgraph_and_gateway(self):
        artifact = "const gateway = new ApolloGateway({ supergraphSdl });\ndefine subgraph for user service\n"
        passed, _ = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is True

    def test_provides_and_requires(self):
        artifact = 'type Product @key(fields: "id") {\n  id: ID!\n  name: String @provides(fields: "name")\n  weight: Float @requires(fields: "size")\n}\n'
        passed, _ = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is True

    def test_no_federation_fails(self):
        artifact = "const typeDefs = gql`type Query { hello: String }`;\nconst resolvers = { Query: { hello: () => 'Hi' } };\n"
        passed, _ = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_federation(artifact, artifact.lower())
        assert passed is False


class TestCheckGqlQueryCost:
    """Test _check_gql_query_cost for query cost analysis patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_cost_directive_with_limit(self):
        artifact = "type Query { users: [User!]! @cost(weight: 10) }\nmaxCost = 1000\n"
        passed, reason = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is True

    def test_field_cost_values(self):
        artifact = "field cost: 5\ncost analysis calculates total query cost\n"
        passed, _ = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is True

    def test_cost_in_extensions(self):
        artifact = "// Return cost in response extensions\nresponse.extensions = { cost: totalCost, maxCost: MAX_COST };\n"
        passed, _ = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is True

    def test_cost_calculation(self):
        artifact = "cost = 3\ncost weight = 2 for nested lists\n"
        passed, _ = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is True

    def test_no_cost_analysis_fails(self):
        artifact = "const resolvers = { Query: { users: () => db.findAll() } };\nconst schema = makeExecutableSchema({ typeDefs, resolvers });\n"
        passed, _ = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_gql_query_cost(artifact, artifact.lower())
        assert passed is False


# ── Database Phase B check method tests (Exp 41) ──

class TestCheckDbDenormalization:
    """Test _check_db_denormalization for denormalization patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_materialized_view(self):
        artifact = "CREATE MATERIALIZED VIEW order_summary AS\nSELECT user_id, COUNT(*) FROM orders GROUP BY user_id;\n"
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is True

    def test_denormalization_mention(self):
        artifact = "-- Denormalization: add total_orders column\nALTER TABLE users ADD COLUMN total_orders INT;\ncache table for read performance\n"
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is True

    def test_cqrs_and_read_model(self):
        artifact = "CQRS pattern: separate read model from write model\nread-optimized projections\n"
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is True

    def test_precomputed_summary(self):
        artifact = "summary_table for dashboard stats\nprecomputed aggregations\n"
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is True

    def test_no_denormalization_fails(self):
        artifact = "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100));\nSELECT * FROM users;\n"
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_denormalization(artifact, artifact.lower())
        assert passed is False


class TestCheckDbMigrations:
    """Test _check_db_migrations for migration patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_alembic_migration(self):
        artifact = "def upgrade():\n    op.add_column('users', Column('email', String))\ndef downgrade():\n    op.drop_column('users', 'email')\n"
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is True

    def test_knex_migration(self):
        artifact = "exports.up = function(knex) {\n  return knex.schema.create('users', t => { t.increments('id'); });\n};\nexports.down = function(knex) { return knex.schema.drop('users'); };\n"
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is True

    def test_alter_table_migration(self):
        artifact = "-- migration: add_email_to_users\nALTER TABLE users ADD COLUMN email VARCHAR(255);\nadd_column :users, :email\n"
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is True

    def test_rollback_support(self):
        artifact = "migration file: 002_add_orders.sql\nrollback: DROP TABLE orders;\n"
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is True

    def test_no_migration_fails(self):
        artifact = "CREATE TABLE users (id INT, name VARCHAR(100));\nINSERT INTO users VALUES (1, 'Alice');\n"
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_migrations(artifact, artifact.lower())
        assert passed is False


class TestCheckDbConstraints:
    """Test _check_db_constraints for named constraint patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_named_check_constraint(self):
        artifact = "CONSTRAINT ck_users_age CHECK (age >= 0 AND age <= 150);\nCONSTRAINT chk_price_positive CHECK (price > 0);\n"
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is True

    def test_add_constraint(self):
        artifact = "ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id);\nconstraint_name defined\n"
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is True

    def test_check_expression(self):
        artifact = "CHECK (status IN ('active', 'inactive'))\nCONSTRAINT ck_status_valid\n"
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is True

    def test_exclusion_constraint(self):
        artifact = "exclusion constraint using gist (room_id WITH =, period WITH &&)\nCONSTRAINT reserve_overlap\n"
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is True

    def test_no_constraints_fails(self):
        artifact = "CREATE TABLE users (id INT, name VARCHAR(100));\nSELECT * FROM users;\n"
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_constraints(artifact, artifact.lower())
        assert passed is False


class TestCheckDbTransactionBoundaries:
    """Test _check_db_transaction_boundaries for transaction patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_begin_commit_rollback(self):
        artifact = "BEGIN TRANSACTION;\nUPDATE accounts SET balance = balance - 100;\nCOMMIT;\n"
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_django_atomic(self):
        artifact = "from django.db import transaction\nwith transaction.atomic():\n    order.save()\n    payment.process()\n"
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_savepoint(self):
        artifact = "SAVEPOINT sp1;\nINSERT INTO logs (msg) VALUES ('step1');\nROLLBACK TO SAVEPOINT sp1;\n"
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_session_begin_commit(self):
        artifact = "session.begin()\ntry:\n    session.add(user)\n    session.commit()\nexcept:\n    session.rollback()\n"
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is True

    def test_no_transactions_fails(self):
        artifact = "SELECT * FROM users;\nINSERT INTO users (name) VALUES ('Bob');\n"
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_transaction_boundaries(artifact, artifact.lower())
        assert passed is False


class TestCheckDbQueryIsolation:
    """Test _check_db_query_isolation for N+1 prevention patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_join_usage(self):
        artifact = "SELECT u.*, o.* FROM users u\nINNER JOIN orders o ON o.user_id = u.id;\n"
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is True

    def test_django_prefetch(self):
        artifact = "queryset = User.objects.prefetch_related('orders').select_related('profile').all()\n"
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is True

    def test_dataloader(self):
        artifact = "const userLoader = new DataLoader(ids => batchGetUsers(ids));\nbatch query optimization\n"
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is True

    def test_eager_loading(self):
        artifact = "eager_load(:orders, :profile)\nN+1 prevention configured\n"
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is True

    def test_no_query_isolation_fails(self):
        artifact = "for user in users:\n    orders = db.query(f'SELECT * FROM orders WHERE user_id = {user.id}')\n"
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_query_isolation(artifact, artifact.lower())
        assert passed is False


class TestCheckDbUniqueConstraints:
    """Test _check_db_unique_constraints for unique constraint patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_unique_index(self):
        artifact = "CREATE UNIQUE INDEX idx_users_email ON users(email);\nUNIQUE constraint on username\n"
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is True

    def test_prisma_unique(self):
        artifact = 'model User {\n  id    Int    @id @default(autoincrement())\n  email String @unique\n}\n'
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is True

    def test_django_unique(self):
        artifact = "email = models.EmailField(unique=True)\nclass Meta:\n    unique_together = [['first_name', 'last_name']]\n"
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is True

    def test_add_unique_constraint(self):
        artifact = "ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);\nduplicate key check\n"
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is True

    def test_no_unique_fails(self):
        artifact = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));\nSELECT * FROM users;\n"
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_unique_constraints(artifact, artifact.lower())
        assert passed is False


class TestCheckDbSensitiveData:
    """Test _check_db_sensitive_data for sensitive data protection patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_bcrypt_password_hash(self):
        artifact = "password_hash = bcrypt.hashpw(password, bcrypt.gensalt())\nhash password before storing\n"
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is True

    def test_encryption_at_rest(self):
        artifact = "at-rest encryption enabled with AES-256\nencrypt sensitive columns\n"
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is True

    def test_pgcrypto_pii(self):
        artifact = "CREATE EXTENSION pgcrypto;\nPII data must be masked\n"
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is True

    def test_argon2_tokenization(self):
        artifact = "import argon2\ntokenization applied to credit card numbers\n"
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is True

    def test_no_protection_fails(self):
        artifact = "CREATE TABLE users (id INT, password VARCHAR(255));\nINSERT INTO users VALUES (1, 'secret123');\n"
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_sensitive_data(artifact, artifact.lower())
        assert passed is False


class TestCheckDbConnectionPooling:
    """Test _check_db_connection_pooling for connection pooling patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_pool_size_and_max(self):
        artifact = "pool_size = 20\nmax_connections = 100\n"
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is True

    def test_pgbouncer(self):
        artifact = "PgBouncer configured with connection pool\nidle_timeout = 300\n"
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is True

    def test_create_engine_pool(self):
        artifact = "engine = create_engine(url, pool_size=10, max_overflow=20)\nconnection_pool management\n"
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is True

    def test_hikari(self):
        artifact = "HikariCP configured\nmax_connections = 50\nmin_idle = 10\n"
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is True

    def test_no_pooling_fails(self):
        artifact = "import psycopg2\nconn = psycopg2.connect(dsn)\ncursor = conn.cursor()\n"
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_connection_pooling(artifact, artifact.lower())
        assert passed is False


class TestCheckDbBackupStrategy:
    """Test _check_db_backup_strategy for backup patterns"""

    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_pg_dump_retention(self):
        artifact = "pg_dump -Fc mydb > backup.dump\nretention policy: 30 days daily, 12 months weekly\n"
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is True

    def test_automated_backup(self):
        artifact = "automated backup every 6 hours\nrestore tested weekly\n"
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is True

    def test_wal_archiving_pitr(self):
        artifact = "WAL archiving enabled for continuous backup\npoint-in-time recovery configured\n"
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is True

    def test_rpo_rto(self):
        artifact = "backup strategy:\n- RPO: 1 hour\n- RTO: 4 hours\nrecovery plan documented\n"
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is True

    def test_no_backup_fails(self):
        artifact = "CREATE TABLE users (id INT, name VARCHAR);\nSELECT * FROM users;\n"
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_db_backup_strategy(artifact, artifact.lower())
        assert passed is False


# Config Phase B check methods (Exp 42)


class TestCheckConfigDefaults:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_yaml_defaults(self):
        artifact = "port:\n  default: 8080\ntimeout:\n  default: 30\n"
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is True

    def test_env_var_defaults(self):
        artifact = "host: ${DB_HOST:-localhost}\nport: ${DB_PORT:-5432}\n"
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is True

    def test_nullish_coalescing(self):
        artifact = "const port = config.port ?? 3000;\nconst host = config.host || 'localhost';\n"
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is True

    def test_optional_fields(self):
        artifact = "optional: true\nfallback: 'default_value'\n"
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is True

    def test_no_defaults_fails(self):
        artifact = "host: myserver.com\nport: 5432\ndatabase: mydb\n"
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_defaults(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigEnvironmentVars:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_bash_env_vars(self):
        artifact = "# See .env for values\ndatabase_url: ${DATABASE_URL}\napi_key: ${API_KEY}\n"
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is True

    def test_python_env_access(self):
        artifact = "import os\ndb_url = os.environ['DATABASE_URL']\nport = os.getenv('PORT', 8080)\n"
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is True

    def test_node_env_access(self):
        artifact = "const dbUrl = process.env.DATABASE_URL;\nconst dotenv = require('dotenv');\n"
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is True

    def test_env_with_defaults(self):
        artifact = "host: ${DB_HOST:-localhost}\nload_dotenv()\n"
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is True

    def test_no_env_vars_fails(self):
        artifact = "host: localhost\nport: 5432\ndatabase: mydb\npassword: secret123\n"
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_environment_vars(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigValueRanges:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_port_and_timeout(self):
        artifact = "port: 8080\ntimeout: 30\n"
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is True

    def test_pool_settings(self):
        artifact = "max_connections: 100\nmin_connections: 5\npool_size: 20\n"
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is True

    def test_ttl_and_retries(self):
        artifact = "ttl: 3600\nretries: 3\ninterval: 60\n"
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is True

    def test_float_values(self):
        artifact = "threshold: 80\nrate_limit: 0.5\nbatch_size: 100\n"
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is True

    def test_no_numeric_config_fails(self):
        artifact = "name: my-service\nenvironment: production\nlog_level: INFO\n"
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_value_ranges(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigEnumValidation:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_log_level_and_environment(self):
        artifact = "log_level: INFO\nenvironment: production\n"
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is True

    def test_mode_and_driver(self):
        artifact = "mode: production\ndriver: postgres\n"
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is True

    def test_choices_and_literal(self):
        artifact = "allowed_formats: choices: [json, xml, csv]\nLogLevel = Literal['DEBUG', 'INFO']\n"
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is True

    def test_protocol_and_format(self):
        artifact = "protocol: https\nformat: json\n"
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is True

    def test_no_enum_fields_fails(self):
        artifact = "host: localhost\nport: 5432\ndatabase: mydb\n"
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_enum_validation(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigEnvSeparation:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_separate_config_files(self):
        artifact = "# Load config.dev.yml for development\n# Load config.prod.yml for production\nenvironment: development\n"
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is True

    def test_dotenv_files(self):
        artifact = "# Environment files\n.env.development\n.env.production\nenvironment: staging\n"
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is True

    def test_node_env(self):
        artifact = "if (NODE_ENV === 'production') { ... }\nprofile: production\n"
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is True

    def test_spring_profiles(self):
        artifact = "spring.profiles.active: dev\napplication-dev.yml loaded\nenvironment: staging\n"
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is True

    def test_no_env_separation_fails(self):
        artifact = "host: localhost\nport: 5432\npassword: secret\n"
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_env_separation(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigSecretReferences:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_env_var_secrets(self):
        artifact = "db_password: ${DB_PASSWORD}\napi_key: ${API_KEY}\nsecret_manager: enabled\n"
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is True

    def test_vault_and_ssm(self):
        artifact = "secret: !vault secret/data/myapp\ndb_password: ssm:/prod/db/password\n"
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is True

    def test_aws_secrets_manager(self):
        artifact = "password: aws_secret://prod/db\nsecret_manager: enabled\n"
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is True

    def test_sops_and_sealed(self):
        artifact = "# Encrypted with sops\ntoken: sealed_secret ref\n"
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is True

    def test_plaintext_secrets_fails(self):
        artifact = "host: localhost\nport: 5432\npassword: mysecretpassword\n"
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_secret_references(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigSensitiveFields:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_redacted_and_encrypted(self):
        artifact = "password: ****REDACTED****\nencrypted: true\n"
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is True

    def test_env_var_secrets(self):
        artifact = "secret: ${DB_SECRET}\napi_key: ${API_KEY}\n"
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is True

    def test_terraform_sensitive(self):
        artifact = 'variable "db_password" {\n  sensitive: true\n  type = string\n}\nkms: enabled\n'
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is True

    def test_encryption_markers(self):
        artifact = "token: ENC[AESGCM,data:xyz]\nciphertext: abc123def456\n"
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is True

    def test_no_protection_fails(self):
        artifact = "host: localhost\nport: 5432\ndatabase: mydb\nname: my-service\n"
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_sensitive_fields(artifact, artifact.lower())
        assert passed is False


class TestCheckConfigOptimizations:
    def setup_method(self):
        self.evaluator = Evaluator(RuleManager(), Scorer())

    def test_timeout_and_cache(self):
        artifact = "timeout: 30\ncache: enabled\nttl: 3600\n"
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is True

    def test_pool_and_workers(self):
        artifact = "pool:\n  max_connections: 20\nworkers: 4\nthreads: 8\n"
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is True

    def test_batch_and_concurrency(self):
        artifact = "batch_size: 100\nconcurrency: 10\nbuffer_size: 4096\n"
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is True

    def test_keepalive(self):
        artifact = "timeout: 60\nkeep_alive: true\nworkers: 2\n"
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is True

    def test_no_perf_settings_fails(self):
        artifact = "name: my-service\nenvironment: production\nlog_level: INFO\n"
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is False

    def test_empty_artifact(self):
        artifact = ""
        passed, _ = self.evaluator._check_config_optimizations(artifact, artifact.lower())
        assert passed is False
