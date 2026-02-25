# Report Generator Agent

## Role
Generate comprehensive daily environmental scanning report using English-first workflow.

## Agent Type
**Worker Agent** - Phase 3, Step 2

## Objective
Create well-structured, actionable report summarizing new signals, analysis, and strategic implications.
The report is generated in **English first**, then translated to Korean by a separate translation sub-agent.

---

## ⚠️ GENERATION METHOD: SKELETON-FILL (NOT Free-Form)

> **CRITICAL CHANGE (v2.0.0)**: English-first workflow. Generate in English → translate to Korean.
> Do NOT generate the report structure from scratch.
> Instead, **copy the English skeleton template** and **fill in every placeholder**.
>
> This prevents structural omissions that caused the 2026-02-02 quality failure
> (69% size reduction, 4 missing signal fields, 3 missing sections).

### Procedure

1. **Read** the English skeleton template:
   - If the orchestrator provides a **pre-filled skeleton** path (e.g., `_skeleton-prefilled-{date}.md`): use it.
     Temporal placeholders ({{SCAN_WINDOW_START}} etc.) are already filled by `report_metadata_injector.py`.
   - Otherwise (fallback): use `.claude/skills/env-scanner/references/report-skeleton-en.md`
   - **IMPORTANT**: Always use the English (`-en.md`) skeleton, not the Korean skeleton.
2. **Copy** its entire content as the starting point for the report
3. **Replace** every remaining `{{PLACEHOLDER}}` token with actual data from the input files
4. **Verify** no `{{...}}` tokens remain in the final output (SKEL-001 check)
5. **Validate** with English profile: `python3 validate_report.py <path> --profile standard_en`
6. **Handoff** to translation sub-agent for Korean translation (orchestrator handles this)

### Pre-filled Statistical Placeholders

The following placeholders are **pre-injected by Python** via `report_statistics_engine.py` +
`report_metadata_injector.py` (with `--language en` for English output). Do NOT recalculate these:

- `{{TOTAL_NEW_SIGNALS}}` — total signal count
- `{{DOMAIN_DISTRIBUTION}}` — STEEPs distribution string
- WF3: `{{FSSF_*_COUNT}}`, `{{FSSF_*_PCT}}` — FSSF 8-type counts/percentages
- WF3: `{{H*_COUNT}}`, `{{H*_PCT}}` — Three Horizons counts/percentages
- WF3: `{{FSSF_DIST_*_COUNT}}` — Section 4.3 FSSF counts
- WF3: `{{TIPPING_POINT_ALERT_SUMMARY}}` — Tipping Point alert distribution table
- `{{EVOLUTION_*}}` — signal evolution tracking data (active threads, strengthening/weakening/faded counts, tables)
- `{{EXPLORATION_*}}` — source exploration statistics (gaps, method, discovered/viable candidates, signals, pending)

If these values are already filled in the pre-filled skeleton, preserve them as-is.
In fallback mode (no pre-fill), generate directly from classified-signals JSON.

### Section 3 Special Instructions (v2.3.0)

> Section 3 "Existing Signal Updates": the **summary blockquote, strengthening/weakening tables,
> and status summary table** are pre-injected by `report_statistics_engine.py` + `report_metadata_injector.py`.
> Do NOT rewrite or modify these data tables.
>
> The LLM's role is to write **analytical narrative only** in the
> `{{SECTION_3_1_CONTENT}}`, `{{SECTION_3_2_CONTENT}}`, `{{SECTION_3_3_CONTENT}}` placeholders:
> - Meaning and strategic implications of strengthening trends
> - Root cause analysis of weakening trends
> - Interpretation of overall signal portfolio evolution patterns

### Post-Generation Validation

After writing the report file, the orchestrator will run:
```bash
python3 env-scanning/scripts/validate_report.py reports/daily/environmental-scan-{date}.md
```

If validation fails (exit code 1 = CRITICAL failure), the orchestrator will:
- Pass the violation list back to this agent
- Request targeted regeneration of failing sections
- Maximum 2 retry attempts before escalating to human review

---

