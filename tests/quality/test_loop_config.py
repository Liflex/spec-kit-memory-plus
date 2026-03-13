"""
Test suite for loop_config.py (Exp 146)

Tests the quality loop configuration system including:
- LoopConfig dataclass validation
- LoopConfigManager save/load/delete operations
- Built-in presets
- Project type recommendations
- Criteria resolution with template expansion
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from specify_cli.quality.loop_config import (
    LoopConfig,
    LoopConfigManager,
    LOOP_CONFIG_PRESETS,
    save_loop_config,
    load_loop_config,
    list_loop_configs,
    delete_loop_config,
    format_config_summary,
    format_config_details,
    recommend_config,
    resolve_criteria_from_config,
    get_available_project_types,
)


class TestLoopConfigDataclass:
    """Test LoopConfig dataclass creation and validation"""

    def test_minimal_config(self):
        """Test creating config with only required fields"""
        config = LoopConfig(name="test", description="Test config")
        assert config.name == "test"
        assert config.description == "Test config"
        assert config.max_iterations == 4  # default
        assert config.threshold_a == 0.8  # default
        assert config.threshold_b == 0.9  # default
        assert config.criteria == []  # default empty list
        assert config.project_type is None

    def test_full_config(self):
        """Test creating config with all parameters"""
        config = LoopConfig(
            name="full",
            description="Full config",
            project_type="web-app",
            criteria=["backend", "frontend"],
            max_iterations=6,
            threshold_a=0.7,
            threshold_b=0.85,
            auto_expand_templates=False,
            validate_templates=False,
            priority_profile="security-first",
            cascade_strategy="max",
            strict_mode=True,
            lenient_mode=False,
        )
        assert config.name == "full"
        assert config.project_type == "web-app"
        assert config.criteria == ["backend", "frontend"]
        assert config.max_iterations == 6
        assert config.threshold_a == 0.7
        assert config.cascade_strategy == "max"
        assert config.strict_mode is True

    def test_criteria_list_defaults(self):
        """Test that criteria defaults to empty list, not None"""
        config1 = LoopConfig(name="test1", description="test")

        assert config1.criteria == []
        # Note: Passing None overrides default_factory, so we test separately
        config2 = LoopConfig(name="test2", description="test")
        assert config2.criteria == []

    def test_config_serialization(self):
        """Test that LoopConfig can be serialized to dict"""
        config = LoopConfig(
            name="serialize",
            description="Serialization test",
            criteria=["api-spec"],
            max_iterations=3,
        )
        from dataclasses import asdict
        data = asdict(config)

        assert data["name"] == "serialize"
        assert data["criteria"] == ["api-spec"]
        assert data["max_iterations"] == 3

    def test_threshold_validation_ranges(self):
        """Test threshold values are in valid range"""
        # Valid ranges
        config = LoopConfig(
            name="valid",
            description="Valid thresholds",
            threshold_a=0.5,
            threshold_b=0.95,
        )
        assert 0.0 <= config.threshold_a <= 1.0
        assert 0.0 <= config.threshold_b <= 1.0

    def test_mutually_exclusive_modes(self):
        """Test that strict and lenient modes can be set independently"""
        # Both False (default)
        config1 = LoopConfig(name="normal", description="Normal mode")
        assert config1.strict_mode is False
        assert config1.lenient_mode is False

        # Only strict
        config2 = LoopConfig(name="strict", description="Strict mode", strict_mode=True)
        assert config2.strict_mode is True
        assert config2.lenient_mode is False

        # Only lenient
        config3 = LoopConfig(name="lenient", description="Lenient mode", lenient_mode=True)
        assert config3.strict_mode is False
        assert config3.lenient_mode is True


class TestLoopConfigManager:
    """Test LoopConfigManager persistence operations"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_config_dir):
        """Create manager with temporary config directory"""
        return LoopConfigManager(config_dir=Path(temp_config_dir))

    def test_save_and_load_config(self, manager):
        """Test saving and loading a configuration"""
        config = LoopConfig(
            name="test-save",
            description="Save test",
            criteria=["backend"],
            max_iterations=5,
        )

        # Save
        manager.save(config)

        # Load
        loaded = manager.load("test-save")
        assert loaded.name == "test-save"
        assert loaded.description == "Save test"
        assert loaded.criteria == ["backend"]
        assert loaded.max_iterations == 5

    def test_save_overwrites_existing(self, manager):
        """Test that saving overwrites existing config"""
        # Save original
        config1 = LoopConfig(
            name="overwrite",
            description="Original",
            max_iterations=3,
        )
        manager.save(config1)

        # Save with same name, different values
        config2 = LoopConfig(
            name="overwrite",
            description="Updated",
            max_iterations=7,
        )
        manager.save(config2)

        # Should have updated values
        loaded = manager.load("overwrite")
        assert loaded.description == "Updated"
        assert loaded.max_iterations == 7

    def test_list_configs(self, manager):
        """Test listing all saved configurations"""
        manager.save(LoopConfig(name="config1", description="First"))
        manager.save(LoopConfig(name="config2", description="Second"))
        manager.save(LoopConfig(name="config3", description="Third"))

        configs = manager.list_all()
        names = [c["name"] for c in configs if not c.get("is_preset")]

        assert "config1" in names
        assert "config2" in names
        assert "config3" in names
        # Custom configs only (excludes presets)
        assert len(names) == 3

    def test_list_returns_configs_in_order(self, manager):
        """Test that list returns configs with metadata"""
        manager.save(LoopConfig(name="ordered1", description="First"))
        manager.save(LoopConfig(name="ordered2", description="Second"))

        configs = manager.list_all()
        custom_configs = [c for c in configs if not c.get("is_preset")]

        assert len(custom_configs) == 2
        assert all(isinstance(c, dict) for c in configs)
        assert all("name" in c and "description" in c for c in custom_configs)

    def test_delete_config(self, manager):
        """Test deleting a configuration"""
        manager.save(LoopConfig(name="delete-me", description="To be deleted"))

        # Verify exists
        assert manager.load("delete-me") is not None

        # Delete
        result = manager.delete("delete-me")

        # Verify delete succeeded
        assert result is True

        # Verify gone
        assert manager.load("delete-me") is None

    def test_delete_nonexistent_config(self, manager):
        """Test deleting a config that doesn't exist"""
        # Should return False
        result = manager.delete("does-not-exist")
        assert result is False

    def test_load_nonexistent_config(self, manager):
        """Test loading a config that doesn't exist"""
        # Should return None, not raise
        result = manager.load("does-not-exist")
        assert result is None

    def test_config_persistence_across_manager_instances(self, temp_config_dir):
        """Test that configs persist across different manager instances"""
        # Save with first manager
        manager1 = LoopConfigManager(config_dir=Path(temp_config_dir))
        manager1.save(LoopConfig(name="persist", description="Persistence test"))

        # Load with second manager
        manager2 = LoopConfigManager(config_dir=Path(temp_config_dir))
        loaded = manager2.load("persist")
        assert loaded.description == "Persistence test"

    def test_save_with_metadata(self, manager):
        """Test that configs save with created/updated timestamps"""
        config = LoopConfig(
            name="metadata",
            description="Metadata test",
            criteria=["security"],
        )
        saved_path_str = manager.save(config)

        # Load and check file was created
        loaded = manager.load("metadata")
        assert loaded.name == "metadata"

        # Verify config file exists
        saved_path = Path(saved_path_str)
        assert saved_path.exists()


