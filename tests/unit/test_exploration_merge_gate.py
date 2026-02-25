"""Tests for exploration_merge_gate.py — Atomic signal merge + exhaustive verification."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "env-scanning"))
from core.exploration_merge_gate import (
    merge_exploration_signals,
    verify_exploration_signals,
    _is_exploration_signal,
    _extract_items,
    _get_items_key,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_is_exploration_signal_by_tier(self):
        sig = {"id": "foo", "source": {"tier": "exploration"}}
        assert _is_exploration_signal(sig) is True

    def test_is_exploration_signal_by_id_prefix(self):
        sig = {"id": "explore-20260210-test-001"}
        assert _is_exploration_signal(sig) is True

    def test_is_not_exploration_signal(self):
        sig = {"id": "blog-20260210-001", "source": {"tier": "base"}}
        assert _is_exploration_signal(sig) is False

    def test_extract_items_from_items_key(self):
        data = {"items": [{"id": "1"}, {"id": "2"}]}
        assert len(_extract_items(data)) == 2

    def test_extract_items_from_classified_signals_key(self):
        data = {"classified_signals": [{"id": "1"}]}
        assert len(_extract_items(data)) == 1

    def test_extract_items_from_list(self):
        data = [{"id": "1"}]
        assert len(_extract_items(data)) == 1

    def test_get_items_key(self):
        assert _get_items_key({"items": []}) == "items"
        assert _get_items_key({"classified_signals": []}) == "classified_signals"
        assert _get_items_key({"signals": []}) == "signals"
        assert _get_items_key({"other": []}) is None


# ---------------------------------------------------------------------------
# Merge tests
# ---------------------------------------------------------------------------

class TestMerge:
    def test_merge_appends_to_both_files(self, temp_dir):
        # Setup: raw with 3 signals, classified with 3 signals
        raw_data = {"items": [
            {"id": "blog-001", "title": "A"},
            {"id": "blog-002", "title": "B"},
            {"id": "blog-003", "title": "C"},
        ]}
        cls_data = {"classified_signals": [
            {"id": "blog-001", "title": "A", "category": "T"},
            {"id": "blog-002", "title": "B", "category": "S"},
            {"id": "blog-003", "title": "C", "category": "E"},
        ]}
        exp_signals = {"signals": [
            {"id": "explore-20260210-test-001", "title": "X", "source": {"tier": "exploration"}},
            {"id": "explore-20260210-test-002", "title": "Y", "source": {"tier": "exploration"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        exp_path = temp_dir / "exp.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)
        _write_json(exp_path, exp_signals)

        result = merge_exploration_signals(str(exp_path), str(raw_path), str(cls_path))

        assert result["status"] == "SUCCESS"
        assert result["statistics"]["merged"] == 2

        # Verify both files have 5 signals
        with open(raw_path) as f:
            raw_after = json.load(f)
        with open(cls_path) as f:
            cls_after = json.load(f)
        assert len(raw_after["items"]) == 5
        assert len(cls_after["classified_signals"]) == 5

    def test_merge_skips_duplicates(self, temp_dir):
        # Signal already exists in raw
        raw_data = {"items": [
            {"id": "explore-20260210-test-001", "title": "X", "source": {"tier": "exploration"}},
        ]}
        cls_data = {"classified_signals": [
            {"id": "explore-20260210-test-001", "title": "X", "source": {"tier": "exploration"}},
        ]}
        exp_signals = {"signals": [
            {"id": "explore-20260210-test-001", "title": "X", "source": {"tier": "exploration"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        exp_path = temp_dir / "exp.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)
        _write_json(exp_path, exp_signals)

        result = merge_exploration_signals(str(exp_path), str(raw_path), str(cls_path))
        assert result["status"] == "SKIPPED"
        assert result["statistics"]["skipped_duplicate"] == 1

    def test_merge_empty_signals_skips(self, temp_dir):
        exp_signals = {"signals": []}
        raw_data = {"items": [{"id": "1"}]}
        cls_data = {"classified_signals": [{"id": "1"}]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        exp_path = temp_dir / "exp.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)
        _write_json(exp_path, exp_signals)

        result = merge_exploration_signals(str(exp_path), str(raw_path), str(cls_path))
        assert result["status"] == "SKIPPED"

    def test_merge_preserves_original_on_missing_file(self, temp_dir):
        exp_path = temp_dir / "exp.json"
        _write_json(exp_path, {"signals": [{"id": "x"}]})

        with pytest.raises(FileNotFoundError):
            merge_exploration_signals(str(exp_path), "nonexistent.json", "also_nonexistent.json")

    def test_merge_writes_report(self, temp_dir):
        raw_data = {"items": [{"id": "1"}]}
        cls_data = {"classified_signals": [{"id": "1"}]}
        exp_signals = {"signals": [
            {"id": "explore-001", "source": {"tier": "exploration"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        exp_path = temp_dir / "exp.json"
        report_path = temp_dir / "report.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)
        _write_json(exp_path, exp_signals)

        result = merge_exploration_signals(
            str(exp_path), str(raw_path), str(cls_path),
            output_report_path=str(report_path),
        )
        assert report_path.exists()
        with open(report_path) as f:
            report = json.load(f)
        assert report["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# Verify tests
# ---------------------------------------------------------------------------

class TestVerify:
    def test_verify_passes_clean_data(self, temp_dir):
        raw_data = {"items": [
            {"id": "blog-001", "source": {"tier": "base"}},
            {"id": "explore-20260210-test-001", "source": {"tier": "exploration"},
             "exploration_source": "TestSource"},
        ]}
        cls_data = {"classified_signals": [
            {"id": "blog-001", "source": {"tier": "base"}},
            {"id": "explore-20260210-test-001", "source": {"tier": "exploration"},
             "exploration_source": "TestSource"},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(str(raw_path), str(cls_path))
        assert result["status"] == "PASS"
        assert len(result["violations"]) == 0

    def test_verify_detects_missing_tier_tag(self, temp_dir):
        raw_data = {"items": [
            {"id": "explore-20260210-test-001", "source": {"tier": "base"}},
        ]}
        cls_data = {"classified_signals": [
            {"id": "explore-20260210-test-001", "source": {"tier": "base"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(str(raw_path), str(cls_path))
        assert result["status"] == "FAIL"
        tier_violations = [v for v in result["violations"] if v["check"] == "V1_tier_tag"]
        assert len(tier_violations) > 0

    def test_verify_detects_wrong_id_prefix(self, temp_dir):
        raw_data = {"items": [
            {"id": "wrong-prefix-001", "source": {"tier": "exploration"}},
        ]}
        cls_data = {"classified_signals": [
            {"id": "wrong-prefix-001", "source": {"tier": "exploration"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(str(raw_path), str(cls_path))
        assert result["status"] == "FAIL"
        id_violations = [v for v in result["violations"] if v["check"] == "V2_id_prefix"]
        assert len(id_violations) > 0

    def test_verify_detects_excluded_source(self, temp_dir):
        raw_data = {"items": [
            {"id": "explore-20260210-blocked-001", "source": {"tier": "exploration"},
             "exploration_source": "ArXiv Blog"},
        ]}
        cls_data = {"classified_signals": [
            {"id": "explore-20260210-blocked-001", "source": {"tier": "exploration"},
             "exploration_source": "ArXiv Blog"},
        ]}
        excluded = {"excluded_sources": ["arXiv Blog", "Naver Tech"]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        exc_path = temp_dir / "excluded.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)
        _write_json(exc_path, excluded)

        result = verify_exploration_signals(
            str(raw_path), str(cls_path), excluded_sources_path=str(exc_path)
        )
        assert result["status"] == "FAIL"
        exc_violations = [v for v in result["violations"] if v["check"] == "V3_excluded_source"]
        assert len(exc_violations) == 1

    def test_verify_detects_count_exceeds_max(self, temp_dir):
        # Create 10 exploration signals, but set max to 5
        raw_signals = [
            {"id": f"explore-20260210-test-{i:03d}", "source": {"tier": "exploration"}}
            for i in range(10)
        ]
        raw_data = {"items": raw_signals}
        cls_data = {"classified_signals": list(raw_signals)}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(
            str(raw_path), str(cls_path), max_exploration_signals=5
        )
        assert result["status"] == "FAIL"
        count_violations = [v for v in result["violations"] if v["check"] == "V4_count_limit"]
        assert len(count_violations) == 1
        assert count_violations[0]["count"] == 10

    def test_verify_detects_inconsistency_between_files(self, temp_dir):
        raw_data = {"items": [
            {"id": "explore-20260210-test-001", "source": {"tier": "exploration"}},
            {"id": "explore-20260210-test-002", "source": {"tier": "exploration"}},
        ]}
        # classified is missing one signal
        cls_data = {"classified_signals": [
            {"id": "explore-20260210-test-001", "source": {"tier": "exploration"}},
        ]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(str(raw_path), str(cls_path))
        assert result["status"] == "FAIL"
        consistency_violations = [v for v in result["violations"] if v["check"] == "V5_consistency"]
        assert len(consistency_violations) == 1
        assert "explore-20260210-test-002" in consistency_violations[0]["only_in_raw"]

    def test_verify_no_exploration_signals_passes(self, temp_dir):
        raw_data = {"items": [{"id": "blog-001", "source": {"tier": "base"}}]}
        cls_data = {"classified_signals": [{"id": "blog-001", "source": {"tier": "base"}}]}

        raw_path = temp_dir / "raw.json"
        cls_path = temp_dir / "cls.json"
        _write_json(raw_path, raw_data)
        _write_json(cls_path, cls_data)

        result = verify_exploration_signals(str(raw_path), str(cls_path))
        assert result["status"] == "PASS"
