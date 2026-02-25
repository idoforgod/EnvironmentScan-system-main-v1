#!/usr/bin/env python3
"""
Environmental Scanning Report Validator
========================================
Programmatic validation of generated markdown reports.
16-20 checks across FILE, SEC, SIG, QUAL, STEEPS, CW, FSSF, H3HZ, TPNT, EVOL, EXPLO categories.
Check count varies by profile: standard=17, integrated=19, naver=20,
arxiv_fallback=16, weekly=17.
EXPLO-001 is path-conditional (WF1 only, +1 when exploration enabled in SOT),
not profile-conditional. Level: CRITICAL when enforcement=mandatory, ERROR when optional.

Profiles (Korean — final output reports):
    standard    - Individual workflow reports (10 signals, 5000 words)
    integrated  - Integrated report (20 signals, 8000 words, cross-workflow analysis)
    naver       - WF3 Naver News reports (10 signals, 5000 words, FSSF/3H/TP checks)
    arxiv_fallback - WF2 low-signal fallback (8 signals, 3000 words)

Profiles (English — intermediate English-first reports):
    standard_en    - English WF1/WF2 reports (same thresholds, EN headers/fields)
    integrated_en  - English integrated report
    naver_en       - English WF3 report
    arxiv_fallback_en - English WF2 low-signal fallback
    weekly_en      - English weekly meta-analysis

Usage:
    python3 validate_report.py <report_path>
    python3 validate_report.py <report_path> --profile integrated
    python3 validate_report.py reports/daily/environmental-scan-2026-02-01.md

Exit codes:
    0 = PASS (all checks passed)
    1 = FAIL (one or more CRITICAL checks failed)
    2 = WARN (no CRITICAL failures, but ERROR-level issues found)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_SECTION_HEADERS = [
    "## 1. 경영진 요약",
    "## 2. 신규 탐지 신호",
    "## 3. 기존 신호 업데이트",
    "## 4. 패턴 및 연결고리",
    "## 5. 전략적 시사점",
    "## 7. 신뢰도 분석",
    "## 8. 부록",
]

WEEKLY_REQUIRED_SECTION_HEADERS = [
    "## 1. 경영진 요약",
    "## 2. 주간 추세 분석",
    "## 3. 신호 수렴 분석",
    "## 4. 신호 진화 타임라인",
    "## 5. 전략적 시사점",
    "## 7. 신뢰도 분석",
    "## 8. 시스템 성능 리뷰",
    "## 9. 부록",
]

NAVER_SECTION_4_REQUIRED_SUBS = ["4.1", "4.2", "4.3", "4.4", "4.5", "4.6"]

# FSSF 8-type pairs: (English regex pattern, Korean keyword)
# English patterns use \b word boundary to prevent substring matches (e.g. "Trend" inside "Megatrend")
FSSF_TYPE_PAIRS = [
    (r"\bWeak Signal\b", "약신호"),
    (r"\bWild Card\b", "와일드카드"),
    (r"\bDiscontinuity\b", "단절"),
    (r"\bEmerging Issue\b", "부상 이슈"),
    (r"\bDriver\b", "동인"),
    (r"\bPrecursor Event\b", "전조 사건"),
    (r"\bTrend\b", "추세"),         # \b prevents matching inside "Megatrend"
    (r"\bMegatrend\b", "메가트렌드"),
]

SIGNAL_REQUIRED_FIELDS = [
    "분류",
    "출처",
    "핵심 사실",
    "정량 지표",
    "영향도",
    "상세 설명",
    "추론",
    "이해관계자",
    "모니터링 지표",
]

SECTION_MIN_WORDS = {
    "## 1. 경영진 요약": 100,
    "## 2. 신규 탐지 신호": 500,
    "## 3. 기존 신호 업데이트": 30,
    "## 4. 패턴 및 연결고리": 80,
    "## 5. 전략적 시사점": 100,
    "## 7. 신뢰도 분석": 30,
    "## 8. 부록": 30,
}

# ---------------------------------------------------------------------------
# English-language constants (for EN report validation profiles)
# ---------------------------------------------------------------------------

REQUIRED_SECTION_HEADERS_EN = [
    "## 1. Executive Summary",
    "## 2. Newly Detected Signals",
    "## 3. Existing Signal Updates",
    "## 4. Patterns and Connections",
    "## 5. Strategic Implications",
    "## 7. Confidence Analysis",
    "## 8. Appendix",
]

WEEKLY_REQUIRED_SECTION_HEADERS_EN = [
    "## 1. Executive Summary",
    "## 2. Weekly Trend Analysis",
    "## 3. Signal Convergence Analysis",
    "## 4. Signal Evolution Timeline",
    "## 5. Strategic Implications",
    "## 7. Confidence Analysis",
    "## 8. System Performance Review",
    "## 9. Appendix",
]

SIGNAL_REQUIRED_FIELDS_EN = [
    "Classification",
    "Source",
    "Key Facts",
    "Quantitative Metrics",
    "Impact",
    "Detailed Description",
    "Inference",
    "Stakeholders",
    "Monitoring Indicators",
]

SECTION_MIN_WORDS_EN = {
    "## 1. Executive Summary": 100,
    "## 2. Newly Detected Signals": 500,
    "## 3. Existing Signal Updates": 30,
    "## 4. Patterns and Connections": 80,
    "## 5. Strategic Implications": 100,
    "## 7. Confidence Analysis": 30,
    "## 8. Appendix": 30,
}

# Language-dependent regex patterns for signal block detection
_SIGNAL_BLOCK_PATTERNS = {
    "ko": r"^#{3,4}\s*(?:통합\s*)?우선순위\s*\d+",
    "en": r"^#{3,4}\s*(?:Integrated\s*)?Priority\s*\d+",
}
_SIGNAL_TITLE_PATTERNS = {
    "ko": r"#{3,4}\s*(?:통합\s*)?우선순위\s*\d+[:\s]*(.*)",
    "en": r"#{3,4}\s*(?:Integrated\s*)?Priority\s*\d+[:\s]*(.*)",
}
_CLASSIFICATION_FIELD_NAME = {
    "ko": "분류",
    "en": "Classification",
}

# ---------------------------------------------------------------------------
# Profile definitions
# ---------------------------------------------------------------------------

PROFILES = {
    "standard": {
        "min_total_words": 5000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
    },
    "integrated": {
        "min_total_words": 8000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 20,
        "min_fields_per_signal": 9,
        "min_field_global_count": 20,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": True,
        "require_source_tags": True,
        "require_evolution_check": True,
        "steeps_min_categories": 5,
        # CW-001: 통합 보고서의 교차 워크플로우 분석은 Section 4.3에 위치
        "cross_workflow_section": "## 4. 패턴 및 연결고리",
        "cross_workflow_header": r"###\s*4\.3",
        "cross_workflow_subsections": [],  # 이름형 서브섹션 (번호형 아님)
    },
    "arxiv_fallback": {
        "min_total_words": 3000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 8,
        "min_fields_per_signal": 9,
        "min_field_global_count": 8,
        "min_cross_impact_pairs": 2,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": False,
        "steeps_min_categories": 3,
    },
    "naver": {
        "min_total_words": 5000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
        # WF3 전용: Section 4에 FSSF/Three Horizons/Tipping Point/Anomaly 서브섹션 필수
        "s4_required_subs": NAVER_SECTION_4_REQUIRED_SUBS,
        # WF3 전용 체크 플래그
        "require_fssf_table": True,
        "require_three_horizons_table": True,
        "require_tipping_point_section": True,
    },
    "multiglobal-news": {
        "min_total_words": 5000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
        # WF4 전용: Section 4에 FSSF/Three Horizons/Tipping Point/Anomaly 서브섹션 필수
        "s4_required_subs": NAVER_SECTION_4_REQUIRED_SUBS,
        # WF4 전용 체크 플래그 (WF3과 동일한 FSSF 기반 체크)
        "require_fssf_table": True,
        "require_three_horizons_table": True,
        "require_tipping_point_section": True,
    },
    "weekly": {
        "min_total_words": 6000,
        "min_korean_ratio": 0.30,
        "steeps_min_categories": 0,      # 주간은 개별 신호 블록 없음 — STEEPs 분포 체크 스킵
        "min_signal_blocks": 0,          # 주간은 개별 신호 블록이 아닌 추세 블록
        "min_fields_per_signal": 0,
        "min_field_global_count": 0,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": True,   # WF1↔WF2↔WF3 교차 분석 필수
        "require_source_tags": True,      # [WF1]/[WF2] 태그 필수
        "section_headers": WEEKLY_REQUIRED_SECTION_HEADERS,
        "section_min_words": {
            "## 1. 경영진 요약": 100,
            "## 2. 주간 추세 분석": 500,
            "## 3. 신호 수렴 분석": 200,
            "## 4. 신호 진화 타임라인": 200,
            "## 5. 전략적 시사점": 100,
            "## 7. 신뢰도 분석": 30,
            "## 8. 시스템 성능 리뷰": 100,
            "## 9. 부록": 30,
        },
        "min_trend_blocks": 5,           # 추세 블록 최소 5개 (주간 고유)
        # 주간은 교차 워크플로우 분석이 섹션 3.3에 위치 (일일/통합은 4.3)
        "cross_workflow_section": "## 3. 신호 수렴 분석",
        "cross_workflow_header": r"###\s*3\.3",
        "cross_workflow_subsections": [],  # 주간은 3.3 하위에 번호 서브섹션 없음
        # 주간 섹션 3/4 서브섹션 체크 (일일과 다른 구조)
        "s3_section_header": "## 3. 신호 수렴 분석",
        "s3_required_subs": ["3.1", "3.2", "3.3"],
        "s4_section_header": "## 4. 신호 진화 타임라인",
        "s4_required_subs": ["4.1", "4.2", "4.3"],
    },
    # ------------------------------------------------------------------
    # English-language profiles (for English-first workflow)
    # ------------------------------------------------------------------
    "standard_en": {
        "language": "en",
        "min_total_words": 5000,
        "min_korean_ratio": 0.0,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
        "section_headers": REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": SECTION_MIN_WORDS_EN,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
    },
    "integrated_en": {
        "language": "en",
        "min_total_words": 8000,
        "min_korean_ratio": 0.0,
        "min_signal_blocks": 20,
        "min_fields_per_signal": 9,
        "min_field_global_count": 20,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": True,
        "require_source_tags": True,
        "require_evolution_check": True,
        "steeps_min_categories": 5,
        "section_headers": REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": SECTION_MIN_WORDS_EN,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
        "cross_workflow_section": "## 4. Patterns and Connections",
        "cross_workflow_header": r"###\s*4\.3",
        "cross_workflow_subsections": [],
    },
    "arxiv_fallback_en": {
        "language": "en",
        "min_total_words": 3000,
        "min_korean_ratio": 0.0,
        "min_signal_blocks": 8,
        "min_fields_per_signal": 9,
        "min_field_global_count": 8,
        "min_cross_impact_pairs": 2,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": False,
        "steeps_min_categories": 3,
        "section_headers": REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": SECTION_MIN_WORDS_EN,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
    },
    "naver_en": {
        "language": "en",
        "min_total_words": 5000,
        "min_korean_ratio": 0.0,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
        "section_headers": REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": SECTION_MIN_WORDS_EN,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
        "s4_section_header": "## 4. Patterns and Connections",
        "s4_required_subs": NAVER_SECTION_4_REQUIRED_SUBS,
        "require_fssf_table": True,
        "require_three_horizons_table": True,
        "require_tipping_point_section": True,
    },
    "multiglobal-news_en": {
        "language": "en",
        "min_total_words": 5000,
        "min_korean_ratio": 0.0,
        "min_signal_blocks": 10,
        "min_fields_per_signal": 9,
        "min_field_global_count": 10,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": False,
        "require_source_tags": False,
        "require_evolution_check": True,
        "steeps_min_categories": 4,
        "section_headers": REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": SECTION_MIN_WORDS_EN,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
        "s4_section_header": "## 4. Patterns and Connections",
        "s4_required_subs": NAVER_SECTION_4_REQUIRED_SUBS,
        "require_fssf_table": True,
        "require_three_horizons_table": True,
        "require_tipping_point_section": True,
    },
    "weekly_en": {
        "language": "en",
        "min_total_words": 6000,
        "min_korean_ratio": 0.0,
        "steeps_min_categories": 0,
        "min_signal_blocks": 0,
        "min_fields_per_signal": 0,
        "min_field_global_count": 0,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": True,
        "require_source_tags": True,
        "section_headers": WEEKLY_REQUIRED_SECTION_HEADERS_EN,
        "section_min_words": {
            "## 1. Executive Summary": 100,
            "## 2. Weekly Trend Analysis": 500,
            "## 3. Signal Convergence Analysis": 200,
            "## 4. Signal Evolution Timeline": 200,
            "## 5. Strategic Implications": 100,
            "## 7. Confidence Analysis": 30,
            "## 8. System Performance Review": 100,
            "## 9. Appendix": 30,
        },
        "min_trend_blocks": 5,
        "signal_fields": SIGNAL_REQUIRED_FIELDS_EN,
        "cross_workflow_section": "## 3. Signal Convergence Analysis",
        "cross_workflow_header": r"###\s*3\.3",
        "cross_workflow_subsections": [],
        "s3_section_header": "## 3. Signal Convergence Analysis",
        "s3_required_subs": ["3.1", "3.2", "3.3"],
        "s4_section_header": "## 4. Signal Evolution Timeline",
        "s4_required_subs": ["4.1", "4.2", "4.3"],
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    check_id: str
    level: str  # CRITICAL | ERROR
    description: str
    passed: bool
    detail: str = ""


@dataclass
class ValidationReport:
    report_path: str
    results: list = field(default_factory=list)
    profile: str = "standard"

    @property
    def critical_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.level == "CRITICAL"]

    @property
    def error_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.level == "ERROR"]

    @property
    def passed_checks(self) -> list:
        return [r for r in self.results if r.passed]

    @property
    def overall_status(self) -> str:
        if self.critical_failures:
            return "FAIL"
        if self.error_failures:
            return "WARN"
        return "PASS"

    def to_dict(self) -> dict:
        return {
            "report_path": self.report_path,
            "profile": self.profile,
            "overall_status": self.overall_status,
            "summary": {
                "total_checks": len(self.results),
                "passed": len(self.passed_checks),
                "critical_failures": len(self.critical_failures),
                "error_failures": len(self.error_failures),
            },
            "checks": [
                {
                    "check_id": r.check_id,
                    "level": r.level,
                    "description": r.description,
                    "passed": r.passed,
                    "detail": r.detail,
                }
                for r in self.results
            ],
        }

    def human_summary(self) -> str:
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"  Report Validation: {self.overall_status}")
        lines.append(f"  File: {self.report_path}")
        lines.append(f"  Profile: {self.profile}")
        lines.append(f"{'='*60}")
        lines.append(
            f"  Passed: {len(self.passed_checks)}/{len(self.results)}  "
            f"| CRITICAL fails: {len(self.critical_failures)}  "
            f"| ERROR fails: {len(self.error_failures)}"
        )
        lines.append(f"{'-'*60}")

        for r in self.results:
            icon = "✅" if r.passed else ("🔴" if r.level == "CRITICAL" else "🟡")
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  {icon} [{r.check_id}] {r.level:8s} {status:4s} | {r.description}")
            if not r.passed and r.detail:
                for detail_line in r.detail.split("\n"):
                    lines.append(f"      → {detail_line}")

        lines.append(f"{'='*60}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: extract section text between two headers
# ---------------------------------------------------------------------------

def _strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks (``` ... ```) to avoid false matches inside examples."""
    return re.sub(r"```[\s\S]*?```", "", content)


