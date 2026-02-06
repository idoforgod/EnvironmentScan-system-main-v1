# 네이버 뉴스 환경 스캐닝 보고서 스켈레톤 (WF3 Report Skeleton Template)

> **용도**: report-generator 에이전트가 보고서를 "자유 생성"하지 않고, 이 구조를 **채우는** 방식으로 작성합니다.
> 모든 `{{PLACEHOLDER}}` 토큰은 반드시 실제 내용으로 대체되어야 합니다.
> 미채워진 플레이스홀더가 남으면 **SKEL-001 검증 실패**가 발생합니다.
>
> **WF3 전용**: 이 스켈레톤은 네이버 뉴스 환경스캐닝(WF3) 전용입니다.
> WF1/WF2 보고서에는 `report-skeleton.md`를, 통합 보고서에는 `integrated-report-skeleton.md`를 사용하세요.
>
> **WF3 특화 섹션**: FSSF 8-type 분류, Three Horizons 분포, 전환점(Tipping Point) 경고, 이상 탐지 결과
>
> **작성 언어**: 한국어 (기술 용어, 고유명사, 약어는 영문 병기 허용)

---

## 사용 지침

1. 이 템플릿을 복사하여 `reports/daily/environmental-scan-{date}.md`로 저장합니다.
2. 모든 `{{...}}` 플레이스홀더를 데이터에 기반한 실제 내용으로 대체합니다.
3. 섹션 헤더(`## N. ...`)는 **절대 변경하지 마세요** — 정확한 문자열이 검증 대상입니다.
4. 서브섹션 헤더(`### N.N ...`)도 번호를 유지하세요.
5. 생성 완료 후, 파일에 `{{`가 남아 있지 않은지 확인합니다.

---

# 일일 네이버 뉴스 환경 스캐닝 보고서

{{REPORT_HEADER_METADATA}}

> **보고서 유형**: WF3 네이버 뉴스 환경스캐닝 (FSSF + Three Horizons + Tipping Point)

---

## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 3 신호)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - 중요도: {{TOP1_IMPORTANCE}}
   - FSSF 유형: {{TOP1_FSSF_TYPE}}
   - 시간 지평: {{TOP1_HORIZON}}
   - 핵심 내용: {{TOP1_SUMMARY}}
   - 전략적 시사점: {{TOP1_IMPLICATION}}

2. **{{TOP2_TITLE}}** ({{TOP2_DOMAIN}})
   - 중요도: {{TOP2_IMPORTANCE}}
   - FSSF 유형: {{TOP2_FSSF_TYPE}}
   - 시간 지평: {{TOP2_HORIZON}}
   - 핵심 내용: {{TOP2_SUMMARY}}
   - 전략적 시사점: {{TOP2_IMPLICATION}}

3. **{{TOP3_TITLE}}** ({{TOP3_DOMAIN}})
   - 중요도: {{TOP3_IMPORTANCE}}
   - FSSF 유형: {{TOP3_FSSF_TYPE}}
   - 시간 지평: {{TOP3_HORIZON}}
   - 핵심 내용: {{TOP3_SUMMARY}}
   - 전략적 시사점: {{TOP3_IMPLICATION}}

### 주요 변화 요약
- 발견된 신규 신호: {{TOTAL_NEW_SIGNALS}}개
- 우선순위 상위 신호: {{TOP_PRIORITY_COUNT}}개
- 주요 영향 도메인: {{DOMAIN_DISTRIBUTION}}

### FSSF 분류 요약

| FSSF 유형 | 신호 수 | 비율 |
|-----------|---------|------|
| Weak Signal (약신호) | {{FSSF_WEAK_SIGNAL_COUNT}} | {{FSSF_WEAK_SIGNAL_PCT}} |
| Emerging Issue (부상 이슈) | {{FSSF_EMERGING_ISSUE_COUNT}} | {{FSSF_EMERGING_ISSUE_PCT}} |
| Trend (추세) | {{FSSF_TREND_COUNT}} | {{FSSF_TREND_PCT}} |
| Megatrend (메가트렌드) | {{FSSF_MEGATREND_COUNT}} | {{FSSF_MEGATREND_PCT}} |
| Driver (동인) | {{FSSF_DRIVER_COUNT}} | {{FSSF_DRIVER_PCT}} |
| Wild Card (와일드카드) | {{FSSF_WILD_CARD_COUNT}} | {{FSSF_WILD_CARD_PCT}} |
| Discontinuity (단절) | {{FSSF_DISCONTINUITY_COUNT}} | {{FSSF_DISCONTINUITY_PCT}} |
| Precursor Event (전조 사건) | {{FSSF_PRECURSOR_COUNT}} | {{FSSF_PRECURSOR_PCT}} |