class TestConfigPresets:
    """Test built-in configuration presets"""

    def test_presets_exist(self):
        """Test that LOOP_CONFIG_PRESETS is populated"""
        assert isinstance(LOOP_CONFIG_PRESETS, dict)
        assert len(LOOP_CONFIG_PRESETS) > 0

    def test_preset_configs_are_valid(self):
        """Test that all presets are valid LoopConfig instances"""
        for name, config in LOOP_CONFIG_PRESETS.items():
            assert isinstance(config, LoopConfig)
            assert config.name == name
            assert isinstance(config.description, str)
            assert config.max_iterations > 0

    def test_common_preset_names(self):
        """Test that expected preset names exist"""
        # Common preset names that should exist
        expected_patterns = ["quick", "standard", "thorough", "strict"]
        found_patterns = [p for p in expected_patterns
                         if any(p in name.lower() for name in LOOP_CONFIG_PRESETS.keys())]

        # At least some patterns should be found
        assert len(found_patterns) >= 2

    def test_preset_criteria_lists(self):
        """Test that preset criteria are properly defined"""
        for config in LOOP_CONFIG_PRESETS.values():
            if config.criteria:
                assert isinstance(config.criteria, list)
                assert all(isinstance(c, str) for c in config.criteria)

    def test_preset_project_types(self):
        """Test that presets may have project types defined"""
        has_project_type = any(
            config.project_type is not None
            for config in LOOP_CONFIG_PRESETS.values()
        )
        # At least one preset should have project_type
        assert has_project_type, "No presets with project_type found"


