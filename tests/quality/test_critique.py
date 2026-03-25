"""
Comprehensive test suite for Critique module.

Tests cover:
- Critique class initialization
- generate() method with various inputs
- _generate_fix_instruction() for all FIX_INSTRUCTIONS categories
- Generic fix instruction fallback
- Edge cases and boundary conditions
- Integration scenarios
"""

import pytest
from typing import Dict, List
from unittest.mock import patch, MagicMock

from specify_cli.quality.critique import Critique


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def critique_default():
    """Create critique with default settings"""
    return Critique()


@pytest.fixture
def critique_limited():
    """Create critique with limited max_issues"""
    return Critique(max_issues=3)


@pytest.fixture
def critique_unlimited():
    """Create critique with high max_issues"""
    return Critique(max_issues=100)


@pytest.fixture
def sample_artifact_api():
    """Sample API spec artifact"""
    return """
    openapi: 3.0.0
    info:
      title: Sample API
      version: 1.0.0
    paths:
      /users:
        get:
          summary: Get users
    """


@pytest.fixture
def sample_artifact_code():
    """Sample code artifact"""
    return """
    def process_data(data):
        result = data.process()
        return result
    """


@pytest.fixture
def sample_artifact_docs():
    """Sample documentation artifact"""
    return """
    # My Project

    Some description here.
    """


@pytest.fixture
def sample_artifact_config():
    """Sample config artifact"""
    return """
    database:
      host: localhost
      port: 5432
    """


# ============================================================================
# Tests for Critique Initialization
# ============================================================================

class TestCritiqueInit:
    """Tests for Critique class initialization"""

    def test_default_max_issues(self, critique_default):
        """Test default max_issues is 5"""
        assert critique_default.max_issues == 5

    def test_custom_max_issues(self, critique_limited):
        """Test custom max_issues"""
        assert critique_limited.max_issues == 3

    def test_high_max_issues(self, critique_unlimited):
        """Test high max_issues value"""
        assert critique_unlimited.max_issues == 100

    def test_max_issues_one(self):
        """Test max_issues = 1"""
        critique = Critique(max_issues=1)
        assert critique.max_issues == 1

    def test_fix_instructions_exist(self, critique_default):
        """Test FIX_INSTRUCTIONS dictionary exists"""
        assert hasattr(critique_default, 'FIX_INSTRUCTIONS')
        assert isinstance(critique_default.FIX_INSTRUCTIONS, dict)
        assert len(critique_default.FIX_INSTRUCTIONS) > 0


# ============================================================================
# Tests for generate() Method - Basic Scenarios
# ============================================================================

class TestGenerateBasic:
    """Tests for generate() basic scenarios"""

    def test_generate_no_failed_rules(self, critique_default):
        """Test critique with no failed rules"""
        result = critique_default.generate([], "artifact")

        assert result.total_failed == 0
        assert result.addressed == 0
        assert result.skipped == 0
        assert result.issues == []

    def test_generate_single_failed_rule(self, critique_default):
        """Test critique with single failed rule"""
        failed_rules = [{"rule_id": "test.rule", "reason": "Test failure"}]
        result = critique_default.generate(failed_rules, "artifact")

        assert result.total_failed == 1
        assert result.addressed == 1
        assert result.skipped == 0
        assert len(result.issues) == 1
        assert result.issues[0]["rule_id"] == "test.rule"

    def test_generate_respects_max_issues(self, critique_limited):
        """Test generate respects max_issues limit"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(10)
        ]
        result = critique_limited.generate(failed_rules, "artifact")

        assert result.total_failed == 10
        assert result.addressed == 3  # max_issues = 3
        assert result.skipped == 7
        assert len(result.issues) == 3

    def test_generate_fewer_than_max(self, critique_default):
        """Test with fewer issues than max_issues"""
        failed_rules = [
            {"rule_id": "rule.1", "reason": "Reason 1"},
            {"rule_id": "rule.2", "reason": "Reason 2"},
        ]
        result = critique_default.generate(failed_rules, "artifact")

        assert result.total_failed == 2
        assert result.addressed == 2
        assert result.skipped == 0

    def test_generate_exactly_max_issues(self, critique_limited):
        """Test with exactly max_issues failed rules"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(3)  # Exactly max_issues
        ]
        result = critique_limited.generate(failed_rules, "artifact")

        assert result.total_failed == 3
        assert result.addressed == 3
        assert result.skipped == 0

    def test_generate_issue_structure(self, critique_default):
        """Test that generated issues have correct structure"""
        failed_rules = [{"rule_id": "test.rule", "reason": "Test reason"}]
        result = critique_default.generate(failed_rules, "artifact")

        issue = result.issues[0]
        assert "rule_id" in issue
        assert "reason" in issue
        assert "fix" in issue
        assert issue["rule_id"] == "test.rule"
        assert issue["reason"] == "Test reason"
        assert isinstance(issue["fix"], str)

    def test_generate_preserves_order(self, critique_limited):
        """Test that issues are returned in order"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(5)
        ]
        result = critique_limited.generate(failed_rules, "artifact")

        # First 3 should be returned
        assert result.issues[0]["rule_id"] == "rule.0"
        assert result.issues[1]["rule_id"] == "rule.1"
        assert result.issues[2]["rule_id"] == "rule.2"


# ============================================================================
# Tests for FIX_INSTRUCTIONS - API Spec Rules
# ============================================================================

class TestFixInstructionsApiSpec:
    """Tests for API Spec fix instructions"""

    def test_endpoints_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.endpoints"""
        fix = critique_default._generate_fix_instruction(
            "correctness.endpoints",
            "Missing endpoint",
            "artifact"
        )
        assert "CRUD" in fix
        assert "endpoint" in fix.lower()

    def test_status_codes_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.status_codes"""
        fix = critique_default._generate_fix_instruction(
            "correctness.status_codes",
            "Missing status codes",
            "artifact"
        )
        assert "200" in fix
        assert "404" in fix
        assert "500" in fix

    def test_content_types_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.content_types"""
        fix = critique_default._generate_fix_instruction(
            "correctness.content_types",
            "Missing content types",
            "artifact"
        )
        assert "Content-Type" in fix
        assert "application/json" in fix

    def test_auth_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.auth"""
        fix = critique_default._generate_fix_instruction(
            "correctness.auth",
            "Missing auth",
            "artifact"
        )
        assert "auth" in fix.lower()
        assert "Bearer" in fix or "OAuth" in fix or "API key" in fix

    def test_parameters_fix_instruction(self, critique_default):
        """Test fix instruction for quality.parameters"""
        fix = critique_default._generate_fix_instruction(
            "quality.parameters",
            "Missing parameters",
            "artifact"
        )
        assert "parameter" in fix.lower()

    def test_responses_fix_instruction(self, critique_default):
        """Test fix instruction for quality.responses"""
        fix = critique_default._generate_fix_instruction(
            "quality.responses",
            "Missing response docs",
            "artifact"
        )
        assert "response" in fix.lower()


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Code Gen Rules
# ============================================================================

class TestFixInstructionsCodeGen:
    """Tests for Code Gen fix instructions"""

    def test_tests_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.tests"""
        fix = critique_default._generate_fix_instruction(
            "correctness.tests",
            "No tests found",
            "artifact"
        )
        assert "test" in fix.lower()
        assert "unit" in fix.lower()

    def test_error_handling_fix_instruction(self, critique_default):
        """Test fix instruction for quality.error_handling"""
        fix = critique_default._generate_fix_instruction(
            "quality.error_handling",
            "No error handling",
            "artifact"
        )
        assert "error" in fix.lower()
        assert "try" in fix.lower() or "except" in fix.lower()

    def test_readability_fix_instruction(self, critique_default):
        """Test fix instruction for quality.readability"""
        fix = critique_default._generate_fix_instruction(
            "quality.readability",
            "Poor readability",
            "artifact"
        )
        assert "comment" in fix.lower() or "docstring" in fix.lower()

    def test_type_hints_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.type_hints (code gen)"""
        fix = critique_default._generate_fix_instruction(
            "correctness.type_hints",
            "Missing type hints",
            "artifact"
        )
        assert "type hint" in fix.lower() or "type annotation" in fix.lower()

    def test_field_types_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.field_types (config)"""
        fix = critique_default._generate_fix_instruction(
            "correctness.field_types",
            "Wrong field types",
            "artifact"
        )
        assert "field" in fix.lower() or "types" in fix.lower()

    def test_structure_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.structure"""
        fix = critique_default._generate_fix_instruction(
            "correctness.structure",
            "Poor structure",
            "artifact"
        )
        assert "structure" in fix.lower() or "module" in fix.lower()

    def test_input_validation_fix_instruction(self, critique_default):
        """Test fix instruction for security.input_validation"""
        fix = critique_default._generate_fix_instruction(
            "security.input_validation",
            "No input validation",
            "artifact"
        )
        assert "validat" in fix.lower()

    def test_secrets_fix_instruction(self, critique_default):
        """Test fix instruction for security.secrets"""
        fix = critique_default._generate_fix_instruction(
            "security.secrets",
            "Hardcoded secrets",
            "artifact"
        )
        assert "secret" in fix.lower()
        assert "environment" in fix.lower() or "env" in fix.lower()

    def test_complexity_fix_instruction(self, critique_default):
        """Test fix instruction for performance.complexity"""
        fix = critique_default._generate_fix_instruction(
            "performance.complexity",
            "High complexity",
            "artifact"
        )
        assert "complex" in fix.lower()

    def test_logging_fix_instruction(self, critique_default):
        """Test fix instruction for quality.logging"""
        fix = critique_default._generate_fix_instruction(
            "quality.logging",
            "No logging",
            "artifact"
        )
        assert "log" in fix.lower()

    def test_imports_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.imports"""
        fix = critique_default._generate_fix_instruction(
            "correctness.imports",
            "Messy imports",
            "artifact"
        )
        assert "import" in fix.lower()

    def test_caching_fix_instruction(self, critique_default):
        """Test fix instruction for performance.caching"""
        fix = critique_default._generate_fix_instruction(
            "performance.caching",
            "No caching",
            "artifact"
        )
        assert "cach" in fix.lower()


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Security Rules
# ============================================================================

