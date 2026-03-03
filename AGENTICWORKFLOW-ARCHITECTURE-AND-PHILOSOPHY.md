# Agentic Workflow Architecture and Philosophy

> **Quadruple Environmental Scanning System** | Architecture Reference (English)
>
> Version: 2.5.0 | Last Updated: 2026-03-02

This document is the concise English-language companion to `WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`. For the full Korean technical specification, refer to that document.

---

## 1. System Identity

The **Quadruple Environmental Scanning System** is an AI-driven pipeline that scans global information sources -- academic papers, patents, policy documents, tech blogs, Korean news, and 43 direct global news sites in 11 languages -- to detect **early signals of future change** across all domains.

### Absolute Goal (Fixed and Immutable)

> "Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) AS FAST AS POSSIBLE."

"AS FAST AS POSSIBLE" means **speed of signal detection**, not speed of execution. Quality is never sacrificed for throughput. The system optimizes for catching changes early, not for finishing workflows quickly.

---

## 2. Architecture Overview

```
                    MASTER ORCHESTRATOR
                    (SOT Read -> Validate -> Sequential Execution -> Integration)
                    |
        +-----------+-----------+-----------+
        |           |           |           |
        v           v           v           v
    WF1 General  WF2 arXiv  WF3 Naver  WF4 Multi&Global-News
    (25+ sources) (42 cats)  (6 sections) (43 sites, 11 langs)
        |           |           |           |
        +-----+-----+-----+----+-----------+
              |
              v
        INTEGRATION (Agent-Teams 5 members)
        -> pSST unified ranking -> Top 20
```

### Master Orchestrator Responsibilities

- Read SOT (`workflow-registry.yaml`) and bind all variables
- Run `validate_registry.py` (55 checks, exit 0 required)
- Execute WF1 -> WF2 -> WF3 -> WF4 sequentially
- Invoke Agent-Teams for integration
- Manage 9 human checkpoints
- Run SCG (State Consistency Gate) at phase transitions

---

## 3. Workflow Independence

The four workflows are **completely isolated**. This independence is absolute and inviolable:

- **WF1** (General Environmental Scanning): 25+ multi-source, arXiv excluded
- **WF2** (arXiv Academic Deep Scanning): arXiv only, 42 categories, 14-day lookback
- **WF3** (Naver News Environmental Scanning): Naver News only, 6 sections, Korean
- **WF4** (Multi&Global-News Environmental Scanning): 43 direct news sites, 11 languages

**Independence rules:**

1. No workflow knows any other workflow exists
2. No workflow reads or writes another workflow's data directories
3. Each produces a complete, independently valid final report
4. Integration merges **final reports only** -- never raw data or signal databases
5. Any workflow can be disabled or deleted without affecting the others

**Execution order**: WF1 -> WF2 -> WF3 -> WF4 -> Integration (strictly sequential).

---

## 4. 3-Phase Pipeline

Every workflow follows the same strict sequential structure. Phases cannot be skipped or reordered.

### Phase 1: Research (Information Collection)

| Step | Action | Key Agents |
|------|--------|------------|
| 1.1 | Load historical signals DB | archive-loader |
| 1.2 | Scan sources | multi-source-scanner (WF1/WF2), naver-news-crawler (WF3), multiglobal-news-crawler (WF4) |
| 1.3 | Deduplicate (4-stage cascade) | deduplication-filter |
| 1.4 | [Optional] Human review of filter results | -- |

**4-Stage Deduplication Cascade:**
1. URL normalization + exact match (1.0)
2. Jaro-Winkler string similarity (0.9)
3. SBERT semantic similarity (0.8)
4. NER + Jaccard entity matching (0.85)

### Phase 2: Planning (Analysis & Structuring)

| Step | Action | Key Agents |
|------|--------|------------|
| 2.1 | Classify into STEEPs (+ FSSF for WF3/WF4) | **@phase2-analyst** (unified Steps 2.1+2.2), naver/multiglobal-signal-detector |
| 2.2 | Cross-impact analysis | **@phase2-analyst** (unified context with Step 2.1), naver/multiglobal-pattern-detector |
| 2.3 | Priority ranking — **Python 원천봉쇄** | `priority_score_calculator.py` (no LLM) |
| 2.5 | **[REQUIRED] Human analysis review** | -- |

