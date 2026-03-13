"""
Test Suite for Result Card Module (Exp 136)

Covers:
- ResultStatus Enum
- Dataclasses (CategorySummary, ActionItem, ResultCardData)
- ResultCardFormatter class
- Helper functions (create_result_card_data, format_result_card, etc.)
"""

import pytest
from dataclasses import asdict
from specify_cli.quality.result_card import (
    ResultStatus,
    CategorySummary,
    ActionItem,
    ResultCardData,
    ResultCardFormatter,
    create_result_card_data,
    _create_category_summaries,
    format_result_card,
    print_result_card,
)


# =============================================================================
# ResultStatus Enum Tests
# =============================================================================

class TestResultStatus:
    """Test ResultStatus enum values and behavior"""

    def test_status_values(self):
        """Test all expected status values exist"""
        expected_statuses = [
            "EXCELLENT",  # 0.95+ score, no failed rules
            "GOOD",       # 0.85+ score
            "ACCEPTABLE", # 0.75+ score
            "NEEDS_WORK", # 0.65+ score
            "CRITICAL",   # < 0.65 score
        ]
        actual_statuses = [s.name for s in ResultStatus]
        assert actual_statuses == expected_statuses

    def test_status_from_string(self):
        """Test creating status from string value"""
        status = ResultStatus("excellent")
        assert status == ResultStatus.EXCELLENT

    def test_status_value_attribute(self):
        """Test status value attribute"""
        assert ResultStatus.CRITICAL.value == "critical"
        assert ResultStatus.EXCELLENT.value == "excellent"


# =============================================================================
# CategorySummary Dataclass Tests
# =============================================================================

class TestCategorySummary:
    """Test CategorySummary dataclass"""

    def test_creation(self):
        """Test creating CategorySummary"""
        summary = CategorySummary(
            category="security",
            failed_count=3,
            warning_count=1,
            total_count=4,
            priority="high",
            sample_rules=["AUTH_001", "AUTH_002"],
        )
        assert summary.category == "security"
        assert summary.failed_count == 3
        assert summary.warning_count == 1
        assert summary.total_count == 4
        assert summary.priority == "high"
        assert summary.sample_rules == ["AUTH_001", "AUTH_002"]

    def test_defaults(self):
        """Test default values"""
        summary = CategorySummary(
            category="testing",
            failed_count=0,
            warning_count=0,
            total_count=0,
            priority="low",
        )
        assert summary.sample_rules == []

    def test_to_dict(self):
        """Test converting to dict"""
        summary = CategorySummary(
            category="performance",
            failed_count=2,
            warning_count=0,
            total_count=2,
            priority="medium",
            sample_rules=["PERF_001"],
        )
        data = asdict(summary)
        assert data["category"] == "performance"
        assert data["failed_count"] == 2


# =============================================================================
# ActionItem Dataclass Tests
# =============================================================================

class TestActionItem:
    """Test ActionItem dataclass"""

    def test_creation_with_command(self):
        """Test creating ActionItem with command"""
        action = ActionItem(
            priority="critical",
            title="Fix security issues",
            command="speckit.loop --fix-security",
            description="Fix authentication vulnerabilities",
        )
        assert action.priority == "critical"
        assert action.title == "Fix security issues"
        assert action.command == "speckit.loop --fix-security"
        assert action.description == "Fix authentication vulnerabilities"

    def test_creation_minimal(self):
        """Test creating ActionItem with minimal fields"""
        action = ActionItem(
            priority="low",
            title="Minor cleanup",
        )
        assert action.priority == "low"
        assert action.title == "Minor cleanup"
        assert action.command is None
        assert action.description is None

    def test_to_dict(self):
        """Test converting to dict"""
        action = ActionItem(
            priority="high",
            title="Improve tests",
            command="pytest tests/",
        )
        data = asdict(action)
        assert data["priority"] == "high"
        assert data["title"] == "Improve tests"


# =============================================================================
# ResultCardData Dataclass Tests
# =============================================================================

