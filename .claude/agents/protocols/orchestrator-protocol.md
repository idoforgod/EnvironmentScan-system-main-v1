# Orchestrator Protocol (Shared)

## Purpose

This file defines the shared execution protocol used by ALL workflow orchestrators
(env-scan-orchestrator, arxiv-scan-orchestrator, naver-scan-orchestrator, multiglobal-news-scan-orchestrator). It is the single source of truth
for VEV, Pipeline Gates, Retry logic, and Verification Report structure.

**Referenced by**: All workflow orchestrators via `system.execution.protocol` in workflow-registry.yaml.

**Version**: 3.3.0
**Last Updated**: 2026-03-09

---

## 1. VEV (Verify-Execute-Verify) Pattern

Every step in every workflow follows this execution pattern:

```
┌─────────────────────────────────────────────┐
│  1. PRE-VERIFY (선행 조건 확인)                 │
│     - 입력 파일 존재 + 유효성                     │
│     - 이전 Step 출력물의 정합성                    │
│     - 실패 시 → 이전 Step 재확인 or 에러 보고        │
├─────────────────────────────────────────────┤
│  2. EXECUTE (기존 로직 100% 동일)               │
│     - TASK UPDATE (BEFORE)                  │
│     - Invoke worker agent                   │
│     - TASK UPDATE (AFTER)                   │
├─────────────────────────────────────────────┤
│  3. POST-VERIFY (3-Layer 사후 검증)            │
│     Layer 1: Structural (구조적)              │
│       - 파일 존재, JSON 유효, 스키마 준수           │
│     Layer 2: Functional (기능적)              │
│       - 목표 수치 달성, 데이터 무결성, 범위 유효성       │
│     Layer 3: Quality (품질적)                 │
│       - 정확도 목표치, 완전성, 일관성               │
├─────────────────────────────────────────────┤
│  4. RETRY (실패 시 재실행)                      │
│     - Layer 1 실패 → 즉시 재실행 (최대 2회)        │
│     - Layer 2 실패 → 실패 항목만 재실행 (최대 2회)    │
│     - Layer 3 실패 → 경고 + 사용자 알림            │
│     - 2회 재실행 후에도 실패 → 워크플로우 일시정지       │
├─────────────────────────────────────────────┤
│  5. RECORD (검증 결과 기록)                     │
│     - verification-report-{date}.json에 누적    │
│     - workflow-status.json에 step 결과 기록      │
└─────────────────────────────────────────────┘
```

**IMPORTANT**: All file paths in PRE-VERIFY and POST-VERIFY are relative to the
workflow's `data_root` as defined in workflow-registry.yaml. The orchestrator MUST
prepend `data_root` to all data file paths.

---

## 2. Retry Protocol

```yaml
On Post-Verification Failure:
  Layer_1_Fail:  # Structural (file missing, invalid JSON, wrong schema)
    action: immediate_retry
    max_retries: 2
    delay: "exponential_backoff (2s, 4s)"
    on_exhausted:
      critical_step: HALT_workflow
      non_critical_step: HALT_and_ask_user

  Layer_2_Fail:  # Functional (wrong count, out-of-range, missing fields)
    action: targeted_retry
    max_retries: 2
    delay: "exponential_backoff (2s, 4s)"
    on_exhausted:
      critical_step: HALT_workflow
      non_critical_step: HALT_and_ask_user

  Layer_3_Fail:  # Quality (below accuracy target, low confidence)
    action: warn_and_ask_user
    prompt: "품질 목표 미달: {detail}. 계속 진행하시겠습니까?"
    options:
      - "경고 수용 후 진행 (권장)"
      - "해당 Step 재실행"
    max_retries_if_chosen: 1

  Critical_Step_Override:  # Steps marked critical: true (e.g., 3.1 DB Update)
    any_layer_fail:
      action: RESTORE_AND_HALT
      restore_backup: true
      require_user_confirmation: true

Named_Actions:
  HALT_workflow:      "Stop workflow. Set status='failed'. Notify user with error details."
  HALT_and_ask_user:  "Pause workflow. Display failure detail. Ask user: retry manually or skip step."
  WARN_and_continue:  "Log warning. Set final_status='WARN_ACCEPTED'. Continue to next step."
  RESTORE_AND_HALT:   "Restore backup (e.g., signals/snapshots/). Set status='failed'. Log E7000."
```

