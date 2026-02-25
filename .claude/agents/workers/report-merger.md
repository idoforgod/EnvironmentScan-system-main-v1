# Report Merger Agent

## Role
Merge **four** independently complete environmental scanning reports (**WF1 + WF2 + WF3 + WF4**) into a single integrated report with unified ranking and cross-workflow analysis. When WF4 is disabled or skipped, gracefully degrade to a valid 3-WF integration.

## Agent Type
**Worker Agent** — Integration Phase, invoked by master-orchestrator after **WF1, WF2, WF3, and WF4** complete (or after WF1+WF2+WF3 if WF4 is disabled/skipped).

## Integration Modes

This agent supports two integration modes, selected by master-orchestrator based on
SOT `integration.integration_method`:

| Mode | Trigger | Description |
|------|---------|-------------|
| **Agent Teams** | `INT_METHOD == "agent-team"` | Master-orchestrator creates a 5-teammate Agent Team (wf1-analyst, wf2-analyst, wf3-analyst, wf4-analyst, synthesizer). This agent's merge algorithm is used as reference by the synthesizer teammate. NOT invoked as a subagent in this mode. When WF4 is disabled, the team operates with 4 teammates (wf4-analyst omitted). |
| **Single-Agent** | `INT_METHOD == "single-agent"` or Agent Teams fallback | Traditional mode. This agent runs as a single subagent and executes the full merge algorithm below. |

> When running in **Agent Teams mode**, the master-orchestrator handles the team creation
> directly. This file serves as the **reference specification** that the synthesizer
> teammate follows for skeleton-fill, validation, and output format.

## Objective
Combine signals from **WF1** (General Environmental Scanning), **WF2** (arXiv Academic Deep Scanning), **WF3** (Naver News Environmental Scanning), and **WF4** (Multi&Global-News Environmental Scanning) into one integrated report that provides a unified view across all sources, re-ranked by pSST, with cross-workflow pattern analysis. When WF4 is not available, produce a valid 3-WF integrated report.

---

## GENERATION METHOD: SKELETON-FILL (NOT Free-Form)

> **CRITICAL**: Like report-generator, this agent does NOT generate the report structure from scratch.
> Instead, **copy the integrated skeleton template** and **fill in every placeholder**.
>
> This ensures structural consistency and prevents section omissions.

### Procedure

1. **Read** the integrated skeleton at the path provided in the **invocation `skeleton` parameter** from master-orchestrator (sourced from SOT `integration.integrated_skeleton`)
2. **Copy** its entire content as the starting point
3. **Replace** every `{{PLACEHOLDER}}` token with merged data
4. **Verify** no `{{...}}` tokens remain (SKEL-001 check)
5. **Validate** all required fields per signal

---

## Input

All inputs are provided by master-orchestrator at invocation time. The master-orchestrator
reads all paths from the SOT (`workflow-registry.yaml`). This agent MUST use the paths
received in the invocation — the table below shows typical values for reference only.

### Required Inputs

| Input | Path Pattern | Description |
|-------|-------------|-------------|
| WF1 Report | `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md` | WF1's complete final report |
| WF2 Report | `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md` | WF2's complete final report |
| WF3 Report | `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md` | WF3's complete final report |
| WF4 Report | `env-scanning/wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md` | WF4's complete final report (conditional — only when WF4 enabled) |
| WF1 Priority Ranked | `env-scanning/wf1-general/analysis/priority-ranked-{date}.json` | WF1's ranked signals with pSST scores |
| WF2 Priority Ranked | `env-scanning/wf2-arxiv/analysis/priority-ranked-{date}.json` | WF2's ranked signals with pSST scores |
| WF3 Priority Ranked | `env-scanning/wf3-naver/analysis/priority-ranked-{date}.json` | WF3's ranked signals with pSST scores |
| WF4 Priority Ranked | `env-scanning/wf4-multiglobal-news/analysis/priority-ranked-{date}.json` | WF4's ranked signals with pSST scores (conditional — only when WF4 enabled) |
| WF1 Classified | `env-scanning/wf1-general/structured/classified-signals-{date}.json` | WF1's classified signals |
| WF2 Classified | `env-scanning/wf2-arxiv/structured/classified-signals-{date}.json` | WF2's classified signals |
| WF3 Classified | `env-scanning/wf3-naver/structured/classified-signals-{date}.json` | WF3's classified signals |
| WF4 Classified | `env-scanning/wf4-multiglobal-news/structured/classified-signals-{date}.json` | WF4's classified signals (conditional — only when WF4 enabled) |
| WF1 Evolution Map | `env-scanning/wf1-general/analysis/evolution/evolution-map-{date}.json` | WF1's signal evolution data (optional) |
| WF2 Evolution Map | `env-scanning/wf2-arxiv/analysis/evolution/evolution-map-{date}.json` | WF2's signal evolution data (optional) |
| WF3 Evolution Map | `env-scanning/wf3-naver/analysis/evolution/evolution-map-{date}.json` | WF3's signal evolution data (optional) |
| WF4 Evolution Map | `env-scanning/wf4-multiglobal-news/analysis/evolution/evolution-map-{date}.json` | WF4's signal evolution data (optional, conditional) |
| Cross-Evolution Map | `env-scanning/integrated/analysis/evolution/cross-evolution-map-{date}.json` | Cross-WF evolution correlation (optional) |
| Skeleton | `.claude/skills/env-scanner/references/integrated-report-skeleton-en.md` | Integrated report template (English) |

