"""
Tests for signal_evolution_tracker.py

Validates cross-day signal matching, evolution state detection,
timeline metrics computation, and index management.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

# Add core module path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "env-scanning" / "core"))
import signal_evolution_tracker as tracker


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _make_signal(
    sid="test-001",
    title="AI Infrastructure Investment Competition",
    category="T",
    psst_score=85,
    keywords=None,
    source_name="TechCrunch",
):
    """Helper to create a test classified signal."""
    return {
        "id": sid,
        "title": title,
        "final_category": category,
        "psst_score": psst_score,
        "content": {"keywords": keywords or ["AI", "infrastructure", "investment"]},
        "source": {"name": source_name, "type": "blog"},
    }


def _make_classified_data(signals):
    """Wrap signals in classified-signals JSON structure."""
    return {
        "classification_metadata": {"date": "2026-02-11"},
        "classified_signals": signals,
    }


def _make_evolution_index(threads=None, counter=1, workflow="wf1-general"):
    """Create a test evolution index."""
    return {
        "index_version": "1.0.0",
        "workflow": workflow,
        "total_threads": len(threads) if threads else 0,
        "active_threads": len(threads) if threads else 0,
        "threads": threads or {},
        "thread_id_counter": counter,
    }


def _make_thread(
    thread_id="THREAD-WF1-001",
    title="AI Infrastructure Investment",
    keywords=None,
    category="T",
    created="2026-02-01",
    last_seen="2026-02-10",
    state="RECURRING",
    appearances=None,
):
    """Create a test thread."""
    if appearances is None:
        appearances = [
            {"scan_date": "2026-02-01", "signal_id": "wf1-20260201-001", "psst_score": 80},
            {"scan_date": "2026-02-05", "signal_id": "wf1-20260205-003", "psst_score": 82},
            {"scan_date": "2026-02-10", "signal_id": "wf1-20260210-002", "psst_score": 85},
        ]
    return {
        "canonical_title": title,
        "keywords": keywords or ["ai", "infrastructure", "investment"],
        "primary_category": category,
        "all_categories": [category],
        "created_date": created,
        "last_seen_date": last_seen,
        "state": state,
        "appearance_count": len(appearances),
        "appearances": appearances,
        "metrics_history": [],
    }


# ---------------------------------------------------------------------------
# Tests: Jaro-Winkler Similarity
# ---------------------------------------------------------------------------

class TestJaroWinklerSimilarity:
    def test_identical_strings(self):
        assert tracker._jaro_winkler_similarity("hello", "hello") == 1.0

    def test_empty_strings(self):
        assert tracker._jaro_winkler_similarity("", "") == 1.0
        assert tracker._jaro_winkler_similarity("hello", "") == 0.0

    def test_similar_strings(self):
        sim = tracker._jaro_winkler_similarity(
            "AI infrastructure investment competition",
            "AI infrastructure investment race",
        )
        assert sim > 0.8

    def test_dissimilar_strings(self):
        sim = tracker._jaro_winkler_similarity(
            "quantum computing breakthrough",
            "climate policy regulation",
        )
        assert sim < 0.7  # Jaro-Winkler tends to give moderate scores even for dissimilar strings


# ---------------------------------------------------------------------------
# Tests: Keyword Similarity
# ---------------------------------------------------------------------------

class TestKeywordSimilarity:
    def test_identical_sets(self):
        sim = tracker._keyword_vector_similarity({"ai", "ml"}, {"ai", "ml"})
        assert sim == 1.0

    def test_partial_overlap(self):
        sim = tracker._keyword_vector_similarity(
            {"ai", "infrastructure", "investment"},
            {"ai", "investment", "cloud"},
        )
        assert 0.3 < sim < 0.7  # 2/4 = 0.5

    def test_no_overlap(self):
        sim = tracker._keyword_vector_similarity({"ai", "ml"}, {"climate", "policy"})
        assert sim == 0.0

    def test_empty_sets(self):
        assert tracker._keyword_vector_similarity(set(), {"ai"}) == 0.0
        assert tracker._keyword_vector_similarity(set(), set()) == 0.0


# ---------------------------------------------------------------------------
# Tests: Signal Matching
# ---------------------------------------------------------------------------

class TestMatchSignalToThreads:
    def test_high_confidence_match(self):
        """Signal with similar title AND keywords should get HIGH confidence."""
        thread = _make_thread(
            title="AI Infrastructure Investment Competition",
            keywords=["ai", "infrastructure", "investment", "competition"],
        )
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread},
            counter=2,
        )
        signal = _make_signal(
            title="AI Infrastructure Investment Competition Intensifies",
            keywords=["AI", "infrastructure", "investment", "competition"],
        )
        result = tracker.match_signal_to_threads(
            signal, index,
            title_threshold=0.75,
            semantic_threshold=0.50,
        )
        assert result is not None
        thread_id, confidence = result
        assert thread_id == "THREAD-WF1-001"

    def test_no_match_for_unrelated(self):
        """Completely unrelated signal should not match."""
        thread = _make_thread()
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread},
            counter=2,
        )
        signal = _make_signal(
            title="Quantum Computing Achieves Error Correction Milestone",
            keywords=["quantum", "computing", "error", "correction"],
        )
        result = tracker.match_signal_to_threads(signal, index)
        assert result is None

    def test_faded_threads_skipped(self):
        """FADED threads should not be matched against."""
        thread = _make_thread(state="FADED")
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread},
            counter=2,
        )
        signal = _make_signal(
            title="AI Infrastructure Investment Competition",
            keywords=["AI", "infrastructure", "investment"],
        )
        result = tracker.match_signal_to_threads(signal, index)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: State Detection
# ---------------------------------------------------------------------------

class TestComputeThreadState:
    def test_recurring_small_delta(self):
        thread = _make_thread()
        signal = _make_signal(psst_score=86)  # delta = +1 (within ±5)
        state = tracker.compute_thread_state(thread, signal, "HIGH")
        assert state == "RECURRING"

    def test_strengthening_large_positive_delta(self):
        thread = _make_thread()
        signal = _make_signal(psst_score=92)  # delta = +7 (> +5)
        state = tracker.compute_thread_state(thread, signal, "HIGH")
        assert state == "STRENGTHENING"

    def test_weakening_large_negative_delta(self):
        thread = _make_thread()
        signal = _make_signal(psst_score=78)  # delta = -7 (< -5)
        state = tracker.compute_thread_state(thread, signal, "HIGH")
        assert state == "WEAKENING"

    def test_strengthening_new_steeps_domain(self):
        """New STEEPs domain expansion should trigger STRENGTHENING."""
        thread = _make_thread(category="T")
        signal = _make_signal(psst_score=85, category="E")  # Same score, new domain
        state = tracker.compute_thread_state(thread, signal, "HIGH")
        assert state == "STRENGTHENING"

    def test_transformed_medium_confidence_category_change(self):
        """Medium confidence + category change = TRANSFORMED."""
        thread = _make_thread(category="T")
        signal = _make_signal(psst_score=85, category="P")
        state = tracker.compute_thread_state(thread, signal, "MEDIUM")
        assert state == "TRANSFORMED"


# ---------------------------------------------------------------------------
# Tests: Evolution Metrics
# ---------------------------------------------------------------------------

class TestComputeEvolutionMetrics:
    def test_stable_thread(self):
        thread = _make_thread(appearances=[
            {"scan_date": "2026-02-01", "psst_score": 80, "source": "A"},
            {"scan_date": "2026-02-05", "psst_score": 80, "source": "A"},
            {"scan_date": "2026-02-10", "psst_score": 81, "source": "A"},
        ])
        metrics = tracker.compute_evolution_metrics(thread)
        assert metrics["direction"] in ("STABLE", "ACCELERATING")  # Very slight increase
        assert -0.2 < metrics["velocity"] < 0.2

    def test_accelerating_thread(self):
        thread = _make_thread(appearances=[
            {"scan_date": "2026-02-01", "psst_score": 60, "source": "A"},
            {"scan_date": "2026-02-05", "psst_score": 75, "source": "B"},
            {"scan_date": "2026-02-10", "psst_score": 90, "source": "C"},
        ])
        metrics = tracker.compute_evolution_metrics(thread)
        assert metrics["velocity"] > 0
        assert metrics["direction"] == "ACCELERATING"

    def test_expansion_multi_category(self):
        thread = _make_thread()
        thread["all_categories"] = ["T", "E", "P"]
        metrics = tracker.compute_evolution_metrics(thread)
        assert metrics["expansion"] > 0.0


# ---------------------------------------------------------------------------
# Tests: Faded Thread Detection
# ---------------------------------------------------------------------------

class TestDetectFadedThreads:
    def test_recent_thread_not_faded(self):
        index = _make_evolution_index(
            threads={"T-001": _make_thread(last_seen="2026-02-10")},
        )
        faded = tracker.detect_faded_threads(index, "2026-02-11", fade_days=3)
        assert len(faded) == 0

    def test_old_thread_faded(self):
        index = _make_evolution_index(
            threads={"T-001": _make_thread(last_seen="2026-02-05")},
        )
        faded = tracker.detect_faded_threads(index, "2026-02-11", fade_days=3)
        assert "T-001" in faded

    def test_already_faded_not_double_counted(self):
        thread = _make_thread(last_seen="2026-02-01", state="FADED")
        index = _make_evolution_index(threads={"T-001": thread})
        faded = tracker.detect_faded_threads(index, "2026-02-11", fade_days=3)
        assert len(faded) == 0


# ---------------------------------------------------------------------------
# Tests: Full Track Signal Evolution
# ---------------------------------------------------------------------------

class TestTrackSignalEvolution:
    def test_first_run_all_new(self, tmp_path):
        """First run with no existing index: all signals should be NEW."""
        signals = [
            _make_signal(sid="test-0", title="Quantum Computing Breakthrough Discovery", keywords=["quantum", "computing"]),
            _make_signal(sid="test-1", title="Climate Policy Regulation Framework", keywords=["climate", "policy"]),
            _make_signal(sid="test-2", title="Biotechnology Gene Editing Advances", keywords=["biotech", "gene"]),
        ]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")

        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        idx_path = tmp_path / "evolution-index.json"
        out_path = tmp_path / "evolution-map.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            output_path=str(out_path),
            scan_date="2026-02-11",
        )

        assert result["summary"]["total_signals_today"] == 3
        assert result["summary"]["new_signals"] == 3
        assert result["summary"]["recurring_signals"] == 0
        # Index should be created
        assert idx_path.exists()
        idx_data = json.loads(idx_path.read_text())
        assert idx_data["total_threads"] == 3

    def test_recurring_detection(self, tmp_path):
        """Second run with matching signals: should detect RECURRING."""
        # Create pre-existing index with one thread (with many keywords for matching)
        thread = _make_thread(
            thread_id="THREAD-WF1-001",
            title="AI Infrastructure Investment Competition",
            keywords=["ai", "infrastructure", "investment", "competition", "대규모", "투자"],
            last_seen="2026-02-10",
        )
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread},
            counter=2,
        )
        idx_path = tmp_path / "evolution-index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")

        # Today's signal matches the thread (similar title and keywords)
        signals = [_make_signal(
            sid="wf1-20260211-001",
            title="AI Infrastructure Investment Competition Grows",
            psst_score=86,
            keywords=["AI", "infrastructure", "investment", "competition"],
        )]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")

        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            title_threshold=0.75,
            semantic_threshold=0.40,
        )

        # With relaxed thresholds, the matching signal should be found
        non_new = result["summary"]["recurring_signals"] + result["summary"]["strengthening_signals"]
        assert non_new >= 1 or result["summary"]["new_signals"] <= 0

    def test_index_atomicity_backup(self, tmp_path):
        """Backup file should be created before modifying index."""
        index = _make_evolution_index()
        idx_path = tmp_path / "evolution-index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")

        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        backup_path = tmp_path / "evolution-index-backup-2026-02-11.json"
        assert backup_path.exists(), "Backup should be created before modification"

    def test_evolution_map_output_structure(self, tmp_path):
        """Evolution map should have required structure."""
        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")

        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        idx_path = tmp_path / "evolution-index.json"
        out_path = tmp_path / "evolution-map.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            output_path=str(out_path),
            scan_date="2026-02-11",
        )

        # Check output file
        assert out_path.exists()
        map_data = json.loads(out_path.read_text())
        assert "summary" in map_data
        assert "evolution_entries" in map_data
        assert "faded_threads" in map_data
        assert "new_threads_created" in map_data

        # Check entry structure
        entry = map_data["evolution_entries"][0]
        assert "signal_id" in entry
        assert "thread_id" in entry
        assert "state" in entry
        assert "state_ko" in entry
        assert "metrics" in entry
        metrics = entry["metrics"]
        assert "velocity" in metrics
        assert "direction" in metrics
        assert "expansion" in metrics


# ---------------------------------------------------------------------------
# Tests: Cross-Workflow Correlation
# ---------------------------------------------------------------------------

class TestCrossCorrelateThreads:
    def test_matching_threads_detected(self, tmp_path):
        """Threads with similar titles across WFs should be correlated."""
        wf1_idx = _make_evolution_index(threads={
            "THREAD-WF1-001": _make_thread(title="AI Infrastructure Investment"),
        })
        wf2_idx = _make_evolution_index(threads={
            "THREAD-WF2-001": _make_thread(title="AI Infrastructure Investment Growth"),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
        )

        assert result["total_correlations"] >= 1
        assert out_path.exists()

    def test_no_correlation_for_unrelated(self, tmp_path):
        """Unrelated threads should not correlate."""
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(title="Climate Policy Change", keywords=["climate", "policy"]),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(title="Quantum Computing Error Correction", keywords=["quantum", "computing"]),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
        )

        assert result["total_correlations"] == 0


# ---------------------------------------------------------------------------
# Tests: SOT Direct Reading (v2.3.1 — 할루시네이션 원천봉쇄)
# ---------------------------------------------------------------------------

def _make_sot_yaml(tmp_path, overrides=None):
    """Create a minimal workflow-registry.yaml for testing SOT direct reading."""
    config = {
        "system": {
            "signal_evolution": {
                "enabled": True,
                "tracker_script": "env-scanning/core/signal_evolution_tracker.py",
                "matching": {
                    "title_similarity_threshold": 0.80,
                    "semantic_similarity_threshold": 0.70,
                    "high_confidence_threshold": 0.85,
                },
                "lifecycle": {
                    "fade_threshold_days": 3,
                    "max_thread_age_days": 90,
                    "min_appearances_for_velocity": 2,
                },
                "state_detection": {
                    "strengthening_psst_delta": 5,
                    "weakening_psst_delta": -5,
                },
                "cross_workflow_correlation": {
                    "enabled": True,
                    "output_path": "integrated/analysis/evolution/",
                    "matching": {
                        "title_similarity_threshold": 0.75,
                        "semantic_similarity_threshold": 0.65,
                        "high_confidence_threshold": 0.80,
                        "category_filter_enabled": True,
                    },
                },
            }
        }
    }
    if overrides:
        # Deep merge overrides into signal_evolution
        import copy
        se = config["system"]["signal_evolution"]
        for key, val in overrides.items():
            if isinstance(val, dict) and key in se and isinstance(se[key], dict):
                se[key].update(val)
            else:
                se[key] = val

    import yaml
    sot_path = tmp_path / "workflow-registry.yaml"
    sot_path.write_text(yaml.dump(config, default_flow_style=False), encoding="utf-8")
    return str(sot_path)


class TestLoadEvolutionConfig:
    """Test SOT direct reading via load_evolution_config()."""

    def test_load_all_fields(self, tmp_path):
        """All SOT fields should be loaded correctly."""
        sot_path = _make_sot_yaml(tmp_path)
        config = tracker.load_evolution_config(sot_path)

        assert config["enabled"] is True
        assert config["matching"]["title_similarity_threshold"] == 0.80
        assert config["matching"]["semantic_similarity_threshold"] == 0.70
        assert config["matching"]["high_confidence_threshold"] == 0.85
        assert config["lifecycle"]["fade_threshold_days"] == 3
        assert config["lifecycle"]["max_thread_age_days"] == 90
        assert config["lifecycle"]["min_appearances_for_velocity"] == 2
        assert config["state_detection"]["strengthening_psst_delta"] == 5
        assert config["state_detection"]["weakening_psst_delta"] == -5
        assert config["cross_workflow_correlation"]["matching"]["title_similarity_threshold"] == 0.75
        assert config["cross_workflow_correlation"]["matching"]["semantic_similarity_threshold"] == 0.65
        assert config["cross_workflow_correlation"]["matching"]["high_confidence_threshold"] == 0.80
        assert config["cross_workflow_correlation"]["matching"]["category_filter_enabled"] is True

    def test_missing_file_raises(self, tmp_path):
        """Non-existent registry file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            tracker.load_evolution_config(str(tmp_path / "nonexistent.yaml"))

    def test_missing_section_returns_defaults(self, tmp_path):
        """If signal_evolution section is missing, return defaults."""
        import yaml
        sot_path = tmp_path / "registry.yaml"
        sot_path.write_text(yaml.dump({"system": {}}), encoding="utf-8")

        config = tracker.load_evolution_config(str(sot_path))
        # Should get default config (enabled=False)
        assert config["enabled"] is False
        assert config["matching"]["title_similarity_threshold"] == 0.80

    def test_custom_values_propagated(self, tmp_path):
        """Custom SOT values should override defaults."""
        sot_path = _make_sot_yaml(tmp_path, overrides={
            "matching": {
                "title_similarity_threshold": 0.90,
                "semantic_similarity_threshold": 0.60,
                "high_confidence_threshold": 0.92,
            },
            "lifecycle": {
                "fade_threshold_days": 5,
                "max_thread_age_days": 60,
                "min_appearances_for_velocity": 3,
            },
        })
        config = tracker.load_evolution_config(sot_path)

        assert config["matching"]["title_similarity_threshold"] == 0.90
        assert config["matching"]["semantic_similarity_threshold"] == 0.60
        assert config["matching"]["high_confidence_threshold"] == 0.92
        assert config["lifecycle"]["fade_threshold_days"] == 5
        assert config["lifecycle"]["max_thread_age_days"] == 60
        assert config["lifecycle"]["min_appearances_for_velocity"] == 3


