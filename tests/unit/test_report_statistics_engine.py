"""
Tests for report_statistics_engine.py

Validates that Python correctly counts statistics from classified-signals JSON,
ensuring report placeholders match actual data (no LLM hallucination).
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add core module path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "env-scanning" / "core"))
import report_statistics_engine as engine


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _make_signal(
    sid="test-001",
    title="테스트 신호",
    category="E",
    fssf_type="Trend",
    horizon="H1",
    psst_score=85,
    alert_level="GREEN",
    pattern=None,
    psst_grade=None,
):
    """Helper to create a test signal dict."""
    signal = {
        "id": sid,
        "title": title,
        "final_category": category,
        "fssf_type": fssf_type,
        "horizon": horizon,
        "psst_score": psst_score,
        "tipping_point": {"alert_level": alert_level},
    }
    if pattern:
        signal["tipping_point"]["pattern"] = pattern
    if psst_grade:
        signal["psst_grade"] = psst_grade
    return signal


def _make_classified_data(signals):
    """Wrap signals in classified-signals JSON structure."""
    return {
        "classification_metadata": {"date": "2026-02-10", "total_classified": len(signals)},
        "classified_signals": signals,
    }


# ---------------------------------------------------------------------------
# TestComputeStatsUniversal
# ---------------------------------------------------------------------------

class TestComputeStatsUniversal:
    def test_total_new_signals(self):
        signals = [_make_signal(sid=f"s-{i}") for i in range(15)]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 15
        assert stats["placeholders"]["TOTAL_NEW_SIGNALS"] == "15"

    def test_steeps_distribution_all_categories(self):
        signals = [
            _make_signal(category="E"),
            _make_signal(category="E"),
            _make_signal(category="T"),
            _make_signal(category="S"),
            _make_signal(category="P"),
            _make_signal(category="E_Environmental"),
            _make_signal(category="s"),
        ]
        dist = engine.compute_steeps_distribution(signals)
        assert dist["E"] == 2
        assert dist["T"] == 1
        assert dist["S"] == 1
        assert dist["P"] == 1
        assert dist["E_Environmental"] == 1
        assert dist["s"] == 1

    def test_steeps_zero_fill_missing(self):
        signals = [_make_signal(category="T")]
        dist = engine.compute_steeps_distribution(signals)
        assert dist["E"] == 0
        assert dist["S"] == 0
        assert dist["P"] == 0
        assert dist["E_Environmental"] == 0
        assert dist["s"] == 0
        assert dist["T"] == 1

    def test_domain_distribution_format(self):
        dist = {"E": 4, "T": 3, "S": 3, "P": 3, "E_Environmental": 1, "s": 1}
        result = engine.format_domain_distribution(dist)
        assert "경제(E) 4건" in result
        assert "기술(T) 3건" in result
        assert "사회(S) 3건" in result
        # E should come first (highest count)
        assert result.index("경제(E)") < result.index("환경(E)")


# ---------------------------------------------------------------------------
# TestComputeStatsFSSF
# ---------------------------------------------------------------------------

class TestComputeStatsFSSF:
    def test_fssf_all_8_types(self):
        signals = [
            _make_signal(fssf_type="Weak Signal"),
            _make_signal(fssf_type="Wild Card"),
            _make_signal(fssf_type="Discontinuity"),
            _make_signal(fssf_type="Driver"),
            _make_signal(fssf_type="Emerging Issue"),
            _make_signal(fssf_type="Precursor Event"),
            _make_signal(fssf_type="Trend"),
            _make_signal(fssf_type="Megatrend"),
        ]
        dist = engine.compute_fssf_distribution(signals)
        for ftype in engine.FSSF_TYPES:
            assert dist[ftype] == 1, f"Expected 1 for {ftype}, got {dist[ftype]}"

    def test_fssf_zero_fill_megatrend(self):
        signals = [
            _make_signal(fssf_type="Trend"),
            _make_signal(fssf_type="Trend"),
        ]
        dist = engine.compute_fssf_distribution(signals)
        assert dist["Trend"] == 2
        assert dist["Megatrend"] == 0
        assert dist["Weak Signal"] == 0

    def test_fssf_percentage_rounding(self):
        # 2 out of 3 = 67%, 1 out of 3 = 33%
        signals = [
            _make_signal(fssf_type="Trend"),
            _make_signal(fssf_type="Trend"),
            _make_signal(fssf_type="Driver"),
        ]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "naver")
        assert stats["placeholders"]["FSSF_TREND_PCT"] == "67%"
        assert stats["placeholders"]["FSSF_DRIVER_PCT"] == "33%"


# ---------------------------------------------------------------------------
# TestComputeStatsHorizons
# ---------------------------------------------------------------------------

class TestComputeStatsHorizons:
    def test_three_horizons_basic(self):
        signals = [
            _make_signal(horizon="H1"),
            _make_signal(horizon="H1"),
            _make_signal(horizon="H2"),
            _make_signal(horizon="H3"),
        ]
        dist = engine.compute_three_horizons_distribution(signals)
        assert dist["H1"] == 2
        assert dist["H2"] == 1
        assert dist["H3"] == 1

    def test_horizons_percentages(self):
        signals = [_make_signal(horizon="H1") for _ in range(10)]
        signals += [_make_signal(horizon="H2") for _ in range(4)]
        signals += [_make_signal(horizon="H3")]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "naver")
        assert stats["placeholders"]["H1_COUNT"] == "10"
        assert stats["placeholders"]["H1_PCT"] == "67%"
        assert stats["placeholders"]["H2_COUNT"] == "4"
        assert stats["placeholders"]["H2_PCT"] == "27%"
        assert stats["placeholders"]["H3_COUNT"] == "1"
        assert stats["placeholders"]["H3_PCT"] == "7%"


# ---------------------------------------------------------------------------
# TestComputeStatsTippingPoint
# ---------------------------------------------------------------------------

class TestComputeStatsTippingPoint:
    def test_alert_distribution_exact_counts(self):
        signals = [
            _make_signal(alert_level="RED", title="출산율 0.68 역대 최저"),
            _make_signal(alert_level="ORANGE", title="신호A"),
            _make_signal(alert_level="ORANGE", title="신호B"),
            _make_signal(alert_level="YELLOW", title="신호C"),
            _make_signal(alert_level="GREEN", title="신호D"),
            _make_signal(alert_level="GREEN", title="신호E"),
        ]
        dist = engine.compute_tipping_point_distribution(signals)
        assert dist["RED"]["count"] == 1
        assert dist["ORANGE"]["count"] == 2
        assert dist["YELLOW"]["count"] == 1
        assert dist["GREEN"]["count"] == 2

    def test_alert_with_signal_titles(self):
        signals = [
            _make_signal(alert_level="RED", title="위기 신호"),
            _make_signal(alert_level="ORANGE", title="주의 신호"),
        ]
        dist = engine.compute_tipping_point_distribution(signals)
        assert "위기 신호" in dist["RED"]["signals"]
        assert "주의 신호" in dist["ORANGE"]["signals"]

    def test_all_green_scenario(self):
        signals = [_make_signal(alert_level="GREEN", title=f"안전 {i}") for i in range(5)]
        dist = engine.compute_tipping_point_distribution(signals)
        assert dist["RED"]["count"] == 0
        assert dist["ORANGE"]["count"] == 0
        assert dist["YELLOW"]["count"] == 0
        assert dist["GREEN"]["count"] == 5
        # Table should be empty since format_tipping_point_summary_table skips 0-count levels
        # But GREEN with count should appear
        table = engine.format_tipping_point_summary_table(dist)
        assert "GREEN" in table
        assert "RED" not in table


# ---------------------------------------------------------------------------
# TestComputeStatsPSST
# ---------------------------------------------------------------------------

class TestComputeStatsPSST:
    def test_grade_distribution(self):
        signals = [
            _make_signal(psst_grade="A"),
            _make_signal(psst_grade="B"),
            _make_signal(psst_grade="B"),
            _make_signal(psst_grade="C"),
        ]
        dist = engine.compute_psst_grade_distribution(signals)
        assert dist["A"] == 1
        assert dist["B"] == 2
        assert dist["C"] == 1
        assert dist["D"] == 0

    def test_grade_from_score_fallback(self):
        signals = [
            _make_signal(psst_score=95),   # A
            _make_signal(psst_score=85),   # B
            _make_signal(psst_score=60),   # C
            _make_signal(psst_score=30),   # D
        ]
        dist = engine.compute_psst_grade_distribution(signals)
        assert dist["A"] == 1
        assert dist["B"] == 1
        assert dist["C"] == 1
        assert dist["D"] == 1


# ---------------------------------------------------------------------------
# TestBuildPlaceholderMap
# ---------------------------------------------------------------------------

class TestBuildPlaceholderMap:
    def test_standard_only_universal(self):
        signals = [_make_signal(category="T") for _ in range(5)]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "standard")
        ph = stats["placeholders"]
        # Universal keys present
        assert "TOTAL_NEW_SIGNALS" in ph
        assert "DOMAIN_DISTRIBUTION" in ph
        # WF3-specific keys absent
        assert "FSSF_WEAK_SIGNAL_COUNT" not in ph
        assert "H1_COUNT" not in ph
        assert "TIPPING_POINT_ALERT_SUMMARY" not in ph

    def test_naver_includes_fssf_horizons_tipping(self):
        signals = [
            _make_signal(
                category="E", fssf_type="Trend", horizon="H1",
                alert_level="ORANGE", psst_score=85,
            ),
        ]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "naver")
        ph = stats["placeholders"]
        # Universal
        assert ph["TOTAL_NEW_SIGNALS"] == "1"
        # FSSF
        assert "FSSF_TREND_COUNT" in ph
        assert ph["FSSF_TREND_COUNT"] == "1"
        assert ph["FSSF_TREND_PCT"] == "100%"
        # Section 4.3
        assert ph["FSSF_DIST_TR_COUNT"] == "1"
        assert ph["FSSF_DIST_WS_COUNT"] == "0"
        # Horizons
        assert ph["H1_COUNT"] == "1"
        assert ph["H1_PCT"] == "100%"
        # Tipping Point
        assert "TIPPING_POINT_ALERT_SUMMARY" in ph


# ---------------------------------------------------------------------------
# TestFormatTippingPointTable
# ---------------------------------------------------------------------------

class TestFormatTippingPointTable:
    def test_format_with_all_levels(self):
        tp = {
            "RED": {"count": 1, "signals": ["출산율 0.68"]},
            "ORANGE": {"count": 2, "signals": ["관세 위협", "정국 불안"]},
            "YELLOW": {"count": 1, "signals": ["기준금리"]},
            "GREEN": {"count": 3, "signals": ["신호A", "신호B", "신호C"]},
        }
        table = engine.format_tipping_point_summary_table(tp)
        lines = table.strip().split("\n")
        assert len(lines) == 4  # All 4 levels have count > 0
        assert "RED" in lines[0]
        assert "출산율 0.68" in lines[0]
        assert "ORANGE" in lines[1]
        assert "GREEN" in lines[3]

    def test_signal_titles_max_3_per_level(self):
        tp = {
            "RED": {"count": 0, "signals": []},
            "ORANGE": {"count": 5, "signals": ["A", "B", "C", "D", "E"]},
            "YELLOW": {"count": 0, "signals": []},
            "GREEN": {"count": 0, "signals": []},
        }
        table = engine.format_tipping_point_summary_table(tp)
        assert "외 2건" in table  # 5 signals, shows 3 + "외 2건"
        assert "A, B, C" in table


# ---------------------------------------------------------------------------
# TestRealData — Integration-like test with actual WF3 data
# ---------------------------------------------------------------------------

class TestRealData:
    @pytest.fixture
    def real_data_path(self):
        path = Path(__file__).resolve().parents[2] / "env-scanning" / "wf3-naver" / "structured" / "classified-signals-2026-02-10.json"
        if not path.exists():
            pytest.skip(f"Real data file not found: {path}")
        return path

    def test_with_actual_wf3_classified_signals(self, real_data_path):
        with open(real_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        stats = engine.compute_statistics(data, "naver")

        # Known ground truth from manual count
        assert stats["total_signals"] == 15

        # Tipping Point: RED=1, ORANGE=5, YELLOW=4, GREEN=5
        tp = stats["raw_distributions"]["tipping_point_alerts"]
        assert tp["RED"]["count"] == 1, f"Expected RED=1, got {tp['RED']['count']}"
        assert tp["ORANGE"]["count"] == 5, f"Expected ORANGE=5, got {tp['ORANGE']['count']}"
        assert tp["YELLOW"]["count"] == 4, f"Expected YELLOW=4, got {tp['YELLOW']['count']}"
        assert tp["GREEN"]["count"] == 5, f"Expected GREEN=5, got {tp['GREEN']['count']}"

        # RED signal is "출산율 0.68 역대 최저"
        assert "출산율 0.68 역대 최저" in tp["RED"]["signals"]

        # STEEPs — engine counts from final_category, not metadata
        # E=4, T=3, S=4, P=3, E_Environmental=1 (total=15)
        # Note: metadata says S=3, s=1 but actual signals have S=4, s=0
        steeps = stats["raw_distributions"]["steeps"]
        assert steeps["E"] == 4
        assert steeps["T"] == 3
        assert steeps["P"] == 3
        assert steeps["E_Environmental"] == 1
        assert sum(steeps.values()) == 15

        # FSSF: Megatrend should be 0
        fssf = stats["raw_distributions"]["fssf"]
        assert fssf["Megatrend"] == 0

        # Horizons: H1=10, H2=4, H3=1
        horizons = stats["raw_distributions"]["horizons"]
        assert horizons["H1"] == 10
        assert horizons["H2"] == 4
        assert horizons["H3"] == 1

        # Placeholders generated
        ph = stats["placeholders"]
        assert ph["TOTAL_NEW_SIGNALS"] == "15"
        assert "TIPPING_POINT_ALERT_SUMMARY" in ph
        assert "RED" in ph["TIPPING_POINT_ALERT_SUMMARY"]


# ---------------------------------------------------------------------------
# TestEvolutionStatistics
# ---------------------------------------------------------------------------

class TestEvolutionStatistics:
    """Test evolution statistics computation and placeholder generation."""

    def _make_evolution_map(self):
        """Create a sample evolution-map for testing."""
        return {
            "summary": {
                "total_signals_today": 15,
                "new_signals": 8,
                "recurring_signals": 3,
                "strengthening_signals": 2,
                "weakening_signals": 1,
                "faded_threads": 1,
                "transformed_signals": 0,
                "active_threads": 12,
            },
            "evolution_entries": [
                {
                    "signal_id": "wf1-20260211-001",
                    "thread_id": "THREAD-WF1-001",
                    "canonical_title": "AI 인프라 대규모 투자 경쟁",
                    "state": "STRENGTHENING",
                    "appearance_count": 8,
                    "metrics": {
                        "days_tracked": 10,
                        "psst_current": 91,
                        "psst_previous": 85,
                        "psst_delta": "+6",
                        "direction": "ACCELERATING",
                        "expansion": 0.67,
                    },
                    "thread_history_summary": [
                        {"date": "2026-01-30", "title": "AI 인프라 투자 경쟁", "psst": 82},
                        {"date": "2026-02-11", "title": "AI 인프라 대규모 투자", "psst": 91},
                    ],
                },
                {
                    "signal_id": "wf1-20260211-005",
                    "thread_id": "THREAD-WF1-003",
                    "canonical_title": "지정학적 분절화 심화",
                    "state": "STRENGTHENING",
                    "appearance_count": 6,
                    "metrics": {
                        "days_tracked": 7,
                        "psst_current": 83,
                        "psst_previous": 78,
                        "psst_delta": "+5",
                        "direction": "STABLE",
                        "expansion": 0.50,
                    },
                    "thread_history_summary": [
                        {"date": "2026-02-04", "title": "지정학적 분절화", "psst": 78},
                        {"date": "2026-02-11", "title": "지정학적 분절화 심화", "psst": 83},
                    ],
                },
                {
                    "signal_id": "wf1-20260211-010",
                    "thread_id": "THREAD-WF1-007",
                    "canonical_title": "NFT 시장 침체",
                    "state": "WEAKENING",
                    "appearance_count": 4,
                    "metrics": {
                        "days_tracked": 5,
                        "psst_current": 60,
                        "psst_previous": 70,
                        "psst_delta": "-10",
                        "direction": "DECELERATING",
                        "expansion": 0.33,
                    },
                    "thread_history_summary": [
                        {"date": "2026-02-06", "title": "NFT 시장 축소", "psst": 70},
                        {"date": "2026-02-11", "title": "NFT 시장 침체", "psst": 60},
                    ],
                },
            ],
            "faded_threads": [
                {"thread_id": "THREAD-WF1-005", "last_seen": "2026-02-07"},
            ],
        }

    def test_evolution_placeholders_with_data(self):
        """When evolution_map is provided, EVOLUTION_* placeholders should be populated."""
        signals = [_make_signal(sid=f"s-{i}") for i in range(15)]
        data = _make_classified_data(signals)
        evo_map = self._make_evolution_map()
        stats = engine.compute_statistics(data, "standard", evolution_map=evo_map)
        ph = stats["placeholders"]
        assert ph["EVOLUTION_ACTIVE_THREADS"] == "12"
        assert ph["EVOLUTION_NEW_COUNT"] == "8"
        assert ph["EVOLUTION_STRENGTHENING_COUNT"] == "2"
        assert ph["EVOLUTION_WEAKENING_COUNT"] == "1"
        assert ph["EVOLUTION_FADED_COUNT"] == "1"
        assert ph["EVOLUTION_NEW_PCT"] == "53%"

    def test_evolution_placeholders_without_data(self):
        """When no evolution_map is provided, EVOLUTION_* should be zero/dash."""
        signals = [_make_signal(sid=f"s-{i}") for i in range(5)]
        data = _make_classified_data(signals)
        stats = engine.compute_statistics(data, "standard")
        ph = stats["placeholders"]
        assert ph["EVOLUTION_ACTIVE_THREADS"] == "0"
        assert ph["EVOLUTION_NEW_COUNT"] == "0"
        assert ph["EVOLUTION_NEW_PCT"] == "—"
        assert ph["EVOLUTION_TABLE_STRENGTHENING"] == "해당 없음"
        assert ph["EVOLUTION_TABLE_WEAKENING"] == "해당 없음"

    def test_evolution_strengthening_table_format(self):
        """Strengthening table should contain markdown table with entries."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        table = ph["EVOLUTION_TABLE_STRENGTHENING"]
        assert "추적 스레드" in table
        assert "AI 인프라" in table
        assert "지정학적 분절화" in table
        assert "▲ 가속" in table
        lines = table.strip().split("\n")
        assert len(lines) == 4  # header + separator + 2 data rows

    def test_evolution_weakening_table_format(self):
        """Weakening table should contain 1 entry."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        table = ph["EVOLUTION_TABLE_WEAKENING"]
        assert "NFT" in table
        assert "▼ 감속" in table
        lines = table.strip().split("\n")
        assert len(lines) == 3  # header + separator + 1 data row

    def test_empty_evolution_entries(self):
        """When evolution_entries is empty, tables should show '해당 없음'."""
        evo_map = {
            "summary": {"total_signals_today": 5, "new_signals": 5,
                        "recurring_signals": 0, "strengthening_signals": 0,
                        "weakening_signals": 0, "faded_threads": 0,
                        "transformed_signals": 0, "active_threads": 0},
            "evolution_entries": [],
            "faded_threads": [],
        }
        ph = engine.compute_evolution_statistics(evo_map)
        assert ph["EVOLUTION_TABLE_STRENGTHENING"] == "해당 없음"
        assert ph["EVOLUTION_TABLE_WEAKENING"] == "해당 없음"
        assert ph["EVOLUTION_STRENGTHENING_COUNT"] == "0"

    def test_faded_pct_is_dash(self):
        """H1 fix: FADED percentage should be '—' (not a numeric %).
        Faded threads are absent history threads, NOT a subset of today's signals.
        Mixing populations in a single % table produces meaningless statistics."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        assert ph["EVOLUTION_FADED_PCT"] == "—", \
            "Faded percentage must be '—' to avoid population mixing error"
        # Count should still be numeric
        assert ph["EVOLUTION_FADED_COUNT"] == "1"

    def test_table_has_6_columns_with_appearances(self):
        """H2 fix: evolution table must have 6 columns including 등장횟수."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        table = ph["EVOLUTION_TABLE_STRENGTHENING"]
        header_line = table.strip().split("\n")[0]
        # Must include the new 등장횟수 column
        assert "등장횟수" in header_line, "Table header must include 등장횟수 column"
        # Count columns by pipe separators (6 columns = 7 pipes including edges)
        columns = [c.strip() for c in header_line.split("|") if c.strip()]
        assert len(columns) == 6, f"Expected 6 columns, got {len(columns)}: {columns}"
        assert "추적 스레드" in columns[0]
        assert "추적일수" in columns[1]
        assert "등장횟수" in columns[2]

    def test_table_uses_canonical_title_not_thread_id(self):
        """C1 fix: table must display human-readable title, not machine THREAD-WF1-NNN ID."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        table = ph["EVOLUTION_TABLE_STRENGTHENING"]
        # Should contain human-readable titles from canonical_title
        assert "AI 인프라 대규모 투자 경쟁" in table
        assert "지정학적 분절화 심화" in table
        # Should NOT contain machine thread IDs
        assert "THREAD-WF1-001" not in table
        assert "THREAD-WF1-003" not in table

    def test_table_includes_appearance_count_values(self):
        """H2 fix: each row in evolution table must show appearance_count."""
        evo_map = self._make_evolution_map()
        ph = engine.compute_evolution_statistics(evo_map)
        table = ph["EVOLUTION_TABLE_STRENGTHENING"]
        # First entry has appearance_count=8, second has 6
        assert "8회" in table, "First entry's appearance count (8회) should appear"
        assert "6회" in table, "Second entry's appearance count (6회) should appear"

    def test_evolution_raw_distribution(self):
        """Evolution raw distribution should be stored in raw_distributions."""
        signals = [_make_signal(sid=f"s-{i}") for i in range(15)]
        data = _make_classified_data(signals)
        evo_map = self._make_evolution_map()
        stats = engine.compute_statistics(data, "standard", evolution_map=evo_map)
        evo_dist = stats["raw_distributions"]["evolution"]
        assert evo_dist["new"] == 8
        assert evo_dist["strengthening"] == 2
        assert evo_dist["active_threads"] == 12