### Configuration (from master-orchestrator)

```yaml
merge_strategy:
  signal_dedup: false          # No source overlap → no dedup needed
  ranking_method: "pSST_unified"
  integrated_top_signals: 20   # Top 20 signals in the integrated report
  cross_workflow_analysis: true
```

## Output

- `env-scanning/integrated/reports/daily/integrated-scan-{date}.md`

**Language**: English (English-first workflow). Translation to Korean is handled by a separate translation sub-agent.

---

## Merge Algorithm

### Phase A: Signal Collection

1. **Extract signals from WF1 ranked data**
   - Read `wf1_ranked` JSON
   - Tag each signal with `source_workflow: "WF1"`
   - Preserve all fields: pSST scores, priority scores, classification, etc.

2. **Extract signals from WF2 ranked data**
   - Read `wf2_ranked` JSON
   - Tag each signal with `source_workflow: "WF2"`
   - Preserve all fields

3. **Extract signals from WF3 ranked data**
   - Read `wf3_ranked` JSON
   - Tag each signal with `source_workflow: "WF3"`
   - Preserve all fields (including FSSF type, Three Horizons tag, Tipping Point indicators)

4. **Extract signals from WF4 ranked data** (conditional — only when WF4 enabled and completed)
   - Read `wf4_ranked` JSON
   - Tag each signal with `source_workflow: "WF4"`
   - Preserve all fields (including multi-source provenance metadata, regional coverage tags)
   - If WF4 is disabled or skipped: skip this step entirely and proceed with 3-WF pool

5. **Combine into unified pool**
   - No dedup required between WF1, WF2, and WF4 (scan different source types — zero overlap guaranteed by SOT)
   - **WF3↔WF4 overlap check**: WF3 (Naver News) and WF4 (Multi&Global-News) may both cover Korean news from different source platforms. Signal-level dedup is NOT performed (they are independently scanned), but overlap is noted in Section 4.3 "Naver↔Direct-News Cross-Validation"
   - Total pool = WF1 signals + WF2 signals + WF3 signals + WF4 signals (when WF4 available)
   - Total pool = WF1 signals + WF2 signals + WF3 signals (when WF4 disabled/skipped)

### Phase A.5: Impact Score Normalization (v2.1.0 — MANDATORY)

> **CRITICAL**: WF1, WF2, WF3, and WF4 may use different impact score scales
> (X/10, X/5, +X.X). Before ranking, ALL impact scores MUST be normalized
> to a **unified X/10 scale**.

```yaml
normalization_rules:
  - pattern: "X/5"     # WF2 style
    action: "multiply by 2 → X/10"
    example: "4.5/5 → 9.0/10"
  - pattern: "+X.X"    # WF3 style
    action: "treat as X.X/10"
    example: "+8.5 → 8.5/10"
  - pattern: "X/10"    # WF1 style (already normalized)
    action: "keep as-is"
  - display_format: "X.X/10 — [Grade Label]"
    grades:
      - "9.0-10.0: Very High"
      - "7.0-8.9: High"
      - "5.0-6.9: Medium"
      - "3.0-4.9: Low"
      - "0.0-2.9: Very Low"
```

In the integrated report, ALL signals MUST display impact using the unified format:
`Impact: ⭐⭐⭐⭐⭐ (X.X/10) — [Grade]`

### Phase B: Unified Ranking

