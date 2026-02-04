"""
Unit tests for validate_report.py

Tests validation logic against:
- Synthetic "good" reports (should PASS)
- Synthetic "bad" reports mimicking 2026-02-02 failures (should FAIL)
- Real report files when available (conditional)
"""

import json
import os
import sys
import textwrap
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "scripts"))
from validate_report import (
    ValidationReport,
    validate_report,
    _count_words,
    _count_signal_blocks,
    _check_signal_fields,
    _extract_section,
    _count_field_occurrences,
)


# ---------------------------------------------------------------------------
# Fixtures: Generate synthetic reports
# ---------------------------------------------------------------------------

def _make_signal_block(n: int, full: bool = True) -> str:
    """Generate a single signal block with 9 fields (or partial if full=False)."""
    block = f"### 우선순위 {n}: 테스트 신호 제목 {n}번\n\n"
    block += f"- **신뢰도**: pSST 미산출 (우선순위 점수 기반: {8.0 - n * 0.1:.1f}/10.0)\n\n"
    block += f"1. **분류**: 기술 (T) — 테스트 카테고리\n"
    block += f"2. **출처**: TestSource, 2026-02-01, ID: test-{n:03d}\n"
    block += f"3. **핵심 사실**: 이것은 테스트 신호 {n}번의 핵심 사실입니다. 중요한 발견 내용을 기술합니다.\n"
    block += f"4. **정량 지표**:\n   - 영향도(Impact): 8.0/10\n   - 발생확률(Probability): 7.0/10\n"
    block += f"5. **영향도**: ⭐⭐⭐⭐ ({8.0 - n * 0.1:.1f}/10.0) — 높음\n"
    if full:
        block += f"6. **상세 설명**: 이것은 상세 설명입니다. 테스트 신호 {n}번에 대한 자세한 분석을 포함하고 있습니다. 여러 문장으로 구성된 깊이 있는 분석을 제공합니다.\n"
        block += f"7. **추론**: 의사결정자를 위한 전략적 해석입니다. 이 신호가 미래에 어떤 영향을 미칠 수 있는지 분석합니다.\n"
        block += f"8. **이해관계자**: 정부기관, 기업A, 기업B, 국제기구, 학계\n"
        block += f"9. **모니터링 지표**:\n   - 관련 특허 출원 건수\n   - 투자 동향 변화\n"
    block += "\n---\n\n"
    return block


