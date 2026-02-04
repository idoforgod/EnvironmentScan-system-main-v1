# Task Management System - Execution Guide for Orchestrator

## Purpose

This guide provides **executable instructions** for the Environmental Scanning Orchestrator to integrate Task Management System while preserving all existing workflow philosophy.

## When to Use This Guide

The orchestrator should follow these instructions when:
1. Starting a new environmental scanning workflow
2. Resuming an interrupted workflow
3. Updating progress during execution

## Integration Points

### ══════════════════════════════════════════════
### WORKFLOW START: Initialize Task Hierarchy
### ══════════════════════════════════════════════

**Location**: Before Phase 1 execution, immediately after creating workflow-status.json

**Action**: Create complete Task hierarchy for the entire workflow

**Code**:

```yaml
# ═══════════════════════════════════════════════════
# Step 1: Create Phase-level tasks (3 tasks)
# ═══════════════════════════════════════════════════
TaskCreate:
  subject: "Phase 1: Research - Collect and filter signals"
  description: "Scan multiple sources, classify signals using STEEPs framework, filter duplicates using 4-stage cascade"
  activeForm: "Executing Phase 1 (Research)"
  # Store returned task_id as: phase1_id

TaskCreate:
  subject: "Phase 2: Planning - Analyze and structure signals"
  description: "Verify classifications, analyze impacts, rank priorities, optionally build scenarios"
  activeForm: "Executing Phase 2 (Planning)"
  # Store returned task_id as: phase2_id

TaskUpdate:
  taskId: {phase2_id}
  addBlockedBy: [{phase1_id}]

TaskCreate:
  subject: "Phase 3: Implementation - Generate and archive report"
  description: "Update database, generate bilingual report, archive, await final approval"
  activeForm: "Executing Phase 3 (Implementation)"
  # Store returned task_id as: phase3_id

TaskUpdate:
  taskId: {phase3_id}
  addBlockedBy: [{phase2_id}]

# ═══════════════════════════════════════════════════
# Step 2: Create Phase 1 sub-tasks (13 tasks)
# ═══════════════════════════════════════════════════
TaskCreate:
  subject: "1.1a: Load signals database"
  description: "Load signals/database.json into memory for deduplication baseline"
  activeForm: "Loading signals DB"
  # Store as: task1_1a_id

TaskCreate:
  subject: "1.1b: Load archive reports"
  description: "Load reports/archive/**/*.json for historical context"
  activeForm: "Loading archives"
  # Store as: task1_1b_id
TaskUpdate: { taskId: {task1_1b_id}, addBlockedBy: [{task1_1a_id}] }

TaskCreate:
  subject: "1.1c: Build deduplication indexes"
  description: "Build URL, title, and entity indexes from loaded data"
  activeForm: "Building indexes"
  # Store as: task1_1c_id
TaskUpdate: { taskId: {task1_1c_id}, addBlockedBy: [{task1_1b_id}] }

TaskCreate:
  subject: "1.1d: Validate configuration files"
  description: "Verify sources.yaml, domains.yaml, thresholds.yaml are valid and complete"
  activeForm: "Validating configs"
  # Store as: task1_1d_id
TaskUpdate: { taskId: {task1_1d_id}, addBlockedBy: [{task1_1c_id}] }

TaskCreate:
  subject: "1.2a: Run multi-source scanner"
  description: "Execute arXiv and configured source scanners to collect raw signals"
  activeForm: "Scanning sources"
  # Store as: task1_2a_id
TaskUpdate: { taskId: {task1_2a_id}, addBlockedBy: [{task1_1d_id}] }

TaskCreate:
  subject: "1.2b: Translate raw scan results (KR)"
  description: "Translate raw scan output titles and summaries to Korean"
  activeForm: "Translating scan results"
  # Store as: task1_2b_id
TaskUpdate: { taskId: {task1_2b_id}, addBlockedBy: [{task1_2a_id}] }

TaskCreate:
  subject: "1.2c: Classify signals (STEEPs)"
  description: "Classify each signal into STEEPs categories with confidence scores"
  activeForm: "Classifying signals"
  # Store as: task1_2c_id
TaskUpdate: { taskId: {task1_2c_id}, addBlockedBy: [{task1_2a_id}] }

TaskCreate:
  subject: "1.2d: Translate classified signals (KR)"
  description: "Translate classification labels and rationale to Korean"
  activeForm: "Translating classifications"
  # Store as: task1_2d_id
TaskUpdate: { taskId: {task1_2d_id}, addBlockedBy: [{task1_2c_id}] }

TaskCreate:
  subject: "1.3a: Run 4-stage deduplication cascade"
  description: "URL → String → Semantic → Entity matching deduplication pipeline"
  activeForm: "Filtering duplicates"
  # Store as: task1_3a_id
TaskUpdate: { taskId: {task1_3a_id}, addBlockedBy: [{task1_2c_id}] }

TaskCreate:
  subject: "1.3b: Generate dedup log"
  description: "Log all duplicate matches with confidence scores and removal reasons"
  activeForm: "Generating dedup log"
  # Store as: task1_3b_id
TaskUpdate: { taskId: {task1_3b_id}, addBlockedBy: [{task1_3a_id}] }

TaskCreate:
  subject: "1.3c: Translate filtered results (KR)"
  description: "Translate filtered signal set and dedup summary to Korean"
  activeForm: "Translating filter results"
  # Store as: task1_3c_id
TaskUpdate: { taskId: {task1_3c_id}, addBlockedBy: [{task1_3a_id}] }

TaskCreate:
  subject: "1.4: Human review of filtering"
  description: "Review duplicate removal results if AI confidence < 0.9"
  activeForm: "Awaiting human review"
  metadata: {"checkpoint": true, "required": false}
  # Store as: task1_4_id
TaskUpdate: { taskId: {task1_4_id}, addBlockedBy: [{task1_3a_id}] }

TaskCreate:
  subject: "PG1: Pipeline Gate 1 - Phase 1→2 verification"
  description: "Verify all Phase 1 outputs exist, are valid JSON, and pass quality checks"
  activeForm: "Verifying Phase 1 outputs"
  # Store as: task_pg1_id
TaskUpdate: { taskId: {task_pg1_id}, addBlockedBy: [{task1_4_id}] }

# NOTE: Task 1.5 (Expert Validation) is conditional - create only if >50 signals

# ═══════════════════════════════════════════════════
# Step 3: Create Phase 2 sub-tasks (12 tasks)
# ═══════════════════════════════════════════════════
TaskCreate:
  subject: "2.1a: Verify classification quality"
  description: "Verify STEEPs categories, check confidence scores, correct invalid classifications"
  activeForm: "Verifying classifications"
  # Store as: task2_1a_id
TaskUpdate: { taskId: {task2_1a_id}, addBlockedBy: [{phase1_id}] }

TaskCreate:
  subject: "2.1b: Translate quality log (KR)"
  description: "Translate classification quality verification log to Korean"
  activeForm: "Translating quality log"
  # Store as: task2_1b_id
TaskUpdate: { taskId: {task2_1b_id}, addBlockedBy: [{task2_1a_id}] }

TaskCreate:
  subject: "2.2a: Identify impacts (Futures Wheel)"
  description: "Apply Futures Wheel method to identify direct and indirect impacts"
  activeForm: "Analyzing impacts"
  # Store as: task2_2a_id
TaskUpdate: { taskId: {task2_2a_id}, addBlockedBy: [{task2_1a_id}] }

TaskCreate:
  subject: "2.2b: Build cross-impact matrix"
  description: "Construct signal interaction matrix for cross-influence analysis"
  activeForm: "Building cross-impact matrix"
  # Store as: task2_2b_id
TaskUpdate: { taskId: {task2_2b_id}, addBlockedBy: [{task2_2a_id}] }

TaskCreate:
  subject: "2.2c: Bayesian network inference"
  description: "Calculate conditional probabilities and scenario likelihoods via Bayesian network"
  activeForm: "Running Bayesian inference"
  # Store as: task2_2c_id
TaskUpdate: { taskId: {task2_2c_id}, addBlockedBy: [{task2_2b_id}] }

TaskCreate:
  subject: "2.2d: Calculate pSST IC dimension"
  description: "Compute pSST Information Credibility dimension scores for each signal"
  activeForm: "Calculating pSST IC"
  # Store as: task2_2d_id
TaskUpdate: { taskId: {task2_2d_id}, addBlockedBy: [{task2_2a_id}] }

TaskCreate:
  subject: "2.2e: Translate impact analysis (KR)"
  description: "Translate impact analysis results, cross-impact matrix, and Bayesian output to Korean"
  activeForm: "Translating impact analysis"
  # Store as: task2_2e_id
TaskUpdate: { taskId: {task2_2e_id}, addBlockedBy: [{task2_2c_id}] }

TaskCreate:
  subject: "2.3a: Calculate priority scores"
  description: "Weighted ranking: Impact 40%, Probability 30%, Urgency 20%, Novelty 10%"
  activeForm: "Calculating priorities"
  # Store as: task2_3a_id
TaskUpdate: { taskId: {task2_3a_id}, addBlockedBy: [{task2_2c_id}] }

TaskCreate:
  subject: "2.3b: Aggregate pSST final scores"
  description: "Combine IC, RT, and other pSST dimensions into final trust scores"
  activeForm: "Aggregating pSST scores"
  # Store as: task2_3b_id
TaskUpdate: { taskId: {task2_3b_id}, addBlockedBy: [{task2_3a_id}] }

TaskCreate:
  subject: "2.3c: Translate priority rankings (KR)"
  description: "Translate priority ranking results and pSST scores to Korean"
  activeForm: "Translating rankings"
  # Store as: task2_3c_id
TaskUpdate: { taskId: {task2_3c_id}, addBlockedBy: [{task2_3a_id}] }

# NOTE: Task 2.4a/2.4b (Scenario Building) is conditional - create only if complexity > 0.15

TaskCreate:
  subject: "2.5: Human review of analysis (required)"
  description: "Review STEEPs classifications, priority rankings, pSST scores, approve or request changes"
  activeForm: "Awaiting human review"
  metadata: {"checkpoint": true, "required": true}
  # Store as: task2_5_id
TaskUpdate: { taskId: {task2_5_id}, addBlockedBy: [{task2_3b_id}] }

TaskCreate:
  subject: "PG2: Pipeline Gate 2 - Phase 2→3 verification"
  description: "Verify all Phase 2 outputs exist, are valid, and analysis quality meets thresholds"
  activeForm: "Verifying Phase 2 outputs"
  # Store as: task_pg2_id
TaskUpdate: { taskId: {task_pg2_id}, addBlockedBy: [{task2_5_id}] }

# ═══════════════════════════════════════════════════
# Step 4: Create Phase 3 sub-tasks (20 tasks)
# ═══════════════════════════════════════════════════
TaskCreate:
  subject: "3.1a: Create database backup"
  description: "Create timestamped backup of signals/database.json before modification"
  activeForm: "Creating DB backup"
  metadata: {"critical": true}
  # Store as: task3_1a_id
TaskUpdate: { taskId: {task3_1a_id}, addBlockedBy: [{phase2_id}] }

TaskCreate:
  subject: "3.1b: Update signals database"
  description: "Atomic update to database.json with new signals from this scan"
  activeForm: "Updating database"
  metadata: {"critical": true}
  # Store as: task3_1b_id
TaskUpdate: { taskId: {task3_1b_id}, addBlockedBy: [{task3_1a_id}] }

TaskCreate:
  subject: "3.1c: Verify database integrity"
  description: "Verify updated database.json is valid JSON, signal count matches, no data corruption"
  activeForm: "Verifying DB integrity"
  # Store as: task3_1c_id
TaskUpdate: { taskId: {task3_1c_id}, addBlockedBy: [{task3_1b_id}] }

TaskCreate:
  subject: "3.2a: Generate EN report"
  description: "Generate English environmental scanning report in markdown format"
  activeForm: "Generating EN report"
  # Store as: task3_2a_id
TaskUpdate: { taskId: {task3_2a_id}, addBlockedBy: [{task3_1c_id}] }

TaskCreate:
  subject: "3.2b: Quality check EN report"
  description: "Verify report structure, signal coverage, citation accuracy"
  activeForm: "Checking report quality"
  # Store as: task3_2b_id
TaskUpdate: { taskId: {task3_2b_id}, addBlockedBy: [{task3_2a_id}] }

TaskCreate:
  subject: "3.2c: Translate report to KR"
  description: "Translate EN report to Korean with back-translation verification"
  activeForm: "Translating report"
  # Store as: task3_2c_id
TaskUpdate: { taskId: {task3_2c_id}, addBlockedBy: [{task3_2b_id}] }

TaskCreate:
  subject: "3.2d: Verify KR translation quality"
  description: "Back-translate KR→EN, compare semantic similarity, verify key terms"
  activeForm: "Verifying KR translation"
  # Store as: task3_2d_id
TaskUpdate: { taskId: {task3_2d_id}, addBlockedBy: [{task3_2c_id}] }

TaskCreate:
  subject: "3.2e: Generate pSST trust analysis"
  description: "Generate pSST trust analysis section for inclusion in final report"
  activeForm: "Generating trust analysis"
  # Store as: task3_2e_id
TaskUpdate: { taskId: {task3_2e_id}, addBlockedBy: [{task3_2a_id}] }

TaskCreate:
  subject: "3.3a: Archive EN+KR reports"
  description: "Copy EN and KR reports to reports/archive/{year}/{month}/ directory"
  activeForm: "Archiving reports"
  # Store as: task3_3a_id
TaskUpdate: { taskId: {task3_3a_id}, addBlockedBy: [{task3_2d_id}] }

TaskCreate:
  subject: "3.3b: Create signal snapshot"
  description: "Create timestamped snapshot of signals/database.json in signals/snapshots/"
  activeForm: "Creating snapshot"
  # Store as: task3_3b_id
TaskUpdate: { taskId: {task3_3b_id}, addBlockedBy: [{task3_3a_id}] }

TaskCreate:
  subject: "3.3c: Send notifications"
  description: "Notify stakeholders that new environmental scan report is available"
  activeForm: "Sending notifications"
  # Store as: task3_3c_id
TaskUpdate: { taskId: {task3_3c_id}, addBlockedBy: [{task3_3a_id}] }

TaskCreate:
  subject: "3.3d: Translate daily summary (KR)"
  description: "Translate daily summary log to Korean"
  activeForm: "Translating summary"
  # Store as: task3_3d_id
TaskUpdate: { taskId: {task3_3d_id}, addBlockedBy: [{task3_3a_id}] }

TaskCreate:
  subject: "3.4: Final approval (required)"
  description: "Present EN+KR report to user, await /approve or /revision command"
  activeForm: "Awaiting final approval"
  metadata: {"checkpoint": true, "required": true}
  # Store as: task3_4_id
TaskUpdate: { taskId: {task3_4_id}, addBlockedBy: [{task3_3a_id}] }

TaskCreate:
  subject: "3.5a: Generate quality metrics (EN)"
  description: "Calculate execution times, quality scores, compare to targets in English"
  activeForm: "Generating metrics"
  # Store as: task3_5a_id
TaskUpdate: { taskId: {task3_5a_id}, addBlockedBy: [{task3_4_id}] }

TaskCreate:
  subject: "3.5b: Translate quality metrics (KR)"
  description: "Translate quality metrics report to Korean"
  activeForm: "Translating metrics"
  # Store as: task3_5b_id
TaskUpdate: { taskId: {task3_5b_id}, addBlockedBy: [{task3_5a_id}] }

TaskCreate:
  subject: "3.5c: Generate VEV verification summary"
  description: "Compile VEV protocol verification results into final summary"
  activeForm: "Generating VEV summary"
  # Store as: task3_5c_id
TaskUpdate: { taskId: {task3_5c_id}, addBlockedBy: [{task3_5a_id}] }

TaskCreate:
  subject: "3.6a: Analyze performance metrics"
  description: "Analyze workflow execution performance, identify bottlenecks"
  activeForm: "Analyzing performance"
  # Store as: task3_6a_id
TaskUpdate: { taskId: {task3_6a_id}, addBlockedBy: [{task3_5a_id}] }

TaskCreate:
  subject: "3.6b: Propose improvements"
  description: "Generate improvement proposals based on performance analysis"
  activeForm: "Proposing improvements"
  # Store as: task3_6b_id
TaskUpdate: { taskId: {task3_6b_id}, addBlockedBy: [{task3_6a_id}] }

TaskCreate:
  subject: "3.6c: Execute approved MINOR changes"
  description: "Apply user-approved minor workflow improvements (config tweaks only)"
  activeForm: "Executing minor changes"
  # Store as: task3_6c_id
TaskUpdate: { taskId: {task3_6c_id}, addBlockedBy: [{task3_6b_id}] }

TaskCreate:
  subject: "PG3: Pipeline Gate 3 - Final verification"
  description: "Final verification of all workflow outputs, report integrity, and database consistency"
  activeForm: "Verifying final outputs"
  # Store as: task_pg3_id
TaskUpdate: { taskId: {task_pg3_id}, addBlockedBy: [{task3_6c_id}] }
```