class TestWeeklyEvolutionStatistics:
    """Tests for compute_weekly_evolution_stats() function."""

    @staticmethod
    def _make_daily_evo_map(
        entries=None, faded=None, new_count=0, strengthening_count=0,
    ):
        if entries is None:
            entries = []
        if faded is None:
            faded = []
        return {
            "summary": {
                "total_signals_today": len(entries),
                "new_signals": new_count,
                "strengthening_signals": strengthening_count,
            },
            "evolution_entries": entries,
            "faded_threads": faded,
        }

    def test_weekly_with_data(self):
        """Weekly evolution should aggregate across multiple daily maps."""
        day1 = self._make_daily_evo_map(
            entries=[
                {"thread_id": "T-001", "state": "NEW", "metrics": {"velocity": 0.3, "direction": "ACCELERATING", "days_tracked": 1},
                 "thread_history_summary": [{"title": "AI Infra Investment", "psst": 82}]},
                {"thread_id": "T-002", "state": "STRENGTHENING", "metrics": {"velocity": 0.5, "direction": "ACCELERATING", "days_tracked": 3},
                 "thread_history_summary": [{"title": "Quantum Computing Advance", "psst": 90}]},
            ],
            new_count=1,
        )
        day2 = self._make_daily_evo_map(
            entries=[
                {"thread_id": "T-001", "state": "RECURRING", "metrics": {"velocity": 0.1, "direction": "STABLE", "days_tracked": 2},
                 "thread_history_summary": [{"title": "AI Infra Investment", "psst": 83}]},
                {"thread_id": "T-003", "state": "NEW", "metrics": {"velocity": -0.2, "direction": "DECELERATING", "days_tracked": 1},
                 "thread_history_summary": [{"title": "Trade Policy Shift", "psst": 70}]},
            ],
            faded=[{"thread_id": "T-999"}],
            new_count=1,
        )
        result = engine.compute_weekly_evolution_stats([day1, day2])
        assert result["WEEKLY_EVOLUTION_TOTAL_THREADS"] == "3"  # T-001, T-002, T-003
        assert result["WEEKLY_EVOLUTION_NEW_THREADS"] == "2"  # T-001 (day1 NEW), T-003 (day2 NEW)
        assert result["WEEKLY_EVOLUTION_FADED_THREADS"] == "1"  # T-999
        assert "가속" in result["WEEKLY_EVOLUTION_TOP_ACCELERATING"]
        assert "Quantum Computing" in result["WEEKLY_EVOLUTION_TOP_ACCELERATING"]

    def test_weekly_without_data(self):
        """Empty input should return zero/dash defaults."""
        result = engine.compute_weekly_evolution_stats([])
        assert result["WEEKLY_EVOLUTION_TOTAL_THREADS"] == "0"
        assert result["WEEKLY_EVOLUTION_NEW_THREADS"] == "0"
        assert result["WEEKLY_EVOLUTION_FADED_THREADS"] == "0"
        assert result["WEEKLY_EVOLUTION_TOP_ACCELERATING"] == "해당 없음"
        assert result["WEEKLY_EVOLUTION_TOP_DECELERATING"] == "해당 없음"

    def test_weekly_deceleration_table(self):
        """Decelerating threads should be in top decelerating table."""
        day = self._make_daily_evo_map(entries=[
            {"thread_id": "T-010", "state": "WEAKENING",
             "metrics": {"velocity": -0.6, "direction": "DECELERATING", "days_tracked": 5},
             "thread_history_summary": [{"title": "Crypto Decline", "psst": 60}]},
        ])
        result = engine.compute_weekly_evolution_stats([day])
        assert "감속" in result["WEEKLY_EVOLUTION_TOP_DECELERATING"]
        assert "Crypto Decline" in result["WEEKLY_EVOLUTION_TOP_DECELERATING"]
        assert result["WEEKLY_EVOLUTION_TOP_ACCELERATING"] == "해당 없음"  # no accelerating


