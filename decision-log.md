# Decision Log

> Architectural decisions made during the evolution of the Quadruple Environmental Scanning System.
>
> System: Quadruple Environmental Scanning System v3.2.0
> Period: 2026-02-24 ~ 2026-03-09

---

## DEC-001: WF4 Naming Convention

**Date**: 2026-02-24
**Context**: WF4 needed a name that conveyed both its multi-source nature (43 news sites) and its global scope (11 languages). The name must work in both human-readable contexts and as a filesystem-safe identifier.

**Decision**: Display name is "Multi&Global-News". File system name is `multiglobal-news` (no ampersand, no uppercase).

**Rationale**: The ampersand in the display name emphasizes the dual nature (multi-source AND global reach). The filesystem name follows existing conventions (`wf3-naver` pattern) -- lowercase, hyphenated, no special characters. The data directory is `wf4-multiglobal-news/`.

**Alternatives Considered**:
- `wf4-global-news` -- Too generic, does not convey the multi-source aspect
- `wf4-world-news` -- Ambiguous, could imply a single "world news" source
- `wf4-multinews` -- Too abbreviated, unclear meaning

**Impact**: All file paths, signal IDs, agent names, and config keys use the `multiglobal-news` form. Display in reports and UI uses "Multi&Global-News".

---

## DEC-002: Skeleton Base -- WF3 FSSF Extended

**Date**: 2026-02-24
**Context**: WF4 reports need a skeleton template. The system has two skeleton families: the standard skeleton (WF1/WF2, 8 sections, STEEPs only) and the Naver skeleton (WF3, 8 sections + FSSF/3H/TP sections).

**Decision**: WF4 skeleton is based on the WF3 Naver FSSF skeleton, extended with WF4-specific sections (crawling stats, translation stats, defense log). It is NOT based on the standard WF1/WF2 skeleton.

**Rationale**: WF4 shares the FSSF 8-type classification, Three Horizons tagging, and Tipping Point detection with WF3. Starting from the WF3 skeleton and adding WF4 sections avoids duplicating FSSF/3H/TP template work. The standard skeleton lacks these sections entirely, so extending it would require more modifications.

**Alternatives Considered**:
- Standard skeleton + FSSF sections added manually -- More work, risk of inconsistency with WF3
- Completely new skeleton from scratch -- Unnecessary divergence, maintenance burden

**Impact**: WF4 skeleton file: `multiglobal-news-report-skeleton.md` (and EN variant). Shares FSSF/3H/TP sections with WF3 but adds: crawling statistics table, translation quality matrix, paywall defense log section.

---

## DEC-003: Paywall Strategy -- Total War

**Date**: 2026-02-24
**Context**: Several high-value news sources (NYT, FT, WSJ, Bloomberg) are behind paywalls. These are among the most authoritative sources for Economic and Political signals. Skipping them would create significant coverage gaps.

**Decision**: Implement a "Total War" paywall strategy for NYT, FT, WSJ, and Bloomberg. This means infinite retry with escalating bypass strategies until success or explicit strategy exhaustion.

**Rationale**: These four sources represent irreplaceable signal quality for financial markets, geopolitics, and technology policy. The cost of missing their signals (coverage gap in E and P categories) outweighs the cost of additional crawling time. The Total War strategy is bounded by strategy exhaustion (not by retry count), ensuring the system eventually moves on if all approaches fail.

**Alternatives Considered**:
- Standard retry (3 attempts) -- Insufficient for sophisticated paywalls
- Skip paywalled sites entirely -- Unacceptable coverage gap
- Manual subscription/API keys -- Not always available; system should be autonomous
- Selective Total War (only NYT) -- All four sources are equally critical

**Impact**: WF4 crawler includes a `PaywallBreacher` component. Defense logs are included in reports. Failed paywall breaches are logged but do not halt the workflow -- the site is skipped and the coverage gap is noted in the report.

---

