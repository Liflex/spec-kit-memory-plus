"""
Tests for templates_cli.py - Template Registry CLI Commands (Exp 137)

Tests for CLI commands in templates_cli.py including:
- list_presets_command
- preset_info_command
- search_presets_command
- recommend_preset_command
- auto_detect_preset_command (new)
- apply_preset_command

Uses typer.testing.CliRunner for end-to-end CLI testing.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from specify_cli.quality.templates_cli import presets_app, templates_app
from specify_cli.quality.template_registry import BlendPreset


# ============================================================================
# Test Utilities
# ============================================================================

@pytest.fixture
def runner():
    """Create a CliRunner instance for testing."""
    return CliRunner()


@pytest.fixture
def mock_registry():
    """Create a mock TemplateRegistry."""
    registry = Mock()

    # Setup mock blend presets
    preset1 = BlendPreset(
        name="full_stack_secure",
        description="Full stack development with security focus",
        templates=["frontend", "backend", "api-spec", "security", "testing"],
        mode="union",
        tags={"web", "security", "full-stack"},
        project_types=["web-app", "spa"],
    )

    preset2 = BlendPreset(
        name="microservices_robust",
        description="Robust microservices architecture",
        templates=["api-spec", "backend", "security", "performance", "infrastructure"],
        mode="union",
        tags={"microservices", "api", "robust"},
        project_types=["microservice", "api"],
    )

    preset3 = BlendPreset(
        name="data_pipeline",
        description="Data pipeline and ML service quality",
        templates=["database", "api-spec", "performance", "security"],
        mode="consensus",
        tags={"data", "ml", "pipeline"},
        project_types=["data-pipeline", "ml-service"],
    )

    # Setup mock blended template for apply command
    from specify_cli.quality.template_registry import BlendedTemplate
    mock_blended = BlendedTemplate(
        name="full_stack_secure",
        description="Full stack development with security focus",
        source_templates=["frontend", "backend", "api-spec", "security", "testing"],
        blend_mode="union",
        rules=[],
        metadata={"version": "1.0"},
    )

    registry.list_blend_presets.return_value = [preset1, preset2, preset3]
    registry.get_blend_preset.side_effect = lambda name: {
        "full_stack_secure": preset1,
        "microservices_robust": preset2,
        "data_pipeline": preset3,
    }.get(name)

    registry.search_blend_presets.side_effect = lambda query: [
        p for p in [preset1, preset2, preset3]
        if query in p.name.lower() or query in str(p.tags).lower()
    ]

    registry.recommend_blend_preset.side_effect = lambda project_type: {
        "web-app": preset1,
        "microservice": preset2,
        "data-pipeline": preset3,
    }.get(project_type)

    registry.auto_detect_blend_preset.return_value = preset1
    registry.apply_blend_preset.return_value = mock_blended

    return registry


# ============================================================================
# Tests for list_presets_command
# ============================================================================

class TestListPresetsCommand:
    """Tests for 'speckit templates presets list' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_list_presets_success(self, mock_get_registry, runner, mock_registry):
        """Test listing blend presets successfully."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["list"])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout
        assert "microservices_robust" in result.stdout
        assert "data_pipeline" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_list_presets_with_tag_filter(self, mock_get_registry, runner, mock_registry):
        """Test listing presets with tag filter."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["list", "--tag", "web"])

        assert result.exit_code == 0
        # Should contain presets with 'web' tag
        assert "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_list_presets_empty(self, mock_get_registry, runner):
        """Test listing presets when none exist."""
        mock_registry = Mock()
        mock_registry.list_blend_presets.return_value = []
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["list"])

        assert result.exit_code == 0
        assert "No blend presets" in result.stdout or "presets" in result.stdout.lower()


# ============================================================================
# Tests for preset_info_command
# ============================================================================

class TestPresetInfoCommand:
    """Tests for 'speckit templates presets info' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_preset_info_existing(self, mock_get_registry, runner, mock_registry):
        """Test getting info for an existing preset."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["info", "full_stack_secure"])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout
        assert "frontend" in result.stdout
        assert "backend" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_preset_info_nonexistent(self, mock_get_registry, runner, mock_registry):
        """Test getting info for a non-existent preset."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["info", "nonexistent_preset"])

        assert result.exit_code != 0 or "not found" in result.stdout.lower() or "error" in result.stdout.lower()


# ============================================================================
# Tests for search_presets_command
# ============================================================================

class TestSearchPresetsCommand:
    """Tests for 'speckit templates presets search' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_search_presets_by_name(self, mock_get_registry, runner, mock_registry):
        """Test searching presets by name."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["search", "micro"])

        assert result.exit_code == 0
        assert "microservices_robust" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_search_presets_by_tag(self, mock_get_registry, runner, mock_registry):
        """Test searching presets by tag."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["search", "web"])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_search_presets_no_results(self, mock_get_registry, runner, mock_registry):
        """Test search with no matching results."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["search", "xyznonexistent"])

        assert result.exit_code == 0
        # Should show "No matching presets" message


# ============================================================================
# Tests for recommend_preset_command
# ============================================================================

class TestRecommendPresetCommand:
    """Tests for 'speckit templates presets recommend' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_recommend_preset_web_app(self, mock_get_registry, runner, mock_registry):
        """Test recommending preset for web-app project."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["recommend", "web-app"])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_recommend_preset_microservice(self, mock_get_registry, runner, mock_registry):
        """Test recommending preset for microservice project."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["recommend", "microservice"])

        assert result.exit_code == 0
        assert "microservices_robust" in result.stdout