class TestResultCardData:
    """Test ResultCardData dataclass"""

    def test_creation_basic(self):
        """Test creating ResultCardData with basic fields"""
        data = ResultCardData(
            score=0.85,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=2,
            max_iterations=4,
            phase="B",
            total_rules=20,
            passed_rules=17,
            failed_rules=3,
            warnings=1,
        )
        assert data.score == 0.85
        assert data.passed is True
        assert data.status == ResultStatus.GOOD
        assert data.iteration == 2
        assert data.max_iterations == 4

    def test_defaults(self):
        """Test default values"""
        data = ResultCardData(
            score=0.5,
            passed=False,
            status=ResultStatus.CRITICAL,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=10,
            passed_rules=5,
            failed_rules=5,
            warnings=0,
        )
        assert data.duration_seconds == 0.0
        assert data.category_summaries == []
        assert data.action_items == []
        assert data.priority_profile == "default"
        assert data.trend_change is None
        assert data.gate_status is None

    def test_with_optional_fields(self):
        """Test with all optional fields"""
        data = ResultCardData(
            score=0.90,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=3,
            max_iterations=4,
            phase="C",
            total_rules=30,
            passed_rules=27,
            failed_rules=3,
            warnings=2,
            duration_seconds=45.5,
            category_summaries=[
                CategorySummary("security", 2, 0, 2, "high", ["SEC_001"])
            ],
            action_items=[
                ActionItem("high", "Fix auth", "speckit.loop --fix-auth")
            ],
            priority_profile="strict",
            trend_change=0.05,
            gate_status="PASSED",
        )
        assert data.duration_seconds == 45.5
        assert len(data.category_summaries) == 1
        assert data.trend_change == 0.05
        assert data.gate_status == "PASSED"


# =============================================================================
# ResultCardFormatter Initialization Tests
# =============================================================================

class TestResultCardFormatterInit:
    """Test ResultCardFormatter initialization"""

    def test_default_initialization(self):
        """Test default initialization"""
        formatter = ResultCardFormatter()
        assert formatter.compact is False
        # Terminal capabilities auto-detected
        assert hasattr(formatter, '_terminal_info')

    def test_compact_mode(self):
        """Test compact mode"""
        formatter = ResultCardFormatter(compact=True)
        assert formatter.compact is True

    def test_force_unicode(self):
        """Test forcing Unicode on/off"""
        formatter_unicode = ResultCardFormatter(use_unicode=True)
        formatter_ascii = ResultCardFormatter(use_unicode=False)
        assert formatter_unicode._supports_unicode is True
        assert formatter_ascii._supports_unicode is False

    def test_force_colors(self):
        """Test forcing colors on/off"""
        formatter_colors = ResultCardFormatter(use_colors=True)
        formatter_no_colors = ResultCardFormatter(use_colors=False)
        assert formatter_colors._supports_colors is True
        assert formatter_no_colors._supports_colors is False


# =============================================================================
# ResultCardFormatter Color and Status Tests
# =============================================================================

class TestResultCardFormatterColors:
    """Test color and status handling in ResultCardFormatter"""

    def test_get_status_color(self):
        """Test _get_status_color returns correct colors"""
        formatter = ResultCardFormatter()

        assert formatter._get_status_color(ResultStatus.EXCELLENT) == "green"
        assert formatter._get_status_color(ResultStatus.GOOD) == "cyan"
        assert formatter._get_status_color(ResultStatus.ACCEPTABLE) == "yellow"
        assert formatter._get_status_color(ResultStatus.NEEDS_WORK) == "bright_yellow"
        assert formatter._get_status_color(ResultStatus.CRITICAL) == "red"

    def test_get_priority_color(self):
        """Test _get_priority_color returns correct colors"""
        formatter = ResultCardFormatter()

        assert formatter._get_priority_color("critical") == "red"
        assert formatter._get_priority_color("high") == "bright_red"
        assert formatter._get_priority_color("medium") == "yellow"
        assert formatter._get_priority_color("low") == "gray"
        assert formatter._get_priority_color("unknown") == "gray"  # fallback

    def test_format_score_bar(self):
        """Test _format_score_bar visual bar"""
        formatter = ResultCardFormatter(use_colors=False)

        # Excellent score (green)
        bar_100 = formatter._format_score_bar(1.0)
        assert "[" in bar_100 and "]" in bar_100

        # Medium score (yellow)
        bar_70 = formatter._format_score_bar(0.7)
        assert "[" in bar_70 and "]" in bar_70

        # Low score (red)
        bar_50 = formatter._format_score_bar(0.5)
        assert "[" in bar_50 and "]" in bar_50

    def test_format_duration(self):
        """Test _format_duration time formatting"""
        formatter = ResultCardFormatter()

        # Milliseconds
        assert formatter._format_duration(0.5) == "500ms"
        assert formatter._format_duration(0.123) == "123ms"

        # Seconds
        assert formatter._format_duration(5.5) == "5.5s"
        assert formatter._format_duration(45.0) == "45.0s"

        # Minutes (note: 125.5s = 2m 5.5s, rounds to 2m 6s)
        assert formatter._format_duration(65.0) == "1m 5s"
        assert formatter._format_duration(125.5) == "2m 6s"


