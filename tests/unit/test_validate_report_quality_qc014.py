"""Unit tests for QC-014: Executive Summary Statistics vs Source Data."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from scripts.validate_report_quality import (
    QCValidationReport,
    _check_qc014_exec_summary_stats,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ranked(total: int, steeps_list: list[str] | None = None) -> dict:
    """Build a minimal priority-ranked JSON structure."""
    signals = []
    for i in range(total):
        sig = {"rank": i + 1, "id": f"test-{i+1}", "title": f"Signal {i+1}"}
        if steeps_list:
            sig["steeps"] = steeps_list[i % len(steeps_list)]
        else:
            sig["steeps"] = ""
        signals.append(sig)
    return {
        "ranking_metadata": {"total_ranked": total},
        "ranked_signals": signals,
    }


def _run_qc014(content: str, ranked: dict, lang: str = "en") -> dict:
    """Run QC-014 and return the check result dict."""
    vr = QCValidationReport(report_path="test.md", ranked_path="test.json", language=lang)
    _check_qc014_exec_summary_stats(vr, content, ranked, lang)
    assert len(vr.results) == 1
    r = vr.results[0]
    return r.to_dict()


# ---------------------------------------------------------------------------
# Sub-check A: Total Signal Count
# ---------------------------------------------------------------------------

class TestTotalSignalCount:

    def test_en_exact_match(self):
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 25
"""
        r = _run_qc014(content, _make_ranked(25))
        assert r["passed"] is True
        assert "25" in r["detail"]

    def test_en_mismatch(self):
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 30
"""
        r = _run_qc014(content, _make_ranked(25))
        assert r["passed"] is False
        assert "mismatch" in r["detail"].lower()
        assert "total-count" in r["failed_signal_ids"]

    def test_ko_bold_suffix(self):
        content = """\
## 1. 경영진 요약

### 주요 변화 요약
- 신규 탐지 시그널: **33건**
"""
        r = _run_qc014(content, _make_ranked(33), lang="ko")
        assert r["passed"] is True

    def test_ko_alt_phrasing(self):
        content = """\
## 1. 경영진 요약

### 주요 변화 요약
- 발견된 신규 신호: 10개
"""
        r = _run_qc014(content, _make_ranked(10), lang="ko")
        assert r["passed"] is True

    def test_ko_gamji_phrasing(self):
        content = """\
## 1. 경영진 요약

### 주요 변화 요약
- 신규 감지 시그널: 46개
"""
        r = _run_qc014(content, _make_ranked(46), lang="ko")
        assert r["passed"] is True

    def test_ko_with_parenthetical(self):
        """Only the first number before parenthetical is extracted."""
        content = """\
## 1. 경영진 요약

### 주요 변화 요약
- 신규 탐지 시그널: **33건** (250건 중 상위 33건)
"""
        r = _run_qc014(content, _make_ranked(33), lang="ko")
        assert r["passed"] is True

    def test_comma_separated_number(self):
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 1,200
"""
        r = _run_qc014(content, _make_ranked(1200))
        assert r["passed"] is True

    def test_no_count_found_skips(self):
        """When no total count pattern exists, QC-014 passes with skip note."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- Some other content here
"""
        r = _run_qc014(content, _make_ranked(25))
        assert r["passed"] is True
        assert "skipped" in r["detail"].lower() or "no summary" in r["detail"].lower()

    def test_missing_section1_skips(self):
        content = """\
## 2. Newly Detected Signals

Some content without Section 1.
"""
        r = _run_qc014(content, _make_ranked(25))
        assert r["passed"] is True


# ---------------------------------------------------------------------------
# Sub-check B: STEEPs Distribution
# ---------------------------------------------------------------------------