## DEC-004: Sub-Agent vs Agent-Teams -- Quality-Based Selection

**Date**: 2026-02-24
**Context**: Each workflow step can be executed by a single sub-agent or by an Agent-Teams group (multiple agents collaborating). The choice affects output quality, execution time, and resource usage.

**Decision**: Use quality-based selection per phase:
- **Sub-agent** for Phase 1 (data collection) and Phase 2 (analysis per WF) -- deterministic, well-defined tasks
- **Agent-Teams (5 members)** for Integration -- complex judgment requiring diverse perspectives

**Rationale**: Data collection and per-workflow analysis are well-defined tasks where a single specialized agent produces optimal results. Integration requires synthesizing insights from 4 different workflows, comparing signals across domains, and making judgment calls about unified rankings. This benefits from the diversity of perspectives that Agent-Teams provides.

**Alternatives Considered**:
- Agent-Teams for everything -- Excessive overhead for simple tasks, slower execution
- Sub-agent for everything -- Insufficient quality for integration step
- Agent-Teams for Phase 2 only -- Phase 2 analysis is still per-WF and well-defined

**Impact**: Integration Agent-Teams has 5 members: report-merger (coordinator), wf1-analyst, wf2-analyst, wf3-analyst, wf4-analyst. Each analyst is an expert in their workflow's domain and contributes to the unified ranking discussion.

---

## DEC-005: English-First Processing

**Date**: 2026-02-24
**Context**: WF4 collects news in 11 languages. Analysis must produce consistent, comparable results across all sources. The final output must be in Korean.

**Decision**: All internal processing is conducted in English. Source articles in non-English languages are translated to English immediately upon collection. Analysis, classification, impact assessment, and ranking all operate on English text. The final report is translated from English to Korean as the last step.

**Rationale**: English-first ensures consistent LLM performance across all signals regardless of source language. STEEPs classification, FSSF typing, and pSST scoring are all calibrated for English text. Translating to a single working language eliminates the need for 11 separate classification models or prompts. This aligns with the system-wide bilingual protocol (Internal=EN, External=KO).

**Alternatives Considered**:
- Process each language natively, translate at report time -- Inconsistent classification quality across languages
- Korean-first (translate everything to Korean) -- LLM classification less accurate in Korean for global topics
- Mixed-language processing -- Impossible to maintain consistent scoring

**Impact**: WF4 Phase 1 includes a `multiglobal-translator` agent that translates all non-English content to English before classification. Translation quality scores are tracked per language pair and reported in the translation statistics section.

---

## DEC-006: Content Field Schema -- Standard `abstract` Preserved

**Date**: 2026-02-24
**Context**: The standard signal format uses `content.abstract` for the signal summary. WF4 collects articles in foreign languages and translates them. The question is how to store both the original and translated text.

**Decision**: Preserve the standard `content.abstract` field for the English-translated version. Add `content.original_abstract` for the original-language text. Add `content.source_language` to indicate the original language.

**Rationale**: All downstream processing (classification, impact analysis, deduplication) operates on `content.abstract`, which must be in English per the English-first protocol. Storing the original text in `original_abstract` preserves provenance and enables quality auditing. The standard field name ensures compatibility with all shared worker agents (signal-classifier, deduplication-filter, etc.) without modification.

**Alternatives Considered**:
- Replace `abstract` with translated text, discard original -- Loses provenance
- Rename `abstract` to `translated_abstract` -- Breaks compatibility with shared workers
- Use `abstract` for original, add `en_abstract` -- Breaks English-first assumption in shared workers

**Impact**: WF4 signal JSON schema adds two fields to `content`: `original_abstract` (string) and `source_language` (ISO 639-1 code). All shared workers continue to read `content.abstract` without modification.

---

## DEC-007: WF3/WF4 Content Overlap -- Not a Source Overlap Violation