### Three Horizons 분포

| 시간 지평 | 신호 수 | 비율 | 설명 |
|-----------|---------|------|------|
| H1 (0-2년) | {{H1_COUNT}} | {{H1_PCT}} | 현재 체제 내 변화 |
| H2 (2-7년) | {{H2_COUNT}} | {{H2_PCT}} | 전환기 신호 |
| H3 (7년+) | {{H3_COUNT}} | {{H3_PCT}} | 미래 체제 맹아 |

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. 신규 탐지 신호

{{SECTION2_INTRO}}

---

### 우선순위 1: {{SIGNAL_1_TITLE}}

- **신뢰도**: {{SIGNAL_1_PSST}}
- **FSSF 유형**: {{SIGNAL_1_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_1_HORIZON}}
- **불확실성**: {{SIGNAL_1_UNCERTAINTY}}

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

### 우선순위 2: {{SIGNAL_2_TITLE}}

- **신뢰도**: {{SIGNAL_2_PSST}}
- **FSSF 유형**: {{SIGNAL_2_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_2_HORIZON}}
- **불확실성**: {{SIGNAL_2_UNCERTAINTY}}

1. **분류**: {{SIGNAL_2_CLASSIFICATION}}
2. **출처**: {{SIGNAL_2_SOURCE}}
3. **핵심 사실**: {{SIGNAL_2_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_2_METRICS}}
5. **영향도**: {{SIGNAL_2_IMPACT}}
6. **상세 설명**: {{SIGNAL_2_DETAIL}}
7. **추론**: {{SIGNAL_2_INFERENCE}}
8. **이해관계자**: {{SIGNAL_2_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_2_MONITORING}}

---

### 우선순위 3: {{SIGNAL_3_TITLE}}

- **신뢰도**: {{SIGNAL_3_PSST}}
- **FSSF 유형**: {{SIGNAL_3_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_3_HORIZON}}
- **불확실성**: {{SIGNAL_3_UNCERTAINTY}}

1. **분류**: {{SIGNAL_3_CLASSIFICATION}}
2. **출처**: {{SIGNAL_3_SOURCE}}
3. **핵심 사실**: {{SIGNAL_3_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_3_METRICS}}
5. **영향도**: {{SIGNAL_3_IMPACT}}
6. **상세 설명**: {{SIGNAL_3_DETAIL}}
7. **추론**: {{SIGNAL_3_INFERENCE}}
8. **이해관계자**: {{SIGNAL_3_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_3_MONITORING}}

---

### 우선순위 4: {{SIGNAL_4_TITLE}}

- **신뢰도**: {{SIGNAL_4_PSST}}
- **FSSF 유형**: {{SIGNAL_4_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_4_HORIZON}}
- **불확실성**: {{SIGNAL_4_UNCERTAINTY}}

1. **분류**: {{SIGNAL_4_CLASSIFICATION}}
2. **출처**: {{SIGNAL_4_SOURCE}}
3. **핵심 사실**: {{SIGNAL_4_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_4_METRICS}}
5. **영향도**: {{SIGNAL_4_IMPACT}}
6. **상세 설명**: {{SIGNAL_4_DETAIL}}
7. **추론**: {{SIGNAL_4_INFERENCE}}
8. **이해관계자**: {{SIGNAL_4_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_4_MONITORING}}

---

### 우선순위 5: {{SIGNAL_5_TITLE}}

- **신뢰도**: {{SIGNAL_5_PSST}}
- **FSSF 유형**: {{SIGNAL_5_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_5_HORIZON}}
- **불확실성**: {{SIGNAL_5_UNCERTAINTY}}

1. **분류**: {{SIGNAL_5_CLASSIFICATION}}
2. **출처**: {{SIGNAL_5_SOURCE}}
3. **핵심 사실**: {{SIGNAL_5_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_5_METRICS}}
5. **영향도**: {{SIGNAL_5_IMPACT}}
6. **상세 설명**: {{SIGNAL_5_DETAIL}}
7. **추론**: {{SIGNAL_5_INFERENCE}}
8. **이해관계자**: {{SIGNAL_5_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_5_MONITORING}}

---

### 우선순위 6: {{SIGNAL_6_TITLE}}

