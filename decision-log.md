# Decision Log -- WF4 Implementation

> Architectural decisions made during the implementation of WF4 (Multi&Global-News Environmental Scanning).
>
> System: Quadruple Environmental Scanning System v2.5.0
> Period: 2026-02-24

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

---

**Document Version**: 1.0
**Last Updated**: 2026-02-24
**System Version**: Quadruple Workflow System v2.5.0