def _extract_section(content: str, header: str) -> Optional[str]:
    """Extract text belonging to a specific section (until next ## header or EOF).
    Ignores ## headers inside code blocks."""
    cleaned = _strip_code_blocks(content)
    pattern = re.escape(header)
    match = re.search(pattern, cleaned)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"\n## \d+\.", cleaned[start:])
    if next_section:
        return cleaned[start : start + next_section.start()]
    return cleaned[start:]


def _count_words(text: str) -> int:
    """Count words including Korean (each CJK char counts as 1 word)."""
    # Remove markdown formatting
    clean = re.sub(r"[#*|\-`>\[\](){}]", " ", text)
    # Count CJK characters as individual words
    cjk_chars = len(re.findall(r"[\u3000-\u9fff\uac00-\ud7af]", clean))
    # Count non-CJK words
    non_cjk = re.sub(r"[\u3000-\u9fff\uac00-\ud7af]", " ", clean)
    ascii_words = len(non_cjk.split())
    return cjk_chars + ascii_words


def _count_signal_blocks(content: str, language: str = "ko") -> int:
    """Count signal blocks by looking for priority headers.
    Matches both ### and #### heading levels (multiline, anchored to line start).
    Excludes matches inside markdown code blocks (``` ... ```)."""
    cleaned = _strip_code_blocks(content)
    pattern = _SIGNAL_BLOCK_PATTERNS.get(language, _SIGNAL_BLOCK_PATTERNS["ko"])
    return len(re.findall(pattern, cleaned, re.MULTILINE))


