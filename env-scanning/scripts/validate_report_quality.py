#!/usr/bin/env python3
"""
Environmental Scanning Report Quality Validator (Cross-Reference)
==================================================================
14 deterministic cross-reference checks that compare the generated report
against its source data files (priority-ranked JSON, scan-window JSON).

This script is Layer 2b of the Quality Defense:
  L1: Skeleton-Fill Method → report-generator.md
  L2a: Structural Validation → validate_report.py (15-20 checks)
  L2b: Cross-Reference Quality → validate_report_quality.py (13 checks) ← THIS
  L3: Semantic Depth Review → quality-reviewer.md (LLM sub-agent)
  L4: Golden Reference → report-generator.md

Checks:
  QC-001: Priority Order Consistency (report vs JSON pSST order) — CRITICAL
  QC-002: Executive Summary Top-3 Match (Section 1 vs Section 2) — ERROR
  QC-003: pSST Badge Accuracy (badge color/grade vs actual score) — CRITICAL
  QC-004: Source Date Within Scan Window — ERROR
  QC-005: Cross-Impact Reference Validity (Section 4 ↔ pairs vs Section 2 signals) — ERROR
  QC-006: Field Depth Minimum (per-field sentence/item counting) — ERROR
  QC-007: STEEPs Classification vs Content Consistency (keyword-based, flags for LLM) — WARN
  QC-008: Intra-Report Duplicate Detection (Jaro-Winkler on titles) — CRITICAL
  QC-009: Quantitative Grounding (numeric values in 정량 지표) — ERROR
  QC-010: Vague Language Blocklist (영향도/추론 specificity) — WARN
  QC-011: Cross-Signal Synthesis in Section 5 (signal references per implication) — ERROR
  QC-012: Time Horizon Keywords in Section 5 — WARN
  QC-013: Action Verb Presence in Section 5 — WARN
  QC-014: Executive Summary Statistics vs Source Data — ERROR

Usage:
  python3 validate_report_quality.py <report_path> <priority_ranked_json> [options]
  python3 validate_report_quality.py report.md ranked.json --scan-window scan-window.json
  python3 validate_report_quality.py report.md ranked.json --json

Exit codes:
  0 = PASS (all checks passed)
  1 = FAIL (one or more CRITICAL checks failed)
  2 = WARN (no CRITICAL failures, but ERROR/WARN-level issues found)
"""

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes (compatible with validate_report.py pattern)
# ---------------------------------------------------------------------------

@dataclass
class QCCheckResult:
    """Single quality check result with optional remedy guidance."""
    check_id: str
    level: str  # CRITICAL | ERROR | WARN
    description: str
    passed: bool
    detail: str = ""
    remedy: str = ""
    failed_signal_ids: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "check_id": self.check_id,
            "level": self.level,
            "description": self.description,
            "passed": self.passed,
            "detail": self.detail,
        }
        if self.remedy:
            d["remedy"] = self.remedy
        if self.failed_signal_ids:
            d["failed_signal_ids"] = self.failed_signal_ids
        return d