**After Creation**: Store all 48 task IDs in workflow-status.json metadata section

```json
{
  "workflow_id": "scan-2026-01-30",
  "task_mapping": {
    "phase1": "{phase1_id}", "phase2": "{phase2_id}", "phase3": "{phase3_id}",
    "1.1a": "{task1_1a_id}", "1.1b": "{task1_1b_id}", "1.1c": "{task1_1c_id}", "1.1d": "{task1_1d_id}",
    "1.2a": "{task1_2a_id}", "1.2b": "{task1_2b_id}", "1.2c": "{task1_2c_id}", "1.2d": "{task1_2d_id}",
    "1.3a": "{task1_3a_id}", "1.3b": "{task1_3b_id}", "1.3c": "{task1_3c_id}",
    "1.4": "{task1_4_id}", "PG1": "{task_pg1_id}",
    "2.1a": "{task2_1a_id}", "2.1b": "{task2_1b_id}",
    "2.2a": "{task2_2a_id}", "2.2b": "{task2_2b_id}", "2.2c": "{task2_2c_id}", "2.2d": "{task2_2d_id}", "2.2e": "{task2_2e_id}",
    "2.3a": "{task2_3a_id}", "2.3b": "{task2_3b_id}", "2.3c": "{task2_3c_id}",
    "2.5": "{task2_5_id}", "PG2": "{task_pg2_id}",
    "3.1a": "{task3_1a_id}", "3.1b": "{task3_1b_id}", "3.1c": "{task3_1c_id}",
    "3.2a": "{task3_2a_id}", "3.2b": "{task3_2b_id}", "3.2c": "{task3_2c_id}", "3.2d": "{task3_2d_id}", "3.2e": "{task3_2e_id}",
    "3.3a": "{task3_3a_id}", "3.3b": "{task3_3b_id}", "3.3c": "{task3_3c_id}", "3.3d": "{task3_3d_id}",
    "3.4": "{task3_4_id}",
    "3.5a": "{task3_5a_id}", "3.5b": "{task3_5b_id}", "3.5c": "{task3_5c_id}",
    "3.6a": "{task3_6a_id}", "3.6b": "{task3_6b_id}", "3.6c": "{task3_6c_id}",
    "PG3": "{task_pg3_id}"
  }
}
```
NOTE: Keys "1.5", "2.4a", "2.4b" will be added dynamically if conditional steps are activated