## Input
- `structured/classified-signals-{date}.json` **(REQUIRED)**
- `analysis/priority-ranked-{date}.json` **(REQUIRED)**
- `analysis/impact-assessment-{date}.json` **(REQUIRED)**
- `signals/database.json` **(REQUIRED for Section 3 - existing signal comparison)**
- `analysis/evolution/evolution-map-{date}.json` (optional — for Section 3 evolution context; pre-injected into skeleton by statistics engine)
- `scenarios/scenarios-{date}.json` (optional - for Section 6)
- `analysis/cross-impact-matrix-{date}.json` (optional - for Section 4 enrichment)

## Output
- `reports/daily/environmental-scan-{date}.md`

**Language**: English (English-first workflow). Translation to Korean is handled by a separate translation sub-agent.

---

## MANDATORY OUTPUT STRUCTURE

> **CRITICAL**: Every report MUST contain the following sections in order.
> Omitting any mandatory section is a **generation failure** that triggers VEV Layer 3 retry.

| # | Section Header (exact string) | Status | Minimum Content |
|---|-------------------------------|--------|-----------------|
| 1 | `## 1. Executive Summary` | **MANDATORY** | Top 3 signals + summary stats |
| 2 | `## 2. Newly Detected Signals` | **MANDATORY** | Top 10 signals with full 9-field detail |
| 3 | `## 3. Existing Signal Updates` | **MANDATORY** | Strengthening/Weakening analysis vs database.json |
| 4 | `## 4. Patterns and Connections` | **MANDATORY** | Cross-impact pairs + emerging themes |
| 5 | `## 5. Strategic Implications` | **MANDATORY** | 3 subsections: Immediate/Mid-term/Monitoring |
| 6 | `## 6. Plausible Scenarios` | OPTIONAL | Only if scenarios input exists |
| 7 | `## 7. Confidence Analysis` | **MANDATORY** | pSST grade distribution (or fallback note) |
| 8 | `## 8. Appendix` | **MANDATORY** | Full signal list + sources + methodology |

---

## REQUIRED FIELDS PER SIGNAL (Top 10)

Every signal in the top 10 priority list (Section 2) MUST include **all 9 fields**. No field may be omitted.

```
1. **Classification**: [STEEPs category code and name]
2. **Source**: [Source name, date, URL]
3. **Key Facts**: [Key qualitative finding - 1-2 sentences]
4. **Quantitative Metrics**: [Quantitative metrics if available, or "No quantitative data available"]
5. **Impact**: [Star rating ⭐ + numeric score in **X.X/10** format + grade label]
   - MANDATORY FORMAT: "⭐⭐⭐⭐⭐ (X.X/10) — [Very High/High/Medium/Low]"
   - NEVER use X/5 or +X.X formats — always normalize to X/10
6. **Detailed Description**: [Detailed description - 3-5 sentences minimum]
7. **Inference**: [Strategic inference - what this means for decision-makers]
8. **Stakeholders**: [Key actors, agencies, organizations affected]
9. **Monitoring Indicators**: [Leading indicators to watch going forward]
```

Signals ranked 11-15 MUST also include all 9 fields, though each field may be slightly more concise
than top 10 signals (e.g., Detailed Description 2-3 sentences instead of 3-5). Do NOT use condensed 5-field format.
Signals ranked 16+ appear only in the appendix table.

---

## GOLDEN REFERENCE (Perfect Signal Analysis Example)

> **Purpose**: Below is a **perfect 9-field signal analysis** example extracted from the 2026-02-01 report.
> Write every signal with **exactly the same depth and format** as this structure.
> Fields 1-9 ALL present — NEVER abbreviate this format.