def _make_good_report() -> str:
    """Create a synthetic report that should pass all 14 checks."""
    sections = []

    # Header
    sections.append("# 일일 환경 스캐닝 보고서\n\n**날짜**: 2026년 2월 1일\n\n---\n\n")

    # Section 1
    sections.append("## 1. 경영진 요약\n\n")
    sections.append("### 오늘의 핵심 발견 (Top 3 신호)\n\n")
    for i in range(1, 4):
        sections.append(f"{i}. **테스트 신호 {i}** (기술 영역)\n   - 중요도: ⭐⭐⭐⭐⭐\n   - 핵심 내용: 테스트 요약 {i}\n   - 전략적 시사점: 전략적 의미 {i}\n\n")
    sections.append("### 주요 변화 요약\n- 발견된 신규 신호: 100개\n- 우선순위 상위 신호: 15개\n- 주요 영향 도메인: 기술(40%), 경제(30%), 정치(20%), 사회(10%)\n\n---\n\n")

    # Section 2
    sections.append("## 2. 신규 탐지 신호\n\n> 통합 우선순위 기준 분석 결과입니다.\n\n---\n\n")
    for i in range(1, 16):
        sections.append(_make_signal_block(i, full=(i <= 10)))

    # Section 3
    sections.append("## 3. 기존 신호 업데이트\n\n")
    sections.append("### 3.1 강화 추세 (Strengthening)\n\n")
    sections.append("- **SIG-001**: 양자 컴퓨팅 기술 발전\n  - 변화: emerging → developing\n  - 이유: 추가 출처 확인, 점수 상승\n\n")
    sections.append("### 3.2 약화 추세 (Weakening)\n\n")
    sections.append("- **SIG-042**: 블록체인 투표 시스템\n  - 변화: developing → stagnating\n  - 이유: 관련 뉴스 감소\n\n")
    sections.append("### 3.3 신호 상태 요약\n\n- 강화 추세 신호: 5개\n- 약화 추세 신호: 3개\n- 상태 변화 없음: 42개\n\n---\n\n")

    # Section 4
    sections.append("## 4. 패턴 및 연결고리\n\n")
    sections.append("### 4.1 신호 간 교차 영향\n\n")
    sections.append("- **양자 컴퓨팅 발전** ↔ **반도체 공급망 변화**: 양자 기술이 기존 반도체 수요 구조를 변화시킬 수 있음 (+3)\n")
    sections.append("- **AI 노동 대체** ↔ **교육 시스템 개편**: 자동화 가속이 교육 재설계 압력을 증가시킴 (+4)\n")
    sections.append("- **기후 정책 변화** ↔ **에너지 전환 가속**: 미국 파리협정 탈퇴가 EU 기후 리더십을 강화함 (+3)\n")
    sections.append("- **디지털 화폐** ↔ **금융 규제**: 중앙은행 디지털 화폐 도입이 규제 프레임워크 변화를 촉진함 (+2)\n\n")
    sections.append("### 4.2 떠오르는 테마\n\n")
    sections.append("1. **기술 주권 경쟁**\n   - 관련 신호: 25개\n   - STEEPs 교차: T, P, E\n   - 의미: 반도체, AI, 에너지 분야에서 국가 간 기술 자립 경쟁 심화\n\n")
    sections.append("2. **노동시장 구조 전환**\n   - 관련 신호: 18개\n   - STEEPs 교차: S, T, E\n   - 의미: AI 자동화로 인한 일자리 변동이 사회 안전망 재설계를 요구\n\n---\n\n")

    # Section 5
    sections.append("## 5. 전략적 시사점\n\n")
    sections.append("### 5.1 즉시 조치 필요 (0-6개월)\n\n")
    sections.append("1. **광학 컴퓨팅 기술 동향 모니터링 체계 구축**\n   - 근거 신호: 우선순위 1번 (광학 컴퓨팅)\n   - 이유: 기술 성숙도가 급속히 향상 중\n   - 권고: 전담 모니터링 팀 구성\n\n")
    sections.append("2. **AI 인력 재교육 프로그램 기획**\n   - 근거 신호: 우선순위 2번 (AI 노동 대체)\n   - 이유: 화이트칼라 직종 영향 임박\n   - 권고: 사내 재교육 예산 확보\n\n")
    sections.append("### 5.2 중기 모니터링 (6-18개월)\n\n")
    sections.append("1. **기후 정책 지형 변화 추적**\n   - 근거 신호: 우선순위 3번 (파리기후협정)\n   - 관찰 지표: CBAM 시행 일정, EU 탄소 가격\n   - 시나리오 분기점: 미국 재가입 여부\n\n")
    sections.append("2. **양자 컴퓨팅 상용화 일정**\n   - 근거 신호: 우선순위 4번\n   - 관찰 지표: 오류 정정 기술 발전 속도\n   - 시나리오 분기점: 100큐빗 오류 정정 달성 시점\n\n")
    sections.append("### 5.3 모니터링 강화 필요 영역\n\n")
    sections.append("- **우주 경제**: 민간 우주 산업 투자 급증에 따른 규제 프레임워크 변화 추적 필요\n")
    sections.append("- **합성 생물학**: 유전자 편집 기술의 산업적 적용 확대 모니터링\n\n---\n\n")

    # Section 6 (optional)
    sections.append("## 6. 플러서블 시나리오\n\n금일 교차영향 복잡도 미달로 시나리오 생성 미발동.\n\n---\n\n")

    # Section 7
    sections.append("## 7. 신뢰도 분석\n\n")
    sections.append("### 7.1 pSST 등급 분포\n\n")
    sections.append("| 등급 | 신호 수 | 비율 |\n|------|---------|------|\n")
    sections.append("| 🟢 A (≥90) | 10 | 10% |\n| 🔵 B (70-89) | 40 | 40% |\n| 🟡 C (50-69) | 30 | 30% |\n| 🔴 D (<50) | 20 | 20% |\n\n")
    sections.append("**평균 pSST**: 68.5/100\n\n---\n\n")

    # Section 8
    sections.append("## 8. 부록\n\n")
    sections.append("### 8.1 전체 신호 목록\n\n| # | 신호 ID | 제목 | 분류 | 영향도 |\n|---|---------|------|------|--------|\n")
    for i in range(1, 21):
        sections.append(f"| {i} | SIG-{i:03d} | 테스트 신호 {i} | T | {8.0 - i * 0.1:.1f} |\n")
    sections.append("\n### 8.2 방법론\n\n자동화된 환경 스캐닝 시스템을 통해 수집, 분류, 분석된 신호입니다.\n")

    return "".join(sections)


