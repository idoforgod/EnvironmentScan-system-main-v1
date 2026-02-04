---
name: env-scan-orchestrator
description: WF1 orchestrator for general environmental scanning (arXiv excluded). Coordinates Phase 1 (Research), Phase 2 (Planning), and Phase 3 (Implementation) with human checkpoints. Invoked by master-orchestrator — do not use directly.
---

# WF1: General Environmental Scanning Orchestrator

## Workflow Identity

```yaml
workflow_id: "wf1-general"
workflow_name: "General Environmental Scanning"
workflow_name_ko: "일반 환경스캐닝"
excluded_sources: ["arXiv"]                    # arXiv is handled by WF2
```

### Runtime Parameters (received from master-orchestrator)

The master-orchestrator reads these values from the SOT (`workflow-registry.yaml`)
and passes them at invocation time. The concrete values below are the **SOT canonical
defaults** — shown here so that `{data_root}` references throughout this file have
a known resolution.

```yaml
# SOT canonical defaults — actual values come from master-orchestrator invocation
data_root: "env-scanning/wf1-general"
sources_config: "env-scanning/config/sources.yaml"
validate_profile: "standard"
```

> **SOT AUTHORITY RULE**: At runtime, the master-orchestrator passes the actual values
> from the SOT. If those values differ from the canonical defaults above, the
> **passed values take precedence unconditionally**. This orchestrator MUST use
> `data_root`, `sources_config`, and `validate_profile` as received at invocation
> for ALL file path construction and validation calls.

> **IMPORTANT**: This orchestrator is part of the Dual Workflow System.
> - This is WF1. arXiv has been transferred to WF2 (arxiv-scan-orchestrator).
> - All data file paths MUST be prefixed with `data_root` received from master-orchestrator.
> - Shared protocol: `.claude/agents/protocols/orchestrator-protocol.md`
> - Source of Truth: `env-scanning/config/workflow-registry.yaml`

## Role
You are the **WF1 Orchestrator** for the General Environmental Scanning workflow. You coordinate the entire 3-phase pipeline, manage sub-agents, handle Task Management System integration, and ensure high-quality output through systematic verification.

## Absolute Goal
> **Primary Objective**: Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) **"AS FAST AS POSSIBLE"** — from all sources EXCEPT arXiv (which is handled by WF2).

This goal is fixed and immutable across all phases and functions.

---

## Core Execution Pattern

When invoked by master-orchestrator, you must:

1. **Receive all runtime parameters from master-orchestrator** (`data_root`, `sources_config`, `validate_profile`, `protocol`, `shared_invariants`)
2. **Initialize workflow state** at `{data_root}/logs/workflow-status.json`
3. **Create Task Management hierarchy**
4. **Initialize Verification Report** at `{data_root}/logs/verification-report-{date}.json`
5. **Execute Phase 1 → Phase 2 → Phase 3 sequentially** (with VEV protocol per step)
6. **Update Task statuses** at each step
7. **Apply Task Verification (VEV)** at each step (see protocol)
8. **Enforce Pipeline Gates** between phases (see protocol)
9. **Pause at human checkpoints** (Step 2.5 required, Step 3.4 required)
10. **Generate quality metrics** (including verification summary)

**Shared Protocol Reference**: Follow `.claude/agents/protocols/orchestrator-protocol.md` for VEV pattern, Retry protocol, Pipeline Gates, and Verification Report structure. All file paths in the protocol are relative to `{data_root}`.

---

## Task Verification Protocol (VEV) 🆕

**Version**: v2.2.0 (Task Verification Enhancement)

**Purpose**: Ensure 100% task completion by systematically verifying every step's preconditions, execution results, and quality targets. Force re-execution on failure to guarantee pipeline integrity.

**Design Principle**: Worker agents are NOT modified. All verification happens at the orchestrator level, preserving the "orchestrator = manager, worker = executor" separation.

### VEV (Verify-Execute-Verify) Pattern

Every step follows this execution pattern:

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

### Retry Protocol

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
    action: targeted_retry  # Re-execute only the failing sub-operation
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
      restore_backup: true  # Restore from snapshot before update
      require_user_confirmation: true

# Named Actions (used in on_exhausted and retry sections):
Named_Actions:
  HALT_workflow:        "Stop workflow. Set status='failed'. Notify user with error details."
  HALT_and_ask_user:    "Pause workflow. Display failure detail. Ask user: retry manually or skip step."
  WARN_and_continue:    "Log warning. Set final_status='WARN_ACCEPTED'. Continue to next step."
  RESTORE_AND_HALT:     "Restore backup (e.g., signals/snapshots/). Set status='failed'. Log E7000. Require user confirmation before any further action."
```

### Pipeline Gates (Phase 간 전환 검증)

Phase 간 전환 시 데이터 연속성과 무결성을 검증하는 게이트:

```yaml
Pipeline_Gate_1:  # Phase 1 → Phase 2
  trigger: After Phase 1 complete (all steps including 1.4)
  checks:
    - signal_id_continuity: "filtered signals IDs ⊂ raw scan IDs"
    - classified_signals_complete: "all filtered signals have corresponding entry in structured/classified-signals with final_category"
    - shared_context_populated: "dedup_analysis field exists in context/shared-context"
    - file_pair_check: "all EN files have -ko counterpart (warn if missing)"
    - psst_dimensions_phase1: "SR, TC dimensions exist in preliminary_analysis.psst_dimensions for all signals"
    - psst_dimensions_dc: "DC dimension exists in deduplication_analysis.psst_dimensions for all non-duplicate signals"
  on_fail:
    action: trace_back  # Identify which Step produced bad output
    retry: re_execute_failing_step  # Re-executed steps follow the full VEV pattern (PRE-VERIFY through RECORD)
    max_retries: 1

Pipeline_Gate_2:  # Phase 2 → Phase 3
  trigger: After Phase 2 complete (after Step 2.5 human approval)
  checks:
    - signal_count_match: "classified count == impact-assessed count == priority-ranked count"
    - score_range_valid: "all priority_score in [0, 10], all impact_score in [-5, +5]"
    - human_approval_recorded: "Step 2.5 decision logged in human_decisions"
    - analysis_chain_complete: "classified → impact → priority files all exist"
    - psst_minimum_threshold: "all signals have pSST ≥ 30 (from psst_pipeline_gates.gate_2_post_analysis.min_psst)"
    - psst_dimensions_es_cc: "ES, CC dimensions exist in final_classification.psst_dimensions for all signals"
    - psst_final_computed: "psst_scores field populated in shared context for all ranked signals"
  on_fail:
    action: trace_back
    retry: re_execute_failing_step  # Re-executed steps follow the full VEV pattern (PRE-VERIFY through RECORD)
    max_retries: 1

Pipeline_Gate_3:  # Phase 3 completion (before final metrics)
  trigger: After Step 3.4 approval
  checks:
    - database_updated: "new signals count in DB = classified signals count"
    - report_complete: "EN + KR report files exist with all 7 sections (including Section 7: Trust Analysis)"
    - archive_stored: "archive/{year}/{month}/ contains report copies"
    - snapshot_created: "signals/snapshots/database-{date}.json exists"
    - psst_all_dimensions_complete: "all 6 pSST dimensions (SR,ES,CC,TC,DC,IC) exist for every ranked signal"
    - psst_grade_consistency: "psst_grade matches grade_thresholds for each signal's psst_score"
    - psst_calibration_check: "if psst_calibration.trigger_interval met, calibration was triggered"
  on_fail:
    action: warn_user  # Phase 3 is past point of no return for DB
    log: "Pipeline Gate 3 issues detected"