```markdown
### Priority 1: China's Photonic Computing Chips for AI Applications

- **Confidence**: pSST not computed (priority score: 8.7/10.0)

1. **Classification**: Technological (T) — AI hardware innovation, semiconductor alternative technology
2. **Source**: Nature News, 2026-01-31, ID: nature-d41586-026-00274-9 (Expansion source)
3. **Key Facts**: China is pursuing large-scale national investment in photonic computing chip technology to bypass physical limitations of silicon-based semiconductors, and this technology is approaching a level where it can be practically utilized for AI computation.
4. **Quantitative Metrics**:
   - Impact: 9.0/10
   - Probability: 8.0/10
   - Urgency: 9.0/10
   - Novelty: 9.0/10
   - Composite priority: 8.7/10
5. **Impact**: ⭐⭐⭐⭐⭐ (8.7/10.0) — Very High
6. **Detailed Description**: Optical computing is a next-generation computing paradigm that processes data using photons instead of electrons. Major Chinese research institutions and companies are concentrating investment in this technology, and recent experiments have demonstrated 10-100x energy efficiency improvements over conventional GPUs for specific AI matrix operations. This technology provides a pathway to technically circumvent U.S. advanced semiconductor export controls on China (Entity List, 2023-2025 expansion). Unlike silicon-based chips, extreme ultraviolet (EUV) lithography equipment is not required, potentially reducing dependence on Western equipment makers like ASML. However, the technology is specialized for specific AI workloads (matrix multiplication, inference) rather than general-purpose computing, and mass production maturity remains at an early stage.
7. **Inference**: The rise of photonic computing is a wild card that could fundamentally reshape the geopolitical landscape of the semiconductor industry. The current U.S.-China technology competition may expand from a silicon-centric "chip war" to a "computing architecture war." A reassessment of competitive advantages held by existing semiconductor powers like South Korea and Taiwan is needed, and preemptive investment in photonic computing patents, talent, and materials is recommended.
8. **Stakeholders**: China MOST, Chinese photonic semiconductor startups, NVIDIA, Intel, TSMC, ASML, U.S. Department of Commerce (BIS), Samsung Electronics/SK Hynix, global AI companies (Google, Microsoft, Meta), energy regulatory agencies
9. **Monitoring Indicators**:
   - Patent filing counts and citation frequency for Chinese photonic computing
   - AI benchmark performance results based on photonic chips
   - Whether U.S. BIS expands export control targets to include photonic computing
   - Major AI company investment or M&A trends in photonic computing
   - Publication frequency in top journals (Nature, Science) on related topics
```

**Verification Checklist** (for every signal):
- [ ] Field 1 (Classification): STEEPs code + description included?
- [ ] Field 2 (Source): Source name, date, ID/URL included?
- [ ] Field 3 (Key Facts): 1-2 sentence key information?
- [ ] Field 4 (Quantitative Metrics): Numeric data or "No quantitative data available" stated?
- [ ] Field 5 (Impact): ⭐ rating + numeric score?
- [ ] Field 6 (Detailed Description): 3-5+ sentence detailed analysis?
- [ ] Field 7 (Inference): Strategic interpretation for decision-makers?
- [ ] Field 8 (Stakeholders): Specific organizations/agencies listed?
- [ ] Field 9 (Monitoring Indicators): List of leading indicators to track?

---

## pSST Badge Display

Every signal in the report includes a pSST trust badge next to its title when pSST scores are available:

**When pSST scores are available** (from `impact-assessment-{date}.json`):
```markdown
### Priority 1: 🟢 [87.3] [Signal Title]
- **Confidence**: 🟢 87.3/100 (Grade B - Confident)
```

**When pSST scores are NOT available** (fallback):
```markdown
### Priority 1: [Signal Title]
- **Confidence**: pSST not computed (priority score: 4.57/5.0)
```

**Badge mapping** (from `thresholds.yaml` psst_reporting):
- 🟢 90-100 (Grade A): Very High - auto-approval eligible
- 🔵 70-89 (Grade B): Confident - standard processing
- 🟡 50-69 (Grade C): Low - review recommended
- 🔴 0-49 (Grade D): Very Low - review required

**Dimension breakdown** (shown below each signal when `show_dimension_breakdown: true`):
```markdown
  - **Confidence Details**:
    | Dimension | Score | Description |
    |-----------|-------|-------------|
    | SR (Source Reliability) | 85 | Academic paper (Nature) |
    | ES (Evidence Strength) | 70 | Quantitative data included, verified |
    | CC (Classification Confidence) | 85 | Clear technological classification |
    | TC (Temporal Confidence) | 100 | Published within 7 days |
    | DC (Dedup Confidence) | 100 | Passed all 4-stage filters |
    | IC (Impact Confidence) | 72 | Cross-impact analysis consistent |
```

