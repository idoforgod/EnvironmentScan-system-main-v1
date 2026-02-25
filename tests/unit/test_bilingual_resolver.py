"""
Unit tests for bilingual_resolver.py — Deterministic Language Routing.

Tests that the resolver correctly reads SOT bilingual config and outputs
deterministic routing parameters (skeleton paths, profiles, languages)
for all workflows, in both bilingual-enabled and disabled modes.
"""

import json
import sys
from pathlib import Path

import pytest
import yaml

# Add paths so modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "core"))

from bilingual_resolver import (
    resolve_bilingual_config,
    load_bilingual_config,
    get_workflow_config,
)


# ============================================================================
# Shared fixtures
# ============================================================================

REGISTRY_PATH = str(
    Path(__file__).parent.parent.parent
    / "env-scanning"
    / "config"
    / "workflow-registry.yaml"
)


@pytest.fixture
def bilingual_config():
    """Resolve bilingual config from real SOT."""
    return resolve_bilingual_config(REGISTRY_PATH)


@pytest.fixture
def bilingual_config_file(tmp_path):
    """Resolve bilingual config and write to file."""
    output = str(tmp_path / "bilingual-config.json")
    result = resolve_bilingual_config(REGISTRY_PATH, output_path=output)
    return output, result


@pytest.fixture
def disabled_registry(tmp_path):
    """Create a SOT with bilingual.enabled=false."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    registry["system"]["bilingual"]["enabled"] = False
    disabled_path = str(tmp_path / "registry-disabled.yaml")
    with open(disabled_path, "w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True)
    return disabled_path


# ============================================================================
# Core resolution tests
# ============================================================================

class TestBilingualResolver:
    def test_returns_dict(self, bilingual_config):
        assert isinstance(bilingual_config, dict)

    def test_resolver_metadata(self, bilingual_config):
        assert bilingual_config["resolver"] == "bilingual_resolver.py"
        assert "resolver_version" in bilingual_config

    def test_bilingual_enabled(self, bilingual_config):
        assert bilingual_config["bilingual_enabled"] is True

    def test_english_first_when_enabled(self, bilingual_config):
        assert bilingual_config["english_first"] is True
        assert bilingual_config["internal_language"] == "en"
        assert bilingual_config["external_language"] == "ko"

    def test_all_six_workflows_present(self, bilingual_config):
        wfs = bilingual_config["workflows"]
        expected = {"wf1-general", "wf2-arxiv", "wf3-naver", "wf4-multiglobal-news", "integrated", "weekly"}
        assert set(wfs.keys()) == expected

    def test_scripts_section_present(self, bilingual_config):
        scripts = bilingual_config["scripts"]
        assert "skeleton_mirror" in scripts
        assert "translation_validator" in scripts
        assert "bilingual_resolver" in scripts


class TestEnglishFirstRouting:
    """Test that English-first mode routes to EN skeletons and profiles."""

    def test_wf1_en_skeleton(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf1-general"]
        assert wf["report_skeleton"].endswith("-en.md")
        assert "report-skeleton-en.md" in wf["report_skeleton"]

    def test_wf1_en_profile(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf1-general"]
        assert wf["validate_profile"] == "standard_en"

    def test_wf1_en_language(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf1-general"]
        assert wf["statistics_language"] == "en"
        assert wf["metadata_injector_language"] == "en"

    def test_wf1_translation_needed(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf1-general"]
        assert wf["translation_needed"] is True

    def test_wf1_ko_fallback(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf1-general"]
        assert wf["ko_skeleton"].endswith("report-skeleton.md")
        assert not wf["ko_skeleton"].endswith("-en.md")
        assert wf["ko_validate_profile"] == "standard"

    def test_wf2_shares_skeleton_with_wf1(self, bilingual_config):
        wf1 = bilingual_config["workflows"]["wf1-general"]
        wf2 = bilingual_config["workflows"]["wf2-arxiv"]
        assert wf1["report_skeleton"] == wf2["report_skeleton"]

    def test_wf3_naver_en_skeleton(self, bilingual_config):
        wf = bilingual_config["workflows"]["wf3-naver"]
        assert "naver-report-skeleton-en.md" in wf["report_skeleton"]
        assert wf["validate_profile"] == "naver_en"

    def test_integrated_en_skeleton(self, bilingual_config):
        wf = bilingual_config["workflows"]["integrated"]
        assert "integrated-report-skeleton-en.md" in wf["report_skeleton"]
        assert wf["validate_profile"] == "integrated_en"

    def test_weekly_en_skeleton(self, bilingual_config):
        wf = bilingual_config["workflows"]["weekly"]
        assert "weekly-report-skeleton-en.md" in wf["report_skeleton"]
        assert wf["validate_profile"] == "weekly_en"

    def test_all_workflows_have_en_language(self, bilingual_config):
        for wf_id, wf in bilingual_config["workflows"].items():
            assert wf["statistics_language"] == "en", f"{wf_id}: expected en"
            assert wf["metadata_injector_language"] == "en", f"{wf_id}: expected en"

    def test_all_workflows_need_translation(self, bilingual_config):
        for wf_id, wf in bilingual_config["workflows"].items():
            assert wf["translation_needed"] is True, f"{wf_id}: expected True"


class TestDisabledBilingual:
    """Test that bilingual.enabled=false falls back to KO-only mode."""

    def test_disabled_returns_ko_only(self, disabled_registry):
        result = resolve_bilingual_config(disabled_registry)
        assert result["bilingual_enabled"] is False
        assert result["english_first"] is False

    def test_disabled_no_translation(self, disabled_registry):
        result = resolve_bilingual_config(disabled_registry)
        for wf_id, wf in result["workflows"].items():
            assert wf["translation_needed"] is False, f"{wf_id}: expected False"
            assert wf["statistics_language"] == "ko", f"{wf_id}: expected ko"

    def test_disabled_ko_skeletons(self, disabled_registry):
        result = resolve_bilingual_config(disabled_registry)
        wf1 = result["workflows"]["wf1-general"]
        assert not wf1["report_skeleton"].endswith("-en.md")
        assert wf1["validate_profile"] == "standard"

    def test_disabled_naver_ko_skeleton(self, disabled_registry):
        result = resolve_bilingual_config(disabled_registry)
        wf3 = result["workflows"]["wf3-naver"]
        assert "naver-report-skeleton.md" in wf3["report_skeleton"]
        assert not wf3["report_skeleton"].endswith("-en.md")
        assert wf3["validate_profile"] == "naver"


class TestFileIO:
    """Test file output and loading."""

    def test_write_and_load(self, bilingual_config_file):
        output_path, original = bilingual_config_file
        loaded = load_bilingual_config(output_path)
        assert loaded["resolver"] == original["resolver"]
        assert loaded["bilingual_enabled"] == original["bilingual_enabled"]
        assert loaded["workflows"] == original["workflows"]

    def test_get_workflow_config(self, bilingual_config):
        wf = get_workflow_config(bilingual_config, "wf1-general")
        assert "report_skeleton" in wf
        assert "validate_profile" in wf

    def test_get_workflow_config_missing(self, bilingual_config):
        with pytest.raises(KeyError, match="not-a-workflow"):
            get_workflow_config(bilingual_config, "not-a-workflow")

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_bilingual_config("/nonexistent/path.json")


class TestEdgeCases:
    """Test error handling and edge cases."""

    def test_missing_sot_raises(self):
        with pytest.raises(FileNotFoundError):
            resolve_bilingual_config("/nonexistent/registry.yaml")

    def test_en_profile_derivation_pattern(self, bilingual_config):
        """Verify all EN profiles follow {base}_en pattern."""
        for wf_id, wf in bilingual_config["workflows"].items():
            en_profile = wf["validate_profile"]
            ko_profile = wf["ko_validate_profile"]
            assert en_profile == f"{ko_profile}_en", (
                f"{wf_id}: EN profile '{en_profile}' != '{ko_profile}_en'"
            )

    def test_en_skeleton_paths_are_distinct_from_ko(self, bilingual_config):
        """Verify EN and KO skeleton paths are different when bilingual enabled."""
        for wf_id, wf in bilingual_config["workflows"].items():
            assert wf["report_skeleton"] != wf["ko_skeleton"], (
                f"{wf_id}: EN and KO skeleton paths should differ"
            )
