---
name: env-scanner
description: Triple Workflow Environmental Scanning System — WF1 (general multi-source) + WF2 (arXiv academic deep scan) + WF3 (Naver News with FSSF/Tipping Point) with integrated report. Use when the user wants to (1) run daily environmental scanning, (2) check scanning workflow status, (3) review or approve scanning results, or (4) manage the signals database.
agent: master-orchestrator
---

# Environmental Scanner Skill

## Description
Triple Workflow Environmental Scanning System for detecting weak signals of future changes across STEEPs domains (Social, Technological, Economic, Environmental, Political, spiritual). Operates three completely independent workflows — WF1 (general multi-source), WF2 (arXiv academic deep scan), and WF3 (Naver News with FSSF classification, Three Horizons tagging, and Tipping Point detection) — each producing independently complete reports, which are then merged into a unified integrated report.

## Purpose
Enable systematic daily scanning of global information sources to catch early signals of trends, paradigm shifts, and emerging futures "AS FAST AS POSSIBLE" across Korea, Asia, Europe, Africa, and Americas — from mainstream sources, academic research, and Korean media.

---

## Architecture

### Triple Workflow System

```
┌─────────────────────────────────────────────────┐
│  Master Orchestrator                             │
│    SOT: workflow-registry.yaml (23 checks)       │
├─────────────────────────────────────────────────┤
│  WF1: General Environmental Scanning             │
│    Sources: 20+ (patents, policy, blogs, etc.)   │
│    arXiv: EXCLUDED                               │
│    Checkpoints: 2 (Step 2.5, Step 3.4)          │
├─────────────────────────────────────────────────┤
│  WF2: arXiv Academic Deep Scanning               │
│    Sources: arXiv ONLY (30+ categories)          │
│    Parameters: 14 days, 50/category              │
│    Checkpoints: 2 (Step 2.5, Step 3.4)          │
├─────────────────────────────────────────────────┤
│  WF3: Naver News Environmental Scanning          │
│    Sources: NaverNews ONLY (6 sections)          │
│    FSSF 8-type + Three Horizons + Tipping Point  │
│    Checkpoints: 2 (Step 2.5, Step 3.4)          │
├─────────────────────────────────────────────────┤
│  Integration: Report Merger                      │
│    Merge: pSST unified ranking (top 20)          │
│    Cross-workflow analysis (WF1↔WF2↔WF3)        │
│    Checkpoint: 1 (final approval)                │
└─────────────────────────────────────────────────┘
```

**Independence**: WF1, WF2, and WF3 are completely independent — separate data directories, separate signal databases, no runtime data sharing. Any can be disabled or run standalone without affecting the others.

**Source of Truth**: `env-scanning/config/workflow-registry.yaml` — single authoritative definition validated at startup.

---

## Commands

This skill provides the following slash commands:

- `/run-daily-scan` - Execute full dual scan (WF1 + WF2 + Integration)
- `/run-daily-scan --base-only` - WF1 base sources only + WF2 + Integration
- `/run-daily-scan --arxiv-only` - WF2 only (standalone arXiv scan)
- `/run-arxiv-scan` - WF2 standalone (alias for --arxiv-only)
- `/run-naver-scan` - WF3 standalone (Naver News with FSSF/Tipping Point)
- `/run-weekly-scan` - Execute weekly meta-analysis (no new scanning, analyzes last 7 days)
- `/status` - Check current workflow progress
- `/review-filter` - Review duplicate filtering results (Step 1.4)
- `/review-analysis` - Review analysis results and adjust priorities (Step 2.5)
- `/approve` - Approve report (Step 3.4 / Integration)
- `/revision "feedback"` - Request report revision with specific feedback
- `/trigger-delphi` - Manually activate expert panel validation (Phase 1.5)
- `/generate-scenarios` - Manually activate scenario builder (Step 7.5)

---

## Workflow Overview

### Execution Flow: WF1 → WF2 → WF3 → Integration

Each workflow (WF1, WF2) follows the same 3-phase structure:

### Phase 1: Research (Information Collection)
1. Load historical signals database (each workflow has its own)
2. Scan sources (WF1: multi-source marathon / WF2: arXiv deep scan)
3. Filter duplicates using 4-stage cascade (URL → String → Semantic → Entity)
4. (Optional) Expert panel validation if >50 new signals