- **신뢰도**: {{SIGNAL_6_PSST}}
- **FSSF 유형**: {{SIGNAL_6_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_6_HORIZON}}
- **불확실성**: {{SIGNAL_6_UNCERTAINTY}}

1. **분류**: {{SIGNAL_6_CLASSIFICATION}}
2. **출처**: {{SIGNAL_6_SOURCE}}
3. **핵심 사실**: {{SIGNAL_6_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_6_METRICS}}
5. **영향도**: {{SIGNAL_6_IMPACT}}
6. **상세 설명**: {{SIGNAL_6_DETAIL}}
7. **추론**: {{SIGNAL_6_INFERENCE}}
8. **이해관계자**: {{SIGNAL_6_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_6_MONITORING}}

---

### 우선순위 7: {{SIGNAL_7_TITLE}}

- **신뢰도**: {{SIGNAL_7_PSST}}
- **FSSF 유형**: {{SIGNAL_7_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_7_HORIZON}}
- **불확실성**: {{SIGNAL_7_UNCERTAINTY}}

1. **분류**: {{SIGNAL_7_CLASSIFICATION}}
2. **출처**: {{SIGNAL_7_SOURCE}}
3. **핵심 사실**: {{SIGNAL_7_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_7_METRICS}}
5. **영향도**: {{SIGNAL_7_IMPACT}}
6. **상세 설명**: {{SIGNAL_7_DETAIL}}
7. **추론**: {{SIGNAL_7_INFERENCE}}
8. **이해관계자**: {{SIGNAL_7_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_7_MONITORING}}

---

### 우선순위 8: {{SIGNAL_8_TITLE}}

- **신뢰도**: {{SIGNAL_8_PSST}}
- **FSSF 유형**: {{SIGNAL_8_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_8_HORIZON}}
- **불확실성**: {{SIGNAL_8_UNCERTAINTY}}

1. **분류**: {{SIGNAL_8_CLASSIFICATION}}
2. **출처**: {{SIGNAL_8_SOURCE}}
3. **핵심 사실**: {{SIGNAL_8_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_8_METRICS}}
5. **영향도**: {{SIGNAL_8_IMPACT}}
6. **상세 설명**: {{SIGNAL_8_DETAIL}}
7. **추론**: {{SIGNAL_8_INFERENCE}}
8. **이해관계자**: {{SIGNAL_8_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_8_MONITORING}}

---

### 우선순위 9: {{SIGNAL_9_TITLE}}

- **신뢰도**: {{SIGNAL_9_PSST}}
- **FSSF 유형**: {{SIGNAL_9_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_9_HORIZON}}
- **불확실성**: {{SIGNAL_9_UNCERTAINTY}}

1. **분류**: {{SIGNAL_9_CLASSIFICATION}}
2. **출처**: {{SIGNAL_9_SOURCE}}
3. **핵심 사실**: {{SIGNAL_9_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_9_METRICS}}
5. **영향도**: {{SIGNAL_9_IMPACT}}
6. **상세 설명**: {{SIGNAL_9_DETAIL}}
7. **추론**: {{SIGNAL_9_INFERENCE}}
8. **이해관계자**: {{SIGNAL_9_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_9_MONITORING}}

---

### 우선순위 10: {{SIGNAL_10_TITLE}}

- **신뢰도**: {{SIGNAL_10_PSST}}
- **FSSF 유형**: {{SIGNAL_10_FSSF_TYPE}}
- **시간 지평**: {{SIGNAL_10_HORIZON}}
- **불확실성**: {{SIGNAL_10_UNCERTAINTY}}

1. **분류**: {{SIGNAL_10_CLASSIFICATION}}
2. **출처**: {{SIGNAL_10_SOURCE}}
3. **핵심 사실**: {{SIGNAL_10_KEY_FACT}}
4. **정량 지표**: {{SIGNAL_10_METRICS}}
5. **영향도**: {{SIGNAL_10_IMPACT}}
6. **상세 설명**: {{SIGNAL_10_DETAIL}}
7. **추론**: {{SIGNAL_10_INFERENCE}}
8. **이해관계자**: {{SIGNAL_10_STAKEHOLDERS}}
9. **모니터링 지표**: {{SIGNAL_10_MONITORING}}

---

{{SIGNALS_11_TO_15_CONDENSED}}

---

## 3. 기존 신호 업데이트

### 3.1 강화 추세 (Strengthening)

{{SECTION_3_1_CONTENT}}

### 3.2 약화 추세 (Weakening)

{{SECTION_3_2_CONTENT}}

### 3.3 신호 상태 요약

{{SECTION_3_3_CONTENT}}