### ══════════════════════════════════════════════
### STEP EXECUTION: Update Task Status
### ══════════════════════════════════════════════

**Location**: Before and after each step execution

**Pattern**:

```yaml
# BEFORE executing step X.Y (use first sub-task)
TaskUpdate:
  taskId: {task_id_for_first_subtask}  # e.g., task_mapping["1.1a"]
  status: "in_progress"

# EXECUTE step (invoke worker agent)
[Execute existing step logic]

# AFTER successful completion (mark all sub-tasks)
for each subtask_key in step_subtasks:
  TaskUpdate:
    taskId: {task_mapping[subtask_key]}
    status: "completed"

# Update workflow-status.json (existing)
[Add X.Y to completed_steps array]
```

**Example for Step 1.1** (has 4 sub-tasks: 1.1a, 1.1b, 1.1c, 1.1d):

```yaml
# Before (mark first sub-task in_progress)
TaskUpdate:
  taskId: {task_mapping["1.1a"]}
  status: "in_progress"

# Execute
Task:
  subagent_type: "Explore"
  description: "Load historical signals"
  prompt: "Execute @archive-loader worker agent..."

# After (mark all sub-tasks completed)
TaskUpdate: { taskId: {task_mapping["1.1a"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["1.1b"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["1.1c"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["1.1d"]}, status: "completed" }
```

