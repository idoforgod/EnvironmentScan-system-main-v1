---
name: run-weekly-scan
description: Execute weekly meta-analysis of the past 7 days of daily scans (no new scanning)
context: fork
---

# Run Weekly Meta-Analysis Scan

Execute the weekly meta-analysis — a higher-level re-analysis of the past 7 days' daily scan results.
**No new source scanning is performed.** All data access is READ-ONLY.

## Usage

```bash
/run-weekly-scan
```

## What This Command Does

This command invokes the **master-orchestrator** in weekly mode (Step 5 only).
It does NOT execute WF1, WF2, or daily integration.

1. **SOT Validation** — Same startup validation (19 checks including SOT-017~019 for weekly)
2. **Pre-Check (PEC-003)** — Verify at least 5 daily scans exist in the last 7 days
3. **Data Loading** — Load 7 days of daily reports + ranked JSON + signal DB stats (READ-ONLY)
4. **Meta-Analysis** — Trend analysis, convergence clusters, TIS scoring, scenario adjustment
5. **Report Generation** — Weekly skeleton-based report with L1-L4 quality defense

### Key Difference from Daily Scan

```
Daily:  Source scanning → Signal discovery → Analysis → Report  (microscopic — individual signals)
Weekly: Daily data loading → Trend analysis → Meta-analysis → Report  (macroscopic — pattern discovery)
```

| Dimension | Daily | Weekly |
|-----------|-------|--------|
| Question | "What's new today?" | "How did the landscape change this week?" |
| Data source | External web/API | Internal accumulated data (READ-ONLY) |
| Analysis unit | 10-15 individual signals | 5-7 trend clusters |
| Unique metric | pSST (signal confidence) | TIS (Trend Intensity Score) |
| Time horizons | 0-6mo, 6-18mo | 0-6mo, 6-18mo, **18mo+** |

## Pre-Execution Check

Before running, the system verifies:
- **PEC-003**: At least 5 daily integrated reports exist within the last 7 days
- **Duplicate check**: If a weekly report for this week (ISO 8601 week ID) already exists, asks for confirmation

If insufficient data, the user is warned and asked to proceed or abort.

## Checkpoints (2 total)

| # | Step | Type | Command |
|---|------|------|---------|
| 1 | Step 5.2 Analysis Review | Required | Review meta-analysis results |
| 2 | Step 5.3 Report Approval | Required | `/approve` or `/revision` |

## Output Files

- **Report**: `env-scanning/integrated/weekly/reports/weekly-scan-{week_id}.md`
- **Analysis**: `env-scanning/integrated/weekly/analysis/`
- **Status**: `env-scanning/integrated/weekly/logs/weekly-status-{week_id}.json`
- **Archive**: `env-scanning/integrated/weekly/reports/archive/{year}/{month}/`

Week ID format: ISO 8601 (e.g., `2026-W06`)

## TIS (Trend Intensity Score)

Weekly-specific metric for measuring trend momentum:

```
TIS = (N_sources x 0.3) + (pSST_delta x 0.3) + (frequency x 0.2) + (cross_domain x 0.2)
```

Grades:
- **Surging**: TIS >= 0.8
- **Rising**: 0.6 <= TIS < 0.8
- **Stable**: 0.4 <= TIS < 0.6
- **Declining**: 0.2 <= TIS < 0.4
- **Fading**: TIS < 0.2

## Report Structure

The weekly report uses a different structure from daily reports:

1. Executive Summary (Top 3 Trends)
2. Weekly Trend Analysis (STEEPs trends, accelerating/decelerating/new/faded)
3. Signal Convergence Analysis (clusters, diverging signals, WF1-WF2 cross-validation)
4. Signal Evolution Timeline (pSST changes, maturity transitions)
5. Strategic Implications (immediate/mid-term/long-term + week-over-week)
6. Plausible Scenarios
7. Confidence Analysis (pSST distribution trend, source reliability)
8. System Performance Review (quality metrics, calibration recommendations)
9. Appendix

## When to Use

- End of the work week for weekly synthesis
- When you have 5+ days of daily scan data accumulated
- For strategic-level pattern recognition across daily signals
- To generate week-over-week trend comparisons

## Error Handling

- **Insufficient data** (< 5 daily scans): Warning + user confirmation
- **Missing daily reports**: Proceeds with available data, notes gaps
- **Already run this week**: Asks to re-run or skip

## Related Commands

- `/run-daily-scan` - Full dual daily scan (WF1 + WF2 + Integration)
- `/run-arxiv-scan` - WF2 standalone arXiv scan
- `/status` - Check workflow progress
- `/approve` - Approve report

## Version
**Command Version**: 1.0.0
**Last Updated**: 2026-02-06