class TestFixInstructionsSecurity:
    """Tests for Security template fix instructions"""

    def test_no_hardcoded_secrets(self, critique_default):
        """Test fix instruction for security.no_hardcoded_secrets"""
        fix = critique_default._generate_fix_instruction(
            "security.no_hardcoded_secrets",
            "Hardcoded secrets found",
            "artifact"
        )
        assert "environment variable" in fix.lower()
        assert "secret" in fix.lower()

    def test_sql_injection_prevention(self, critique_default):
        """Test fix instruction for security.sql_injection_prevention"""
        fix = critique_default._generate_fix_instruction(
            "security.sql_injection_prevention",
            "SQL injection risk",
            "artifact"
        )
        assert "parameterized" in fix.lower()
        assert "sql" in fix.lower()

    def test_xss_prevention(self, critique_default):
        """Test fix instruction for security.xss_prevention"""
        fix = critique_default._generate_fix_instruction(
            "security.xss_prevention",
            "XSS vulnerability",
            "artifact"
        )
        assert "xss" in fix.lower()
        assert "escap" in fix.lower() or "encod" in fix.lower()

    def test_authentication(self, critique_default):
        """Test fix instruction for security.authentication"""
        fix = critique_default._generate_fix_instruction(
            "security.authentication",
            "No authentication",
            "artifact"
        )
        assert "auth" in fix.lower()
        assert "middleware" in fix.lower() or "guard" in fix.lower()

    def test_authorization(self, critique_default):
        """Test fix instruction for security.authorization"""
        fix = critique_default._generate_fix_instruction(
            "security.authorization",
            "No authorization checks",
            "artifact"
        )
        assert "permission" in fix.lower()
        assert "403" in fix or "rbac" in fix.lower() or "access control" in fix.lower()

    def test_https_only(self, critique_default):
        """Test fix instruction for security.https_only"""
        fix = critique_default._generate_fix_instruction(
            "security.https_only",
            "HTTP allowed",
            "artifact"
        )
        assert "https" in fix.lower()
        assert "hsts" in fix.lower() or "redirect" in fix.lower()

    def test_csrf_protection(self, critique_default):
        """Test fix instruction for security.csrf_protection"""
        fix = critique_default._generate_fix_instruction(
            "security.csrf_protection",
            "No CSRF protection",
            "artifact"
        )
        assert "csrf" in fix.lower()
        assert "token" in fix.lower() or "samesite" in fix.lower()

    def test_error_handling(self, critique_default):
        """Test fix instruction for security.error_handling"""
        fix = critique_default._generate_fix_instruction(
            "security.error_handling",
            "Stack traces exposed",
            "artifact"
        )
        assert "error" in fix.lower()
        assert "stack trace" in fix.lower() or "generic" in fix.lower()

    def test_dependencies(self, critique_default):
        """Test fix instruction for security.dependencies"""
        fix = critique_default._generate_fix_instruction(
            "security.dependencies",
            "Vulnerable dependencies",
            "artifact"
        )
        assert "audit" in fix.lower()
        assert "vulnerabilit" in fix.lower() or "update" in fix.lower()

    def test_cors_configuration(self, critique_default):
        """Test fix instruction for security.cors_configuration"""
        fix = critique_default._generate_fix_instruction(
            "security.cors_configuration",
            "CORS misconfigured",
            "artifact"
        )
        assert "cors" in fix.lower()
        assert "origin" in fix.lower()

    def test_csp_headers(self, critique_default):
        """Test fix instruction for security.csp_headers"""
        fix = critique_default._generate_fix_instruction(
            "security.csp_headers",
            "No CSP headers",
            "artifact"
        )
        assert "content security policy" in fix.lower() or "csp" in fix.lower()
        assert "default-src" in fix.lower() or "script-src" in fix.lower()

    def test_rate_limiting(self, critique_default):
        """Test fix instruction for security.rate_limiting"""
        fix = critique_default._generate_fix_instruction(
            "security.rate_limiting",
            "No rate limiting",
            "artifact"
        )
        assert "rate limit" in fix.lower()
        assert "429" in fix

    def test_jwt_token_handling(self, critique_default):
        """Test fix instruction for security.jwt_token_handling"""
        fix = critique_default._generate_fix_instruction(
            "security.jwt_token_handling",
            "Insecure JWT handling",
            "artifact"
        )
        assert "jwt" in fix.lower()
        assert "expir" in fix.lower() or "signature" in fix.lower()

    def test_api_key_management(self, critique_default):
        """Test fix instruction for security.api_key_management"""
        fix = critique_default._generate_fix_instruction(
            "security.api_key_management",
            "API keys mismanaged",
            "artifact"
        )
        assert "api key" in fix.lower()
        assert "rotation" in fix.lower() or "permission" in fix.lower()

    def test_env_variable_usage(self, critique_default):
        """Test fix instruction for security.env_variable_usage"""
        fix = critique_default._generate_fix_instruction(
            "security.env_variable_usage",
            "Hardcoded config",
            "artifact"
        )
        assert "environment variable" in fix.lower() or "env var" in fix.lower()
        assert ".gitignore" in fix.lower() or ".env" in fix.lower()

    def test_secret_rotation(self, critique_default):
        """Test fix instruction for security.secret_rotation"""
        fix = critique_default._generate_fix_instruction(
            "security.secret_rotation",
            "No rotation policy",
            "artifact"
        )
        assert "rotation" in fix.lower()
        assert "certificate" in fix.lower() or "key" in fix.lower()

    def test_all_security_rules_have_specific_instructions(self, critique_default):
        """Verify all security.yml rule IDs have specific (not generic) fix instructions"""
        security_rule_ids = [
            "security.no_hardcoded_secrets",
            "security.input_validation",
            "security.sql_injection_prevention",
            "security.xss_prevention",
            "security.authentication",
            "security.authorization",
            "security.https_only",
            "security.csrf_protection",
            "security.error_handling",
            "security.dependencies",
            "security.cors_configuration",
            "security.csp_headers",
            "security.rate_limiting",
            "security.jwt_token_handling",
            "security.api_key_management",
            "security.env_variable_usage",
            "security.secret_rotation",
        ]
        for rule_id in security_rule_ids:
            fix = critique_default._generate_fix_instruction(rule_id, "test", "art")
            # Should NOT be generic (generic contains "Fix issue:")
            assert "Fix issue:" not in fix, (
                f"{rule_id} falls through to generic fix instruction"
            )


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Frontend Rules
# ============================================================================

