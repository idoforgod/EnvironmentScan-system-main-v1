"""
Unit tests for validate_completion.py (Master Gate M4)

Tests the Completion Gate validator against:
- Synthetic complete deliverables (should PASS)
- Missing KO reports (CG-002 FAIL)
- Unfilled PLACEHOLDER tokens (CG-005 FAIL)
- Skeleton template headers (CG-009 FAIL)
- Low Korean character ratio (CG-007 FAIL)
- Missing timeline map (CG-006 FAIL)

Origin: Created 2026-03-09 after autopilot mode skipped 3 deliverable types.
"""

import json
import os
import sys
import textwrap
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "scripts"))
from validate_completion import (
    validate_completion,
    _korean_char_ratio,
    _count_placeholders,
    _file_exists_and_nonempty,
    _resolve_wf_paths,
    _resolve_int_paths,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCAN_DATE = "2026-01-15"

# Minimal SOT structure for testing
MINIMAL_SOT = {
    "workflows": {
        "wf1-general": {
            "enabled": True,
            "data_root": "env-scanning/wf1-general",
            "paths": {
                "reports_daily": "reports/daily/",
                "reports_archive": "reports/archive/",
            },
            "deliverables": {
                "report_en": "environmental-scan-{date}.md",
                "report_ko": "environmental-scan-{date}-ko.md",
            },
        },
    },
    "integration": {
        "output_root": "env-scanning/integrated",
        "paths": {
            "reports_daily": "reports/daily/",
            "reports_archive": "reports/archive/",
        },
        "deliverables": {
            "report_en": "integrated-scan-{date}.md",
            "report_ko": "integrated-scan-{date}-ko.md",
            "timeline_map": "timeline-map-{date}.md",
        },
    },
    "system": {
        "signal_evolution": {
            "enabled": True,
            "timeline_map": {"enabled": True},
        },
    },
}

# Korean-heavy content for KO reports (≥30% Korean)
KOREAN_REPORT = textwrap.dedent("""\
    # 일일 환경스캐닝 보고서

    **날짜**: 2026-01-15
    **워크플로우**: 일반 환경스캐닝

    ## 요약

    오늘의 주요 발견 사항을 요약합니다. 기술, 사회, 경제, 환경, 정치, 정신 분야에서
    중요한 변화 신호를 감지했습니다. 특히 인공지능 거버넌스와 관련된 신호가 강하게 나타났습니다.

    ## 상세 분석

    기술 분야에서는 대규모 언어 모델의 발전이 계속되고 있으며, 이로 인한 사회적 영향이
    점차 구체화되고 있습니다. 경제 분야에서는 글로벌 공급망 재편이 가속화되고 있습니다.
""")

# English-only content (will fail CG-007)
ENGLISH_REPORT = textwrap.dedent("""\
    # Daily Environmental Scanning Report

    **Date**: 2026-01-15
    **Workflow**: WF1 General Environmental Scanning

    ## Executive Summary

    Today we detected significant signals across Technology, Social, and Economic domains.
    The AI governance cluster remains the strongest theme.
""")

# Skeleton template (will fail CG-009)
SKELETON_REPORT = textwrap.dedent("""\
    # WF1 Report Skeleton Template

    > **Purpose**: The report-generator agent fills this structure.

    ## Section 1
    [Data pending: EXECUTIVE_SUMMARY]
""")

# Report with placeholders (will fail CG-005)
PLACEHOLDER_REPORT = textwrap.dedent("""\
    # 일일 환경스캐닝 보고서

    ## 요약
    {{EXECUTIVE_SUMMARY}}
    오늘의 분석 결과를 요약합니다.

    ## 분석
    [Data pending for ANALYSIS_CONTENT]
""")


@pytest.fixture
def setup_complete_deliverables(tmp_path):
    """Create a complete set of deliverables that should PASS all checks."""
    # Create SOT file
    sot_dir = tmp_path / "env-scanning" / "config"
    sot_dir.mkdir(parents=True)
    sot_path = sot_dir / "workflow-registry.yaml"

    # Adjust SOT paths to use tmp_path
    sot = {
        "workflows": {
            "wf1-general": {
                "enabled": True,
                "data_root": str(tmp_path / "env-scanning" / "wf1-general"),
                "paths": {
                    "reports_daily": "reports/daily/",
                    "reports_archive": "reports/archive/",
                },
                "deliverables": {
                    "report_en": "environmental-scan-{date}.md",
                    "report_ko": "environmental-scan-{date}-ko.md",
                },
            },
        },
        "integration": {
            "output_root": str(tmp_path / "env-scanning" / "integrated"),
            "paths": {
                "reports_daily": "reports/daily/",
                "reports_archive": "reports/archive/",
            },
            "deliverables": {
                "report_en": "integrated-scan-{date}.md",
                "report_ko": "integrated-scan-{date}-ko.md",
                "timeline_map": "timeline-map-{date}.md",
            },
        },
        "system": {
            "signal_evolution": {
                "enabled": True,
                "timeline_map": {"enabled": True},
            },
        },
    }

    import yaml
    sot_path.write_text(yaml.dump(sot), encoding="utf-8")

    # Create WF1 reports
    wf1_daily = tmp_path / "env-scanning" / "wf1-general" / "reports" / "daily"
    wf1_daily.mkdir(parents=True)
    (wf1_daily / f"environmental-scan-{SCAN_DATE}.md").write_text(ENGLISH_REPORT, encoding="utf-8")
    (wf1_daily / f"environmental-scan-{SCAN_DATE}-ko.md").write_text(KOREAN_REPORT, encoding="utf-8")

    # Create WF1 archives
    wf1_arch = tmp_path / "env-scanning" / "wf1-general" / "reports" / "archive" / "2026" / "01"
    wf1_arch.mkdir(parents=True)
    (wf1_arch / f"environmental-scan-{SCAN_DATE}.md").write_text(ENGLISH_REPORT, encoding="utf-8")
    (wf1_arch / f"environmental-scan-{SCAN_DATE}-ko.md").write_text(KOREAN_REPORT, encoding="utf-8")

    # Create integrated reports
    int_daily = tmp_path / "env-scanning" / "integrated" / "reports" / "daily"
    int_daily.mkdir(parents=True)
    (int_daily / f"integrated-scan-{SCAN_DATE}.md").write_text(ENGLISH_REPORT, encoding="utf-8")
    (int_daily / f"integrated-scan-{SCAN_DATE}-ko.md").write_text(KOREAN_REPORT, encoding="utf-8")
    (int_daily / f"timeline-map-{SCAN_DATE}.md").write_text(
        "# Timeline Map\n\n" + "Signal evolution analysis across all workflows. " * 10,
        encoding="utf-8"
    )

    # Create integrated archives
    int_arch = tmp_path / "env-scanning" / "integrated" / "reports" / "archive" / "2026" / "01"
    int_arch.mkdir(parents=True)
    (int_arch / f"integrated-scan-{SCAN_DATE}.md").write_text(ENGLISH_REPORT, encoding="utf-8")
    (int_arch / f"integrated-scan-{SCAN_DATE}-ko.md").write_text(KOREAN_REPORT, encoding="utf-8")

    return str(sot_path)


# ---------------------------------------------------------------------------
# Unit tests: helper functions
# ---------------------------------------------------------------------------

class TestKoreanCharRatio:
    def test_pure_korean(self):
        assert _korean_char_ratio("안녕하세요") >= 0.99

    def test_pure_english(self):
        assert _korean_char_ratio("Hello World") == 0.0

    def test_mixed(self):
        ratio = _korean_char_ratio("안녕하세요 Hello")
        assert 0.3 <= ratio <= 0.7

    def test_empty(self):
        assert _korean_char_ratio("") == 0.0

    def test_whitespace_only(self):
        assert _korean_char_ratio("   \n\t  ") == 0.0


class TestCountPlaceholders:
    def test_double_brace(self):
        assert _count_placeholders("{{PLACEHOLDER}}") == 1

    def test_data_pending(self):
        assert _count_placeholders("[Data pending: SOMETHING]") == 1

    def test_data_pending_for(self):
        assert _count_placeholders("[Data pending for ANALYSIS]") == 1

    def test_no_placeholders(self):
        assert _count_placeholders("Normal text without placeholders") == 0

    def test_multiple(self):
        text = "{{A}} and {{B}} and [Data pending: C]"
        assert _count_placeholders(text) == 3


class TestResolveWfPaths:
    def test_basic_resolution(self):
        cfg = {
            "paths": {"reports_daily": "reports/daily/", "reports_archive": "reports/archive/"},
            "deliverables": {"report_en": "scan-{date}.md", "report_ko": "scan-{date}-ko.md"},
        }
        result = _resolve_wf_paths(cfg)
        assert result["en_pattern"] == "reports/daily/scan-{date}.md"
        assert result["ko_pattern"] == "reports/daily/scan-{date}-ko.md"
        assert result["archive_en"] == "reports/archive/{year}/{month}/scan-{date}.md"

    def test_missing_deliverables(self):
        cfg = {"paths": {"reports_daily": "reports/daily/"}}
        result = _resolve_wf_paths(cfg)
        assert result["en_pattern"] == ""


class TestResolveIntPaths:
    def test_with_timeline(self):
        cfg = {
            "paths": {"reports_daily": "reports/daily/", "reports_archive": "reports/archive/"},
            "deliverables": {
                "report_en": "int-{date}.md",
                "report_ko": "int-{date}-ko.md",
                "timeline_map": "timeline-{date}.md",
            },
        }
        result = _resolve_int_paths(cfg)
        assert result["timeline_map"] == "reports/daily/timeline-{date}.md"


# ---------------------------------------------------------------------------
# Integration tests: full validate_completion
# ---------------------------------------------------------------------------

class TestValidateCompletion:
    def test_complete_deliverables_pass(self, setup_complete_deliverables):
        """All deliverables present → PASS."""
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        # Debug: print failed checks if any
        failed = [c for c in result["checks"] if not c["passed"]]
        assert result["status"] == "PASS", f"Failed checks: {failed}"
        assert result["critical_failures"] == 0

    def test_missing_ko_report(self, setup_complete_deliverables, tmp_path):
        """Missing KO report → CG-002 FAIL."""
        ko_path = tmp_path / "env-scanning" / "wf1-general" / "reports" / "daily" / f"environmental-scan-{SCAN_DATE}-ko.md"
        ko_path.unlink()
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        assert result["status"] == "FAIL"
        cg002_checks = [c for c in result["checks"] if c["id"] == "CG-002"]
        assert any(not c["passed"] for c in cg002_checks)

    def test_placeholder_tokens(self, setup_complete_deliverables, tmp_path):
        """Report with PLACEHOLDERs → CG-005 FAIL."""
        en_path = tmp_path / "env-scanning" / "wf1-general" / "reports" / "daily" / f"environmental-scan-{SCAN_DATE}.md"
        en_path.write_text(PLACEHOLDER_REPORT, encoding="utf-8")
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        cg005_checks = [c for c in result["checks"] if c["id"] == "CG-005"]
        assert any(not c["passed"] for c in cg005_checks)

    def test_skeleton_header(self, setup_complete_deliverables, tmp_path):
        """Report with 'Skeleton Template' header → CG-009 FAIL."""
        en_path = tmp_path / "env-scanning" / "wf1-general" / "reports" / "daily" / f"environmental-scan-{SCAN_DATE}.md"
        en_path.write_text(SKELETON_REPORT, encoding="utf-8")
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        cg009_checks = [c for c in result["checks"] if c["id"] == "CG-009"]
        assert any(not c["passed"] for c in cg009_checks)

    def test_low_korean_ratio(self, setup_complete_deliverables, tmp_path):
        """KO report with <30% Korean → CG-007 FAIL."""
        ko_path = tmp_path / "env-scanning" / "wf1-general" / "reports" / "daily" / f"environmental-scan-{SCAN_DATE}-ko.md"
        ko_path.write_text(ENGLISH_REPORT, encoding="utf-8")  # English in KO file
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        cg007_checks = [c for c in result["checks"] if c["id"] == "CG-007"]
        assert any(not c["passed"] for c in cg007_checks)

    def test_missing_timeline_map(self, setup_complete_deliverables, tmp_path):
        """Missing timeline map → CG-006 FAIL."""
        tm_path = tmp_path / "env-scanning" / "integrated" / "reports" / "daily" / f"timeline-map-{SCAN_DATE}.md"
        tm_path.unlink()
        result = validate_completion(setup_complete_deliverables, SCAN_DATE)
        cg006_checks = [c for c in result["checks"] if c["id"] == "CG-006"]
        assert any(not c["passed"] for c in cg006_checks)
