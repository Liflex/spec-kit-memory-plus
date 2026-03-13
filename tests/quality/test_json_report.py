"""
Tests for json_report.py - JSON Report Generator

Tests for:
- JSON Schema (QUALITY_REPORT_SCHEMA, validation)
- Schema utility functions (get_schema, validate_schema, export_schema, etc.)
- Distribution statistics (calculate_distribution_stats, get_severity_distribution)
- JSONReportGenerator class
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from specify_cli.quality.json_report import (
    # Schema
    QUALITY_REPORT_SCHEMA,
    get_schema,
    validate_schema,
    get_schema_json,
    export_schema,
    get_schema_info,
    print_schema_info,

    # Distribution stats
    calculate_distribution_stats,
    get_severity_distribution,

    # Main class and function
    JSONReportGenerator,
    generate_json_report,
)


# ============================================================================
# Tests for Schema Constants and Functions
# ============================================================================

class TestQualityReportSchema:
    """Tests for QUALITY_REPORT_SCHEMA constant"""

    def test_schema_structure(self):
        """Test schema has required top-level properties"""
        assert "$schema" in QUALITY_REPORT_SCHEMA
        assert "$id" in QUALITY_REPORT_SCHEMA
        assert "title" in QUALITY_REPORT_SCHEMA
        assert "type" in QUALITY_REPORT_SCHEMA
        assert "required" in QUALITY_REPORT_SCHEMA
        assert "properties" in QUALITY_REPORT_SCHEMA

    def test_schema_required_sections(self):
        """Test schema defines required sections"""
        required = QUALITY_REPORT_SCHEMA.get("required", [])
        assert "meta" in required
        assert "summary" in required
        assert "category_breakdown" in required

    def test_schema_meta_properties(self):
        """Test schema defines meta section properties"""
        properties = QUALITY_REPORT_SCHEMA.get("properties", {})
        assert "meta" in properties
        meta_props = properties["meta"].get("properties", {})
        assert "version" in meta_props
        assert "generated_at" in meta_props
        assert "generator" in meta_props

    def test_schema_summary_properties(self):
        """Test schema defines summary section properties"""
        properties = QUALITY_REPORT_SCHEMA.get("properties", {})
        assert "summary" in properties
        summary_props = properties["summary"].get("properties", {})
        assert "score" in summary_props
        assert "passed" in summary_props
        assert "status" in summary_props
        assert "priority_profile" in summary_props


class TestGetSchema:
    """Tests for get_schema function"""

    def test_get_schema_returns_dict(self):
        """Test get_schema returns a dictionary"""
        schema = get_schema()
        assert isinstance(schema, dict)
        assert schema == QUALITY_REPORT_SCHEMA

    def test_get_schema_matches_constant(self):
        """Test that get_schema returns the constant (not a copy)"""
        schema = get_schema()
        # get_schema returns QUALITY_REPORT_SCHEMA directly (not a copy)
        # This is acceptable as schema should not be modified
        assert schema is QUALITY_REPORT_SCHEMA


class TestValidateSchema:
    """Tests for validate_schema function"""

    def test_validate_valid_report(self):
        """Test validation passes for valid report"""
        valid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.85,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [
                    {"name": "security", "failed": 0, "warnings": 1, "total": 1}
                ],
                "total_issues": 1
            }
        }
        is_valid, errors = validate_schema(valid_report)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_required_section(self):
        """Test validation fails with missing required section"""
        invalid_report = {
            "meta": {"version": "1.0", "generated_at": datetime.now().isoformat()}
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("summary" in e for e in errors)
        assert any("category_breakdown" in e for e in errors)

    def test_validate_missing_meta_fields(self):
        """Test validation fails with missing meta fields"""
        invalid_report = {
            "meta": {"version": "1.0"},  # Missing generated_at, generator
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("generated_at" in e for e in errors)
        assert any("generator" in e for e in errors)

    def test_validate_missing_summary_fields(self):
        """Test validation fails with missing summary fields"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {"score": 0.8},  # Missing passed, status, priority_profile
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("passed" in e or "status" in e or "priority_profile" in e for e in errors)

    def test_validate_invalid_score_type(self):
        """Test validation fails with non-numeric score"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": "invalid",  # Should be number
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("score" in e and "number" in e for e in errors)

    def test_validate_invalid_score_range(self):
        """Test validation fails with score out of range"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 1.5,  # Should be 0.0 to 1.0
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("score" in e and "between" in e for e in errors)

    def test_validate_invalid_passed_type(self):
        """Test validation fails with non-boolean passed"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": "true",  # Should be boolean
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("passed" in e and "boolean" in e for e in errors)

    def test_validate_invalid_status(self):
        """Test validation fails with invalid status"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "invalid_status",  # Should be completed/failed/stopped
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("status" in e for e in errors)

    def test_validate_missing_categories(self):
        """Test validation fails with missing categories"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                # Missing categories
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("categories" in e for e in errors)

    def test_validate_invalid_categories_type(self):
        """Test validation fails with non-array categories"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": "not_an_array",
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("categories" in e and "array" in e for e in errors)

    def test_validate_missing_category_fields(self):
        """Test validation fails with missing category fields"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [
                    {"name": "security"}  # Missing failed, warnings, total
                ],
                "total_issues": 0
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("failed" in e or "warnings" in e or "total" in e for e in errors)

    def test_validate_invalid_failed_rules_type(self):
        """Test validation fails with non-array failed_rules"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            },
            "failed_rules": "not_an_array"
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("failed_rules" in e and "array" in e for e in errors)

    def test_validate_invalid_score_timeline_type(self):
        """Test validation fails with non-array score_timeline"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            },
            "score_timeline": "not_an_array"
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("score_timeline" in e and "array" in e for e in errors)

    def test_validate_invalid_gate_result(self):
        """Test validation fails with invalid gate_result values"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            },
            "gate_result": {
                "gate_result": "invalid_value",  # Should be passed/failed/warning
                "passed": True
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("gate_result" in e for e in errors)

    def test_validate_invalid_gate_passed(self):
        """Test validation fails with non-boolean gate.passed"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            },
            "gate_result": {
                "gate_result": "passed",
                "passed": "yes"  # Should be boolean
            }
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("passed" in e and "boolean" in e for e in errors)

    def test_validate_invalid_distribution(self):
        """Test validation fails with invalid distribution"""
        invalid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.8,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            },
            "distribution": "not_an_object"
        }
        is_valid, errors = validate_schema(invalid_report)
        assert is_valid is False
        assert any("distribution" in e for e in errors)


class TestGetSchemaJson:
    """Tests for get_schema_json function"""

    def test_get_schema_json_returns_string(self):
        """Test get_schema_json returns a string"""
        schema_json = get_schema_json()
        assert isinstance(schema_json, str)

    def test_get_schema_json_pretty(self):
        """Test get_schema_json with pretty=True includes indentation"""
        schema_json = get_schema_json(pretty=True)
        assert "\n" in schema_json  # Pretty JSON has newlines
        # Parse to verify valid JSON
        parsed = json.loads(schema_json)
        assert isinstance(parsed, dict)

    def test_get_schema_json_compact(self):
        """Test get_schema_json with pretty=False is compact"""
        schema_json = get_schema_json(pretty=False)
        assert "\n" not in schema_json  # Compact JSON has no newlines
        # Parse to verify valid JSON
        parsed = json.loads(schema_json)
        assert isinstance(parsed, dict)


class TestGetSchemaInfo:
    """Tests for get_schema_info function"""

    def test_get_schema_info_returns_dict(self):
        """Test get_schema_info returns a dictionary"""
        info = get_schema_info()
        assert isinstance(info, dict)

    def test_get_schema_info_has_required_keys(self):
        """Test get_schema_info has all expected keys"""
        info = get_schema_info()
        expected_keys = [
            "schema_id", "title", "version", "schema_format",
            "description", "required_sections", "available_sections"
        ]
        for key in expected_keys:
            assert key in info

    def test_get_schema_info_values_are_correct(self):
        """Test get_schema_info returns correct values"""
        info = get_schema_info()
        assert info["title"] == QUALITY_REPORT_SCHEMA.get("title")
        assert info["version"] == "1.0"
        assert isinstance(info["required_sections"], list)
        assert isinstance(info["available_sections"], list)
        assert len(info["required_sections"]) > 0
        assert len(info["available_sections"]) > 0


# ============================================================================
# Tests for Distribution Statistics Functions
# ============================================================================

class TestCalculateDistributionStats:
    """Tests for calculate_distribution_stats function"""

    def test_empty_list_returns_empty_stats(self):
        """Test with empty list returns zeroed stats"""
        stats = calculate_distribution_stats([])
        assert stats["count"] == 0
        assert stats["min"] is None
        assert stats["max"] is None
        assert stats["mean"] is None
        assert stats["median"] is None

    def test_single_value(self):
        """Test with single value"""
        stats = calculate_distribution_stats([0.5])
        assert stats["count"] == 1
        assert stats["min"] == 0.5
        assert stats["max"] == 0.5
        assert stats["mean"] == 0.5
        assert stats["median"] == 0.5

    def test_two_values(self):
        """Test with two values"""
        stats = calculate_distribution_stats([0.3, 0.7])
        assert stats["count"] == 2
        assert stats["min"] == 0.3
        assert stats["max"] == 0.7
        assert stats["mean"] == 0.5
        assert stats["median"] == 0.5

    def test_multiple_values(self):
        """Test with multiple values"""
        scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        stats = calculate_distribution_stats(scores)
        assert stats["count"] == 10
        assert stats["min"] == 0.1
        assert stats["max"] == 1.0
        assert 0.5 <= stats["mean"] <= 0.6
        assert stats["median"] == 0.55  # Middle of 0.5 and 0.6

    def test_percentiles(self):
        """Test percentile calculations"""
        scores = [i / 100 for i in range(1, 101)]  # 0.01 to 1.00
        stats = calculate_distribution_stats(scores)
        # Percentiles are calculated using linear interpolation
        # For 100 elements (0-99 indices), p25 is at index 24.75
        assert abs(stats["p25"] - 0.25) < 0.01  # 25th percentile (approx)
        assert abs(stats["median"] - 0.50) < 0.01  # 50th percentile (median)
        assert abs(stats["p75"] - 0.75) < 0.01  # 75th percentile
        assert abs(stats["p90"] - 0.90) < 0.01  # 90th percentile
        assert abs(stats["p95"] - 0.95) < 0.01  # 95th percentile
        # Verify monotonic increasing
        assert stats["p25"] < stats["median"] < stats["p75"] < stats["p90"] < stats["p95"]

    def test_values_rounded(self):
        """Test values are rounded to 3 decimal places"""
        scores = [0.123456, 0.987654]
        stats = calculate_distribution_stats(scores)
        # Check that values have at most 3 decimal places
        for key in ["min", "max", "mean", "median", "p25", "p75", "p90", "p95"]:
            if stats[key] is not None:
                # Convert to string and check decimal places
                str_val = f"{stats[key]:.10f}".rstrip('0').rstrip('.')
                decimals = len(str_val.split('.')[-1]) if '.' in str_val else 0
                assert decimals <= 3

    def test_identical_values(self):
        """Test with all identical values"""
        stats = calculate_distribution_stats([0.5, 0.5, 0.5, 0.5, 0.5])
        assert stats["count"] == 5
        assert stats["min"] == 0.5
        assert stats["max"] == 0.5
        assert stats["mean"] == 0.5
        assert stats["median"] == 0.5
        assert stats["p25"] == 0.5
        assert stats["p75"] == 0.5


class TestGetSeverityDistribution:
    """Tests for get_severity_distribution function"""

    def test_empty_lists(self):
        """Test with empty lists"""
        dist = get_severity_distribution([], [])
        assert dist["critical"] == 0
        assert dist["high"] == 0
        assert dist["medium"] == 0
        assert dist["low"] == 0
        assert dist["info"] == 0
        assert dist["unknown"] == 0

    def test_failed_rules_with_severity(self):
        """Test with failed rules having severity"""
        failed_rules = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "info"}
        ]
        dist = get_severity_distribution(failed_rules, [])
        assert dist["critical"] == 1
        assert dist["high"] == 1
        assert dist["medium"] == 1
        assert dist["low"] == 1
        assert dist["info"] == 1
        assert dist["unknown"] == 0

    def test_warnings_with_severity(self):
        """Test with warnings having severity"""
        warnings = [
            {"severity": "info"},
            {"severity": "low"},
            {"severity": "info"}
        ]
        dist = get_severity_distribution([], warnings)
        assert dist["info"] == 2
        assert dist["low"] == 1
        assert dist["medium"] == 0
        assert dist["unknown"] == 0

    def test_combined_failed_and_warnings(self):
        """Test with both failed rules and warnings"""
        failed_rules = [
            {"severity": "critical"},
            {"severity": "high"}
        ]
        warnings = [
            {"severity": "medium"},
            {"severity": "info"}
        ]
        dist = get_severity_distribution(failed_rules, warnings)
        assert dist["critical"] == 1
        assert dist["high"] == 1
        assert dist["medium"] == 1
        assert dist["info"] == 1
        assert dist["low"] == 0

    def test_case_insensitive_severity(self):
        """Test severity matching is case-insensitive"""
        failed_rules = [
            {"severity": "CRITICAL"},
            {"severity": "High"},
            {"severity": "MeDiUm"}
        ]
        dist = get_severity_distribution(failed_rules, [])
        assert dist["critical"] == 1
        assert dist["high"] == 1
        assert dist["medium"] == 1

    def test_unknown_severity(self):
        """Test unknown severity is counted as unknown"""
        failed_rules = [
            {"severity": "urgent"},
            {"severity": "none"},
            {}  # Missing severity
        ]
        dist = get_severity_distribution(failed_rules, [])
        assert dist["unknown"] == 3

    def test_missing_severity_defaults_to_info_for_warnings(self):
        """Test warnings without severity default to info"""
        warnings = [
            {},
            {"other_field": "value"}
        ]
        dist = get_severity_distribution([], warnings)
        assert dist["info"] == 2

    def test_missing_severity_defaults_to_unknown_for_failed(self):
        """Test failed rules without severity default to unknown"""
        failed_rules = [
            {},
            {"other_field": "value"}
        ]
        dist = get_severity_distribution(failed_rules, [])
        assert dist["unknown"] == 2


# ============================================================================
# Tests for JSONReportGenerator Class
# ============================================================================

class TestJSONReportGeneratorInit:
    """Tests for JSONReportGenerator initialization"""

    def test_init(self):
        """Test JSONReportGenerator can be instantiated"""
        generator = JSONReportGenerator()
        assert generator is not None
        assert hasattr(generator, "calculate_distribution_stats")
        assert hasattr(generator, "get_severity_distribution")


class TestJSONReportGeneratorGenerate:
    """Tests for JSONReportGenerator.generate method"""

    def get_sample_result(self) -> Dict[str, Any]:
        """Helper to create a sample evaluation result"""
        return {
            "score": 0.85,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "iteration": 1,
                "phase": "A",
                "max_iterations": 4,
                "run_id": "test-run-123",
                "task_alias": "test-task",
                "current_score": 0.85,
                "last_score": 0.75,
                "evaluation": {
                    "total_rules": 10,
                    "passed_rules": 8,
                    "failed_rules": [
                        {
                            "rule_id": "security-001",
                            "category": "security",
                            "reason": "Missing auth check",
                            "score": 0.0,
                            "severity": "critical"
                        },
                        {
                            "rule_id": "testing-002",
                            "category": "testing",
                            "reason": "No unit tests",
                            "score": 0.3,
                            "severity": "high"
                        }
                    ],
                    "warnings": [
                        {
                            "rule_id": "docs-001",
                            "category": "documentation",
                            "reason": "Incomplete API docs",
                            "score": 0.7,
                            "severity": "info"
                        }
                    ]
                }
            },
            "gate_result": {
                "gate_result": "passed",
                "passed": True,
                "blocked": False,
                "policy_name": "ci",
                "policy_description": "CI quality gate",
                "overall_threshold": 0.8,
                "overall_score": 0.85
            }
        }

    def test_generate_returns_string(self):
        """Test generate returns JSON string"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        assert isinstance(json_str, str)

    def test_generate_valid_json(self):
        """Test generate returns valid JSON"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_generate_has_required_sections(self):
        """Test generate creates all required sections"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "meta" in parsed
        assert "summary" in parsed
        assert "category_breakdown" in parsed

    def test_generate_meta_section(self):
        """Test meta section is populated correctly"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "meta" in parsed
        assert parsed["meta"]["version"] == "1.0"
        assert "generated_at" in parsed["meta"]
        assert parsed["meta"]["generator"] == "Spec Kit Quality Loop"

    def test_generate_summary_section(self):
        """Test summary section is populated correctly"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "summary" in parsed
        assert parsed["summary"]["score"] == 0.85
        assert parsed["summary"]["passed"] is True
        assert parsed["summary"]["status"] == "completed"
        assert parsed["summary"]["priority_profile"] == "default"
        assert parsed["summary"]["iteration"] == 1
        assert parsed["summary"]["phase"] == "A"

    def test_generate_category_breakdown(self):
        """Test category_breakdown section is populated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "category_breakdown" in parsed
        breakdown = parsed["category_breakdown"]
        assert "categories" in breakdown
        assert "total_issues" in breakdown

    def test_generate_failed_rules(self):
        """Test failed_rules section is populated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "failed_rules" in parsed
        assert len(parsed["failed_rules"]) == 2
        assert parsed["failed_rules"][0]["category"] == "security"
        assert parsed["failed_rules"][1]["category"] == "testing"

    def test_generate_warnings(self):
        """Test warnings section is populated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "warnings" in parsed
        assert len(parsed["warnings"]) == 1
        assert parsed["warnings"][0]["category"] == "documentation"

    def test_generate_score_timeline(self):
        """Test score_timeline section is populated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "score_timeline" in parsed
        timeline = parsed["score_timeline"]
        assert len(timeline) >= 2  # Start + at least one iteration

    def test_generate_distribution(self):
        """Test distribution section is populated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "distribution" in parsed
        dist = parsed["distribution"]
        assert "severity" in dist
        assert "score_distribution" in dist

    def test_generate_with_pretty_true(self):
        """Test generate with pretty=True includes indentation"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result, pretty=True)
        assert "\n" in json_str

    def test_generate_with_pretty_false(self):
        """Test generate with pretty=False is compact"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result, pretty=False)
        assert "\n" not in json_str

    def test_generate_with_include_categories(self):
        """Test generate with include_categories filter"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result, include_categories=["security"])
        parsed = json.loads(json_str)

        # Only security category should be present
        categories = parsed["category_breakdown"]["categories"]
        assert len(categories) == 1
        assert categories[0]["name"] == "security"
        # Only security failed rules
        assert len(parsed["failed_rules"]) == 1
        assert parsed["failed_rules"][0]["category"] == "security"

    def test_generate_with_exclude_categories(self):
        """Test generate with exclude_categories filter"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result, exclude_categories=["security"])
        parsed = json.loads(json_str)

        # Security category should not be present
        categories = parsed["category_breakdown"]["categories"]
        assert not any(c["name"] == "security" for c in categories)
        # No security failed rules
        assert not any(r["category"] == "security" for r in parsed["failed_rules"])

    def test_generate_with_minimal_result(self):
        """Test generate with minimal result (missing fields)"""
        generator = JSONReportGenerator()
        minimal_result = {
            "score": 0.5,
            "passed": False,
            "priority_profile": "default",
            "state": {}
        }
        json_str = generator.generate(minimal_result)
        parsed = json.loads(json_str)

        # Should still create valid structure
        assert "meta" in parsed
        assert "summary" in parsed
        assert parsed["summary"]["score"] == 0.5
        assert parsed["summary"]["passed"] is False
        assert parsed["summary"]["status"] == "failed"

    def test_generate_with_gate_result(self):
        """Test gate_result is included when present"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "gate_result" in parsed
        gate = parsed["gate_result"]
        assert gate["gate_result"] == "passed"
        assert gate["policy_name"] == "ci"

    def test_generate_without_gate_result(self):
        """Test gate_result is omitted when not present"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        del result["gate_result"]
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        assert "gate_result" not in parsed

    def test_generate_distribution_stats(self):
        """Test distribution statistics are calculated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        score_dist = parsed["distribution"]["score_distribution"]
        assert "count" in score_dist
        assert "min" in score_dist
        assert "max" in score_dist
        assert "mean" in score_dist
        # Should have stats for 2 failed rules
        assert score_dist["count"] == 2

    def test_generate_severity_distribution(self):
        """Test severity distribution is calculated"""
        generator = JSONReportGenerator()
        result = self.get_sample_result()
        json_str = generator.generate(result)
        parsed = json.loads(json_str)

        severity = parsed["distribution"]["severity"]
        assert severity["critical"] == 1
        assert severity["high"] == 1
        assert severity["info"] == 1  # From warnings


class TestJSONReportGeneratorValidateReport:
    """Tests for JSONReportGenerator.validate_report method"""

    def test_validate_report_valid(self):
        """Test validate_report with valid report"""
        generator = JSONReportGenerator()
        valid_report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit"
            },
            "summary": {
                "score": 0.85,
                "passed": True,
                "status": "completed",
                "priority_profile": "default"
            },
            "category_breakdown": {
                "categories": [],
                "total_issues": 0
            }
        }
        is_valid, errors = generator.validate_report(valid_report)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_report_invalid(self):
        """Test validate_report with invalid report"""
        generator = JSONReportGenerator()
        invalid_report = {
            "meta": {"version": "1.0"}
        }
        is_valid, errors = generator.validate_report(invalid_report)
        assert is_valid is False
        assert len(errors) > 0