def _make_bad_report_02_02_style() -> str:
    """Create a report mimicking 2026-02-02 failures:
    - Missing 상세 설명, 추론, 이해관계자, 모니터링 지표 fields
    - Missing Section 5, 7, 8
    - Wrong Section 3 subsection names
    - Abbreviated Section 4
    """
    sections = []
    sections.append("# 일일 환경 스캐닝 보고서\n\n**날짜**: 2026년 2월 2일\n\n---\n\n")

    # Section 1 (present but minimal)
    sections.append("## 1. 경영진 요약\n\n### 오늘의 핵심 발견\n\n1. 신호 A\n2. 신호 B\n3. 신호 C\n\n### 주요 변화 요약\n- 신규 신호 수: 50개\n\n---\n\n")

    # Section 2 with incomplete signals (only 5 fields)
    sections.append("## 2. 신규 탐지 신호\n\n")
    for i in range(1, 11):
        sections.append(f"### 우선순위 {i}: 결함 신호 {i}\n\n")
        sections.append(f"1. **분류**: 기술 (T)\n")
        sections.append(f"2. **출처**: Source {i}\n")
        sections.append(f"3. **핵심 사실**: 핵심 사실 {i}\n")
        sections.append(f"4. **정량 지표**: 데이터 없음\n")
        sections.append(f"5. **영향도**: ⭐⭐⭐ ({6.0 + i * 0.1:.1f}/10)\n")
        # Missing: 상세 설명, 추론, 이해관계자, 모니터링 지표
        sections.append("\n---\n\n")

    # Section 3 with WRONG subsection names (mimicking 02-02 bug)
    sections.append("## 3. 기존 신호 업데이트\n\n")
    sections.append("### STEEPs별 분석\n\n기존 신호 없음.\n\n---\n\n")

    # Section 4 (abbreviated — only 2 lines)
    sections.append("## 4. 패턴 및 연결고리\n\n기술 분야와 정치 분야의 교차 패턴이 관찰됨.\n\n---\n\n")

    # Section 5 COMPLETELY MISSING
    # Section 7 COMPLETELY MISSING
    # Section 8 COMPLETELY MISSING

    return "".join(sections)


@pytest.fixture
def good_report_file(tmp_path):
    f = tmp_path / "good-report.md"
    f.write_text(_make_good_report(), encoding="utf-8")
    return str(f)


@pytest.fixture
def bad_report_file(tmp_path):
    f = tmp_path / "bad-report.md"
    f.write_text(_make_bad_report_02_02_style(), encoding="utf-8")
    return str(f)


@pytest.fixture
def empty_report_file(tmp_path):
    f = tmp_path / "empty-report.md"
    f.write_text("", encoding="utf-8")
    return str(f)


@pytest.fixture
def skeleton_report_file(tmp_path):
    """A report with unfilled placeholders."""
    f = tmp_path / "skeleton-report.md"
    content = _make_good_report().replace("테스트 신호 제목 1번", "{{SIGNAL_1_TITLE}}")
    f.write_text(content, encoding="utf-8")
    return str(f)


# ---------------------------------------------------------------------------
# Tests: Good Report (should PASS)
# ---------------------------------------------------------------------------