> **Step 2.3 Architecture**: Priority scoring is fully deterministic Python. Formula: `impact×0.40 + prob×0.30 + urgency×0.20 + novelty×0.10`. URGENCY_LOOKUP and DC_STAGE_SCORES are Python lookup tables — no LLM involved. Score range: [1, 5]. Exit codes: 0=OK, 2=warn (fallbacks used), 1=HALT.

### Phase 3: Implementation (Report Generation)

| Step | Action | Key Agents |
|------|--------|------------|
| 3.1 | Update signals database (atomic backup) | database-updater |
| 3.2 | Generate report (skeleton-fill method) | report-generator |
| 3.3 | Archive report and notify | archive-notifier |
| 3.4 | **[REQUIRED] Human report approval** | -- |
| 3.5 | Self-Improvement Analysis (SIE) | self-improvement-analyzer |

**Gate checks** (6 per transition) enforce quality between phases.

---

## 5. Quality-First Design

### Sub-Agent vs Agent-Teams

The system makes quality-based decisions on whether to use a single sub-agent or a multi-member Agent-Teams for each task:

- **Sub-Agent** (single): Used for deterministic, well-defined tasks (data collection, deduplication, validation)
- **Agent-Teams** (5 members): Used for complex judgment tasks requiring diverse perspectives (integration, cross-workflow analysis)

The integration step uses **Agent-Teams with 5 members**:
1. `report-merger` -- merge coordinator
2. `wf1-analyst` -- general signals expert
3. `wf2-analyst` -- academic signals expert
4. `wf3-analyst` -- Korean news expert
5. `wf4-analyst` -- global multilingual news expert

### 4-Layer Quality Defense

Every report must pass through all 4 layers before human review:

| Layer | Name | Mechanism |
|-------|------|-----------|
| L1 | Skeleton-Fill | Fill template, not free-form generation |
| L2a | Structural Validation | `validate_report.py` (15–20 checks, profile-dependent) |
| L2b | Cross-Reference QC | `validate_report_quality.py` (13 QC checks: QC-001~013) |
| L3 | Semantic Depth Review | `quality-reviewer.md` LLM sub-agent (3-pass review) |
| L4 | Golden Reference | 9-field signal example anchors completeness |

**Progressive Retry** on any failure: targeted fix → full regen → human escalation (max 2 retries).

**L2b QC Check Categories**: priority ordering (QC-001, CRITICAL), signal count vs claimed (QC-003, CRITICAL), FSSF distribution for WF3/WF4 (QC-008, CRITICAL), plus 10 ERROR/WARN level checks.

**L3 Review Passes**: Pass 1 — individual signal content quality; Pass 2 — section synthesis and coherence; Pass 3 — strategic implications traceability.

Required signal fields (9): 분류, 출처, 핵심 사실, 정량 지표, 영향도, 상세 설명, 추론, 이해관계자, 모니터링 지표.

---

## 6. Python/LLM Split

The system enforces "**Python 원천봉쇄**" — "계산은 Python이, 판단은 LLM이" (Python computes, LLM judges). All deterministic computations are implemented in Python with no LLM fallback; only semantic judgment tasks use LLM agents.

### Deterministic (Python) -- 33 modules

These modules perform calculations, validation, and data manipulation where correctness is verifiable:

| Category | Modules |
|----------|---------|
| **Validation** | validate_registry.py, validate_report.py, validate_report_quality.py, translation_validator.py |
| **Data Processing** | dedup_gate.py, temporal_gate.py, temporal_anchor.py |
| **Scoring** | psst_calculator.py, psst_calibrator.py, **priority_score_calculator.py**, report_statistics_engine.py |
| **Database** | database_recovery.py, signal_evolution_tracker.py |
| **Infrastructure** | naver_crawler.py, news_direct_crawler.py, adaptive_fetcher.py, source_health_checker.py, redirect_resolver.py |
| **Report Engineering** | skeleton_mirror.py, report_metadata_injector.py, timeline_map_generator.py, lazy_report_generator.py |
| **Translation** | translation_validator.py, bilingual_resolver.py, translation_parallelizer.py |
| **Exploration** | source_explorer.py, frontier_selector.py, exploration_gate.py, exploration_merge_gate.py |
| **Context** | context_manager.py, unified_task_manager.py, index_cache_manager.py, index_cache_manager.py |
| **Embedding** | embedding_deduplicator.py, impact_matrix_compressor.py |

