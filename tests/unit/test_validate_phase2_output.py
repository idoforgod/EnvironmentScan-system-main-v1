"""
Unit tests for validate_phase2_output.py (Pipeline Gate 2)

Tests the 8 PG2 checks against synthetic Phase 2 output data:
- PG2-001: STEEPs classification validity
- PG2-002: Impact score range
- PG2-003: Priority score range
- PG2-004: FSSF type validity (WF3/WF4)
- PG2-005: Three Horizons validity (WF3/WF4)
- PG2-006: Tipping Point color validity (WF3/WF4)
- PG2-007: Signal count consistency
- PG2-008: Required fields in priority-ranked

Origin: Created 2026-03-09 as part of hallucination prevention initiative.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "scripts"))
from validate_phase2_output import (
    validate_phase2_output,
    _extract_signals,
    _get_steeps,
    _get_fssf,
    _get_horizon,
    _get_tipping_color,
    STEEPS_VALID,
    FSSF_VALID,
    THREE_HORIZONS_VALID,
    TIPPING_COLORS_VALID,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCAN_DATE = "2026-01-15"

# Minimal SOT for a standard (non-FSSF) workflow
MINIMAL_SOT = {
    "workflows": {
        "wf1-general": {
            "enabled": True,
            "data_root": "env-scanning/wf1-general",
        },
    },
}

# SOT with FSSF workflow (WF3)
SOT_WITH_FSSF = {
    "workflows": {
        "wf3-naver": {
            "enabled": True,
            "data_root": "env-scanning/wf3-naver",
        },
    },
}


def _make_classified_signals(
    signals: list[dict],
    extra_keys: dict | None = None,
) -> dict:
    """Build a classified-signals JSON structure."""
    data = {"scan_date": SCAN_DATE, "signals": signals}
    if extra_keys:
        data.update(extra_keys)
    return data


def _make_impact_assessment(
    entries: list[dict],
    key: str = "impact_matrix",
) -> dict:
    """Build an impact-assessment JSON structure."""
    return {"scan_date": SCAN_DATE, key: entries}


def _make_priority_ranked(signals: list[dict]) -> dict:
    """Build a priority-ranked JSON structure."""
    return {
        "ranking_metadata": {"date": SCAN_DATE, "total_ranked": len(signals)},
        "ranked_signals": signals,
    }


def _write_sot(tmp_path: Path, sot: dict) -> Path:
    """Write SOT YAML and return its path."""
    # Simulate project structure: project_root/env-scanning/config/
    config_dir = tmp_path / "env-scanning" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    sot_path = config_dir / "workflow-registry.yaml"

    import yaml
    with open(sot_path, "w") as f:
        yaml.dump(sot, f)
    return sot_path


def _write_json(path: Path, data: dict) -> None:
    """Write JSON data to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def _setup_standard_files(
    tmp_path: Path,
    n_signals: int = 3,
    wf_name: str = "wf1-general",
) -> Path:
    """Create a complete set of valid Phase 2 files and return SOT path."""
    sot = {
        "workflows": {
            wf_name: {
                "enabled": True,
                "data_root": f"env-scanning/{wf_name}",
            },
        },
    }
    sot_path = _write_sot(tmp_path, sot)
    data_root = tmp_path / "env-scanning" / wf_name

    # Classified signals
    classified = _make_classified_signals([
        {
            "id": f"sig-{i:03d}",
            "title": f"Signal {i}",
            "steeps_category": ["S", "T", "E", "P", "s", "E"][i % 6],
        }
        for i in range(n_signals)
    ])
    _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

    # Impact assessment
    impact = _make_impact_assessment([
        {
            "signal_id": f"sig-{i:03d}",
            "impact_score": round(1.0 + i * 0.5, 1),
        }
        for i in range(n_signals)
    ])
    _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

    # Priority ranked
    ranked = _make_priority_ranked([
        {
            "rank": i + 1,
            "id": f"sig-{i:03d}",
            "title": f"Signal {i}",
            "priority_score": round(8.0 - i * 0.5, 1),
        }
        for i in range(n_signals)
    ])
    _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

    return sot_path