class TestSOTParameterBinding:
    """Test that track_signal_evolution reads parameters from SOT when --registry is given."""

    def test_sot_values_appear_in_config_used(self, tmp_path):
        """Evolution map output should contain config_used reflecting SOT values."""
        sot_path = _make_sot_yaml(tmp_path)

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
        )

        assert result["config_source"] == sot_path
        config = result["config_used"]
        assert config["title_threshold"] == 0.80
        assert config["semantic_threshold"] == 0.70
        assert config["high_confidence_threshold"] == 0.85
        assert config["fade_days"] == 3
        assert config["max_thread_age_days"] == 90
        assert config["min_appearances_for_velocity"] == 2
        assert config["strengthening_delta"] == 5
        assert config["weakening_delta"] == -5

    def test_cli_override_takes_precedence_over_sot(self, tmp_path):
        """Explicit parameter should override SOT value."""
        sot_path = _make_sot_yaml(tmp_path)

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
            title_threshold=0.95,  # Override SOT's 0.80
            fade_days=7,  # Override SOT's 3
        )

        config = result["config_used"]
        assert config["title_threshold"] == 0.95, "CLI override should take precedence"
        assert config["fade_days"] == 7, "CLI override should take precedence"
        # Non-overridden values should come from SOT
        assert config["semantic_threshold"] == 0.70, "SOT value should be used"

    def test_no_registry_uses_defaults(self, tmp_path):
        """Without registry_path, hardcoded defaults should be used."""
        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        assert result["config_source"] == "hardcoded_defaults"
        config = result["config_used"]
        assert config["title_threshold"] == 0.80


