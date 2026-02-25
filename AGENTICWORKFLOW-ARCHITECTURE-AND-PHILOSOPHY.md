# Agentic Workflow Architecture and Philosophy

> **Quadruple Environmental Scanning System** | Architecture Reference (English)
>
> Version: 2.5.0 | Last Updated: 2026-02-24

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
| 2.1 | Classify into STEEPs (+ FSSF for WF3/WF4) | signal-classifier, naver/multiglobal-signal-detector |
| 2.2 | Cross-impact analysis | impact-analyzer, naver/multiglobal-pattern-detector |
| 2.3 | Priority ranking | priority-ranker |
| 2.5 | **[REQUIRED] Human analysis review** | -- |

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

Every report must pass through all 4 layers:

| Layer | Name | Mechanism |
|-------|------|-----------|
| L1 | Skeleton-Fill | Fill template, not free-form generation |
| L2 | Programmatic Validation | `validate_report.py` (15-18 checks, profile-dependent) |
| L3 | Progressive Retry | On CRITICAL failure: targeted fix -> full regen -> human escalation |
| L4 | Golden Reference | 9-field signal example anchors completeness |

Required signal fields (9): Category, Source, Core Fact, Quantitative Indicator, Impact Score, Detailed Description, Reasoning, Stakeholders, Monitoring Indicators.

---

## 6. Python/LLM Split

The system follows a strict "Python counts, LLM judges" principle:

### Deterministic (Python) -- 29 modules

These modules perform calculations, validation, and data manipulation where correctness is verifiable:

| Category | Modules |
|----------|---------|
| **Validation** | validate_registry.py, validate_report.py, translation_validator.py |
| **Data Processing** | dedup_gate.py, temporal_gate.py, temporal_anchor.py |
| **Scoring** | psst_calculator.py, psst_calibrator.py, report_statistics_engine.py |
| **Database** | database_recovery.py, signal_evolution_tracker.py |
| **Infrastructure** | naver_crawler.py, adaptive_fetcher.py, source_health_checker.py, redirect_resolver.py |
| **Report Engineering** | skeleton_mirror.py, report_metadata_injector.py, timeline_map_generator.py, lazy_report_generator.py |
| **Translation** | translation_validator.py, bilingual_resolver.py |
| **Exploration** | source_explorer.py, frontier_selector.py, exploration_gate.py, exploration_merge_gate.py |
| **Context** | context_manager.py, unified_task_manager.py, index_cache_manager.py |

### Creative (LLM) -- 11 agent tasks

These require judgment, synthesis, and natural language generation:

| Task | Agent |
|------|-------|
| Signal classification | signal-classifier |
| Impact analysis | impact-analyzer |
| Priority ranking | priority-ranker |
| FSSF classification | naver/multiglobal-signal-detector |
| Pattern detection | naver/multiglobal-pattern-detector |
| Report generation | report-generator |
| Report merging | report-merger (Agent-Teams) |
| Translation | translation-agent |
| Scenario building | scenario-builder |
| Expert panel | realtime-delphi-facilitator |
| Self-improvement | self-improvement-analyzer |

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
| `naver_signal_processor.py` | FSSF/ThreeHorizons/TippingPoint/Anomaly detection |
| `adaptive_fetcher.py` | Adaptive web data fetching |
| `source_health_checker.py` | Source availability monitoring |
| `redirect_resolver.py` | URL redirect resolution |

### Scoring and Validation

| Module | Role |
|--------|------|
| `psst_calculator.py` | pSST 6-dimension score calculation |
| `psst_calibrator.py` | Platt Scaling-based pSST calibration |
| `report_statistics_engine.py` | Report quality metrics |
| `translation_validator.py` | Translation structural integrity |
| `bilingual_resolver.py` | EN/KO term resolution |

### Data Processing

