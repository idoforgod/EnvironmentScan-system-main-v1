# Environmental Scanning System

Automated AI-powered environmental scanning system for detecting weak signals of future changes across STEEPs domains.

## 🎯 Absolute Goal

> **Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) "AS FAST AS POSSIBLE".**

**운영 가이드**: 일일 운영 절차, 커맨드 사용법, 설정 변경법은 [USER_GUIDE.md](USER_GUIDE.md)를 참조하세요.

## Overview

This system automates the daily process of scanning global information sources, filtering duplicates, classifying signals, analyzing impacts, and generating strategic reports for decision-makers.

### Key Features

- **Multi-Source Scanning**: Academic papers, patents, policy documents, tech blogs
- **4-Stage Deduplication**: URL → String → Semantic → Entity matching (>95% accuracy)
- **STEEPs Classification**: 6-category framework (Social, Technological, Economic, Environmental, Political, spiritual)
- **Impact Analysis**: Probabilistic Cross-Impact Matrix + Bayesian Network
- **Expert Validation**: Real-Time AI Delphi for high-volume signals (optional)
- **Scenario Generation**: QUEST-based plausible future scenarios (optional)
- **Bilingual Output**: English-first workflow with automatic Korean translation
  - All outputs generated in both EN and KR
  - Korean-first user interface
  - 100% STEEPs terminology preservation
  - High-quality back-translation verification

## Architecture

### Orchestrator-Agent Pattern

```
Orchestrator Agent
    ├── Phase 1: Research (4 workers)
    │   ├── archive-loader
    │   ├── multi-source-scanner
    │   ├── deduplication-filter
    │   └── realtime-delphi-facilitator (optional)
    │
    ├── Phase 2: Planning (4 workers)
    │   ├── signal-classifier
    │   ├── impact-analyzer
    │   ├── priority-ranker
    │   └── scenario-builder (optional)
    │
    └── Phase 3: Implementation (3 workers)
        ├── database-updater
        ├── report-generator
        └── archive-notifier
```

### Human-in-the-Loop Checkpoints

1. **Step 1.4** (optional): Review duplicate filtering
2. **Step 2.5** (required): Review analysis and adjust priorities
3. **Step 3.4** (required): Approve final report

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
# In Claude Code CLI
/run-daily-scan
```

The workflow will:
1. Scan configured sources
2. Filter duplicates
3. Classify and analyze signals
4. Pause for your review
5. Generate Korean report
6. Wait for final approval

### 4. Review and Approve

```bash
# Check progress
/status

# At Step 2.5 - Review analysis
/review-analysis

# At Step 3.4 - Approve report
/approve
```

## Directory Structure

```
EnvironmentScan-system-main/
├── .claude/
│   ├── agents/
│   │   ├── env-scan-orchestrator.md
│   │   └── workers/
│   │       ├── archive-loader.md
│   │       ├── multi-source-scanner.md
│   │       ├── deduplication-filter.md
│   │       └── ... (8 more workers)
│   ├── skills/
│   │   └── env-scanner/
│   │       ├── SKILL.md
│   │       └── references/
│   └── commands/
│       └── env-scan/
│           ├── run.md
│           ├── status.md
│           └── ... (4 more commands)
│
├── env-scanning/
│   ├── config/
│   │   ├── domains.yaml
│   │   ├── sources.yaml
│   │   ├── thresholds.yaml
│   │   └── ml-models.yaml
│   ├── reports/
│   │   ├── daily/
│   │   └── archive/{year}/{month}/
│   ├── signals/
│   │   ├── database.json
│   │   └── snapshots/
│   ├── raw/
│   ├── filtered/
│   ├── structured/
│   ├── analysis/
│   └── logs/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── README.md
```

## Available Commands

- `/run-daily-scan` - Execute full workflow
- `/status` - Check workflow progress
- `/review-filter` - Review duplicate filtering (Step 1.4)
- `/review-analysis` - Review analysis results (Step 2.5)
- `/approve` - Approve final report (Step 3.4)
- `/revision "feedback"` - Request report changes
- `/trigger-delphi` - Manually activate expert validation
- `/generate-scenarios` - Manually activate scenario builder

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

Restore from snapshot:

```bash
cp env-scanning/signals/snapshots/database-{recent-date}.json \
   env-scanning/signals/database.json
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

- **System Version**: 2.0.0 (Bilingual EN-KR)
- **Workflow Version**: Enhanced Environmental Scanning v1.0
- **Translation Layer**: v1.0
- **Last Updated**: 2026-01-30

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
