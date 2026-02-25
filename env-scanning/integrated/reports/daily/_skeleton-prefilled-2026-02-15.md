# 통합 보고서 스켈레톤 템플릿 (Integrated Report Skeleton Template)

> **용도**: report-merger 에이전트가 보고서를 "자유 생성"하지 않고, 이 구조를 **채우는** 방식으로 작성합니다.
> 모든 `{{PLACEHOLDER}}` 토큰은 반드시 실제 내용으로 대체되어야 합니다.
> 미채워진 플레이스홀더가 남으면 **SKEL-001 검증 실패**가 발생합니다.
>
> **중요**: 이 스켈레톤은 WF1(일반), WF2(arXiv), WF3(네이버 뉴스) 세 독립 워크플로우의 결과를
> 통합한 보고서용입니다. 개별 워크플로우 보고서에는 `report-skeleton.md`(WF1/WF2) 또는 `naver-report-skeleton.md`(WF3)를 사용하세요.
>
> **작성 언어**: 한국어 (기술 용어, 고유명사, 약어는 영문 병기 허용)

---

## 사용 지침

1. 이 템플릿을 복사하여 `integrated/reports/daily/integrated-scan-{date}.md`로 저장합니다.
2. 모든 `{{...}}` 플레이스홀더를 데이터에 기반한 실제 내용으로 대체합니다.
3. 섹션 헤더(`## N. ...`)는 **절대 변경하지 마세요** — 정확한 문자열이 검증 대상입니다.
4. 서브섹션 헤더(`### N.N ...`)도 번호를 유지하세요.
5. 모든 신호에 `[WF1]`, `[WF2]`, 또는 `[WF3]` 소스 태그를 반드시 포함하세요.
6. 생성 완료 후, 파일에 `{{`가 남아 있지 않은지 확인합니다.

---

# 통합 일일 환경 스캐닝 보고서

{{REPORT_HEADER_METADATA}}

> **보고서 유형**: 통합 보고서 (WF1 일반 환경스캐닝 + WF2 arXiv 학술 심층스캐닝 + WF3 네이버 뉴스 환경스캐닝)
> **스캔 시간 범위**: 2026년 02월 13일 01:58 UTC ~ 2026년 02월 15일 01:58 UTC
> **기준 시점 (T₀)**: 2026년 02월 15일 01:58:05 UTC
> **개별 스캔 범위**: WF1 24시간 | WF2 48시간 | WF3 24시간

---

## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 5 신호)