def _count_field_occurrences(content: str, field_name: str) -> int:
    """Count occurrences of a bold field name like **분류**."""
    # Match both `**field**:` and `N. **field**:` patterns
    pattern = rf"\*\*{re.escape(field_name)}\*\*"
    return len(re.findall(pattern, content))


def _check_signal_fields(content: str, max_signals: int = 10, language: str = "ko") -> tuple[int, int, list]:
    """
    For each of the first `max_signals` signal blocks, check that all 9 fields
    are present. Returns (total_signals, complete_signals, list_of_missing_by_signal).
    """
    # Strip code blocks to avoid matching examples in documentation
    cleaned = _strip_code_blocks(content)
    block_pattern = _SIGNAL_BLOCK_PATTERNS.get(language, _SIGNAL_BLOCK_PATTERNS["ko"])
    title_pattern = _SIGNAL_TITLE_PATTERNS.get(language, _SIGNAL_TITLE_PATTERNS["ko"])
    fields = SIGNAL_REQUIRED_FIELDS_EN if language == "en" else SIGNAL_REQUIRED_FIELDS
    # Find all signal block boundaries (anchored to line start)
    signal_starts = [m.start() for m in re.finditer(block_pattern, cleaned, re.MULTILINE)]
    if not signal_starts:
        return 0, 0, []

    total = min(len(signal_starts), max_signals)
    complete = 0
    missing_report = []

    for i in range(total):
        start = signal_starts[i]
        end = signal_starts[i + 1] if i + 1 < len(signal_starts) else len(cleaned)
        block = cleaned[start:end]

        missing = []
        for f in fields:
            if not re.search(rf"\*\*{re.escape(f)}\*\*", block):
                missing.append(f)

        if not missing:
            complete += 1
        else:
            # Extract signal title for reporting
            title_match = re.search(title_pattern, block)
            title = title_match.group(1).strip() if title_match else f"Signal #{i+1}"
            missing_report.append({"signal": title, "missing_fields": missing})

    return total, complete, missing_report


# ---------------------------------------------------------------------------
# STEEPs distribution helper
# ---------------------------------------------------------------------------

# Korean category name → distinct STEEPs code mapping.
# Uses full-form codes consistent with validate_registry.py (SOT-043).
# Two "E" categories are disambiguated by Korean text (경제 vs 환경).
# "영적" is a variant used in integrated reports alongside "정신적".
_STEEPS_KO_TO_CODE = {
    "사회": "S_Social",
    "기술": "T_Technological",
    "경제": "E_Economic",
    "환경": "E_Environmental",
    "정치": "P_Political",
    "정신적": "s_spiritual",
    "영적": "s_spiritual",
}