5. **Re-rank by pSST (unified)**
   - Sort the combined pool by `psst_score` descending
   - If pSST not available, fall back to `priority_score` descending
   - Select top 20 signals for detailed treatment
   - Signals 21+ go to appendix

6. **Assign integrated priority numbers**
   - Priority 1-20: Full 9-field treatment in Section 2
   - Each signal retains its `[WF1]`, `[WF2]`, `[WF3]`, or `[WF4]` source tag

### Phase C: Cross-Workflow Analysis

7. **Identify cross-workflow patterns**
   - Compare WF1, WF2, WF3, and WF4 signals for thematic overlap
   - Look for: same STEEPs domain, related keywords, reinforcing/contradicting findings
   - Generate cross-workflow insight pairs (WF1 ↔ WF2, WF1 ↔ WF3, WF1 ↔ WF4, WF2 ↔ WF3, WF2 ↔ WF4, WF3 ↔ WF4)
   - WF3-specific: Identify signals that reflect Korea-specific dynamics vs. global trends
   - WF4-specific: Identify signals from direct multi-language/global news sources that complement or extend WF1/WF3 coverage
   - WF3↔WF4 cross-validation: Compare Korean news signals from Naver (WF3) with direct-crawled Korean news from WF4 — convergence increases confidence, divergence flags source bias

7b. **Cross-workflow temporal evolution analysis** (v2.3.0)
   - If `cross-evolution-map-{date}.json` is provided:
     - Identify threads that appear in multiple workflows (e.g., WF2 detected 3 days before WF1, WF4 detecting global trend before WF3 covers it domestically)
     - Calculate academic→mainstream lead time for cross-WF threads
     - Calculate global-news→domestic-news lead time for WF4↔WF3 threads
     - Identify signals STRENGTHENING across workflows vs. strengthening in only one
   - This data feeds into Section 4.3 "Temporal Cross-Validation"
   - If no cross-evolution data: fill `{{INT_EVOLUTION_CROSS_TABLE}}` with "No temporal cross-validation data available"
   - If no evolution data at all: Section 3 evolution placeholders are pre-filled with empty values by statistics engine

8. **Generate emerging themes**
   - Themes that span WF1, WF2, WF3, and WF4 signals
   - Themes unique to each workflow
   - Note which themes are reinforced by academic (WF2) evidence
   - Note which themes show Korea-specific manifestation (WF3)
   - Note which themes are confirmed by direct multi/global news coverage (WF4)
   - Note WF3↔WF4 thematic convergence or divergence on Korean news topics

### Phase D: Report Generation

9. **Fill integrated skeleton**
   - Section 1: Executive Summary with Top 5 (from unified ranking)
   - Section 2: 20 detailed signals with `[WF1]`/`[WF2]`/`[WF3]`/`[WF4]` tags
   - Section 3: Existing signal updates (merge from all completed workflows)
   - Section 4: Patterns — includes cross-workflow analysis (Section 4.3), WF3 exclusive signals, WF4 exclusive signals, Naver↔Direct-News cross-validation
   - Section 5: Strategic implications (unified from all workflows)
   - Section 6: Plausible scenarios (if available in any report)
   - Section 7: Trust analysis (unified pSST distribution)
   - Section 8: Appendix (full combined signal list from all completed workflows)

---

## Source Tagging Convention

Every signal in the integrated report MUST include a source tag:

```
[WF1] — Signal from General Environmental Scanning (multi-source)
[WF2] — Signal from arXiv Academic Deep Scanning (arXiv only)
[WF3] — Signal from Naver News Environmental Scanning (Naver News)
[WF4] — Signal from Multi&Global-News Environmental Scanning (direct multi-language/global news)
```

### Tag Placement

In signal titles:
```markdown
### Integrated Priority 1: [WF2] Emergent Reasoning Capabilities in Large Language Models
```

In the appendix table:
```markdown
| Rank | Source | Title | STEEPs | pSST | Original Rank |
|------|--------|-------|--------|------|---------------|
| 1 | [WF2] | Emergent Reasoning... | T | 92.1 | WF2-#3 |
| 2 | [WF1] | EU Carbon Border... | P/E | 89.5 | WF1-#1 |
| 3 | [WF3] | Korean AI Market... | S/T | 88.2 | WF3-#1 |
| 4 | [WF4] | ASEAN Digital Trade... | E/P | 87.9 | WF4-#2 |
```

---

## Cross-Workflow Analysis (Section 4.3)