**Date**: 2026-02-24
**Context**: WF3 (Naver News) covers Korean news. WF4 (Multi&Global-News) includes Korean news sites (Chosun Ilbo, JoongAng Ilbo, Hankyoreh). Some news stories may appear in both Naver aggregation and the direct Korean news sites. The system's immutable rule SOT-012 states: "No source overlap between workflows."

**Decision**: WF3/WF4 Korean news overlap is NOT a source overlap violation. The sources are different (Naver News aggregator vs. direct publisher sites). Content overlap between different sources is expected and is handled by integration-level cross-validation, not by source exclusivity rules.

**Rationale**: SOT-012 prohibits the same **source** from appearing in multiple workflows (e.g., arXiv cannot be in both WF1 and WF2). It does not prohibit different sources from covering the same **stories**. Naver News (an aggregator) and Chosun Ilbo (a direct publisher) are fundamentally different sources even if they sometimes carry the same content. The integration step explicitly performs cross-workflow analysis to identify and leverage such overlaps for cross-validation.

**Alternatives Considered**:
- Exclude Korean news sites from WF4 -- Reduces WF4's regional coverage, artificial limitation
- Exclude Naver from WF3 when WF4 is enabled -- Breaks WF3 independence
- Add deduplication between WF3 and WF4 -- Violates workflow independence principle

**Impact**: Integration cross-workflow analysis explicitly looks for WF3/WF4 overlap as a cross-validation signal. When the same story appears in both, it increases confidence (pSST boost). This is documented as "Regional Cross-Validation" in the integrated report.

---

## DEC-008: Integration Method -- Agent-Teams 5 Members

**Date**: 2026-02-24
**Context**: With 4 workflows (up from 3), the integration step is more complex. The previous system used a single `report-merger` agent. The question is whether this is sufficient for 4-workflow integration.

**Decision**: Replace single-agent integration with Agent-Teams of 5 members. Each workflow gets a dedicated analyst agent, plus the report-merger as coordinator.

**Rationale**: With 4 workflows producing diverse signal types (academic, general media, Korean news, global multilingual news), a single merger agent cannot adequately represent all perspectives in the unified ranking. The Agent-Teams approach allows each workflow's analyst to advocate for their signals' importance, creating a more balanced integration. The 5th member (wf4-analyst) was added specifically for the WF4 addition.

**Alternatives Considered**:
- Single report-merger (status quo) -- Insufficient for 4-WF complexity
- Agent-Teams of 3 (merger + 2 analysts) -- Under-represents WF3 and WF4
- Agent-Teams of 4 (one per WF) -- No neutral coordinator
- Agent-Teams of 7+ -- Excessive, diminishing returns

**Impact**: Integration section of SOT (`integration.agent_teams: 5`) defines the team composition. The report-merger coordinates discussion and produces the final unified ranking. Each analyst provides domain expertise for their workflow's signals.

---

## DEC-009: Signal ID Format -- `news-{YYYYMMDD}-{site_short}-{NNN}`

**Date**: 2026-02-24
**Context**: Each workflow has a defined signal ID format. WF4 needs its own format that is unique, sortable, and informative.

**Decision**: WF4 signal IDs follow the format `news-{YYYYMMDD}-{site_short}-{NNN}`.

Examples:
- `news-20260224-nyt-001` (New York Times)
- `news-20260224-ft-003` (Financial Times)
- `news-20260224-spiegel-002` (Der Spiegel)
- `news-20260224-scmp-001` (South China Morning Post)

**Rationale**: The `news-` prefix distinguishes WF4 signals from WF1 (`{source}-`), WF2 (`{source}-`), WF3 (`naver-`), and exploration (`explore-`). The site short code enables quick identification of the signal's origin. The date and sequence number follow the established pattern for sortability and uniqueness.

**Alternatives Considered**:
- `wf4-{YYYYMMDD}-{NNN}` -- Does not indicate source site
- `global-{YYYYMMDD}-{site}-{NNN}` -- `global` prefix too long
- `mg-{YYYYMMDD}-{site}-{NNN}` -- `mg` abbreviation unclear

