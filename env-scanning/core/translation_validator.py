#!/usr/bin/env python3
"""
Translation Validator — Structural EN↔KO Report Validation
===========================================================
Validates that an English report and its Korean translation have
identical structural properties. All checks are DETERMINISTIC
(Python-only, no LLM). Semantic quality is left to the translation
agent's back-translation check.

Structural Invariants Checked:
    STRUCT-001: Section header count match (## N.)
    STRUCT-002: Subsection header count match (### N.N)
    STRUCT-003: Signal block count match (### Priority N: / ### 우선순위 N:)
    STRUCT-004: Placeholder token set equality ({{TOKEN}})
    STRUCT-005: Signal field count match per block (9 fields each)
    STRUCT-006: Table row count match
    STRUCT-007: Markdown horizontal rule count match (---)
    STRUCT-008: Word count ratio within bounds (KO typically 0.5x-0.9x of EN)

Design Principle: "계산은 Python이, 판단은 LLM이."
    Structural integrity = deterministic = Python validates.
    Translation quality = semantic = LLM validates.

Usage (CLI):
    python3 env-scanning/core/translation_validator.py \\
        --en reports/environmental-scan-2026-02-18-en.md \\
        --ko reports/environmental-scan-2026-02-18.md

Usage (importable):
    from core.translation_validator import validate_translation_pair
    result = validate_translation_pair(en_content, ko_content)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

VERSION = "1.0.0"

# ============================================================================
# Check IDs
# ============================================================================

STRUCT_001 = "STRUCT-001"  # Section header count
STRUCT_002 = "STRUCT-002"  # Subsection header count
STRUCT_003 = "STRUCT-003"  # Signal block count
STRUCT_004 = "STRUCT-004"  # Placeholder set equality
STRUCT_005 = "STRUCT-005"  # Signal field count per block
STRUCT_006 = "STRUCT-006"  # Table row count
STRUCT_007 = "STRUCT-007"  # Horizontal rule count
STRUCT_008 = "STRUCT-008"  # Word count ratio

# Word count ratio bounds (KO / EN)
WORD_RATIO_MIN = 0.3
WORD_RATIO_MAX = 1.5


# ============================================================================
# Extraction Helpers
# ============================================================================

def _count_section_headers(content: str) -> int:
    """Count ## N. section headers (not ### subsections)."""
    return len(re.findall(r"^## \d+\.", content, re.MULTILINE))


def _count_subsection_headers(content: str) -> int:
    """Count ### N.N subsection headers."""
    return len(re.findall(r"^### \d+\.\d+", content, re.MULTILINE))


def _count_signal_blocks(content: str) -> int:
    """Count signal block headers (Priority/우선순위/Integrated Priority/통합 우선순위)."""
    en_pattern = r"^### (?:Integrated )?Priority \d+:"
    ko_pattern = r"^### (?:통합 )?우선순위 \d+:"
    en_count = len(re.findall(en_pattern, content, re.MULTILINE))
    ko_count = len(re.findall(ko_pattern, content, re.MULTILINE))
    return en_count + ko_count


def _extract_placeholders(content: str) -> Set[str]:
    """Extract all {{PLACEHOLDER}} token names."""
    return set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", content))


def _count_signal_fields_per_block(content: str) -> List[int]:
    """Count numbered field lines (1. **Label**: ...) in each signal block."""
    # Split content at signal block headers
    blocks = re.split(r"^### (?:Integrated )?(?:Priority|우선순위|통합 우선순위) \d+:", content, flags=re.MULTILINE)
    if len(blocks) <= 1:
        return []

    field_counts = []
    for block in blocks[1:]:  # Skip content before first signal block
        # Count lines matching "N. **label**:" pattern
        fields = re.findall(r"^\d+\.\s+\*\*[^*]+\*\*:", block, re.MULTILINE)
        field_counts.append(len(fields))
    return field_counts


def _count_table_rows(content: str) -> int:
    """Count markdown table data rows (excluding header and separator)."""
    count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # Skip separator rows (|---|---|)
            if not re.match(r"^\|[\s\-:|]+\|$", stripped):
                count += 1
    return count


def _count_horizontal_rules(content: str) -> int:
    """Count markdown horizontal rules (--- on their own line)."""
    return len(re.findall(r"^---\s*$", content, re.MULTILINE))


def _word_count(content: str) -> int:
    """Approximate word count (split on whitespace)."""
    return len(content.split())


# ============================================================================
# Core Validation
# ============================================================================