class TestFixInstructionsFrontend:
    """Tests for Frontend template fix instructions"""

    def test_components_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.components"""
        fix = critique_default._generate_fix_instruction(
            "correctness.components", "No component structure", "artifact"
        )
        assert "component" in fix.lower()
        assert "export" in fix.lower() or "functional" in fix.lower()

    def test_state_management_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.state_management"""
        fix = critique_default._generate_fix_instruction(
            "correctness.state_management", "No state management", "artifact"
        )
        assert "state" in fix.lower()
        assert "useState" in fix or "useReducer" in fix

    def test_props_validation_fix_instruction(self, critique_default):
        """Test fix instruction for quality.props_validation"""
        fix = critique_default._generate_fix_instruction(
            "quality.props_validation", "No prop types", "artifact"
        )
        assert "prop" in fix.lower()
        assert "TypeScript" in fix or "PropTypes" in fix

    def test_routing_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.routing"""
        fix = critique_default._generate_fix_instruction(
            "correctness.routing", "No routing", "artifact"
        )
        assert "route" in fix.lower() or "router" in fix.lower()

    def test_responsive_fix_instruction(self, critique_default):
        """Test fix instruction for quality.responsive"""
        fix = critique_default._generate_fix_instruction(
            "quality.responsive", "Not responsive", "artifact"
        )
        assert "responsive" in fix.lower() or "media quer" in fix.lower()

    def test_alt_text_fix_instruction(self, critique_default):
        """Test fix instruction for accessibility.alt_text"""
        fix = critique_default._generate_fix_instruction(
            "accessibility.alt_text", "Missing alt text", "artifact"
        )
        assert "alt" in fix.lower()
        assert "img" in fix.lower() or "image" in fix.lower()

    def test_lazy_loading_fix_instruction(self, critique_default):
        """Test fix instruction for performance.lazy_loading"""
        fix = critique_default._generate_fix_instruction(
            "performance.lazy_loading", "No lazy loading", "artifact"
        )
        assert "lazy" in fix.lower()
        assert "React.lazy" in fix or "dynamic import" in fix.lower()

    def test_semantic_html_fix_instruction(self, critique_default):
        """Test fix instruction for quality.semantic_html"""
        fix = critique_default._generate_fix_instruction(
            "quality.semantic_html", "No semantic HTML", "artifact"
        )
        assert "semantic" in fix.lower() or "header" in fix.lower()
        assert "div" in fix.lower()

    def test_css_organization_fix_instruction(self, critique_default):
        """Test fix instruction for quality.css_organization"""
        fix = critique_default._generate_fix_instruction(
            "quality.css_organization", "CSS disorganized", "artifact"
        )
        assert "css" in fix.lower()
        assert "module" in fix.lower() or "scop" in fix.lower()

    def test_react_hooks_optimization_fix_instruction(self, critique_default):
        """Test fix instruction for performance.react_hooks_optimization"""
        fix = critique_default._generate_fix_instruction(
            "performance.react_hooks_optimization", "Unoptimized hooks", "artifact"
        )
        assert "useMemo" in fix or "useCallback" in fix

    def test_error_boundaries_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.error_boundaries"""
        fix = critique_default._generate_fix_instruction(
            "correctness.error_boundaries", "No error boundaries", "artifact"
        )
        assert "error" in fix.lower()
        assert "boundary" in fix.lower() or "ErrorBoundary" in fix

    def test_component_composition_fix_instruction(self, critique_default):
        """Test fix instruction for quality.component_composition"""
        fix = critique_default._generate_fix_instruction(
            "quality.component_composition", "Using inheritance", "artifact"
        )
        assert "composition" in fix.lower()
        assert "children" in fix.lower() or "render prop" in fix.lower()

    def test_api_integration_fix_instruction(self, critique_default):
        """Test fix instruction for quality.api_integration"""
        fix = critique_default._generate_fix_instruction(
            "quality.api_integration", "Poor API handling", "artifact"
        )
        assert "loading" in fix.lower() or "error" in fix.lower()
        assert "api" in fix.lower()

    def test_form_validation_fix_instruction(self, critique_default):
        """Test fix instruction for quality.form_validation"""
        fix = critique_default._generate_fix_instruction(
            "quality.form_validation", "No form validation", "artifact"
        )
        assert "validat" in fix.lower()
        assert "form" in fix.lower()

    def test_environment_config_fix_instruction(self, critique_default):
        """Test fix instruction for quality.environment_config"""
        fix = critique_default._generate_fix_instruction(
            "quality.environment_config", "Hardcoded config", "artifact"
        )
        assert "environment" in fix.lower()
        assert ".env" in fix.lower() or "env" in fix.lower()

    def test_state_persistence_fix_instruction(self, critique_default):
        """Test fix instruction for quality.state_persistence"""
        fix = critique_default._generate_fix_instruction(
            "quality.state_persistence", "No persistence handling", "artifact"
        )
        assert "localStorage" in fix or "sessionStorage" in fix or "storage" in fix.lower()
        assert "try" in fix.lower() or "catch" in fix.lower() or "fallback" in fix.lower()

    def test_all_frontend_rules_have_specific_instructions(self, critique_default):
        """Verify all frontend.yml rule IDs have specific fix instructions"""
        frontend_rule_ids = [
            "correctness.components",
            "correctness.state_management",
            "quality.props_validation",
            "correctness.routing",
            "quality.responsive",
            "accessibility.alt_text",
            "performance.lazy_loading",
            "quality.semantic_html",
            "security.xss_prevention",
            "quality.css_organization",
            "performance.react_hooks_optimization",
            "correctness.error_boundaries",
            "quality.component_composition",
            "quality.api_integration",
            "quality.form_validation",
            "quality.environment_config",
            "quality.state_persistence",
        ]
        for rule_id in frontend_rule_ids:
            fix = critique_default._generate_fix_instruction(rule_id, "test", "art")
            assert "Fix issue:" not in fix, (
                f"{rule_id} falls through to generic fix instruction"
            )


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Backend Rules (Exp 26)
# ============================================================================