---

## 3. Pipeline Gates

Phase transitions require data continuity and integrity validation.

**IMPORTANT**: All file paths in gate checks are relative to `data_root`.

```yaml
Pipeline_Gate_1:  # Phase 1 → Phase 2
  trigger: After Phase 1 complete (all steps including 1.4)
  checks:
    - signal_id_continuity: "filtered signals IDs ⊂ raw scan IDs"
    - classified_signals_complete: "all filtered signals have entry in structured/classified-signals"
    - shared_context_populated: "dedup_analysis field exists in context/shared-context"
    - file_pair_check: "all EN files have -ko counterpart (warn if missing)"
    - psst_dimensions_phase1: "SR, TC dimensions exist for all signals"
    - psst_dimensions_dc: "DC dimension exists for all non-duplicate signals"
    - temporal_boundary_check: |
        TC-003: MANDATORY Python enforcement — temporal_gate.py validates every signal.
        Each WF orchestrator invokes temporal_gate.py at Pipeline Gate 1 with the
        scan_window_state_file. See individual WF orchestrator specs for exact command.
        Exit code 0 = proceed, 1 = HALT (no signals remain after temporal filtering).
  on_fail:
    action: trace_back
    retry: re_execute_failing_step
    max_retries: 1

Pipeline_Gate_2:  # Phase 2 → Phase 3
  trigger: After Phase 2 complete (after Step 2.5 human approval)
  enforcement: MANDATORY
  script: >
    python3 env-scanning/scripts/validate_phase2_output.py
    --sot {SOT_PATH} --workflow {WORKFLOW_NAME} --date {SCAN_DATE} --json
  exit_code_0: proceed to Phase 3
  exit_code_1: HALT (CRITICAL failures — invalid enumerations or ranges)
  exit_code_2: WARN (ERROR-level issues — count mismatches)
  checks:
    - pg2_001_steeps_validity: "STEEPs category ∈ valid codes (Python-enforced)"
    - pg2_002_impact_range: "impact_score ∈ [-10.0, +10.0] (Python-enforced)"
    - pg2_003_priority_range: "priority_score ∈ [0.0, 10.0] (Python-enforced)"
    - pg2_004_fssf_validity: "FSSF type ∈ 8 canonical types (WF3/WF4 only, Python-enforced)"
    - pg2_005_three_horizons: "Three Horizons ∈ {H1, H2, H3} (WF3/WF4 only, Python-enforced)"
    - pg2_006_tipping_color: "Tipping Point color ∈ {GREEN, YELLOW, ORANGE, RED} (WF3/WF4 only)"
    - pg2_007_count_consistency: "classified count ≈ impact count ≈ ranked count"
    - pg2_008_required_fields: "id, title, priority_score, rank exist in all ranked signals"
    - human_approval_recorded: "Step 2.5 decision logged in human_decisions"
    - psst_minimum_threshold: "all signals have pSST ≥ 30"
    - psst_dimensions_es_cc: "ES, CC dimensions exist for all signals"
    - psst_final_computed: "psst_scores populated for all ranked signals"
  on_fail:
    action: trace_back
    retry: re_execute_failing_step
    max_retries: 1

Pipeline_Gate_3:  # Phase 3 completion
  trigger: After Step 3.4 approval
  checks:
    - database_updated: "new signals count in DB = classified signals count"
    - report_complete: "report file exists with all required sections"
    - quality_review_completed: |
        NORMAL PATH: logs/quality-review-{date}.json exists
          AND summary.recommendation != "escalate_to_human"
          AND summary.overall_grade in [A, B, C]
        ESCALATION PATH: If retry exhausted and human approved with warning banner
          (step_3_4 decision = "approved_with_quality_warning"),
          this check passes with WARN status. Human oversight supersedes gate.
    - archive_stored: "archive/{year}/{month}/ contains report copies"
    - snapshot_created: "signals/snapshots/database-{date}.json exists"
    - psst_all_dimensions_complete: "all 6 pSST dimensions exist for every ranked signal"
    - psst_grade_consistency: "psst_grade matches grade_thresholds"
    - psst_calibration_check: "calibration triggered if interval met"
  on_fail:
    action: warn_user
    log: "Pipeline Gate 3 issues detected"
```

