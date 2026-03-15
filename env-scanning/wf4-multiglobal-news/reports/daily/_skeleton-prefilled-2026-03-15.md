# WF4 Report Skeleton Template (Multi&Global-News)

> **Purpose**: The report-generator agent fills this structure rather than generating free-form reports.
> All `{{PLACEHOLDER}}` tokens must be replaced with actual content.
> Unfilled placeholders will trigger **SKEL-001 validation failure**.
>
> **WF4 Only**: This skeleton is exclusively for Multi&Global-News environmental scanning (WF4).
> For WF1/WF2 reports use `report-skeleton.md`; for WF3 reports use `naver-report-skeleton.md`; for integrated reports use `integrated-report-skeleton.md`.
>
> **WF4-specific sections**: FSSF 8-type classification, Three Horizons distribution, Tipping Point alerts, anomaly detection, multi-language crawling statistics, translation statistics, defense log summary
>
> **Validation profile**: `multiglobal-news_en` (validate_report.py --profile multiglobal-news_en)
>
> **Language**: English (technical terms and acronyms preserved as-is)

---

## Usage Instructions

1. Copy this template to `reports/daily/environmental-scan-{date}.md`.
2. Replace all `{{...}}` placeholders with data-driven content.
3. Section headers (`## N. ...`) must **never be modified** — exact strings are validated.
4. Subsection headers (`### N.N ...`) must retain their numbering.
5. After generation, verify no `{{` tokens remain in the file.

---

# Daily Multi&Global-News Environmental Scanning Report

{{REPORT_HEADER_METADATA}}

> **Report Type**: WF4 Multi&Global-News Environmental Scanning (FSSF + Three Horizons + Tipping Point)
> **Scan Window**: March 13, 2026 21:36 UTC ~ March 14, 2026 21:36 UTC (24 hours)
> **Anchor Time (T₀)**: March 14, 2026 21:36:58 UTC

---

## 1. Executive Summary

### Today's Key Findings (Top 3 Signals)

1. **{{TOP1_TITLE}}** ({{TOP1_DOMAIN}})
   - Importance: {{TOP1_IMPORTANCE}}
   - FSSF Type: {{TOP1_FSSF_TYPE}}
   - Time Horizon: {{TOP1_HORIZON}}
   - Key Content: {{TOP1_SUMMARY}}
   - Strategic Implications: {{TOP1_IMPLICATION}}

2. **{{TOP2_TITLE}}** ({{TOP2_DOMAIN}})
   - Importance: {{TOP2_IMPORTANCE}}
   - FSSF Type: {{TOP2_FSSF_TYPE}}
   - Time Horizon: {{TOP2_HORIZON}}
   - Key Content: {{TOP2_SUMMARY}}
   - Strategic Implications: {{TOP2_IMPLICATION}}

3. **{{TOP3_TITLE}}** ({{TOP3_DOMAIN}})
   - Importance: {{TOP3_IMPORTANCE}}
   - FSSF Type: {{TOP3_FSSF_TYPE}}
   - Time Horizon: {{TOP3_HORIZON}}
   - Key Content: {{TOP3_SUMMARY}}
   - Strategic Implications: {{TOP3_IMPLICATION}}

### Key Changes Summary
- New signals detected: 12
- Top priority signals: 0
- Major impact domains: {{DOMAIN_DISTRIBUTION}}

### Crawling Statistics Summary
- Sites crawled: 0 sites, 0 succeeded, 0 failed
- Language breakdown: 0 Korean, 0 English, 0 Chinese, 0 Japanese, 0 German, 0 French, 0 Russian, 0 Other
- Translation: 0 translated, 0 failed

### FSSF Classification Summary

| FSSF Type | Signal Count | Ratio |
|-----------|---------|------|
| Weak Signal | 1 | 8% |
| Emerging Issue | 2 | 17% |
| Trend | 1 | 8% |
| Megatrend | 1 | 8% |
| Driver | 1 | 8% |
| Wild Card | 2 | 17% |
| Discontinuity | 2 | 17% |
| Precursor Event | 2 | 17% |

