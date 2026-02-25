# Quadruple Environmental Scanning System — Methodology

> **Cross-platform canonical document.** This file is read by all AI CLI tools
> (Claude Code, Gemini CLI, OpenAI Codex CLI, GitHub Copilot, Cursor, Cline, etc.)
> to ensure adherence to the workflow methodology regardless of toolchain.
>
> **This is a ROUTER, not an encyclopedia.** Immutable rules are stated inline.
> All mutable parameters are referenced by file path — never copied here.

---

## 1. Identity

This project is the **Quadruple Environmental Scanning System** — an AI-driven pipeline that scans global information sources (academic papers, patents, policy documents, tech blogs, Korean news, global multilingual news) to detect **early signals of future change** across all domains.

### Absolute Goal (Fixed and Immutable)

> **"Catch up on early signals of future trends, medium-term changes, macro shifts,
> paradigm transformations, critical transitions, singularities, sudden events,
> and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas)
> AS FAST AS POSSIBLE."**

"AS FAST AS POSSIBLE" means speed of signal detection, not speed of execution. Quality is never sacrificed for throughput.

---

## 2. Immutable Rules (Tier 1)

These rules come from `env-scanning/config/core-invariants.yaml` and are architecturally immutable. They are embedded here because they **never change by definition** — drift is impossible. SOT-026 validates this section's integrity.

### 2.1 STEEPs Categories

All signals are classified into exactly 6 categories. This framework is the foundational classification system and cannot be altered.

| Code | Name | Scope |
|------|------|-------|
| **S** | Social | demographics, education, labor — NO spiritual content |
| **T** | Technological | innovation, digital transformation, AI, quantum computing |
| **E** | Economic | markets, finance, trade, platform economy |
| **E** | Environmental | climate, sustainability, resources, biodiversity |
| **P** | Political | policy, law, regulation, institutions, geopolitics |
| **s** | spiritual | ethics, psychology, values, meaning, AI ethics |

### 2.2 3-Phase Pipeline

Every workflow follows this strict sequential structure. Phases cannot be skipped or reordered.

| Phase | Name | Description |
|-------|------|-------------|
| **Phase 1** | Research | Information Collection: source scanning, deduplication, expert validation |
| **Phase 2** | Planning | Analysis & Structuring: classification, impact analysis, priority ranking |
| **Phase 3** | Implementation | Report Generation: DB update, report creation, archiving, self-improvement |

Gate checks (6 per transition) enforce quality between phases.

### 2.3 Workflow Independence

The system operates multiple independent workflows. This independence is absolute and inviolable:

- **WF1** (General Environmental Scanning): multi-source, arXiv excluded
- **WF2** (arXiv Academic Deep Scanning): arXiv only
- **WF3** (Naver News Environmental Scanning): Naver News only
- **WF4** (Multi&Global-News Environmental Scanning): 43 direct news sites, multilingual

> **Source counts, lookback periods, and category numbers are mutable parameters.**
> Always READ `env-scanning/config/workflow-registry.yaml` for current values.

**Independence rules:**
- WF1 does NOT know WF2, WF3, or WF4 exists. WF2 does NOT know WF1, WF3, or WF4 exists. WF3 does NOT know WF1, WF2, or WF4 exists. WF4 does NOT know WF1, WF2, or WF3 exists.
- No workflow reads or writes another workflow's data directories during execution
- Each produces a complete, independently valid final report
- Integration merges **final reports only** — never raw data or signal databases
- Any workflow can be disabled or deleted without affecting the others