@dataclass
class QCValidationReport:
    """Aggregated quality validation report."""
    report_path: str
    ranked_path: str
    results: list = field(default_factory=list)
    language: str = "en"  # en or ko

    @property
    def critical_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.level == "CRITICAL"]

    @property
    def error_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.level == "ERROR"]

    @property
    def warn_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.level == "WARN"]

    @property
    def overall_status(self) -> str:
        if self.critical_failures:
            return "FAIL"
        if self.error_failures:
            return "WARN"
        if self.warn_failures:
            return "WARN"
        return "PASS"

    def to_dict(self) -> dict:
        return {
            "report_path": self.report_path,
            "ranked_path": self.ranked_path,
            "language": self.language,
            "overall_status": self.overall_status,
            "summary": {
                "total_checks": len(self.results),
                "passed": len([r for r in self.results if r.passed]),
                "critical_failures": len(self.critical_failures),
                "error_failures": len(self.error_failures),
                "warn_failures": len(self.warn_failures),
            },
            "checks": [r.to_dict() for r in self.results],
        }

    def human_summary(self) -> str:
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  Quality Validation (Cross-Reference): {self.overall_status}")
        lines.append(f"  Report: {self.report_path}")
        lines.append(f"  Ranked: {self.ranked_path}")
        lines.append(f"{'=' * 60}")
        passed_count = len([r for r in self.results if r.passed])
        lines.append(
            f"  Passed: {passed_count}/{len(self.results)}  "
            f"| CRITICAL: {len(self.critical_failures)}  "
            f"| ERROR: {len(self.error_failures)}  "
            f"| WARN: {len(self.warn_failures)}"
        )
        lines.append(f"{'-' * 60}")

        for r in self.results:
            if r.passed:
                icon = "\u2705"
            elif r.level == "CRITICAL":
                icon = "\U0001f534"
            elif r.level == "ERROR":
                icon = "\U0001f7e1"
            else:
                icon = "\U0001f7e0"
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"  {icon} [{r.check_id}] {r.level:8s} {status:4s} | {r.description}")
            if not r.passed and r.detail:
                for detail_line in r.detail.split("\n"):
                    lines.append(f"      \u2192 {detail_line}")
            if not r.passed and r.remedy:
                lines.append(f"      FIX: {r.remedy}")

        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks to avoid false matches."""
    return re.sub(r"```[\s\S]*?```", "", content)


def _extract_section(content: str, header: str) -> Optional[str]:
    """Extract text belonging to a section (until next ## header or EOF)."""
    cleaned = _strip_code_blocks(content)
    pattern = re.escape(header)
    match = re.search(pattern, cleaned)
    if not match:
        return None
    start = match.end()
    next_section = re.search(r"\n## \d+\.", cleaned[start:])
    if next_section:
        return cleaned[start: start + next_section.start()]
    return cleaned[start:]


def _extract_signal_titles(content: str, language: str = "en") -> list[tuple[int, str]]:
    """Extract (priority_number, title) pairs from signal blocks in the report.
    Returns list of (rank, title) tuples."""
    cleaned = _strip_code_blocks(content)
    if language == "en":
        pattern = r"^#{3,4}\s*(?:Integrated\s*)?Priority\s*(\d+)[:\s]*(.*)"
    else:
        pattern = r"^#{3,4}\s*(?:통합\s*)?우선순위\s*(\d+)[:\s]*(.*)"
    results = []
    for m in re.finditer(pattern, cleaned, re.MULTILINE):
        rank = int(m.group(1))
        title = m.group(2).strip()
        results.append((rank, title))
    return results


def _extract_signal_blocks(content: str, language: str = "en") -> list[dict]:
    """Extract signal blocks with their text content for analysis.
    Returns list of dicts with 'rank', 'title', 'text' keys."""
    cleaned = _strip_code_blocks(content)
    if language == "en":
        pattern = r"^#{3,4}\s*(?:Integrated\s*)?Priority\s*(\d+)[:\s]*(.*)"
    else:
        pattern = r"^#{3,4}\s*(?:통합\s*)?우선순위\s*(\d+)[:\s]*(.*)"
    starts = list(re.finditer(pattern, cleaned, re.MULTILINE))
    blocks = []
    for i, m in enumerate(starts):
        rank = int(m.group(1))
        title = m.group(2).strip()
        block_start = m.start()
        block_end = starts[i + 1].start() if i + 1 < len(starts) else len(cleaned)
        text = cleaned[block_start:block_end]
        blocks.append({"rank": rank, "title": title, "text": text})
    return blocks


def _jaro_similarity(s1: str, s2: str) -> float:
    """Compute Jaro similarity between two strings.
    Returns a float in [0, 1] where 1 means identical."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3


def _jaro_winkler_similarity(s1: str, s2: str, p: float = 0.1) -> float:
    """Compute Jaro-Winkler similarity. Higher p gives more weight to prefix matches.
    Standard p=0.1, max prefix length=4."""
    jaro = _jaro_similarity(s1, s2)
    # Common prefix length (max 4)
    prefix_len = 0
    for i in range(min(len(s1), len(s2), 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break
    return jaro + prefix_len * p * (1 - jaro)


def _normalize_title(title: str) -> str:
    """Normalize a signal title for comparison: lowercase, strip punctuation."""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s\uac00-\ud7af\u3000-\u9fff]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------------------------------------------------------
# pSST grade boundaries (from thresholds.yaml via SOT — never hardcoded)
# ---------------------------------------------------------------------------

# Default thresholds matching thresholds.yaml defaults.
# These are ONLY used when thresholds.yaml cannot be loaded at runtime.
_DEFAULT_GRADE_THRESHOLDS = {
    "very_high": 90,
    "confident": 70,
    "low": 50,
    "very_low": 0,
}
# Level 2 grade_a_threshold default (when L2 enabled)
_DEFAULT_GRADE_A_THRESHOLD = 95

# STEEPs category prefixes — only match these in distribution tables
_STEEPS_PREFIXES = {"S_", "T_", "E_", "P_", "s_"}


def _is_steeps_code(cat: str) -> bool:
    """Return True if *cat* starts with a known STEEPs prefix."""
    return any(cat.startswith(p) for p in _STEEPS_PREFIXES)


try:
    import yaml as _yaml
except ImportError:
    _yaml = None  # type: ignore[assignment]


def _load_grade_thresholds() -> tuple[dict, Optional[int]]:
    """Load grade thresholds from thresholds.yaml (SOT-binding).

    Returns:
        (thresholds_dict, grade_a_threshold_or_None)
    """
    if _yaml is None:
        return _DEFAULT_GRADE_THRESHOLDS, _DEFAULT_GRADE_A_THRESHOLD

    # Search for thresholds.yaml relative to this script
    script_dir = Path(__file__).resolve().parent
    # scripts/ → env-scanning/ → config/
    thresholds_path = script_dir.parent / "config" / "thresholds.yaml"
    if not thresholds_path.exists():
        return _DEFAULT_GRADE_THRESHOLDS, _DEFAULT_GRADE_A_THRESHOLD

    try:
        with open(thresholds_path, encoding="utf-8") as f:
            cfg = _yaml.safe_load(f)
        scoring = cfg.get("psst_scoring", {})
        thresholds = scoring.get("grade_thresholds", _DEFAULT_GRADE_THRESHOLDS)
        l2_cfg = scoring.get("level2_config", {})
        grade_a = l2_cfg.get("grade_a_threshold", _DEFAULT_GRADE_A_THRESHOLD)
        return thresholds, grade_a
    except Exception:
        return _DEFAULT_GRADE_THRESHOLDS, _DEFAULT_GRADE_A_THRESHOLD


def _expected_grade(score: int) -> str:
    """Return the expected pSST grade letter for a given score.

    Grade logic matches psst_calculator.py._determine_grade():
      A: score >= grade_a_threshold (default 95, or very_high if L2 disabled)
      B: score >= confident (default 70)
      C: score >= low (default 50)
      D: score < low
    """
    thresholds, grade_a_threshold = _load_grade_thresholds()
    # Use grade_a_threshold (Level 2 elevated threshold) if available
    very_high = grade_a_threshold if grade_a_threshold is not None else thresholds.get("very_high", 90)
    if score >= very_high:
        return "A"
    if score >= thresholds.get("confident", 70):
        return "B"
    if score >= thresholds.get("low", 50):
        return "C"
    return "D"


# ---------------------------------------------------------------------------
# STEEPs keyword maps for QC-007 content consistency
# ---------------------------------------------------------------------------

_STEEPS_CONTENT_KEYWORDS = {
    "S_Social": [
        "demographic", "education", "labor", "population", "immigration",
        "inequality", "workforce", "social", "aging", "urbanization",
        "인구", "교육", "노동", "사회", "불평등", "고령화", "도시화",
    ],
    "T_Technological": [
        "ai", "artificial intelligence", "quantum", "digital", "software",
        "algorithm", "robot", "autonomous", "computing", "technology",
        "인공지능", "양자", "디지털", "소프트웨어", "알고리즘", "로봇", "기술",
    ],
    "E_Economic": [
        "market", "gdp", "trade", "finance", "investment", "inflation",
        "currency", "stock", "economic", "fiscal", "funding", "valuation",
        "시장", "경제", "무역", "투자", "인플레이션", "금융",
    ],
    "E_Environmental": [
        "climate", "carbon", "emission", "renewable", "biodiversity",
        "sustainability", "pollution", "ocean", "environment", "energy transition",
        "기후", "탄소", "배출", "재생에너지", "생물다양성", "환경",
    ],
    "P_Political": [
        "policy", "regulation", "government", "law", "legislation",
        "sanction", "geopolit", "election", "military", "political",
        "정책", "규제", "정부", "법", "제재", "지정학", "군사", "정치",
    ],
    "s_spiritual": [
        "ethic", "psychological", "values", "meaning", "ai ethics",
        "mental health", "wellbeing", "consciousness", "philosophy",
        "윤리", "심리", "가치", "의미", "정신건강", "의식", "철학",
    ],
}

# STEEPs code extraction from classification field (reused from validate_report.py pattern)
_STEEPS_KO_TO_CODE = {
    "사회": "S_Social", "기술": "T_Technological", "경제": "E_Economic",
    "환경": "E_Environmental", "정치": "P_Political", "정신적": "s_spiritual",
    "영적": "s_spiritual",
}
_CODE_TO_STEEPS = {
    "T": "T_Technological", "S": "S_Social", "P": "P_Political", "s": "s_spiritual",
    "T_Technological": "T_Technological", "S_Social": "S_Social",
    "E_Economic": "E_Economic", "E_Environmental": "E_Environmental",
    "P_Political": "P_Political", "s_spiritual": "s_spiritual",
    "Technological": "T_Technological", "Social": "S_Social",
    "Economic": "E_Economic", "Environmental": "E_Environmental",
    "Political": "P_Political", "spiritual": "s_spiritual",
}
_FIELD_SEPARATOR_RE = re.compile(r"\s*(?:--|—|–)\s*")


def _classify_steeps_field(field_text: str) -> set[str]:
    """Classify a Classification field into STEEPs codes (3-layer detection)."""
    category_part = _FIELD_SEPARATOR_RE.split(field_text, maxsplit=1)[0]
    found: set[str] = set()
    for ko, code in _STEEPS_KO_TO_CODE.items():
        if re.search(rf"(?<![가-힣]){re.escape(ko)}(?![가-힣])", category_part):
            found.add(code)
    for paren_match in re.finditer(r"\(([A-Za-z_]+)", category_part):
        token = paren_match.group(1)
        if token in _CODE_TO_STEEPS:
            found.add(_CODE_TO_STEEPS[token])
    if not found:
        for token_match in re.finditer(r"\b([A-Za-z_]+)\b", category_part):
            token = token_match.group(1)
            if token in _CODE_TO_STEEPS:
                found.add(_CODE_TO_STEEPS[token])
    return found


# ---------------------------------------------------------------------------
# QC Checks
# ---------------------------------------------------------------------------

def _extract_ranked_signals(ranked_data: dict) -> list[dict]:
    """Extract ranked signal list from priority-ranked JSON.
    Handles format variations: 'top_10', 'ranked_signals', or 'signals'."""
    for key in ("top_10", "ranked_signals", "signals"):
        if key in ranked_data and isinstance(ranked_data[key], list):
            return ranked_data[key]
    return []


def _get_signal_psst(item: dict) -> int:
    """Extract pSST score from a ranked signal item.
    Handles variations: 'psst', 'psst_score', 'pSST'."""
    for key in ("psst", "psst_score", "pSST"):
        if key in item:
            return int(item[key])
    return 0


def _check_qc001_priority_order(
    vr: QCValidationReport,
    content: str,
    ranked_data: dict,
    language: str,
) -> None:
    """QC-001: Priority Order Consistency.
    Report signal order must match priority-ranked JSON pSST order."""
    report_titles = _extract_signal_titles(content, language)
    json_top = _extract_ranked_signals(ranked_data)

    if not json_top:
        vr.results.append(QCCheckResult(
            check_id="QC-001", level="CRITICAL",
            description="Priority order consistency (report vs ranked JSON)",
            passed=False, detail="No 'top_10' found in ranked JSON",
            remedy="Ensure priority-ranked JSON contains a 'top_10' array.",
        ))
        return

    if not report_titles:
        vr.results.append(QCCheckResult(
            check_id="QC-001", level="CRITICAL",
            description="Priority order consistency (report vs ranked JSON)",
            passed=False, detail="No signal blocks found in report",
            remedy="Report must contain Priority N: ... signal headers.",
        ))
        return

    # Compare rank ordering for the top N signals present in both
    max_compare = min(len(json_top), len(report_titles), 10)
    mismatches = []
    for i in range(max_compare):
        json_rank = json_top[i].get("rank", i + 1)
        report_rank = report_titles[i][0]
        if report_rank != json_rank:
            mismatches.append(
                f"Position {i+1}: report has Priority {report_rank}, "
                f"JSON expects rank {json_rank}"
            )

    # Note: We do NOT check pSST monotonic ordering because ranking may use
    # a composite priority_score (impact*0.4 + probability*0.3 + ...), which
    # can differ from raw pSST. The rank field is the authoritative ordering.

    passed = len(mismatches) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-001", level="CRITICAL",
        description="Priority order consistency (report vs ranked JSON)",
        passed=passed,
        detail="\n".join(mismatches) if mismatches else "",
        remedy="Re-order signal blocks in report to match pSST ranking from priority-ranked JSON."
            if not passed else "",
    ))


def _check_qc002_exec_summary_top3(
    vr: QCValidationReport,
    content: str,
    ranked_data: dict,
    language: str,
) -> None:
    """QC-002: Executive Summary Top-3 Match.
    Section 1 must reference the same top-3 signals as Section 2."""
    if language == "en":
        s1_header = "## 1. Executive Summary"
    else:
        s1_header = "## 1. 경영진 요약"

    s1_text = _extract_section(content, s1_header) or ""
    json_top3 = _extract_ranked_signals(ranked_data)[:3]

    if not json_top3:
        vr.results.append(QCCheckResult(
            check_id="QC-002", level="ERROR",
            description="Executive Summary top-3 match",
            passed=False, detail="No top-3 signals in ranked JSON",
            remedy="Ensure priority-ranked JSON has at least 3 entries in top_10.",
        ))
        return

    if not s1_text.strip():
        vr.results.append(QCCheckResult(
            check_id="QC-002", level="ERROR",
            description="Executive Summary top-3 match",
            passed=False, detail="Section 1 (Executive Summary) is empty or missing",
            remedy="Section 1 must contain top-3 signal summaries.",
        ))
        return

    # Check: each top-3 signal title (or significant keywords) appears in Section 1
    s1_lower = s1_text.lower()
    missing = []
    for item in json_top3:
        title = item.get("title", "")
        # Extract significant words (>3 chars) from title
        keywords = [w for w in re.split(r"[\s\-—–/]+", title.lower()) if len(w) > 3]
        # Require at least 40% of keywords present in Section 1
        if not keywords:
            continue
        found = sum(1 for kw in keywords if kw in s1_lower)
        ratio = found / len(keywords)
        if ratio < 0.4:
            missing.append(
                f"Rank {item.get('rank', '?')}: '{title}' — "
                f"only {found}/{len(keywords)} keywords found in Sec 1"
            )

    passed = len(missing) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-002", level="ERROR",
        description="Executive Summary top-3 match",
        passed=passed,
        detail="\n".join(missing) if missing else "",
        remedy="Section 1 must summarize all top-3 signals from the priority ranking."
            if not passed else "",
    ))


def _check_qc003_psst_badge(
    vr: QCValidationReport,
    content: str,
    ranked_data: dict,
    language: str,
) -> None:
    """QC-003: pSST Badge Accuracy.
    Report pSST score/grade badges must match the ranked JSON scores."""
    # Extract pSST badges from report: "pSST 85/A" or "pSST 85/B" format
    badge_pattern = r"pSST\s*(\d+)\s*/\s*([A-F])"
    report_badges = {}
    for m in re.finditer(badge_pattern, content):
        score = int(m.group(1))
        grade = m.group(2)
        report_badges[score] = grade

    json_top = _extract_ranked_signals(ranked_data)
    mismatches = []
    failed_ids = []

    for item in json_top:
        json_score = _get_signal_psst(item)
        json_id = item.get("id", "unknown")
        expected = _expected_grade(json_score)

        # Find this score in report badges
        if json_score in report_badges:
            actual_grade = report_badges[json_score]
            if actual_grade != expected:
                mismatches.append(
                    f"Signal {json_id}: pSST {json_score} should be grade "
                    f"'{expected}' but report shows '{actual_grade}'"
                )
                failed_ids.append(json_id)

    # Also check: report badges that don't match expected grade
    for score, grade in report_badges.items():
        expected = _expected_grade(score)
        if grade != expected and f"pSST {score} should be grade" not in "\n".join(mismatches):
            mismatches.append(
                f"Report badge pSST {score}/{grade}: expected grade '{expected}'"
            )

    passed = len(mismatches) == 0
    # Build dynamic remedy from actual thresholds
    thresholds, grade_a = _load_grade_thresholds()
    a_min = grade_a if grade_a is not None else thresholds.get("very_high", 90)
    b_min = thresholds.get("confident", 70)
    c_min = thresholds.get("low", 50)
    remedy_text = (
        f"Correct pSST grade letters to match thresholds.yaml: "
        f"A>={a_min}, B={b_min}-{a_min-1}, C={c_min}-{b_min-1}, D<{c_min}."
    ) if not passed else ""
    vr.results.append(QCCheckResult(
        check_id="QC-003", level="CRITICAL",
        description="pSST badge accuracy (score/grade consistency)",
        passed=passed,
        detail="\n".join(mismatches) if mismatches else "",
        remedy=remedy_text,
        failed_signal_ids=failed_ids,
    ))


def _check_qc004_source_date(
    vr: QCValidationReport,
    content: str,
    scan_window: Optional[dict],
    language: str,
) -> None:
    """QC-004: Source Date Within Scan Window.
    All source dates cited in the report must fall within the scan window."""
    if scan_window is None:
        vr.results.append(QCCheckResult(
            check_id="QC-004", level="ERROR",
            description="Source dates within scan window",
            passed=True,  # Cannot check without scan window — pass with note
            detail="No scan-window JSON provided — check skipped.",
        ))
        return

    # Extract window boundaries
    # Handles multiple JSON formats:
    #   Format A (02-28+): {"start": ..., "end": ...}
    #   Format B (02-27):  {"window_start": ..., "window_end": ...}
    #   Format C (nested): {"windows": {"wf1": {"start": ...}}}
    #   Format D (nested): {"workflows": {"wf1": {"window_start": ...}}}
    window_start = None
    window_end = None

    # Try direct fields first (both naming conventions)
    for start_key, end_key in [("start", "end"), ("window_start", "window_end")]:
        if start_key in scan_window and end_key in scan_window:
            window_start = scan_window[start_key]
            window_end = scan_window[end_key]
            break

    # Fallback: nested container
    if not window_start:
        for container_key in ("windows", "workflows"):
            if container_key in scan_window:
                for _wf_id, wf_window in scan_window[container_key].items():
                    for start_key, end_key in [("start", "end"), ("window_start", "window_end")]:
                        if start_key in wf_window and end_key in wf_window:
                            window_start = wf_window[start_key]
                            window_end = wf_window[end_key]
                            break
                    if window_start:
                        break
            if window_start:
                break

    if not window_start or not window_end:
        vr.results.append(QCCheckResult(
            check_id="QC-004", level="ERROR",
            description="Source dates within scan window",
            passed=False,
            detail="Could not extract start/end from scan-window JSON",
            remedy="Ensure scan-window JSON has 'start' and 'end' fields.",
        ))
        return

    # Parse window boundaries (ISO8601)
    try:
        # Handle timezone-aware datetimes
        win_start = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
        win_end = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as e:
        vr.results.append(QCCheckResult(
            check_id="QC-004", level="ERROR",
            description="Source dates within scan window",
            passed=False, detail=f"Invalid window datetime format: {e}",
            remedy="Scan window JSON must use ISO8601 format.",
        ))
        return

    # Tolerance from scan window (default 30 minutes)
    tolerance_minutes = scan_window.get("tolerance_minutes", 30)

    # Extract source dates from report: "published YYYY-MM-DD" pattern
    date_pattern = r"published\s+(\d{4}-\d{2}-\d{2})"
    out_of_range = []
    for m in re.finditer(date_pattern, content):
        pub_date_str = m.group(1)
        try:
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            # Date-level check: published date should be within window start date - tolerance
            # to window end date + tolerance (whole-day granularity)
            win_start_date = win_start.replace(hour=0, minute=0, second=0, microsecond=0)
            win_end_date = win_end.replace(hour=23, minute=59, second=59, microsecond=0)
            if pub_date < win_start_date or pub_date > win_end_date:
                out_of_range.append(
                    f"Published {pub_date_str} outside window "
                    f"[{win_start.strftime('%Y-%m-%d')} ~ {win_end.strftime('%Y-%m-%d')}]"
                )
        except ValueError:
            continue

    passed = len(out_of_range) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-004", level="ERROR",
        description="Source dates within scan window",
        passed=passed,
        detail="\n".join(out_of_range) if out_of_range else "",
        remedy="Remove or flag signals with publication dates outside the scan window."
            if not passed else "",
    ))


def _check_qc005_cross_impact_refs(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-005: Cross-Impact Reference Validity.
    Section 4 cross-impact pairs (A ↔ B) must reference signals that exist in Section 2."""
    if language == "en":
        s4_header = "## 4. Patterns and Connections"
    else:
        s4_header = "## 4. 패턴 및 연결고리"

    s4_text = _extract_section(content, s4_header) or ""

    # Extract all ↔ pairs — handles both plain and bold formats:
    #   Pattern A: "Topic A ↔ Topic B"
    #   Pattern B: "**Topic A ↔ Topic B**"
    #   Pattern C: "1. **Topic A ↔ Topic B** (Signals ...)"
    # Strategy: first strip bold markers, then extract ↔ pairs.
    # Right side is bounded by: "(" for signal citations, ":" for descriptions, or EOL.
    s4_cleaned = re.sub(r"\*\*", "", s4_text)
    pair_pattern = r"([^↔\n]{3,}?)\s*↔\s*([^↔\n(:]{3,})"
    pairs = re.findall(pair_pattern, s4_cleaned)

    if not pairs:
        # No cross-impact pairs found — this is checked by S4-002 in validate_report.py
        vr.results.append(QCCheckResult(
            check_id="QC-005", level="ERROR",
            description="Cross-impact reference validity (Section 4 ↔ Section 2)",
            passed=True,
            detail="No ↔ pairs found in Section 4 — deferred to S4-002 check.",
        ))
        return

    # Get all signal titles from report
    signal_titles = _extract_signal_titles(content, language)
    title_set = {_normalize_title(title) for _, title in signal_titles}

    # Extract signal number set for citation validation
    report_ranks = {rank for rank, _ in signal_titles}

    # For each ↔ pair, check if it references actual signals.
    # Cross-impact references come in two forms:
    #   A. Direct title reference ("Iran Crisis" ≈ signal title)
    #   B. Thematic label with signal citations ("AI Critique" + "(Signals 3, 15)")
    # Strategy: find the full line in s4_cleaned containing the ↔ pair.
    # If explicit signal numbers are cited and valid, the pair is valid.
    invalid_refs = []
    s4_lines = s4_cleaned.split("\n")
    for left, right in pairs:
        # Find the full line containing this pair
        full_line = ""
        left_needle = left.strip()[:20]  # Use prefix to find line
        for line in s4_lines:
            if left_needle in line and "↔" in line:
                full_line = line
                break

        # Check for explicit signal number citations in full line AND pair text.
        # Patterns: "(Signals 3, 15, 19)", "(Signal #11)", "Signal #12"
        search_text = full_line + " " + left + " " + right
        cited_nums = []
        for cite_match in re.finditer(r"Signal[s]?\s*#?\s*([\d,\s#]+)", search_text, re.IGNORECASE):
            cited_nums.extend(int(n) for n in re.findall(r"\d+", cite_match.group(1)))
        # If explicit signal citations exist, the reference is traceable.
        # (Condensed signals beyond top-10 may lack Priority headers but
        # citing "Signal #11" proves the author traced to specific signals.)
        if cited_nums:
            continue  # Explicitly cited signals — pair is traceable

        # Strip leading numbering like "1. " or "- "
        left_stripped = re.sub(r"^\d+\.\s*", "", left.strip()).strip()
        right_stripped = re.sub(r"^\d+\.\s*", "", right.strip()).strip()
        left_clean = _normalize_title(left_stripped)
        right_clean = _normalize_title(right_stripped)

        for ref_text, original in [(left_clean, left_stripped), (right_clean, right_stripped)]:
            if not ref_text or len(ref_text) < 3:
                continue
            # Strategy 1: Jaro-Winkler similarity
            best_score = 0.0
            for t in title_set:
                score = _jaro_winkler_similarity(ref_text, t)
                best_score = max(best_score, score)

            # Strategy 2: Substring containment (handles abbreviated refs)
            has_substring = any(ref_text in t or t in ref_text for t in title_set)

            # Strategy 3: Keyword overlap (handles thematic references)
            ref_words = set(ref_text.split())
            ref_words = {w for w in ref_words if len(w) > 2}  # Skip short words
            best_keyword_ratio = 0.0
            if ref_words:
                for t in title_set:
                    t_words = set(t.split())
                    overlap = len(ref_words & t_words)
                    ratio = overlap / len(ref_words)
                    best_keyword_ratio = max(best_keyword_ratio, ratio)

            if best_score < 0.70 and not has_substring and best_keyword_ratio < 0.50:
                invalid_refs.append(
                    f"'{original}' (best JW: {best_score:.2f}, keyword: {best_keyword_ratio:.0%}) — "
                    f"no matching signal in Section 2"
                )

    passed = len(invalid_refs) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-005", level="ERROR",
        description="Cross-impact reference validity (Section 4 ↔ Section 2)",
        passed=passed,
        detail="\n".join(invalid_refs[:10]) if invalid_refs else "",
        remedy="Section 4 cross-impact pairs must reference actual signals from Section 2."
            if not passed else "",
    ))