---

## 4. Verification Report Structure

**File**: `{data_root}/logs/verification-report-{date}.json`

```json
{
  "workflow_id": "{workflow_name}-{date}",
  "vev_protocol_version": "2.2.1",
  "verification_summary": {
    "total_checks": 0,
    "passed": 0,
    "warned": 0,
    "failed": 0,
    "retries_triggered": 0,
    "overall_status": "PENDING"
  },
  "steps": {},
  "pipeline_gates": {},
  "generated_at": "{ISO8601}"
}
```

Each step records:
```json
{
  "step_id": {
    "pre_verification": { "status": "PASS|FAIL", "checks": [...] },
    "execution": { "status": "PASS|FAIL", "duration_seconds": 0 },
    "post_verification": {
      "layer_1": { "status": "PASS|FAIL", "checks": [...] },
      "layer_2": { "status": "PASS|FAIL", "checks": [...] },
      "layer_3": { "status": "PASS|FAIL|WARN", "checks": [...] }
    },
    "retries": { "count": 0, "details": [] },
    "final_status": "PASS|FAIL|WARN_ACCEPTED"
  }
}
```

---

## 5. Data Root Parameterization

Every orchestrator receives its `data_root` from workflow-registry.yaml. All data
file operations use paths relative to this root:

```
{data_root}/raw/daily-scan-{date}.json
{data_root}/filtered/new-signals-{date}.json
{data_root}/structured/classified-signals-{date}.json
{data_root}/analysis/impact-assessment-{date}.json
{data_root}/analysis/priority-ranked-{date}.json
{data_root}/signals/database.json
{data_root}/signals/snapshots/database-{date}.json
{data_root}/reports/daily/environmental-scan-{date}.md
{data_root}/reports/archive/{year}/{month}/
{data_root}/context/shared-context-{date}.json
{data_root}/context/previous-signals.json
{data_root}/logs/workflow-status.json
{data_root}/logs/verification-report-{date}.json
{data_root}/logs/qc-results-{date}.json
{data_root}/logs/quality-review-{date}.json
```

Worker agents receive the full resolved path (data_root + relative path) as
input parameters. Workers do NOT read workflow-registry.yaml directly.

---

## 6. Human Checkpoint Protocol

```yaml
human_checkpoints:
  step_1_4:
    type: optional
    trigger: "AI confidence < 0.9 in deduplication"
    command: "/review-filter"

  step_2_5:
    type: required
    description: "Required human review of analysis and priority rankings"
    command: "/review-analysis"
    display: "bilingual (KR primary, EN reference)"

  step_3_4:
    type: required
    description: "Required human approval of final report"
    command: "/approve or /revision"
    alternatives:
      approve: "Accept report and proceed to archiving"
      revision: "Request changes with specific feedback"
```

---

## 7. Report Quality Defense (4-Layer)

The 4-layer defense structure is defined in core-invariants.yaml. Layers L2 and L3 have been
expanded with sub-layers for deeper cross-reference and semantic validation.

```
L1:  Skeleton-Fill Method    — report-skeleton template enforces structure
L2a: Structural Validation   — validate_report.py (15–20 checks, profile-dependent)
L2b: Cross-Reference Quality — validate_report_quality.py (14 QC checks)
L3:  Semantic Depth Review   — quality-reviewer.md (LLM sub-agent, 3-pass review)
L4:  Golden Reference        — 9-field signal example in report-generator.md
```

