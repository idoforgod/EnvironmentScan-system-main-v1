---
name: run-naver-scan
description: Execute WF3 (Naver News Environmental Scanning) as a standalone workflow
context: fork
---

# Run Naver News Environmental Scan (WF3 Standalone)

Execute WF3 independently — Naver News crawling with FSSF classification, Three Horizons tagging, and Tipping Point detection.
This produces a complete, independently valid report without requiring WF1, WF2, or integration.

## Usage

```bash
/run-naver-scan
```

## What This Command Does

This command invokes the **master-orchestrator** in WF3-only mode:

1. **SOT Validation** — Same startup validation (SOT-001 through SOT-023)
2. **WF3 Execution** — Full 3-phase pipeline on Naver News only
3. **No WF1/WF2** — WF1 and WF2 are skipped entirely
4. **No Integration** — No report merge (WF3 report is the final output)

### WF3 Parameters

| Parameter | Value |
|-----------|-------|
| Source | NaverNews only (6 sections) |
| Sections | 정치, 경제, 사회, 생활문화, 세계, IT과학 |
| FSSF Classification | 8-type signal taxonomy |
| Three Horizons | H1 (0-2yr), H2 (2-7yr), H3 (7yr+) |
| Tipping Point | Critical Slowing Down + Flickering detection |
| Anomaly Detection | Statistical + Structural |

### WF3 Phases

- **Phase 1**: Crawl Naver News 6 sections, noise filter, deduplicate
- **Phase 2**: STEEPs + FSSF classify → Impact + Tipping Point → Priority → **Human review (required)**
- **Phase 3**: DB update → Report (naver skeleton) → Archive + Alert → **Human approval (required)**

## Checkpoints (2 total)

| # | Step | Type | Command |
|---|------|------|---------|
| 1 | WF3 Step 2.5 | Required | `/review-analysis` |
| 2 | WF3 Step 3.4 | Required | `/approve` or `/revision` |

## Output

- Report: `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md`
- Database: `env-scanning/wf3-naver/signals/database.json`
- Archive: `env-scanning/wf3-naver/reports/archive/{year}/{month}/`
- Alerts: `env-scanning/wf3-naver/logs/alerts-{date}.json`
- Tipping Points: `env-scanning/wf3-naver/analysis/tipping-point-indicators-{date}.json`

## When to Use

- When you need Korean mainstream media signals only
- When WF1+WF2 have already been run and you want supplementary Naver data
- When Naver crawling failed during a triple scan and you want to retry WF3
- When you need FSSF / Three Horizons / Tipping Point analysis specifically

## Error Handling

- **Naver crawl blocked**: CrawlDefender 7-strategy cascade (automatic escalation)
- **Low article count** (< 50): Re-crawl with increased delays, then prompt user
- **All strategies exhausted**: User prompted to configure proxy or abort

## Related Commands

- `/run-daily-scan` - Full triple scan (WF1 + WF2 + WF3 + Integration)
- `/run-arxiv-scan` - WF2 standalone (arXiv only)
- `/status` - Check workflow progress
- `/approve` - Approve final report

## Version
**Command Version**: 1.0.0
**Last Updated**: 2026-02-06