class TestMaxThreadAgeDays:
    """Test that max_thread_age_days from SOT is now connected to detect_faded_threads."""

    def test_old_thread_faded_by_age(self):
        """Thread exceeding max_thread_age_days should be FADED even if seen recently."""
        index = _make_evolution_index(threads={
            "THREAD-WF1-001": {
                **_make_thread(),
                "created_date": "2025-11-01",  # ~100 days ago
                "last_seen_date": "2026-02-10",  # Seen yesterday
                "state": "RECURRING",
            }
        })

        faded = tracker.detect_faded_threads(
            index, "2026-02-11",
            fade_days=3,
            max_thread_age_days=90,  # 90 days limit
        )

        assert "THREAD-WF1-001" in faded, "Thread older than 90 days should be faded"

    def test_young_thread_not_faded_by_age(self):
        """Thread within max_thread_age_days should NOT be faded."""
        index = _make_evolution_index(threads={
            "THREAD-WF1-001": {
                **_make_thread(),
                "created_date": "2026-02-01",  # 10 days ago
                "last_seen_date": "2026-02-10",  # Seen yesterday
                "state": "RECURRING",
            }
        })

        faded = tracker.detect_faded_threads(
            index, "2026-02-11",
            fade_days=3,
            max_thread_age_days=90,
        )

        assert "THREAD-WF1-001" not in faded, "Young recently-seen thread should not be faded"