---

## 4. 패턴 및 연결고리

### 4.1 신호 간 교차 영향

{{SECTION_4_1_CROSS_IMPACTS}}

### 4.2 떠오르는 테마

{{SECTION_4_2_THEMES}}

### 4.3 FSSF 신호 분류 분포

{{SECTION_4_3_FSSF_DISTRIBUTION}}

| FSSF 유형 | 신호 수 | 대표 신호 | 주요 특징 |
|-----------|---------|-----------|-----------|
| Weak Signal | {{FSSF_DIST_WS_COUNT}} | {{FSSF_DIST_WS_REPR}} | {{FSSF_DIST_WS_NOTE}} |
| Emerging Issue | {{FSSF_DIST_EI_COUNT}} | {{FSSF_DIST_EI_REPR}} | {{FSSF_DIST_EI_NOTE}} |
| Trend | {{FSSF_DIST_TR_COUNT}} | {{FSSF_DIST_TR_REPR}} | {{FSSF_DIST_TR_NOTE}} |
| Megatrend | {{FSSF_DIST_MT_COUNT}} | {{FSSF_DIST_MT_REPR}} | {{FSSF_DIST_MT_NOTE}} |
| Driver | {{FSSF_DIST_DR_COUNT}} | {{FSSF_DIST_DR_REPR}} | {{FSSF_DIST_DR_NOTE}} |
| Wild Card | {{FSSF_DIST_WC_COUNT}} | {{FSSF_DIST_WC_REPR}} | {{FSSF_DIST_WC_NOTE}} |
| Discontinuity | {{FSSF_DIST_DC_COUNT}} | {{FSSF_DIST_DC_REPR}} | {{FSSF_DIST_DC_NOTE}} |
| Precursor Event | {{FSSF_DIST_PE_COUNT}} | {{FSSF_DIST_PE_REPR}} | {{FSSF_DIST_PE_NOTE}} |

### 4.4 Three Horizons 분포

{{SECTION_4_4_THREE_HORIZONS}}

| 시간 지평 | 신호 목록 | 주요 테마 |
|-----------|-----------|-----------|
| H1 (0-2년) | {{H1_SIGNAL_LIST}} | {{H1_THEMES}} |
| H2 (2-7년) | {{H2_SIGNAL_LIST}} | {{H2_THEMES}} |
| H3 (7년+) | {{H3_SIGNAL_LIST}} | {{H3_THEMES}} |

### 4.5 전환점(Tipping Point) 경고

{{SECTION_4_5_TIPPING_POINT}}

| 경고 레벨 | 신호 | 지표 | 근거 |
|-----------|------|------|------|
{{TIPPING_POINT_TABLE}}

### 4.6 이상 탐지 결과

{{SECTION_4_6_ANOMALY}}

| 유형 | 신호 | 이상 지표 | 심각도 |
|------|------|-----------|--------|
{{ANOMALY_TABLE}}

---

## 5. 전략적 시사점

### 5.1 즉시 조치 필요 (0-6개월)

{{SECTION_5_1_IMMEDIATE}}

### 5.2 중기 모니터링 (6-18개월)

{{SECTION_5_2_MIDTERM}}

### 5.3 모니터링 강화 필요 영역

{{SECTION_5_3_WATCH}}

---

## 6. 플러서블 시나리오

{{SECTION_6_SCENARIOS}}

---

## 7. 신뢰도 분석

{{SECTION_7_TRUST_ANALYSIS}}

---

## 8. 부록

### 8.1 크롤링 통계

| 항목 | 값 |
|------|-----|
| 크롤링 일시 | {{CRAWL_DATETIME}} |
| 총 수집 기사 | {{TOTAL_ARTICLES}} |
| 정치 | {{SECTION_100_COUNT}} |
| 경제 | {{SECTION_101_COUNT}} |
| 사회 | {{SECTION_102_COUNT}} |
| 생활문화 | {{SECTION_103_COUNT}} |
| 세계 | {{SECTION_104_COUNT}} |
| IT과학 | {{SECTION_105_COUNT}} |
| S/N Ratio | {{SN_RATIO}} |
| CrawlDefender 전략 | {{CRAWL_STRATEGY_USED}} |

### 8.2 FSSF 분류 방법론

{{SECTION_8_2_FSSF_METHODOLOGY}}

### 8.3 전체 신호 목록

{{SECTION_8_3_FULL_SIGNAL_TABLE}}

### 8.4 출처 목록

{{SECTION_8_4_SOURCE_LIST}}
