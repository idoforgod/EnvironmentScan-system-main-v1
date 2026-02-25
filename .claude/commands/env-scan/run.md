---
name: run-daily-scan
description: Execute complete quadruple environmental scanning workflow (WF1 + WF2 + WF3 + WF4 + Integration)
context: fork
---

# Run Daily Environmental Scan

Execute the full quadruple workflow environmental scanning system with automatic pause at human review checkpoints.

## Usage

```bash
# Default mode — Full quadruple scan (WF1 + WF2 + WF3 + WF4 + Integration)
/run-daily-scan

# Base-only mode for WF1 (skip expansion sources in WF1)
/run-daily-scan --base-only

# arXiv only — Run WF2 standalone (skip WF1/WF3, no integration)
/run-daily-scan --arxiv-only

# Naver only — Run WF3 standalone (skip WF1/WF2/WF4, no integration)
/run-daily-scan --naver-only

# Multi&Global-News only — Run WF4 standalone (skip WF1/WF2/WF3, no integration)
/run-daily-scan --multiglobal-news-only
```

## Options

| Flag | Description |
|------|-------------|
| (none) | Full quadruple scan: WF1 (marathon) → WF2 (arXiv deep) → WF3 (Naver News) → WF4 (Multi&Global-News) → Integrated report |
| `--base-only` | WF1 scans base sources only (skip expansion), WF2/WF3/WF4 run normally |
| `--arxiv-only` | WF2 only: Skip WF1/WF3/WF4, skip integration, produce arXiv report only |
| `--naver-only` | WF3 only: Skip WF1/WF2/WF4, skip integration, produce Naver report only |
| `--multiglobal-news-only` | WF4 only: Skip WF1/WF2/WF3, skip integration, produce Multi&Global-News report only |

## Architecture

This command invokes the **master-orchestrator**, which reads the Source of Truth
(`workflow-registry.yaml`), validates startup conditions, and executes:

```
┌──────────────────────────────────────────────────────┐
│  Step 0: SOT Validation                               │
│    Read workflow-registry.yaml                         │
│    Run validate_registry.py (23 checks)                │
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
│  Step 3: WF3 — Naver News Environmental Scanning       │
│    Sources: NaverNews ONLY (6 sections)                │
│    FSSF 8-type + Three Horizons + Tipping Point        │
│    Checkpoints: Step 2.5 (required), Step 3.4 (required)│
├──────────────────────────────────────────────────────┤
│  Step 4: WF4 — Multi&Global-News Environmental Scanning│
│    Sources: 43 global news sites (11 languages)        │
│    FSSF 8-type + Tipping Point + Translation pipeline  │
│    Checkpoints: Step 2.5 (required), Step 3.4 (required)│
├──────────────────────────────────────────────────────┤
│  Step 5: Integration — Report Merge                    │
│    Merge WF1 + WF2 + WF3 + WF4 reports (pSST ranking) │
│    Cross-workflow analysis (WF1↔WF2↔WF3↔WF4)           │
│    Checkpoint: Final approval (9th checkpoint)          │
└──────────────────────────────────────────────────────┘
```

## What This Command Does

1. **SOT Validation**
   - Reads `env-scanning/config/workflow-registry.yaml`
   - Runs `validate_registry.py` (23 checks: file existence, arXiv placement, no source overlap)
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

4. **WF3: Naver News Environmental Scanning**
   - Phase 1: Crawl Naver News (6 sections: 정치/경제/사회/생활문화/세계/IT과학)
   - Phase 2: FSSF classify → Tipping Point → Priority → **Human review (2.5)**
   - Phase 3: DB update → Report → Archive → **Human approval (3.4)**
   - Output: `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md`

5. **WF4: Multi&Global-News Environmental Scanning**
   - Phase 1: Crawl 43 global news sites (11 languages), translate to English
   - Phase 2: FSSF classify → Tipping Point → Priority → **Human review (2.5)**
   - Phase 3: DB update → Report → Archive → **Human approval (3.4)**
   - Output: `env-scanning/wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md`

6. **Integration: Report Merge**
   - Combine WF1 + WF2 + WF3 + WF4 signals, re-rank by pSST
   - Cross-workflow analysis (WF1↔WF2↔WF3↔WF4: reinforced, academic-early, media-first, naver-exclusive, global-exclusive)
   - Generate integrated report (top 20 signals)
   - **Final human approval (9th checkpoint)**
   - Output: `env-scanning/integrated/reports/daily/integrated-scan-{date}.md`

## Checkpoints (9 total)

| # | Step | Type | Command |
|---|------|------|---------|
| 1 | WF1 Step 2.5 | Required | `/review-analysis` |
| 2 | WF1 Step 3.4 | Required | `/approve` or `/revision` |
| 3 | WF2 Step 2.5 | Required | `/review-analysis` |
| 4 | WF2 Step 3.4 | Required | `/approve` or `/revision` |
| 5 | WF3 Step 2.5 | Required | `/review-analysis` |
| 6 | WF3 Step 3.4 | Required | `/approve` or `/revision` |
| 7 | WF4 Step 2.5 | Required | `/review-analysis` |
| 8 | WF4 Step 3.4 | Required | `/approve` or `/revision` |
| 9 | Integration | Required | `/approve` or `/revision` |

## Output Files

### WF1 (General)
- Report: `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf1-general/signals/database.json`
- Analysis: `env-scanning/wf1-general/analysis/`

### WF2 (arXiv)
- Report: `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf2-arxiv/signals/database.json`
- Analysis: `env-scanning/wf2-arxiv/analysis/`

### WF3 (Naver News)
- Report: `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf3-naver/signals/database.json`
- Analysis: `env-scanning/wf3-naver/analysis/`
- Alerts: `env-scanning/wf3-naver/logs/alerts-{date}.json`

### WF4 (Multi&Global-News)
- Report: `env-scanning/wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md`
- DB: `env-scanning/wf4-multiglobal-news/signals/database.json`
- Archive: `env-scanning/wf4-multiglobal-news/reports/archive/`

### Integrated
- Report: `env-scanning/integrated/reports/daily/integrated-scan-{date}.md`
- Archive: `env-scanning/integrated/reports/archive/{year}/{month}/`

## Error Handling

- **SOT validation failure**: Halt before any scanning
- **WF1 failure**: Option to skip WF1 and run WF2+WF3+WF4 only (degraded integration)
- **WF2 failure**: Option to skip WF2 and run WF1+WF3+WF4 only (degraded integration)
- **WF3 failure**: Option to skip WF3 and run WF1+WF2+WF4 only (degraded integration)
- **WF4 failure**: Option to re-run WF4 / skip WF4 and produce 3-WF integrated report (WF1+WF2+WF3) / halt
- **Integration failure**: Option to use individual reports separately
- **arXiv API unreachable**: WF2 halts with 3 retry attempts; option to skip WF2
- **Naver crawl failure**: WF3 halts with 3 retry attempts; option to skip WF3

## Related Commands

- `/status` - Check current workflow progress
- `/review-filter` - Review filtering results (Step 1.4)
- `/review-analysis` - Review analysis results (Step 2.5)
- `/approve` - Approve report (Step 3.4 / Integration)
- `/revision "feedback"` - Request report revision

## Version
**Command Version**: 6.0.0 (Quadruple Workflow System)
**Last Updated**: 2026-02-24