### Three Horizons Distribution

| Time Horizon | Signal Count | Ratio | Description |
|-----------|---------|------|------|
| H1 (0-2 years) | 0 | 0% | Changes within current regime |
| H2 (2-7 years) | 0 | 0% | Transitional signals |
| H3 (7+ years) | 0 | 0% | Seeds of future regime |

### Tipping Point Alert Summary

| Alert Level | Signal Count | Key Signal |
|-----------|---------|----------|
| GREEN | 12 | US Withdraws Global AI Chip Export Permit Rule — Deregulation Reversal, US Strikes Obliterate Iran's Kharg Island Oil Terminal — 90% of Iran's Exports at Risk, Record March Heat Wave in Western US: Arizona/California 90F+ as Heat Dome Expands and 9 |

{{ADDITIONAL_EXEC_SUMMARY}}

---

## 2. Newly Detected Signals

{{SECTION2_INTRO}}

---

### Priority 1: {{SIGNAL_1_TITLE}}

- **Confidence**: {{SIGNAL_1_PSST}}
- **FSSF Type**: {{SIGNAL_1_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_1_HORIZON}}
- **Uncertainty**: {{SIGNAL_1_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_1_LANGUAGE}}

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

### Priority 2: {{SIGNAL_2_TITLE}}

- **Confidence**: {{SIGNAL_2_PSST}}
- **FSSF Type**: {{SIGNAL_2_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_2_HORIZON}}
- **Uncertainty**: {{SIGNAL_2_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_2_LANGUAGE}}

1. **Classification**: {{SIGNAL_2_CLASSIFICATION}}
2. **Source**: {{SIGNAL_2_SOURCE}}
3. **Key Facts**: {{SIGNAL_2_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_2_METRICS}}
5. **Impact**: {{SIGNAL_2_IMPACT}}
6. **Detailed Description**: {{SIGNAL_2_DETAIL}}
7. **Inference**: {{SIGNAL_2_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_2_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_2_MONITORING}}

---

### Priority 3: {{SIGNAL_3_TITLE}}

- **Confidence**: {{SIGNAL_3_PSST}}
- **FSSF Type**: {{SIGNAL_3_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_3_HORIZON}}
- **Uncertainty**: {{SIGNAL_3_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_3_LANGUAGE}}

1. **Classification**: {{SIGNAL_3_CLASSIFICATION}}
2. **Source**: {{SIGNAL_3_SOURCE}}
3. **Key Facts**: {{SIGNAL_3_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_3_METRICS}}
5. **Impact**: {{SIGNAL_3_IMPACT}}
6. **Detailed Description**: {{SIGNAL_3_DETAIL}}
7. **Inference**: {{SIGNAL_3_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_3_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_3_MONITORING}}

---

### Priority 4: {{SIGNAL_4_TITLE}}

- **Confidence**: {{SIGNAL_4_PSST}}
- **FSSF Type**: {{SIGNAL_4_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_4_HORIZON}}
- **Uncertainty**: {{SIGNAL_4_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_4_LANGUAGE}}

1. **Classification**: {{SIGNAL_4_CLASSIFICATION}}
2. **Source**: {{SIGNAL_4_SOURCE}}
3. **Key Facts**: {{SIGNAL_4_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_4_METRICS}}
5. **Impact**: {{SIGNAL_4_IMPACT}}
6. **Detailed Description**: {{SIGNAL_4_DETAIL}}
7. **Inference**: {{SIGNAL_4_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_4_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_4_MONITORING}}

---

### Priority 5: {{SIGNAL_5_TITLE}}

- **Confidence**: {{SIGNAL_5_PSST}}
- **FSSF Type**: {{SIGNAL_5_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_5_HORIZON}}
- **Uncertainty**: {{SIGNAL_5_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_5_LANGUAGE}}

1. **Classification**: {{SIGNAL_5_CLASSIFICATION}}
2. **Source**: {{SIGNAL_5_SOURCE}}
3. **Key Facts**: {{SIGNAL_5_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_5_METRICS}}
5. **Impact**: {{SIGNAL_5_IMPACT}}
6. **Detailed Description**: {{SIGNAL_5_DETAIL}}
7. **Inference**: {{SIGNAL_5_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_5_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_5_MONITORING}}

