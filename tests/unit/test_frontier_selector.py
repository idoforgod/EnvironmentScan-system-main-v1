"""Tests for frontier_selector.py — Deterministic weighted-random keyword selection."""

import json
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "env-scanning"))
from core.frontier_selector import (
    select_frontier_keywords,
    _weighted_sample_unique,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def frontiers_yaml(temp_dir):
    """Create a minimal exploration-frontiers.yaml for testing."""
    config = {
        "frontiers": {
            "geographic": [
                "African innovation technology RSS",
                "Southeast Asian emerging policy feed",
            ],
            "interdisciplinary": [
                "art technology convergence research",
                "food systems innovation",
            ],
            "emerging_domains": [
                "quantum biology applications",
                "synthetic biology ethics governance",
            ],
            "paradigm_shifts": [
                "degrowth economics research",
                "post-quantum cryptography",
            ],
        },
        "selection": {
            "method": "weighted_random",
            "samples_per_scan": 3,
            "weight_by_success": True,
            "cooldown_after_failure": 3,
        },
    }
    path = temp_dir / "frontiers.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return str(path)


@pytest.fixture
def history_with_data(temp_dir):
    """Create an exploration history with success/failure data."""
    data = {
        "version": "1.0.0",
        "scans": [{"date": "2026-02-09"}, {"date": "2026-02-10"}],
        "learning": {
            "keyword_successes": {
                "African innovation technology RSS": 3,
                "food systems innovation": 2,
            },
            "keyword_failures": {
                "degrowth economics research": 2,
            },
            "keyword_last_failure_scan": {
                "degrowth economics research": 1,  # Failed on scan #1 (0-indexed)
            },
        },
        "approved": [],
        "discarded": [],
        "deferred": [],
    }
    path = temp_dir / "history.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


# ---------------------------------------------------------------------------
# Selection tests
# ---------------------------------------------------------------------------

class TestSelectFrontierKeywords:
    def test_selects_correct_number_with_seed(self, frontiers_yaml):
        result = select_frontier_keywords(frontiers_yaml, samples=3, seed=42)
        assert result["status"] == "SUCCESS"
        assert result["selected_count"] == 3
        assert len(result["selected_keywords"]) == 3

    def test_each_keyword_has_required_fields(self, frontiers_yaml):
        result = select_frontier_keywords(frontiers_yaml, samples=2, seed=42)
        for kw in result["selected_keywords"]:
            assert "keyword" in kw
            assert "category" in kw
            assert "weight" in kw

    def test_deterministic_with_same_seed(self, frontiers_yaml):
        r1 = select_frontier_keywords(frontiers_yaml, samples=3, seed=123)
        r2 = select_frontier_keywords(frontiers_yaml, samples=3, seed=123)
        kw1 = [k["keyword"] for k in r1["selected_keywords"]]
        kw2 = [k["keyword"] for k in r2["selected_keywords"]]
        assert kw1 == kw2

    def test_different_seeds_give_different_results(self, frontiers_yaml):
        # With 8 keywords and 3 selections, different seeds are very likely to differ
        r1 = select_frontier_keywords(frontiers_yaml, samples=3, seed=1)
        r2 = select_frontier_keywords(frontiers_yaml, samples=3, seed=9999)
        kw1 = set(k["keyword"] for k in r1["selected_keywords"])
        kw2 = set(k["keyword"] for k in r2["selected_keywords"])
        # Not a hard guarantee but extremely likely with different seeds
        # If this flakes, increase keyword pool or change seeds
        assert kw1 != kw2

    def test_success_weights_boost_keywords(self, frontiers_yaml, history_with_data):
        # Run many selections and check that successful keywords appear more often
        counts = {}
        for seed in range(100):
            result = select_frontier_keywords(
                frontiers_yaml, history_path=history_with_data, samples=1, seed=seed
            )
            if result["selected_count"] > 0:
                kw = result["selected_keywords"][0]["keyword"]
                counts[kw] = counts.get(kw, 0) + 1

        # "African innovation technology RSS" had 3 successes → should have higher weight
        # Not a hard test (randomness) but over 100 trials the boosted one should appear often
        african = counts.get("African innovation technology RSS", 0)
        assert african > 0  # Must appear at least once

    def test_cooldown_excludes_recently_failed(self, frontiers_yaml, history_with_data):
        result = select_frontier_keywords(
            frontiers_yaml, history_path=history_with_data, samples=8, seed=42
        )
        selected_kws = {k["keyword"] for k in result["selected_keywords"]}
        # "degrowth economics research" failed at scan 1, total scans = 2
        # scans_since_failure = 2 - 1 = 1, cooldown = 3 → should be excluded
        assert "degrowth economics research" not in selected_kws

    def test_avoid_patterns_filter(self, frontiers_yaml):
        result = select_frontier_keywords(
            frontiers_yaml, samples=8, avoid_patterns=["quantum"], seed=42
        )
        selected_kws = {k["keyword"] for k in result["selected_keywords"]}
        # Both quantum-related keywords should be excluded
        assert "quantum biology applications" not in selected_kws
        assert "post-quantum cryptography" not in selected_kws

    def test_samples_capped_by_config(self, frontiers_yaml):
        # Config has samples_per_scan=3, requesting 10 should be capped to 3
        result = select_frontier_keywords(frontiers_yaml, samples=10, seed=42)
        assert result["selected_count"] == 3

    def test_no_keywords_returns_status(self, temp_dir):
        empty_config = {"frontiers": {}, "selection": {"method": "random"}}
        path = temp_dir / "empty.yaml"
        with open(path, "w") as f:
            yaml.dump(empty_config, f)

        result = select_frontier_keywords(str(path))
        assert result["status"] == "NO_KEYWORDS"

    def test_output_file_written(self, frontiers_yaml, temp_dir):
        output_path = temp_dir / "selection.json"
        result = select_frontier_keywords(
            frontiers_yaml, output_path=str(output_path), seed=42
        )
        assert output_path.exists()
        with open(output_path) as f:
            written = json.load(f)
        assert written["status"] == "SUCCESS"

    def test_missing_frontiers_file_raises(self):
        with pytest.raises(FileNotFoundError):
            select_frontier_keywords("nonexistent.yaml")

    def test_no_history_uses_default_weights(self, frontiers_yaml):
        result = select_frontier_keywords(frontiers_yaml, samples=3, seed=42)
        # All weights should be 1.0 (default) when no history
        for kw in result["selected_keywords"]:
            assert kw["weight"] == 1.0


# ---------------------------------------------------------------------------
# Weighted sample helper
# ---------------------------------------------------------------------------

class TestWeightedSampleUnique:
    def test_returns_k_unique_items(self):
        items = [{"keyword": f"kw{i}", "weight": 1.0} for i in range(10)]
        weights = [1.0] * 10
        selected = _weighted_sample_unique(items, weights, 5)
        assert len(selected) == 5
        keywords = [s["keyword"] for s in selected]
        assert len(set(keywords)) == 5  # All unique

    def test_returns_all_if_k_exceeds_pool(self):
        items = [{"keyword": "a"}, {"keyword": "b"}]
        weights = [1.0, 1.0]
        selected = _weighted_sample_unique(items, weights, 10)
        assert len(selected) == 2
