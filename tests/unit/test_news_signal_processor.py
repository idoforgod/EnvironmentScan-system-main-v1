"""
Unit tests for news_signal_processor.py — WF4 News Signal Processor.

Tests cover:
- compute_fssf_hints(): FSSF hint computation (frequency, novelty, etc.)
- compute_tipping_point(): CSD analysis — flat and nested formats
- compute_variance_trend(): variance ratio for CSD detection
- compute_autocorrelation(): lag-1 autocorrelation for CSD detection
- detect_flickering(): rapid oscillation detection
- detect_anomaly(): z-score / cross-domain / single-source anomaly detection
- evaluate_alert_triggers(): 5 alert conditions with severity levels
- _determine_alert_level(): alert level decision table
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from core.news_signal_processor import (
    FSSFHints,
    compute_autocorrelation,
    compute_fssf_hints,
    compute_tipping_point,
    compute_variance_trend,
    detect_anomaly,
    detect_flickering,
    evaluate_alert_triggers,
    _determine_alert_level,
    _variance,
)


# ---------------------------------------------------------------------------
# compute_fssf_hints
# ---------------------------------------------------------------------------

class TestComputeFssfHints:
    """Tests for compute_fssf_hints() — FSSF classification hints."""

    def test_returns_dict_with_required_keys(self):
        """Output must contain all required hint keys."""
        signal = {
            "id": "news-20260224-bbc-001",
            "title": "AI breakthrough in quantum computing",
            "source": {"name": "BBC", "type": "news"},
            "content": {"abstract": "Researchers announced quantum supremacy."},
            "preliminary_category": "T",
            "collected_at": "2026-02-24T10:00:00Z",
        }
        result = compute_fssf_hints(signal, history=[])
        required_keys = [
            "signal_id", "frequency", "novelty_score", "cross_domain_count",
            "source_count", "is_event", "is_first_occurrence", "breaks_pattern",
            "impact_breadth", "suggested_fssf", "fssf_confidence",
            "suggested_horizon", "horizon_confidence",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_novel_signal_high_novelty(self):
        """Signal with no history should have novelty_score = 1.0."""
        signal = {
            "id": "news-20260224-test-001",
            "title": "Completely unique novel topic XYZ123",
            "source": {"name": "Test"},
            "content": {"abstract": "Never seen before."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["novelty_score"] == 1.0

    def test_repeated_signal_lower_novelty(self):
        """Signal with many history matches should have lower novelty."""
        signal = {
            "id": "news-20260224-test-001",
            "title": "AI technology breakthrough in computing",
            "source": {"name": "Test"},
            "content": {"abstract": "AI computing advances."},
        }
        history = [
            {"title": "AI technology advances in computing"},
            {"title": "AI technology breakthrough report"},
            {"title": "AI computing technology update"},
            {"title": "breakthrough in AI technology"},
            {"title": "computing technology AI news"},
        ]
        result = compute_fssf_hints(signal, history)
        assert result["novelty_score"] < 1.0
        assert result["frequency"] > 0.0

    def test_event_keyword_detection(self):
        """Signal with event keywords should flag is_event."""
        signal = {
            "id": "news-20260224-test-001",
            "title": "Government announces new AI regulation policy",
            "source": {"name": "Test"},
            "content": {"abstract": "The government approved the new regulation."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["is_event"] is True

    def test_pattern_break_detection(self):
        """Signal with pattern-breaking keywords should flag breaks_pattern."""
        signal = {
            "id": "news-20260224-test-001",
            "title": "Unprecedented shift in global trade paradigm",
            "source": {"name": "Test"},
            "content": {"abstract": "A historic reversal in trade patterns."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["breaks_pattern"] is True

    def test_cross_domain_count_minimum_1(self):
        """cross_domain_count should be at least 1."""
        signal = {
            "id": "test-001",
            "title": "Abstract topic with no domain keywords",
            "source": {"name": "Test"},
            "content": {"abstract": "No specific domain mentioned."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["cross_domain_count"] >= 1

    def test_suggested_fssf_is_valid_type(self):
        """suggested_fssf must be one of the 8 FSSF types or a valid default."""
        valid_types = [
            "Weak Signal", "Emerging Issue", "Trend", "Megatrend",
            "Driver", "Wild Card", "Discontinuity", "Precursor Event",
        ]
        signal = {
            "id": "test-001",
            "title": "Some test signal",
            "source": {"name": "Test"},
            "content": {"abstract": "Content."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["suggested_fssf"] in valid_types

    def test_fssf_confidence_between_0_and_1(self):
        """fssf_confidence must be between 0.0 and 1.0."""
        signal = {
            "id": "test-001",
            "title": "Test signal",
            "source": {"name": "Test"},
            "content": {"abstract": "Content."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert 0.0 <= result["fssf_confidence"] <= 1.0

    def test_suggested_horizon_is_valid(self):
        """suggested_horizon must be H1, H2, or H3."""
        signal = {
            "id": "test-001",
            "title": "Test signal about current market",
            "source": {"name": "Test"},
            "content": {"abstract": "Current market analysis."},
        }
        result = compute_fssf_hints(signal, history=[])
        assert result["suggested_horizon"] in ("H1", "H2", "H3")


# ---------------------------------------------------------------------------
# compute_tipping_point — flat format
# ---------------------------------------------------------------------------

class TestComputeTippingPointFlat:
    """Tests for compute_tipping_point() with flat format [{date, count}]."""

    def test_flat_format_basic(self):
        """Flat format [{'date': ..., 'count': N}] should work."""
        daily_counts = [
            {"date": f"2026-02-{d:02d}", "count": 5}
            for d in range(1, 15)
        ]
        result = compute_tipping_point(daily_counts, window=7)
        assert "overall_alert" in result
        assert "clusters" in result
        assert "summary" in result
        assert result["overall_alert"] in ("GREEN", "YELLOW", "ORANGE", "RED")

    def test_empty_counts_returns_green(self):
        """Empty input should return GREEN overall alert."""
        result = compute_tipping_point([], window=7)
        assert result["overall_alert"] == "GREEN"
        assert result["summary"]["total_clusters_analyzed"] == 0

    def test_constant_series_is_green(self):
        """Constant count series (no variance change) should be GREEN."""
        daily_counts = [
            {"date": f"2026-02-{d:02d}", "count": 10}
            for d in range(1, 15)
        ]
        result = compute_tipping_point(daily_counts, window=7)
        assert result["overall_alert"] == "GREEN"

    def test_insufficient_data_produces_no_clusters(self):
        """Less data than the window size should skip analysis."""
        daily_counts = [
            {"date": "2026-02-01", "count": 5},
            {"date": "2026-02-02", "count": 6},
        ]
        result = compute_tipping_point(daily_counts, window=7)
        assert result["summary"]["total_clusters_analyzed"] == 0


# ---------------------------------------------------------------------------
# compute_tipping_point — nested format (fixed bug)
# ---------------------------------------------------------------------------

class TestComputeTippingPointNested:
    """Tests for compute_tipping_point() with nested format [{date, counts: {T: N}}]."""

    def test_nested_format_works(self):
        """Nested format [{'date': ..., 'counts': {'T': N, 'E': M}}] should work."""
        daily_counts = [
            {"date": f"2026-02-{d:02d}", "counts": {"T": 5, "E": 3}}
            for d in range(1, 15)
        ]
        result = compute_tipping_point(daily_counts, window=7)
        assert "overall_alert" in result
        assert result["overall_alert"] in ("GREEN", "YELLOW", "ORANGE", "RED")
        # Should analyze at least one cluster (T and/or E)
        assert result["summary"]["total_clusters_analyzed"] >= 1

    def test_nested_format_multiple_categories(self):
        """Nested format with multiple STEEPs categories produces per-category analysis."""
        daily_counts = [
            {"date": f"2026-02-{d:02d}", "counts": {"T": d, "S": 10 - d, "P": 5}}
            for d in range(1, 15)
        ]
        result = compute_tipping_point(daily_counts, window=7)
        cluster_ids = {c["signal_id"] for c in result["clusters"]}
        # At least T and S should appear (P is constant, may or may not trigger)
        assert len(cluster_ids) >= 1

    def test_flat_per_category_format(self):
        """Flat per-category format [{'date': ..., 'T': N, 'E': M}] should work."""
        daily_counts = [
            {"date": f"2026-02-{d:02d}", "T": 5, "E": 3}
            for d in range(1, 15)
        ]
        result = compute_tipping_point(daily_counts, window=7)
        assert "overall_alert" in result
        assert result["summary"]["total_clusters_analyzed"] >= 1


# ---------------------------------------------------------------------------
# compute_variance_trend
# ---------------------------------------------------------------------------

class TestComputeVarianceTrend:
    """Tests for compute_variance_trend() — CSD indicator."""

    def test_constant_series_returns_zero_or_one(self):
        """Constant series has zero variance in both halves."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        vt = compute_variance_trend(values)
        assert vt == 0.0

    def test_increasing_variance_positive(self):
        """Series with increasing variance in recent half → positive trend."""
        # Baseline: stable (low variance)
        # Recent: volatile (high variance)
        values = [10.0, 10.0, 10.0, 10.0, 5.0, 15.0, 3.0, 17.0]
        vt = compute_variance_trend(values)
        assert vt > 0.0, f"Expected positive variance trend, got {vt}"

    def test_decreasing_variance(self):
        """Series with decreasing variance → ratio < 1.0."""
        # Baseline: volatile
        # Recent: stable
        values = [5.0, 15.0, 3.0, 17.0, 10.0, 10.0, 10.0, 10.0]
        vt = compute_variance_trend(values)
        assert vt < 1.0, f"Expected ratio < 1.0, got {vt}"

    def test_insufficient_data_returns_zero(self):
        """Less than 4 data points → 0.0."""
        assert compute_variance_trend([1.0, 2.0, 3.0]) == 0.0
        assert compute_variance_trend([]) == 0.0

    def test_zero_baseline_nonzero_recent_returns_2(self):
        """Zero variance baseline with non-zero recent → returns 2.0."""
        values = [5.0, 5.0, 5.0, 5.0, 3.0, 7.0, 2.0, 8.0]
        vt = compute_variance_trend(values)
        # Baseline [5,5,5,5] has var=0, recent [3,7,2,8] has var>0 → 2.0
        assert vt == 2.0


