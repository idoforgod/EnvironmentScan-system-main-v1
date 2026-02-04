# Task Management System Integration Guide

## Overview

This document describes how the new Claude Code Task Management System integrates with the Environmental Scanning workflow while preserving all existing philosophy and structure.

## Design Principles

1. **Philosophy Preservation**: Maintain 3-phase sequential structure, Human checkpoints, STEEPs framework
2. **Non-invasive**: Keep workflow-status.json unchanged, add Task system alongside
3. **Single Session**: Sequential execution within one session (no parallel cross-session work)
4. **User Visibility**: Task system provides real-time progress to user via `Ctrl+T`

## Dual-State Architecture

### workflow-status.json (Workflow Metadata)
- **Purpose**: Record what has been completed, decisions made, errors encountered
- **Lifecycle**: Created at workflow start, updated at phase transitions
- **Location**: `env-scanning/logs/workflow-status.json`
- **Content**: Phase/step completion, human decisions, artifacts, errors

### Task System (Progress Tracking)
- **Purpose**: Show current progress, enable user monitoring via `Ctrl+T`
- **Lifecycle**: Created at workflow start, updated at every step
- **Location**: `~/.claude/tasks/[TASK_LIST_ID]/`
- **Content**: Task status (pending/in_progress/completed), dependencies, timing

## Task Hierarchy

### Level 1: Phases (3 main tasks)

```
Task 1: "Phase 1: Research - Collect and filter signals"
  activeForm: "Executing Phase 1 (Research)"
  status: pending → in_progress → completed
  blockedBy: []

Task 2: "Phase 2: Planning - Analyze and structure signals"
  activeForm: "Executing Phase 2 (Planning)"
  status: pending
  blockedBy: [1]  # Cannot start until Phase 1 complete

Task 3: "Phase 3: Implementation - Generate and archive report"
  activeForm: "Executing Phase 3 (Implementation)"
  status: pending
  blockedBy: [2]  # Cannot start until Phase 2 complete
```

### Level 2: Steps (detailed sub-tasks)

**Phase 1 Steps:**
```
Task 1.1: "Step 1.1: Load historical signals database"
  activeForm: "Loading archive"
  blockedBy: []

Task 1.2: "Step 1.2: Scan sources and classify signals"
  activeForm: "Scanning and classifying"
  blockedBy: [1.1]

Task 1.3: "Step 1.3: Filter duplicate signals"
  activeForm: "Filtering duplicates"
  blockedBy: [1.2]

Task 1.4: "Step 1.4: Human review of filtering (optional)"
  activeForm: "Awaiting human review"
  blockedBy: [1.3]
  metadata: { checkpoint: true, required: false }

Task 1.5: "Step 1.5: Expert panel validation (conditional)"
  activeForm: "Expert validation in progress"
  blockedBy: [1.4]
  metadata: { conditional: true }
```

**Phase 2 Steps:**
```
Task 2.1: "Step 2.1: Verify classification quality"
  activeForm: "Verifying classifications"
  blockedBy: [1]  # Blocked by entire Phase 1

Task 2.2: "Step 2.2: Analyze impacts and cross-influences"
  activeForm: "Analyzing impacts"
  blockedBy: [2.1]

Task 2.3: "Step 2.3: Rank signals by priority"
  activeForm: "Ranking priorities"
  blockedBy: [2.2]

Task 2.4: "Step 2.4: Generate scenarios (conditional)"
  activeForm: "Building scenarios"
  blockedBy: [2.3]
  metadata: { conditional: true }

Task 2.5: "Step 2.5: Human review of analysis (required)"
  activeForm: "Awaiting human review"
  blockedBy: [2.4]
  metadata: { checkpoint: true, required: true }
```

**Phase 3 Steps:**
```
Task 3.1: "Step 3.1: Update master signals database"
  activeForm: "Updating database"
  blockedBy: [2]  # Blocked by entire Phase 2
  metadata: { critical: true }

Task 3.2: "Step 3.2: Generate bilingual report"
  activeForm: "Generating report"
  blockedBy: [3.1]

Task 3.3: "Step 3.3: Archive report and send notifications"
  activeForm: "Archiving and notifying"
  blockedBy: [3.2]

Task 3.4: "Step 3.4: Final approval (required)"
  activeForm: "Awaiting final approval"
  blockedBy: [3.3]
  metadata: { checkpoint: true, required: true }

Task 3.5: "Step 3.5: Generate quality metrics"
  activeForm: "Generating metrics"
  blockedBy: [3.4]
```