**Impact**: Site short codes are defined in `sources-multiglobal-news.yaml`. Each site has a unique 2-7 character short code. Signal ID uniqueness is enforced by the database-updater agent per the database atomicity invariant.

---

## DEC-010: 44 Sites (Plan Said 43) -- Accepted

**Date**: 2026-02-24
**Context**: The implementation plan specified 43 direct news sites. During the enumeration of sources across 11 languages, the actual count came to 44 (one additional site was included in the Asia region).

**Decision**: Accept 44 sites. The plan's "43" was an approximation. The additional site provides value without any architectural impact.

**Rationale**: The difference between 43 and 44 sites has zero architectural impact. The system handles N sites generically -- adding or removing one site requires only a config change, not a code change. The additional site fills a coverage gap in the Southeast Asian region. Forcing removal of a valuable site to match an arbitrary number would reduce signal quality.

**Alternatives Considered**:
- Remove one site to match 43 -- Artificial constraint, reduces coverage
- Update all documentation to say 44 -- Creates inconsistency with planning documents

**Impact**: The system documentation continues to reference "43 sites" as the nominal count (matching the original plan). The actual source config contains 44 entries. The validate_registry.py check verifies that WF4 has "at least 40" enabled sources, not an exact count. Future source additions/removals are governed by the MAJOR change process and require user approval.

---

## DEC-011: Python 원천봉쇄 for Step 2.3 (Priority Ranking)

**Date**: 2026-03-02
**Context**: The 2nd Critical Reflection identified ~50 deterministic placeholders being delegated to the LLM despite the established "계산은 Python이, 판단은 LLM이" principle. Priority ranking (Step 2.3) was the most critical: the LLM was generating priority scores using a formula (`impact×0.40 + prob×0.30 + urgency×0.20 + novelty×0.10`), but there was no guarantee it applied the formula correctly — it could hallucinate scores.

**Decision**: Move Step 2.3 entirely to `priority_score_calculator.py` (Python). The LLM's (@phase2-analyst) sole responsibility is to provide the correct input fields; Python applies the formula deterministically.

**Rationale**: Priority scores determine which signals get attention. A hallucinated priority score is a critical failure mode — a dangerous signal might be deprioritized, or a trivial signal elevated. This is exactly the kind of correctness guarantee that Python provides and LLMs cannot. The formula is deterministic by definition; there is no "judgment" component.

**Alternatives Considered**:
- Keep LLM but add output validation — Validation cannot catch subtle formula misapplication
- Use LLM as fallback when Python fails — Defeats the purpose; fallback hallucination is still hallucination
- Hybrid (Python for formula, LLM for weights) — Weights are defined in thresholds.yaml (SOT), not a judgment call

**Impact**: `priority_score_calculator.py` added (632 lines). All 4 WF orchestrators updated: Step 2.3 now invokes Python CLI. Statistics engine calls updated with `--priority-ranked` argument. Priority score range is [1, 5] (verified in POST-VERIFY checks). Exit code 2 indicates fallback usage; exit code 1 = HALT.

---

## DEC-012: Unified Phase 2 Agent (`phase2-analyst.md`)

**Date**: 2026-03-02
**Context**: The system previously had 3 separate LLM agents for Phase 2: `signal-classifier.md` (Step 2.1), `impact-analyzer.md` (Step 2.2), and `priority-ranker.md` (Step 2.3). Each invocation required re-establishing context (workflow type, signal batch, STEEPs framework, FSSF definitions). This context fragmentation reduced quality.

**Decision**: Replace the 3 separate agents with a single `phase2-analyst.md` agent that handles Steps 2.1 + 2.2 in a unified context. Step 2.3 is no longer an LLM task (see DEC-011).

