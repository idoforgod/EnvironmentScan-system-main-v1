# Claude Code Instructions

@AGENTS.md

---

## Claude Code-Specific Directives

### Agent System

This project uses Claude Code's agent architecture. The orchestration hierarchy is:

```
master-orchestrator.md                    ← Top-level entry point
├── env-scan-orchestrator.md              ← WF1 (General)
├── arxiv-scan-orchestrator.md            ← WF2 (arXiv)
├── naver-scan-orchestrator.md            ← WF3 (Naver News)
├── multiglobal-news-scan-orchestrator.md ← WF4 (Multi&Global-News)
└── workers/
    ├── report-merger.md                  ← Integration
    └── (25+ worker agents)               ← Shared + WF-specific workers
```

Agent definitions live in `.claude/agents/`. Worker agents live in `.claude/agents/workers/`. These define detailed per-step behaviors that extend the methodology in AGENTS.md.

### Slash Commands

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

### Skills

The `env-scanner` skill (`.claude/skills/env-scanner/SKILL.md`) provides the full interface definition. Reference files under `.claude/skills/env-scanner/references/` contain report skeletons, format guides, and STEEPs framework details.

### Task Management

Use `TaskCreate`/`TaskUpdate` tools to track workflow progress through phases. This provides visibility to the user during long-running scans.

### Context Preservation

Context backup hooks in `.claude/hooks/` automatically save workflow state. On session restoration, read `.claude/context-backups/latest-context.md` to resume.

### Development Principles (MANDATORY — applies to ALL code changes)

> **Origin**: v2.1.0 구현에서 CRITICAL 결함 3건이 성찰 과정에서 발견됨.
> 스켈레톤 템플릿 미동기, SOT 검증 규칙 누락, 분기문 ELSE 절 부재.
> 이 원칙들은 동일 유형의 결함이 재발하지 않도록 영구적으로 적용된다.

#### 1. Modification Cascade Rule (수정 연쇄 규칙)

이 시스템은 4개의 결합된 층으로 구성된다:

| Layer | Files | Role |
|-------|-------|------|
| **A. SOT** | `workflow-registry.yaml` | 파라미터 선언 |
| **B. Agent Spec** | `.claude/agents/*.md` | 행동 정의 |
| **C. Skeleton** | `references/*-skeleton.md` | 보고서 구조 |
| **D. Validation** | `validate_registry.py`, `validate_report.py` | 무결성 보장 |

**한 층을 변경하면, 결합된 나머지 층도 반드시 동시에 업데이트한다.**

| 변경 유형 | 필수 연쇄 업데이트 |
|-----------|-------------------|
| 새 SOT 필드 추가 | → Agent Spec 사용 로직 + `validate_registry.py` 체크(SOT-NNN) |
| 새 필수 보고서 섹션 | → Skeleton 서브섹션 + `{{PLACEHOLDER}}` 토큰 |
| 새 SOT 값 기반 분기 | → ELSE/default 절 + 안전한 폴백 경로 |
| 새 검증 규칙 추가 | → SOT `startup_validation.rules`에 규칙 ID 선언 |

#### 2. Unvalidated SOT Is Not SOT (검증 없는 SOT는 SOT가 아니다)

`validate_registry.py`에 검증 규칙이 없는 SOT 필드는 "선언"일 뿐 "보장"이 아니다.
런타임 행동을 제어하는 모든 SOT 필드는 반드시 유효 값 검증 규칙을 가져야 한다.

#### 3. Pre-Completion Checklist (구현 완료 전 필수 확인)

**모든 구현 작업을 "완료"로 선언하기 전에 아래를 반드시 확인한다:**

- [ ] 새 SOT 필드가 있는가? → `validate_registry.py`에 대응 체크 존재하는가?
- [ ] 새 필수 보고서 섹션이 있는가? → 해당 스켈레톤 템플릿에 서브섹션 + 플레이스홀더가 있는가?
- [ ] SOT 값 기반 IF 분기가 있는가? → ELSE/default 절이 있는가?
- [ ] `validate_registry.py` 실행 → 전체 PASS 확인했는가?
- [ ] 유닛 테스트 실행 → 전체 PASS 확인했는가?