class TestGoodReport:
    def test_overall_pass_or_warn(self, good_report_file):
        """Good report should PASS or at most WARN (no CRITICAL failures).
        Synthetic fixtures may be slightly under word count threshold."""
        result = validate_report(good_report_file)
        assert result.overall_status in ("PASS", "WARN"), result.human_summary()

    def test_all_14_checks_run(self, good_report_file):
        result = validate_report(good_report_file)
        assert len(result.results) == 14

    def test_no_critical_failures(self, good_report_file):
        result = validate_report(good_report_file)
        assert len(result.critical_failures) == 0, \
            f"Unexpected critical failures: {[r.check_id for r in result.critical_failures]}"

    def test_file_exists_check(self, good_report_file):
        result = validate_report(good_report_file)
        file_check = next(r for r in result.results if r.check_id == "FILE-001")
        assert file_check.passed

    def test_section_headers_check(self, good_report_file):
        result = validate_report(good_report_file)
        sec_check = next(r for r in result.results if r.check_id == "SEC-001")
        assert sec_check.passed

    def test_signal_blocks_check(self, good_report_file):
        result = validate_report(good_report_file)
        sig_check = next(r for r in result.results if r.check_id == "SIG-001")
        assert sig_check.passed

    def test_signal_fields_check(self, good_report_file):
        result = validate_report(good_report_file)
        sig_check = next(r for r in result.results if r.check_id == "SIG-002")
        assert sig_check.passed, f"SIG-002 failed: {sig_check.detail}"

    def test_section5_subsections(self, good_report_file):
        result = validate_report(good_report_file)
        s5_check = next(r for r in result.results if r.check_id == "S5-001")
        assert s5_check.passed

    def test_json_output_structure(self, good_report_file):
        result = validate_report(good_report_file)
        d = result.to_dict()
        assert d["overall_status"] in ("PASS", "WARN")
        assert d["summary"]["total_checks"] == 14
        assert d["summary"]["critical_failures"] == 0


# ---------------------------------------------------------------------------
# Tests: Bad Report (should FAIL — mimics 02-02 bugs)
# ---------------------------------------------------------------------------

class TestBadReport0202Style:
    def test_overall_fail(self, bad_report_file):
        result = validate_report(bad_report_file)
        assert result.overall_status == "FAIL", result.human_summary()

    def test_sig002_fails(self, bad_report_file):
        """SIG-002 should fail: signals are missing 4 fields."""
        result = validate_report(bad_report_file)
        sig_check = next(r for r in result.results if r.check_id == "SIG-002")
        assert not sig_check.passed
        # Verify the specific missing fields are detected
        detail = sig_check.detail
        assert "상세 설명" in detail
        assert "추론" in detail
        assert "이해관계자" in detail
        assert "모니터링 지표" in detail

    def test_sec001_fails(self, bad_report_file):
        """SEC-001 should fail: missing sections 5, 7, 8."""
        result = validate_report(bad_report_file)
        sec_check = next(r for r in result.results if r.check_id == "SEC-001")
        assert not sec_check.passed
        assert "5. 전략적 시사점" in sec_check.detail
        assert "7. 신뢰도 분석" in sec_check.detail
        assert "8. 부록" in sec_check.detail

    def test_s5001_fails(self, bad_report_file):
        """S5-001 should fail: Section 5 completely missing."""
        result = validate_report(bad_report_file)
        s5_check = next(r for r in result.results if r.check_id == "S5-001")
        assert not s5_check.passed

    def test_s3001_fails(self, bad_report_file):
        """S3-001 should fail: wrong subsection names in Section 3."""
        result = validate_report(bad_report_file)
        s3_check = next(r for r in result.results if r.check_id == "S3-001")
        assert not s3_check.passed

    def test_s4002_fails(self, bad_report_file):
        """S4-002 should fail: no cross-impact pairs (↔)."""
        result = validate_report(bad_report_file)
        s4_check = next(r for r in result.results if r.check_id == "S4-002")
        assert not s4_check.passed

    def test_critical_failure_count(self, bad_report_file):
        """Should have multiple CRITICAL failures."""
        result = validate_report(bad_report_file)
        assert len(result.critical_failures) >= 3, \
            f"Expected >= 3 CRITICAL failures, got {len(result.critical_failures)}: " \
            f"{[r.check_id for r in result.critical_failures]}"


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_nonexistent_file(self):
        result = validate_report("/nonexistent/report.md")
        assert result.overall_status == "FAIL"
        assert len(result.results) == 14  # All checks present
        file_check = next(r for r in result.results if r.check_id == "FILE-001")
        assert not file_check.passed

    def test_empty_file(self, empty_report_file):
        result = validate_report(empty_report_file)
        assert result.overall_status == "FAIL"
        file_size = next(r for r in result.results if r.check_id == "FILE-002")
        assert not file_size.passed

    def test_skeleton_placeholder_detected(self, skeleton_report_file):
        """SKEL-001 should detect unfilled {{PLACEHOLDER}} tokens."""
        result = validate_report(skeleton_report_file)
        skel_check = next(r for r in result.results if r.check_id == "SKEL-001")
        assert not skel_check.passed
        assert "SIGNAL_1_TITLE" in skel_check.detail