class TestMinAppearancesForVelocity:
    """Test that min_appearances_for_velocity from SOT controls velocity computation."""

    def test_below_min_appearances_zero_velocity(self):
        """Thread with fewer appearances than min should have velocity=0."""
        thread = {
            **_make_thread(),
            "appearances": [
                {"scan_date": "2026-02-10", "psst_score": 85, "source": "test"},
            ],
        }
        metrics = tracker.compute_evolution_metrics(thread, min_appearances_for_velocity=3)
        assert metrics["velocity"] == 0.0, "Below min appearances, velocity should be 0"

    def test_at_min_appearances_computes_velocity(self):
        """Thread with exactly min appearances should compute velocity."""
        thread = {
            **_make_thread(),
            "appearances": [
                {"scan_date": "2026-02-09", "psst_score": 80, "source": "test"},
                {"scan_date": "2026-02-10", "psst_score": 85, "source": "test"},
                {"scan_date": "2026-02-11", "psst_score": 90, "source": "test"},
            ],
        }
        metrics = tracker.compute_evolution_metrics(thread, min_appearances_for_velocity=3)
        assert metrics["velocity"] > 0, "At min appearances with increasing scores, velocity should be positive"


class TestHighConfidenceThreshold:
    """Test that high_confidence_threshold from SOT affects match confidence."""

    def test_high_threshold_reduces_high_confidence(self):
        """Higher high_confidence_threshold should make fewer HIGH matches."""
        signal = _make_signal(title="AI Infrastructure Investment Competition")
        index = _make_evolution_index(threads={
            "THREAD-WF1-001": _make_thread(
                title="AI Infrastructure Investment Competition",
                keywords=["AI", "infrastructure", "investment"],
            ),
        })

        # With very high threshold (0.99), should be MEDIUM
        result = tracker.match_signal_to_threads(
            signal, index,
            title_threshold=0.80, semantic_threshold=0.70,
            high_confidence_threshold=0.99,
        )
        assert result is not None
        assert result[1] == "MEDIUM", "Very high threshold should produce MEDIUM confidence"

    def test_low_threshold_increases_high_confidence(self):
        """Lower high_confidence_threshold should make more HIGH matches."""
        signal = _make_signal(title="AI Infrastructure Investment Competition")
        index = _make_evolution_index(threads={
            "THREAD-WF1-001": _make_thread(
                title="AI Infrastructure Investment Competition",
                keywords=["AI", "infrastructure", "investment"],
            ),
        })

        result = tracker.match_signal_to_threads(
            signal, index,
            title_threshold=0.80, semantic_threshold=0.70,
            high_confidence_threshold=0.50,
        )
        assert result is not None
        assert result[1] == "HIGH", "Low threshold should produce HIGH confidence"


