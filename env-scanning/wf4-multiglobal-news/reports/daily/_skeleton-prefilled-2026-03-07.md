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
> **Scan Window**: March 06, 2026 00:46 UTC ~ March 07, 2026 00:46 UTC (24 hours)
> **Anchor Time (T₀)**: March 07, 2026 00:46:38 UTC

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
- New signals detected: 46
- Top priority signals: 22
- Major impact domains: {{DOMAIN_DISTRIBUTION}}

### Crawling Statistics Summary
- Sites crawled: 38 sites, 38 succeeded, 0 failed
- Language breakdown: 880 Korean, 945 English, 3 Chinese, 28 Japanese, 3 German, 17 French, 100 Russian, 100 Other
- Translation: 1131 translated, 0 failed

### FSSF Classification Summary

| FSSF Type | Signal Count | Ratio |
|-----------|---------|------|
| Weak Signal | 2 | 4% |
| Emerging Issue | 11 | 24% |
| Trend | 5 | 11% |
| Megatrend | 0 | 0% |
| Driver | 7 | 15% |
| Wild Card | 9 | 20% |
| Discontinuity | 5 | 11% |
| Precursor Event | 7 | 15% |

### Three Horizons Distribution

| Time Horizon | Signal Count | Ratio | Description |
|-----------|---------|------|------|
| H1 (0-2 years) | 24 | 52% | Changes within current regime |
| H2 (2-7 years) | 19 | 41% | Transitional signals |
| H3 (7+ years) | 3 | 7% | Seeds of future regime |

### Tipping Point Alert Summary

| Alert Level | Signal Count | Key Signal |
|-----------|---------|----------|
| GREEN | 46 | Korea Activates Strategic Petroleum Reserves as Hormuz Crisis Drives Oil to $125, El-Sisi Says Egypt in 'State of Near-Emergency' as War Threatens Economy, Swedish Intelligence Warns of Increased Middle East War Fallout in Europe and 43 |

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
| New | 0 | 0% |
| Strengthening | 0 | 0% |
| Recurring | 0 | 0% |
| Weakening | 0 | 0% |
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
| Weak Signal | 2 | {{FSSF_DIST_WS_REPR}} | {{FSSF_DIST_WS_NOTE}} |
| Emerging Issue | 11 | {{FSSF_DIST_EI_REPR}} | {{FSSF_DIST_EI_NOTE}} |
| Trend | 5 | {{FSSF_DIST_TR_REPR}} | {{FSSF_DIST_TR_NOTE}} |
| Megatrend | 0 | {{FSSF_DIST_MT_REPR}} | {{FSSF_DIST_MT_NOTE}} |
| Driver | 7 | {{FSSF_DIST_DR_REPR}} | {{FSSF_DIST_DR_NOTE}} |
| Wild Card | 9 | {{FSSF_DIST_WC_REPR}} | {{FSSF_DIST_WC_NOTE}} |
| Discontinuity | 5 | {{FSSF_DIST_DC_REPR}} | {{FSSF_DIST_DC_NOTE}} |
| Precursor Event | 7 | {{FSSF_DIST_PE_REPR}} | {{FSSF_DIST_PE_NOTE}} |

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
| Site | Language | Articles | Strategy | Success Rate |
|------|----------|----------|----------|--------------|
| nknews | en | 300 | rss | 100% |
| joongang | ko | 257 | web_crawl | 100% |
| apnews | en | 122 | web_crawl | 100% |
| sedaily | ko | 117 | web_crawl | 100% |
| chosun | ko | 100 | rss | 100% |
| mt | ko | 100 | rss | 100% |
| globeandmail | en | 100 | rss | 100% |
| rt | ru | 100 | rss | 100% |
| elfinanciero | es | 100 | rss | 100% |
| donga | ko | 50 | rss | 100% |
| mk | ko | 50 | rss | 100% |
| scmp | en | 50 | rss | 100% |
| straitstimes | en | 50 | rss | 100% |
| hankyung | ko | 49 | rss | 100% |
| washingtonpost | en | 41 | rss | 100% |
| khan | ko | 38 | rss | 100% |
| bbc | en | 36 | rss | 100% |
| aitimes | ko | 31 | rss | 100% |
| nytimes | en | 31 | rss | 100% |
| reuters | en | 31 | web_crawl | 100% |
| hani | ko | 30 | rss | 100% |
| politico | en | 30 | rss | 100% |
| japantimes | en | 30 | rss | 100% |
| nikkei | ja | 28 | web_crawl | 100% |
| etnews | ko | 25 | rss | 100% |
| aljazeera | en | 25 | rss | 100% |
| wsj | en | 20 | rss | 100% |
| techcrunch | en | 20 | rss | 100% |
| arstechnica | en | 20 | rss | 100% |
| bloter | ko | 18 | web_crawl | 100% |
| lemonde | fr | 17 | rss | 100% |
| koreaherald | en | 16 | web_crawl | 100% |
| zdnet_kr | ko | 13 | web_crawl | 100% |
| ft | en | 13 | rss | 100% |
| arabnews | en | 10 | rss | 100% |
| caixin | zh | 3 | web_crawl | 100% |
| handelsblatt | de | 3 | web_crawl | 100% |
| sciencetimes | ko | 2 | web_crawl | 100% |

| Item | Value |
|------|-------|
| Crawling Datetime | 2026-03-07T04:06:05.012224+00:00 |
| Total Sites Crawled | 38 |
| Sites Succeeded | 38 |
| Sites Failed | 0 |
| Total Articles Collected | 2076 |
| S/N Ratio | 2076:2076 |

### 8.2 Translation Statistics

| Language | Total | Translated | Failed | Avg Confidence |
|----------|-------|------------|--------|----------------|
| Language | Total | Translated | Failed | Avg Confidence |
|----------|-------|------------|--------|----------------|
| de | 3 | 3 | 0 | 1.00 |
| en | 945 | 0 | 0 | N/A |
| es | 100 | 100 | 0 | 1.00 |
| fr | 17 | 17 | 0 | 1.00 |
| ja | 28 | 28 | 0 | 1.00 |
| ko | 880 | 880 | 0 | 1.00 |
| ru | 100 | 100 | 0 | 1.00 |
| zh | 3 | 3 | 0 | 1.00 |

| Item | Value |
|------|-------|
| Total Translated | 1131 |
| Translation Failed | 0 |
| By Language — Korean | 880 |
| By Language — English | 945 |
| By Language — Chinese | 3 |
| By Language — Japanese | 28 |
| By Language — German | 3 |
| By Language — French | 17 |
| By Language — Russian | 100 |
| By Language — Other | 100 |

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
