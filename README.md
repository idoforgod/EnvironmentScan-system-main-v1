# Quadruple Environmental Scanning System

Automated AI-powered environmental scanning system for detecting weak signals of future changes across STEEPs domains. The system runs **4 independent workflows** (General, arXiv, Naver News, Multi&Global-News) that are integrated into a unified strategic report.

## 🎯 Absolute Goal

> **Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) "AS FAST AS POSSIBLE".**

**운영 가이드**: 일일 운영 절차, 커맨드 사용법, 설정 변경법은 [USER_GUIDE.md](USER_GUIDE.md)를 참조하세요.

## Overview

This system automates the daily process of scanning global information sources across 4 independent workflows, filtering duplicates, classifying signals, analyzing impacts, and generating strategic reports for decision-makers.

### 4 Independent Workflows

| Workflow | Scope | Sources |
|----------|-------|---------|
| **WF1** General | Patents, policy, tech blogs | Multi-source (arXiv excluded) |
| **WF2** arXiv | Academic papers | arXiv only |
| **WF3** Naver News | Korean news | Naver News only |
| **WF4** Multi&Global-News | Global multilingual news | 43 direct news sites, 11 languages |

Each workflow is fully independent -- it cannot see or access any other workflow's data. Integration happens only at the final report stage.

### Key Features

- **Quadruple Workflow Architecture**: 4 independent scanning pipelines with unified integration
- **Multi-Source Scanning**: Academic papers, patents, policy documents, tech blogs, Korean news, global multilingual news
- **4-Stage Deduplication**: URL → String → Semantic → Entity matching (>95% accuracy)
- **STEEPs Classification**: 6-category framework (Social, Technological, Economic, Environmental, Political, spiritual)
- **FSSF 8-Type Classification** (WF3/WF4): Weak Signal, Wild Card, Discontinuity, Driver, Emerging Issue, Precursor Event, Trend, Megatrend
- **Three Horizons** (WF3/WF4): H1 (0-2yr), H2 (2-7yr), H3 (7yr+)
- **Tipping Point Detection** (WF3/WF4): Critical Slowing Down and Flickering pattern analysis
- **Python 원천봉쇄**: "계산은 Python이, 판단은 LLM이" — deterministic scoring, dedup, temporal filtering, pipeline gates all Python-enforced
- **Hallucination Prevention**: Pipeline Gate 2 (`validate_phase2_output.py`, 8 PG2 checks), translation TERM fidelity (TERM-001~003), executive summary cross-reference (QC-014)
- **Unified Phase 2 Agent**: `phase2-analyst.md` handles Steps 2.1+2.2 (LLM); Step 2.3 delegated to `priority_score_calculator.py` (Python)
- **Timeline Map with Challenge-Response**: Cross-theme strategic synthesis via adversarial peer review (challenger agent → narrative refinement), Python narrative gate (NG-001~005), full L2a+L2b+L3 quality parity
- **4-Layer Quality Defense**: L1 (Skeleton-Fill) → L2a (structural 15–20 checks) → L2b (14 QC checks) → L3 (LLM semantic review) → L4 (Golden Reference)
- **Impact Analysis**: Probabilistic Cross-Impact Matrix + Bayesian Network
- **Expert Validation**: Real-Time AI Delphi for high-volume signals (optional)
- **Scenario Generation**: QUEST-based plausible future scenarios (optional)
- **Bilingual Output**: English-first workflow with automatic Korean translation
  - All outputs generated in both EN and KR
  - Korean-first user interface
  - 100% STEEPs terminology preservation
  - High-quality back-translation verification
- **WF4 Multilingual Pipeline**: 11-language source scanning with English-first translation pipeline

## Architecture

### Quadruple Orchestrator-Agent Pattern

```
Master Orchestrator
├── WF1: env-scan-orchestrator (General)
│   ├── Phase 1: Research (4 workers)
│   ├── Phase 2: Planning (4 workers)
│   └── Phase 3: Implementation (3 workers)
│
├── WF2: arxiv-scan-orchestrator (arXiv)
│   ├── Phase 1: Research (4 workers)
│   ├── Phase 2: Planning (4 workers)
│   └── Phase 3: Implementation (3 workers)
│
├── WF3: naver-scan-orchestrator (Naver News)
│   ├── Phase 1: Research (4 workers)
│   ├── Phase 2: Planning (4 workers + FSSF)
│   └── Phase 3: Implementation (3 workers)
│
├── WF4: multiglobal-news-scan-orchestrator (Multi&Global-News)
│   ├── Phase 1: Research (4 workers + multilingual translation)
│   ├── Phase 2: Planning (4 workers + FSSF)
│   └── Phase 3: Implementation (3 workers)
│
├── Timeline Map: timeline-map-orchestrator
│   ├── Phase A: Data Foundation (Python: theme discovery + data assembly)
│   ├── Phase B: Narrative Analysis with Challenge-Response
│   │   ├── B1: @timeline-narrative-analyst (draft)
│   │   ├── B2: @timeline-quality-challenger (adversarial review)
│   │   ├── B3: @timeline-narrative-analyst (refinement)
│   │   └── B4: narrative_gate.py (Python verification)
│   ├── Phase C: Assembly (skeleton fill + composer)
│   └── Phase D: Quality Defense (L2a + L2b + L3)
│
└── Integration: report-merger
    └── Agent Team (5 members: wf1-analyst, wf2-analyst, wf3-analyst, wf4-analyst, synthesizer)
```