def validate_translation_pair(
    en_content: str,
    ko_content: str,
) -> Dict:
    """
    Validate structural integrity between EN and KO report pair.

    All checks are deterministic (Python-only). Returns a report
    with per-check results and overall status.

    Args:
        en_content: English report content
        ko_content: Korean report content

    Returns:
        Validation report dict with:
        - checks: list of individual check results
        - status: "PASS" | "WARN" | "FAIL"
        - critical_failures: count of FAIL checks
        - warnings: count of WARN checks
    """
    checks = []

    # STRUCT-001: Section header count
    en_sections = _count_section_headers(en_content)
    ko_sections = _count_section_headers(ko_content)
    checks.append({
        "id": STRUCT_001,
        "name": "Section header count",
        "en_value": en_sections,
        "ko_value": ko_sections,
        "status": "PASS" if en_sections == ko_sections else "FAIL",
    })

    # STRUCT-002: Subsection header count
    en_subsections = _count_subsection_headers(en_content)
    ko_subsections = _count_subsection_headers(ko_content)
    checks.append({
        "id": STRUCT_002,
        "name": "Subsection header count",
        "en_value": en_subsections,
        "ko_value": ko_subsections,
        "status": "PASS" if en_subsections == ko_subsections else "FAIL",
    })

    # STRUCT-003: Signal block count
    en_signals = _count_signal_blocks(en_content)
    ko_signals = _count_signal_blocks(ko_content)
    checks.append({
        "id": STRUCT_003,
        "name": "Signal block count",
        "en_value": en_signals,
        "ko_value": ko_signals,
        "status": "PASS" if en_signals == ko_signals else "FAIL",
    })

    # STRUCT-004: Placeholder set equality
    en_placeholders = _extract_placeholders(en_content)
    ko_placeholders = _extract_placeholders(ko_content)
    missing_in_ko = en_placeholders - ko_placeholders
    extra_in_ko = ko_placeholders - en_placeholders
    checks.append({
        "id": STRUCT_004,
        "name": "Placeholder token set",
        "en_value": len(en_placeholders),
        "ko_value": len(ko_placeholders),
        "missing_in_ko": sorted(missing_in_ko) if missing_in_ko else [],
        "extra_in_ko": sorted(extra_in_ko) if extra_in_ko else [],
        "status": "PASS" if not missing_in_ko and not extra_in_ko else "FAIL",
    })

    # STRUCT-005: Signal field count per block
    en_fields = _count_signal_fields_per_block(en_content)
    ko_fields = _count_signal_fields_per_block(ko_content)
    fields_match = (len(en_fields) == len(ko_fields) and
                    all(e == k for e, k in zip(en_fields, ko_fields)))
    checks.append({
        "id": STRUCT_005,
        "name": "Signal field count per block",
        "en_value": en_fields,
        "ko_value": ko_fields,
        "status": "PASS" if fields_match else "FAIL",
    })

    # STRUCT-006: Table row count
    en_tables = _count_table_rows(en_content)
    ko_tables = _count_table_rows(ko_content)
    checks.append({
        "id": STRUCT_006,
        "name": "Table row count",
        "en_value": en_tables,
        "ko_value": ko_tables,
        "status": "PASS" if en_tables == ko_tables else "WARN",
    })

    # STRUCT-007: Horizontal rule count
    en_hr = _count_horizontal_rules(en_content)
    ko_hr = _count_horizontal_rules(ko_content)
    checks.append({
        "id": STRUCT_007,
        "name": "Horizontal rule count",
        "en_value": en_hr,
        "ko_value": ko_hr,
        "status": "PASS" if en_hr == ko_hr else "WARN",
    })

    # STRUCT-008: Word count ratio
    en_words = _word_count(en_content)
    ko_words = _word_count(ko_content)
    ratio = ko_words / en_words if en_words > 0 else 0.0
    ratio_ok = WORD_RATIO_MIN <= ratio <= WORD_RATIO_MAX
    checks.append({
        "id": STRUCT_008,
        "name": "Word count ratio (KO/EN)",
        "en_value": en_words,
        "ko_value": ko_words,
        "ratio": round(ratio, 3),
        "bounds": f"[{WORD_RATIO_MIN}, {WORD_RATIO_MAX}]",
        "status": "PASS" if ratio_ok else "WARN",
    })

    # Aggregate results
    critical_failures = sum(1 for c in checks if c["status"] == "FAIL")
    warnings = sum(1 for c in checks if c["status"] == "WARN")

    if critical_failures > 0:
        overall = "FAIL"
    elif warnings > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "module": "translation_validator",
        "version": VERSION,
        "checks": checks,
        "total_checks": len(checks),
        "critical_failures": critical_failures,
        "warnings": warnings,
        "status": overall,
    }


def validate_translation_files(
    en_path: str,
    ko_path: str,
) -> Dict:
    """File I/O wrapper for validate_translation_pair."""
    en_p = Path(en_path)
    ko_p = Path(ko_path)
    if not en_p.exists():
        raise FileNotFoundError(f"EN report not found: {en_path}")
    if not ko_p.exists():
        raise FileNotFoundError(f"KO report not found: {ko_path}")

    en_content = en_p.read_text(encoding="utf-8")
    ko_content = ko_p.read_text(encoding="utf-8")
    result = validate_translation_pair(en_content, ko_content)
    result["en_file"] = str(en_path)
    result["ko_file"] = str(ko_path)
    return result


# ============================================================================
# CLI Entrypoint
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Translation Validator: structural EN\u2194KO report validation"
    )
    parser.add_argument("--en", required=True, help="English report file path")
    parser.add_argument("--ko", required=True, help="Korean report file path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    try:
        result = validate_translation_files(args.en, args.ko)
        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            icon = {"PASS": "\u2705", "WARN": "\u26a0\ufe0f", "FAIL": "\u274c"}
            print(f"\n{icon.get(result['status'], '?')} Translation Validation: {result['status']}")
            print(f"   EN: {args.en}")
            print(f"   KO: {args.ko}")
            print("-" * 50)
            for c in result["checks"]:
                ci = icon.get(c["status"], "?")
                print(f"   {ci} {c['id']} {c['name']}: EN={c['en_value']} KO={c['ko_value']} [{c['status']}]")
            print("-" * 50)
            print(f"   Total: {result['total_checks']} checks | "
                  f"{result['critical_failures']} failures | "
                  f"{result['warnings']} warnings")

        sys.exit(0 if result["status"] != "FAIL" else 1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
