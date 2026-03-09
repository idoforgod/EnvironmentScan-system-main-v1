# Integrated Report Skeleton Template

> **Purpose**: The report-merger agent fills this structure rather than generating free-form reports.
> All `{{PLACEHOLDER}}` tokens must be replaced with actual content.
> Unfilled placeholders will trigger **SKEL-001 validation failure**.
>
> **Important**: This skeleton integrates results from four independent workflows:
> WF1 (General), WF2 (arXiv), WF3 (Naver News), WF4 (Multi&Global-News). For individual reports, use `report-skeleton.md` or `naver-report-skeleton.md`.
>
> **Language**: English (technical terms and acronyms preserved as-is)

---

## Usage Instructions

1. Copy this template to `integrated/reports/daily/integrated-scan-{date}.md`.
2. Replace all `{{...}}` placeholders with data-driven content.
3. Section headers (`## N. ...`) must **never be modified** — exact strings are validated.
4. Subsection headers (`### N.N ...`) must retain their numbering.
5. All signals must include `[WF1]`, `[WF2]`, `[WF3]`, or `[WF4]` source tags.
6. After generation, verify no `{{` tokens remain in the file.

---

# Integrated Daily Environmental Scanning Report

{{REPORT_HEADER_METADATA}}

> **Report Type**: Integrated Report (WF1 General + WF2 arXiv Academic + WF3 Naver News + WF4 Multi&Global-News)
> **Scan Window**: March 06, 2026 22:36 UTC ~ March 09, 2026 15:00 UTC
> **Anchor Time (T₀)**: March 08, 2026 22:36:42 UTC
> **Per-Workflow Scan Range**: WF1 24 hours | WF2 48 hours | WF3 24 hours | WF4 24 hours

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

- **WF1 (General Environmental Scanning)**: 24 signals collected
- **WF2 (arXiv Academic Deep Scan)**: 686 signals collected
- **WF3 (Naver News)**: 251 signals collected
- **WF4 (Multi&Global-News)**: 1372 signals collected
- **Integrated Signal Pool**: 2333
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

> Active tracking threads: 2423 | Strengthening: 0 | Weakening: 446 | Faded: 532

### 3.1 Strengthening Trends

N/A

{{SECTION_3_1_CONTENT}}

### 3.2 Weakening Trends