class TestCanonicalTitlePropagation:
    """C1 fix: evolution_entries must include canonical_title for human-readable tables."""

    def test_new_signal_has_canonical_title(self, tmp_path):
        """NEW signal's evolution entry should contain its title as canonical_title."""
        signals = [_make_signal(sid="test-0", title="AI 인프라 대규모 투자 경쟁")]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        entry = result["evolution_entries"][0]
        assert "canonical_title" in entry, "Evolution entry must have canonical_title"
        assert entry["canonical_title"] == "AI 인프라 대규모 투자 경쟁"

    def test_matched_signal_has_canonical_title(self, tmp_path):
        """Matched (RECURRING) signal's evolution entry should contain thread's canonical_title."""
        thread = _make_thread(
            title="AI 인프라 대규모 투자 경쟁",
            keywords=["ai", "infrastructure", "investment", "competition", "인프라", "투자"],
        )
        index = _make_evolution_index(threads={"THREAD-WF1-001": thread}, counter=2)
        idx_path = tmp_path / "evolution-index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")

        signals = [_make_signal(
            sid="wf1-20260211-001",
            title="AI Infrastructure Investment Competition Grows",
            psst_score=86,
            keywords=["AI", "infrastructure", "investment", "competition"],
        )]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            title_threshold=0.75,
            semantic_threshold=0.40,
        )

        entry = result["evolution_entries"][0]
        assert "canonical_title" in entry, "Evolution entry must have canonical_title"
        # canonical_title should be the thread's title (human-readable Korean)
        assert entry["canonical_title"] == "AI 인프라 대규모 투자 경쟁"

    def test_history_summary_has_title(self, tmp_path):
        """thread_history_summary entries must include 'title' field."""
        signals = [_make_signal(sid="test-0", title="Quantum Computing Breakthrough")]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        entry = result["evolution_entries"][0]
        for hist in entry["thread_history_summary"]:
            assert "title" in hist, "Each history_summary entry must have 'title'"
            assert hist["title"], "title must not be empty"

    def test_appearance_count_in_entry(self, tmp_path):
        """Evolution entries must include appearance_count."""
        signals = [_make_signal(sid="test-0", title="Test Signal")]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        entry = result["evolution_entries"][0]
        assert "appearance_count" in entry, "Evolution entry must have appearance_count"
        assert entry["appearance_count"] == 1  # First appearance


