---
name: run-arxiv-scan
description: Execute WF2 (arXiv Academic Deep Scanning) as a standalone workflow
context: fork
---

# Run arXiv Academic Deep Scan (WF2 Standalone)

Execute WF2 independently — deep scanning of arXiv academic papers only.
This produces a complete, independently valid report without requiring WF1 or integration.

## Usage

```bash
/run-arxiv-scan
```

## What This Command Does

This command invokes the **master-orchestrator** in WF2-only mode:

1. **SOT Validation** — Same 13-check startup validation
2. **WF2 Execution** — Full 3-phase pipeline on arXiv only
3. **No WF1** — WF1 is skipped entirely
4. **No Integration** — No report merge (WF2 report is the final output)

### WF2 Parameters

| Parameter | Value |
|-----------|-------|
| Source | arXiv only |
| Lookback | 14 days |
| Results per category | 50 |
| arXiv categories | 30+ (extended mapping) |
| Timeout | 60 seconds |

### WF2 Phases

- **Phase 1**: Deep scan arXiv across 6 STEEPs domains (30+ categories)
- **Phase 2**: Classify → Impact → Priority → **Human review (required)**
- **Phase 3**: DB update → Report → Archive → **Human approval (required)**

## Checkpoints (2 total)

| # | Step | Type | Command |
|---|------|------|---------|
| 1 | WF2 Step 2.5 | Required | `/review-analysis` |
| 2 | WF2 Step 3.4 | Required | `/approve` or `/revision` |

## Output

- Report: `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md`
- Database: `env-scanning/wf2-arxiv/signals/database.json`
- Archive: `env-scanning/wf2-arxiv/reports/archive/{year}/{month}/`

## When to Use

- When you need academic-focused signals only
- When WF1 has already been run and you want supplementary arXiv data
- When arXiv API was unavailable during a dual scan and you want to retry WF2

## Error Handling

- **arXiv API failure**: 3 retry attempts with exponential backoff (3s, 9s, 27s)
- **Low signal count** (< 10): Automatic fallback to 21 days / 80 per category
- **Still insufficient**: User prompted to continue or abort

## Related Commands

- `/run-daily-scan` - Full dual scan (WF1 + WF2 + Integration)
- `/status` - Check workflow progress
- `/approve` - Approve final report

## Version
**Command Version**: 1.0.0
**Last Updated**: 2026-02-03
