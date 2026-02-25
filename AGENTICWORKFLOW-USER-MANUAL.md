# Agentic Workflow User Manual

> **Quadruple Environmental Scanning System** | Quick Reference (English)
>
> Version: 5.0 | Last Updated: 2026-02-24

This document is the concise English-language companion to `USER-MANUAL.md`. For the full Korean operational guide, refer to that document.

---

## 1. Quick Start

### Prerequisites

- Python 3.8+
- Claude Code CLI installed
- Internet connection

### First Scan

```bash
# 1. Navigate to project directory and launch Claude Code
cd EnvironmentScan-system-main-v4
claude

# 2. Run full scan (WF1 + WF2 + WF3 + WF4 + Integration)
/env-scan:run

# 3. Follow checkpoint prompts as they appear
```

The system will automatically:
1. Validate SOT (55 rules)
2. WF1: Scan 25+ sources -> analyze -> generate report
3. WF2: Scan arXiv 42 categories -> analyze -> generate report
4. WF3: Crawl Naver News 6 sections -> FSSF classify -> generate report
5. WF4: Crawl 43 global news sites (11 languages) -> FSSF classify -> generate report
6. Integration: Merge 4 reports via Agent-Teams (5 members) -> pSST unified ranking

---

## 2. Available Commands

| Command | Description | When |
|---------|-------------|------|
| `/env-scan:run` | Full scan: WF1+WF2+WF3+WF4+Integration | Daily |
| `/env-scan:run --base-only` | WF1 base sources only + WF2+WF3+WF4+Integration | Quick scan |
| `/env-scan:run --multiglobal-news-only` | WF4 standalone | Global news only |
| `/env-scan:run-arxiv` | WF2 standalone (arXiv only) | Academic focus |
| `/env-scan:run-naver` | WF3 standalone (Naver only) | Korean news focus |
| `/env-scan:run-multiglobal-news` | WF4 standalone (global news) | Global news focus |
| `/env-scan:run-weekly` | Weekly meta-analysis (READ-ONLY, no new scan) | Weekly (Mon) |
| `/env-scan:status` | Check current workflow progress | Anytime |
| `/env-scan:review-filter` | Review dedup filter results (Step 1.4) | Optional |
| `/env-scan:review-analysis` | Review analysis results (Step 2.5) | **Required** |
| `/env-scan:approve` | Approve final report (Step 3.4) | **Required** |
| `/env-scan:revision "feedback"` | Request report revision | As needed |

---

## 3. Daily Operation

### Full Scan Flow

```
/env-scan:run
    |
    +-- SOT Validation (55 rules)
    |
    +-- WF1: General Environmental Scanning
    |   Phase 1: 25+ source scan -> 4-stage dedup
    |   Phase 2: STEEPs classify -> impact analysis -> pSST ranking
    |     -> [REQUIRED] /env-scan:review-analysis
    |   Phase 3: DB update -> report generation
    |     -> [REQUIRED] /env-scan:approve
    |
    +-- WF2: arXiv Academic Deep Scanning
    |   Phase 1: arXiv 42 categories (14-day, 50/category)
    |   Phase 2: STEEPs classify -> impact -> ranking
    |     -> [REQUIRED] /env-scan:review-analysis
    |   Phase 3: DB update -> report
    |     -> [REQUIRED] /env-scan:approve
    |
    +-- WF3: Naver News Scanning
    |   Phase 1: 6 sections crawl -> dedup
    |   Phase 2: STEEPs + FSSF classify -> Tipping Point -> ranking
    |     -> [REQUIRED] /env-scan:review-analysis
    |   Phase 3: DB update -> report
    |     -> [REQUIRED] /env-scan:approve
    |
    +-- WF4: Multi&Global-News Scanning
    |   Phase 1: 43 sites crawl (11 languages) -> translate -> dedup
    |   Phase 2: STEEPs + FSSF classify -> Tipping Point -> ranking
    |     -> [REQUIRED] /env-scan:review-analysis
    |   Phase 3: DB update -> report
    |     -> [REQUIRED] /env-scan:approve
    |
    +-- Integration
        Merge 4 reports -> Agent-Teams 5 -> pSST unified ranking -> Top 20
        -> [REQUIRED] /env-scan:approve
```

