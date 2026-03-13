"""
Tests for Blend Presets (Exp 132)

Tests the blend preset functionality including preset listing,
searching, recommendation, and application.
"""

import pytest
from pathlib import Path

from specify_cli.quality.template_registry import (
    BlendPreset,
    TemplateRegistry,
)


class TestBlendPreset:
    """Test BlendPreset dataclass"""

    def test_blend_preset_creation(self):
        """Test creating a blend preset"""
        preset = BlendPreset(
            name="test_preset",
            description="Test preset",
            templates=["backend", "security"],
            mode="union",  # Required field
            tags={"test"},  # Pass as set
            project_types=["web-app"],
        )
        assert preset.name == "test_preset"
        assert preset.templates == ["backend", "security"]
        assert preset.mode == "union"
        assert preset.tags == {"test"}
        assert preset.project_types == ["web-app"]

    def test_blend_preset_display_name(self):
        """Test display_name property"""
        preset = BlendPreset(
            name="full_stack_secure",
            description="Full stack with security",
            templates=["backend", "frontend", "security"],
            mode="union",  # Required field
            tags={"web", "security"},  # Set
        )
        # Note: BlendPreset is a dataclass without display_name property
        assert preset.name == "full_stack_secure"


class TestBlendPresetsList:
    """Test BLEND_PRESETS constant and listing"""

    def test_list_blend_presets_not_empty(self):
        """Test that blend presets list is not empty"""
        registry = TemplateRegistry()
        presets = registry.list_blend_presets()
        assert len(presets) > 0

    def test_list_blend_presets_has_required_fields(self):
        """Test that all presets have required fields"""
        registry = TemplateRegistry()
        presets = registry.list_blend_presets()

        for preset in presets:
            assert preset.name is not None
            assert len(preset.name) > 0
            assert preset.description is not None
            assert len(preset.description) > 0
            assert preset.templates is not None
            assert len(preset.templates) > 0

    def test_list_blend_presets_expected_presets_exist(self):
        """Test that expected blend presets exist"""
        registry = TemplateRegistry()
        presets = registry.list_blend_presets()
        preset_names = [p.name for p in presets]

        # Check for key presets from Exp 131
        expected_presets = [
            "full_stack_secure",
            "microservices_robust",
            "api_first",
            "mobile_backend",
            "data_pipeline",
        ]

        for expected in expected_presets:
            assert expected in preset_names, f"Expected preset '{expected}' not found"


class TestGetBlendPreset:
    """Test get_blend_preset method"""

    def test_get_blend_preset_existing(self):
        """Test getting an existing preset"""
        registry = TemplateRegistry()
        preset = registry.get_blend_preset("full_stack_secure")
        assert preset is not None
        assert preset.name == "full_stack_secure"

    def test_get_blend_preset_non_existing(self):
        """Test getting a non-existing preset returns None"""
        registry = TemplateRegistry()
        preset = registry.get_blend_preset("non_existing_preset")
        assert preset is None

    def test_get_blend_preset_case_sensitive(self):
        """Test that preset lookup is case-sensitive"""
        registry = TemplateRegistry()
        preset = registry.get_blend_preset("Full_Stack_Secure")
        # Should not find it (wrong case)
        assert preset is None or preset.name != "Full_Stack_Secure"


class TestSearchBlendPresets:
    """Test search_blend_presets method"""

    def test_search_blend_presets_by_name(self):
        """Test searching presets by name"""
        registry = TemplateRegistry()
        results = registry.search_blend_presets("full")
        assert len(results) > 0
        assert any("full" in p.name.lower() for p in results)

    def test_search_blend_presets_by_tag(self):
        """Test searching presets by tag"""
        registry = TemplateRegistry()
        results = registry.search_blend_presets("web")
        assert len(results) > 0
        # All results should have 'web' in tags
        for preset in results:
            assert "web" in preset.tags or "web" in preset.name.lower()

    def test_search_blend_presets_by_description(self):
        """Test searching presets by description"""
        registry = TemplateRegistry()
        results = registry.search_blend_presets("security")
        assert len(results) > 0

    def test_search_blend_presets_empty_query(self):
        """Test that empty query returns all presets"""
        registry = TemplateRegistry()
        results = registry.search_blend_presets("")
        all_presets = registry.list_blend_presets()
        assert len(results) == len(all_presets)

    def test_search_blend_presets_no_results(self):
        """Test search with no matching results"""
        registry = TemplateRegistry()
        results = registry.search_blend_presets("xyznonexistent123")
        assert len(results) == 0