# ============================================================================
# Tests for Convenience Function
# ============================================================================

class TestGenerateJsonReport:
    """Tests for generate_json_report convenience function"""

    def test_generate_json_report_returns_string(self):
        """Test generate_json_report returns JSON string"""
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        json_str = generate_json_report(result)
        assert isinstance(json_str, str)

    def test_generate_json_report_valid_json(self):
        """Test generate_json_report returns valid JSON"""
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        json_str = generate_json_report(result)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_generate_json_report_with_output_path(self, tmp_path):
        """Test generate_json_report writes to file when output_path provided"""
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        output_file = tmp_path / "report.json"
        json_str = generate_json_report(result, output_path=str(output_file))

        # File should exist
        assert output_file.exists()
        # Content should match returned string
        file_content = output_file.read_text(encoding="utf-8")
        assert file_content == json_str

    def test_generate_json_report_creates_parent_dirs(self, tmp_path):
        """Test generate_json_report creates parent directories"""
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        output_file = tmp_path / "subdir" / "nested" / "report.json"
        json_str = generate_json_report(result, output_path=str(output_file))

        # Parent directories should be created
        assert output_file.exists()
        assert output_file.parent.exists()


# ============================================================================
# Tests for Integration with Schema Validation
# ============================================================================

class TestSchemaValidationIntegration:
    """Tests for schema validation integration with generate"""

    def test_generate_validates_by_default(self):
        """Test generate validates by default"""
        generator = JSONReportGenerator()
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        # Should not raise an exception for valid data
        json_str = generator.generate(result, validate=True)
        assert isinstance(json_str, str)

    def test_generate_skip_validation(self):
        """Test generate can skip validation"""
        generator = JSONReportGenerator()
        result = {
            "score": 0.8,
            "passed": True,
            "priority_profile": "default",
            "state": {
                "evaluation": {
                    "failed_rules": [],
                    "warnings": []
                }
            }
        }
        json_str = generator.generate(result, validate=False)
        assert isinstance(json_str, str)