Shared workers across all workflows: archive-loader, multi-source-scanner, deduplication-filter, **phase2-analyst** (unified Steps 2.1+2.2), report-generator, database-updater, archive-notifier, quality-reviewer, self-improvement-analyzer, and more (42 agent specs total). Step 2.3 priority ranking is handled by `priority_score_calculator.py` (Python 원천봉쇄). Timeline Map uses Challenge-Response pattern: `timeline-narrative-analyst` + `timeline-quality-challenger` + `timeline-map-composer`.

### Human-in-the-Loop Checkpoints (9 total)

Per workflow (x4):
1. **Phase 2.5** (required): Review analysis and adjust priorities
2. **Phase 3.4** (required): Approve final report

After integration (x1):
3. **Integrated Report Approval** (required): Approve merged quadruple report

## Quick Start

### 1. Installation

```bash
# Clone repository
cd /path/to/EnvironmentScan-system-main

# Install dependencies
pip install -r requirements.txt  # If Python scripts used

# Configure API keys
export SERPAPI_KEY="your_key_here"
```

### 2. Configuration

Edit configuration files in `env-scanning/config/`:

- `domains.yaml` - Adjust STEEPs keywords
- `sources.yaml` - Enable/disable sources, add API keys
- `thresholds.yaml` - Tune filtering thresholds
- `ml-models.yaml` - Configure AI models

### 3. Run First Scan

```bash
# In Claude Code CLI — full quadruple scan (WF1 + WF2 + WF3 + WF4 + Integration)
/env-scan:run
```

The workflow will:
1. Execute WF1 (General), WF2 (arXiv), WF3 (Naver), WF4 (Multi&Global-News) sequentially
2. Each workflow: scan sources → filter duplicates → classify → analyze → pause for review → generate report → wait for approval
3. Merge all 4 approved reports into a unified integrated report
4. Wait for final integrated report approval

### 4. Review and Approve

```bash
# Check progress
/env-scan:status

# At Phase 2.5 - Review analysis
/env-scan:review-analysis

# At Phase 3.4 - Approve report
/env-scan:approve
```

## Directory Structure

```
EnvironmentScan-system-main/
├── .claude/
│   ├── agents/
│   │   ├── master-orchestrator.md
│   │   ├── env-scan-orchestrator.md              (WF1)
│   │   ├── arxiv-scan-orchestrator.md             (WF2)
│   │   ├── naver-scan-orchestrator.md             (WF3)
│   │   ├── multiglobal-news-scan-orchestrator.md  (WF4)
│   │   └── workers/                               (25+ shared workers)
│   ├── skills/
│   │   └── env-scanner/
│   │       ├── SKILL.md
│   │       └── references/                        (10 skeleton files)
│   └── commands/
│       └── env-scan/
│           ├── run.md
│           ├── status.md
│           └── ... (7 more commands)
│
├── env-scanning/
│   ├── config/
│   │   ├── workflow-registry.yaml   ← SOT (Source of Truth)
│   │   ├── core-invariants.yaml
│   │   ├── domains.yaml
│   │   ├── sources.yaml             (WF1)
│   │   ├── sources-arxiv.yaml       (WF2)
│   │   ├── sources-naver.yaml       (WF3)
│   │   ├── sources-multiglobal-news.yaml  (WF4)
│   │   ├── thresholds.yaml
│   │   ├── translation-terms.yaml
│   │   └── ... (12 config files total)
│   ├── core/                        (36 Python modules, incl. priority_score_calculator.py)
│   ├── scripts/                     (validation scripts: validate_registry, validate_report, validate_report_quality, validate_phase2_output, validate_timeline_map, validate_timeline_map_quality, narrative_gate, validate_completion, validate_state_consistency)
│   ├── wf1-general/                 ← WF1 data directory
│   │   ├── raw/ structured/ filtered/ analysis/ signals/ reports/
│   │   └── exploration/             (v2.5.0 source exploration)
│   ├── wf2-arxiv/                   ← WF2 data directory
│   │   └── raw/ structured/ filtered/ analysis/ signals/ reports/
│   ├── wf3-naver/                   ← WF3 data directory
│   │   └── raw/ structured/ filtered/ analysis/ signals/ reports/
│   ├── wf4-multiglobal-news/        ← WF4 data directory
│   │   └── raw/ structured/ filtered/ analysis/ signals/ reports/
│   └── integrated/                  ← Merged output
│       ├── reports/daily/
│       ├── reports/archive/{year}/{month}/
│       └── weekly/
│
├── tests/                           (28 test files, ~995 tests)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── AGENTS.md                        ← Cross-platform methodology
├── CLAUDE.md                        ← Claude Code directives
├── GEMINI.md                        ← Gemini CLI directives
└── README.md
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/env-scan:run` | Execute full quadruple scan (WF1 + WF2 + WF3 + WF4 + Integration) |
| `/env-scan:run-arxiv` | WF2 standalone (arXiv only) |
| `/env-scan:run-naver` | WF3 standalone (Naver News only) |
| `/env-scan:run-multiglobal-news` | WF4 standalone (Multi&Global-News only) |
| `/env-scan:run-weekly` | Weekly meta-analysis (no new scanning) |
| `/env-scan:status` | Check current workflow progress |
| `/env-scan:review-filter` | Review duplicate filtering results |
| `/env-scan:review-analysis` | Review analysis and adjust priorities |
| `/env-scan:approve` | Approve final report |
| `/env-scan:revision` | Request report revision with feedback |