# ---------------------------------------------------------------------------
# TestIntegratedEvolutionStatistics
# ---------------------------------------------------------------------------

class TestIntegratedEvolutionStatistics:
    """Test integrated mode: merge_evolution_maps + cross-evolution table."""

    def test_merge_evolution_maps_basic(self):
        """Merging 2 WF evolution-maps should sum counts and concat entries."""
        map1 = {
            "summary": {"total_signals_today": 10, "new_signals": 5,
                        "recurring_signals": 3, "strengthening_signals": 1,
                        "weakening_signals": 1, "faded_threads": 0, "active_threads": 8},
            "evolution_entries": [
                {"signal_id": "wf1-001", "state": "STRENGTHENING", "metrics": {}},
            ],
            "faded_threads": [],
        }
        map2 = {
            "summary": {"total_signals_today": 8, "new_signals": 4,
                        "recurring_signals": 2, "strengthening_signals": 1,
                        "weakening_signals": 0, "faded_threads": 1, "active_threads": 6},
            "evolution_entries": [
                {"signal_id": "wf2-001", "state": "NEW", "metrics": {}},
                {"signal_id": "wf2-002", "state": "WEAKENING", "metrics": {}},
            ],
            "faded_threads": [{"thread_id": "THREAD-WF2-003"}],
        }
        merged = engine.merge_evolution_maps([map1, map2])
        assert merged["summary"]["total_signals_today"] == 18
        assert merged["summary"]["new_signals"] == 9
        assert merged["summary"]["strengthening_signals"] == 2
        assert merged["summary"]["faded_threads"] == 1
        assert merged["summary"]["active_threads"] == 14
        assert len(merged["evolution_entries"]) == 3
        assert len(merged["faded_threads"]) == 1

    def test_merge_evolution_maps_empty(self):
        """Merging empty list should return zero summary."""
        merged = engine.merge_evolution_maps([])
        assert merged["summary"]["total_signals_today"] == 0
        assert len(merged["evolution_entries"]) == 0

    def test_merge_evolution_maps_skips_none(self):
        """None entries in the list should be skipped."""
        map1 = {
            "summary": {"total_signals_today": 5, "new_signals": 3,
                        "recurring_signals": 1, "strengthening_signals": 1,
                        "weakening_signals": 0, "faded_threads": 0, "active_threads": 4},
            "evolution_entries": [{"signal_id": "wf1-001"}],
            "faded_threads": [],
        }
        merged = engine.merge_evolution_maps([map1, None, {}, map1])
        assert merged["summary"]["total_signals_today"] == 10
        assert len(merged["evolution_entries"]) == 2

    def test_cross_evolution_table_format(self):
        """Cross-evolution table should format correlations as markdown."""
        cross_map = {
            "correlations": [
                {"source_wf": "wf2", "target_wf": "wf1",
                 "source_title": "AI Safety Research", "target_title": "AI 안전 규제",
                 "title_similarity": 0.82, "keyword_similarity": 0.75, "lead_days": 3},
                {"source_wf": "wf1", "target_wf": "wf3",
                 "source_title": "Global Chip Shortage", "target_title": "반도체 공급 부족",
                 "title_similarity": 0.70, "keyword_similarity": 0.80, "lead_days": 0},
            ],
        }
        table = engine.compute_cross_evolution_table(cross_map)
        assert "소스 WF" in table
        assert "WF2(arXiv)" in table
        assert "WF1(일반)" in table
        assert "3일" in table
        assert "동시" in table

    def test_cross_evolution_table_empty(self):
        """Empty correlations should return fallback message."""
        table = engine.compute_cross_evolution_table({"correlations": []})
        assert "교차 상관 없음" in table

    def test_cross_evolution_placeholder_empty(self):
        """Empty placeholder helper should return default message."""
        result = engine._empty_cross_evolution_placeholder()
        assert "시간축" in result

    def test_build_placeholder_map_integrated_with_cross(self):
        """Integrated mode build_placeholder_map should include INT_EVOLUTION_CROSS_TABLE."""
        evo_map = {
            "summary": {"total_signals_today": 15, "new_signals": 8,
                        "recurring_signals": 3, "strengthening_signals": 2,
                        "weakening_signals": 1, "faded_threads": 1,
                        "transformed_signals": 0, "active_threads": 12},
            "evolution_entries": [],
            "faded_threads": [],
        }
        cross_map = {
            "correlations": [
                {"source_wf": "wf2", "target_wf": "wf1",
                 "source_title": "Test", "target_title": "테스트",
                 "title_similarity": 0.85, "keyword_similarity": 0.80, "lead_days": 2},
            ],
        }
        stats = {
            "total_signals": 15,
            "raw_distributions": {"steeps": {"E": 5, "T": 4, "S": 3, "P": 2, "E_Environmental": 1, "s": 0}},
        }
        ph = engine.build_placeholder_map(stats, "integrated", evo_map, cross_map)
        assert "INT_EVOLUTION_CROSS_TABLE" in ph
        assert "WF2(arXiv)" in ph["INT_EVOLUTION_CROSS_TABLE"]
        assert ph["EVOLUTION_ACTIVE_THREADS"] == "12"

    def test_build_placeholder_map_integrated_no_cross(self):
        """Integrated without cross_evolution_map should have empty cross table."""
        stats = {
            "total_signals": 5,
            "raw_distributions": {"steeps": {"E": 2, "T": 2, "S": 1, "P": 0, "E_Environmental": 0, "s": 0}},
        }
        ph = engine.build_placeholder_map(stats, "integrated")
        assert ph["INT_EVOLUTION_CROSS_TABLE"] == engine._empty_cross_evolution_placeholder()
        assert ph["EVOLUTION_ACTIVE_THREADS"] == "0"  # no evolution data


