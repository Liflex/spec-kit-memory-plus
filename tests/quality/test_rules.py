"""
Unit tests for RuleManager
"""

import pytest
from pathlib import Path
from specify_cli.quality.rules import RuleManager, CriteriaNotFound


class TestRuleManager:
    """Test RuleManager class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.rule_manager = RuleManager()

    def test_list_criteria(self):
        """Test listing available criteria templates"""
        criteria = self.rule_manager.list_criteria()

        assert isinstance(criteria, list)
        assert len(criteria) > 0
        assert "code-gen" in criteria
        assert "api-spec" in criteria

    def test_load_criteria_exists(self):
        """Test loading an existing criteria template"""
        criteria = self.rule_manager.load_criteria("code-gen")

        assert criteria is not None
        assert criteria.name == "Code Generation"
        assert len(criteria.rules) > 0

    def test_load_criteria_not_found(self):
        """Test loading a non-existent criteria template"""
        with pytest.raises(CriteriaNotFound) as exc_info:
            self.rule_manager.load_criteria("non-existent")

        assert "non-existent" in str(exc_info.value)

    def test_get_rules_for_phase_a(self):
        """Test getting rules for Phase A"""
        criteria = self.rule_manager.load_criteria("code-gen")
        rules_a = self.rule_manager.get_rules_for_phase(criteria, "A")

        assert len(rules_a) > 0
        # Phase A should have active rules

    def test_get_rules_for_phase_b(self):
        """Test getting rules for Phase B"""
        criteria = self.rule_manager.load_criteria("code-gen")
        rules_b = self.rule_manager.get_rules_for_phase(criteria, "B")

        # Phase B might have fewer rules than A
        assert isinstance(rules_b, list)

    def test_auto_detect_criteria_api(self):
        """Test auto-detect for API-related descriptions"""
        detected = self.rule_manager.auto_detect_criteria("Create REST API endpoint")

        assert detected == "api-spec"

    def test_auto_detect_criteria_code(self):
        """Test auto-detect for code-related descriptions"""
        detected = self.rule_manager.auto_detect_criteria("Implement user class")

        assert detected == "code-gen"

    def test_auto_detect_criteria_docs(self):
        """Test auto-detect for documentation descriptions"""
        detected = self.rule_manager.auto_detect_criteria("Write README documentation")

        assert detected == "docs"

    def test_auto_detect_criteria_config(self):
        """Test auto-detect for configuration descriptions"""
        detected = self.rule_manager.auto_detect_criteria("Update config settings")

        assert detected == "config"

    def test_auto_detect_criteria_default(self):
        """Test auto-detect default for unknown descriptions"""
        detected = self.rule_manager.auto_detect_criteria("Do something random")

        assert detected == "code-gen"  # Default
