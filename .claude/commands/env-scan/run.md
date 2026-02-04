---
name: run-daily-scan
description: Execute complete dual environmental scanning workflow (WF1 + WF2 + Integration)
context: fork
---

# Run Daily Environmental Scan

Execute the full dual workflow environmental scanning system with automatic pause at human review checkpoints.

## Usage

```bash
# Default mode — Full dual scan (WF1 + WF2 + Integration)
/run-daily-scan

# Base-only mode for WF1 (skip expansion sources in WF1)
/run-daily-scan --base-only

# arXiv only — Run WF2 standalone (skip WF1, no integration)
/run-daily-scan --arxiv-only
```

## Options

| Flag | Description |
|------|-------------|
| (none) | Full dual scan: WF1 (marathon) → WF2 (arXiv deep) → Integrated report |
| `--base-only` | WF1 scans base sources only (skip expansion), WF2 runs normally |
| `--arxiv-only` | WF2 only: Skip WF1, skip integration, produce arXiv report only |

## Architecture

This command invokes the **master-orchestrator**, which reads the Source of Truth
(`workflow-registry.yaml`), validates startup conditions, and executes:

```
┌──────────────────────────────────────────────────────┐
│  Step 0: SOT Validation                               │
│    Read workflow-registry.yaml                         │
│    Run validate_registry.py (13 checks)                │
├──────────────────────────────────────────────────────┤
│  Step 1: WF1 — General Environmental Scanning          │
│    Sources: 20+ (patents, policy, blogs, academic)     │
│    arXiv: EXCLUDED (handled by WF2)                    │
│    Checkpoints: Step 2.5 (required), Step 3.4 (required)│
├──────────────────────────────────────────────────────┤
│  Step 2: WF2 — arXiv Academic Deep Scanning            │
│    Sources: arXiv ONLY (extended: 30+ categories)      │
│    Parameters: 14 days, 50 results/category            │
│    Checkpoints: Step 2.5 (required), Step 3.4 (required)│
├──────────────────────────────────────────────────────┤
│  Step 3: Integration — Report Merge                    │
│    Merge WF1 + WF2 reports (pSST unified ranking)      │
│    Cross-workflow analysis                              │
│    Checkpoint: Final approval (5th checkpoint)          │
└──────────────────────────────────────────────────────┘
```

## What This Command Does

1. **SOT Validation**
   - Reads `env-scanning/config/workflow-registry.yaml`
   - Runs `validate_registry.py` (13 checks: file existence, arXiv placement, no source overlap)
   - On HALT: stops with specific failure details

2. **WF1: General Environmental Scanning**
   - Phase 1: Scan 20+ sources (base + expansion in marathon mode)
   - Phase 2: Classify → Impact → Priority → **Human review (2.5)**
   - Phase 3: DB update → Report → Archive → **Human approval (3.4)**
   - Output: `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md`

3. **WF2: arXiv Academic Deep Scanning**
   - Phase 1: Deep scan arXiv (14 days, 50/category, 30+ categories)
   - Phase 2: Classify → Impact → Priority → **Human review (2.5)**
   - Phase 3: DB update → Report → Archive → **Human approval (3.4)**
   - Output: `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md`

4. **Integration: Report Merge**
   - Combine WF1 + WF2 signals, re-rank by pSST
   - Cross-workflow analysis (reinforced, academic-early, media-first)
   - Generate integrated report (top 15 signals)
   - **Final human approval (5th checkpoint)**
   - Output: `env-scanning/integrated/reports/daily/integrated-scan-{date}.md`

## Checkpoints (5 total)

| # | Step | Type | Command |
|---|------|------|---------|
| 1 | WF1 Step 2.5 | Required | `/review-analysis` |
| 2 | WF1 Step 3.4 | Required | `/approve` or `/revision` |
| 3 | WF2 Step 2.5 | Required | `/review-analysis` |
| 4 | WF2 Step 3.4 | Required | `/approve` or `/revision` |
| 5 | Integration | Required | `/approve` or `/revision` |

## Output Files

### WF1 (General)
- Report: `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf1-general/signals/database.json`
- Analysis: `env-scanning/wf1-general/analysis/`

### WF2 (arXiv)
- Report: `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf2-arxiv/signals/database.json`
- Analysis: `env-scanning/wf2-arxiv/analysis/`

### Integrated
- Report: `env-scanning/integrated/reports/daily/integrated-scan-{date}.md`
- Archive: `env-scanning/integrated/reports/archive/{year}/{month}/`

## Error Handling

- **SOT validation failure**: Halt before any scanning
- **WF1 failure**: Option to skip WF1 and run WF2 only (no integration)
- **WF2 failure**: Option to skip WF2 and use WF1 report as final output
- **Integration failure**: Option to use both independent reports separately
- **arXiv API unreachable**: WF2 halts with 3 retry attempts; option to skip WF2

## Related Commands

- `/status` - Check current workflow progress
- `/review-filter` - Review filtering results (Step 1.4)
- `/review-analysis` - Review analysis results (Step 2.5)
- `/approve` - Approve report (Step 3.4 / Integration)
- `/revision "feedback"` - Request report revision

## Version
**Command Version**: 4.0.0 (Dual Workflow System)
**Last Updated**: 2026-02-03
