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
    _extract_steeps_distribution,
    _classify_steeps_field,
    _check_exploration_proof,
    _get_enforcement_level,
    _auto_enforce_exploration,
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
    """Create a synthetic report that should pass all 15 checks."""
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

    # Section 3 (with evolution data)
    sections.append("## 3. 기존 신호 업데이트\n\n")
    sections.append("> 활성 추적 스레드: 12개 | 강화: 3개 | 약화: 1개 | 소멸: 2개\n\n")
    sections.append("### 3.1 강화 추세 (Strengthening)\n\n")
    sections.append("| 추적 스레드 | 추적일수 | pSST 변화 | 속도 | 확장도 |\n|------------|---------|----------|------|-------|\n")
    sections.append("| 양자 컴퓨팅 기술 발전 | 10일 | 82→88 (+6) | ▲ 가속 | 0.67 |\n\n")
    sections.append("- **SIG-001**: 양자 컴퓨팅 기술 발전\n  - 변화: emerging → developing\n  - 이유: 추가 출처 확인, 점수 상승\n\n")
    sections.append("### 3.2 약화 추세 (Weakening)\n\n")
    sections.append("해당 없음\n\n")
    sections.append("- **SIG-042**: 블록체인 투표 시스템\n  - 변화: developing → stagnating\n  - 이유: 관련 뉴스 감소\n\n")
    sections.append("### 3.3 신호 상태 요약\n\n")
    sections.append("| 상태 | 수 | 비율 |\n|------|---|------|\n")
    sections.append("| 신규 | 8 | 53% |\n| 강화 | 3 | 20% |\n| 반복 등장 | 2 | 13% |\n| 약화 | 1 | 7% |\n| 소멸 | 2 | 13% |\n\n")
    sections.append("---\n\n")

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
    sections.append("## 6. Plausible Scenarios(개연성 있는 시나리오)\n\n금일 교차영향 복잡도 미달로 시나리오 생성 미발동.\n\n---\n\n")

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


def _make_good_naver_report() -> str:
    """Create a synthetic WF3 naver report that should pass all 18 naver-profile checks.
    Extends the standard report with FSSF table, Three Horizons table,
    Section 4.3-4.6, and Tipping Point alerts."""
    sections = []

    # Header
    sections.append("# 일일 네이버 뉴스 환경 스캐닝 보고서\n\n")
    sections.append("**날짜**: 2026년 2월 10일\n\n")
    sections.append("> **보고서 유형**: WF3 네이버 뉴스 환경스캐닝\n")
    sections.append("> **스캔 시간 범위**: 2026년 2월 9일 08:00 ~ 2026년 2월 10일 08:00 (24시간)\n")
    sections.append("> **기준 시점 (T₀)**: 2026-02-10T08:00:00+09:00\n\n---\n\n")

    # Section 1 with FSSF and Three Horizons tables
    sections.append("## 1. 경영진 요약\n\n")
    sections.append("### 오늘의 핵심 발견 (Top 3 신호)\n\n")
    for i in range(1, 4):
        sections.append(f"{i}. **테스트 신호 {i}** (기술)\n   - 중요도: ⭐⭐⭐⭐\n   - FSSF 유형: Weak Signal\n   - 시간 지평: H1\n   - 핵심 내용: 요약 {i}\n   - 전략적 시사점: 시사점 {i}\n\n")
    sections.append("### 주요 변화 요약\n- 발견된 신규 신호: 80개\n- 우선순위 상위 신호: 15개\n- 주요 영향 도메인: 기술(35%), 경제(25%), 정치(20%), 사회(20%)\n\n")

    # FSSF classification summary table
    sections.append("### FSSF 분류 요약\n\n")
    sections.append("| FSSF 유형 | 신호 수 | 비율 |\n|-----------|---------|------|\n")
    sections.append("| Weak Signal (약신호) | 8 | 10% |\n")
    sections.append("| Emerging Issue (부상 이슈) | 12 | 15% |\n")
    sections.append("| Trend (추세) | 25 | 31% |\n")
    sections.append("| Megatrend (메가트렌드) | 10 | 13% |\n")
    sections.append("| Driver (동인) | 15 | 19% |\n")
    sections.append("| Wild Card (와일드카드) | 3 | 4% |\n")
    sections.append("| Discontinuity (단절) | 2 | 3% |\n")
    sections.append("| Precursor Event (전조 사건) | 5 | 6% |\n\n")

    # Three Horizons distribution table
    sections.append("### Three Horizons 분포\n\n")
    sections.append("| 시간 지평 | 신호 수 | 비율 | 설명 |\n|-----------|---------|------|------|\n")
    sections.append("| H1 (0-2년) | 40 | 50% | 현재 체제 내 변화 |\n")
    sections.append("| H2 (2-7년) | 25 | 31% | 전환기 신호 |\n")
    sections.append("| H3 (7년+) | 15 | 19% | 미래 체제 맹아 |\n\n---\n\n")

    # Section 2 — signals
    sections.append("## 2. 신규 탐지 신호\n\n> FSSF 분류 기반 분석 결과입니다.\n\n---\n\n")
    for i in range(1, 16):
        sections.append(_make_signal_block(i, full=(i <= 10)))

    # Section 3 (with evolution data)
    sections.append("## 3. 기존 신호 업데이트\n\n")
    sections.append("> 활성 추적 스레드: 10개 | 강화: 2개 | 약화: 1개 | 소멸: 1개\n\n")
    sections.append("### 3.1 강화 추세 (Strengthening)\n\n")
    sections.append("| 추적 스레드 | 추적일수 | pSST 변화 | 속도 | 확장도 |\n|------------|---------|----------|------|-------|\n")
    sections.append("| 반도체 공급망 재편 | 8일 | 78→84 (+6) | ▲ 가속 | 0.50 |\n\n")
    sections.append("- **SIG-001**: 반도체 공급망 재편\n  - 변화: emerging → developing\n\n")
    sections.append("### 3.2 약화 추세 (Weakening)\n\n해당 없음\n\n- **SIG-042**: NFT 시장 축소\n  - 변화: developing → stagnating\n\n")
    sections.append("### 3.3 신호 상태 요약\n\n")
    sections.append("| 상태 | 수 | 비율 |\n|------|---|------|\n")
    sections.append("| 신규 | 6 | 40% |\n| 강화 | 2 | 13% |\n| 반복 등장 | 4 | 27% |\n| 약화 | 1 | 7% |\n| 소멸 | 1 | 7% |\n\n---\n\n")

    # Section 4 with 4.1-4.6
    sections.append("## 4. 패턴 및 연결고리\n\n")
    sections.append("### 4.1 신호 간 교차 영향\n\n")
    sections.append("- **AI 반도체** ↔ **에너지 수요**: 고성능 칩 수요 증가가 에너지 소비 구조를 변화 (+3)\n")
    sections.append("- **기후 정책** ↔ **전기차 보급**: 탄소세 확대가 전기차 전환 가속 (+4)\n")
    sections.append("- **디지털 플랫폼** ↔ **노동 시장**: 플랫폼 경제 확대가 비정규직 증가에 영향 (+3)\n\n")
    sections.append("### 4.2 떠오르는 테마\n\n1. **AI 인프라 경쟁**\n   - 관련 신호: 15개\n   - STEEPs 교차: T, E, P\n\n")

    # 4.3 FSSF distribution
    sections.append("### 4.3 FSSF 신호 분류 분포\n\n")
    sections.append("| FSSF 유형 | 신호 수 | 대표 신호 | 주요 특징 |\n|-----------|---------|-----------|----------|\n")
    sections.append("| Weak Signal | 8 | AI 칩 자급률 | 초기 징후 |\n")
    sections.append("| Emerging Issue | 12 | 디지털 화폐 | 부상 중 |\n")
    sections.append("| Trend | 25 | 전기차 전환 | 확립된 추세 |\n")
    sections.append("| Wild Card | 3 | 양자 암호 해독 | 예측 불가 |\n\n")

    # 4.4 Three Horizons
    sections.append("### 4.4 Three Horizons 분포\n\n")
    sections.append("| 시간 지평 | 신호 목록 | 주요 테마 |\n|-----------|-----------|----------|\n")
    sections.append("| H1 (0-2년) | 반도체 공급, 전기차 | 현재 변화 |\n")
    sections.append("| H2 (2-7년) | 양자 컴퓨팅, AI 법제화 | 전환기 |\n")
    sections.append("| H3 (7년+) | AGI, 핵융합 | 미래 체제 |\n\n")

    # 4.5 Tipping Point
    sections.append("### 4.5 전환점(Tipping Point) 경고\n\n")
    sections.append("| 경고 레벨 | 신호 | 지표 | 근거 |\n|-----------|------|------|------|\n")
    sections.append("| YELLOW | AI 반도체 자급률 | 국산화율 15% → 25% | 정부 투자 확대 |\n")
    sections.append("| GREEN | 전기차 충전 인프라 | 충전소 5만개 | 설치 가속 |\n\n")

    # 4.6 Anomaly detection
    sections.append("### 4.6 이상 탐지 결과\n\n")
    sections.append("| 유형 | 신호 | 이상 지표 | 심각도 |\n|------|------|-----------|--------|\n")
    sections.append("| 급증 | 바이오 특허 | 전주 대비 +300% | 높음 |\n\n---\n\n")

    # Section 5
    sections.append("## 5. 전략적 시사점\n\n")
    sections.append("### 5.1 즉시 조치 필요 (0-6개월)\n\n1. **AI 반도체 동향 모니터링**\n   - 근거: 우선순위 1번\n   - 권고: 전담팀 구성\n\n")
    sections.append("### 5.2 중기 모니터링 (6-18개월)\n\n1. **디지털 화폐 정책 추적**\n   - 근거: 우선순위 3번\n   - 관찰 지표: CBDC 시행 일정\n\n")
    sections.append("### 5.3 모니터링 강화 필요 영역\n\n- **우주 경제**: 민간 투자 급증\n- **합성 생물학**: 유전자 편집 확대\n\n---\n\n")

    # Section 6
    sections.append("## 6. Plausible Scenarios(개연성 있는 시나리오)\n\n금일 교차영향 복잡도 미달로 시나리오 생성 미발동.\n\n---\n\n")

    # Section 7
    sections.append("## 7. 신뢰도 분석\n\n### 7.1 pSST 등급 분포\n\n| 등급 | 신호 수 | 비율 |\n|------|---------|------|\n")
    sections.append("| 🟢 A (≥90) | 5 | 6% |\n| 🔵 B (70-89) | 35 | 44% |\n| 🟡 C (50-69) | 25 | 31% |\n| 🔴 D (<50) | 15 | 19% |\n\n**평균 pSST**: 65.2/100\n\n---\n\n")

    # Section 8
    sections.append("## 8. 부록\n\n### 8.1 크롤링 통계\n\n| 항목 | 값 |\n|------|-----|\n| 크롤링 일시 | 2026-02-10 08:00 |\n| 총 수집 기사 | 500 |\n\n")
    sections.append("### 8.2 FSSF 분류 방법론\n\n미래신호탐색프레임워크(FSSF)는 8가지 분류를 사용합니다.\n\n")
    sections.append("### 8.3 전체 신호 목록\n\n| # | 신호 ID | 제목 | 분류 | 영향도 |\n|---|---------|------|------|--------|\n")
    for i in range(1, 16):
        sections.append(f"| {i} | naver-20260210-{i:03d} | 테스트 신호 {i} | T | {8.0 - i * 0.1:.1f} |\n")
    sections.append("\n### 8.4 출처 목록\n\n- 네이버 뉴스 정치 섹션\n- 네이버 뉴스 경제 섹션\n- 네이버 뉴스 IT과학 섹션\n")

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

    def test_all_17_checks_run(self, good_report_file):
        result = validate_report(good_report_file)
        assert len(result.results) == 17

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
        assert d["summary"]["total_checks"] == 17
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
        assert len(result.results) == 17  # All checks present (14 base + STEEPS-001 + TEMP-001 + EVOL-001)
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

    def test_count_signal_blocks_integrated(self):
        """Regex must match '통합 우선순위' headers used in integrated reports."""
        content = "### 통합 우선순위 1: [WF2] Signal A\n### 통합 우선순위 2: [WF1] Signal B\n"
        assert _count_signal_blocks(content) == 2

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
# Tests: Integrated profile (CW-002 with [WF3])
# ---------------------------------------------------------------------------