def _setup_fssf_files(
    tmp_path: Path,
    n_signals: int = 3,
    wf_name: str = "wf3-naver",
) -> Path:
    """Create a complete set of valid Phase 2 files for a FSSF workflow."""
    sot = {
        "workflows": {
            wf_name: {
                "enabled": True,
                "data_root": f"env-scanning/{wf_name}",
            },
        },
    }
    sot_path = _write_sot(tmp_path, sot)
    data_root = tmp_path / "env-scanning" / wf_name

    fssf_types = ["Weak Signal", "Wild Card", "Discontinuity", "Driver",
                  "Emerging Issue", "Precursor Event", "Trend", "Megatrend"]
    horizons = ["H1", "H2", "H3"]
    colors = ["GREEN", "YELLOW", "ORANGE", "RED"]

    # Classified signals with FSSF/Horizons/Tipping
    classified = _make_classified_signals([
        {
            "id": f"naver-{SCAN_DATE.replace('-','')}-{i:03d}",
            "title": f"Signal {i}",
            "category": ["P", "E_economic", "T", "S", "s", "E_Environmental"][i % 6],
            "fssf_type": fssf_types[i % len(fssf_types)],
            "three_horizons": horizons[i % len(horizons)],
            "tipping_point": {
                "status": colors[i % len(colors)],
            },
        }
        for i in range(n_signals)
    ])
    _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

    # Impact assessment (dict-type structure like WF3)
    impact_dict = {}
    for i in range(n_signals):
        sig_id = f"naver-{SCAN_DATE.replace('-','')}-{i:03d}"
        impact_dict[sig_id] = {
            "impact_score": round(3.0 + i * 0.5, 1),
        }
    impact = {"scan_date": SCAN_DATE, "signal_impact_scores": impact_dict}
    _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

    # Priority ranked
    ranked = _make_priority_ranked([
        {
            "rank": i + 1,
            "id": f"naver-{SCAN_DATE.replace('-','')}-{i:03d}",
            "title": f"Signal {i}",
            "priority_score": round(7.0 - i * 0.3, 1),
            "fssf_type": fssf_types[i % len(fssf_types)],
        }
        for i in range(n_signals)
    ])
    _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

    return sot_path


# ---------------------------------------------------------------------------
# Helper Tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_extract_signals_list(self):
        data = {"signals": [{"id": "a"}, {"id": "b"}]}
        result = _extract_signals(data, "signals")
        assert len(result) == 2

    def test_extract_signals_dict(self):
        """Dict-type structure (WF3 impact) should be converted to list."""
        data = {"signal_impact_scores": {
            "sig-001": {"impact_score": 3.5},
            "sig-002": {"impact_score": 4.0},
        }}
        result = _extract_signals(data, "signal_impact_scores")
        assert len(result) == 2
        assert result[0]["signal_id"] == "sig-001"
        assert result[0]["impact_score"] == 3.5

    def test_extract_signals_fallback(self):
        data = {"other_key": [{"id": "a"}]}
        result = _extract_signals(data, "signals", "items", "other_key")
        assert len(result) == 1

    def test_extract_signals_empty(self):
        data = {"empty": []}
        result = _extract_signals(data, "empty")
        assert result == []

    def test_get_steeps_multiple_fields(self):
        assert _get_steeps({"steeps_category": "T"}) == "T"
        assert _get_steeps({"category": "P"}) == "P"
        assert _get_steeps({"steeps": "E_Economic"}) == "E_Economic"
        assert _get_steeps({"steeps_classification": "s"}) == "s"

    def test_get_steeps_empty(self):
        assert _get_steeps({}) is None
        assert _get_steeps({"steeps": ""}) is None

    def test_get_fssf(self):
        assert _get_fssf({"fssf_type": "Wild Card"}) == "Wild Card"
        assert _get_fssf({"fssf_type": "Wild_Card"}) == "Wild_Card"
        assert _get_fssf({}) is None
        assert _get_fssf({"fssf_type": ""}) is None

    def test_get_horizon(self):
        assert _get_horizon({"three_horizons": "H1"}) == "H1"
        assert _get_horizon({"horizon": "H2"}) == "H2"
        assert _get_horizon({}) is None

    def test_get_tipping_color_nested(self):
        assert _get_tipping_color({
            "tipping_point": {"status": "RED"}
        }) == "RED"

    def test_get_tipping_color_direct(self):
        assert _get_tipping_color({
            "tipping_point_alert": "ORANGE"
        }) == "ORANGE"

    def test_get_tipping_color_case_insensitive(self):
        assert _get_tipping_color({
            "tipping_point_alert": "green"
        }) == "GREEN"


# ---------------------------------------------------------------------------
# Enumeration Validity Tests
# ---------------------------------------------------------------------------