# ---------------------------------------------------------------------------
# R1: Key-Variant Fallback Tests
# ---------------------------------------------------------------------------

class TestClassifiedSignalsKeyVariant:
    """Verify compute_statistics handles all known classified-signals key variants."""

    def _signals(self):
        return [_make_signal("s1", category="T"), _make_signal("s2", category="E")]

    def test_classified_signals_key(self):
        """Standard v2.1.0+ format with 'classified_signals' key."""
        data = {"classification_metadata": {}, "classified_signals": self._signals()}
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 2

    def test_signals_key(self):
        """v2.0.x format with 'signals' key."""
        data = {"classification_metadata": {}, "signals": self._signals()}
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 2

    def test_items_key(self):
        """v1.x raw format with 'items' key."""
        data = {"scan_metadata": {}, "items": self._signals()}
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 2

    def test_empty_data_returns_zero(self):
        """No recognized key → 0 signals (graceful degradation)."""
        data = {"some_other_key": [1, 2, 3]}
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 0

    def test_classified_signals_takes_priority(self):
        """When both keys exist, 'classified_signals' takes priority."""
        data = {
            "classified_signals": self._signals(),
            "signals": [_make_signal("only-one")],
        }
        stats = engine.compute_statistics(data, "standard")
        assert stats["total_signals"] == 2  # from classified_signals, not signals


