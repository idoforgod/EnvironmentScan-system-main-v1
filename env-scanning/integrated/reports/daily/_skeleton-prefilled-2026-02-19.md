# Integrated Report Skeleton Template

> **Purpose**: The report-merger agent fills this structure rather than generating free-form reports.
> All `{{PLACEHOLDER}}` tokens must be replaced with actual content.
> Unfilled placeholders will trigger **SKEL-001 validation failure**.
>
> **Important**: This skeleton integrates results from three independent workflows:
> WF1 (General), WF2 (arXiv), WF3 (Naver News). For individual reports, use `report-skeleton.md` or `naver-report-skeleton.md`.
>
> **Language**: English (technical terms and acronyms preserved as-is)

---

## Usage Instructions

1. Copy this template to `integrated/reports/daily/integrated-scan-{date}.md`.
2. Replace all `{{...}}` placeholders with data-driven content.
3. Section headers (`## N. ...`) must **never be modified** — exact strings are validated.
4. Subsection headers (`### N.N ...`) must retain their numbering.
5. All signals must include `[WF1]`, `[WF2]`, or `[WF3]` source tags.
6. After generation, verify no `{{` tokens remain in the file.

---

# Integrated Daily Environmental Scanning Report

{{REPORT_HEADER_METADATA}}

> **Report Type**: Integrated Report (WF1 General + WF2 arXiv Academic + WF3 Naver News)
> **Scan Window**: February 18, 2026 00:44 UTC ~ February 20, 2026 00:44 UTC
> **Anchor Time (T₀)**: February 20, 2026 00:44:56 UTC
> **Per-Workflow Scan Range**: WF1 24 hours | WF2 48 hours | WF3 24 hours

---

## 1. Executive Summary

### Today's Key Findings (Top 5 Signals)

