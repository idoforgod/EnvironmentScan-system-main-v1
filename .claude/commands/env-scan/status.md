---
name: status
description: Check current environmental scanning workflow progress and state
---

# Workflow Status

Display current progress, completed steps, and next actions for the active environmental scanning workflow.

## Usage

```bash
/status
```

## Output Information

### 1. Workflow Overview
- Workflow ID
- Start time
- Current phase and step
- Overall status (in_progress, blocked, completed, failed)
- Elapsed time

### 2. Phase Progress
- Phase 1: Research [Completed ✓ / In Progress ⏳ / Pending ⏸]
- Phase 2: Planning [Status]
- Phase 3: Implementation [Status]

### 3. Step Details
- Completed steps with timestamps
- Current step with progress indicator
- Pending steps
- Blocked steps (waiting for user input)

### 4. Artifacts Generated
- List of output files created so far (EN + KR pairs)
- File paths and sizes
- Translation status

### 5. Translation Quality
- Number of translations completed
- Average translation confidence
- STEEPs terminology accuracy
- EN-KR file pairs verified

### 6. Errors/Warnings
- Any errors encountered
- Retry attempts made
- Translation warnings (if any)
- Other warnings issued

### 7. Next Action
- What needs to happen next
- Required user action (if any)
- Suggested commands

## Example Output

```
═══════════════════════════════════════════════════
   Environmental Scanning Workflow Status
═══════════════════════════════════════════════════

Workflow ID: scan-2026-01-29
Started: 2026-01-29 06:00:15
Elapsed Time: 12 minutes 34 seconds
Status: ⏸ BLOCKED (Awaiting human review)

─────────────────────────────────────────────────
Phase Progress
─────────────────────────────────────────────────

Phase 1: Research [✓ COMPLETED]
  ✓ Step 1.1: Archive loader (3.2s)
  ✓ Step 1.2: Multi-source scanner (45.3s)
  ✓ Step 1.3: Deduplication filter (12.4s)
  ⏭ Step 1.4: Human review (skipped - high confidence)

Phase 2: Planning [⏳ IN PROGRESS]
  ✓ Step 2.1a: Signal classifier (18.7s)
  ✓ Step 2.1b: Translate classification (3.2s) ✓ KR
  ✓ Step 2.2a: Impact analyzer (28.3s)
  ✓ Step 2.2b: Translate impact analysis (4.1s) ✓ KR
  ✓ Step 2.3a: Priority ranker (4.1s)
  ✓ Step 2.3b: Translate rankings (2.8s) ✓ KR
  ⏭ Step 2.4: Scenario builder (not triggered)
  ⏸ Step 2.5: Analysis review (AWAITING USER)

Phase 3: Implementation [⏸ PENDING]
  ⏸ Step 3.1: Database updater
  ⏸ Step 3.2: Report generator
  ⏸ Step 3.3: Archive notifier
  ⏸ Step 3.4: Final approval

─────────────────────────────────────────────────
산출물 / Artifacts Generated (Bilingual)
─────────────────────────────────────────────────

✓ context/previous-signals.json (2.3 MB, EN-only)
✓ raw/daily-scan-2026-01-29.json (1.8 MB) + -ko (2.1 MB)
✓ filtered/new-signals-2026-01-29.json (456 KB) + -ko (548 KB)
✓ structured/classified-signals-2026-01-29.json (512 KB) + -ko (615 KB)
✓ analysis/impact-assessment-2026-01-29.json (387 KB) + -ko (465 KB)
✓ analysis/cross-impact-matrix-2026-01-29.json (245 KB, EN-only)
✓ analysis/priority-ranked-2026-01-29.json (298 KB) + -ko (358 KB)

EN-KR Pairs: 6/6 verified ✓

─────────────────────────────────────────────────
성능 지표 / Performance Metrics
─────────────────────────────────────────────────

• Sources scanned: 8/8 (100%)
• Raw items collected: 247
• Duplicates removed: 168 (68% filter rate)
• New signals: 79
• High priority signals: 15 (top 20%)

─────────────────────────────────────────────────
번역 품질 / Translation Quality
─────────────────────────────────────────────────

• Translations completed: 6/6 (100%)
• Average confidence: 0.95
• Back-translation similarity: 0.93
• STEEPs terminology accuracy: 100% (0 violations)
• Translation overhead: +18.2s (15% of workflow time)

─────────────────────────────────────────────────
⚠ 경고 / Warnings
─────────────────────────────────────────────────

• TechCrunch API timeout (retry successful)
• 5 signals flagged for low confidence (<0.7)
• No translation errors

─────────────────────────────────────────────────
📌 Next Action
─────────────────────────────────────────────────

REQUIRED: Review analysis results and adjust priorities

Run: /review-analysis

This will display top 10 signals for your review.
After review, workflow will continue to Phase 3.

═══════════════════════════════════════════════════
```

## Related Commands

- `/run-daily-scan` - Start new workflow
- `/review-filter` - Review filtering (if blocked at Step 1.4)
- `/review-analysis` - Review analysis (if blocked at Step 2.5)
- `/approve` - Final approval (if blocked at Step 3.4)

## Notes

- Status reflects state from `logs/workflow-status.json`
- Real-time updates as workflow progresses
- Shows only the most recent active workflow
- Historical workflows can be found in logs archive

## Bilingual Status Display

Status command now shows:
- Translation progress for each step (✓ KR indicates Korean translation completed)
- EN-KR file pairs verification status
- Translation quality metrics
- Bilingual artifact listings

## Version
**Command Version**: 1.1.0 (Bilingual Status)
**Last Updated**: 2026-01-30
