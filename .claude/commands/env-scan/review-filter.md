---
name: review-filter
description: Review duplicate filtering results (Phase 1, Step 1.4) - Optional checkpoint
---

# Review Filtering Results

Inspect signals removed by the deduplication filter and decide whether to include any exceptions.

## Usage

```bash
/review-filter
```

## When To Use

This command is triggered at **Phase 1, Step 1.4** after duplicate filtering completes. It's an **OPTIONAL** checkpoint - workflow can continue without human review if AI confidence is high.

## Auto-Skip Conditions

Workflow automatically skips this review if:
- AI confidence > 0.9 for all removed signals (> 90% of cases)
- No low-confidence removals (confidence < 0.7)

You'll be notified if review is recommended:
```
⚠️ 5 signals removed with low confidence (<0.7)
Recommendation: Run /review-filter to inspect
(Or continue automatically - workflow will proceed in 30 seconds)
```

## What You'll See

### 1. Filtering Statistics
- Total raw items collected
- Duplicates removed (by stage)
- New signals retained
- Filter rate percentage

### 2. Removed Signals by Confidence
- High confidence (>0.9): Auto-approved, listed briefly
- Medium confidence (0.7-0.9): Sample shown
- Low confidence (<0.7): All shown for review

### 3. Deduplication Reasoning
For each removed signal:
- Which existing signal it matched
- Stage where duplicate was detected (1-4)
- Confidence score
- Reasoning (explainable AI)

## Example Interaction

```
═══════════════════════════════════════════════════
   Filtering Review (Phase 1, Step 1.4)
═══════════════════════════════════════════════════

Filtering Statistics:
  • Raw items collected: 247
  • Duplicates removed: 168 (68% filter rate)
  • New signals retained: 79

Breakdown by Stage:
  Stage 1 (URL exact match): 85 signals
  Stage 2 (String similarity): 42 signals
  Stage 3 (Semantic similarity): 31 signals
  Stage 4 (Entity matching): 10 signals

─────────────────────────────────────────────────
High Confidence Removals (145 signals)
─────────────────────────────────────────────────

✓ These duplicates were correctly identified (confidence >0.9)
[Brief list - not shown in detail]

─────────────────────────────────────────────────
Medium Confidence Removals (18 signals)
─────────────────────────────────────────────────

Showing 3 random samples for spot check:

Signal: "OpenAI announces GPT-5 preview"
  Matched: signal-087 "GPT-5 beta released by OpenAI"
  Stage: 2 (String similarity: 0.92)
  Confidence: 0.88
  Reasoning: Very similar titles, same event

Signal: [2 more samples...]

─────────────────────────────────────────────────
⚠️ Low Confidence Removals (5 signals)
─────────────────────────────────────────────────

These require your attention:

1. Signal: "Quantum computing breakthrough in China"
   Matched: signal-042 "IBM quantum processor milestone"
   Stage: 3 (Semantic similarity: 0.81)
   Confidence: 0.67
   Reasoning: Both about quantum computing, but different actors/events

   ❓ Decision: Keep as duplicate OR Force include?

2. Signal: [Next low-confidence signal...]

─────────────────────────────────────────────────
Review Options
─────────────────────────────────────────────────

For each low-confidence removal, choose:
  ✓ Confirm duplicate - Keep removed
  ✗ Force include - Add back to new signals

[Interactive selection interface]

> Your selections:
  Signal 1: Force include (different event)
  Signal 2: Confirm duplicate
  Signal 3: Force include (important nuance)
  Signal 4: Confirm duplicate
  Signal 5: Force include

─────────────────────────────────────────────────
✓ Review Complete
─────────────────────────────────────────────────

Changes applied:
  • 3 signals added back to new signals
  • Final new signal count: 82 (was 79)

Updated statistics:
  • Total raw: 247
  • Duplicates: 165 (67% filter rate)
  • New signals: 82

Continuing to Phase 2: Planning...
```

## Force Include

If you force include a signal:
1. Signal is added back to `filtered/new-signals-{date}.json`
2. It proceeds to Phase 2 for classification
3. Your decision is logged for model improvement

## Quality Improvement

Your corrections are saved in:
- `logs/quality-metrics/human-corrections.json`

This data is used to:
- Retrain deduplication models
- Adjust confidence thresholds
- Improve future filtering accuracy

## When To Skip Review

Skip this review if:
- All removals have high confidence (>0.9)
- You trust the AI's judgment
- Time-sensitive and need fast execution

The workflow will continue automatically after 30 seconds if no input.

## Related Commands

- `/status` - Check if filtering review is available
- `/run-daily-scan` - Start workflow (will reach this checkpoint)

## Notes

- This is the ONLY optional checkpoint in the workflow
- Most runs (>90%) skip this automatically due to high confidence
- Your feedback directly improves AI accuracy over time
- Forced inclusions do not affect deduplication quality metrics

## Version
**Command Version**: 1.0.0
**Last Updated**: 2026-01-29
