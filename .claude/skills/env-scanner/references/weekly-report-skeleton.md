# 주간 보고서 스켈레톤 템플릿 (Weekly Report Skeleton Template)

> **용도**: 주간 메타분석 보고서를 "자유 생성"하지 않고, 이 구조를 **채우는** 방식으로 작성합니다.
> 모든 `{{PLACEHOLDER}}` 토큰은 반드시 실제 내용으로 대체되어야 합니다.
> 미채워진 플레이스홀더가 남으면 **SKEL-001 검증 실패**가 발생합니다.
>
> **중요**: 이 스켈레톤은 7일간의 일일 스캔 결과를 거시적으로 재분석한
> 주간 메타분석 보고서용입니다. 일일 보고서에는 `report-skeleton.md`를,
> 통합 일일 보고서에는 `integrated-report-skeleton.md`를 사용하세요.
>
> **작성 언어**: 한국어 (기술 용어, 고유명사, 약어는 영문 병기 허용)
>
> **검증 프로파일**: `weekly` (validate_report.py --profile weekly)

---

## 사용 지침

1. 이 템플릿을 복사하여 `integrated/weekly/reports/weekly-scan-{week_id}.md`로 저장합니다.
2. 모든 `{{...}}` 플레이스홀더를 데이터에 기반한 실제 내용으로 대체합니다.
3. 섹션 헤더(`## N. ...`)는 **절대 변경하지 마세요** — 정확한 문자열이 검증 대상입니다.
4. 서브섹션 헤더(`### N.N ...`)도 번호를 유지하세요.
5. 모든 신호/추세에 `[WF1]`, `[WF2]`, `[WF3]`, 또는 `[WF4]` 소스 태그를 반드시 포함하세요.
6. 생성 완료 후, 파일에 `{{`가 남아 있지 않은지 확인합니다.

---

# 주간 환경 스캐닝 보고서

{{REPORT_HEADER_METADATA}}

> **보고서 유형**: 주간 메타분석 보고서 (Weekly Meta-Analysis)
> **분석 기간**: {{ANALYSIS_START_DATE}} ~ {{ANALYSIS_END_DATE}} ({{DAILY_SCAN_COUNT}}일)
> **주간 ID**: {{WEEK_ID}}
> **일일 스캔 기준**: 각 일일 스캔은 T₀ 기준 {{DAILY_LOOKBACK_HOURS}}시간 범위

---

## 1. 경영진 요약

### 금주의 3대 핵심 추세

1. **{{TREND_1_TITLE}}** ({{TREND_1_TIS_GRADE}})
   - 추세 강도(TIS): {{TREND_1_TIS_SCORE}}
   - 핵심 내용: {{TREND_1_SUMMARY}}
   - 전략적 시사점: {{TREND_1_IMPLICATION}}

2. **{{TREND_2_TITLE}}** ({{TREND_2_TIS_GRADE}})
   - 추세 강도(TIS): {{TREND_2_TIS_SCORE}}
   - 핵심 내용: {{TREND_2_SUMMARY}}
   - 전략적 시사점: {{TREND_2_IMPLICATION}}

3. **{{TREND_3_TITLE}}** ({{TREND_3_TIS_GRADE}})
   - 추세 강도(TIS): {{TREND_3_TIS_SCORE}}
   - 핵심 내용: {{TREND_3_SUMMARY}}
   - 전략적 시사점: {{TREND_3_IMPLICATION}}

### 주간 신호 통계 요약

- **분석 기간**: {{ANALYSIS_START_DATE}} ~ {{ANALYSIS_END_DATE}}
- **분석 일일 스캔 수**: {{DAILY_SCAN_COUNT}}일
- **분석 대상 총 신호**: {{TOTAL_SIGNALS_ANALYZED}}개
  - WF1 (일반): {{WF1_TOTAL_SIGNALS}}개
  - WF2 (arXiv): {{WF2_TOTAL_SIGNALS}}개
  - WF3 (네이버 뉴스): {{WF3_TOTAL_SIGNALS}}개
  - WF4 (멀티글로벌 뉴스): {{WF4_TOTAL_SIGNALS}}개