1. **{{TOP1_TAG}} {{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - 중요도: {{TOP1_IMPORTANCE}}
   - 핵심 내용: {{TOP1_SUMMARY}}
   - 전략적 시사점: {{TOP1_IMPLICATION}}

2. **{{TOP2_TAG}} {{TOP2_TITLE}}** ({{TOP2_DOMAIN}})
   - 중요도: {{TOP2_IMPORTANCE}}
   - 핵심 내용: {{TOP2_SUMMARY}}
   - 전략적 시사점: {{TOP2_IMPLICATION}}

3. **{{TOP3_TAG}} {{TOP3_TITLE}}** ({{TOP3_DOMAIN}})
   - 중요도: {{TOP3_IMPORTANCE}}
   - 핵심 내용: {{TOP3_SUMMARY}}
   - 전략적 시사점: {{TOP3_IMPLICATION}}

4. **{{TOP4_TAG}} {{TOP4_TITLE}}** ({{TOP4_DOMAIN}})
   - 중요도: {{TOP4_IMPORTANCE}}
   - 핵심 내용: {{TOP4_SUMMARY}}
   - 전략적 시사점: {{TOP4_IMPLICATION}}

5. **{{TOP5_TAG}} {{TOP5_TITLE}}** ({{TOP5_DOMAIN}})
   - 중요도: {{TOP5_IMPORTANCE}}
   - 핵심 내용: {{TOP5_SUMMARY}}
   - 전략적 시사점: {{TOP5_IMPLICATION}}

### 주요 변화 요약

- **WF1 (일반 환경스캐닝)**: {{WF1_TOTAL_SIGNALS}}개 신호 수집
- **WF2 (arXiv 학술 심층)**: {{WF2_TOTAL_SIGNALS}}개 신호 수집
- **WF3 (네이버 뉴스)**: {{WF3_TOTAL_SIGNALS}}개 신호 수집
- **통합 신호 풀**: {{TOTAL_COMBINED_SIGNALS}}개
- **상위 20개 신호 선정** (pSST 통합 순위 기준)
- 주요 영향 도메인: {{DOMAIN_DISTRIBUTION}}

### 워크플로우 교차 하이라이트

{{CROSS_WORKFLOW_HEADLINE}}

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. 신규 탐지 신호

{{SECTION2_INTRO}}

---

### 통합 우선순위 1: {{INT_SIGNAL_1_TAG}} {{INT_SIGNAL_1_TITLE}}

- **신뢰도**: {{INT_SIGNAL_1_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_1_ORIGIN}}

1. **분류**: {{INT_SIGNAL_1_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_1_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_1_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_1_METRICS}}
5. **영향도**: {{INT_SIGNAL_1_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_1_DETAIL}}
7. **추론**: {{INT_SIGNAL_1_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_1_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_1_MONITORING}}

---

### 통합 우선순위 2: {{INT_SIGNAL_2_TAG}} {{INT_SIGNAL_2_TITLE}}

- **신뢰도**: {{INT_SIGNAL_2_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_2_ORIGIN}}

1. **분류**: {{INT_SIGNAL_2_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_2_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_2_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_2_METRICS}}
5. **영향도**: {{INT_SIGNAL_2_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_2_DETAIL}}
7. **추론**: {{INT_SIGNAL_2_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_2_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_2_MONITORING}}

---

### 통합 우선순위 3: {{INT_SIGNAL_3_TAG}} {{INT_SIGNAL_3_TITLE}}

- **신뢰도**: {{INT_SIGNAL_3_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_3_ORIGIN}}

1. **분류**: {{INT_SIGNAL_3_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_3_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_3_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_3_METRICS}}
5. **영향도**: {{INT_SIGNAL_3_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_3_DETAIL}}
7. **추론**: {{INT_SIGNAL_3_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_3_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_3_MONITORING}}

---

### 통합 우선순위 4: {{INT_SIGNAL_4_TAG}} {{INT_SIGNAL_4_TITLE}}

- **신뢰도**: {{INT_SIGNAL_4_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_4_ORIGIN}}

1. **분류**: {{INT_SIGNAL_4_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_4_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_4_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_4_METRICS}}
5. **영향도**: {{INT_SIGNAL_4_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_4_DETAIL}}
7. **추론**: {{INT_SIGNAL_4_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_4_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_4_MONITORING}}

---

### 통합 우선순위 5: {{INT_SIGNAL_5_TAG}} {{INT_SIGNAL_5_TITLE}}

- **신뢰도**: {{INT_SIGNAL_5_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_5_ORIGIN}}

1. **분류**: {{INT_SIGNAL_5_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_5_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_5_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_5_METRICS}}
5. **영향도**: {{INT_SIGNAL_5_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_5_DETAIL}}
7. **추론**: {{INT_SIGNAL_5_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_5_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_5_MONITORING}}

---

### 통합 우선순위 6: {{INT_SIGNAL_6_TAG}} {{INT_SIGNAL_6_TITLE}}

- **신뢰도**: {{INT_SIGNAL_6_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_6_ORIGIN}}

1. **분류**: {{INT_SIGNAL_6_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_6_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_6_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_6_METRICS}}
5. **영향도**: {{INT_SIGNAL_6_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_6_DETAIL}}
7. **추론**: {{INT_SIGNAL_6_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_6_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_6_MONITORING}}

---

### 통합 우선순위 7: {{INT_SIGNAL_7_TAG}} {{INT_SIGNAL_7_TITLE}}

- **신뢰도**: {{INT_SIGNAL_7_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_7_ORIGIN}}

1. **분류**: {{INT_SIGNAL_7_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_7_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_7_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_7_METRICS}}
5. **영향도**: {{INT_SIGNAL_7_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_7_DETAIL}}
7. **추론**: {{INT_SIGNAL_7_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_7_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_7_MONITORING}}

---

### 통합 우선순위 8: {{INT_SIGNAL_8_TAG}} {{INT_SIGNAL_8_TITLE}}

- **신뢰도**: {{INT_SIGNAL_8_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_8_ORIGIN}}

1. **분류**: {{INT_SIGNAL_8_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_8_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_8_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_8_METRICS}}
5. **영향도**: {{INT_SIGNAL_8_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_8_DETAIL}}
7. **추론**: {{INT_SIGNAL_8_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_8_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_8_MONITORING}}

---

### 통합 우선순위 9: {{INT_SIGNAL_9_TAG}} {{INT_SIGNAL_9_TITLE}}

- **신뢰도**: {{INT_SIGNAL_9_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_9_ORIGIN}}

1. **분류**: {{INT_SIGNAL_9_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_9_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_9_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_9_METRICS}}
5. **영향도**: {{INT_SIGNAL_9_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_9_DETAIL}}
7. **추론**: {{INT_SIGNAL_9_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_9_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_9_MONITORING}}

---

### 통합 우선순위 10: {{INT_SIGNAL_10_TAG}} {{INT_SIGNAL_10_TITLE}}

- **신뢰도**: {{INT_SIGNAL_10_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_10_ORIGIN}}

1. **분류**: {{INT_SIGNAL_10_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_10_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_10_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_10_METRICS}}
5. **영향도**: {{INT_SIGNAL_10_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_10_DETAIL}}
7. **추론**: {{INT_SIGNAL_10_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_10_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_10_MONITORING}}

---

### 통합 우선순위 11: {{INT_SIGNAL_11_TAG}} {{INT_SIGNAL_11_TITLE}}

- **신뢰도**: {{INT_SIGNAL_11_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_11_ORIGIN}}

1. **분류**: {{INT_SIGNAL_11_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_11_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_11_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_11_METRICS}}
5. **영향도**: {{INT_SIGNAL_11_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_11_DETAIL}}
7. **추론**: {{INT_SIGNAL_11_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_11_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_11_MONITORING}}

---

### 통합 우선순위 12: {{INT_SIGNAL_12_TAG}} {{INT_SIGNAL_12_TITLE}}

- **신뢰도**: {{INT_SIGNAL_12_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_12_ORIGIN}}

1. **분류**: {{INT_SIGNAL_12_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_12_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_12_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_12_METRICS}}
5. **영향도**: {{INT_SIGNAL_12_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_12_DETAIL}}
7. **추론**: {{INT_SIGNAL_12_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_12_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_12_MONITORING}}

---

### 통합 우선순위 13: {{INT_SIGNAL_13_TAG}} {{INT_SIGNAL_13_TITLE}}

- **신뢰도**: {{INT_SIGNAL_13_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_13_ORIGIN}}

1. **분류**: {{INT_SIGNAL_13_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_13_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_13_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_13_METRICS}}
5. **영향도**: {{INT_SIGNAL_13_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_13_DETAIL}}
7. **추론**: {{INT_SIGNAL_13_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_13_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_13_MONITORING}}

---

### 통합 우선순위 14: {{INT_SIGNAL_14_TAG}} {{INT_SIGNAL_14_TITLE}}

- **신뢰도**: {{INT_SIGNAL_14_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_14_ORIGIN}}

1. **분류**: {{INT_SIGNAL_14_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_14_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_14_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_14_METRICS}}
5. **영향도**: {{INT_SIGNAL_14_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_14_DETAIL}}
7. **추론**: {{INT_SIGNAL_14_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_14_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_14_MONITORING}}

---

### 통합 우선순위 15: {{INT_SIGNAL_15_TAG}} {{INT_SIGNAL_15_TITLE}}

- **신뢰도**: {{INT_SIGNAL_15_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_15_ORIGIN}}

1. **분류**: {{INT_SIGNAL_15_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_15_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_15_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_15_METRICS}}
5. **영향도**: {{INT_SIGNAL_15_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_15_DETAIL}}
7. **추론**: {{INT_SIGNAL_15_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_15_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_15_MONITORING}}

---

### 통합 우선순위 16: {{INT_SIGNAL_16_TAG}} {{INT_SIGNAL_16_TITLE}}

- **신뢰도**: {{INT_SIGNAL_16_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_16_ORIGIN}}

1. **분류**: {{INT_SIGNAL_16_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_16_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_16_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_16_METRICS}}
5. **영향도**: {{INT_SIGNAL_16_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_16_DETAIL}}
7. **추론**: {{INT_SIGNAL_16_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_16_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_16_MONITORING}}

---

### 통합 우선순위 17: {{INT_SIGNAL_17_TAG}} {{INT_SIGNAL_17_TITLE}}

- **신뢰도**: {{INT_SIGNAL_17_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_17_ORIGIN}}

1. **분류**: {{INT_SIGNAL_17_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_17_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_17_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_17_METRICS}}
5. **영향도**: {{INT_SIGNAL_17_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_17_DETAIL}}
7. **추론**: {{INT_SIGNAL_17_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_17_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_17_MONITORING}}

---

### 통합 우선순위 18: {{INT_SIGNAL_18_TAG}} {{INT_SIGNAL_18_TITLE}}

- **신뢰도**: {{INT_SIGNAL_18_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_18_ORIGIN}}

1. **분류**: {{INT_SIGNAL_18_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_18_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_18_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_18_METRICS}}
5. **영향도**: {{INT_SIGNAL_18_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_18_DETAIL}}
7. **추론**: {{INT_SIGNAL_18_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_18_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_18_MONITORING}}

---

### 통합 우선순위 19: {{INT_SIGNAL_19_TAG}} {{INT_SIGNAL_19_TITLE}}

- **신뢰도**: {{INT_SIGNAL_19_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_19_ORIGIN}}

1. **분류**: {{INT_SIGNAL_19_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_19_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_19_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_19_METRICS}}
5. **영향도**: {{INT_SIGNAL_19_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_19_DETAIL}}
7. **추론**: {{INT_SIGNAL_19_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_19_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_19_MONITORING}}

---

### 통합 우선순위 20: {{INT_SIGNAL_20_TAG}} {{INT_SIGNAL_20_TITLE}}

- **신뢰도**: {{INT_SIGNAL_20_PSST}}
- **원본 워크플로우**: {{INT_SIGNAL_20_ORIGIN}}

1. **분류**: {{INT_SIGNAL_20_CLASSIFICATION}}
2. **출처**: {{INT_SIGNAL_20_SOURCE}}
3. **핵심 사실**: {{INT_SIGNAL_20_KEY_FACT}}
4. **정량 지표**: {{INT_SIGNAL_20_METRICS}}
5. **영향도**: {{INT_SIGNAL_20_IMPACT}}
6. **상세 설명**: {{INT_SIGNAL_20_DETAIL}}
7. **추론**: {{INT_SIGNAL_20_INFERENCE}}
8. **이해관계자**: {{INT_SIGNAL_20_STAKEHOLDERS}}
9. **모니터링 지표**: {{INT_SIGNAL_20_MONITORING}}

---

{{SIGNALS_21_PLUS_CONDENSED}}

---

## 3. 기존 신호 업데이트

> 활성 추적 스레드: 582개 | 강화: 0개 | 약화: 0개 | 소멸: 0개

### 3.1 강화 추세 (Strengthening)

해당 없음

{{SECTION_3_1_CONTENT}}

### 3.2 약화 추세 (Weakening)

해당 없음

{{SECTION_3_2_CONTENT}}

### 3.3 신호 상태 요약

| 상태 | 수 | 비율 |
|------|---|------|
| 신규 | 582 | 100% |
| 강화 | 0 | 0% |
| 반복 등장 | 1 | 0% |
| 약화 | 0 | 0% |
| 소멸 | 0 | — |

{{SECTION_3_3_CONTENT}}

---

## 4. 패턴 및 연결고리

### 4.1 신호 간 교차 영향

{{SECTION_4_1_CROSS_IMPACTS}}

### 4.2 떠오르는 테마

{{SECTION_4_2_THEMES}}

### 4.3 워크플로우 교차 분석 (Cross-Workflow Analysis)

#### 상호 강화 신호 (Reinforced Signals)

{{SECTION_4_3_REINFORCED}}

#### 학술 선행 신호 (Academic Early Signals)

{{SECTION_4_3_ACADEMIC_EARLY}}

#### 미디어 선행 신호 (Media-First Signals)

{{SECTION_4_3_MEDIA_FIRST}}

#### 워크플로우 간 긴장/모순 (Cross-Workflow Tensions)

{{SECTION_4_3_TENSIONS}}

#### WF3 고유 신호 (Naver-Exclusive Signals)

{{SECTION_4_3_NAVER_EXCLUSIVE}}

#### 시간축 교차 확인 (Temporal Cross-Validation)

시간축 교차 데이터 없음

{{SECTION_4_3_TEMPORAL_CROSS}}

---

## 5. 전략적 시사점

### 5.1 즉시 조치 필요 (0-6개월)

{{SECTION_5_1_IMMEDIATE}}

### 5.2 중기 모니터링 (6-18개월)

{{SECTION_5_2_MIDTERM}}

### 5.3 모니터링 강화 필요 영역

{{SECTION_5_3_WATCH}}

---

## 6. Plausible Scenarios(개연성 있는 시나리오)

{{SECTION_6_SCENARIOS}}

---

## 7. 신뢰도 분석

### 7.1 통합 pSST 등급 분포

{{SECTION_7_1_UNIFIED_DISTRIBUTION}}

### 7.2 워크플로우별 pSST 비교

{{SECTION_7_2_WORKFLOW_COMPARISON}}

### 7.3 자동 승인 가능 목록 (Grade A)

{{SECTION_7_3_AUTO_APPROVE}}

### 7.4 검토 필요 목록 (Grade C/D)

{{SECTION_7_4_REVIEW_NEEDED}}

### 7.5 차원별 평균 분석

{{SECTION_7_5_DIMENSION_ANALYSIS}}

---

## 8. 부록

### 8.1 전체 신호 목록

{{SECTION_8_1_FULL_SIGNAL_TABLE}}

### 8.2 출처 목록

{{SECTION_8_2_SOURCE_LIST}}

### 8.3 방법론

{{SECTION_8_3_METHODOLOGY}}

### 8.4 워크플로우 실행 요약

| 항목 | WF1 (일반) | WF2 (arXiv) | WF3 (네이버) | 통합 |
|------|-----------|-------------|-------------|------|
| 소스 수 | {{WF1_SOURCE_COUNT}} | 1 (arXiv) | 1 (NaverNews) | {{TOTAL_SOURCE_COUNT}} |
| 수집 신호 | {{WF1_SIGNAL_COUNT}} | {{WF2_SIGNAL_COUNT}} | {{WF3_SIGNAL_COUNT}} | {{TOTAL_SIGNAL_COUNT}} |
| 중복 제거 후 | {{WF1_DEDUP_COUNT}} | {{WF2_DEDUP_COUNT}} | {{WF3_DEDUP_COUNT}} | {{TOTAL_DEDUP_COUNT}} |
| 상위 신호 | {{WF1_TOP_COUNT}}개 | {{WF2_TOP_COUNT}}개 | {{WF3_TOP_COUNT}}개 | 20개 |
| 평균 pSST | {{WF1_AVG_PSST}} | {{WF2_AVG_PSST}} | {{WF3_AVG_PSST}} | {{TOTAL_AVG_PSST}} |
| 실행 시간 | {{WF1_DURATION}} | {{WF2_DURATION}} | {{WF3_DURATION}} | {{TOTAL_DURATION}} |