**Execution order**: strictly sequential as defined in SOT (`execution.mode` and each workflow's `execution_order`).

### 2.4 VEV Protocol (Verify-Execute-Verify)

Every operation follows this 5-stage quality protocol:

1. **PRE-VERIFY** — Check preconditions before execution
2. **EXECUTE** — Perform the operation
3. **POST-VERIFY** — Validate results (3 layers)
4. **RETRY** — On failure, progressive escalation (max 2 retries)
5. **RECORD** — Log execution proof and metrics

### 2.5 Human Checkpoints

Human-in-the-Loop checkpoints ensure oversight and cannot be removed. The immutable checkpoint structure is:

- **Phase 2.5 (Analysis Review)**: required for each enabled workflow
- **Phase 3.4 (Report Approval)**: required for each enabled workflow
- **Integrated Report Approval**: required after merge

> **The total number of checkpoints depends on how many workflows are enabled.**
> READ `env-scanning/config/workflow-registry.yaml` → `checkpoints_total` and each workflow's `checkpoints` section for the current count and types.

### 2.6 Bilingual Protocol

- **Internal processing**: English (en)
- **External output**: Korean (ko)
- **English-first workflow**: Reports are generated in English → validated with EN profiles → translated to Korean by translation sub-agent → validated structurally by `translation_validator.py`
- STEEPs terminology must be 100% preserved in translation
- All reports are delivered in Korean

### 2.7 Database Atomicity

Signal database operations MUST follow this sequence:

1. Create pre-update snapshot
2. Perform atomic write with backup
3. On failure: restore from snapshot
4. Enforce signal ID uniqueness

### 2.8 Skeleton-Fill Report Generation

Reports MUST be generated by filling a pre-defined skeleton template — NOT by free-form generation. The skeleton contains all required section headers and signal blocks with placeholder tokens. The AI fills content into this structure; it does NOT create the structure itself.

### 2.9 4-Layer Quality Defense

Every report must pass through all 4 layers:

| Layer | Name | Mechanism |
|-------|------|-----------|
| L1 | Skeleton-Fill | Fill template, not free-form |
| L2 | Programmatic Validation | `env-scanning/scripts/validate_report.py` (15–18 checks, profile-dependent) |
| L3 | Progressive Retry | On CRITICAL failure: targeted fix → full regen → human escalation |
| L4 | Golden Reference | 9-field signal example anchors completeness |

Required signal fields (9): 분류, 출처, 핵심 사실, 정량 지표, 영향도, 상세 설명, 추론, 이해관계자, 모니터링 지표.

### 2.10 WF3-Specific Frameworks

WF3 (Naver News) uses additional classification systems beyond STEEPs:

**FSSF 8-Type Classification** (Future Signal Scanning Framework):
- Weak Signal, Wild Card, Discontinuity (CRITICAL priority)
- Driver, Emerging Issue, Precursor Event (HIGH priority)
- Trend, Megatrend (MEDIUM priority)

**Three Horizons**: H1 (0–2yr), H2 (2–7yr), H3 (7yr+)

**Tipping Point Detection**: Critical Slowing Down, Flickering patterns. Alert levels: GREEN → YELLOW → ORANGE → RED.

**Naver Section→STEEPs Mapping**: Defined in `env-scanning/config/sources-naver.yaml`. Each news section maps to a STEEPs category. READ the config file for current mappings — do not hardcode.

### 2.11 Temporal Consistency (시간적 일관성)

모든 일일 환경스캐닝은 마스터 오케스트레이터가 정의한 단일 시간 범위(scan window) 내에서 수행된다. 이것은 환경스캐닝의 가장 근본적인 원칙이다.

- **T₀**: 마스터 오케스트레이터 실행 시작 시점 (anchor timestamp)
- **Scan Window**: [T₀ - lookback_hours, T₀]
- 모든 워크플로우(WF1, WF2, WF3)는 동일한 T₀를 기준으로 한다
- lookback_hours는 SOT에서 워크플로우별로 정의된다 (기본: 24시간)
- 수집 시점(collection-time)과 수집 후(post-collection) 2중으로 시간 범위를 강제한다
- 범위 외 시그널은 Pipeline Gate 1에서 프로그래매틱으로 제거된다
- 모든 보고서에 스캔 시간 범위를 명시한다

> **"매 24시간 단위로 일정하고 고르고 지속적으로 변화를 모니터링한다"** — 이 원칙의 위반은 스캔 결과의 비교 가능성, 추세 분석의 정확성, 일일 모니터링의 연속성을 모두 훼손한다.

> Temporal consistency parameters are mutable (defined in SOT `system.temporal_consistency` and each workflow's `parameters.scan_window`). READ `env-scanning/config/workflow-registry.yaml` for current values — do not hardcode.

---

## 3. SOT Binding (Tier 2 — Read These Files)

All mutable parameters, thresholds, paths, and configurations live in the files below. **NEVER hardcode or memorize values from these files** — always read them at runtime.

### 3.1 Mandatory First Steps

Before executing ANY workflow:

1. **READ** `env-scanning/config/workflow-registry.yaml` — the Source of Truth (SOT) for all execution parameters, paths, and workflow definitions
2. **RUN** `python3 env-scanning/scripts/validate_registry.py` — must return exit code 0 (PASS) before proceeding
3. **READ** `env-scanning/config/core-invariants.yaml` — defines immutable boundaries and tunable parameter ranges

### 3.2 Configuration Files (READ before execution)

| File | Contains |
|------|----------|
| `env-scanning/config/workflow-registry.yaml` | **SOT**: workflow definitions, execution order, paths, parameters, checkpoints, integration settings |
| `env-scanning/config/core-invariants.yaml` | Immutable rules, tunable parameter bounds, major change domains |
| `env-scanning/config/domains.yaml` | STEEPs keyword definitions and search terms |
| `env-scanning/config/sources.yaml` | WF1 source list (arXiv disabled) |
| `env-scanning/config/sources-arxiv.yaml` | WF2 source list (arXiv only) |
| `env-scanning/config/sources-naver.yaml` | WF3 source list (Naver News only) |
| `env-scanning/config/thresholds.yaml` | Scoring thresholds, dedup parameters, AI confidence levels |
| `env-scanning/config/translation-terms.yaml` | Korean translation term mappings |

### 3.3 Validation Scripts (RUN after generation)

| Script | When | Exit Codes |
|--------|------|------------|
| `env-scanning/scripts/validate_registry.py` | Before ANY workflow starts | 0=PASS, 1=HALT, 2=WARN |
| `env-scanning/scripts/validate_report.py` | After EVERY report is generated | 0=PASS, 1=CRITICAL, 2=WARN |

### 3.4 Report Skeletons (READ for report generation)

| Skeleton (Korean) | Skeleton (English) | Workflow |
|--------------------|---------------------|----------|
| `references/report-skeleton.md` | `references/report-skeleton-en.md` | WF1, WF2 |
| `references/naver-report-skeleton.md` | `references/naver-report-skeleton-en.md` | WF3 |
| `references/integrated-report-skeleton.md` | `references/integrated-report-skeleton-en.md` | Integration |
| `references/weekly-report-skeleton.md` | `references/weekly-report-skeleton-en.md` | Weekly meta-analysis |

> All paths relative to `.claude/skills/env-scanner/`. English-first workflow uses the EN skeleton; the KO skeleton is used for translation validation.

---

## 4. Execution Protocol

### 4.1 Daily Scan Flow

```
Step 0: Read SOT → Validate (validate_registry.py) → Extract parameters
Step 1: WF1 — Phase 1 → Phase 2 → [Human Review] → Phase 3 → [Human Approval]
Step 2: WF2 — Phase 1 → Phase 2 → [Human Review] → Phase 3 → [Human Approval]
Step 3: WF3 — Phase 1 → Phase 2 → [Human Review] → Phase 3 → [Human Approval]
Step 4: WF4 — Phase 1 → Phase 2 → [Human Review] → Phase 3 → [Human Approval]
Step 5: Integration — Merge 4 reports → pSST unified ranking → [Human Approval]
```

### 4.2 Each Workflow's Internal Flow

```
Phase 1: Research
  1.1 Load historical signals DB (each WF has its own)
  1.2 Scan sources (per sources_config from SOT)
  1.3 Deduplicate (4-stage cascade: URL → String → Semantic → Entity)
  1.4 [Optional] Human review of filter results

Phase 2: Planning
  2.1 Classify into STEEPs (+ FSSF for WF3)
  2.2 Cross-impact analysis
  2.3 Priority ranking (weights defined in env-scanning/config/thresholds.yaml — tunable by SIE)
  2.4 [Optional] Scenario generation
  2.5 [REQUIRED] Human analysis review

Phase 3: Implementation
  3.1 Update signals database (with atomic backup)
  3.2 Generate report (skeleton-fill method) → validate_report.py
  3.3 Archive report and notify
  3.4 [REQUIRED] Human report approval
  3.5 Self-Improvement Analysis (SIE — independent per workflow)
```

### 4.3 Quality Rules

- Every generated report MUST pass `validate_report.py` BEFORE human review
- On CRITICAL validation failure: retry up to 2 times with progressive escalation
- Reports with unfilled `{{PLACEHOLDER}}` tokens are ALWAYS rejected
- Minimum quality: ≥5000 words, ≥30% Korean characters, ≥10 signal blocks, 7 sections

---

## 5. Data Organization

### 5.1 Directory Structure

```
env-scanning/
├── config/          ← All configuration files (SOT, sources, thresholds)
├── core/            ← Python modules (17 modules)
├── scripts/         ← Validation scripts
├── wf1-general/     ← WF1 data (raw/structured/filtered/analysis/signals/reports)
│   ├── exploration/        ← Source exploration data (v2.5.0)
│   │   ├── candidates/     ← Daily candidate files
│   │   └── history/        ← Persistent exploration history
│   └── ...
├── wf2-arxiv/       ← WF2 data (same structure as WF1)
├── wf3-naver/       ← WF3 data (same structure + FSSF outputs)
├── wf4-multiglobal-news/ ← WF4 data (same structure + FSSF + multilingual translation)
└── integrated/      ← Merged output (reports/daily, reports/archive, weekly/)
```

Each workflow's data directory is self-contained. Cross-workflow data access is forbidden.

### 5.2 Standard Signal Format

Raw signal files use `items[]` array. Each item contains:
- `id`, `title`, `source` (object: name, type, url, published_date)
- `content` (object: abstract, keywords, language)
- `preliminary_category`, `collected_at`
- `scan_metadata.execution_proof` (Proof of Execution — mandatory)

### 5.3 Signal ID Formats

- WF1/WF2: `{source}-{YYYYMMDD}-{sequence}`
- WF3: `naver-{YYYYMMDD}-{SID}-{NNN}`
- Exploration: `explore-{YYYYMMDD}-{source_name}-{NNN}`

---

## 6. Design Principles

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | "Improve the tuning, never break the machine" | Only fine-tune parameters within bounds; never alter core structure |
| 2 | Orchestrator-Worker Separation | Managers coordinate; workers execute. Never mix roles |
| 3 | Human-in-the-Loop | 7 checkpoints ensure human oversight |
| 4 | Quality-Based Progression | Advance by quality gates, not by time |
| 5 | Controlled Source Management | Adding/removing sources requires user approval |
| 6 | Bilingual Protocol | Internal: English. External: Korean |
| 7 | Database Atomicity | Snapshot → Write → Restore on failure |
| 8 | Workflow Independence | WF1/WF2/WF3 are invisible to each other |

---

## 7. Academic Foundations

| Methodology | Source | Applied In |
|-------------|--------|------------|
| WISDOM Framework | arXiv:2409.15340v1 | Multi-source scanning |
| Real-Time AI Delphi | ScienceDirect | Expert panel validation (Phase 1.5) |
| Cross-Impact Analysis | Wiley Online Library | Impact matrix (Step 2.2) |
| Millennium Project FRM 3.0 | millennium-project.org | Futures research methodology |
| FSSF 8-Type Classification | Futures studies standard | WF3 signal classification |
| Three Horizons | Curry & Hodgson | WF3 time horizon tagging |

---

## 8. Key Constraints

- **Source of Truth**: `env-scanning/config/workflow-registry.yaml` is the SINGLE authoritative definition. All paths and parameters come from this file. Never hardcode paths.
- **Validation at startup**: `validate_registry.py` must pass before any workflow executes. Failure = HALT.
- **No source overlap**: No enabled source may appear in more than one workflow.
- **SIE policy**: Each workflow runs its own Self-Improvement Engine independently. Shared configs (thresholds.yaml, domains.yaml) are NOT modifiable by SIE — they require user approval.
- **Report-only integration**: The integration step merges final reports. It never accesses raw data or signal databases of individual workflows.