---

### Priority 6: {{SIGNAL_6_TITLE}}

- **Confidence**: {{SIGNAL_6_PSST}}
- **FSSF Type**: {{SIGNAL_6_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_6_HORIZON}}
- **Uncertainty**: {{SIGNAL_6_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_6_LANGUAGE}}

1. **Classification**: {{SIGNAL_6_CLASSIFICATION}}
2. **Source**: {{SIGNAL_6_SOURCE}}
3. **Key Facts**: {{SIGNAL_6_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_6_METRICS}}
5. **Impact**: {{SIGNAL_6_IMPACT}}
6. **Detailed Description**: {{SIGNAL_6_DETAIL}}
7. **Inference**: {{SIGNAL_6_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_6_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_6_MONITORING}}

---

### Priority 7: {{SIGNAL_7_TITLE}}

- **Confidence**: {{SIGNAL_7_PSST}}
- **FSSF Type**: {{SIGNAL_7_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_7_HORIZON}}
- **Uncertainty**: {{SIGNAL_7_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_7_LANGUAGE}}

1. **Classification**: {{SIGNAL_7_CLASSIFICATION}}
2. **Source**: {{SIGNAL_7_SOURCE}}
3. **Key Facts**: {{SIGNAL_7_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_7_METRICS}}
5. **Impact**: {{SIGNAL_7_IMPACT}}
6. **Detailed Description**: {{SIGNAL_7_DETAIL}}
7. **Inference**: {{SIGNAL_7_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_7_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_7_MONITORING}}

---

### Priority 8: {{SIGNAL_8_TITLE}}

- **Confidence**: {{SIGNAL_8_PSST}}
- **FSSF Type**: {{SIGNAL_8_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_8_HORIZON}}
- **Uncertainty**: {{SIGNAL_8_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_8_LANGUAGE}}

1. **Classification**: {{SIGNAL_8_CLASSIFICATION}}
2. **Source**: {{SIGNAL_8_SOURCE}}
3. **Key Facts**: {{SIGNAL_8_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_8_METRICS}}
5. **Impact**: {{SIGNAL_8_IMPACT}}
6. **Detailed Description**: {{SIGNAL_8_DETAIL}}
7. **Inference**: {{SIGNAL_8_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_8_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_8_MONITORING}}

---

### Priority 9: {{SIGNAL_9_TITLE}}

- **Confidence**: {{SIGNAL_9_PSST}}
- **FSSF Type**: {{SIGNAL_9_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_9_HORIZON}}
- **Uncertainty**: {{SIGNAL_9_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_9_LANGUAGE}}

1. **Classification**: {{SIGNAL_9_CLASSIFICATION}}
2. **Source**: {{SIGNAL_9_SOURCE}}
3. **Key Facts**: {{SIGNAL_9_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_9_METRICS}}
5. **Impact**: {{SIGNAL_9_IMPACT}}
6. **Detailed Description**: {{SIGNAL_9_DETAIL}}
7. **Inference**: {{SIGNAL_9_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_9_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_9_MONITORING}}

---

### Priority 10: {{SIGNAL_10_TITLE}}

- **Confidence**: {{SIGNAL_10_PSST}}
- **FSSF Type**: {{SIGNAL_10_FSSF_TYPE}}
- **Time Horizon**: {{SIGNAL_10_HORIZON}}
- **Uncertainty**: {{SIGNAL_10_UNCERTAINTY}}
- **Source Language**: {{SIGNAL_10_LANGUAGE}}

1. **Classification**: {{SIGNAL_10_CLASSIFICATION}}
2. **Source**: {{SIGNAL_10_SOURCE}}
3. **Key Facts**: {{SIGNAL_10_KEY_FACT}}
4. **Quantitative Metrics**: {{SIGNAL_10_METRICS}}
5. **Impact**: {{SIGNAL_10_IMPACT}}
6. **Detailed Description**: {{SIGNAL_10_DETAIL}}
7. **Inference**: {{SIGNAL_10_INFERENCE}}
8. **Stakeholders**: {{SIGNAL_10_STAKEHOLDERS}}
9. **Monitoring Indicators**: {{SIGNAL_10_MONITORING}}

