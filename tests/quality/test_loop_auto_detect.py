"""
Tests for auto-detection integration in QualityLoop (Exp 133)

Tests that auto_detect_blend_preset() is properly integrated
into QualityLoop.run() for zero-config user experience.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from specify_cli.quality.loop import QualityLoop
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.evaluator import Evaluator
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.critique import Critique
from specify_cli.quality.refiner import Refiner
from specify_cli.quality.state import LoopStateManager


@pytest.fixture
def quality_loop():
    """Create a QualityLoop instance for testing."""
    rule_manager = Mock(spec=RuleManager)
    evaluator = Mock(spec=Evaluator)
    scorer = Mock(spec=Scorer)
    critique = Mock(spec=Critique)
    refiner = Mock(spec=Refiner)
    state_manager = Mock(spec=LoopStateManager)

    # Setup rule manager mocks
    mock_criteria = Mock()
    mock_criteria.phases = {
        "a": Mock(threshold=0.8),
        "b": Mock(threshold=0.9)
    }
    mock_criteria.list_priority_profiles = Mock(return_value=[])

    rule_manager.load_criteria.return_value = mock_criteria
    rule_manager.load_merged_criteria.return_value = mock_criteria

    # Setup evaluator mock
    mock_eval_result = Mock()
    mock_eval_result.score = 0.85
    mock_eval_result.passed = True
    mock_eval_result.failed_rules = []
    evaluator.evaluate.return_value = mock_eval_result

    # Setup scorer mock
    scorer.calculate_score.return_value = 0.85
    scorer.check_passed.return_value = True

    # Setup critique mock
    critique.generate.return_value = {
        "issues": [],
        "suggestions": [],
        "addressed": 0
    }

    # Setup refiner mock
    refiner.apply.return_value = "refined artifact"

    # Setup state manager mocks
    state_manager.save_state = Mock()
    state_manager.save_artifact = Mock()
    state_manager.append_event = Mock()
    state_manager.clear_active_loop = Mock()

    return QualityLoop(
        rule_manager=rule_manager,
        evaluator=evaluator,
        scorer=scorer,
        critique=critique,
        refiner=refiner,
        state_manager=state_manager,
    )


class TestAutoDetectionIntegration:
    """Test auto-detection integration in QualityLoop.run()"""

    @patch('specify_cli.quality.loop.get_registry')
    def test_auto_detect_enabled_uses_detected_preset(self, mock_get_registry, quality_loop):
        """Test that auto_detect=True uses the detected blend preset."""
        # Setup: auto-detect returns full_stack_secure preset
        mock_preset = Mock()
        mock_preset.templates = ["frontend", "backend", "api-spec", "security", "testing"]

        mock_registry = Mock()
        mock_registry.auto_detect_blend_preset.return_value = mock_preset
        mock_get_registry.return_value = mock_registry

        # Run with auto_detect=True (no blend_preset or project_type)
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",  # Should be overridden by auto-detection
            auto_detect=True,
            max_iterations=1,
        )

        # Verify auto-detection was called
        mock_registry.auto_detect_blend_preset.assert_called_once()

        # Verify blend preset templates were used (merged criteria)
        quality_loop.rule_manager.load_merged_criteria.assert_called_once()
        call_args = quality_loop.rule_manager.load_merged_criteria.call_args
        loaded_templates = call_args[0][0] if call_args[0] else ""
        assert "frontend" in loaded_templates
        assert "backend" in loaded_templates
        assert "security" in loaded_templates

    @patch('specify_cli.quality.loop.get_registry')
    def test_auto_detect_disabled_does_not_call_detection(self, mock_get_registry, quality_loop):
        """Test that auto_detect=False (default) does not call auto-detection."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        # Run with auto_detect=False (default)
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            auto_detect=False,
            max_iterations=1,
        )

        # Verify auto-detection was NOT called
        mock_registry.auto_detect_blend_preset.assert_not_called()

        # Verify original criteria_name was used
        quality_loop.rule_manager.load_criteria.assert_called_once_with("backend")

    @patch('specify_cli.quality.loop.get_registry')
    def test_blend_preset_takes_precedence_over_auto_detect(self, mock_get_registry, quality_loop):
        """Test that explicit blend_preset takes precedence over auto_detect."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        # Setup: blend preset exists
        mock_preset = Mock()
        mock_preset.templates = ["frontend", "backend"]
        mock_registry.get_blend_preset.return_value = mock_preset

        # Run with both blend_preset and auto_detect
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            blend_preset="full_stack_secure",
            auto_detect=True,  # Should be ignored
            max_iterations=1,
        )

        # Verify blend_preset was used, not auto-detection
        mock_registry.get_blend_preset.assert_called_once_with("full_stack_secure")
        mock_registry.auto_detect_blend_preset.assert_not_called()

    @patch('specify_cli.quality.loop.get_registry')
    def test_project_type_takes_precedence_over_auto_detect(self, mock_get_registry, quality_loop):
        """Test that explicit project_type takes precedence over auto_detect."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        # Setup: project type has blend preset recommendation
        mock_preset = Mock()
        mock_preset.templates = ["api-spec", "security", "performance"]
        mock_registry.recommend_blend_preset.return_value = mock_preset

        # Run with both project_type and auto_detect
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            project_type="microservice",
            auto_detect=True,  # Should be ignored
            max_iterations=1,
        )

        # Verify project_type was used, not auto-detection
        mock_registry.recommend_blend_preset.assert_called_once_with("microservice")
        mock_registry.auto_detect_blend_preset.assert_not_called()

    @patch('specify_cli.quality.loop.get_registry')
    def test_auto_detect_falls_back_to_criteria_name_on_failure(self, mock_get_registry, quality_loop):
        """Test that when auto-detection fails, falls back to criteria_name."""
        mock_registry = Mock()
        mock_registry.auto_detect_blend_preset.return_value = None  # Detection failed
        mock_get_registry.return_value = mock_registry

        # Run with auto_detect=True but detection fails
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            auto_detect=True,
            max_iterations=1,
        )

        # Verify auto-detection was called
        mock_registry.auto_detect_blend_preset.assert_called_once()

        # Verify fallback to original criteria_name
        quality_loop.rule_manager.load_criteria.assert_called_once_with("backend")

    @patch('specify_cli.quality.loop.get_registry')
    def test_auto_detect_with_project_analysis(self, mock_get_registry, quality_loop):
        """Test that auto_detect passes project_root parameter correctly."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        mock_preset = Mock()
        mock_preset.templates = ["frontend", "backend"]
        mock_registry.auto_detect_blend_preset.return_value = mock_preset

        # Run with auto_detect
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            auto_detect=True,
            max_iterations=1,
        )

        # Verify auto-detection was called with project_root (Path object)
        mock_registry.auto_detect_blend_preset.assert_called_once()
        call_kwargs = mock_registry.auto_detect_blend_preset.call_args[1]
        assert "project_root" in call_kwargs
        # project_root should be a Path object
        assert isinstance(call_kwargs["project_root"], Path)


class TestAutoDetectionPrecedence:
    """Test parameter precedence with auto_detect"""

    @patch('specify_cli.quality.loop.get_registry')
    def test_precedence_order_blend_preset_first(self, mock_get_registry, quality_loop):
        """Test precedence: blend_preset > project_type > auto_detect > criteria_name"""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        mock_preset = Mock()
        mock_preset.templates = ["custom"]
        mock_registry.get_blend_preset.return_value = mock_preset

        # All parameters provided - blend_preset should win
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            blend_preset="custom_preset",
            project_type="web-app",
            auto_detect=True,
            max_iterations=1,
        )

        # Only blend_preset should be used
        mock_registry.get_blend_preset.assert_called_once_with("custom_preset")
        mock_registry.recommend_blend_preset.assert_not_called()
        mock_registry.auto_detect_blend_preset.assert_not_called()

    @patch('specify_cli.quality.loop.get_registry')
    def test_precedence_order_project_type_second(self, mock_get_registry, quality_loop):
        """Test precedence: project_type > auto_detect > criteria_name"""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        mock_preset = Mock()
        mock_preset.templates = ["api-spec", "security"]
        mock_registry.recommend_blend_preset.return_value = mock_preset

        # project_type and auto_detect provided - project_type should win
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            project_type="microservice",
            auto_detect=True,
            max_iterations=1,
        )

        # Only project_type should be used
        mock_registry.recommend_blend_preset.assert_called_once_with("microservice")
        mock_registry.auto_detect_blend_preset.assert_not_called()

    @patch('specify_cli.quality.loop.get_registry')
    def test_precedence_order_auto_detect_third(self, mock_get_registry, quality_loop):
        """Test precedence: auto_detect > criteria_name"""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        mock_preset = Mock()
        mock_preset.templates = ["frontend", "backend"]
        mock_registry.auto_detect_blend_preset.return_value = mock_preset

        # Only auto_detect and criteria_name provided - auto_detect should win
        result = quality_loop.run(
            artifact="test artifact",
            task_alias="test_task",
            criteria_name="backend",
            auto_detect=True,
            max_iterations=1,
        )

        # auto_detect should be used, not criteria_name
        mock_registry.auto_detect_blend_preset.assert_called_once()
        # Should use merged criteria from preset, not single criteria
        quality_loop.rule_manager.load_merged_criteria.assert_called_once()