### Phase 2: Planning (Analysis & Structuring)
1. Classify signals into STEEPs categories
2. Analyze impacts using Probabilistic Cross-Impact Matrix
3. Rank by priority (Impact 40%, Probability 30%, Urgency 20%, Novelty 10%)
4. (Optional) Generate plausible scenarios

### Phase 3: Implementation (Report Generation)
1. Update signals database with backups
2. Generate comprehensive Korean report (skeleton-fill method)
3. Archive report and send notifications
4. Self-Improvement Analysis (independent per workflow)

---

## Usage

### Basic Usage

```bash
# Full dual scan (WF1 marathon + WF2 arXiv + Integration)
/run-daily-scan

# WF1 base sources only + WF2 + Integration
/run-daily-scan --base-only

# WF2 standalone (arXiv only, no WF1, no integration)
/run-arxiv-scan

# Check progress
/status

# At Human Review checkpoints, use:
/review-filter    # Optional review at Step 1.4
/review-analysis  # Required review at Step 2.5
/approve          # Approve report at Step 3.4 / Integration
```

### Execution Modes

**Full Triple Scan** (default): WF1 marathon → WF2 arXiv deep → WF3 Naver News → Integrated report
- 7 human checkpoints, top 20 signals in integrated report
- WF1 scans 20+ sources; WF2 scans arXiv 30+ categories; WF3 crawls Naver 6 sections

**arXiv Standalone**: WF2 only, produces independent arXiv academic report
- 2 human checkpoints, no integration
- Use when you need academic-focused signals only

**Naver Standalone**: WF3 only, produces independent Naver report with FSSF/Tipping Point
- 2 human checkpoints, no integration
- Use when you need Korean mainstream media signals only

### Advanced Usage

```bash
# Manually trigger optional features
/trigger-delphi          # Activate expert validation
/generate-scenarios      # Create plausible future scenarios

# Request revisions
/revision "상위 5개 신호에 대해 더 자세한 분석 추가"
```

---

## Configuration

### Source of Truth
- `env-scanning/config/workflow-registry.yaml` - **SOT** — single authoritative definition of the dual workflow system

### Shared Configs (read-only reference)
- `env-scanning/config/domains.yaml` - STEEPs domain definitions and keywords
- `env-scanning/config/thresholds.yaml` - Filtering and scoring thresholds
- `env-scanning/config/core-invariants.yaml` - Immutable workflow boundaries (SIE safety)
- `env-scanning/config/self-improvement-config.yaml` - Self-Improvement Engine settings

### Workflow-Specific Configs
- `env-scanning/config/sources.yaml` - WF1 data sources (arXiv disabled)
- `env-scanning/config/sources-arxiv.yaml` - WF2 data sources (arXiv only, extended)
- `env-scanning/config/sources-naver.yaml` - WF3 data sources (NaverNews only, crawl)

---

## Output Files

### WF1 (General) — `env-scanning/wf1-general/`
- Report: `reports/daily/environmental-scan-{date}.md`
- Database: `signals/database.json`
- Archive: `reports/archive/{year}/{month}/`

### WF2 (arXiv) — `env-scanning/wf2-arxiv/`
- Report: `reports/daily/environmental-scan-{date}.md`
- Database: `signals/database.json`
- Archive: `reports/archive/{year}/{month}/`

### WF3 (Naver News) — `env-scanning/wf3-naver/`
- Report: `reports/daily/environmental-scan-{date}.md`
- Database: `signals/database.json`
- Archive: `reports/archive/{year}/{month}/`
- Alerts: `logs/alerts-{date}.json`
- Tipping Points: `analysis/tipping-point-indicators-{date}.json`

### Integrated — `env-scanning/integrated/`
- Report: `reports/daily/integrated-scan-{date}.md`
- Archive: `reports/archive/{year}/{month}/`

### Self-Improvement (per workflow)
- WF1: `env-scanning/wf1-general/self-improvement/`
- WF2: managed within WF2 data root

---

## Self-Improvement Engine (Step 3.6)

After quality metrics are generated, the system automatically analyzes performance and tunes parameters:

- **MINOR changes** (threshold ±10%, timeout adjustments): Auto-applied safely
- **MAJOR changes** (behavioral changes): Proposed for user approval
- **CRITICAL changes** (core invariant violations): Always blocked

Safety boundaries are defined in `config/core-invariants.yaml`. Workflow phases, human checkpoints, STEEPs categories, and the VEV protocol can never be modified by the engine.

Analysis covers 5 areas: threshold tuning, agent performance, classification quality, workflow efficiency, and hallucination tracking. SIE failure never halts the main workflow.