> **priority_score_calculator.py** (Python 원천봉쇄): Enforces deterministic priority scoring. The LLM (`@phase2-analyst`) provides classification + impact analysis output fields; Python reads them and applies the formula. No LLM is invoked at Step 2.3.

### Semantic Judgment (LLM) -- 9 agent tasks

These require judgment, synthesis, and natural language generation:

| Task | Agent | Notes |
|------|-------|-------|
| Signal classification + impact analysis | **@phase2-analyst** (unified Steps 2.1+2.2) | Replaces signal-classifier + impact-analyzer + priority-ranker |
| FSSF classification | naver/multiglobal-signal-detector | WF3/WF4 only |
| Pattern detection | naver/multiglobal-pattern-detector | WF3/WF4 only |
| Report generation | report-generator | L1 skeleton-fill |
| Semantic quality review | **quality-reviewer** (L3, 3-pass) | New in v2.5.0 |
| Report merging | report-merger (Agent-Teams 5 members) | Integration only |
| Translation | translation-agent | EN→KO |
| Scenario building | scenario-builder | Optional |
| Expert panel | realtime-delphi-facilitator | Optional (>50 signals) |
| Self-improvement | self-improvement-analyzer | Per-workflow |

---

## 7. English-First Bilingual Protocol

All analysis is conducted in English first, then translated to Korean at each step:

```
Worker Agent (EN) -> EN Output -> VEV Validation -> @translation-agent -> KR Output -> VEV Lite Validation
```

**Key rules:**
- Internal processing: English (en)
- External output: Korean (ko)
- Reports are generated in English -> validated with EN profiles -> translated to Korean
- `translation_validator.py` validates structural integrity of translations
- STEEPs terminology must be 100% preserved in translation
- All final reports are delivered in Korean

**Translation quality targets:**
- Average confidence: > 0.90
- STEEPs term preservation: 100% (zero violations)
- Back-translation similarity: > 0.95 (for key reports)
- Translation overhead: < 25% of total workflow time

---

## 8. SOT Architecture

### Single Source of Truth

`env-scanning/config/workflow-registry.yaml` (v2.5.0) is the **single authoritative definition** for the entire system. All orchestrators read paths, parameters, and settings from this file.

**SOT rules:**
1. Master orchestrator MUST read this file at startup
2. `validate_registry.py` MUST pass (55 checks) before any workflow executes
3. Shared settings are referenced, never duplicated
4. Agents never hardcode paths -- SOT provides them
5. HALT-severity validation failures completely stop the workflow

### Configuration Files

| File | Purpose |
|------|---------|
| `workflow-registry.yaml` | SOT: workflow definitions, execution order, paths, parameters |
| `core-invariants.yaml` | Immutable rules, tunable parameter bounds |
| `domains.yaml` | STEEPs keyword definitions |
| `sources.yaml` | WF1 source list |
| `sources-arxiv.yaml` | WF2 source list |
| `sources-naver.yaml` | WF3 source list |
| `sources-multiglobal-news.yaml` | WF4 source list |
| `thresholds.yaml` | Scoring thresholds, dedup parameters |
| `translation-terms.yaml` | Korean translation term mappings |
| `self-improvement-config.yaml` | SIE behavior and safety limits |

### 55 Validation Checks

The validation script (`validate_registry.py`) runs 55 checks across categories:

- File existence (orchestrators, workers, skeletons, sources)
- Directory existence (data roots, output directories)
- Execution order uniqueness and sequentiality
- Source exclusivity (no overlap between workflows)
- Schema validity (PoE, SCG rules)
- WF-specific constraints (arXiv in WF2 only, Naver in WF3 only, MultiGlobalNews in WF4 only)

---

## 9. RLM Pattern (Reinforcement Learning from Monitoring)

### Self-Improvement Engine (SIE)

Each workflow runs its own SIE independently at Step 3.5:

**5 analysis areas:**
1. Threshold Tuning (dedup precision/recall)
2. Agent Performance (execution time, error rate)
3. Classification Quality (distribution skew, confidence gaps)
4. Workflow Efficiency (phase times, bottlenecks)
5. Hallucination Tracking (fabricated signals, URL validity)

**Safety tiers:**