- **상승 추세**: {{ACCELERATING_COUNT}}개
- **하락 추세**: {{DECELERATING_COUNT}}개
- **신규 등장**: {{NEW_EMERGED_COUNT}}개
- **소멸/해소**: {{FADED_COUNT}}개
- **수렴 클러스터**: {{CLUSTER_COUNT}}개

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. 주간 추세 분석

{{SECTION2_INTRO}}

### 2.1 STEEPs별 주간 동향

{{STEEPS_WEEKLY_TRENDS}}

### 2.2 상승 추세 (Accelerating)

{{ACCELERATING_TRENDS}}

### 2.3 하락 추세 (Decelerating)

{{DECELERATING_TRENDS}}

### 2.4 신규 등장 (Newly Emerged)

{{NEWLY_EMERGED}}

### 2.5 소멸/해소 (Faded)

{{FADED_SIGNALS}}

---

## 3. 신호 수렴 분석

{{SECTION3_INTRO}}

### 3.1 수렴 클러스터 (Converging Clusters)

{{CONVERGENCE_CLUSTERS}}

### 3.2 발산 신호 (Diverging Signals)

{{DIVERGING_SIGNALS}}

### 3.3 WF1↔WF2 교차 검증

{{WF1_WF2_CROSS_VALIDATION}}

---

## 4. 신호 진화 타임라인

> 주간 활성 스레드: {{WEEKLY_EVOLUTION_TOTAL_THREADS}}개 | 신규: {{WEEKLY_EVOLUTION_NEW_THREADS}}개 | 소멸: {{WEEKLY_EVOLUTION_FADED_THREADS}}개

### 4.1 주간 신호 진화 흐름

{{WEEKLY_EVOLUTION_TOP_ACCELERATING}}

{{SIGNAL_EVOLUTION_FLOW}}

### 4.2 pSST 점수 변동 추적

{{WEEKLY_EVOLUTION_TOP_DECELERATING}}

{{PSST_CHANGES}}

### 4.3 신호 성숙도 변화

{{MATURITY_TRANSITIONS}}

---

## 5. 전략적 시사점

### 5.1 즉시 조치 필요 (0-6개월)

{{IMMEDIATE_ACTIONS}}

### 5.2 중기 모니터링 (6-18개월)

{{MIDTERM_MONITORING}}

### 5.3 장기 관찰 필요 (18개월+)

{{LONGTERM_WATCH}}

### 5.4 이전 주 대비 변화

{{WEEK_OVER_WEEK_CHANGES}}

---

## 6. Plausible Scenarios(개연성 있는 시나리오)

{{WEEKLY_SCENARIOS}}

---

## 7. 신뢰도 분석

### 7.1 주간 pSST 등급 분포 추이

{{PSST_DISTRIBUTION_TREND}}

### 7.2 소스별 신뢰도 주간 평균

{{SOURCE_RELIABILITY_WEEKLY}}

### 7.3 STEEPs별 평균 pSST 변동

{{STEEPS_PSST_CHANGES}}

---

## 8. 시스템 성능 리뷰

### 8.1 주간 스캐닝 품질 지표

{{QUALITY_METRICS}}

### 8.2 소스 건강 현황

{{SOURCE_HEALTH}}

### 8.3 캘리브레이션 권고

{{CALIBRATION_RECOMMENDATIONS}}

---

## 9. 부록

### 9.1 분석 대상 일일 보고서 목록

{{DAILY_REPORTS_LIST}}

### 9.2 주간 전체 추세 목록

{{FULL_TREND_LIST}}

### 9.3 방법론

{{METHODOLOGY}}

### 9.4 실행 요약

| 항목 | 값 |
|------|---|
| 주간 ID | {{WEEK_ID}} |
| 분석 기간 | {{ANALYSIS_START_DATE}} ~ {{ANALYSIS_END_DATE}} |
| 일일 스캔 수 | {{DAILY_SCAN_COUNT}}일 |
| 분석 신호 수 | {{TOTAL_SIGNALS_ANALYZED}}개 |
| 수렴 클러스터 | {{CLUSTER_COUNT}}개 |
| 핵심 추세 | {{TOP_TRENDS_COUNT}}개 |
| 실행 시간 | {{EXECUTION_DURATION}} |