## STEEPs Framework

The 6-category classification system (IMMUTABLE):

- **S** - Social (demographics, education, labor)
- **T** - Technological (innovation, digital transformation)
- **E** - Economic (markets, finance, trade)
- **E** - Environmental (climate, sustainability)
- **P** - Political (policy, law, regulation, institutions)
- **s** - spiritual (ethics, psychology, values, meaning)

See `.claude/skills/env-scanner/references/steep-framework.md` for detailed definitions.

## Performance Targets

- **Duplicate detection accuracy**: > 95%
- **Processing time reduction**: 30% vs baseline
- **Signal detection speed**: 2x vs manual
- **Expert feedback time**: < 3 days (if Delphi activated)

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run end-to-end test
pytest tests/e2e/
```

## Troubleshooting

### Issue: Low filter rate (< 30%)

Check if sources are returning old content. Verify date filters in `config/sources.yaml`.

### Issue: Database corruption

Restore from snapshot (each workflow has its own database):

```bash
# Example for WF1:
cp env-scanning/wf1-general/signals/snapshots/database-{recent-date}.json \
   env-scanning/wf1-general/signals/database.json
```

### Issue: Classification errors

Review STEEPs definitions in `config/domains.yaml`. Check AI model configuration in `config/ml-models.yaml`.

## Contributing

This system uses Claude Code's agent architecture. To modify:

1. **Agents**: Edit files in `.claude/agents/`
2. **Commands**: Edit files in `.claude/commands/env-scan/`
3. **Configuration**: Edit YAML files in `env-scanning/config/`

All agent instructions are written in **English** for optimal AI performance. The bilingual workflow automatically translates outputs to Korean while preserving technical terminology.

## Bilingual Workflow

### English-First, Korean Always

The system operates in **English** for optimal AI performance, then automatically translates all outputs to **Korean**:

```
Agent (EN) → Output (EN) → Translation Agent → Output (KR)
```

**File Naming Convention**:
- English: `environmental-scan-2026-01-30.md`
- Korean: `environmental-scan-2026-01-30-ko.md`

**What Gets Translated**:
- Reports (Markdown)
- Signal classifications (JSON)
- Analysis results (JSON)
- Log summaries (Log files)
- Quality metrics (JSON)

**What Stays English-Only**:
- `database.json` (data integrity)
- Configuration files
- Agent instructions
- Technical field names

**Translation Quality**:
- Average confidence: >0.90
- STEEPs term preservation: 100%
- Back-translation verification: Enabled
- Processing overhead: ~22% (+40s per workflow)

## Version

- **System Version**: 3.2.0 (Quadruple Workflow, Bilingual EN-KR, Python 원천봉쇄, Hallucination Prevention, Timeline Map Challenge-Response)
- **Workflow Version**: Quadruple Environmental Scanning v3.2.0
- **Architecture**: 42 agent specs, 36 Python modules + 9 validation scripts, 12 config files, 14 skeleton files, 28 test files (~1069 tests)
- **Validation**: 61 SOT checks (SOT-001~061), 4-layer quality defense (L1→L4), 14 QC checks (L2b), 8 PG2 checks, 11 Timeline QC checks (TQ-001~011), 5 narrative gate checks (NG-001~005), 3 TERM fidelity checks
- **Last Updated**: 2026-03-09

## References

Academic foundations:
- [WISDOM Framework](https://arxiv.org/html/2409.15340v1)
- [Real-Time AI Delphi](https://www.sciencedirect.com/science/article/pii/S0016328725001661)
- [Cross-Impact Analysis](https://onlinelibrary.wiley.com/doi/full/10.1002/ffo2.165)
- [Millennium Project Futures Research Methodology](https://www.millennium-project.org/publications/futures-research-methodology-version-3-0-2/)

## License

Internal use only.

## Support

For issues:
1. Check logs in `env-scanning/logs/`
2. Review quality metrics in `logs/quality-metrics/`
3. Check orchestrator state in `logs/workflow-status.json`