| Tier | Action | Example |
|------|--------|---------|
| MINOR | Auto-apply (max 3/cycle) | Dedup threshold +/-5%, timeout adjustment |
| MAJOR | User approval required | Source add/remove, strategy changes |
| CRITICAL | Always blocked | Core invariant violations |

### Learned Patterns

- Signal evolution tracking across daily scans
- Source quality scoring based on historical signal yield
- Priority weight calibration from human feedback
- Dedup threshold optimization from correction patterns

### Human Feedback Loop

9 checkpoints across the full scan provide structured human feedback:

| Checkpoint | Type | Per-WF |
|------------|------|--------|
| Phase 2.5 | Analysis Review | 4 (WF1, WF2, WF3, WF4) |
| Phase 3.4 | Report Approval | 4 (WF1, WF2, WF3, WF4) |
| Integration | Final Approval | 1 |

Human corrections (priority adjustments, classification fixes) feed back into SIE for the next cycle.

---

## 10. Key Python Modules (33 modules)

### Core Infrastructure

| Module | Role |
|--------|------|
| `naver_crawler.py` | Naver News crawler + CrawlDefender 7-strategy cascade |
| `news_direct_crawler.py` | WF4 multilingual crawler (43 sites, 11 languages) |
| `naver_signal_processor.py` | WF3 FSSF/ThreeHorizons/TippingPoint/Anomaly detection |
| `news_signal_processor.py` | WF4 FSSF/ThreeHorizons/TippingPoint (multilingual) |
| `adaptive_fetcher.py` | Adaptive web data fetching |
| `source_health_checker.py` | Source availability monitoring |
| `redirect_resolver.py` | URL redirect resolution |

### Scoring and Validation

| Module | Role |
|--------|------|
| `psst_calculator.py` | pSST 6-dimension score calculation |
| `psst_calibrator.py` | Platt Scaling-based pSST calibration |
| `priority_score_calculator.py` | **Step 2.3 Python 원천봉쇄** — deterministic priority scoring (impact×0.40 + prob×0.30 + urgency×0.20 + novelty×0.10) |
| `report_statistics_engine.py` | Report quality metrics and placeholder computation |
| `validate_report_quality.py` | L2b cross-reference QC (13 checks: QC-001~013) |
| `translation_validator.py` | Translation structural integrity |
| `bilingual_resolver.py` | EN/KO term resolution |

### Data Processing

| Module | Role |
|--------|------|
| `dedup_gate.py` | 4-stage deduplication cascade (URL→Topic→Title→Entity) |
| `temporal_gate.py` | Temporal consistency enforcement (scan window) |
| `temporal_anchor.py` | T₀ anchor generation and scan window arithmetic |
| `signal_evolution_tracker.py` | Cross-day signal matching (NEW/RECURRING/STRENGTHENING/WEAKENING/FADED/TRANSFORMED) |
| `embedding_deduplicator.py` | SBERT embedding-based semantic dedup |
| `impact_matrix_compressor.py` | Cross-impact matrix sparse compression |

### Report Generation

| Module | Role |
|--------|------|
| `skeleton_mirror.py` | Skeleton template mirroring (EN/KO) |
| `report_metadata_injector.py` | Metadata injection (scan window, temporal consistency) |
| `timeline_map_generator.py` | 7-day Korean markdown timeline visualization |
| `lazy_report_generator.py` | Skeleton-fill report generation (L1 QA) |

### Exploration and Discovery

| Module | Role |
|--------|------|
| `source_explorer.py` | New source frontier discovery |
| `frontier_selector.py` | Exploration frontier ranking (VP-5 SIE) |
| `exploration_gate.py` | Exploration stage A/B/C quality gate |
| `exploration_merge_gate.py` | Cross-scan exploration result merge (VP-1~VP-5) |

### System Infrastructure

| Module | Role |
|--------|------|
| `self_improvement_engine.py` | SIE core engine (per-workflow, independent) |
| `database_recovery.py` | Snapshot-based DB recovery |
| `context_manager.py` | SharedContextManager (inter-agent context) |
| `unified_task_manager.py` | Unified task management |
| `translation_parallelizer.py` | Concurrent EN→KO translation worker pool |
| `index_cache_manager.py` | Vector embedding index cache |

---

## 11. Agent Hierarchy (41 agents)

### 5 Orchestrators