## Orchestrator Integration Points

### Workflow Initialization

**Location**: Orchestrator start, before Phase 1

```python
# 1. Create workflow state (existing)
create_workflow_status_json()

# 2. Generate unique Task List ID (NEW)
task_list_id = f"env-scan-{date}"
add_to_workflow_status("task_list_id", task_list_id)

# 3. Create Task hierarchy (NEW)
create_task_hierarchy(task_list_id)
```

### Task Hierarchy Creation

**Pseudo-code:**

```python
def create_task_hierarchy(task_list_id):
    # Phase 1 Main Task
    task1 = TaskCreate(
        subject="Phase 1: Research - Collect and filter signals",
        description="Scan sources, classify signals, filter duplicates",
        activeForm="Executing Phase 1 (Research)",
        metadata={"phase": 1, "task_list_id": task_list_id}
    )

    # Phase 1 Sub-tasks
    task1_1 = TaskCreate(
        subject="Step 1.1: Load historical signals database",
        description="Load archive files and previous signals for deduplication",
        activeForm="Loading archive"
    )
    TaskUpdate(task1_1.id, addBlockedBy=[])  # No dependencies

    task1_2 = TaskCreate(
        subject="Step 1.2: Scan sources and classify signals",
        description="Execute multi-source scanner and direct classification",
        activeForm="Scanning and classifying"
    )
    TaskUpdate(task1_2.id, addBlockedBy=[task1_1.id])

    task1_3 = TaskCreate(
        subject="Step 1.3: Filter duplicate signals",
        description="4-stage deduplication: URL → String → Semantic → Entity",
        activeForm="Filtering duplicates"
    )
    TaskUpdate(task1_3.id, addBlockedBy=[task1_2.id])

    task1_4 = TaskCreate(
        subject="Step 1.4: Human review of filtering (optional)",
        description="Review duplicate removal if confidence < 0.9",
        activeForm="Awaiting human review",
        metadata={"checkpoint": True, "required": False}
    )
    TaskUpdate(task1_4.id, addBlockedBy=[task1_3.id])

    task1_5 = TaskCreate(
        subject="Step 1.5: Expert panel validation (conditional)",
        description="RT-AID expert validation if signals > 50",
        activeForm="Expert validation in progress",
        metadata={"conditional": True}
    )
    TaskUpdate(task1_5.id, addBlockedBy=[task1_4.id])

    # Phase 2 Main Task (blocked by Phase 1)
    task2 = TaskCreate(
        subject="Phase 2: Planning - Analyze and structure signals",
        description="Classify, analyze impacts, rank priorities",
        activeForm="Executing Phase 2 (Planning)",
        metadata={"phase": 2}
    )
    TaskUpdate(task2.id, addBlockedBy=[task1.id])

    # Phase 2 Sub-tasks...
    # (Similar pattern for 2.1-2.5)

    # Phase 3 Main Task (blocked by Phase 2)
    task3 = TaskCreate(
        subject="Phase 3: Implementation - Generate and archive report",
        description="Update database, generate report, archive",
        activeForm="Executing Phase 3 (Implementation)",
        metadata={"phase": 3}
    )
    TaskUpdate(task3.id, addBlockedBy=[task2.id])

    # Phase 3 Sub-tasks...
    # (Similar pattern for 3.1-3.5)
```

### Step Execution Pattern

**For each step in workflow:**

```python
# Before executing step
task_id = get_task_id_for_step(current_step)
TaskUpdate(task_id, status="in_progress")

# Execute step (existing logic)
result = execute_step(current_step)

# After step completion
if result.success:
    TaskUpdate(task_id, status="completed")
    update_workflow_status_json(current_step, "completed")
else:
    # Handle error (existing logic)
    pass
```

### Human Checkpoint Handling

**For Step 1.4, 2.5, 3.4:**

```python
# When reaching checkpoint
task_id = get_task_id_for_step(current_step)
TaskUpdate(task_id, status="in_progress")  # Show as "Awaiting..."

# Use AskUserQuestion (existing)
user_response = AskUserQuestion(...)

# Process response
if user_approves():
    TaskUpdate(task_id, status="completed")
    update_workflow_status_json(current_step, "completed")
    log_human_decision(user_response)
else:
    # Handle revision request
    pass
```

### Conditional Step Handling

**For Step 1.5 (Expert Validation) and Step 2.4 (Scenarios):**