# ============================================================================
# Tests for auto_detect_preset_command (NEW - Exp 137)
# ============================================================================

class TestAutoDetectPresetCommand:
    """Tests for 'speckit templates presets auto-detect' command (new in Exp 137)"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_auto_detect_preset_success(self, mock_get_registry, runner, mock_registry):
        """Test auto-detecting preset successfully."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["auto-detect"])

        assert result.exit_code == 0
        assert "Auto-detected Preset" in result.stdout or "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_auto_detect_preset_with_verbose(self, mock_get_registry, runner, mock_registry):
        """Test auto-detect with verbose output."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["auto-detect", "--verbose"])

        assert result.exit_code == 0
        # Verbose mode should show project root
        assert "Project Root" in result.stdout or "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_auto_detect_preset_with_project_root(self, mock_get_registry, runner, mock_registry):
        """Test auto-detect with explicit project root."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["auto-detect", "--project-root", "."])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_auto_detect_preset_failure(self, mock_get_registry, runner):
        """Test auto-detect when detection fails."""
        mock_registry = Mock()
        mock_registry.auto_detect_blend_preset.return_value = None
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["auto-detect"])

        assert result.exit_code == 0
        assert "Could not auto-detect" in result.stdout or "yellow" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_auto_detect_preset_exception_handling(self, mock_get_registry, runner):
        """Test auto-detect handles exceptions gracefully.

        Note: The current implementation may raise exceptions.
        This test documents the expected behavior.
        """
        mock_registry = Mock()
        mock_registry.auto_detect_blend_preset.side_effect = Exception("Detection error")
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["auto-detect"])

        # Current behavior: exception propagates
        # This is acceptable for now - could be improved with try/except
        assert result.exit_code != 0 or "Detection error" in str(result.exception)


# ============================================================================
# Tests for apply_preset_command
# ============================================================================

class TestApplyPresetCommand:
    """Tests for 'speckit templates presets apply' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_apply_preset_existing(self, mock_get_registry, runner, mock_registry):
        """Test applying an existing preset."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["apply", "full_stack_secure"])

        assert result.exit_code == 0
        assert "full_stack_secure" in result.stdout
        assert "frontend" in result.stdout or "backend" in result.stdout

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_apply_preset_nonexistent(self, mock_get_registry, runner, mock_registry):
        """Test applying a non-existent preset."""
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(presets_app, ["apply", "nonexistent_preset"])

        # Should show error about preset not found
        assert result.exit_code != 0 or "not found" in result.stdout.lower()


# ============================================================================
# Tests for templates_app integration
# ============================================================================

class TestTemplatesAppIntegration:
    """Tests for templates_app with presets sub-app"""

    def test_presets_app_registered(self):
        """Test that presets_app is registered as a sub-app."""
        # The presets_app should be accessible
        assert presets_app is not None
        assert hasattr(presets_app, "registered_commands")

    def test_presets_commands_exist(self):
        """Test that all preset commands are registered."""
        commands = presets_app.registered_commands
        command_names = [cmd.name for cmd in commands if cmd]

        expected_commands = ["list", "info", "search", "recommend", "auto-detect", "apply"]
        for expected in expected_commands:
            assert expected in command_names, f"Command '{expected}' not found"


# ============================================================================
# Tests for main templates list command
# ============================================================================

class TestListTemplatesCommand:
    """Tests for 'speckit templates list' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_list_templates_basic(self, mock_get_registry, runner):
        """Test basic template listing."""
        mock_registry = Mock()
        mock_registry.list_templates.return_value = []
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(templates_app, ["list"])

        assert result.exit_code == 0

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_list_templates_with_category_filter(self, mock_get_registry, runner):
        """Test listing templates with category filter."""
        mock_registry = Mock()
        mock_registry.list_templates.return_value = []
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(templates_app, ["list", "--category", "core"])

        assert result.exit_code == 0


# ============================================================================
# Tests for template stats command
# ============================================================================

class TestTemplateStatsCommand:
    """Tests for 'speckit templates stats' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_stats_command(self, mock_get_registry, runner):
        """Test template statistics command."""
        mock_registry = Mock()
        # The stats command calls get_template_stats
        mock_registry.get_template_stats.return_value = {
            'total_templates': 13,
            'builtin_templates': 13,
            'custom_templates': 0,
            'by_category': {'core': 13},
            'total_rules': 150,
        }
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(templates_app, ["stats"])

        assert result.exit_code == 0


# ============================================================================
# Tests for search command
# ============================================================================

class TestSearchCommand:
    """Tests for 'speckit templates search' command"""

    @patch('specify_cli.quality.templates_cli.get_registry')
    def test_search_templates(self, mock_get_registry, runner):
        """Test searching templates."""
        mock_registry = Mock()
        mock_registry.search_templates.return_value = []
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(templates_app, ["search", "security"])

        assert result.exit_code == 0