**Progressive Retry** is the recovery mechanism applied when any layer fails:
- L2a CRITICAL → targeted fix (retry 1) → full regen (retry 2) → human escalation
- L2b CRITICAL → targeted fix using remedy field (retry 1) → full regen (retry 2) → human escalation
- L3 must_fix 1–5 → pass must_fix items to report-generator for targeted retry (max 2 retries)
- L3 must_fix > 5 → escalate to human review immediately
- L3 grade D → human escalation

**Execution order within Step 3.2 of every workflow**:
1. Generate report (L1 + L4 enforced by report-generator)
2. Run `validate_report.py` (L2a)
3. If L2a PASS or WARN: Run `validate_report_quality.py` (L2b)
4. If L2b PASS or WARN: Invoke `quality-reviewer` sub-agent (L3)
5. If L3 grade ≥ C: Proceed to translation
6. On any CRITICAL failure: trigger progressive retry

---

## 8. Phase-Specific Context Loading (v3.2.0 — Context Memory Optimization)

> **Principle**: "에이전트에게 불필요한 정보를 주면, 판단 품질이 저하된다."
> 각 Phase에서 필요한 데이터만 로딩하여 LLM의 신호 대 잡음 비를 최적화한다.

### Phase 1 (Research) — Required Context

| Data | Source | Purpose |
|------|--------|---------|
| sources config | `{sources_config}` | Scan targets |
| scan window state | `{scan_window_state_file}` | Temporal boundaries |
| signal DB (recent 7 days) | `{data_root}/signals/database.json` via **RecursiveArchiveLoader** | Dedup baseline |
| domains config | `env-scanning/config/domains.yaml` | STEEPs keywords |

**DO NOT load**: priority-ranked data, evolution indices, report statistics, integration data

### Phase 2 (Planning) — Required Context

| Data | Source | Purpose |
|------|--------|---------|
| classified signals | `{data_root}/structured/classified-signals-{date}.json` | Analysis input |
| thresholds | `env-scanning/config/thresholds.yaml` | Scoring parameters |
| shared context (selective) | via **SharedContextManager** — load only `final_classification`, `impact_analysis` | Field-level efficiency |

**DO NOT load**: raw scan data, dedup indexes, archive reports, report skeletons

### Phase 3 (Implementation) — Required Context

| Data | Source | Purpose |
|------|--------|---------|
| priority-ranked signals | `{data_root}/analysis/priority-ranked-{date}.json` | Report content |
| report skeleton | `{report_skeleton}` from SOT | L1 template |
| report statistics | `{data_root}/reports/report-statistics-{date}.json` | Metadata injection |
| evolution data | `{data_root}/analysis/evolution/evolution-map-{date}.json` | Timeline context |

**DO NOT load**: raw scan data, sources config, dedup indexes, intermediate classification files

### RLM Module Usage (Mandatory)

- **RecursiveArchiveLoader**: MUST use in Phase 1 for signal DB loading (7-day window, 10-20x reduction)
- **SharedContextManager**: MUST use in Phase 2 for selective field access (3-5x reduction)
- Both modules preserve full backward compatibility via legacy methods

---

## Version History
- v3.3.0 (2026-03-09): Pipeline Gate 2 Python enforcement (validate_phase2_output.py). 8 deterministic checks (PG2-001~008) replace LLM-only verification. Prevents hallucinated STEEPs codes, out-of-range scores, and invalid FSSF/Horizons/Tipping values from propagating to Phase 3.
- v3.2.0 (2026-03-09): Added Phase-Specific Context Loading (Section 8). Mandated RecursiveArchiveLoader for Phase 1, SharedContextManager for Phase 2. Context memory optimization for maximum LLM judgment quality.
- v2.3.0 (2026-03-01): Expanded Report Quality Defense to 4-layer with L2a/L2b/L3 sub-layers. Added quality_review_completed to Pipeline Gate 3. Added multiglobal-news-scan-orchestrator to scope.
- v2.2.1 (2026-02-10): Added naver-scan-orchestrator to scope. Added temporal_boundary_check (TC-003) to Pipeline Gate 1. Updated version strings.
- v2.2.0 (2026-02-03): Extracted from env-scan-orchestrator.md as shared protocol
- v2.2.0 (2026-02-02): Original VEV protocol in env-scan-orchestrator.md