# =============================================================================
# ResultCardFormatter Status Determination Tests
# =============================================================================

class TestResultCardFormatterDetermineStatus:
    """Test _determine_status logic"""

    def test_status_critical_many_failures(self):
        """Test CRITICAL when many failed rules"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.80,
            passed=False,
            status=ResultStatus.GOOD,  # Will be overridden
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=10,
            failed_rules=10,  # > 5 failures
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.CRITICAL

    def test_status_critical_low_score(self):
        """Test CRITICAL when score < 0.65"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.60,
            passed=False,
            status=ResultStatus.GOOD,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=12,
            failed_rules=3,
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.CRITICAL

    def test_status_excellent(self):
        """Test EXCELLENT when score >= 0.95 and no failures"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.95,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=20,
            failed_rules=0,  # No failures
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.EXCELLENT

    def test_status_good(self):
        """Test GOOD when score >= 0.85"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.88,
            passed=True,
            status=ResultStatus.ACCEPTABLE,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=18,
            failed_rules=2,
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.GOOD

    def test_status_acceptable(self):
        """Test ACCEPTABLE when score >= 0.75"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.78,
            passed=True,
            status=ResultStatus.CRITICAL,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=16,
            failed_rules=4,
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.ACCEPTABLE

    def test_status_needs_work(self):
        """Test NEEDS_WORK when score >= 0.65 but < 0.75 and < 5 failures"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.70,
            passed=False,
            status=ResultStatus.CRITICAL,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=14,
            failed_rules=4,  # < 5 failures
            warnings=0,
        )
        status = formatter._determine_status(data)
        assert status == ResultStatus.NEEDS_WORK


# =============================================================================
# ResultCardFormatter Action Items Tests
# =============================================================================

class TestResultCardFormatterActionItems:
    """Test _generate_action_items"""

    def test_generate_actions_with_failures(self):
        """Test generating actions for failed rules"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.70,
            passed=False,
            status=ResultStatus.NEEDS_WORK,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=15,
            failed_rules=5,
            warnings=0,
            category_summaries=[
                CategorySummary("security", 3, 0, 3, "high", ["AUTH_001", "AUTH_002"]),
                CategorySummary("testing", 2, 0, 2, "medium", ["TEST_001"]),
            ],
        )
        actions = formatter._generate_action_items(data)
        assert len(actions) > 0
        # Should have actions for fixing categories
        assert any("security" in a.title.lower() for a in actions)

    def test_generate_actions_score_improvement(self):
        """Test generating score improvement action"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.80,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=16,
            failed_rules=4,
            warnings=0,
            category_summaries=[],
        )
        actions = formatter._generate_action_items(data)
        assert any("Improve quality score" in a.title for a in actions)

    def test_generate_actions_goals_suggestion(self):
        """Test generating goals suggestion for low scores"""
        formatter = ResultCardFormatter()
        data = ResultCardData(
            score=0.75,
            passed=True,
            status=ResultStatus.ACCEPTABLE,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=15,
            failed_rules=5,
            warnings=0,
            category_summaries=[],
        )
        actions = formatter._generate_action_items(data)
        assert any("quality goals" in a.title.lower() for a in actions)


# =============================================================================
# ResultCardFormatter Format Tests
# =============================================================================

