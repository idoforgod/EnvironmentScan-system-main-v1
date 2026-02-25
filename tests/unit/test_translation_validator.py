"""Unit tests for translation_validator.py — Structural EN↔KO Report Validation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from core.translation_validator import (
    validate_translation_pair,
    _count_section_headers,
    _count_subsection_headers,
    _count_signal_blocks,
    _extract_placeholders,
    _count_signal_fields_per_block,
    _count_table_rows,
    _count_horizontal_rules,
    _word_count,
)


# ---------------------------------------------------------------------------
# Matching EN/KO pair for testing
# ---------------------------------------------------------------------------

EN_REPORT = """\
## 1. Executive Summary

### Today's Key Findings (Top 3 Signals)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})

### Key Changes Summary
- New signals detected: {{TOTAL_NEW_SIGNALS}}

---

## 2. Newly Detected Signals

### Priority 1: {{SIGNAL_1_TITLE}}

- **Confidence**: {{SIGNAL_1_PSST}}

1. **Classification**: {{SIGNAL_1_CLASSIFICATION}}
2. **Source**: {{SIGNAL_1_SOURCE}}
3. **Key Facts**: {{SIGNAL_1_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_1_METRICS}}
5. **Impact**: {{SIGNAL_1_IMPACT}}
6. **Detailed Description**: {{SIGNAL_1_DETAIL}}
7. **Inference**: {{SIGNAL_1_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_1_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_1_MONITORING}}

---

## 3. Existing Signal Updates

### 3.1 Strengthening Trends

| Status | Count | Ratio |
|--------|-------|-------|
| New | 5 | 33% |
| Strengthening | 3 | 20% |
"""

KO_REPORT = """\
## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 3 신호)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})

### 주요 변화 요약
- 발견된 신규 신호: {{TOTAL_NEW_SIGNALS}}개

---

## 2. 신규 탐지 신호

### 우선순위 1: {{SIGNAL_1_TITLE}}

- **신뢰도**: {{SIGNAL_1_PSST}}

1. **분류**: {{SIGNAL_1_CLASSIFICATION}}
2. **출처**: {{SIGNAL_1_SOURCE}}
3. **핵심 사실**: {{SIGNAL_1_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_1_METRICS}}
5. **영향도**: {{SIGNAL_1_IMPACT}}
6. **상세 설명**: {{SIGNAL_1_DETAIL}}
7. **추론**: {{SIGNAL_1_INFERENCE}}
8. **이해관계자**: {{SIGNAL_1_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_1_MONITORING}}

---

## 3. 기존 신호 업데이트

### 3.1 강화 추세 (Strengthening)

| 상태 | 수 | 비율 |
|------|---|------|
| 신규 | 5 | 33% |
| 강화 | 3 | 20% |
"""


# ---------------------------------------------------------------------------
# Tests: Extraction Helpers
# ---------------------------------------------------------------------------

class TestExtractionHelpers:

    def test_count_section_headers(self):
        assert _count_section_headers(EN_REPORT) == 3
        assert _count_section_headers(KO_REPORT) == 3

    def test_count_subsection_headers(self):
        assert _count_subsection_headers(EN_REPORT) == 1  # 3.1
        assert _count_subsection_headers(KO_REPORT) == 1

    def test_count_signal_blocks_en(self):
        assert _count_signal_blocks(EN_REPORT) == 1

    def test_count_signal_blocks_ko(self):
        assert _count_signal_blocks(KO_REPORT) == 1

    def test_extract_placeholders(self):
        en_ph = _extract_placeholders(EN_REPORT)
        ko_ph = _extract_placeholders(KO_REPORT)
        assert en_ph == ko_ph

    def test_count_signal_fields(self):
        en_fields = _count_signal_fields_per_block(EN_REPORT)
        ko_fields = _count_signal_fields_per_block(KO_REPORT)
        assert en_fields == [9]
        assert ko_fields == [9]

    def test_count_table_rows(self):
        en_rows = _count_table_rows(EN_REPORT)
        ko_rows = _count_table_rows(KO_REPORT)
        assert en_rows == ko_rows

    def test_count_horizontal_rules(self):
        assert _count_horizontal_rules(EN_REPORT) == 2
        assert _count_horizontal_rules(KO_REPORT) == 2


# ---------------------------------------------------------------------------
# Tests: Full Validation
# ---------------------------------------------------------------------------

class TestValidateTranslationPair:

    def test_matching_pair_passes(self):
        result = validate_translation_pair(EN_REPORT, KO_REPORT)
        assert result["status"] == "PASS"
        assert result["critical_failures"] == 0

    def test_all_checks_present(self):
        result = validate_translation_pair(EN_REPORT, KO_REPORT)
        assert result["total_checks"] == 8
        check_ids = {c["id"] for c in result["checks"]}
        assert "STRUCT-001" in check_ids
        assert "STRUCT-008" in check_ids

    def test_missing_section_fails(self):
        """EN has 3 sections but KO only has 2 → STRUCT-001 FAIL."""
        ko_missing = KO_REPORT.replace("## 3. 기존 신호 업데이트", "")
        result = validate_translation_pair(EN_REPORT, ko_missing)
        s001 = next(c for c in result["checks"] if c["id"] == "STRUCT-001")
        assert s001["status"] == "FAIL"
        assert result["status"] == "FAIL"

    def test_missing_placeholder_fails(self):
        """KO drops a placeholder → STRUCT-004 FAIL."""
        ko_dropped = KO_REPORT.replace("{{SIGNAL_1_MONITORING}}", "모니터링 지표 값")
        result = validate_translation_pair(EN_REPORT, ko_dropped)
        s004 = next(c for c in result["checks"] if c["id"] == "STRUCT-004")
        assert s004["status"] == "FAIL"
        assert "SIGNAL_1_MONITORING" in s004["missing_in_ko"]

    def test_missing_signal_field_fails(self):
        """KO drops a signal field → STRUCT-005 FAIL."""
        # Remove field 9 from KO
        ko_dropped = KO_REPORT.replace("9. **모니터링 지표**: {{SIGNAL_1_MONITORING}}\n", "")
        result = validate_translation_pair(EN_REPORT, ko_dropped)
        s005 = next(c for c in result["checks"] if c["id"] == "STRUCT-005")
        assert s005["status"] == "FAIL"

    def test_word_ratio_within_bounds(self):
        result = validate_translation_pair(EN_REPORT, KO_REPORT)
        s008 = next(c for c in result["checks"] if c["id"] == "STRUCT-008")
        assert s008["status"] == "PASS"
        assert 0.3 <= s008["ratio"] <= 1.5

    def test_empty_reports_handled(self):
        result = validate_translation_pair("", "")
        # Should not crash; word ratio will be edge case
        assert "status" in result


class TestIntegratedSignalBlocks:
    """Test detection of integrated signal block headers."""

    def test_integrated_priority_counted(self):
        content = """\
### Integrated Priority 1: Signal A
### Integrated Priority 2: Signal B
"""
        assert _count_signal_blocks(content) == 2

    def test_mixed_en_ko_not_double_counted(self):
        """A single report should only have EN or KO headers, not both."""
        en_only = "### Priority 1: A\n### Priority 2: B\n"
        assert _count_signal_blocks(en_only) == 2

        ko_only = "### 우선순위 1: A\n### 우선순위 2: B\n"
        assert _count_signal_blocks(ko_only) == 2