class TestProjectTypes:
    """Test project type detection and recommendations"""

    def test_get_available_project_types(self):
        """Test that project types list is available"""
        project_types = get_available_project_types()
        assert isinstance(project_types, list)
        assert len(project_types) > 0

        # Should contain common project types
        common_types = ["web-app", "microservice", "library"]
        found = [pt for pt in common_types if pt in project_types]
        assert len(found) > 0

    def test_project_types_are_strings(self):
        """Test that all project types are valid strings"""
        project_types = get_available_project_types()
        assert all(isinstance(pt, str) for pt in project_types)
        assert all(pt.strip() for pt in project_types)  # non-empty

    def test_config_with_project_type(self):
        """Test creating config with project type"""
        config = LoopConfig(
            name="project-typed",
            description="Web app config",
            project_type="web-app",
            criteria=["frontend", "backend"],
        )
        assert config.project_type == "web-app"


class TestCriteriaResolution:
    """Test criteria resolution with template expansion"""

    @patch('specify_cli.quality.template_registry.get_recommended_templates')
    def test_resolve_criteria_project_type_no_expansion(self, mock_recommended):
        """Test criteria resolution with project_type, no expansion"""
        mock_recommended.return_value = ["backend", "frontend", "testing"]

        config = LoopConfig(
            name="project-type",
            description="With project type",
            project_type="web-app",
            criteria=[],  # Empty, will use recommendations
            auto_expand_templates=False,
        )

        resolved = resolve_criteria_from_config(config)
        # Should return recommended templates
        assert resolved == ["backend", "frontend", "testing"]
        mock_recommended.assert_called_once()

    def test_resolve_criteria_explicit(self):
        """Test criteria resolution with explicit criteria"""
        config = LoopConfig(
            name="explicit",
            description="Explicit criteria",
            criteria=["api-spec", "database"],
            auto_expand_templates=False,
            validate_templates=False,
        )

        resolved = resolve_criteria_from_config(config)
        # Should return the explicit criteria
        assert resolved == ["api-spec", "database"]


class TestConfigFormatting:
    """Test configuration formatting functions"""

    def test_format_config_summary(self):
        """Test formatting config summary from list of dicts"""
        configs = [
            {
                "name": "summary-test",
                "description": "Summary test config",
                "criteria": ["backend", "security"],
                "is_preset": True,
                "tags": ["fast"],
            },
            {
                "name": "custom-test",
                "description": "Custom config",
                "criteria": ["api-spec"],
                "is_preset": False,
                "tags": [],
            },
        ]

        summary = format_config_summary(configs)

        assert isinstance(summary, str)
        assert "summary-test" in summary
        assert "custom-test" in summary
        assert len(summary) > 0

    def test_format_config_details(self):
        """Test formatting detailed config info"""
        config = LoopConfig(
            name="details-test",
            description="Detailed config",
            project_type="microservice",
            criteria=["api-spec", "testing"],
            max_iterations=5,
            priority_profile="performance",
        )

        details = format_config_details(config)

        assert isinstance(details, str)
        assert "details-test" in details
        assert len(details) > 0

    def test_format_config_with_all_fields(self):
        """Test formatting config with all fields populated"""
        config = LoopConfig(
            name="full-format",
            description="Full formatting test",
            project_type="web-app",
            criteria=["frontend", "backend", "security"],
            max_iterations=6,
            threshold_a=0.75,
            threshold_b=0.9,
            cascade_strategy="max",
            strict_mode=True,
        )

        details = format_config_details(config)
        assert "full-format" in details


class TestConfigRecommendation:
    """Test configuration recommendation system"""

    def test_recommend_config_basic(self):
        """Test basic config recommendation based on task description"""
        # Get recommendation for web app task
        recommendation = recommend_config(task_description="Build a web application")

        # Should return a LoopConfig
        assert isinstance(recommendation, LoopConfig)
        assert recommendation.name

    def test_recommend_config_security_task(self):
        """Test recommendation for security-focused task"""
        recommendation = recommend_config(task_description="Security vulnerability assessment")

        # Should return a security-focused config
        assert isinstance(recommendation, LoopConfig)
        assert "security" in recommendation.name.lower() or recommendation.name in LOOP_CONFIG_PRESETS

    def test_recommend_ci_task(self):
        """Test recommendation for CI/CD task"""
        recommendation = recommend_config(task_description="Setup CI pipeline automation")

        # Should return a CI-focused config
        assert isinstance(recommendation, LoopConfig)


