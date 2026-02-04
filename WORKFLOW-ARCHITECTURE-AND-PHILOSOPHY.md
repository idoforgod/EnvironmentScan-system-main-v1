# WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY

> **Environmental Scanning System** | 워크플로우 아키텍처와 철학
>
> Version: 1.0.0 | Last Updated: 2026-01-31

---

**운영 가이드**: 일일 운영 절차, 커맨드 사용법 등 실무 가이드는 [USER_GUIDE.md](USER_GUIDE.md)를 참조하세요. 본 문서는 시스템의 기술 명세입니다.

## 목차

1. [철학과 핵심 목표](#제1장-철학과-핵심-목표)
2. [아키텍처 전체도와 오케스트레이터](#제2장-아키텍처-전체도와-오케스트레이터)
3. [VEV 프로토콜과 검증 체계](#제3장-vev-프로토콜과-검증-체계)
4. [3단계 워크플로우](#제4장-3단계-워크플로우)
5. [태스크 관리와 실행 흐름](#제5장-태스크-관리와-실행-흐름)
6. [pSST 신뢰도 프레임워크](#제6장-psst-신뢰도-프레임워크)
7. [에이전트 체계](#제7장-에이전트-체계)
8. [자기개선엔진 (SIE)](#제8장-자기개선엔진-sie)
9. [설정과 확장 포인트](#제9장-설정과-확장-포인트)
10. [불변의 경계](#제10장-불변의-경계)

---

## 제1장: 철학과 핵심 목표

### 1.1 절대 목표 (Absolute Goal)

> **"Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) AS FAST AS POSSIBLE."**

이 목표는 시스템의 존재 이유이며, 모든 단계와 기능에 걸쳐 고정 불변(fixed and immutable)이다. "AS FAST AS POSSIBLE"은 워크플로우 실행 속도가 아니라 **신호 포착의 신속성**을 의미한다. 품질을 희생하여 빨리 끝내는 것이 아니라, 세계의 변화를 가능한 한 빠르게 감지하는 것이 핵심이다.

### 1.2 7대 설계 원칙

| # | 원칙 | 출처 | 의미 |
|---|------|------|------|
| 1 | **"Improve the tuning, never break the machine"** | `core-invariants.yaml` | 시스템의 핵심 구조를 변경하지 않고 세부 조정만 허용한다 |
| 2 | **오케스트레이터-워커 분리** | `env-scan-orchestrator.md` | 관리자(오케스트레이터)와 실행자(워커)의 역할을 명확히 분리한다 |
| 3 | **Human-in-the-Loop** | `core-invariants.yaml` | 3개의 인간 검토 체크포인트(1.4, 2.5, 3.4)를 통해 인간의 감독을 보장한다 |
| 4 | **품질 기반 실행** | VEV 프로토콜 | 시간이 아닌 품질 검증을 기준으로 단계를 진행한다 |
| 5 | **통제된 소스 관리** | `core-invariants.yaml` (MAJOR change domain) | 모든 소스는 사전 설정되고, 추가/제거는 사용자 승인을 요한다 |
| 6 | **이중언어 프로토콜** | `core-invariants.yaml` (bilingual_protocol) | 내부 처리는 영어, 외부 출력은 한국어. STEEPs 용어 100% 보존 |
| 7 | **데이터베이스 원자성** | `core-invariants.yaml` (database_atomicity) | DB 업데이트는 반드시 스냅샷 → 원자적 쓰기 → 실패 시 복원 순서를 따른다 |

### 1.3 STEEPs 프레임워크

6개 분류 카테고리는 시스템의 **분류 기반(foundational classification framework)** 이며, 불변이다:

| 코드 | 이름 | 범위 |
|------|------|------|
| **S** | Social | 인구통계, 교육, 노동 (spiritual 제외) |
| **T** | Technological | 혁신, 디지털 전환, AI, 양자 컴퓨팅 |
| **E** | Economic | 시장, 금융, 무역, 플랫폼 경제 |
| **E** | Environmental | 기후, 지속가능성, 자원, 생물다양성 |
| **P** | Political | 정책, 법률, 규제, 제도, 지정학 |
| **s** | spiritual | 윤리, 심리, 가치관, 의미, AI 윤리 |

정의는 `env-scanning/config/domains.yaml`에 키워드와 검색어가 수록되어 있다. 각 카테고리별 12~15개의 키워드가 정의되어 있으며, 배제 키워드(celebrity gossip, sports scores 등)와 언어 우선순위(primary: en/ko, secondary: zh/ja/de/fr/es)도 설정되어 있다.

### 1.4 학술적 기반

| 방법론 | 출처 | 적용 위치 |
|--------|------|----------|
| WISDOM Framework | arXiv:2409.15340v1 | 다중 소스 스캐닝 |
| Real-Time AI Delphi | ScienceDirect | 전문가 패널 검증 (Phase 1.5) |
| Cross-Impact Analysis | Wiley Online Library | 교차영향 매트릭스 (Step 2.2) |
| Millennium Project FRM 3.0 | millennium-project.org | 미래연구 방법론 |

---

## 제2장: 아키텍처 전체도와 오케스트레이터

### 2.1 디렉토리 구조

```
EnvironmentScan-system-main/
├── .claude/
│   ├── agents/
│   │   ├── env-scan-orchestrator.md          ← 마스터 오케스트레이터 (4,070줄)
│   │   └── workers/                          ← 17개 워커 에이전트 + 1 프롬프트 템플릿
│   │       ├── archive-loader.md
│   │       ├── multi-source-scanner.md
│   │       ├── deduplication-filter.md
│   │       ├── signal-classifier.md
│   │       ├── impact-analyzer.md
│   │       ├── priority-ranker.md
│   │       ├── database-updater.md
│   │       ├── report-generator.md
│   │       ├── archive-notifier.md
│   │       ├── translation-agent.md
│   │       ├── self-improvement-analyzer.md
│   │       ├── realtime-delphi-facilitator.md  (조건부)
│   │       ├── scenario-builder.md             (조건부)
│   │       ├── arxiv-agent.md                  (소스별 스캐너)
│   │       ├── patent-agent.md
│   │       ├── policy-agent.md
│   │       ├── blog-agent.md
│   │       └── classification-prompt-template.md  (프롬프트 템플릿, 에이전트 아님)
│   ├── skills/
│   │   └── env-scanner/
│   │       ├── SKILL.md                      ← 스킬 인터페이스
│   │       └── references/
│   │           ├── steep-framework.md
│   │           ├── signal-template.md
│   │           └── report-format.md
│   └── commands/env-scan/
│       ├── run.md          ← /run-daily-scan [--base-only]
│       ├── status.md       ← /status
│       ├── review-filter.md
│       ├── review-analysis.md
│       ├── approve.md
│       └── revision.md
│
├── env-scanning/
│   ├── config/
│   │   ├── domains.yaml                ← STEEPs 키워드 정의
│   │   ├── sources.yaml                ← 2-Tier 소스 아키텍처 (v3.0.0)
│   │   ├── thresholds.yaml             ← 채점/필터링 임계치 + pSST + 마라톤 설정
│   │   ├── ml-models.yaml              ← AI 모델 설정
│   │   ├── translation-terms.yaml      ← 번역 용어 매핑
│   │   ├── core-invariants.yaml        ← 불변 경계 정의
│   │   └── self-improvement-config.yaml ← SIE 설정
│   ├── raw/                  ← 일일 스캔 원본 데이터
│   ├── filtered/             ← 중복 제거 후 데이터
│   ├── structured/           ← 분류된 신호 데이터
│   ├── analysis/             ← 영향 분석 및 우선순위 결과
│   ├── reports/
│   │   ├── daily/            ← 일일 보고서 (EN + KR)
│   │   └── archive/{year}/{month}/
│   ├── signals/
│   │   ├── database.json     ← 마스터 신호 데이터베이스
│   │   └── snapshots/        ← 일별 DB 스냅샷
│   ├── self-improvement/     ← SIE 로그 및 제안
│   ├── calibration/          ← pSST 보정 데이터
│   ├── logs/                 ← 실행 로그 및 검증 보고서
│   └── context/              ← 에이전트 간 공유 컨텍스트
│
├── tests/                    ← 단위/통합/E2E 테스트
├── docs/                     ← 기술 문서
└── prompt/                   ← 원본 워크플로우 설계 문서
```

### 2.2 데이터 흐름도

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (마스터)                              │
│                                                                          │
│   ┌─Phase 1: Research──────────────────────────────────────────────┐     │
│   │                                                                │     │
│   │   [1.1] archive-loader → context/previous-signals.json        │     │
│   │                     ↓                                          │     │
│   │   [1.2] multi-source-scanner                                   │     │
│   │         ├─ Stage A: base sources → raw/daily-scan-{date}.json  │     │
│   │         └─ Stage B: expansion sources (기본, --base-only 시 생략)│     │
│   │                     ↓ (병합)                                    │     │
│   │         → structured/classified-signals-{date}.json            │     │
│   │                     ↓                                          │     │
│   │   [1.3] deduplication-filter → filtered/new-signals-{date}.json│     │
│   │                     ↓                                          │     │
│   │   [1.4] Human Review (선택적) ← /review-filter                 │     │
│   │                     ↓                                          │     │
│   │   ━━━ Pipeline Gate 1 (6개 검증) ━━━                            │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                         ↓                                                │
│   ┌─Phase 2: Planning─────────────────────────────────────────────┐     │
│   │                                                                │     │
│   │   [2.1] signal-classifier (검증/보강)                           │     │
│   │                     ↓                                          │     │
│   │   [2.2] impact-analyzer                                        │     │
│   │         ├─ Futures Wheel                                       │     │
│   │         ├─ Cross-Impact Matrix                                 │     │
│   │         └─ Bayesian Network                                    │     │
│   │                     ↓                                          │     │
│   │   [2.3] priority-ranker → analysis/priority-ranked-{date}.json │     │
│   │                     ↓                                          │     │
│   │   [2.5] Human Review (필수) ← /review-analysis                 │     │
│   │                     ↓                                          │     │
│   │   ━━━ Pipeline Gate 2 (6개 검증) ━━━                            │     │
│   └────────────────────────────────────────────────────────────────┘     │
│                         ↓                                                │
│   ┌─Phase 3: Implementation──────────────────────────────────────┐      │
│   │                                                                │     │
│   │   [3.1] database-updater (CRITICAL)                            │     │
│   │         → signals/database.json + snapshots/                   │     │
│   │                     ↓                                          │     │
│   │   [3.2] report-generator → reports/daily/...md (EN + KR)      │     │
│   │                     ↓                                          │     │
│   │   [3.3] archive-notifier → reports/archive/                    │     │
│   │                     ↓                                          │     │
│   │   [3.4] Human Review (필수) ← /approve 또는 /revision          │     │
│   │                     ↓                                          │     │
│   │   [3.5] Quality Metrics 생성                                   │     │
│   │                     ↓                                          │     │
│   │   [3.6] Self-Improvement Engine (자기개선)                      │     │
│   │                     ↓                                          │     │
│   │   ━━━ Pipeline Gate 3 (6개 검증) ━━━                            │     │
│   └────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 오케스트레이터의 역할

오케스트레이터(`env-scan-orchestrator.md`, 4,070줄)는 시스템의 **유일한 관리자**이다. 모든 의사결정과 검증은 오케스트레이터 수준에서 이루어지며, 워커 에이전트는 순수한 실행자로만 동작한다.

**오케스트레이터의 책임**:

- 워크플로우 상태 관리 (`workflow-status.json`)
- 태스크 계층 생성 및 업데이트
- VEV 프로토콜 적용 (PRE-VERIFY → POST-VERIFY)
- Pipeline Gate 실행
- 인간 체크포인트 관리
- 에러 처리 및 재시도 결정
- 검증 보고서 누적 (`verification-report-{date}.json`)
- 마라톤 모드 시간 예산 관리

**핵심 설계 원칙**: 워커 에이전트는 수정하지 않는다. 모든 검증은 오케스트레이터 레벨에서 발생하며, 이는 "orchestrator = manager, worker = executor" 분리를 보존한다.

---

## 제3장: VEV 프로토콜과 검증 체계

### 3.1 VEV (Verify-Execute-Verify) 패턴

v2.2.0에서 도입된 VEV 프로토콜은 모든 워크플로우 스텝의 100% 작업 완료를 보장하는 체계적 검증 메커니즘이다.

```
┌─────────────────────────────────────────────┐
│  1. PRE-VERIFY (선행 조건 확인)                 │
│     - 입력 파일 존재 + 유효성                     │
│     - 이전 Step 출력물의 정합성                    │
│     - 실패 시 → 이전 Step 재확인 or 에러 보고        │
├─────────────────────────────────────────────┤
│  2. EXECUTE (기존 로직 100% 동일)               │
│     - TASK UPDATE (BEFORE)                  │
│     - Invoke worker agent                   │
│     - TASK UPDATE (AFTER)                   │
├─────────────────────────────────────────────┤
│  3. POST-VERIFY (3-Layer 사후 검증)            │
│     Layer 1: Structural (구조적)              │
│       - 파일 존재, JSON 유효, 스키마 준수           │
│     Layer 2: Functional (기능적)              │
│       - 목표 수치 달성, 데이터 무결성, 범위 유효성       │
│     Layer 3: Quality (품질적)                 │
│       - 정확도 목표치, 완전성, 일관성               │
├─────────────────────────────────────────────┤
│  4. RETRY (실패 시 재실행)                      │
│     - Layer 1 실패 → 즉시 재실행 (최대 2회)        │
│     - Layer 2 실패 → 실패 항목만 재실행 (최대 2회)    │
│     - Layer 3 실패 → 경고 + 사용자 알림            │
│     - 2회 재실행 후에도 실패 → 워크플로우 일시정지       │
├─────────────────────────────────────────────┤
│  5. RECORD (검증 결과 기록)                     │
│     - verification-report-{date}.json에 누적    │
│     - workflow-status.json에 step 결과 기록      │
└─────────────────────────────────────────────┘
```

### 3.2 두 가지 VEV 변형

| 유형 | 적용 대상 | 단계 | 설명 |
|------|----------|------|------|
| **Full VEV** (5단계) | 핵심 워크플로우 스텝 | PRE → EXECUTE → POST(3-Layer) → RETRY → RECORD | 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.5, 3.6 |
| **VEV Lite** (3단계) | 번역 서브스텝 | PRE_CHECK → POST_CHECK → ON_FAIL | 1.2b, 1.2d, 1.3b, 2.1b, 2.2b, 2.3b, 2.4b, 3.2b, 3.3b |

VEV Lite는 번역 실패가 워크플로우를 중단시키지 않는다는 설계 원칙을 반영한다. 번역은 비핵심(non-critical) 기능이다.

### 3.3 Layer 3 실패 처리 정책

Layer 3(품질) 실패는 스텝의 컨텍스트에 따라 3가지 패턴 중 하나를 따른다:

| 패턴 | 적용 스텝 | 행동 | 이유 |
|------|----------|------|------|
| **A. Immediate Ask** | 1.2 | 사용자에게 즉시 질문 | 독립적 품질 영향 |
| **B. Defer to Checkpoint** | 1.3, 2.1, 2.3, 3.2 | 경고 로그 후 다음 체크포인트에서 리뷰 | 인간이 1.4/2.5/3.4에서 이슈를 확인할 수 있음 |
| **C. Silent Warn** | 1.1, 2.2, 3.1, 3.3 | 경고 로그 후 무음 진행 | 구조적으로 정확하며 품질 메모만 기록 |

### 3.4 Pipeline Gate (Phase 간 전환 검증)

3개의 Pipeline Gate가 Phase 간 데이터 연속성과 무결성을 보장한다:

**Pipeline Gate 1** (Phase 1 → Phase 2):
1. 신호 ID 연속성: filtered IDs ⊂ raw scan IDs
2. 분류 완전성: 모든 필터된 신호에 `final_category` 존재
3. 공유 컨텍스트 확인: `dedup_analysis` 필드 존재
4. EN-KR 파일 쌍 검증
5. pSST Phase 1 차원 검증: 모든 신호에 SR, TC 차원 존재
6. pSST DC 차원 검증: 비중복 신호에 DC 차원 존재

**Pipeline Gate 2** (Phase 2 → Phase 3):
1. 신호 수 일치: classified == impact-assessed == priority-ranked
2. 점수 범위 유효: priority_score [0, 10], impact_score [-5, +5]
3. 인간 승인 기록 확인 (Step 2.5)
4. 분석 체인 완전성: classified → impact → priority 파일 존재
5. pSST 최소 임계치: 모든 신호 pSST ≥ 30
6. pSST ES/CC 차원 검증 + 최종 pSST 점수 계산 완료

**Pipeline Gate 3** (Phase 3 완료):
1. DB 업데이트 무결성
2. 보고서 완전성 (EN + KR, 7개 섹션 포함)
3. 아카이브 저장 확인
4. 스냅샷 생성 확인
5. 모든 스텝 검증 트레일 완전성
6. 인간 승인 기록 완전성

각 Gate 실패 시: TRACE_BACK → 실패한 Step 재실행 (최대 1회) → 재검증. 재시도 후에도 실패 시 HALT.

### 3.5 검증 보고서

모든 VEV 결과는 `logs/verification-report-{date}.json`에 누적된다. 최종 `overall_status`:

- `ALL_VERIFIED`: 모든 스텝 VERIFIED 또는 SKIPPED
- `VERIFIED_WITH_WARNINGS`: WARN_ACCEPTED 스텝 존재
- `PARTIAL`: FAILED 스텝 존재

### 3.6 검증 상태 값

| 상태 | 의미 |
|------|------|
| `VERIFIED` | 3개 Layer 모두 통과 |
| `WARN_ACCEPTED` | Layer 3 경고 있으나 실행 계속 |
| `RETRY_SUCCESS` | 초기 실패 후 재시도 성공 |
| `FAILED` | 최대 재시도 후에도 실패 |
| `SKIPPED` | 조건부 스텝 미활성화 |

---

## 제4장: 3단계 워크플로우

### 4.1 Phase 1: Research (정보 수집)

| 스텝 | 이름 | 에이전트 | 입력 | 출력 | 임계(critical) |
|------|------|---------|------|------|---------------|
| 1.1 | Archive Loading | @archive-loader | signals/database.json, reports/archive/ | context/previous-signals.json | No |
| 1.2 | Multi-Source Scan & Classification | @multi-source-scanner | config/sources.yaml, config/domains.yaml | raw/daily-scan-{date}.json, structured/classified-signals-{date}.json | arXiv=Yes |
| 1.3 | Deduplication | @deduplication-filter | raw scan + previous-signals | filtered/new-signals-{date}.json | No |
| 1.4 | Human Review (선택적) | - | filtered signals + dedup log | 사용자 결정 기록 | - |
| 1.5 | Expert Panel (조건부) | @realtime-delphi-facilitator | >50개 신호 시 활성화 | expert-validated signals | No |

**4단계 중복제거 캐스케이드**:

| 단계 | 방법 | 임계치 | 설명 |
|------|------|--------|------|
| Stage 1 | URL 정규화 + 완전 일치 | 1.0 (100%) | URL 정확 매칭 |
| Stage 2 | Jaro-Winkler 문자열 유사도 | 0.9 (90%) | 제목 기반 문자열 매칭 |
| Stage 3 | SBERT 의미적 유사도 | 0.8 (80%) | 코사인 유사도 (all-MiniLM-L6-v2) |
| Stage 4 | NER + Jaccard 엔터티 매칭 | 0.85 (85%) | 명명 엔터티 기반 매칭 |

**마라톤 모드 (Step 1.2, 기본 모드)**:

마라톤 모드는 기본 실행 모드다. Step 1.2는 2단계로 구성된다 (`--base-only` 사용 시 Stage B 생략):

- **Stage A**: 기본(base) 소스 스캔 — 항상 실행
- **Stage B**: 확장(expansion) 소스 스캔 — 남은 시간 예산 내에서 실행 (기본 동작, `--base-only` 시 생략)
- **Merge**: Stage A + B 결과를 `raw/daily-scan-{date}.json`에 병합. 확장 신호에 `source.tier: "expansion"` 태그 부여

30분은 **상한선**(ceiling)이다. 모든 확장 소스 스캔이 끝나면 조기 종료한다. 시간을 억지로 채우지 않는다.

### 4.2 Phase 2: Planning (분석 및 구조화)

| 스텝 | 이름 | 에이전트 | 핵심 행동 |
|------|------|---------|----------|
| 2.1 | Classification Verification | @signal-classifier | 분류 품질 검증, 저신뢰도 신호 식별, 전문가 검증 결과 반영 |
| 2.2 | Impact Analysis | @impact-analyzer | Futures Wheel(1차/2차 영향), Cross-Impact Matrix, Bayesian Network 추론 |
| 2.3 | Priority Ranking | @priority-ranker | 가중 점수: Impact 40% + Probability 30% + Urgency 20% + Novelty 10% |
| 2.4 | Scenario Building (조건부) | @scenario-builder | 교차영향 복잡도 > 0.15 시 QUEST 기반 시나리오 생성 ¹ |
| 2.5 | Human Review (필수) | - | STEEPs 분류 검토, 우선순위 조정, 추가 코멘트 |

**우선순위 점수 가중치**:

```
priority_score = impact × 0.40 + probability × 0.30 + urgency × 0.20 + novelty × 0.10
```

모든 가중치의 합은 반드시 1.0이어야 한다. 점수 범위는 [0, 10]이다.

> ¹ **시나리오 활성화 임계치 주의**: 오케스트레이터(`env-scan-orchestrator.md` line 2428)는 `complexity_score > 0.15`를 사용하고, `thresholds.yaml`의 `conditional_features.step_7_5_scenarios`는 `cross_impact_complexity > 0.5`을 정의한다. 이는 코드베이스 내 기존 불일치이다. 실제 실행 시 오케스트레이터의 값(0.15)이 적용된다.

### 4.3 Phase 3: Implementation (보고서 생성)

| 스텝 | 이름 | 에이전트 | 핵심 행동 | 임계 |
|------|------|---------|----------|------|
| 3.1 | Database Update | @database-updater | 스냅샷 생성 → 원자적 DB 업데이트 → 무결성 검증 | **CRITICAL** |
| 3.2 | Report Generation | @report-generator | EN 보고서(6개 필수 섹션) + KR 번역(역번역 검증) | No |
| 3.3 | Archive & Notify | @archive-notifier | 아카이브 복사 + 스냅샷 + 알림 | No |
| 3.4 | Final Approval (필수) | - | `/approve` 또는 `/revision "피드백"`. 최대 3회 수정 | - |
| 3.5 | Quality Metrics | 오케스트레이터 | 실행 시간, 에이전트 성능, 품질 점수, 검증 요약 생성 | No |
| 3.6 | Self-Improvement | @self-improvement-analyzer | 5개 영역 분석, MINOR 자동 적용, MAJOR 제안 | No |

**보고서 필수 섹션** (6개):
1. Executive Summary (500단어 이하)
2. New Signals Detected
3. Existing Signal Updates
4. Patterns and Connections
5. Strategic Implications (전략적 시사점)
6. Appendix (부록)

**수정 루프 프로토콜** (`/revision` 시):
- Steps 3.2 → 3.2b → 3.3 → 3.4를 Full VEV로 재실행
- 최대 3회 수정. 초과 시 강제 승인 또는 HALT 선택
- 검증 보고서에 `{step_id}_rev{N}` 형식으로 기록 (원본 보존)

### 4.4 이중언어 워크플로우

```
Worker Agent (EN) → EN Output → VEV 검증 → @translation-agent → KR Output → VEV Lite 검증
```

**번역 트리거 포인트**: Phase 1에서 4회, Phase 2에서 4회, Phase 3에서 3회 = 총 11회 번역 발생

**번역 품질 기준**:
- 평균 신뢰도: > 0.90
- STEEPs 용어 보존: 100% (위반 제로)
- 역번역 유사도: > 0.95 (핵심 보고서)
- 번역 오버헤드: 전체 워크플로우의 < 25% (약 40초)

---

## 제5장: 태스크 관리와 실행 흐름

### 5.1 태스크 체계 개요

Claude Code v2.1.16+의 TaskCreate/TaskUpdate API를 활용하여 사용자에게 `Ctrl+T` 실시간 진행 가시성을 제공한다.

**핵심 원칙**:
- **비침습적**: workflow-status.json과 병행 운영 (대체 아님)
- **비핵심적**: 태스크 업데이트 실패는 워크플로우를 중단하지 않음
- **사용자 가시성 전용**: 사용자가 `Ctrl+T`로 진행 상황을 확인하는 용도

### 5.2 태스크 계층 (48 정적 + 3 조건부)

```
Phase 1: Research (phase1)
├── 1.1a: Load signals database
├── 1.1b: Load archive reports          [blockedBy: 1.1a]
├── 1.1c: Build deduplication indexes   [blockedBy: 1.1b]
├── 1.1d: Validate configuration files  [blockedBy: 1.1c]
├── 1.2a: Run multi-source scanner - Stage A base  [blockedBy: 1.1d]
├── 1.2a-M: Run expansion scanner - Stage B  [blockedBy: 1.2a] [기본; --base-only 시 생략]
├── 1.2b: Translate raw scan results (KR)  [blockedBy: 1.2a-M, 또는 1.2a if --base-only]
├── 1.2c: Classify signals (STEEPs)     [blockedBy: 1.2a-M, 또는 1.2a if --base-only]
├── 1.2d: Translate classified signals   [blockedBy: 1.2c]
├── 1.3a: Run 4-stage dedup cascade     [blockedBy: 1.2c]
├── 1.3b: Generate dedup log            [blockedBy: 1.3a]
├── 1.3c: Translate filtered results    [blockedBy: 1.3a]
├── 1.4:  Human review [checkpoint]     [blockedBy: 1.3a]
├── PG1:  Pipeline Gate 1               [blockedBy: 1.4]
└── 1.5:  Expert panel [조건부: >50 신호]

Phase 2: Planning (phase2) [blockedBy: phase1]
├── 2.1a: Verify classification quality  [blockedBy: phase1]
├── 2.1b: Translate quality log          [blockedBy: 2.1a]
├── 2.2a: Identify impacts (Futures Wheel)  [blockedBy: 2.1a]
├── 2.2b: Build cross-impact matrix      [blockedBy: 2.2a]
├── 2.2c: Bayesian network inference     [blockedBy: 2.2b]
├── 2.2d: Calculate pSST IC dimension    [blockedBy: 2.2a]
├── 2.2e: Translate impact analysis      [blockedBy: 2.2c]
├── 2.3a: Calculate priority scores      [blockedBy: 2.2c]
├── 2.3b: Aggregate pSST final scores   [blockedBy: 2.3a]
├── 2.3c: Translate priority rankings    [blockedBy: 2.3a]
├── 2.5:  Human review [checkpoint]      [blockedBy: 2.3b]
├── PG2:  Pipeline Gate 2                [blockedBy: 2.5]
├── 2.4a: Build scenarios [조건부: 복잡도>0.15 ¹]
└── 2.4b: Translate scenarios            [blockedBy: 2.4a]

Phase 3: Implementation (phase3) [blockedBy: phase2]
├── 3.1a: Create database backup         [blockedBy: phase2]
├── 3.1b: Update signals database        [blockedBy: 3.1a] [CRITICAL]
├── 3.1c: Verify database integrity      [blockedBy: 3.1b]
├── 3.2a: Generate EN report             [blockedBy: 3.1c]
├── 3.2b: Quality check EN report        [blockedBy: 3.2a]
├── 3.2c: Translate report to KR         [blockedBy: 3.2b]
├── 3.2d: Verify KR translation quality  [blockedBy: 3.2c]
├── 3.2e: Generate pSST trust analysis   [blockedBy: 3.2a]
├── 3.3a: Archive EN+KR reports          [blockedBy: 3.2d]
├── 3.3b: Create signal snapshot         [blockedBy: 3.3a]
├── 3.3c: Send notifications             [blockedBy: 3.3a]
├── 3.3d: Translate daily summary        [blockedBy: 3.3a]
├── 3.4:  Final approval [checkpoint]    [blockedBy: 3.3a]
├── 3.5a: Generate quality metrics (EN)  [blockedBy: 3.4]
├── 3.5b: Translate quality metrics      [blockedBy: 3.5a]
├── 3.5c: Generate VEV verification summary  [blockedBy: 3.5a]
├── 3.6a: Analyze performance metrics    [blockedBy: 3.5a]
├── 3.6b: Propose improvements           [blockedBy: 3.6a]
├── 3.6c: Execute approved MINOR changes [blockedBy: 3.6b]
└── PG3:  Pipeline Gate 3                [blockedBy: 3.6c]
```

### 5.3 에러 처리

```python
# 모든 Task 업데이트는 try-except으로 래핑
try:
    TaskUpdate(task_id, status="completed")
except Exception:
    log_warning("Task update failed")
    # 계속 진행 - workflow-status.json이 진실의 원천(source of truth)
```

태스크 시스템은 순수한 **가시성 기능**이다. 그 실패는 워크플로우 실행에 영향을 주지 않는다.

---

## 제6장: pSST 신뢰도 프레임워크

### 6.1 개요

pSST(predicted Signal Scanning Trust)는 AlphaFold의 pLDDT에서 영감을 받은 **신호별 신뢰도 채점 체계**이다. 각 신호의 신뢰도를 6개 차원으로 분해하여 0~100 점수를 산출한다.

### 6.2 6개 차원

| 차원 | 이름 | 가중치 | 측정 대상 | 사용 가능 시점 |
|------|------|--------|----------|-------------|
| **SR** | Source Reliability | 0.20 | 소스의 신뢰성 (학술:85, 특허:80, 블로그:45, SNS:30) | Stage 1 (수집) |
| **ES** | Evidence Strength | 0.20 | 정량적 데이터 보유, 다중 소스 확인, 검증 상태 | Stage 3 (분류) |
| **CC** | Classification Confidence | 0.15 | 카테고리 마진, 키워드 일치, 전문가 검증 | Stage 3 (분류) |
| **TC** | Temporal Confidence | 0.15 | 발행일 신선도 (7일:100, 90일+:30) + 신호 성숙도 보너스 | Stage 1 (수집) |
| **DC** | Distinctiveness Confidence | 0.15 | 중복제거 캐스케이드 통과 단계 (4단계 통과:100, 중복:0) | Stage 2 (필터링) |
| **IC** | Impact Confidence | 0.15 | 영향 클러스터 안정성, 교차영향 합의, 점수 일관성 | Stage 4 (영향분석) |

### 6.3 복합 점수 계산

```
pSST_score = (SR×0.20 + ES×0.20 + CC×0.15 + TC×0.15 + DC×0.15 + IC×0.15) × coverage_factor

coverage_factor = (available_weight / total_weight) ^ 0.5
```

가용 차원이 6개 미만일 때 커버리지 패널티가 적용된다. 지수 0.5(제곱근)는 중간 강도의 패널티를 의미한다.

### 6.4 Level 2 고급 채점

Level 2는 상위 등급 차별화를 위한 세밀한 기준을 추가한다:

```
total = level1 × 0.85 + level2_scaled × 0.15
```

| 차원 | Level 2 기준 | 점수 |
|------|-------------|------|
| SR | 방법론 보유 | +5 |
| SR | 재현성 | +5 |
| SR | 데이터 투명성 | +5 |
| TC | 모멘텀 (가속/안정/감속) | +6/+3/0 |
| TC | 업데이트 보유 | +5 |
| DC | 의미적 거리 (>=0.7: very_novel) | +7 |
| DC | 정보 이득 | +5 |
| DC | 교차 카테고리 새로움 | +3 |

Level 2 데이터 없이 달성 가능한 최대 점수: 92.5. Grade A 임계치(95)를 달성하려면 최소 1개의 Level 2 차원이 필요하다.

### 6.5 등급 체계

| 등급 | 점수 범위 | 행동 | 뱃지 |
|------|----------|------|------|
| **A** (very_high) | >= 95 (L2 활성 시) / >= 90 (L2 비활성 시) | 자동 승인 | 🟢 |
| **B** (confident) | >= 70 | 표준 처리 | 🔵 |
| **C** (low) | >= 50 | 리뷰 플래그 | 🟡 |
| **D** (very_low) | < 50 | 인간 리뷰 필수 | 🔴 |

### 6.6 파이프라인 게이트별 필수 차원

| 게이트 | 필수 차원 | 최소 pSST |
|--------|----------|----------|
| Gate 1 (수집 후) | SR, TC | 없음 |
| Gate 2 (분석 후) | SR, TC, DC, ES, CC | 30 |
| Gate 3 (완료 후) | SR, TC, DC, ES, CC, IC (전체 6개) | 없음 (보정 체크) |

### 6.7 보정 (Calibration)

| 항목 | 값 |
|------|---|
| 방법 | Platt Scaling |
| 목표 ECE | 0.05 |
| 최소 샘플 | 20개 인간 리뷰 |
| 트리거 간격 | 10회 스캔마다 |
| 이력 파일 | `calibration/psst-review-history.json` |

---

## 제7장: 에이전트 체계

### 7.1 에이전트 구성

```
env-scan-orchestrator (마스터)
│
├── Phase 1 워커 (4+1 필수 + 2 조건부)
│   ├── @archive-loader         ← 이력 데이터 로딩
│   ├── @multi-source-scanner   ← 다중 소스 스캔 (v1.3.0, 마라톤 지원)
│   │   ├── @arxiv-agent        ← 소스별 서브에이전트
│   │   ├── @patent-agent
│   │   ├── @policy-agent
│   │   └── @blog-agent
│   ├── @deduplication-filter   ← 4단계 중복제거 캐스케이드
│   ├── @translation-agent      ← 이중언어 번역 (EN→KR)
│   ├── @realtime-delphi-facilitator  (조건부: >50 신호)
│   └── @scenario-builder       (조건부: 복잡도 >0.15 ¹)
│
├── Phase 2 워커 (3 필수)
│   ├── @signal-classifier      ← 분류 검증/보강
│   ├── @impact-analyzer        ← Futures Wheel + Cross-Impact + Bayesian
│   └── @priority-ranker        ← 가중 점수 기반 순위화
│
└── Phase 3 워커 (4 필수)
    ├── @database-updater       ← CRITICAL: 원자적 DB 업데이트
    ├── @report-generator       ← EN 보고서 생성 (6 필수 섹션)
    ├── @archive-notifier       ← 아카이브 + 알림
    └── @self-improvement-analyzer  ← SIE Step 3.6
```

### 7.2 워커 에이전트 설계 원칙

| 원칙 | 설명 |
|------|------|
| **순수 실행자** | 워커는 의사결정을 하지 않는다. 전달받은 소스 목록만 스캔한다 |
| **상태 무관** | 워커는 "마라톤 모드"를 알지 못한다. 오케스트레이터가 파라미터만 다르게 전달 |
| **독립 검증 없음** | 모든 검증(VEV)은 오케스트레이터 레벨에서 수행 |
| **실패 시 보고** | 워커는 에러를 반환하고, 재시도 결정은 오케스트레이터가 내린다 |

### 7.3 multi-source-scanner 런타임 파라미터 (v1.3.0)

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--days-back` | 스캔 기간 (일) | 7 |
| `--tier` | 소스 티어 필터 (`base` 또는 `expansion`) | base |
| `--time-budget` | 스캔 시간 예산 (초) | 없음 |

`--tier` 파라미터는 `sources.yaml`에서 해당 tier의 `enabled: true` 소스만 필터링한다. 워커는 마라톤 모드의 존재를 알지 못한다.

### 7.4 소스별 서브에이전트

`@multi-source-scanner`는 내부적으로 4개의 소스별 에이전트를 병렬 호출한다:

| 에이전트 | 소스 유형 | 담당 범위 |
|---------|----------|----------|
| @arxiv-agent | academic | arXiv, Google Scholar, SSRN |
| @patent-agent | patent | Google Patents, KIPRIS |
| @policy-agent | government/policy | Federal Register, EU Press, WHO |
| @blog-agent | news/blog | TechCrunch, MIT Tech Review, Economist |

각 에이전트는 독립 프로세스에서 실행되며, 출력을 `raw/daily-scan-{date}.json`에 병합한다.

---

## 제8장: 자기개선엔진 (SIE)

### 8.1 설계 원칙

> **"Improve the tuning, never break the machine"**

SIE는 Step 3.6에서 실행되며, 워크플로우 품질 메트릭을 분석하여 매개변수를 안전하게 조정한다. SIE 실패는 **절대로** 워크플로우를 중단하지 않는다.

### 8.2 5개 분석 영역

| # | 영역 | 메트릭 | 제약 |
|---|------|--------|------|
| 1 | **Threshold Tuning** | false_positive_rate, false_negative_rate, human_corrections | max_delta_per_cycle, min/max 범위 |
| 2 | **Agent Performance** | execution_time, error_rate, retry_count (에이전트별) | 에이전트 비활성화/추가 불가 |
| 3 | **Classification Quality** | category_distribution_skew, confidence_gap, human_correction_patterns | STEEPs 카테고리 변경 불가 (불변) |
| 4 | **Workflow Efficiency** | phase_times_vs_targets, bottleneck_identification, idle_time | Phase 순서 변경/단계 생략 불가 |
| 5 | **Hallucination Tracking** | fabricated_signal_count, id_corruption_rate, url_invalidity_rate, date_anomaly_rate | 검증을 느슨하게 만들 수 없음 (엄격화만 가능) |

### 8.3 변경 분류 체계

| 분류 | 행동 | 예시 |
|------|------|------|
| **MINOR** | 자동 적용 (주기당 최대 3개) | 중복제거 임계치 ±5%, 타임아웃 조정 |
| **MAJOR** | 사용자 승인 후 적용 | 소스 추가/제거, 중복제거 전략 변경, 보고서 구조 변경 |
| **CRITICAL** | 즉시 차단 (사용자 오버라이드 불가) | 불변 경계(core invariants) 위반 시도 |

### 8.4 안전 한도

| 항목 | 값 |
|------|---|
| 주기당 최대 MINOR 자동 적용 | 3개 |
| 주기당 최대 조정 폭 | ±10% |
| 최소 증거 샘플 크기 | 10개 데이터 포인트 |
| 최소 과거 워크플로우 수 | 3개 (비교 기준) |
| 자동 롤백 퇴보 임계치 | >5% 성능 저하 |
| 롤백 이력 보관 | 최근 10개 변경 스냅샷 |

### 8.5 실패 처리

```yaml
On_Fail:
  action: ROLLBACK_all_changes_this_cycle
  log: "SIE cycle failed — all changes reverted"
  continue: true  # SIE 실패는 절대로 워크플로우를 중단하지 않음
```

SIE 내 VEV POST-VERIFY Layer 2에서 불변 경계 위반이 감지되면, 해당 주기의 **모든** 변경을 롤백한다.

### 8.6 마라톤 모드 연동

마라톤 모드 실행 후, SIE는 확장 소스의 품질을 자동 추적한다:
- 어떤 확장 소스가 고품질 신호를 생산했는지 분석
- "PubMed에서 12개 고품질 신호 발견 → base tier 승격 제안" 가능
- 이는 MAJOR change 프로세스를 통해 사용자 승인 후 적용

---

## 제9장: 설정과 확장 포인트

### 9.1 설정 파일 (7개)

| 파일 | 버전 | 역할 |
|------|------|------|
| `config/domains.yaml` | 1.0.0 | STEEPs 6개 카테고리 키워드 및 검색어 정의 |
| `config/sources.yaml` | 3.1.0 | 2-Tier 소스 아키텍처 (base 11개 + expansion 18개, 마라톤 기본) |
| `config/thresholds.yaml` | 1.2.0 | 중복제거/AI 신뢰도/우선순위/pSST/마라톤 임계치 |
| `config/ml-models.yaml` | - | AI/ML 모델 설정 (SBERT, 분류기) |
| `config/translation-terms.yaml` | - | EN-KR 번역 용어 매핑 |
| `config/core-invariants.yaml` | 1.0.0 | 불변 경계 정의 (제10장 참조) |
| `config/self-improvement-config.yaml` | 1.0.0 | SIE 행동, 안전 한도, 분석 영역 설정 |

### 9.2 2-Tier 소스 아키텍처 (sources.yaml v3.0.0)

**Base Tier** (항상 스캔 — 11개):

| 소스 | 유형 | 신뢰도 | STEEPs 초점 |
|------|------|--------|------------|
| arXiv | academic | 0.9 | T, S |
| Google Scholar | academic | 0.85 | 전체 |
| SSRN | academic | 0.85 | E(econ), S |
| Google Patents | patent | 0.8 | T |
| KIPRIS | patent | 0.75 | T |
| EU Press | government | 0.85 | P |
| US Federal Register | government | 0.9 | P |
| WHO | government | 0.9 | S, E(env) |
| TechCrunch | blog/news | 0.7 | T |
| MIT Technology Review | blog/news | 0.8 | T, S |
| The Economist | blog/news | 0.85 | E(econ), P |

**Expansion Tier** (기본 스캔, `--base-only` 시 생략 — 18개):

| 카테고리 | 소스 | 유형 | 신뢰도 |
|---------|------|------|--------|
| Academic | PubMed Central, Nature News, Science Magazine, IEEE Spectrum | academic | 0.85-0.9 |
| Policy | OECD Newsroom, World Bank Blogs, UN News, EUR-Lex | policy/government | 0.8-0.85 |
| Think Tank | Brookings, WEF Agenda, Pew Research | think_tank | 0.8-0.85 |
| Tech | Hacker News, Wired, Ars Technica | blog/news | 0.6-0.75 |
| Environmental | NASA Climate Change, Carbon Brief | academic/news | 0.8-0.85 |
| Economic | IMF Blog, BIS Speeches | government | 0.85-0.9 |

모든 확장 소스는 `sources.yaml`에 사전 등록되며, 각각 `type`, `rate_limit`, `timeout`, `reliability` 필드가 정의되어 pSST SR 차원의 정상 작동을 보장한다.

### 9.3 마라톤 모드 설정 (thresholds.yaml)

```yaml
marathon_mode:
  total_budget_minutes: 30          # 상한선 (ceiling)
  stage_b_min_budget_minutes: 5     # Stage B 최소 보장 시간
  expansion_source_priority: "type_diversity"  # 소스 우선순위 전략
  expansion_signal_tag: "expansion"  # 확장 신호 태그
  psst_expansion_policy: "same_as_base"  # pSST 동일 적용
```

소스 우선순위 전략 3가지:
- `type_diversity`: 소스 유형별 라운드 로빈 (STEEPs 커버리지 극대화)
- `reliability`: 높은 신뢰도 소스 우선
- `steeps_coverage`: Stage A 결과에서 부족한 STEEPs 카테고리 보완

### 9.4 슬래시 커맨드 (6개)

| 커맨드 | 파일 | 기능 |
|--------|------|------|
| `/run-daily-scan` | `commands/env-scan/run.md` | 전체 워크플로우 실행 (마라톤 기본) |
| `/run-daily-scan --base-only` | 동일 | Base 소스만 스캔 (Expansion 생략) |
| `/status` | `commands/env-scan/status.md` | 현재 워크플로우 진행 상황 확인 |
| `/review-filter` | `commands/env-scan/review-filter.md` | Step 1.4 중복 필터링 리뷰 |
| `/review-analysis` | `commands/env-scan/review-analysis.md` | Step 2.5 분석 결과 리뷰 |
| `/approve` | `commands/env-scan/approve.md` | Step 3.4 최종 보고서 승인 |
| `/revision "피드백"` | `commands/env-scan/revision.md` | 보고서 수정 요청 |

### 9.5 스킬 (6개)

| 스킬 | 설명 |
|------|------|
| `env-scanner` | 환경 스캐닝 시스템 (본 시스템) |
| `skill-creator` | 새 스킬 생성 도구 |
| `slash-command-creator` | 슬래시 커맨드 생성 도구 |
| `subagent-creator` | 서브에이전트 생성 도구 |
| `hook-creator` | Claude Code 훅 생성 도구 |
| `youtube-collector` | YouTube 데이터 수집기 |

---

## 제10장: 불변의 경계

### 10.1 개요

`core-invariants.yaml`은 시스템의 **절대 불변 요소**를 정의한다. SIE는 모든 제안된 변경을 이 파일과 대조 검증해야 하며, 불변 요소를 건드리는 변경은 CRITICAL로 분류되어 **즉시 차단**된다. 사용자 오버라이드도 불가능하다.

### 10.2 CRITICAL: 불변 요소 (9개)

| # | 불변 요소 | 설명 |
|---|----------|------|
| 1 | **3-Phase 워크플로우** | Research → Planning → Implementation 구조 |
| 2 | **인간 체크포인트** | 1.4(선택), 2.5(필수), 3.4(필수) 제거 불가 |
| 3 | **STEEPs 6개 카테고리** | S, T, E, E, P, s 카테고리 자체를 변경 불가 |
| 4 | **VEV 프로토콜 5단계** | PRE-VERIFY → EXECUTE → POST-VERIFY → RETRY → RECORD |
| 5 | **Pipeline Gate 3개** | Phase 간 전환 검증 게이트 제거/우회 불가 |
| 6 | **데이터베이스 원자성** | 스냅샷 → 원자적 쓰기 → 실패 시 복원 → ID 유니크성 |
| 7 | **Phase 순서** | [1, 2, 3] 순서 엄수, 건너뛰기 불가 |
| 8 | **이중언어 프로토콜** | 내부=영어, 외부=한국어 통신 패턴 |
| 9 | **보고서 품질 4중 방어** | L1(스켈레톤) → L2(검증) → L3(재시도) → L4(골든 레퍼런스), 어떤 레이어도 우회/비활성화 불가 |

> **불변 요소 #9 상세** (v1.3.0, 2026-02-02 도입)
>
> 2026-02-02 보고서 회귀 사건(22KB vs 71KB, 신호 필드 5/9, 섹션 3개 누락)으로 인해 도입된 4중 방어 체계이다.
> LLM 비결정성으로 인한 품질 저하를 구조적으로 차단하며, **모든 레이어가 매 보고서 생성 주기에서 실행**되어야 한다.
>
> | Layer | 이름 | 역할 | 관련 아티팩트 |
> |-------|------|------|-------------|
> | L1 | **스켈레톤 템플릿** | 자유 생성이 아닌 구조 채우기 방식 강제 | `references/report-skeleton.md` |
> | L2 | **프로그래밍적 검증** | 14개 체크 자동 실행 (CRITICAL 7개, ERROR 7개) | `scripts/validate_report.py` |
> | L3 | **점진적 재시도** | CRITICAL 실패 시 3단계 에스컬레이션 (표적 수정 → 전체 재생성 → 인간 에스컬레이션) | 오케스트레이터 Step 3.2 |
> | L4 | **골든 레퍼런스** | 완전한 9필드 신호 예시를 에이전트에 상시 삽입 | `report-generator.md` GOLDEN REFERENCE |
>
> **금지 행위**:
> - L2 검증 스크립트 실행 건너뛰기
> - L1 스켈레톤 없이 자유 형식 생성
> - L3 재시도 없이 CRITICAL FAIL 보고서 승인 진행
> - L4 골든 레퍼런스 섹션 삭제 또는 9개 미만으로 축소
> - `validate_report.py`의 CRITICAL 체크 기준값 완화 (예: min_signal_blocks < 10)
> - SIE에 의한 `quality_thresholds` 값 변경 (min_total_words, min_korean_char_ratio 등은 불변)
> - `_touches_core_invariant`의 `immutable_keywords` 리스트에서 `report_quality_defense` 제거

### 10.3 MINOR: SIE 자동 조정 가능 매개변수

| 매개변수 | 현재값 | 범위 | 주기당 최대 조정 |
|---------|--------|------|---------------|
| Stage 2 문자열 유사도 | 0.9 | [0.7, 0.98] | ±0.05 |
| Stage 3 의미적 유사도 | 0.8 | [0.6, 0.95] | ±0.05 |
| Stage 4 엔터티 매칭 | 0.85 | [0.7, 0.98] | ±0.05 |
| AI 신뢰도 (high) | 0.9 | [0.8, 0.99] | ±0.05 |
| AI 신뢰도 (medium) | 0.7 | [0.5, 0.85] | ±0.05 |
| Phase 1 실행 시간 | 60s | [30, 180]s | ±15s |
| Phase 2 실행 시간 | 40s | [20, 120]s | ±10s |
| Phase 3 실행 시간 | 35s | [15, 90]s | ±10s |
| pSST SR 가중치 | 0.20 | [0.10, 0.35] | ±0.03 |
| pSST ES 가중치 | 0.20 | [0.10, 0.35] | ±0.03 |
| pSST CC 가중치 | 0.15 | [0.05, 0.30] | ±0.03 |
| pSST TC 가중치 | 0.15 | [0.05, 0.30] | ±0.03 |
| pSST DC 가중치 | 0.15 | [0.05, 0.30] | ±0.03 |
| pSST IC 가중치 | 0.15 | [0.05, 0.30] | ±0.03 |
| 중복탐지 정밀도 목표 | 0.95 | [0.85, 0.99] | ±0.02 |
| 중복탐지 재현율 목표 | 0.90 | [0.80, 0.99] | ±0.02 |
| 분류 정확도 목표 | 0.90 | [0.80, 0.99] | ±0.02 |
| 우선순위: Impact | 0.40 | [0.20, 0.60] | ±0.05 |
| 우선순위: Probability | 0.30 | [0.10, 0.50] | ±0.05 |
| 우선순위: Urgency | 0.20 | [0.05, 0.40] | ±0.05 |
| 우선순위: Novelty | 0.10 | [0.05, 0.30] | ±0.05 |

**제약**: pSST 가중치 합 = 1.0, 우선순위 가중치 합 = 1.0

### 10.4 MAJOR: 사용자 승인 필수 영역 (6개)

| 영역 | 설명 | 관련 파일 |
|------|------|----------|
| scanner_sources | 데이터 소스 추가/제거/순서 변경 | sources.yaml |
| dedup_strategy | 중복제거 캐스케이드 단계 변경 | thresholds.yaml |
| report_structure | 보고서 섹션 변경 | references/report-format.md |
| classification_prompt | 분류 프롬프트 대폭 변경 | workers/classification-prompt-template.md |
| new_analysis_area | 새 분석 차원 추가 | - |
| translation_strategy | 번역 방식 또는 품질 요구 변경 | - |

---

## 부록: 성능 목표

| 항목 | 목표 |
|------|------|
| 중복탐지 정확도 | > 95% |
| 처리 시간 단축 | 30% (기준선 대비) |
| 신호 탐지 속도 | 2x (수동 대비) |
| 전문가 피드백 시간 | < 3일 (Phase 1.5 활성화 시) |
| 번역 품질 | > 0.90 평균 신뢰도 |
| 번역 오버헤드 | < 25% 추가 시간 (~40초/워크플로우) |
| STEEPs 용어 정확도 | 100% (위반 제로) |

---

## 교차 참조

| 문서 | 위치 | 내용 |
|------|------|------|
| 오케스트레이터 전체 명세 | `.claude/agents/env-scan-orchestrator.md` | 4,070줄 마스터 명세서 |
| 태스크 관리 통합 가이드 | `docs/task-management-integration.md` | 49+3 태스크 상세 |
| 메모리 최적화 가이드 | `docs/memory-optimization-guide.md` | SharedContextManager, RecursiveArchiveLoader |
| 원본 워크플로우 설계 | `prompt/environmental-scanning-workflow.md` | 초기 설계 (403줄) |
| 정제 워크플로우 | `prompt/final-workflow-1.md` | 정제 설계 (1,077줄) |
| 구현 가이드 | `IMPLEMENTATION_GUIDE.md` | 10개 구현 영역 상세 |
| 변경 이력 | `CHANGELOG.md` | 버전별 변경 기록 |

---

## 버전 정보

| 구성요소 | 버전 |
|---------|------|
| 시스템 | 2.1.0 (Bilingual EN-KR + Marathon Default) |
| 오케스트레이터 | 3.1.0 (VEV + SIE + Marathon Default) |
| 소스 아키텍처 | 3.1.0 (2-Tier, Marathon Default) |
| VEV 프로토콜 | 2.2.0 |
| pSST 프레임워크 | 1.0.0 |
| SIE | 1.0.0 |
| 마라톤 모드 | 1.1.0 (Default) |
| 스킬 (env-scanner) | 1.5.0 |
| 본 문서 | 1.1.0 |
| 최종 갱신 | 2026-02-01 |