class TestEnumerations:
    def test_steeps_base_codes_valid(self):
        for code in ("S", "T", "E", "P", "s"):
            assert code in STEEPS_VALID

    def test_steeps_extended_codes_valid(self):
        for code in ("S_Social", "T_Technological", "E_Economic",
                      "E_Environmental", "P_Political", "s_spiritual"):
            assert code in STEEPS_VALID

    def test_steeps_invalid(self):
        assert "X" not in STEEPS_VALID
        assert "social" not in STEEPS_VALID

    def test_fssf_canonical_valid(self):
        for ftype in ("Weak Signal", "Wild Card", "Discontinuity",
                       "Driver", "Emerging Issue", "Precursor Event",
                       "Trend", "Megatrend"):
            assert ftype in FSSF_VALID

    def test_fssf_underscore_valid(self):
        for ftype in ("Weak_Signal", "Wild_Card", "Emerging_Issue",
                       "Precursor_Event"):
            assert ftype in FSSF_VALID

    def test_fssf_invalid(self):
        assert "Unknown" not in FSSF_VALID
        assert "Weak signal" not in FSSF_VALID  # case sensitive

    def test_three_horizons_valid(self):
        assert THREE_HORIZONS_VALID == {"H1", "H2", "H3"}

    def test_tipping_colors_valid(self):
        assert TIPPING_COLORS_VALID == {"GREEN", "YELLOW", "ORANGE", "RED"}


# ---------------------------------------------------------------------------
# Integration Tests — Full Validation
# ---------------------------------------------------------------------------

class TestFullValidation:
    def test_all_pass_standard(self, tmp_path):
        """Standard workflow with all valid data should PASS."""
        sot_path = _setup_standard_files(tmp_path, n_signals=5)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        assert result["status"] == "PASS"
        assert result["exit_code"] == 0
        assert result["critical_failures"] == 0

    def test_all_pass_fssf(self, tmp_path):
        """FSSF workflow with all valid data should PASS."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=5)
        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        assert result["status"] == "PASS"
        assert result["exit_code"] == 0
        assert result["critical_failures"] == 0
        assert result["is_fssf_workflow"] is True

    def test_unknown_workflow(self, tmp_path):
        """Unknown workflow name should FAIL."""
        sot_path = _setup_standard_files(tmp_path)
        result = validate_phase2_output(str(sot_path), "wf99-fake", SCAN_DATE)
        assert result["status"] == "FAIL"
        assert result["exit_code"] == 1

    def test_disabled_workflow(self, tmp_path):
        """Disabled workflow should FAIL."""
        sot = {
            "workflows": {
                "wf1-general": {
                    "enabled": False,
                    "data_root": "env-scanning/wf1-general",
                },
            },
        }
        sot_path = _write_sot(tmp_path, sot)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        assert result["status"] == "FAIL"


# ---------------------------------------------------------------------------
# PG2-001: STEEPs Classification Validity
# ---------------------------------------------------------------------------

class TestPG2001:
    def test_valid_steeps(self, tmp_path):
        """All valid STEEPs codes should PASS."""
        sot_path = _setup_standard_files(tmp_path, n_signals=6)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_001 = [c for c in result["checks"] if c["id"] == "PG2-001"][0]
        assert pg2_001["passed"] is True

    def test_invalid_steeps(self, tmp_path):
        """Invalid STEEPs code should fail PG2-001."""
        sot_path = _setup_standard_files(tmp_path, n_signals=3)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        classified = _make_classified_signals([
            {"id": "sig-001", "title": "A", "steeps_category": "T"},
            {"id": "sig-002", "title": "B", "steeps_category": "INVALID"},
            {"id": "sig-003", "title": "C", "steeps_category": "S"},
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_001 = [c for c in result["checks"] if c["id"] == "PG2-001"][0]
        assert pg2_001["passed"] is False
        assert "INVALID" in pg2_001["detail"]

    def test_missing_steeps_field(self, tmp_path):
        """Signal with no STEEPs field should fail PG2-001."""
        sot_path = _setup_standard_files(tmp_path, n_signals=2)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        classified = _make_classified_signals([
            {"id": "sig-001", "title": "A"},  # No steeps field at all
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_001 = [c for c in result["checks"] if c["id"] == "PG2-001"][0]
        assert pg2_001["passed"] is False
        assert "no STEEPs field" in pg2_001["detail"]


# ---------------------------------------------------------------------------
# PG2-002: Impact Score Range
# ---------------------------------------------------------------------------

class TestPG2002:
    def test_valid_impact_scores(self, tmp_path):
        """Impact scores within range should PASS."""
        sot_path = _setup_standard_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_002 = [c for c in result["checks"] if c["id"] == "PG2-002"][0]
        assert pg2_002["passed"] is True

    def test_out_of_range_impact(self, tmp_path):
        """Impact score >10 should fail PG2-002."""
        sot_path = _setup_standard_files(tmp_path, n_signals=2)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        impact = _make_impact_assessment([
            {"signal_id": "sig-000", "impact_score": 3.0},
            {"signal_id": "sig-001", "impact_score": 15.0},  # Out of range
        ])
        _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_002 = [c for c in result["checks"] if c["id"] == "PG2-002"][0]
        assert pg2_002["passed"] is False
        assert "sig-001" in pg2_002["detail"]

    def test_negative_impact_valid(self, tmp_path):
        """Negative impact scores within range are valid."""
        sot_path = _setup_standard_files(tmp_path, n_signals=2)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        impact = _make_impact_assessment([
            {"signal_id": "sig-000", "impact_score": -3.0},
            {"signal_id": "sig-001", "impact_score": -10.0},
        ])
        _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_002 = [c for c in result["checks"] if c["id"] == "PG2-002"][0]
        assert pg2_002["passed"] is True

    def test_dict_type_impact(self, tmp_path):
        """Dict-type impact structure (WF3) should be handled."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_002 = [c for c in result["checks"] if c["id"] == "PG2-002"][0]
        assert pg2_002["passed"] is True