---

{{SIGNALS_11_TO_15_CONDENSED}}

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

### 4.3 FSSF Signal Classification Distribution

{{SECTION_4_3_FSSF_DISTRIBUTION}}

| FSSF Type | Signal Count | Representative Signal | Key Features |
|-----------|---------|-----------|-----------|
| Weak Signal | 1 | {{FSSF_DIST_WS_REPR}} | {{FSSF_DIST_WS_NOTE}} |
| Emerging Issue | 2 | {{FSSF_DIST_EI_REPR}} | {{FSSF_DIST_EI_NOTE}} |
| Trend | 1 | {{FSSF_DIST_TR_REPR}} | {{FSSF_DIST_TR_NOTE}} |
| Megatrend | 1 | {{FSSF_DIST_MT_REPR}} | {{FSSF_DIST_MT_NOTE}} |
| Driver | 1 | {{FSSF_DIST_DR_REPR}} | {{FSSF_DIST_DR_NOTE}} |
| Wild Card | 2 | {{FSSF_DIST_WC_REPR}} | {{FSSF_DIST_WC_NOTE}} |
| Discontinuity | 2 | {{FSSF_DIST_DC_REPR}} | {{FSSF_DIST_DC_NOTE}} |
| Precursor Event | 2 | {{FSSF_DIST_PE_REPR}} | {{FSSF_DIST_PE_NOTE}} |

### 4.4 Three Horizons Distribution

{{SECTION_4_4_THREE_HORIZONS}}

| Time Horizon | Signal List | Key Themes |
|-----------|-----------|-----------|
| H1 (0-2 years) | {{H1_SIGNAL_LIST}} | {{H1_THEMES}} |
| H2 (2-7 years) | {{H2_SIGNAL_LIST}} | {{H2_THEMES}} |
| H3 (7+ years) | {{H3_SIGNAL_LIST}} | {{H3_THEMES}} |

### 4.5 Tipping Point Alerts

{{SECTION_4_5_TIPPING_POINT}}

| Alert Level | Signal | Indicator | Evidence |
|-----------|------|------|------|
{{TIPPING_POINT_TABLE}}

### 4.6 Anomaly Detection Results

{{SECTION_4_6_ANOMALY}}

| Type | Signal | Anomaly Indicator | Severity |
|------|------|-----------|--------|
{{ANOMALY_TABLE}}

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

{{SECTION_7_TRUST_ANALYSIS}}

---

## 8. Appendix

### 8.1 Crawling Statistics

| Site | Language | Articles | Strategy | Success Rate |
|------|----------|----------|----------|--------------|
N/A

| Item | Value |
|------|-------|
| Crawling Datetime | N/A |
| Total Sites Crawled | 0 |
| Sites Succeeded | 0 |
| Sites Failed | 0 |
| Total Articles Collected | 0 |
| S/N Ratio | N/A |

### 8.2 Translation Statistics

| Language | Total | Translated | Failed | Avg Confidence |
|----------|-------|------------|--------|----------------|
N/A

| Item | Value |
|------|-------|
| Total Translated | 0 |
| Translation Failed | 0 |
| By Language — Korean | 0 |
| By Language — English | 0 |
| By Language — Chinese | 0 |
| By Language — Japanese | 0 |
| By Language — German | 0 |
| By Language — French | 0 |
| By Language — Russian | 0 |
| By Language — Other | 0 |

### 8.3 Defense Log Summary

| Block Type | Count | Strategy Used | Success Rate |
|------------|-------|---------------|--------------|
N/A

### 8.4 FSSF Classification Methodology

{{SECTION_8_4_FSSF_METHODOLOGY}}

### 8.5 Full Signal List

{{SECTION_8_5_FULL_SIGNAL_TABLE}}

### 8.6 Source List

{{SECTION_8_6_SOURCE_LIST}}