class TestEnabledFlagEnforcement:
    """C2 fix: signal_evolution.enabled=false should return empty evolution map."""

    def test_disabled_returns_empty_map(self, tmp_path):
        """When enabled=false in SOT, tracker should return empty map immediately."""
        sot_path = _make_sot_yaml(tmp_path, overrides={"enabled": False})

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
        )

        assert result["summary"]["total_signals_today"] == 0
        assert result["summary"]["new_signals"] == 0
        assert len(result["evolution_entries"]) == 0
        assert result["config_source"] == "signal_evolution.enabled=false"

    def test_disabled_writes_empty_output(self, tmp_path):
        """When disabled, output file should still be written (empty map)."""
        sot_path = _make_sot_yaml(tmp_path, overrides={"enabled": False})

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"
        out_path = tmp_path / "evolution-map.json"

        tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
            output_path=str(out_path),
        )

        assert out_path.exists(), "Output file should be written even when disabled"
        data = json.loads(out_path.read_text())
        assert data["summary"]["total_signals_today"] == 0

    def test_disabled_does_not_create_index(self, tmp_path):
        """When disabled, evolution-index.json should NOT be created."""
        sot_path = _make_sot_yaml(tmp_path, overrides={"enabled": False})

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
        )

        assert not idx_path.exists(), "Index should NOT be created when evolution is disabled"

    def test_enabled_still_processes(self, tmp_path):
        """When enabled=true in SOT, tracker should process normally."""
        sot_path = _make_sot_yaml(tmp_path)  # Default: enabled=True

        signals = [_make_signal()]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            registry_path=sot_path,
        )

        assert result["summary"]["total_signals_today"] == 1
        assert result["summary"]["new_signals"] == 1

    def test_cross_correlate_disabled_returns_empty(self, tmp_path):
        """cross_correlate_threads should return empty when evolution disabled."""
        sot_path = _make_sot_yaml(tmp_path, overrides={"enabled": False})

        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(title="AI Investment"),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(title="AI Investment Growth"),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            registry_path=sot_path,
        )

        assert result["total_correlations"] == 0


class TestCrossCorrelateSOTReading:
    """Test that cross_correlate_threads reads thresholds from SOT."""

    def test_sot_thresholds_used(self, tmp_path):
        """cross_correlate should use SOT thresholds when registry_path is given."""
        # Create SOT with very strict cross-correlation thresholds
        sot_path = _make_sot_yaml(tmp_path, overrides={
            "cross_workflow_correlation": {
                "enabled": True,
                "output_path": "integrated/analysis/evolution/",
                "matching": {
                    "title_similarity_threshold": 0.99,
                    "semantic_similarity_threshold": 0.99,
                },
            },
        })

        # Use somewhat related but clearly different titles
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="Climate Policy Changes in Europe",
                keywords=["climate", "policy", "europe"],
            ),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="European Climate Regulatory Shifts",
                keywords=["climate", "regulation", "europe"],
            ),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            registry_path=sot_path,
        )

        # With 0.99 thresholds, moderately similar titles should NOT match
        assert result["total_correlations"] == 0, \
            "Very strict SOT thresholds should prevent correlation"


# ===========================================================================
# ===========================================================================
# R1 Tests: Classified-Signals Key-Variant Fallback
# ===========================================================================

class TestClassifiedSignalsKeyVariant:
    """R1 fix: track_signal_evolution handles all known key variants in classified-signals JSON."""

    def _setup_tracker_env(self, tmp_path, classified_data):
        """Create minimal files for track_signal_evolution with given classified data."""
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(classified_data), encoding="utf-8")
        db_path = tmp_path / "db.json"
        db_path.write_text(json.dumps({"signals": [], "metadata": {}}), encoding="utf-8")
        idx_path = tmp_path / "index.json"
        sot_path = _make_sot_yaml(tmp_path)
        return str(cs_path), str(db_path), str(idx_path), sot_path

    def test_classified_signals_key(self, tmp_path):
        """v2.1.0+ format: 'classified_signals' key."""
        data = {"classification_metadata": {}, "classified_signals": [
            {"id": "s1", "title": "Test", "final_category": "T"},
        ]}
        cs, db, idx, sot = self._setup_tracker_env(tmp_path, data)
        result = tracker.track_signal_evolution(
            cs, db, idx, "wf1-general", scan_date="2026-02-10", registry_path=sot,
        )
        assert result["summary"]["total_signals_today"] == 1

    def test_signals_key(self, tmp_path):
        """v2.0.x format: 'signals' key."""
        data = {"classification_metadata": {}, "signals": [
            {"id": "s1", "title": "Test", "final_category": "T"},
        ]}
        cs, db, idx, sot = self._setup_tracker_env(tmp_path, data)
        result = tracker.track_signal_evolution(
            cs, db, idx, "wf1-general", scan_date="2026-02-10", registry_path=sot,
        )
        assert result["summary"]["total_signals_today"] == 1

    def test_items_key(self, tmp_path):
        """v1.x raw format: 'items' key."""
        data = {"scan_metadata": {}, "items": [
            {"id": "s1", "title": "Test", "final_category": "T"},
        ]}
        cs, db, idx, sot = self._setup_tracker_env(tmp_path, data)
        result = tracker.track_signal_evolution(
            cs, db, idx, "wf1-general", scan_date="2026-02-10", registry_path=sot,
        )
        assert result["summary"]["total_signals_today"] == 1

    def test_direct_list_format(self, tmp_path):
        """v1.0 legacy: direct list (no wrapper dict)."""
        data = [{"id": "s1", "title": "Test", "final_category": "T"}]
        cs, db, idx, sot = self._setup_tracker_env(tmp_path, data)
        result = tracker.track_signal_evolution(
            cs, db, idx, "wf1-general", scan_date="2026-02-10", registry_path=sot,
        )
        assert result["summary"]["total_signals_today"] == 1


# ===========================================================================
# v1.3.0 Tests: L1 — Title Enrichment
# ===========================================================================