### ══════════════════════════════════════════════
### HUMAN CHECKPOINT: Wait for User Input
### ══════════════════════════════════════════════

**Location**: Steps 1.4, 2.5, 3.4

**Pattern**:

```yaml
# Mark task as in_progress (shows "Awaiting...")
TaskUpdate:
  taskId: {checkpoint_task_id}
  status: "in_progress"

# Display checkpoint to user (existing AskUserQuestion)
AskUserQuestion:
  questions: [...]

# WAIT for user response

# After user approval
TaskUpdate:
  taskId: {checkpoint_task_id}
  status: "completed"

# Log decision (existing)
[Add to workflow-status.json human_decisions]
```

**User Experience**:

While waiting at checkpoint, user can press `Ctrl+T` to see:

```
Task List: env-scan-2026-01-30

[✓] Phase 1: Research (14/14 sub-tasks complete)
[▶] Phase 2: Planning (in_progress)
  [✓] 2.1a Verify quality  [✓] 2.1b Translate log    [✓] 2.2a Futures Wheel
  [✓] 2.2b Cross-impact    [✓] 2.2c Bayesian         [✓] 2.2d pSST IC
  [✓] 2.2e Translate impact [✓] 2.3a Calc priorities  [✓] 2.3b pSST scores
  [✓] 2.3c Translate ranks  [▶] 2.5 Human review      [ ] PG2 Pipeline Gate 2
[ ] Phase 3: Implementation (blocked)

Current: 2.5 - Awaiting human review
```