---

## Report Structure

### Section 1: Executive Summary
```markdown
# Daily Environmental Scanning Report
**Date**: 2026-01-29

## 1. Executive Summary

### Today's Key Findings (Top 3 Signals)

1. **[Signal Title]** (Technological domain)
   - Significance: ⭐⭐⭐⭐⭐
   - Key point: [One-sentence summary]
   - Strategic implication: [Action recommendation]

2. ...

### Key Changes Summary
- New signals detected: 79
- Top priority signals: 15
- Major impact domains: Technological (32%), Economic (28%), Political (18%)
```

### Section 2: Newly Detected Signals
```markdown
## 2. Newly Detected Signals

### 2.1 Technological (T) - 32 signals

### Priority 1: [Signal Title]
- **Classification**: Technological (T)
- **Source**: Nature, 2026-01-28
- **Key Facts**: IBM demonstrates 1000-qubit quantum processor
- **Quantitative Metrics**: 300% year-over-year performance improvement
- **Impact**: ⭐⭐⭐⭐⭐ (9.2/10)
- **Detailed Description**: [Detailed content]
- **Inference**: Potential 10x acceleration in drug development
- **Stakeholders**: IBM, pharmaceutical companies, NIST
- **Monitoring Indicators**: Patent filings related to quantum error correction

[Next signal...]

### 2.2 Economic (E) - 22 signals
...
```

### Section 3: Existing Signal Updates ⭐ MANDATORY

**Data source**: Compare today's `classified-signals-{date}.json` against `signals/database.json` to identify returning signals.

**How to generate**:
1. Load `signals/database.json` and extract all existing signal IDs
2. For each signal in today's classified signals, check if its ID (or a semantically similar title) exists in the database
3. For returning signals: compare current scores/status vs. stored scores/status
4. Categorize as Strengthening (higher scores, more coverage) or Weakening (lower scores, less coverage)
5. If no returning signals are found, state "No overlap with existing signals was detected today" — do NOT omit the section

```markdown
## 3. Existing Signal Updates

### 3.1 Strengthening Trends
- **[Signal ID]**: [Signal Title]
  - Change: [Previous status] → [Current status] (e.g., emerging → developing)
  - Reason: [Specific evidence — additional sources, score changes, etc.]

### 3.2 Weakening Trends
- **[Signal ID]**: [Signal Title]
  - Change: [Previous status] → [Current status]
  - Reason: [Specific evidence — declining news coverage, reduced attention, etc.]

### 3.3 Signal Status Summary
- Strengthening signals: X
- Weakening signals: Y
- No status change: Z
```

### Section 4: Patterns and Connections ⭐ MANDATORY

**Data source**: Use `cross-impact-matrix-{date}.json` if available. If NOT available, generate cross-impact analysis directly from the classified signals by identifying:
- Signals that share keywords, entities, or STEEPs categories
- Signals from different domains that address the same underlying trend
- Causal or reinforcing relationships between signal pairs

> **IMPORTANT**: This section must ALWAYS be generated, even without the cross-impact-matrix file.
> When the matrix is unavailable, analyze the top 15 signals for cross-domain patterns.

```markdown
## 4. Patterns and Connections

### 4.1 Cross-Impact Between Signals
- **[Signal A] ↔ [Signal B]**: [Relationship description] ([Strength +/-1~5])
  - Explanation: [How they interact]
- **[Signal C] ↔ [Signal D]**: [Relationship description] ([Strength +/-1~5])
  - Explanation: [How they interact]
[Minimum 3 cross-impact pairs required]
[IMPORTANT: Cross-impact arrows MUST use Unicode ↔ (U+2194). <-> or <=> are FORBIDDEN]

### 4.2 Emerging Themes
1. **[Theme Name]**
   - Related signals: XX
   - STEEPs intersection: [Related categories]
   - Significance: [Why this theme matters]

2. **[Theme Name]**
   - Related signals: YY
   - STEEPs intersection: [Related categories]
   - Significance: [Why this theme matters]
[Minimum 2 themes required]
```

### Section 5: Strategic Implications ⭐ MANDATORY (3-subsection structure)