**Rationale**: Classification and impact analysis are deeply interdependent — the STEEPs category affects the impact assessment, and cross-domain impacts require understanding all categories simultaneously. Splitting them into two separate agent invocations forces artificial context boundaries. A unified agent retains full context across both steps, producing more coherent impact assessments. The original 3 agent specs are preserved as reference documents.

**Alternatives Considered**:
- Keep 3 agents but improve context passing — Context passing between agents is lossy; unified context is qualitatively better
- Merge all 3 steps including Python — Step 2.3 is deterministic; combining it with LLM would re-introduce hallucination risk
- 2-agent approach (classifier + combined impact+priority) — Priority ranking is Python; no benefit to combining with impact analysis

**Impact**: `phase2-analyst.md` added to `.claude/agents/workers/`. All 4 WF orchestrators updated. Worker agents (`deduplication-filter.md`, `realtime-delphi-facilitator.md`, `database-updater.md`, `scenario-builder.md`) updated to reference `@phase2-analyst`.

---

## DEC-013: 4-Layer Quality Defense (L2b + L3 Addition)

**Date**: 2026-03-01
**Context**: The quality defense system had L1 (Skeleton-Fill) and L2 (validate_report.py structural checks). However, the structural validator cannot detect semantic issues: wrong priority order, signals that don't match their claimed STEEPs category, strategic implications not derived from signal evidence, etc.

**Decision**: Add two new quality layers:
- **L2b** (`validate_report_quality.py`): 14 cross-reference QC checks (QC-001~014) — verifiable by Python
- **L3** (`quality-reviewer.md`): LLM semantic depth review — 3-pass review (signal content, section synthesis, strategic coherence)

**Rationale**: Python (L2b) can check verifiable properties: priority order, signal counts, FSSF distribution, citation completeness. LLM (L3) can check semantic properties: whether implications follow from evidence, whether H3 signals have sufficiently long time horizons, whether the executive summary accurately reflects the body. The two layers are complementary and non-redundant.

**Alternatives Considered**:
- Only L3 (LLM review only) — LLM cannot reliably count signals or verify priority order
- Only L2b (extended Python checks) — Python cannot evaluate semantic coherence
- Human review for quality (no L3) — 9 checkpoints already saturate human attention; automated first-pass is essential

**Impact**: `validate_report_quality.py` added (13 checks). `quality-reviewer.md` added (L3 agent). All WF orchestrators updated to invoke both before human review checkpoint. Progressive retry applies: targeted fix → full regen → human escalation (max 2 retries).

---

## DEC-014: Integrated/Weekly Statistics Preparation (master-orchestrator Step 5.1.2.5)

**Date**: 2026-03-02
**Context**: `report_statistics_engine.py` had `compute_integrated_execution_summary()` and `compute_weekly_aggregates()` functions but the master-orchestrator was not passing the required arguments (`--wf1-classified` through `--wf4-classified`, `--wf-exec-data`, `--daily-stats-data`). These functions produced placeholder values instead of real statistics.

**Decision**: Add Step 5.1.2.5 to master-orchestrator: inline Python that reads each WF's classified-signals + priority-ranked JSONs and writes `integrated-exec-summary-{date}.json`. Pass this file and WF-classified files to the statistics engine call. Weekly call gets all 28 daily stats files (7 days × 4 WFs).

**Rationale**: The statistics engine was already written to compute integrated statistics; the missing piece was preparation of the input data. Step 5.1.2.5 is a pure Python data preparation step with no judgment component — it reads JSON files and extracts counts. Adding it as inline Python in the orchestrator (rather than a new module) keeps the implementation minimal and avoids a new file just for JSON reshaping.

**Alternatives Considered**:
- Add a new Python module for integrated stats preparation — Overkill for simple JSON reshaping
- Have LLM prepare the exec summary — Would re-introduce hallucination risk for counts
- Skip integrated execution statistics — Reduces report informativeness; users need cross-WF stats

**Impact**: master-orchestrator.md updated with Step 5.1.2.5 inline Python. Statistics calls updated with 5 new integrated args and 28-file weekly arg. Integrated reports now show real WF execution statistics.