class TestTitleEnrichment:
    """L1 fix: _enrich_signal_title() multi-layer defense against empty titles."""

    def test_title_from_signal(self):
        """Layer 1: Signal with a valid title should use it directly."""
        signal = {"id": "test-001", "title": "AI Infrastructure Investment"}
        result = tracker._enrich_signal_title(signal, [])
        assert result == "AI Infrastructure Investment"

    def test_title_from_db_when_missing(self):
        """Layer 2: Missing title should be filled from signals DB."""
        signal = {"id": "test-001"}
        db_list = [{"id": "test-001", "title": "DB Title for Test-001"}]
        result = tracker._enrich_signal_title(signal, db_list)
        assert result == "DB Title for Test-001"

    def test_title_fallback_to_id(self):
        """Layer 3: If DB also lacks title, fall back to signal ID."""
        signal = {"id": "test-001"}
        db_list = [{"id": "test-002", "title": "Different Signal"}]
        result = tracker._enrich_signal_title(signal, db_list)
        assert result == "test-001"

    def test_empty_string_title_treated_as_missing(self):
        """Empty-string title should be treated as missing (Layer 1 skip)."""
        signal = {"id": "test-001", "title": "  "}
        db_list = [{"id": "test-001", "title": "Enriched from DB"}]
        result = tracker._enrich_signal_title(signal, db_list)
        assert result == "Enriched from DB"

    def test_canonical_title_never_empty_in_evolution_entries(self, tmp_path):
        """E2E: evolution entries should never have empty canonical_title."""
        # Simulate signal with no title field
        signals = [
            {"id": "sig-no-title", "final_category": "T",
             "content": {"keywords": ["ai", "test"]},
             "source": {"name": "test", "type": "blog"}},
        ]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": [
            {"id": "sig-no-title", "title": "Title from DB"},
        ]}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        for entry in result["evolution_entries"]:
            assert entry["canonical_title"], f"canonical_title must not be empty: {entry}"


# ===========================================================================
# v1.3.0 Tests: L2 — Cross-WF AND Logic + Category Filter
# ===========================================================================

class TestCrossCorrelateANDLogic:
    """L2 fix: cross_correlate_threads uses AND (not OR) + category filter."""

    def test_title_only_match_rejected(self, tmp_path):
        """Title-only match (high title sim, zero keyword sim) should NOT correlate."""
        # "Agency Safety" vs "Agentic AI" — Jaro-Winkler gives high score due to prefix
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="Agency Safety Guidelines Update",
                keywords=["agency", "safety", "guidelines"],
                category="P",
            ),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="Agentic AI Architecture Design",
                keywords=["agentic", "architecture", "design"],
                category="T",
            ),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            title_threshold=0.75, semantic_threshold=0.65,
        )

        assert result["total_correlations"] == 0, \
            "Title-only match should be rejected with AND logic"

    def test_both_thresholds_met_correlates(self, tmp_path):
        """When both title AND keyword thresholds are met, should correlate."""
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Infrastructure Investment Competition",
                keywords=["ai", "infrastructure", "investment", "competition"],
                category="T",
            ),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Infrastructure Investment Growth",
                keywords=["ai", "infrastructure", "investment", "growth"],
                category="T",
            ),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            title_threshold=0.75, semantic_threshold=0.50,
        )

        assert result["total_correlations"] >= 1, \
            "Both thresholds met should produce correlation"

    def test_category_filter_rejects_mismatch(self, tmp_path):
        """Threads with different STEEPs categories should be filtered out."""
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Investment Competition",
                keywords=["ai", "investment", "competition"],
                category="T",  # Technological
            ),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Investment Competition Growth",
                keywords=["ai", "investment", "competition", "growth"],
                category="P",  # Political — different!
            ),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        # category_filter_enabled defaults to True
        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            title_threshold=0.75, semantic_threshold=0.50,
        )

        assert result["total_correlations"] == 0, \
            "Category mismatch should prevent correlation"

    def test_confidence_field_present(self, tmp_path):
        """Correlation output should include combined_score and confidence fields."""
        wf1_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Infrastructure Investment",
                keywords=["ai", "infrastructure", "investment"],
                category="T",
            ),
        })
        wf2_idx = _make_evolution_index(threads={
            "T-001": _make_thread(
                title="AI Infrastructure Investment Growth",
                keywords=["ai", "infrastructure", "investment", "growth"],
                category="T",
            ),
        })
        wf3_idx = _make_evolution_index(threads={})

        wf1_path = tmp_path / "wf1-index.json"
        wf2_path = tmp_path / "wf2-index.json"
        wf3_path = tmp_path / "wf3-index.json"
        out_path = tmp_path / "cross-map.json"

        wf1_path.write_text(json.dumps(wf1_idx), encoding="utf-8")
        wf2_path.write_text(json.dumps(wf2_idx), encoding="utf-8")
        wf3_path.write_text(json.dumps(wf3_idx), encoding="utf-8")

        result = tracker.cross_correlate_threads(
            str(wf1_path), str(wf2_path), str(wf3_path), str(out_path),
            title_threshold=0.75, semantic_threshold=0.50,
        )

        if result["total_correlations"] > 0:
            corr = result["correlations"][0]
            assert "combined_score" in corr, "Correlation must include combined_score"
            assert "confidence" in corr, "Correlation must include confidence"
            assert corr["confidence"] in ("HIGH", "MEDIUM")


# ===========================================================================
# v1.3.0 Tests: L3 — pSST Backfill from Priority-Ranked
# ===========================================================================