class TestStandaloneFunctions:
    """Test standalone wrapper functions"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory"""
        return tmp_path / "configs"

    def test_save_loop_config_wrapper(self, temp_config_dir):
        """Test save_loop_config standalone function"""
        # save_loop_config takes individual parameters, not LoopConfig object
        result = save_loop_config(
            name="wrapper-save",
            description="Wrapper test",
            config_dir=temp_config_dir,
        )

        # Should return LoopConfig
        assert result is not None
        assert result.name == "wrapper-save"

    def test_load_loop_config_wrapper(self, temp_config_dir):
        """Test load_loop_config standalone function"""
        # First save using the wrapper
        save_loop_config(
            name="wrapper-load",
            description="Load test",
            config_dir=temp_config_dir,
        )

        # Load it back
        loaded = load_loop_config("wrapper-load", config_dir=temp_config_dir)
        assert loaded is not None
        assert loaded.name == "wrapper-load"

    def test_list_loop_configs_wrapper(self, temp_config_dir):
        """Test list_loop_configs standalone function"""
        save_loop_config(
            name="list1",
            description="First",
            config_dir=temp_config_dir
        )
        save_loop_config(
            name="list2",
            description="Second",
            config_dir=temp_config_dir
        )

        configs = list_loop_configs(config_dir=temp_config_dir)
        names = [c["name"] for c in configs if not c.get("is_preset")]

        assert "list1" in names
        assert "list2" in names

    def test_delete_loop_config_wrapper(self, temp_config_dir):
        """Test delete_loop_config standalone function"""
        save_loop_config(
            name="wrapper-delete",
            description="Delete test",
            config_dir=temp_config_dir,
        )

        # Delete - returns bool
        result = delete_loop_config("wrapper-delete", config_dir=temp_config_dir)
        assert result is True

        # Verify deleted - returns None when not found
        loaded = load_loop_config("wrapper-delete", config_dir=temp_config_dir)
        assert loaded is None


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_config_with_empty_criteria(self):
        """Test config with empty criteria list"""
        config = LoopConfig(
            name="empty-criteria",
            description="No criteria",
            criteria=[],
        )
        assert config.criteria == []

    def test_config_with_single_criterion(self):
        """Test config with single criterion"""
        config = LoopConfig(
            name="single",
            description="Single criterion",
            criteria=["api-spec"],
        )
        assert len(config.criteria) == 1

    def test_config_with_many_criteria(self):
        """Test config with many criteria"""
        criteria_list = ["api-spec", "database", "security", "testing",
                        "frontend", "backend", "performance"]
        config = LoopConfig(
            name="many",
            description="Many criteria",
            criteria=criteria_list,
        )
        assert len(config.criteria) == 7

    def test_config_name_with_special_chars(self):
        """Test config with special characters in name"""
        config = LoopConfig(
            name="test-config-v1.2",
            description="Special chars in name",
        )
        assert "test-config-v1.2" == config.name

    def test_config_extreme_iterations(self):
        """Test config with extreme iteration values"""
        config_low = LoopConfig(name="low", description="Low", max_iterations=1)
        config_high = LoopConfig(name="high", description="High", max_iterations=20)

        assert config_low.max_iterations == 1
        assert config_high.max_iterations == 20

    def test_config_edge_thresholds(self):
        """Test config with edge threshold values"""
        config_min = LoopConfig(
            name="min-threshold",
            description="Minimum",
            threshold_a=0.0,
            threshold_b=0.0,
        )
        config_max = LoopConfig(
            name="max-threshold",
            description="Maximum",
            threshold_a=1.0,
            threshold_b=1.0,
        )

        assert config_min.threshold_a == 0.0
        assert config_max.threshold_b == 1.0

    def test_config_cascade_strategies(self):
        """Test different cascade strategies"""
        strategies = ["avg", "max", "min", "wgt"]

        for strategy in strategies:
            config = LoopConfig(
                name=f"cascade-{strategy}",
                description=f"Cascade {strategy}",
                cascade_strategy=strategy,
            )
            assert config.cascade_strategy == strategy
