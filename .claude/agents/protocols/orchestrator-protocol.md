# Orchestrator Protocol (Shared)

## Purpose

This file defines the shared execution protocol used by ALL workflow orchestrators
(env-scan-orchestrator, arxiv-scan-orchestrator, naver-scan-orchestrator). It is the single source of truth
for VEV, Pipeline Gates, Retry logic, and Verification Report structure.

**Referenced by**: All workflow orchestrators via `system.execution.protocol` in workflow-registry.yaml.

**Version**: 2.2.1
**Last Updated**: 2026-02-10

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
  checks:
    - signal_count_match: "classified count == impact-assessed count == priority-ranked count"
    - score_range_valid: "all priority_score in [0, 10], all impact_score in [-5, +5]"
    - human_approval_recorded: "Step 2.5 decision logged in human_decisions"
    - analysis_chain_complete: "classified → impact → priority files all exist"
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

## 7. Report Quality 4-Layer Defense

This defense is IMMUTABLE per core-invariants.yaml:

```
L1: Skeleton-Fill Method — use report-skeleton.md template
L2: Programmatic Validation — validate_report.py (14 checks)
L3: Progressive Escalation Retry — 3 stages (targeted → full regen → human)
L4: Golden Reference — 9-field signal example in report-generator.md
```

---

## Version History
- v2.2.1 (2026-02-10): Added naver-scan-orchestrator to scope. Added temporal_boundary_check (TC-003) to Pipeline Gate 1. Updated version strings.
- v2.2.0 (2026-02-03): Extracted from env-scan-orchestrator.md as shared protocol
- v2.2.0 (2026-02-02): Original VEV protocol in env-scan-orchestrator.md