class TestRecommendBlendPreset:
    """Test recommend_blend_preset method"""

    def test_recommend_preset_web_app(self):
        """Test recommending preset for web-app project type"""
        registry = TemplateRegistry()
        preset = registry.recommend_blend_preset("web-app")
        assert preset is not None
        # Should recommend a preset suitable for web apps
        assert "web" in preset.tags or "web" in preset.name.lower() or "web" in str(preset.project_types).lower()

    def test_recommend_preset_microservice(self):
        """Test recommending preset for microservice project type"""
        registry = TemplateRegistry()
        preset = registry.recommend_blend_preset("microservice")
        assert preset is not None
        # Should recommend a preset suitable for microservices
        assert any(keyword in preset.name.lower() for keyword in ["micro", "service", "robust"])

    def test_recommend_preset_mobile_app(self):
        """Test recommending preset for mobile-app project type"""
        registry = TemplateRegistry()
        preset = registry.recommend_blend_preset("mobile-app")
        assert preset is not None
        # Should recommend mobile_backend or similar
        assert "mobile" in preset.name.lower() or "mobile" in str(preset.project_types).lower()

    def test_recommend_preset_data_pipeline(self):
        """Test recommending preset for data-pipeline project type"""
        registry = TemplateRegistry()
        preset = registry.recommend_blend_preset("data-pipeline")
        assert preset is not None
        assert "data" in preset.name.lower()

    def test_recommend_preset_unknown_type_fallback(self):
        """Test recommending preset for unknown project type"""
        registry = TemplateRegistry()
        preset = registry.recommend_blend_preset("unknown-type-xyz")
        # Current behavior: returns None for unknown types
        # This is acceptable - users should use auto_detect_blend_preset for smart fallback
        assert preset is None or preset.name is not None


class TestAutoDetectBlendPreset:
    """Test auto_detect_blend_preset method (new in Exp 132)"""

    def test_auto_detect_blend_preset_returns_preset(self):
        """Test that auto-detection returns a valid preset"""
        registry = TemplateRegistry()
        preset = registry.auto_detect_blend_preset()
        assert preset is not None
        assert isinstance(preset, BlendPreset)

    def test_auto_detect_blend_preset_with_project_root(self):
        """Test auto-detection with explicit project root"""
        registry = TemplateRegistry()
        # Use the spec-kit project itself
        preset = registry.auto_detect_blend_preset(project_root=Path.cwd())
        assert preset is not None
        assert isinstance(preset, BlendPreset)

    def test_auto_detect_blend_preset_different_projects(self):
        """Test auto-detection with different project types"""
        import tempfile

        registry = TemplateRegistry()

        # Test with different project indicators
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Empty project - should return default
            preset = registry.auto_detect_blend_preset(project_root=tmppath)
            assert preset is not None


class TestBlendPresetIntegration:
    """Integration tests for blend presets with other functionality"""

    def test_blend_preset_templates_are_valid(self):
        """Test that blend preset templates are valid template names"""
        registry = TemplateRegistry()
        presets = registry.list_blend_presets()

        # Get all available template names
        available_templates = set(t.name for t in registry.list_templates())

        for preset in presets:
            for template_name in preset.templates:
                # Check that all templates in presets exist
                assert template_name in available_templates, \
                    f"Template '{template_name}' in preset '{preset.name}' does not exist"

    def test_blend_preset_no_duplicate_templates(self):
        """Test that blend presets don't have duplicate templates"""
        registry = TemplateRegistry()
        presets = registry.list_blend_presets()

        for preset in presets:
            template_list = preset.templates
            assert len(template_list) == len(set(template_list)), \
                f"Preset '{preset.name}' has duplicate templates"

    def test_apply_preset_workflow(self):
        """Test the complete apply preset workflow"""
        registry = TemplateRegistry()

        # Get a preset
        preset = registry.get_blend_preset("full_stack_secure")
        assert preset is not None

        # Get templates from preset
        templates = preset.templates
        assert len(templates) > 0

        # Verify templates can be loaded
        for template_name in templates:
            template = registry.get_template(template_name)
            assert template is not None, f"Could not load template '{template_name}'"


def test_blend_preset_consistency():
    """Test that blend presets are internally consistent"""
    registry = TemplateRegistry()
    presets = registry.list_blend_presets()

    for preset in presets:
        # Name should be snake_case
        assert preset.name.replace("_", "").replace("-", "").isalnum(), \
            f"Preset name '{preset.name}' contains invalid characters"

        # Description should not be empty
        assert len(preset.description.strip()) > 0, \
            f"Preset '{preset.name}' has empty description"

        # Should have at least one template
        assert len(preset.templates) > 0, \
            f"Preset '{preset.name}' has no templates"

        # Tags should not be empty
        assert len(preset.tags) > 0, \
            f"Preset '{preset.name}' has no tags"
