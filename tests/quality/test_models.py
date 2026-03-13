"""Tests for quality data models (models.py)

Comprehensive test coverage for all data structures used in quality evaluation.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import yaml

from specify_cli.quality.models import (
    Phase,
    LoopStatus,
    StopReason,
    RuleSeverity,
    RuleCheckType,
    QualityRule,
    PhaseConfig,
    PriorityProfile,
    CriteriaTemplate,
    FailedRule,
    EvaluationResult,
    CritiqueResult,
    LoopState,
    LoopEvent,
)


class TestEnums:
    """Test enum definitions and values"""

    def test_phase_enum(self):
        """Phase enum has correct values"""
        assert Phase.A.value == "A"
        assert Phase.B.value == "B"

    def test_loop_status_enum(self):
        """LoopStatus enum has all expected statuses"""
        assert LoopStatus.running.value == "running"
        assert LoopStatus.completed.value == "completed"
        assert LoopStatus.stopped.value == "stopped"
        assert LoopStatus.failed.value == "failed"

    def test_stop_reason_enum(self):
        """StopReason enum has all expected reasons"""
        assert StopReason.threshold_reached.value == "threshold_reached"
        assert StopReason.no_major_issues.value == "no_major_issues"
        assert StopReason.iteration_limit.value == "iteration_limit"
        assert StopReason.stagnation.value == "stagnation"
        assert StopReason.user_stop.value == "user_stop"
        assert StopReason.error.value == "error"

    def test_rule_severity_enum(self):
        """RuleSeverity enum has correct weights implied"""
        assert RuleSeverity.fail.value == "fail"
        assert RuleSeverity.warn.value == "warn"
        assert RuleSeverity.info.value == "info"

    def test_rule_check_type_enum(self):
        """RuleCheckType enum has all types"""
        assert RuleCheckType.content.value == "content"
        assert RuleCheckType.executable.value == "executable"
        assert RuleCheckType.hybrid.value == "hybrid"


class TestQualityRule:
    """Test QualityRule dataclass"""

    def test_quality_rule_creation(self):
        """Create QualityRule with all fields"""
        rule = QualityRule(
            id="test-rule",
            description="Test rule description",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="some pattern",
            check_type=RuleCheckType.content,
            domain_tags=["web", "api"],
            category="security",
        )
        assert rule.id == "test-rule"
        assert rule.severity == RuleSeverity.fail
        assert rule.weight == 2
        assert rule.phase == Phase.A
        assert rule.domain_tags == ["web", "api"]
        assert rule.category == "security"

    def test_quality_rule_defaults(self):
        """QualityRule has correct default values"""
        rule = QualityRule(
            id="test-rule",
            description="Test",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.B,
            check="pattern",
        )
        assert rule.check_type == RuleCheckType.content
        assert rule.domain_tags == []
        assert rule.category == "general"

    def test_quality_rule_to_dict(self):
        """Convert QualityRule to dict"""
        rule = QualityRule(
            id="rule1",
            description="Test rule",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="pattern",
            domain_tags=["web"],
            category="performance",
        )
        data = rule.to_dict()
        assert data["id"] == "rule1"
        assert data["severity"] == "fail"
        assert data["weight"] == 2
        assert data["phase"] == "A"
        assert data["check"] == "pattern"
        assert data["check_type"] == "content"
        assert data["domain_tags"] == ["web"]
        assert data["category"] == "performance"

    def test_quality_rule_from_dict(self):
        """Create QualityRule from dict"""
        data = {
            "id": "rule2",
            "description": "Test",
            "severity": "warn",
            "weight": 1,
            "phase": "B",
            "check": "regex",
            "check_type": "content",
            "domain_tags": ["api"],
            "category": "testing",
        }
        rule = QualityRule.from_dict(data)
        assert rule.id == "rule2"
        assert rule.severity == RuleSeverity.warn
        assert rule.weight == 1
        assert rule.phase == Phase.B
        assert rule.domain_tags == ["api"]
        assert rule.category == "testing"

    def test_quality_rule_from_dict_string_weight(self):
        """Handle weight as string from YAML parsing"""
        data = {
            "id": "rule3",
            "description": "Test",
            "severity": "fail",
            "weight": "2",  # String from YAML
            "phase": "A",
            "check": "pattern",
        }
        rule = QualityRule.from_dict(data)
        assert rule.weight == 2
        assert isinstance(rule.weight, int)

    def test_quality_rule_from_dict_defaults(self):
        """Handle missing optional fields in from_dict"""
        data = {
            "id": "rule4",
            "description": "Test",
            "severity": "info",
            "weight": 0,
            "phase": "B",
            "check": "pattern",
        }
        rule = QualityRule.from_dict(data)
        assert rule.check_type == RuleCheckType.content
        assert rule.domain_tags == []
        assert rule.category == "general"

    def test_get_effective_weight_basic(self):
        """Basic effective weight without multipliers"""
        rule = QualityRule(
            id="rule1",
            description="Test",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="pattern",
            domain_tags=[],
        )
        assert rule.get_effective_weight({}) == 2.0

    def test_get_effective_weight_with_domain_multiplier(self):
        """Effective weight with domain multipliers"""
        rule = QualityRule(
            id="rule1",
            description="Test",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="pattern",
            domain_tags=["web", "api"],
        )
        multipliers = {"web": 1.5, "api": 2.0}
        # Max of matching tags = 2.0
        assert rule.get_effective_weight(multipliers) == 4.0  # 2 * 2.0

    def test_get_effective_weight_with_category_multiplier(self):
        """Effective weight with category multipliers (Exp 46)"""
        rule = QualityRule(
            id="rule1",
            description="Test",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="pattern",
            category="security",
        )
        category_multipliers = {"security": 1.5}
        assert rule.get_effective_weight({}, category_multipliers) == 3.0  # 2 * 1.5

    def test_get_effective_weight_with_both_multipliers(self):
        """Effective weight with both domain and category multipliers"""
        rule = QualityRule(
            id="rule1",
            description="Test",
            severity=RuleSeverity.fail,
            weight=2,
            phase=Phase.A,
            check="pattern",
            domain_tags=["web"],
            category="security",
        )
        domain_multipliers = {"web": 1.5}
        category_multipliers = {"security": 2.0}
        # 2 * 1.5 * 2.0 = 6.0
        assert rule.get_effective_weight(domain_multipliers, category_multipliers) == 6.0

    def test_get_effective_weight_no_match(self):
        """Returns base weight when no multipliers match"""
        rule = QualityRule(
            id="rule1",
            description="Test",
            severity=RuleSeverity.warn,
            weight=1,
            phase=Phase.B,
            check="pattern",
            domain_tags=["mobile"],
            category="ui",
        )
        multipliers = {"web": 2.0, "api": 1.5}
        category_multipliers = {"security": 1.5}
        # No match, should return base weight
        assert rule.get_effective_weight(multipliers, category_multipliers) == 1.0


class TestPhaseConfig:
    """Test PhaseConfig dataclass"""

    def test_phase_config_creation(self):
        """Create PhaseConfig with all fields"""
        config = PhaseConfig(threshold=0.8, active_levels=["A", "B"])
        assert config.threshold == 0.8
        assert config.active_levels == ["A", "B"]

    def test_phase_config_defaults(self):
        """PhaseConfig has correct default active_levels"""
        config = PhaseConfig(threshold=0.9)
        assert config.active_levels == ["A"]

    def test_phase_config_to_dict(self):
        """Convert PhaseConfig to dict"""
        config = PhaseConfig(threshold=0.85, active_levels=["A", "B"])
        data = config.to_dict()
        assert data["threshold"] == 0.85
        assert data["active_levels"] == ["A", "B"]

    def test_phase_config_from_dict(self):
        """Create PhaseConfig from dict"""
        data = {"threshold": 0.75, "active_levels": ["B"]}
        config = PhaseConfig.from_dict(data)
        assert config.threshold == 0.75
        assert config.active_levels == ["B"]

    def test_phase_config_from_dict_defaults(self):
        """Handle missing active_levels in from_dict"""
        data = {"threshold": 0.8}
        config = PhaseConfig.from_dict(data)
        assert config.threshold == 0.8
        assert config.active_levels == ["A"]


class TestPriorityProfile:
    """Test PriorityProfile dataclass"""

    def test_priority_profile_creation(self):
        """Create PriorityProfile with all fields"""
        profile = PriorityProfile(
            name="backend-focused",
            multipliers={"api": 2.0, "database": 1.5},
            description="Backend focused profile",
            category_multipliers={"security": 1.5, "performance": 1.3},
        )
        assert profile.name == "backend-focused"
        assert profile.multipliers == {"api": 2.0, "database": 1.5}
        assert profile.description == "Backend focused profile"
        assert profile.category_multipliers == {"security": 1.5, "performance": 1.3}

    def test_priority_profile_defaults(self):
        """PriorityProfile has correct default values"""
        profile = PriorityProfile(name="default")
        assert profile.multipliers == {}
        assert profile.description == ""
        assert profile.category_multipliers == {}

    def test_priority_profile_to_dict(self):
        """Convert PriorityProfile to dict"""
        profile = PriorityProfile(
            name="web-focused",
            multipliers={"web": 2.0},
            description="Web profile",
            category_multipliers={"ui": 1.5},
        )
        data = profile.to_dict()
        assert data["name"] == "web-focused"
        assert data["multipliers"] == {"web": 2.0}
        assert data["description"] == "Web profile"
        assert data["category_multipliers"] == {"ui": 1.5}

    def test_priority_profile_from_dict_nested(self):
        """Create PriorityProfile from nested dict format"""
        data = {
            "multipliers": {"web": 2.0, "api": 1.5},
            "description": "Full format",
            "category_multipliers": {"security": 1.5},
        }
        profile = PriorityProfile.from_dict("test-profile", data)
        assert profile.name == "test-profile"
        assert profile.multipliers == {"web": 2.0, "api": 1.5}
        assert profile.description == "Full format"
        assert profile.category_multipliers == {"security": 1.5}

    def test_priority_profile_from_dict_flat(self):
        """Create PriorityProfile from flat dict (backward compat)"""
        data = {"web": 2.0, "api": 1.5}
        profile = PriorityProfile.from_dict("flat-profile", data)
        assert profile.name == "flat-profile"
        assert profile.multipliers == {"web": 2.0, "api": 1.5}
        assert profile.description == ""
        assert profile.category_multipliers == {}

    def test_get_multiplier(self):
        """Get multiplier for domain tag"""
        profile = PriorityProfile(
            name="test",
            multipliers={"web": 2.0, "api": 1.5},
        )
        assert profile.get_multiplier("web") == 2.0
        assert profile.get_multiplier("api") == 1.5
        assert profile.get_multiplier("mobile") == 1.0  # Default

    def test_get_category_multiplier(self):
        """Get multiplier for category (Exp 46)"""
        profile = PriorityProfile(
            name="test",
            category_multipliers={"security": 1.5, "performance": 1.3},
        )
        assert profile.get_category_multiplier("security") == 1.5
        assert profile.get_category_multiplier("performance") == 1.3
        assert profile.get_category_multiplier("ui") == 1.0  # Default


class TestCriteriaTemplate:
    """Test CriteriaTemplate dataclass"""

    def test_criteria_template_creation(self):
        """Create CriteriaTemplate with all fields"""
        phases = {
            "a": PhaseConfig(threshold=0.8, active_levels=["A"]),
            "b": PhaseConfig(threshold=0.9, active_levels=["A", "B"]),
        }
        rules = [
            QualityRule(
                id="rule1",
                description="Test rule",
                severity=RuleSeverity.fail,
                weight=2,
                phase=Phase.A,
                check="pattern",
            )
        ]
        profiles = {
            "default": PriorityProfile(
                name="default",
                multipliers={"web": 1.0},
            )
        }

        template = CriteriaTemplate(
            name="test-template",
            version=1.0,
            description="Test template",
            phases=phases,
            rules=rules,
            priority_profiles=profiles,
        )

        assert template.name == "test-template"
        assert template.version == 1.0
        assert template.description == "Test template"
        assert len(template.rules) == 1
        assert len(template.priority_profiles) == 1

    def test_criteria_template_defaults(self):
        """CriteriaTemplate has correct default values"""
        template = CriteriaTemplate(
            name="minimal",
            version=1.0,
            description="Minimal template",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
        )
        assert template.priority_profiles == {}

    def test_get_phase_config_with_enum(self):
        """Get phase config using Phase enum"""
        phases = {
            "a": PhaseConfig(threshold=0.8, active_levels=["A"]),
            "b": PhaseConfig(threshold=0.9, active_levels=["A", "B"]),
        }
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases=phases,
            rules=[],
        )

        config_a = template.get_phase_config(Phase.A)
        assert config_a is not None
        assert config_a.threshold == 0.8

        config_b = template.get_phase_config(Phase.B)
        assert config_b is not None
        assert config_b.threshold == 0.9

    def test_get_phase_config_with_string(self):
        """Get phase config using string"""
        phases = {
            "a": PhaseConfig(threshold=0.8),
            "b": PhaseConfig(threshold=0.9),
        }
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases=phases,
            rules=[],
        )

        config = template.get_phase_config("a")
        assert config is not None
        assert config.threshold == 0.8

        config = template.get_phase_config("A")  # Case insensitive
        assert config is not None
        assert config.threshold == 0.8

    def test_get_phase_config_not_found(self):
        """Return None for non-existent phase"""
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
        )

        config = template.get_phase_config("c")
        assert config is None

    def test_get_active_rules(self):
        """Get rules active in a phase"""
        rules = [
            QualityRule(
                id="rule1",
                description="Rule 1",
                severity=RuleSeverity.fail,
                weight=2,
                phase=Phase.A,
                check="pattern1",
            ),
            QualityRule(
                id="rule2",
                description="Rule 2",
                severity=RuleSeverity.warn,
                weight=1,
                phase=Phase.B,
                check="pattern2",
            ),
            QualityRule(
                id="rule3",
                description="Rule 3",
                severity=RuleSeverity.info,
                weight=0,
                phase=Phase.A,
                check="pattern3",
            ),
        ]
        phases = {
            "a": PhaseConfig(threshold=0.8, active_levels=["A"]),
            "b": PhaseConfig(threshold=0.9, active_levels=["A", "B"]),
        }
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases=phases,
            rules=rules,
        )

        # Phase A only
        active_a = template.get_active_rules(Phase.A)
        assert len(active_a) == 2
        assert {r.id for r in active_a} == {"rule1", "rule3"}

        # Phase A and B
        active_b = template.get_active_rules(Phase.B)
        assert len(active_b) == 3
        assert {r.id for r in active_b} == {"rule1", "rule2", "rule3"}

    def test_get_active_rules_no_config(self):
        """Return empty list when phase config not found"""
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
        )

        active = template.get_active_rules("b")
        assert active == []

    def test_get_priority_profile_builtin(self):
        """Get built-in priority profile"""
        profiles = {
            "backend": PriorityProfile(
                name="backend",
                multipliers={"api": 2.0},
            )
        }
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles=profiles,
        )

        profile = template.get_priority_profile("backend")
        assert profile is not None
        assert profile.name == "backend"
        assert profile.multipliers == {"api": 2.0}

    def test_get_priority_profile_not_found(self):
        """Return None for non-existent profile"""
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles={},
        )

        profile = template.get_priority_profile("nonexistent")
        assert profile is None

    def test_get_priority_profile_custom_file(self):
        """Get priority profile from custom project file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .speckit directory and priority-profiles.yml
            speckit_dir = Path(tmpdir) / ".speckit"
            speckit_dir.mkdir()
            profiles_file = speckit_dir / "priority-profiles.yml"

            custom_data = {
                "priority_profiles": {
                    "custom-profile": {
                        "multipliers": {"web": 3.0},
                        "description": "Custom profile",
                        "category_multipliers": {"ui": 2.0},
                    }
                }
            }

            with open(profiles_file, "w", encoding="utf-8") as f:
                yaml.dump(custom_data, f)

            template = CriteriaTemplate(
                name="test",
                version=1.0,
                description="Test",
                phases={"a": PhaseConfig(threshold=0.8)},
                rules=[],
                priority_profiles={},
            )

            profile = template.get_priority_profile("custom-profile", project_root=tmpdir)
            assert profile is not None
            assert profile.name == "custom-profile"
            assert profile.multipliers == {"web": 3.0}
            assert profile.category_multipliers == {"ui": 2.0}

    def test_list_priority_profiles_builtin_only(self):
        """List built-in priority profiles"""
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles={"default": PriorityProfile(name="default"), "backend": PriorityProfile(name="backend")},
        )

        profiles = template.list_priority_profiles()
        assert set(profiles) == {"default", "backend"}

    def test_list_priority_profiles_with_custom(self):
        """List priority profiles including custom from project"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create custom profiles file
            speckit_dir = Path(tmpdir) / ".speckit"
            speckit_dir.mkdir()
            profiles_file = speckit_dir / "priority-profiles.yml"

            custom_data = {
                "priority_profiles": {
                    "custom1": {"multipliers": {"web": 2.0}},
                    "custom2": {"multipliers": {"api": 1.5}},
                }
            }

            with open(profiles_file, "w", encoding="utf-8") as f:
                yaml.dump(custom_data, f)

            template = CriteriaTemplate(
                name="test",
                version=1.0,
                description="Test",
                phases={"a": PhaseConfig(threshold=0.8)},
                rules=[],
                priority_profiles={"builtin": PriorityProfile(name="builtin")},
            )

            profiles = template.list_priority_profiles(project_root=tmpdir)
            assert set(profiles) == {"builtin", "custom1", "custom2"}

    def test_get_default_profile_existing(self):
        """Get existing default profile"""
        default_profile = PriorityProfile(
            name="default",
            multipliers={"web": 1.0},
        )
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles={"default": default_profile},
        )

        profile = template.get_default_profile()
        assert profile is default_profile

    def test_get_default_profile_create(self):
        """Create default profile if not exists"""
        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases={"a": PhaseConfig(threshold=0.8)},
            rules=[],
            priority_profiles={},
        )

        profile = template.get_default_profile()
        assert profile is not None
        assert profile.name == "default"
        assert "web" in profile.multipliers
        assert "api" in profile.multipliers
        assert profile.multipliers["web"] == 1.0

        # Should be added to template
        assert "default" in template.priority_profiles

    def test_criteria_template_to_dict(self):
        """Convert CriteriaTemplate to dict"""
        phases = {"a": PhaseConfig(threshold=0.8)}
        rules = [
            QualityRule(
                id="rule1",
                description="Test",
                severity=RuleSeverity.fail,
                weight=2,
                phase=Phase.A,
                check="pattern",
            )
        ]
        profiles = {"default": PriorityProfile(name="default", multipliers={"web": 1.0})}

        template = CriteriaTemplate(
            name="test",
            version=1.0,
            description="Test",
            phases=phases,
            rules=rules,
            priority_profiles=profiles,
        )

        data = template.to_dict()
        assert data["name"] == "test"
        assert data["version"] == 1.0
        assert data["description"] == "Test"
        assert "a" in data["phases"]
        assert len(data["rules"]) == 1
        assert "default" in data["priority_profiles"]

    def test_criteria_template_from_dict(self):
        """Create CriteriaTemplate from dict"""
        data = {
            "name": "test",
            "version": 1.0,
            "description": "Test template",
            "phases": {
                "a": {"threshold": 0.8, "active_levels": ["A"]},
                "b": {"threshold": 0.9, "active_levels": ["A", "B"]},
            },
            "rules": [
                {
                    "id": "rule1",
                    "description": "Test rule",
                    "severity": "fail",
                    "weight": 2,
                    "phase": "A",
                    "check": "pattern",
                    "check_type": "content",
                    "domain_tags": [],
                    "category": "general",
                }
            ],
            "priority_profiles": {
                "default": {
                    "multipliers": {"web": 1.0},
                    "description": "Default",
                    "category_multipliers": {},
                }
            },
        }

        template = CriteriaTemplate.from_dict(data)
        assert template.name == "test"
        assert template.version == 1.0
        assert len(template.phases) == 2
        assert len(template.rules) == 1
        assert len(template.priority_profiles) == 1


class TestFailedRule:
    """Test FailedRule dataclass"""

    def test_failed_rule_creation(self):
        """Create FailedRule with all fields"""
        failed = FailedRule(
            rule_id="rule1",
            reason="Test failed",
            category="security",
        )
        assert failed.rule_id == "rule1"
        assert failed.reason == "Test failed"
        assert failed.category == "security"

    def test_failed_rule_defaults(self):
        """FailedRule has correct default category"""
        failed = FailedRule(
            rule_id="rule2",
            reason="Warning",
        )
        assert failed.category == "general"

    def test_failed_rule_to_dict(self):
        """Convert FailedRule to dict"""
        failed = FailedRule(
            rule_id="rule1",
            reason="Test failed",
            category="performance",
        )
        data = failed.to_dict()
        assert data["rule_id"] == "rule1"
        assert data["reason"] == "Test failed"
        assert data["category"] == "performance"

    def test_failed_rule_from_dict(self):
        """Create FailedRule from dict"""
        data = {
            "rule_id": "rule2",
            "reason": "Warning message",
            "category": "ui",
        }
        failed = FailedRule.from_dict(data)
        assert failed.rule_id == "rule2"
        assert failed.reason == "Warning message"
        assert failed.category == "ui"

    def test_failed_rule_from_dict_defaults(self):
        """Handle missing category in from_dict"""
        data = {
            "rule_id": "rule3",
            "reason": "Test",
        }
        failed = FailedRule.from_dict(data)
        assert failed.category == "general"


class TestEvaluationResult:
    """Test EvaluationResult dataclass"""

    def test_evaluation_result_creation(self):
        """Create EvaluationResult with all fields"""
        passed_rules = ["rule1", "rule2"]
        failed_rules = [
            FailedRule(rule_id="rule3", reason="Failed"),
        ]
        warnings = [
            FailedRule(rule_id="rule4", reason="Warning"),
        ]

        result = EvaluationResult(
            score=0.85,
            passed=True,
            threshold=0.8,
            phase="A",
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            evaluated_at="2024-01-01T12:00:00",
            priority_profile="backend",
            category_breakdown={"security": 0.9, "performance": 0.8},
            category_scores={"security": {"passed": 10, "failed": 1}},
            severity_counts={"fail": 1, "warn": 1},
        )

        assert result.score == 0.85
        assert result.passed is True
        assert result.threshold == 0.8
        assert result.phase == "A"
        assert result.priority_profile == "backend"
        assert result.category_breakdown == {"security": 0.9, "performance": 0.8}

    def test_evaluation_result_defaults(self):
        """EvaluationResult has correct default values"""
        result = EvaluationResult(
            score=0.75,
            passed=False,
            threshold=0.8,
            phase="B",
            passed_rules=[],
            failed_rules=[],
            warnings=[],
            evaluated_at="2024-01-01",
        )
        assert result.priority_profile is None
        assert result.category_breakdown is None
        assert result.category_scores is None
        assert result.severity_counts is None

    def test_evaluation_result_to_dict(self):
        """Convert EvaluationResult to dict"""
        result = EvaluationResult(
            score=0.9,
            passed=True,
            threshold=0.85,
            phase="A",
            passed_rules=["rule1"],
            failed_rules=[],
            warnings=[],
            evaluated_at="2024-01-01",
            priority_profile="default",
            severity_counts={"fail": 0, "warn": 0},
        )

        data = result.to_dict()
        assert data["score"] == 0.9
        assert data["passed"] is True
        assert data["threshold"] == 0.85
        assert data["phase"] == "A"
        assert data["priority_profile"] == "default"
        assert data["severity_counts"] == {"fail": 0, "warn": 0}

    def test_evaluation_result_from_dict(self):
        """Create EvaluationResult from dict"""
        data = {
            "score": 0.85,
            "passed": True,
            "threshold": 0.8,
            "phase": "A",
            "passed_rules": ["rule1", "rule2"],
            "failed_rules": [],
            "warnings": [],
            "evaluated_at": "2024-01-01",
            "priority_profile": "backend",
            "category_breakdown": {"security": 0.9},
            "category_scores": {"security": {"passed": 5}},
            "severity_counts": {"fail": 0, "warn": 1},
        }

        result = EvaluationResult.from_dict(data)
        assert result.score == 0.85
        assert result.passed is True
        assert result.priority_profile == "backend"
        assert result.category_breakdown == {"security": 0.9}
        assert result.severity_counts == {"fail": 0, "warn": 1}

    def test_evaluation_result_from_dict_defaults(self):
        """Handle missing optional fields in from_dict"""
        data = {
            "score": 0.75,
            "passed": False,
            "threshold": 0.8,
            "phase": "B",
            "passed_rules": [],
            "failed_rules": [],
            "warnings": [],
            "evaluated_at": "2024-01-01",
        }

        result = EvaluationResult.from_dict(data)
        assert result.priority_profile is None
        assert result.category_breakdown is None
        assert result.category_scores is None
        assert result.severity_counts is None


class TestCritiqueResult:
    """Test CritiqueResult dataclass"""

    def test_critique_result_creation(self):
        """Create CritiqueResult with all fields"""
        issues = [
            {"rule_id": "rule1", "reason": "Issue 1", "fix": "Fix 1"},
            {"rule_id": "rule2", "reason": "Issue 2", "fix": "Fix 2"},
        ]

        result = CritiqueResult(
            issues=issues,
            total_failed=2,
            addressed=1,
            skipped=1,
        )

        assert len(result.issues) == 2
        assert result.total_failed == 2
        assert result.addressed == 1
        assert result.skipped == 1

    def test_critique_result_defaults(self):
        """CritiqueResult creates with skipped=0"""
        result = CritiqueResult(
            issues=[],
            total_failed=0,
            addressed=0,
            skipped=0,
        )
        assert result.skipped == 0

    def test_critique_result_to_dict(self):
        """Convert CritiqueResult to dict"""
        issues = [{"rule_id": "rule1", "reason": "Issue", "fix": "Fix"}]
        result = CritiqueResult(
            issues=issues,
            total_failed=1,
            addressed=1,
            skipped=0,
        )

        data = result.to_dict()
        assert len(data["issues"]) == 1
        assert data["total_failed"] == 1
        assert data["addressed"] == 1
        assert data["skipped"] == 0

    def test_critique_result_from_dict(self):
        """Create CritiqueResult from dict"""
        data = {
            "issues": [
                {"rule_id": "rule1", "reason": "Issue", "fix": "Fix"}
            ],
            "total_failed": 1,
            "addressed": 0,
            "skipped": 1,
        }

        result = CritiqueResult.from_dict(data)
        assert len(result.issues) == 1
        assert result.total_failed == 1
        assert result.addressed == 0
        assert result.skipped == 1

    def test_critique_result_from_dict_defaults(self):
        """Handle missing skipped in from_dict"""
        data = {
            "issues": [],
            "total_failed": 0,
            "addressed": 0,
        }

        result = CritiqueResult.from_dict(data)
        assert result.skipped == 0


class TestLoopState:
    """Test LoopState dataclass"""

    def test_loop_state_creation(self):
        """Create LoopState with all fields"""
        evaluation = EvaluationResult(
            score=0.85,
            passed=True,
            threshold=0.8,
            phase="A",
            passed_rules=[],
            failed_rules=[],
            warnings=[],
            evaluated_at="2024-01-01",
        )
        critique = CritiqueResult(
            issues=[],
            total_failed=0,
            addressed=0,
            skipped=0,
        )

        state = LoopState(
            run_id="run-123",
            task_alias="test-task",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="evaluating",
            current_score=0.85,
            last_score=0.75,
            evaluation=evaluation,
            critique=critique,
            stop={"reason": "threshold_reached"},
            started_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:05:00",
            priority_profile="backend",
        )

        assert state.run_id == "run-123"
        assert state.task_alias == "test-task"
        assert state.status == LoopStatus.running
        assert state.iteration == 1
        assert state.max_iterations == 4
        assert state.phase == Phase.A
        assert state.current_step == "evaluating"
        assert state.current_score == 0.85
        assert state.last_score == 0.75
        assert state.priority_profile == "backend"

    def test_loop_state_defaults(self):
        """LoopState has correct default optional values"""
        state = LoopState(
            run_id="run-456",
            task_alias="task2",
            status=LoopStatus.completed,
            iteration=4,
            max_iterations=4,
            phase=Phase.B,
            current_step="completed",
        )
        assert state.current_score is None
        assert state.last_score is None
        assert state.evaluation is None
        assert state.critique is None
        assert state.stop is None
        assert state.started_at is None
        assert state.updated_at is None
        assert state.priority_profile is None

    def test_loop_state_to_dict(self):
        """Convert LoopState to dict"""
        state = LoopState(
            run_id="run-789",
            task_alias="task3",
            status=LoopStatus.running,
            iteration=2,
            max_iterations=4,
            phase=Phase.A,
            current_step="refining",
            current_score=0.8,
            priority_profile="web",
        )

        data = state.to_dict()
        assert data["run_id"] == "run-789"
        assert data["status"] == "running"
        assert data["phase"] == "A"
        assert data["current_score"] == 0.8
        assert data["priority_profile"] == "web"

    def test_loop_state_to_dict_with_nested_objects(self):
        """Convert LoopState with nested evaluation/critique to dict"""
        evaluation = EvaluationResult(
            score=0.9,
            passed=True,
            threshold=0.8,
            phase="A",
            passed_rules=["rule1"],
            failed_rules=[],
            warnings=[],
            evaluated_at="2024-01-01",
        )

        state = LoopState(
            run_id="run-999",
            task_alias="task4",
            status=LoopStatus.completed,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="done",
            evaluation=evaluation,
        )

        data = state.to_dict()
        assert data["evaluation"]["score"] == 0.9
        assert data["evaluation"]["passed"] is True

    def test_loop_state_from_dict(self):
        """Create LoopState from dict"""
        data = {
            "run_id": "run-111",
            "task_alias": "task5",
            "status": "completed",
            "iteration": 3,
            "max_iterations": 4,
            "phase": "B",
            "current_step": "done",
            "current_score": 0.9,
            "last_score": 0.85,
            "evaluation": {
                "score": 0.9,
                "passed": True,
                "threshold": 0.9,
                "phase": "B",
                "passed_rules": [],
                "failed_rules": [],
                "warnings": [],
                "evaluated_at": "2024-01-01",
            },
            "critique": {
                "issues": [],
                "total_failed": 0,
                "addressed": 0,
            },
            "stop": {"reason": "threshold_reached"},
            "started_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T10:10:00",
            "priority_profile": "default",
        }

        state = LoopState.from_dict(data)
        assert state.run_id == "run-111"
        assert state.status == LoopStatus.completed
        assert state.phase == Phase.B
        assert state.current_score == 0.9
        assert state.evaluation is not None
        assert state.critique is not None
        assert state.stop is not None
        assert state.priority_profile == "default"

    def test_loop_state_from_dict_defaults(self):
        """Handle missing optional fields in from_dict"""
        data = {
            "run_id": "run-222",
            "task_alias": "task6",
            "status": "running",
            "iteration": 1,
            "max_iterations": 4,
            "phase": "A",
            "current_step": "starting",
        }

        state = LoopState.from_dict(data)
        assert state.current_score is None
        assert state.evaluation is None
        assert state.critique is None
        assert state.priority_profile is None


class TestLoopEvent:
    """Test LoopEvent dataclass"""

    def test_loop_event_creation(self):
        """Create LoopEvent with all fields"""
        event = LoopEvent(
            timestamp="2024-01-01T12:00:00",
            event_type="evaluation_done",
            iteration=1,
            phase="A",
            details={"score": 0.85, "passed": True},
        )

        assert event.timestamp == "2024-01-01T12:00:00"
        assert event.event_type == "evaluation_done"
        assert event.iteration == 1
        assert event.phase == "A"
        assert event.details == {"score": 0.85, "passed": True}

    def test_loop_event_defaults(self):
        """LoopEvent has correct default optional values"""
        event = LoopEvent(
            timestamp="2024-01-01",
            event_type="loop_started",
        )
        assert event.iteration is None
        assert event.phase is None
        assert event.details is None

    def test_loop_event_to_dict(self):
        """Convert LoopEvent to dict"""
        event = LoopEvent(
            timestamp="2024-01-01T13:00:00",
            event_type="refinement_done",
            iteration=2,
            phase="B",
            details={"improvements": 3},
        )

        data = event.to_dict()
        assert data["timestamp"] == "2024-01-01T13:00:00"
        assert data["event_type"] == "refinement_done"
        assert data["iteration"] == 2
        assert data["phase"] == "B"
        assert data["details"] == {"improvements": 3}

    def test_loop_event_from_dict(self):
        """Create LoopEvent from dict"""
        data = {
            "timestamp": "2024-01-01T14:00:00",
            "event_type": "loop_completed",
            "iteration": 4,
            "phase": "A",
            "details": {"final_score": 0.92},
        }

        event = LoopEvent.from_dict(data)
        assert event.timestamp == "2024-01-01T14:00:00"
        assert event.event_type == "loop_completed"
        assert event.iteration == 4
        assert event.phase == "A"
        assert event.details == {"final_score": 0.92}

    def test_loop_event_from_dict_defaults(self):
        """Handle missing optional fields in from_dict"""
        data = {
            "timestamp": "2024-01-01",
            "event_type": "loop_started",
        }

        event = LoopEvent.from_dict(data)
        assert event.iteration is None
        assert event.phase is None
        assert event.details is None

    def test_loop_event_to_jsonl(self):
        """Convert LoopEvent to JSONL format"""
        event = LoopEvent(
            timestamp="2024-01-01T15:00:00",
            event_type="checkpoint",
            iteration=2,
            phase="A",
        )

        jsonl = event.to_jsonl()
        assert "2024-01-01T15:00:00" in jsonl
        assert "checkpoint" in jsonl
        assert "\"iteration\": 2" in jsonl
        assert "\"phase\": \"A\"" in jsonl


class TestModelIntegration:
    """Integration tests for model interactions"""

    def test_full_template_to_dict_roundtrip(self):
        """Test complete roundtrip: template -> dict -> template"""
        original = CriteriaTemplate(
            name="full-test",
            version=2.0,
            description="Full test template",
            phases={
                "a": PhaseConfig(threshold=0.8, active_levels=["A"]),
                "b": PhaseConfig(threshold=0.9, active_levels=["A", "B"]),
            },
            rules=[
                QualityRule(
                    id="rule1",
                    description="Security rule",
                    severity=RuleSeverity.fail,
                    weight=2,
                    phase=Phase.A,
                    check="auth.*pattern",
                    check_type=RuleCheckType.content,
                    domain_tags=["api", "auth"],
                    category="security",
                ),
                QualityRule(
                    id="rule2",
                    description="Performance rule",
                    severity=RuleSeverity.warn,
                    weight=1,
                    phase=Phase.B,
                    check="slow.*query",
                    check_type=RuleCheckType.executable,
                    domain_tags=["database"],
                    category="performance",
                ),
            ],
            priority_profiles={
                "backend": PriorityProfile(
                    name="backend",
                    multipliers={"api": 2.0, "database": 1.5},
                    description="Backend focused",
                    category_multipliers={"security": 1.5, "performance": 1.3},
                ),
            },
        )

        # Convert to dict
        data = original.to_dict()

        # Convert back
        restored = CriteriaTemplate.from_dict(data)

        # Verify
        assert restored.name == original.name
        assert restored.version == original.version
        assert len(restored.phases) == len(original.phases)
        assert len(restored.rules) == len(original.rules)
        assert len(restored.priority_profiles) == len(original.priority_profiles)

        # Check rule details
        restored_rule = restored.rules[0]
        assert restored_rule.id == "rule1"
        assert restored_rule.category == "security"
        assert restored_rule.domain_tags == ["api", "auth"]

    def test_loop_state_with_full_results(self):
        """Test LoopState with complete evaluation and critique"""
        evaluation = EvaluationResult(
            score=0.88,
            passed=True,
            threshold=0.85,
            phase="B",
            passed_rules=["rule1", "rule2", "rule3"],
            failed_rules=[
                FailedRule(rule_id="rule4", reason="Critical issue", category="security"),
            ],
            warnings=[
                FailedRule(rule_id="rule5", reason="Warning", category="performance"),
            ],
            evaluated_at="2024-01-01T12:00:00",
            priority_profile="backend",
            category_breakdown={"security": 0.95, "performance": 0.82},
            category_scores={"security": {"passed": 8, "failed": 1}},
            severity_counts={"fail": 1, "warn": 1, "info": 0},
        )

        critique = CritiqueResult(
            issues=[
                {"rule_id": "rule4", "reason": "Auth missing", "fix": "Add authentication"},
                {"rule_id": "rule5", "reason": "Slow query", "fix": "Add index"},
            ],
            total_failed=2,
            addressed=1,
            skipped=1,
        )

        state = LoopState(
            run_id="test-run-full",
            task_alias="full-test",
            status=LoopStatus.completed,
            iteration=3,
            max_iterations=4,
            phase=Phase.B,
            current_step="completed",
            current_score=0.88,
            last_score=0.82,
            evaluation=evaluation,
            critique=critique,
            stop={"reason": "threshold_reached", "score": 0.88},
            started_at="2024-01-01T11:00:00",
            updated_at="2024-01-01T12:00:00",
            priority_profile="backend",
        )

        # Convert to dict and back
        state_dict = state.to_dict()
        restored = LoopState.from_dict(state_dict)

        assert restored.run_id == "test-run-full"
        assert restored.current_score == 0.88
        assert restored.evaluation.passed is True
        assert len(restored.evaluation.failed_rules) == 1
        assert restored.evaluation.failed_rules[0].category == "security"
        assert restored.critique.total_failed == 2
        assert restored.priority_profile == "backend"