### Report Locations

| Report | Path |
|--------|------|
| WF1 General | `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md` |
| WF2 arXiv | `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md` |
| WF3 Naver | `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md` |
| WF4 Global News | `env-scanning/wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md` |
| **Integrated** | `env-scanning/integrated/reports/daily/integrated-scan-{date}.md` |
| Weekly | `env-scanning/integrated/weekly/reports/weekly-scan-{week-id}.md` |

---

## 4. Checkpoints

The system has **9 mandatory human checkpoints**:

| # | Checkpoint | Workflow | What to Review |
|---|------------|----------|----------------|
| 1 | Phase 2.5 Analysis Review | WF1 | STEEPs classification accuracy, priority ranking |
| 2 | Phase 3.4 Report Approval | WF1 | 8 sections complete, 9-field signals, quality |
| 3 | Phase 2.5 Analysis Review | WF2 | Academic signal classification, priority ranking |
| 4 | Phase 3.4 Report Approval | WF2 | Report completeness and quality |
| 5 | Phase 2.5 Analysis Review | WF3 | STEEPs + FSSF classification, Tipping Point levels |
| 6 | Phase 3.4 Report Approval | WF3 | Naver report with FSSF/3H/TP sections |
| 7 | Phase 2.5 Analysis Review | WF4 | STEEPs + FSSF classification, multi-language quality |
| 8 | Phase 3.4 Report Approval | WF4 | Global news report with crawl/translation stats |
| 9 | Integration Approval | All | Cross-WF analysis, unified ranking, completeness |

### At Each Analysis Review (Phase 2.5)

1. **STEEPs classification correct?** -- Check that S/T/E/E/P/s assignments match signal content
2. **Priority ranking reasonable?** -- Top 10 signals should be genuinely important
3. **For WF3/WF4:** FSSF types appropriate? Tipping Point levels reasonable? Three Horizons assignments valid?

### At Each Report Approval (Phase 3.4)

Verify all 8 sections are present and complete:
- Section 1: Executive Summary (Top 3 signals + statistics)
- Section 2: Newly Detected Signals (Top 10, each with 9 fields)
- Section 3: Existing Signal Updates
- Section 4: Patterns and Connections
- Section 5: Strategic Implications
- Section 7: Trust Analysis (pSST distribution)
- Section 8: Appendix

**Actions:** `/env-scan:approve` (accept) or `/env-scan:revision "feedback"` (request changes).

---

## 5. Report Reading Guide

### WF4 Report Specifics

WF4 reports share the standard 8-section structure with additional WF4-specific content:

**Crawling Statistics:**
```
Total 43 sites | Success: 40 | Failed: 2 | Paywall blocked: 1
NYT: Success (Total War attempt 3) | FT: Failed (paywall breach failed)
Average response time: 2.3s | Total articles collected: 287
```

**Translation Statistics:**
```
Source language distribution: EN 45% | KO 12% | JA 10% | ZH 8% | DE 7% | FR 6% | Other 12%
Translation quality (avg): 0.93 | Lowest: 0.87 (Arabic) | Highest: 0.98 (EN->KO)
STEEPs term preservation: 100%
```

**Defense Log (Paywall):**
```
Paywall strategy execution:
  NYT -- Total War: Attempt 1 fail -> Attempt 2 fail -> Attempt 3 success
  WSJ -- Total War: Attempt 1 success
  Bloomberg -- Total War: Unreachable (skipped)
  FT -- Total War: All strategies exhausted (fallback source used)
```

### FSSF Classification (WF3/WF4)

Signals are classified into 8 types with associated priority levels:

| Type | Priority | Description |
|------|----------|-------------|
| Weak Signal | CRITICAL | Low-visibility early indicator |
| Wild Card | CRITICAL | Low probability, extreme impact |
| Discontinuity | CRITICAL | Abrupt break from existing patterns |
| Driver | HIGH | Causal force driving change |
| Emerging Issue | HIGH | Growing attention, not yet mainstream |
| Precursor Event | HIGH | Specific event foreshadowing larger change |
| Trend | MEDIUM | Data-confirmed directional change |
| Megatrend | MEDIUM | Large-scale, long-term macro flow |

### Three Horizons

