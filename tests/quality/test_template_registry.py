"""
Tests for template_registry.py — Template Registry and Discovery System.

Covers:
- TemplateCategory enum
- TemplateMetadata, TemplateCombination, BlendPreset, BlendedTemplate dataclasses
- TemplateRegistry class (all methods)
- TemplateIntegration class (all methods)
- Standalone functions: blend_templates, print_*, compare_*, format_*, save_*, get_registry
- Edge cases: empty data, missing files, invalid YAML, boundary conditions
"""

import os
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import fields

from specify_cli.quality.template_registry import (
    TemplateCategory,
    TemplateMetadata,
    TemplateCombination,
    BlendPreset,
    BlendedTemplate,
    TemplateRegistry,
    TemplateIntegration,
    get_registry,
    print_template_table,
    print_combination_table,
    compare_templates,
    format_template_diff,
    blend_templates,
    save_blended_template,
    format_blended_template,
    get_recommended_templates,
    validate_templates,
    expand_templates,
    _blend_union,
    _blend_consensus,
    _blend_weighted,
)


# ============================================================
# Helpers
# ============================================================

def _make_metadata(
    name="test-template",
    version="1.0",
    description="Test template",
    file_path="/tmp/test.yml",
    category=TemplateCategory.CORE,
    rule_count=10,
    domain_tags=None,
    has_priority_profiles=False,
    priority_profile_names=None,
    phases=None,
    severity_breakdown=None,
):
    return TemplateMetadata(
        name=name,
        version=version,
        description=description,
        file_path=file_path,
        category=category,
        rule_count=rule_count,
        domain_tags=domain_tags or set(),
        has_priority_profiles=has_priority_profiles,
        priority_profile_names=priority_profile_names or [],
        phases=phases or [],
        severity_breakdown=severity_breakdown or {},
    )


def _make_yaml_file(tmp_path, name, content):
    """Create a YAML template file in tmp_path."""
    file_path = tmp_path / f"{name}.yml"
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f)
    return file_path


def _make_template_dir(tmp_path, templates):
    """Create a directory with multiple YAML template files.
    templates: dict of {name: content}
    """
    for name, content in templates.items():
        _make_yaml_file(tmp_path, name, content)
    return tmp_path


# ============================================================
# 1. TemplateCategory Enum
# ============================================================

class TestTemplateCategory:
    def test_core_value(self):
        assert TemplateCategory.CORE.value == "core"

    def test_infrastructure_value(self):
        assert TemplateCategory.INFRASTRUCTURE.value == "infrastructure"

    def test_architecture_value(self):
        assert TemplateCategory.ARCHITECTURE.value == "architecture"

    def test_domain_value(self):
        assert TemplateCategory.DOMAIN.value == "domain"

    def test_all_categories_defined(self):
        expected = {"core", "infrastructure", "architecture", "domain"}
        actual = {c.value for c in TemplateCategory}
        assert expected == actual


# ============================================================
# 2. TemplateMetadata Dataclass
# ============================================================

class TestTemplateMetadata:
    def test_create_minimal(self):
        m = TemplateMetadata(
            name="test", version="1.0", description="desc",
            file_path="/tmp/test.yml", category=TemplateCategory.CORE,
        )
        assert m.name == "test"
        assert m.rule_count == 0
        assert m.domain_tags == set()
        assert m.has_priority_profiles is False
        assert m.priority_profile_names == []
        assert m.phases == []
        assert m.severity_breakdown == {}

    def test_display_name_replaces_separators(self):
        m = _make_metadata(name="api-spec")
        assert m.display_name == "Api Spec"

    def test_display_name_underscores(self):
        m = _make_metadata(name="my_template")
        assert m.display_name == "My Template"

    def test_is_builtin_true_for_core(self):
        m = _make_metadata(category=TemplateCategory.CORE)
        assert m.is_builtin is True

    def test_is_builtin_false_for_infra(self):
        m = _make_metadata(category=TemplateCategory.INFRASTRUCTURE)
        assert m.is_builtin is False

    def test_is_builtin_false_for_domain(self):
        m = _make_metadata(category=TemplateCategory.DOMAIN)
        assert m.is_builtin is False

    def test_domain_tags_set(self):
        m = _make_metadata(domain_tags={"web", "api"})
        assert m.domain_tags == {"web", "api"}

    def test_severity_breakdown(self):
        m = _make_metadata(severity_breakdown={"fail": 5, "warn": 3})
        assert m.severity_breakdown["fail"] == 5


# ============================================================
# 3. TemplateCombination Dataclass
# ============================================================

class TestTemplateCombination:
    def test_create(self):
        tc = TemplateCombination(
            name="test_combo",
            description="A combo",
            templates=["a", "b"],
            use_case="Testing",
            project_types=["web-app"],
        )
        assert tc.name == "test_combo"
        assert len(tc.templates) == 2
        assert tc.project_types == ["web-app"]


# ============================================================
# 4. BlendPreset Dataclass
# ============================================================

class TestBlendPreset:
    def test_create_minimal(self):
        bp = BlendPreset(
            name="test", description="desc",
            templates=["a", "b"], mode="union",
        )
        assert bp.weights is None
        assert bp.project_types == []
        assert bp.tags == set()

    def test_create_full(self):
        bp = BlendPreset(
            name="test", description="desc",
            templates=["a", "b"], mode="weighted",
            weights={"a": 2.0, "b": 1.0},
            project_types=["web-app"],
            tags={"web", "security"},
        )
        assert bp.mode == "weighted"
        assert bp.weights["a"] == 2.0
        assert "web" in bp.tags