def _check_qc006_field_depth(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-006: Field Depth Minimum.
    Each signal's 9 fields must have sufficient content depth.

    Minimums:
    - Detailed Description: >= 3 sentences
    - Inference: >= 2 sentences
    - Stakeholders: >= 3 items (comma or semicolon separated)
    - Monitoring Indicators: >= 3 items
    - Other fields: >= 1 sentence
    """
    blocks = _extract_signal_blocks(content, language)

    if language == "en":
        depth_rules = {
            "Detailed Description": ("sentences", 3),
            "Inference": ("sentences", 2),
            "Stakeholders": ("items", 3),
            "Monitoring Indicators": ("items", 3),
        }
        field_names = [
            "Classification", "Source", "Key Facts", "Quantitative Metrics",
            "Impact", "Detailed Description", "Inference", "Stakeholders",
            "Monitoring Indicators",
        ]
    else:
        depth_rules = {
            "상세 설명": ("sentences", 3),
            "추론": ("sentences", 2),
            "이해관계자": ("items", 3),
            "모니터링 지표": ("items", 3),
        }
        field_names = [
            "분류", "출처", "핵심 사실", "정량 지표", "영향도",
            "상세 설명", "추론", "이해관계자", "모니터링 지표",
        ]

    shallow_signals = []
    failed_ids = []

    for block in blocks[:10]:  # Check top 10 only
        block_text = block["text"]
        issues = []
        for fname in field_names:
            # Extract field content
            field_match = re.search(
                rf"\*\*{re.escape(fname)}\*\*[:\s]*([^\n]*(?:\n(?!\d+\.\s*\*\*|\*\*|###|---)[^\n]*)*)",
                block_text,
            )
            if not field_match:
                continue
            field_content = field_match.group(1).strip()

            if fname in depth_rules:
                check_type, min_count = depth_rules[fname]
                if check_type == "sentences":
                    # Count sentences by period/question mark/exclamation
                    sentences = re.split(r"[.!?]+", field_content)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
                    if len(sentences) < min_count:
                        issues.append(
                            f"**{fname}**: {len(sentences)} sentences (min {min_count})"
                        )
                elif check_type == "items":
                    # Count items by comma, semicolon, or newline separation
                    items = re.split(r"[,;]\s*|\n", field_content)
                    items = [it.strip() for it in items if len(it.strip()) > 2]
                    if len(items) < min_count:
                        issues.append(
                            f"**{fname}**: {len(items)} items (min {min_count})"
                        )
            else:
                # Other fields: at least 1 meaningful sentence (>20 chars)
                if len(field_content) < 20:
                    issues.append(f"**{fname}**: content too short ({len(field_content)} chars)")

        if issues:
            shallow_signals.append(
                f"Priority {block['rank']}: {'; '.join(issues)}"
            )
            failed_ids.append(f"priority-{block['rank']}")

    passed = len(shallow_signals) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-006", level="ERROR",
        description="Field depth minimum (per-field content analysis)",
        passed=passed,
        detail="\n".join(shallow_signals[:5]) if shallow_signals else "",
        remedy="Expand shallow fields: Detailed Description needs >=3 sentences, "
               "Inference >=2, Stakeholders >=3 items, Monitoring Indicators >=3 items."
            if not passed else "",
        failed_signal_ids=failed_ids,
    ))


def _check_qc007_steeps_content(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-007: STEEPs Classification vs Content Consistency.
    Flags signals where the classification field doesn't match content keywords.
    Level WARN — flags for LLM quality-reviewer to investigate."""
    blocks = _extract_signal_blocks(content, language)
    classification_field = "Classification" if language == "en" else "분류"

    flagged = []
    flagged_ids = []

    for block in blocks[:10]:
        block_text = block["text"]
        # Extract classification field
        class_match = re.search(
            rf"\*\*{re.escape(classification_field)}\*\*[:\s]*([^\n]+)",
            block_text,
        )
        if not class_match:
            continue
        class_text = class_match.group(1).strip()
        declared_codes = _classify_steeps_field(class_text)

        if not declared_codes:
            flagged.append(
                f"Priority {block['rank']}: no STEEPs code detected in classification"
            )
            flagged_ids.append(f"priority-{block['rank']}")
            continue

        # Check content keywords match
        block_lower = block_text.lower()
        for code in declared_codes:
            keywords = _STEEPS_CONTENT_KEYWORDS.get(code, [])
            if not keywords:
                continue
            found = sum(1 for kw in keywords if kw.lower() in block_lower)
            # Require at least 2 keyword matches for content consistency
            if found < 2:
                flagged.append(
                    f"Priority {block['rank']}: classified as {code} but only "
                    f"{found} content keywords found (min 2)"
                )
                flagged_ids.append(f"priority-{block['rank']}")

    passed = len(flagged) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-007", level="WARN",
        description="STEEPs classification vs content consistency (flags for LLM review)",
        passed=passed,
        detail="\n".join(flagged[:5]) if flagged else "",
        remedy="Review flagged signals: classification may not match actual content. "
               "LLM quality-reviewer should assess these cases."
            if not passed else "",
        failed_signal_ids=flagged_ids,
    ))