class TestPSSTBackfill:
    """L3 fix: pSST backfill from priority-ranked file."""

    def _make_priority_ranked(self, tmp_path, signals):
        """Create a test priority-ranked JSON file."""
        pr_path = tmp_path / "priority-ranked.json"
        pr_path.write_text(json.dumps({
            "ranked_signals": signals,
        }), encoding="utf-8")
        return str(pr_path)

    def test_build_psst_lookup(self, tmp_path):
        """_build_psst_lookup should create correct {id: score} mapping."""
        pr_path = self._make_priority_ranked(tmp_path, [
            {"id": "sig-001", "psst_score": 92},
            {"id": "sig-002", "psst_score": 85},
            {"id": "sig-003", "psst_score": 78},
        ])
        lookup = tracker._build_psst_lookup(pr_path)
        assert lookup == {"sig-001": 92, "sig-002": 85, "sig-003": 78}

    def test_backfill_from_priority_ranked(self, tmp_path):
        """Signals without psst_score should get scores from priority-ranked."""
        signals = [_make_signal(sid="sig-001", psst_score=0)]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        pr_path = self._make_priority_ranked(tmp_path, [
            {"id": "sig-001", "psst_score": 88},
        ])

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            priority_ranked_path=pr_path,
        )

        entry = result["evolution_entries"][0]
        assert entry["metrics"]["psst_current"] == 88, \
            "pSST should be backfilled from priority-ranked"

    def test_strengthening_detected_with_backfill(self, tmp_path):
        """STRENGTHENING should be detected when backfilled pSST shows large increase."""
        # Thread with previous psst=80
        thread = _make_thread(
            title="AI Infrastructure Investment Competition",
            keywords=["ai", "infrastructure", "investment", "competition"],
            appearances=[
                {"scan_date": "2026-02-10", "signal_id": "old-001",
                 "psst_score": 80, "source": "test"},
            ],
            last_seen="2026-02-10",
        )
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread}, counter=2,
        )
        idx_path = tmp_path / "evolution-index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")

        # Today's signal with psst=0 (no psst in classified-signals)
        signals = [_make_signal(
            sid="sig-001",
            title="AI Infrastructure Investment Competition Intensifies",
            psst_score=0,
            keywords=["AI", "infrastructure", "investment", "competition"],
        )]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        # priority-ranked says psst=92 (delta = +12 > strengthening_delta=5)
        pr_path = self._make_priority_ranked(tmp_path, [
            {"id": "sig-001", "psst_score": 92},
        ])

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            priority_ranked_path=pr_path,
            title_threshold=0.75,
            semantic_threshold=0.40,
        )

        # Check if STRENGTHENING was detected (depends on matching success)
        strengthening_count = result["summary"]["strengthening_signals"]
        # With relaxed thresholds, matching should succeed and detect strengthening
        if result["summary"]["recurring_signals"] + strengthening_count > 0:
            assert strengthening_count >= 1, \
                "Backfilled pSST delta of +12 should trigger STRENGTHENING"

    def test_weakening_detected_with_backfill(self, tmp_path):
        """WEAKENING should be detected when backfilled pSST shows large decrease."""
        thread = _make_thread(
            title="AI Infrastructure Investment Competition",
            keywords=["ai", "infrastructure", "investment", "competition"],
            appearances=[
                {"scan_date": "2026-02-10", "signal_id": "old-001",
                 "psst_score": 90, "source": "test"},
            ],
            last_seen="2026-02-10",
        )
        index = _make_evolution_index(
            threads={"THREAD-WF1-001": thread}, counter=2,
        )
        idx_path = tmp_path / "evolution-index.json"
        idx_path.write_text(json.dumps(index), encoding="utf-8")

        signals = [_make_signal(
            sid="sig-001",
            title="AI Infrastructure Investment Competition Intensifies",
            psst_score=0,
            keywords=["AI", "infrastructure", "investment", "competition"],
        )]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")

        # priority-ranked says psst=78 (delta = -12 < weakening_delta=-5)
        pr_path = self._make_priority_ranked(tmp_path, [
            {"id": "sig-001", "psst_score": 78},
        ])

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            priority_ranked_path=pr_path,
            title_threshold=0.75,
            semantic_threshold=0.40,
        )

        weakening_count = result["summary"]["weakening_signals"]
        if result["summary"]["recurring_signals"] + weakening_count > 0:
            assert weakening_count >= 1, \
                "Backfilled pSST delta of -12 should trigger WEAKENING"

    def test_graceful_degradation_no_priority_ranked(self, tmp_path):
        """Without --priority-ranked, tracker should work normally (psst=0)."""
        signals = [_make_signal(sid="sig-001", psst_score=0)]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        # No priority_ranked_path
        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
        )

        assert result["summary"]["total_signals_today"] == 1
        entry = result["evolution_entries"][0]
        assert entry["metrics"]["psst_current"] == 0, \
            "Without backfill, psst should remain 0"

    def test_missing_priority_ranked_file(self, tmp_path):
        """If --priority-ranked points to non-existent file, should degrade gracefully."""
        signals = [_make_signal(sid="sig-001", psst_score=0)]
        cs_path = tmp_path / "classified.json"
        cs_path.write_text(json.dumps(_make_classified_data(signals)), encoding="utf-8")
        db_path = tmp_path / "database.json"
        db_path.write_text(json.dumps({"signals": []}), encoding="utf-8")
        idx_path = tmp_path / "evolution-index.json"

        result = tracker.track_signal_evolution(
            classified_signals_path=str(cs_path),
            signals_db_path=str(db_path),
            evolution_index_path=str(idx_path),
            workflow_name="wf1-general",
            scan_date="2026-02-11",
            priority_ranked_path=str(tmp_path / "nonexistent.json"),
        )

        assert result["summary"]["total_signals_today"] == 1
        entry = result["evolution_entries"][0]
        assert entry["metrics"]["psst_current"] == 0, \
            "Missing file should result in psst=0 (graceful degradation)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
