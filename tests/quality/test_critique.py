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

        assert result["total_failed"] == 0
        assert result["addressed"] == 0
        assert result["skipped"] == 0
        assert result["issues"] == []

    def test_generate_single_failed_rule(self, critique_default):
        """Test critique with single failed rule"""
        failed_rules = [{"rule_id": "test.rule", "reason": "Test failure"}]
        result = critique_default.generate(failed_rules, "artifact")

        assert result["total_failed"] == 1
        assert result["addressed"] == 1
        assert result["skipped"] == 0
        assert len(result["issues"]) == 1
        assert result["issues"][0]["rule_id"] == "test.rule"

    def test_generate_respects_max_issues(self, critique_limited):
        """Test generate respects max_issues limit"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(10)
        ]
        result = critique_limited.generate(failed_rules, "artifact")

        assert result["total_failed"] == 10
        assert result["addressed"] == 3  # max_issues = 3
        assert result["skipped"] == 7
        assert len(result["issues"]) == 3

    def test_generate_fewer_than_max(self, critique_default):
        """Test with fewer issues than max_issues"""
        failed_rules = [
            {"rule_id": "rule.1", "reason": "Reason 1"},
            {"rule_id": "rule.2", "reason": "Reason 2"},
        ]
        result = critique_default.generate(failed_rules, "artifact")

        assert result["total_failed"] == 2
        assert result["addressed"] == 2
        assert result["skipped"] == 0

    def test_generate_exactly_max_issues(self, critique_limited):
        """Test with exactly max_issues failed rules"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(3)  # Exactly max_issues
        ]
        result = critique_limited.generate(failed_rules, "artifact")

        assert result["total_failed"] == 3
        assert result["addressed"] == 3
        assert result["skipped"] == 0

    def test_generate_issue_structure(self, critique_default):
        """Test that generated issues have correct structure"""
        failed_rules = [{"rule_id": "test.rule", "reason": "Test reason"}]
        result = critique_default.generate(failed_rules, "artifact")

        issue = result["issues"][0]
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
        assert result["issues"][0]["rule_id"] == "rule.0"
        assert result["issues"][1]["rule_id"] == "rule.1"
        assert result["issues"][2]["rule_id"] == "rule.2"


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

        assert result["total_failed"] == 1
        assert result["addressed"] == 0
        assert result["skipped"] == 1
        assert result["issues"] == []

    def test_very_long_reason(self, critique_default):
        """Test with very long reason string"""
        long_reason = "x" * 10000
        result = critique_default.generate(
            [{"rule_id": "test", "reason": long_reason}],
            "artifact"
        )
        assert result["issues"][0]["reason"] == long_reason

    def test_very_long_artifact(self, critique_default):
        """Test with very long artifact"""
        long_artifact = "x" * 100000
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            long_artifact
        )
        assert result["total_failed"] == 1

    def test_unicode_in_reason(self, critique_default):
        """Test with unicode characters in reason"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "Ошибка: 数据错误 🚨"}],
            "artifact"
        )
        assert result["issues"][0]["reason"] == "Ошибка: 数据错误 🚨"

    def test_unicode_in_artifact(self, critique_default):
        """Test with unicode characters in artifact"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            "Artifact with unicode: 你好 мир 🎉"
        )
        assert result["total_failed"] == 1

    def test_special_chars_in_rule_id(self, critique_default):
        """Test with special characters in rule_id"""
        result = critique_default.generate(
            [{"rule_id": "test.rule-with_special.chars:123", "reason": "test"}],
            "artifact"
        )
        assert result["issues"][0]["rule_id"] == "test.rule-with_special.chars:123"

    def test_empty_reason(self, critique_default):
        """Test with empty reason string"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": ""}],
            "artifact"
        )
        assert result["issues"][0]["reason"] == ""

    def test_many_failed_rules(self, critique_unlimited):
        """Test with many failed rules"""
        failed_rules = [
            {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
            for i in range(100)
        ]
        result = critique_unlimited.generate(failed_rules, "artifact")

        assert result["total_failed"] == 100
        assert result["addressed"] == 100
        assert len(result["issues"]) == 100


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

        assert "issues" in result
        assert "total_failed" in result
        assert "addressed" in result
        assert "skipped" in result

    def test_result_types(self, critique_default):
        """Test result value types"""
        result = critique_default.generate(
            [{"rule_id": "test", "reason": "test"}],
            "artifact"
        )

        assert isinstance(result["issues"], list)
        assert isinstance(result["total_failed"], int)
        assert isinstance(result["addressed"], int)
        assert isinstance(result["skipped"], int)

    def test_math_consistency(self, critique_default):
        """Test that addressed + skipped = total_failed"""
        for num_rules in [0, 1, 5, 10, 20]:
            failed_rules = [
                {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
                for i in range(num_rules)
            ]
            result = critique_default.generate(failed_rules, "artifact")

            assert result["addressed"] + result["skipped"] == result["total_failed"]

    def test_addressed_equals_issues_count(self, critique_default):
        """Test that addressed count matches issues list length"""
        for num_rules in [0, 1, 3, 5, 10]:
            failed_rules = [
                {"rule_id": f"rule.{i}", "reason": f"Reason {i}"}
                for i in range(num_rules)
            ]
            result = critique_default.generate(failed_rules, "artifact")

            assert result["addressed"] == len(result["issues"])


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

        assert result["total_failed"] == 3
        assert all("fix" in issue for issue in result["issues"])

    def test_full_workflow_code(self, critique_default, sample_artifact_code):
        """Test full workflow with code artifact"""
        failed_rules = [
            {"rule_id": "correctness.tests", "reason": "No unit tests"},
            {"rule_id": "correctness.type_hints", "reason": "Missing type hints"},
            {"rule_id": "quality.error_handling", "reason": "No error handling"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_code)

        assert result["total_failed"] == 3
        for issue in result["issues"]:
            assert issue["fix"] is not None

    def test_full_workflow_docs(self, critique_default, sample_artifact_docs):
        """Test full workflow with docs artifact"""
        failed_rules = [
            {"rule_id": "quality.installation", "reason": "No installation guide"},
            {"rule_id": "quality.usage", "reason": "No usage examples"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_docs)

        assert result["total_failed"] == 2

    def test_full_workflow_config(self, critique_default, sample_artifact_config):
        """Test full workflow with config artifact"""
        failed_rules = [
            {"rule_id": "quality.defaults", "reason": "Missing default values"},
            {"rule_id": "quality.environment_vars", "reason": "Hardcoded host"},
        ]

        result = critique_default.generate(failed_rules, sample_artifact_config)

        assert result["total_failed"] == 2

    def test_mixed_rule_types(self, critique_default):
        """Test with mixed known and unknown rule types"""
        failed_rules = [
            {"rule_id": "correctness.tests", "reason": "Known rule"},
            {"rule_id": "custom.unknown.rule", "reason": "Unknown rule"},
            {"rule_id": "security.secrets", "reason": "Another known rule"},
        ]

        result = critique_default.generate(failed_rules, "artifact")

        assert result["total_failed"] == 3
        # Known rules should have specific instructions
        assert "test" in result["issues"][0]["fix"].lower()
        # Unknown rule should have generic instruction
        assert "custom.unknown.rule" in result["issues"][1]["fix"]


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