### ══════════════════════════════════════════════
### CONDITIONAL STEP: Create Task Dynamically
### ══════════════════════════════════════════════

**Location**: Step 1.5 (Expert Validation), Step 2.4 (Scenarios)

**Pattern**:

```yaml
# Check activation condition
if condition_met:
  # Create task if it doesn't exist
  TaskCreate:
    subject: "Step X.Y: [Conditional step name]"
    description: "..."
    activeForm: "..."
    # Store as: conditional_task_id

  # Set up dependencies
  TaskUpdate:
    taskId: {conditional_task_id}
    addBlockedBy: [{previous_step_id}]

  # Update next step to block on this conditional step
  TaskUpdate:
    taskId: {next_step_id}
    addBlockedBy: [{conditional_task_id}]

  # Execute
  TaskUpdate:
    taskId: {conditional_task_id}
    status: "in_progress"

  [Execute conditional step]

  TaskUpdate:
    taskId: {conditional_task_id}
    status: "completed"

else:
  # Condition not met - skip step
  # No task update needed (task was never created)
  pass
```

**Example for Step 1.5 (Expert Validation)**:

```yaml
# After Step 1.4 and PG1 complete
signal_count = count_signals("filtered/new-signals-{date}.json")

if signal_count > 50:
  # Ask user if they want expert validation
  AskUserQuestion: [...]

  if user_activates_expert_validation:
    # Create task
    TaskCreate:
      subject: "1.5: Expert panel validation (RT-AID)"
      description: "RT-AID expert validation for {signal_count} signals"
      activeForm: "Expert validation in progress"
      # Store as: task1_5_id

    TaskUpdate:
      taskId: {task1_5_id}
      addBlockedBy: [{task1_4_id}]

    # Store in task_mapping
    # task_mapping["1.5"] = task1_5_id

    # Execute expert validation
    TaskUpdate:
      taskId: {task1_5_id}
      status: "in_progress"

    [Invoke @realtime-delphi-facilitator agent]
    [Wait 48 hours for expert responses]

    TaskUpdate:
      taskId: {task1_5_id}
      status: "completed"
else:
  # Skip expert validation (< 50 signals)
  pass
```