---

## DEC-015: Challenge-Response Pattern for Timeline Map Narratives

**Date**: 2026-03-06
**Context**: The Timeline Map requires cross-theme strategic synthesis — identifying compound effects like "tariff war + semiconductor regulation → supply chain crisis." This cross-theme insight is the core quality differentiator of the Timeline Map. The question is which agent pattern produces the highest quality: Sub-agent, Agent-Teams, or a new pattern.

**Decision**: Use **Challenge-Response** pattern — a dedicated adversarial reviewer (`@timeline-quality-challenger`) reviews the draft narratives from `@timeline-narrative-analyst`, and the analyst then refines based on challenges. This is NOT Agent-Teams and NOT simple self-review.

**Rationale**: Cross-theme synthesis requires **all themes in one context window**. Agent-Teams would fragment context across members, destroying the ability to identify theme interactions. A single sub-agent produces adequate quality but lacks peer review. Challenge-Response preserves unified context while adding adversarial quality assurance — mirroring academic peer review.

**Alternatives Considered**:
- Agent-Teams (3+ members per theme) — Context fragmentation destroys cross-theme insight
- Single sub-agent without review — No adversarial testing of narrative quality
- Self-review (same agent reviews its own work) — Blind spot persistence; separate agent detects more issues

**Impact**: Phase B expanded from B1 to B1-B4. New agent: `timeline-quality-challenger.md` (5 challenge dimensions, severity calibration: must_address/should_consider/minor). Challenger targets 3-8 challenges per review cycle. `must_address_count` gates whether refinement (B3) is mandatory.

---

## DEC-016: Python Narrative Gate (`narrative_gate.py`) for Phase B4

**Date**: 2026-03-06
**Context**: Phase B4 "Narrative Gate" was initially described as LLM instructions in the orchestrator. The 2nd Critical Reflection identified this as a Python 원천봉쇄 gap — structural verification of narratives (required fields, date counts, numeric consistency) is deterministic and should be Python-enforced, not LLM-instructed.

**Decision**: Implement `narrative_gate.py` as an actual Python script with 5 checks (NG-001~005). The orchestrator invokes it via CLI, not via LLM instructions.

**Rationale**: "계산은 Python이, 판단은 LLM이" — checking whether a JSON field exists, counting date patterns, verifying set membership are all deterministic operations. An LLM might incorrectly pass narratives with missing fields or insufficient date references. Python cannot make these mistakes.

**Alternatives Considered**:
- Keep as LLM instructions in orchestrator — Hallucination risk for structural checks
- Add checks to existing validate_timeline_map_quality.py — That script validates the final report, not the intermediate narratives; different lifecycle stage

**Impact**: `narrative_gate.py` added (5 checks: NG-001 required fields, NG-002 numeric consistency, NG-003 ≥2 date refs, NG-004 synthesis requirements, NG-005 refinement completeness). SOT path: `narrative_gate_script`. SOT-059 validates its existence. Orchestrator B4 invokes Python CLI.

---

## DEC-017: Timeline Map L2b Quality Defense Parity (TQ-009~011)

**Date**: 2026-03-06
**Context**: The Timeline Map's L2b validator (`validate_timeline_map_quality.py`) had 8 cross-reference checks (TQ-001~008). The 2nd Critical Reflection identified 3 PB verbatim verification gaps: PB-1 (ASCII timelines), PB-2 (cross-WF table numeric cells), and PB-3 (lead-lag days). These are the most critical Python 원천봉쇄 boundaries — if the LLM modifies these values, the entire pre-rendering pipeline is compromised.

**Decision**: Add TQ-009 (PB-1 ASCII verbatim match), TQ-010 (PB-2 table cell match), TQ-011 (PB-3 lead-lag citation accuracy) — all CRITICAL severity.

