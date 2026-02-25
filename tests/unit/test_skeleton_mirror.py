"""Unit tests for skeleton_mirror.py — Deterministic KO→EN Skeleton Transformation."""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from core.skeleton_mirror import (
    extract_placeholders,
    mirror_skeleton,
    mirror_skeleton_file,
    mirror_all_skeletons,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REFERENCES_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "env-scanner" / "references"

SAMPLE_STANDARD = """\
# 보고서 스켈레톤 템플릿 (Report Skeleton Template)

> **작성 언어**: 한국어 (기술 용어, 고유명사, 약어는 영문 병기 허용)

## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 3 신호)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - 중요도: {{TOP1_IMPORTANCE}}
   - 핵심 내용: {{TOP1_SUMMARY}}

### 주요 변화 요약
- 발견된 신규 신호: {{TOTAL_NEW_SIGNALS}}개
- 주요 영향 도메인: {{DOMAIN_DISTRIBUTION}}

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

## 3. 기존 신호 업데이트

> 활성 추적 스레드: {{EVOLUTION_ACTIVE_THREADS}}개 | 강화: {{EVOLUTION_STRENGTHENING_COUNT}}개

### 3.1 강화 추세 (Strengthening)

| 상태 | 수 | 비율 |
|------|---|------|
| 신규 | {{EVOLUTION_NEW_COUNT}} | {{EVOLUTION_NEW_PCT}} |
| 강화 | {{EVOLUTION_STRENGTHENING_COUNT}} | {{EVOLUTION_STRENGTHENING_PCT}} |
| 반복 등장 | {{EVOLUTION_RECURRING_COUNT}} | {{EVOLUTION_RECURRING_PCT}} |

## 6. Plausible Scenarios(개연성 있는 시나리오)

## 7. 신뢰도 분석

## 8. 부록
"""


# ---------------------------------------------------------------------------
# Tests: Core transformation
# ---------------------------------------------------------------------------

class TestMirrorSkeleton:
    """Tests for the mirror_skeleton() function."""

    def test_placeholder_integrity(self):
        """All {{PLACEHOLDER}} tokens must be preserved exactly."""
        en_content, report = mirror_skeleton(SAMPLE_STANDARD)
        assert report["placeholder_integrity"] is True
        assert report["status"] == "SUCCESS"
        assert report["placeholders_missing"] == []
        assert report["placeholders_added"] == []

    def test_section_headers_translated(self):
        """Section headers (## N.) must be in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "## 1. Executive Summary" in en_content
        assert "## 2. Newly Detected Signals" in en_content
        assert "## 3. Existing Signal Updates" in en_content
        assert "## 6. Plausible Scenarios" in en_content
        assert "## 7. Confidence Analysis" in en_content
        assert "## 8. Appendix" in en_content

    def test_korean_section_headers_removed(self):
        """Korean section headers must NOT remain."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "경영진 요약" not in en_content
        assert "신규 탐지 신호" not in en_content
        assert "기존 신호 업데이트" not in en_content
        assert "개연성 있는 시나리오" not in en_content
        assert "신뢰도 분석" not in en_content
        assert "부록" not in en_content

    def test_signal_field_labels_translated(self):
        """9-field signal labels must be in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "**Classification**:" in en_content
        assert "**Source**:" in en_content
        assert "**Key Facts**:" in en_content
        assert "**Quantitative Metrics**:" in en_content
        assert "**Impact**:" in en_content
        assert "**Detailed Description**:" in en_content
        assert "**Inference**:" in en_content
        assert "**Stakeholders**:" in en_content
        assert "**Monitoring Indicators**:" in en_content

    def test_korean_field_labels_removed(self):
        """Korean field labels must NOT remain."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "**분류**:" not in en_content
        assert "**출처**:" not in en_content
        assert "**핵심 사실**:" not in en_content
        assert "**정량 지표**:" not in en_content
        assert "**상세 설명**:" not in en_content
        assert "**추론**:" not in en_content
        assert "**이해관계자**:" not in en_content
        assert "**모니터링 지표**:" not in en_content

    def test_signal_block_headers_translated(self):
        """### 우선순위 N: must become ### Priority N:."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "### Priority 1: {{SIGNAL_1_TITLE}}" in en_content
        assert "우선순위" not in en_content

    def test_counter_suffixes_removed(self):
        """Korean counter suffixes (개, 시간) after placeholders."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "}}개" not in en_content
        # Check {{TOTAL_NEW_SIGNALS}} has no 개 suffix
        assert "{{TOTAL_NEW_SIGNALS}}\n" in en_content or "{{TOTAL_NEW_SIGNALS}}" in en_content

    def test_evolution_table_translated(self):
        """Evolution status table headers and cells in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "| Status | Count | Ratio |" in en_content
        assert "| New |" in en_content
        assert "| Strengthening |" in en_content
        assert "| Recurring |" in en_content

    def test_subsection_headers_translated(self):
        """Key subsection headers must be in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "### Today's Key Findings" in en_content
        assert "### Key Changes Summary" in en_content
        assert "### 3.1 Strengthening Trends" in en_content

    def test_bullet_labels_translated(self):
        """Inline bullet labels must be in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "- Importance:" in en_content
        assert "- Key Content:" in en_content
        assert "- New signals detected:" in en_content
        assert "**Confidence**:" in en_content

    def test_evolution_blockquote_translated(self):
        """Section 3 evolution summary blockquote in English."""
        en_content, _ = mirror_skeleton(SAMPLE_STANDARD)
        assert "Active tracking threads:" in en_content
        assert "| Strengthening:" in en_content


class TestExtractPlaceholders:
    """Tests for extract_placeholders()."""

    def test_basic_extraction(self):
        text = "Hello {{FOO}} and {{BAR}}"
        result = extract_placeholders(text)
        assert result == {"FOO", "BAR"}

    def test_no_placeholders(self):
        result = extract_placeholders("No placeholders here")
        assert result == set()

    def test_duplicate_placeholders(self):
        text = "{{A}} then {{A}} again"
        result = extract_placeholders(text)
        assert result == {"A"}

    def test_nested_braces_ignored(self):
        text = "{{{NOT_A_PLACEHOLDER}}}"
        result = extract_placeholders(text)
        assert "NOT_A_PLACEHOLDER" in result


class TestNaverSkeleton:
    """Tests specific to WF3 Naver skeleton transformation."""

    NAVER_SNIPPET = """\