| Agent | Scope |
|-------|-------|
| **master-orchestrator** | Top-level: SOT validation, WF sequencing, integration, 9 checkpoints |
| **env-scan-orchestrator** | WF1: General environmental scanning + mandatory source exploration |
| **arxiv-scan-orchestrator** | WF2: arXiv academic deep scanning (48h lookback) |
| **naver-scan-orchestrator** | WF3: Naver news scanning + FSSF/3H/TP |
| **multiglobal-news-scan-orchestrator** | WF4: Multi&Global-News (43 sites, 11 languages) + FSSF/3H/TP |

### 13 Shared Workers

Used by multiple workflows:

| Agent | Role |
|-------|------|
| **phase2-analyst** | **NEW (v2.5.0)** — unified Steps 2.1+2.2 (classification + impact); replaces signal-classifier + impact-analyzer |
| **quality-reviewer** | **NEW (v2.5.0)** — L3 semantic depth review (3-pass LLM sub-agent) |
| archive-loader | Historical signal DB loading |
| multi-source-scanner | Multi-source HTTP fetching |
| deduplication-filter | 4-stage LLM dedup (handles uncertain cases) |
| report-generator | L1 skeleton-fill report generation |
| database-updater | Atomic DB updates with snapshot |
| archive-notifier | Report archiving and notification |
| translation-agent | EN→KO translation |
| self-improvement-analyzer | Per-workflow SIE (MINOR/MAJOR/CRITICAL safety tiers) |
| source-explorer | WF1 source exploration (mandatory) |
| realtime-delphi-facilitator | Expert validation (conditional: >50 signals) |
| scenario-builder | QUEST scenario generation (conditional) |

> **Step 2.3 Note**: Priority ranking is NOT an LLM agent task. `priority_score_calculator.py` (Python) handles it after `@phase2-analyst` completes Steps 2.1+2.2.

### 4 Source Sub-Agents

arxiv-agent, patent-agent, policy-agent, blog-agent.

### 4 WF3-Exclusive Workers

naver-news-crawler, naver-signal-detector, naver-pattern-detector, naver-alert-dispatcher.

### 5 WF4-Exclusive Workers

news-direct-crawler, news-translation-agent, news-signal-detector, news-pattern-detector, news-alert-dispatcher.

### 5 Integration Agent-Teams Members

report-merger (coordinator), wf1-analyst, wf2-analyst, wf3-analyst, wf4-analyst.

### 3 Source Discovery Workers

discovery-alpha (gap-directed), discovery-beta (random serendipitous), discovery-evaluator (independent scoring).

### 2 Support Files

orchestrator-protocol.md (shared VEV protocol), TASK_MANAGEMENT_EXECUTION_GUIDE.md.

---

## 12. Immutable Boundaries

These 10 elements can never be changed, not even by user override:

| # | Invariant | Description |
|---|-----------|-------------|
| 1 | 3-Phase Pipeline | Research -> Planning -> Implementation |
| 2 | Human Checkpoints | 9 checkpoints (4×2 per-WF + 1 integration) |
| 3 | STEEPs 6 Categories | S, T, E, E, P, s |
| 4 | VEV Protocol | 5-stage quality protocol |
| 5 | Pipeline Gates | 3 gates between phases |
| 6 | Database Atomicity | Snapshot -> Write -> Restore on failure |
| 7 | Phase Order | [1, 2, 3] strictly sequential |
| 8 | Bilingual Protocol | Internal=EN, External=KO |
| 9 | 4-Layer Quality Defense | L1 (Skeleton-Fill) → L2a (structural) → L2b (13 QC checks) → L3 (semantic LLM review) → L4 (Golden Reference) |
| 10 | Workflow Independence | No cross-WF data access during execution |

---

## Cross-References

| Document | Purpose |
|----------|---------|
| `WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | Full Korean technical specification |
| `USER-MANUAL.md` | Korean operational guide (v5.0) |
| `AGENTICWORKFLOW-USER-MANUAL.md` | English operational guide |
| `decision-log.md` | WF4 architectural decision log |
| `AGENTS.md` | Cross-platform methodology document |

---

**Document Version**: 3.0
**Last Updated**: 2026-03-02
**System Version**: Quadruple Workflow System v2.5.0 (Python 원천봉쇄 + 4-Layer Quality Defense)