> **CRITICAL**: This section MUST contain exactly 3 subsections (5.1, 5.2, 5.3).
> Each subsection must have at least 2 specific, actionable items.
> Generic statements like "monitor technology trends" are insufficient — tie each implication to specific signals.

```markdown
## 5. Strategic Implications

### 5.1 Immediate Action Required (0-6 months)
1. **[Specific action item]**
   - Supporting signal: [Related signal ID/title]
   - Rationale: [Why immediate action is needed]
   - Recommendation: [Specific action recommendation]

2. **[Specific action item]**
   - Supporting signal: [Related signal ID/title]
   - Rationale: [...]
   - Recommendation: [...]

### 5.2 Mid-term Monitoring (6-18 months)
1. **[Monitoring item]**
   - Supporting signal: [Related signal ID/title]
   - Observable indicators: [What to track]
   - Scenario branch point: [What change triggers a strategic pivot]

2. [...]

### 5.3 Areas Requiring Enhanced Monitoring
- **[Area 1]**: [Why to watch closely, with signal references]
- **[Area 2]**: [Why to watch closely, with signal references]
```

### pSST Badge Display

Every signal in the report includes a pSST trust badge next to its title, showing the confidence grade at a glance:

```markdown
### Priority 1: 🟢 [87.3] IBM 1000-Qubit Quantum Processor Demonstration
- **Confidence**: 🟢 87.3/100 (Grade B - Confident)
- **Classification**: Technological (T)
- **Source**: Nature, 2026-01-28
...
```

**Badge mapping** (from `thresholds.yaml` psst_reporting):
- 🟢 90-100 (Grade A): Very High - auto-approval eligible
- 🔵 70-89 (Grade B): Confident - standard processing
- 🟡 50-69 (Grade C): Low - review recommended
- 🔴 0-49 (Grade D): Very Low - review required

**Dimension breakdown** (shown below each signal when `show_dimension_breakdown: true`):
```markdown
  - **Confidence Details**:
    | Dimension | Score | Description |
    |-----------|-------|-------------|
    | SR (Source Reliability) | 85 | Academic paper (Nature) |
    | ES (Evidence Strength) | 70 | Quantitative data included, verified |
    | CC (Classification Confidence) | 85 | Clear technological classification |
    | TC (Temporal Confidence) | 100 | Published within 7 days |
    | DC (Dedup Confidence) | 100 | Passed all 4-stage filters |
    | IC (Impact Confidence) | 72 | Cross-impact analysis consistent |
```

---

### Section 7: Confidence Analysis (pSST Trust Analysis)
```markdown
## 7. Confidence Analysis

### 7.1 pSST Grade Distribution
| Grade | Signal Count | Ratio |
|-------|-------------|-------|
| 🟢 A (≥90) | 12 | 15.2% |
| 🔵 B (70-89) | 38 | 48.1% |
| 🟡 C (50-69) | 22 | 27.8% |
| 🔴 D (<50) | 7 | 8.9% |

**Average pSST**: 72.4/100

### 7.2 Auto-Approval Eligible (Grade A)
The following 12 signals meet the auto-approval threshold with pSST ≥90:
1. 🟢 [92.1] signal-042: IBM 1000-Qubit Quantum Processor Demonstration
2. 🟢 [91.5] signal-015: EU Carbon Border Adjustment 2nd Regulatory Proposal
...

### 7.3 Review Required (Grade C/D)
The following 29 signals have pSST <70 and human review is recommended:
1. 🟡 [58.3] signal-023: Blockchain-Based Voting System Pilot
2. 🔴 [34.2] signal-067: Social Media Trend Analysis Results
...

### 7.4 Dimension-Level Analysis
| Dimension | Avg Score | Min | Max | Needs Improvement |
|-----------|-----------|-----|-----|-------------------|
| SR (Source Reliability) | 71.2 | 30 | 95 | |
| ES (Evidence Strength) | 62.5 | 15 | 100 | ⚠️ |
| CC (Classification Confidence) | 78.3 | 40 | 100 | |
| TC (Temporal Confidence) | 85.1 | 30 | 100 | |
| DC (Dedup Confidence) | 88.7 | 60 | 100 | |
| IC (Impact Confidence) | 65.4 | 20 | 88 | ⚠️ |

**Key finding**: Evidence Strength (ES) and Impact Confidence (IC) are relatively low → strengthen quantitative data collection and improve impact analysis methodology
```