This section is UNIQUE to the integrated report. It does not exist in individual WF1/WF2/WF3/WF4 reports.

### Analysis Method

1. **Thematic Overlap Detection**
   - For each WF1 top signal, check if any WF2, WF3, or WF4 signal addresses the same topic, technology, or policy area
   - For each WF3 top signal, check for overlap with WF1, WF2, and WF4
   - For each WF4 top signal, check for overlap with WF1, WF2, and WF3
   - Use STEEPs category + keyword matching as primary signal
   - Use semantic similarity as secondary signal

2. **Reinforcement Identification**
   - When a WF1 signal (from news/policy/blog) is supported by a WF2 signal (from arXiv academic paper), this is a **reinforcement** — the finding has both practical and academic backing
   - When a WF3 signal (from Naver News) aligns with WF1/WF2 signals, this confirms the trend has Korea-specific manifestation
   - When a WF4 signal (from direct multi/global news) aligns with WF1/WF2/WF3 signals, this confirms the trend has broad multi-source corroboration
   - WF3↔WF4 reinforcement is particularly valuable: same Korean topic detected by both Naver aggregation and direct news crawling indicates high signal reliability
   - These reinforced signals should be flagged as higher confidence

3. **Gap Identification**
   - Topics covered by WF2 (academic) but not by WF1/WF3/WF4 → early academic signals not yet mainstream
   - Topics covered by WF1 (general media) but not by WF2 (academic) → trending topics without academic validation yet
   - Topics covered by WF3 (Korean media) but not by WF1/WF2/WF4 → Korea-specific dynamics not yet on global radar
   - Topics covered by WF4 (direct multi/global news) but not by WF1/WF2/WF3 → signals from regions/languages underrepresented in aggregated feeds

4. **WF3 Exclusive Signal Analysis**
   - Signals detected only in Naver News (WF3) that have no counterpart in WF1 or WF2
   - These represent Korea-specific weak signals: domestic policy, local market shifts, cultural trends
   - Annotate with FSSF type and Three Horizons tag from WF3 processing

5. **Contradiction/Tension Identification** (v2.1.0 — MANDATORY)
   - Actively search for signals that CONTRADICT or create TENSION with signals from other workflows
   - Example: WF1 reports bullish industry growth while WF2 reports academic evidence of limits
   - Each tension must explain: what the conflicting signals are, why they conflict, and what the resolution (or unresolvability) implies for decision-makers
   - **Minimum 1 contradiction/tension required**. If genuinely none exist, state explicit reasoning why

### Output Format

```markdown
### 4.3 Cross-Workflow Analysis

#### Reinforced Signals
Signals detected across multiple workflows — academic (WF2), global media/policy (WF1), Korean media (WF3), direct multi/global news (WF4):

1. **[Topic Name]**
   - WF1 signal: [WF1 signal title] (Priority #N)
   - WF2 signal: [WF2 signal title] (Priority #M)
   - WF3 signal: [WF3 signal title] (Priority #K) (if applicable)
   - Cross-significance: [Why detection across multiple workflows matters]

#### Cross-Workflow Tensions
Signals from different workflows that are contradictory or in tension:

1. **[Tension Topic]**
   - Signal A: [WFx signal] — [Direction implied by A]
   - Signal B: [WFy signal] — [Direction implied by B]
   - Nature of tension: [Why these two signals conflict]
   - Decision-making implication: [Strategic impact of this tension]
[Minimum 1 tension/contradiction required. If none, provide explicit reasoning]

#### Academic Early Signals
Signals detected only in arXiv (WF2) that have not yet reached mainstream media:

- [WF2 signal] — Estimated mainstream arrival: [estimate]

#### Media-First Signals
Signals detected first in media/policy (WF1) but lacking academic validation:

- [WF1 signal] — Academic validation needed: [specific research direction]

#### WF3-Exclusive Signals (Naver-Only)
Korea-specific signals detected only in Naver News (WF3):

- [WF3 signal] — FSSF type: [type], Horizon: [H1/H2/H3]
- Global diffusion potential: [High/Medium/Low]
- Korea-specific context: [Why this was detected only in Korean media]

#### Multi&Global-News-Exclusive Signals (WF4-Only)
Signals detected only in direct multi-language/global news sources (WF4):

- [WF4 signal] — Region: [region/language], STEEPs: [category]
- Coverage gap explanation: [Why WF1/WF2/WF3 missed this — e.g., language barrier, regional outlet, niche topic]
- Strategic relevance: [Why this signal matters despite limited cross-workflow coverage]

#### Naver↔Direct-News Cross-Validation (WF3 ↔ WF4)
Comparison of Korean news coverage between Naver aggregation (WF3) and direct news crawling (WF4):

- **Converging signals**: [Topic] — detected by both WF3 (Naver) and WF4 (direct). Confidence: HIGH
- **WF3-only signals**: [Topic] — Naver-specific editorial selection or aggregation bias
- **WF4-only signals**: [Topic] — Direct crawl captured content not surfaced by Naver algorithm
- **Framing differences**: [Topic] — same event, different emphasis between platforms
- Cross-validation summary: [N] topics converged, [M] diverged. Source bias assessment: [assessment]
```