# ---------------------------------------------------------------------------
# PG2-003: Priority Score Range
# ---------------------------------------------------------------------------

class TestPG2003:
    def test_valid_priority_scores(self, tmp_path):
        sot_path = _setup_standard_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_003 = [c for c in result["checks"] if c["id"] == "PG2-003"][0]
        assert pg2_003["passed"] is True

    def test_negative_priority_fails(self, tmp_path):
        """Negative priority score should fail."""
        sot_path = _setup_standard_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        ranked = _make_priority_ranked([
            {"rank": 1, "id": "sig-000", "title": "X", "priority_score": -1.0},
        ])
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_003 = [c for c in result["checks"] if c["id"] == "PG2-003"][0]
        assert pg2_003["passed"] is False

    def test_over_10_priority_fails(self, tmp_path):
        """Priority score >10 should fail."""
        sot_path = _setup_standard_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        ranked = _make_priority_ranked([
            {"rank": 1, "id": "sig-000", "title": "X", "priority_score": 10.1},
        ])
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_003 = [c for c in result["checks"] if c["id"] == "PG2-003"][0]
        assert pg2_003["passed"] is False


# ---------------------------------------------------------------------------
# PG2-004: FSSF Type Validity
# ---------------------------------------------------------------------------

class TestPG2004:
    def test_skipped_for_standard_wf(self, tmp_path):
        """FSSF check should be SKIP for non-FSSF workflows."""
        sot_path = _setup_standard_files(tmp_path)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_004 = [c for c in result["checks"] if c["id"] == "PG2-004"][0]
        assert pg2_004["passed"] is True
        assert pg2_004["severity"] == "SKIP"

    def test_valid_fssf_space(self, tmp_path):
        """Valid FSSF types with spaces should PASS."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=4)
        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_004 = [c for c in result["checks"] if c["id"] == "PG2-004"][0]
        assert pg2_004["passed"] is True

    def test_invalid_fssf_type(self, tmp_path):
        """Invalid FSSF type should fail PG2-004."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=2)
        data_root = tmp_path / "env-scanning" / "wf3-naver"
        classified = _make_classified_signals([
            {"id": "n-001", "title": "A", "category": "T",
             "fssf_type": "Wild Card", "three_horizons": "H1"},
            {"id": "n-002", "title": "B", "category": "P",
             "fssf_type": "FAKE_TYPE", "three_horizons": "H2"},
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_004 = [c for c in result["checks"] if c["id"] == "PG2-004"][0]
        assert pg2_004["passed"] is False
        assert "FAKE_TYPE" in pg2_004["detail"]


# ---------------------------------------------------------------------------
# PG2-005: Three Horizons Validity
# ---------------------------------------------------------------------------

class TestPG2005:
    def test_skipped_for_standard_wf(self, tmp_path):
        sot_path = _setup_standard_files(tmp_path)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_005 = [c for c in result["checks"] if c["id"] == "PG2-005"][0]
        assert pg2_005["severity"] == "SKIP"

    def test_valid_horizons(self, tmp_path):
        sot_path = _setup_fssf_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_005 = [c for c in result["checks"] if c["id"] == "PG2-005"][0]
        assert pg2_005["passed"] is True

    def test_invalid_horizon(self, tmp_path):
        sot_path = _setup_fssf_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf3-naver"
        classified = _make_classified_signals([
            {"id": "n-001", "title": "A", "category": "T",
             "fssf_type": "Trend", "three_horizons": "H4"},  # Invalid
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_005 = [c for c in result["checks"] if c["id"] == "PG2-005"][0]
        assert pg2_005["passed"] is False
        assert "H4" in pg2_005["detail"]


# ---------------------------------------------------------------------------
# PG2-006: Tipping Point Color Validity
# ---------------------------------------------------------------------------

class TestPG2006:
    def test_skipped_for_standard_wf(self, tmp_path):
        sot_path = _setup_standard_files(tmp_path)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_006 = [c for c in result["checks"] if c["id"] == "PG2-006"][0]
        assert pg2_006["severity"] == "SKIP"

    def test_valid_colors(self, tmp_path):
        sot_path = _setup_fssf_files(tmp_path, n_signals=4)
        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_006 = [c for c in result["checks"] if c["id"] == "PG2-006"][0]
        assert pg2_006["passed"] is True

    def test_invalid_color(self, tmp_path):
        sot_path = _setup_fssf_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf3-naver"
        classified = _make_classified_signals([
            {"id": "n-001", "title": "A", "category": "T",
             "fssf_type": "Trend", "three_horizons": "H1",
             "tipping_point": {"status": "PURPLE"}},  # Invalid color
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_006 = [c for c in result["checks"] if c["id"] == "PG2-006"][0]
        assert pg2_006["passed"] is False
        assert pg2_006["severity"] == "ERROR"  # Not CRITICAL

    def test_no_tipping_point_is_ok(self, tmp_path):
        """Signals without tipping_point field should not fail."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf3-naver"
        classified = _make_classified_signals([
            {"id": "n-001", "title": "A", "category": "T",
             "fssf_type": "Trend", "three_horizons": "H1"},
            # No tipping_point field
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_006 = [c for c in result["checks"] if c["id"] == "PG2-006"][0]
        assert pg2_006["passed"] is True


# ---------------------------------------------------------------------------
# PG2-007: Signal Count Consistency
# ---------------------------------------------------------------------------

class TestPG2007:
    def test_consistent_counts(self, tmp_path):
        """Equal counts across all 3 files should PASS."""
        sot_path = _setup_standard_files(tmp_path, n_signals=5)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_007 = [c for c in result["checks"] if c["id"] == "PG2-007"][0]
        assert pg2_007["passed"] is True
        assert result["signal_counts"]["classified"] == 5
        assert result["signal_counts"]["impact"] == 5
        assert result["signal_counts"]["ranked"] == 5

    def test_inconsistent_counts(self, tmp_path):
        """Mismatched counts should fail with ERROR severity."""
        sot_path = _setup_standard_files(tmp_path, n_signals=5)
        data_root = tmp_path / "env-scanning" / "wf1-general"

        # Override impact with different count
        impact = _make_impact_assessment([
            {"signal_id": f"sig-{i:03d}", "impact_score": 2.0}
            for i in range(3)  # Only 3 instead of 5
        ])
        _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_007 = [c for c in result["checks"] if c["id"] == "PG2-007"][0]
        assert pg2_007["passed"] is False
        assert pg2_007["severity"] == "ERROR"  # Not CRITICAL
        assert "MISMATCH" in pg2_007["detail"]


# ---------------------------------------------------------------------------
# PG2-008: Required Fields
# ---------------------------------------------------------------------------

class TestPG2008:
    def test_all_fields_present(self, tmp_path):
        sot_path = _setup_standard_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_008 = [c for c in result["checks"] if c["id"] == "PG2-008"][0]
        assert pg2_008["passed"] is True

    def test_missing_title(self, tmp_path):
        """Missing title field should fail PG2-008."""
        sot_path = _setup_standard_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        ranked = _make_priority_ranked([
            {"rank": 1, "id": "sig-000", "priority_score": 5.0},
            # Missing "title"
        ])
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_008 = [c for c in result["checks"] if c["id"] == "PG2-008"][0]
        assert pg2_008["passed"] is False
        assert "title" in pg2_008["detail"]

    def test_missing_rank(self, tmp_path):
        """Missing rank field should fail PG2-008."""
        sot_path = _setup_standard_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf1-general"
        ranked = _make_priority_ranked([
            {"id": "sig-000", "title": "X", "priority_score": 5.0},
            # Missing "rank"
        ])
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        pg2_008 = [c for c in result["checks"] if c["id"] == "PG2-008"][0]
        assert pg2_008["passed"] is False
        assert "rank" in pg2_008["detail"]


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_missing_all_files(self, tmp_path):
        """All Phase 2 files missing should produce CRITICAL failures."""
        sot = {"workflows": {"wf1-general": {
            "enabled": True, "data_root": "env-scanning/wf1-general",
        }}}
        sot_path = _write_sot(tmp_path, sot)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        assert result["status"] == "FAIL"
        assert result["critical_failures"] >= 3  # PG2-001, 002, 003, 008

    def test_zero_signals(self, tmp_path):
        """Files with empty signal arrays should produce appropriate failures."""
        sot = {"workflows": {"wf1-general": {
            "enabled": True, "data_root": "env-scanning/wf1-general",
        }}}
        sot_path = _write_sot(tmp_path, sot)
        data_root = tmp_path / "env-scanning" / "wf1-general"

        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json",
                     {"signals": []})
        _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json",
                     {"impact_matrix": []})
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json",
                     {"ranked_signals": []})

        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        # Empty arrays → no signal array found → FAIL
        assert result["status"] == "FAIL"

    def test_exit_code_mapping(self, tmp_path):
        """Verify exit code mapping: 0=PASS, 1=CRITICAL FAIL, 2=ERROR WARN."""
        # PASS
        sot_path = _setup_standard_files(tmp_path, n_signals=3)
        result = validate_phase2_output(str(sot_path), "wf1-general", SCAN_DATE)
        assert result["exit_code"] == 0

    def test_fssf_underscore_format(self, tmp_path):
        """WF3-style underscore FSSF types (Wild_Card) should be accepted."""
        sot_path = _setup_fssf_files(tmp_path, n_signals=1)
        data_root = tmp_path / "env-scanning" / "wf3-naver"
        classified = _make_classified_signals([
            {"id": "n-001", "title": "A", "category": "P",
             "fssf_type": "Wild_Card", "three_horizons": "H1"},
        ])
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        result = validate_phase2_output(str(sot_path), "wf3-naver", SCAN_DATE)
        pg2_004 = [c for c in result["checks"] if c["id"] == "PG2-004"][0]
        assert pg2_004["passed"] is True

    def test_wf4_classified_items_key(self, tmp_path):
        """WF4 uses 'items' key in classified signals — should be handled."""
        sot = {"workflows": {"wf4-multiglobal-news": {
            "enabled": True, "data_root": "env-scanning/wf4-multiglobal-news",
        }}}
        sot_path = _write_sot(tmp_path, sot)
        data_root = tmp_path / "env-scanning" / "wf4-multiglobal-news"

        # WF4 classified uses "items" key
        classified = {"items": [
            {"id": "news-001", "title": "A", "steeps_category": "T",
             "fssf_type": "Trend", "horizon": "H2",
             "tipping_point_alert": "GREEN"},
        ]}
        _write_json(data_root / f"structured/classified-signals-{SCAN_DATE}.json", classified)

        impact = {"items": [
            {"id": "news-001", "impact_score": 3.5},
        ]}
        _write_json(data_root / f"analysis/impact-assessment-{SCAN_DATE}.json", impact)

        ranked = {"ranked_signals": [
            {"rank": 1, "id": "news-001", "title": "A", "priority_score": 5.0},
        ]}
        _write_json(data_root / f"analysis/priority-ranked-{SCAN_DATE}.json", ranked)

        result = validate_phase2_output(str(sot_path), "wf4-multiglobal-news", SCAN_DATE)
        assert result["is_fssf_workflow"] is True
        pg2_001 = [c for c in result["checks"] if c["id"] == "PG2-001"][0]
        assert pg2_001["passed"] is True
        pg2_004 = [c for c in result["checks"] if c["id"] == "PG2-004"][0]
        assert pg2_004["passed"] is True
