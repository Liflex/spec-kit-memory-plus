"""
Tests for html_report.py - HTML Report Generator

Tests for:
- HTMLReportGenerator class constants
- HTMLReportGenerator initialization
- HTMLReportGenerator.generate() with various options
- Private methods for HTML section generation
- Convenience function generate_html_report()
"""

import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import shutil

from specify_cli.quality.html_report import (
    HTMLReportGenerator,
    generate_html_report,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_result() -> Dict[str, Any]:
    """Sample evaluation result for testing"""
    return {
        "state": {
            "run_id": "test-run-123",
            "task_alias": "test-task",
            "status": "completed",
            "iteration": 2,
            "max_iterations": 4,
            "phase": "A",
            "started_at": "2026-03-13T10:00:00",
            "current_score": 0.75,
            "last_score": 0.60,
            "evaluation": {
                "failed_rules": [
                    {
                        "rule_id": "SEC001",
                        "category": "security",
                        "severity": "high",
                        "reason": "Missing authentication",
                        "score": 0.3
                    },
                    {
                        "rule_id": "PERF001",
                        "category": "performance",
                        "severity": "medium",
                        "reason": "Slow query detected",
                        "score": 0.5
                    },
                    {
                        "rule_id": "DOC001",
                        "category": "documentation",
                        "severity": "low",
                        "reason": "Missing API docs",
                        "score": 0.7
                    }
                ],
                "warnings": [
                    {
                        "rule_id": "TEST001",
                        "category": "testing",
                        "severity": "info",
                        "reason": "Low test coverage"
                    }
                ]
            }
        },
        "score": 0.75,
        "passed": True,
        "priority_profile": "backend",
        "gate_result": {
            "gate_result": "passed",
            "passed": True,
            "blocked": False,
            "policy_name": "strict",
            "policy_description": "Strict quality policy",
            "overall_threshold": 0.80,
            "overall_score": 0.85,
            "messages": [],
            "severity_counts": {
                "critical": 0,
                "high": 1,
                "medium": 1,
                "low": 1,
                "info": 1
            },
            "category_scores": {
                "security": 0.90,
                "performance": 0.75,
                "testing": 0.60
            }
        }
    }


@pytest.fixture
def minimal_result() -> Dict[str, Any]:
    """Minimal result for edge case testing"""
    return {
        "state": {
            "run_id": "minimal",
            "task_alias": "minimal-task",
            "status": "unknown",
            "evaluation": {
                "failed_rules": [],
                "warnings": []
            }
        },
        "score": 0.0,
        "passed": False,
        "priority_profile": "default"
    }


@pytest.fixture
def failed_gate_result() -> Dict[str, Any]:
    """Result with failed gate for testing"""
    return {
        "state": {
            "run_id": "failed-gate",
            "task_alias": "failed-task",
            "status": "failed",
            "iteration": 1,
            "max_iterations": 4,
            "phase": "A",
            "evaluation": {
                "failed_rules": [
                    {
                        "rule_id": "CRIT001",
                        "category": "security",
                        "severity": "critical",
                        "reason": "Critical security flaw"
                    }
                ],
                "warnings": []
            }
        },
        "score": 0.25,
        "passed": False,
        "priority_profile": "default",
        "gate_result": {
            "gate_result": "failed",
            "passed": False,
            "blocked": True,
            "policy_name": "standard",
            "policy_description": "Standard quality policy",
            "overall_threshold": 0.70,
            "overall_score": 0.25,
            "messages": [
                "Critical severity issues found",
                "Score below threshold"
            ],
            "severity_counts": {
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "category_scores": {
                "security": 0.0
            }
        }
    }


@pytest.fixture
def temp_dir():
    """Temporary directory for file output tests"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


# ============================================================================
# Tests for Constants
# ============================================================================

class TestHTMLReportGeneratorConstants:
    """Tests for HTMLReportGenerator class constants"""

    def test_severity_colors_defined(self):
        """Test SEVERITY_COLORS has all expected severities"""
        expected_severities = [
            "critical", "high", "medium", "low", "info", "unknown"
        ]
        for severity in expected_severities:
            assert severity in HTMLReportGenerator.SEVERITY_COLORS
            assert isinstance(HTMLReportGenerator.SEVERITY_COLORS[severity], str)
            assert HTMLReportGenerator.SEVERITY_COLORS[severity].startswith("#")

    def test_severity_colors_are_valid_hex(self):
        """Test severity colors are valid hex color codes"""
        for color in HTMLReportGenerator.SEVERITY_COLORS.values():
            assert len(color) == 7  # #RRGGBB format
            assert color[0] == "#"
            assert all(c in "0123456789abcdefABCDEF" for c in color[1:])

    def test_severity_order_defined(self):
        """Test SEVERITY_ORDER has all severities in correct order"""
        expected_order = ["critical", "high", "medium", "low", "info", "unknown"]
        assert HTMLReportGenerator.SEVERITY_ORDER == expected_order


# ============================================================================
# Tests for Initialization
# ============================================================================

class TestHTMLReportGeneratorInit:
    """Tests for HTMLReportGenerator initialization"""

    def test_init_creates_instance(self):
        """Test initialization creates generator instance"""
        gen = HTMLReportGenerator()
        assert gen is not None
        assert hasattr(gen, 'template_dir')
        assert hasattr(gen, 'calculate_distribution_stats')
        assert hasattr(gen, 'get_severity_distribution')

    def test_template_dir_is_path(self):
        """Test template_dir is a Path object"""
        gen = HTMLReportGenerator()
        assert isinstance(gen.template_dir, Path)

    def test_distribution_functions_are_callable(self):
        """Test imported distribution functions are callable"""
        gen = HTMLReportGenerator()
        assert callable(gen.calculate_distribution_stats)
        assert callable(gen.get_severity_distribution)


# ============================================================================
# Tests for Main generate() Method
# ============================================================================

class TestHTMLReportGeneratorGenerate:
    """Tests for HTMLReportGenerator.generate() method"""

    def test_generate_returns_string(self, sample_result):
        """Test generate() returns HTML string"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_contains_html_structure(self, sample_result):
        """Test generated HTML contains basic structure"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result)

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_generate_contains_title(self, sample_result):
        """Test generated HTML contains title"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result)
        assert "<title>Spec Kit Quality Report</title>" in html

    def test_generate_with_output_path_saves_file(self, sample_result, temp_dir):
        """Test generate() saves file when output_path provided"""
        gen = HTMLReportGenerator()
        output_file = temp_dir / "report.html"

        html = gen.generate(sample_result, output_path=str(output_file))

        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == html

    def test_generate_creates_parent_directories(self, sample_result, temp_dir):
        """Test generate() creates parent directories if needed"""
        gen = HTMLReportGenerator()
        output_file = temp_dir / "subdir" / "nested" / "report.html"

        gen.generate(sample_result, output_path=str(output_file))

        assert output_file.exists()
        assert output_file.parent.is_dir()

    def test_generate_include_timeline_false(self, sample_result):
        """Test generate() with include_timeline=False excludes timeline"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result, include_timeline=False)

        assert "Score Timeline" not in html
        assert "timelineChart" not in html

    def test_generate_include_timeline_true(self, sample_result):
        """Test generate() with include_timeline=True includes timeline"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result, include_timeline=True)

        assert "Score Timeline" in html
        assert "timelineChart" in html

    def test_generate_include_details_false(self, sample_result):
        """Test generate() with include_details=False excludes details"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result, include_details=False)

        assert "Failed Rules & Warnings" not in html

    def test_generate_include_details_true(self, sample_result):
        """Test generate() with include_details=True includes details"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result, include_details=True)

        assert "Failed Rules & Warnings" in html

    def test_generate_with_minimal_result(self, minimal_result):
        """Test generate() handles minimal result without errors"""
        gen = HTMLReportGenerator()
        html = gen.generate(minimal_result)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html

    def test_generate_contains_chart_js(self, sample_result):
        """Test generated HTML includes Chart.js CDN"""
        gen = HTMLReportGenerator()
        html = gen.generate(sample_result)

        assert "chart.js" in html
        assert "chart.umd.min.js" in html


# ============================================================================
# Tests for HTML Section Methods
# ============================================================================

class TestHTMLReportGeneratorSections:
    """Tests for individual HTML section generation methods"""

    def test_get_html_header(self):
        """Test _get_html_header() returns valid HTML header"""
        gen = HTMLReportGenerator()
        header = gen._get_html_header()

        assert "<!DOCTYPE html>" in header
        assert "<html lang=\"en\">" in header
        assert "<head>" in header
        assert "<meta charset=\"UTF-8\">" in header
        assert "<title>Spec Kit Quality Report</title>" in header
        assert "chart.js" in header

    def test_get_styles_returns_css(self):
        """Test _get_styles() returns CSS styles"""
        gen = HTMLReportGenerator()
        styles = gen._get_styles()

        assert "<style>" in styles
        assert "</style>" in styles
        assert "body {" in styles
        assert ".container {" in styles
        assert ".header {" in styles
        assert ".score-badge {" in styles

    def test_get_header_section_passed(self, sample_result):
        """Test _get_header_section() with passed result"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]
        score = sample_result["score"]
        passed = sample_result["passed"]
        profile = sample_result["priority_profile"]

        header = gen._get_header_section(state, score, passed, profile)

        assert "Spec Kit Quality Report" in header
        assert "test-task" in header
        assert "test-run-123" in header
        assert "0.75" in header
        assert "score-passed" in header
        assert "PASSED" in header
        assert "Profile: backend" in header

    def test_get_header_section_failed(self, minimal_result):
        """Test _get_header_section() with failed result"""
        gen = HTMLReportGenerator()
        state = minimal_result["state"]
        score = minimal_result["score"]
        passed = minimal_result["passed"]
        profile = minimal_result["priority_profile"]

        header = gen._get_header_section(state, score, passed, profile)

        assert "score-failed" in header
        assert "FAILED" in header

    def test_get_summary_section(self, sample_result):
        """Test _get_summary_section() generates summary"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]
        score = sample_result["score"]
        passed = sample_result["passed"]

        summary = gen._get_summary_section(state, score, passed)

        assert "Summary" in summary
        assert "2/4" in summary  # iteration/max_iterations
        assert "<div class=\"label\">Phase</div>" in summary  # Phase label
        assert "<div class=\"value\">A</div>" in summary  # Phase value
        assert "0.75" in summary
        assert "PASS" in summary

    def test_get_summary_section_with_category_breakdown(self, sample_result):
        """Test _get_summary_section() includes category breakdown"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]
        score = sample_result["score"]
        passed = sample_result["passed"]

        summary = gen._get_summary_section(state, score, passed)

        assert "Issues by Category" in summary
        assert "security" in summary
        assert "performance" in summary

    def test_get_gate_section_passed(self, sample_result):
        """Test _get_gate_section() with passed gate"""
        gen = HTMLReportGenerator()
        gate_result = sample_result["gate_result"]

        gate_section = gen._get_gate_section(gate_result)

        assert "Quality Gate Results" in gate_section
        assert "strict" in gate_section
        assert "PASSED" in gate_section
        assert "0.85" in gate_section
        assert "0.80" in gate_section

    def test_get_gate_section_failed(self, failed_gate_result):
        """Test _get_gate_section() with failed gate"""
        gen = HTMLReportGenerator()
        gate_result = failed_gate_result["gate_result"]

        gate_section = gen._get_gate_section(gate_result)

        assert "FAILED" in gate_section
        assert "Critical severity issues found" in gate_section
        assert "critical" in gate_section.lower()

    def test_get_gate_section_without_messages(self, sample_result):
        """Test _get_gate_section() with no messages"""
        gen = HTMLReportGenerator()
        gate_result = {
            "gate_result": "passed",
            "passed": True,
            "blocked": False,
            "policy_name": "test",
            "policy_description": "Test policy",
            "overall_threshold": 0.5,
            "overall_score": 0.8,
            "messages": [],
            "severity_counts": {},
            "category_scores": {}
        }

        gate_section = gen._get_gate_section(gate_result)

        assert "All gate checks passed!" in gate_section

    def test_get_category_breakdown(self, sample_result):
        """Test _get_category_breakdown() groups by category"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        breakdown = gen._get_category_breakdown(state)

        assert "Issues by Category" in breakdown
        assert "security" in breakdown
        assert "performance" in breakdown
        assert "categoryChart" in breakdown  # Canvas for doughnut chart
        assert "doughnut" in breakdown  # Chart type

    def test_get_category_breakdown_empty(self, minimal_result):
        """Test _get_category_breakdown() with empty evaluation"""
        gen = HTMLReportGenerator()
        state = minimal_result["state"]

        breakdown = gen._get_category_breakdown(state)

        assert breakdown == ""

    def test_get_distribution_section(self, sample_result):
        """Test _get_distribution_section() generates charts"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        dist_section = gen._get_distribution_section(state)

        assert "Quality Distribution" in dist_section
        assert "severityChart" in dist_section
        assert "scoreDistChart" in dist_section

    def test_get_timeline_section(self, sample_result):
        """Test _get_timeline_section() generates timeline"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        timeline = gen._get_timeline_section(state)

        assert "Score Timeline" in timeline
        assert "timelineChart" in timeline
        assert "Iteration 2" in timeline

    def test_get_details_section(self, sample_result):
        """Test _get_details_section() shows failed rules"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        details = gen._get_details_section(state)

        assert "Failed Rules & Warnings by Category" in details
        assert "SEC001" in details
        assert "Missing authentication" in details
        assert "TEST001" in details

    def test_get_details_section_empty(self, minimal_result):
        """Test _get_details_section() with no issues"""
        gen = HTMLReportGenerator()
        state = minimal_result["state"]

        details = gen._get_details_section(state)

        assert "No issues found!" in details

    def test_get_footer(self):
        """Test _get_footer() contains timestamp"""
        gen = HTMLReportGenerator()
        footer = gen._get_footer()

        assert "Generated by Spec Kit Quality Loop" in footer
        assert "Spec Kit - AI-powered quality evaluation" in footer

        # Check for timestamp pattern (YYYY-MM-DD HH:MM:SS)
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', footer)


# ============================================================================
# Tests for Helper Methods
# ============================================================================

class TestHTMLReportGeneratorHelpers:
    """Tests for helper methods"""

    def test_extract_score_events_with_last_score(self, sample_result):
        """Test _extract_score_events() includes last_score"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        events = gen._extract_score_events(state)

        assert len(events) >= 2
        assert events[0]["label"] == "Start"
        assert events[0]["score"] == 0.0
        assert any(e["label"] == "Iteration 2" for e in events)

    def test_extract_score_events_without_last_score(self, minimal_result):
        """Test _extract_score_events() without last_score"""
        gen = HTMLReportGenerator()
        state = minimal_result["state"]

        events = gen._extract_score_events(state)

        assert len(events) >= 2
        assert events[0]["label"] == "Start"

    def test_extract_rule_score_with_score_field(self):
        """Test _extract_rule_score() with score in rule"""
        gen = HTMLReportGenerator()
        rule = {"score": 0.75, "severity": "medium"}

        score = gen._extract_rule_score(rule)

        assert score == 0.75

    def test_extract_rule_score_without_score_field(self):
        """Test _extract_rule_score() calculates from severity"""
        gen = HTMLReportGenerator()

        # Test each severity
        assert gen._extract_rule_score({"severity": "critical"}) == 0.0
        assert gen._extract_rule_score({"severity": "high"}) == 0.3
        assert gen._extract_rule_score({"severity": "medium"}) == 0.5
        assert gen._extract_rule_score({"severity": "low"}) == 0.7
        assert gen._extract_rule_score({"severity": "info"}) == 0.9
        assert gen._extract_rule_score({"severity": "unknown"}) == 0.5

    def test_extract_rule_score_missing_severity(self):
        """Test _extract_rule_score() with missing severity defaults to medium"""
        gen = HTMLReportGenerator()
        rule = {}

        score = gen._extract_rule_score(rule)

        assert score == 0.5  # medium default


# ============================================================================
# Tests for Chart Generation
# ============================================================================

class TestHTMLReportGeneratorCharts:
    """Tests for chart generation methods"""

    def test_get_severity_pie_chart(self, sample_result):
        """Test _get_severity_pie_chart() generates valid JS"""
        gen = HTMLReportGenerator()
        state = sample_result["state"]

        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])
        warnings = evaluation.get("warnings", [])

        severity_dist = gen.get_severity_distribution(failed_rules, warnings)
        chart_html = gen._get_severity_pie_chart(severity_dist)

        assert "severityCtx" in chart_html
        assert "new Chart" in chart_html
        assert "type: 'pie'" in chart_html
        # Check that labels array contains severity names
        assert '"high"' in chart_html or '"medium"' in chart_html
        assert "backgroundColor" in chart_html

    def test_get_severity_pie_chart_empty(self):
        """Test _get_severity_pie_chart() with empty distribution"""
        gen = HTMLReportGenerator()
        chart_html = gen._get_severity_pie_chart({})

        assert "No severity data" in chart_html

    def test_get_score_distribution_chart(self, sample_result):
        """Test _get_score_distribution_chart() generates valid JS"""
        gen = HTMLReportGenerator()

        # Create distribution stats
        dist_stats = {
            "count": 5,
            "min": 0.3,
            "max": 0.9,
            "mean": 0.6,
            "median": 0.6,
            "p25": 0.4,
            "p75": 0.8,
            "p90": 0.85,
            "p95": 0.88
        }

        chart_html = gen._get_score_distribution_chart(dist_stats)

        assert "scoreDistCtx" in chart_html
        assert "new Chart" in chart_html
        assert "type: 'bar'" in chart_html
        # Check that labels array contains percentile names
        assert '"Min"' in chart_html or '"P25"' in chart_html
        assert "Score (%)" in chart_html  # Dataset label

    def test_get_score_distribution_chart_empty(self):
        """Test _get_score_distribution_chart() with empty stats"""
        gen = HTMLReportGenerator()
        chart_html = gen._get_score_distribution_chart(None)

        assert "No score distribution data" in chart_html

    def test_get_score_distribution_chart_zero_count(self):
        """Test _get_score_distribution_chart() with zero count"""
        gen = HTMLReportGenerator()
        chart_html = gen._get_score_distribution_chart({"count": 0})

        assert "No score distribution data" in chart_html