---

## Quality Standards

### Performance Targets
- Duplicate detection accuracy: > 95%
- Processing time reduction: 30% vs baseline
- Signal detection speed: 2x vs manual
- Expert feedback time: < 3 days (if Phase 1.5 activated)

### Quality Metrics
- Precision and Recall for deduplication
- Classification accuracy for STEEPs
- Human-AI agreement scores
- Report completeness checklist

### Task Verification Protocol (v2.2.0)

Every workflow step is governed by the **VEV (Verify-Execute-Verify)** protocol:

- **Pre-Verification**: Precondition checks before each step execution
- **Post-Verification (3-Layer)**:
  - Layer 1 (Structural): File existence, JSON validity, schema compliance
  - Layer 2 (Functional): Data integrity, count accuracy, range validation
  - Layer 3 (Quality): Accuracy targets, completeness, consistency
- **Retry Protocol**: Automatic re-execution on Layer 1/2 failure (max 2 retries)
- **Pipeline Gates**: Data continuity checks between Phase 1→2, Phase 2→3, Phase 3 completion

Verification results are recorded in `logs/verification-report-{date}.json` and summarized in quality metrics.

See orchestrator protocol (`.claude/agents/protocols/orchestrator-protocol.md`) for full specification.

---

## STEEPs Framework (Core Classification)

**6 Categories (IMMUTABLE)**:

- **S** - Social (demographics, education, labor - NO spiritual)
- **T** - Technological (innovation, digital transformation)
- **E** - Economic (markets, finance, trade)
- **E** - Environmental (climate, sustainability, resources)
- **P** - Political (policy, law, regulation, institutions, geopolitics)
- **s** - spiritual (ethics, psychology, values, meaning, AI ethics)

---

## Example Workflow Execution

```bash
# Morning: 6:00 AM (automated trigger — marathon mode by default)
/run-daily-scan

# System executes Phase 1 (Steps 1-3)
# ... Scanning 26 sources (6 base + 20 expansion) ...
# ... Found 450+ items ...
# ... Filtered to 120 new signals ...

# Step 1.4: Optional human review
# (If AI confidence low, system prompts: "Run /review-filter to inspect")

# Phase 2 executes (Steps 5-7)
# ... Classified signals ...
# ... Analyzed impacts ...
# ... Ranked by priority ...

# Step 2.5: Required human review
/review-analysis
# User reviews top 10 signals, makes adjustments

# Phase 3 executes (Steps 9-11)
# ... Updated database ...
# ... Generated Korean report ...
# ... Archived and notified ...

# Step 3.4: Final approval
/approve

# ✅ Workflow complete!
```

---

## Troubleshooting

### Common Issues

**Issue**: Low filter rate (< 30%)
**Solution**: Check if sources are returning old content. Verify date filters.

**Issue**: Too many signals (> 100)
**Solution**: Adjust keyword specificity in `config/domains.yaml`

**Issue**: Classification errors
**Solution**: Review STEEPs definitions in `config/domains.yaml`, adjust LLM prompt

**Issue**: Database corruption
**Solution**: Restore from `signals/snapshots/database-{recent-date}.json`

---

## Dependencies

### Required
- Claude Code CLI (version >= 1.0)
- Python 3.9+ (for utility scripts)
- API keys for data sources (Google Scholar, etc.)

### Optional
- SBERT model for semantic similarity
- Expert panel contact list for Phase 1.5
- Slack/Email notification setup

---

## References

See `references/` directory for:
- `steep-framework.md` - Detailed STEEPs definitions
- `signal-template.md` - Standard signal structure
- `report-format.md` - Report generation guidelines
- `report-skeleton.md` - Individual workflow report skeleton (10 signals)
- `integrated-report-skeleton.md` - Integrated report skeleton (15 signals)

---

## Version
- **Skill Version**: 3.0.0 (Triple Workflow System)
- **Compatible with**: Claude Code v1.0+
- **System Version**: 2.0.0 (Triple Workflow + SOT + Integration)
- **Sources Version**: 5.0.0 (arXiv → WF2, NaverNews → WF3)
- **Protocol Version**: 2.2.0 (VEV + Pipeline Gates)
- **Last Updated**: 2026-02-06

---

## Support

For issues or questions:
1. Check logs in `env-scanning/logs/`
2. Review quality metrics in `logs/quality-metrics/`
3. Consult orchestrator state in `logs/workflow-status.json`