**Rationale**: PB-1~3 represent the hardest Python 원천봉쇄 boundary: ASCII art (PB-1), numeric table cells (PB-2), and cited numeric values (PB-3) must be character-for-character identical to what Python generated. Without programmatic verification, there is no way to guarantee the LLM copied them verbatim. A single altered digit in a table cell could change a decision-maker's interpretation.

**Alternatives Considered**:
- Trust the LLM instructions (PB rules in agent spec) — Instructions are advisory; programmatic verification is mandatory
- Manual spot-check by human reviewer — Humans miss single-digit changes in dense tables
- Hash-based verification — Too rigid; report formatting may add whitespace around PB content

**Impact**: `validate_timeline_map_quality.py` upgraded to v1.1.0 (8→11 checks). TQ-009 uses line-by-line comparison with whitespace normalization. TQ-010 extracts numeric cells from both expected and actual tables. TQ-011 verifies cited lag_days values against `lead_lag_computed` data.

---

## DEC-018: Pipeline Gate 2 Python Enforcement (`validate_phase2_output.py`)

**Date**: 2026-03-09
**Context**: The Phase 2 → Phase 3 transition (Pipeline Gate 2) had no Python enforcement. Each orchestrator contained inline LLM-instructed checks that could be hallucinated or inconsistently applied. Some orchestrators had conflicting field range definitions (e.g., impact_score `[-5, +5]` vs `[-10.0, +10.0]`).

**Decision**: Create `validate_phase2_output.py` with 8 deterministic checks (PG2-001~008) and require all orchestrators to invoke it as "Step A (Python MANDATORY)" before any additional LLM checks at PG2.

**Rationale**: Pipeline gates are the most critical quality enforcement points — they determine whether a phase's output is valid enough to proceed. An LLM cannot reliably check whether required JSON fields exist, whether score ranges are valid, or whether signal counts are consistent across files. These are all deterministic checks. The critical reflection found that 3 of 4 orchestrators had inline PG2 definitions that would never call the Python script.

**Alternatives Considered**:
- Keep inline LLM checks only — Found during reflection to be inconsistent across orchestrators
- Add Python as optional fallback — Defeats purpose; Python must be mandatory
- Integrate into validate_registry.py — Wrong lifecycle stage; registry is pre-execution, PG2 is mid-execution

**Impact**: `validate_phase2_output.py` (8 checks: PG2-001~008). SOT-060/061 ensure existence and binding. All 4 orchestrators updated with explicit `python3` invocation. 53 unit tests.

---

## DEC-019: Translation TERM Fidelity Checks (TERM-001~003)

**Date**: 2026-03-09
**Context**: `translation_validator.py` validated structural integrity (section headers, signal counts) but did not verify that critical terminology was preserved during EN→KO translation. Terms like "STEEPs", "FSSF", "pSST" could be mistranslated, mangled, or dropped by the translation LLM.

**Decision**: Add 3 TERM checks to `translation_validator.py`:
- TERM-001: Immutable terms (STEEPs, FSSF, pSST, etc.) must appear verbatim
- TERM-002: Preserve-list terms from `translation-terms.yaml` preserved (≥90%)
- TERM-003: Standardized mapping terms used (≥60% coverage)

**Rationale**: Term fidelity is the intersection of Python 원천봉쇄 and bilingual protocol. Whether a term appears in text is deterministic (string matching). Whether it's correctly translated can be verified against `translation-terms.yaml`. TERM-001 is strictest (binary: present or not). TERM-002 allows 10% miss for edge cases. TERM-003 is softest (checks standardization, not preservation).

**Alternatives Considered**:
- LLM self-check during translation — LLM is the translator; self-checking has blind spots
- Manual spot-check — Humans miss subtle term variations in dense Korean text
- Separate TERM validator script — Adds file proliferation; translation_validator.py is the natural home

**Impact**: `translation_validator.py` v1.1.0. Bug fix: ASCII-only word boundaries for Korean particle handling. 17 new tests (34 total).