def _check_qc008_intra_duplicates(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-008: Intra-Report Duplicate Detection.
    Uses Jaro-Winkler similarity on normalized signal titles.
    Threshold: >= 0.85 similarity is flagged as potential duplicate."""
    signal_titles = _extract_signal_titles(content, language)

    if len(signal_titles) < 2:
        vr.results.append(QCCheckResult(
            check_id="QC-008", level="CRITICAL",
            description="Intra-report duplicate detection (Jaro-Winkler >= 0.85)",
            passed=True,
            detail="Fewer than 2 signals — no duplicate check possible.",
        ))
        return

    duplicates = []
    failed_ids = []
    normalized = [(rank, title, _normalize_title(title)) for rank, title in signal_titles]

    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            rank_i, title_i, norm_i = normalized[i]
            rank_j, title_j, norm_j = normalized[j]
            sim = _jaro_winkler_similarity(norm_i, norm_j)
            if sim >= 0.85:
                duplicates.append(
                    f"Priority {rank_i} \u2194 Priority {rank_j}: "
                    f"similarity {sim:.2f} — '{title_i}' vs '{title_j}'"
                )
                failed_ids.extend([f"priority-{rank_i}", f"priority-{rank_j}"])

    passed = len(duplicates) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-008", level="CRITICAL",
        description="Intra-report duplicate detection (Jaro-Winkler >= 0.85)",
        passed=passed,
        detail="\n".join(duplicates) if duplicates else "",
        remedy="Remove or merge duplicate signals. Each signal must be distinct."
            if not passed else "",
        failed_signal_ids=list(set(failed_ids)),
    ))


# ---------------------------------------------------------------------------
# Vague language blocklist for QC-010
# ---------------------------------------------------------------------------

_VAGUE_BLOCKLIST_EN = [
    "significant impact",
    "will be important",
    "could be significant",
    "may have implications",
    "remains to be seen",
    "time will tell",
    "only time will tell",
    "it is unclear",
    "further research is needed",
    "more data is needed",
    "this is a developing story",
    "this could go either way",
    "the future is uncertain",
    "various stakeholders",
    "many experts",
    "some analysts",
    "industry observers",
    "it is expected that",
    "it is anticipated that",
    "is likely to have an impact",
    "will probably affect",
    "might play a role",
    "could potentially",
    "in the coming years",
    "going forward",
    "at the end of the day",
]

_VAGUE_BLOCKLIST_KO = [
    "상당한 영향",
    "중요할 것이다",
    "중요할 수 있다",
    "시사하는 바가 있다",
    "두고 볼 일이다",
    "시간이 지나면 알 수 있다",
    "불분명하다",
    "추가 연구가 필요하다",
    "더 많은 데이터가 필요하다",
    "주목할 필요가 있다",
    "다양한 이해관계자",
    "많은 전문가",
    "일부 분석가",
    "업계 관계자",
    "예상된다",
    "영향을 미칠 것으로 보인다",
    "역할을 할 수 있다",
    "앞으로",
    "향후",
]


# ---------------------------------------------------------------------------
# Action verb lists for QC-013
# ---------------------------------------------------------------------------

_ACTION_VERBS_EN = [
    "monitor", "track", "prepare", "assess", "evaluate", "review",
    "develop", "implement", "establish", "accelerate", "prioritize",
    "invest", "diversify", "hedge", "mitigate", "engage", "strengthen",
    "build", "launch", "negotiate", "audit", "scenario-plan",
    "lock in", "secure", "deploy", "update", "revise", "explore",
]

_ACTION_VERBS_KO = [
    "모니터링", "추적", "준비", "평가", "검토", "개발",
    "구현", "수립", "가속", "우선순위", "투자", "다각화",
    "헤지", "완화", "강화", "구축", "협상", "감사",
    "시나리오", "확보", "배치", "업데이트", "수정", "탐색",
    "대비", "점검", "분석", "조치",
]


def _check_qc009_quantitative_grounding(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-009: Quantitative Grounding.
    Top-10 signals' 'Quantitative Metrics' (정량 지표) field must contain
    at least 2 distinct numeric values (integers, decimals, percentages, currency).

    Rationale: 정량 지표 without numbers is a contradiction — the field's purpose
    is to provide measurable data points. Vague qualitative statements
    (e.g., "multiple agencies affected") do not satisfy this field's contract.
    """
    blocks = _extract_signal_blocks(content, language)
    field_name = "Quantitative Metrics" if language == "en" else "정량 지표"

    # Regex: integers, decimals, percentages, currency ($, €, ¥, ₩), fractions
    numeric_pattern = re.compile(
        r"(?:"
        r"[\$€¥₩£][\s]*\d[\d,]*(?:\.\d+)?"  # Currency values: $3T, ₩1,200
        r"|\d[\d,]*(?:\.\d+)?[\s]*%"          # Percentages: 40%, 3.5%
        r"|\d[\d,]*(?:\.\d+)?[\s]*(?:x|X)"    # Multipliers: 10x
        r"|\d[\d,]*(?:\.\d+)?[\s]*(?:B|T|M|K|billion|trillion|million)" # Magnitudes
        r"|\d[\d,]*(?:\.\d+)?[\s]*(?:GW|MW|kW|GWh|MWh|TWh)"  # Energy units
        r"|\d[\d,]*(?:\.\d+)?[\s]*/[\s]*\d+"  # Fractions/scores: 82/100
        r"|\b\d{1,3}(?:,\d{3})+\b"            # Comma-separated numbers: 1,200,000
        r"|\b\d+(?:\.\d+)?\b"                 # Plain numbers: 42, 3.5
        r")"
    )

    insufficient = []
    failed_ids = []

    for block in blocks[:10]:  # Top 10 only
        block_text = block["text"]
        # Extract the Quantitative Metrics field content
        field_match = re.search(
            rf"\*\*{re.escape(field_name)}\*\*[:\s]*([^\n]*(?:\n(?!\d+\.\s*\*\*|\*\*|###|---)[^\n]*)*)",
            block_text,
        )
        if not field_match:
            insufficient.append(
                f"Priority {block['rank']}: '{field_name}' field not found"
            )
            failed_ids.append(f"priority-{block['rank']}")
            continue

        field_content = field_match.group(1).strip()
        # Find all numeric values
        nums = numeric_pattern.findall(field_content)
        # Deduplicate: normalize and count distinct values
        distinct = set()
        for n in nums:
            # Strip currency symbols and whitespace for dedup
            cleaned = re.sub(r"[\s$€¥₩£%xXBTMKGWMWkWhTWh,]", "", n).strip(".")
            if cleaned and any(c.isdigit() for c in cleaned):
                distinct.add(cleaned)

        if len(distinct) < 2:
            insufficient.append(
                f"Priority {block['rank']}: '{field_name}' has {len(distinct)} "
                f"numeric value(s) (min 2). Content: \"{field_content[:80]}...\""
            )
            failed_ids.append(f"priority-{block['rank']}")

    passed = len(insufficient) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-009", level="ERROR",
        description="Quantitative grounding (numeric values in Quantitative Metrics)",
        passed=passed,
        detail="\n".join(insufficient[:5]) if insufficient else "",
        remedy="Each signal's Quantitative Metrics field must contain at least 2 "
               "distinct numeric values (e.g., dollar amounts, percentages, counts)."
            if not passed else "",
        failed_signal_ids=failed_ids,
    ))