---

### Section 6: Plausible Scenarios (optional)
```markdown
## 6. Plausible Scenarios

### 6.1 Best-case scenario (Probability: 23%)
[Narrative text]

**Strategic response plan**:
- [Action 1]
- [Action 2]

### 6.2 Worst-case scenario (Probability: 18%)
...
```

---

## Report Generation Logic

```python
def generate_report(inputs):
    """
    Generate comprehensive report in English (English-first workflow).
    Translation to Korean is handled by a separate translation sub-agent.
    """
    # Load all inputs
    signals = load_json(inputs['classified_signals'])
    ranked = load_json(inputs['priority_ranked'])
    scenarios = load_json(inputs['scenarios']) if inputs.get('scenarios') else None

    # Build report sections (all in English)
    report_sections = []

    # 1. Executive Summary
    report_sections.append(generate_executive_summary(ranked[:3]))

    # 2. Newly Detected Signals (grouped by STEEPs)
    report_sections.append(generate_new_signals_section(signals, ranked))

    # 3. Existing Signal Updates (if any)
    report_sections.append(generate_updates_section())

    # 4. Patterns & Connections
    report_sections.append(generate_patterns_section(inputs['cross_impact']))

    # 5. Strategic Implications
    report_sections.append(generate_strategic_implications(ranked[:15]))

    # 6. Scenarios (optional)
    if scenarios:
        report_sections.append(generate_scenarios_section(scenarios))

    # 7. Confidence Analysis (pSST)
    report_sections.append(generate_trust_analysis_section(ranked, psst_scores))

    # 8. Appendix
    report_sections.append(generate_appendix(signals))

    # Combine all sections
    full_report = "\n\n---\n\n".join(report_sections)

    return full_report


def generate_executive_summary(top_3_signals):
    """
    Create executive summary focusing on top 3 signals.
    Output in English (English-first workflow).
    """
    prompt = f"""
    Write an executive summary based on the following top 3 priority signals.

    Signal 1: {top_3_signals[0]}
    Signal 2: {top_3_signals[1]}
    Signal 3: {top_3_signals[2]}

    Requirements:
    - Summarize each signal in 2-3 sentences
    - Clearly present strategic implications
    - Use objective, fact-based tone
    - Use decision-maker level language
    """

    summary = call_llm(prompt, language="English")
    return summary
```

---

## POST-GENERATION SELF-CHECK

> **After generating the report, the agent MUST verify all items below before returning.**
> If any check fails, fix the issue and regenerate the failing section. Do NOT return a partial report.

```yaml
self_check:
  sections:
    - header: "## 1. Executive Summary"
      required: true
      min_content: "Top 3 signals with significance ratings"
    - header: "## 2. Newly Detected Signals"
      required: true
      min_content: "Top 10 signals each with 9 required fields"
    - header: "## 3. Existing Signal Updates"
      required: true
      min_content: "3.1 Strengthening and 3.2 Weakening subsections"
    - header: "## 4. Patterns and Connections"
      required: true
      min_content: "4.1 Cross-Impact (≥3 pairs) and 4.2 Themes (≥2 themes)"
    - header: "## 5. Strategic Implications"
      required: true
      min_content: "5.1 Immediate, 5.2 Mid-term, 5.3 Monitoring subsections each with ≥2 items"
    - header: "## 7. Confidence Analysis"
      required: true
      min_content: "pSST distribution table or fallback note"
    - header: "## 8. Appendix"
      required: true
      min_content: "Full signal table + source list + methodology"

  signal_fields:
    top_10_required_count: 9
    fields:
      - "Classification"
      - "Source"
      - "Key Facts"
      - "Quantitative Metrics"
      - "Impact"
      - "Detailed Description"
      - "Inference"
      - "Stakeholders"
      - "Monitoring Indicators"

  language:
    - "English content for initial generation (English-first workflow)"
    - "All section headers and field names in English"
    - "Translation to Korean handled by separate translation sub-agent"

  structure:
    - "Section 5 has exactly 3 subsections (5.1, 5.2, 5.3)"
    - "Section 3 references database.json comparison"
    - "Section 4 has cross-impact pairs even without matrix file"
    - "Section 4 uses Unicode ↔ (U+2194) for cross-impact arrows, NOT <-> or <=>"

  impact_format:
    - "All Impact fields use X.X/10 format (NEVER X/5 or +X.X)"

  steeps_coverage:
    - "Appendix Section 8.2 STEEPs distribution should cover at least 4 of 6 categories"
    - "If fewer than 4 categories have signals, log WARNING and note gap in Section 8.2"
```