class TestFixInstructionsBackend:
    """Tests for Backend template fix instructions"""

    def test_api_structure_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.api_structure", "No REST structure", "artifact"
        )
        assert "rest" in fix.lower() or "http" in fix.lower()
        assert "GET" in fix or "POST" in fix

    def test_service_layer_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.service_layer", "No service layer", "artifact"
        )
        assert "service" in fix.lower()
        assert "controller" in fix.lower() or "business" in fix.lower()

    def test_dependency_injection_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.dependency_injection", "No DI", "artifact"
        )
        assert "inject" in fix.lower() or "constructor" in fix.lower()

    def test_error_responses_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.error_responses", "Bad error format", "artifact"
        )
        assert "error" in fix.lower()
        assert "status" in fix.lower() or "code" in fix.lower()

    def test_validation_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.validation", "No validation", "artifact"
        )
        assert "validat" in fix.lower()

    def test_async_operations_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "performance.async_operations", "No async", "artifact"
        )
        assert "async" in fix.lower() or "await" in fix.lower()

    def test_http_status_codes_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.http_status_codes", "Wrong status codes", "artifact"
        )
        assert "200" in fix or "201" in fix or "status" in fix.lower()

    def test_content_negotiation_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.content_negotiation", "No content negotiation", "artifact"
        )
        assert "accept" in fix.lower() or "content-type" in fix.lower()

    def test_resource_naming_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.resource_naming", "Bad naming", "artifact"
        )
        assert "plural" in fix.lower() or "resource" in fix.lower()

    def test_rate_limiting_backend_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.rate_limiting", "No rate limiting", "artifact"
        )
        assert "rate" in fix.lower() or "limit" in fix.lower()
        assert "429" in fix

    def test_cors_configuration_backend_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.cors_configuration", "No CORS", "artifact"
        )
        assert "cors" in fix.lower() or "origin" in fix.lower()

    def test_security_headers_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.security_headers", "Missing headers", "artifact"
        )
        assert "x-content-type" in fix.lower() or "x-frame" in fix.lower() or "security" in fix.lower()

    def test_domain_errors_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.domain_errors", "No domain errors", "artifact"
        )
        assert "domain" in fix.lower() or "422" in fix or "400" in fix

    def test_error_consistency_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.error_consistency", "Inconsistent errors", "artifact"
        )
        assert "error" in fix.lower()
        assert "request_id" in fix.lower() or "code" in fix.lower()

    def test_stack_trace_sanitization_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "security.stack_trace_sanitization", "Stack trace exposed", "artifact"
        )
        assert "stack" in fix.lower() or "production" in fix.lower()

    def test_api_versioning_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.api_versioning", "No versioning", "artifact"
        )
        assert "version" in fix.lower()
        assert "/v1" in fix.lower() or "v1" in fix.lower()

    def test_schema_validation_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "correctness.schema_validation", "No schema validation", "artifact"
        )
        assert "schema" in fix.lower() or "validat" in fix.lower()

    def test_idempotency_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.idempotency", "No idempotency", "artifact"
        )
        assert "idempoten" in fix.lower()

    def test_all_backend_non_graphql_rules_have_specific_instructions(self, critique_default):
        """Verify all non-GraphQL backend.yml rule IDs have specific fix instructions"""
        backend_rule_ids = [
            "correctness.api_structure",
            "correctness.service_layer",
            "correctness.dependency_injection",
            "quality.error_responses",
            "correctness.validation",
            "quality.logging",
            "security.authentication",
            "security.authorization",
            "performance.caching",
            "performance.async_operations",
            "quality.http_status_codes",
            "correctness.content_negotiation",
            "quality.resource_naming",
            "quality.rate_limiting",
            "quality.cors_configuration",
            "quality.security_headers",
            "quality.domain_errors",
            "quality.error_consistency",
            "security.stack_trace_sanitization",
            "quality.api_versioning",
            "correctness.schema_validation",
            "quality.idempotency",
        ]
        for rule_id in backend_rule_ids:
            fix = critique_default._generate_fix_instruction(rule_id, "test", "art")
            assert "Fix issue:" not in fix, (
                f"{rule_id} falls through to generic fix instruction"
            )