class TestResultCardFormatterFormat:
    """Test format() method"""

    def test_format_basic(self):
        """Test basic format with minimal data"""
        formatter = ResultCardFormatter(use_colors=False, use_unicode=False)
        data = ResultCardData(
            score=0.85,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=2,
            max_iterations=4,
            phase="B",
            total_rules=20,
            passed_rules=17,
            failed_rules=3,
            warnings=1,
        )
        output = formatter.format(data)
        assert isinstance(output, str)
        assert len(output) > 0
        assert "0.85" in output or "85" in output

    def test_format_with_trend(self):
        """Test format with trend indicator"""
        formatter = ResultCardFormatter(use_colors=False, use_unicode=False)
        data = ResultCardData(
            score=0.90,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=2,
            max_iterations=4,
            phase="B",
            total_rules=20,
            passed_rules=18,
            failed_rules=2,
            warnings=0,
            trend_change=0.05,  # Improved by 0.05
        )
        output = formatter.format(data)
        assert "Trend" in output or "trend" in output

    def test_format_with_gate_status(self):
        """Test format with gate status"""
        formatter = ResultCardFormatter(use_colors=False, use_unicode=False)
        data = ResultCardData(
            score=0.85,
            passed=True,
            status=ResultStatus.GOOD,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=17,
            failed_rules=3,
            warnings=0,
            gate_status="PASSED",
        )
        output = formatter.format(data)
        assert "Gate" in output or "gate" in output

    def test_format_compact_mode(self):
        """Test compact mode format"""
        formatter = ResultCardFormatter(compact=True, use_colors=False, use_unicode=False)
        data = ResultCardData(
            score=0.75,
            passed=True,
            status=ResultStatus.ACCEPTABLE,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=15,
            passed_rules=12,
            failed_rules=3,
            warnings=0,
        )
        output = formatter.format(data)
        # Compact mode should be shorter
        assert isinstance(output, str)

    def test_format_with_category_summaries(self):
        """Test format with category breakdown"""
        formatter = ResultCardFormatter(use_colors=False, use_unicode=False)
        data = ResultCardData(
            score=0.70,
            passed=False,
            status=ResultStatus.NEEDS_WORK,
            iteration=1,
            max_iterations=4,
            phase="A",
            total_rules=20,
            passed_rules=14,
            failed_rules=6,
            warnings=0,
            category_summaries=[
                CategorySummary("security", 3, 0, 3, "high", ["SEC_001"]),
                CategorySummary("testing", 2, 0, 2, "medium", ["TEST_001"]),
                CategorySummary("performance", 1, 0, 1, "low", ["PERF_001"]),
            ],
        )
        output = formatter.format(data)
        # Should mention categories
        assert "Category" in output or "category" in output or "security" in output.lower()


# =============================================================================
# Helper Functions Tests
# =============================================================================