class TestSTEEPsDistribution:

    def test_table_format_match(self):
        """STEEPs distribution table matches JSON data."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 20

**STEEPs Distribution Today**:
| Domain | Count | % | Trend |
|--------|-------|---|-------|
| T_Technological | 10 | 50% | dominant |
| S_Social | 6 | 30% | steady |
| E_Economic | 4 | 20% | low |
"""
        steeps = (["T_Technological"] * 10 +
                  ["S_Social"] * 6 +
                  ["E_Economic"] * 4)
        r = _run_qc014(content, _make_ranked(20, steeps))
        assert r["passed"] is True
        assert "3 STEEPs categories checked" in r["detail"]

    def test_table_format_mismatch(self):
        """STEEPs table has wrong count for a category."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 20

| Domain | Count | % |
|--------|-------|---|
| T_Technological | 15 | 75% |
| S_Social | 5 | 25% |
"""
        steeps = (["T_Technological"] * 10 +
                  ["S_Social"] * 10)
        r = _run_qc014(content, _make_ranked(20, steeps))
        assert r["passed"] is False
        assert "T_Technological" in r["detail"]

    def test_inline_format_match(self):
        """Inline STEEPs format 'T_Technological (10)' is parsed."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 20
- Major impact domains: T_Technological (10), S_Social (6), E_Economic (4)
"""
        steeps = (["T_Technological"] * 10 +
                  ["S_Social"] * 6 +
                  ["E_Economic"] * 4)
        r = _run_qc014(content, _make_ranked(20, steeps))
        assert r["passed"] is True

    def test_tolerance_within_10pct(self):
        """Counts within 10% tolerance pass."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 100

| Domain | Count |
|--------|-------|
| T_Technological | 52 |
| S_Social | 48 |
"""
        steeps = (["T_Technological"] * 50 +
                  ["S_Social"] * 50)
        r = _run_qc014(content, _make_ranked(100, steeps))
        # 52 vs 50: diff=2, tolerance=max(1, 5)=5. Within tolerance.
        assert r["passed"] is True

    def test_tolerance_exceeded(self):
        """Counts beyond 10% tolerance fail."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 100

| Domain | Count |
|--------|-------|
| T_Technological | 70 |
| S_Social | 30 |
"""
        steeps = (["T_Technological"] * 50 +
                  ["S_Social"] * 50)
        r = _run_qc014(content, _make_ranked(100, steeps))
        # 70 vs 50: diff=20, tolerance=max(1, 5)=5. Exceeds.
        assert r["passed"] is False

    def test_empty_steeps_skips_check(self):
        """When all signals have empty steeps, sub-check B is skipped."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 50

| Domain | Count |
|--------|-------|
| T_Technological | 999 |
"""
        r = _run_qc014(content, _make_ranked(50))  # No steeps populated
        # Should pass — steeps check skipped, total count matches
        assert r["passed"] is True
        assert "STEEPs" not in r["detail"]

    def test_low_coverage_skips_check(self):
        """When <50% of signals have steeps, sub-check B is skipped."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 10

| Domain | Count |
|--------|-------|
| T_Technological | 999 |
"""
        # Only 4 out of 10 signals have steeps (40% < 50%)
        steeps = ["T_Technological", "", "", "S_Social", "", "", "T_Technological", "", "", "S_Social"]
        ranked = _make_ranked(10)
        for i, s in enumerate(steeps):
            ranked["ranked_signals"][i]["steeps"] = s

        r = _run_qc014(content, ranked)
        assert r["passed"] is True

    def test_fssf_types_not_matched_as_steeps(self):
        """FSSF types (Trend, Driver, etc.) in tables should NOT be matched."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- 신규 탐지 시그널: **33건**

| 유형 | 수 |
|------|---|
| Trend | 5 |
| Driver | 8 |
| Discontinuity | 4 |
"""
        steeps = ["E_economic"] * 33
        r = _run_qc014(content, _make_ranked(33, steeps), lang="ko")
        # FSSF types should be ignored; only STEEPs categories are checked
        assert r["passed"] is True

    def test_tipping_colors_not_matched_as_steeps(self):
        """Tipping Point colors (RED, GREEN, etc.) should NOT be matched."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 20

| Alert Level | Count |
|-------------|-------|
| RED | 4 |
| ORANGE | 4 |
| YELLOW | 6 |
| GREEN | 6 |
"""
        steeps = ["T_Technological"] * 20
        r = _run_qc014(content, _make_ranked(20, steeps))
        assert r["passed"] is True


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_report(self):
        r = _run_qc014("", _make_ranked(10))
        assert r["passed"] is True

    def test_empty_ranked_data(self):
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 0
"""
        r = _run_qc014(content, {"ranking_metadata": {"total_ranked": 0}, "ranked_signals": []})
        assert r["passed"] is True

    def test_check_id_and_level(self):
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 5
"""
        r = _run_qc014(content, _make_ranked(5))
        assert r["check_id"] == "QC-014"
        assert r["level"] == "ERROR"

    def test_signals_key_fallback(self):
        """If ranked_signals is missing, fall back to 'signals' key."""
        content = """\
## 1. Executive Summary

### Key Changes Summary
- New signals detected: 3
"""
        ranked = {
            "ranking_metadata": {"total_ranked": 3},
            "signals": [
                {"rank": 1, "id": "a", "steeps": ""},
                {"rank": 2, "id": "b", "steeps": ""},
                {"rank": 3, "id": "c", "steeps": ""},
            ],
        }
        r = _run_qc014(content, ranked)
        assert r["passed"] is True
