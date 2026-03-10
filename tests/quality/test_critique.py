"""
Unit tests for Critique
"""

import pytest
from specify_cli.quality.critique import Critique


class TestCritique:
    """Test Critique class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.critique = Critique(max_issues=5)

    def test_generate_max_issues(self):
        """Test that critique limits to max_issues"""
        failed_rules = [
            {"rule_id": f"rule{i}", "reason": f"Reason {i}"}
            for i in range(10)  # More than max_issues
        ]

        artifact = "Some artifact content"
        result = self.critique.generate(failed_rules, artifact)

        assert result["total_failed"] == 10
        assert result["addressed"] == 5  # max_issues
        assert result["skipped"] == 5
        assert len(result["issues"]) == 5

    def test_generate_few_issues(self):
        """Test critique with fewer issues than max"""
        failed_rules = [
            {"rule_id": "rule1", "reason": "Reason 1"},
            {"rule_id": "rule2", "reason": "Reason 2"},
        ]

        artifact = "Some artifact content"
        result = self.critique.generate(failed_rules, artifact)

        assert result["total_failed"] == 2
        assert result["addressed"] == 2
        assert result["skipped"] == 0
        assert len(result["issues"]) == 2

    def test_generate_fix_instruction(self):
        """Test fix instruction generation"""
        failed = {"rule_id": "correctness.tests", "reason": "No tests found"}
        artifact = "Some code without tests"

        fix = self.critique._generate_fix_instruction(
            failed["rule_id"],
            failed["reason"],
            artifact
        )

        assert fix is not None
        assert len(fix) > 0
        assert "test" in fix.lower()  # Should mention tests

    def test_generate_no_failed_rules(self):
        """Test critique with no failed rules"""
        result = self.critique.generate([], "Some artifact")

        assert result["total_failed"] == 0
        assert result["addressed"] == 0
        assert len(result["issues"]) == 0