class TestFixInstructionsBackendGraphQL:
    """Tests for Backend GraphQL fix instructions (Exp 26)"""

    def test_graphql_n_plus1_prevention_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_n_plus1_prevention", "N+1 detected", "artifact"
        )
        assert "dataloader" in fix.lower() or "batch" in fix.lower()

    def test_graphql_error_handling_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_error_handling", "Bad errors", "artifact"
        )
        assert "error" in fix.lower()
        assert "extensions" in fix.lower() or "code" in fix.lower()

    def test_graphql_pagination_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_pagination", "No pagination", "artifact"
        )
        assert "cursor" in fix.lower() or "connection" in fix.lower() or "pageinfo" in fix.lower()

    def test_graphql_subscriptions_auth_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_subscriptions_auth", "No sub auth", "artifact"
        )
        assert "websocket" in fix.lower() or "subscription" in fix.lower()
        assert "auth" in fix.lower()

    def test_graphql_description_documentation_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_description_documentation", "No docs", "artifact"
        )
        assert "description" in fix.lower() or "deprecated" in fix.lower()

    def test_graphql_federation_consistency_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "quality.graphql_federation_consistency", "Bad federation", "artifact"
        )
        assert "@key" in fix.lower() or "federation" in fix.lower() or "entity" in fix.lower()

    def test_graphql_query_cost_analysis_fix_instruction(self, critique_default):
        fix = critique_default._generate_fix_instruction(
            "performance.graphql_query_cost_analysis", "No cost analysis", "artifact"
        )
        assert "cost" in fix.lower() or "weight" in fix.lower()

    def test_all_backend_graphql_rules_have_specific_instructions(self, critique_default):
        """Verify all GraphQL backend.yml rule IDs have specific fix instructions"""
        graphql_rule_ids = [
            "quality.graphql_n_plus1_prevention",
            "quality.graphql_error_handling",
            "quality.graphql_pagination",
            "quality.graphql_subscriptions_auth",
            "quality.graphql_description_documentation",
            "quality.graphql_federation_consistency",
            "performance.graphql_query_cost_analysis",
        ]
        for rule_id in graphql_rule_ids:
            fix = critique_default._generate_fix_instruction(rule_id, "test", "art")
            assert "Fix issue:" not in fix, (
                f"{rule_id} falls through to generic fix instruction"
            )


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Docs Rules
# ============================================================================

class TestFixInstructionsDocs:
    """Tests for Docs fix instructions"""

    def test_title_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.title"""
        fix = critique_default._generate_fix_instruction(
            "correctness.title",
            "Missing title",
            "artifact"
        )
        assert "title" in fix.lower()

    def test_purpose_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.purpose"""
        fix = critique_default._generate_fix_instruction(
            "correctness.purpose",
            "Missing purpose",
            "artifact"
        )
        assert "overview" in fix.lower() or "introduction" in fix.lower()

    def test_installation_fix_instruction(self, critique_default):
        """Test fix instruction for quality.installation"""
        fix = critique_default._generate_fix_instruction(
            "quality.installation",
            "Missing installation docs",
            "artifact"
        )
        assert "installation" in fix.lower() or "install" in fix.lower()

    def test_usage_fix_instruction(self, critique_default):
        """Test fix instruction for quality.usage"""
        fix = critique_default._generate_fix_instruction(
            "quality.usage",
            "Missing usage docs",
            "artifact"
        )
        assert "usage" in fix.lower() or "example" in fix.lower()

    def test_structure_docs_fix_instruction(self, critique_default):
        """Test fix instruction for quality.structure (docs)"""
        fix = critique_default._generate_fix_instruction(
            "quality.structure",
            "Poor heading hierarchy",
            "artifact"
        )
        assert "heading" in fix.lower() or "##" in fix

    def test_spelling_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.spelling"""
        fix = critique_default._generate_fix_instruction(
            "correctness.spelling",
            "Spelling errors",
            "artifact"
        )
        assert "spell" in fix.lower()

    def test_code_blocks_fix_instruction(self, critique_default):
        """Test fix instruction for quality.code_blocks"""
        fix = critique_default._generate_fix_instruction(
            "quality.code_blocks",
            "Poor code blocks",
            "artifact"
        )
        assert "```" in fix or "code" in fix.lower()

    def test_links_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.links (Exp 31)"""
        fix = critique_default._generate_fix_instruction(
            "correctness.links",
            "No valid links",
            "artifact"
        )
        assert "link" in fix.lower() or "[text](url)" in fix


# ============================================================================
# Tests for FIX_INSTRUCTIONS - Config Rules
# ============================================================================

class TestFixInstructionsConfig:
    """Tests for Config fix instructions"""

    def test_syntax_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.syntax"""
        fix = critique_default._generate_fix_instruction(
            "correctness.syntax",
            "Syntax error",
            "artifact"
        )
        assert "syntax" in fix.lower() or "yaml" in fix.lower() or "json" in fix.lower()

    def test_required_fields_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.required_fields"""
        fix = critique_default._generate_fix_instruction(
            "correctness.required_fields",
            "Missing required fields",
            "artifact"
        )
        assert "required" in fix.lower() or "field" in fix.lower()

    def test_paths_fix_instruction(self, critique_default):
        """Test fix instruction for correctness.paths"""
        fix = critique_default._generate_fix_instruction(
            "correctness.paths",
            "Invalid path",
            "artifact"
        )
        assert "path" in fix.lower()

    def test_defaults_fix_instruction(self, critique_default):
        """Test fix instruction for quality.defaults"""
        fix = critique_default._generate_fix_instruction(
            "quality.defaults",
            "Missing defaults",
            "artifact"
        )
        assert "default" in fix.lower()

    def test_environment_vars_fix_instruction(self, critique_default):
        """Test fix instruction for quality.environment_vars"""
        fix = critique_default._generate_fix_instruction(
            "quality.environment_vars",
            "Hardcoded values",
            "artifact"
        )
        assert "environment" in fix.lower() or "${" in fix