| Tracking Thread | Days Tracked | Appearances | pSST Change | Velocity | Expansion |
|------------|---------|---------|----------|------|-------|
| Transformer-Based Inpainting for Real-Time 3D Streaming in Sparse Multi-Camera Setups | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| EdgeDAM: Real-time Object Tracking for Mobile Devices | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Residual RL--MPC for Robust Microrobotic Cell Pushing Under Time-Varying Flow | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Latent Wasserstein Adversarial Imitation Learning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Ensembling Language Models with Sequential Monte Carlo | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| OpenFrontier: General Navigation with Visual-Language Grounded Frontiers | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Robust Node Affinities via Jaccard-Biased Random Walks and Rank Aggregation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Safe-SAGE: Social-Semantic Adaptive Guidance for Safe Engagement through Laplace-Modulated Poisson Safety Functions | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Omni-Manip: Beyond-FOV Large-Workspace Humanoid Manipulation with Omnidirectional 3D Perception | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| CT-Enabled Patient-Specific Simulation and Contact-Aware Robotic Planning for Cochlear Implantation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| UltraDexGrasp: Learning Universal Dexterous Grasping for Bimanual Robots with Synthetic Data | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Latent Policy Steering through One-Step Flow Policies | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Iterative On-Policy Refinement of Hierarchical Diffusion Policies for Language-Conditioned Manipulation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Digital Twin Driven Textile Classification and Foreign Object Recognition in Automated Sorting Systems | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| V2N-Based Algorithm and Communication Protocol for Autonomous Non-Stop Intersections | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Lifelong Language-Conditioned Robotic Manipulation Learning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Decoupling Task and Behavior: A Two-Stage Reward Curriculum in Reinforcement Learning for Robotics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Practical Post-Quantum Distributed Ledger Protocol for Financial Institutions | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Public Sector Open Source Program Offices - Archetypes for how to Grow (Common) Institutional Capabilities | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Turning Trust to Transactions: Tracking Affiliate Marketing and FTC Compliance in YouTube's Influencer Economy | 4d | 3x | 74.2→23.8 (-50.400000000000006) | ▼ Decel | 0.18 |
| Robustness of Agentic AI Systems via Adversarially-Aligned Jacobian Regularization | 4d | 2x | 76.0→23.8 (-52.2) | ▼ Decel | 0.18 |
| Breaking Bad Email Habits: Bounding the Impact of Simulated Phishing Campaigns | 4d | 2x | 76.2→23.8 (-52.400000000000006) | ▼ Decel | 0.18 |
| FeedAIde: Guiding App Users to Submit Rich Feedback Reports by Asking Context-Aware Follow-Up Questions | 4d | 2x | 74.7→23.8 (-50.900000000000006) | ▼ Decel | 0.18 |
| Code Fingerprints: Disentangled Attribution of LLM-Generated Code | 4d | 2x | 78.4→23.8 (-54.60000000000001) | ▼ Decel | 0.18 |
| Why Are Linear RNNs More Parallelizable? | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| O^3-LSM: Maximizing Disaggregated LSM Write Performance via Three-Layer Offloading | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Boosting ASR Robustness via Test-Time Reinforcement Learning with Audio-Text Semantic Rewards | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Debiasing Sequential Recommendation with Time-aware Inverse Propensity Scoring | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| CONE: Embeddings for Complex Numerical Data Preserving Unit and Variable Semantics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Designing for Adolescent Voice in Health Decisions: Embodied Conversational Agents for HPV Vaccination | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Competitive Multi-Operator Reinforcement Learning for Joint Pricing and Fleet Rebalancing in AMoD Systems | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Mind the Gap: Mapping Wearer-Bystander Privacy Tensions and Context-Adaptive Pathways for Camera Glasses | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Differential Privacy in Two-Layer Networks: How DP-SGD Harms Fairness and Robustness | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SCoUT: Scalable Communication via Utility-Guided Temporal Grouping in Multi-Agent Reinforcement Learning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Autoscoring Anticlimax: A Meta-analytic Understanding of AI's Short-answer Shortcomings and Wording Weaknesses | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SparkTales: Facilitating Cross-Language Collaborative Storytelling through Coordinator-AI Collaboration | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Evaluating and Correcting Human Annotation Bias in Dynamic Micro-Expression Recognition | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Analysis of Terms of Service on Social Media Platforms: Consent Challenges and Assessment Metrics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Integral Formulation and the Brézis-Ekeland-Nayroles-Type Principle for Prox-Regular Sweeping Processes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Quantifying Salt Precipitation During CO2 Injection: How Flow Rate, Temperature, and Phase State Control Near-Wellbore Crystallization | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Evaluation of the performance of an analytical-numerical coupled method for droplet impacts on soft material surfaces | 4d | 2x | 78.4→23.8 (-54.60000000000001) | ▼ Decel | 0.18 |
| Revealing the Topology invariance of vectorial vortex beam in complex media | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Equilibrium Thermochemistry and Crystallographic Morphology of Manganese Sulfide Nanocrystals | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Asset Returns, Portfolio Choice, and Proportional Wealth Taxation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Continuous Ventricular Volumetric Quantification in Patients with Arrhythmias using Real-Time 3D CMR-MOTUS | 4d | 2x | 76.9→23.8 (-53.10000000000001) | ▼ Decel | 0.18 |
| A FAST Survey of H I Absorption in Low-power Radio Sources | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| TILARA: Template-Independent Line-by-line Algorithm for Radial velocity Analysis. I. Description of the code and application on a Sun-like star | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| EMU/GAMA: A statistical perspective on active galactic nuclei diagnostics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Shift-Invariant Deep Learning Framework for Automated Analysis of XPS Spectra | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Machine Learning the Strong Disorder Renormalization Group Method for Disordered Quantum Spin Chains | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Connecting Flavor and Baryon Asymmetry via Leptogenesis in Effective Froggatt-Nielsen Theory | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Discrete \texorpdfstring{$θ$}{theta} Projection: A Gauge-Protected Solution to the Strong CP Problem Without Axions | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| External magnetic field influence on massive binary black hole inspiral gravitational waves and its similarity with environmental effects | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Mirror codes: High-threshold quantum LDPC codes beyond the CSS regime | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SpiderCat: Optimal Fault-Tolerant Cat State Preparation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Constant-Depth Quantum Imaginary Time Evolution Using Dynamic Fan-out Circuits | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Bandwidth Selection for Spatial HAC Standard Errors | 4d | 2x | 79.0→23.8 (-55.2) | ▼ Decel | 0.18 |
| Candidate Moderation under Instant Runoff and Condorcet Voting: Evidence from the Cooperative Election Survey | 4d | 2x | 76.9→23.8 (-53.10000000000001) | ▼ Decel | 0.18 |
| Towards a data-scale independent regulariser for robust sparse identification of non-linear dynamics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Areal Disaggregation: A Small Area Estimation Perspective | 4d | 2x | 74.7→23.8 (-50.900000000000006) | ▼ Decel | 0.18 |
| Dose-Dependent Cardiac Complexity Changes in Children Following Prenatal Glucocorticoid Exposure: Complementary Evidence from Multiscale Entropy Analysis and ECG Foundation Models | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Performance of Conventional EEG Biomarkers Across Different Clinical Phases of Major Depressive Disorder: A Comprehensive Evaluation | 4d | 2x | 77.5→23.8 (-53.7) | ▼ Decel | 0.18 |
| A Comprehensive Approach to Directly Addressing Estimation Delays in Stochastic Guidance | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Impact of Preprocessing Methods on Racial Encoding and Model Robustness in CXR Diagnosis | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Design of Grid Forming Multi Timescale Coordinated Control Strategies for Dynamic Virtual Power Plants | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Vertical Challenge of Low-Altitude Economy: Why We Need a Unified Height System? | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Detection of GNSS Interference Using Reflected Signal Ob-servations from the LEO Satellite Constellation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Adaptive Policy Switching of Two-Wheeled Differential Robots for Traversing over Diverse Terrains | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Unseen Cost of Space Computing: Quantifying LEO Battery Aging via Physics-Driven Modeling | 4d | 2x | 76.6→23.8 (-52.8) | ▼ Decel | 0.18 |
| The Spike, the Sparse and the Sink: Anatomy of Massive Activations and Attention Sinks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Towards Provably Unbiased LLM Judges via Bias-Bounded Evaluation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Towards Multimodal Lifelong Understanding: A Dataset and Agentic Baseline | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Towards 3D Scene Understanding of Gas Plumes in LWIR Hyperspectral Images Using Neural Radiance Fields | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Leveraging LLM Parametric Knowledge for Fact Checking without Retrieval | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Kraus Constrained Sequence Learning For Quantum Trajectories from Continuous Measurement | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Beyond Scattered Acceptance: Fast and Coherent Inference for DLMs via Longest Stable Prefixes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Distributed Partial Information Puzzles: Examining Common Ground Construction Under Epistemic Asymmetry | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| On-Policy Self-Distillation for Reasoning Compression | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Spatial and Temporal Resolution of Motor Intention in Multi-Target Prediction | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Harnessing Synthetic Data from Generative AI for Statistical Inference | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Legal interpretation and AI: from expert systems to argumentation and LLMs | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Fusion-CAM: Integrating Gradient and Region-Based Class Activation Maps for Robust Visual Explanations | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Learning Causal Structure of Time Series using Best Order Score Search | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| cuRoboV2: Dynamics-Aware Motion Generation with Depth-Fused Distance Fields for High-DoF Robots | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| From Code to Road: A Vehicle-in-the-Loop and Digital Twin-Based Framework for Central Car Server Testing in Autonomous Driving | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Curve-Induced Dynamical Systems on Riemannian Manifolds and Lie Groups | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| AI+HW 2035: Shaping the Next Decade | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Scaling Real-Time Traffic Analytics on Edge-Cloud Fabrics for City-Scale Camera Networks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Leveraging Structural Knowledge for Solving Election in Anonymous Networks with Shared Randomness | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SeedPolicy: Horizon Scaling via Self-Evolving Diffusion Policy for Robot Manipulation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| AIM-SLAM: Dense Monocular SLAM via Adaptive and Informative Multi-View Keyframe Prioritization with Foundation Model | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| PromptTuner: SLO-Aware Elastic System for LLM Prompt Tuning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| VinePT-Map: Pole-Trunk Semantic Mapping for Resilient Autonomous Robotics in Vineyards | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Direct Contact-Tolerant Motion Planning With Vision Language Models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Observer Design for Augmented Reality-based Teleoperation of Soft Robots | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Person Detection and Tracking from an Overhead Crane LiDAR | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A framework for assessing the capabilities of code generation of constraint domain-specific languages with large language models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Benchmarking Framework for Model Datasets | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Robust Single-message Shuffle Differential Privacy Protocol for Accurate Distribution Estimation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Cyber Threat Intelligence for Artificial Intelligence Systems | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Why Do You Contribute to Stack Overflow? Understanding Cross-Cultural Motivations and Usage Patterns before the Age of LLMs | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| ShieldBypass: On the Persistence of Impedance Leakage Beyond EM Shielding | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| MOOSEnger -- a Domain-Specific AI Agent for the MOOSE Ecosystem | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Behaviour Driven Development Scenario Generation with Large Language Models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Dual-Helix Governance Approach Towards Reliable Agentic AI for WebGIS Development | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| PTOPOFL: Privacy-Preserving Personalised Federated Learning via Persistent Homology | 4d | 2x | 75.3→23.8 (-51.5) | ▼ Decel | 0.18 |
| LikeThis! Empowering App Users to Submit UI Improvement Suggestions Instead of Complaints | 4d | 2x | 76.9→23.8 (-53.10000000000001) | ▼ Decel | 0.18 |
| CAM-LDS: Cyber Attack Manifestations for Automatic Interpretation of System Logs and Security Alerts | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Core-based Hierarchies for Efficient GraphRAG | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| CRISP: Correlation-Resilient Indexing via Subspace Partitioning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| WaterSIC: information-theoretically (near) optimal linear layer quantization | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Scaling Laws for Reranking in Information Retrieval | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SLO-Aware Compute Resource Allocation for Prefill-Decode Disaggregated LLM Inference | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Training for Technology: Adoption and Productive Use of Generative AI in Legal Analysis | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| VizCrit: Exploring Strategies for Displaying Computational Feedback in a Visual Design Tool | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Memory as Ontology: A Constitutional Memory Architecture for Persistent Digital Citizens | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| LEGS-POMDP: Language and Gesture-Guided Object Search in Partially Observable Environments | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Second-Order Algorithm Based on Affine Scaling Interior-Point Methods for nonlinear minimization with bound constraints | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Accurate and Efficient Hybrid-Ensemble Atmospheric Data Assimilation in Latent Space with Uncertainty Quantification | 4d | 2x | 76.2→23.8 (-52.400000000000006) | ▼ Decel | 0.18 |
| Efficient simulation of Bose-Einstein condensates in nontrivial topologies | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Integrated Microcomb-Driven Vortex Electromagnetic Waves for Broadband Forward-looking Sensing | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Real-Space Plasmon Imaging Reveals Modified Electronic Structure of Gold at the Monolayer Limit | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Beam Geometry-Controlled Nonequilibrium Formation of WS2/CsPbBr3 Hybrids and Interfacial Carrier Dynamics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Multiband Hybrid Metasurface for Enhanced Second-Harmonic Generation via Coupled Gap Surface Plasmon Modes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Modular memristor model with synaptic-like plasticity and volatile memory | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Thermal stable nonlinear Raman-Nath diffraction and Cherenkov radiation in PPKTP crystals | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| HoloPASWIN: Robust Inline Holographic Reconstruction via Physics-Aware Swin Transformers | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Hollow toroidal rotation profiles in strongly electron heated H-mode plasmas in the ASDEX Upgrade tokamak | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Hyperuniform Disorder in Photonic Crystal Slabs with Intrinsic non-Hermiticity | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| MQED-QD: An Open-Source Package for Quantum Dynamics Simulation in Complex Dielectric Environments | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Uncertainty-aware Blood Glucose Prediction from Continuous Glucose Monitoring Data | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Cell-Cell Adhesion as a Double-Edged Sword in Tissue Fluidity | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Structure-resolved free energy estimation of the 38-atom Lennard Jones cluster via population annealing | 4d | 2x | 76.2→23.8 (-52.400000000000006) | ▼ Decel | 0.18 |
| The Bayesian view of DESI DR2: Evidence and tension in a combined analysis with CMB and supernovae across cosmological models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Local Tremaine-Weinberg Method for Galactic Pattern Speed: Theory and its Application to IllustrisTNG | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Sound Mode and Scale-Dependent Growth in Two-Fluid Dynamical Dark Energy | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Euclid: A blue galaxy population and a brightest cluster galaxy in the making in a $z\sim1.74$ MaDCoWS2 galaxy cluster candidate | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Age of the Universe with Globular Clusters IV: Multiple Stellar Populations | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Early Planet Formation in Embedded Disks (eDisk). XVIII. Indication of a possible spiral structure in the dust-continuum emission of the protostellar disk around IRAS 16544-1604 in CB 68 | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| AstroInspect: a web-based system to organize, assess, and visually inspect astronomical objects | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Temperature-Dependent Dielectric Function of Tantalum Nitride Formed by Atomic Layer Deposition for Tunnel Barriers in Josephson Junctions | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Epitaxial Growth and Electronic Properties of QuasiFreeStanding Rhombohedral WSe2 Bilayers on Cubic W110 | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Flavor Democracy Calls for Vector Like Leptons and Quarks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Constrained Symplectic Quantization: Disclosing the Deterministic Framework Behind Quantum Mechanics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| On the robustness of the indirect determination of the width of the detected Higgs boson | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Spatiotemporal Pauli processes: Quantum combs for modelling correlated noise in quantum error correction | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| All You Need is Amplifier: Spectral Imposters Without Pulse Shaping | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Standardizing Access to Heterogeneous Quantum Backends: A Case Study on Cloud Service Integration with QDMI | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The "Gold Rush" in AI and Robotics Patenting Activity. Do innovation systems have a role? | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Algorithmic Compliance and Regulatory Loss in Digital Assets | 4d | 3x | 72.7→23.8 (-48.900000000000006) | ▼ Decel | 0.18 |
| Statistical Inference for Score Decompositions | 4d | 2x | 78.1→23.8 (-54.3) | ▼ Decel | 0.18 |
| Monitoring Covariance in Multichannel Profiles via Functional Graphical Models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Federated Causal Discovery Across Heterogeneous Datasets under Latent Confounding | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Modeling cyclostationarity in time series using ASCA | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Non-Euclidean Gradient Descent Operates at the Edge of Stability | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| How Does the ReLU Activation Affect the Implicit Bias of Gradient Descent on High-dimensional Neural Network Regression? | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The Inductive Bias of Convolutional Neural Networks: Locality and Weight Sharing Reshape Implicit Regularization | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Multi-Fidelity Tensor Emulator for Spatiotemporal Outputs: Emulation of Arctic Sea Ice Dynamics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Theory Discovery in Social Networks: Automating ERGM Specification with Large Language Models | 4d | 2x | 76.0→23.8 (-52.2) | ▼ Decel | 0.18 |
| A mixture model for subtype identification in the context of disease progression modeling | 4d | 2x | 74.7→23.8 (-50.900000000000006) | ▼ Decel | 0.18 |
| Beyond Mixtures and Products for Ensemble Aggregation: A Likelihood Perspective on Generalized Means | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Stable and Steerable Sparse Autoencoders with Weight Regularization | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Ising Models of Cooperativity in Muscle Contraction | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Tracking Feral Horses in Aerial Video Using Oriented Bounding Boxes | 4d | 2x | 75.6→23.8 (-51.8) | ▼ Decel | 0.18 |
| Exploring the potential and limitations of Model Merging for Multi-Domain Adaptation in ASR | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Visual-Informed Speech Enhancement Using Attention-Based Beamforming | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| On Dual-Fed Pinching Antenna Systems with In-Waveguide Attenuation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Limited-Angle CT Reconstruction Using Multi-Volume Latent Consistency Model | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Anti-Aliasing Snapshot HDR Imaging Using Non-Regular Sensing | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Voice Timbre Attribute Detection with Compact and Interpretable Training-Free Acoustic Parameters | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Receding-Horizon Maximum-Likelihood Estimation of Neural-ODE Dynamics and Thresholds from Event Cameras | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Unified Hybrid Control Architecture for Multi-DOF Robotic Manipulators | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| U-OBCA: Uncertainty-Aware Optimization-Based Collision Avoidance via Wasserstein Distributionally Robust Chance Constraints | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Policy Optimization of Mixed H2/H-infinity Control: Benign Nonconvexity and Global Optimality | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Data-Driven Control of a Magnetically Actuated Fish-Like Robot | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| bayesgrid: An Open-Source Python Tool for Generating Probabilistic Synthetic Transmission-Distribution Grids Using Bayesian Hierarchical Models | 4d | 2x | 77.2→23.8 (-53.400000000000006) | ▼ Decel | 0.18 |
| FaceCam: Portrait Video Camera Control via Scale-Aware Conditioning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Accelerating Text-to-Video Generation with Calibrated Sparse Attention | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Censored LLMs as a Natural Testbed for Secret Knowledge Elicitation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| HALP: Detecting Hallucinations in Vision-Language Models without Generating a Single Token | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SAIL: Similarity-Aware Guidance and Inter-Caption Augmentation-based Learning for Weakly-Supervised Dense Video Captioning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| An Exploration-Analysis-Disambiguation Reasoning Framework for Word Sense Disambiguation with Low-Parameter LLMs | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Loop Closure via Maximal Cliques in 3D LiDAR-Based SLAM | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| On the Necessity of Learnable Sheaf Laplacians | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| ORMOT: A Dataset and Framework for Omnidirectional Referring Multi-Object Tracking | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Embedded Inter-Subject Variability in Adversarial Learning for Inertial Sensor-Based Human Activity Recognition | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Progressive Residual Warmup for Language Model Pretraining | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Observing and Controlling Features in Vision-Language-Action Models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Accelerating Sampling-Based Control via Learned Linear Koopman Dynamics | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Constraint-Free Static Modeling of Continuum Parallel Robot | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Rethinking the Role of Collaborative Robots in Rehabilitation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Design and Analysis of an Improved Constrained Hypercube Mixer in Quantum Approximate Optimization Algorithm | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Critic in the Loop: A Tri-System VLA Framework for Robust Long-Horizon Manipulation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Act, Think or Abstain: Complexity-Aware Adaptive Inference for Vision-Language-Action Models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SPIRIT: Perceptive Shared Autonomy for Robust Robotic Manipulation under Deep Learning Uncertainty | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| GaussTwin: Unified Simulation and Correction with Gaussian Splatting for Robotic Digital Twins | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| MCEL: Margin-Based Cross-Entropy Loss for Error-Tolerant Quantized Neural Networks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| VMXDOTP: A RISC-V Vector ISA Extension for Efficient Microscaling (MX) Format Acceleration | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Analysis of Proactive Uncoordinated Techniques to Mitigate Interference in FMCW Automotive Radars | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| FluxSieve: Unifying Streaming and Analytical Data Planes for Scalable Cloud Observability | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| RepoLaunch: Automating Build&Test Pipeline of Code Repositories on ANY Language and ANY Platform | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| AgentSCOPE: Evaluating Contextual Privacy Across Agentic Workflows | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Osmosis Distillation: Model Hijacking with the Fewest Samples | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Efficient Privacy-Preserving Sparse Matrix-Vector Multiplication Using Homomorphic Encryption | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| When Denoising Becomes Unsigning: Theoretical and Empirical Analysis of Watermark Fragility Under Diffusion-Based Image Editing | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| SpotIt+: Verification-based Text-to-SQL Evaluation with Database Constraints | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| CodeTaste: Can LLMs Generate Human-Level Code Refactorings? | 4d | 2x | 76.2→23.8 (-52.400000000000006) | ▼ Decel | 0.18 |
| Truth Predicate of Inductive Definitions and Logical Complexity of Infinite-Descent Proofs | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| Learning Foundations Beneath the Stars | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| Improved Decoding of Quantum Tanner Codes Using Generalized Check Nodes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Spatially-aware Secondary License Sharing in mmWave Networks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Bala-Join: An Adaptive Hash Join for Balancing Communication and Computation in Geo-Distributed SQL Databases | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Hierarchical Decoding for Discrete Speech Synthesis with Multi-Resolution Spoof Detection | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Adaptive Sampling for Storage of Progressive Images on DNA | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| RESYSTANCE: Unleashing Hidden Performance of Compaction in LSM-trees via eBPF | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Asymptotic Behavior of Multi--Task Learning: Implicit Regularization and Double Descent Effects | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| On LLR Mismatch in Belief Propagation Decoding of Overcomplete QLDPC Codes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| DeformTrace: A Deformable State Space Model with Relay Tokens for Temporal Forgery Localization | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Beyond Linear LLM Invocation: An Efficient and Effective Semantic Filter Paradigm | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| DARE: Aligning LLM Agents with the R Statistical Ecosystem via Distribution-Aware Retrieval | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Ailed: A Psyche-Driven Chess Engine with Dynamic Emotional Modulation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Oral to Web: Digitizing 'Zero Resource'Languages of Bangladesh | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Optimization with Parametric Variational Inequality Constraints on a Moving Set | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Quantitative Error Estimates for Learning Macroscopic Mobilities from Microscopic Fluctuations | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Evidence for Vortex Rings with Multiquantum Circulation in He II | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Multi-Fidelity Parametric Framework for Reduced-Order Modeling using Optimal Transport-based Interpolation: Applications to Diffused-Interface Two-Phase Flows | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| A Robust Compressible APIC/FLIP Particle Grid Method with Conservative Resampling and Adaptive APIC/PIC Blending | 4d | 2x | 78.4→23.8 (-54.60000000000001) | ▼ Decel | 0.18 |
| Idealized Impacts of Mountainous Terrain on the Energetics of Hurricane Melissa (2025) | 4d | 2x | 79.0→23.8 (-55.2) | ▼ Decel | 0.18 |
| Probing vacuum birefringence in an Ultrastrong Laser Field via High-energy Gamma-ray Polarimetry | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Equivalent Circuit Modeling of Mutually Resistively Coupled Microwave Cavities with Enhanced Phase Sensitivity Using Thin Metallic Foils | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Simultaneous Misalignment and Mode Mismatch Sensing in Optical Cavities Using Intensity-Only Measurements | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| ICHOR: A Robust Representation Learning Approach for ASL CBF Maps with Self-Supervised Masked Autoencoders | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Compounding Vulnerability: Hub Removal Triggers Cascade Phase Transitions While Degrading Percolation Robustness in Scale-Free Networks | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Trans-Neptunian Binary Mutual Events in the 2020s and 2030s | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Stellar contents and Star Formation in IRAS 18456-0223 | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Reassessing the SIGW Interpretation of PTA Signal: The Role of Third-Order Gravitational Waves and Implications for the PBH Overproduction | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Long-period magnetic activity in the K dwarf GJ 1137 and a new super-Earth on a 9-day orbit | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| High-Pressure Inelastic Neutron Spectroscopy: A true test of Machine-Learned Interatomic Potential energy landscapes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Automated High-Throughput Screening of Polymers Using a Computational Workflow | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Observation of Superfluidity and Meissner Effect of Composite Bosons in GaAs Quantum Hall System | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Multi-fidelity Machine Learning Interatomic Potentials for Charged Point Defects | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Geometry-Adaptive Deep Variational Framework for Phase Discovery in the Landau-Brazovskii Model | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Renormalization and Factorization Scale-Invariant Predictions for the Higgs Rare Decay $H\to J/ψ+γ$ via the Principle of Maximum Conformality | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| The eV-Scale Sterile Neutrino and Neutrinoless Double Beta Decay | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Renormalisation of Chiral Gauge Theories with Non-Anticommuting $γ_5$ at the Multi-Loop Level | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Observational and Thermodynamic aspects of one-dimensional Dark Energy EoS parametrization models | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Ansatz-Free Learning of Lindbladian Dynamics In Situ | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Quantum Simulation of Coupled Harmonic Oscillators: From Theory to Implementation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Heuristics for Shuttling Sequence Optimization for a Linear Segmented Trapped-Ion Quantum Computer | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Decay Rates in Interleaved Benchmarking with Single-Qubit References | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| QGPU: Parallel logic in quantum LDPC codes | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Security bounds for unidimensional discrete-modulated CV-QKD: a Gaussian extremality approach | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A Dynamical Lie-Algebraic Framework for Hamiltonian Engineering and Quantum Control | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Testing Full Mediation of Treatment Effects and the Identifiability of Causal Mechanisms | 4d | 2x | 74.7→23.8 (-50.900000000000006) | ▼ Decel | 0.18 |
| Doubly Robust Estimation of Treatment Effects in Staggered Difference-in-Differences with Time-Varying Covariates | 4d | 2x | 76.9→23.8 (-53.10000000000001) | ▼ Decel | 0.18 |
| Revitalizing AR Process Simulation of Non-Gaussian Radar Clutter via Series-Based Analytic Continuation | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Distributional Equivalence in Linear Non-Gaussian Latent-Variable Cyclic Causal Models: Characterization and Learning | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Cluster-Level Experiments using Temporal Switchback Designs: Precision Gains in Pricing A/B Tests at LATAM Airlines | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Semi-Supervised Generative Learning via Latent Space Distribution Matching | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| Exploiting Subgradient Sparsity in Max-Plus Neural Networks | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| SeekRBP: Leveraging Sequence-Structure Integration with Reinforcement Learning for Receptor-Binding Protein Identification | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Topological Origin of the Diversity of Timescales in Recurrent Neural Circuits | 4d | 2x | 76.6→23.8 (-52.8) | ▼ Decel | 0.18 |
| Revisiting the Role of Foundation Models in Cell-Level Histopathological Image Analysis under Small-Patch Constraints -- Effects of Training Data Scale and Blur Perturbations on CNNs and Vision Transformers | 4d | 2x | 76.3→23.8 (-52.5) | ▼ Decel | 0.18 |
| Two-phase quadratic integrate-and-fire neurons: Exact low-dimensional description for ensembles of finite-voltage neurons | 4d | 2x | 75.4→23.8 (-51.60000000000001) | ▼ Decel | 0.18 |
| Near-Optimal Low-Complexity MIMO Detection via Structured Reduced-Search Enumeration | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Trajectory Tracking for Uncrewed Surface Vessels with Input Saturation and Dynamic Motion Constraints | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| A 360-degree Multi-camera System for Blue Emergency Light Detection Using Color Attention RT-DETR and the ABLDataset | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| Label Hijacking in Track Consensus-Based Distributed Multi-Target Tracking | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| An Approach to Simultaneous Acquisition of Real-Time MRI Video, EEG, and Surface EMG for Articulatory, Brain, and Muscle Activity During Speech Production | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| MIMO Channel Prediction via Deep Learning-based Conformal Bayes Filter | 2d | 2x | 53.7→23.8 (-29.900000000000002) | ▼ Decel | 0.18 |
| PhysiFlow: Physics-Aware Humanoid Whole-Body VLA via Multi-Brain Latent Flow Matching and Robust Tracking | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Algebraic Characterization of Reversible First Degree Cellular Automata over $\mathbb{Z}_d$ | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Detecting RAG Advertisements Across Advertising Styles | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Causality Elicitation from Large Language Models | 4d | 2x | 75.4→23.6 (-51.800000000000004) | ▼ Decel | 0.18 |
| Allocating Resources under Strategic Misrepresentation | 4d | 2x | 75.6→23.6 (-51.99999999999999) | ▼ Decel | 0.18 |
| A Random Rule Model | 4d | 2x | 77.5→23.6 (-53.9) | ▼ Decel | 0.18 |
| A Neural Topic Method Using a Large-Language-Model-in-the-Loop for Business Research | 4d | 2x | 76.0→23.6 (-52.4) | ▼ Decel | 0.18 |
| State-dependent marginal emission factors with autoregressive components | 4d | 2x | 77.4→23.6 (-53.800000000000004) | ▼ Decel | 0.18 |
| A Fully Open-source Implementation of an Analog 8-PAM Demapper for High-speed Communications | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Cheap Thrills: Effective Amortized Optimization Using Inexpensive Labels | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| NaiLIA: Multimodal Nail Design Retrieval Based on Dense Intent Descriptions and Palette Queries | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Dissociating Direct Access from Inference in AI Introspection | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Network Design for Wafer-Scale Systems with Wafer-on-Wafer Hybrid Bonding | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Reachability in VASS Extended with Integer Counters | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| FireBench: Evaluating Instruction Following in Enterprise and API-Driven LLM Applications | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Body-scale NFC for wearables: human-centric body-scale NFC networking for ultra-low-power wearable devices (Demo of UTokyo Kawahara Lab 2025) | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| A Space-Time Galerkin Boundary Element Method for Aeroacoustic Scattering | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| The Inverse Micromechanics Problem given Dielectric Constants for Isotropic Composites with Spherical Inclusions | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Grid-agnostic volume of fluid approach with interface sharpening and surface tension for compressible multiphase flows | 4d | 2x | 78.4→23.6 (-54.800000000000004) | ▼ Decel | 0.18 |
| Optomicrofluidic measurement of particle-encapsulated droplet system | 4d | 2x | 78.4→23.6 (-54.800000000000004) | ▼ Decel | 0.18 |
| An analytical-numerical coupled model of liquid droplet impact on solid material surfaces | 4d | 2x | 78.4→23.6 (-54.800000000000004) | ▼ Decel | 0.18 |
| Separation induced transition in a low pressure turbine under varying compressibility | 4d | 2x | 78.4→23.6 (-54.800000000000004) | ▼ Decel | 0.18 |
| Technical design report of a complete and compact broadband high-harmonics femtosecond beamline based on a modular hollow waveguide for photons generation centered on the upper region of the extreme ultraviolet spectral range | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Cubic magneto-optic Kerr effect in Co(111) thin films | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| When minor issues matter: symmetries, pluralism, and polarization in similarity-based opinion dynamics | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| False Metallization in Short-Ranged Machine Learned Interatomic Potentials | 4d | 2x | 75.4→23.6 (-51.800000000000004) | ▼ Decel | 0.18 |
| GASTON-GP: Source catalogue and millimetre variability of massive protostellar objects | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| On curvature corrections for field theory cosmic strings | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Exploring the chemical evolution in hot molecular cores | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Accelerated size evolution in the FirstLight simulations from z=14 to z=5 | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Measurement Induced Asymmetric Entanglement in Deconfined Quantum Critical Ground State | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Correcting hybrid density functionals to model Y6 and other non-fullerene acceptors | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Lattice dynamics of the charge density wave compounds TaTe$_4$ and NbTe$_4$ and their evolution across solid solutions | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Precise control of crystallography and magnetism in focused-ion-beam transformed iron-nickel thin films | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| First-principles calculation of coherence length and penetration depth based on density functional theory for superconductors | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| TeV-scale unification of light dark matter and neutrino mass | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| New Improved Schwarzschild Black Hole and Its Thermodynamics and Topological Classification | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Nonreciprocal transparency windows, Fano resonance, and slow/fast light in a membrane-in-the-middle magnomechanical system induced by the Barnett effect | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Parsimonious Quantum Low-Density Parity-Check Code Surgery | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Markov-Based Modelling for Reservoir Management: Assessing Reliability and Resilience | 4d | 2x | 76.3→23.6 (-52.699999999999996) | ▼ Decel | 0.18 |
| Detection and Identification of Penguins Using Appearance and Motion Features | 4d | 2x | 76.0→23.6 (-52.4) | ▼ Decel | 0.18 |
| Uncertainty and Autarky: Cooperative Game Theory for Stable Local Energy Market Partitioning | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Video-based Locomotion Analysis for Fish Health Monitoring | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Lambda-randomization: multi-dimensional randomized response made easy | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Roomify: Spatially-Grounded Style Transformation for Immersive Virtual Environments | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Accretion Disk Perturbations and Their Effects on Kerr Black Hole Superradiance and Gravitational Atom Evolution | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| On the fair abatement of riparian pollution | 4d | 2x | 77.7→23.6 (-54.1) | ▼ Decel | 0.18 |
| Judge Reliability Harness: Stress Testing the Reliability of LLM Judges | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| A monitoring system for collecting and aggregating metrics from distributed clouds | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Integrated cooperative localization of heterogeneous measurement swarm: A unified data-driven method | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Auto-Generating Personas from User Reviews in VR App Stores | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Statistical Effort Modelling of Game Resource Localisation Attacks | 4d | 2x | 74.7→23.6 (-51.1) | ▼ Decel | 0.18 |
| Beyond Text: Aligning Vision and Language for Multimodal E-Commerce Retrieval | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| LLM-Guided Decentralized Exploration with Self-Organizing Robot Teams | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| An efficient and accurate numerical method for computing the ground states of three-dimensional rotating dipolar Bose-Einstein condensates under strongly anisotropic trap | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Regularization of the superposition principle: Potential theory meets Fokker-Planck equations | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Dynamic Wettability Modulation of Textured, Soft and LIS Interfaces Using Electrowetting | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Dynamic properties in a collisional model for confined granular fluids. A review | 4d | 2x | 76.2→23.6 (-52.6) | ▼ Decel | 0.18 |
| Atmospheric effects on cosmic-ray muon rate at high latitude (78.9°N) | 4d | 2x | 75.4→23.6 (-51.800000000000004) | ▼ Decel | 0.18 |
| Impact of perturbed eddy-viscosity modeling on stability and shape sensitivity of the hydro-turbine vortex rope using linearized Reynolds-averaged Navier-Stokes equations | 4d | 2x | 79.0→23.6 (-55.4) | ▼ Decel | 0.18 |
| Inverse-design of two-dimensional magnonic crystals via topology optimization with frequency-domain micromagnetics | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Fast array-based particle coincidence detection in a TimePix3-based velocity map imaging instrument | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Spectral dynamics reservoir computing for high-speed hardware-efficient neuromorphic processing | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Stochastic inner workings of subdiffraction laser writing | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Graphs are focal hypergraphs: strict containment in higher-order interaction dynamics | 4d | 2x | 76.9→23.6 (-53.300000000000004) | ▼ Decel | 0.18 |
| Resolving the sub-parsec circumnuclear density profiles of quiescent galaxies: Evidence for Bondi accretion flows in tidal disruption event hosts | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| HC$_3$N, H$^{13}$CN, and HN$^{13}$C in molecular cores evolving towards star-forming regions | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Extreme Quantum Cognition Machines for Deliberative Decision Making | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Non-equilibrium bosonization of fractional quantum Hall edges | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Lepton mixing and charged lepton flavour violation from inverse seesaw with non-degenerate heavy states | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Canonical Quantisation of Bound and Unbound WQFT | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Computing Green's functions and improving ground state energy estimation on quantum computers with Liouvillian recursion | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Advantage of flexible catalysis for entanglement and quantum thermodynamics | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Classical shadows for non-iid quantum sources | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| How important are the genes to explain the outcome - the asymmetric Shapley value as an honest importance metric for high-dimensional features | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| The Pivotal Information Criterion | 4d | 2x | 76.3→23.6 (-52.699999999999996) | ▼ Decel | 0.18 |
| Neural geometry in the human hippocampus enables generalization across spatial position and gaze | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| DEBISS: a Corpus of Individual, Semi-structured and Spoken Debates | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Computing Scaled Relative Graphs of Discrete-time LTI Systems from Data | 2d | 2x | 53.7→23.6 (-30.1) | ▼ Decel | 0.18 |
| Computational Complexity of Alignments | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Local limits of uniform triangulations with boundaries in high genus | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Comparison of data-driven symmetry-preserving closure models for large-eddy simulation | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Solution of a bilevel optimistic scheduling problem on parallel machines | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Robust adaptive NMPC using ellipsoidal tubes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Impact of scissors-correction schemes on second-harmonic generation in ultraviolet nonlinear-optical crystals | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Pulse-duration-sensitive high harmonics and attosecond locally-chiral light from a chiral topological Weyl semimetal | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Total Angular Momentum Coherent State Fields | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Sub-wavelength mid-infrared imaging of locally driven photocurrents using diamond campanile probes | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| Surprising increase of electron temperature in metal-rich star-forming region | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Sensitivity of a closed dielectric haloscope to axion dark matter | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Universal quantum computation with group surface codes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Manipulation of ferromagnetism with a light-driven nonlinear Edelstein-Zeeman field | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Domain-Direct Band Gaps: Classification and Material Realization | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Scattering amplitudes in dimensionless quadratic gravity coupled to QED | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| 7D (non-)susy vacua & DWs from dynamical open strings | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Intrinsic Width of the flux tube in 2+1 dimensional Yang-Mills theories | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Gauge-string duality, monomial bases and graph determinants | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Effective vertexes in magnetized quark-gluon plasma | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Muon collider experiments as electron/positron beam sources: case studies of new light-particle searches | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| High-performance syndrome extraction circuits for quantum codes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Constant depth magic state cultivation with Clifford measurements by gauging | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Achieving Thresholds via Standalone Belief Propagation on Surface Codes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Uniform process tensor approach for the calculation of multi-time correlation functions of non-Markovian open systems | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Electric current dynamics in the stellarator coil winding surface model | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| Optimal strategies in Markov decision processes with finitely additive evaluations | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| Is an investor stolen their profits by mimic investors? Investigated by an agent-based model | 4d | 2x | 76.9→23.2 (-53.7) | ▼ Decel | 0.18 |
| ROScopter: A Multirotor Autopilot based on ROSflight 2.0 | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Bayesian Adversarial Privacy | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| Generalized matching decoders for 2D topological translationally-invariant codes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Towards a B+-tree with Fluctuation-Free Performance | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Wire Your Way: Hardware-Contextualized Guidance and In-situ Tests for Personalized Circuit Prototyping | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| New Berry-Esseen bounds for parameter estimation of Gaussian processes observed at high frequency | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Global versus local internal-external field separation on the sphere: a Hardy-Hodge perspective | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Wave interactions in a screeching jet | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Reproducing anomalous transport coefficients from electro-static tokamak edge turbulent dynamics | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Waiting-time based entropy estimators in continuous space without Markovian events | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Approximate master equations for the spatial public goods game | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Large-scale Integration of Experimental and Computational Data for 2D Materials | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Accelerating Feynman Integral Evaluation by Avoiding Contour Deformation | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Simplified circuit-level decoding using Knill error correction | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Robust and optimal control of open quantum systems | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| False traps on quantum-classical optimization landscapes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Emergence of Turbulence in a counterflow geometry of 2D Polariton Quantum Fluids | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Quantum Weight Reduction with Layer Codes | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Generic Camera Calibration using Blurry Images | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| PolyBench: A Benchmark for Compositional Reasoning in Polyphonic Audio | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Self-organization of cavity solitons in Brillouin-Kerr ring resonators | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| The self-generation of core fields and electron scattering in flux ropes during magnetic reconnection | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| 3D Rotation of the Open Cluster NGC 2516 | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Antialtermagnetic Magnons and Nonrelativistic Thermal Edelstein Effect | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Crystal growth and magnetic properties of spin-$1/2$ distorted triangular lattice antiferromagnet CuLa$_2$Ge$_2$O$_8$ | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Low-depth amplitude estimation via statistical eigengap estimation | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Recursive Magic State Distillation on the Surface Code | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Index and Robustness of Mixed Equilibria: An Algebraic Approach | 4d | 2x | 76.9→23.2 (-53.7) | ▼ Decel | 0.18 |
| A class of stochastic control problems with state constraints | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Predicting oscillations in complex networks with delayed feedback | 4d | 2x | 76.6→23.2 (-53.39999999999999) | ▼ Decel | 0.18 |
| The Complexity of the Constructive Master Modality | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| The role of spatial scales in assessing urban mobility models | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| 2D capillary liquid drops with constant vorticity: rotating waves existence and a conditional energetic stability result for rotating circles | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Long-lived metastable states in the 4f$^{13}$5d6s configuration of Yb$^+$ | 4d | 2x | 75.4→23.2 (-52.2) | ▼ Decel | 0.18 |
| Emergence of the geometric contribution to the superfluid density in the inner crust of neutron stars | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Double-sphere enhanced optomechanical spectroscopy constrains symmetron dark energy | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| A loop quantization of the marginally bound Lemaître-Tolman-Bondi dust model | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Calculating trace distances of bosonic states in Krylov subspace | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Local strategies are pretty good at computing Boolean properties of quantum sequences | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Interplay of internal and external coupling phases in cavity magnonics: from level repulsion to attraction | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| A spectral inference method for determining the number of communities in networks | 4d | 2x | 76.6→23.2 (-53.39999999999999) | ▼ Decel | 0.18 |
| The effect of a toroidal opinion space on opinion bi-polarisation | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Boundary stabilization of flows in networks of open channels modeled by Saint-Venant equations | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| A likelihood analysis for gamma-ray background models | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Thin amorphous molybdenum silicide superconducting shells around individual nanowires deposited via magnetron co-sputtering | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Can Light Cross a Singularity? Exact Solutions from Analogue Gravity | 2d | 2x | 53.7→23.2 (-30.500000000000004) | ▼ Decel | 0.18 |
| Thresholds for colouring the random Borsuk graph | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Tree codes and sort-and-sweep algorithms for neighborhood computation: A cache-conscious comparison | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Constraints on millicharged particles from thunderstorms on the Solar system planets | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Strong breaking of black-hole uniqueness from coexisting scalarization mechanisms | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| BabAR: from phoneme recognition to developmental measures of young children's speech production | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Maximum of sparsely equicorrelated Gaussian fields and applications | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Volumetric effects in viscous flows in circular and annular tubes with wavy walls | 4d | 2x | 78.4→23.1 (-55.300000000000004) | ▼ Decel | 0.18 |
| Progress on artificial flat band systems: classifying, perturbing, applying | 4d | 2x | 76.3→23.1 (-53.199999999999996) | ▼ Decel | 0.18 |
| Evaluation of Feynman integrals via numerical integration of differential equations | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Constraint Learning for Non-confluent Proof Search | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Dyson Brownian motion on a Jordan curve | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Drift parameter estimation in the double mixed fractional Brownian model via solutions of Fredholm equations with singular kernels | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Accelerating massive galaxy formation with primordial black hole seed nuclei | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Robust estimation via $γ$-divergence for diffusion processes | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Controlled fields, rough stochastic calculus, and Itô-Wentzell-Alekseev-Gröbner identities | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| Air shower development through the time dependence of its induced electric field | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| A Method to Derate the Rate-Dependency in the Pass-Band Droop of Comb Decimators | 2d | 2x | 53.7→23.1 (-30.6) | ▼ Decel | 0.18 |
| On Solving String Equations via Powers and Parikh Images | 2d | 2x | 53.7→22.8 (-30.900000000000002) | ▼ Decel | 0.18 |
| 2-Coloring Cycles in One Round | 4d | 2x | 75.4→22.8 (-52.60000000000001) | ▼ Decel | 0.18 |
| Regularization by noise for Gevrey well-posedeness of a weakly hyperbolic operator | 2d | 2x | 53.7→22.8 (-30.900000000000002) | ▼ Decel | 0.18 |
| History-Deterministic Büchi Automata are Succinct | 2d | 2x | 53.7→22.8 (-30.900000000000002) | ▼ Decel | 0.18 |
| Higher harmonics in Mott-Hubbard insulators as sensors | 2d | 2x | 53.7→22.6 (-31.1) | ▼ Decel | 0.18 |
| Modification to Fully Homomorphic Modified Rivest Scheme | 2d | 2x | 53.7→22.6 (-31.1) | ▼ Decel | 0.18 |