**Example for Step 2.4a/2.4b (Scenario Building)**:

```yaml
# After Step 2.3b complete
if complexity_score > 0.15:
  TaskCreate:
    subject: "2.4a: Build plausible scenarios"
    activeForm: "Building scenarios"
    # Store as: task2_4a_id
  TaskUpdate: { taskId: {task2_4a_id}, addBlockedBy: [{task2_3b_id}] }

  TaskCreate:
    subject: "2.4b: Translate scenarios (KR)"
    activeForm: "Translating scenarios"
    # Store as: task2_4b_id
  TaskUpdate: { taskId: {task2_4b_id}, addBlockedBy: [{task2_4a_id}] }

  # Update 2.5 to wait for scenarios
  TaskUpdate:
    taskId: {task2_5_id}
    addBlockedBy: [{task2_4b_id}]

  # Store in task_mapping
  # task_mapping["2.4a"] = task2_4a_id
  # task_mapping["2.4b"] = task2_4b_id
```

### ══════════════════════════════════════════════
### PHASE COMPLETION: Mark Phase Task Complete
### ══════════════════════════════════════════════

**Location**: After last step of each phase

**Pattern**:

```yaml
# After completing all steps in Phase X
TaskUpdate:
  taskId: {phaseX_id}
  status: "completed"

# Update workflow-status.json
{
  "current_phase": X+1,
  "phase_X_metrics": {
    "signals_collected": ...,
    "execution_time": ...,
    ...
  }
}
```