# ---------------------------------------------------------------------------
# compute_autocorrelation
# ---------------------------------------------------------------------------

class TestComputeAutocorrelation:
    """Tests for compute_autocorrelation() — lag-1 autocorrelation."""

    def test_constant_series_returns_zero(self):
        """Constant series has zero autocorrelation (zero variance denominator)."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        ac = compute_autocorrelation(values)
        assert ac == 0.0

    def test_perfect_autocorrelation(self):
        """Monotonically increasing series should have high positive autocorrelation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        ac = compute_autocorrelation(values)
        assert ac > 0.5, f"Expected high autocorrelation, got {ac}"

    def test_oscillating_series_negative(self):
        """Oscillating series (alternating high/low) should have negative autocorrelation."""
        values = [1.0, 10.0, 1.0, 10.0, 1.0, 10.0, 1.0, 10.0]
        ac = compute_autocorrelation(values)
        assert ac < 0.0, f"Expected negative autocorrelation, got {ac}"

    def test_insufficient_data_returns_zero(self):
        """Less than lag+3 data points → 0.0."""
        assert compute_autocorrelation([1.0, 2.0]) == 0.0
        assert compute_autocorrelation([]) == 0.0

    def test_result_within_bounds(self):
        """Autocorrelation should be in range [-1.0, 1.0]."""
        values = [3.0, 7.0, 2.0, 8.0, 4.0, 6.0, 1.0, 9.0]
        ac = compute_autocorrelation(values)
        assert -1.0 <= ac <= 1.0