# ============================================================================
# Tests for Generic Fix Instruction
# ============================================================================

class TestGenericFixInstruction:
    """Tests for generic fix instruction fallback"""

    def test_unknown_rule_id_uses_generic(self, critique_default):
        """Test unknown rule_id returns generic fix"""
        fix = critique_default._generate_fix_instruction(
            "unknown.rule.id",
            "Some reason",
            "artifact content"
        )
        # Generic fix includes the reason
        assert "Some reason" in fix

    def test_generic_fix_includes_rule_id(self, critique_default):
        """Test generic fix includes rule_id"""
        fix = critique_default._generate_fix_instruction(
            "custom.rule.123",
            "Custom reason",
            "artifact"
        )
        assert "custom.rule.123" in fix

    def test_generic_fix_has_steps(self, critique_default):
        """Test generic fix has numbered steps"""
        fix = critique_default._generate_fix_instruction(
            "unknown.rule",
            "Test reason",
            "artifact"
        )
        # Should have numbered steps
        assert "1." in fix or "2." in fix or "3." in fix

    def test_generic_with_empty_artifact(self, critique_default):
        """Test generic fix with empty artifact"""
        fix = critique_default._generate_fix_instruction(
            "unknown.rule",
            "Test reason",
            ""
        )
        assert "Test reason" in fix

    def test_generic_with_special_chars_in_reason(self, critique_default):
        """Test generic fix handles special characters"""
        fix = critique_default._generate_fix_instruction(
            "test.rule",
            "Reason with <special> & \"chars\"",
            "artifact"
        )
        assert "special" in fix


# ============================================================================
# Tests for _generate_fix_instruction Method
# ============================================================================

class TestGenerateFixInstructionMethod:
    """Tests for _generate_fix_instruction method"""

    def test_returns_string(self, critique_default):
        """Test method always returns string"""
        fix = critique_default._generate_fix_instruction(
            "any.rule",
            "reason",
            "artifact"
        )
        assert isinstance(fix, str)

    def test_non_empty_result(self, critique_default):
        """Test method never returns empty string"""
        fix = critique_default._generate_fix_instruction(
            "any.rule",
            "reason",
            "artifact"
        )
        assert len(fix) > 0

    def test_artifact_parameter_used(self, critique_default):
        """Test artifact is accepted (even if not used in current impl)"""
        # Should not raise
        fix = critique_default._generate_fix_instruction(
            "any.rule",
            "reason",
            "long artifact content " * 100
        )
        assert fix is not None


# ============================================================================
# Tests for Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_max_issues_zero(self):
        """Test critique with max_issues=0"""
        critique = Critique(max_issues=0)
        failed_rules = [{"rule_id": "test", "reason": "test"}]
        result = critique.generate(failed_rules, "artifact")

        assert result.total_failed == 1
        assert result.addressed == 0
        assert result.skipped == 1
        assert result.issues == []

    def test_very_long_reason(self, critique_default):
        """Test with very long reason string"""
        long_reason = "x" * 10000
        result = critique_default.generate(
            [{"rule_id": "test", "reason": long_reason}],
            "artifact"
        )
        assert result.issues[0]["reason"] == long_reason

    def test_very_long_artifact(self, critique_default):
        """Test with very long artifact"""
        long_artifact = "x" * 100000
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            long_artifact
        )
        assert result.total_failed == 1

    def test_unicode_in_reason(self, critique_default):
        """Test with unicode characters in reason"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "Ошибка: 数据错误 🚨"}],
            "artifact"
        )
        assert result.issues[0]["reason"] == "Ошибка: 数据错误 🚨"

    def test_unicode_in_artifact(self, critique_default):
        """Test with unicode characters in artifact"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            "Artifact with unicode: 你好 мир 🎉"
        )
        assert result.total_failed == 1

    def test_special_chars_in_rule_id(self, critique_default):
        """Test with special characters in rule_id"""
        result = critique_default.generate(
            [{"rule_id": "test.rule-with_special.chars:123", "reason": "test"}],
            "artifact"
        )
        assert result.issues[0]["rule_id"] == "test.rule-with_special.chars:123"

    def test_empty_reason(self, critique_default):
        """Test with empty reason string"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": ""}],
            "artifact"
        )
        assert result.issues[0]["reason"] == ""

    def test_many_failed_rules(self, critique_unlimited):
        """Test with many failed rules"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(100)
        ]
        result = critique_unlimited.generate(failed_rules, "artifact")

        assert result.total_failed == 100
        assert result.addressed == 100
        assert len(result.issues) == 100


# ============================================================================
# Tests for Result Structure
# ============================================================================