# Parenthesized code / leading token → STEEPs mapping.
# Handles English-first formats: T (Technological), Political (P),
# full-code formats: P_Political (비교정치), s_spiritual (심리/체제 논리).
_CODE_TO_STEEPS = {
    # Single-letter codes (from parenthesized format).
    # "E" is intentionally EXCLUDED — it is ambiguous between E_Economic and
    # E_Environmental.  Korean Layer 1 ("경제"/"환경") or full codes resolve this.
    "T": "T_Technological",
    "S": "S_Social",
    "P": "P_Political",
    "s": "s_spiritual",
    # Full codes
    "T_Technological": "T_Technological",
    "S_Social": "S_Social",
    "E_Economic": "E_Economic",
    "E_Environmental": "E_Environmental",
    "P_Political": "P_Political",
    "s_spiritual": "s_spiritual",
    # English names
    "Technological": "T_Technological",
    "Social": "S_Social",
    "Economic": "E_Economic",
    "Environmental": "E_Environmental",
    "Political": "P_Political",
    "spiritual": "s_spiritual",
}

# All 6 canonical STEEPs codes (for missing-category reporting)
_ALL_STEEPS_CODES = {"S_Social", "T_Technological", "E_Economic", "E_Environmental", "P_Political", "s_spiritual"}

# Separator pattern to split category part from description part.
# Matches: " -- ", " — ", " – " (em dash, en dash, double hyphen).
_FIELD_SEPARATOR_RE = re.compile(r"\s*(?:--|—|–)\s*")


def _classify_steeps_field(field_text: str) -> set[str]:
    """Classify a **분류** field into STEEPs codes using multi-layer detection.

    Handles all observed real-world formats:
      - Korean-first: 기술 (T) — AI/LLM
      - English-first: Political (P) -- 사법부의
      - Code-first: P_Political (비교정치), s_spiritual (심리/체제)
      - Multi-category: 경제(E) + 사회(S) + 정치(P) -- econ.GN
      - Variant: 영적/윤리 (s) -- 사회 심리

    Returns set of matched STEEPs codes (may be multiple for dual-category signals).
    """
    # Step 0: Isolate category part from description (split at -- / — / –)
    category_part = _FIELD_SEPARATOR_RE.split(field_text, maxsplit=1)[0]

    found: set[str] = set()

    # Layer 1: Korean keywords (boundary-aware, no break — finds ALL matches)
    for ko, code in _STEEPS_KO_TO_CODE.items():
        if re.search(rf"(?<![가-힣]){re.escape(ko)}(?![가-힣])", category_part):
            found.add(code)

    # Layer 2: Parenthesized codes — (T), (s), (E_Environmental), (Technological)
    # NOTE: closing \) removed to handle (spiritual/ethical) where / breaks [A-Za-z_]+
    for paren_match in re.finditer(r"\(([A-Za-z_]+)", category_part):
        token = paren_match.group(1)
        if token in _CODE_TO_STEEPS:
            found.add(_CODE_TO_STEEPS[token])

    # Layer 3: Scan ALL recognized code tokens — only when Layer 1+2 found nothing.
    # Safe because: (a) Layer 1+2 already failed so no Korean/parenthesized codes,
    # (b) Korean description words don't match [A-Za-z_]+, (c) non-code English
    # tokens (e.g. "AI") are filtered by _CODE_TO_STEEPS lookup.
    if not found:
        for token_match in re.finditer(r"\b([A-Za-z_]+)\b", category_part):
            token = token_match.group(1)
            if token in _CODE_TO_STEEPS:
                found.add(_CODE_TO_STEEPS[token])

    return found