**Example after Phase 1**:

```yaml
# After PG1 passes (or 1.5 if activated)
TaskUpdate: { taskId: {task_pg1_id}, status: "completed" }
TaskUpdate: { taskId: {phase1_id}, status: "completed" }

# workflow-status.json update
{
  "current_phase": 2,
  "completed_steps": ["1.1", "1.2", "1.3", "1.4", "PG1"],
  "phase_1_metrics": {
    "signals_collected": 247,
    "signals_filtered": 79,
    "dedup_rate": 68,
    "avg_confidence": 0.92
  }
}
```

### ══════════════════════════════════════════════
### WORKFLOW COMPLETION: Finalize All Tasks
### ══════════════════════════════════════════════

**Location**: After Steps 3.5 + 3.6 (Quality Metrics + Performance Analysis) complete

**Action**:

```yaml
# Mark all remaining Phase 3 sub-tasks complete
TaskUpdate: { taskId: {task_mapping["3.5a"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["3.5b"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["3.5c"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["3.6a"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["3.6b"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["3.6c"]}, status: "completed" }
TaskUpdate: { taskId: {task_mapping["PG3"]}, status: "completed" }

# Mark Phase 3 complete
TaskUpdate: { taskId: {phase3_id}, status: "completed" }

# Ensure Phase 1 is completed (if not already)
TaskUpdate: { taskId: {phase1_id}, status: "completed" }

# Update workflow-status.json
{
  "status": "completed",
  "end_time": "{ISO8601}",
  "phase_3_metrics": {
    "report_generated": true,
    "archive_path": "reports/archive/2026/01/...",
    "total_signals_in_db": 1014
  }
}

# Generate quality metrics (existing)
[Create logs/quality-metrics/workflow-{date}.json]

# Notify user
print("✅ Workflow complete. Press Ctrl+T to view full task history.")
```

### ══════════════════════════════════════════════
### ERROR HANDLING: Task Update Failures
### ══════════════════════════════════════════════

**Critical Principle**: Task updates are **non-critical** - they should NEVER halt the workflow

**Pattern**:

```yaml
try:
  TaskUpdate:
    taskId: {task_id}
    status: "completed"
except Exception as e:
  # Log warning but DO NOT halt
  log_warning(f"Task update failed for {task_id}: {e}")
  # Continue with workflow
  # workflow-status.json is the source of truth
```