# ============================================================
# 5. BlendedTemplate Dataclass
# ============================================================

class TestBlendedTemplate:
    def test_create(self):
        bt = BlendedTemplate(
            name="blended",
            description="Blended desc",
            source_templates=["a", "b"],
            blend_mode="union",
            rules=[{"id": "r1"}],
            metadata={"total_rules": 1},
        )
        assert bt.name == "blended"
        assert len(bt.rules) == 1
        assert bt.metadata["total_rules"] == 1


# ============================================================
# 6. TemplateRegistry — Init and Loading
# ============================================================

class TestTemplateRegistryInit:
    def test_init_with_nonexistent_dir(self, tmp_path):
        registry = TemplateRegistry(tmp_path / "nonexistent")
        assert registry.list_templates() == []

    def test_init_with_empty_dir(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry.list_templates() == []

    def test_init_loads_yaml_files(self, tmp_path):
        _make_yaml_file(tmp_path, "backend", {
            "version": "1.0",
            "description": "Backend rules",
            "rules": [{"category": "code", "name": "r1", "severity": "fail"}],
        })
        registry = TemplateRegistry(tmp_path)
        templates = registry.list_templates()
        assert len(templates) == 1
        assert templates[0].name == "backend"

    def test_init_skips_invalid_yaml(self, tmp_path):
        # Write truly invalid YAML (tab character in wrong place causes parse error)
        bad_file = tmp_path / "bad.yml"
        bad_file.write_bytes(b"\x00\x01\x02\x03")  # binary garbage
        _make_yaml_file(tmp_path, "good", {"version": "1.0", "description": "ok", "rules": []})
        registry = TemplateRegistry(tmp_path)
        templates = registry.list_templates()
        assert len(templates) == 1

    def test_init_skips_empty_yaml(self, tmp_path):
        empty_file = tmp_path / "empty.yml"
        empty_file.write_text("", encoding="utf-8")
        registry = TemplateRegistry(tmp_path)
        assert registry.list_templates() == []


# ============================================================
# 7. TemplateRegistry — _determine_category
# ============================================================

class TestDetermineCategory:
    def test_builtin_is_core(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry._determine_category("backend") == TemplateCategory.CORE
        assert registry._determine_category("security") == TemplateCategory.CORE

    def test_infrastructure_templates(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry._determine_category("api-gateway") == TemplateCategory.INFRASTRUCTURE
        assert registry._determine_category("terraform") == TemplateCategory.INFRASTRUCTURE
        assert registry._determine_category("serverless") == TemplateCategory.INFRASTRUCTURE

    def test_architecture_templates(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry._determine_category("grpc") == TemplateCategory.ARCHITECTURE
        assert registry._determine_category("desktop") == TemplateCategory.ARCHITECTURE

    def test_domain_templates(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry._determine_category("mobile") == TemplateCategory.DOMAIN

    def test_unknown_defaults_to_core(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry._determine_category("unknown-thing") == TemplateCategory.CORE


# ============================================================
# 8. TemplateRegistry — _extract_metadata
# ============================================================

class TestExtractMetadata:
    def test_extracts_all_fields(self, tmp_path):
        _make_yaml_file(tmp_path, "test", {
            "version": "2.0",
            "description": "My template",
            "rules": [
                {"category": "code", "name": "r1", "severity": "fail", "domain_tags": ["web"]},
                {"category": "code", "name": "r2", "severity": "warn", "domain_tags": ["api"]},
            ],
            "priority_profiles": {"default": {"multipliers": {}}},
            "phases": {"A": {"threshold": 0.8}, "B": {"threshold": 0.9}},
        })
        registry = TemplateRegistry(tmp_path)
        t = registry.get_template("test")
        assert t is not None
        assert t.version == "2.0"
        assert t.description == "My template"
        assert t.rule_count == 2
        assert t.domain_tags == {"web", "api"}
        assert t.has_priority_profiles is True
        assert t.priority_profile_names == ["default"]
        assert set(t.phases) == {"A", "B"}
        assert t.severity_breakdown == {"fail": 1, "warn": 1}

    def test_missing_version_defaults(self, tmp_path):
        _make_yaml_file(tmp_path, "noversion", {"description": "ok", "rules": []})
        registry = TemplateRegistry(tmp_path)
        t = registry.get_template("noversion")
        assert t.version == "1.0"

    def test_missing_rules_returns_zero(self, tmp_path):
        _make_yaml_file(tmp_path, "norules", {"version": "1.0", "description": "ok"})
        registry = TemplateRegistry(tmp_path)
        t = registry.get_template("norules")
        assert t.rule_count == 0

    def test_rules_without_domain_tags(self, tmp_path):
        _make_yaml_file(tmp_path, "notags", {
            "version": "1.0", "description": "ok",
            "rules": [{"category": "code", "name": "r1", "severity": "fail"}],
        })
        registry = TemplateRegistry(tmp_path)
        t = registry.get_template("notags")
        assert t.domain_tags == set()


# ============================================================
# 9. TemplateRegistry — list_templates
# ============================================================

class TestListTemplates:
    def _make_registry(self, tmp_path):
        _make_yaml_file(tmp_path, "backend", {"version": "1.0", "description": "b", "rules": []})
        _make_yaml_file(tmp_path, "api-gateway", {"version": "1.0", "description": "ag", "rules": []})
        _make_yaml_file(tmp_path, "mobile", {"version": "1.0", "description": "m", "rules": []})
        return TemplateRegistry(tmp_path)

    def test_list_all(self, tmp_path):
        registry = self._make_registry(tmp_path)
        templates = registry.list_templates()
        assert len(templates) == 3

    def test_sorted_by_name(self, tmp_path):
        registry = self._make_registry(tmp_path)
        templates = registry.list_templates()
        names = [t.name for t in templates]
        assert names == sorted(names)

    def test_filter_by_category(self, tmp_path):
        registry = self._make_registry(tmp_path)
        infra = registry.list_templates(category=TemplateCategory.INFRASTRUCTURE)
        assert len(infra) == 1
        assert infra[0].name == "api-gateway"

    def test_builtin_only(self, tmp_path):
        registry = self._make_registry(tmp_path)
        builtins = registry.list_templates(builtin_only=True)
        names = [t.name for t in builtins]
        assert "backend" in names
        assert "api-gateway" not in names  # infrastructure, not builtin


# ============================================================
# 10. TemplateRegistry — get_template
# ============================================================

class TestGetTemplate:
    def test_get_existing(self, tmp_path):
        _make_yaml_file(tmp_path, "backend", {"version": "1.0", "description": "b", "rules": []})
        registry = TemplateRegistry(tmp_path)
        t = registry.get_template("backend")
        assert t is not None
        assert t.name == "backend"

    def test_get_nonexistent(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry.get_template("nonexistent") is None


# ============================================================
# 11. TemplateRegistry — search_templates
# ============================================================

class TestSearchTemplates:
    def _make_registry(self, tmp_path):
        _make_yaml_file(tmp_path, "backend", {"version": "1.0", "description": "Backend rules for servers", "rules": []})
        _make_yaml_file(tmp_path, "frontend", {"version": "1.0", "description": "Frontend UI rules", "rules": [
            {"category": "ui", "name": "r1", "severity": "warn", "domain_tags": ["web", "react"]}
        ]})
        _make_yaml_file(tmp_path, "security", {"version": "1.0", "description": "Security validation", "rules": []})
        return TemplateRegistry(tmp_path)

    def test_search_by_name(self, tmp_path):
        registry = self._make_registry(tmp_path)
        results = registry.search_templates("back")
        assert len(results) == 1
        assert results[0].name == "backend"

    def test_search_by_description(self, tmp_path):
        registry = self._make_registry(tmp_path)
        results = registry.search_templates("validation")
        assert len(results) == 1
        assert results[0].name == "security"

    def test_search_by_domain_tag(self, tmp_path):
        registry = self._make_registry(tmp_path)
        results = registry.search_templates("react")
        assert len(results) == 1
        assert results[0].name == "frontend"

    def test_search_case_insensitive(self, tmp_path):
        registry = self._make_registry(tmp_path)
        results = registry.search_templates("BACKEND")
        assert len(results) == 1

    def test_search_no_results(self, tmp_path):
        registry = self._make_registry(tmp_path)
        results = registry.search_templates("nonexistent_query")
        assert results == []


# ============================================================
# 12. TemplateRegistry — get_recommendations
# ============================================================

class TestGetRecommendations:
    def test_matching_project_type(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        recs = registry.get_recommendations("web-app")
        assert len(recs) >= 1
        assert any("web-app" in r.project_types for r in recs)

    def test_no_matching_project_type(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        recs = registry.get_recommendations("unknown-project-type-xyz")
        assert recs == []

    def test_with_domain_tags(self, tmp_path):
        _make_yaml_file(tmp_path, "frontend", {
            "version": "1.0", "description": "FE",
            "rules": [{"category": "ui", "name": "r1", "severity": "warn", "domain_tags": ["web"]}],
        })
        registry = TemplateRegistry(tmp_path)
        recs = registry.get_recommendations("web-app", domain_tags={"web"})
        assert len(recs) >= 1


# ============================================================
# 13. TemplateRegistry — get_template_stats
# ============================================================

class TestGetTemplateStats:
    def test_stats_structure(self, tmp_path):
        _make_yaml_file(tmp_path, "backend", {"version": "1.0", "description": "b", "rules": [{"severity": "fail"}]})
        registry = TemplateRegistry(tmp_path)
        stats = registry.get_template_stats()
        assert "total_templates" in stats
        assert "builtin_templates" in stats
        assert "custom_templates" in stats
        assert "by_category" in stats
        assert "total_rules" in stats
        assert stats["total_templates"] == 1
        assert stats["total_rules"] == 1

    def test_stats_empty_registry(self, tmp_path):
        registry = TemplateRegistry(tmp_path / "empty")
        stats = registry.get_template_stats()
        assert stats["total_templates"] == 0
        assert stats["total_rules"] == 0


# ============================================================
# 14. TemplateRegistry — get_compatible_templates
# ============================================================

class TestGetCompatibleTemplates:
    def test_finds_compatible(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        compatible = registry.get_compatible_templates("frontend")
        # frontend is in full_stack_web_app combo with backend, api-spec, etc.
        assert "backend" in compatible
        assert "frontend" not in compatible  # should not include itself

    def test_unknown_template_returns_empty(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry.get_compatible_templates("nonexistent_xyz") == []

    def test_returns_sorted(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        compatible = registry.get_compatible_templates("backend")
        assert compatible == sorted(compatible)


# ============================================================
# 15. TemplateRegistry — Blend Presets
# ============================================================

class TestBlendPresets:
    def test_list_all_presets(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        presets = registry.list_blend_presets()
        assert len(presets) == 10  # 10 defined presets

    def test_filter_by_tag(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        presets = registry.list_blend_presets(tag="security")
        assert all(
            "security" in {t.lower() for t in p.tags}
            for p in presets
        )

    def test_filter_by_project_type(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        presets = registry.list_blend_presets(project_type="web-app")
        assert len(presets) >= 1
        assert all(
            "web-app" in {pt.lower() for pt in p.project_types}
            for p in presets
        )

    def test_filter_by_unknown_tag(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        presets = registry.list_blend_presets(tag="nonexistent_tag_xyz")
        assert presets == []

    def test_get_preset_existing(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        preset = registry.get_blend_preset("full_stack_secure")
        assert preset is not None
        assert preset.name == "full_stack_secure"

    def test_get_preset_nonexistent(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry.get_blend_preset("nonexistent") is None


# ============================================================
# 16. TemplateRegistry — search_blend_presets
# ============================================================

class TestSearchBlendPresets:
    def test_search_by_name(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        results = registry.search_blend_presets("full_stack")
        assert len(results) >= 1
        assert results[0].name == "full_stack_secure"

    def test_search_by_description(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        results = registry.search_blend_presets("microservices")
        assert len(results) >= 1

    def test_search_by_tag(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        results = registry.search_blend_presets("mvp")
        assert any(p.name == "startup_mvp" for p in results)

    def test_search_by_template_name(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        results = registry.search_blend_presets("terraform")
        assert any(p.name == "devsecops" for p in results)

    def test_search_no_match(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        results = registry.search_blend_presets("xyznonexistent")
        assert results == []


# ============================================================
# 17. TemplateRegistry — recommend_blend_preset
# ============================================================

class TestRecommendBlendPreset:
    def test_direct_mapping(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        preset = registry.recommend_blend_preset("web-app")
        assert preset is not None
        assert preset.name == "full_stack_secure"

    def test_direct_mapping_case_insensitive(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        preset = registry.recommend_blend_preset("Web-App")
        assert preset is not None

    def test_multiple_mappings(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        assert registry.recommend_blend_preset("microservice").name == "microservices_robust"
        assert registry.recommend_blend_preset("mobile-app").name == "mobile_backend"
        assert registry.recommend_blend_preset("serverless").name == "cloud_native"
        assert registry.recommend_blend_preset("startup").name == "startup_mvp"
        assert registry.recommend_blend_preset("iot").name == "iot_platform"
        assert registry.recommend_blend_preset("devops").name == "devsecops"

    def test_fallback_to_tag_matching(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        # "unknown-type" is not in preset_mapping, should fallback
        result = registry.recommend_blend_preset("unknown-type-xyz")
        # May return None if no tag match
        assert result is None or isinstance(result, BlendPreset)


# ============================================================
# 18. TemplateRegistry — apply_blend_preset
# ============================================================

class TestApplyBlendPreset:
    def test_apply_nonexistent_preset(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        result = registry.apply_blend_preset("nonexistent")
        assert result is None

    def test_apply_preset_no_templates_found(self, tmp_path):
        # Registry with no actual template files, so preset templates won't resolve
        registry = TemplateRegistry(tmp_path)
        result = registry.apply_blend_preset("full_stack_secure")
        assert result is None  # No template files to load

    def test_apply_preset_with_templates(self, tmp_path):
        # Create template files matching a preset
        for name in ["frontend", "backend", "api-spec", "security", "performance", "testing"]:
            _make_yaml_file(tmp_path, name, {
                "version": "1.0", "description": f"{name} rules",
                "rules": [{"category": "code", "name": f"{name}_r1", "check": f"check_{name}", "severity": "warn"}],
            })
        registry = TemplateRegistry(tmp_path)
        result = registry.apply_blend_preset("full_stack_secure")
        assert result is not None
        assert isinstance(result, BlendedTemplate)
        assert result.name == "full_stack_secure"
        assert len(result.rules) >= 1

    def test_apply_preset_with_custom_name(self, tmp_path):
        for name in ["frontend", "backend", "api-spec", "security", "performance", "testing"]:
            _make_yaml_file(tmp_path, name, {
                "version": "1.0", "description": f"{name} rules",
                "rules": [{"category": "code", "name": f"{name}_r1", "check": f"check_{name}", "severity": "warn"}],
            })
        registry = TemplateRegistry(tmp_path)
        result = registry.apply_blend_preset("full_stack_secure", custom_name="my_blend", custom_description="My custom blend")
        assert result.name == "my_blend"
        assert result.description == "My custom blend"


# ============================================================
# 19. TemplateRegistry — get_all_blend_presets_info
# ============================================================

class TestGetAllBlendPresetsInfo:
    def test_returns_list_of_dicts(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        info = registry.get_all_blend_presets_info()
        assert isinstance(info, list)
        assert len(info) == 10

    def test_dict_structure(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        info = registry.get_all_blend_presets_info()
        for item in info:
            assert "name" in item
            assert "description" in item
            assert "templates" in item
            assert "mode" in item
            assert "project_types" in item
            assert "tags" in item
            assert isinstance(item["tags"], list)


# ============================================================
# 20. TemplateRegistry — auto_detect_blend_preset
# ============================================================

class TestAutoDetectBlendPreset:
    def test_returns_preset_on_detection(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        with patch("specify_cli.quality.autodetect.ProfileDetector") as mock_detector:
            mock_instance = MagicMock()
            mock_instance.detect.return_value = "web-app"
            mock_detector.return_value = mock_instance
            result = registry.auto_detect_blend_preset(tmp_path)
            # Returns None or BlendPreset (no actual templates in tmp_path)
            assert result is None or isinstance(result, BlendPreset)

    def test_returns_fallback_on_error(self, tmp_path):
        registry = TemplateRegistry(tmp_path)
        with patch("specify_cli.quality.autodetect.ProfileDetector", side_effect=Exception("fail")):
            result = registry.auto_detect_blend_preset(tmp_path)
            # Should return fallback (full_stack_secure or None depending on registry)
            assert result is None or isinstance(result, BlendPreset)


# ============================================================
# 21. get_registry singleton
# ============================================================

class TestGetRegistry:
    def test_returns_registry_instance(self, tmp_path):
        import specify_cli.quality.template_registry as mod
        old = mod._registry_instance
        try:
            mod._registry_instance = None
            registry = get_registry(tmp_path)
            assert isinstance(registry, TemplateRegistry)
        finally:
            mod._registry_instance = old

    def test_returns_same_instance(self, tmp_path):
        import specify_cli.quality.template_registry as mod
        old = mod._registry_instance
        try:
            mod._registry_instance = None
            r1 = get_registry(tmp_path)
            r2 = get_registry()
            assert r1 is r2
        finally:
            mod._registry_instance = old

    def test_new_instance_on_custom_dir(self, tmp_path):
        import specify_cli.quality.template_registry as mod
        old = mod._registry_instance
        try:
            mod._registry_instance = None
            r1 = get_registry(tmp_path)
            r2 = get_registry(tmp_path / "other")
            assert r1 is not r2
        finally:
            mod._registry_instance = old


# ============================================================
# 22. print_template_table
# ============================================================

class TestPrintTemplateTable:
    def test_empty_list(self):
        result = print_template_table([])
        assert result == "No templates found."

    def test_formats_table(self):
        templates = [
            _make_metadata(name="backend", version="2.0", description="Backend rules", rule_count=15),
        ]
        result = print_template_table(templates)
        assert "Backend" in result
        assert "2.0" in result
        assert "15" in result
        assert "=" * 100 in result

    def test_truncates_long_description(self):
        long_desc = "A" * 50
        templates = [_make_metadata(description=long_desc)]
        result = print_template_table(templates)
        assert "..." in result


# ============================================================
# 23. print_combination_table
# ============================================================

class TestPrintCombinationTable:
    def test_empty_list(self):
        result = print_combination_table([])
        assert result == "No recommendations found."

    def test_formats_combinations(self):
        combos = [
            TemplateCombination(
                name="web_app", description="Web app combo",
                templates=["frontend", "backend", "security"],
                use_case="Full web app", project_types=["web-app"],
            )
        ]
        result = print_combination_table(combos)
        assert "Web App" in result
        assert "frontend" in result

    def test_truncates_templates_over_5(self):
        combos = [
            TemplateCombination(
                name="big", description="Many templates",
                templates=["a", "b", "c", "d", "e", "f", "g"],
                use_case="Big combo", project_types=["test"],
            )
        ]
        result = print_combination_table(combos)
        assert "+2 more" in result


# ============================================================
# 24. compare_templates
# ============================================================

class TestCompareTemplates:
    def test_empty_list(self):
        assert compare_templates([]) == "No templates to compare."

    def test_single_template(self):
        result = compare_templates([_make_metadata()])
        assert "Need at least 2" in result

    def test_two_templates(self):
        t1 = _make_metadata(name="a", domain_tags={"web"}, severity_breakdown={"fail": 3}, phases=["A"])
        t2 = _make_metadata(name="b", domain_tags={"api"}, severity_breakdown={"warn": 2}, phases=["B"])
        result = compare_templates([t1, t2])
        assert "TEMPLATE COMPARISON" in result
        assert "web" in result
        assert "api" in result

    def test_max_four_templates(self):
        templates = [_make_metadata(name=f"t{i}") for i in range(6)]
        result = compare_templates(templates)
        # Should only display up to 4
        assert "T0" in result
        assert "T3" in result

    def test_no_phases(self):
        t1 = _make_metadata(name="a")
        t2 = _make_metadata(name="b")
        result = compare_templates([t1, t2])
        assert "No phases defined" in result

    def test_no_profiles(self):
        t1 = _make_metadata(name="a", priority_profile_names=[])
        t2 = _make_metadata(name="b", priority_profile_names=[])
        result = compare_templates([t1, t2])
        assert "No profiles defined" in result

    def test_with_profiles(self):
        t1 = _make_metadata(name="a", priority_profile_names=["default", "web"])
        t2 = _make_metadata(name="b", priority_profile_names=["default"])
        result = compare_templates([t1, t2])
        assert "default" in result
        assert "web" in result


# ============================================================
# 25. format_template_diff
# ============================================================

class TestFormatTemplateDiff:
    def test_identical_templates(self):
        t = _make_metadata()
        result = format_template_diff(t, t)
        assert "TEMPLATE DIFF" in result
        assert "[DIFF]" not in result  # No diffs for identical

    def test_category_diff(self):
        t1 = _make_metadata(category=TemplateCategory.CORE)
        t2 = _make_metadata(category=TemplateCategory.INFRASTRUCTURE)
        result = format_template_diff(t1, t2)
        assert "[DIFF] Category" in result

    def test_rules_diff(self):
        t1 = _make_metadata(rule_count=10)
        t2 = _make_metadata(rule_count=15)
        result = format_template_diff(t1, t2)
        assert "[DIFF] Rules: 10" in result
        assert "+5" in result

    def test_domain_tags_diff(self):
        t1 = _make_metadata(domain_tags={"web", "shared"})
        t2 = _make_metadata(domain_tags={"api", "shared"})
        result = format_template_diff(t1, t2)
        assert "[DIFF] Domain Tags" in result
        assert "web" in result
        assert "api" in result

    def test_severity_diff(self):
        t1 = _make_metadata(severity_breakdown={"fail": 5})
        t2 = _make_metadata(severity_breakdown={"fail": 3, "warn": 2})
        result = format_template_diff(t1, t2)
        assert "[DIFF] Severity" in result


# ============================================================
# 26. blend_templates
# ============================================================

class TestBlendTemplates:
    def _make_templates(self, tmp_path):
        """Create two template files and return their metadata."""
        _make_yaml_file(tmp_path, "t1", {
            "version": "1.0", "description": "T1",
            "rules": [
                {"category": "code", "name": "r1", "check": "check1", "severity": "fail"},
                {"category": "code", "name": "r2", "check": "check2", "severity": "warn"},
            ],
            "phases": {"A": {"threshold": 0.8}},
            "priority_profiles": {"default": {"multipliers": {"web": 1.5}}},
        })
        _make_yaml_file(tmp_path, "t2", {
            "version": "1.0", "description": "T2",
            "rules": [
                {"category": "code", "name": "r1", "check": "check1", "severity": "warn"},  # duplicate with different severity
                {"category": "code", "name": "r3", "check": "check3", "severity": "fail"},
            ],
            "phases": {"B": {"threshold": 0.9}},
        })
        registry = TemplateRegistry(tmp_path)
        return [registry.get_template("t1"), registry.get_template("t2")]

    def test_blend_less_than_2_raises(self):
        with pytest.raises(ValueError, match="at least 2"):
            blend_templates([_make_metadata()])

    def test_blend_more_than_8_raises(self):
        templates = [_make_metadata(name=f"t{i}") for i in range(9)]
        with pytest.raises(ValueError, match="more than 8"):
            blend_templates(templates)

    def test_blend_invalid_mode_raises(self):
        templates = [_make_metadata(name="a"), _make_metadata(name="b")]
        with pytest.raises(ValueError, match="Invalid blend mode"):
            blend_templates(templates, mode="invalid")

    def test_blend_weighted_without_weights_raises(self):
        templates = [_make_metadata(name="a"), _make_metadata(name="b")]
        with pytest.raises(ValueError, match="Weights must be provided"):
            blend_templates(templates, mode="weighted")

    def test_blend_union_mode(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(templates, mode="union", name="test_blend")
        assert isinstance(result, BlendedTemplate)
        assert result.blend_mode == "union"
        # r1 is deduped, so 3 unique rules (r1, r2, r3)
        assert len(result.rules) == 3

    def test_blend_consensus_mode(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(templates, mode="consensus", name="test_consensus")
        # r1 appears in both (2/2 >= 1 threshold), r2 and r3 only once (1/2 >= 1, so they also pass)
        # With threshold = 2/2 = 1, all rules with count >= 1 pass
        assert len(result.rules) >= 1

    def test_blend_weighted_mode(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(
            templates, mode="weighted",
            weights={"t1": 2.0, "t2": 1.0},
            name="test_weighted",
        )
        assert result.blend_mode == "weighted"
        assert len(result.rules) >= 1

    def test_blend_merges_phases(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(templates, mode="union", name="test")
        phases = result.metadata.get("phases", {})
        assert "A" in phases
        assert "B" in phases

    def test_blend_merges_priority_profiles(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(templates, mode="union", name="test")
        profiles = result.metadata.get("priority_profiles", {})
        assert "t1_default" in profiles

    def test_blend_no_valid_contents_raises(self, tmp_path):
        t1 = _make_metadata(name="a", file_path="/nonexistent/path.yml")
        t2 = _make_metadata(name="b", file_path="/nonexistent/path2.yml")
        with pytest.raises(ValueError, match="No valid template contents"):
            blend_templates([t1, t2])

    def test_blend_auto_generates_name(self, tmp_path):
        templates = self._make_templates(tmp_path)
        result = blend_templates(templates, mode="union", name="", description="")
        assert result.name.startswith("blend-")
        assert "Blended template from" in result.description


# ============================================================
# 27. _blend_union
# ============================================================

class TestBlendUnion:
    def test_deduplicates_rules(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1"}]},
            {"rules": [{"category": "c", "name": "r1", "check": "ch1"}]},
        ]
        result = _blend_union(contents)
        assert len(result) == 1

    def test_keeps_unique_rules(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1"}]},
            {"rules": [{"category": "c", "name": "r2", "check": "ch2"}]},
        ]
        result = _blend_union(contents)
        assert len(result) == 2

    def test_empty_rules(self):
        contents = [{"rules": []}, {"rules": []}]
        result = _blend_union(contents)
        assert result == []

    def test_no_rules_key(self):
        contents = [{}, {}]
        result = _blend_union(contents)
        assert result == []


# ============================================================
# 28. _blend_consensus
# ============================================================

class TestBlendConsensus:
    def test_majority_rule(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "fail"}]},
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "warn"}]},
            {"rules": [{"category": "c", "name": "r2", "check": "ch2", "severity": "warn"}]},
        ]
        result = _blend_consensus(contents)
        # r1 appears 2/3 >= 1.5 threshold, r2 appears 1/3 < 1.5
        names = [r.get("name") for r in result]
        assert "r1" in names
        assert "r2" not in names

    def test_uses_highest_severity(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "warn"}]},
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "fail"}]},
        ]
        result = _blend_consensus(contents)
        assert result[0]["severity"] == "fail"


# ============================================================
# 29. _blend_weighted
# ============================================================

class TestBlendWeighted:
    def test_weighted_selection(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "warn"}]},
            {"rules": [{"category": "c", "name": "r2", "check": "ch2", "severity": "fail"}]},
        ]
        templates = [_make_metadata(name="t1"), _make_metadata(name="t2")]
        weights = {"t1": 2.0, "t2": 1.0}
        result = _blend_weighted(contents, weights, templates)
        assert len(result) >= 1

    def test_zero_total_weight(self):
        contents = [
            {"rules": [{"category": "c", "name": "r1", "check": "ch1", "severity": "warn"}]},
            {"rules": [{"category": "c", "name": "r2", "check": "ch2", "severity": "fail"}]},
        ]
        templates = [_make_metadata(name="t1"), _make_metadata(name="t2")]
        weights = {"t1": 0.0, "t2": 0.0}
        # Should not crash - total_weight defaults to 1
        result = _blend_weighted(contents, weights, templates)
        assert isinstance(result, list)


# ============================================================
# 30. save_blended_template
# ============================================================

class TestSaveBlendedTemplate:
    def test_saves_yaml(self, tmp_path):
        bt = BlendedTemplate(
            name="saved", description="Saved blend",
            source_templates=["a", "b"], blend_mode="union",
            rules=[{"id": "r1", "severity": "fail"}],
            metadata={
                "priority_profiles": {"prof1": {"x": 1}},
                "phases": {"A": {"threshold": 0.8}},
            },
        )
        output = tmp_path / "output" / "saved.yml"
        save_blended_template(bt, output, version="2.0")
        assert output.exists()

        with open(output, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        assert content["version"] == "2.0"
        assert content["description"] == "Saved blend"
        assert content["blend_mode"] == "union"
        assert len(content["rules"]) == 1
        assert "priority_profiles" in content
        assert "phases" in content

    def test_creates_parent_dirs(self, tmp_path):
        bt = BlendedTemplate(
            name="test", description="test",
            source_templates=["a"], blend_mode="union",
            rules=[], metadata={},
        )
        output = tmp_path / "deep" / "nested" / "dir" / "test.yml"
        save_blended_template(bt, output)
        assert output.exists()


# ============================================================
# 31. format_blended_template
# ============================================================

class TestFormatBlendedTemplate:
    def test_formats_union(self):
        bt = BlendedTemplate(
            name="my_blend", description="A blended template",
            source_templates=["a", "b"], blend_mode="union",
            rules=[{"id": "r1"}], metadata={},
        )
        result = format_blended_template(bt)
        assert "my_blend" in result
        assert "union" in result
        assert "a, b" in result

    def test_formats_weighted_with_weights(self):
        bt = BlendedTemplate(
            name="weighted_blend", description="Weighted",
            source_templates=["a", "b"], blend_mode="weighted",
            rules=[], metadata={"weights": {"a": 2.0, "b": 1.0}},
        )
        result = format_blended_template(bt)
        assert "weighted" in result
        assert "2.00" in result


# ============================================================
# 32. TemplateIntegration — get_recommended_templates
# ============================================================

class TestTemplateIntegrationGetRecommended:
    def test_known_project_type(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            combo = TemplateCombination(
                name="test", description="test",
                templates=["frontend", "backend"],
                use_case="test", project_types=["web-app"],
            )
            mock_instance.get_recommendations.return_value = [combo]
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.get_recommended_templates("web-app")
            assert result == ["frontend", "backend"]

    def test_unknown_type_fallback(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_recommendations.return_value = []
            mock_reg.return_value = mock_instance
            with patch("specify_cli.quality.template_registry._get_integration_console") as mock_console:
                mock_console.return_value = MagicMock()
                result = TemplateIntegration.get_recommended_templates("unknown-xyz")
                assert result == ["backend", "security", "testing", "docs"]

    def test_unknown_type_no_fallback(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_recommendations.return_value = []
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.get_recommended_templates("unknown-xyz", fallback_to_default=False)
            assert result == []

    def test_alias_normalization(self):
        assert TemplateIntegration.PROJECT_TYPE_ALIASES["web"] == "web-app"
        assert TemplateIntegration.PROJECT_TYPE_ALIASES["ml"] == "ml-service"
        assert TemplateIntegration.PROJECT_TYPE_ALIASES["fullstack"] == "full-stack"


# ============================================================
# 33. TemplateIntegration — validate_template_combination
# ============================================================

class TestTemplateIntegrationValidate:
    def test_all_valid(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata()
            mock_reg.return_value = mock_instance
            is_valid, valid_list, warning = TemplateIntegration.validate_template_combination(["backend"])
            assert is_valid is True
            assert len(valid_list) == 1
            assert warning is None

    def test_some_invalid(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.side_effect = lambda n: _make_metadata() if n == "backend" else None
            mock_reg.return_value = mock_instance
            is_valid, valid_list, warning = TemplateIntegration.validate_template_combination(["backend", "nonexistent"])
            assert is_valid is False
            assert "nonexistent" in warning


# ============================================================
# 34. TemplateIntegration — expand_templates
# ============================================================

class TestTemplateIntegrationExpand:
    def test_expand_with_dependencies(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata()
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.expand_templates(["frontend"])
            assert "testing" in result  # frontend depends on testing

    def test_no_expand(self):
        result = TemplateIntegration.expand_templates(["frontend"], include_dependencies=False)
        assert result == ["frontend"]

    def test_expand_returns_sorted(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata()
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.expand_templates(["backend", "frontend"])
            assert result == sorted(result)


# ============================================================
# 35. TemplateIntegration — suggest_from_codebase
# ============================================================

class TestTemplateIntegrationSuggest:
    def test_suggests_security_always(self, tmp_path):
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "security" in result

    def test_detects_frontend(self, tmp_path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "frontend" in result

    def test_detects_backend(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask", encoding="utf-8")
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "backend" in result

    def test_detects_tests(self, tmp_path):
        (tmp_path / "tests").mkdir()
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "testing" in result

    def test_detects_docs(self, tmp_path):
        (tmp_path / "docs").mkdir()
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "docs" in result

    def test_detects_database(self, tmp_path):
        (tmp_path / "migrations").mkdir()
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "database" in result

    def test_detects_infrastructure(self, tmp_path):
        (tmp_path / "docker").mkdir()
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert "infrastructure" in result

    def test_returns_sorted(self, tmp_path):
        result = TemplateIntegration.suggest_from_codebase(tmp_path)
        assert result == sorted(result)


# ============================================================
# 36. TemplateIntegration — format_template_summary
# ============================================================

class TestTemplateIntegrationFormatSummary:
    def test_empty_templates(self):
        result = TemplateIntegration.format_template_summary([])
        assert "No templates selected" in result

    def test_with_templates(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata(name="backend", description="Backend rules", rule_count=10)
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.format_template_summary(["backend"])
            assert isinstance(result, str)
            assert len(result) > 0

    def test_unknown_template_shows_error(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = None
            mock_reg.return_value = mock_instance
            result = TemplateIntegration.format_template_summary(["nonexistent"])
            assert isinstance(result, str)


# ============================================================
# 37. TemplateIntegration — _detect_conflicts
# ============================================================

class TestDetectConflicts:
    def test_no_conflicts(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata(domain_tags={"web"})
            mock_reg.return_value = mock_instance
            conflicts = TemplateIntegration._detect_conflicts(["backend"])
            assert conflicts == []

    def test_react_vue_conflict(self):
        with patch("specify_cli.quality.template_registry.get_registry") as mock_reg:
            mock_instance = MagicMock()
            mock_instance.get_template.return_value = _make_metadata(domain_tags={"react", "vue"})
            mock_reg.return_value = mock_instance
            conflicts = TemplateIntegration._detect_conflicts(["frontend"])
            assert len(conflicts) >= 1
            assert "React and Vue" in conflicts[0]


# ============================================================
# 38. Convenience functions
# ============================================================

class TestConvenienceFunctions:
    def test_get_recommended_templates_delegates(self):
        with patch.object(TemplateIntegration, "get_recommended_templates", return_value=["a"]) as mock:
            result = get_recommended_templates("web-app")
            mock.assert_called_once_with(project_type="web-app", fallback_to_default=True)
            assert result == ["a"]

    def test_validate_templates_delegates(self):
        with patch.object(TemplateIntegration, "validate_template_combination", return_value=(True, ["a"], None)) as mock:
            result = validate_templates(["a"])
            mock.assert_called_once_with(["a"])
            assert result == (True, ["a"], None)

    def test_expand_templates_delegates(self):
        with patch.object(TemplateIntegration, "expand_templates", return_value=["a", "b"]) as mock:
            result = expand_templates(["a"])
            mock.assert_called_once_with(templates=["a"], include_dependencies=True)
            assert result == ["a", "b"]


# ============================================================
# 39. BUILTIN_CRITERIA constant
# ============================================================

class TestBuiltinCriteria:
    def test_contains_13_criteria(self):
        assert len(TemplateRegistry.BUILTIN_CRITERIA) == 13

    def test_known_criteria(self):
        for name in ["api-spec", "code-gen", "docs", "config", "database",
                      "frontend", "backend", "infrastructure", "testing",
                      "security", "performance", "ui-ux", "live-test"]:
            assert name in TemplateRegistry.BUILTIN_CRITERIA


# ============================================================
# 40. BLEND_PRESETS constant
# ============================================================

class TestBlendPresetsConstant:
    def test_10_presets_defined(self):
        assert len(TemplateRegistry.BLEND_PRESETS) == 10

    def test_all_presets_have_name(self):
        for preset in TemplateRegistry.BLEND_PRESETS:
            assert preset.name
            assert preset.description
            assert len(preset.templates) >= 2
            assert preset.mode in ("union", "consensus", "weighted")

    def test_preset_names_unique(self):
        names = [p.name for p in TemplateRegistry.BLEND_PRESETS]
        assert len(names) == len(set(names))


# ============================================================
# 41. RECOMMENDED_COMBINATIONS constant
# ============================================================

class TestRecommendedCombinations:
    def test_8_combinations_defined(self):
        assert len(TemplateRegistry.RECOMMENDED_COMBINATIONS) == 8

    def test_all_have_required_fields(self):
        for combo in TemplateRegistry.RECOMMENDED_COMBINATIONS:
            assert combo.name
            assert combo.description
            assert len(combo.templates) >= 2
            assert combo.use_case
            assert len(combo.project_types) >= 1

    def test_combination_names_unique(self):
        names = [c.name for c in TemplateRegistry.RECOMMENDED_COMBINATIONS]
        assert len(names) == len(set(names))


# ============================================================
# 42. COMPATIBILITY_GROUPS constant
# ============================================================

class TestCompatibilityGroups:
    def test_groups_defined(self):
        groups = TemplateIntegration.COMPATIBILITY_GROUPS
        assert "web-stack" in groups
        assert "api-stack" in groups
        assert "data-stack" in groups
        assert "infra-stack" in groups
        assert "mobile-stack" in groups

    def test_groups_are_sets(self):
        for group_name, templates in TemplateIntegration.COMPATIBILITY_GROUPS.items():
            assert isinstance(templates, set)
            assert len(templates) >= 2