# ---------------------------------------------------------------------------
# Tests: Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_count_words_korean(self):
        text = "이것은 한국어 테스트입니다"
        wc = _count_words(text)
        assert wc > 5

    def test_count_words_mixed(self):
        text = "Hello 세계 world 테스트"
        wc = _count_words(text)
        assert wc >= 4

    def test_count_signal_blocks(self):
        content = "### 우선순위 1: A\n### 우선순위 2: B\n### 우선순위 3: C\n"
        assert _count_signal_blocks(content) == 3

    def test_count_signal_blocks_empty(self):
        assert _count_signal_blocks("no signals here") == 0

    def test_extract_section(self):
        content = "## 1. 경영진 요약\nHello\n## 2. 신규 탐지 신호\nWorld\n"
        section = _extract_section(content, "## 1. 경영진 요약")
        assert "Hello" in section
        assert "World" not in section

    def test_count_field_occurrences(self):
        content = "**분류**: T\n**분류**: S\n**분류**: E\n"
        assert _count_field_occurrences(content, "분류") == 3

    def test_check_signal_fields_complete(self):
        content = _make_signal_block(1, full=True)
        total, complete, missing = _check_signal_fields(content)
        assert total == 1
        assert complete == 1
        assert len(missing) == 0

    def test_check_signal_fields_incomplete(self):
        content = _make_signal_block(1, full=False)
        total, complete, missing = _check_signal_fields(content)
        assert total == 1
        assert complete == 0
        assert len(missing) == 1
        assert "상세 설명" in missing[0]["missing_fields"]


# ---------------------------------------------------------------------------
# Tests: Real reports (conditional — only run if files exist)
# ---------------------------------------------------------------------------

REPORT_DIR = Path(__file__).parent.parent.parent / "env-scanning" / "reports" / "daily"


@pytest.mark.skipif(
    not (REPORT_DIR / "environmental-scan-2026-02-01.md").exists(),
    reason="Real 02-01 report not available",
)
class TestRealReport0201:
    def test_0201_passes_validation(self):
        result = validate_report(str(REPORT_DIR / "environmental-scan-2026-02-01.md"))
        # The 02-01 report is known good — should pass or at most WARN
        assert result.overall_status in ("PASS", "WARN"), result.human_summary()

    def test_0201_no_critical_failures(self):
        result = validate_report(str(REPORT_DIR / "environmental-scan-2026-02-01.md"))
        assert len(result.critical_failures) == 0, \
            f"02-01 report CRITICAL failures: {[r.check_id + ': ' + r.detail for r in result.critical_failures]}"


@pytest.mark.skipif(
    not (REPORT_DIR / "environmental-scan-2026-02-02.md").exists(),
    reason="Real 02-02 report not available",
)
class TestRealReport0202:
    """
    02-02 report was regenerated with 4-layer defense (2026-02-02).
    It should now PASS validation, just like 02-01.
    The original defective pattern is covered by TestBadReport0202Style (synthetic).
    """

    def test_0202_passes_validation(self):
        result = validate_report(str(REPORT_DIR / "environmental-scan-2026-02-02.md"))
        assert result.overall_status in ("PASS", "WARN"), \
            f"Expected 02-02 report (regenerated) to PASS but got {result.overall_status}\n{result.human_summary()}"

    def test_0202_no_critical_failures(self):
        result = validate_report(str(REPORT_DIR / "environmental-scan-2026-02-02.md"))
        assert len(result.critical_failures) == 0, \
            f"02-02 report CRITICAL failures: {[r.check_id + ': ' + r.detail for r in result.critical_failures]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