| Module | Role |
|--------|------|
| `dedup_gate.py` | Deduplication gate logic |
| `temporal_gate.py` | Temporal consistency enforcement |
| `temporal_anchor.py` | Scan window anchoring |
| `signal_evolution_tracker.py` | Cross-day signal evolution |
| `embedding_deduplicator.py` | SBERT embedding-based dedup |
| `impact_matrix_compressor.py` | Cross-impact matrix compression |

### Report Generation

| Module | Role |
|--------|------|
| `skeleton_mirror.py` | Skeleton template mirroring (EN/KO) |
| `report_metadata_injector.py` | Metadata injection into reports |
| `timeline_map_generator.py` | Timeline visualization generation |
| `lazy_report_generator.py` | Deferred report generation optimization |

### Exploration and Discovery

| Module | Role |
|--------|------|
| `source_explorer.py` | New source discovery engine |
| `frontier_selector.py` | Exploration frontier selection |
| `exploration_gate.py` | Exploration quality gate |
| `exploration_merge_gate.py` | Exploration result merge validation |

### System Infrastructure

| Module | Role |
|--------|------|
| `self_improvement_engine.py` | SIE core engine |
| `database_recovery.py` | Snapshot-based DB recovery |
| `context_manager.py` | SharedContextManager (inter-agent context) |
| `unified_task_manager.py` | Unified task management |
| `translation_parallelizer.py` | Translation parallelization |
| `index_cache_manager.py` | Index cache management |

---

## 11. Agent Hierarchy (40 agents)

### 5 Orchestrators

| Agent | Scope |
|-------|-------|
| **master-orchestrator** | Top-level: SOT validation, WF sequencing, integration |
| **env-scan-orchestrator** | WF1: General environmental scanning |
| **arxiv-scan-orchestrator** | WF2: arXiv academic deep scanning |
| **naver-scan-orchestrator** | WF3: Naver news scanning |
| **multiglobal-news-orchestrator** | WF4: Multi&Global-News scanning |

### 11 Shared Workers

Used by all workflows: archive-loader, multi-source-scanner, deduplication-filter, signal-classifier, impact-analyzer, priority-ranker, database-updater, report-generator, archive-notifier, translation-agent, self-improvement-analyzer.

### 4 Source Sub-Agents

arxiv-agent, patent-agent, policy-agent, blog-agent.

### 4 WF3-Specific Workers

naver-news-crawler, naver-signal-detector, naver-pattern-detector, naver-alert-dispatcher.

### 5 WF4-Specific Workers

multiglobal-news-crawler, multiglobal-translator, multiglobal-signal-detector, multiglobal-pattern-detector, multiglobal-alert-dispatcher.

### 5 Integration Agent-Teams Members

report-merger, wf1-analyst, wf2-analyst, wf3-analyst, wf4-analyst.

### 4 Conditional Workers

realtime-delphi-facilitator (>50 signals), scenario-builder (complexity > threshold), patent-agent (unimplemented), policy-agent (unimplemented).

### 2 Support Files

orchestrator-protocol.md (shared protocol), classification-prompt-template.md (prompt template).

---

## 12. Immutable Boundaries

These 10 elements can never be changed, not even by user override:

| # | Invariant | Description |
|---|-----------|-------------|
| 1 | 3-Phase Pipeline | Research -> Planning -> Implementation |
| 2 | Human Checkpoints | 9 checkpoints (4x2 per-WF + 1 integration) |
| 3 | STEEPs 6 Categories | S, T, E, E, P, s |
| 4 | VEV Protocol | 5-stage quality protocol |
| 5 | Pipeline Gates | 3 gates between phases |
| 6 | Database Atomicity | Snapshot -> Write -> Restore on failure |
| 7 | Phase Order | [1, 2, 3] strictly sequential |
| 8 | Bilingual Protocol | Internal=EN, External=KO |
| 9 | 4-Layer Quality Defense | Skeleton -> Validation -> Retry -> Golden Reference |
| 10 | Workflow Independence | No cross-WF data access |

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

**Document Version**: 2.5.0
**Last Updated**: 2026-02-24
**System Version**: Quadruple Workflow System v2.5.0