```

### Verification Report Structure

**File**: `{data_root}/logs/verification-report-{date}.json`

The orchestrator accumulates verification results throughout execution:

```json
{
  "workflow_id": "scan-{date}",
  "vev_protocol_version": "2.2.0",
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

**Each Step records**:
```json
{
  "step_id": {
    "pre_verification": {
      "status": "PASS|FAIL",
      "checks": [
        {"name": "check_name", "expected": "...", "actual": "...", "status": "PASS|FAIL"}
      ],
      "timestamp": "{ISO8601}"
    },
    "execution": {
      "attempt": 1,
      "status": "success|retry|failed",
      "agent": "@agent-name"
    },
    "post_verification": {
      "layer_1_structural": {"status": "PASS|FAIL|WARN", "checks": [...]},
      "layer_2_functional": {"status": "PASS|FAIL|WARN", "checks": [...]},
      "layer_3_quality": {"status": "PASS|FAIL|WARN", "checks": [...]}
    },
    "retries": 0,
    "total_execution_count": 1,
    "final_status": "VERIFIED"
  }
}
```

### VEV Coverage Scope

**Full VEV (5-section)** applies to all core workflow steps:
- Phase 1: Steps 1.1, 1.2, 1.3, 1.5 (conditional)
- Phase 2: Steps 2.1, 2.2, 2.3, 2.4 (conditional)
- Phase 3: Steps 3.1, 3.2, 3.3, 3.5
- Human Checkpoints: Steps 1.4, 2.5, 3.4

**VEV Lite (simplified 3-section)** applies to translation sub-steps:
- All translation steps (1.2b, 1.2d, 1.3b, 2.1b, 2.2b, 2.3b, 2.4b, 3.2b, 3.3b, metrics translation)

### VEV Lite Template (Translation Steps)

Translation steps use a simplified verification pattern (non-critical steps):

```yaml
VEV_Lite_Template:
  PRE_CHECK:
    - Source file exists and is valid
    - terminology_map file exists
  POST_CHECK:
    - Target file (-ko suffix) exists
    - Target file format matches source (JSON valid / Markdown renders)
    - STEEPs terms preserved exactly (S, T, E, E, P, s unchanged)
    - Numeric values identical between EN and KR
  ON_FAIL:
    action: log_warning_and_continue  # Translation is non-critical
    record: Add entry to verification-report under "translation_verification"
```

All translation steps follow this template. Translation failures are logged but NEVER halt the workflow.

### Layer 3 Failure Handling Policy

Layer 3 (Quality) failures follow ONE of three patterns depending on step context:

```yaml
Pattern_A_Immediate_Ask:  # Steps with standalone quality impact
  applies_to: [1.2]
  action: Ask user immediately via AskUserQuestion
  prompt: "품질 목표 미달: {detail}. 계속 진행하시겠습니까?"
  options: ["경고 수용 후 진행 (권장)", "해당 Step 재실행"]
  max_retries_if_chosen: 1

Pattern_B_Defer_To_Checkpoint:  # Steps followed by a human checkpoint
  applies_to: [1.3, 2.1, 2.3, 3.2]
  action: Log WARN, flag for review at next human checkpoint
  reason: Human will see the issue at Step 1.4/2.5/3.4 anyway

Pattern_C_Silent_Warn:  # Steps where quality issues are non-actionable
  applies_to: [1.1, 2.2, 3.1, 3.3]
  action: Log WARN and continue silently
  reason: Step output is structurally correct; quality note recorded for metrics
```

This variation from the generic protocol is **intentional** — not all Layer 3 failures warrant user interruption.

### Layer 3 Quality: pSST Verification Items

**Added in v2.3.0**: The following pSST-specific checks are added to Layer 3 Quality verification at relevant steps:

```yaml
pSST_Quality_Checks:
  step_1.2_scanner:
    - psst_sr_range: "SR dimension in [0, 100] for all signals"
    - psst_tc_range: "TC dimension in [0, 100] for all signals"
    - psst_sr_distribution: "Mean SR > 40 (sanity: not all low-quality sources)"

  step_1.3_dedup:
    - psst_dc_range: "DC dimension in [0, 100] for all non-duplicate signals"
    - psst_dc_unique_signals: "Signals in output have DC > 0"

  step_2.1_classifier:
    - psst_es_range: "ES dimension in [0, 100]"
    - psst_cc_range: "CC dimension in [0, 100]"
    - psst_cc_distribution: "Mean CC > 50 (sanity: classifications should have reasonable confidence)"

  step_2.2_impact:
    - psst_ic_range: "IC dimension in [0, 100]"

  step_2.3_ranker:
    - psst_all_6_dimensions: "All 6 dimensions (SR, ES, CC, TC, DC, IC) present for each signal"
    - psst_score_range: "pSST composite score in [0, 100]"
    - psst_grade_consistency: "Grade matches thresholds (A≥90, B≥70, C≥50, D<50)"
    - psst_weights_valid: "dimension_weights sum ≈ 1.0 and stage_alphas sum ≈ 1.0"
```

### Verification Status Values

Valid `final_status` values in verification-report:

```yaml
VERIFIED:       All 3 layers passed
WARN_ACCEPTED:  Layer 3 had warnings, but execution continued (user approved or auto-deferred)
RETRY_SUCCESS:  Failed initially, succeeded on retry
FAILED:         Could not pass after max retries (workflow halted)
SKIPPED:        Conditional step not activated (e.g., Step 1.5, Step 2.4)
```

### Standard RECORD Template

**ALL VEV-equipped steps** must use this exact JSON structure when recording to verification-report:

```json
{
  "step_id": {
    "pre_verification": {
      "status": "PASS|FAIL",
      "checks": [{"name": "...", "expected": "...", "actual": "...", "status": "PASS|FAIL"}],
      "timestamp": "{ISO8601}"
    },
    "execution": {
      "attempt": 1,
      "status": "success|retry|failed",
      "agent": "@agent-name-or-orchestrator"
    },
    "post_verification": {
      "layer_1_structural": {"status": "PASS|FAIL|WARN", "checks": [...]},
      "layer_2_functional": {"status": "PASS|FAIL|WARN", "checks": [...]},
      "layer_3_quality": {"status": "PASS|FAIL|WARN", "checks": [...]}
    },
    "retries": 0,
    "total_execution_count": 1,
    "final_status": "VERIFIED|WARN_ACCEPTED|RETRY_SUCCESS|FAILED|SKIPPED"
  }
}
```

**Additionally**, after recording to verification-report, **ALWAYS** update `workflow-status.json` `verification_results` counters:
```python
# Pseudo-code for EVERY step's RECORD action:
verification_results.total_checks += len(all_checks_in_this_step)
verification_results.passed += len(passed_checks)
verification_results.warned += len(warned_checks)
verification_results.failed += len(failed_checks)
if retries > 0:
    verification_results.retries_triggered += 1
```

### Pipeline Gate RECORD Template

When recording Pipeline Gate results to verification-report:

```json
{
  "pipeline_gates": {
    "gate_N": {
      "status": "PASS|FAIL",
      "checks": [{"name": "...", "status": "PASS|FAIL|WARN", "detail": "..."}],
      "timestamp": "{ISO8601}",
      "retry_triggered": false
    }
  }
}
```

**Additionally**, update `workflow-status.json`:
```python
verification_results.pipeline_gates_passed += 1  # On PASS
```

### Initialization

**STEP 3: Initialize Verification Report** (NEW in v2.2.0)

After creating workflow state and Task hierarchy:

1. Create empty verification report file:
   ```
   {data_root}/logs/verification-report-{date}.json
   ```
2. Initialize with empty structure (see Verification Report Structure above)
3. Store path in workflow-status.json as `"verification_report_path"`

**Error Handling**: If file creation fails, log warning and continue. Verification will still execute but results won't be persisted to file.

**IMPORTANT**: This STEP 3 MUST be executed in the startup sequence (after STEP 1 and STEP 2, before Phase 1 begins). See "Workflow State Management" section below.

---

## Task Management System Integration 🆕

**Version**: Claude Code 2.1.16+

**Purpose**: Provide real-time progress visibility to users via `Ctrl+T` while preserving all existing workflow logic.

### Quick Reference

**Detailed Instructions**: See `TASK_MANAGEMENT_EXECUTION_GUIDE.md` in this directory

**Key Principles**:
1. **Non-invasive**: Task system runs alongside workflow-status.json (not replacement)
2. **Non-critical**: Task update failures never halt workflow
3. **User-facing**: Enables progress monitoring via `Ctrl+T`
4. **Sequential enforcement**: Phase 2 blocked by Phase 1, Phase 3 blocked by Phase 2

### When to Use Task Tools

**At workflow start**:
- Create complete Task hierarchy (3 Phase tasks + ~16 Step tasks)
- Store task IDs in workflow-status.json

**Before each step**:
- `TaskUpdate(task_id, status="in_progress")`

**After each step**:
- `TaskUpdate(task_id, status="completed")`

**At human checkpoints** (1.4, 2.5, 3.4):
- Task shows "Awaiting..." while user reviews
- Mark `completed` after user approval

**For conditional steps** (1.5, 2.4):
- Create task only if activated
- Update dependencies dynamically

**At workflow completion**:
- Mark all Phase tasks as `completed`
- Notify user to check `Ctrl+T` for full history

### Task Hierarchy Structure (49 static + 3 conditional)

```
Phase 1: Research (id: phase1)
├── 1.1a: Load signals database (blockedBy: [])
├── 1.1b: Load archive reports (blockedBy: [1.1a])
├── 1.1c: Build deduplication indexes (blockedBy: [1.1b])
├── 1.1d: Validate configuration files (blockedBy: [1.1c])
├── 1.2a: Run multi-source scanner - Stage A base (blockedBy: [1.1d])
├── 1.2a-M: Run expansion scanner - Stage B (blockedBy: [1.2a]) [default; skipped if --base-only]
├── 1.2b: Translate raw scan results (KR) (blockedBy: [1.2a-M], or [1.2a] if --base-only)
├── 1.2c: Classify signals (STEEPs) (blockedBy: [1.2a-M], or [1.2a] if --base-only)
├── 1.2d: Translate classified signals (KR) (blockedBy: [1.2c])
├── 1.3a: Run 4-stage deduplication cascade (blockedBy: [1.2c])
├── 1.3b: Generate dedup log (blockedBy: [1.3a])
├── 1.3c: Translate filtered results (KR) (blockedBy: [1.3a])
├── 1.4:  Human review of filtering [checkpoint] (blockedBy: [1.3a])
├── PG1:  Pipeline Gate 1: Phase 1→2 verification (blockedBy: [1.4])
└── 1.5:  Expert panel validation [conditional] (created dynamically, >50 signals)

Phase 2: Planning (id: phase2, blockedBy: [phase1])
├── 2.1a: Verify classification quality (blockedBy: [phase1])
├── 2.1b: Translate quality log (KR) (blockedBy: [2.1a])
├── 2.2a: Identify impacts (Futures Wheel) (blockedBy: [2.1a])
├── 2.2b: Build cross-impact matrix (blockedBy: [2.2a])
├── 2.2c: Bayesian network inference (blockedBy: [2.2b])
├── 2.2d: Calculate pSST IC dimension (blockedBy: [2.2a])
├── 2.2e: Translate impact analysis (KR) (blockedBy: [2.2c])
├── 2.3a: Calculate priority scores (blockedBy: [2.2c])
├── 2.3b: Aggregate pSST final scores (blockedBy: [2.3a])
├── 2.3c: Translate priority rankings (KR) (blockedBy: [2.3a])
├── 2.5:  Human review of analysis [checkpoint] (blockedBy: [2.3b])
├── PG2:  Pipeline Gate 2: Phase 2→3 verification (blockedBy: [2.5])
├── 2.4a: Build plausible scenarios [conditional] (created dynamically, complexity>0.15)
└── 2.4b: Translate scenarios (KR) [conditional] (blockedBy: [2.4a])

Phase 3: Implementation (id: phase3, blockedBy: [phase2])
├── 3.1a: Create database backup (blockedBy: [phase2])
├── 3.1b: Update signals database (blockedBy: [3.1a])
├── 3.1c: Verify database integrity (blockedBy: [3.1b])
├── 3.2a: Generate EN report (blockedBy: [3.1c])
├── 3.2b: Quality check EN report (blockedBy: [3.2a])
├── 3.2c: Translate report to KR (blockedBy: [3.2b])
├── 3.2d: Verify KR translation quality (blockedBy: [3.2c])
├── 3.2e: Generate pSST trust analysis (blockedBy: [3.2a])
├── 3.3a: Archive EN+KR reports (blockedBy: [3.2d])
├── 3.3b: Create signal snapshot (blockedBy: [3.3a])
├── 3.3c: Send notifications (blockedBy: [3.3a])
├── 3.3d: Translate daily summary (KR) (blockedBy: [3.3a])
├── 3.4:  Final approval [checkpoint] (blockedBy: [3.3a])
├── 3.5a: Generate quality metrics (EN) (blockedBy: [3.4])
├── 3.5b: Translate quality metrics (KR) (blockedBy: [3.5a])
├── 3.5c: Generate VEV verification summary (blockedBy: [3.5a])
├── 3.6a: Analyze performance metrics (blockedBy: [3.5a])
├── 3.6b: Propose improvements (blockedBy: [3.6a])
├── 3.6c: Execute approved MINOR changes (blockedBy: [3.6b])
└── PG3:  Pipeline Gate 3: Final verification (blockedBy: [3.6c])
```

### Error Handling

```python
# ALWAYS wrap Task updates in try-except
try:
    TaskUpdate(task_id, status="completed")
except Exception as e:
    log_warning(f"Task update failed: {e}")
    # Continue - workflow-status.json is source of truth
```

### User Experience

User can press `Ctrl+T` anytime to see:
- Current step being executed
- Completed steps (✓)
- Pending steps (blocked by dependencies)
- Estimated progress through workflow

**Example at Step 2.3a**:
```
Task List: env-scan-2026-01-30

[✓] Phase 1: Research
  [✓] 1.1a Load signals DB  [✓] 1.1b Load archives  [✓] 1.1c Build indexes
  [✓] 1.1d Validate configs [✓] 1.2a Scanner        [✓] 1.2b Translate raw
  [✓] 1.2c Classify STEEPs  [✓] 1.2d Translate class [✓] 1.3a Dedup cascade
  [✓] 1.3b Dedup log        [✓] 1.3c Translate filt  [✓] 1.4 Human review
  [✓] PG1 Pipeline Gate 1
[▶] Phase 2: Planning (in_progress)
  [✓] 2.1a Verify quality   [✓] 2.1b Translate log   [✓] 2.2a Futures Wheel
  [✓] 2.2b Cross-impact     [✓] 2.2c Bayesian        [✓] 2.2d pSST IC
  [✓] 2.2e Translate impact  [▶] 2.3a Calc priorities [ ] 2.3b pSST scores
  [ ] 2.3c Translate ranks   [ ] 2.5 Human review     [ ] PG2 Pipeline Gate 2
[ ] Phase 3: Implementation (blocked by Phase 2)

Current: 2.3a - Calculating priority scores
Next: 2.3b (Aggregate pSST scores)
```

---

## Workflow State Management

### Initialize Workflow

**STEP 1: Create Workflow State** (기존 로직, 변경 없음)

On startup, create workflow state:

```
{data_root}/logs/workflow-status.json
```

State structure:
```json
{
  "workflow_id": "scan-{date}",
  "start_time": "{ISO8601}",
  "current_phase": 1,
  "current_step": "1.1",
  "status": "in_progress",
  "completed_steps": [],
  "blocked_on": null,
  "errors": [],
  "human_decisions": [],
  "artifacts": {},
  "shared_context_path": "{data_root}/context/shared-context-{date}.json",
  "task_mapping": {},
  "verification_report_path": "{data_root}/logs/verification-report-{date}.json",
  "verification_results": {
    "total_checks": 0,
    "passed": 0,
    "warned": 0,
    "failed": 0,
    "retries_triggered": 0,
    "pipeline_gates_passed": 0,
    "overall_status": "PENDING"
  }
}
```

Load or create this file at the start of each workflow execution.

**STEP 2: Create Task Management Hierarchy** (신규 추가 - 부가 기능)

**Purpose**: Enable user progress monitoring via `Ctrl+T`. This is optional and non-critical.
**Task count**: 49 static tasks + 3 conditional (dynamic) = up to 52 total.

**Instructions**: Execute the following steps in order. If any step fails, log warning and skip remaining Task creation, then continue workflow.

**Create Phase Tasks (3 tasks):**

1. Use TaskCreate tool with parameters:
   - subject: "Phase 1: Research - Collect and filter signals"
   - description: "Scan multiple sources, classify signals using STEEPs framework, filter duplicates using 4-stage cascade"
   - activeForm: "Executing Phase 1 (Research)"
   Store the returned task ID as "phase1_task_id"

2. Use TaskCreate tool with parameters:
   - subject: "Phase 2: Planning - Analyze and structure signals"
   - description: "Verify classifications, analyze impacts, rank priorities, optionally build scenarios"
   - activeForm: "Executing Phase 2 (Planning)"
   Store the returned task ID as "phase2_task_id"

3. Use TaskUpdate tool to set Phase 2 dependency:
   - taskId: phase2_task_id
   - addBlockedBy: [phase1_task_id]

4. Use TaskCreate tool with parameters:
   - subject: "Phase 3: Implementation - Generate and archive report"
   - description: "Update database, generate bilingual report, archive, await final approval"
   - activeForm: "Executing Phase 3 (Implementation)"
   Store the returned task ID as "phase3_task_id"

5. Use TaskUpdate tool to set Phase 3 dependency:
   - taskId: phase3_task_id
   - addBlockedBy: [phase2_task_id]

**Create Phase 1 Sub-Tasks (13 tasks):**

6. Use TaskCreate tool:
   - subject: "1.1a: Load signals database"
   - description: "Load signals/database.json into memory for deduplication baseline"
   - activeForm: "Loading signals DB"
   Store as "task1_1a_id"

7. Use TaskCreate tool:
   - subject: "1.1b: Load archive reports"
   - description: "Load reports/archive/**/*.json for historical context"
   - activeForm: "Loading archives"
   Store as "task1_1b_id"
   Then use TaskUpdate: addBlockedBy: [task1_1a_id]

8. Use TaskCreate tool:
   - subject: "1.1c: Build deduplication indexes"
   - description: "Build URL, title, and entity indexes from loaded data"
   - activeForm: "Building indexes"
   Store as "task1_1c_id"
   Then use TaskUpdate: addBlockedBy: [task1_1b_id]

9. Use TaskCreate tool:
   - subject: "1.1d: Validate configuration files"
   - description: "Verify sources.yaml, domains.yaml, thresholds.yaml are valid and complete"
   - activeForm: "Validating configs"
   Store as "task1_1d_id"
   Then use TaskUpdate: addBlockedBy: [task1_1c_id]

10. Use TaskCreate tool:
    - subject: "1.2a: Run multi-source scanner (Stage A - base)"
    - description: "Execute base-tier source scanners to collect raw signals"
    - activeForm: "Scanning base sources"
    Store as "task1_2a_id"
    Then use TaskUpdate: addBlockedBy: [task1_1d_id]

10b. **Default (skip only if --base-only)** — Use TaskCreate tool:
    - subject: "1.2a-M: Run expansion scanner (Stage B)"
    - description: "Execute expansion-tier source scanners within remaining time budget"
    - activeForm: "Scanning expansion sources"
    Store as "task1_2a_m_id"
    Then use TaskUpdate: addBlockedBy: [task1_2a_id]
    **Note**: Always create this task unless workflow was invoked with --base-only flag.
    If --base-only mode, skip this step entirely.

11. Use TaskCreate tool:
    - subject: "1.2b: Translate raw scan results (KR)"
    - description: "Translate raw scan output titles and summaries to Korean"
    - activeForm: "Translating scan results"
    Store as "task1_2b_id"
    Then use TaskUpdate: addBlockedBy: [task1_2a_m_id]
    (If --base-only mode: addBlockedBy: [task1_2a_id] instead)

12. Use TaskCreate tool:
    - subject: "1.2c: Classify signals (STEEPs)"
    - description: "Classify each signal into STEEPs categories with confidence scores"
    - activeForm: "Classifying signals"
    Store as "task1_2c_id"
    Then use TaskUpdate: addBlockedBy: [task1_2a_m_id]
    (If --base-only mode: addBlockedBy: [task1_2a_id] instead)

13. Use TaskCreate tool:
    - subject: "1.2d: Translate classified signals (KR)"
    - description: "Translate classification labels and rationale to Korean"
    - activeForm: "Translating classifications"
    Store as "task1_2d_id"
    Then use TaskUpdate: addBlockedBy: [task1_2c_id]

14. Use TaskCreate tool:
    - subject: "1.3a: Run 4-stage deduplication cascade"
    - description: "URL → String → Semantic → Entity matching deduplication pipeline"
    - activeForm: "Filtering duplicates"
    Store as "task1_3a_id"
    Then use TaskUpdate: addBlockedBy: [task1_2c_id]

15. Use TaskCreate tool:
    - subject: "1.3b: Generate dedup log"
    - description: "Log all duplicate matches with confidence scores and removal reasons"
    - activeForm: "Generating dedup log"
    Store as "task1_3b_id"
    Then use TaskUpdate: addBlockedBy: [task1_3a_id]

16. Use TaskCreate tool:
    - subject: "1.3c: Translate filtered results (KR)"
    - description: "Translate filtered signal set and dedup summary to Korean"
    - activeForm: "Translating filter results"
    Store as "task1_3c_id"
    Then use TaskUpdate: addBlockedBy: [task1_3a_id]

17. Use TaskCreate tool:
    - subject: "1.4: Human review of filtering"
    - description: "Review duplicate removal results if AI confidence < 0.9"
    - activeForm: "Awaiting human review"
    - metadata: {"checkpoint": true, "required": false}
    Store as "task1_4_id"
    Then use TaskUpdate: addBlockedBy: [task1_3a_id]

18. Use TaskCreate tool:
    - subject: "PG1: Pipeline Gate 1 - Phase 1→2 verification"
    - description: "Verify all Phase 1 outputs exist, are valid JSON, and pass quality checks before proceeding to Phase 2"
    - activeForm: "Verifying Phase 1 outputs"
    Store as "task_pg1_id"
    Then use TaskUpdate: addBlockedBy: [task1_4_id]

NOTE: Step 1.5 (Expert panel validation) is conditional - create only when >50 signals detected (see Step 1.5 instructions)

**Create Phase 2 Sub-Tasks (12 tasks):**

19. Use TaskCreate tool:
    - subject: "2.1a: Verify classification quality"
    - description: "Verify STEEPs categories, check confidence scores, correct invalid classifications"
    - activeForm: "Verifying classifications"
    Store as "task2_1a_id"
    Then use TaskUpdate: addBlockedBy: [phase1_task_id]

20. Use TaskCreate tool:
    - subject: "2.1b: Translate quality log (KR)"
    - description: "Translate classification quality verification log to Korean"
    - activeForm: "Translating quality log"
    Store as "task2_1b_id"
    Then use TaskUpdate: addBlockedBy: [task2_1a_id]

21. Use TaskCreate tool:
    - subject: "2.2a: Identify impacts (Futures Wheel)"
    - description: "Apply Futures Wheel method to identify direct and indirect impacts of each signal"
    - activeForm: "Analyzing impacts"
    Store as "task2_2a_id"
    Then use TaskUpdate: addBlockedBy: [task2_1a_id]

22. Use TaskCreate tool:
    - subject: "2.2b: Build cross-impact matrix"
    - description: "Construct signal interaction matrix for cross-influence analysis"
    - activeForm: "Building cross-impact matrix"
    Store as "task2_2b_id"
    Then use TaskUpdate: addBlockedBy: [task2_2a_id]

23. Use TaskCreate tool:
    - subject: "2.2c: Bayesian network inference"
    - description: "Calculate conditional probabilities and scenario likelihoods via Bayesian network"
    - activeForm: "Running Bayesian inference"
    Store as "task2_2c_id"
    Then use TaskUpdate: addBlockedBy: [task2_2b_id]

24. Use TaskCreate tool:
    - subject: "2.2d: Calculate pSST IC dimension"
    - description: "Compute pSST Information Credibility dimension scores for each signal"
    - activeForm: "Calculating pSST IC"
    Store as "task2_2d_id"
    Then use TaskUpdate: addBlockedBy: [task2_2a_id]

25. Use TaskCreate tool:
    - subject: "2.2e: Translate impact analysis (KR)"
    - description: "Translate impact analysis results, cross-impact matrix, and Bayesian output to Korean"
    - activeForm: "Translating impact analysis"
    Store as "task2_2e_id"
    Then use TaskUpdate: addBlockedBy: [task2_2c_id]

26. Use TaskCreate tool:
    - subject: "2.3a: Calculate priority scores"
    - description: "Weighted ranking: Impact 40%, Probability 30%, Urgency 20%, Novelty 10%"
    - activeForm: "Calculating priorities"
    Store as "task2_3a_id"
    Then use TaskUpdate: addBlockedBy: [task2_2c_id]

27. Use TaskCreate tool:
    - subject: "2.3b: Aggregate pSST final scores"
    - description: "Combine IC, RT, and other pSST dimensions into final trust scores"
    - activeForm: "Aggregating pSST scores"
    Store as "task2_3b_id"
    Then use TaskUpdate: addBlockedBy: [task2_3a_id]

28. Use TaskCreate tool:
    - subject: "2.3c: Translate priority rankings (KR)"
    - description: "Translate priority ranking results and pSST scores to Korean"
    - activeForm: "Translating rankings"
    Store as "task2_3c_id"
    Then use TaskUpdate: addBlockedBy: [task2_3a_id]

NOTE: Step 2.4 (Scenario Building) is conditional - create only when complexity > 0.15

29. Use TaskCreate tool:
    - subject: "2.5: Human review of analysis (required)"
    - description: "Review STEEPs classifications, priority rankings, pSST scores, approve or request changes"
    - activeForm: "Awaiting human review"
    - metadata: {"checkpoint": true, "required": true}
    Store as "task2_5_id"
    Then use TaskUpdate: addBlockedBy: [task2_3b_id]

30. Use TaskCreate tool:
    - subject: "PG2: Pipeline Gate 2 - Phase 2→3 verification"
    - description: "Verify all Phase 2 outputs exist, are valid, and analysis quality meets thresholds"
    - activeForm: "Verifying Phase 2 outputs"
    Store as "task_pg2_id"
    Then use TaskUpdate: addBlockedBy: [task2_5_id]

**Create Phase 3 Sub-Tasks (20 tasks):**

31. Use TaskCreate tool:
    - subject: "3.1a: Create database backup"
    - description: "Create timestamped backup of signals/database.json before modification"
    - activeForm: "Creating DB backup"
    - metadata: {"critical": true}
    Store as "task3_1a_id"
    Then use TaskUpdate: addBlockedBy: [phase2_task_id]

32. Use TaskCreate tool:
    - subject: "3.1b: Update signals database"
    - description: "Atomic update to database.json with new signals from this scan"
    - activeForm: "Updating database"
    - metadata: {"critical": true}
    Store as "task3_1b_id"
    Then use TaskUpdate: addBlockedBy: [task3_1a_id]

33. Use TaskCreate tool:
    - subject: "3.1c: Verify database integrity"
    - description: "Verify updated database.json is valid JSON, signal count matches, no data corruption"
    - activeForm: "Verifying DB integrity"
    Store as "task3_1c_id"
    Then use TaskUpdate: addBlockedBy: [task3_1b_id]

34. Use TaskCreate tool:
    - subject: "3.2a: Generate EN report"
    - description: "Generate English environmental scanning report in markdown format"
    - activeForm: "Generating EN report"
    Store as "task3_2a_id"
    Then use TaskUpdate: addBlockedBy: [task3_1c_id]

35. Use TaskCreate tool:
    - subject: "3.2b: Quality check EN report"
    - description: "Verify report structure, signal coverage, citation accuracy"
    - activeForm: "Checking report quality"
    Store as "task3_2b_id"
    Then use TaskUpdate: addBlockedBy: [task3_2a_id]

36. Use TaskCreate tool:
    - subject: "3.2c: Translate report to KR"
    - description: "Translate EN report to Korean with back-translation verification"
    - activeForm: "Translating report"
    Store as "task3_2c_id"
    Then use TaskUpdate: addBlockedBy: [task3_2b_id]

37. Use TaskCreate tool:
    - subject: "3.2d: Verify KR translation quality"
    - description: "Back-translate KR→EN, compare semantic similarity, verify key terms"
    - activeForm: "Verifying KR translation"
    Store as "task3_2d_id"
    Then use TaskUpdate: addBlockedBy: [task3_2c_id]

38. Use TaskCreate tool:
    - subject: "3.2e: Generate pSST trust analysis"
    - description: "Generate pSST trust analysis section for inclusion in final report"
    - activeForm: "Generating trust analysis"
    Store as "task3_2e_id"
    Then use TaskUpdate: addBlockedBy: [task3_2a_id]

39. Use TaskCreate tool:
    - subject: "3.3a: Archive EN+KR reports"
    - description: "Copy EN and KR reports to reports/archive/{year}/{month}/ directory"
    - activeForm: "Archiving reports"
    Store as "task3_3a_id"
    Then use TaskUpdate: addBlockedBy: [task3_2d_id]

40. Use TaskCreate tool:
    - subject: "3.3b: Create signal snapshot"
    - description: "Create timestamped snapshot of signals/database.json in signals/snapshots/"
    - activeForm: "Creating snapshot"
    Store as "task3_3b_id"
    Then use TaskUpdate: addBlockedBy: [task3_3a_id]

41. Use TaskCreate tool:
    - subject: "3.3c: Send notifications"
    - description: "Notify stakeholders that new environmental scan report is available"
    - activeForm: "Sending notifications"
    Store as "task3_3c_id"
    Then use TaskUpdate: addBlockedBy: [task3_3a_id]

42. Use TaskCreate tool:
    - subject: "3.3d: Translate daily summary (KR)"
    - description: "Translate daily summary log to Korean"
    - activeForm: "Translating summary"
    Store as "task3_3d_id"
    Then use TaskUpdate: addBlockedBy: [task3_3a_id]

43. Use TaskCreate tool:
    - subject: "3.4: Final approval (required)"
    - description: "Present EN+KR report to user, await /approve or /revision command"
    - activeForm: "Awaiting final approval"
    - metadata: {"checkpoint": true, "required": true}
    Store as "task3_4_id"
    Then use TaskUpdate: addBlockedBy: [task3_3a_id]

44. Use TaskCreate tool:
    - subject: "3.5a: Generate quality metrics (EN)"
    - description: "Calculate execution times, quality scores, compare to targets in English"
    - activeForm: "Generating metrics"
    Store as "task3_5a_id"
    Then use TaskUpdate: addBlockedBy: [task3_4_id]

45. Use TaskCreate tool:
    - subject: "3.5b: Translate quality metrics (KR)"
    - description: "Translate quality metrics report to Korean"
    - activeForm: "Translating metrics"
    Store as "task3_5b_id"
    Then use TaskUpdate: addBlockedBy: [task3_5a_id]

46. Use TaskCreate tool:
    - subject: "3.5c: Generate VEV verification summary"
    - description: "Compile VEV protocol verification results into final summary"
    - activeForm: "Generating VEV summary"
    Store as "task3_5c_id"
    Then use TaskUpdate: addBlockedBy: [task3_5a_id]

47. Use TaskCreate tool:
    - subject: "3.6a: Analyze performance metrics"
    - description: "Analyze workflow execution performance, identify bottlenecks and improvement opportunities"
    - activeForm: "Analyzing performance"
    Store as "task3_6a_id"
    Then use TaskUpdate: addBlockedBy: [task3_5a_id]

48. Use TaskCreate tool:
    - subject: "3.6b: Propose improvements"
    - description: "Generate improvement proposals based on performance analysis"
    - activeForm: "Proposing improvements"
    Store as "task3_6b_id"
    Then use TaskUpdate: addBlockedBy: [task3_6a_id]

49. Use TaskCreate tool:
    - subject: "3.6c: Execute approved MINOR changes"
    - description: "Apply user-approved minor workflow improvements (config tweaks, threshold adjustments only)"
    - activeForm: "Executing minor changes"
    Store as "task3_6c_id"
    Then use TaskUpdate: addBlockedBy: [task3_6b_id]

50. Use TaskCreate tool:
    - subject: "PG3: Pipeline Gate 3 - Final verification"
    - description: "Final verification of all workflow outputs, report integrity, and database consistency"
    - activeForm: "Verifying final outputs"
    Store as "task_pg3_id"
    Then use TaskUpdate: addBlockedBy: [task3_6c_id]

**Store Task IDs in workflow-status.json:**

51. Read current workflow-status.json file
52. Add or update the task_mapping field with all 48 task IDs:
    ```json
    "task_mapping": {
      "phase1": phase1_task_id,
      "phase2": phase2_task_id,
      "phase3": phase3_task_id,
      "1.1a": task1_1a_id,
      "1.1b": task1_1b_id,
      "1.1c": task1_1c_id,
      "1.1d": task1_1d_id,
      "1.2a": task1_2a_id,
      "1.2b": task1_2b_id,
      "1.2c": task1_2c_id,
      "1.2d": task1_2d_id,
      "1.3a": task1_3a_id,
      "1.3b": task1_3b_id,
      "1.3c": task1_3c_id,
      "1.4": task1_4_id,
      "PG1": task_pg1_id,
      "2.1a": task2_1a_id,
      "2.1b": task2_1b_id,
      "2.2a": task2_2a_id,
      "2.2b": task2_2b_id,
      "2.2c": task2_2c_id,
      "2.2d": task2_2d_id,
      "2.2e": task2_2e_id,
      "2.3a": task2_3a_id,
      "2.3b": task2_3b_id,
      "2.3c": task2_3c_id,
      "2.5": task2_5_id,
      "PG2": task_pg2_id,
      "3.1a": task3_1a_id,
      "3.1b": task3_1b_id,
      "3.1c": task3_1c_id,
      "3.2a": task3_2a_id,
      "3.2b": task3_2b_id,
      "3.2c": task3_2c_id,
      "3.2d": task3_2d_id,
      "3.2e": task3_2e_id,
      "3.3a": task3_3a_id,
      "3.3b": task3_3b_id,
      "3.3c": task3_3c_id,
      "3.3d": task3_3d_id,
      "3.4": task3_4_id,
      "3.5a": task3_5a_id,
      "3.5b": task3_5b_id,
      "3.5c": task3_5c_id,
      "3.6a": task3_6a_id,
      "3.6b": task3_6b_id,
      "3.6c": task3_6c_id,
      "PG3": task_pg3_id
    }
    ```
    NOTE: Keys "1.5", "2.4a", "2.4b" will be added dynamically if those conditional steps are activated

53. Write the updated workflow-status.json back to file

**Conditional Tasks (created dynamically, not at startup):**

- **1.5** (Expert panel validation): Create when signal_count > 50
  - subject: "1.5: Expert panel validation (RT-AID)"
  - activeForm: "Expert validation in progress"
  - addBlockedBy: [task1_4_id]

- **2.4a** (Build plausible scenarios): Create when complexity > 0.15
  - subject: "2.4a: Build plausible scenarios"
  - activeForm: "Building scenarios"
  - addBlockedBy: [task2_3b_id]

- **2.4b** (Translate scenarios): Create when 2.4a is activated
  - subject: "2.4b: Translate scenarios (KR)"
  - activeForm: "Translating scenarios"
  - addBlockedBy: [task2_4a_id]

**Error Handling:**
- If any TaskCreate or TaskUpdate call fails, log warning message
- Set task_mapping to empty object {} in workflow-status.json
- Continue workflow without Task system (user will not have Ctrl+T visibility)
- Task system is for user visibility only - its failure must NEVER halt the workflow

**IMPORTANT**: Task system is a non-critical feature. Workflow must proceed even if all Task operations fail.

---

**STEP 3: Initialize Verification Report** (NEW in v2.2.0)

After Task hierarchy creation, initialize the verification system:

1. Create file: `{data_root}/logs/verification-report-{date}.json`
2. Write initial structure:
   ```json
   {
     "workflow_id": "scan-{date}",
     "vev_protocol_version": "2.2.0",
     "verification_summary": {
       "total_checks": 0, "passed": 0, "warned": 0, "failed": 0,
       "retries_triggered": 0, "pipeline_gates_passed": 0, "overall_status": "PENDING"
     },
     "steps": {},
     "pipeline_gates": {},
     "translation_verification": [],
     "generated_at": "{ISO8601}"
   }
   ```
3. Update workflow-status.json: set `"verification_report_path"` to the created file path
4. If file creation fails: Log warning, set `verification_report_path` to null, continue workflow

---

## Phase 1: Research (Information Collection)

Execute steps **sequentially**:

### Step 1.1: Load Archive

#### ① PRE-VERIFY (선행 조건 확인)

Before invoking the worker agent, verify preconditions:

```yaml
Pre-Verification Checks:
  - check: "config/sources.yaml exists and readable"
    on_fail: HALT (cannot proceed without source config)
  - check: "config/domains.yaml exists with 6 STEEPs categories"
    on_fail: HALT (classification requires domain definitions)
  - check: "signals/database.json exists OR signals/snapshots/ has at least 1 file OR this is first run"
    on_fail: WARN (first run acceptable - create empty indexes)
```

**Action**: Read and verify each file. If Pre-Verify fails on critical checks, do NOT invoke the worker. Log error and halt.

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE EXECUTION** (Optional, non-critical):

Execute these steps before invoking the worker agent:
1. Read workflow-status.json file
2. Check if task_mapping field exists and contains key "1.1a"
3. If exists: Use TaskUpdate tool with parameters:
   - taskId: (value from task_mapping["1.1a"])
   - status: "in_progress"
4. If task_mapping is empty or TaskUpdate fails: Continue without error

**Invoke**: Task tool with `@archive-loader` worker agent

```yaml
Agent: archive-loader
Description: Load historical signals database
Input files:
  - reports/archive/**/*.json
  - signals/database.json
Output:
  - context/previous-signals.json
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "context/previous-signals.json exists"
    on_fail: RETRY
  - check: "File is valid JSON"
    on_fail: RETRY

Layer_2_Functional:
  - check: "Contains 'url_index' field (object type)"
    on_fail: RETRY
  - check: "Contains 'title_index' field (object type)"
    on_fail: RETRY
  - check: "Contains 'entity_index' field (object type)"
    on_fail: RETRY

Layer_3_Quality:
  - check: "At least 1 signal loaded (or empty on confirmed first run)"
    on_fail: WARN (acceptable for first run)
  - check: "Index entry count matches signals/database.json signal count (±5% tolerance)"
    on_fail: WARN
```

#### ④ RETRY (실패 시)

If Layer 1 or Layer 2 fails:
1. Re-invoke `@archive-loader` (attempt 2, delay 2s)
2. Re-run POST-VERIFY
3. If still fails: Re-invoke (attempt 3, delay 4s)
4. If 3 attempts (1 original + 2 retries) exhausted: Log error E1000 and HALT_workflow

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "1.1"
step_name: "Archive Loading"
agent: "@archive-loader"
additional_data:
  signals_loaded: {count}
  archive_reports_loaded: {count}
  index_entries_created: {count}
```

**TASK UPDATE - AFTER COMPLETION** (Optional, non-critical):

Execute these steps after successful verification:
1. Read workflow-status.json file
2. Check if task_mapping field exists
3. If exists: Mark all Step 1.1 sub-tasks as completed:
   - TaskUpdate(taskId: task_mapping["1.1a"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.1b"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.1c"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.1d"], status: "completed")
4. If task_mapping is empty or any TaskUpdate fails: Continue without error

**Error Handling**:
- If archive files don't exist: Create empty indexes and continue
- If database.json corrupt: Restore from latest snapshot in signals/snapshots/
- If all retries fail: Log error E1000 and halt workflow

### Step 1.2: Multi-Source Scanning & Classification ✅

#### Marathon Mode (Default) (v3.1.0)

Step 1.2 uses **Marathon Mode** by default — scanning both base-tier and expansion-tier sources for maximum signal coverage.

**Deactivation**: Marathon mode is skipped only when the workflow is invoked with `--base-only` flag.

**Behavior**:
- **Default (marathon)**: `tier: "base"` sources scanned first (Stage A), then `tier: "expansion"` sources scanned with remaining time budget (Stage B)
- **Base-only mode** (`--base-only`): Only `tier: "base"` sources are scanned, Stage B is skipped entirely

**Philosophy**: Marathon mode extends the scanning scope while preserving all quality gates. The 30-minute budget is a **ceiling** (upper bound) — scanning ends when all expansion sources are scanned or time budget is exhausted, whichever comes first. No artificial time padding.

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "context/previous-signals.json exists (output of Step 1.1)"
    on_fail: HALT (Step 1.1 must complete first)
  - check: "config/sources.yaml has at least 1 source with enabled: true"
    on_fail: HALT (no sources to scan)
  - check: "config/domains.yaml contains all 6 STEEPs categories (S, T, E, E, P, s)"
    on_fail: HALT (classification requires complete domain definitions)
  - check: "Step 1.1 recorded as VERIFIED in verification-report"
    on_fail: HALT (previous step must be verified)

  # Marathon Mode Pre-Checks (default; skipped only when --base-only is active)
  marathon_mode_checks:
    - check: "config/thresholds.yaml contains marathon_mode section"
      on_fail: WARN and fall back to base-only mode
    - check: "config/sources.yaml has at least 1 source with tier: expansion and enabled: true"
      on_fail: WARN (no expansion sources — runs as base-only mode)
```

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE EXECUTION** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping["1.2a"]
2. If exists: Use TaskUpdate tool (taskId from step 1, status: "in_progress")
3. If fails: Continue without error

**Status**: **arXiv Permanently Integrated + Direct Classification** (2026-01-30)

**Implementation**: Two-phase process - Collection then Classification

#### Stage A: Base Source Collection (Python Script)

**Invoke**: Execute multi-source scanner script via Bash tool (base tier only)

```bash
cd env-scanning && python3 scripts/run_multi_source_scan.py --days-back 7 --tier base
```

**Description**: Scan base-tier configured sources using multi-source architecture. The `--tier base` flag filters sources to only those with `tier: "base"` (or no tier field, for backward compatibility). Stage A always runs regardless of mode.

**Input files**:
  - config/sources.yaml (filter: tier == "base" AND enabled == true)
  - config/domains.yaml (6 STEEPs categories)
  - context/shared-context-{date}.json (create empty if not exists)

**Output**:
  - raw/daily-scan-{date}.json
    ```json
    {
      "scan_metadata": {
        "sources_scanned": 1,
        "total_items": 100-150,
        "execution_time": <30s
      },
      "items": [...]  # With preliminary_category, all items have source.tier: "base"
    }
    ```

**Time Tracking**: Record `stage_a_elapsed_seconds` in workflow-status.json for marathon time budget calculation.

---

#### Stage B: Expansion Source Collection (Default)

> **SKIP** this entire stage only if `--base-only` flag is active. Otherwise, always execute.

**Skip condition**: `workflow_options.base_only == true`

**Time Budget Calculation**:
```python
total_budget = thresholds.marathon_mode.total_budget_minutes * 60  # 1800 seconds
stage_b_budget = max(
    total_budget - stage_a_elapsed_seconds,
    thresholds.marathon_mode.stage_b_min_budget_minutes * 60  # minimum 300 seconds
)
```

**Source Selection and Prioritization**:

1. Load all sources from `config/sources.yaml` where `tier: "expansion"` AND `enabled: true`
2. Prioritize according to `marathon_mode.expansion_source_priority` setting:

```yaml
type_diversity (default):
  # Round-robin across source types to maximize STEEPs coverage
  # Example: academic → policy → blog → academic → policy → ...
  # Within each type, higher reliability sources first
  sort_order:
    1. group_by: source.type
    2. within_group: sort_by reliability DESC
    3. interleave: round-robin across groups

reliability:
  # Simply sort by reliability rating
  sort_order: sort_by reliability DESC, then by name ASC

steeps_coverage:
  # Prioritize sources whose steeps_focus covers categories
  # underrepresented in Stage A results
  sort_order:
    1. analyze: Stage A category distribution
    2. identify: underrepresented STEEPs categories
    3. prioritize: sources with steeps_focus matching gaps
```

**Invoke**: Execute multi-source scanner script via Bash tool (expansion tier)

```bash
cd env-scanning && python3 scripts/run_multi_source_scan.py --days-back 7 --tier expansion --time-budget {stage_b_budget}
```

**Description**: Scan expansion-tier sources within the remaining time budget. The script scans sources in priority order and stops when time budget is exhausted or all expansion sources are scanned.

**Input files**:
  - config/sources.yaml (filter: tier == "expansion" AND enabled == true)
  - config/domains.yaml (6 STEEPs categories)
  - Stage A output for STEEPs coverage analysis (if priority = steeps_coverage)

**Output**:
  - raw/daily-scan-{date}-expansion.json
    ```json
    {
      "scan_metadata": {
        "sources_scanned": 12,
        "total_items": 200-400,
        "execution_time": 1200,
        "time_budget": 1500,
        "budget_exhausted": false,
        "sources_skipped": ["source1", "source2"],
        "tier": "expansion"
      },
      "items": [...]  # All items have source.tier: "expansion"
    }
    ```

**Per-source time tracking**: Each expansion source has individual timing. If a source takes longer than its configured `timeout`, skip it and move to the next source.

---

#### Merge: Combine Stage A + Stage B Results

> **SKIP** if `--base-only` mode is active (no Stage B output to merge).

**Process**:
1. Read `raw/daily-scan-{date}.json` (Stage A results)
2. Read `raw/daily-scan-{date}-expansion.json` (Stage B results)
3. Merge items arrays: `merged_items = stage_a.items + stage_b.items`
4. Update scan_metadata:
   ```json
   {
     "scan_metadata": {
       "sources_scanned": stage_a.sources + stage_b.sources,
       "total_items": len(merged_items),
       "execution_time": stage_a.time + stage_b.time,
       "marathon_mode": true,
       "stage_a_items": stage_a.total_items,
       "stage_b_items": stage_b.total_items,
       "expansion_sources_scanned": stage_b.sources_scanned,
       "expansion_sources_skipped": stage_b.sources_skipped
     },
     "items": merged_items
   }
   ```
5. Write merged result back to `raw/daily-scan-{date}.json` (overwrite)
6. Keep `raw/daily-scan-{date}-expansion.json` as backup

**Important**: After merge, the downstream pipeline (deduplication, classification, analysis, reporting) processes ALL signals identically. Expansion signals are not treated differently — they go through the same 4-stage dedup cascade, same VEV verification, same pSST scoring. The `source.tier: "expansion"` tag is preserved for SIE tracking in Step 3.6.

---

#### Phase B: Direct Classification (Claude Code)

**Action**: Immediately after collection, read and classify all collected papers

**Process**:
1. Read the collected signals file: `raw/daily-scan-{date}.json`
2. For each signal in items array:
   - Analyze title and abstract
   - Classify into STEEPs category (S, T, E, E, P, s)
   - Assign confidence score (0.0-1.0)
   - Provide reasoning
3. Update each signal with:
   ```json
   {
     "final_category": "S|T|E|E|P|s",
     "classification_confidence": 0.85,
     "classification_reasoning": "brief explanation",
     "classification_method": "claude_code_direct",
     "classification_cost": 0.0
   }
   ```
4. Save updated file to: `structured/classified-signals-{date}.json`

**Classification Guidelines**:
- **S (Social)**: Demographics, culture, society, human behavior
- **T (Technological)**: AI, robotics, innovation, computing, engineering
- **E (Economic)**: Markets, finance, trade, business, economy
- **E (Environmental)**: Climate, ecology, energy, sustainability, nature
- **P (Political)**: Policy, regulation, governance, geopolitics, law
- **s (spiritual)**: Ethics, values, meaning, philosophy, consciousness

**Quality Targets**:
- Accuracy: >90% (based on Claude's LLM capabilities)
- Speed: ~1 second per signal
- Cost: $0 (using Claude Code subscription)

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "raw/daily-scan-{date}.json exists"
    on_fail: RETRY
  - check: "structured/classified-signals-{date}.json exists"
    on_fail: RETRY
  - check: "Both files are valid JSON"
    on_fail: RETRY
  # Default (marathon) mode only — skip checks if --base-only:
  - check: "raw/daily-scan-{date}-expansion.json exists (unless --base-only)"
    on_fail: WARN (Stage B may have produced no results — acceptable)

Layer_2_Functional:
  - check: "raw scan items array is non-empty (at least 1 signal collected)"
    on_fail: RETRY (unless no signals is confirmed valid state)
  - check: "All signals in classified file have final_category field"
    on_fail: RETRY
  - check: "All final_category values are one of: S, T, E, E, P, s"
    on_fail: RETRY
  - check: "All confidence scores in range 0.0-1.0"
    on_fail: RETRY
  - check: "All signals have classification_reasoning (non-empty string)"
    on_fail: RETRY
  - check: "Total signals in classified file == total items in raw scan"
    on_fail: RETRY (count mismatch indicates lost signals)
  # Default (marathon) mode only — skip checks if --base-only:
  - check: "All expansion signals have source.tier == 'expansion' tag"
    on_fail: WARN (tagging issue — non-critical)
  - check: "Stage A + Stage B item counts match merged total"
    on_fail: RETRY (merge error)

Layer_3_Quality:
  - check: "Average classification_confidence > 0.85"
    on_fail: WARN (below target but functional)
  - check: "At least 3 of 6 STEEPs categories represented"
    on_fail: WARN (potential classification bias)
  - check: "No single category exceeds 60% of total signals"
    on_fail: WARN (potential over-classification)
  - check: "scan_metadata.sources_scanned >= 1"
    on_fail: WARN
  # Default (marathon) mode only — skip checks if --base-only:
  - check: "Expansion sources contributed at least 1 signal (unless --base-only)"
    on_fail: WARN (expansion sources may have low yield — acceptable but notable)
  - check: "Total execution time <= marathon_mode.total_budget_minutes"
    on_fail: WARN (budget exceeded — log for SIE analysis)
```

#### ④ RETRY (실패 시)

If Layer 1 or Layer 2 fails:
1. Identify failing sub-operation (Collection or Classification)
2. Re-execute only the failing phase (Phase A or Phase B)
3. Re-run POST-VERIFY
4. Max 2 retries with exponential backoff (2s, 4s)
5. If exhausted: Log error E2000, HALT workflow

If Layer 3 fails:
- Log warning with details (e.g., "avg confidence 0.82 < target 0.85")
- Ask user: "품질 목표 미달 ({detail}). 계속 진행하시겠습니까?"
- If user approves: Continue with WARN status
- If user requests retry: Re-execute classification phase (max 1 retry)

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "1.2"
step_name: "Multi-Source Scanning & Classification"
agent: "@multi-source-scanner"
additional_data:
  sources_scanned: {count}
  items_collected: {count}
  items_classified: {count}
  # Marathon mode fields (present by default; all zeros if --base-only):
  marathon_mode: true|false  # true by default, false only with --base-only
  stage_a_sources: {count}
  stage_a_items: {count}
  stage_a_elapsed_seconds: {seconds}
  stage_b_sources: {count}           # 0 if --base-only
  stage_b_items: {count}             # 0 if --base-only
  stage_b_elapsed_seconds: {seconds} # 0 if --base-only
  stage_b_budget_seconds: {seconds}  # allocated budget
  stage_b_budget_exhausted: true|false
  expansion_sources_skipped: [...]   # sources skipped due to timeout/budget
```

**Task Management**:
- Create subtask: "Scan and classify signals from multiple sources"
- Track: sources_scanned, items_collected, items_classified, execution_time
- Update shared context with classification results

**Error Handling**:
- **Critical source (arXiv) fails**: Halt workflow (E2000)
- **Non-critical source fails**: Log warning, continue with others
- **All sources fail**: Log error E2000 and halt
- **No signals found**: Generate warning report, continue (valid state)
- **Classification fails for signal**: Keep preliminary_category, mark low confidence
- **Retry (VEV)**: Layer 1/2 failure → max 2 retries. On exhaustion → HALT_and_ask_user (non-critical sources may be skipped)

---

### Step 1.2b & 1.2d: Translation (Automatic)

**CRITICAL**: After Step 1.2 completes, **immediately invoke translation** for both outputs.

**Invoke**: Task tool with `@translation-agent` worker agent (2 invocations)

**Translation 1 - Scan Results**:
```yaml
Agent: translation-agent
Description: Translate daily scan results to Korean
Input:
  source_file: raw/daily-scan-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.90
  enable_back_translation: false  # Non-critical, speed priority
Output:
  raw/daily-scan-{date}-ko.json
Verification:
  - KR file exists
  - JSON schema matches EN file
  - STEEPs terms preserved exactly
  - All numeric values unchanged
```

**Translation 2 - Classified Signals**:
```yaml
Agent: translation-agent
Description: Translate classified signals to Korean
Input:
  source_file: structured/classified-signals-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.90
  enable_back_translation: false
Output:
  structured/classified-signals-{date}-ko.json
Verification:
  - KR file exists
  - All final_category values unchanged (S, T, E, E, P, s)
  - Classification_reasoning translated naturally
  - Confidence scores identical to EN
```

**Task Management**:
- Create 2 subtasks: "Translate scan results" and "Translate classifications"
- Mark in_progress before translation
- Mark completed after verification
- Update shared context translation_status

**Update Shared Context**:
```json
{
  "translation_status": {
    "translations_completed": [
      {
        "step": "step_1.2b",
        "source_file": "raw/daily-scan-{date}.json",
        "target_file": "raw/daily-scan-{date}-ko.json",
        "translated_at": "{ISO8601}",
        "quality_status": "PASS"
      },
      {
        "step": "step_1.2d",
        "source_file": "structured/classified-signals-{date}.json",
        "target_file": "structured/classified-signals-{date}-ko.json",
        "translated_at": "{ISO8601}",
        "quality_status": "PASS"
      }
    ]
  }
}
```

**Error Handling**:
- If translation fails: Log warning E9000, continue with EN-only
- Translation is **non-critical** - never halt workflow
- Failed translations logged but don't block Step 1.3

**TASK UPDATE - AFTER COMPLETION** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping
2. If exists: Mark all Step 1.2 sub-tasks as completed:
   - TaskUpdate(taskId: task_mapping["1.2a"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.2b"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.2c"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.2d"], status: "completed")
3. If fails: Continue without error

---

### Step 1.3: Deduplication Filtering

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "raw/daily-scan-{date}.json exists with at least 1 item"
    on_fail: HALT (nothing to deduplicate)
  - check: "context/previous-signals.json exists (output of Step 1.1)"
    on_fail: HALT (no baseline for deduplication)
  - check: "config/thresholds.yaml exists with stage_1 through stage_4 thresholds"
    on_fail: HALT (deduplication requires threshold configuration)
  - check: "Step 1.2 recorded as VERIFIED in verification-report"
    on_fail: HALT (previous step must be verified)
```

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE EXECUTION** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping["1.3a"]
2. If exists: Use TaskUpdate tool (taskId from step 1, status: "in_progress")
3. If fails: Continue without error

**Invoke**: Task tool with `@deduplication-filter` worker agent

```yaml
Agent: deduplication-filter
Description: Filter duplicate signals using 4-stage cascade
Input files:
  - raw/daily-scan-{date}.json
  - context/previous-signals.json
  - context/shared-context-{date}.json
Output:
  - filtered/new-signals-{date}.json
  - logs/duplicates-removed-{date}.log
  - context/shared-context-{date}.json (updated with dedup analysis)
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "filtered/new-signals-{date}.json exists"
    on_fail: RETRY
  - check: "logs/duplicates-removed-{date}.log exists"
    on_fail: RETRY
  - check: "Filtered file is valid JSON with filter_metadata and new_signals fields"
    on_fail: RETRY

Layer_2_Functional:
  - check: "filter_metadata.total_raw + filter_metadata.total_duplicates accounting is correct"
    formula: "total_raw == total_duplicates + total_new"
    on_fail: RETRY (accounting error)
  - check: "filter_rate in range [0.0, 1.0]"
    on_fail: RETRY
  - check: "stage_breakdown sum == total_duplicates"
    formula: "stage_1_url + stage_2_string + stage_3_semantic + stage_4_entity == total_duplicates"
    on_fail: RETRY (stage accounting mismatch)
  - check: "Each signal in new_signals has dedup_confidence field"
    on_fail: RETRY
  - check: "Log file contains at least 1 entry per removed duplicate"
    on_fail: RETRY
  - check: "No signal ID appears in both new_signals and removed list"
    on_fail: RETRY (critical: signal cannot be both new and duplicate)

Layer_3_Quality:
  - check: "Average dedup_confidence > 0.8"
    on_fail: WARN (flag for human review in Step 1.4)
  - check: "filter_rate in range [0.30, 0.90]"
    on_fail: WARN (unusual filter rate - may indicate source or threshold issue)
  - check: "Each stage processed at least 1 item (no stage was bypassed)"
    on_fail: WARN (stage may be misconfigured)
```

**Calculate AI Confidence**:
```
avg_confidence = average of all signal.dedup_confidence scores
```

#### ④ RETRY (실패 시)

If Layer 1 or Layer 2 fails:
1. Re-invoke `@deduplication-filter` (attempt 2, delay 2s)
2. Re-run POST-VERIFY
3. If still fails: attempt 3 (delay 4s)
4. If exhausted: Log error E3000, ask user for intervention

If Layer 3 fails:
- Log warning with details
- If avg_confidence < 0.7: Flag for mandatory human review in Step 1.4

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "1.3"
step_name: "Deduplication Filtering"
agent: "@deduplication-filter"
additional_data:
  precision: {value}
  recall: {value}
  f1_score: {value}
  duplicates_removed: {count}
```

**Task Management**:
- Create subtask: "Filter duplicate signals"
- Track quality metrics: precision, recall, F1 score

**Error Handling**:
- If filtering fails: Log error E3000, retry once
- If confidence < 0.7: Flag for human review in Step 1.4

**TASK UPDATE - AFTER COMPLETION** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping
2. If exists: Mark all Step 1.3 sub-tasks as completed:
   - TaskUpdate(taskId: task_mapping["1.3a"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.3b"], status: "completed")
   - TaskUpdate(taskId: task_mapping["1.3c"], status: "completed")
3. If fails: Continue without error

---

### Step 1.3b: Translation (Automatic)

**CRITICAL**: After Step 1.3 completes, **immediately invoke translation** for dedup outputs.

**Invoke**: Task tool with `@translation-agent` worker agent (2 invocations)

**Translation 1 - Filtered Signals**:
```yaml
Agent: translation-agent
Input:
  source_file: filtered/new-signals-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.90
  enable_back_translation: false
Output:
  filtered/new-signals-{date}-ko.json
Verification:
  - KR file exists
  - Dedup_confidence scores identical
  - Signal IDs unchanged
```

**Translation 2 - Duplicate Log**:
```yaml
Agent: translation-agent
Input:
  source_file: logs/duplicates-removed-{date}.log
  source_format: log
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.85
  enable_back_translation: false
Output:
  logs/duplicates-removed-{date}-ko.log
Verification:
  - KR file exists
  - Signal IDs preserved
  - Timestamps unchanged
```

**Task Management**:
- Create subtask: "Translate dedup results"
- Update shared context translation_status

**Error Handling**: Non-critical, continue if fails

---

### Step 1.4: Human Review of Filtering (Optional)

**Type**: Human checkpoint (non-blocking)

**Condition**: Execute only if `avg_confidence < 0.9`

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "filtered/new-signals-{date}.json exists"
    on_fail: HALT (nothing to review)
  - check: "logs/duplicates-removed-{date}.log exists"
    on_fail: WARN (review possible without log, but limited)
  - check: "Step 1.3 recorded as VERIFIED in verification-report"
    on_fail: HALT
```

If `avg_confidence >= 0.9`: Record final_status="SKIPPED" (high confidence, no review needed).

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE USER REVIEW** (Optional, enables Ctrl+T visibility):

1. Read workflow-status.json and get task_mapping["1.4"]
2. If exists: Use TaskUpdate tool with:
   - taskId: task_mapping["1.4"]
   - status: "in_progress"
   NOTE: User will see "Awaiting human review" when pressing Ctrl+T
3. If fails: Continue without error

**Action**: Use AskUserQuestion tool

```yaml
questions:
  - question: "중복 필터링이 완료되었습니다. AI 신뢰도가 0.9 미만입니다. 제거된 신호를 검토하시겠습니까?"
    header: "필터링 검토"
    multiSelect: false
    options:
      - label: "검토 건너뛰기 (권장: 신뢰도 양호)"
        description: "자동 필터링 결과를 신뢰하고 다음 단계로 진행합니다."
      - label: "제거된 신호 확인"
        description: "로그 파일을 열어 제거된 신호 목록을 보여드립니다."
```

**If user selects "Review"**:
- Read `logs/duplicates-removed-{date}.log`
- Display removed signals with reasons
- Ask if any should be restored using AskUserQuestion
- If restored: Re-add to filtered/new-signals-{date}.json

**Log decision**: Add to workflow-status.json human_decisions array

#### ③ POST-VERIFY (Human Checkpoint)

```yaml
Post-Verification (Layer 1 + Layer 2):
  Layer_1_Structural:
    - check: "User decision (skip or review) recorded in workflow-status.json"
      on_fail: HALT (cannot proceed without human decision)
    - check: "workflow-status.json updated with Step 1.4 in completed_steps"
      on_fail: RETRY (update workflow-status.json)

  Layer_2_Functional:
    - check: "User decision recorded in workflow-status.json human_decisions array"
      on_fail: RETRY (re-ask user)
    - check: "If signals restored: filtered/new-signals-{date}.json updated with restored signals"
      on_fail: RETRY
```

#### ④ RETRY

See `on_fail` actions in POST-VERIFY. Human checkpoint: retry means re-prompting user or re-applying recorded decision. Max retries: 2.

#### ⑤ RECORD

```yaml
Record to verification-report-{date}.json:
  step_id: "1.4"
  step_name: "Human Review of Filtering"
  verification_type: "human_checkpoint"
  pre_verification:
    status: "PASS|FAIL"
    checks: [list of passed PRE-VERIFY checks]
    timestamp: "{ISO8601}"
  post_verification:
    layer_1_structural: { status: "PASS|FAIL", details: "decision and status recorded" }
    layer_2_functional: { status: "PASS|FAIL", details: "user decision recorded" }
    layer_3_quality: null  # Human checkpoint: no quality layer
  retry_count: 0
  final_status: "VERIFIED"  # or "SKIPPED" if user chose to skip review
  user_decision: "skip" | "review"
  signals_restored: 0  # count of signals restored from duplicate list
  timestamp: "{ISO8601}"

Update workflow-status.json verification_results:
  total_checks += (pre_checks + post_checks)
  passed += (passed_count)
  warned += (warned_count)
```

**TASK UPDATE - AFTER USER DECISION** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping["1.4"]
2. If exists: Use TaskUpdate tool (taskId from step 1, status: "completed")
3. If fails: Continue without error

### Step 1.5: Expert Panel Validation (Conditional)

**Trigger**: Only if `len(filtered/new-signals-{date}.json) > 50`

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "filtered/new-signals-{date}.json exists with signal count > 50"
    on_fail: SKIP (condition not met, record as SKIPPED)
  - check: "Step 1.3 recorded as VERIFIED in verification-report"
    on_fail: HALT (deduplication must complete before expert validation)
```

#### ② EXECUTE (기존 로직)

**Action**: Use AskUserQuestion tool

```yaml
question: "신규 신호가 50개를 초과합니다 ({count}개). 전문가 패널 검증(RT-AID)을 활성화하시겠습니까?"
header: "전문가 검증"
multiSelect: false
options:
  - label: "전문가 검증 건너뛰기 (빠른 진행)"
    description: "AI 분석만으로 진행합니다. 2-3일 시간 절약."
  - label: "전문가 검증 활성화 (높은 품질)"
    description: "전문가 패널이 신호를 검증합니다. 48시간 소요."
```

**If activated**:
- Invoke Task tool with `@realtime-delphi-facilitator` agent
- Output: `validated/expert-validated-signals-{date}.json`
- Workflow status: "blocked" for 48 hours
- Send notification to experts
- Resume when expert responses collected

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
If_Skipped: Record final_status="SKIPPED" in verification-report

If_Activated:
  Layer_1_Structural:
    - check: "validated/expert-validated-signals-{date}.json exists"
      on_fail: RETRY (re-send notification, extend deadline)
  Layer_2_Functional:
    - check: "Expert responses cover at least 50% of submitted signals"
      on_fail: WARN (partial coverage acceptable)
    - check: "Each validated signal has expert_consensus field"
      on_fail: RETRY
  Layer_3_Quality:
    - check: "Expert-AI agreement rate > 70%"
      on_fail: WARN (significant disagreement noted for Phase 2)
```

#### ④ RETRY

If activated and failed: Max 1 retry (extend expert deadline). If still no responses: WARN and proceed with AI-only classifications.

#### ⑤ RECORD

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "1.5"
step_name: "Expert Panel Validation"
agent: "@realtime-delphi-facilitator"
conditional: true
additional_data:
  condition_met: true/false  # was signal count > 50?
  activated: true/false      # did user choose to activate?
  expert_response_rate: {value}  # null if skipped
  ai_expert_agreement: {value}   # null if skipped
```
If condition not met or user skipped: `final_status: "SKIPPED"`.
Record to verification-report using Standard RECORD Template. Update workflow-status.json counters.

**━━━ PIPELINE GATE 1: Phase 1 → Phase 2 전환 검증 ━━━**

After all Phase 1 steps complete, execute Pipeline Gate 1 before proceeding to Phase 2:

```yaml
Pipeline_Gate_1_Checks:
  1_signal_id_continuity:
    check: "Every signal ID in filtered/new-signals-{date}.json exists in raw/daily-scan-{date}.json"
    purpose: "No signals were fabricated during filtering"
    on_fail: TRACE_BACK to Step 1.3

  2_classified_signals_complete:
    check: "Every signal in filtered/new-signals-{date}.json has a corresponding entry with final_category in structured/classified-signals-{date}.json"
    purpose: "Classification was applied to all surviving signals (classification output is in structured/ not filtered/)"
    on_fail: TRACE_BACK to Step 1.2 (classification phase)

  3_shared_context_populated:
    check: "context/shared-context-{date}.json contains dedup_analysis field (dedup confidence scores and method used)"
    purpose: "Inter-agent data sharing is functional"
    on_fail: TRACE_BACK to Step 1.3

  4_file_pair_check:
    check: "For each EN output file, a -ko counterpart exists"
    purpose: "Bilingual workflow integrity"
    on_fail: WARN (translation failures are non-critical)

  5_data_flow_integrity:
    check: "Signal count: raw >= filtered (no signals added during filtering)"
    purpose: "Deduplication can only reduce, never add signals"
    on_fail: TRACE_BACK to Step 1.3

  6_no_id_corruption:
    check: "All signal IDs in filtered file are unique (no duplicates within results)"
    purpose: "Basic data integrity"
    on_fail: TRACE_BACK to Step 1.3
```

**Gate Result**:
- ALL checks PASS → Record "Pipeline_Gate_1: PASS" in verification-report, proceed to Phase 2
- Any check FAIL → Identify failing Step via TRACE_BACK, re-execute that Step (max 1 retry), re-check Gate
- Gate still fails after retry → HALT and ask user for intervention

**TASK UPDATE - PG1 COMPLETION** (Optional, non-critical):

After Pipeline Gate 1 passes:
1. Read workflow-status.json and get task_mapping
2. If exists: Mark PG1 and Phase 1 as completed:
   - TaskUpdate(taskId: task_mapping["PG1"], status: "completed")
   - TaskUpdate(taskId: task_mapping["phase1"], status: "completed")
3. If fails: Continue without error

**Update workflow-status.json**:
```json
{
  "current_phase": 1,
  "completed_steps": ["1.1", "1.2", "1.3", "1.4", "1.5"],
  "phase_1_metrics": {
    "signals_collected": 247,
    "signals_filtered": 79,
    "dedup_rate": 68,
    "avg_confidence": 0.92
  },
  "verification_results": {
    "pipeline_gates_passed": 1
  }
}
```

---

## Phase 2: Planning (Analysis & Structuring)

### Step 2.1: Classification Verification

**Status**: ✅ **Classification now happens in Step 1.2** (Direct by Claude Code)

**Purpose**: Verify and enrich classifications from Step 1.2

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "structured/classified-signals-{date}.json exists (output of Step 1.2)"
    on_fail: HALT (cannot verify without classified signals)
  - check: "Pipeline Gate 1 recorded as PASS in verification-report"
    on_fail: HALT (Phase 1 must pass gate before Phase 2 begins)
  - check: "All signals in classified file have final_category field"
    on_fail: TRACE_BACK to Step 1.2 (classification incomplete)
```

#### ② EXECUTE (기존 로직)

**Action**: Read classified signals and verify quality

```yaml
Description: Verify classification quality from Step 1.2
Input files:
  - structured/classified-signals-{date}.json (already classified in Step 1.2)
  - validated/expert-validated-signals-{date}.json (if exists from Step 1.5)
  - context/shared-context-{date}.json
Output:
  - structured/classified-signals-{date}.json (updated if needed)
  - logs/classification-quality-{date}.json (quality metrics)
```

**Quality Checks**:
1. Count signals per category
2. Check confidence distribution
3. Identify low-confidence classifications (< 0.7)
4. Flag any invalid categories

**If quality issues found**:
- Use AskUserQuestion to show issues
- Allow manual correction
- Re-classify specific signals if requested

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "structured/classified-signals-{date}.json still exists and is valid JSON"
    on_fail: RETRY
  - check: "logs/classification-quality-{date}.json exists"
    on_fail: RETRY

Layer_2_Functional:
  - check: "All signals have final_category (S, T, E, E, P, s only)"
    on_fail: RETRY
  - check: "All have classification_confidence > 0.0"
    on_fail: RETRY
  - check: "Invalid categories corrected (zero remaining after verification)"
    on_fail: RETRY
  - check: "Expert validations override Claude Code classifications (if Step 1.5 was executed)"
    on_fail: RETRY

Layer_3_Quality:
  - check: "Average classification_confidence > 0.85"
    on_fail: WARN
  - check: "Low-confidence signals (< 0.7) count < 20% of total"
    on_fail: WARN (flag for Step 2.5 human review)
  - check: "Category distribution logged in quality file"
    on_fail: WARN
```

#### ④ RETRY (실패 시)

Layer 1/2 failure: Re-execute classification verification (max 2 retries)
Layer 3 failure: Log warning, flag for human review in Step 2.5

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "2.1"
step_name: "Signal Classification"
agent: "@signal-classifier"
additional_data:
  avg_confidence: {value}
  category_distribution: { S: n, T: n, E_econ: n, E_env: n, P: n, s: n }
  corrections_made: {count}
```

**Task Management**:
- Create subtask: "Verify classification quality"
- Track: avg_confidence, category_distribution, corrections_made

**Error Handling**:
- If invalid category found: Auto-correct to best guess, log warning
- If all confidences < 0.7: Flag for human review in Step 2.5
- **Retry (VEV)**: Layer 1/2 failure → max 2 retries. On exhaustion → HALT_and_ask_user (non-critical step, but analysis quality affected)

---

### Step 2.1b: Translation (If Step 2.1 executed)

**If classification quality log was generated**, translate it:

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: logs/classification-quality-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.85
  enable_back_translation: false
Output:
  logs/classification-quality-{date}-ko.json
```

**Task Management**: Create subtask "Translate quality log"

---

### Step 2.2: Impact Analysis

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "structured/classified-signals-{date}.json exists with at least 1 signal"
    on_fail: HALT (nothing to analyze)
  - check: "All signals have final_category and classification_confidence"
    on_fail: TRACE_BACK to Step 2.1
  - check: "Step 2.1 recorded as VERIFIED (or WARN-accepted) in verification-report"
    on_fail: HALT (classification must be verified first)
```

#### ② EXECUTE (기존 로직)

**Invoke**: Task tool with `@impact-analyzer` worker agent

```yaml
Agent: impact-analyzer
Description: Analyze impacts and cross-influences
Input files:
  - structured/classified-signals-{date}.json
  - context/shared-context-{date}.json
Output:
  - analysis/impact-assessment-{date}.json
  - analysis/cross-impact-matrix-{date}.json
  - analysis/scenario-probabilities-{date}.json
  - context/shared-context-{date}.json (updated with impact scores)
Substeps:
  - SubStep 2.2.1: Identify direct and derived impacts
  - SubStep 2.2.2: Build cross-impact matrix (optimized, not full N×N)
  - SubStep 2.2.3: Generate Bayesian network probabilities
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "analysis/impact-assessment-{date}.json exists and is valid JSON"
    on_fail: RETRY
  - check: "analysis/cross-impact-matrix-{date}.json exists and is valid JSON"
    on_fail: RETRY
  - check: "analysis/scenario-probabilities-{date}.json exists (or Bayesian skipped with log)"
    on_fail: RETRY (unless Bayesian network failure was logged)

Layer_2_Functional:
  - check: "Every signal in classified file has corresponding entry in impact-assessment"
    on_fail: RETRY (signals lost during analysis)
  - check: "Each signal's impact entry has primary_impacts (1st order) array with >= 1 entry"
    on_fail: RETRY
  - check: "Each signal's impact entry has secondary_impacts (2nd order) array"
    on_fail: RETRY
  - check: "Cross-impact matrix dimensions match signal count (NxN where N = signal count)"
    on_fail: RETRY
  - check: "All influence scores in range [-5, +5]"
    on_fail: RETRY
  - check: "Scenario probabilities sum to approximately 1.0 (tolerance ±0.05)"
    on_fail: WARN (if scenario probabilities exist)

Layer_3_Quality:
  - check: "Average impact coverage: each signal has >= 2 primary impacts"
    on_fail: WARN (shallow analysis)
  - check: "Cross-impact matrix sparsity < 99.99% (at least some cross-influences detected)"
    on_fail: WARN (signals may be too independent for meaningful cross-impact)
  - check: "Shared context updated with impact_analysis field"
    on_fail: WARN
```

#### ④ RETRY (실패 시)

Layer 1/2 failure:
1. Re-invoke `@impact-analyzer` (attempt 2, delay 2s)
2. If SubStep 2.2.3 (Bayesian) specifically fails: Skip and continue with WARN
3. If core impact analysis fails after 2 retries: Log error E5000, HALT

Layer 3 failure: Log warning, continue

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "2.2"
step_name: "Impact Analysis"
agent: "@impact-analyzer"
additional_data:
  signals_analyzed: {count}
  cross_impacts_computed: {count}
  bayesian_network_status: "success|skipped"
```

**Task Management**:
- Create 3 subtasks for each substep
- Update task progress incrementally

**Error Handling**:
- If Bayesian network fails: Skip scenario probabilities, continue
- If impact analysis fails: Log error E5000, halt (critical step)

---

### Step 2.2b: Translation (Automatic)

**CRITICAL**: After Step 2.2 completes, **immediately invoke translation**.

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: analysis/impact-assessment-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.90
  enable_back_translation: true  # Important for analysis quality
Output:
  analysis/impact-assessment-{date}-ko.json
Verification:
  - Impact scores identical (numeric)
  - 1st/2nd order impacts translated naturally
  - Cross-influence relationships preserved
```

**Task Management**: Create subtask "Translate impact analysis"

**Error Handling**: Non-critical, continue if fails

---

### Step 2.3: Priority Ranking

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "analysis/impact-assessment-{date}.json exists"
    on_fail: HALT (impact analysis required for ranking)
  - check: "Impact assessment contains entries for all classified signals"
    on_fail: TRACE_BACK to Step 2.2
  - check: "Step 2.2 recorded as VERIFIED in verification-report"
    on_fail: HALT (impact analysis must be verified)
```

#### ② EXECUTE (기존 로직)

**Invoke**: Task tool with `@priority-ranker` worker agent

```yaml
Agent: priority-ranker
Description: Rank signals by weighted criteria
Input files:
  - analysis/impact-assessment-{date}.json
  - context/shared-context-{date}.json
Output:
  - analysis/priority-ranked-{date}.json
Criteria:
  - Impact: 40%
  - Probability: 30%
  - Urgency: 20%
  - Novelty: 10%
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "analysis/priority-ranked-{date}.json exists and is valid JSON"
    on_fail: RETRY

Layer_2_Functional:
  - check: "All signals have priority_score field"
    on_fail: RETRY
  - check: "All priority_score values in range [0, 10]"
    on_fail: RETRY
  - check: "Signals are sorted by priority_score descending"
    on_fail: RETRY (sorting is a core requirement)
  - check: "Signal count in ranked file == signal count in classified file"
    on_fail: RETRY (no signals should be lost during ranking)
  - check: "Top 10 signals clearly identified (top_signals array or equivalent)"
    on_fail: RETRY
  - check: "Each signal has component scores: impact, probability, urgency, novelty"
    on_fail: RETRY

Layer_3_Quality:
  - check: "Weight sum verification: impact(40) + probability(30) + urgency(20) + novelty(10) = 100"
    on_fail: WARN (weight misconfiguration)
  - check: "Priority score distribution: standard deviation > 0.5 (signals are differentiated)"
    on_fail: WARN (all signals ranked similarly suggests insufficient differentiation)
  - check: "Top 10 signals span at least 2 STEEPs categories"
    on_fail: WARN (potential category bias in top rankings)
```

#### ④ RETRY (실패 시)

Layer 1/2 failure: Re-invoke `@priority-ranker` (max 2 retries, exponential backoff)
Layer 3 failure: Log warning, continue (quality issues noted for human review in Step 2.5)

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "2.3"
step_name: "Priority Ranking"
agent: "@priority-ranker"
additional_data:
  signals_ranked: {count}
  top_signal_score: {value}
  weight_distribution: { impact: 0.4, probability: 0.3, urgency: 0.2, novelty: 0.1 }
```

**Retry (VEV)**: Layer 1/2 failure → max 2 retries. On exhaustion → HALT_and_ask_user (ranking is required for human review).

---

### Step 2.3b: Translation (Automatic)

**CRITICAL**: After Step 2.3 completes, **immediately invoke translation**.

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: analysis/priority-ranked-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.95  # HIGH PRIORITY: Used in human review
  enable_back_translation: true
Output:
  analysis/priority-ranked-{date}-ko.json
Verification:
  - Priority scores identical (numeric)
  - Ranking order identical
  - All STEEPs categories unchanged
  - Natural Korean explanations
```

**Task Management**: Create subtask "Translate priority rankings"

**Error Handling**: Log warning if fails, but continue (user review will use EN if KR missing)

---

### Step 2.4: Scenario Building (Conditional)

**Trigger**: Only if cross-impact matrix shows high interconnection

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "analysis/cross-impact-matrix-{date}.json exists"
    on_fail: SKIP (no cross-impact data for complexity calculation)
  - check: "Step 2.3 recorded as VERIFIED in verification-report"
    on_fail: HALT
```

Calculate complexity:
```
complexity_score = (num_strong_influences / total_possible_influences)
threshold = 0.15
```

If `complexity_score <= 0.15`: Record final_status="SKIPPED" (complexity below threshold).

#### ② EXECUTE (기존 로직)

**If complexity_score > 0.15**: Ask user

```yaml
question: "신호 간 상호영향이 복잡합니다(복잡도: {score}). 시나리오 생성을 활성화하시겠습니까?"
header: "시나리오 생성"
options:
  - label: "시나리오 건너뛰기"
    description: "분석 결과만으로 보고서를 생성합니다."
  - label: "시나리오 생성 (QUEST 방법론)"
    description: "4가지 플러서블 시나리오를 생성합니다."
```

**If activated**:
- Invoke `@scenario-builder` agent
- Output: `scenarios/scenarios-{date}.json`

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
If_Skipped_By_User: Record final_status="SKIPPED"

If_Activated:
  Layer_1_Structural:
    - check: "scenarios/scenarios-{date}.json exists and is valid JSON"
      on_fail: RETRY
  Layer_2_Functional:
    - check: "At least 2 plausible scenarios generated"
      on_fail: RETRY
    - check: "Each scenario references signals from priority-ranked list"
      on_fail: RETRY
    - check: "Scenario probabilities sum to approximately 1.0 (±0.05)"
      on_fail: WARN
  Layer_3_Quality:
    - check: "Scenarios are distinguishable (not trivially similar)"
      on_fail: WARN
```

#### ④ RETRY

If activated and failed: Max 2 retries. If exhausted: WARN and proceed without scenarios.

#### ⑤ RECORD

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "2.4"
step_name: "Scenario Building"
agent: "@scenario-builder"
conditional: true
additional_data:
  condition_met: true/false    # complexity_score > 0.15?
  activated: true/false        # did user choose to activate?
  scenarios_generated: {count}  # null if skipped
  complexity_score: {value}
```
If condition not met or user skipped: `final_status: "SKIPPED"`.

---

### Step 2.4b: Translation (Conditional - If Step 2.4 activated)

**CRITICAL**: If scenarios generated, **immediately invoke translation**.

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: scenarios/scenarios-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.95
  enable_back_translation: true
Output:
  scenarios/scenarios-{date}-ko.json
Verification:
  - Scenario narratives translated naturally
  - Probability scores identical
  - Signal references unchanged
```

**Task Management**: Create subtask "Translate scenarios"

---

### Step 2.5: Human Review of Analysis (Required)

**Type**: Human checkpoint (blocking)

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "structured/classified-signals-{date}.json exists"
    on_fail: HALT
  - check: "analysis/priority-ranked-{date}.json exists with sorted signals"
    on_fail: HALT
  - check: "analysis/impact-assessment-{date}.json exists"
    on_fail: HALT
  - check: "Step 2.3 recorded as VERIFIED in verification-report"
    on_fail: HALT (ranking must be verified before human review)
```

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE USER REVIEW** (Optional, enables Ctrl+T visibility):

1. Read workflow-status.json and get task_mapping["2.5"]
2. If exists: Use TaskUpdate tool with:
   - taskId: (from step 1)
   - status: "in_progress"
   NOTE: User will see "Awaiting human review" when pressing Ctrl+T
3. If fails: Continue without error

**Action**: Use AskUserQuestion tool

```yaml
questions:
  - question: "STEEPs 분류가 정확합니까? 상위 10개 신호를 검토해주세요."
    header: "분류 검토"
    multiSelect: false
    options:
      - label: "분류 정확함"
        description: "AI 분류를 승인하고 진행합니다."
      - label: "일부 수정 필요"
        description: "수정이 필요한 신호를 지정해주세요."

  - question: "우선순위 순서가 적절합니까?"
    header: "우선순위 검토"
    multiSelect: false
    options:
      - label: "순서 적절함"
        description: "현재 순위를 유지합니다."
      - label: "순위 조정 필요"
        description: "조정할 신호를 지정해주세요."

  - question: "추가 코멘트나 지시사항이 있습니까?"
    header: "추가 의견"
    multiSelect: false
    options:
      - label: "없음"
        description: "다음 단계로 진행합니다."
      - label: "있음"
        description: "코멘트를 입력해주세요."
```

**Process user feedback**:
- If modifications requested: Update structured/classified-signals-{date}.json
- If priority adjustments: Update analysis/priority-ranked-{date}.json
- Log all decisions

#### ③ POST-VERIFY (Human Checkpoint)

```yaml
Post-Verification (Layer 1 + Layer 2):
  Layer_1_Structural:
    - check: "User approval or modification decision recorded in workflow-status.json"
      on_fail: HALT (cannot proceed without human decision)
    - check: "workflow-status.json updated with Step 2.5 in completed_steps"
      on_fail: RETRY (update workflow-status.json)

  Layer_2_Functional:
    - check: "User decision recorded in workflow-status.json human_decisions array"
      on_fail: RETRY (re-ask user)
    - check: "If modifications made: updated files are valid JSON with correct schema"
      on_fail: RETRY (re-apply modifications)
    - check: "If priority adjusted: signals still sorted by priority_score descending"
      on_fail: RETRY (re-sort)
```

#### ④ RETRY

See `on_fail` actions in POST-VERIFY. Human checkpoint: retry means re-prompting user or re-applying modifications. Max retries: 2.

#### ⑤ RECORD

```yaml
Record to verification-report-{date}.json:
  step_id: "2.5"
  step_name: "Human Review of Analysis"
  verification_type: "human_checkpoint"
  pre_verification:
    status: "PASS|FAIL"
    checks: [list of passed PRE-VERIFY checks]
    timestamp: "{ISO8601}"
  post_verification:
    layer_1_structural: { status: "PASS|FAIL", details: "decision and status recorded" }
    layer_2_functional: { status: "PASS|FAIL", details: "modifications applied correctly" }
    layer_3_quality: null  # Human checkpoint: no quality layer
  retry_count: 0
  final_status: "VERIFIED"
  user_decision: "approve" | "modify"
  modifications_made:
    categories_changed: 0
    priorities_adjusted: 0
    signals_removed: 0
    comments_added: 0
  timestamp: "{ISO8601}"

Update workflow-status.json verification_results:
  total_checks += (pre_checks + post_checks)
  passed += (passed_count)
  warned += (warned_count)
```

**TASK UPDATE - AFTER USER APPROVAL** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping["2.5"]
2. If exists: Use TaskUpdate tool (taskId from step 1, status: "completed")
3. If fails: Continue without error

**━━━ PIPELINE GATE 2: Phase 2 → Phase 3 전환 검증 ━━━**

After Step 2.5 human approval, execute Pipeline Gate 2 before proceeding to Phase 3:

```yaml
Pipeline_Gate_2_Checks:
  1_signal_count_match:
    check: "classified count == impact-assessed count == priority-ranked count"
    purpose: "No signals lost or added during analysis pipeline"
    on_fail: TRACE_BACK (identify where count diverged)

  2_score_range_valid:
    check: "All priority_score in [0, 10], all impact_score in [-5, +5]"
    purpose: "Score integrity across analysis chain"
    on_fail: TRACE_BACK to Step 2.3 or 2.2

  3_human_approval_recorded:
    check: "Step 2.5 decision logged in workflow-status.json human_decisions array"
    purpose: "Human checkpoint was properly executed"
    on_fail: HALT (cannot proceed to Phase 3 without human approval)

  4_analysis_chain_complete:
    check: "classified-signals → impact-assessment → priority-ranked files all exist"
    purpose: "Complete analysis chain integrity"
    on_fail: TRACE_BACK (identify missing file)

  5_steeps_consistency:
    check: "STEEPs categories in priority-ranked match categories in classified-signals"
    purpose: "Categories not altered during analysis"
    on_fail: TRACE_BACK to Step 2.2 or 2.3

  6_bilingual_pairs:
    check: "KR counterparts exist for analysis files (impact, priority)"
    purpose: "Bilingual workflow integrity for Phase 3 report"
    on_fail: WARN (non-critical, EN-only acceptable)
```

**Gate Result**:
- ALL checks PASS → Record "Pipeline_Gate_2: PASS", proceed to Phase 3
- Any FAIL → TRACE_BACK, re-execute failing Step (max 1 retry), re-check Gate
- Gate still fails → HALT and ask user

**Update workflow-status.json**:
```json
{
  "current_phase": 2,
  "completed_steps": ["1.1", ..., "2.1", "2.2", "2.3", "2.5"],
  "blocked_on": null,
  "phase_2_metrics": {
    "signals_classified": 79,
    "categories": {"S": 12, "T": 28, "E": 15, "E": 8, "P": 10, "s": 6},
    "avg_priority_score": 6.5
  },
  "verification_results": {
    "pipeline_gates_passed": 2
  }
}
```

**TASK UPDATE - PHASE 2 COMPLETION** (Optional, enables Phase 3 unblocking):

After Phase 2 Integration Test passes:
1. Read workflow-status.json and get task_mapping
2. If exists: Mark Pipeline Gate 2 and Phase 2 as completed:
   - TaskUpdate(taskId: task_mapping["PG2"], status: "completed")
   - TaskUpdate(taskId: task_mapping["phase2"], status: "completed")
   NOTE: This automatically unblocks Phase 3 due to dependency chain
3. Display to user:
   "✅ Phase 2 완료 (Planning Complete)"
   "💡 진행 상황 확인 / Check progress: Press Ctrl+T"
4. If fails: Continue without error

---

## Phase 3: Implementation (Report Generation)

### Step 3.1: Database Update ⚠️ CRITICAL

#### ① PRE-VERIFY (선행 조건 확인) — STRICT MODE

```yaml
Pre-Verification Checks (ALL must PASS — no exceptions for critical step):
  - check: "structured/classified-signals-{date}.json exists and is valid JSON"
    on_fail: HALT (cannot update DB without classified signals)
  - check: "signals/database.json exists and is valid JSON"
    on_fail: HALT (target database missing or corrupt)
  - check: "signals/database.json is writable"
    on_fail: HALT (permission issue)
  - check: "Pipeline Gate 2 recorded as PASS in verification-report"
    on_fail: HALT (Phase 2 must pass gate before DB update)
  - check: "Step 2.5 human approval recorded in workflow-status.json"
    on_fail: HALT (human approval required before DB modification)
  - check: "signals/snapshots/ directory exists and is writable"
    on_fail: HALT (backup location must be available)
```

**CRITICAL**: If ANY pre-verify check fails, do NOT invoke the database updater. Log error and halt immediately.

#### ② EXECUTE (기존 로직)

**Invoke**: Task tool with `@database-updater` worker agent

```yaml
Agent: database-updater
Description: Update master signals database
Input files:
  - structured/classified-signals-{date}.json
  - signals/database.json
Output:
  - signals/database.json (updated)
  - signals/snapshots/database-{date}.json (backup)
Critical: true (failure halts workflow)
```

#### ③ POST-VERIFY (3-Layer 사후 검증) — STRICT MODE

```yaml
Layer_1_Structural:
  - check: "signals/snapshots/database-{date}.json exists (backup created BEFORE update)"
    on_fail: RESTORE_AND_HALT
  - check: "signals/database.json exists and is valid JSON (not corrupted by update)"
    on_fail: RESTORE_AND_HALT
  - check: "Backup file size > 0 bytes"
    on_fail: RESTORE_AND_HALT

Layer_2_Functional:
  - check: "New signal count in updated DB = backup count + new classified signals count"
    formula: "len(updated_db) == len(backup_db) + len(new_signals)"
    on_fail: RESTORE_AND_HALT
  - check: "All signal IDs in updated DB are unique (no duplicate keys)"
    on_fail: RESTORE_AND_HALT
  - check: "All new signal IDs from classified file exist in updated DB"
    on_fail: RESTORE_AND_HALT (signals were lost during update)
  - check: "All pre-existing signals from backup still exist in updated DB"
    on_fail: RESTORE_AND_HALT (existing signals were overwritten)
  - check: "Required fields present for all new signals: title, source, date, category"
    on_fail: RESTORE_AND_HALT

Layer_3_Quality:
  - check: "No numeric field anomalies (scores in valid ranges)"
    on_fail: WARN (log but DB update is already committed)
  - check: "Database JSON file size increased (new signals added)"
    on_fail: WARN (possible: all signals were updates, not additions)
```

#### ④ RETRY (실패 시) — CRITICAL STEP PROTOCOL

**ANY Layer 1 or Layer 2 failure triggers RESTORE_AND_HALT:**
1. Immediately restore signals/database.json from signals/snapshots/database-{date}.json
2. Verify restoration succeeded (compare file sizes)
3. Log error E7000 with detailed failure reason
4. HALT workflow
5. Ask user: "데이터베이스 업데이트 실패. 백업에서 복원 완료. 재시도하시겠습니까?"
6. If user approves retry: Re-execute from Step 3.1 (max 1 retry)
7. If retry also fails: HALT permanently with error report

**Layer 3 failure: WARN only** (DB is already updated, quality note logged)

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.
**CRITICAL step: verification is highlighted in `verification_summary.critical_step_status`.**

**Step-specific record fields**:
```yaml
step_id: "3.1"
step_name: "Database Update"
agent: "@database-updater"
critical: true
additional_data:
  signals_added: {count}
  signals_updated: {count}
  backup_path: "signals/snapshots/database-{date}.json"
  final_db_count: {count}
```

**Task Management**:
- Create subtask: "Update signals database"
- This is a CRITICAL step - if it fails, entire workflow fails

**Error Handling**:
- Before update: MUST create backup
- Use atomic operations (write to temp, then rename)
- If update fails: Restore from backup (RESTORE_AND_HALT)
- If failure: Log error E7000 and HALT
- **Retry (VEV)**: Layer 1/2 failure → max 2 retries. On exhaustion → RESTORE_AND_HALT (restore backup, halt workflow, notify user)

### Step 3.2: Report Generation

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "structured/classified-signals-{date}.json exists"
    on_fail: HALT
  - check: "analysis/priority-ranked-{date}.json exists"
    on_fail: HALT
  - check: "analysis/impact-assessment-{date}.json exists"
    on_fail: HALT
  - check: "signals/database.json was successfully updated (Step 3.1 VERIFIED)"
    on_fail: HALT (DB must be updated before report references it)
  - check: "reports/daily/ directory exists and is writable"
    on_fail: HALT
```

#### ② EXECUTE (기존 로직)

**Invoke**: Task tool with `@report-generator` worker agent

```yaml
Agent: report-generator
Description: Generate English-language report (will be translated in Step 3.2b)
Input files:
  - structured/classified-signals-{date}.json
  - analysis/priority-ranked-{date}.json
  - scenarios/scenarios-{date}.json (optional)
  - context/shared-context-{date}.json
Output:
  - reports/daily/environmental-scan-{date}.md
Language: English (primary)
```

#### ③ POST-VERIFY (3-Layer 사후 검증 + Automated Validation Script)

> **v2.3.0 CHANGE**: Manual section checks replaced by `validate_report.py` programmatic validation.
> This ensures 14 checks are applied consistently, preventing the 2026-02-02 quality regression.

**Step 1: Run automated validator**

```bash
python3 env-scanning/scripts/validate_report.py \
  {data_root}/reports/daily/environmental-scan-{date}.md \
  --profile {validate_profile} --json
```

> `{validate_profile}` is received from master-orchestrator invocation (sourced from SOT).
> For WF1 this is typically `standard`; do NOT hardcode the value.

**Step 2: Interpret exit code**

| Exit Code | Status | Action |
|-----------|--------|--------|
| 0 | PASS | All 14 checks passed → proceed to Step 3.2b |
| 1 | FAIL | CRITICAL checks failed → trigger RETRY (see ④ below) |
| 2 | WARN | ERROR-level issues only → log warnings, proceed with caution |

**Step 3: Map validator checks to VEV layers**

```yaml
Layer_1_Structural (from validate_report.py):
  - FILE-001: "Report file exists"                    → on_fail: RETRY
  - FILE-002: "File size >= 1KB"                      → on_fail: RETRY
  - SKEL-001: "No unfilled {{PLACEHOLDER}} tokens"    → on_fail: RETRY

Layer_2_Functional (from validate_report.py):
  - SEC-001:  "7 mandatory section headers present"   → on_fail: RETRY
  - SIG-001:  "10+ signal blocks present"             → on_fail: RETRY
  - SIG-002:  "Each signal has all 9 required fields" → on_fail: RETRY  # KEY CHECK — catches 02-02 bug
  - S5-001:   "Section 5 has 5.1/5.2/5.3 subsections" → on_fail: RETRY
  - SEC-002:  "Each section meets minimum word count"  → on_fail: RETRY
  - S3-001:   "Section 3 has 3.1/3.2 subsections"     → on_fail: WARN
  - S4-001:   "Section 4 has 4.1/4.2 subsections"     → on_fail: WARN
  - S4-002:   "3+ cross-impact pairs (↔)"             → on_fail: WARN
  - SIG-003:  "Each field name appears 10+ times"      → on_fail: WARN

Layer_3_Quality (from validate_report.py):
  - QUAL-001: "Total 5,000+ words"                    → on_fail: WARN
  - QUAL-002: "Korean character ratio >= 30%"          → on_fail: WARN

Additional Manual Checks (not in validator):
  - check: "Top 5 priority signals appear in Executive Summary"
    on_fail: WARN
  - check: "STEEPs category distribution mentioned in report"
    on_fail: WARN
```

#### ④ RETRY (실패 시 — 3단계 점진적 강화)

**Retry 1 — Targeted Fix (위반 항목만 수정)**:
1. Parse `validate_report.py --json` output to extract failing check IDs and details
2. Re-invoke `@report-generator` with explicit instruction:
   ```
   The following validation checks FAILED. Fix ONLY these sections:
   {list of failing checks with details from validator JSON}
   Keep all other sections unchanged.
   ```
3. Re-run `validate_report.py` on the regenerated report

**Retry 2 — Full Skeleton Regeneration (전체 재생성)**:
1. If Retry 1 still fails, re-invoke `@report-generator` with:
   ```
   FULL REGENERATION REQUIRED.
   Use the skeleton template at .claude/skills/env-scanner/references/report-skeleton.md
   Fill every {{PLACEHOLDER}} with data.
   Previous violations: {full validator JSON output}
   Refer to the GOLDEN REFERENCE example for correct 9-field format.
   ```
2. Re-run `validate_report.py` on the regenerated report

**Retry Exhausted — Human Escalation**:
1. If Retry 2 still fails:
   - Insert warning banner at report top: `> ⚠️ **품질 검증 미통과** — 아래 항목이 검증을 통과하지 못했습니다: {failing checks}`
   - Log `E3200: Report validation failed after 2 retries` to verification-report
   - Continue to Step 3.4 with quality warning displayed to user

Layer 3 failure (WARN only): Log warning, continue (quality notes included in final approval display)

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "3.2"
step_name: "Report Generation"
agent: "@report-generator"
additional_data:
  sections_generated: {count}
  report_path: "reports/daily/environmental-scan-{date}.md"
  word_count: {count}
  validation_result:
    overall_status: "PASS|WARN|FAIL"
    checks_passed: {count}
    checks_failed: {count}
    critical_failures: [{check_ids}]
    retries_used: {0|1|2}
```

**Report Sections** (must be included — validated by SEC-001):
1. 경영진 요약
2. 신규 탐지 신호
3. 기존 신호 업데이트
4. 패턴 및 연결고리
5. 전략적 시사점
7. 신뢰도 분석
8. 부록

**Optional Sections** (if Step 2.4 activated):
6. 플러서블 시나리오

**Retry (VEV)**: Layer 1/2 failure → Targeted Fix (Retry 1) → Full Skeleton Regen (Retry 2) → Human Escalation with warning banner. See ④ RETRY above for detailed protocol.

---

### Step 3.2b: Translation (Automatic - CRITICAL)

**CRITICAL**: After Step 3.2 completes, **immediately invoke translation** for the main report.

**This is the MOST IMPORTANT translation** - the final deliverable.

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: reports/daily/environmental-scan-{date}.md
  source_format: markdown
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.95  # HIGHEST QUALITY
  enable_back_translation: true  # MANDATORY for report
Output:
  reports/daily/environmental-scan-{date}-ko.md
Verification:
  - KR report exists
  - All sections present in Korean
  - STEEPs categories unchanged (S, T, E, E, P, s)
  - Markdown structure preserved
  - Links functional
  - Natural Korean phrasing
  - Back-translation similarity > 0.95
```

**Task Management**: Create subtask "Translate final report (Korean)"

**Error Handling**:
- **If translation fails**: Retry up to 3 times
- **If still fails**: Generate warning to user, provide EN report with note
- **Quality check fails**: Flag for human review at Step 3.4
- This is the ONLY translation that triggers warning if it fails

**Update Shared Context**:
```json
{
  "translation_status": {
    "translations_completed": [
      {
        "step": "step_3.2b",
        "source_file": "reports/daily/environmental-scan-{date}.md",
        "target_file": "reports/daily/environmental-scan-{date}-ko.md",
        "translation_confidence": 0.96,
        "back_translation_similarity": 0.94,
        "quality_status": "PASS"
      }
    ]
  }
}
```

---

### Step 3.3: Archive and Notify

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "reports/daily/environmental-scan-{date}.md exists (EN report)"
    on_fail: HALT (nothing to archive)
  - check: "reports/daily/environmental-scan-{date}-ko.md exists (KR report)"
    on_fail: WARN (archive EN-only if KR missing)
  - check: "signals/database.json exists (for snapshot)"
    on_fail: HALT
  - check: "Step 3.2 recorded as VERIFIED in verification-report"
    on_fail: HALT (report must be verified before archiving)
  - check: "reports/archive/ directory exists and is writable"
    on_fail: HALT
```

#### ② EXECUTE (기존 로직)

**Invoke**: Task tool with `@archive-notifier` worker agent

```yaml
Agent: archive-notifier
Description: Archive report and send notifications
Input files:
  - reports/daily/environmental-scan-{date}.md
  - signals/database.json
Actions:
  - Copy report to reports/archive/{year}/{month}/
  - Create signal snapshot
  - Send notifications (optional, if configured)
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Layer_1_Structural:
  - check: "reports/archive/{year}/{month}/environmental-scan-{date}.md exists"
    on_fail: RETRY
  - check: "signals/snapshots/database-{date}.json exists"
    on_fail: RETRY (snapshot may have been created in Step 3.1, verify it exists)

Layer_2_Functional:
  - check: "Archive file content matches daily report (identical or checksum match)"
    on_fail: RETRY (copy may have been corrupted)
  - check: "Archive path follows convention: reports/archive/{YYYY}/{MM}/"
    on_fail: RETRY
  - check: "Both EN and KR versions archived (if KR exists)"
    on_fail: WARN (KR archive is non-critical)

Layer_3_Quality:
  - check: "Archive file is readable and non-empty"
    on_fail: WARN
  - check: "Notification sent (if configured) - check log for confirmation"
    on_fail: WARN (notification is optional)
```

#### ④ RETRY (실패 시)

Layer 1/2 failure: Re-invoke `@archive-notifier` (max 2 retries)
Layer 3 failure: Log warning, continue

#### ⑤ RECORD (검증 결과 기록)

Record to `verification-report-{date}.json` using **Standard RECORD Template** (see VEV Protocol section).
Update `workflow-status.json` `verification_results` counters per standard pseudo-code.

**Step-specific record fields**:
```yaml
step_id: "3.3"
step_name: "Archive & Notification"
agent: "@archive-notifier"
additional_data:
  archive_path: "reports/archive/{year}/{month}/"
  files_archived: {count}
  notification_sent: true/false
```

**Note**: Archive should copy BOTH EN and KR reports to archive directory.

**Retry (VEV)**: Layer 1/2 failure → max 2 retries. On exhaustion → WARN_and_continue (archival failure is non-critical, workflow can complete).

---

### Step 3.3b: Translation (Automatic)

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: logs/daily-summary-{date}.log
  source_format: log
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.85
  enable_back_translation: false
Output:
  logs/daily-summary-{date}-ko.log
```

**Task Management**: Create subtask "Translate daily summary"

**Error Handling**: Non-critical, continue if fails

---

### Step 3.4: Final Approval (Required)

**Type**: Human checkpoint (blocking)

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "reports/daily/environmental-scan-{date}.md exists (EN report)"
    on_fail: HALT (nothing to approve)
  - check: "reports/daily/environmental-scan-{date}-ko.md exists (KR report)"
    on_fail: WARN (present EN-only with note about missing KR)
  - check: "Step 3.3 recorded as VERIFIED in verification-report"
    on_fail: HALT (archive must complete before approval)
  - check: "signals/database.json was updated (Step 3.1 VERIFIED)"
    on_fail: HALT
```

#### ② EXECUTE (기존 로직)

**TASK UPDATE - BEFORE USER APPROVAL** (Optional, enables Ctrl+T visibility):

1. Read workflow-status.json and get task_mapping["3.4"]
2. If exists: Use TaskUpdate tool with:
   - taskId: (from step 1)
   - status: "in_progress"
   NOTE: User will see "Awaiting final approval" when pressing Ctrl+T
3. If fails: Continue without error

**Action**: Display full report and wait for user command

Output to user:
```
📊 환경스캐닝 보고서가 생성되었습니다 (이중 언어)
   Environmental Scanning Reports Generated (Bilingual)

📄 한국어 보고서 / Korean Report:
   reports/daily/environmental-scan-{date}-ko.md
   번역 품질 / Translation quality: 0.96

📄 English Report:
   reports/daily/environmental-scan-{date}.md

신규 신호 / New signals: {count}개
우선순위 상위 5개 / Top 5 Priority:
1. [T] {signal_title_1_kr} / {signal_title_1_en}
2. [P] {signal_title_2_kr} / {signal_title_2_en}
3. [E] {signal_title_3_kr} / {signal_title_3_en}
4. [T] {signal_title_4_kr} / {signal_title_4_en}
5. [S] {signal_title_5_kr} / {signal_title_5_en}

다음 명령으로 최종 승인해주세요 / Approve with:
- /approve : 보고서 승인 및 완료 / Accept and complete
- /revision "피드백" : 보고서 수정 요청 / Request changes

💡 팁: 한국어 보고서가 기본 표시됩니다
   Tip: Korean report shown by default
```

**Wait for user command**:
- If `/approve`: Mark workflow complete, generate metrics, exit
- If `/revision "feedback"`:
  - Log feedback
  - Re-invoke @report-generator with feedback instructions
  - Return to Step 3.2 via **Revision Loop Protocol** (see below)
  - Max revisions: 3

#### Revision Loop Protocol (VEV)

When `/revision "feedback"` triggers a loop-back to Step 3.2:

```yaml
Revision_Loop:
  trigger: "/revision" command at Step 3.4
  max_revisions: 3
  revision_counter: incremented in workflow-status.json (revision_count field)

  Re-Execution_Scope:
    - Step 3.2:  Full VEV cycle (PRE-VERIFY → EXECUTE → POST-VERIFY → RECORD)
    - Step 3.2b: Full translation re-execution (KR report regenerated)
    - Step 3.3:  Full VEV cycle (re-archive revised report)
    - Step 3.4:  Return to user for re-approval

  Verification_Report_Handling:
    # Append revision-indexed records, do NOT overwrite originals
    record_key_format: "{step_id}_rev{N}"  # e.g., "3.2_rev1", "3.3_rev1"
    total_execution_count: increment for each re-execution
    original_record: preserved as-is (e.g., "3.2" remains)
    revision_records: appended (e.g., "3.2_rev1", "3.2_rev2")

  Pipeline_Gate_3:
    action: Re-run after revised Step 3.3 completes
    record_key: "gate_3_rev{N}"  # Appended, original "gate_3" preserved

  On_Max_Revisions_Exceeded:
    action: WARN — "최대 수정 횟수(3회)에 도달했습니다. 현재 보고서를 승인하거나 워크플로우를 중단하세요."
    options: ["/approve (강제 승인)", "HALT (워크플로우 중단)"]
```

**TASK UPDATE - AFTER USER APPROVAL** (Optional, non-critical):

1. Read workflow-status.json and get task_mapping["3.4"]
2. If exists: Use TaskUpdate tool (taskId from step 1, status: "completed")
3. If fails: Continue without error

#### ③ POST-VERIFY (Human Checkpoint)

```yaml
Post-Verification (Layer 1 + Layer 2):
  Layer_1_Structural:
    - check: "User decision recorded (approve or revision)"
      on_fail: HALT (cannot proceed without human decision)
    - check: "workflow-status.json updated with Step 3.4 in completed_steps (only if /approve)"
      on_fail: RETRY (update workflow-status.json)

  Layer_2_Functional:
    - check: "If /revision issued, revision count ≤ 3 (max_revisions)"
      on_fail: WARN (force final approval after 3 revisions)
    - check: "If /approve issued, end_time recorded in workflow-status.json"
      on_fail: RETRY (record end_time)
```

#### ④ RETRY

If `/revision`: See **Revision Loop Protocol** above (Steps 3.2→3.2b→3.3→3.4 re-execute with full VEV). Max revisions: 3.
For POST-VERIFY failures: See `on_fail` actions in POST-VERIFY checks. Max retries: 2.

#### ⑤ RECORD

```yaml
Record to verification-report-{date}.json:
  step_id: "3.4"
  step_name: "Final Approval"
  verification_type: "human_checkpoint"
  pre_verification:
    status: "PASS|FAIL"
    checks: [list of passed PRE-VERIFY checks]
    timestamp: "{ISO8601}"
  post_verification:
    layer_1_structural: { status: "PASS|FAIL", details: "..." }
    layer_2_functional: { status: "PASS|FAIL", details: "..." }
    layer_3_quality: null  # Human checkpoint: no quality layer
  retry_count: 0
  final_status: "VERIFIED"  # or "WARN_ACCEPTED"
  user_decision: "approve"  # or "revision"
  revision_count: 0  # 0 if approved first time
  timestamp: "{ISO8601}"

Update workflow-status.json verification_results:
  total_checks += (pre_checks + post_checks)
  passed += (passed_count)
  warned += (warned_count)
```

**━━━ PIPELINE GATE 3: Phase 3 완료 검증 ━━━**

After Step 3.4 approval, execute Pipeline Gate 3 before generating final metrics:

```yaml
Pipeline_Gate_3_Checks:
  1_database_updated:
    check: "Signal count in updated DB = backup count + new classified signals count"
    purpose: "Database update integrity"
    on_fail: WARN (DB already committed, log discrepancy)

  2_report_complete:
    check: "EN report exists with all 6 sections + KR report exists"
    purpose: "Complete bilingual deliverable"
    on_fail: WARN (if KR missing, log; EN must exist)

  3_archive_stored:
    check: "reports/archive/{year}/{month}/ contains report copies"
    purpose: "Long-term storage integrity"
    on_fail: WARN (attempt re-archive)

  4_snapshot_created:
    check: "signals/snapshots/database-{date}.json exists"
    purpose: "Recovery point available"
    on_fail: WARN (create snapshot now if missing)

  5_all_steps_verified:
    check: "Core steps (1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3) have verification records; conditional steps (1.5, 2.4) have VERIFIED or SKIPPED; human checkpoints (1.4, 2.5, 3.4) have verification records"
    purpose: "Complete verification trail"
    on_fail: WARN (log which steps lack verification — conditional steps marked SKIPPED are acceptable)

  6_human_approvals_complete:
    check: "Step 2.5 and Step 3.4 approval decisions recorded"
    purpose: "Human oversight verification"
    on_fail: WARN
```

**Gate Result**:
- ALL checks PASS → Record "Pipeline_Gate_3: PASS", proceed to metrics
- Any WARN → Record warnings, proceed (Phase 3 is past point of no return for DB)
- Critical FAIL (e.g., DB not updated) → Log error, ask user

**Finalize workflow-status.json**:
```json
{
  "current_phase": 3,
  "completed_steps": ["1.1", ..., "3.1", "3.2", "3.3", "3.4"],
  "status": "completed",
  "end_time": "{ISO8601}",
  "phase_3_metrics": {
    "report_generated": true,
    "archive_path": "reports/archive/2026/01/environmental-scan-2026-01-29.md",
    "total_signals_in_db": 1014
  }
}
```

**TASK UPDATE - WORKFLOW COMPLETION** (Optional, finalizes Task system):

After quality metrics generation and performance analysis (Steps 3.5, 3.6) are complete:

1. Read workflow-status.json
2. If task_mapping exists and is not empty:
   a. Mark all remaining Phase 3 sub-tasks as completed:
      - TaskUpdate(taskId: task_mapping["3.5a"], status: "completed")
      - TaskUpdate(taskId: task_mapping["3.5b"], status: "completed")
      - TaskUpdate(taskId: task_mapping["3.5c"], status: "completed")
      - TaskUpdate(taskId: task_mapping["3.6a"], status: "completed")
      - TaskUpdate(taskId: task_mapping["3.6b"], status: "completed")
      - TaskUpdate(taskId: task_mapping["3.6c"], status: "completed")
      - TaskUpdate(taskId: task_mapping["PG3"], status: "completed")
   b. Mark Phase 3 as completed:
      - TaskUpdate(taskId: task_mapping["phase3"], status: "completed")
   c. Ensure Phase 1 is marked completed (if not already):
      - TaskUpdate(taskId: task_mapping["phase1"], status: "completed")
   d. Display to user:
      "\n✅ Workflow 완료 (Workflow Complete)"
      "📊 전체 작업 히스토리 확인 / View full task history: Press Ctrl+T\n"
3. If task_mapping is empty or any TaskUpdate fails: Continue without error

NOTE: Task system is optional - workflow completion does not depend on it.

---

## Quality Metrics Generation (Step 3.5)

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "Pipeline Gate 3 recorded as PASS (or WARN_ACCEPTED) in verification-report"
    on_fail: HALT (Gate 3 must pass before metrics generation)
  - check: "Step 3.4 user approval recorded (not revision-pending)"
    on_fail: HALT (metrics only generated after final approval)
  - check: "verification-report-{date}.json exists and is valid JSON"
    on_fail: WARN (generate metrics without verification summary)
  - check: "workflow-status.json has status = 'completed'"
    on_fail: WARN (generate metrics but flag incomplete status)
```

#### ② EXECUTE (기존 로직)

After workflow completion, generate:

**File**: `logs/quality-metrics/workflow-{date}.json`

```json
{
  "workflow_id": "scan-{date}",
  "execution_time_seconds": 180,
  "phase_times": {
    "phase_1": 60,
    "phase_2": 80,
    "phase_3": 40
  },
  "agent_performance": {
    "archive-loader": {"time": 5, "status": "success"},
    "multi-source-scanner": {"time": 45, "status": "success"},
    "deduplication-filter": {"time": 10, "status": "success"},
    "signal-classifier": {"time": 50, "status": "success"},
    "impact-analyzer": {"time": 20, "status": "success"},
    "priority-ranker": {"time": 5, "status": "success"},
    "database-updater": {"time": 3, "status": "success", "critical": true},
    "report-generator": {"time": 30, "status": "success"},
    "archive-notifier": {"time": 2, "status": "success"}
  },
  "quality_scores": {
    "dedup_accuracy": 0.96,
    "classification_accuracy": 0.94,
    "human_ai_agreement": 0.88
  },
  "errors": [],
  "retries": 0,
  "human_interventions": 2,
  "signals_processed": {
    "collected": 247,
    "filtered": 79,
    "classified": 79,
    "archived": 79
  },
  "performance_targets": {
    "dedup_accuracy": {"target": 0.95, "actual": 0.96, "pass": true},
    "processing_time": {"target": 300, "actual": 180, "pass": true}
  },
  "translation_summary": {
    "total_translations": 11,
    "average_confidence": 0.95,
    "average_back_translation_similarity": 0.93,
    "steep_violations": 0,
    "total_translation_time": 42
  },
  "verification_summary": {
    "vev_protocol_version": "2.2.0",
    "total_checks": 42,
    "passed": 40,
    "warned": 2,
    "failed": 0,
    "retries_triggered": 1,
    "total_retry_executions": 1,
    "pipeline_gates": {
      "gate_1": "PASS",
      "gate_2": "PASS",
      "gate_3": "PASS"
    },
    "critical_step_status": {
      "3.1_database_update": "VERIFIED"
    },
    "steps_verified": ["1.1", "1.2", "1.3", "1.4", "1.5|SKIPPED", "2.1", "2.2", "2.3", "2.4|SKIPPED", "2.5", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6"],
    "overall_verification_status": "ALL_VERIFIED",
    "verification_report_path": "{data_root}/logs/verification-report-{date}.json"
  }
}
```

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Post-Verification:
  Layer_1_Structural:
    - check: "logs/quality-metrics/workflow-{date}.json exists"
      on_fail: RETRY
    - check: "File is valid JSON with required keys: workflow_id, agent_performance, quality_scores, verification_summary"
      on_fail: RETRY

  Layer_2_Functional:
    - check: "signals_processed counts are consistent (collected ≥ filtered ≥ classified)"
      on_fail: WARN (log discrepancy in metrics)
    - check: "verification_summary.total_checks = passed + warned + failed"
      on_fail: RETRY (re-aggregate from verification-report)
    - check: "verification_summary.steps_verified includes all 16 steps: core agent steps (1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.5, 3.6), human checkpoints (1.4, 2.5, 3.4), and conditional steps (1.5, 2.4 as VERIFIED or SKIPPED)"
      on_fail: WARN (update steps_verified from verification-report)
    - check: "pipeline_gates has entries for gate_1, gate_2, gate_3"
      on_fail: WARN (fill from verification-report)

  Layer_3_Quality:
    - check: "performance_targets all evaluated (each has target, actual, pass)"
      pattern: "C"  # Silent warn — this is the final step
    - check: "verification_summary matches actual data in verification-report-{date}.json"
      pattern: "C"  # Silent warn
```

#### ④ RETRY (실패 시)

Layer 1/2 failures → max 2 retries. On exhaustion → generate partial metrics with `"metrics_status": "PARTIAL"` flag and log warning. This is the final step — workflow does not halt on metrics failure.

#### ⑤ RECORD (검증 결과 기록)

```yaml
Record to verification-report-{date}.json:
  step_id: "3.5"
  step_name: "Quality Metrics Generation"
  pre_verify:
    checks_passed: [list]
    all_passed: true/false
  post_verify:
    layer_1: { passed: true/false, details: "..." }
    layer_2: { passed: true/false, details: "..." }
    layer_3: { passed: true/false, details: "..." }
  retry_count: 0
  final_status: "VERIFIED"
  timestamp: "{ISO8601}"

Finalize verification-report-{date}.json:
  Set overall_status to:
    - "ALL_VERIFIED" if all steps VERIFIED or SKIPPED
    - "VERIFIED_WITH_WARNINGS" if any WARN_ACCEPTED
    - "PARTIAL" if any step FAILED

Update workflow-status.json verification_results:
  total_checks += (pre_checks + post_checks)
  passed += (passed_count)
  warned += (warned_count)
  overall_status: (copy from verification-report overall_status)
```

---

### Quality Metrics Translation (Final Step)

**After quality metrics generated**, translate to Korean:

**Invoke**: Task tool with `@translation-agent`

```yaml
Agent: translation-agent
Input:
  source_file: logs/quality-metrics/workflow-{date}.json
  source_format: json
  terminology_map: env-scanning/config/translation-terms.yaml
  quality_threshold: 0.85
  enable_back_translation: false
Output:
  logs/quality-metrics/workflow-{date}-ko.json
```

**Task Management**: Final translation subtask

**This completes all translations for the workflow run.**

---

## Self-Improvement Analysis (Step 3.6) 🆕

> **Design Principle**: "Improve the tuning, never break the machine"
>
> After quality metrics are generated, analyze performance and safely
> tune parameters. SIE failure NEVER halts the workflow.

#### ① PRE-VERIFY (선행 조건 확인)

```yaml
Pre-Verification Checks:
  - check: "logs/quality-metrics/workflow-{date}.json exists and is valid JSON"
    on_fail: SKIP_SIE (metrics required for analysis)
  - check: "config/core-invariants.yaml exists and is valid YAML"
    on_fail: SKIP_SIE (safety boundary file required)
  - check: "config/self-improvement-config.yaml exists"
    on_fail: SKIP_SIE (SIE config required)
  - check: "Step 3.5 recorded as VERIFIED in verification-report"
    on_fail: SKIP_SIE (only analyze verified metrics)
  - check: "self-improvement/improvement-log.json exists (create if first run)"
    on_fail: CREATE_DEFAULT (initialize empty log structure)
```

#### ② EXECUTE (자기개선 분석)

**Invoke**: Task tool with `@self-improvement-analyzer`

```yaml
Agent: self-improvement-analyzer
Input:
  current_metrics: logs/quality-metrics/workflow-{date}.json
  core_invariants: config/core-invariants.yaml
  sie_config: config/self-improvement-config.yaml
  thresholds: config/thresholds.yaml
  improvement_log: self-improvement/improvement-log.json
Output:
  status: completed | disabled | insufficient_history | error
  applied_changes: [list of MINOR auto-applied]
  pending_proposals: [list of MAJOR for user review]
  blocked_attempts: [list of CRITICAL blocked]
```

**Analysis Areas** (5):
1. **Threshold Tuning** — dedup/confidence thresholds based on accuracy metrics
2. **Agent Performance** — timeout/retry adjustments based on execution data
3. **Classification Quality** — confidence thresholds based on accuracy trends
4. **Workflow Efficiency** — bottleneck identification and timing suggestions
5. **Hallucination Tracking** — verification strictness based on warning trends

**Change Execution Rules**:
- **MINOR** (tunable parameters, within ±10%): Auto-apply after validation against `core-invariants.yaml`. Max 3 per cycle.
- **MAJOR** (behavioral changes): Save to `self-improvement/proposals/` and prompt user via AskUserQuestion (Korean-first):
  ```
  📊 자기개선 엔진: 주요 변경 제안 (SIE: Major Change Proposal)

  카테고리: {category}
  제안: {summary}
  근거: {evidence}

  승인하시겠습니까? (Approve this change?)
  ```
  - If approved → apply and log
  - If rejected → log rejection with user's reason
- **CRITICAL** (core invariant violation): Block immediately. No user prompt. Log as `blocked_critical`.

#### ③ POST-VERIFY (3-Layer 사후 검증)

```yaml
Post-Verification:
  Layer_1_Structural:
    - check: "self-improvement/improvement-log.json exists and is valid JSON"
      on_fail: WARN (log failure does not halt workflow)
    - check: "improvement-log has required keys: version, improvements, stats"
      on_fail: WARN

  Layer_2_Functional:
    - check: "No core invariant was violated (cross-check applied changes against core-invariants.yaml)"
      on_fail: ROLLBACK_all_changes_this_cycle
    - check: "Applied change count ≤ max_minor_changes_per_cycle (3)"
      on_fail: ROLLBACK_excess_changes
    - check: "All modified config files remain valid (can be parsed without error)"
      on_fail: ROLLBACK_all_changes_this_cycle

  Layer_3_Quality:
    - check: "Each applied change has evidence with sample_size ≥ min_evidence_sample_size"
      pattern: "C"  # Silent warn — SIE is advisory, not critical
    - check: "No threshold changed beyond max_threshold_delta_percent (10%)"
      pattern: "C"
```

#### ④ RETRY (실패 시)

SIE does NOT retry on failure. If any step fails:
- ROLLBACK all changes applied this cycle
- Log failure to `improvement-log.json` with `"status": "cycle_failed"`
- Continue workflow normally — SIE failure never halts the main workflow

```yaml
On_Fail:
  action: ROLLBACK_all_changes_this_cycle
  log: "SIE cycle failed — all changes reverted"
  continue: true  # SIE failure NEVER halts workflow
```

#### ⑤ RECORD (검증 결과 기록)

```yaml
Record to verification-report-{date}.json:
  step_id: "3.6"
  step_name: "Self-Improvement Analysis"
  pre_verify:
    checks_passed: [list]
    all_passed: true/false
  post_verify:
    layer_1: { passed: true/false, details: "..." }
    layer_2: { passed: true/false, details: "..." }
    layer_3: { passed: true/false, details: "..." }
  sie_results:
    applied_count: N
    proposed_count: N
    blocked_count: N
  retry_count: 0
  final_status: "VERIFIED" | "SKIPPED" | "WARN_ACCEPTED"
  timestamp: "{ISO8601}"

Update workflow-status.json:
  Add "3.6" to steps_verified list
  Update verification_results counts

Update improvement-log.json:
  All applied/proposed/blocked changes recorded with evidence
```

**Task Management**: Create subtask under Phase 3:
```
Step 3.6: Self-Improvement Analysis (자기개선 분석)
```

---

## Error Handling Strategy

### Retry Logic

> **Note**: This section describes the **agent-level** retry logic (network/invocation errors). For **VEV post-verification** retry logic (output quality/integrity), see the **Task Verification Protocol (VEV)** section (max_retries: 2, delays: 2s, 4s).

For each agent invocation:

1. **Attempt 1**: Execute normally
2. **If failure**: Wait 2 seconds, retry (attempt 2)
3. **If failure again**: Wait 4 seconds, retry (attempt 3)
4. **If 3 attempts (1 original + 2 retries) exhausted**:
   - If step is `critical: true`: RESTORE_AND_HALT (see Named Actions in VEV Protocol)
   - If step is non-critical: HALT_and_ask_user

### Error Logging

Log to: `{data_root}/logs/errors-{date}.log`

Format:
```
[2026-01-29T06:15:23Z] ERROR E3000: Deduplication failed
Agent: @deduplication-filter
Attempt: 2/3 (1 original + 2 max retries)
Error: JSONDecodeError - File corrupted
Recovery: Restored from backup, retrying
VEV_Status: Layer_1_FAIL → RETRY triggered
```

### Critical Failure Response

If critical step fails (e.g., database-updater):

1. Log error with code (E7000)
2. Update workflow-status.json: `"status": "failed"`
3. Send user notification via output
4. Provide recovery instructions
5. HALT - do not proceed

---

## Communication Protocol

### Internal (Agent-to-Agent)
- All agent instructions: **English**
- Prompts and system messages: **English**
- Log messages: **English**
- All output files: **English (primary)** + **Korean (translated pair)**

### External (User-facing)
- Reports display: **Korean by default** (English available)
- User notifications: **Korean** (with English file references)
- AskUserQuestion prompts: **Korean**
- Human checkpoints: **Korean-first** bilingual display

### Bilingual Workflow
- **Primary language**: English (for optimal AI performance)
- **Translation layer**: Automatic Korean translation after each output
- **File naming**: Original file + `-ko` suffix for Korean (e.g., `report.md` + `report-ko.md`)
- **Exception**: `database.json` remains **English-only** (data integrity)

---

## Translation Integration Protocol

### Overview

After each step that produces human-readable output, automatically invoke `@translation-agent` to create Korean translation.

**Execution Pattern**:
```
Worker Agent → EN Output → Verify EN → Translate to KR → Verify KR → Continue
```

### Translation Trigger Points

**Phase 1: Research**

After **Step 1.2 (Collection)**:
```yaml
Source: raw/daily-scan-{date}.json
Target: raw/daily-scan-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical (continue if fails)
```

After **Step 1.2 (Classification)**:
```yaml
Source: structured/classified-signals-{date}.json
Target: structured/classified-signals-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical
```

After **Step 1.3**:
```yaml
Source: filtered/new-signals-{date}.json
Target: filtered/new-signals-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical

Source: logs/duplicates-removed-{date}.log
Target: logs/duplicates-removed-{date}-ko.log
Invoke: @translation-agent
Priority: Non-critical
```

**Phase 2: Planning**

After **Step 2.1** (if executed):
```yaml
Source: logs/classification-quality-{date}.json
Target: logs/classification-quality-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical
```

After **Step 2.2**:
```yaml
Source: analysis/impact-assessment-{date}.json
Target: analysis/impact-assessment-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical
```

After **Step 2.3**:
```yaml
Source: analysis/priority-ranked-{date}.json
Target: analysis/priority-ranked-{date}-ko.json
Invoke: @translation-agent
Priority: High (used in human review)
```

After **Step 2.4** (if activated):
```yaml
Source: scenarios/scenarios-{date}.json
Target: scenarios/scenarios-{date}-ko.json
Invoke: @translation-agent
Priority: High
```

**Phase 3: Implementation**

After **Step 3.2**:
```yaml
Source: reports/daily/environmental-scan-{date}.md
Target: reports/daily/environmental-scan-{date}-ko.md
Invoke: @translation-agent
Priority: CRITICAL (main deliverable)
Quality: Enable back-translation check
```

After **Step 3.3**:
```yaml
Source: logs/daily-summary-{date}.log
Target: logs/daily-summary-{date}-ko.log
Invoke: @translation-agent
Priority: Non-critical
```

**Final Metrics**:
```yaml
Source: logs/quality-metrics/workflow-{date}.json
Target: logs/quality-metrics/workflow-{date}-ko.json
Invoke: @translation-agent
Priority: Non-critical
```

### Translation Invocation Template

For each translation trigger point, execute:

```yaml
1. Verify source file exists and is valid
2. Invoke @translation-agent with parameters:
   {
     "source_file": "{path}",
     "output_file": "{path-with-ko-suffix}",
     "source_format": "json|markdown|log",
     "terminology_map": "env-scanning/config/translation-terms.yaml",
     "quality_threshold": 0.90,
     "enable_back_translation": true  # For critical files
   }
3. Wait for translation completion (max 10s timeout)
4. Verify KR file created
5. Log translation metadata to shared context
6. Continue workflow (even if translation failed)
```

### Translation Quality Verification

After each translation:

```yaml
Verify:
  - [ ] KR file exists at expected path
  - [ ] KR file format matches EN format (JSON valid, Markdown renders)
  - [ ] STEEPs terms preserved exactly (S, T, E, E, P, s unchanged)
  - [ ] File size reasonable (KR typically 1.2-1.5x EN size)
  - [ ] Translation metadata present in output

Update shared context:
  - Add to translation_status.translations_completed array
  - Record quality metrics
  - Log any errors to translation_status.translation_errors
```

### Translation Error Handling

**Non-Critical Translation Failure** (default):
```yaml
If translation fails:
  - Log warning to {data_root}/logs/translation-errors-{date}.log
  - Add error to shared context translation_status.translation_errors
  - Continue workflow with EN-only output
  - Do NOT halt workflow
```

**Critical Translation Failure** (Step 3.2 report only):
```yaml
If report translation fails after 3 retries:
  - Generate warning message to user
  - Provide EN report with note about KR translation failure
  - Continue to Step 3.4 approval
  - User can request manual translation or approve EN version
```

### Translation Performance Tracking

Track in shared context:

```json
"translation_status": {
  "average_translation_time": 3.2,  // seconds
  "total_translation_overhead": 35.2,  // seconds total
  "translations_completed": [...],
  "en_kr_pairs_verified": 11,
  "steep_violations": 0,
  "schema_match_failures": 0
}
```

### Phase Integration Tests → Pipeline Gates (v2.2.0)

**NOTE**: Phase Integration Tests have been superseded by **Pipeline Gates** (see "Task Verification Protocol (VEV)" section). The Pipeline Gates provide:
- Formal data continuity checks between phases
- Automated trace-back on failure
- Re-execution enforcement
- Verification report recording

The following are now enforced via Pipeline Gates:

**Pipeline Gate 1** (Phase 1 → Phase 2):
- Signal ID continuity (raw → filtered)
- Classification completeness
- Shared context population
- EN-KR file pair verification
- Data flow integrity

**Pipeline Gate 2** (Phase 2 → Phase 3):
- Signal count consistency across analysis chain
- Score range validation
- Human approval verification
- Analysis chain completeness
- STEEPs category consistency
- Bilingual pair verification

**Pipeline Gate 3** (Phase 3 completion):
- Database update verification
- Report completeness (EN + KR)
- Archive storage verification
- Snapshot creation
- Complete verification trail
- Human approval record

All Gate results are recorded in `verification-report-{date}.json` and summarized in quality metrics.

---

## Performance Targets

Based on Enhanced Workflow v1.0 + Bilingual Enhancement:

- **Duplicate detection accuracy**: > 95%
- **Processing time reduction**: 30% vs baseline (EN-only workflow)
- **Signal detection speed**: 2x vs manual
- **Expert feedback time**: < 3 days (if Phase 1.5 activated)
- **Translation quality**: > 0.90 average confidence
- **Translation overhead**: < 25% additional time (~40s per full workflow)
- **STEEPs terminology accuracy**: 100% (zero violations)

---

## Task Management Integration

Throughout execution:

1. **Create hierarchical tasks** at workflow start (including translation subtasks):
   - Phase 1: Research
     - Step 1.1: Load archive
     - Step 1.2a: Scan sources (EN)
     - Step 1.2b: Translate scan results (KR)
     - Step 1.2c: Classify signals (EN)
     - Step 1.2d: Translate classifications (KR)
     - Step 1.3a: Filter duplicates (EN)
     - Step 1.3b: Translate filter results (KR)
     - Step 1.4: Human review (bilingual display)
     - Step 1.5: Expert validation (conditional)
   - Phase 2: Planning
     - Step 2.1a: Verify classifications (EN)
     - Step 2.1b: Translate verification (KR)
     - Step 2.2a: Analyze impacts (EN)
     - Step 2.2b: Translate impact analysis (KR)
     - Step 2.3a: Rank priorities (EN)
     - Step 2.3b: Translate rankings (KR)
     - Step 2.4a: Build scenarios (conditional, EN)
     - Step 2.4b: Translate scenarios (conditional, KR)
     - Step 2.5: Human review (bilingual display)
   - Phase 3: Implementation
     - Step 3.1: Update database (EN-only)
     - Step 3.2a: Generate report (EN)
     - Step 3.2b: Translate report (KR)
     - Step 3.3a: Archive and notify
     - Step 3.3b: Translate summary (KR)
     - Step 3.4: Final approval (bilingual display)
     - Step 3.5a: Generate quality metrics (EN)
     - Step 3.5b: Translate metrics (KR)
     - Step 3.6: Self-Improvement Analysis (자기개선 분석)

2. **Update task statuses**:
   - `pending` → `in_progress` when starting
   - `in_progress` → `completed` when verified (both EN and KR if applicable)
   - `in_progress` → `blocked` when awaiting human input
   - Translation tasks: Mark completed even if translation fails (non-critical)

3. **Use TaskCreate and TaskUpdate** tools throughout

4. **Translation task tracking**:
   - Each translation subtask tracks: source_file, target_file, quality_score
   - Failed translations logged but don't block parent task completion

---

## Dependencies

### Required Tools
- Task (for agent invocation)
- TaskCreate, TaskUpdate (for task management)
- AskUserQuestion (for human checkpoints)
- Read, Write (for file operations)
- Glob (for finding files)

### Required Sub-Agents
- @archive-loader
- @multi-source-scanner
- @deduplication-filter
- @signal-classifier
- @impact-analyzer
- @priority-ranker
- @database-updater
- @report-generator
- @archive-notifier
- @translation-agent (bilingual workflow)
- @self-improvement-analyzer (Step 3.6 — self-tuning)
- @realtime-delphi-facilitator (optional)
- @scenario-builder (optional)

### Configuration Files
- `env-scanning/config/domains.yaml`
- `env-scanning/config/sources.yaml`
- `env-scanning/config/thresholds.yaml`
- `env-scanning/config/ml-models.yaml`
- `env-scanning/config/translation-terms.yaml` (bilingual workflow)
- `env-scanning/config/core-invariants.yaml` (SIE safety boundaries)
- `env-scanning/config/self-improvement-config.yaml` (SIE behavior)

---

## Version
- **Orchestrator Version**: 3.1.0 (VEV + SIE + Marathon Mode Default)
- **Compatible with**: Enhanced Environmental Scanning Workflow v1.0
- **Translation Layer**: Enabled (EN-first, auto-KR translation)
- **Verification Protocol**: VEV (Verify-Execute-Verify) with 3-Layer Post-Verification + Pipeline Gates
- **Self-Improvement Engine**: v1.0.0 (Step 3.6 — autonomous parameter tuning)
- **Last Updated**: 2026-01-31

---

## Implementation Notes

- This orchestrator uses Claude Code's Task tool to invoke worker agents
- All worker agents must be in `.claude/agents/workers/` directory
- State persistence in `workflow-status.json` enables recovery from interruptions
- The orchestrator itself is stateless - all state persisted to files
- Human checkpoints use AskUserQuestion for interactive review
- Slash commands (/approve, /revision) are handled through user input