1. **{{TOP1_TAG}} {{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - Importance: {{TOP1_IMPORTANCE}}
   - Key Content: {{TOP1_SUMMARY}}
   - Strategic Implications: {{TOP1_IMPLICATION}}

2. **{{TOP2_TAG}} {{TOP2_TITLE}}** ({{TOP2_DOMAIN}})
   - Importance: {{TOP2_IMPORTANCE}}
   - Key Content: {{TOP2_SUMMARY}}
   - Strategic Implications: {{TOP2_IMPLICATION}}

3. **{{TOP3_TAG}} {{TOP3_TITLE}}** ({{TOP3_DOMAIN}})
   - Importance: {{TOP3_IMPORTANCE}}
   - Key Content: {{TOP3_SUMMARY}}
   - Strategic Implications: {{TOP3_IMPLICATION}}

4. **{{TOP4_TAG}} {{TOP4_TITLE}}** ({{TOP4_DOMAIN}})
   - Importance: {{TOP4_IMPORTANCE}}
   - Key Content: {{TOP4_SUMMARY}}
   - Strategic Implications: {{TOP4_IMPLICATION}}

5. **{{TOP5_TAG}} {{TOP5_TITLE}}** ({{TOP5_DOMAIN}})
   - Importance: {{TOP5_IMPORTANCE}}
   - Key Content: {{TOP5_SUMMARY}}
   - Strategic Implications: {{TOP5_IMPLICATION}}

### Key Changes Summary

- **WF1 (General Environmental Scanning)**: {{WF1_TOTAL_SIGNALS}} signals collected
- **WF2 (arXiv Academic Deep Scan)**: {{WF2_TOTAL_SIGNALS}} signals collected
- **WF3 (Naver News)**: {{WF3_TOTAL_SIGNALS}} signals collected
- **Integrated Signal Pool**: {{TOTAL_COMBINED_SIGNALS}}
- **Top 20 Signals Selected** (by unified pSST ranking)
- Major impact domains: {{DOMAIN_DISTRIBUTION}}

### Cross-Workflow Highlights

{{CROSS_WORKFLOW_HEADLINE}}

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. Newly Detected Signals

{{SECTION2_INTRO}}

---

### Integrated Priority 1: {{INT_SIGNAL_1_TAG}} {{INT_SIGNAL_1_TITLE}}

- **Confidence**: {{INT_SIGNAL_1_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_1_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_1_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_1_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_1_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_1_METRICS}}
5. **Impact**: {{INT_SIGNAL_1_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_1_DETAIL}}
7. **Inference**: {{INT_SIGNAL_1_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_1_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_1_MONITORING}}

---

### Integrated Priority 2: {{INT_SIGNAL_2_TAG}} {{INT_SIGNAL_2_TITLE}}

- **Confidence**: {{INT_SIGNAL_2_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_2_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_2_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_2_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_2_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_2_METRICS}}
5. **Impact**: {{INT_SIGNAL_2_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_2_DETAIL}}
7. **Inference**: {{INT_SIGNAL_2_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_2_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_2_MONITORING}}

---

### Integrated Priority 3: {{INT_SIGNAL_3_TAG}} {{INT_SIGNAL_3_TITLE}}

- **Confidence**: {{INT_SIGNAL_3_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_3_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_3_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_3_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_3_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_3_METRICS}}
5. **Impact**: {{INT_SIGNAL_3_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_3_DETAIL}}
7. **Inference**: {{INT_SIGNAL_3_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_3_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_3_MONITORING}}

---

### Integrated Priority 4: {{INT_SIGNAL_4_TAG}} {{INT_SIGNAL_4_TITLE}}

- **Confidence**: {{INT_SIGNAL_4_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_4_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_4_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_4_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_4_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_4_METRICS}}
5. **Impact**: {{INT_SIGNAL_4_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_4_DETAIL}}
7. **Inference**: {{INT_SIGNAL_4_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_4_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_4_MONITORING}}

---

### Integrated Priority 5: {{INT_SIGNAL_5_TAG}} {{INT_SIGNAL_5_TITLE}}

- **Confidence**: {{INT_SIGNAL_5_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_5_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_5_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_5_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_5_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_5_METRICS}}
5. **Impact**: {{INT_SIGNAL_5_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_5_DETAIL}}
7. **Inference**: {{INT_SIGNAL_5_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_5_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_5_MONITORING}}

---

### Integrated Priority 6: {{INT_SIGNAL_6_TAG}} {{INT_SIGNAL_6_TITLE}}

- **Confidence**: {{INT_SIGNAL_6_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_6_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_6_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_6_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_6_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_6_METRICS}}
5. **Impact**: {{INT_SIGNAL_6_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_6_DETAIL}}
7. **Inference**: {{INT_SIGNAL_6_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_6_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_6_MONITORING}}

---

### Integrated Priority 7: {{INT_SIGNAL_7_TAG}} {{INT_SIGNAL_7_TITLE}}

- **Confidence**: {{INT_SIGNAL_7_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_7_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_7_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_7_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_7_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_7_METRICS}}
5. **Impact**: {{INT_SIGNAL_7_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_7_DETAIL}}
7. **Inference**: {{INT_SIGNAL_7_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_7_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_7_MONITORING}}

---

### Integrated Priority 8: {{INT_SIGNAL_8_TAG}} {{INT_SIGNAL_8_TITLE}}

- **Confidence**: {{INT_SIGNAL_8_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_8_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_8_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_8_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_8_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_8_METRICS}}
5. **Impact**: {{INT_SIGNAL_8_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_8_DETAIL}}
7. **Inference**: {{INT_SIGNAL_8_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_8_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_8_MONITORING}}

---

### Integrated Priority 9: {{INT_SIGNAL_9_TAG}} {{INT_SIGNAL_9_TITLE}}

- **Confidence**: {{INT_SIGNAL_9_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_9_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_9_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_9_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_9_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_9_METRICS}}
5. **Impact**: {{INT_SIGNAL_9_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_9_DETAIL}}
7. **Inference**: {{INT_SIGNAL_9_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_9_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_9_MONITORING}}

---

### Integrated Priority 10: {{INT_SIGNAL_10_TAG}} {{INT_SIGNAL_10_TITLE}}

- **Confidence**: {{INT_SIGNAL_10_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_10_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_10_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_10_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_10_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_10_METRICS}}
5. **Impact**: {{INT_SIGNAL_10_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_10_DETAIL}}
7. **Inference**: {{INT_SIGNAL_10_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_10_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_10_MONITORING}}

---

### Integrated Priority 11: {{INT_SIGNAL_11_TAG}} {{INT_SIGNAL_11_TITLE}}

- **Confidence**: {{INT_SIGNAL_11_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_11_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_11_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_11_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_11_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_11_METRICS}}
5. **Impact**: {{INT_SIGNAL_11_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_11_DETAIL}}
7. **Inference**: {{INT_SIGNAL_11_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_11_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_11_MONITORING}}

---

### Integrated Priority 12: {{INT_SIGNAL_12_TAG}} {{INT_SIGNAL_12_TITLE}}

- **Confidence**: {{INT_SIGNAL_12_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_12_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_12_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_12_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_12_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_12_METRICS}}
5. **Impact**: {{INT_SIGNAL_12_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_12_DETAIL}}
7. **Inference**: {{INT_SIGNAL_12_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_12_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_12_MONITORING}}

---

### Integrated Priority 13: {{INT_SIGNAL_13_TAG}} {{INT_SIGNAL_13_TITLE}}

- **Confidence**: {{INT_SIGNAL_13_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_13_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_13_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_13_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_13_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_13_METRICS}}
5. **Impact**: {{INT_SIGNAL_13_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_13_DETAIL}}
7. **Inference**: {{INT_SIGNAL_13_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_13_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_13_MONITORING}}

---

### Integrated Priority 14: {{INT_SIGNAL_14_TAG}} {{INT_SIGNAL_14_TITLE}}

- **Confidence**: {{INT_SIGNAL_14_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_14_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_14_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_14_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_14_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_14_METRICS}}
5. **Impact**: {{INT_SIGNAL_14_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_14_DETAIL}}
7. **Inference**: {{INT_SIGNAL_14_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_14_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_14_MONITORING}}

---

### Integrated Priority 15: {{INT_SIGNAL_15_TAG}} {{INT_SIGNAL_15_TITLE}}

- **Confidence**: {{INT_SIGNAL_15_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_15_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_15_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_15_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_15_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_15_METRICS}}
5. **Impact**: {{INT_SIGNAL_15_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_15_DETAIL}}
7. **Inference**: {{INT_SIGNAL_15_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_15_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_15_MONITORING}}

---

### Integrated Priority 16: {{INT_SIGNAL_16_TAG}} {{INT_SIGNAL_16_TITLE}}

- **Confidence**: {{INT_SIGNAL_16_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_16_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_16_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_16_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_16_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_16_METRICS}}
5. **Impact**: {{INT_SIGNAL_16_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_16_DETAIL}}
7. **Inference**: {{INT_SIGNAL_16_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_16_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_16_MONITORING}}

---

### Integrated Priority 17: {{INT_SIGNAL_17_TAG}} {{INT_SIGNAL_17_TITLE}}

- **Confidence**: {{INT_SIGNAL_17_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_17_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_17_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_17_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_17_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_17_METRICS}}
5. **Impact**: {{INT_SIGNAL_17_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_17_DETAIL}}
7. **Inference**: {{INT_SIGNAL_17_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_17_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_17_MONITORING}}

---

### Integrated Priority 18: {{INT_SIGNAL_18_TAG}} {{INT_SIGNAL_18_TITLE}}

- **Confidence**: {{INT_SIGNAL_18_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_18_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_18_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_18_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_18_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_18_METRICS}}
5. **Impact**: {{INT_SIGNAL_18_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_18_DETAIL}}
7. **Inference**: {{INT_SIGNAL_18_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_18_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_18_MONITORING}}

---

### Integrated Priority 19: {{INT_SIGNAL_19_TAG}} {{INT_SIGNAL_19_TITLE}}

- **Confidence**: {{INT_SIGNAL_19_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_19_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_19_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_19_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_19_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_19_METRICS}}
5. **Impact**: {{INT_SIGNAL_19_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_19_DETAIL}}
7. **Inference**: {{INT_SIGNAL_19_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_19_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_19_MONITORING}}

---

### Integrated Priority 20: {{INT_SIGNAL_20_TAG}} {{INT_SIGNAL_20_TITLE}}

- **Confidence**: {{INT_SIGNAL_20_PSST}}
- **Origin Workflow**: {{INT_SIGNAL_20_ORIGIN}}

1. **Classification**: {{INT_SIGNAL_20_CLASSIFICATION}}
2. **Source**: {{INT_SIGNAL_20_SOURCE}}
3. **Key Facts**: {{INT_SIGNAL_20_KEY_FACT}}
4. **Quantitative Metrics**: {{INT_SIGNAL_20_METRICS}}
5. **Impact**: {{INT_SIGNAL_20_IMPACT}}
6. **Detailed Description**: {{INT_SIGNAL_20_DETAIL}}
7. **Inference**: {{INT_SIGNAL_20_INFERENCE}}
8. **Stakeholders**: {{INT_SIGNAL_20_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{INT_SIGNAL_20_MONITORING}}

---

{{SIGNALS_21_PLUS_CONDENSED}}

---

## 3. Existing Signal Updates

> Active tracking threads: 0 | Strengthening: 0 | Weakening: 0 | Faded: 0

### 3.1 Strengthening Trends

N/A

{{SECTION_3_1_CONTENT}}

### 3.2 Weakening Trends

N/A

{{SECTION_3_2_CONTENT}}

### 3.3 Signal Status Summary

| Status | Count | Ratio |
|------|---|------|
| New | 0 | — |
| Strengthening | 0 | — |
| Recurring | 0 | — |
| Weakening | 0 | — |
| Faded | 0 | — |

{{SECTION_3_3_CONTENT}}

---

## 4. Patterns and Connections

### 4.1 Cross-Impact Between Signals

{{SECTION_4_1_CROSS_IMPACTS}}

### 4.2 Emerging Themes

{{SECTION_4_2_THEMES}}

### 4.3 Cross-Workflow Analysis

#### Reinforced Signals

{{SECTION_4_3_REINFORCED}}

#### Academic Early Signals

{{SECTION_4_3_ACADEMIC_EARLY}}

#### Media-First Signals

{{SECTION_4_3_MEDIA_FIRST}}

#### Cross-Workflow Tensions

{{SECTION_4_3_TENSIONS}}

#### Naver-Exclusive Signals

{{SECTION_4_3_NAVER_EXCLUSIVE}}

#### Temporal Cross-Validation

No cross-evolution data

{{SECTION_4_3_TEMPORAL_CROSS}}

---

## 5. Strategic Implications

### 5.1 Immediate Actions Required (0-6 months)

{{SECTION_5_1_IMMEDIATE}}

### 5.2 Medium-term Monitoring (6-18 months)

{{SECTION_5_2_MIDTERM}}

### 5.3 Areas Requiring Enhanced Monitoring

{{SECTION_5_3_WATCH}}

---

## 6. Plausible Scenarios

{{SECTION_6_SCENARIOS}}

---

## 7. Confidence Analysis

### 7.1 Unified pSST Grade Distribution

{{SECTION_7_1_UNIFIED_DISTRIBUTION}}

### 7.2 Per-Workflow pSST Comparison

{{SECTION_7_2_WORKFLOW_COMPARISON}}

### 7.3 Auto-Approvable List (Grade A)

{{SECTION_7_3_AUTO_APPROVE}}

### 7.4 Review Required List (Grade C/D)

{{SECTION_7_4_REVIEW_NEEDED}}

### 7.5 Per-Dimension Average Analysis

{{SECTION_7_5_DIMENSION_ANALYSIS}}

---

## 8. Appendix

### 8.1 Full Signal List

{{SECTION_8_1_FULL_SIGNAL_TABLE}}

### 8.2 Source List

{{SECTION_8_2_SOURCE_LIST}}

### 8.3 Methodology

{{SECTION_8_3_METHODOLOGY}}

### 8.4 Workflow Execution Summary

| Item | WF1 (General) | WF2 (arXiv) | WF3 (Naver) | Integrated |
|------|-----------|-------------|-------------|------|
| Source Count | {{WF1_SOURCE_COUNT}} | 1 (arXiv) | 1 (NaverNews) | {{TOTAL_SOURCE_COUNT}} |
| Collected Signals | {{WF1_SIGNAL_COUNT}} | {{WF2_SIGNAL_COUNT}} | {{WF3_SIGNAL_COUNT}} | {{TOTAL_SIGNAL_COUNT}} |
| After Dedup | {{WF1_DEDUP_COUNT}} | {{WF2_DEDUP_COUNT}} | {{WF3_DEDUP_COUNT}} | {{TOTAL_DEDUP_COUNT}} |
| Top Signals | {{WF1_TOP_COUNT}} | {{WF2_TOP_COUNT}} | {{WF3_TOP_COUNT}} | 20 |
| Avg pSST | {{WF1_AVG_PSST}} | {{WF2_AVG_PSST}} | {{WF3_AVG_PSST}} | {{TOTAL_AVG_PSST}} |
| Execution Time | {{WF1_DURATION}} | {{WF2_DURATION}} | {{WF3_DURATION}} | {{TOTAL_DURATION}} |