# ---------------------------------------------------------------------------
# detect_flickering
# ---------------------------------------------------------------------------

class TestDetectFlickering:
    """Tests for detect_flickering() — rapid oscillation detection."""

    def test_oscillating_values_detected(self):
        """Rapidly oscillating values should trigger flickering detection.
        The threshold default is 2.0 (strict >), so we use threshold=1.5
        to verify the oscillation IS detected when threshold is lower."""
        # Perfect alternation gives ratio = 2.0, which equals the default threshold.
        # Using a lower threshold confirms the oscillation pattern is recognized.
        values = [1.0, 100.0, 1.0, 100.0, 1.0, 100.0, 1.0, 100.0,
                  1.0, 100.0, 1.0, 100.0]
        assert detect_flickering(values, threshold=1.5) is True

    def test_monotonic_series_not_flickering(self):
        """Monotonically increasing series should NOT flicker."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        assert detect_flickering(values) is False

    def test_constant_series_not_flickering(self):
        """Constant series should NOT flicker."""
        values = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        assert detect_flickering(values) is False

    def test_insufficient_data_returns_false(self):
        """Less than 4 data points → False."""
        assert detect_flickering([1.0, 2.0, 3.0]) is False
        assert detect_flickering([]) is False

    def test_mild_oscillation_not_flickering(self):
        """Mild oscillation below threshold should NOT flicker (default threshold=2.0)."""
        values = [5.0, 6.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        assert detect_flickering(values) is False


# ---------------------------------------------------------------------------
# detect_anomaly
# ---------------------------------------------------------------------------

class TestDetectAnomaly:
    """Tests for detect_anomaly() — z-score / cross-domain / single-source."""

    def test_normal_distribution_no_anomalies(self):
        """Stable category counts (with minor variance) should produce no z-score anomalies."""
        signal_counts = {
            "category_counts": {
                # Small natural variation around 5.0 — no spike
                "T": [5.0, 5.1, 4.9, 5.0, 5.1, 4.9, 5.0, 5.1,
                      4.9, 5.0, 5.1, 4.9, 5.0, 5.1, 5.0],
            },
            "signals": [],
            "source_distribution": {},
        }
        anomalies = detect_anomaly(signal_counts, window=14)
        z_score_anomalies = [a for a in anomalies if a["anomaly_type"] == "z_score"]
        assert len(z_score_anomalies) == 0

    def test_spike_detected_as_anomaly(self):
        """A large spike in the latest count should be flagged."""
        signal_counts = {
            "category_counts": {
                "T": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0,
                      5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 100.0],
            },
            "signals": [],
            "source_distribution": {},
        }
        anomalies = detect_anomaly(signal_counts, window=14)
        z_score_anomalies = [a for a in anomalies if a["anomaly_type"] == "z_score"]
        assert len(z_score_anomalies) >= 1
        assert z_score_anomalies[0]["signal_id"] == "CATEGORY-T"

    def test_single_source_concentration(self):
        """One source contributing >70% should be flagged."""
        signal_counts = {
            "category_counts": {},
            "signals": [],
            "source_distribution": {
                "BBC": 80,
                "Reuters": 10,
                "Guardian": 10,
            },
        }
        anomalies = detect_anomaly(signal_counts)
        single_source = [a for a in anomalies if a["anomaly_type"] == "single_source"]
        assert len(single_source) >= 1
        assert "BBC" in single_source[0]["detail"]

    def test_balanced_sources_no_concentration(self):
        """Balanced sources should NOT flag single_source anomaly."""
        signal_counts = {
            "category_counts": {},
            "signals": [],
            "source_distribution": {
                "BBC": 30,
                "Reuters": 30,
                "Guardian": 40,
            },
        }
        anomalies = detect_anomaly(signal_counts)
        single_source = [a for a in anomalies if a["anomaly_type"] == "single_source"]
        assert len(single_source) == 0

    def test_empty_input_no_anomalies(self):
        """Empty input should return no anomalies."""
        anomalies = detect_anomaly({})
        assert len(anomalies) == 0


# ---------------------------------------------------------------------------
# evaluate_alert_triggers
# ---------------------------------------------------------------------------

class TestEvaluateAlertTriggers:
    """Tests for evaluate_alert_triggers() — 5 alert conditions."""

    def test_wild_card_high_impact_triggers_alert(self):
        """Wild Card + impact > 0.7 should trigger HIGH alert."""
        signals = [
            {
                "id": "news-20260224-test-001",
                "title": "Unexpected quantum breakthrough",
                "fssf_type": "Wild Card",
                "impact_score": 0.85,
                "tipping_level": "GREEN",
                "three_horizons": "H2",
                "cross_steeps_count": 1,
                "preliminary_category": "T",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        assert len(alerts) >= 1
        high_alerts = [a for a in alerts if a["severity"] == "HIGH"]
        assert len(high_alerts) >= 1
        assert high_alerts[0]["condition"] == "wild_card_high_impact"

    def test_trend_low_impact_no_alert(self):
        """Trend + low impact should NOT trigger any alert."""
        signals = [
            {
                "id": "news-20260224-test-002",
                "title": "Gradual EV adoption continues",
                "fssf_type": "Trend",
                "impact_score": 0.3,
                "tipping_level": "GREEN",
                "three_horizons": "H1",
                "cross_steeps_count": 1,
                "preliminary_category": "T",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        assert len(alerts) == 0

    def test_red_tipping_point_triggers_critical(self):
        """RED tipping point level should trigger CRITICAL alert."""
        signals = [
            {
                "id": "news-20260224-test-003",
                "title": "Critical system transition",
                "fssf_type": "Discontinuity",
                "impact_score": 0.9,
                "tipping_level": "RED",
                "three_horizons": "H1",
                "cross_steeps_count": 2,
                "preliminary_category": "T",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        critical_alerts = [a for a in alerts if a["severity"] == "CRITICAL"]
        assert len(critical_alerts) >= 1
        assert critical_alerts[0]["condition"] == "tipping_point_red"

    def test_discontinuity_high_impact_triggers_high(self):
        """Discontinuity + impact > 0.7 should trigger HIGH alert."""
        signals = [
            {
                "id": "news-20260224-test-004",
                "title": "Pattern break in energy markets",
                "fssf_type": "Discontinuity",
                "impact_score": 0.8,
                "tipping_level": "GREEN",
                "three_horizons": "H2",
                "cross_steeps_count": 3,
                "preliminary_category": "E",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        high_alerts = [a for a in alerts if a["severity"] == "HIGH"]
        assert len(high_alerts) >= 1
        assert any(a["condition"] == "discontinuity_high_impact" for a in high_alerts)

    def test_h3_weak_signal_cross_steeps_triggers_medium(self):
        """H3 + Weak Signal + cross_steeps >= 2 should trigger MEDIUM alert."""
        signals = [
            {
                "id": "news-20260224-test-005",
                "title": "Emerging AGI research trend",
                "fssf_type": "Weak Signal",
                "impact_score": 0.5,
                "tipping_level": "GREEN",
                "three_horizons": "H3",
                "cross_steeps_count": 3,
                "preliminary_category": "T",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        medium_alerts = [a for a in alerts if a["severity"] == "MEDIUM"]
        assert len(medium_alerts) >= 1
        assert any(a["condition"] == "h3_weak_signal_cross_steeps" for a in medium_alerts)

    def test_anomaly_cluster_triggers_medium(self):
        """3+ anomalies in the same STEEPs category should trigger MEDIUM."""
        signals = [
            {
                "id": f"news-20260224-test-{i:03d}",
                "title": f"Tech anomaly signal {i}",
                "fssf_type": "Emerging Issue",
                "impact_score": 0.5,
                "tipping_level": "GREEN",
                "three_horizons": "H1",
                "cross_steeps_count": 1,
                "preliminary_category": "T",
                "anomaly_flags": [{"anomaly_type": "z_score"}],
            }
            for i in range(1, 5)  # 4 signals, each with 1 anomaly → 4 anomalies in "T"
        ]
        alerts = evaluate_alert_triggers(signals)
        anomaly_alerts = [a for a in alerts if a["condition"] == "anomaly_cluster"]
        assert len(anomaly_alerts) >= 1

    def test_empty_signals_no_alerts(self):
        """No signals should produce no alerts."""
        assert evaluate_alert_triggers([]) == []

    def test_wild_card_low_impact_no_alert(self):
        """Wild Card + low impact (< 0.7) should NOT trigger alert."""
        signals = [
            {
                "id": "test-001",
                "title": "Minor wild card event",
                "fssf_type": "Wild Card",
                "impact_score": 0.3,
                "tipping_level": "GREEN",
                "three_horizons": "H1",
                "cross_steeps_count": 1,
                "preliminary_category": "T",
                "anomaly_flags": [],
            }
        ]
        alerts = evaluate_alert_triggers(signals)
        assert len(alerts) == 0


# ---------------------------------------------------------------------------
# _determine_alert_level — decision table
# ---------------------------------------------------------------------------

class TestDetermineAlertLevel:
    """Tests for _determine_alert_level() — CSD-based alert level decision."""

    def test_red_condition(self):
        """variance_trend > 0.5 AND autocorrelation > 0.7 → RED."""
        assert _determine_alert_level(0.6, 0.8) == "RED"
        assert _determine_alert_level(1.0, 0.9) == "RED"
        assert _determine_alert_level(0.51, 0.71) == "RED"

    def test_orange_condition(self):
        """variance_trend > 0.3 AND autocorrelation > 0.5 → ORANGE."""
        assert _determine_alert_level(0.4, 0.6) == "ORANGE"
        assert _determine_alert_level(0.35, 0.55) == "ORANGE"

    def test_yellow_condition(self):
        """variance_trend > 0.1 OR autocorrelation > 0.3 → YELLOW."""
        assert _determine_alert_level(0.2, 0.0) == "YELLOW"
        assert _determine_alert_level(0.0, 0.4) == "YELLOW"
        assert _determine_alert_level(0.15, 0.2) == "YELLOW"

    def test_green_condition(self):
        """Below all thresholds → GREEN."""
        assert _determine_alert_level(0.0, 0.0) == "GREEN"
        assert _determine_alert_level(0.05, 0.1) == "GREEN"
        assert _determine_alert_level(0.1, 0.3) == "GREEN"

    def test_boundary_red_not_triggered(self):
        """Exactly at boundary (0.5, 0.7) should NOT be RED (> not >=)."""
        assert _determine_alert_level(0.5, 0.7) != "RED"

    def test_boundary_orange_not_triggered(self):
        """Exactly at boundary (0.3, 0.5) should NOT be ORANGE."""
        assert _determine_alert_level(0.3, 0.5) != "ORANGE"

    def test_red_takes_priority_over_orange(self):
        """When both RED and ORANGE conditions met, RED wins."""
        # variance_trend=0.8 > 0.5 AND autocorrelation=0.9 > 0.7 → RED
        assert _determine_alert_level(0.8, 0.9) == "RED"


# ---------------------------------------------------------------------------
# FSSFHints.suggest_fssf_type
# ---------------------------------------------------------------------------

class TestFSSFHintsSuggestType:
    """Tests for the FSSF hint decision tree."""

    def test_event_first_occurrence_is_precursor(self):
        """is_event + is_first_occurrence → Precursor Event."""
        hints = FSSFHints(is_event=True, is_first_occurrence=True)
        fssf_type, confidence = hints.suggest_fssf_type()
        assert fssf_type == "Precursor Event"
        assert confidence > 0.0

    def test_event_pattern_break_is_discontinuity(self):
        """is_event + breaks_pattern → Discontinuity."""
        hints = FSSFHints(is_event=True, breaks_pattern=True)
        fssf_type, confidence = hints.suggest_fssf_type()
        assert fssf_type == "Discontinuity"

    def test_high_novelty_low_sources_is_weak_signal(self):
        """novelty > 0.8 + source_count <= 2 → Weak Signal."""
        hints = FSSFHints(novelty_score=0.9, source_count=1)
        fssf_type, _ = hints.suggest_fssf_type()
        assert fssf_type == "Weak Signal"

    def test_many_sources_broad_global_is_megatrend(self):
        """source_count > 10 + cross_domain >= 3 + global → Megatrend."""
        hints = FSSFHints(
            source_count=15, cross_domain_count=4, impact_breadth="global"
        )
        fssf_type, _ = hints.suggest_fssf_type()
        assert fssf_type == "Megatrend"

    def test_many_sources_is_trend(self):
        """source_count > 10 (not global/broad) → Trend."""
        hints = FSSFHints(
            source_count=15, cross_domain_count=1, impact_breadth="narrow"
        )
        fssf_type, _ = hints.suggest_fssf_type()
        assert fssf_type == "Trend"

    def test_medium_sources_is_emerging_issue(self):
        """3-10 sources → Emerging Issue."""
        hints = FSSFHints(source_count=5, novelty_score=0.3)
        fssf_type, _ = hints.suggest_fssf_type()
        assert fssf_type == "Emerging Issue"

    def test_default_is_weak_signal(self):
        """Default FSSFHints() has source_count=1 and frequency=0 → Weak Signal."""
        hints = FSSFHints()
        fssf_type, confidence = hints.suggest_fssf_type()
        # With defaults: source_count=1, frequency=0.0 → matches Weak Signal condition
        assert fssf_type == "Weak Signal"
        assert confidence > 0.0


# ---------------------------------------------------------------------------
# _variance helper
# ---------------------------------------------------------------------------

class TestVarianceHelper:
    """Tests for the _variance() internal helper."""

    def test_constant_variance_is_zero(self):
        assert _variance([5.0, 5.0, 5.0, 5.0]) == 0.0

    def test_known_variance(self):
        """Variance of [1, 2, 3, 4, 5] = 2.0 (population variance)."""
        v = _variance([1.0, 2.0, 3.0, 4.0, 5.0])
        assert abs(v - 2.0) < 0.001

    def test_empty_list_returns_zero(self):
        assert _variance([]) == 0.0

    def test_single_value_returns_zero(self):
        assert _variance([42.0]) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