class TestResultStructure:
    """Tests for result structure validation"""

    def test_result_has_required_keys(self, critique_default):
        """Test result has all required keys"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            "artifact"
        )

        assert hasattr(result, "issues")
        assert hasattr(result, "total_failed")
        assert hasattr(result, "addressed")
        assert hasattr(result, "skipped")

    def test_result_types(self, critique_default):
        """Test result value types"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            "artifact"
        )

        assert isinstance(result.issues, list)
        assert isinstance(result.total_failed, int)
        assert isinstance(result.addressed, int)
        assert isinstance(result.skipped, int)

    def test_math_consistency(self, critique_default):
        """Test that addressed + skipped = total_failed"""
        for num_rules in [0, 1, 5, 10, 20]:
            failed_rules = [
                {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
                for i in range(num_rules)
            ]
            result = critique_default.generate(failed_rules, "artifact")

            assert result.addressed + result.skipped == result.total_failed

    def test_addressed_equals_issues_count(self, critique_default):
        """Test that addressed count matches issues list length"""
        for num_rules in [0, 1, 3, 5, 10]:
            failed_rules = [
                {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
                for i in range(num_rules)
            ]
            result = critique_default.generate(failed_rules, "artifact")

            assert result.addressed == len(result.issues)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Critique module"""

    def test_full_workflow_api_spec(self, critique_default, sample_artifact_api):
        """Test full workflow with API spec artifact"""
        failed_rules = [
            {"rule_id": "correctness.endpoints", "reason": "Missing DELETE endpoint"},
            {"rule_id": "correctness.status_codes", "reason": "Missing 201 status"},
            {"rule_id": "correctness.auth", "reason": "No auth documentation"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_api)

        assert result.total_failed == 3
        assert all("fix" in issue for issue in result.issues)

    def test_full_workflow_code(self, critique_default, sample_artifact_code):
        """Test full workflow with code artifact"""
        failed_rules = [
            {"rule_id": "correctness.tests", "reason": "No unit tests"},
            {"rule_id": "correctness.type_hints", "reason": "Missing type hints"},
            {"rule_id": "quality.error_handling", "reason": "No error handling"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_code)

        assert result.total_failed == 3
        for issue in result.issues:
            assert issue["fix"] is not None

    def test_full_workflow_docs(self, critique_default, sample_artifact_docs):
        """Test full workflow with docs artifact"""
        failed_rules = [
            {"rule_id": "quality.installation", "reason": "No installation guide"},
            {"rule_id": "quality.usage", "reason": "No usage examples"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_docs)

        assert result.total_failed == 2

    def test_full_workflow_config(self, critique_default, sample_artifact_config):
        """Test full workflow with config artifact"""
        failed_rules = [
            {"rule_id": "quality.defaults", "reason": "Missing default values"},
            {"rule_id": "quality.environment_vars", "reason": "Hardcoded host"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_config)

        assert result.total_failed == 2

    def test_mixed_rule_types(self, critique_default):
        """Test with mixed known and unknown rule types"""
        failed_rules = [
            {"rule_id": "correctness.tests", "reason": "Known rule"},
            {"rule_id": "custom.unknown.rule", "reason": "Unknown rule"},
            {"rule_id": "security.secrets", "reason": "Another known rule"},
        ]

        result = critique_default.generate(failed_rules, "artifact")

        assert result.total_failed == 3
        # Known rules should have specific instructions
        assert "test" in result.issues[0]["fix"].lower()
        # Unknown rule should have generic instruction
        assert "custom.unknown.rule" in result.issues[1]["fix"]


# ============================================================================
# Tests for FIX_INSTRUCTIONS Coverage
# ============================================================================

class TestFixInstructionsCoverage:
    """Tests to ensure all FIX_INSTRUCTIONS are valid"""

    def test_all_fix_instructions_are_strings(self, critique_default):
        """Test all FIX_INSTRUCTIONS values are non-empty strings"""
        for rule_id, instruction in critique_default.FIX_INSTRUCTIONS.items():
            assert isinstance(instruction, str), f"Instruction for {rule_id} is not a string"
            assert len(instruction) > 0, f"Instruction for {rule_id} is empty"

    def test_fix_instructions_have_steps(self, critique_default):
        """Test all FIX_INSTRUCTIONS have numbered steps"""
        for rule_id, instruction in critique_default.FIX_INSTRUCTIONS.items():
            # Most instructions should have numbered steps
            has_steps = "1." in instruction or "2." in instruction
            assert has_steps, f"Instruction for {rule_id} lacks numbered steps"

    def test_all_fix_instructions_accessible(self, critique_default):
        """Test all FIX_INSTRUCTIONS are accessible via method"""
        for rule_id in critique_default.FIX_INSTRUCTIONS.keys():
            fix = critique_default._generate_fix_instruction(
                rule_id,
                "Test reason",
                "artifact"
            )
            # Should return the specific instruction, not generic
            assert fix == critique_default.FIX_INSTRUCTIONS[rule_id]


class TestTestingFixInstructions:
    """Test FIX_INSTRUCTIONS for testing.yml template rules (Exp 30)"""

    @pytest.fixture
    def critique(self):
        return Critique()

    TESTING_RULE_IDS = [
        "correctness.test_structure",
        "correctness.assertions",
        "quality.test_isolation",
        "correctness.edge_cases",
        "quality.mocks_usage",
        "correctness.error_tests",
        "quality.coverage",
        "testing.e2e_coverage",
        "testing.component_testing",
    ]

    def test_all_testing_rules_have_fix_instructions(self, critique):
        """All testing Phase A rules have specific FIX_INSTRUCTIONS"""
        for rule_id in self.TESTING_RULE_IDS:
            assert rule_id in critique.FIX_INSTRUCTIONS, f"Missing FIX_INSTRUCTION for {rule_id}"

    def test_testing_instructions_have_numbered_steps(self, critique):
        """All testing FIX_INSTRUCTIONS have actionable steps"""
        for rule_id in self.TESTING_RULE_IDS:
            instruction = critique.FIX_INSTRUCTIONS[rule_id]
            assert "1." in instruction, f"No steps in {rule_id}"
            assert "2." in instruction, f"Less than 2 steps in {rule_id}"

    def test_test_structure_mentions_aaa(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["correctness.test_structure"]
        assert "arrange" in instruction.lower() or "assert" in instruction.lower()

    def test_assertions_mentions_specific(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["correctness.assertions"]
        assert "assert" in instruction.lower()

    def test_isolation_mentions_fixture(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["quality.test_isolation"]
        assert "fixture" in instruction.lower() or "setup" in instruction.lower()

    def test_edge_cases_mentions_null(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["correctness.edge_cases"]
        assert "null" in instruction.lower() or "none" in instruction.lower()

    def test_mocks_mentions_mock(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["quality.mocks_usage"]
        assert "mock" in instruction.lower()

    def test_error_tests_mentions_raises(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["correctness.error_tests"]
        assert "raises" in instruction.lower() or "exception" in instruction.lower()

    def test_coverage_mentions_threshold(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["quality.coverage"]
        assert "coverage" in instruction.lower()

    def test_e2e_mentions_playwright(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["testing.e2e_coverage"]
        assert "playwright" in instruction.lower() or "cypress" in instruction.lower()

    def test_component_mentions_testing_library(self, critique):
        instruction = critique.FIX_INSTRUCTIONS["testing.component_testing"]
        assert "testing-library" in instruction.lower() or "component" in instruction.lower()


# ============================================================================
# Exp 37: Weight-Based Priority Sorting Tests
# ============================================================================

class TestCritiquePrioritySorting:
    """Test that critique sorts failed rules by weight (descending)"""

    @pytest.fixture
    def critique(self):
        return Critique(max_issues=3)

    def test_high_weight_rules_come_first(self, critique):
        """High-weight rules should be addressed before low-weight ones"""
        failed = [
            {"rule_id": "quality.readability", "reason": "Low weight", "weight": 1},
            {"rule_id": "security.secrets", "reason": "High weight", "weight": 2},
            {"rule_id": "quality.logging", "reason": "Low weight", "weight": 1},
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["rule_id"] == "security.secrets"

    def test_sorting_with_mixed_weights(self, critique):
        """Rules with higher weight should always appear first"""
        failed = [
            {"rule_id": "a", "reason": "r1", "weight": 1},
            {"rule_id": "b", "reason": "r2", "weight": 2},
            {"rule_id": "c", "reason": "r3", "weight": 2},
            {"rule_id": "d", "reason": "r4", "weight": 1},
        ]
        result = critique.generate(failed, "artifact")
        # max_issues=3, so weight-2 rules should be first
        ids = [i["rule_id"] for i in result.issues]
        assert ids[0] in ("b", "c")
        assert ids[1] in ("b", "c")

    def test_sorting_preserves_all_when_no_truncation(self):
        """When all rules fit, sorting still applies"""
        critique = Critique(max_issues=10)
        failed = [
            {"rule_id": "low", "reason": "r", "weight": 1},
            {"rule_id": "high", "reason": "r", "weight": 2},
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["rule_id"] == "high"
        assert result.issues[1]["rule_id"] == "low"

    def test_truncation_drops_low_weight_rules(self):
        """When truncating, low-weight rules are dropped first"""
        critique = Critique(max_issues=2)
        failed = [
            {"rule_id": "low1", "reason": "r", "weight": 1},
            {"rule_id": "high1", "reason": "r", "weight": 2},
            {"rule_id": "low2", "reason": "r", "weight": 1},
            {"rule_id": "high2", "reason": "r", "weight": 2},
        ]
        result = critique.generate(failed, "artifact")
        ids = [i["rule_id"] for i in result.issues]
        assert "high1" in ids
        assert "high2" in ids
        assert "low1" not in ids
        assert "low2" not in ids

    def test_default_weight_is_one(self, critique):
        """Rules without explicit weight default to 1"""
        failed = [
            {"rule_id": "no_weight", "reason": "r"},
            {"rule_id": "has_weight", "reason": "r", "weight": 2},
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["rule_id"] == "has_weight"

    def test_equal_weights_preserves_order(self, critique):
        """Same-weight rules maintain relative order (stable sort)"""
        failed = [
            {"rule_id": "first", "reason": "r", "weight": 1},
            {"rule_id": "second", "reason": "r", "weight": 1},
            {"rule_id": "third", "reason": "r", "weight": 1},
        ]
        result = critique.generate(failed, "artifact")
        ids = [i["rule_id"] for i in result.issues]
        assert ids == ["first", "second", "third"]


class TestCritiqueCategoryInOutput:
    """Test that critique includes category field in output"""

    @pytest.fixture
    def critique(self):
        return Critique()

    def test_category_included_in_issues(self, critique):
        """Each issue should include category from failed rule"""
        failed = [
            {"rule_id": "security.secrets", "reason": "r", "category": "security"},
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["category"] == "security"

    def test_category_defaults_to_general(self, critique):
        """Category defaults to 'general' when not provided"""
        failed = [
            {"rule_id": "some.rule", "reason": "r"},
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["category"] == "general"

    def test_multiple_categories(self, critique):
        """Different categories are preserved per issue"""
        failed = [
            {"rule_id": "a", "reason": "r", "category": "security"},
            {"rule_id": "b", "reason": "r", "category": "performance"},
            {"rule_id": "c", "reason": "r", "category": "testing"},
        ]
        result = critique.generate(failed, "artifact")
        categories = [i["category"] for i in result.issues]
        assert categories == ["security", "performance", "testing"]


# ============================================================================
# Exp 40: Tests for Typed API (CritiqueResult return, FailedRule input)
# ============================================================================

class TestTypedAPI:
    """Tests for typed CritiqueResult return and FailedRule input (Exp 40)"""

    @pytest.fixture
    def critique(self):
        return Critique(max_issues=5)

    def test_returns_critique_result_dataclass(self, critique):
        """Test that generate() returns CritiqueResult, not dict"""
        from specify_cli.quality.models import CritiqueResult
        result = critique.generate(
            [{"rule_id": "test", "reason": "test"}], "artifact"
        )
        assert isinstance(result, CritiqueResult)

    def test_accepts_failed_rule_objects(self, critique):
        """Test that generate() accepts List[FailedRule]"""
        from specify_cli.quality.models import FailedRule
        failed = [
            FailedRule(rule_id="correctness.tests", reason="No tests"),
            FailedRule(rule_id="security.secrets", reason="Hardcoded key"),
        ]
        result = critique.generate(failed, "artifact")
        assert result.total_failed == 2
        assert result.addressed == 2
        assert len(result.issues) == 2

    def test_failed_rule_weight_sorting(self, critique):
        """Test that FailedRule objects are sorted by weight"""
        from specify_cli.quality.models import FailedRule
        failed = [
            FailedRule(rule_id="low.rule", reason="Low", weight=1),
            FailedRule(rule_id="high.rule", reason="High", weight=2),
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["rule_id"] == "high.rule"
        assert result.issues[1]["rule_id"] == "low.rule"

    def test_failed_rule_category_preserved(self, critique):
        """Test that FailedRule.category is preserved in output"""
        from specify_cli.quality.models import FailedRule
        failed = [
            FailedRule(rule_id="test", reason="r", category="security"),
        ]
        result = critique.generate(failed, "artifact")
        assert result.issues[0]["category"] == "security"

    def test_mixed_input_dict_and_failed_rule(self, critique):
        """Test that generate() accepts mixed List of dicts and FailedRules"""
        from specify_cli.quality.models import FailedRule
        failed = [
            FailedRule(rule_id="typed.rule", reason="Typed"),
            {"rule_id": "dict.rule", "reason": "Dict"},
        ]
        result = critique.generate(failed, "artifact")
        assert result.total_failed == 2
        rule_ids = [i["rule_id"] for i in result.issues]
        assert "typed.rule" in rule_ids
        assert "dict.rule" in rule_ids

    def test_critique_result_to_dict(self, critique):
        """Test that CritiqueResult.to_dict() works correctly"""
        result = critique.generate(
            [{"rule_id": "test", "reason": "test"}], "artifact"
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["total_failed"] == 1
        assert d["addressed"] == 1
        assert isinstance(d["issues"], list)

    def test_empty_failed_rules_typed(self, critique):
        """Test with empty FailedRule list"""
        from specify_cli.quality.models import CritiqueResult
        result = critique.generate([], "artifact")
        assert isinstance(result, CritiqueResult)
        assert result.total_failed == 0
        assert result.issues == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