def _check_qc010_vague_language(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-010: Vague Language Blocklist.
    Checks Impact (영향도) and Inference (추론) fields of top-10 signals
    for vague/filler phrases that reduce analytical specificity.

    Level WARN — flags for report improvement but not blocking.
    """
    blocks = _extract_signal_blocks(content, language)

    if language == "en":
        target_fields = ["Impact", "Inference"]
        blocklist = _VAGUE_BLOCKLIST_EN
    else:
        target_fields = ["영향도", "추론"]
        blocklist = _VAGUE_BLOCKLIST_KO

    flagged = []
    flagged_ids = []

    for block in blocks[:10]:
        block_text = block["text"]
        block_issues = []

        for fname in target_fields:
            field_match = re.search(
                rf"\*\*{re.escape(fname)}\*\*[:\s]*([^\n]*(?:\n(?!\d+\.\s*\*\*|\*\*|###|---)[^\n]*)*)",
                block_text,
            )
            if not field_match:
                continue
            field_content = field_match.group(1).strip().lower()

            matches = []
            for phrase in blocklist:
                if phrase.lower() in field_content:
                    matches.append(phrase)

            if matches:
                block_issues.append(
                    f"**{fname}**: found {len(matches)} vague phrase(s): "
                    f"{', '.join(repr(m) for m in matches[:3])}"
                )

        if block_issues:
            flagged.append(
                f"Priority {block['rank']}: {'; '.join(block_issues)}"
            )
            flagged_ids.append(f"priority-{block['rank']}")

    passed = len(flagged) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-010", level="WARN",
        description="Vague language blocklist (Impact/Inference specificity)",
        passed=passed,
        detail="\n".join(flagged[:5]) if flagged else "",
        remedy="Replace vague phrases with specific, measurable statements. "
               "Avoid 'significant impact', 'will be important', 'remains to be seen' etc."
            if not passed else "",
        failed_signal_ids=flagged_ids,
    ))


def _extract_section5_implications(content: str, language: str) -> list[dict]:
    """Extract individual implications from Section 5 subsections.

    Returns list of dicts with keys:
      'subsection': '5.1'|'5.2'|'5.3',
      'number': int (numbered item within subsection),
      'text': str (full text of the implication).
    """
    if language == "en":
        s5_header = "## 5. Strategic Implications"
    else:
        s5_header = "## 5. 전략적 시사점"

    s5_text = _extract_section(content, s5_header)
    if not s5_text:
        return []

    implications = []

    # Split by subsection headers (### 5.1, ### 5.2, ### 5.3)
    subsection_pattern = re.compile(r"###\s*(5\.\d)\s+.*")
    subsection_splits = list(subsection_pattern.finditer(s5_text))

    for idx, m in enumerate(subsection_splits):
        sub_id = m.group(1)
        start = m.end()
        end = subsection_splits[idx + 1].start() if idx + 1 < len(subsection_splits) else len(s5_text)
        sub_text = s5_text[start:end]

        # Section 5.1 and 5.2: numbered items (1. **Title**: ...)
        # Section 5.3: bullet items (- **Title**: ...)
        if sub_id in ("5.1", "5.2"):
            # Numbered items: "1. **...**: ..." or "1. ..."
            item_pattern = re.compile(r"^\s*(\d+)\.\s+(.*)", re.MULTILINE)
            item_starts = list(item_pattern.finditer(sub_text))
            for i, im in enumerate(item_starts):
                num = int(im.group(1))
                istart = im.start()
                iend = item_starts[i + 1].start() if i + 1 < len(item_starts) else end - start
                full_text = sub_text[istart:iend].strip()
                implications.append({
                    "subsection": sub_id,
                    "number": num,
                    "text": full_text,
                })
        elif sub_id == "5.3":
            # Bullet items: "- **Title**: ..."
            item_pattern = re.compile(r"^\s*[-•]\s+(.*)", re.MULTILINE)
            item_starts = list(item_pattern.finditer(sub_text))
            for i, im in enumerate(item_starts):
                istart = im.start()
                iend = item_starts[i + 1].start() if i + 1 < len(item_starts) else end - start
                full_text = sub_text[istart:iend].strip()
                implications.append({
                    "subsection": sub_id,
                    "number": i + 1,
                    "text": full_text,
                })

    return implications


def _check_qc011_cross_signal_synthesis(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-011: Cross-Signal Synthesis in Section 5.
    Each implication in Section 5.1 and 5.2 must reference at least 2 signals
    (by number, title keyword, or explicit 'Signal(s) N' citation).

    This ensures strategic implications are synthesized from multiple signals
    rather than being single-signal restatements.
    """
    implications = _extract_section5_implications(content, language)
    signal_titles = _extract_signal_titles(content, language)
    signal_keywords: dict[int, set[str]] = {}
    for rank, title in signal_titles:
        # Extract significant words (>3 chars) from each signal title
        words = {w.lower() for w in re.split(r"[\s\-—–/,]+", title) if len(w) > 3}
        signal_keywords[rank] = words

    # Only check 5.1 and 5.2 (actionable implications, not monitoring watchlist)
    target_implications = [imp for imp in implications if imp["subsection"] in ("5.1", "5.2")]

    if not target_implications:
        vr.results.append(QCCheckResult(
            check_id="QC-011", level="ERROR",
            description="Cross-signal synthesis in Section 5 (≥2 signal refs per implication)",
            passed=True,
            detail="No implications found in Section 5.1/5.2 — deferred to structural check.",
        ))
        return

    weak_implications = []

    for imp in target_implications:
        text = imp["text"]
        text_lower = text.lower()

        # Strategy 1: Explicit signal number references
        # Patterns: "Signal 3", "Signals 1, 5", "Signal #7", "Priority 2"
        explicit_refs: set[int] = set()
        for ref_match in re.finditer(
            r"(?:Signal|Priority|시그널|우선순위)[s]?\s*#?\s*([\d,\s#and]+)",
            text, re.IGNORECASE
        ):
            for num in re.findall(r"\d+", ref_match.group(1)):
                explicit_refs.add(int(num))

        # Strategy 2: Title keyword matching (≥2 keywords from a signal title)
        keyword_matched_signals: set[int] = set()
        for rank, kws in signal_keywords.items():
            if len(kws) < 2:
                continue
            matched = sum(1 for kw in kws if kw in text_lower)
            if matched >= 2:
                keyword_matched_signals.add(rank)

        total_refs = len(explicit_refs | keyword_matched_signals)

        if total_refs < 2:
            weak_implications.append(
                f"Section {imp['subsection']} item {imp['number']}: "
                f"only {total_refs} signal reference(s) detected "
                f"(explicit: {sorted(explicit_refs)}, keyword: {sorted(keyword_matched_signals)})"
            )

    passed = len(weak_implications) == 0
    vr.results.append(QCCheckResult(
        check_id="QC-011", level="ERROR",
        description="Cross-signal synthesis in Section 5 (≥2 signal refs per implication)",
        passed=passed,
        detail="\n".join(weak_implications[:5]) if weak_implications else "",
        remedy="Each strategic implication in Section 5.1/5.2 must synthesize insights "
               "from at least 2 signals. Add explicit signal references (e.g., 'Signals 3, 7')."
            if not passed else "",
    ))


def _check_qc012_time_horizon(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-012: Time Horizon Keywords in Section 5.
    Section 5 must contain temporal specificity — at least some time horizon
    keywords indicating short-term, medium-term, or long-term framing.

    Checks the entire Section 5 for the presence of temporal language.
    """
    if language == "en":
        s5_header = "## 5. Strategic Implications"
        time_keywords = [
            # Short-term markers
            "week", "weeks", "month", "months", "quarter", "quarterly",
            "immediate", "immediately", "near-term", "short-term",
            "0-6 month", "0–6 month", "within 6 month",
            # Medium-term markers
            "6-18 month", "6–18 month", "1-2 year", "1–2 year",
            "medium-term", "mid-term",
            # Long-term markers
            "year", "years", "decade", "long-term", "long term",
            "18+ month", "2-5 year", "2–5 year",
            # Relative time markers
            "by 2027", "by 2028", "by 2030", "by 2035", "by 2040",
            "in 2026", "in 2027", "in 2028", "in 2029", "in 2030",
            "next quarter", "next year", "coming months", "coming years",
            "within the next", "over the next",
        ]
    else:
        s5_header = "## 5. 전략적 시사점"
        time_keywords = [
            # Short-term markers
            "주", "개월", "분기", "즉시", "단기", "0-6개월", "0–6개월",
            # Medium-term markers
            "6-18개월", "6–18개월", "1-2년", "1–2년", "중기",
            # Long-term markers
            "년", "장기", "10년", "18개월", "2-5년", "2–5년",
            # Relative time markers
            "2027년", "2028년", "2030년", "2035년",
            "향후", "이내", "다음",
        ]

    s5_text = _extract_section(content, s5_header) or ""

    if not s5_text.strip():
        vr.results.append(QCCheckResult(
            check_id="QC-012", level="WARN",
            description="Time horizon keywords in Section 5",
            passed=False,
            detail="Section 5 is empty or missing.",
            remedy="Section 5 must contain Strategic Implications with temporal framing.",
        ))
        return

    # Strip subsection headers (### 5.N ...) to prevent false positives.
    # Headers like "### 5.1 Immediate Actions Required (0-6 months)" contain
    # time keywords that would always satisfy the threshold, making this check
    # useless if headers are included.
    s5_content_only = re.sub(r"^#{2,4}\s+5\.\d+\s+.*$", "", s5_text, flags=re.MULTILINE)
    s5_lower = s5_content_only.lower()
    found_keywords = [kw for kw in time_keywords if kw.lower() in s5_lower]

    # Require at least 3 distinct time keywords across Section 5
    passed = len(found_keywords) >= 3
    vr.results.append(QCCheckResult(
        check_id="QC-012", level="WARN",
        description="Time horizon keywords in Section 5",
        passed=passed,
        detail=f"Found {len(found_keywords)} time keyword(s): "
               f"{', '.join(repr(kw) for kw in found_keywords[:5])}"
               + ("..." if len(found_keywords) > 5 else "")
            if not passed else
               f"Found {len(found_keywords)} time keywords across Section 5.",
        remedy="Section 5 must contain temporal framing: use specific timeframes "
               "(e.g., '0-6 months', 'by 2028', 'within the next year')."
            if not passed else "",
    ))


def _check_qc013_action_verbs(
    vr: QCValidationReport,
    content: str,
    language: str,
) -> None:
    """QC-013: Action Verb Presence in Section 5.
    Section 5 strategic implications must contain actionable language.
    Checks for action verbs like 'Monitor', 'Prepare', 'Track', 'Assess', etc.

    This ensures implications are prescriptive rather than purely descriptive.
    """
    if language == "en":
        s5_header = "## 5. Strategic Implications"
        action_verbs = _ACTION_VERBS_EN
    else:
        s5_header = "## 5. 전략적 시사점"
        action_verbs = _ACTION_VERBS_KO

    s5_text = _extract_section(content, s5_header) or ""

    if not s5_text.strip():
        vr.results.append(QCCheckResult(
            check_id="QC-013", level="WARN",
            description="Action verb presence in Section 5",
            passed=False,
            detail="Section 5 is empty or missing.",
            remedy="Section 5 must contain actionable strategic implications.",
        ))
        return

    # Strip subsection headers to prevent false positives from skeleton structure.
    # Korean headers contain action verbs (모니터링, 강화, 조치) that would inflate count.
    s5_content_only = re.sub(r"^#{2,4}\s+5\.\d+\s+.*$", "", s5_text, flags=re.MULTILINE)
    s5_lower = s5_content_only.lower()
    found_verbs = []
    for verb in action_verbs:
        # Use word boundary for English, simple containment for Korean
        if language == "en":
            if re.search(rf"\b{re.escape(verb)}\b", s5_lower):
                found_verbs.append(verb)
        else:
            if verb in s5_lower:
                found_verbs.append(verb)

    # Require at least 3 distinct action verbs across Section 5
    passed = len(found_verbs) >= 3
    vr.results.append(QCCheckResult(
        check_id="QC-013", level="WARN",
        description="Action verb presence in Section 5",
        passed=passed,
        detail=f"Found {len(found_verbs)} action verb(s): "
               f"{', '.join(repr(v) for v in found_verbs[:5])}"
               + ("..." if len(found_verbs) > 5 else "")
            if not passed else
               f"Found {len(found_verbs)} action verbs across Section 5.",
        remedy="Section 5 must use prescriptive language: 'Monitor', 'Track', "
               "'Prepare', 'Assess', 'Invest', 'Diversify', etc."
            if not passed else "",
    ))


def _check_qc014_exec_summary_stats(
    vr: QCValidationReport,
    content: str,
    ranked_data: dict,
    language: str,
) -> None:
    """QC-014: Executive Summary Statistics vs Source Data.
    Cross-references quantitative statistics in the Executive Summary
    (Section 1, Key Changes Summary) against the priority-ranked JSON.

    Sub-check A: Total signal count — report's "New signals detected: N"
                 must match ranking_metadata.total_ranked.
    Sub-check B: STEEPs distribution — if ranked signals have steeps data,
                 verify per-category counts against the JSON. Skipped when
                 <50% of signals have steeps populated.

    Level ERROR — hallucinated counts reduce trust but are not structural.
    """
    # --- Ground truth from ranked JSON ---
    metadata = ranked_data.get("ranking_metadata", {})
    signals = ranked_data.get("ranked_signals", ranked_data.get("signals", []))
    if not isinstance(signals, list):
        signals = []
    json_total = metadata.get("total_ranked", len(signals))

    # --- Extract Section 1 ---
    if language == "en":
        s1_header = "## 1. Executive Summary"
    else:
        s1_header = "## 1. 경영진 요약"
    s1_text = _extract_section(content, s1_header) or ""

    issues = []
    failed_ids = []

    # ── Sub-check A: Total signal count ──
    report_total = None
    if s1_text:
        if language == "en":
            m = re.search(
                r"[Nn]ew\s+signals?\s+detected[:\s]+\*{0,2}(\d[\d,]*)\*{0,2}",
                s1_text,
            )
        else:
            m = re.search(
                r"(?:신규\s*(?:탐지|감지)\s*(?:시그널|신호)|발견된\s*신규\s*(?:신호|시그널))"
                r"[:\s]*\*{0,2}(\d[\d,]*)\*{0,2}(?:건|개)?",
                s1_text,
            )
        if m:
            report_total = int(m.group(1).replace(",", ""))

    if report_total is not None:
        if report_total != json_total:
            issues.append(
                f"Total count mismatch: report={report_total}, "
                f"source JSON={json_total}"
            )
            failed_ids.append("total-count")
    # If count not found in report, skip sub-check A silently

    # ── Sub-check B: STEEPs distribution ──
    steeps_values = [
        s.get("steeps", "") or s.get("steeps_category", "") or s.get("category", "")
        for s in signals
    ]
    populated = [v for v in steeps_values if v]
    coverage = len(populated) / len(signals) if signals else 0.0

    if coverage >= 0.5:
        json_dist = Counter(populated)

        # Parse STEEPs distribution from report
        report_dist: dict[str, int] = {}

        # Pattern 1: Table rows "| T_Technological | 384 | ..."
        for tm in re.finditer(
            r"\|\s*([A-Za-z_]+)\s*\|\s*(\d[\d,]*)\s*\|",
            s1_text,
        ):
            cat = tm.group(1)
            cnt = int(tm.group(2).replace(",", ""))
            if _is_steeps_code(cat):
                report_dist[cat] = cnt

        # Pattern 2: Inline "T_Technological (384)" or "T_Technological (9 signals, 36%)"
        if not report_dist:
            for im in re.finditer(
                r"([A-Za-z]_[A-Za-z]+)\s*\((\d[\d,]*)",
                s1_text,
            ):
                cat = im.group(1)
                cnt = int(im.group(2).replace(",", ""))
                if _is_steeps_code(cat):
                    report_dist[cat] = cnt

        if report_dist:
            for cat, r_count in report_dist.items():
                j_count = json_dist.get(cat, 0)
                tolerance = max(1, int(j_count * 0.10))
                if abs(r_count - j_count) > tolerance:
                    issues.append(
                        f"STEEPs '{cat}': report={r_count}, "
                        f"source={j_count} (tolerance ±{tolerance})"
                    )
                    failed_ids.append(f"steeps-{cat}")

    passed = len(issues) == 0
    detail = ""
    if issues:
        detail = "\n".join(issues[:5])
    elif report_total is not None:
        detail = f"Total count verified ({report_total})"
        if coverage >= 0.5 and report_dist:
            detail += f"; {len(report_dist)} STEEPs categories checked"
    else:
        detail = "No summary statistics found in Section 1 (skipped)"

    vr.results.append(QCCheckResult(
        check_id="QC-014", level="ERROR",
        description="Executive Summary statistics vs source data",
        passed=passed,
        detail=detail,
        remedy="Ensure 'New signals detected' count and STEEPs distribution in "
               "the Executive Summary match the priority-ranked JSON data."
            if not passed else "",
        failed_signal_ids=failed_ids,
    ))


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

def validate_report_quality(
    report_path: str,
    ranked_path: str,
    scan_window_path: Optional[str] = None,
    language: str = "en",
    workflow_id: Optional[str] = None,
) -> QCValidationReport:
    """Run all 14 cross-reference quality checks.

    Args:
        report_path: Path to the markdown report file.
        ranked_path: Path to the priority-ranked JSON file.
        scan_window_path: Optional path to the scan-window JSON file.
        language: 'en' or 'ko' (determines section headers and field names).
        workflow_id: Optional workflow ID to select correct scan window.

    Returns:
        QCValidationReport with all check results.
    """
    vr = QCValidationReport(
        report_path=report_path,
        ranked_path=ranked_path,
        language=language,
    )

    # Load report
    report_file = Path(report_path)
    if not report_file.exists():
        vr.results.append(QCCheckResult(
            check_id="QC-PRE", level="CRITICAL",
            description="Report file exists",
            passed=False, detail=f"File not found: {report_path}",
        ))
        return vr

    content = report_file.read_text(encoding="utf-8")

    # Load ranked JSON
    ranked_file = Path(ranked_path)
    if not ranked_file.exists():
        vr.results.append(QCCheckResult(
            check_id="QC-PRE", level="CRITICAL",
            description="Priority-ranked JSON exists",
            passed=False, detail=f"File not found: {ranked_path}",
        ))
        return vr

    try:
        ranked_data = json.loads(ranked_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        vr.results.append(QCCheckResult(
            check_id="QC-PRE", level="CRITICAL",
            description="Priority-ranked JSON valid",
            passed=False, detail=f"Invalid JSON: {e}",
        ))
        return vr

    # Load scan window (optional)
    scan_window = None
    if scan_window_path:
        sw_file = Path(scan_window_path)
        if sw_file.exists():
            try:
                raw_sw = json.loads(sw_file.read_text(encoding="utf-8"))
                # If workflow_id specified, extract that workflow's window
                if workflow_id:
                    # Handle both formats: "windows" (02-28+) and "workflows" (02-27)
                    for container_key in ("windows", "workflows"):
                        if container_key in raw_sw:
                            wf_window = raw_sw[container_key].get(workflow_id)
                            if wf_window:
                                scan_window = wf_window
                                break
                    if scan_window is None:
                        scan_window = raw_sw
                else:
                    scan_window = raw_sw
            except json.JSONDecodeError:
                pass  # Scan window loading failure is not fatal

    # Run all 13 checks
    _check_qc001_priority_order(vr, content, ranked_data, language)
    _check_qc002_exec_summary_top3(vr, content, ranked_data, language)
    _check_qc003_psst_badge(vr, content, ranked_data, language)
    _check_qc004_source_date(vr, content, scan_window, language)
    _check_qc005_cross_impact_refs(vr, content, language)
    _check_qc006_field_depth(vr, content, language)
    _check_qc007_steeps_content(vr, content, language)
    _check_qc008_intra_duplicates(vr, content, language)
    _check_qc009_quantitative_grounding(vr, content, language)
    _check_qc010_vague_language(vr, content, language)
    _check_qc011_cross_signal_synthesis(vr, content, language)
    _check_qc012_time_horizon(vr, content, language)
    _check_qc013_action_verbs(vr, content, language)
    _check_qc014_exec_summary_stats(vr, content, ranked_data, language)

    return vr


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate report quality via cross-reference checks (Layer 2b)"
    )
    parser.add_argument("report_path", help="Path to the markdown report file")
    parser.add_argument("ranked_path", help="Path to the priority-ranked JSON file")
    parser.add_argument(
        "--scan-window", default=None, dest="scan_window",
        help="Path to scan-window JSON file (enables QC-004 source date check)",
    )
    parser.add_argument(
        "--language", choices=["en", "ko"], default="en",
        help="Report language (default: en)",
    )
    parser.add_argument(
        "--workflow-id", default=None, dest="workflow_id",
        help="Workflow ID to select correct scan window (e.g., wf1-general)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output results as JSON instead of human-readable summary",
    )
    args = parser.parse_args()

    result = validate_report_quality(
        report_path=args.report_path,
        ranked_path=args.ranked_path,
        scan_window_path=args.scan_window,
        language=args.language,
        workflow_id=args.workflow_id,
    )

    if args.json_output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.human_summary())

    # Exit code: 0=PASS, 1=FAIL(CRITICAL), 2=WARN
    status = result.overall_status
    if status == "FAIL":
        sys.exit(1)
    elif status == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