- **H1** (0-2 years): Short-term developments within current system
- **H2** (2-7 years): Transitional changes, new systems emerging
- **H3** (7+ years): Fundamental transformation, paradigm shifts

### Tipping Point Alert Levels

- **GREEN**: Normal monitoring
- **YELLOW**: Enhanced tracking
- **ORANGE**: Immediate analysis required
- **RED**: Emergency alert dispatched

---

## 6. Configuration

### Key Config Files

| File | Location | What It Controls |
|------|----------|-----------------|
| **SOT** | `env-scanning/config/workflow-registry.yaml` | Everything: workflows, paths, parameters, checkpoints |
| Sources (WF1) | `env-scanning/config/sources.yaml` | 25+ general sources (arXiv excluded) |
| Sources (WF2) | `env-scanning/config/sources-arxiv.yaml` | arXiv categories and parameters |
| Sources (WF3) | `env-scanning/config/sources-naver.yaml` | Naver News sections and crawling settings |
| Sources (WF4) | `env-scanning/config/sources-multiglobal-news.yaml` | 43 global news sites, languages, paywall config |
| Thresholds | `env-scanning/config/thresholds.yaml` | Dedup thresholds, scoring weights, pSST weights |
| Domains | `env-scanning/config/domains.yaml` | STEEPs keyword definitions |
| Translation | `env-scanning/config/translation-terms.yaml` | EN-KO term mappings |
| Invariants | `env-scanning/config/core-invariants.yaml` | Immutable system boundaries |
| SIE | `env-scanning/config/self-improvement-config.yaml` | Self-improvement engine settings |

### After Any Config Change

Always run validation:

```bash
python3 env-scanning/scripts/validate_registry.py
```

All 55 rules must PASS before workflows can execute.

---

## 7. Troubleshooting

### SOT Validation Failure

```bash
python3 env-scanning/scripts/validate_registry.py
```

| Severity | Meaning | Action |
|----------|---------|--------|
| HALT | Workflow cannot run | Fix the failing rule |
| CREATE | Directory auto-created | Resolved automatically |
| WARN | Warning only | Review and fix if needed |

**Common failures:**

| Rule | Cause | Fix |
|------|-------|-----|
| SOT-001 | Shared file path error | Verify file exists, correct path |
| SOT-005 | Data directory missing | Auto-created |
| SOT-010 | arXiv in WF1 | Disable arXiv in sources.yaml |
| SOT-012 | Source overlap between WFs | Ensure each source in exactly one WF |
| SOT-030 | WF4 orchestrator missing | Create multiglobal-news-orchestrator.md |

### Report Validation Failure

```bash
python3 env-scanning/scripts/validate_report.py <report-file-path>
```

System auto-retries up to 2 times with progressive escalation on CRITICAL failures.

### WF3 Naver Block

CrawlDefender automatically applies 7 strategies in cascade. If all fail, the workflow pauses. Wait and retry:

```bash
/env-scan:run-naver
```

### WF4 Paywall Failure

Total War strategy auto-retries for premium sites (NYT, FT, WSJ, Bloomberg). If all strategies exhausted, the site is skipped and logged. The workflow continues with remaining sites:

```bash
/env-scan:run --multiglobal-news-only
```

### Database Recovery

Each workflow creates pre-update snapshots automatically:

```bash
ls env-scanning/wf1-general/signals/snapshots/
ls env-scanning/wf4-multiglobal-news/signals/snapshots/
```

### Context Loss

If a Claude Code session is interrupted:

```bash
# Restart Claude Code
claude

# Context Preservation hooks auto-detect and prompt restoration
# Check workflow state
/env-scan:status
```

All collected data (raw/, structured/) is persisted to disk and never lost.

---

## Document Map

| Document | Language | Purpose |
|----------|----------|---------|
| `USER-MANUAL.md` | Korean | Full operational guide (1400+ lines) |
| **This document** | English | Quick operational reference |
| `WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | Korean | Full technical specification |
| `AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | English | Concise technical reference |
| `decision-log.md` | English | WF4 architectural decisions |
| `AGENTS.md` | English | Cross-platform methodology |

---

**Document Version**: 5.0
**Last Updated**: 2026-02-24
**System Version**: Quadruple Workflow System v2.5.0