---

## DEC-020: QC-014 Executive Summary Statistics Cross-Reference

**Date**: 2026-03-09
**Context**: L2b (`validate_report_quality.py`) had 13 QC checks but none verified that the Executive Summary's statistics (total signal count, STEEPs distribution) matched the actual source data. An LLM could hallucinate statistics (e.g., "25 signals detected" when only 18 exist).

**Decision**: Add QC-014: cross-reference executive summary statistics against priority-ranked source data.
- Sub-check A: Total signal count (exact match)
- Sub-check B: STEEPs distribution (±10% tolerance)

**Rationale**: The Executive Summary is the most-read section of every report. Decision-makers rely on its statistics to understand the scan scope. A hallucinated count could lead to under/over-estimation of signal volume. Python can extract the claimed count via regex and compare against source JSON — this is pure computation. The ±10% tolerance for STEEPs distribution accounts for rounding in percentage displays.

**Alternatives Considered**:
- Exact match for STEEPs distribution — Too rigid; 33.3% displays as "33%" or "34%"
- Skip STEEPs distribution, check total only — Distribution is equally important for coverage assessment
- Check in L3 (LLM review) — LLM cannot reliably count signals in source JSON

**Impact**: `validate_report_quality.py` 13→14 checks. FSSF types filtered via `_STEEPS_PREFIXES` to prevent false matches in WF3/WF4 reports. 22 unit tests.

---

## Summary

| ID | Decision | Key Rationale |
|----|----------|---------------|
| DEC-001 | "Multi&Global-News" / `multiglobal-news` | Dual nature in display, filesystem-safe in code |
| DEC-002 | WF3 FSSF skeleton extended | Shared FSSF/3H/TP framework, less duplication |
| DEC-003 | Total War paywall strategy | Irreplaceable signal quality from premium sources |
| DEC-004 | Quality-based sub-agent/Agent-Teams | Sub-agent for deterministic, Agent-Teams for judgment |
| DEC-005 | English-first all processing | Consistent LLM performance across 11 languages |
| DEC-006 | Standard `abstract` + `original_abstract` | Backward compatibility with shared workers |
| DEC-007 | WF3/WF4 overlap is not source overlap | Different sources, same stories = cross-validation |
| DEC-008 | Agent-Teams 5 members for integration | Balanced representation for 4 workflows |
| DEC-009 | `news-{date}-{site}-{seq}` signal IDs | Unique, sortable, source-informative |
| DEC-010 | 44 sites accepted (plan said 43) | Zero architectural impact, better coverage |
| DEC-011 | Python 원천봉쇄 for Step 2.3 priority scoring | Deterministic formula must be Python-enforced |
| DEC-012 | Unified `phase2-analyst.md` (Steps 2.1+2.2) | Unified context = better quality; Python handles 2.3 |
| DEC-013 | 4-Layer Quality Defense (L2b + L3) | Python checks verifiable; LLM checks semantic |
| DEC-014 | Integrated/weekly stats preparation (Step 5.1.2.5) | Real stats from Python, not LLM-generated placeholders |
| DEC-015 | Challenge-Response for Timeline Map narratives | Unified context + adversarial review = highest quality |
| DEC-016 | Python narrative gate (`narrative_gate.py`) for B4 | Structural verification must be Python, not LLM |
| DEC-017 | Timeline Map L2b parity (TQ-009~011) | PB-1/2/3 verbatim verification is non-negotiable |
| DEC-018 | Pipeline Gate 2 Python enforcement | Phase 2→3 transition must be Python-verified, not LLM-instructed |
| DEC-019 | Translation TERM fidelity (TERM-001~003) | Critical terminology preservation is deterministic string matching |
| DEC-020 | QC-014 exec summary stats cross-reference | Executive Summary statistics must match source data exactly |

---

**Document Version**: 4.0
**Last Updated**: 2026-03-09
**System Version**: Quadruple Workflow System v3.2.0