# ============================================================================
# Tests for Convenience Function
# ============================================================================

class TestGenerateHtmlReport:
    """Tests for generate_html_report() convenience function"""

    def test_generate_html_report_returns_string(self, sample_result):
        """Test generate_html_report() returns HTML string"""
        html = generate_html_report(sample_result)

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html

    def test_generate_html_report_with_output_path(self, sample_result, temp_dir):
        """Test generate_html_report() saves to file"""
        output_file = temp_dir / "convenience_report.html"

        html = generate_html_report(sample_result, output_path=str(output_file))

        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == html

    def test_generate_html_report_with_options(self, sample_result):
        """Test generate_html_report() with options"""
        html = generate_html_report(
            sample_result,
            include_timeline=False,
            include_details=False
        )

        assert "Score Timeline" not in html
        assert "Failed Rules & Warnings" not in html


# ============================================================================
# Tests for Edge Cases and Integration
# ============================================================================

class TestHTMLReportGeneratorEdgeCases:
    """Tests for edge cases and integration scenarios"""

    def test_generate_with_unicode_characters(self):
        """Test generate() handles unicode in results"""
        gen = HTMLReportGenerator()
        result = {
            "state": {
                "run_id": "test-unicode-你好",
                "task_alias": "task-привет",
                "status": "completed",
                "evaluation": {
                    "failed_rules": [{
                        "rule_id": "ÜBER-001",
                        "category": "security",
                        "severity": "high",
                        "reason": "Sécurité: problème détecté",
                        "score": 0.3
                    }],
                    "warnings": []
                }
            },
            "score": 0.7,
            "passed": True,
            "priority_profile": "default"
        }

        html = gen.generate(result)

        assert "test-unicode-你好" in html
        assert "task-привет" in html

    def test_generate_with_large_failed_rules_list(self):
        """Test generate() handles many failed rules"""
        gen = HTMLReportGenerator()

        # Create 100 failed rules
        failed_rules = [
            {
                "rule_id": f"RULE{i:03d}",
                "category": "testing",
                "severity": "low",
                "reason": f"Test issue {i}",
                "score": 0.5
            }
            for i in range(100)
        ]

        result = {
            "state": {
                "run_id": "large-test",
                "task_alias": "large-task",
                "status": "completed",
                "evaluation": {
                    "failed_rules": failed_rules,
                    "warnings": []
                }
            },
            "score": 0.5,
            "passed": False,
            "priority_profile": "default"
        }

        html = gen.generate(result)

        assert "RULE000" in html
        assert "RULE099" in html

    def test_generate_html_encoding(self, sample_result, temp_dir):
        """Test generated HTML file uses UTF-8 encoding"""
        gen = HTMLReportGenerator()
        output_file = temp_dir / "encoding_test.html"

        gen.generate(sample_result, output_path=str(output_file))

        # Read as UTF-8
        content = output_file.read_text(encoding="utf-8")
        assert "charset=\"UTF-8\"" in content

    def test_multiple_generations_reusability(self, sample_result):
        """Test generator can be reused for multiple generations"""
        gen = HTMLReportGenerator()

        html1 = gen.generate(sample_result)
        html2 = gen.generate(sample_result)

        # Should produce identical output
        assert html1 == html2