{{SECTION_3_2_CONTENT}}

### 3.3 Signal Status Summary

| Status | Count | Ratio |
|------|---|------|
| New | 1854 | 80% |
| Strengthening | 0 | 0% |
| Recurring | 9 | 0% |
| Weakening | 446 | 19% |
| Faded | 532 | — |

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

#### Multi&Global-News-Exclusive Signals

{{SECTION_4_3_WF4_EXCLUSIVE}}

#### Naver↔Direct-News Cross-Validation

{{SECTION_4_3_NAVER_DIRECTNEWS_CROSS}}

#### Temporal Cross-Validation

No cross-workflow temporal correlations

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

### 7.6 Signal Evolution Timeline Summary

> Full timeline map: see `timeline-map-{date}.md`

{{INT_TIMELINE_SUMMARY}}

---

## 8. Appendix

### 8.1 Full Signal List

{{SECTION_8_1_FULL_SIGNAL_TABLE}}

### 8.2 Source List

{{SECTION_8_2_SOURCE_LIST}}

### 8.3 Methodology

{{SECTION_8_3_METHODOLOGY}}

### 8.4 Workflow Execution Summary

| Item | WF1 (General) | WF2 (arXiv) | WF3 (Naver) | WF4 (Multi&Global) | Integrated |
|------|-----------|-------------|-------------|-------------|------|
| Source Count | N/A | 1 (arXiv) | 1 (NaverNews) | N/A | N/A |
| Collected Signals | 24 | 686 | 251 | 1372 | 2333 |
| After Dedup | 0 | 0 | 0 | 0 | 0 |
| Top Signals | 24 | 686 | 251 | 1372 | 20 |
| Avg pSST | 31.3 | 23.6 | 5.3 | 4.7 | 16.2 |
| Execution Time | N/A | N/A | N/A | N/A | N/A |
