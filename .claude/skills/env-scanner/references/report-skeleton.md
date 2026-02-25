# 보고서 스켈레톤 템플릿 (Report Skeleton Template)

> **용도**: report-generator 에이전트가 보고서를 "자유 생성"하지 않고, 이 구조를 **채우는** 방식으로 작성합니다.
> 모든 `{{PLACEHOLDER}}` 토큰은 반드시 실제 내용으로 대체되어야 합니다.
> 미채워진 플레이스홀더가 남으면 **SKEL-001 검증 실패**가 발생합니다.
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

# 일일 환경 스캐닝 보고서

{{REPORT_HEADER_METADATA}}

> **스캔 시간 범위**: {{SCAN_WINDOW_START}} ~ {{SCAN_WINDOW_END}} ({{LOOKBACK_HOURS}}시간)
> **기준 시점 (T₀)**: {{SCAN_ANCHOR_TIMESTAMP}}

---

## 1. 경영진 요약

### 오늘의 핵심 발견 (Top 3 신호)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - 중요도: {{TOP1_IMPORTANCE}}
   - 핵심 내용: {{TOP1_SUMMARY}}
   - 전략적 시사점: {{TOP1_IMPLICATION}}

2. **{{TOP2_TITLE}}** ({{TOP2_DOMAIN}})
   - 중요도: {{TOP2_IMPORTANCE}}
   - 핵심 내용: {{TOP2_SUMMARY}}
   - 전략적 시사점: {{TOP2_IMPLICATION}}

3. **{{TOP3_TITLE}}** ({{TOP3_DOMAIN}})
   - 중요도: {{TOP3_IMPORTANCE}}
   - 핵심 내용: {{TOP3_SUMMARY}}
   - 전략적 시사점: {{TOP3_IMPLICATION}}

### 주요 변화 요약
- 발견된 신규 신호: {{TOTAL_NEW_SIGNALS}}개
- 우선순위 상위 신호: {{TOP_PRIORITY_COUNT}}개
- 주요 영향 도메인: {{DOMAIN_DISTRIBUTION}}

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. 신규 탐지 신호

{{SECTION2_INTRO}}

---

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

### 우선순위 2: {{SIGNAL_2_TITLE}}

- **신뢰도**: {{SIGNAL_2_PSST}}

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

> 활성 추적 스레드: {{EVOLUTION_ACTIVE_THREADS}}개 | 강화: {{EVOLUTION_STRENGTHENING_COUNT}}개 | 약화: {{EVOLUTION_WEAKENING_COUNT}}개 | 소멸: {{EVOLUTION_FADED_COUNT}}개

### 3.1 강화 추세 (Strengthening)

{{EVOLUTION_TABLE_STRENGTHENING}}

{{SECTION_3_1_CONTENT}}

### 3.2 약화 추세 (Weakening)

{{EVOLUTION_TABLE_WEAKENING}}

{{SECTION_3_2_CONTENT}}

### 3.3 신호 상태 요약

| 상태 | 수 | 비율 |
|------|---|------|
| 신규 | {{EVOLUTION_NEW_COUNT}} | {{EVOLUTION_NEW_PCT}} |
| 강화 | {{EVOLUTION_STRENGTHENING_COUNT}} | {{EVOLUTION_STRENGTHENING_PCT}} |
| 반복 등장 | {{EVOLUTION_RECURRING_COUNT}} | {{EVOLUTION_RECURRING_PCT}} |
| 약화 | {{EVOLUTION_WEAKENING_COUNT}} | {{EVOLUTION_WEAKENING_PCT}} |
| 소멸 | {{EVOLUTION_FADED_COUNT}} | {{EVOLUTION_FADED_PCT}} |

{{SECTION_3_3_CONTENT}}

---

## 4. 패턴 및 연결고리

### 4.1 신호 간 교차 영향

{{SECTION_4_1_CROSS_IMPACTS}}

### 4.2 떠오르는 테마

{{SECTION_4_2_THEMES}}

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

{{SECTION_7_TRUST_ANALYSIS}}

---

## 8. 부록

{{SECTION_8_APPENDIX}}