# ---------------------------------------------------------------------------
# R2: combined_score in Cross-Evolution Table
# ---------------------------------------------------------------------------

class TestCrossEvolutionTableCombinedScore:
    """Verify compute_cross_evolution_table uses combined_score when available."""

    def test_combined_score_used(self):
        """When combined_score is present, it should be used over max(title, keyword)."""
        cross_map = {
            "correlations": [{
                "source_wf": "wf1", "target_wf": "wf2",
                "source_title": "AI Agent", "target_title": "AI Agent Paper",
                "title_similarity": 0.85, "keyword_similarity": 0.70,
                "combined_score": 0.775,  # 0.85*0.5 + 0.70*0.5
                "confidence": "MEDIUM",
                "lead_days": 3,
            }],
        }
        table = engine.compute_cross_evolution_table(cross_map)
        assert "0.78" in table or "0.77" in table  # combined_score, not max(0.85, 0.70)

    def test_fallback_to_max_without_combined_score(self):
        """Pre-v1.3.0 data without combined_score → fallback to max()."""
        cross_map = {
            "correlations": [{
                "source_wf": "wf1", "target_wf": "wf2",
                "source_title": "Test", "target_title": "Test",
                "title_similarity": 0.90, "keyword_similarity": 0.60,
                "lead_days": 0,
            }],
        }
        table = engine.compute_cross_evolution_table(cross_map)
        assert "0.90" in table  # max(0.90, 0.60)