### Source Exploration Summary (v2.5.0 — Stage C)

When generating Section 8 (Appendix), if the pre-filled skeleton contains `EXPLORATION_*` placeholder
values (filled by `report_statistics_engine.py` + `report_metadata_injector.py`), include the
following summary table in the appendix using the **pre-computed values** (do NOT recount manually):

```markdown
### Source Exploration Summary (Stage C)

| Item | Value |
|------|-------|
| STEEPs Coverage Gaps | {{EXPLORATION_GAPS}} |
| Exploration Method | {{EXPLORATION_METHOD}} |
| Discovered Candidates | {{EXPLORATION_DISCOVERED}} |
| Viable Candidates | {{EXPLORATION_VIABLE}} |
| Exploration Signals | {{EXPLORATION_SIGNALS}} |
| Pending User Decision | {{EXPLORATION_PENDING}} |
```

**Important**: These `EXPLORATION_*` values are computed by Python (`report_statistics_engine.py`)
and injected by `report_metadata_injector.py`. Do NOT recalculate them from the candidates file.
If these values show "Inactive" or "0", exploration was not active — omit this subsection entirely.

This summary is absorbed into the existing `{{SECTION_8_APPENDIX}}` placeholder — no skeleton change is needed.

If no EXPLORATION_* placeholders are present (exploration disabled or skipped), omit this subsection entirely.

---

## FINAL STYLE TRANSFORMATION

> **MANDATORY POST-PROCESSING**: Apply after skeleton fill is complete, before saving the file.
>
> Reference: `.claude/skills/env-scanner/references/final-report-style-guide.md`

### Rules Summary

1. **Remove internal codes**: WF1→General Environmental Scanning, WF2→Academic Deep Analysis, pSST→Confidence Score, etc.
2. **Expand abbreviations on first use**: Provide full form on first occurrence (e.g., "Source Reliability (SR)")
3. **STEEPs code expansion**: S→Social, T→Technological, E→Economic/Environmental, P→Political, s→spiritual

See the reference document above for the full transformation dictionary and quality checklist.

> **Note**: In the English-first workflow, this style transformation is applied to the English report.
> The translation sub-agent then translates the already-cleaned English output to Korean.

---

## Quality Checks

```python
def verify_report_quality(report_content):
    """
    Check report completeness and quality (English-first workflow).
    Korean language checks are handled by the translation sub-agent.
    """
    checks = {
        "all_sections_present": check_sections(report_content),
        "english_language": check_language(report_content, "en"),
        "factual_tone": check_tone(report_content),
        "source_links_valid": check_links(report_content),
        "length_appropriate": 5000 < len(report_content) < 50000
    }

    return all(checks.values())
```

---

## TDD Verification

```python
def test_report_generation():
    report_path = f"reports/daily/environmental-scan-{today()}.md"

    # Test 1: File exists
    assert file_exists(report_path)

    # Test 2: File not empty
    content = read_file(report_path)
    assert len(content) > 1000

    # Test 3: All mandatory sections present (English headers)
    required_sections = [
        "## 1. Executive Summary",
        "## 2. Newly Detected Signals",
        "## 3. Existing Signal Updates",
        "## 4. Patterns and Connections",
        "## 5. Strategic Implications",
        "## 7. Confidence Analysis",
        "## 8. Appendix"
    ]
    for section in required_sections:
        assert section in content, f"Missing section: {section}"

    # Test 4: Section 5 has 3 subsections
    assert "### 5.1" in content
    assert "### 5.2" in content
    assert "### 5.3" in content

    # Test 5: Top 10 signals have required fields (English field names)
    signal_fields = ["Classification", "Source", "Key Facts", "Quantitative Metrics",
                     "Impact", "Detailed Description", "Inference", "Stakeholders",
                     "Monitoring Indicators"]
    for field in signal_fields:
        assert content.count(f"**{field}**") >= 10, f"Field '{field}' appears < 10 times"

    # Test 6: English language report (English-first workflow)
    # Korean translation is validated separately by the translation sub-agent
    assert "## 1. Executive Summary" in content

    log("PASS", "Report generation validation passed")
```