def _extract_steeps_distribution(content: str, language: str = "ko") -> dict[str, int]:
    """Extract STEEPs category distribution from signal classification fields.

    Uses 3-layer detection (Korean keywords → parenthesized codes → leading
    codes/names) with category/description separation to handle all real-world
    report formats. Multi-category signals count for all matched categories.

    Returns dict mapping distinct STEEPs codes to signal counts.
    """
    distribution: dict[str, int] = {}
    cleaned = _strip_code_blocks(content)
    field_name = _CLASSIFICATION_FIELD_NAME.get(language, "분류")
    for match in re.finditer(rf"\*\*{re.escape(field_name)}\*\*[:\s]*([^\n]+)", cleaned):
        field_text = match.group(1).strip()
        codes = _classify_steeps_field(field_text)
        for code in codes:
            distribution[code] = distribution.get(code, 0) + 1
    return distribution


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def validate_report(report_path: str, profile: str = "standard") -> ValidationReport:
    """Run validation checks against a report file using the specified profile."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile '{profile}'. Valid: {list(PROFILES.keys())}")
    prof = PROFILES[profile]
    lang = prof.get("language", "ko")

    vr = ValidationReport(report_path=report_path, profile=profile)
    path = Path(report_path)

    # ── FILE-001: File exists ──
    exists = path.exists()
    vr.results.append(CheckResult(
        check_id="FILE-001",
        level="CRITICAL",
        description="보고서 파일 존재 여부",
        passed=exists,
        detail="" if exists else f"File not found: {report_path}",
    ))
    if not exists:
        # Cannot proceed without file — fill remaining checks as FAIL
        min_sigs = prof["min_signal_blocks"]
        min_fc = prof["min_field_global_count"]
        min_cp = prof["min_cross_impact_pairs"]
        min_tw = prof["min_total_words"]
        min_kr = prof["min_korean_ratio"]
        checks_stub = [
            ("FILE-002", "CRITICAL", "파일 크기 최소 1KB"),
            ("SEC-001", "CRITICAL", "필수 섹션 헤더 7개 존재"),
            ("SEC-002", "ERROR", "각 섹션 최소 단어 수 충족"),
            ("SIG-001", "CRITICAL", f"신호 블록 {min_sigs}개 이상 존재"),
            ("SIG-002", "CRITICAL", "각 신호에 9개 필드 모두 존재"),
            ("SIG-003", "ERROR", f"각 필드명 전체 보고서에 {min_fc}회 이상 등장"),
            ("S5-001", "CRITICAL", "섹션 5에 5.1/5.2/5.3 서브섹션"),
            ("S3-001", "ERROR", "섹션 3에 3.1/3.2 서브섹션"),
            ("S4-001", "ERROR", "섹션 4에 4.1/4.2 서브섹션"),
            ("S4-002", "ERROR", f"교차영향 쌍(↔) {min_cp}개 이상"),
            ("QUAL-001", "ERROR", f"전체 {min_tw:,}단어 이상"),
            ("QUAL-002", "ERROR", f"한국어 문자 비율 {min_kr:.0%} 이상"),
            ("SKEL-001", "CRITICAL", "미채워진 {{PLACEHOLDER}} 토큰 없음"),
        ]
        steeps_min = prof.get("steeps_min_categories", 0)
        if steeps_min > 0:
            checks_stub.append(("STEEPS-001", "ERROR", f"STEEPs 분포 최소 {steeps_min}개 카테고리 이상"))
        if prof["require_cross_workflow"]:
            checks_stub.append(("CW-001", "CRITICAL", "섹션 4.3 교차 워크플로우 분석 존재"))
            checks_stub.append(("CW-002", "ERROR", "[WF1]/[WF2]/[WF3] 출처 태그 존재"))
        checks_stub.append(("TEMP-001", "ERROR", "스캔 시간 범위 정보 존재 및 유효성 (TC-004)"))
        if prof.get("require_fssf_table"):
            checks_stub.append(("FSSF-001", "CRITICAL", "FSSF 8-type 분류 테이블 존재 (3개 이상 유형 키워드)"))
        if prof.get("require_three_horizons_table"):
            checks_stub.append(("H3HZ-001", "CRITICAL", "Three Horizons (H1/H2/H3) 테이블 존재"))
        if prof.get("require_tipping_point_section"):
            checks_stub.append(("TPNT-001", "ERROR", "전환점(Tipping Point) 섹션 및 경보 레벨 존재"))
        if prof.get("require_evolution_check"):
            checks_stub.append(("EVOL-001", "ERROR", "섹션 3에 신호 진화 상태 요약 존재"))
        for cid, lvl, desc in checks_stub:
            vr.results.append(CheckResult(cid, lvl, desc, False, "File not found"))
        return vr

    content = path.read_text(encoding="utf-8")
    file_size = path.stat().st_size

    # ── FILE-002: File size >= 1KB ──
    vr.results.append(CheckResult(
        check_id="FILE-002",
        level="CRITICAL",
        description="파일 크기 최소 1KB",
        passed=file_size >= 1024,
        detail=f"File size: {file_size} bytes" if file_size < 1024 else "",
    ))

    # ── SEC-001: Required section headers (profile-dependent) ──
    section_headers = prof.get("section_headers", REQUIRED_SECTION_HEADERS)
    missing_sections = [h for h in section_headers if h not in content]
    vr.results.append(CheckResult(
        check_id="SEC-001",
        level="CRITICAL",
        description="필수 섹션 헤더 7개 존재 여부",
        passed=len(missing_sections) == 0,
        detail=f"Missing: {missing_sections}" if missing_sections else "",
    ))

    # ── SEC-002: Each section minimum word count ──
    section_min_words = prof.get("section_min_words", SECTION_MIN_WORDS)
    below_min = []
    for header, min_words in section_min_words.items():
        section_text = _extract_section(content, header)
        if section_text is None:
            below_min.append(f"{header}: section not found")
            continue
        wc = _count_words(section_text)
        if wc < min_words:
            below_min.append(f"{header}: {wc} words (min {min_words})")
    vr.results.append(CheckResult(
        check_id="SEC-002",
        level="ERROR",
        description="각 섹션 최소 단어 수 충족",
        passed=len(below_min) == 0,
        detail="\n".join(below_min) if below_min else "",
    ))

    # ── SIG-001: Signal blocks >= profile minimum ──
    sig_count = _count_signal_blocks(content, language=lang)
    min_sigs = prof["min_signal_blocks"]
    vr.results.append(CheckResult(
        check_id="SIG-001",
        level="CRITICAL",
        description=f"신호 블록 {min_sigs}개 이상 존재",
        passed=sig_count >= min_sigs,
        detail=f"Found {sig_count} signal blocks (need >= {min_sigs})" if sig_count < min_sigs else "",
    ))

    # ── SIG-002: Each signal has 9 fields ──
    total_sigs, complete_sigs, missing_info = _check_signal_fields(content, max_signals=min_sigs, language=lang)
    vr.results.append(CheckResult(
        check_id="SIG-002",
        level="CRITICAL",
        description="각 신호에 9개 필드 모두 존재",
        passed=total_sigs >= min_sigs and complete_sigs == min(total_sigs, min_sigs),
        detail=json.dumps(missing_info, ensure_ascii=False, indent=2) if missing_info else "",
    ))

    # ── SIG-003: Each field name appears >= min times globally ──
    min_field_count = prof["min_field_global_count"]
    signal_fields = prof.get("signal_fields", SIGNAL_REQUIRED_FIELDS)
    low_fields = []
    for f_name in signal_fields:
        count = _count_field_occurrences(content, f_name)
        if count < min_field_count:
            low_fields.append(f"**{f_name}**: {count} occurrences (need >= {min_field_count})")
    vr.results.append(CheckResult(
        check_id="SIG-003",
        level="ERROR",
        description=f"각 필드명 전체 보고서에 {min_field_count}회 이상 등장",
        passed=len(low_fields) == 0,
        detail="\n".join(low_fields) if low_fields else "",
    ))

    # ── S5-001: Section 5 has 5.1, 5.2, 5.3 subsections ──
    # Scoped search: only look within Section 5 content
    s5_header = "## 5. Strategic Implications" if lang == "en" else "## 5. 전략적 시사점"
    s5_text = _extract_section(content, s5_header) or ""
    s5_subs = []
    for sub in ["5.1", "5.2", "5.3"]:
        if not re.search(rf"###\s*{re.escape(sub)}", s5_text):
            s5_subs.append(sub)
    vr.results.append(CheckResult(
        check_id="S5-001",
        level="CRITICAL",
        description="섹션 5에 5.1/5.2/5.3 서브섹션 존재",
        passed=len(s5_subs) == 0,
        detail=f"Missing subsections: {s5_subs}" if s5_subs else "",
    ))

    # ── S3-001: Section 3 subsections (profile-dependent) ──
    default_s3 = "## 3. Existing Signal Updates" if lang == "en" else "## 3. 기존 신호 업데이트"
    s3_section_header = prof.get("s3_section_header", default_s3)
    s3_required_subs = prof.get("s3_required_subs", ["3.1", "3.2"])
    s3_text = _extract_section(content, s3_section_header) or ""
    s3_subs = []
    for sub in s3_required_subs:
        if not re.search(rf"###\s*{re.escape(sub)}", s3_text):
            s3_subs.append(sub)
    vr.results.append(CheckResult(
        check_id="S3-001",
        level="ERROR",
        description=f"섹션 3에 {'/'.join(s3_required_subs)} 서브섹션 존재" if s3_required_subs else "섹션 3 서브섹션 (해당 없음)",
        passed=len(s3_subs) == 0,
        detail=f"Missing subsections: {s3_subs}" if s3_subs else "",
    ))

    # ── S4-001: Section 4 subsections (profile-dependent) ──
    default_s4 = "## 4. Patterns and Connections" if lang == "en" else "## 4. 패턴 및 연결고리"
    s4_section_header = prof.get("s4_section_header", default_s4)
    s4_required_subs = prof.get("s4_required_subs", ["4.1", "4.2"])
    s4_text = _extract_section(content, s4_section_header) or ""
    s4_subs = []
    for sub in s4_required_subs:
        if not re.search(rf"###\s*{re.escape(sub)}", s4_text):
            s4_subs.append(sub)
    vr.results.append(CheckResult(
        check_id="S4-001",
        level="ERROR",
        description=f"섹션 4에 {'/'.join(s4_required_subs)} 서브섹션 존재" if s4_required_subs else "섹션 4 서브섹션 (해당 없음)",
        passed=len(s4_subs) == 0,
        detail=f"Missing subsections: {s4_subs}" if s4_subs else "",
    ))

    # ── S4-002: Cross-impact pairs (↔) >= profile minimum ──
    min_pairs = prof["min_cross_impact_pairs"]
    cross_pairs = len(re.findall(r"↔", content))
    vr.results.append(CheckResult(
        check_id="S4-002",
        level="ERROR",
        description=f"교차영향 쌍(↔) {min_pairs}개 이상",
        passed=cross_pairs >= min_pairs,
        detail=f"Found {cross_pairs} cross-impact pairs (need >= {min_pairs})" if cross_pairs < min_pairs else "",
    ))

    # ── QUAL-001: Total words >= profile minimum ──
    min_words_total = prof["min_total_words"]
    total_words = _count_words(content)
    vr.results.append(CheckResult(
        check_id="QUAL-001",
        level="ERROR",
        description=f"전체 {min_words_total:,}단어 이상",
        passed=total_words >= min_words_total,
        detail=f"Total words: {total_words} (need >= {min_words_total})" if total_words < min_words_total else "",
    ))

    # ── QUAL-002: Korean character ratio >= profile minimum ──
    min_kr = prof["min_korean_ratio"]
    korean_chars = len(re.findall(r"[\uac00-\ud7af]", content))
    all_alpha = len(re.findall(r"[\w]", content))
    ratio = korean_chars / max(all_alpha, 1)
    vr.results.append(CheckResult(
        check_id="QUAL-002",
        level="ERROR",
        description=f"한국어 문자 비율 {min_kr:.0%} 이상",
        passed=ratio >= min_kr,
        detail=f"Korean ratio: {ratio:.1%} ({korean_chars}/{all_alpha})" if ratio < min_kr else "",
    ))

    # ── SKEL-001: No unfilled {{PLACEHOLDER}} tokens ──
    placeholders = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    vr.results.append(CheckResult(
        check_id="SKEL-001",
        level="CRITICAL",
        description="미채워진 {{PLACEHOLDER}} 토큰 없음",
        passed=len(placeholders) == 0,
        detail=f"Unfilled placeholders: {placeholders}" if placeholders else "",
    ))

    # ── STEEPS-001: STEEPs category distribution coverage ──
    steeps_min = prof.get("steeps_min_categories", 0)
    if steeps_min > 0:
        steeps_dist = _extract_steeps_distribution(content, language=lang)
        distinct_cats = len(steeps_dist)
        missing_cats = sorted(_ALL_STEEPS_CODES - set(steeps_dist.keys()))
        steeps_passed = distinct_cats >= steeps_min
        steeps_detail = ""
        if not steeps_passed:
            dist_str = ", ".join(f"{k}={v}" for k, v in sorted(steeps_dist.items()))
            steeps_detail = (
                f"Found {distinct_cats} categories (need >= {steeps_min}). "
                f"Distribution: {{{dist_str}}}. Missing: {missing_cats}"
            )
        vr.results.append(CheckResult(
            check_id="STEEPS-001",
            level="ERROR",
            description=f"STEEPs 분포 최소 {steeps_min}개 카테고리 이상",
            passed=steeps_passed,
            detail=steeps_detail,
        ))

    # ── CW-001: Cross-workflow analysis section (profile-dependent location) ──
    if prof["require_cross_workflow"]:
        cw_header_pattern = prof.get("cross_workflow_header", r"###\s*4\.3")
        cw_subsection_ids = prof.get("cross_workflow_subsections", ["4.3.1", "4.3.2", "4.3.3"])
        default_cw_section = "## 4. Signal Evolution Timeline" if lang == "en" else "## 4. 신호 진화 타임라인"
        cw_section_key = prof.get("cross_workflow_section", default_cw_section)
        cw_search_text = _extract_section(content, cw_section_key) or ""
        has_cw_header = bool(re.search(cw_header_pattern, cw_search_text))
        cw_missing_subs = []
        for sub in cw_subsection_ids:
            if not re.search(rf"####?\s*{re.escape(sub)}", cw_search_text):
                cw_missing_subs.append(sub)
        vr.results.append(CheckResult(
            check_id="CW-001",
            level="CRITICAL",
            description="섹션 4.3 교차 워크플로우 분석 존재",
            passed=has_cw_header and len(cw_missing_subs) == 0,
            detail=f"Missing: header={not has_cw_header}, subsections={cw_missing_subs}" if not has_cw_header or cw_missing_subs else "",
        ))

    # ── CW-002: Source tags [WF1]/[WF2]/[WF3] present ──
    if prof["require_source_tags"]:
        has_wf1 = bool(re.search(r"\[WF1\]", content))
        has_wf2 = bool(re.search(r"\[WF2\]", content))
        has_wf3 = bool(re.search(r"\[WF3\]", content))
        # integrated profile: WF3 required; weekly: WF3 optional (legacy compat)
        require_wf3 = profile in ("integrated", "integrated_en")
        all_present = has_wf1 and has_wf2 and (has_wf3 if require_wf3 else True)
        vr.results.append(CheckResult(
            check_id="CW-002",
            level="ERROR",
            description="[WF1]/[WF2]/[WF3] 출처 태그 존재",
            passed=all_present,
            detail=f"[WF1]:{has_wf1}, [WF2]:{has_wf2}, [WF3]:{has_wf3}" if not all_present else "",
        ))

    # ── TEMP-001: Scan window information present AND valid (TC-004) ──
    # Level 1: Check presence of scan window text (language-aware)
    if lang == "en":
        has_scan_window_text = bool(
            re.search(r'[Ss]can\s*[Ww]indow', content)
            or re.search(r'T₀', content)
            or re.search(r'[Aa]nchor\s*[Tt]ime', content)
        )
    else:
        has_scan_window_text = bool(
            re.search(r'스캔\s*시간\s*범위', content)
            or re.search(r'T₀', content)
            or re.search(r'기준\s*시점', content)
        )
    # Level 2: Check that no unfilled temporal placeholders remain
    unfilled_temporal = re.findall(
        r"\{\{(SCAN_WINDOW_START|SCAN_WINDOW_END|SCAN_ANCHOR_TIMESTAMP|LOOKBACK_HOURS"
        r"|WF[123]_LOOKBACK_HOURS|DAILY_LOOKBACK_HOURS)\}\}",
        content,
    )
    # Level 3: Check that actual datetime values exist (not just labels)
    if lang == "en":
        has_datetime_value = bool(
            re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}', content)
        )
    else:
        has_datetime_value = bool(
            re.search(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일\s*\d{1,2}:\d{2}', content)
            or re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', content)
        )
    temp001_passed = has_scan_window_text and not unfilled_temporal and has_datetime_value
    temp001_details = []
    if not has_scan_window_text:
        temp001_details.append("No scan window / T₀ / anchor time text found in report")
    if unfilled_temporal:
        temp001_details.append(f"Unfilled temporal placeholders: {unfilled_temporal}")
    if not has_datetime_value:
        temp001_details.append("No actual datetime values (ISO8601 or localized) found")
    vr.results.append(CheckResult(
        check_id="TEMP-001",
        level="ERROR",
        description="스캔 시간 범위 정보 존재 및 유효성 (TC-004)",
        passed=temp001_passed,
        detail="; ".join(temp001_details) if temp001_details else "",
    ))

    # ── FSSF-001: FSSF 8-type classification table present (naver only) ──
    # Counts DISTINCT FSSF types (not raw keyword matches).
    # Each type is a (English regex, Korean keyword) pair — matching either counts as 1.
    if prof.get("require_fssf_table"):
        distinct_types = sum(
            1 for en_pat, ko_kw in FSSF_TYPE_PAIRS
            if re.search(en_pat, content, re.IGNORECASE) or ko_kw in content
        )
        fssf_passed = distinct_types >= 3
        vr.results.append(CheckResult(
            check_id="FSSF-001",
            level="CRITICAL",
            description="FSSF 8-type 분류 테이블 존재 (3개 이상 유형)",
            passed=fssf_passed,
            detail=f"Found {distinct_types} distinct FSSF types (need >= 3)" if not fssf_passed else "",
        ))

    # ── H3HZ-001: Three Horizons (H1/H2/H3) table present (naver only) ──
    if prof.get("require_three_horizons_table"):
        has_h1 = bool(re.search(r"H1\s*[\(（]?\s*0\s*[-–~]\s*2", content))
        has_h2 = bool(re.search(r"H2\s*[\(（]?\s*2\s*[-–~]\s*7", content))
        has_h3 = bool(re.search(r"H3\s*[\(（]?\s*7", content))
        horizons_count = sum([has_h1, has_h2, has_h3])
        h3hz_passed = horizons_count >= 2
        h3hz_details = []
        if not has_h1:
            h3hz_details.append("H1(0-2년) missing")
        if not has_h2:
            h3hz_details.append("H2(2-7년) missing")
        if not has_h3:
            h3hz_details.append("H3(7년+) missing")
        vr.results.append(CheckResult(
            check_id="H3HZ-001",
            level="CRITICAL",
            description="Three Horizons (H1/H2/H3) 테이블 존재",
            passed=h3hz_passed,
            detail="; ".join(h3hz_details) if h3hz_details else "",
        ))

    # ── TPNT-001: Tipping Point section present (naver only) ──
    # Uses word-boundary regex to avoid false positives (e.g. "PREDICTED" matching "RED")
    if prof.get("require_tipping_point_section"):
        has_tp_text = bool(
            re.search(r"전환점", content) or re.search(r"[Tt]ipping\s*[Pp]oint", content)
        )
        alert_keywords = ["GREEN", "YELLOW", "ORANGE", "RED"]
        alert_count = sum(
            1 for kw in alert_keywords
            if re.search(rf"\b{kw}\b", content, re.IGNORECASE)
        )
        tpnt_passed = has_tp_text and alert_count >= 1
        tpnt_details = []
        if not has_tp_text:
            tpnt_details.append("'전환점' 또는 'Tipping Point' 텍스트 없음")
        if alert_count < 1:
            tpnt_details.append(f"경보 레벨 키워드(GREEN/YELLOW/ORANGE/RED) 없음 (found {alert_count})")
        vr.results.append(CheckResult(
            check_id="TPNT-001",
            level="ERROR",
            description="전환점(Tipping Point) 섹션 및 경보 레벨 존재",
            passed=tpnt_passed,
            detail="; ".join(tpnt_details) if tpnt_details else "",
        ))

    # ── EVOL-001: Evolution state summary table in Section 3 (profile-dependent) ──
    if prof.get("require_evolution_check"):
        evol_s3_header = "## 3. Existing Signal Updates" if lang == "en" else "## 3. 기존 신호 업데이트"
        s3_text_for_evol = _extract_section(content, evol_s3_header) or ""
        # Check for evolution summary keywords (state table OR thread count)
        if lang == "en":
            has_evolution_table = bool(
                re.search(r"[Aa]ctive\s*[Tt]racking\s*[Tt]hreads", s3_text_for_evol)
                or re.search(r"\|\s*New\s*\|", s3_text_for_evol)
                or re.search(r"\|\s*Strengthening\s*\|", s3_text_for_evol)
            )
        else:
            has_evolution_table = bool(
                re.search(r"활성\s*추적\s*스레드", s3_text_for_evol)
                or re.search(r"\|\s*신규\s*\|", s3_text_for_evol)
                or re.search(r"\|\s*강화\s*\|", s3_text_for_evol)
            )
        vr.results.append(CheckResult(
            check_id="EVOL-001",
            level="ERROR",
            description="섹션 3에 신호 진화 상태 요약 존재",
            passed=has_evolution_table,
            detail="Section 3 missing evolution summary (active tracking threads / state table)" if not has_evolution_table else "",
        ))

    return vr


# ---------------------------------------------------------------------------
# Exploration proof check (option-based, NOT profile-based)
# ---------------------------------------------------------------------------

def _check_exploration_proof(vr: ValidationReport, proof_path: str, level: str = "ERROR") -> None:
    """
    EXPLO-001: Verify exploration proof file exists and is valid.

    This check is triggered by --exploration-proof CLI option, NOT by profile.
    Reason: WF1 and WF2 share the "standard" profile, but only WF1 has
    source exploration. Adding this to the profile would break WF2.

    Level is determined by the caller:
      - "CRITICAL" when SOT enforcement == "mandatory"
      - "ERROR" when SOT enforcement == "optional" (default)
    """
    passed = False
    detail = ""
    try:
        path = Path(proof_path)
        if not path.exists():
            detail = f"Proof file not found: {proof_path}"
        else:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # Verify required fields
            required_keys = {"gate_id", "gate_decision", "execution_status", "date"}
            missing = required_keys - set(data.keys())
            if missing:
                detail = f"Proof file missing fields: {missing}"
            else:
                passed = True
    except json.JSONDecodeError as e:
        detail = f"Invalid JSON in proof file: {e}"
    except Exception as e:
        detail = f"Error reading proof file: {e}"

    vr.results.append(CheckResult(
        check_id="EXPLO-001",
        level=level,
        description="소스 탐사(Stage C) 실행 증명 파일 존재 및 유효",
        passed=passed,
        detail=detail,
    ))


# ---------------------------------------------------------------------------
# SOT enforcement level helper
# ---------------------------------------------------------------------------

def _get_enforcement_level(report_path: str) -> str:
    """
    Read SOT to determine EXPLO-001 check level for a given report path.

    Returns "CRITICAL" if enforcement=mandatory in SOT and the report is WF1.
    Returns "ERROR" otherwise (optional enforcement, non-WF1, or any failure).
    """
    if yaml is None:
        return "ERROR"
    try:
        report_abs = str(Path(report_path).resolve())
        if "wf1-general" not in report_abs:
            return "ERROR"
        report_dir = Path(report_path).resolve().parent
        project_root = report_dir.parent.parent.parent.parent
        sot_path = project_root / "env-scanning" / "config" / "workflow-registry.yaml"
        if not sot_path.exists():
            return "ERROR"
        with open(sot_path, encoding="utf-8") as f:
            registry = yaml.safe_load(f)
        enforcement = (registry.get("workflows", {})
                       .get("wf1-general", {})
                       .get("parameters", {})
                       .get("source_exploration", {})
                       .get("enforcement", "optional"))
        return "CRITICAL" if enforcement == "mandatory" else "ERROR"
    except Exception:
        return "ERROR"


# ---------------------------------------------------------------------------
# Auto-enforcement: detect mandatory exploration from SOT
# ---------------------------------------------------------------------------

def _auto_enforce_exploration(vr: ValidationReport, report_path: str) -> None:
    """
    EXPLO-001 auto-detection: read SOT to determine if exploration enforcement
    is mandatory, then validate proof file existence automatically.

    This function is the "validate, don't instruct" mechanism — it runs
    deterministically regardless of whether the LLM remembered to call
    the exploration gate. If enforcement is mandatory and proof is missing,
    the report CANNOT pass validation (CRITICAL failure).

    Only applies to WF1 reports (path contains 'wf1-general').
    """
    # Guard: yaml must be available
    if yaml is None:
        return

    # Step 1: Extract date from report filename
    report_name = Path(report_path).name
    date_match = re.search(r"environmental-scan-(\d{4}-\d{2}-\d{2})\.md$", report_name)
    if not date_match:
        return  # Non-standard filename — skip gracefully

    scan_date = date_match.group(1)

    # Step 2: Check if this is a WF1 report
    report_abs = str(Path(report_path).resolve())
    if "wf1-general" not in report_abs:
        return  # WF2/WF3 — not applicable

    # Step 3: Find project root and SOT
    # Navigate from report path: wf1-general/reports/daily/file.md → up 4 levels = project root
    try:
        report_dir = Path(report_path).resolve().parent
        # Go up from reports/daily/ → reports/ → wf1-general/ → env-scanning/ → project_root
        project_root = report_dir.parent.parent.parent.parent
        sot_path = project_root / "env-scanning" / "config" / "workflow-registry.yaml"
        if not sot_path.exists():
            # SOT not found — visible ERROR (not silent skip)
            vr.results.append(CheckResult(
                check_id="EXPLO-001",
                level="ERROR",
                description="소스 탐사(Stage C) 실행 증명 파일 존재 및 유효",
                passed=False,
                detail=f"SOT file not found at expected path: {sot_path}. "
                       "Cannot determine exploration enforcement setting.",
            ))
            return
    except Exception as e:
        # Path resolution error — visible ERROR
        vr.results.append(CheckResult(
            check_id="EXPLO-001",
            level="ERROR",
            description="소스 탐사(Stage C) 실행 증명 파일 존재 및 유효",
            passed=False,
            detail=f"Failed to resolve project root from report path: {e}",
        ))
        return

    # Step 4: Read SOT and check enforcement setting
    try:
        with open(sot_path, encoding="utf-8") as f:
            registry = yaml.safe_load(f)
        wf1 = registry.get("workflows", {}).get("wf1-general", {})
        exploration_cfg = wf1.get("parameters", {}).get("source_exploration", {})
        if not exploration_cfg.get("enabled", False):
            return  # Exploration disabled — legitimate silent skip
        enforcement = exploration_cfg.get("enforcement", "optional")
    except Exception as e:
        # SOT parse error — CRITICAL ("최악의 경우 가정" principle)
        # Cannot determine if exploration is mandatory → assume worst case
        vr.results.append(CheckResult(
            check_id="EXPLO-001",
            level="CRITICAL",
            description="소스 탐사(Stage C) 실행 증명 파일 존재 및 유효",
            passed=False,
            detail=f"SOT parse failed: {e}. Cannot determine exploration enforcement. "
                   "Assuming worst case (mandatory enforcement).",
        ))
        return

    # Step 5: Determine check level based on enforcement
    level = "CRITICAL" if enforcement == "mandatory" else "ERROR"

    # Step 6: Construct proof path and validate
    data_root = project_root / wf1.get("data_root", "env-scanning/wf1-general")
    proof_path = data_root / "exploration" / f"exploration-proof-{scan_date}.json"

    passed = False
    detail = ""
    try:
        if not proof_path.exists():
            detail = f"Proof file not found: {proof_path}"
        else:
            with open(proof_path, encoding="utf-8") as f:
                data = json.load(f)
            required_keys = {"gate_id", "gate_decision", "execution_status", "date"}
            missing = required_keys - set(data.keys())
            if missing:
                detail = f"Proof file missing fields: {missing}"
            else:
                passed = True
    except json.JSONDecodeError as e:
        detail = f"Invalid JSON in proof file: {e}"
    except Exception as e:
        detail = f"Error reading proof file: {e}"

    if not passed and enforcement == "mandatory":
        detail += " [enforcement=mandatory → CRITICAL]"

    vr.results.append(CheckResult(
        check_id="EXPLO-001",
        level=level,
        description="소스 탐사(Stage C) 실행 증명 파일 존재 및 유효",
        passed=passed,
        detail=detail,
    ))


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate environmental scanning report quality"
    )
    parser.add_argument("report_path", help="Path to the markdown report file")
    parser.add_argument(
        "--profile", choices=list(PROFILES.keys()), default="standard",
        help="Validation profile (default: standard)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output results as JSON instead of human-readable summary",
    )
    parser.add_argument(
        "--exploration-proof", default=None, dest="exploration_proof",
        help="Path to exploration-proof-{date}.json (adds EXPLO-001 check, WF1 only)",
    )
    args = parser.parse_args()

    result = validate_report(args.report_path, profile=args.profile)

    # Option-based check: EXPLO-001 (not profile-based — WF1/WF2 share "standard")
    # Level is ALWAYS determined from SOT enforcement setting (mandatory→CRITICAL, optional→ERROR).
    # --exploration-proof overrides the proof PATH, not the enforcement LEVEL.
    if args.exploration_proof:
        level = _get_enforcement_level(args.report_path)
        _check_exploration_proof(result, args.exploration_proof, level=level)
    else:
        # Auto-enforcement: detect WF1 + mandatory enforcement from SOT
        _auto_enforce_exploration(result, args.report_path)

    if args.json_output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.human_summary())

    # Exit code: 0=PASS, 1=FAIL(CRITICAL), 2=WARN(ERROR only)
    status = result.overall_status
    if status == "FAIL":
        sys.exit(1)
    elif status == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