class TestCreateResultCardData:
    """Test create_result_card_data function"""

    def test_create_from_result_basic(self):
        """Test creating ResultCardData from basic result dict"""
        result = {
            "score": 0.85,
            "passed": True,
            "state": {
                "iteration": 2,
                "max_iterations": 4,
                "phase": "B",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 17,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "TEST_002", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        data = create_result_card_data(result)
        assert data.score == 0.85
        assert data.passed is True
        assert data.iteration == 2
        assert data.total_rules == 20
        assert data.passed_rules == 17
        assert data.failed_rules == 3

    def test_create_with_previous_score(self):
        """Test trend calculation with previous score"""
        result = {
            "score": 0.90,
            "passed": True,
            "state": {
                "iteration": 2,
                "max_iterations": 4,
                "phase": "B",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 18,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        data = create_result_card_data(result, previous_score=0.85)
        assert data.trend_change == pytest.approx(0.05)  # Use approx for float comparison

    def test_create_with_gate_result(self):
        """Test with gate result"""
        result = {
            "score": 0.85,
            "passed": True,
            "gate_result": {
                "gate_result": "PASSED"
            },
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 17,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "TEST_002", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        data = create_result_card_data(result)
        assert data.gate_status == "PASSED"

    def test_create_determines_status(self):
        """Test status is determined from score and failures"""
        result = {
            "score": 0.60,
            "passed": False,
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 12,
                    "failed_rules": [
                        {"rule_id": f"TEST_{i:03d}", "category": "testing"}
                        for i in range(8)
                    ],
                    "warnings": [],
                }
            }
        }
        data = create_result_card_data(result)
        # Low score with many failures = CRITICAL
        assert data.status == ResultStatus.CRITICAL


class TestCreateCategorySummaries:
    """Test _create_category_summaries function"""

    def test_empty_evaluation(self):
        """Test with no failed rules"""
        evaluation = {
            "failed_rules": []
        }
        summaries = _create_category_summaries(evaluation)
        assert summaries == []

    def test_single_category(self):
        """Test with single category failures"""
        evaluation = {
            "failed_rules": [
                {"rule_id": "SEC_001", "category": "security", "severity": "critical"},
                {"rule_id": "SEC_002", "category": "security", "severity": "high"},
            ]
        }
        summaries = _create_category_summaries(evaluation)
        assert len(summaries) == 1
        assert summaries[0].category == "security"
        assert summaries[0].failed_count == 2

    def test_multiple_categories(self):
        """Test with multiple category failures"""
        evaluation = {
            "failed_rules": [
                {"rule_id": "SEC_001", "category": "security"},
                {"rule_id": "SEC_002", "category": "security"},
                {"rule_id": "SEC_003", "category": "security"},
                {"rule_id": "TEST_001", "category": "testing"},
                {"rule_id": "PERF_001", "category": "performance"},
            ]
        }
        summaries = _create_category_summaries(evaluation)
        assert len(summaries) == 3
        categories = [s.category for s in summaries]
        assert "security" in categories
        assert "testing" in categories
        assert "performance" in categories

    def test_priority_determination(self):
        """Test priority is based on count"""
        evaluation = {
            "failed_rules": [
                {"rule_id": f"SEC_{i:03d}", "category": "security"}
                for i in range(6)  # 6 failures = critical
            ] + [
                {"rule_id": f"TEST_{i:03d}", "category": "testing"}
                for i in range(3)  # 3 failures = high
            ] + [
                {"rule_id": f"PERF_{i:03d}", "category": "performance"}
                for i in range(1)  # 1 failure = medium
            ]
        }
        summaries = _create_category_summaries(evaluation)

        security = next(s for s in summaries if s.category == "security")
        testing = next(s for s in summaries if s.category == "testing")
        performance = next(s for s in summaries if s.category == "performance")

        assert security.priority == "critical"
        assert testing.priority == "high"
        assert performance.priority == "medium"

    def test_sorting(self):
        """Test summaries are sorted by priority then count"""
        evaluation = {
            "failed_rules": [
                {"rule_id": "LOW_001", "category": "low_priority"},
                {"rule_id": "HIGH_001", "category": "high_count"},
                {"rule_id": "HIGH_002", "category": "high_count"},
            ]
        }
        summaries = _create_category_summaries(evaluation)
        # high_count (2) should come before low_priority (1)
        assert summaries[0].failed_count >= summaries[-1].failed_count


class TestFormatResultCard:
    """Test format_result_card function"""

    def test_format_default(self):
        """Test format with default parameters"""
        result = {
            "score": 0.85,
            "passed": True,
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 17,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "TEST_002", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        output = format_result_card(result)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_compact(self):
        """Test format with compact=True"""
        result = {
            "score": 0.75,
            "passed": True,
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 15,
                    "passed_rules": 12,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "TEST_002", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        output = format_result_card(result, compact=True)
        assert isinstance(output, str)

    def test_format_with_theme(self):
        """Test format with different themes"""
        result = {
            "score": 0.90,
            "passed": True,
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 18,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        for theme in ["default", "dark", "high-contrast", "minimal"]:
            output = format_result_card(result, theme=theme)
            assert isinstance(output, str)

    def test_format_with_previous_score(self):
        """Test format with trend from previous score"""
        result = {
            "score": 0.92,
            "passed": True,
            "state": {
                "iteration": 2,
                "max_iterations": 4,
                "phase": "B",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 18,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        output = format_result_card(result, previous_score=0.85)
        assert isinstance(output, str)


class TestPrintResultCard:
    """Test print_result_card function"""

    def test_print_result_card(self, capsys):
        """Test print writes to stdout"""
        result = {
            "score": 0.88,
            "passed": True,
            "state": {
                "iteration": 1,
                "max_iterations": 4,
                "phase": "A",
                "evaluation": {
                    "total_rules": 20,
                    "passed_rules": 18,
                    "failed_rules": [
                        {"rule_id": "TEST_001", "category": "testing"},
                        {"rule_id": "SEC_001", "category": "security"},
                    ],
                    "warnings": [],
                }
            }
        }
        print_result_card(result, compact=False)
        captured = capsys.readouterr()
        assert len(captured.out) > 0