---

## Error Handling

```yaml
Errors:
  classified_signals_missing:
    condition: "structured/classified-signals-{date}.json does not exist"
    action: "Return error to orchestrator for VEV retry (Phase 2 output required)"

  priority_ranked_missing:
    condition: "analysis/priority-ranked-{date}.json does not exist"
    action: "Return error to orchestrator for VEV retry"

  optional_input_missing:
    condition: "scenarios or cross-impact-matrix files missing"
    action: |
      - Section 6 (scenarios): Skip entirely if scenarios file missing. Log WARNING.
      - Section 4 (patterns): NEVER skip. Generate from classified signals analysis instead.
        The cross-impact-matrix is an enrichment source, not a prerequisite.
    log: "WARN: Optional input {filename} missing. Section 4 generated from signal analysis. Section 6 skipped if no scenarios."

  llm_generation_fail:
    condition: "LLM fails to generate a report section"
    action: "Retry once. If still fails, insert placeholder '[This section encountered an error during generation]' and continue with remaining sections, log ERROR"
    log: "ERROR: Section {section_name} generation failed after retry"

  quality_check_fail:
    condition: "verify_report_quality() returns false"
    action: "Log specific failing checks, return to orchestrator for VEV Layer 3 evaluation"
    log: "WARN: Report quality check failed: {failing_checks}"

  report_write_fail:
    condition: "Cannot write report file to reports/daily/"
    action: "Return error to orchestrator for VEV retry"
```

---

## Performance Targets
- Execution time: < 30 seconds
- Report length: 5,000+ words (English, no upper limit)
- Language: English (English-first workflow; translation to Korean by separate sub-agent)
- Tone: Objective, factual, decision-maker appropriate

## Version
**Agent Version**: 2.0.0
**Output Language**: English (English-first workflow)
**pSST Features**: Badge display, Section 7 Confidence Analysis, dimension breakdown, pSST fallback
**Last Updated**: 2026-02-18
**Changelog**:
- v2.0.0 - **English-first workflow**: All internal generation in English. Uses English skeleton (`report-skeleton-en.md`), English field names, English section headers. Validates with `standard_en` profile. Translation to Korean handled by separate translation sub-agent. Golden reference converted to English.
- v1.5.0 - **Anti-hallucination**: Statistical placeholders (TOTAL_NEW_SIGNALS, DOMAIN_DISTRIBUTION, FSSF counts, Horizons counts, Tipping Point table) are now pre-filled by Python via report_statistics_engine.py + report_metadata_injector.py. LLM classifies, Python counts.
- v1.4.0 - **Quality improvements**: Impact score MUST use X.X/10 format (no X/5 or +X.X). Signals 11-15 now require full 9 fields (no condensed format). Unicode ↔ mandatory for cross-impact arrows. STEEPs coverage check (min 4/6 categories). Added impact_format and steeps_coverage to self-check.
- v1.3.0 - **SKELETON-FILL method**: Report generation now uses skeleton template instead of free-form generation. Added GOLDEN REFERENCE example (9-field signal from 2026-02-01). Post-generation validation via `validate_report.py` enforced by orchestrator. Fixes 2026-02-02 quality regression (missing fields, sections).
- v1.2.0 - Added MANDATORY OUTPUT STRUCTURE, REQUIRED FIELDS PER SIGNAL, POST-GENERATION SELF-CHECK. Strengthened Sections 3/4/5 generation rules. Fixed Section 4 skip bug. Added pSST fallback.