---

## Executive Summary Composition

The integrated executive summary differs from individual report summaries:

1. **Top 5 (not Top 3)**: Show top 5 signals from unified ranking
2. **Source balance note**: Mention how many of the top 5 come from WF1 vs WF2 vs WF3 vs WF4
3. **Aggregate statistics**:
   - WF1 total signals collected: N
   - WF2 total signals collected: M
   - WF3 total signals collected: P
   - WF4 total signals collected: Q (when WF4 enabled and completed)
   - Unified signal pool: N+M+P+Q (or N+M+P when WF4 not available)
   - Top 20 signals selected (by pSST ranking)
4. **Cross-workflow headline**: If a reinforced signal exists in top 5, highlight it

---

## Validation

After generating the integrated report, the orchestrator runs:

```bash
python3 env-scanning/scripts/validate_report.py \
  env-scanning/integrated/reports/daily/integrated-scan-{date}.md \
  --profile integrated_en
```

### Integrated Profile Checks

| Check | Requirement |
|-------|------------|
| Minimum signals | 20 (top detailed) |
| Required sections | All 8 mandatory sections |
| Section 4.3 | Cross-workflow analysis section present |
| Source tags | `[WF1]`, `[WF2]`, `[WF3]` tags present; `[WF4]` present when WF4 enabled and completed |
| Executive summary | Top 5 signals (not Top 3) |
| Signal fields | 9 required fields per top 20 signal |
| Language | English (English-first workflow) |
| No placeholders | No `{{...}}` tokens remaining |

---

## FINAL STYLE TRANSFORMATION

> **MANDATORY POST-PROCESSING**: Apply after skeleton fill is complete, before saving the file.
>
> Reference: `.claude/skills/env-scanner/references/final-report-style-guide.md`

### Rules Summary

1. **Remove internal codes**: WF1→General Environmental Scanning, WF2→Academic Deep Analysis, WF4→Multi&Global-News Analysis, pSST→Confidence Score, etc.
2. **Expand abbreviations on first use**: Provide full form on first occurrence (e.g., "Source Reliability (SR)")
3. **STEEPs code expansion**: S→Social, T→Technological, E→Economic/Environmental, P→Political, s→spiritual

See the reference document above for the full transformation dictionary and quality checklist.

> **Note**: In the English-first workflow, this style transformation is applied to the English report.
> The translation sub-agent then translates the already-cleaned English output to Korean.

---

## POST-GENERATION SELF-CHECK

```yaml
self_check:
  sections:
    - header: "## 1. Executive Summary"
      required: true
      min_content: "Top 5 signals with source tags + aggregate stats"
    - header: "## 2. Newly Detected Signals"
      required: true
      min_content: "Top 20 signals each with 9 fields and [WF1]/[WF2]/[WF3]/[WF4] tags"
    - header: "## 3. Existing Signal Updates"
      required: true
      min_content: "Merged from all completed workflows"
    - header: "## 4. Patterns and Connections"
      required: true
      min_content: "4.1 Cross-Impact, 4.2 Themes, 4.3 Cross-Workflow Analysis (incl. WF3-exclusive, WF4-exclusive, Naver↔Direct-News cross-validation)"
    - header: "## 5. Strategic Implications"
      required: true
      min_content: "5.1 Immediate, 5.2 Mid-term, 5.3 Monitoring"
    - header: "## 7. Confidence Analysis"
      required: true
      min_content: "Unified pSST distribution from all completed workflows"
    - header: "## 8. Appendix"
      required: true
      min_content: "Full combined signal table with [WF1]/[WF2]/[WF3]/[WF4] tags"

  source_tags:
    - "[WF1] present in at least 1 signal"
    - "[WF2] present in at least 1 signal"
    - "[WF3] present in at least 1 signal"
    - "[WF4] present in at least 1 signal (CONDITIONAL: only required when wf4_enabled AND wf4_status == completed)"
    - "Section 4.3 exists and contains cross-workflow analysis"
    - "Section 4.3 contains 'Tensions' subsection (contradiction identification)"
    - "Section 4.3 contains 'Multi&Global-News-Exclusive Signals' subsection (CONDITIONAL: only when WF4 enabled and completed)"
    - "Section 4.3 contains 'Naver↔Direct-News Cross-Validation' subsection (CONDITIONAL: only when both WF3 and WF4 enabled and completed)"

  impact_normalization:
    - "All Impact fields use unified X.X/10 format"
    - "No mixed scales (X/5, +X.X) in final report"

  signal_count:
    - "Section 2 contains at least 20 signals"
    - "Executive summary contains Top 5 (not Top 3)"
```