### FSSF 분류 요약

| FSSF 유형 | 신호 수 | 비율 |
|-----------|---------|------|
| Weak Signal (약신호) | {{FSSF_WEAK_SIGNAL_COUNT}} | {{FSSF_WEAK_SIGNAL_PCT}} |
| Emerging Issue (부상 이슈) | {{FSSF_EMERGING_ISSUE_COUNT}} | {{FSSF_EMERGING_ISSUE_PCT}} |

### Three Horizons 분포

| 시간 지평 | 신호 수 | 비율 | 설명 |
|-----------|---------|------|------|
| H1 (0-2년) | {{H1_COUNT}} | {{H1_PCT}} | 현재 체제 내 변화 |
| H2 (2-7년) | {{H2_COUNT}} | {{H2_PCT}} | 전환기 신호 |

### 우선순위 1: {{SIGNAL_1_TITLE}}

- **신뢰도**: {{SIGNAL_1_PSST}}
- **FSSF 유형**: {{SIGNAL_1_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_1_HORIZON}}
- **불확실성**: {{SIGNAL_1_UNCERTAINTY}}
"""

    def test_fssf_table_translated(self):
        en, report = mirror_skeleton(self.NAVER_SNIPPET)
        assert report["placeholder_integrity"] is True
        assert "### FSSF Classification Summary" in en
        assert "| FSSF Type | Signal Count | Ratio |" in en
        assert "| Weak Signal |" in en
        assert "(약신호)" not in en
        assert "(부상 이슈)" not in en

    def test_three_horizons_translated(self):
        en, _ = mirror_skeleton(self.NAVER_SNIPPET)
        assert "### Three Horizons Distribution" in en
        assert "(0-2 years)" in en
        assert "(2-7 years)" in en
        assert "Changes within current regime" in en
        assert "Transitional signals" in en

    def test_naver_bullet_labels(self):
        en, _ = mirror_skeleton(self.NAVER_SNIPPET)
        assert "**FSSF Type**:" in en
        assert "**Time Horizon**:" in en
        assert "**Uncertainty**:" in en


class TestIntegratedSkeleton:
    """Tests specific to integrated skeleton transformation."""

    INTEGRATED_SNIPPET = """\
### 통합 우선순위 1: {{INT_SIGNAL_1_TAG}} {{INT_SIGNAL_1_TITLE}}

- **원본 워크플로우**: {{INT_SIGNAL_1_ORIGIN}}

### 통합 우선순위 2: {{INT_SIGNAL_2_TAG}} {{INT_SIGNAL_2_TITLE}}

#### 상호 강화 신호 (Reinforced Signals)

| 항목 | WF1 (일반) | WF2 (arXiv) | WF3 (네이버) | 통합 |
| 소스 수 | {{WF1_SOURCE_COUNT}} | 1 (arXiv) | 1 (NaverNews) | {{TOTAL_SOURCE_COUNT}} |
"""

    def test_integrated_priority_headers(self):
        en, report = mirror_skeleton(self.INTEGRATED_SNIPPET)
        assert report["placeholder_integrity"] is True
        assert "### Integrated Priority 1:" in en
        assert "### Integrated Priority 2:" in en
        assert "통합 우선순위" not in en

    def test_integrated_labels(self):
        en, _ = mirror_skeleton(self.INTEGRATED_SNIPPET)
        assert "**Origin Workflow**:" in en
        assert "원본 워크플로우" not in en

    def test_integrated_sub_subsections(self):
        en, _ = mirror_skeleton(self.INTEGRATED_SNIPPET)
        assert "#### Reinforced Signals" in en
        assert "상호 강화 신호" not in en

    def test_integrated_table_headers(self):
        en, _ = mirror_skeleton(self.INTEGRATED_SNIPPET)
        assert "| Item | WF1 (General) | WF2 (arXiv) | WF3 (Naver) | Integrated |" in en
        assert "| Source Count |" in en


class TestWeeklySkeleton:
    """Tests specific to weekly skeleton transformation."""

    WEEKLY_SNIPPET = """\
