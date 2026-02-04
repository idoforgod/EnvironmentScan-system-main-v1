#!/usr/bin/env python3
"""
Environmental Scanning Report Validator
========================================
Programmatic validation of generated markdown reports.
14+ checks across FILE, SEC, SIG, QUAL, CW categories.

Profiles:
    standard    - Individual workflow reports (10 signals, 5000 words)
    integrated  - Integrated report (15 signals, 8000 words, cross-workflow analysis)
    arxiv_fallback - WF2 low-signal fallback (8 signals, 3000 words)

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
    },
    "integrated": {
        "min_total_words": 8000,
        "min_korean_ratio": 0.30,
        "min_signal_blocks": 15,
        "min_fields_per_signal": 9,
        "min_field_global_count": 15,
        "min_cross_impact_pairs": 3,
        "require_cross_workflow": True,
        "require_source_tags": True,
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


def _count_signal_blocks(content: str) -> int:
    """Count signal blocks by looking for priority headers (우선순위 N:).
    Matches both ### and #### heading levels (multiline, anchored to line start).
    Excludes matches inside markdown code blocks (``` ... ```)."""
    cleaned = _strip_code_blocks(content)
    return len(re.findall(r"^#{3,4}\s*우선순위\s*\d+", cleaned, re.MULTILINE))


def _count_field_occurrences(content: str, field_name: str) -> int:
    """Count occurrences of a bold field name like **분류**."""
    # Match both `**field**:` and `N. **field**:` patterns
    pattern = rf"\*\*{re.escape(field_name)}\*\*"
    return len(re.findall(pattern, content))


def _check_signal_fields(content: str, max_signals: int = 10) -> tuple[int, int, list]:
    """
    For each of the first `max_signals` signal blocks, check that all 9 fields
    are present. Returns (total_signals, complete_signals, list_of_missing_by_signal).
    """
    # Strip code blocks to avoid matching examples in documentation
    cleaned = _strip_code_blocks(content)
    # Find all signal block boundaries (anchored to line start)
    signal_starts = [m.start() for m in re.finditer(r"^#{3,4}\s*우선순위\s*\d+", cleaned, re.MULTILINE)]
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
        for f in SIGNAL_REQUIRED_FIELDS:
            if not re.search(rf"\*\*{re.escape(f)}\*\*", block):
                missing.append(f)

        if not missing:
            complete += 1
        else:
            # Extract signal title for reporting
            title_match = re.search(r"#{3,4}\s*우선순위\s*\d+[:\s]*(.*)", block)
            title = title_match.group(1).strip() if title_match else f"Signal #{i+1}"
            missing_report.append({"signal": title, "missing_fields": missing})

    return total, complete, missing_report


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def validate_report(report_path: str, profile: str = "standard") -> ValidationReport:
    """Run validation checks against a report file using the specified profile."""
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile '{profile}'. Valid: {list(PROFILES.keys())}")
    prof = PROFILES[profile]

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
        if prof["require_cross_workflow"]:
            checks_stub.append(("CW-001", "CRITICAL", "섹션 4.3 교차 워크플로우 분석 존재"))
            checks_stub.append(("CW-002", "ERROR", "[WF1]/[WF2] 출처 태그 존재"))
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

    # ── SEC-001: Required section headers (7) ──
    missing_sections = [h for h in REQUIRED_SECTION_HEADERS if h not in content]
    vr.results.append(CheckResult(
        check_id="SEC-001",
        level="CRITICAL",
        description="필수 섹션 헤더 7개 존재 여부",
        passed=len(missing_sections) == 0,
        detail=f"Missing: {missing_sections}" if missing_sections else "",
    ))

    # ── SEC-002: Each section minimum word count ──
    below_min = []
    for header, min_words in SECTION_MIN_WORDS.items():
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
    sig_count = _count_signal_blocks(content)
    min_sigs = prof["min_signal_blocks"]
    vr.results.append(CheckResult(
        check_id="SIG-001",
        level="CRITICAL",
        description=f"신호 블록 {min_sigs}개 이상 존재",
        passed=sig_count >= min_sigs,
        detail=f"Found {sig_count} signal blocks (need >= {min_sigs})" if sig_count < min_sigs else "",
    ))

    # ── SIG-002: Each signal has 9 fields ──
    total_sigs, complete_sigs, missing_info = _check_signal_fields(content, max_signals=min_sigs)
    vr.results.append(CheckResult(
        check_id="SIG-002",
        level="CRITICAL",
        description="각 신호에 9개 필드 모두 존재",
        passed=total_sigs >= min_sigs and complete_sigs == min(total_sigs, min_sigs),
        detail=json.dumps(missing_info, ensure_ascii=False, indent=2) if missing_info else "",
    ))

    # ── SIG-003: Each field name appears >= min times globally ──
    min_field_count = prof["min_field_global_count"]
    low_fields = []
    for f_name in SIGNAL_REQUIRED_FIELDS:
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
    s5_text = _extract_section(content, "## 5. 전략적 시사점") or ""
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

    # ── S3-001: Section 3 has 3.1, 3.2 subsections ──
    s3_text = _extract_section(content, "## 3. 기존 신호 업데이트") or ""
    s3_subs = []
    for sub in ["3.1", "3.2"]:
        if not re.search(rf"###\s*{re.escape(sub)}", s3_text):
            s3_subs.append(sub)
    vr.results.append(CheckResult(
        check_id="S3-001",
        level="ERROR",
        description="섹션 3에 3.1/3.2 서브섹션 존재",
        passed=len(s3_subs) == 0,
        detail=f"Missing subsections: {s3_subs}" if s3_subs else "",
    ))

    # ── S4-001: Section 4 has 4.1, 4.2 subsections ──
    s4_text = _extract_section(content, "## 4. 패턴 및 연결고리") or ""
    s4_subs = []
    for sub in ["4.1", "4.2"]:
        if not re.search(rf"###\s*{re.escape(sub)}", s4_text):
            s4_subs.append(sub)
    vr.results.append(CheckResult(
        check_id="S4-001",
        level="ERROR",
        description="섹션 4에 4.1/4.2 서브섹션 존재",
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

    # ── CW-001: Cross-workflow analysis section (integrated profile) ──
    if prof["require_cross_workflow"]:
        cw_subs = []
        for sub in ["4.3.1", "4.3.2", "4.3.3"]:
            if not re.search(rf"####?\s*{re.escape(sub)}", s4_text):
                cw_subs.append(sub)
        has_s43 = bool(re.search(r"###\s*4\.3", s4_text))
        vr.results.append(CheckResult(
            check_id="CW-001",
            level="CRITICAL",
            description="섹션 4.3 교차 워크플로우 분석 존재",
            passed=has_s43 and len(cw_subs) == 0,
            detail=f"Missing: 4.3 header={not has_s43}, subsections={cw_subs}" if not has_s43 or cw_subs else "",
        ))

    # ── CW-002: Source tags [WF1]/[WF2] present (integrated profile) ──
    if prof["require_source_tags"]:
        has_wf1 = bool(re.search(r"\[WF1\]", content))
        has_wf2 = bool(re.search(r"\[WF2\]", content))
        vr.results.append(CheckResult(
            check_id="CW-002",
            level="ERROR",
            description="[WF1]/[WF2] 출처 태그 존재",
            passed=has_wf1 and has_wf2,
            detail=f"[WF1] found: {has_wf1}, [WF2] found: {has_wf2}" if not (has_wf1 and has_wf2) else "",
        ))

    return vr


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
    args = parser.parse_args()

    result = validate_report(args.report_path, profile=args.profile)

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