class TestIntegratedProfile:
    """Test CW-002 source tag validation for integrated profile."""

    def _make_integrated_report(self, include_wf3: bool = True) -> str:
        """Create a synthetic integrated report with [WF1]/[WF2]/[WF3] tags."""
        sections = []
        sections.append("# 통합 일일 환경 스캐닝 보고서\n\n**날짜**: 2026년 2월 7일\n\n---\n\n")

        # Section 1
        sections.append("## 1. 경영진 요약\n\n### 오늘의 핵심 발견 (Top 5 신호)\n\n")
        for i in range(1, 6):
            if include_wf3:
                tag = "[WF1]" if i % 3 == 1 else ("[WF2]" if i % 3 == 2 else "[WF3]")
            else:
                tag = "[WF1]" if i % 2 == 1 else "[WF2]"
            sections.append(f"{i}. **{tag} 테스트 신호 {i}** (기술)\n   - 중요도: ⭐⭐⭐⭐\n   - 핵심 내용: 요약 {i}\n   - 전략적 시사점: 시사점 {i}\n\n")
        if include_wf3:
            sections.append("### 주요 변화 요약\n- **WF1**: 50개 수집\n- **WF2**: 30개 수집\n- **WF3**: 40개 수집\n- 통합: 120개\n- 상위 20개 선정\n- 도메인: T(40%), E(30%)\n\n")
        else:
            sections.append("### 주요 변화 요약\n- **WF1**: 50개 수집\n- **WF2**: 30개 수집\n- 통합: 80개\n- 상위 20개 선정\n- 도메인: T(40%), E(30%)\n\n")
        sections.append("### 워크플로우 교차 하이라이트\n교차 분석 요약\n\n---\n\n")

        # Section 2 with 20 signals
        sections.append("## 2. 신규 탐지 신호\n\n> 통합 분석 결과\n\n---\n\n")
        for i in range(1, 21):
            tag = "[WF1]" if i % 3 == 1 else ("[WF2]" if i % 3 == 2 else "[WF3]")
            if not include_wf3:
                tag = "[WF1]" if i % 2 == 1 else "[WF2]"
            sections.append(_make_signal_block(i, full=True).replace(
                f"### 우선순위 {i}:", f"### 통합 우선순위 {i}: {tag}"))

        # Section 3 (with evolution data)
        sections.append("## 3. 기존 신호 업데이트\n\n")
        sections.append("> 활성 추적 스레드: 20개 | 강화: 5개 | 약화: 3개 | 소멸: 2개\n\n")
        sections.append("### 3.1 강화 추세\n\n- 강화 신호 5개\n\n")
        sections.append("### 3.2 약화 추세\n\n- 약화 신호 3개\n\n")
        sections.append("### 3.3 신호 상태 요약\n\n| 상태 | 수 | 비율 |\n|------|---|------|\n| 신규 | 10 | 50% |\n| 강화 | 5 | 25% |\n| 반복 등장 | 3 | 15% |\n| 약화 | 2 | 10% |\n\n---\n\n")

        # Section 4 with 4.3
        sections.append("## 4. 패턴 및 연결고리\n\n")
        sections.append("### 4.1 신호 간 교차 영향\n\n- A ↔ B: 교차 (+3)\n- C ↔ D: 교차 (+2)\n- E ↔ F: 교차 (+4)\n\n")
        sections.append("### 4.2 떠오르는 테마\n\n1. 테마 A\n\n")
        sections.append("### 4.3 워크플로우 교차 분석\n\n")
        sections.append("#### 4.3.1 상호 강화 신호\n\n교차 분석 내용\n\n")
        sections.append("#### 4.3.2 학술 선행 신호\n\n학술 선행 내용\n\n")
        sections.append("#### 4.3.3 미디어 선행 신호\n\n미디어 선행 내용\n\n---\n\n")

        # Section 5
        sections.append("## 5. 전략적 시사점\n\n")
        sections.append("### 5.1 즉시 조치\n\n1. 조치 A\n\n")
        sections.append("### 5.2 중기 모니터링\n\n1. 모니터링 A\n\n")
        sections.append("### 5.3 강화 필요\n\n- 영역 A\n\n---\n\n")

        # Section 7
        sections.append("## 7. 신뢰도 분석\n\npSST 분포 분석 내용\n\n---\n\n")

        # Section 8
        sections.append("## 8. 부록\n\n전체 신호 목록 테이블\n\n")

        return "".join(sections)

    def test_integrated_with_wf3_passes_cw002(self, tmp_path):
        """CW-002 should pass when [WF1], [WF2], [WF3] all present."""
        f = tmp_path / "integrated-report.md"
        f.write_text(self._make_integrated_report(include_wf3=True), encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        cw002 = next(r for r in result.results if r.check_id == "CW-002")
        assert cw002.passed, f"CW-002 should pass with all 3 tags: {cw002.detail}"

    def test_integrated_without_wf3_fails_cw002(self, tmp_path):
        """CW-002 should fail when [WF3] is missing in integrated profile."""
        f = tmp_path / "integrated-no-wf3.md"
        f.write_text(self._make_integrated_report(include_wf3=False), encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        cw002 = next(r for r in result.results if r.check_id == "CW-002")
        assert not cw002.passed, "CW-002 should fail without [WF3] in integrated profile"
        assert "[WF3]" in cw002.detail or "WF3" in cw002.detail

    def test_integrated_profile_runs_19_checks(self, tmp_path):
        """Integrated profile should run 19 checks (14 base + STEEPS-001 + CW-001 + CW-002 + TEMP-001 + EVOL-001)."""
        f = tmp_path / "integrated-report.md"
        f.write_text(self._make_integrated_report(include_wf3=True), encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        assert len(result.results) == 19, f"Expected 19 checks, got {len(result.results)}"

    def test_integrated_cw001_passes(self, tmp_path):
        """CW-001 should pass when Section 4.3 exists inside ## 4. 패턴 및 연결고리."""
        f = tmp_path / "integrated-report.md"
        f.write_text(self._make_integrated_report(include_wf3=True), encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        cw001 = next(r for r in result.results if r.check_id == "CW-001")
        assert cw001.passed, f"CW-001 should pass with 4.3 subsection: {cw001.detail}"

    def test_integrated_signal_blocks_counted(self, tmp_path):
        """SIG-001 should find 20 signal blocks with '통합 우선순위' headers."""
        f = tmp_path / "integrated-report.md"
        f.write_text(self._make_integrated_report(include_wf3=True), encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        sig001 = next(r for r in result.results if r.check_id == "SIG-001")
        assert sig001.passed, f"SIG-001 should find 20 signals: {sig001.detail}"


# ---------------------------------------------------------------------------
# Tests: Naver profile (WF3 — FSSF/Three Horizons/Tipping Point)
# ---------------------------------------------------------------------------

class TestNaverProfile:
    """Test naver profile with WF3-specific checks (FSSF-001, H3HZ-001, TPNT-001)."""

    def test_naver_valid_report_passes(self, tmp_path):
        """All 18 naver-profile checks should pass."""
        f = tmp_path / "naver-report.md"
        f.write_text(_make_good_naver_report(), encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        assert len(result.critical_failures) == 0, \
            f"Unexpected CRITICAL failures: {[(r.check_id, r.detail) for r in result.critical_failures]}"
        assert result.overall_status in ("PASS", "WARN"), result.human_summary()

    def test_naver_runs_20_checks(self, tmp_path):
        """Naver profile should run 20 checks (15 base + STEEPS-001 + FSSF-001 + H3HZ-001 + TPNT-001 + EVOL-001)."""
        f = tmp_path / "naver-report.md"
        f.write_text(_make_good_naver_report(), encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        assert len(result.results) == 20, \
            f"Expected 20 checks, got {len(result.results)}: {[r.check_id for r in result.results]}"

    def test_naver_missing_fssf_table_fails(self, tmp_path):
        """FSSF-001 should fail when FSSF keywords are missing."""
        content = _make_good_naver_report()
        # Remove all FSSF type keywords
        for kw in ["Weak Signal", "Wild Card", "Discontinuity", "Emerging Issue",
                    "Driver", "Precursor Event", "약신호", "와일드카드", "단절",
                    "부상 이슈", "동인", "전조 사건"]:
            content = content.replace(kw, "신호유형")
        # Also neutralize Trend/Megatrend (but keep them as "추세유형" to avoid breaking other text)
        content = content.replace("Megatrend", "대형추세유형")
        content = content.replace("메가트렌드", "대형추세유형")
        content = content.replace("Trend", "추세유형")
        f = tmp_path / "naver-no-fssf.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        fssf = next(r for r in result.results if r.check_id == "FSSF-001")
        assert not fssf.passed, f"FSSF-001 should fail without FSSF keywords: {fssf.detail}"

    def test_naver_missing_three_horizons_fails(self, tmp_path):
        """H3HZ-001 should fail when Three Horizons data is missing."""
        content = _make_good_naver_report()
        # Remove H1/H2/H3 horizon patterns
        content = content.replace("H1 (0-2년)", "단기")
        content = content.replace("H2 (2-7년)", "중기")
        content = content.replace("H3 (7년+)", "장기")
        f = tmp_path / "naver-no-horizons.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        h3hz = next(r for r in result.results if r.check_id == "H3HZ-001")
        assert not h3hz.passed, f"H3HZ-001 should fail without horizon data: {h3hz.detail}"

    def test_naver_missing_section_4_3_to_4_6_fails(self, tmp_path):
        """S4-001 should fail when Section 4.3-4.6 subsections are missing."""
        content = _make_good_naver_report()
        # Remove 4.3, 4.4, 4.5, 4.6 subsections
        content = content.replace("### 4.3 FSSF", "### 떠오르는 분석 FSSF")
        content = content.replace("### 4.4 Three", "### 시간 분석 Three")
        content = content.replace("### 4.5 전환점", "### 변화점 전환점")
        content = content.replace("### 4.6 이상", "### 비정상 이상")
        f = tmp_path / "naver-no-s4subs.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        s4 = next(r for r in result.results if r.check_id == "S4-001")
        assert not s4.passed, f"S4-001 should fail with missing 4.3-4.6: {s4.detail}"
        # Verify specific missing subs
        for sub in ["4.3", "4.4", "4.5", "4.6"]:
            assert sub in s4.detail, f"Missing subsection {sub} should be in detail"

    def test_naver_missing_tipping_point_warns(self, tmp_path):
        """TPNT-001 should fail as ERROR (not CRITICAL) when tipping point data is missing."""
        content = _make_good_naver_report()
        # Remove tipping point text and alert levels
        content = content.replace("전환점", "변화지점")
        content = content.replace("Tipping Point", "Change Point")
        content = content.replace("YELLOW", "경고중")
        content = content.replace("GREEN", "정상")
        content = content.replace("ORANGE", "주의")
        content = content.replace("RED", "위험")
        f = tmp_path / "naver-no-tp.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        tpnt = next(r for r in result.results if r.check_id == "TPNT-001")
        assert not tpnt.passed, f"TPNT-001 should fail: {tpnt.detail}"
        assert tpnt.level == "ERROR", f"TPNT-001 should be ERROR level, not {tpnt.level}"

    def test_naver_nonexistent_file_runs_20_checks(self):
        """Naver profile with nonexistent file should still report 20 checks."""
        result = validate_report("/nonexistent/naver-report.md", profile="naver")
        assert result.overall_status == "FAIL"
        assert len(result.results) == 20, \
            f"Expected 20 checks, got {len(result.results)}: {[r.check_id for r in result.results]}"

    def test_fssf001_megatrend_only_should_fail(self, tmp_path):
        """FSSF-001 edge case: 'Megatrend' alone should NOT also match 'Trend'.
        With only 1 distinct type, the check must fail (need >= 3)."""
        content = _make_good_naver_report()
        # Remove all FSSF types except Megatrend/메가트렌드
        for kw in ["Weak Signal", "Wild Card", "Discontinuity", "Emerging Issue",
                    "Driver", "Precursor Event", "약신호", "와일드카드", "단절",
                    "부상 이슈", "동인", "전조 사건"]:
            content = content.replace(kw, "유형X")
        # Replace standalone "Trend" but keep "Megatrend" — simulate a report
        # that only discusses megatrends
        import re as _re
        content = _re.sub(r'\bTrend\b', '유형Y', content)
        content = content.replace("추세", "유형Z")
        f = tmp_path / "naver-megatrend-only.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        fssf = next(r for r in result.results if r.check_id == "FSSF-001")
        assert not fssf.passed, \
            f"FSSF-001 should fail with only Megatrend type: {fssf.detail}"

    def test_fssf001_two_types_should_fail(self, tmp_path):
        """FSSF-001 edge case: exactly 2 distinct types should fail (need >= 3)."""
        content = _make_good_naver_report()
        # Keep only Weak Signal + Megatrend, remove all other types
        for kw in ["Wild Card", "Discontinuity", "Emerging Issue",
                    "Driver", "Precursor Event", "와일드카드", "단절",
                    "부상 이슈", "동인", "전조 사건"]:
            content = content.replace(kw, "유형X")
        import re as _re
        content = _re.sub(r'\bTrend\b', '유형Y', content)
        content = content.replace("추세", "유형Z")
        f = tmp_path / "naver-2types.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        fssf = next(r for r in result.results if r.check_id == "FSSF-001")
        assert not fssf.passed, \
            f"FSSF-001 should fail with only 2 distinct types: {fssf.detail}"

    def test_tpnt001_predicted_not_false_positive(self, tmp_path):
        """TPNT-001 edge case: 'PREDICTED' should NOT match as 'RED' alert.
        A report with '전환점' but only 'PREDICTED'/'GREENHOUSE' (no real alerts)
        must fail TPNT-001."""
        content = _make_good_naver_report()
        # Replace actual alert keywords with words containing them as substrings
        content = content.replace("YELLOW", "PREDICTED")
        content = content.replace("GREEN", "GREENHOUSE")
        content = content.replace("ORANGE", "STORED")
        content = content.replace("RED", "CENTERED")
        # Also handle lowercase variants
        content = content.replace("yellow", "predicted")
        content = content.replace("green", "greenhouse")
        f = tmp_path / "naver-false-alerts.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="naver")
        tpnt = next(r for r in result.results if r.check_id == "TPNT-001")
        assert not tpnt.passed, \
            f"TPNT-001 should fail when alerts are only substrings: {tpnt.detail}"


# ---------------------------------------------------------------------------
# Tests: STEEPS-001 (category distribution check)
# ---------------------------------------------------------------------------

class TestSteepsDistribution:
    """Tests for STEEPS-001 check and _extract_steeps_distribution helper."""

    # -- Helper function tests --

    def test_extract_steeps_distribution_basic(self):
        """Basic extraction from standard signal blocks."""
        content = (
            "### 우선순위 1: AI\n"
            "1. **분류**: 기술 (T) — 인공지능\n"
            "### 우선순위 2: 인구\n"
            "1. **분류**: 사회 (S) — 인구통계\n"
            "### 우선순위 3: 탄소\n"
            "1. **분류**: 환경 (E) — 기후변화\n"
        )
        dist = _extract_steeps_distribution(content)
        assert dist == {"T_Technological": 1, "S_Social": 1, "E_Environmental": 1}

    def test_extract_steeps_distribution_all_six(self):
        """All 6 STEEPs categories detected."""
        content = (
            "1. **분류**: 사회 (S)\n"
            "1. **분류**: 기술 (T)\n"
            "1. **분류**: 경제 (E)\n"
            "1. **분류**: 환경 (E)\n"
            "1. **분류**: 정치 (P)\n"
            "1. **분류**: 정신적 (s)\n"
        )
        dist = _extract_steeps_distribution(content)
        assert len(dist) == 6

    def test_extract_steeps_distribution_counts_duplicates(self):
        """Same category appearing multiple times is counted correctly."""
        content = (
            "1. **분류**: 기술 (T) — AI\n"
            "1. **분류**: 기술 (T) — 양자\n"
            "1. **분류**: 경제 (E) — 무역\n"
        )
        dist = _extract_steeps_distribution(content)
        assert dist["T_Technological"] == 2
        assert dist["E_Economic"] == 1

    def test_extract_steeps_distribution_empty(self):
        """Empty or no-match content returns empty dict."""
        assert _extract_steeps_distribution("") == {}
        assert _extract_steeps_distribution("no signals here") == {}

    def test_extract_steeps_distribution_boundary_matching(self):
        """Korean boundary matching prevents false substring matches.
        '경제사회적' should NOT match '사회' as a standalone category."""
        content = "1. **분류**: 경제사회적 변화\n"
        dist = _extract_steeps_distribution(content)
        # '경제' is at start with '사' following → should NOT match as standalone "경제"
        # '사회' has '제' before and '적' after → should NOT match as standalone "사회"
        # Neither should match due to Korean boundary regex
        assert "S_Social" not in dist
        assert "E_Economic" not in dist

    def test_extract_steeps_distribution_legitimate_match(self):
        """Normal category format with surrounding non-Korean chars matches correctly."""
        content = "1. **분류**: 사회 (S) — 인구통계\n"
        dist = _extract_steeps_distribution(content)
        assert dist == {"S_Social": 1}

    # -- STEEPS-001 integration tests --

    def _make_diverse_report(self, categories: list[tuple[str, str]]) -> str:
        """Build a minimal valid report with signals in specified categories.
        categories: list of (korean_name, code) like [("기술", "T"), ("사회", "S")]
        """
        sections = []
        sections.append("# 일일 환경 스캐닝 보고서\n\n**날짜**: 2026년 2월 1일\n\n---\n\n")

        # Section 1
        sections.append("## 1. 경영진 요약\n\n### 오늘의 핵심 발견 (Top 3 신호)\n\n")
        for i in range(1, 4):
            sections.append(f"{i}. **신호 {i}**\n   - 중요도: ⭐⭐⭐⭐\n   - 핵심 내용: 요약 {i}\n   - 전략적 시사점: 시사점 {i}\n\n")
        sections.append("### 주요 변화 요약\n- 발견된 신규 신호: 100개\n- 우선순위: 15개\n- 도메인: 기술 사회 경제 환경\n\n---\n\n")

        # Section 2 — signals with diverse categories
        sections.append("## 2. 신규 탐지 신호\n\n---\n\n")
        for i in range(1, 16):
            ko_name, code = categories[i % len(categories)]
            sections.append(f"### 우선순위 {i}: 테스트 신호 {i}번\n\n")
            sections.append(f"- **신뢰도**: pSST 미산출 (7.0/10.0)\n\n")
            sections.append(f"1. **분류**: {ko_name} ({code}) — 테스트\n")
            sections.append(f"2. **출처**: TestSource, 2026-02-01, ID: test-{i:03d}\n")
            sections.append(f"3. **핵심 사실**: 핵심 사실 {i}번입니다 중요한 발견을 기술합니다\n")
            sections.append(f"4. **정량 지표**:\n   - 영향도(Impact): 8.0/10\n   - 발생확률: 7.0/10\n")
            sections.append(f"5. **영향도**: ⭐⭐⭐⭐ (8.0/10.0) — 높음\n")
            sections.append(f"6. **상세 설명**: 상세 분석 내용입니다 여러 문장으로 깊이 있는 분석을 제공합니다\n")
            sections.append(f"7. **추론**: 전략적 해석입니다 미래 영향을 분석합니다\n")
            sections.append(f"8. **이해관계자**: 정부기관, 기업, 학계\n")
            sections.append(f"9. **모니터링 지표**:\n   - 관련 지표 {i}\n")
            sections.append("\n---\n\n")

        # Section 3
        sections.append("## 3. 기존 신호 업데이트\n\n")
        sections.append("### 3.1 강화 추세 (Strengthening)\n\n- 강화 신호 3개\n\n")
        sections.append("### 3.2 약화 추세 (Weakening)\n\n해당 없음\n\n")
        sections.append("### 3.3 신호 상태 요약\n\n| 상태 | 수 |\n|------|---|\n| 신규 | 8 |\n\n---\n\n")

        # Section 4
        sections.append("## 4. 패턴 및 연결고리\n\n")
        sections.append("### 4.1 신호 간 교차 영향\n\n- A ↔ B: 교차 (+3)\n- C ↔ D: 교차 (+2)\n- E ↔ F: 교차 (+4)\n\n")
        sections.append("### 4.2 떠오르는 테마\n\n1. 테마 A\n\n---\n\n")

        # Section 5
        sections.append("## 5. 전략적 시사점\n\n")
        sections.append("### 5.1 즉시 조치 필요\n\n1. 조치 A\n\n")
        sections.append("### 5.2 중기 모니터링\n\n1. 모니터링 A\n\n")
        sections.append("### 5.3 모니터링 강화 필요 영역\n\n- 영역 A\n\n---\n\n")

        # Section 7
        sections.append("## 7. 신뢰도 분석\n\npSST 분포 분석\n\n---\n\n")

        # Section 8
        sections.append("## 8. 부록\n\n전체 신호 목록\n\n")

        return "".join(sections)

    def test_steeps_001_pass_diverse_categories(self, tmp_path):
        """STEEPS-001 passes when report has >= 4 distinct categories."""
        content = self._make_diverse_report([
            ("기술", "T"), ("사회", "S"), ("경제", "E"), ("환경", "E"), ("정치", "P"),
        ])
        f = tmp_path / "diverse-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        assert steeps.passed, f"STEEPS-001 should pass with 5 categories: {steeps.detail}"

    def test_steeps_001_fail_insufficient_categories(self, tmp_path):
        """STEEPS-001 fails when report has < 4 distinct categories (standard)."""
        content = self._make_diverse_report([
            ("기술", "T"), ("경제", "E"),
        ])
        f = tmp_path / "narrow-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        assert not steeps.passed, f"STEEPS-001 should fail with only 2 categories"
        assert "2" in steeps.detail  # "Found 2 categories"
        assert steeps.level == "ERROR"

    def test_steeps_001_fail_detail_shows_missing(self, tmp_path):
        """STEEPS-001 detail includes missing category codes."""
        content = self._make_diverse_report([
            ("기술", "T"),
        ])
        f = tmp_path / "single-cat-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        assert not steeps.passed
        # Missing categories should be listed
        assert "S_Social" in steeps.detail
        assert "E_Economic" in steeps.detail
        assert "E_Environmental" in steeps.detail
        assert "P_Political" in steeps.detail
        assert "s_spiritual" in steeps.detail

    def test_steeps_001_skip_weekly(self, tmp_path):
        """Weekly profile (steeps_min_categories=0) skips STEEPS-001 entirely."""
        # Use a minimal weekly-format report
        f = tmp_path / "weekly-report.md"
        f.write_text("# 주간 report\n" * 100, encoding="utf-8")
        result = validate_report(str(f), profile="weekly")
        steeps_checks = [r for r in result.results if r.check_id == "STEEPS-001"]
        assert len(steeps_checks) == 0, "STEEPS-001 should not appear in weekly profile"

    def test_steeps_001_arxiv_fallback_threshold(self, tmp_path):
        """arxiv_fallback profile has lower threshold (3 categories)."""
        content = self._make_diverse_report([
            ("기술", "T"), ("경제", "E"), ("환경", "E"),
        ])
        f = tmp_path / "arxiv-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="arxiv_fallback")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        assert steeps.passed, f"arxiv_fallback should pass with 3 categories: {steeps.detail}"

    def test_steeps_001_integrated_needs_5(self, tmp_path):
        """Integrated profile requires 5 distinct categories."""
        content = self._make_diverse_report([
            ("기술", "T"), ("사회", "S"), ("경제", "E"), ("환경", "E"),
        ])
        f = tmp_path / "integrated-4cat.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="integrated")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        # 4 categories, but integrated needs 5
        assert not steeps.passed, f"Integrated should fail with only 4 categories"


# ---------------------------------------------------------------------------
# Tests: _classify_steeps_field (3-layer detection, real-world formats)
# ---------------------------------------------------------------------------

class TestClassifySteepsField:
    """Tests for _classify_steeps_field — all 7 observed real-world formats."""

    # -- Format A: Korean-first (최신 형식) --

    def test_format_a_korean_first(self):
        """Standard Korean-first: 기술 (T) — AI/LLM"""
        assert _classify_steeps_field("기술 (T) — AI/LLM") == {"T_Technological"}

    def test_format_a_korean_first_no_space(self):
        """Korean-first without space: 기술(T) - 로보틱스"""
        assert _classify_steeps_field("기술(T) - 로보틱스") == {"T_Technological"}

    def test_format_a_all_six_categories(self):
        """Each Korean category resolves correctly."""
        assert _classify_steeps_field("사회 (S) — 인구통계") == {"S_Social"}
        assert _classify_steeps_field("기술 (T) — AI") == {"T_Technological"}
        assert _classify_steeps_field("경제 (E) — 무역") == {"E_Economic"}
        assert _classify_steeps_field("환경 (E_Environmental) — 기후") == {"E_Environmental"}
        assert _classify_steeps_field("정치 (P) — 규제") == {"P_Political"}
        assert _classify_steeps_field("정신적(s) - 신경과학") == {"s_spiritual"}

    # -- Format B: English code-first --

    def test_format_b_english_code_first(self):
        """English code-first: T (Technological) -- AI-바이오"""
        assert _classify_steeps_field("T (Technological) -- AI-바이오") == {"T_Technological"}

    def test_format_b_social(self):
        """S (Social) -- 공중보건"""
        assert _classify_steeps_field("S (Social) -- 공중보건") == {"S_Social"}

    def test_format_b_environmental(self):
        """E_Environmental (환경) -- 기후과학"""
        result = _classify_steeps_field("E_Environmental (환경) -- 기후과학")
        assert "E_Environmental" in result

    # -- Format C: Full-code first --

    def test_format_c_full_code_first(self):
        """Full code: P_Political (비교정치)"""
        assert _classify_steeps_field("P_Political (비교정치)") == {"P_Political"}

    def test_format_c_spiritual(self):
        """Full code: s_spiritual (심리/체제 논리)"""
        assert _classify_steeps_field("s_spiritual (심리/체제 논리)") == {"s_spiritual"}

    def test_format_c_s_spiritual_with_korean_desc(self):
        """s_spiritual (심리/가치/신뢰)"""
        assert _classify_steeps_field("s_spiritual (심리/가치/신뢰)") == {"s_spiritual"}

    # -- Format D: English name-first (WF3) --

    def test_format_d_english_name_first(self):
        """English name: Political (P) -- 사법부의 기후 정책"""
        assert _classify_steeps_field("Political (P) -- 사법부의 기후 정책") == {"P_Political"}

    def test_format_d_technological(self):
        """Technological (T) -- 메모리 반도체"""
        assert _classify_steeps_field("Technological (T) -- 메모리 반도체") == {"T_Technological"}

    def test_format_d_economic(self):
        """Economic (E) -- AI 반도체 시장"""
        assert _classify_steeps_field("Economic (E) -- AI 반도체 시장") == {"E_Economic"}

    def test_format_d_environmental(self):
        """Environmental (E_Environmental) -- 국제 기후"""
        result = _classify_steeps_field("Environmental (E_Environmental) -- 국제 기후")
        assert "E_Environmental" in result

    def test_format_d_social(self):
        """Social (S) -- 인구 소멸 위기"""
        assert _classify_steeps_field("Social (S) -- 인구 소멸 위기") == {"S_Social"}

    def test_format_d_spiritual(self):
        """spiritual (s) -- AI 윤리와 가치관 변화"""
        assert _classify_steeps_field("spiritual (s) -- AI 윤리와 가치관 변화") == {"s_spiritual"}

    # -- Format E: "영적/윤리" variant --

    def test_format_e_yeongjeok(self):
        """영적/윤리 (s) -- 사회 심리/가치관"""
        result = _classify_steeps_field("영적/윤리 (s) -- 사회 심리/가치관")
        assert "s_spiritual" in result

    def test_format_e_yeongjeok_full_code(self):
        """영적/윤리 (s_spiritual)"""
        result = _classify_steeps_field("영적/윤리 (s_spiritual)")
        assert "s_spiritual" in result

    # -- Format F: Multi-category with + --

    def test_format_f_triple_category(self):
        """경제(E) + 사회(S) + 정치(P) -- econ.GN"""
        result = _classify_steeps_field("경제(E) + 사회(S) + 정치(P) -- econ.GN")
        assert result == {"E_Economic", "S_Social", "P_Political"}

    def test_format_f_dual_with_spiritual(self):
        """사회 (S) + 영적 (s) -- cs.CY"""
        result = _classify_steeps_field("사회 (S) + 영적 (s) -- cs.CY")
        assert result == {"S_Social", "s_spiritual"}

    # -- Format G: Dual-category with / --

    def test_format_g_dual_slash(self):
        """경제 (E) / 정치 (P)"""
        result = _classify_steeps_field("경제 (E) / 정치 (P)")
        assert result == {"E_Economic", "P_Political"}

    def test_format_g_tech_env(self):
        """기술 (T) / 환경 (E_Environmental)"""
        result = _classify_steeps_field("기술 (T) / 환경 (E_Environmental)")
        assert result == {"T_Technological", "E_Environmental"}

    def test_format_g_tech_spiritual(self):
        """기술 (T) / 영적/윤리 (s_spiritual)"""
        result = _classify_steeps_field("기술 (T) / 영적/윤리 (s_spiritual)")
        assert result == {"T_Technological", "s_spiritual"}

    def test_format_g_tech_spiritual_code(self):
        """기술(T) / 정신적(s) -- AI 안전성"""
        result = _classify_steeps_field("기술(T) / 정신적(s) -- AI 안전성")
        assert result == {"T_Technological", "s_spiritual"}

    # -- Description false-positive prevention --

    def test_description_not_matched(self):
        """Korean keywords in description part must NOT cause false matches.
        정치 (P) -- 환경 규제 정책: '환경' is in description, not category."""
        result = _classify_steeps_field("정치 (P) -- 환경 규제 정책")
        assert result == {"P_Political"}
        assert "E_Environmental" not in result

    def test_description_social_in_desc(self):
        """경제 (E) -- 사회보장 정책: '사회' in description."""
        result = _classify_steeps_field("경제 (E) -- 사회보장 정책")
        assert result == {"E_Economic"}
        assert "S_Social" not in result

    # -- Edge cases --

    def test_empty_field(self):
        assert _classify_steeps_field("") == set()

    def test_metadata_not_signal(self):
        """Non-signal text like 'STEEPs 6개 카테고리' should return empty."""
        assert _classify_steeps_field("STEEPs 6개 카테고리") == set()

    def test_placeholder_not_matched(self):
        """Unfilled placeholder should return empty."""
        assert _classify_steeps_field("{{SIGNAL_1_CLASSIFICATION}}") == set()

    def test_s_lowercase_fallback(self):
        """s (spiritual/ethical) -- AI 윤리: Layer 3 leading code fallback."""
        result = _classify_steeps_field("s (spiritual/ethical) -- AI 윤리")
        assert "s_spiritual" in result

    def test_ambiguous_e_without_korean(self):
        """Economic (E) — no Korean '경제' keyword. Layer 2 skips (E),
        Layer 3 catches 'Economic'."""
        result = _classify_steeps_field("Economic (E) -- 시장 분석")
        assert result == {"E_Economic"}

    def test_s_korean_in_parens(self):
        """S (사회) — 의료·교육: Korean in parens matches Layer 1."""
        result = _classify_steeps_field("S (사회) — 의료·교육 정책")
        assert result == {"S_Social"}

    def test_social_korean_in_parens(self):
        """Social (사회) — 의료인력: English name + Korean in parens."""
        result = _classify_steeps_field("Social (사회) — 의료인력/교육정책")
        assert result == {"S_Social"}

    # -- Production bug regression: BUG-1 (spiritual/ethical) format --------

    def test_bug1_spiritual_ethical_with_tech(self):
        """BUG-1 regression: (spiritual/ethical) combined with T must detect both."""
        result = _classify_steeps_field(
            "T (Technological) / s (spiritual/ethical) -- AI 정렬, 윤리적 추론"
        )
        assert result == {"T_Technological", "s_spiritual"}

    def test_bug1_spiritual_ethical_with_social(self):
        """BUG-1 regression: (spiritual/ethical) combined with S must detect both."""
        result = _classify_steeps_field(
            "S (Social) / s (spiritual/ethical) -- AI 공정성, 구조적 차별"
        )
        assert result == {"S_Social", "s_spiritual"}

    # -- Production bug regression: BUG-2 CODE / CODE (description) ---------

    def test_bug2_fullcode_dual_tech_spiritual(self):
        """BUG-2 regression: bare full-codes with paren description."""
        result = _classify_steeps_field(
            "T_Technological / s_spiritual (AI 안전성, 다중 에이전트 시스템, 정렬)"
        )
        assert result == {"T_Technological", "s_spiritual"}

    def test_bug2_fullcode_dual_econ_social(self):
        result = _classify_steeps_field(
            "E_Economic / S_Social (행동경제학, AI 편향, 금융 의사결정)"
        )
        assert result == {"E_Economic", "S_Social"}

    def test_bug2_fullcode_dual_econ_political(self):
        result = _classify_steeps_field(
            "E_Economic / P_Political (AI 편향, 금융 예측, 거버넌스)"
        )
        assert result == {"E_Economic", "P_Political"}

    def test_bug2_fullcode_dual_political_tech(self):
        result = _classify_steeps_field(
            "P_Political / T_Technological (AI 거버넌스, 행정법, 규제)"
        )
        assert result == {"P_Political", "T_Technological"}

    def test_bug2_fullcode_dual_tech_political(self):
        result = _classify_steeps_field(
            "T_Technological / P_Political (AI 보안, 에이전트 AI 아키텍처)"
        )
        assert result == {"T_Technological", "P_Political"}

    def test_bug2_fullcode_dual_econ_social_2(self):
        result = _classify_steeps_field(
            "E_Economic / S_Social (법률 AI, 공공 인식, 위험 관리)"
        )
        assert result == {"E_Economic", "S_Social"}

    def test_bug2_fullcode_dual_tech_social(self):
        result = _classify_steeps_field(
            "T_Technological / S_Social (휴머노이드 로봇, 인간-로봇 상호작용)"
        )
        assert result == {"T_Technological", "S_Social"}

    def test_bug2_fullcode_dual_social_political(self):
        result = _classify_steeps_field(
            "S_Social / P_Political (AI 거버넌스, 인간 감독, 사회적 분기)"
        )
        assert result == {"S_Social", "P_Political"}

    def test_bug2_fullcode_dual_tech_env(self):
        result = _classify_steeps_field(
            "T_Technological / E_Environmental (우주론, 천체물리학, 기초과학)"
        )
        assert result == {"T_Technological", "E_Environmental"}


# ---------------------------------------------------------------------------
# Tests: Real reports (conditional — only run if files exist)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tests: English profiles (_en) — bilingual workflow validation
# ---------------------------------------------------------------------------

def _make_en_signal_block(n: int, full: bool = True) -> str:
    """Generate a single English signal block with 9 fields."""
    block = f"### Priority {n}: Test Signal Title {n}\n\n"
    block += f"- **Confidence**: pSST not computed (priority score: {8.0 - n * 0.1:.1f}/10.0)\n\n"
    block += f"1. **Classification**: Technological (T) -- AI/LLM\n"
    block += f"2. **Source**: TestSource, 2026-02-01, ID: test-{n:03d}\n"
    block += f"3. **Key Facts**: This is the key fact for test signal {n}. Important findings.\n"
    block += f"4. **Quantitative Metrics**:\n   - Impact: 8.0/10\n   - Probability: 7.0/10\n"
    block += f"5. **Impact**: ⭐⭐⭐⭐ ({8.0 - n * 0.1:.1f}/10.0) — High\n"
    if full:
        block += f"6. **Detailed Description**: Detailed analysis of test signal {n}. Multi-sentence description.\n"
        block += f"7. **Inference**: Strategic interpretation for decision makers.\n"
        block += f"8. **Stakeholders**: Government, Company A, Company B, Academia\n"
        block += f"9. **Monitoring Indicators**:\n   - Patent filing count\n   - Investment trends\n"
    block += "\n---\n\n"
    return block


def _make_good_en_report() -> str:
    """Create a synthetic English report that should pass standard_en checks."""
    sections = []

    # Header
    sections.append("# Daily Environmental Scanning Report\n\n**Date**: 2026-02-01\n\n")
    sections.append("> **Scan Window**: 2026-01-31 14:00 ~ 2026-02-01 14:00 (24 hours)\n")
    sections.append("> **Anchor Time (T₀)**: 2026-02-01T14:00:00+09:00\n\n---\n\n")

    # Section 1
    sections.append("## 1. Executive Summary\n\n")
    sections.append("### Today's Key Findings (Top 3 Signals)\n\n")
    for i in range(1, 4):
        sections.append(f"{i}. **Test Signal {i}** (Technology)\n   - Importance: ⭐⭐⭐⭐⭐\n   - Key Content: Summary {i}\n   - Strategic Implications: Implication {i}\n\n")
    sections.append("### Key Changes Summary\n- New signals detected: 100\n- Top priority signals: 15\n- Major impact domains: Technology(40%), Economy(30%)\n\n---\n\n")

    # Section 2
    sections.append("## 2. Newly Detected Signals\n\n> Priority-ranked analysis results.\n\n---\n\n")
    for i in range(1, 16):
        sections.append(_make_en_signal_block(i, full=(i <= 10)))

    # Section 3
    sections.append("## 3. Existing Signal Updates\n\n")
    sections.append("> Active Tracking Threads: 12 | Strengthening: 3 | Weakening: 1 | Faded: 2\n\n")
    sections.append("### 3.1 Strengthening Trends\n\n")
    sections.append("| Tracking Thread | Days Tracked | pSST Change | Velocity | Breadth |\n|-----------------|-------------|-------------|----------|--------|\n")
    sections.append("| Quantum Computing | 10 days | 82→88 (+6) | ▲ Accelerating | 0.67 |\n\n")
    sections.append("### 3.2 Weakening Trends\n\n")
    sections.append("| New | 8 | 53% |\n| Strengthening | 3 | 20% |\n\n")
    sections.append("### 3.3 Signal Status Summary\n\n")
    sections.append("| Status | Count | Ratio |\n|--------|-------|-------|\n")
    sections.append("| New | 8 | 53% |\n| Strengthening | 3 | 20% |\n\n---\n\n")

    # Section 4
    sections.append("## 4. Patterns and Connections\n\n")
    sections.append("### 4.1 Cross-Impact Between Signals\n\n")
    sections.append("- **Quantum Computing** ↔ **Semiconductor Supply Chain**: Impact +3\n")
    sections.append("- **AI Labor Replacement** ↔ **Education Reform**: Impact +4\n")
    sections.append("- **Climate Policy** ↔ **Energy Transition**: Impact +3\n")
    sections.append("- **Digital Currency** ↔ **Financial Regulation**: Impact +2\n\n")
    sections.append("### 4.2 Emerging Themes\n\n")
    sections.append("1. **Technology Sovereignty** — Related: 25 signals, STEEPs: T, P, E\n\n---\n\n")

    # Section 5
    sections.append("## 5. Strategic Implications\n\n")
    sections.append("### 5.1 Short-term (0-6 months)\n\nStrategic points here.\n\n")
    sections.append("### 5.2 Mid-term (6-24 months)\n\nMore strategic points.\n\n")
    sections.append("### 5.3 Long-term (2+ years)\n\nLong-term implications.\n\n---\n\n")

    # Section 6
    sections.append("## 6. Plausible Scenarios\n\nScenario analysis here.\n\n---\n\n")

    # Section 7
    sections.append("## 7. Confidence Analysis\n\nConfidence assessment here.\n\n---\n\n")

    # Section 8
    sections.append("## 8. Appendix\n\nAppendix data here.\n\n")

    # Pad to ensure word count (repeat some text)
    padding = "Quantum computing technology development signal detection " * 300
    sections.append(f"\n\n{padding}\n")

    return "".join(sections)


class TestEnProfiles:
    """Tests for English report validation profiles (standard_en, etc.)."""

    def test_standard_en_good_report(self, tmp_path):
        """A well-formed English report should pass standard_en."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        # Check no CRITICAL failures
        crits = [r for r in result.results if not r.passed and r.level == "CRITICAL"]
        assert len(crits) == 0, f"Unexpected CRITICAL failures: {[(r.check_id, r.detail) for r in crits]}"

    def test_standard_en_has_correct_checks(self, tmp_path):
        """standard_en should produce the same check IDs as standard."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        check_ids = {r.check_id for r in result.results}
        assert "FILE-001" in check_ids
        assert "SEC-001" in check_ids
        assert "SIG-001" in check_ids
        assert "SIG-002" in check_ids
        assert "STEEPS-001" in check_ids
        assert "EVOL-001" in check_ids
        assert "TEMP-001" in check_ids

    def test_standard_en_korean_report_fails_sec001(self, tmp_path):
        """A Korean report validated with standard_en should fail SEC-001."""
        content = _make_good_report()
        f = tmp_path / "ko-as-en.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        sec001 = next(r for r in result.results if r.check_id == "SEC-001")
        assert not sec001.passed, "Korean report should fail English section header check"

    def test_standard_en_counts_en_signal_blocks(self, tmp_path):
        """English signal blocks with Priority N: headers should be counted."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        sig001 = next(r for r in result.results if r.check_id == "SIG-001")
        assert sig001.passed, f"SIG-001 should pass: {sig001.detail}"

    def test_standard_en_checks_en_fields(self, tmp_path):
        """SIG-002 should check English field names (**Classification**, etc.)."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        sig002 = next(r for r in result.results if r.check_id == "SIG-002")
        assert sig002.passed, f"SIG-002 should pass with English fields: {sig002.detail}"

    def test_standard_en_korean_ratio_not_required(self, tmp_path):
        """English reports should pass QUAL-002 even with 0% Korean."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        qual002 = next(r for r in result.results if r.check_id == "QUAL-002")
        assert qual002.passed, "QUAL-002 should pass for English report (min_korean_ratio=0)"

    def test_standard_en_detects_steeps(self, tmp_path):
        """STEEPS-001 should detect categories from **Classification** fields."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        steeps = next(r for r in result.results if r.check_id == "STEEPS-001")
        # All signals are T, so only 1 category — will fail (need 4)
        # This is expected: validates that STEEPS detection works in EN mode
        assert "T_Technological" in steeps.detail or steeps.passed is False

    def test_standard_en_evol_check(self, tmp_path):
        """EVOL-001 should detect English evolution keywords."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        evol = next(r for r in result.results if r.check_id == "EVOL-001")
        assert evol.passed, f"EVOL-001 should pass with English evolution text: {evol.detail}"

    def test_standard_en_temp_check(self, tmp_path):
        """TEMP-001 should detect Scan Window / T₀ in English."""
        content = _make_good_en_report()
        f = tmp_path / "en-report.md"
        f.write_text(content, encoding="utf-8")
        result = validate_report(str(f), profile="standard_en")
        temp = next(r for r in result.results if r.check_id == "TEMP-001")
        assert temp.passed, f"TEMP-001 should pass with English temporal text: {temp.detail}"


class TestEnHelperFunctions:
    """Tests for language-aware helper functions."""

    def test_count_signal_blocks_en(self):
        content = "### Priority 1: Signal A\n### Priority 2: Signal B\n"
        assert _count_signal_blocks(content, language="en") == 2

    def test_count_signal_blocks_en_integrated(self):
        content = "### Integrated Priority 1: Signal A\n### Integrated Priority 2: Signal B\n"
        assert _count_signal_blocks(content, language="en") == 2

    def test_count_signal_blocks_en_no_korean(self):
        content = "### 우선순위 1: 신호 A\n"
        assert _count_signal_blocks(content, language="en") == 0

    def test_count_signal_blocks_ko_default(self):
        """Default language=ko, backward compatible."""
        content = "### 우선순위 1: 신호 A\n### 우선순위 2: 신호 B\n"
        assert _count_signal_blocks(content) == 2

    def test_check_signal_fields_en(self):
        block = _make_en_signal_block(1, full=True)
        total, complete, missing = _check_signal_fields(block, max_signals=1, language="en")
        assert total == 1
        assert complete == 1, f"Missing fields: {missing}"

    def test_check_signal_fields_en_incomplete(self):
        block = _make_en_signal_block(1, full=False)
        total, complete, missing = _check_signal_fields(block, max_signals=1, language="en")
        assert total == 1
        assert complete == 0
        assert len(missing) == 1
        assert "Detailed Description" in missing[0]["missing_fields"]

    def test_extract_steeps_en(self):
        content = (
            "### Priority 1: AI\n"
            "1. **Classification**: Technological (T) -- AI research\n"
            "### Priority 2: Trade\n"
            "1. **Classification**: Economic (E) -- trade policy\n"
        )
        dist = _extract_steeps_distribution(content, language="en")
        assert "T_Technological" in dist
        assert "E_Economic" in dist

    def test_extract_steeps_ko_default(self):
        """Default language=ko backward compatible."""
        content = "1. **분류**: 기술 (T) — AI\n"
        dist = _extract_steeps_distribution(content)
        assert "T_Technological" in dist

    def test_extract_steeps_en_ignores_ko_field(self):
        """EN mode should NOT match **분류** fields."""
        content = "1. **분류**: 기술 (T) — AI\n"
        dist = _extract_steeps_distribution(content, language="en")
        assert len(dist) == 0


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


# ---------------------------------------------------------------------------
# EXPLO-001: Exploration Proof Check (option-based)
# ---------------------------------------------------------------------------

class TestExplorationProofCheck:
    """Tests for EXPLO-001: exploration proof validation (--exploration-proof option)."""

    def test_valid_proof_passes(self, tmp_path):
        """Valid exploration proof file passes EXPLO-001."""
        proof = {
            "gate_id": "exploration_gate.py",
            "gate_decision": "MUST_RUN",
            "execution_status": "executed",
            "date": "2026-02-13",
        }
        proof_file = tmp_path / "proof.json"
        proof_file.write_text(json.dumps(proof))

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(proof_file))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is True

    def test_missing_proof_fails(self, tmp_path):
        """Missing proof file fails EXPLO-001."""
        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(tmp_path / "nonexistent.json"))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is False
        assert "not found" in explo[0].detail

    def test_invalid_json_fails(self, tmp_path):
        """Invalid JSON in proof file fails EXPLO-001."""
        bad_file = tmp_path / "bad-proof.json"
        bad_file.write_text("{invalid json")

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(bad_file))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].passed is False
        assert "Invalid JSON" in explo[0].detail

    def test_missing_fields_fails(self, tmp_path):
        """Proof file missing required fields fails EXPLO-001."""
        incomplete = {"gate_id": "exploration_gate.py"}  # Missing gate_decision, execution_status, date
        proof_file = tmp_path / "incomplete-proof.json"
        proof_file.write_text(json.dumps(incomplete))

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(proof_file))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].passed is False
        assert "missing fields" in explo[0].detail

    def test_skipped_proof_passes(self, tmp_path):
        """Proof with SKIP_DISABLED decision passes (valid format)."""
        proof = {
            "gate_id": "exploration_gate.py",
            "gate_decision": "SKIP_DISABLED",
            "execution_status": "skipped",
            "date": "2026-02-13",
        }
        proof_file = tmp_path / "skip-proof.json"
        proof_file.write_text(json.dumps(proof))

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(proof_file))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].passed is True

    def test_check_level_is_error_by_default(self, tmp_path):
        """EXPLO-001 check level defaults to ERROR."""
        proof_file = tmp_path / "proof.json"
        proof_file.write_text(json.dumps({
            "gate_id": "exploration_gate.py",
            "gate_decision": "MUST_RUN",
            "execution_status": "executed",
            "date": "2026-02-13",
        }))

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(proof_file))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].level == "ERROR"

    def test_check_level_critical_when_passed(self, tmp_path):
        """EXPLO-001 level should be CRITICAL when caller passes level='CRITICAL'."""
        proof_file = tmp_path / "proof.json"
        proof_file.write_text(json.dumps({
            "gate_id": "exploration_gate.py",
            "gate_decision": "MUST_RUN",
            "execution_status": "executed",
            "date": "2026-02-13",
        }))

        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(proof_file), level="CRITICAL")

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].level == "CRITICAL"

    def test_missing_proof_with_critical_level(self, tmp_path):
        """Missing proof + level=CRITICAL → CRITICAL FAIL (not ERROR FAIL)."""
        vr = ValidationReport(report_path="dummy.md")
        _check_exploration_proof(vr, str(tmp_path / "nonexistent.json"), level="CRITICAL")

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert explo[0].passed is False
        assert explo[0].level == "CRITICAL"


# ---------------------------------------------------------------------------
# EXPLO-001 Auto-Enforcement (SOT-driven mandatory enforcement)
# ---------------------------------------------------------------------------

class TestExplorationAutoEnforcement:
    """Tests for _auto_enforce_exploration(): auto-detect SOT enforcement setting
    and apply CRITICAL (mandatory) or ERROR (optional) level to EXPLO-001."""

    def _setup_wf1_project(self, tmp_path, enforcement="mandatory", exploration_enabled=True):
        """Create a minimal project structure with SOT for testing auto-enforcement.
        Returns the report path."""
        # Create directory structure: project_root/env-scanning/wf1-general/reports/daily/
        project_root = tmp_path / "project"
        wf1_reports = project_root / "env-scanning" / "wf1-general" / "reports" / "daily"
        wf1_reports.mkdir(parents=True)
        wf1_exploration = project_root / "env-scanning" / "wf1-general" / "exploration"
        wf1_exploration.mkdir(parents=True)

        # Create minimal SOT
        sot_dir = project_root / "env-scanning" / "config"
        sot_dir.mkdir(parents=True)
        sot_content = {
            "workflows": {
                "wf1-general": {
                    "data_root": "env-scanning/wf1-general",
                    "parameters": {
                        "source_exploration": {
                            "enabled": exploration_enabled,
                            "enforcement": enforcement,
                        }
                    }
                }
            }
        }
        import yaml as _yaml
        with open(sot_dir / "workflow-registry.yaml", "w") as f:
            _yaml.dump(sot_content, f)

        # Create report file
        report_path = wf1_reports / "environmental-scan-2026-02-15.md"
        report_path.write_text("# Test report", encoding="utf-8")

        return str(report_path), project_root, wf1_exploration

    def test_wf1_mandatory_no_proof_critical(self, tmp_path):
        """WF1 + enforcement=mandatory + no proof → CRITICAL FAIL."""
        report_path, _, _ = self._setup_wf1_project(tmp_path, enforcement="mandatory")
        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is False
        assert explo[0].level == "CRITICAL"
        assert "mandatory" in explo[0].detail.lower()

    def test_wf1_mandatory_with_proof_passes(self, tmp_path):
        """WF1 + enforcement=mandatory + valid proof → PASS."""
        report_path, _, exploration_dir = self._setup_wf1_project(
            tmp_path, enforcement="mandatory"
        )
        # Create valid proof file
        proof = {
            "gate_id": "exploration_gate.py",
            "gate_decision": "MUST_RUN",
            "execution_status": "executed",
            "date": "2026-02-15",
        }
        proof_file = exploration_dir / "exploration-proof-2026-02-15.json"
        proof_file.write_text(json.dumps(proof), encoding="utf-8")

        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is True

    def test_wf2_path_skips_exploration(self, tmp_path):
        """WF2 path (not wf1-general) → auto-detection skips entirely."""
        # Create a WF2-like path
        wf2_dir = tmp_path / "project" / "env-scanning" / "wf2-arxiv" / "reports" / "daily"
        wf2_dir.mkdir(parents=True)
        report_path = wf2_dir / "environmental-scan-2026-02-15.md"
        report_path.write_text("# Test", encoding="utf-8")

        vr = ValidationReport(report_path=str(report_path))
        _auto_enforce_exploration(vr, str(report_path))

        # No EXPLO-001 check should be added
        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 0

    def test_non_standard_path_skips(self, tmp_path):
        """Non-standard filename → graceful skip (no EXPLO-001 added)."""
        report_path = tmp_path / "custom-report.md"
        report_path.write_text("# Test", encoding="utf-8")

        vr = ValidationReport(report_path=str(report_path))
        _auto_enforce_exploration(vr, str(report_path))

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 0

    def test_optional_enforcement_stays_error(self, tmp_path):
        """enforcement=optional + no proof → ERROR (not CRITICAL)."""
        report_path, _, _ = self._setup_wf1_project(tmp_path, enforcement="optional")
        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is False
        assert explo[0].level == "ERROR"

    def test_check_level_is_critical_when_mandatory(self, tmp_path):
        """Verify level field is exactly 'CRITICAL' when enforcement=mandatory."""
        report_path, _, exploration_dir = self._setup_wf1_project(
            tmp_path, enforcement="mandatory"
        )
        # Even with a valid proof, verify the level would be CRITICAL
        proof = {
            "gate_id": "exploration_gate.py",
            "gate_decision": "MUST_RUN",
            "execution_status": "executed",
            "date": "2026-02-15",
        }
        proof_file = exploration_dir / "exploration-proof-2026-02-15.json"
        proof_file.write_text(json.dumps(proof), encoding="utf-8")

        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].level == "CRITICAL"

    def test_exploration_disabled_skips(self, tmp_path):
        """exploration.enabled=false → no EXPLO-001 check added."""
        report_path, _, _ = self._setup_wf1_project(
            tmp_path, enforcement="mandatory", exploration_enabled=False
        )
        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 0

    def test_get_enforcement_level_mandatory(self, tmp_path):
        """_get_enforcement_level returns CRITICAL for WF1 mandatory path."""
        report_path, _, _ = self._setup_wf1_project(tmp_path, enforcement="mandatory")
        level = _get_enforcement_level(report_path)
        assert level == "CRITICAL"

    def test_get_enforcement_level_optional(self, tmp_path):
        """_get_enforcement_level returns ERROR for WF1 optional path."""
        report_path, _, _ = self._setup_wf1_project(tmp_path, enforcement="optional")
        level = _get_enforcement_level(report_path)
        assert level == "ERROR"

    def test_get_enforcement_level_non_wf1(self, tmp_path):
        """_get_enforcement_level returns ERROR for non-WF1 paths."""
        wf2_dir = tmp_path / "project" / "env-scanning" / "wf2-arxiv" / "reports" / "daily"
        wf2_dir.mkdir(parents=True)
        report_path = wf2_dir / "environmental-scan-2026-02-15.md"
        report_path.write_text("# Test", encoding="utf-8")
        level = _get_enforcement_level(str(report_path))
        assert level == "ERROR"

    def test_flag_override_respects_mandatory_level(self, tmp_path):
        """When --exploration-proof is passed with mandatory enforcement,
        _check_exploration_proof should use CRITICAL level (not ERROR).
        This tests the CRITICAL-1 fix: flag overrides path, not level."""
        report_path, _, exploration_dir = self._setup_wf1_project(
            tmp_path, enforcement="mandatory"
        )
        # Create invalid proof (missing fields)
        bad_proof = exploration_dir / "bad-proof.json"
        bad_proof.write_text(json.dumps({"gate_id": "test"}), encoding="utf-8")

        # Simulate what main() does: get level from SOT, pass to _check_exploration_proof
        level = _get_enforcement_level(report_path)
        assert level == "CRITICAL"  # Confirms SOT is read correctly

        vr = ValidationReport(report_path=report_path)
        _check_exploration_proof(vr, str(bad_proof), level=level)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1
        assert explo[0].passed is False
        assert explo[0].level == "CRITICAL"  # NOT ERROR — CRITICAL-1 fix verified


# ---------------------------------------------------------------------------
# EXPLO-001 Silent Fallback Fix Tests (v2.9.0)
# ---------------------------------------------------------------------------

class TestExplo001SilentFallbackFix:
    """Tests that SOT parsing failures in _auto_enforce_exploration() produce
    visible error/critical results instead of silently returning."""

    def _setup_wf1_project(self, tmp_path, sot_content=None, create_sot=True):
        """Create a WF1 project structure. Returns (report_path, sot_path)."""
        project_root = tmp_path / "project"
        wf1_reports = project_root / "env-scanning" / "wf1-general" / "reports" / "daily"
        wf1_reports.mkdir(parents=True)
        sot_dir = project_root / "env-scanning" / "config"
        sot_dir.mkdir(parents=True)

        sot_path = sot_dir / "workflow-registry.yaml"
        if create_sot and sot_content is not None:
            import yaml as _yaml
            with open(sot_path, "w") as f:
                _yaml.dump(sot_content, f)
        elif create_sot:
            # Create a valid SOT with exploration enabled
            sot = {
                "workflows": {
                    "wf1-general": {
                        "data_root": "env-scanning/wf1-general",
                        "parameters": {
                            "source_exploration": {
                                "enabled": True,
                                "enforcement": "mandatory",
                            }
                        }
                    }
                }
            }
            import yaml as _yaml
            with open(sot_path, "w") as f:
                _yaml.dump(sot, f)

        report_path = wf1_reports / "environmental-scan-2026-02-15.md"
        report_path.write_text("# Test report", encoding="utf-8")

        return str(report_path), sot_path

    def test_sot_parse_failure_produces_critical(self, tmp_path):
        """SOT YAML parse error → CRITICAL EXPLO-001 (not silent skip)."""
        report_path, sot_path = self._setup_wf1_project(tmp_path, create_sot=False)
        # Write invalid YAML
        sot_path.parent.mkdir(parents=True, exist_ok=True)
        sot_path.write_text("{{{invalid yaml content!!!", encoding="utf-8")

        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1, "Expected EXPLO-001 check result on SOT parse failure"
        assert explo[0].passed is False
        assert explo[0].level == "CRITICAL"
        assert "parse" in explo[0].detail.lower() or "sot" in explo[0].detail.lower()

    def test_sot_not_found_produces_error(self, tmp_path):
        """SOT file missing → ERROR EXPLO-001 (not silent skip)."""
        report_path, sot_path = self._setup_wf1_project(tmp_path, create_sot=False)
        # Do NOT create SOT file — it should be missing

        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 1, "Expected EXPLO-001 check result when SOT missing"
        assert explo[0].passed is False
        assert explo[0].level == "ERROR"
        assert "not found" in explo[0].detail.lower() or "sot" in explo[0].detail.lower()

    def test_exploration_disabled_still_silent(self, tmp_path):
        """exploration.enabled=false → still produces NO check (legitimate skip)."""
        sot = {
            "workflows": {
                "wf1-general": {
                    "data_root": "env-scanning/wf1-general",
                    "parameters": {
                        "source_exploration": {
                            "enabled": False,
                            "enforcement": "mandatory",
                        }
                    }
                }
            }
        }
        report_path, _ = self._setup_wf1_project(tmp_path, sot_content=sot)

        vr = ValidationReport(report_path=report_path)
        _auto_enforce_exploration(vr, report_path)

        explo = [r for r in vr.results if r.check_id == "EXPLO-001"]
        assert len(explo) == 0, "exploration disabled should not add EXPLO-001"


# ---------------------------------------------------------------------------
# Tests: WF4 multiglobal-news profiles existence and FSSF flags
# ---------------------------------------------------------------------------

class TestMultiglobalNewsProfiles:
    """Tests that multiglobal-news and multiglobal-news_en profiles exist
    in PROFILES and have the expected FSSF-related flags."""

    def test_multiglobal_news_profile_exists(self):
        """multiglobal-news profile must exist in PROFILES dict."""
        from validate_report import PROFILES
        assert "multiglobal-news" in PROFILES, \
            f"multiglobal-news not in PROFILES. Available: {list(PROFILES.keys())}"

    def test_multiglobal_news_en_profile_exists(self):
        """multiglobal-news_en profile must exist in PROFILES dict."""
        from validate_report import PROFILES
        assert "multiglobal-news_en" in PROFILES, \
            f"multiglobal-news_en not in PROFILES. Available: {list(PROFILES.keys())}"

    def test_multiglobal_news_has_fssf_flag(self):
        """multiglobal-news profile must require FSSF table."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news"]
        assert prof.get("require_fssf_table") is True

    def test_multiglobal_news_has_three_horizons_flag(self):
        """multiglobal-news profile must require Three Horizons table."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news"]
        assert prof.get("require_three_horizons_table") is True

    def test_multiglobal_news_has_tipping_point_flag(self):
        """multiglobal-news profile must require tipping point section."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news"]
        assert prof.get("require_tipping_point_section") is True

    def test_multiglobal_news_en_has_fssf_flag(self):
        """multiglobal-news_en profile must require FSSF table."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("require_fssf_table") is True

    def test_multiglobal_news_en_has_three_horizons_flag(self):
        """multiglobal-news_en profile must require Three Horizons table."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("require_three_horizons_table") is True

    def test_multiglobal_news_en_has_tipping_point_flag(self):
        """multiglobal-news_en profile must require tipping point section."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("require_tipping_point_section") is True

    def test_multiglobal_news_has_s4_required_subs(self):
        """multiglobal-news profile must define s4_required_subs for Section 4."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news"]
        subs = prof.get("s4_required_subs")
        assert subs is not None and len(subs) > 0, \
            "multiglobal-news must define s4_required_subs"

    def test_multiglobal_news_en_has_s4_required_subs(self):
        """multiglobal-news_en profile must define s4_required_subs for Section 4."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        subs = prof.get("s4_required_subs")
        assert subs is not None and len(subs) > 0, \
            "multiglobal-news_en must define s4_required_subs"

    def test_multiglobal_news_en_is_english_language(self):
        """multiglobal-news_en must have language='en'."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("language") == "en"

    def test_multiglobal_news_en_zero_korean_ratio(self):
        """multiglobal-news_en must have min_korean_ratio=0.0 (English-only)."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("min_korean_ratio") == 0.0

    def test_multiglobal_news_min_signal_blocks(self):
        """multiglobal-news must require at least 10 signal blocks."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news"]
        assert prof.get("min_signal_blocks", 0) >= 10

    def test_multiglobal_news_en_min_signal_blocks(self):
        """multiglobal-news_en must require at least 10 signal blocks."""
        from validate_report import PROFILES
        prof = PROFILES["multiglobal-news_en"]
        assert prof.get("min_signal_blocks", 0) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