# ---------------------------------------------------------------------------
# Exploration Statistics (v2.5.0)
# ---------------------------------------------------------------------------

import tempfile

class TestExplorationStatistics:
    """Tests for compute_exploration_statistics and _empty_exploration_placeholders."""

    def _write_candidates(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def test_valid_candidates_all_fields(self, tmp_path):
        """Full candidates file → all EXPLORATION_* placeholders populated."""
        candidates = {
            "method_used": "agent-team",
            "total_exploration_signals": 7,
            "viable_candidates": [
                {"name": "SourceA", "target_steeps": ["T", "E"]},
                {"name": "SourceB", "target_steeps": ["S"]},
            ],
            "non_viable_candidates": [
                {"name": "SourceC", "target_steeps": ["P"]},
            ],
        }
        path = tmp_path / "candidates.json"
        self._write_candidates(path, candidates)

        result = engine.compute_exploration_statistics(str(path))
        assert result["EXPLORATION_METHOD"] == "agent-team"
        assert result["EXPLORATION_DISCOVERED"] == "3개"
        assert result["EXPLORATION_VIABLE"] == "2개"
        assert result["EXPLORATION_SIGNALS"] == "7개"
        assert result["EXPLORATION_PENDING"] == "2개"
        # Gaps: E, P, S, T (sorted)
        assert "E" in result["EXPLORATION_GAPS"]
        assert "P" in result["EXPLORATION_GAPS"]
        assert "S" in result["EXPLORATION_GAPS"]
        assert "T" in result["EXPLORATION_GAPS"]

    def test_pending_excludes_decided(self, tmp_path):
        """Candidates with user_decision are not counted as pending."""
        candidates = {
            "method_used": "single-agent",
            "total_exploration_signals": 3,
            "viable_candidates": [
                {"name": "SourceA", "target_steeps": ["T"], "user_decision": "approved"},
                {"name": "SourceB", "target_steeps": ["E"]},
            ],
            "non_viable_candidates": [],
        }
        path = tmp_path / "candidates.json"
        self._write_candidates(path, candidates)

        result = engine.compute_exploration_statistics(str(path))
        assert result["EXPLORATION_PENDING"] == "1개"  # Only SourceB

    def test_missing_file_returns_empty(self):
        """Nonexistent file → empty placeholders (graceful degradation)."""
        result = engine.compute_exploration_statistics("/nonexistent/path.json")
        assert result["EXPLORATION_METHOD"] == "비활성"
        assert result["EXPLORATION_DISCOVERED"] == "0개"
        assert result["EXPLORATION_VIABLE"] == "0개"
        assert result["EXPLORATION_SIGNALS"] == "0개"
        assert result["EXPLORATION_PENDING"] == "0개"
        assert result["EXPLORATION_GAPS"] == "없음"

    def test_corrupt_json_returns_empty(self, tmp_path):
        """Corrupt JSON → empty placeholders, not crash."""
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json{{{")

        result = engine.compute_exploration_statistics(str(path))
        assert result["EXPLORATION_METHOD"] == "비활성"

    def test_no_gaps_in_candidates(self, tmp_path):
        """Candidates without target_steeps → gaps = '없음'."""
        candidates = {
            "method_used": "agent-team",
            "total_exploration_signals": 0,
            "viable_candidates": [{"name": "X"}],
            "non_viable_candidates": [],
        }
        path = tmp_path / "candidates.json"
        self._write_candidates(path, candidates)

        result = engine.compute_exploration_statistics(str(path))
        assert result["EXPLORATION_GAPS"] == "없음"

    def test_empty_exploration_placeholders(self):
        """_empty_exploration_placeholders returns all 6 keys."""
        result = engine._empty_exploration_placeholders()
        assert len(result) == 6
        assert set(result.keys()) == engine.EXPLORATION_PLACEHOLDERS

    def test_placeholder_names_match_constant(self, tmp_path):
        """compute_exploration_statistics keys == EXPLORATION_PLACEHOLDERS constant."""
        candidates = {
            "method_used": "agent-team",
            "total_exploration_signals": 1,
            "viable_candidates": [],
            "non_viable_candidates": [],
        }
        path = tmp_path / "candidates.json"
        self._write_candidates(path, candidates)

        result = engine.compute_exploration_statistics(str(path))
        assert set(result.keys()) == engine.EXPLORATION_PLACEHOLDERS

    def test_build_placeholder_map_includes_exploration(self, tmp_path):
        """build_placeholder_map with exploration_candidates_path includes EXPLORATION_*."""
        # Minimal classified signals → compute_statistics first
        data = {
            "classified_signals": [
                _make_signal("sig-001", category="T"),
                _make_signal("sig-002", category="E"),
            ],
        }
        stats = engine.compute_statistics(data, "standard")

        candidates = {
            "method_used": "agent-team",
            "total_exploration_signals": 5,
            "viable_candidates": [{"name": "A", "target_steeps": ["T"]}],
            "non_viable_candidates": [],
        }
        cand_path = tmp_path / "candidates.json"
        self._write_candidates(cand_path, candidates)

        placeholders = engine.build_placeholder_map(
            stats, "standard",
            exploration_candidates_path=str(cand_path),
        )
        assert "EXPLORATION_METHOD" in placeholders
        assert placeholders["EXPLORATION_DISCOVERED"] == "1개"
        assert placeholders["EXPLORATION_SIGNALS"] == "5개"

    def test_build_placeholder_map_without_exploration(self):
        """build_placeholder_map without exploration_candidates_path → no EXPLORATION_* keys."""
        data = {
            "classified_signals": [_make_signal("sig-001", category="T")],
        }
        stats = engine.compute_statistics(data, "standard")
        placeholders = engine.build_placeholder_map(stats, "standard")
        # Should NOT have exploration keys when path is not provided
        assert "EXPLORATION_METHOD" not in placeholders


# ---------------------------------------------------------------------------
# Bilingual (language="en") Tests — v1.3.0
# ---------------------------------------------------------------------------

class TestBilingualEnglish:
    """Tests for language='en' output across all functions."""

    def test_domain_distribution_en(self):
        """English domain distribution uses English labels without counter suffix."""
        steeps = {"E": 5, "T": 3, "S": 2, "P": 1, "E_Environmental": 0, "s": 0}
        result = engine.format_domain_distribution(steeps, language="en")
        assert "Economic(E)" in result
        assert "Technological(T)" in result
        assert "Social(S)" in result
        assert "Political(P)" in result
        # No Korean counter suffix
        assert "건" not in result
        # No Korean labels
        assert "경제" not in result

    def test_domain_distribution_ko_default(self):
        """Default language='ko' produces Korean output (backward compat)."""
        steeps = {"E": 3, "T": 2, "S": 0, "P": 0, "E_Environmental": 0, "s": 0}
        result = engine.format_domain_distribution(steeps)
        assert "경제(E)" in result
        assert "건" in result

    def test_evolution_table_en(self):
        """English evolution table uses English headers."""
        entries = [{
            "canonical_title": "AI Safety Research",
            "state": "STRENGTHENING",
            "appearance_count": 5,
            "metrics": {
                "days_tracked": 3, "psst_previous": 70, "psst_current": 85,
                "psst_delta": "+15", "direction": "ACCELERATING", "expansion": 1.2,
            },
        }]
        table = engine._format_evolution_table(entries, language="en")
        assert "Tracking Thread" in table
        assert "Days Tracked" in table
        assert "Appearances" in table
        assert "Velocity" in table
        assert "Expansion" in table
        assert "▲ Accel" in table
        assert "3d" in table  # days suffix
        assert "5x" in table  # times suffix
        # No Korean
        assert "추적 스레드" not in table
        assert "가속" not in table

    def test_evolution_table_empty_en(self):
        """Empty evolution table returns English N/A."""
        result = engine._format_evolution_table([], language="en")
        assert result == "N/A"

    def test_empty_evolution_placeholders_en(self):
        """English empty evolution placeholders."""
        ph = engine._empty_evolution_placeholders(language="en")
        assert ph["EVOLUTION_TABLE_STRENGTHENING"] == "N/A"
        assert ph["EVOLUTION_TABLE_WEAKENING"] == "N/A"

    def test_compute_evolution_statistics_en(self):
        """compute_evolution_statistics with language='en'."""
        evo_map = {
            "summary": {
                "total_signals_today": 10, "new_signals": 5,
                "recurring_signals": 3, "strengthening_signals": 1,
                "weakening_signals": 1, "faded_threads": 0,
                "transformed_signals": 0, "active_threads": 8,
            },
            "evolution_entries": [{
                "signal_id": "test-001", "state": "STRENGTHENING",
                "canonical_title": "Test Signal",
                "appearance_count": 3,
                "metrics": {
                    "days_tracked": 2, "psst_previous": 60, "psst_current": 75,
                    "psst_delta": "+15", "direction": "ACCELERATING", "expansion": 0.8,
                },
            }],
            "faded_threads": [],
        }
        ph = engine.compute_evolution_statistics(evo_map, language="en")
        assert "Tracking Thread" in ph["EVOLUTION_TABLE_STRENGTHENING"]
        assert "▲ Accel" in ph["EVOLUTION_TABLE_STRENGTHENING"]

    def test_cross_evolution_table_en(self):
        """English cross-evolution table."""
        cross_map = {
            "correlations": [{
                "source_wf": "wf2", "target_wf": "wf1",
                "source_title": "AI Safety", "target_title": "AI Regulation",
                "title_similarity": 0.82, "keyword_similarity": 0.75, "lead_days": 3,
            }],
        }
        table = engine.compute_cross_evolution_table(cross_map, language="en")
        assert "Source WF" in table
        assert "WF2(arXiv)" in table
        assert "WF1(General)" in table
        assert "3d" in table  # days suffix
        assert "일" not in table

    def test_cross_evolution_table_same_day_en(self):
        """Same-day lead shows 'same day' in English."""
        cross_map = {
            "correlations": [{
                "source_wf": "wf1", "target_wf": "wf3",
                "source_title": "Test", "target_title": "Test",
                "title_similarity": 0.90, "keyword_similarity": 0.80, "lead_days": 0,
            }],
        }
        table = engine.compute_cross_evolution_table(cross_map, language="en")
        assert "same day" in table
        assert "동시" not in table

    def test_empty_cross_evolution_en(self):
        """English empty cross-evolution placeholder."""
        result = engine._empty_cross_evolution_placeholder(language="en")
        assert result == "No cross-evolution data"

    def test_weekly_evolution_en(self):
        """Weekly evolution stats with English output."""
        day = {
            "summary": {"total_signals_today": 2, "new_signals": 1},
            "evolution_entries": [
                {"thread_id": "T-001", "state": "NEW",
                 "metrics": {"velocity": 0.5, "direction": "ACCELERATING", "days_tracked": 1},
                 "thread_history_summary": [{"title": "Quantum AI", "psst": 88}]},
            ],
            "faded_threads": [],
        }
        result = engine.compute_weekly_evolution_stats([day], language="en")
        assert "Accelerating" in result["WEEKLY_EVOLUTION_TOP_ACCELERATING"]
        assert "▲ Accel" in result["WEEKLY_EVOLUTION_TOP_ACCELERATING"]
        assert "가속" not in result["WEEKLY_EVOLUTION_TOP_ACCELERATING"]

    def test_weekly_empty_en(self):
        """Empty weekly returns English N/A."""
        result = engine.compute_weekly_evolution_stats([], language="en")
        assert result["WEEKLY_EVOLUTION_TOP_ACCELERATING"] == "N/A"
        assert result["WEEKLY_EVOLUTION_TOP_DECELERATING"] == "N/A"

    def test_exploration_en(self, tmp_path):
        """Exploration statistics with English output."""
        candidates = {
            "method_used": "agent-team",
            "total_exploration_signals": 5,
            "viable_candidates": [{"name": "A", "target_steeps": ["T"]}],
            "non_viable_candidates": [{"name": "B", "target_steeps": ["E"]}],
        }
        path = tmp_path / "cands.json"
        with open(path, "w") as f:
            json.dump(candidates, f)

        result = engine.compute_exploration_statistics(str(path), language="en")
        assert result["EXPLORATION_DISCOVERED"] == "2"  # no 개 suffix
        assert result["EXPLORATION_VIABLE"] == "1"
        assert result["EXPLORATION_SIGNALS"] == "5"
        assert "개" not in result["EXPLORATION_DISCOVERED"]

    def test_exploration_empty_en(self):
        """English empty exploration placeholders."""
        result = engine._empty_exploration_placeholders(language="en")
        assert result["EXPLORATION_GAPS"] == "None"
        assert result["EXPLORATION_METHOD"] == "Disabled"
        assert result["EXPLORATION_DISCOVERED"] == "0"

    def test_tipping_point_en(self):
        """Tipping point summary table in English."""
        tp = {
            "RED": {"count": 1, "signals": ["Critical Signal A"]},
            "ORANGE": {"count": 4, "signals": ["B", "C", "D", "E"]},
            "YELLOW": {"count": 0, "signals": []},
            "GREEN": {"count": 0, "signals": []},
        }
        result = engine.format_tipping_point_summary_table(tp, language="en")
        assert "RED" in result
        assert "and 1" in result  # "and" instead of "외"
        assert "외" not in result

    def test_compute_statistics_language_propagation(self):
        """language='en' propagates through compute_statistics → build_placeholder_map."""
        data = _make_classified_data([
            _make_signal("s1", category="E"),
            _make_signal("s2", category="T"),
            _make_signal("s3", category="E"),
        ])
        stats = engine.compute_statistics(data, "standard", language="en")
        ph = stats["placeholders"]
        assert "Economic(E)" in ph["DOMAIN_DISTRIBUTION"]
        assert "건" not in ph["DOMAIN_DISTRIBUTION"]
        assert ph["EVOLUTION_TABLE_STRENGTHENING"] == "N/A"
