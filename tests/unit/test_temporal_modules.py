"""
Unit tests for v2.2.1 Temporal Enforcement Python modules:
- temporal_anchor.py    — T₀ + scan window calculator
- temporal_gate.py      — programmatic Pipeline Gate
- report_metadata_injector.py — deterministic placeholder fill

Also tests the enhanced TEMP-001 check in validate_report.py (3-level validation).
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Add paths so modules are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "scripts"))

from temporal_anchor import generate_scan_window, load_scan_window, get_workflow_window
from temporal_gate import check_signals_in_window, _parse_date
from report_metadata_injector import build_replacement_map, inject_temporal_metadata
from validate_report import validate_report


# ============================================================================
# Shared fixtures
# ============================================================================

REGISTRY_PATH = str(
    Path(__file__).parent.parent.parent / "env-scanning" / "config" / "workflow-registry.yaml"
)

STANDARD_SKELETON = str(
    Path(__file__).parent.parent.parent
    / ".claude"
    / "skills"
    / "env-scanner"
    / "references"
    / "report-skeleton.md"
)

INTEGRATED_SKELETON = str(
    Path(__file__).parent.parent.parent
    / ".claude"
    / "skills"
    / "env-scanner"
    / "references"
    / "integrated-report-skeleton.md"
)


@pytest.fixture
def fixed_anchor():
    """A deterministic anchor time for reproducible tests."""
    return datetime(2026, 2, 10, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def scan_window_state(tmp_path, fixed_anchor):
    """Generate a scan window state file using real SOT with fixed anchor."""
    output = str(tmp_path / "scan-window.json")
    result = generate_scan_window(REGISTRY_PATH, output_path=output, anchor=fixed_anchor)
    return output, result


@pytest.fixture
def sample_signals_file(tmp_path, fixed_anchor):
    """Create a signal JSON file with signals inside and outside the window."""
    signals = {
        "metadata": {"workflow": "wf1-general", "scan_date": "2026-02-10"},
        "items": [
            {
                "id": "gen-20260210-001",
                "title": "Signal within window",
                "source": {
                    "name": "TestSource",
                    "published_date": (fixed_anchor - timedelta(hours=12)).isoformat(),
                },
            },
            {
                "id": "gen-20260210-002",
                "title": "Signal at window edge",
                "source": {
                    "name": "TestSource",
                    "published_date": (fixed_anchor - timedelta(hours=23)).isoformat(),
                },
            },
            {
                "id": "gen-20260210-003",
                "title": "Signal outside window (too old)",
                "source": {
                    "name": "TestSource",
                    "published_date": (fixed_anchor - timedelta(hours=48)).isoformat(),
                },
            },
            {
                "id": "gen-20260210-004",
                "title": "Signal with no date",
                "source": {"name": "TestSource"},
            },
        ],
    }
    path = tmp_path / "signals.json"
    path.write_text(json.dumps(signals, ensure_ascii=False), encoding="utf-8")
    return str(path)


# ============================================================================
# temporal_anchor.py tests
# ============================================================================

class TestTemporalAnchor:
    def test_generate_returns_dict(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        assert isinstance(result, dict)

    def test_anchor_timestamp_matches(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        assert result["anchor_timestamp"] == fixed_anchor.isoformat()

    def test_all_enabled_workflows_present(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        workflows = result.get("workflows", {})
        # At minimum, wf1-general should be present
        assert "wf1-general" in workflows

    def test_wf1_window_is_24h(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        wf1 = result["workflows"]["wf1-general"]
        assert wf1["lookback_hours"] == 24
        # Verify window_start is 24h before anchor
        start = datetime.fromisoformat(wf1["window_start"])
        end = datetime.fromisoformat(wf1["window_end"])
        assert (end - start).total_seconds() == 24 * 3600

    def test_wf2_window_is_48h(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        wf2 = result.get("workflows", {}).get("wf2-arxiv", {})
        if wf2:
            assert wf2["lookback_hours"] == 48
            start = datetime.fromisoformat(wf2["window_start"])
            end = datetime.fromisoformat(wf2["window_end"])
            assert (end - start).total_seconds() == 48 * 3600

    def test_effective_start_includes_tolerance(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        wf1 = result["workflows"]["wf1-general"]
        eff_start = datetime.fromisoformat(wf1["effective_start"])
        window_start = datetime.fromisoformat(wf1["window_start"])
        # effective_start should be earlier than window_start
        assert eff_start < window_start

    def test_korean_formatted_times_present(self, fixed_anchor):
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        assert "anchor_time_ko" in result
        assert "년" in result["anchor_time_ko"]
        assert "월" in result["anchor_time_ko"]

    def test_english_formatted_times_present(self, fixed_anchor):
        """v1.1.0: EN date formats must be present alongside KO."""
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        assert "anchor_time_en" in result
        # English format: "February 10, 2026 ..."
        assert "February" in result["anchor_time_en"]
        assert "UTC" in result["anchor_time_en"]

    def test_english_per_wf_dates(self, fixed_anchor):
        """v1.1.0: Each WF must have _en formatted dates."""
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        for wf_name, wf in result["workflows"].items():
            assert "window_start_en" in wf, f"{wf_name}: missing window_start_en"
            assert "window_end_en" in wf, f"{wf_name}: missing window_end_en"
            assert "UTC" in wf["window_start_en"]
            # EN format should NOT contain Korean characters
            assert "년" not in wf["window_start_en"]
            assert "월" not in wf["window_start_en"]

    def test_en_ko_dates_same_moment(self, fixed_anchor):
        """EN and KO date strings represent the same time (both from same datetime)."""
        result = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        wf1 = result["workflows"]["wf1-general"]
        # window_start = anchor - 24h = Feb 9, 09:00 UTC
        # Both formats must share the same time component and timezone
        assert "09:00" in wf1["window_start_ko"]
        assert "09:00" in wf1["window_start_en"]
        assert wf1["window_start_ko"].endswith("UTC")
        assert wf1["window_start_en"].endswith("UTC")

    def test_writes_state_file(self, tmp_path, fixed_anchor):
        output = str(tmp_path / "state.json")
        generate_scan_window(REGISTRY_PATH, output_path=output, anchor=fixed_anchor)
        assert Path(output).exists()
        with open(output, "r") as f:
            data = json.load(f)
        assert data["anchor_timestamp"] == fixed_anchor.isoformat()

    def test_load_scan_window(self, scan_window_state):
        path, _ = scan_window_state
        loaded = load_scan_window(path)
        assert "anchor_timestamp" in loaded
        assert "workflows" in loaded

    def test_get_workflow_window(self, scan_window_state):
        _, state = scan_window_state
        wf = get_workflow_window(state, "wf1-general")
        assert "window_start" in wf
        assert "window_end" in wf
        assert "lookback_hours" in wf

    def test_get_workflow_window_nonexistent(self, scan_window_state):
        _, state = scan_window_state
        with pytest.raises(KeyError):
            get_workflow_window(state, "nonexistent-workflow")

    def test_missing_registry_raises(self):
        with pytest.raises(FileNotFoundError):
            generate_scan_window("/nonexistent/registry.yaml")

    def test_determinism(self, fixed_anchor):
        """Same anchor produces identical results every time (except generated_at timestamp)."""
        r1 = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        r2 = generate_scan_window(REGISTRY_PATH, anchor=fixed_anchor)
        # Exclude generated_at (wallclock of function call, not controllable)
        r1.pop("generated_at", None)
        r2.pop("generated_at", None)
        assert r1 == r2


# ============================================================================
# temporal_gate.py tests
# ============================================================================

class TestTemporalGate:
    def test_all_signals_within_window(self, tmp_path, fixed_anchor, scan_window_state):
        """All signals within window → PASS."""
        sw_path, _ = scan_window_state
        signals = {
            "items": [
                {
                    "id": "sig-001",
                    "source": {
                        "published_date": (fixed_anchor - timedelta(hours=6)).isoformat(),
                    },
                },
                {
                    "id": "sig-002",
                    "source": {
                        "published_date": (fixed_anchor - timedelta(hours=12)).isoformat(),
                    },
                },
            ]
        }
        sig_path = str(tmp_path / "signals.json")
        Path(sig_path).write_text(json.dumps(signals), encoding="utf-8")

        result = check_signals_in_window(sig_path, sw_path, "wf1-general")
        assert result["gate_status"] == "PASS"
        assert result["statistics"]["within_window"] == 2
        assert result["statistics"]["outside_window"] == 0

    def test_old_signal_detected(self, sample_signals_file, scan_window_state):
        """Signal 48h old should be outside wf1 24h window."""
        sw_path, _ = scan_window_state
        result = check_signals_in_window(sample_signals_file, sw_path, "wf1-general")
        # Signal gen-20260210-003 is 48h old → outside 24h window
        assert result["statistics"]["outside_window"] >= 1
        outside_ids = [v["signal_id"] for v in result.get("violations", [])]
        assert "gen-20260210-003" in outside_ids

    def test_writes_output_when_requested(self, sample_signals_file, scan_window_state, tmp_path):
        """When output_path given, writes result JSON."""
        sw_path, _ = scan_window_state
        out = str(tmp_path / "gate-result.json")
        check_signals_in_window(sample_signals_file, sw_path, "wf1-general", output_path=out)
        assert Path(out).exists()

    def test_missing_signals_file_raises(self, scan_window_state):
        sw_path, _ = scan_window_state
        with pytest.raises(FileNotFoundError):
            check_signals_in_window("/nonexistent.json", sw_path, "wf1-general")

    def test_missing_scan_window_raises(self, sample_signals_file):
        with pytest.raises(FileNotFoundError):
            check_signals_in_window(sample_signals_file, "/nonexistent.json", "wf1-general")

    def test_unknown_workflow_raises(self, sample_signals_file, scan_window_state):
        sw_path, _ = scan_window_state
        with pytest.raises(KeyError):
            check_signals_in_window(sample_signals_file, sw_path, "nonexistent-wf")

    def test_no_date_signals_kept(self, sample_signals_file, scan_window_state):
        """Signals with no published_date should not be removed."""
        sw_path, _ = scan_window_state
        result = check_signals_in_window(sample_signals_file, sw_path, "wf1-general")
        # gen-20260210-004 has no date — should NOT appear in violations
        violation_ids = [v["signal_id"] for v in result.get("violations", [])]
        assert "gen-20260210-004" not in violation_ids

    def test_empty_signals_returns_pass(self, tmp_path, scan_window_state):
        """Empty signal list should PASS (nothing to filter)."""
        sw_path, _ = scan_window_state
        signals = {"items": []}
        sig_path = str(tmp_path / "empty.json")
        Path(sig_path).write_text(json.dumps(signals), encoding="utf-8")

        result = check_signals_in_window(sig_path, sw_path, "wf1-general")
        assert result["gate_status"] == "PASS"


class TestParseDateFormats:
    """Test _parse_date handles all expected date formats."""

    def test_iso8601_full(self):
        d = _parse_date("2026-02-10T09:00:00+00:00")
        assert d is not None
        assert d.year == 2026 and d.month == 2 and d.day == 10

    def test_iso8601_no_tz(self):
        d = _parse_date("2026-02-10T09:00:00")
        assert d is not None

    def test_date_only(self):
        d = _parse_date("2026-02-10")
        assert d is not None
        assert d.hour == 0

    def test_none_for_garbage(self):
        assert _parse_date("not a date") is None
        assert _parse_date("") is None

    def test_none_for_none(self):
        assert _parse_date(None) is None


# ============================================================================
# report_metadata_injector.py tests
# ============================================================================

class TestReportMetadataInjector:
    def test_build_replacement_map_wf1(self, scan_window_state):
        _, state = scan_window_state
        rmap = build_replacement_map(state, "wf1-general")
        assert "SCAN_WINDOW_START" in rmap
        assert "SCAN_WINDOW_END" in rmap
        assert "SCAN_ANCHOR_TIMESTAMP" in rmap
        assert "LOOKBACK_HOURS" in rmap

    def test_build_replacement_map_integrated(self, scan_window_state):
        _, state = scan_window_state
        rmap = build_replacement_map(state, "integrated")
        assert "WF1_LOOKBACK_HOURS" in rmap
        assert "SCAN_WINDOW_START" in rmap

    def test_inject_replaces_temporal_placeholders(self, scan_window_state, tmp_path):
        sw_path, _ = scan_window_state
        # Create a mini skeleton with temporal + non-temporal placeholders
        skeleton = tmp_path / "skeleton.md"
        skeleton.write_text(
            "# Report\n\nScan: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}}\n"
            "T₀: {{SCAN_ANCHOR_TIMESTAMP}}\n"
            "Hours: {{LOOKBACK_HOURS}}\n"
            "Signals: {{SIGNAL_BLOCKS}}\n"
            "Analysis: {{STRATEGIC_IMPLICATIONS}}\n",
            encoding="utf-8",
        )
        content, report = inject_temporal_metadata(
            str(skeleton), sw_path, "wf1-general"
        )
        # Temporal placeholders should be filled
        assert "{{SCAN_WINDOW_START}}" not in content
        assert "{{SCAN_WINDOW_END}}" not in content
        assert "{{SCAN_ANCHOR_TIMESTAMP}}" not in content
        assert "{{LOOKBACK_HOURS}}" not in content
        # Non-temporal placeholders should be preserved
        assert "{{SIGNAL_BLOCKS}}" in content
        assert "{{STRATEGIC_IMPLICATIONS}}" in content
        # Report should show what was replaced
        assert report["temporal_placeholders_replaced"] >= 4
        assert report["non_deterministic_placeholders_preserved"] >= 2

    def test_inject_writes_output_file(self, scan_window_state, tmp_path):
        sw_path, _ = scan_window_state
        skeleton = tmp_path / "skel.md"
        skeleton.write_text("Window: {{SCAN_WINDOW_START}}\n", encoding="utf-8")
        output = str(tmp_path / "prepared.md")
        inject_temporal_metadata(str(skeleton), sw_path, "wf1-general", output_path=output)
        assert Path(output).exists()
        written = Path(output).read_text(encoding="utf-8")
        assert "{{SCAN_WINDOW_START}}" not in written

    def test_missing_skeleton_raises(self, scan_window_state):
        sw_path, _ = scan_window_state
        with pytest.raises(FileNotFoundError):
            inject_temporal_metadata("/nonexistent.md", sw_path, "wf1-general")

    def test_missing_state_raises(self, tmp_path):
        skeleton = tmp_path / "skel.md"
        skeleton.write_text("{{SCAN_WINDOW_START}}", encoding="utf-8")
        with pytest.raises(FileNotFoundError):
            inject_temporal_metadata(str(skeleton), "/nonexistent.json", "wf1-general")

    @pytest.mark.skipif(
        not Path(STANDARD_SKELETON).exists(),
        reason="Standard skeleton not available",
    )
    def test_real_standard_skeleton(self, scan_window_state):
        """Inject into the actual standard skeleton — verify no temporal placeholders remain."""
        sw_path, _ = scan_window_state
        content, report = inject_temporal_metadata(STANDARD_SKELETON, sw_path, "wf1-general")
        for ph in ["SCAN_WINDOW_START", "SCAN_WINDOW_END", "SCAN_ANCHOR_TIMESTAMP", "LOOKBACK_HOURS"]:
            assert f"{{{{{ph}}}}}" not in content, f"Temporal placeholder {{{{{ph}}}}} not replaced"
        assert report["temporal_placeholders_replaced"] >= 1

    @pytest.mark.skipif(
        not Path(INTEGRATED_SKELETON).exists(),
        reason="Integrated skeleton not available",
    )
    def test_real_integrated_skeleton(self, scan_window_state):
        """Inject into actual integrated skeleton — all WF lookback hours filled."""
        sw_path, _ = scan_window_state
        content, report = inject_temporal_metadata(INTEGRATED_SKELETON, sw_path, "integrated")
        for ph in ["SCAN_WINDOW_START", "SCAN_WINDOW_END", "SCAN_ANCHOR_TIMESTAMP"]:
            assert f"{{{{{ph}}}}}" not in content, f"Temporal placeholder {{{{{ph}}}}} not replaced"


class TestMetadataInjectorLanguage:
    """v1.2.0: Test --language parameter for EN/KO date format selection."""

    def test_default_language_is_ko(self, scan_window_state):
        """Default language should produce Korean dates."""
        _, state = scan_window_state
        rmap = build_replacement_map(state, "wf1-general")
        assert "년" in rmap["SCAN_WINDOW_START"]

    def test_language_ko_explicit(self, scan_window_state):
        """Explicit ko produces Korean dates."""
        _, state = scan_window_state
        rmap = build_replacement_map(state, "wf1-general", language="ko")
        assert "년" in rmap["SCAN_WINDOW_START"]
        assert "년" in rmap["SCAN_ANCHOR_TIMESTAMP"]

    def test_language_en(self, scan_window_state):
        """EN language produces English dates (no Korean characters)."""
        _, state = scan_window_state
        rmap = build_replacement_map(state, "wf1-general", language="en")
        assert "년" not in rmap["SCAN_WINDOW_START"]
        assert "년" not in rmap["SCAN_ANCHOR_TIMESTAMP"]
        assert "UTC" in rmap["SCAN_WINDOW_START"]

    def test_language_en_integrated(self, scan_window_state):
        """EN language works for integrated reports (broadest window)."""
        _, state = scan_window_state
        rmap = build_replacement_map(state, language="en")
        assert "SCAN_WINDOW_START" in rmap
        assert "년" not in rmap["SCAN_WINDOW_START"]

    def test_inject_with_language_en(self, scan_window_state, tmp_path):
        """Full injection with --language en produces English dates."""
        sw_path, _ = scan_window_state
        skeleton = tmp_path / "skeleton.md"
        skeleton.write_text(
            "Scan: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}}\n"
            "T₀: {{SCAN_ANCHOR_TIMESTAMP}}\n"
            "Signals: {{SIGNAL_BLOCKS}}\n",
            encoding="utf-8",
        )
        content, report = inject_temporal_metadata(
            str(skeleton), sw_path, "wf1-general", language="en"
        )
        assert "{{SCAN_WINDOW_START}}" not in content
        assert "년" not in content  # No Korean date chars
        assert "UTC" in content
        assert report["language"] == "en"
        assert "{{SIGNAL_BLOCKS}}" in content  # Non-temporal preserved

    def test_inject_with_language_ko(self, scan_window_state, tmp_path):
        """Full injection with --language ko produces Korean dates."""
        sw_path, _ = scan_window_state
        skeleton = tmp_path / "skeleton.md"
        skeleton.write_text(
            "스캔: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}}\n",
            encoding="utf-8",
        )
        content, report = inject_temporal_metadata(
            str(skeleton), sw_path, "wf1-general", language="ko"
        )
        assert "{{SCAN_WINDOW_START}}" not in content
        assert "년" in content
        assert report["language"] == "ko"

    def test_language_backward_compatibility(self, scan_window_state, tmp_path):
        """Without language param (default), behavior matches KO (backward compat)."""
        sw_path, _ = scan_window_state
        skeleton = tmp_path / "skeleton.md"
        skeleton.write_text("{{SCAN_WINDOW_START}}", encoding="utf-8")
        content_default, _ = inject_temporal_metadata(
            str(skeleton), sw_path, "wf1-general"
        )
        content_ko, _ = inject_temporal_metadata(
            str(skeleton), sw_path, "wf1-general", language="ko"
        )
        assert content_default == content_ko


# ============================================================================
# Enhanced TEMP-001 tests (validate_report.py)
# ============================================================================

def _make_signal_block(n: int) -> str:
    """Generate a single signal block with all 9 fields."""
    return (
        f"### 우선순위 {n}: 신호 {n}\n\n"
        f"- **신뢰도**: pSST 미산출\n\n"
        f"1. **분류**: 기술 (T)\n"
        f"2. **출처**: Source, 2026-02-10, ID: sig-{n:03d}\n"
        f"3. **핵심 사실**: 핵심 사실 {n}.\n"
        f"4. **정량 지표**:\n   - 영향도: 8.0/10\n"
        f"5. **영향도**: ⭐⭐⭐⭐ (8.0/10) — 높음\n"
        f"6. **상세 설명**: 상세 설명 {n}.\n"
        f"7. **추론**: 전략적 해석 {n}.\n"
        f"8. **이해관계자**: A, B, C\n"
        f"9. **모니터링 지표**:\n   - 지표 A\n\n---\n\n"
    )


def _make_report_with_temporal(include_window_text=True, include_datetime=True, include_unfilled_placeholder=False):
    """Create a synthetic report for TEMP-001 testing."""
    sections = []
    sections.append("# 일일 환경 스캐닝 보고서\n\n**날짜**: 2026년 2월 10일\n\n---\n\n")

    # Section 1
    sections.append("## 1. 경영진 요약\n\n### 오늘의 핵심 발견 (Top 3 신호)\n\n")
    for i in range(1, 4):
        sections.append(f"{i}. **신호 {i}** — 요약\n\n")
    sections.append("### 주요 변화 요약\n- 신규: 100개\n- 상위: 15개\n\n")

    if include_window_text:
        sections.append("**스캔 시간 범위**: ")
        if include_datetime:
            sections.append("2026년 2월 9일 09:00 ~ 2026년 2월 10일 09:00 (UTC)\n")
            sections.append("**기준 시점 (T₀)**: 2026년 2월 10일 09:00 UTC\n\n")
        else:
            sections.append("(정보 없음)\n\n")
    if include_unfilled_placeholder:
        sections.append("Window: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}}\n\n")
    sections.append("---\n\n")

    # Section 2 with 15 signals
    sections.append("## 2. 신규 탐지 신호\n\n---\n\n")
    for i in range(1, 16):
        sections.append(_make_signal_block(i))

    # Section 3
    sections.append("## 3. 기존 신호 업데이트\n\n")
    sections.append("### 3.1 강화 추세 (Strengthening)\n- SIG-001\n\n")
    sections.append("### 3.2 약화 추세 (Weakening)\n- SIG-002\n\n")
    sections.append("### 3.3 신호 상태 요약\n- 요약\n\n---\n\n")

    # Section 4
    sections.append("## 4. 패턴 및 연결고리\n\n")
    sections.append("### 4.1 신호 간 교차 영향\n- A ↔ B (+3)\n- C ↔ D (+2)\n- E ↔ F (+4)\n\n")
    sections.append("### 4.2 떠오르는 테마\n1. 테마 A\n\n---\n\n")

    # Section 5
    sections.append("## 5. 전략적 시사점\n\n")
    sections.append("### 5.1 즉시 조치 필요\n1. 조치 A\n\n")
    sections.append("### 5.2 중기 모니터링\n1. 모니터링 A\n\n")
    sections.append("### 5.3 모니터링 강화 필요 영역\n- 영역 A\n\n---\n\n")

    # Section 7
    sections.append("## 7. 신뢰도 분석\n\npSST 분포\n\n---\n\n")

    # Section 8
    sections.append("## 8. 부록\n\n전체 신호 목록\n\n")

    return "".join(sections)


class TestTemp001Enhanced:
    def test_temp001_passes_with_full_temporal(self, tmp_path):
        """TEMP-001 should PASS when window text + datetime values present, no unfilled placeholders."""
        f = tmp_path / "good.md"
        f.write_text(_make_report_with_temporal(
            include_window_text=True,
            include_datetime=True,
            include_unfilled_placeholder=False,
        ), encoding="utf-8")
        result = validate_report(str(f))
        temp001 = next(r for r in result.results if r.check_id == "TEMP-001")
        assert temp001.passed, f"TEMP-001 should pass: {temp001.detail}"

    def test_temp001_fails_no_window_text(self, tmp_path):
        """TEMP-001 should FAIL when scan window text is absent."""
        f = tmp_path / "no-window.md"
        f.write_text(_make_report_with_temporal(
            include_window_text=False,
            include_datetime=False,
        ), encoding="utf-8")
        result = validate_report(str(f))
        temp001 = next(r for r in result.results if r.check_id == "TEMP-001")
        assert not temp001.passed, "TEMP-001 should fail without window text"

    def test_temp001_fails_with_unfilled_placeholder(self, tmp_path):
        """TEMP-001 should FAIL when temporal placeholders remain unfilled."""
        f = tmp_path / "unfilled.md"
        f.write_text(_make_report_with_temporal(
            include_window_text=True,
            include_datetime=True,
            include_unfilled_placeholder=True,
        ), encoding="utf-8")
        result = validate_report(str(f))
        temp001 = next(r for r in result.results if r.check_id == "TEMP-001")
        assert not temp001.passed, "TEMP-001 should fail with unfilled temporal placeholders"

    def test_temp001_fails_no_datetime_values(self, tmp_path):
        """TEMP-001 should FAIL when no actual datetime values exist."""
        f = tmp_path / "no-datetime.md"
        f.write_text(_make_report_with_temporal(
            include_window_text=True,
            include_datetime=False,
        ), encoding="utf-8")
        result = validate_report(str(f))
        temp001 = next(r for r in result.results if r.check_id == "TEMP-001")
        assert not temp001.passed, "TEMP-001 should fail without actual datetime values"


# ============================================================================
# Integration: End-to-end flow (anchor → gate → injector → validation)
# ============================================================================

class TestEndToEndFlow:
    """Test the complete temporal enforcement chain."""

    def test_anchor_to_gate_flow(self, tmp_path, fixed_anchor):
        """anchor generates state → gate uses it to filter signals."""
        # Step 1: Generate state
        sw_path = str(tmp_path / "scan-window.json")
        generate_scan_window(REGISTRY_PATH, output_path=sw_path, anchor=fixed_anchor)

        # Step 2: Create signals (one inside, one outside)
        signals = {
            "items": [
                {
                    "id": "inside-001",
                    "source": {"published_date": (fixed_anchor - timedelta(hours=6)).isoformat()},
                },
                {
                    "id": "outside-001",
                    "source": {"published_date": (fixed_anchor - timedelta(days=5)).isoformat()},
                },
            ]
        }
        sig_path = str(tmp_path / "signals.json")
        Path(sig_path).write_text(json.dumps(signals), encoding="utf-8")

        # Step 3: Gate check
        result = check_signals_in_window(sig_path, sw_path, "wf1-general")
        assert result["statistics"]["within_window"] >= 1
        assert result["statistics"]["outside_window"] >= 1

    def test_anchor_to_injector_flow(self, tmp_path, fixed_anchor):
        """anchor generates state → injector fills temporal placeholders."""
        # Step 1: Generate state
        sw_path = str(tmp_path / "scan-window.json")
        generate_scan_window(REGISTRY_PATH, output_path=sw_path, anchor=fixed_anchor)

        # Step 2: Create mini skeleton
        skeleton = tmp_path / "skeleton.md"
        skeleton.write_text(
            "Scan: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}}\n"
            "Analysis: {{SIGNAL_BLOCKS}}\n",
            encoding="utf-8",
        )

        # Step 3: Inject
        content, report = inject_temporal_metadata(str(skeleton), sw_path, "wf1-general")
        assert "{{SCAN_WINDOW_START}}" not in content
        assert "{{SIGNAL_BLOCKS}}" in content  # preserved for LLM