**Why**:
- Task system is for **user visibility only**
- workflow-status.json remains the authoritative state
- If Task system fails, workflow still completes successfully

### ══════════════════════════════════════════════
### USER NOTIFICATION: Progress Display
### ══════════════════════════════════════════════

**At key milestones**, remind user they can check progress:

```python
# After Phase 1 complete
print("""
✅ Phase 1 완료 (Research Complete)
   신규 신호 / New signals: 79개

💡 진행 상황 확인 / Check progress: Press Ctrl+T

다음: Phase 2 (Planning) 시작
""")

# At checkpoints
print("""
⏸ 검토 필요 / Review Required
   Step 2.5: Human review of analysis

💡 전체 작업 목록 / Full task list: Press Ctrl+T

[AskUserQuestion prompts follow...]
""")
```

## Task ID Storage Strategy

Store all 48 task IDs in workflow-status.json for reference:

```json
{
  "workflow_id": "scan-2026-01-30",
  "task_list_id": "env-scan-2026-01-30",
  "task_mapping": {
    "phase1": "1", "phase2": "2", "phase3": "3",
    "1.1a": "4", "1.1b": "5", "1.1c": "6", "1.1d": "7",
    "1.2a": "8", "1.2b": "9", "1.2c": "10", "1.2d": "11",
    "1.3a": "12", "1.3b": "13", "1.3c": "14",
    "1.4": "15", "PG1": "16",
    "2.1a": "17", "2.1b": "18",
    "2.2a": "19", "2.2b": "20", "2.2c": "21", "2.2d": "22", "2.2e": "23",
    "2.3a": "24", "2.3b": "25", "2.3c": "26",
    "2.5": "27", "PG2": "28",
    "3.1a": "29", "3.1b": "30", "3.1c": "31",
    "3.2a": "32", "3.2b": "33", "3.2c": "34", "3.2d": "35", "3.2e": "36",
    "3.3a": "37", "3.3b": "38", "3.3c": "39", "3.3d": "40",
    "3.4": "41",
    "3.5a": "42", "3.5b": "43", "3.5c": "44",
    "3.6a": "45", "3.6b": "46", "3.6c": "47",
    "PG3": "48"
  }
}
```

This enables recovery if orchestrator is interrupted and resumed.
Conditional keys ("1.5", "2.4a", "2.4b") are added dynamically when activated.

## Testing Checklist

Before deploying Task Management integration:

- [ ] Create task hierarchy at workflow start (49 static tasks)
- [ ] Verify Phase 2 is blocked until Phase 1 complete
- [ ] Verify Phase 3 is blocked until Phase 2 complete
- [ ] Verify sub-task blockedBy chains are correct (no circular dependencies)
- [ ] Test `Ctrl+T` displays correct progress during execution (49 items visible)
- [ ] Test human checkpoint shows "Awaiting..." status
- [ ] Test Pipeline Gate tasks (PG1, PG2, PG3) are created and tracked
- [ ] Test conditional steps (1.5, 2.4a, 2.4b) create tasks only when activated
- [ ] Test task update failures don't halt workflow
- [ ] Verify workflow-status.json remains authoritative
- [ ] Verify task_mapping has exactly 49 keys
- [ ] Test workflow completion marks all tasks complete

## Integration Benefits

1. **Zero Breaking Changes**: Existing workflow logic untouched
2. **User Visibility**: `Ctrl+T` anytime to see progress
3. **Audit Trail**: Task timestamps show exact execution timeline
4. **Recovery**: Task IDs in workflow-status.json enable resumption
5. **Non-Critical**: Task failures never halt workflow

## Version

- **Guide Version**: 2.0.0 (3x Task Hierarchy)
- **Compatible Orchestrator**: v2.2.0+ (Bilingual EN-KR with VEV)
- **Claude Code**: 2.1.16+
- **Task Count**: 49 static + 3 conditional = up to 52
- **Last Updated**: 2026-01-31

---

**Next Steps**: Orchestrator should follow these instructions during next workflow execution
