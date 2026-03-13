"""
Tests for Template Integration (Exp 127)

Tests the integration between template registry and quality loop,
including recommendations, validation, and expansion.
"""

import pytest
from pathlib import Path

from specify_cli.quality.template_registry import (
    TemplateIntegration,
    get_recommended_templates,
    validate_templates,
    expand_templates,
)


class TestTemplateIntegration:
    """Test template integration functionality"""

    def test_get_recommended_templates_web_app(self):
        """Test getting recommended templates for web app"""
        templates = get_recommended_templates("web-app")
        assert templates is not None
        assert len(templates) > 0
        # Web apps should include frontend and backend
        assert any("frontend" in t or "backend" in t for t in templates)

    def test_get_recommended_templates_microservice(self):
        """Test getting recommended templates for microservice"""
        templates = get_recommended_templates("microservice")
        assert templates is not None
        assert len(templates) > 0
        # Microservices should include backend and security
        assert any("backend" in t or "security" in t for t in templates)

    def test_get_recommended_templates_fallback(self):
        """Test fallback to default templates"""
        # Use a project type that doesn't exist
        templates = get_recommended_templates("non-existent-type")
        # Should fall back to defaults
        assert templates is not None
        assert len(templates) > 0

    def test_project_type_aliases(self):
        """Test project type aliases work correctly"""
        web_templates = get_recommended_templates("web")
        webapp_templates = get_recommended_templates("webapp")
        full_web_templates = get_recommended_templates("web-app")

        # All should return the same templates
        assert web_templates == webapp_templates == full_web_templates

    def test_validate_templates_valid(self):
        """Test validation of valid templates"""
        is_valid, valid_templates, warning = validate_templates(["backend", "security"])
        assert is_valid or len(valid_templates) > 0
        assert warning is None or len(valid_templates) > 0

    def test_validate_templates_invalid(self):
        """Test validation with invalid templates"""
        is_valid, valid_templates, warning = validate_templates(["backend", "non-existent"])
        assert not is_valid
        assert len(valid_templates) < 2
        assert warning is not None
        assert "non-existent" in warning

    def test_expand_templates_with_dependencies(self):
        """Test template expansion with dependencies"""
        expanded = expand_templates(["frontend"], include_dependencies=True)
        # Frontend should auto-include testing
        assert "testing" in expanded

    def test_expand_templates_without_dependencies(self):
        """Test template expansion without dependencies"""
        expanded = expand_templates(["frontend"], include_dependencies=False)
        # Should only include the original template
        assert expanded == ["frontend"]

    def test_expand_templates_multiple(self):
        """Test expanding multiple templates"""
        expanded = expand_templates(["backend", "frontend"], include_dependencies=True)
        # Both should include testing but only once
        assert "backend" in expanded
        assert "frontend" in expanded
        assert "testing" in expanded
        # Check no duplicates
        assert len(expanded) == len(set(expanded))

    def test_suggest_from_codebase_fallback(self):
        """Test codebase suggestion with no indicators"""
        # Use a temporary directory with no indicators
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            suggested = TemplateIntegration.suggest_from_codebase(Path(tmpdir))
            # Should at least include security
            assert "security" in suggested

    def test_template_integration_class_methods(self):
        """Test TemplateIntegration class methods directly"""
        # Test class methods work the same as convenience functions
        templates = TemplateIntegration.get_recommended_templates("ml-service")
        assert templates is not None

        is_valid, valid, warning = TemplateIntegration.validate_template_combination(["backend"])
        assert is_valid or len(valid) > 0

        expanded = TemplateIntegration.expand_templates(["backend"])
        assert "backend" in expanded


def test_integration_with_loop_config():
    """Test integration with LoopConfig"""
    from specify_cli.quality.loop_config import (
        LoopConfig,
        resolve_criteria_from_config,
    )

    # Test config with project_type
    config = LoopConfig(
        name="test-smart-web",
        description="Test config",
        project_type="web-app",
        criteria=[],
    )

    criteria = resolve_criteria_from_config(config)
    assert criteria is not None
    assert len(criteria) > 0

    # Test config with explicit criteria
    config2 = LoopConfig(
        name="test-explicit",
        description="Test config",
        criteria=["backend", "security"],
    )

    criteria2 = resolve_criteria_from_config(config2)
    assert "backend" in criteria2
    assert "security" in criteria2


def test_get_available_project_types():
    """Test getting available project types"""
    from specify_cli.quality.loop_config import get_available_project_types

    types = get_available_project_types()
    assert types is not None
    assert len(types) > 0
    assert "web-app" in types
    assert "microservice" in types