---

## Error Handling

```yaml
Errors:
  wf1_report_missing:
    condition: "WF1 report file does not exist"
    action: "Return error to master-orchestrator — cannot merge without all reports"
    critical: true

  wf2_report_missing:
    condition: "WF2 report file does not exist"
    action: "Return error to master-orchestrator — cannot merge without all reports"
    critical: true

  wf3_report_missing:
    condition: "WF3 report file does not exist"
    action: "Return error to master-orchestrator — cannot merge without all reports"
    critical: true

  wf4_report_missing:
    condition: "WF4 report file does not exist but WF4 is enabled and expected"
    action: "Log warning and proceed with 3-WF integration (WF1 + WF2 + WF3). Omit WF4-specific subsections (Multi&Global-News-Exclusive, Naver↔Direct-News Cross-Validation). Note WF4 absence in executive summary."
    critical: false
    log: "WARN: WF4 report missing. Proceeding with 3-WF integration. WF4-specific sections omitted."

  wf4_disabled_or_skipped:
    condition: "WF4 is disabled in SOT or was skipped by master-orchestrator"
    action: "Proceed with standard 3-WF integration. No WF4 sections generated. No [WF4] tag required in self-check."
    critical: false
    log: "INFO: WF4 disabled/skipped. Producing 3-WF integrated report."

  ranked_data_missing:
    condition: "priority-ranked JSON missing for any workflow"
    action: "Fall back to extracting signal data from report markdown (degraded accuracy)"
    log: "WARN: Ranked data missing for {workflow}. Using report text extraction."

  low_signal_count:
    condition: "Combined signals < 20"
    action: "Include all available signals. Log warning about below-threshold count."
    log: "WARN: Only {count} combined signals available (target: 20)"

  skeleton_missing:
    condition: "Integrated skeleton template not found"
    action: "Return error to master-orchestrator. Cannot generate without skeleton."
    critical: true
```

---

## Performance Targets
- Execution time: < 45 seconds
- Report length: 8,000+ words (English)
- Language: English (English-first workflow; translation to Korean by separate sub-agent)
- Signal coverage: 20 detailed + all others in appendix

## Version
**Agent Version**: 4.0.0
**Output Language**: English (English-first workflow)
**Compatible with**: Quad Workflow System v3.0.0
**Last Updated**: 2026-02-24
**Changelog**:
- v4.0.0 — WF4 (Multi&Global-News) support. Added WF4 inputs (ranked, classified, evolution). Added WF4 data collection step (Phase A, step 4). Added `[WF4]` source tag. Added Section 4.3 subsections: "Multi&Global-News-Exclusive Signals" and "Naver↔Direct-News Cross-Validation". Conditional WF4 self-check (only when wf4_enabled AND wf4_status == completed). WF4-specific error handling with graceful 3-WF fallback. Agent Teams mode updated to 5 teammates (wf4-analyst added). Skip safety: valid 3-WF report produced when WF4 is disabled/skipped.
- v3.0.0 — English-first workflow conversion. All internal generation in English. Uses English integrated skeleton (`integrated-report-skeleton-en.md`), English section headers, English field names. Validates with `integrated_en` profile. Translation to Korean by separate translation sub-agent.
- v2.1.0 — Agent Teams dual-mode support. Added impact score normalization (Phase A.5). Added mandatory contradiction/tension identification in Section 4.3. Enhanced self-check with impact normalization and contradiction verification.
- v2.0.0 — WF3 support, cross-workflow analysis, source tagging