```python
# Check condition
if should_activate_optional_step():
    # Create task if it doesn't exist
    if not task_exists(step_id):
        task = TaskCreate(
            subject=f"Step {step_id}: ...",
            description="...",
            activeForm="..."
        )

    # Execute
    TaskUpdate(task.id, status="in_progress")
    execute_step(step_id)
    TaskUpdate(task.id, status="completed")
else:
    # Skip - delete task if it was created
    if task_exists(step_id):
        TaskUpdate(task.id, status="deleted")
```

### Phase Completion

**After all steps in a phase:**

```python
# Mark phase task as completed
phase_task_id = get_task_id_for_phase(current_phase)
TaskUpdate(phase_task_id, status="completed")

# Update workflow status
update_workflow_status_json("current_phase", next_phase)
update_workflow_status_json("phase_{current_phase}_metrics", metrics)
```

### Workflow Completion

**After Phase 3 complete:**

```python
# Mark all remaining tasks as completed
TaskUpdate(task3_5.id, status="completed")  # Quality metrics
TaskUpdate(task3.id, status="completed")    # Phase 3

# Update workflow status
update_workflow_status_json("status", "completed")
update_workflow_status_json("end_time", now())

# Generate quality metrics (existing)
generate_quality_metrics()

# User can view final task list with Ctrl+T
print("✅ Workflow complete. Press Ctrl+T to view full task list.")
```

## User Experience

### Progress Monitoring

User can press **Ctrl+T** at any time to see:

```
Task List: env-scan-2026-01-30

Phase Tasks:
  [✓] Phase 1: Research - Collect and filter signals
  [▶] Phase 2: Planning - Analyze and structure signals
  [ ] Phase 3: Implementation - Generate and archive report

Current Step:
  [▶] Step 2.3: Rank signals by priority (in_progress)

Completed Steps (7):
  ✓ Step 1.1: Load historical signals database
  ✓ Step 1.2: Scan sources and classify signals
  ✓ Step 1.3: Filter duplicate signals
  ✓ Step 1.4: Human review of filtering
  ✓ Step 2.1: Verify classification quality
  ✓ Step 2.2: Analyze impacts and cross-influences

Pending Steps (6):
  ⏸ Step 2.4: Generate scenarios (conditional)
  ⏸ Step 2.5: Human review of analysis (blocked by 2.3)
  ⏸ Step 3.1: Update master signals database (blocked by Phase 2)
  ...
```

### Human Checkpoint Experience

When orchestrator reaches Step 2.5:

```
[Orchestrator marks task 2.5 as in_progress]

📊 분석이 완료되었습니다 (Analysis Complete)

Task Status: Step 2.5 - Awaiting human review
Press Ctrl+T to see full progress.

[Shows AskUserQuestion prompts as before...]
```

## Error Handling

### Task Update Failures

Task updates are **non-critical** - if TaskUpdate fails:

```python
try:
    TaskUpdate(task_id, status="completed")
except Exception as e:
    log_warning(f"Task update failed: {e}")
    # Continue - workflow-status.json is source of truth
```

### Recovery from Interruption

If workflow interrupted:

1. **workflow-status.json** shows last completed step
2. **Task system** may be out of sync
3. On resume, orchestrator can:
   - Read workflow-status.json to determine position
   - Recreate task hierarchy from current state
   - Continue execution

## Implementation Checklist

- [ ] Modify orchestrator to create Task hierarchy at start
- [ ] Add TaskUpdate calls before/after each step
- [ ] Add task_list_id to workflow-status.json
- [ ] Update Human checkpoint handlers to update Task status
- [ ] Handle conditional steps (1.5, 2.4) dynamically
- [ ] Test Task visibility with Ctrl+T during execution
- [ ] Verify blockedBy chains enforce sequential execution
- [ ] Ensure Task failures don't halt workflow

## Benefits

1. **User Visibility**: Press Ctrl+T anytime to see progress
2. **Progress Tracking**: Visual indication of current step
3. **Time Estimation**: Task timestamps show duration of each step
4. **Audit Trail**: Task history shows exact execution timeline
5. **Non-invasive**: Zero changes to existing workflow logic
6. **Failure Resilient**: Task failures don't break workflow

## Compatibility

- **Claude Code Version**: 2.1.16+
- **Task Management**: Enabled by default (can disable with CLAUDE_CODE_ENABLE_TASKS=false)
- **Existing Workflow**: 100% compatible, no breaking changes
- **Workflow Version**: Enhanced Environmental Scanning v1.0

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-30