### 금주의 3대 핵심 추세

1. **{{TREND_1_TITLE}}** ({{TREND_1_TIS_GRADE}})
   - 추세 강도(TIS): {{TREND_1_TIS_SCORE}}
   - 전략적 시사점: {{TREND_1_IMPLICATION}}

### 2.2 상승 추세 (Accelerating)

### 3.1 수렴 클러스터 (Converging Clusters)

> 주간 활성 스레드: {{WEEKLY_EVOLUTION_TOTAL_THREADS}}개 | 신규: {{WEEKLY_EVOLUTION_NEW_THREADS}}개 | 소멸: {{WEEKLY_EVOLUTION_FADED_THREADS}}개

### 5.3 장기 관찰 필요 (18개월+)

### 8.1 주간 스캐닝 품질 지표

| 주간 ID | {{WEEK_ID}} |
| 분석 기간 | {{ANALYSIS_START_DATE}} ~ {{ANALYSIS_END_DATE}} |
"""

    def test_weekly_headers(self):
        en, report = mirror_skeleton(self.WEEKLY_SNIPPET)
        assert report["placeholder_integrity"] is True
        assert "### This Week's Top 3 Key Trends" in en
        assert "### 2.2 Accelerating Trends" in en
        assert "### 3.1 Converging Clusters" in en
        assert "### 5.3 Long-term Observation (18+ months)" in en
        assert "### 8.1 Weekly Scanning Quality Metrics" in en

    def test_weekly_labels(self):
        en, _ = mirror_skeleton(self.WEEKLY_SNIPPET)
        assert "- Trend Intensity Score (TIS):" in en
        assert "- Strategic Implications:" in en

    def test_weekly_evolution_blockquote(self):
        en, _ = mirror_skeleton(self.WEEKLY_SNIPPET)
        assert "Weekly active threads:" in en
        assert "| New:" in en
        assert "| Faded:" in en
        assert "}}개" not in en

    def test_weekly_table_cells(self):
        en, _ = mirror_skeleton(self.WEEKLY_SNIPPET)
        assert "| Week ID |" in en
        assert "| Analysis Period |" in en


class TestRealSkeletonFiles:
    """Integration tests against actual skeleton files (if present)."""

    @pytest.mark.skipif(
        not (REFERENCES_DIR / "report-skeleton.md").exists(),
        reason="Skeleton files not found",
    )
    def test_standard_skeleton_full(self):
        ko = (REFERENCES_DIR / "report-skeleton.md").read_text(encoding="utf-8")
        en, report = mirror_skeleton(ko)
        assert report["status"] == "SUCCESS"
        assert report["placeholders_before"] == report["placeholders_after"]
        assert "## 1. Executive Summary" in en
        assert "**Classification**:" in en

    @pytest.mark.skipif(
        not (REFERENCES_DIR / "naver-report-skeleton.md").exists(),
        reason="Skeleton files not found",
    )
    def test_naver_skeleton_full(self):
        ko = (REFERENCES_DIR / "naver-report-skeleton.md").read_text(encoding="utf-8")
        en, report = mirror_skeleton(ko)
        assert report["status"] == "SUCCESS"
        assert "### FSSF Classification Summary" in en
        assert "### 4.5 Tipping Point Alerts" in en

    @pytest.mark.skipif(
        not (REFERENCES_DIR / "integrated-report-skeleton.md").exists(),
        reason="Skeleton files not found",
    )
    def test_integrated_skeleton_full(self):
        ko = (REFERENCES_DIR / "integrated-report-skeleton.md").read_text(encoding="utf-8")
        en, report = mirror_skeleton(ko)
        assert report["status"] == "SUCCESS"
        assert "### Integrated Priority 1:" in en
        assert "#### Reinforced Signals" in en

    @pytest.mark.skipif(
        not (REFERENCES_DIR / "weekly-report-skeleton.md").exists(),
        reason="Skeleton files not found",
    )
    def test_weekly_skeleton_full(self):
        ko = (REFERENCES_DIR / "weekly-report-skeleton.md").read_text(encoding="utf-8")
        en, report = mirror_skeleton(ko)
        assert report["status"] == "SUCCESS"
        assert "## 8. System Performance Review" in en
        assert "### 9.4 Execution Summary" in en
