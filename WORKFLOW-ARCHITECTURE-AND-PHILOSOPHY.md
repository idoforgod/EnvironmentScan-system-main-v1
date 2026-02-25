# WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY

> **Quadruple Environmental Scanning System** | 워크플로우 아키텍처와 철학
>
> Version: 3.0.0 | Last Updated: 2026-02-24

---

**운영 가이드**: 일일 운영 절차, 커맨드 사용법 등 실무 가이드는 [USER_GUIDE.md](USER_GUIDE.md)를 참조하세요. 본 문서는 시스템의 기술 명세입니다.

## 목차

1. [철학과 핵심 목표](#제1장-철학과-핵심-목표)
2. [아키텍처 전체도와 오케스트레이터](#제2장-아키텍처-전체도와-오케스트레이터)
3. [SOT와 검증 체계](#제3장-sot와-검증-체계)
4. [VEV 프로토콜과 검증 체계](#제4장-vev-프로토콜과-검증-체계)
5. [쿼드러플 워크플로우](#제5장-쿼드러플-워크플로우)
6. [태스크 관리와 실행 흐름](#제6장-태스크-관리와-실행-흐름)
7. [pSST 신뢰도 프레임워크](#제7장-psst-신뢰도-프레임워크)
8. [에이전트 체계](#제8장-에이전트-체계)
9. [WF3/WF4 전용 프레임워크](#제9장-wf3wf4-전용-프레임워크)
10. [자기개선엔진 (SIE)](#제10장-자기개선엔진-sie)
11. [설정과 확장 포인트](#제11장-설정과-확장-포인트)
12. [불변의 경계](#제12장-불변의-경계)

---

## 제1장: 철학과 핵심 목표

### 1.1 절대 목표 (Absolute Goal)

> **"Catch up on early signals of future trends, medium-term changes, macro shifts, paradigm transformations, critical transitions, singularities, sudden events, and unexpected futures from around the world (Korea, Asia, Europe, Africa, Americas) AS FAST AS POSSIBLE."**

이 목표는 시스템의 존재 이유이며, 모든 단계와 기능에 걸쳐 고정 불변(fixed and immutable)이다. "AS FAST AS POSSIBLE"은 워크플로우 실행 속도가 아니라 **신호 포착의 신속성**을 의미한다. 품질을 희생하여 빨리 끝내는 것이 아니라, 세계의 변화를 가능한 한 빠르게 감지하는 것이 핵심이다.

### 1.2 8대 설계 원칙

| # | 원칙 | 출처 | 의미 |
|---|------|------|------|
| 1 | **"Improve the tuning, never break the machine"** | `core-invariants.yaml` | 시스템의 핵심 구조를 변경하지 않고 세부 조정만 허용한다 |
| 2 | **오케스트레이터-워커 분리** | `env-scan-orchestrator.md` | 관리자(오케스트레이터)와 실행자(워커)의 역할을 명확히 분리한다 |
| 3 | **Human-in-the-Loop** | `core-invariants.yaml` | 9개의 인간 검토 체크포인트를 통해 인간의 감독을 보장한다 |
| 4 | **품질 기반 실행** | VEV 프로토콜 | 시간이 아닌 품질 검증을 기준으로 단계를 진행한다 |
| 5 | **통제된 소스 관리** | `core-invariants.yaml` | 모든 소스는 사전 설정되고, 추가/제거는 사용자 승인을 요한다 |
| 6 | **이중언어 프로토콜** | `core-invariants.yaml` | 내부 처리는 영어, 외부 출력은 한국어. STEEPs 용어 100% 보존 |
| 7 | **데이터베이스 원자성** | `core-invariants.yaml` | DB 업데이트는 반드시 스냅샷 → 원자적 쓰기 → 실패 시 복원 순서를 따른다 |
| 8 | **워크플로우 독립성** | `workflow-registry.yaml` | WF1/WF2/WF3/WF4는 서로의 존재를 모른다. 교차 읽기/쓰기 금지 |

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
| FSSF 8유형 분류 | 미래학 표준 분류 | WF3 신호 분류 (제9장 참조) |
| Three Horizons | Curry & Hodgson | WF3 시간 지평 태깅 (제9장 참조) |

---

## 제2장: 아키텍처 전체도와 오케스트레이터

### 2.1 디렉토리 구조

```
EnvironmentScan-system-main-v4/
├── .claude/
│   ├── agents/
│   │   ├── master-orchestrator.md              ← 최상위 오케스트레이터
│   │   ├── env-scan-orchestrator.md            ← WF1 오케스트레이터
│   │   ├── arxiv-scan-orchestrator.md          ← WF2 오케스트레이터
│   │   ├── naver-scan-orchestrator.md          ← WF3 오케스트레이터
│   │   ├── multiglobal-news-scan-orchestrator.md ← WF4 오케스트레이터
│   │   ├── protocols/
│   │   │   └── orchestrator-protocol.md        ← 공유 프로토콜
│   │   ├── TASK_MANAGEMENT_EXECUTION_GUIDE.md  ← 태스크 관리 가이드
│   │   └── workers/                            ← 워커 에이전트
│   │       ├── archive-loader.md               ← 공유 워커 (11개)
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
│   │       ├── arxiv-agent.md                  ← 소스별 서브에이전트 (4개)
│   │       ├── patent-agent.md
│   │       ├── policy-agent.md
│   │       ├── blog-agent.md
│   │       ├── naver-news-crawler.md           ← WF3 전용 워커 (4개)
│   │       ├── naver-signal-detector.md
│   │       ├── naver-pattern-detector.md
│   │       ├── naver-alert-dispatcher.md
│   │       ├── news-direct-crawler.md          ← WF4 전용 워커 (5개)
│   │       ├── news-signal-detector.md
│   │       ├── news-pattern-detector.md
│   │       ├── news-alert-dispatcher.md
│   │       ├── news-language-normalizer.md
│   │       ├── report-merger.md                ← 통합 워커
│   │       ├── realtime-delphi-facilitator.md  ← 조건부 워커 (2개)
│   │       ├── scenario-builder.md
│   │       └── classification-prompt-template.md  ← 프롬프트 템플릿
│   ├── skills/
│   │   ├── env-scanner/
│   │   │   ├── SKILL.md                        ← 스킬 인터페이스
│   │   │   └── references/
│   │   │       ├── steep-framework.md
│   │   │       ├── signal-template.md
│   │   │       ├── report-format.md
│   │   │       ├── report-skeleton.md          ← WF1/WF2 보고서 스켈레톤
│   │   │       ├── integrated-report-skeleton.md  ← 통합 보고서 스켈레톤
│   │   │       ├── naver-report-skeleton.md    ← WF3 보고서 스켈레톤
│   │   │       ├── weekly-report-skeleton.md   ← 주간 보고서 스켈레톤
│   │   │       └── final-report-style-guide.md ← 보고서 스타일 가이드
│   │   └── longform-journalism/
│   │       └── SKILL.md                        ← 장편 저널리즘 스킬
│   ├── commands/env-scan/
│   │   ├── run.md              ← /env-scan:run
│   │   ├── run-arxiv.md        ← /env-scan:run-arxiv
│   │   ├── run-naver.md        ← /env-scan:run-naver
│   │   ├── run-weekly.md       ← /env-scan:run-weekly
│   │   ├── status.md           ← /env-scan:status
│   │   ├── review-filter.md    ← /env-scan:review-filter
│   │   ├── review-analysis.md  ← /env-scan:review-analysis
│   │   ├── approve.md          ← /env-scan:approve
│   │   └── revision.md         ← /env-scan:revision
│   └── context-backups/        ← 컨텍스트 보존 훅 백업
│
├── env-scanning/
│   ├── config/
│   │   ├── workflow-registry.yaml     ← SOT (Source of Truth)
│   │   ├── domains.yaml               ← STEEPs 키워드 정의
│   │   ├── sources.yaml               ← WF1 소스 (arXiv 제외)
│   │   ├── sources-arxiv.yaml         ← WF2 전용 소스
│   │   ├── sources-naver.yaml         ← WF3 전용 소스
│   │   ├── sources-multiglobal-news.yaml ← WF4 전용 소스 (43개 사이트, 11개 언어)
│   │   ├── thresholds.yaml            ← 채점/필터링 임계치
│   │   ├── ml-models.yaml             ← AI 모델 설정
│   │   ├── translation-terms.yaml     ← 번역 용어 매핑
│   │   ├── core-invariants.yaml       ← 불변 경계 정의
│   │   └── self-improvement-config.yaml ← SIE 설정
│   │
│   ├── core/                           ← Python 코어 모듈 (33개)
│   │   ├── naver_crawler.py           ← NaverNewsCrawler + CrawlDefender
│   │   ├── naver_signal_processor.py  ← FSSF/ThreeHorizons/TippingPoint/Anomaly
│   │   ├── psst_calculator.py         ← pSST 점수 계산
│   │   ├── psst_calibrator.py         ← pSST 보정
│   │   ├── embedding_deduplicator.py  ← 임베딩 기반 중복제거
│   │   ├── impact_matrix_compressor.py ← 교차영향 매트릭스 압축
│   │   ├── self_improvement_engine.py ← SIE 엔진
│   │   ├── database_recovery.py       ← DB 복구
│   │   ├── context_manager.py         ← 에이전트 간 공유 컨텍스트
│   │   ├── unified_task_manager.py    ← 통합 태스크 관리
│   │   ├── translation_parallelizer.py ← 번역 병렬화
│   │   ├── adaptive_fetcher.py        ← 적응형 웹 수집
│   │   ├── source_health_checker.py   ← 소스 상태 확인
│   │   ├── redirect_resolver.py       ← URL 리다이렉트 해석
│   │   ├── index_cache_manager.py     ← 인덱스 캐시 관리
│   │   └── lazy_report_generator.py   ← 지연 보고서 생성
│   │
│   ├── scripts/
│   │   ├── validate_report.py         ← 보고서 14개 체크 검증
│   │   └── validate_registry.py       ← SOT 23개 규칙 검증
│   │
│   ├── wf1-general/                   ← WF1 데이터 루트
│   │   ├── raw/
│   │   ├── structured/
│   │   ├── filtered/
│   │   ├── analysis/
│   │   ├── signals/ (database.json + snapshots/)
│   │   ├── reports/ (daily/ + archive/)
│   │   ├── context/
│   │   ├── logs/
│   │   ├── health/
│   │   ├── calibration/
│   │   └── self-improvement/
│   │
│   ├── wf2-arxiv/                     ← WF2 데이터 루트
│   │   ├── (wf1-general과 동일 구조)
│   │   └── ...
│   │
│   ├── wf3-naver/                     ← WF3 데이터 루트
│   │   ├── (wf1-general과 동일 구조)
│   │   └── ...
│   │
│   ├── wf4-multiglobal-news/         ← WF4 데이터 루트
│   │   ├── (wf1-general과 동일 구조 + FSSF + Three Horizons + Tipping Point + 다국어)
│   │   └── ...
│   │
│   └── integrated/                    ← 통합 출력
│       ├── reports/ (daily/ + archive/)
│       ├── logs/
│       └── weekly/                    ← 주간 메타분석 출력
│           ├── reports/
│           ├── analysis/
│           └── logs/
│
├── tests/                             ← 단위/통합/E2E 테스트
├── docs/                              ← 기술 문서
└── prompt/                            ← 원본 워크플로우 설계 문서
```

### 2.2 시스템 전체 데이터 흐름도

```
┌──────────────────────────────────────────────────────────────────────┐
│                    MASTER ORCHESTRATOR (최상위)                        │
│                                                                      │
│  Step 0: SOT 읽기 + validate_registry.py 실행 (23개 규칙)              │
│                         ↓                                            │
│  ┌─ WF1: General ──────────────────────────────────────────────┐    │
│  │  env-scan-orchestrator                                      │    │
│  │  Phase 1 → Phase 2 → Phase 3                               │    │
│  │  소스: sources.yaml (arXiv 제외, 29개 소스)                    │    │
│  │  체크포인트: 1.4(선택), 2.5(필수), 3.4(필수)                    │    │
│  │  출력: wf1-general/reports/daily/environmental-scan-{date}.md│    │
│  └──────────────────────────────────────────────────────────────┘    │
│                         ↓                                            │
│  ┌─ WF2: arXiv ────────────────────────────────────────────────┐    │
│  │  arxiv-scan-orchestrator                                    │    │
│  │  Phase 1 → Phase 2 → Phase 3                               │    │
│  │  소스: sources-arxiv.yaml (arXiv 단일, 심층 파라미터)            │    │
│  │  체크포인트: 1.4(선택), 2.5(필수), 3.4(필수)                    │    │
│  │  출력: wf2-arxiv/reports/daily/environmental-scan-{date}.md  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                         ↓                                            │
│  ┌─ WF3: Naver ────────────────────────────────────────────────┐    │
│  │  naver-scan-orchestrator                                    │    │
│  │  Phase 1 → Phase 2 → Phase 3                               │    │
│  │  소스: sources-naver.yaml (네이버 뉴스 6개 섹션)                 │    │
│  │  FSSF 8유형 분류 + Three Horizons + Tipping Point Detection    │    │
│  │  체크포인트: 1.4(선택), 2.5(필수), 3.4(필수)                    │    │
│  │  출력: wf3-naver/reports/daily/environmental-scan-{date}.md  │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                         ↓                                            │
│  ┌─ WF4: Multi&Global-News ──────────────────────────────────┐    │
│  │  multiglobal-news-scan-orchestrator                        │    │
│  │  Phase 1 → Phase 2 → Phase 3                               │    │
│  │  소스: sources-multiglobal-news.yaml (43개 뉴스 사이트, 11개 언어) │    │
│  │  FSSF 8유형 분류 + Three Horizons + Tipping Point Detection    │    │
│  │  체크포인트: 1.4(선택), 2.5(필수), 3.4(필수)                    │    │
│  │  출력: wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                         ↓                                            │
│  ┌─ Integration (통합) ────────────────────────────────────────┐    │
│  │  report-merger (Agent-Teams 5 members)                      │    │
│  │  WF1 + WF2 + WF3 + WF4 보고서 병합                            │    │
│  │  pSST 기반 교차 워크플로우 재순위화                               │    │
│  │  체크포인트: 통합 보고서 최종 승인(필수)                           │    │
│  │  출력: integrated/reports/daily/integrated-scan-{date}.md    │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  총 인간 체크포인트: 9개 (WF1×2 + WF2×2 + WF3×2 + WF4×2 + 통합×1)     │
└──────────────────────────────────────────────────────────────────────┘

┌─ Weekly Meta-Analysis (별도 실행) ──────────────────────────────────┐
│  /env-scan:run-weekly로 수동 트리거                                   │
│  입력: 최근 7일간 WF1+WF2+WF3+WF4+통합 보고서 (읽기 전용)               │
│  출력: integrated/weekly/reports/weekly-meta-{week_id}.md            │
│  TIS (Trend Intensity Score) 기반 추세 분석                           │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.3 오케스트레이터 계층 구조

쿼드러플 워크플로우 시스템은 **5개의 오케스트레이터**로 구성된다:

| 오케스트레이터 | 파일 | 역할 |
|--------------|------|------|
| **Master Orchestrator** | `master-orchestrator.md` | 최상위 관리자. SOT 읽기, WF1→WF2→WF3→WF4→Merge 순차 실행, 9개 체크포인트 총괄 |
| **WF1 Orchestrator** | `env-scan-orchestrator.md` | 일반 환경스캐닝. 25+개 소스(arXiv 제외) 다중 소스 스캔 |
| **WF2 Orchestrator** | `arxiv-scan-orchestrator.md` | arXiv 학술 심층 스캐닝. arXiv 단일 소스, 확장 파라미터 |
| **WF3 Orchestrator** | `naver-scan-orchestrator.md` | 네이버 뉴스 환경스캐닝. FSSF/ThreeHorizons/TippingPoint |
| **WF4 Orchestrator** | `multiglobal-news-scan-orchestrator.md` | 다국어 글로벌 뉴스 환경스캐닝. 43개 사이트, 11개 언어, FSSF/ThreeHorizons/TippingPoint |

**오케스트레이터 공통 책임**:
- 워크플로우 상태 관리 (`{data_root}/logs/workflow-status-{date}.json`)
- 태스크 계층 생성 및 업데이트
- VEV 프로토콜 적용 (PRE-VERIFY → POST-VERIFY)
- Pipeline Gate 실행
- 인간 체크포인트 관리
- 에러 처리 및 재시도 결정
- 검증 보고서 누적 (`verification-report-{date}.json`)

**Master Orchestrator 추가 책임**:
- SOT(`workflow-registry.yaml`) 읽기 및 변수 바인딩
- `validate_registry.py` 실행 (23개 검증 규칙)
- 워크플로우 실행 순서 관리
- 통합 보고서 생성 지시
- SCG (State Consistency Gate) 실행
- PoE (Proof of Execution) 검증

**핵심 설계 원칙**: 워커 에이전트는 의사결정을 하지 않는다. 모든 검증은 오케스트레이터 레벨에서 발생하며, "orchestrator = manager, worker = executor" 분리를 보존한다.

---

## 제3장: SOT와 검증 체계

### 3.1 SOT (Source of Truth) 개요

`env-scanning/config/workflow-registry.yaml` (v3.0.0)은 쿼드러플 워크플로우 시스템의 **단일 진실의 원천**이다. 모든 오케스트레이터는 이 파일에서 경로, 파라미터, 설정을 읽는다.

**SOT 핵심 규칙**:
1. master-orchestrator는 시작 시 반드시 이 파일을 읽어야 한다
2. `validate_registry.py`가 통과해야 워크플로우 실행 가능
3. 공유 설정은 참조만 하고, 절대 복제하지 않는다
4. 워크플로우 추가/제거는 이 파일을 먼저 수정해야 한다
5. 에이전트는 경로를 하드코딩하지 않는다 — SOT에서 전달받는다
6. 심각도 HALT인 검증 실패는 워크플로우를 완전히 중단한다

### 3.2 SOT 바인딩 규칙

Master Orchestrator는 SOT를 읽은 후 **명명 변수(named variables)** 를 생성하고, 이후 모든 스텝은 이 변수를 참조한다:

| 변수 | SOT 필드 | 설명 |
|------|----------|------|
| `WF1_DATA_ROOT` | `workflows.wf1-general.data_root` | WF1 데이터 루트 경로 |
| `WF1_SOURCES` | `workflows.wf1-general.sources_config` | WF1 소스 설정 파일 |
| `WF1_PROFILE` | `workflows.wf1-general.validate_profile` | WF1 검증 프로파일 |
| `WF2_DATA_ROOT` | `workflows.wf2-arxiv.data_root` | WF2 데이터 루트 경로 |
| `WF2_SOURCES` | `workflows.wf2-arxiv.sources_config` | WF2 소스 설정 파일 |
| `WF2_DAYS_BACK` | `workflows.wf2-arxiv.parameters.days_back` | WF2 스캔 기간 (14일) |
| `WF2_MAX_RESULTS` | `workflows.wf2-arxiv.parameters.max_results_per_category` | WF2 카테고리당 최대 결과 (50) |
| `WF3_DATA_ROOT` | `workflows.wf3-naver.data_root` | WF3 데이터 루트 경로 |
| `WF3_SOURCES` | `workflows.wf3-naver.sources_config` | WF3 소스 설정 파일 |
| `WF3_PROFILE` | `workflows.wf3-naver.validate_profile` | WF3 검증 프로파일 (`naver`) |
| `WF4_DATA_ROOT` | `workflows.wf4-multiglobal-news.data_root` | WF4 데이터 루트 경로 |
| `WF4_SOURCES` | `workflows.wf4-multiglobal-news.sources_config` | WF4 소스 설정 파일 |
| `WF4_PROFILE` | `workflows.wf4-multiglobal-news.validate_profile` | WF4 검증 프로파일 (`multiglobal-news`) |
| `INT_ROOT` | `integration.output_root` | 통합 출력 경로 |
| `INT_PROFILE` | `integration.validate_profile` | 통합 검증 프로파일 |

### 3.3 워크플로우 독립성 보장 (INDEPENDENCE GUARANTEE)

```
- WF1은 WF2, WF3, WF4의 존재를 모른다
- WF2는 WF1, WF3, WF4의 존재를 모른다
- WF3는 WF1, WF2, WF4의 존재를 모른다
- WF4는 WF1, WF2, WF3의 존재를 모른다
- 어떤 워크플로우도 다른 워크플로우의 데이터를 읽거나 쓰지 않는다
- 각 워크플로우는 독립적으로 삭제할 수 있다
- 각 워크플로우는 독립적으로 완전한 보고서를 생산한다
```

### 3.4 SOT 검증 규칙 (23개)

`validate_registry.py`가 시작 시 실행하는 검증 규칙:

| ID | 검사 항목 | 심각도 | 설명 |
|----|----------|--------|------|
| SOT-001 | 공유 불변 파일 존재 | HALT | `shared_invariants`의 모든 파일 존재 확인 |
| SOT-002 | 오케스트레이터 파일 존재 | HALT | 모든 워크플로우 오케스트레이터 파일 존재 |
| SOT-003 | 소스 설정 파일 존재 | HALT | 모든 워크플로우 `sources_config` 파일 존재 |
| SOT-004 | 공유 워커 파일 존재 | HALT | 11개 공유 워커 에이전트 파일 존재 |
| SOT-005 | 데이터 루트 존재 | CREATE | 워크플로우 `data_root` 디렉토리 (없으면 생성) |
| SOT-006 | 통합 출력 루트 존재 | CREATE | `integration.output_root` 디렉토리 |
| SOT-007 | 실행 순서 고유/순차 | HALT | `execution_order` 값 유일성 및 순차성 |
| SOT-008 | 프로토콜 파일 존재 | HALT | `orchestrator-protocol.md` 존재 |
| SOT-009 | 통합 스켈레톤 존재 | HALT | `integrated-report-skeleton.md` 존재 |
| SOT-010 | WF1에서 arXiv 비활성화 | HALT | WF1 소스에서 arXiv가 `enabled: false` |
| SOT-011 | WF2에서 arXiv 활성화 | HALT | WF2 소스에서 arXiv가 `enabled: true` |
| SOT-012 | 소스 중복 없음 | HALT | WF1/WF2/WF3/WF4 간 활성화된 소스 중복 없음 |
| SOT-013 | 병합 에이전트 존재 | HALT | `report-merger.md` 존재 |
| SOT-014 | 실행 무결성 섹션 존재 | HALT | `execution_integrity` 섹션 존재 |
| SOT-015 | SCG 규칙 유효성 | HALT | SCG 규칙에 필수 필드(id, name, severity, checks) 존재 |
| SOT-016 | PoE 스키마 유효성 | HALT | PoE 스키마에 `required_fields` 정의 |
| SOT-017 | 주간 스켈레톤 존재 | HALT | `weekly-report-skeleton.md` 존재 (주간 활성 시) |
| SOT-018 | 주간 출력 루트 존재 | CREATE | 주간 출력 디렉토리 (없으면 생성) |
| SOT-019 | 주간 검증 프로파일 정의 | HALT | `integration.weekly.validate_profile` 정의 |
| SOT-020 | WF3 네이버 소스 전용 | HALT | WF3 소스에서 NaverNews 활성화 |
| SOT-021 | WF3 오케스트레이터 존재 | HALT | `naver-scan-orchestrator.md` 존재 |
| SOT-022 | WF3 데이터 루트 존재 | CREATE | WF3 `data_root` 디렉토리 (없으면 생성) |
| SOT-023 | WF3 소스 설정 존재 | HALT | `sources-naver.yaml` 존재 |

심각도별 행동:
- **HALT**: 워크플로우 즉시 중단
- **CREATE**: 누락 디렉토리 자동 생성 후 계속
- **WARN**: 경고 로그 후 계속 진행

### 3.5 실행 무결성 (Execution Integrity)

#### 3.5.1 상태 파일 패턴

모든 오케스트레이터는 SOT에 정의된 패턴으로 상태 파일을 관리한다:

| 패턴 | 설명 |
|------|------|
| `{data_root}/logs/workflow-status-{date}.json` | 날짜별 워크플로우 상태 |
| `{data_root}/logs/workflow-status-latest.json` | 최신 상태 (기존 호환) |
| `{integration_root}/logs/master-status-{date}.json` | 마스터 상태 (날짜별) |
| `{integration_root}/logs/master-status-latest.json` | 마스터 최신 상태 |
| `{integration_root}/weekly/logs/weekly-status-{week_id}.json` | 주간 상태 |

#### 3.5.2 PoE (Proof of Execution)

모든 raw 데이터 파일에 `scan_metadata.execution_proof`로 실행 증명이 포함된다:

| 필수 필드 | 타입 | 형식 |
|----------|------|------|
| `execution_id` | string | `{workflow_id}-{date}-{time}-{random4}` |
| `started_at` | string | ISO8601 |
| `completed_at` | string | ISO8601 |
| `actual_api_calls` | object | `web_search`, `arxiv_api` 등 |
| `actual_sources_scanned` | array | 최소 1개 이상 |
| `file_created_at` | string | ISO8601 |

검증: 타임스탬프 오차 허용 5분, 최소 API 호출 1회, execution_id 형식 준수.

#### 3.5.3 SCG (State Consistency Gate)

4개 계층(+1 주간)의 일관성 검증이 시작 시, Phase 전환 시, 완료 시 실행된다:

| 계층 | 이름 | 검증 대상 | 심각도 |
|------|------|----------|--------|
| **SCG-L1** | SOT ↔ Master Status | SOT 버전 일치, 워크플로우 목록 일치 | HALT |
| **SCG-L2** | Master ↔ WF Status | WF 상태 일치, 날짜 일치, execution_id 일치 | HALT |
| **SCG-L3** | WF Status ↔ Raw Data | raw 파일 존재, PoE 유효, execution_id 일치 | HALT |
| **SCG-L4** | Raw Data ↔ Report | 신호 수 일관성, 보고서 날짜 일치 | WARN |
| **SCG-L5** | Weekly ↔ Daily | 일일 보고서 수 일치, 신호 수 일관성, 날짜 범위 유효 | WARN |

실패 시: HALT는 워크플로우 즉시 중단 + 사용자 보고, WARN은 경고 로그 + 계속 진행.

#### 3.5.4 사전 실행 검증 (Pre-Execution Check)

| ID | 검사 | 동작 |
|----|------|------|
| PEC-001 | 오늘 상태 파일 존재 여부 | completed→재실행 확인, in_progress→이어서 실행 확인, failed→재시도 확인 |
| PEC-002 | 전일 상태 확인 | 경고용 (미완료 시 알림) |
| PEC-003 | 주간 데이터 충분성 | 최소 5일치 일일 스캔 필요 (주간 전용) |

---

## 제4장: VEV 프로토콜과 검증 체계

### 4.1 VEV (Verify-Execute-Verify) 패턴

VEV 프로토콜은 모든 워크플로우 스텝의 100% 작업 완료를 보장하는 체계적 검증 메커니즘이다. 모든 WF1/WF2/WF3/WF4 오케스트레이터가 공유한다.

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

### 4.2 두 가지 VEV 변형

| 유형 | 적용 대상 | 단계 | 설명 |
|------|----------|------|------|
| **Full VEV** (5단계) | 핵심 워크플로우 스텝 | PRE → EXECUTE → POST(3-Layer) → RETRY → RECORD | 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.5, 3.6 |
| **VEV Lite** (3단계) | 번역 서브스텝 | PRE_CHECK → POST_CHECK → ON_FAIL | 1.2b, 1.2d, 1.3b, 2.1b, 2.2b, 2.3b, 2.4b, 3.2b, 3.3b |

VEV Lite는 번역 실패가 워크플로우를 중단시키지 않는다는 설계 원칙을 반영한다. 번역은 비핵심(non-critical) 기능이다.

### 4.3 Layer 3 실패 처리 정책

Layer 3(품질) 실패는 스텝의 컨텍스트에 따라 3가지 패턴 중 하나를 따른다:

| 패턴 | 적용 스텝 | 행동 | 이유 |
|------|----------|------|------|
| **A. Immediate Ask** | 1.2 | 사용자에게 즉시 질문 | 독립적 품질 영향 |
| **B. Defer to Checkpoint** | 1.3, 2.1, 2.3, 3.2 | 경고 로그 후 다음 체크포인트에서 리뷰 | 인간이 1.4/2.5/3.4에서 이슈를 확인할 수 있음 |
| **C. Silent Warn** | 1.1, 2.2, 3.1, 3.3 | 경고 로그 후 무음 진행 | 구조적으로 정확하며 품질 메모만 기록 |

### 4.4 Pipeline Gate (Phase 간 전환 검증)

3개의 Pipeline Gate가 Phase 간 데이터 연속성과 무결성을 보장한다. 모든 WF1/WF2/WF3/WF4에 동일하게 적용된다:

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
2. 보고서 완전성 (EN + KR, 필수 섹션 포함)
3. 아카이브 저장 확인
4. 스냅샷 생성 확인
5. 모든 스텝 검증 트레일 완전성
6. 인간 승인 기록 완전성

각 Gate 실패 시: TRACE_BACK → 실패한 Step 재실행 (최대 1회) → 재검증. 재시도 후에도 실패 시 HALT.

### 4.5 검증 보고서

모든 VEV 결과는 `{data_root}/logs/verification-report-{date}.json`에 누적된다. 최종 `overall_status`:

- `ALL_VERIFIED`: 모든 스텝 VERIFIED 또는 SKIPPED
- `VERIFIED_WITH_WARNINGS`: WARN_ACCEPTED 스텝 존재
- `PARTIAL`: FAILED 스텝 존재

### 4.6 검증 상태 값

| 상태 | 의미 |
|------|------|
| `VERIFIED` | 3개 Layer 모두 통과 |
| `WARN_ACCEPTED` | Layer 3 경고 있으나 실행 계속 |
| `RETRY_SUCCESS` | 초기 실패 후 재시도 성공 |
| `FAILED` | 최대 재시도 후에도 실패 |
| `SKIPPED` | 조건부 스텝 미활성화 |

---

## 제5장: 쿼드러플 워크플로우

### 5.1 실행 모드

```yaml
mode: "sequential"  # WF1 완료 → WF2 완료 → WF3 완료 → WF4 완료 → Merge
```

Master Orchestrator가 SOT의 `execution_order`에 따라 워크플로우를 순차 실행한다. 각 워크플로우는 독립적으로 3-Phase 파이프라인을 실행한다.

### 5.2 WF1: General Environmental Scanning (일반 환경스캐닝)

**소스**: `sources.yaml` — arXiv 제외, Base Tier 11개 + Expansion Tier 18개

#### Phase 1: Research (정보 수집)

| 스텝 | 이름 | 에이전트 | 입력 | 출력 |
|------|------|---------|------|------|
| 1.1 | Archive Loading | @archive-loader | signals/database.json | context/previous-signals.json |
| 1.2 | Multi-Source Scan | @multi-source-scanner | sources.yaml, domains.yaml | raw/daily-scan-{date}.json |
| 1.3 | Deduplication | @deduplication-filter | raw scan + previous-signals | filtered/new-signals-{date}.json |
| 1.4 | Human Review (선택적) | - | filtered signals | 사용자 결정 기록 |
| 1.5 | Expert Panel (조건부) | @realtime-delphi-facilitator | >50개 신호 시 활성화 | expert-validated signals |

**4단계 중복제거 캐스케이드**:

| 단계 | 방법 | 임계치 | 설명 |
|------|------|--------|------|
| Stage 1 | URL 정규화 + 완전 일치 | 1.0 (100%) | URL 정확 매칭 |
| Stage 2 | Jaro-Winkler 문자열 유사도 | 0.9 (90%) | 제목 기반 문자열 매칭 |
| Stage 3 | SBERT 의미적 유사도 | 0.8 (80%) | 코사인 유사도 (all-MiniLM-L6-v2) |
| Stage 4 | NER + Jaccard 엔터티 매칭 | 0.85 (85%) | 명명 엔터티 기반 매칭 |

**마라톤 모드 (Step 1.2, WF1 기본 모드)**:

마라톤 모드는 WF1의 기본 실행 모드다. Step 1.2는 2단계로 구성된다:

- **Stage A**: 기본(base) 소스 스캔 — 항상 실행
- **Stage B**: 확장(expansion) 소스 스캔 — 남은 시간 예산 내에서 실행 (`--base-only` 시 생략)
- **Merge**: Stage A + B 결과를 `raw/daily-scan-{date}.json`에 병합. 확장 신호에 `source.tier: "expansion"` 태그 부여

30분은 **상한선**(ceiling)이다. 모든 확장 소스 스캔이 끝나면 조기 종료한다.

#### Phase 2: Planning (분석 및 구조화)

| 스텝 | 이름 | 에이전트 | 핵심 행동 |
|------|------|---------|----------|
| 2.1 | Classification Verification | @signal-classifier | 분류 품질 검증, 저신뢰도 신호 식별 |
| 2.2 | Impact Analysis | @impact-analyzer | Futures Wheel + Cross-Impact Matrix + Bayesian Network |
| 2.3 | Priority Ranking | @priority-ranker | 가중 점수: Impact 40% + Probability 30% + Urgency 20% + Novelty 10% |
| 2.4 | Scenario Building (조건부) | @scenario-builder | 교차영향 복잡도 > 0.15 시 활성화 |
| 2.5 | Human Review (필수) | - | STEEPs 분류 검토, 우선순위 조정 |

**우선순위 점수 가중치** (모든 워크플로우 공통):
```
priority_score = impact × 0.40 + probability × 0.30 + urgency × 0.20 + novelty × 0.10
```

#### Phase 3: Implementation (보고서 생성)

| 스텝 | 이름 | 에이전트 | 핵심 행동 | 임계 |
|------|------|---------|----------|------|
| 3.1 | Database Update | @database-updater | 스냅샷 → 원자적 DB 업데이트 → 무결성 검증 | **CRITICAL** |
| 3.2 | Report Generation | @report-generator | 스켈레톤 기반 보고서 생성 (8개 섹션) | No |
| 3.3 | Archive & Notify | @archive-notifier | 아카이브 복사 + 스냅샷 + 알림 | No |
| 3.4 | Final Approval (필수) | - | `/env-scan:approve` 또는 `/env-scan:revision` | - |
| 3.5 | Quality Metrics | 오케스트레이터 | 실행 시간, 에이전트 성능, 품질 점수 | No |
| 3.6 | Self-Improvement | @self-improvement-analyzer | 5개 영역 분석, MINOR 자동 적용 | No |

### 5.3 WF2: arXiv Academic Deep Scanning (arXiv 학술 심층 스캐닝)

**소스**: `sources-arxiv.yaml` — arXiv 단일 소스, 심층 파라미터

| 파라미터 | 값 | 설명 |
|---------|---|------|
| `days_back` | 14 | 스캔 기간 (WF1의 7일 대비 2배) |
| `max_results_per_category` | 50 | STEEPs 카테고리당 최대 결과 수 |
| `arxiv_extended_categories` | true | 확장 arXiv 카테고리 활성화 |
| `marathon_mode` | false | 단일 소스이므로 마라톤 불필요 |

WF2는 WF1과 **동일한 3-Phase 파이프라인**을 실행하되, 소스가 arXiv 단일이고 파라미터가 심층 분석에 최적화되어 있다. 공유 워커 에이전트(signal-classifier, impact-analyzer 등)를 동일하게 사용한다.

### 5.4 WF3: Naver News Environmental Scanning (네이버 뉴스 환경스캐닝)

**소스**: `sources-naver.yaml` — 네이버 뉴스 6개 섹션

WF3는 3-Phase 파이프라인의 기본 구조를 따르되, **4개 전용 워커**와 **WF3 전용 분석 프레임워크**(제9장 참조)를 사용한다.

#### WF3 Phase 1: Research

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 1.1 | Archive Loading | @archive-loader (공유) | 동일 |
| 1.2 | **Naver News Crawling** | **@naver-news-crawler** (전용) | `naver_crawler.py` 실행, 6개 섹션 크롤링 |
| 1.3 | Deduplication | @deduplication-filter (공유) | 동일 |
| 1.4 | Human Review (선택적) | - | 동일 |

#### WF3 Phase 2: Planning

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 2.1 | STEEPs + **FSSF 분류** | @signal-classifier (공유) + **@naver-signal-detector** (전용) | FSSF 8유형 + Three Horizons 태깅 |
| 2.2 | Impact Analysis + **Pattern Detection** | @impact-analyzer (공유) + **@naver-pattern-detector** (전용) | Tipping Point Detection, Anomaly Detection |
| 2.3 | Priority Ranking | @priority-ranker (공유) | 동일 |
| 2.5 | Human Review (필수) | - | 동일 |

#### WF3 Phase 3: Implementation

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 3.1 | Database Update | @database-updater (공유) | 동일 |
| 3.2 | Report Generation | @report-generator (공유) | naver-report-skeleton 사용 |
| 3.3 | Archive & Notify + **Alert Dispatch** | @archive-notifier (공유) + **@naver-alert-dispatcher** (전용) | Tipping Point 경보 발송 |
| 3.4 | Final Approval (필수) | - | 동일 |
| 3.5~3.6 | Quality + SIE | 오케스트레이터 | 동일 |

### 5.5 WF4: Multi&Global-News Environmental Scanning (다국어 글로벌 뉴스 환경스캐닝)

**소스**: `sources-multiglobal-news.yaml` — 43개 직접 뉴스 사이트, 11개 언어

WF4는 WF3과 동일한 FSSF/Three Horizons/Tipping Point 프레임워크를 사용하되, **5개 전용 워커**와 **다국어 직접 크롤링** 방식을 사용한다.

| 파라미터 | 값 | 설명 |
|---------|---|------|
| `sources` | 43개 | 직접 뉴스 사이트 |
| `languages` | 11개 | 다국어 지원 (en, ko, zh, ja, de, fr, es, pt, ar, hi, ru) |
| `crawler` | `news_direct_crawler.py` | 직접 크롤링 (RSS/API 아닌 사이트 직접 접근) |
| `signal_processor` | `news_signal_processor.py` | FSSF/ThreeHorizons/TippingPoint 다국어 적용 |
| `validate_profile` | `multiglobal-news` | WF4 전용 검증 프로파일 |

#### WF4 Phase 1: Research

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 1.1 | Archive Loading | @archive-loader (공유) | 동일 |
| 1.2 | **Direct News Crawling** | **@news-direct-crawler** (전용) | `news_direct_crawler.py` 실행, 43개 사이트 다국어 크롤링 |
| 1.3 | Deduplication | @deduplication-filter (공유) | 동일 |
| 1.4 | Human Review (선택적) | - | 동일 |

#### WF4 Phase 2: Planning

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 2.1 | STEEPs + **FSSF 분류** | @signal-classifier (공유) + **@news-signal-detector** (전용) | FSSF 8유형 + Three Horizons 태깅 |
| 2.2 | Impact Analysis + **Pattern Detection** | @impact-analyzer (공유) + **@news-pattern-detector** (전용) | Tipping Point Detection, Anomaly Detection |
| 2.3 | Priority Ranking | @priority-ranker (공유) | 동일 |
| 2.5 | Human Review (필수) | - | 동일 |

#### WF4 Phase 3: Implementation

| 스텝 | 이름 | 에이전트 | 비고 |
|------|------|---------|------|
| 3.1 | Database Update | @database-updater (공유) | 동일 |
| 3.2 | Report Generation | @report-generator (공유) | multiglobal-news-report-skeleton 사용 |
| 3.3 | Archive & Notify + **Alert Dispatch** | @archive-notifier (공유) + **@news-alert-dispatcher** (전용) | Tipping Point 경보 발송 |
| 3.4 | Final Approval (필수) | - | 동일 |
| 3.5~3.6 | Quality + SIE | 오케스트레이터 | 동일 |

신호 ID 형식: `news-YYYYMMDD-{site_short}-NNN` (예: `news-20260224-reuters-001`)

### 5.6 Integration (통합)

WF1, WF2, WF3, WF4 보고서가 모두 완료되면, Master Orchestrator가 `report-merger` 에이전트(Agent-Teams 5 members)를 호출한다.

| 항목 | 설정 |
|------|------|
| **병합 에이전트** | `report-merger.md` (Agent-Teams 5 members) |
| **병합 범위** | 보고서만 병합 (signal DB는 독립 유지) |
| **신호 중복제거** | 불필요 (WF1/WF2/WF3/WF4 간 소스 중복 없음) |
| **순위화 방법** | pSST 통합 순위화 (`pSST_unified`) |
| **통합 상위 신호** | 20개 |
| **교차 워크플로우 분석** | 활성화 (WF1↔WF2↔WF3↔WF4 신호 상호작용 분석) |
| **스켈레톤** | `integrated-report-skeleton.md` |
| **검증 프로파일** | `integrated` |
| **인간 체크포인트** | 통합 보고서 최종 승인 (필수) |
| **출력** | `integrated/reports/daily/integrated-scan-{date}.md` |

### 5.7 Weekly Meta-Analysis (주간 메타분석)

`/env-scan:run-weekly`로 수동 트리거하는 별도 분석 모드다. 새로운 소스 스캐닝 없이, 최근 7일간 축적된 일일 스캔 결과를 거시적으로 재분석한다.

| 항목 | 설정 |
|------|------|
| **트리거** | 수동 (`/env-scan:run-weekly`) |
| **최소 조건** | 최소 5일치 일일 스캔 결과 필요 |
| **분석 범위** | 최근 7일 (`lookback_days: 7`) |
| **입력** | WF1/WF2/WF3/WF4/통합 보고서 + signal DB + 분석 파일 (읽기 전용) |
| **출력** | `integrated/weekly/reports/weekly-meta-{week_id}.md` |
| **스켈레톤** | `weekly-report-skeleton.md` |
| **검증 프로파일** | `weekly` |
| **주간 ID** | ISO 8601 (`{year}-W{week_number}`, 예: 2026-W06) |

**TIS (Trend Intensity Score) 가중치**:

```
TIS = n_sources × 0.30 + psst_delta × 0.30 + frequency × 0.20 + cross_domain × 0.20
```

| 차원 | 가중치 | 의미 |
|------|--------|------|
| `n_sources` | 0.30 | 해당 추세를 보고한 소스 수 |
| `psst_delta` | 0.30 | 7일간 pSST 점수 변화량 |
| `frequency` | 0.20 | 7일간 출현 빈도 |
| `cross_domain` | 0.20 | STEEPs 교차 도메인 출현 수 |

### 5.8 이중언어 워크플로우

```
Worker Agent (EN) → EN Output → VEV 검증 → @translation-agent → KR Output → VEV Lite 검증
```

**번역 품질 기준**:
- 평균 신뢰도: > 0.90
- STEEPs 용어 보존: 100% (위반 제로)
- 역번역 유사도: > 0.95 (핵심 보고서)
- 번역 오버헤드: 전체 워크플로우의 < 25%

### 5.9 Standard Signal Format (표준 신호 형식)

모든 워크플로우의 raw 데이터는 동일한 표준 형식을 따른다:

```json
{
  "scan_metadata": {
    "execution_proof": { ... }
  },
  "items": [
    {
      "id": "wf1-gen-2026-02-07-001",
      "title": "신호 제목",
      "source": {
        "name": "소스명",
        "type": "academic|patent|government|blog|news",
        "url": "https://...",
        "published_date": "2026-02-07"
      },
      "content": {
        "abstract": "요약",
        "keywords": ["키워드1", "키워드2"],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-02-07T09:15:42Z"
    }
  ]
}
```

WF3의 `content` 객체에는 추가로 `full_text` 필드가 포함된다.

---

## 제6장: 태스크 관리와 실행 흐름

### 6.1 태스크 체계 개요

Claude Code의 TaskCreate/TaskUpdate API를 활용하여 사용자에게 실시간 진행 가시성을 제공한다.

**핵심 원칙**:
- **비침습적**: workflow-status.json과 병행 운영 (대체 아님)
- **비핵심적**: 태스크 업데이트 실패는 워크플로우를 중단하지 않음
- **사용자 가시성 전용**: 사용자가 진행 상황을 확인하는 용도

### 6.2 Master Orchestrator 태스크 계층

```
Master Orchestrator
├── M-0: SOT Validation              ← validate_registry.py 실행
├── M-1: WF1 General Scanning        ← WF1 전체 실행
│   └── (WF1 내부 48+3 태스크)
├── M-2: WF2 arXiv Scanning          ← WF2 전체 실행
│   └── (WF2 내부 48+3 태스크)
├── M-3: WF3 Naver Scanning          ← WF3 전체 실행
│   └── (WF3 내부 태스크 + WF3 전용 태스크)
├── M-4: WF4 Multi&Global-News Scanning ← WF4 전체 실행
│   └── (WF4 내부 태스크 + WF4 전용 태스크)
├── M-5: Report Merge                ← 통합 보고서 병합
└── M-6: Final Approval              ← 통합 보고서 승인
```

### 6.3 개별 워크플로우 태스크 계층 (WF1/WF2 공통, 48 정적 + 3 조건부)

```
Phase 1: Research (phase1)
├── 1.1a: Load signals database
├── 1.1b: Load archive reports          [blockedBy: 1.1a]
├── 1.1c: Build deduplication indexes   [blockedBy: 1.1b]
├── 1.1d: Validate configuration files  [blockedBy: 1.1c]
├── 1.2a: Run multi-source scanner - Stage A base  [blockedBy: 1.1d]
├── 1.2a-M: Run expansion scanner - Stage B  [blockedBy: 1.2a] [WF1만; WF2 생략]
├── 1.2b: Translate raw scan results (KR)  [blockedBy: 1.2a-M]
├── 1.2c: Classify signals (STEEPs)     [blockedBy: 1.2a-M]
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
├── 2.4a: Build scenarios [조건부: 복잡도>0.15]
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

### 6.4 에러 처리

```python
# 모든 Task 업데이트는 try-except으로 래핑
try:
    TaskUpdate(task_id, status="completed")
except Exception:
    log_warning("Task update failed")
    # 계속 진행 - workflow-status.json이 진실의 원천
```

태스크 시스템은 순수한 **가시성 기능**이다. 그 실패는 워크플로우 실행에 영향을 주지 않는다.

---

## 제7장: pSST 신뢰도 프레임워크

### 7.1 개요

pSST(predicted Signal Scanning Trust)는 AlphaFold의 pLDDT에서 영감을 받은 **신호별 신뢰도 채점 체계**이다. 각 신호의 신뢰도를 6개 차원으로 분해하여 0~100 점수를 산출한다. 모든 WF1/WF2/WF3/WF4에 동일하게 적용된다.

### 7.2 6개 차원

| 차원 | 이름 | 가중치 | 측정 대상 | 사용 가능 시점 |
|------|------|--------|----------|-------------|
| **SR** | Source Reliability | 0.20 | 소스의 신뢰성 (학술:85, 특허:80, 블로그:45, SNS:30) | Stage 1 (수집) |
| **ES** | Evidence Strength | 0.20 | 정량적 데이터 보유, 다중 소스 확인, 검증 상태 | Stage 3 (분류) |
| **CC** | Classification Confidence | 0.15 | 카테고리 마진, 키워드 일치, 전문가 검증 | Stage 3 (분류) |
| **TC** | Temporal Confidence | 0.15 | 발행일 신선도 (7일:100, 90일+:30) + 신호 성숙도 보너스 | Stage 1 (수집) |
| **DC** | Distinctiveness Confidence | 0.15 | 중복제거 캐스케이드 통과 단계 (4단계 통과:100, 중복:0) | Stage 2 (필터링) |
| **IC** | Impact Confidence | 0.15 | 영향 클러스터 안정성, 교차영향 합의, 점수 일관성 | Stage 4 (영향분석) |

### 7.3 복합 점수 계산

```
pSST_score = (SR×0.20 + ES×0.20 + CC×0.15 + TC×0.15 + DC×0.15 + IC×0.15) × coverage_factor

coverage_factor = (available_weight / total_weight) ^ 0.5
```

가용 차원이 6개 미만일 때 커버리지 패널티가 적용된다. 지수 0.5(제곱근)는 중간 강도의 패널티를 의미한다.

### 7.4 Level 2 고급 채점

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

### 7.5 등급 체계

| 등급 | 점수 범위 | 행동 | 뱃지 |
|------|----------|------|------|
| **A** (very_high) | >= 95 (L2 활성 시) / >= 90 (L2 비활성 시) | 자동 승인 | 🟢 |
| **B** (confident) | >= 70 | 표준 처리 | 🔵 |
| **C** (low) | >= 50 | 리뷰 플래그 | 🟡 |
| **D** (very_low) | < 50 | 인간 리뷰 필수 | 🔴 |

### 7.6 파이프라인 게이트별 필수 차원

| 게이트 | 필수 차원 | 최소 pSST |
|--------|----------|----------|
| Gate 1 (수집 후) | SR, TC | 없음 |
| Gate 2 (분석 후) | SR, TC, DC, ES, CC | 30 |
| Gate 3 (완료 후) | SR, TC, DC, ES, CC, IC (전체 6개) | 없음 (보정 체크) |

### 7.7 통합 보고서에서의 pSST 활용

통합 보고서(Integration) 단계에서 `report-merger`는 WF1/WF2/WF3/WF4의 모든 신호를 pSST 통합 순위(`pSST_unified`)로 재순위화한다. 이를 통해 워크플로우 출처에 관계없이 가장 신뢰도 높은 신호가 상위에 배치된다.

### 7.8 보정 (Calibration)

| 항목 | 값 |
|------|---|
| 방법 | Platt Scaling |
| 목표 ECE | 0.05 |
| 최소 샘플 | 20개 인간 리뷰 |
| 트리거 간격 | 10회 스캔마다 |
| 이력 파일 | `calibration/psst-review-history.json` |

---

## 제8장: 에이전트 체계

### 8.1 에이전트 전체 구성

```
master-orchestrator (최상위 오케스트레이터)
│
├── env-scan-orchestrator (WF1 오케스트레이터)
│   ├── @archive-loader
│   ├── @multi-source-scanner
│   │   ├── @arxiv-agent          ← WF1에서는 비활성 (arXiv 제외)
│   │   ├── @patent-agent
│   │   ├── @policy-agent
│   │   └── @blog-agent
│   ├── @deduplication-filter
│   ├── @signal-classifier
│   ├── @impact-analyzer
│   ├── @priority-ranker
│   ├── @database-updater         ← CRITICAL
│   ├── @report-generator
│   ├── @archive-notifier
│   ├── @translation-agent
│   ├── @self-improvement-analyzer
│   ├── @realtime-delphi-facilitator  (조건부: >50 신호)
│   └── @scenario-builder             (조건부: 복잡도 >0.15)
│
├── arxiv-scan-orchestrator (WF2 오케스트레이터)
│   ├── (WF1과 동일한 공유 워커 사용)
│   └── @arxiv-agent              ← WF2에서 활성화 (arXiv 전용 심층 스캔)
│
├── naver-scan-orchestrator (WF3 오케스트레이터)
│   ├── (공유 워커 사용: archive-loader, deduplication-filter,
│   │    signal-classifier, impact-analyzer, priority-ranker,
│   │    database-updater, report-generator, archive-notifier,
│   │    translation-agent, self-improvement-analyzer)
│   ├── @naver-news-crawler       ← WF3 전용 (Step 1.2)
│   ├── @naver-signal-detector    ← WF3 전용 (Step 2.1 FSSF/ThreeHorizons)
│   ├── @naver-pattern-detector   ← WF3 전용 (Step 2.2 TippingPoint/Anomaly)
│   └── @naver-alert-dispatcher   ← WF3 전용 (Step 3.3 경보 발송)
│
├── multiglobal-news-scan-orchestrator (WF4 오케스트레이터)
│   ├── (공유 워커 사용: archive-loader, deduplication-filter,
│   │    signal-classifier, impact-analyzer, priority-ranker,
│   │    database-updater, report-generator, archive-notifier,
│   │    translation-agent, self-improvement-analyzer)
│   ├── @news-direct-crawler       ← WF4 전용 (Step 1.2, 43개 사이트 다국어 크롤링)
│   ├── @news-signal-detector      ← WF4 전용 (Step 2.1 FSSF/ThreeHorizons)
│   ├── @news-pattern-detector     ← WF4 전용 (Step 2.2 TippingPoint/Anomaly)
│   ├── @news-alert-dispatcher     ← WF4 전용 (Step 3.3 경보 발송)
│   └── @news-language-normalizer  ← WF4 전용 (다국어 정규화)
│
└── @report-merger (통합 단계, Agent-Teams 5 members)
```

### 8.2 에이전트 분류 요약

| 분류 | 수량 | 에이전트 |
|------|------|---------|
| **오케스트레이터** | 5 | master, env-scan, arxiv-scan, naver-scan, multiglobal-news-scan |
| **공유 워커** | 11 | archive-loader, multi-source-scanner, deduplication-filter, signal-classifier, impact-analyzer, priority-ranker, database-updater, report-generator, archive-notifier, translation-agent, self-improvement-analyzer |
| **소스별 서브에이전트** | 4 | arxiv-agent, patent-agent, policy-agent, blog-agent |
| **WF3 전용 워커** | 4 | naver-news-crawler, naver-signal-detector, naver-pattern-detector, naver-alert-dispatcher |
| **WF4 전용 워커** | 5 | news-direct-crawler, news-signal-detector, news-pattern-detector, news-alert-dispatcher, news-language-normalizer |
| **통합 워커** | 1 | report-merger |
| **조건부 워커** | 2 | realtime-delphi-facilitator, scenario-builder |
| **합계 (에이전트 스펙)** | **~40** | (exploration 에이전트 포함) |
| **프로토콜** | 1 | orchestrator-protocol.md |
| **가이드** | 1 | TASK_MANAGEMENT_EXECUTION_GUIDE.md |
| **프롬프트 템플릿** | 1 | classification-prompt-template.md |

### 8.3 워커 에이전트 설계 원칙

| 원칙 | 설명 |
|------|------|
| **순수 실행자** | 워커는 의사결정을 하지 않는다. 전달받은 소스 목록만 스캔한다 |
| **상태 무관** | 워커는 "마라톤 모드"나 "워크플로우 ID"를 알지 못한다. 오케스트레이터가 파라미터만 다르게 전달 |
| **독립 검증 없음** | 모든 검증(VEV)은 오케스트레이터 레벨에서 수행 |
| **실패 시 보고** | 워커는 에러를 반환하고, 재시도 결정은 오케스트레이터가 내린다 |

### 8.4 multi-source-scanner 런타임 파라미터 (v1.3.0)

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--days-back` | 스캔 기간 (일) | 7 (WF1), 14 (WF2) |
| `--tier` | 소스 티어 필터 (`base` 또는 `expansion`) | base |
| `--time-budget` | 스캔 시간 예산 (초) | 없음 |

### 8.5 소스별 서브에이전트

`@multi-source-scanner`는 내부적으로 4개의 소스별 에이전트를 병렬 호출한다:

| 에이전트 | 소스 유형 | 담당 범위 |
|---------|----------|----------|
| @arxiv-agent | academic | arXiv (WF2에서만 활성) |
| @patent-agent | patent | Google Patents, KIPRIS |
| @policy-agent | government/policy | Federal Register, EU Press, WHO |
| @blog-agent | news/blog | TechCrunch, MIT Tech Review, Economist |

---

## 제9장: WF3/WF4 전용 프레임워크

### 9.1 네이버 뉴스 6개 섹션 매핑

| 섹션 ID | 섹션명 | STEEPs 매핑 |
|---------|--------|------------|
| 100 | 정치 | **P** (Political) |
| 101 | 경제 | **E** (Economic) |
| 102 | 사회 | **S** (Social) |
| 103 | 생활/문화 | **S** (Social) |
| 104 | 세계 | **P** (Political) |
| 105 | IT/과학 | **T** (Technological) |

신호 ID 형식: `naver-YYYYMMDD-SID-NNN` (예: `naver-20260207-102-001`)

> **WF4 공유**: FSSF 8유형 분류, Three Horizons 태깅, Tipping Point Detection, Anomaly Detection은 WF3와 WF4가 공유하는 프레임워크이다. WF4는 `news_signal_processor.py`와 `news_direct_crawler.py`를 통해 동일한 분류 체계를 43개 다국어 뉴스 사이트에 적용한다.

### 9.2 FSSF 8유형 분류 체계

FSSF(Futures Signal System Framework)는 STEEPs와 직교하는 별도 분류 축이다. 모든 WF3/WF4 신호는 STEEPs 분류와 함께 FSSF 8유형 중 하나로 분류된다:

| # | 유형 | 영문 | 설명 |
|---|------|------|------|
| 1 | **약한 신호** | Weak Signal | 초기 변화의 징후, 아직 주류에 진입하지 않음 |
| 2 | **이머징 이슈** | Emerging Issue | 부상하는 이슈, 아직 합의가 형성되지 않음 |
| 3 | **추세** | Trend | 지속적 방향성을 가진 변화 |
| 4 | **메가트렌드** | Megatrend | 거시적, 장기적, 광범위한 변화 흐름 |
| 5 | **동인** | Driver | 변화를 추동하는 근본적 힘 |
| 6 | **와일드 카드** | Wild Card | 발생 확률 낮지만 영향이 극단적인 사건 |
| 7 | **불연속** | Discontinuity | 기존 추세의 급격한 단절 또는 전환 |
| 8 | **전조 사건** | Precursor Event | 더 큰 변화를 예고하는 구체적 사건 |

`naver_signal_processor.py`(WF3) 및 `news_signal_processor.py`(WF4)의 `FSSFClassifier` 클래스가 분류를 수행한다.

### 9.3 Three Horizons (3지평) 태깅

각 WF3/WF4 신호에 시간 지평(Time Horizon)이 태깅된다:

| 지평 | 기간 | 의미 |
|------|------|------|
| **H1** | 0~2년 | 현재 시스템 내 변화, 즉시 대응 가능 |
| **H2** | 2~7년 | 전환기 변화, 새로운 시스템이 부상 |
| **H3** | 7년+ | 근본적 변혁, 새로운 패러다임 |

### 9.4 Tipping Point Detection (티핑 포인트 감지)

`naver_signal_processor.py`(WF3) 및 `news_signal_processor.py`(WF4)의 `TippingPointDetector` 클래스가 두 가지 감지 방식을 사용한다:

| 감지 방식 | 설명 |
|----------|------|
| **Critical Slowing Down** | 시스템 회복 속도 감소 → 전환점 접근 신호 |
| **Flickering** | 두 상태 간 급격한 진동 → 체제 전환 임박 신호 |

**4단계 경보 체계**:

| 수준 | 색상 | 의미 | 행동 |
|------|------|------|------|
| Level 1 | 🟢 GREEN | 정상 | 모니터링 지속 |
| Level 2 | 🟡 YELLOW | 주의 | 추적 강화 |
| Level 3 | 🟠 ORANGE | 경고 | 즉시 분석 필요 |
| Level 4 | 🔴 RED | 위험 | 긴급 경보 발송 (@naver-alert-dispatcher) |

### 9.5 Anomaly Detection (이상 감지)

| 유형 | 설명 |
|------|------|
| **통계적 이상** | 정상 분포에서 크게 벗어나는 신호 빈도/강도 |
| **구조적 이상** | 기존 패턴/네트워크에서 벗어나는 구조적 변화 |

### 9.6 CrawlDefender 방어 체계

`naver_crawler.py`의 `CrawlDefender` 클래스는 7개 전략의 캐스케이드로 네이버 크롤링 차단을 방어한다:

| # | 전략 | 설명 |
|---|------|------|
| 1 | User-Agent 로테이션 | 다중 브라우저 UA 순환 |
| 2 | 요청 속도 제한 | 요청 간 지연 삽입 |
| 3 | 세션 관리 | 쿠키/세션 유지 |
| 4 | 리퍼러 설정 | 적절한 HTTP Referer 헤더 |
| 5 | 재시도 로직 | 실패 시 지수 백오프 재시도 |
| 6 | IP 로테이션 준비 | 프록시 설정 (선택적) |
| 7 | 응답 검증 | 차단 응답 감지 및 전략 전환 |

### 9.7 WF3 전용 Python 모듈

| 모듈 | 크기 | 역할 |
|------|------|------|
| `naver_crawler.py` | ~29KB | NaverNewsCrawler 클래스, CrawlDefender 7-전략, Article 데이터클래스 |
| `naver_signal_processor.py` | ~30KB | FSSFClassifier, ThreeHorizonsTagging, TippingPointDetector, AnomalyDetector |

### 9.8 WF4 전용 Python 모듈

| 모듈 | 역할 |
|------|------|
| `news_direct_crawler.py` | 43개 직접 뉴스 사이트 크롤러, 11개 언어 지원, CrawlDefender 통합 |
| `news_signal_processor.py` | FSSFClassifier, ThreeHorizonsTagging, TippingPointDetector 다국어 적용 |

---

## 제10장: 자기개선엔진 (SIE)

### 10.1 설계 원칙

> **"Improve the tuning, never break the machine"**

SIE는 Step 3.6에서 실행되며, 워크플로우 품질 메트릭을 분석하여 매개변수를 안전하게 조정한다. SIE 실패는 **절대로** 워크플로우를 중단하지 않는다.

### 10.2 독립 SIE 정책

```yaml
sie_policy: "independent"
```

각 워크플로우(WF1/WF2/WF3/WF4)는 자체 SIE를 독립적으로 실행한다. 공유 설정(`thresholds.yaml`, `domains.yaml`)은 SIE가 수정할 수 없으며, 수정하려면 MAJOR change 승인이 필요하다.

### 10.3 5개 분석 영역

| # | 영역 | 메트릭 | 제약 |
|---|------|--------|------|
| 1 | **Threshold Tuning** | false_positive_rate, false_negative_rate, human_corrections | max_delta_per_cycle, min/max 범위 |
| 2 | **Agent Performance** | execution_time, error_rate, retry_count (에이전트별) | 에이전트 비활성화/추가 불가 |
| 3 | **Classification Quality** | category_distribution_skew, confidence_gap, human_correction_patterns | STEEPs 카테고리 변경 불가 (불변) |
| 4 | **Workflow Efficiency** | phase_times_vs_targets, bottleneck_identification, idle_time | Phase 순서 변경/단계 생략 불가 |
| 5 | **Hallucination Tracking** | fabricated_signal_count, id_corruption_rate, url_invalidity_rate, date_anomaly_rate | 검증을 느슨하게 만들 수 없음 (엄격화만 가능) |

### 10.4 변경 분류 체계

| 분류 | 행동 | 예시 |
|------|------|------|
| **MINOR** | 자동 적용 (주기당 최대 3개) | 중복제거 임계치 ±5%, 타임아웃 조정 |
| **MAJOR** | 사용자 승인 후 적용 | 소스 추가/제거, 중복제거 전략 변경, 보고서 구조 변경 |
| **CRITICAL** | 즉시 차단 (사용자 오버라이드 불가) | 불변 경계(core invariants) 위반 시도 |

### 10.5 안전 한도

| 항목 | 값 |
|------|---|
| 주기당 최대 MINOR 자동 적용 | 3개 |
| 주기당 최대 조정 폭 | ±10% |
| 최소 증거 샘플 크기 | 10개 데이터 포인트 |
| 최소 과거 워크플로우 수 | 3개 (비교 기준) |
| 자동 롤백 퇴보 임계치 | >5% 성능 저하 |
| 롤백 이력 보관 | 최근 10개 변경 스냅샷 |

### 10.6 실패 처리

```yaml
On_Fail:
  action: ROLLBACK_all_changes_this_cycle
  log: "SIE cycle failed — all changes reverted"
  continue: true  # SIE 실패는 절대로 워크플로우를 중단하지 않음
```

SIE 내 VEV POST-VERIFY Layer 2에서 불변 경계 위반이 감지되면, 해당 주기의 **모든** 변경을 롤백한다.

### 10.7 마라톤 모드 연동

마라톤 모드 실행 후, SIE는 확장 소스의 품질을 자동 추적한다:
- 어떤 확장 소스가 고품질 신호를 생산했는지 분석
- "PubMed에서 12개 고품질 신호 발견 → base tier 승격 제안" 가능
- 이는 MAJOR change 프로세스를 통해 사용자 승인 후 적용

---

## 제11장: 설정과 확장 포인트

### 11.1 설정 파일 (12개)

| 파일 | 역할 |
|------|------|
| `config/workflow-registry.yaml` | **SOT** — 쿼드러플 워크플로우 시스템 정의 (제3장 참조) |
| `config/domains.yaml` | STEEPs 6개 카테고리 키워드 및 검색어 정의 |
| `config/sources.yaml` | WF1 소스 (arXiv 제외, Base 11개 + Expansion 18개) |
| `config/sources-arxiv.yaml` | WF2 전용 소스 (arXiv 단일, 심층 파라미터) |
| `config/sources-naver.yaml` | WF3 전용 소스 (네이버 뉴스 6개 섹션) |
| `config/sources-multiglobal-news.yaml` | WF4 전용 소스 (43개 직접 뉴스 사이트, 11개 언어) |
| `config/exploration-frontiers.yaml` | 소스 탐색 프론티어 설정 |
| `config/thresholds.yaml` | 중복제거/AI 신뢰도/우선순위/pSST/마라톤 임계치 |
| `config/ml-models.yaml` | AI/ML 모델 설정 (SBERT, 분류기) |
| `config/translation-terms.yaml` | EN-KR 번역 용어 매핑 |
| `config/core-invariants.yaml` | 불변 경계 정의 (제12장 참조) |
| `config/self-improvement-config.yaml` | SIE 행동, 안전 한도, 분석 영역 설정 |

### 11.2 2-Tier 소스 아키텍처 (WF1, sources.yaml)

**Base Tier** (항상 스캔 — 11개):

| 소스 | 유형 | 신뢰도 | STEEPs 초점 |
|------|------|--------|------------|
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
| (+ 기타 base 소스) | | | |

**Expansion Tier** (기본 스캔, `--base-only` 시 생략 — 18개):

| 카테고리 | 소스 | 유형 | 신뢰도 |
|---------|------|------|--------|
| Academic | PubMed Central, Nature News, Science Magazine, IEEE Spectrum | academic | 0.85-0.9 |
| Policy | OECD Newsroom, World Bank Blogs, UN News, EUR-Lex | policy/government | 0.8-0.85 |
| Think Tank | Brookings, WEF Agenda, Pew Research | think_tank | 0.8-0.85 |
| Tech | Hacker News, Wired, Ars Technica | blog/news | 0.6-0.75 |
| Environmental | NASA Climate Change, Carbon Brief | academic/news | 0.8-0.85 |
| Economic | IMF Blog, BIS Speeches | government | 0.85-0.9 |

### 11.3 마라톤 모드 설정 (thresholds.yaml)

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

### 11.4 슬래시 커맨드 (9개)

| 커맨드 | 파일 | 기능 |
|--------|------|------|
| `/env-scan:run` | `commands/env-scan/run.md` | 전체 쿼드러플 워크플로우 실행 (WF1→WF2→WF3→WF4→Merge) |
| `/env-scan:run-arxiv` | `commands/env-scan/run-arxiv.md` | WF2 단독 실행 (arXiv 심층 스캐닝) |
| `/env-scan:run-naver` | `commands/env-scan/run-naver.md` | WF3 단독 실행 (네이버 뉴스 스캐닝) |
| `/env-scan:run-weekly` | `commands/env-scan/run-weekly.md` | 주간 메타분석 실행 |
| `/env-scan:status` | `commands/env-scan/status.md` | 현재 워크플로우 진행 상황 확인 |
| `/env-scan:review-filter` | `commands/env-scan/review-filter.md` | Step 1.4 중복 필터링 리뷰 |
| `/env-scan:review-analysis` | `commands/env-scan/review-analysis.md` | Step 2.5 분석 결과 리뷰 |
| `/env-scan:approve` | `commands/env-scan/approve.md` | Step 3.4 최종 보고서 승인 |
| `/env-scan:revision` | `commands/env-scan/revision.md` | 보고서 수정 요청 |

### 11.5 스킬 (7개)

| 스킬 | 설명 |
|------|------|
| `env-scanner` | 쿼드러플 워크플로우 환경 스캐닝 시스템 |
| `longform-journalism` | 환경 스캐닝 보고서 → 장편 저널리즘 변환 |
| `skill-creator` | 새 스킬 생성 도구 |
| `slash-command-creator` | 슬래시 커맨드 생성 도구 |
| `subagent-creator` | 서브에이전트 생성 도구 |
| `hook-creator` | Claude Code 훅 생성 도구 |
| `youtube-collector` | YouTube 데이터 수집기 |

### 11.6 보고서 스켈레톤 (5종)

| 스켈레톤 | 파일 | 용도 |
|---------|------|------|
| **WF1/WF2 보고서** | `report-skeleton.md` | 일반/arXiv 일일 보고서 (8개 섹션, 15개 신호) |
| **WF3 보고서** | `naver-report-skeleton.md` | 네이버 일일 보고서 (FSSF/ThreeHorizons 포함) |
| **WF4 보고서** | `multiglobal-news-report-skeleton.md` | 다국어 글로벌 뉴스 일일 보고서 (FSSF/ThreeHorizons/TippingPoint 포함) |
| **통합 보고서** | `integrated-report-skeleton.md` | WF1+WF2+WF3+WF4 통합 보고서 (20개 신호, 교차 분석) |
| **주간 보고서** | `weekly-report-skeleton.md` | 주간 메타분석 보고서 (TIS, 추세 분석) |

### 11.7 Context Preservation Hooks (컨텍스트 보존 훅)

세션 연속성을 보장하기 위한 자동 훅 시스템:

| 훅 | 이벤트 | 기능 |
|----|--------|------|
| **SessionStart** | 세션 시작 | 최신 컨텍스트 백업 읽기, 워크플로우 상태 복원 |
| **SessionStop** | 세션 종료 | 현재 상태를 `context-backups/`에 저장 |
| **PreCompact** | 컨텍스트 압축 전 | 작업 상태 백업 |
| **PostToolUse** | 도구 사용 후 | 중요 작업 결과 기록 |

백업 위치: `.claude/context-backups/latest-context.md`

### 11.8 Python 코어 모듈 (33개)

| 모듈 | 역할 |
|------|------|
| `naver_crawler.py` | 네이버 뉴스 크롤러 + CrawlDefender |
| `naver_signal_processor.py` | FSSF/ThreeHorizons/TippingPoint/Anomaly |
| `psst_calculator.py` | pSST 6차원 점수 계산 |
| `psst_calibrator.py` | Platt Scaling 기반 pSST 보정 |
| `embedding_deduplicator.py` | SBERT 임베딩 기반 중복제거 |
| `impact_matrix_compressor.py` | 교차영향 매트릭스 압축 |
| `self_improvement_engine.py` | SIE 핵심 엔진 |
| `database_recovery.py` | 스냅샷 기반 DB 복구 |
| `context_manager.py` | SharedContextManager (에이전트 간 컨텍스트) |
| `unified_task_manager.py` | 통합 태스크 관리 |
| `translation_parallelizer.py` | 번역 병렬 처리 |
| `adaptive_fetcher.py` | 적응형 웹 데이터 수집 |
| `source_health_checker.py` | 소스 가용성/건강 확인 |
| `redirect_resolver.py` | URL 리다이렉트 해석 |
| `index_cache_manager.py` | 인덱스 캐시 관리 |
| `lazy_report_generator.py` | 지연 보고서 생성 최적화 |
| `news_direct_crawler.py` | WF4 직접 뉴스 사이트 크롤러 (43개 사이트, 11개 언어) |
| `news_signal_processor.py` | WF4 FSSF/ThreeHorizons/TippingPoint 다국어 적용 |
| `bilingual_resolver.py` | 이중언어 해석기 |
| `dedup_gate.py` | 중복제거 게이트 |
| `exploration_gate.py` | 소스 탐색 게이트 |
| `exploration_merge_gate.py` | 탐색 병합 게이트 |
| `frontier_selector.py` | 프론티어 선택기 |
| `report_metadata_injector.py` | 보고서 메타데이터 주입기 |
| `report_statistics_engine.py` | 보고서 통계 엔진 |
| `signal_evolution_tracker.py` | 신호 진화 추적기 |
| `skeleton_mirror.py` | 스켈레톤 미러링 |
| `source_explorer.py` | 소스 탐색기 |
| `temporal_anchor.py` | 시간 앵커 |
| `temporal_gate.py` | 시간 게이트 |
| `timeline_map_generator.py` | 타임라인 맵 생성기 |
| `translation_validator.py` | 번역 검증기 |
| `__init__.py` | 패키지 초기화 |

---

## 제12장: 불변의 경계

### 12.1 개요

`core-invariants.yaml`은 시스템의 **절대 불변 요소**를 정의한다. SIE는 모든 제안된 변경을 이 파일과 대조 검증해야 하며, 불변 요소를 건드리는 변경은 CRITICAL로 분류되어 **즉시 차단**된다. 사용자 오버라이드도 불가능하다.

### 12.2 CRITICAL: 불변 요소 (10개)

| # | 불변 요소 | 설명 |
|---|----------|------|
| 1 | **3-Phase 워크플로우** | Research → Planning → Implementation 구조 |
| 2 | **인간 체크포인트** | WF별 2개(2.5 필수, 3.4 필수) + 통합 1개 = 9개 제거 불가 |
| 3 | **STEEPs 6개 카테고리** | S, T, E, E, P, s 카테고리 자체를 변경 불가 |
| 4 | **VEV 프로토콜 5단계** | PRE-VERIFY → EXECUTE → POST-VERIFY → RETRY → RECORD |
| 5 | **Pipeline Gate 3개** | Phase 간 전환 검증 게이트 제거/우회 불가 |
| 6 | **데이터베이스 원자성** | 스냅샷 → 원자적 쓰기 → 실패 시 복원 → ID 유니크성 |
| 7 | **Phase 순서** | [1, 2, 3] 순서 엄수, 건너뛰기 불가 |
| 8 | **이중언어 프로토콜** | 내부=영어, 외부=한국어 통신 패턴 |
| 9 | **보고서 품질 4중 방어** | L1(스켈레톤) → L2(검증) → L3(재시도) → L4(골든 레퍼런스) |
| 10 | **워크플로우 독립성** | WF1/WF2/WF3/WF4 간 교차 읽기/쓰기 금지, 각 WF 독립 삭제 가능 |

> **불변 요소 #9 상세** (v1.3.0, 2026-02-02 도입)
>
> 2026-02-02 보고서 회귀 사건(22KB vs 71KB, 신호 필드 5/9, 섹션 3개 누락)으로 인해 도입된 4중 방어 체계이다.
>
> | Layer | 이름 | 역할 | 관련 아티팩트 |
> |-------|------|------|-------------|
> | L1 | **스켈레톤 템플릿** | 자유 생성이 아닌 구조 채우기 방식 강제 | `references/report-skeleton.md` |
> | L2 | **프로그래밍적 검증** | 14개 체크 자동 실행 (CRITICAL 7개, ERROR 7개) | `scripts/validate_report.py` |
> | L3 | **점진적 재시도** | CRITICAL 실패 시 3단계 에스컬레이션 | 오케스트레이터 Step 3.2 |
> | L4 | **골든 레퍼런스** | 완전한 9필드 신호 예시를 에이전트에 상시 삽입 | `report-generator.md` |
>
> **금지 행위**:
> - L2 검증 스크립트 실행 건너뛰기
> - L1 스켈레톤 없이 자유 형식 생성
> - L3 재시도 없이 CRITICAL FAIL 보고서 승인 진행
> - L4 골든 레퍼런스 섹션 삭제 또는 9개 미만으로 축소
> - `validate_report.py`의 CRITICAL 체크 기준값 완화
> - SIE에 의한 `quality_thresholds` 값 변경 (불변)

### 12.3 MINOR: SIE 자동 조정 가능 매개변수

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

### 12.4 MAJOR: 사용자 승인 필수 영역 (6개)

| 영역 | 설명 | 관련 파일 |
|------|------|----------|
| scanner_sources | 데이터 소스 추가/제거/순서 변경 | sources.yaml, sources-arxiv.yaml, sources-naver.yaml, sources-multiglobal-news.yaml |
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
| STEEPs 용어 정확도 | 100% (위반 제로) |

---

## 교차 참조

| 문서 | 위치 | 내용 |
|------|------|------|
| Master Orchestrator | `.claude/agents/master-orchestrator.md` | 최상위 오케스트레이터 전체 명세 |
| WF1 Orchestrator | `.claude/agents/env-scan-orchestrator.md` | WF1 오케스트레이터 명세 |
| WF2 Orchestrator | `.claude/agents/arxiv-scan-orchestrator.md` | WF2 오케스트레이터 명세 |
| WF3 Orchestrator | `.claude/agents/naver-scan-orchestrator.md` | WF3 오케스트레이터 명세 |
| WF4 Orchestrator | `.claude/agents/multiglobal-news-scan-orchestrator.md` | WF4 오케스트레이터 명세 |
| SOT | `env-scanning/config/workflow-registry.yaml` | 단일 진실의 원천 |
| 태스크 관리 가이드 | `.claude/agents/TASK_MANAGEMENT_EXECUTION_GUIDE.md` | 태스크 계층 상세 |
| 공유 프로토콜 | `.claude/agents/protocols/orchestrator-protocol.md` | VEV/Pipeline Gate 공유 프로토콜 |
| 구현 가이드 | `IMPLEMENTATION_GUIDE.md` | 구현 영역 상세 |
| 사용자 가이드 | `USER_GUIDE.md` | 일일 운영 가이드 (v4.0) |
| 변경 이력 | `CHANGELOG.md` | 버전별 변경 기록 |

---

## 버전 정보

| 구성요소 | 버전 |
|---------|------|
| 시스템 | Quadruple Workflow System v3.0.0 |
| SOT (workflow-registry) | 3.0.0 |
| Master Orchestrator | 1.0.0 |
| WF1 Orchestrator (env-scan) | 3.1.0 |
| WF2 Orchestrator (arxiv-scan) | 1.0.0 |
| WF3 Orchestrator (naver-scan) | 1.0.0 |
| WF4 Orchestrator (multiglobal-news-scan) | 1.0.0 |
| VEV 프로토콜 | 2.2.0 |
| pSST 프레임워크 | 1.0.0 |
| SIE | 1.0.0 |
| Execution Integrity (PoE/SCG) | 1.0.0 |
| 스킬 (env-scanner) | 2.0.0 |
| 본 문서 | 3.0.0 |
| 최종 갱신 | 2026-02-24 |

### 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 2.0.0 | 2026-02-07 | Triple Workflow System — WF1/WF2/WF3 아키텍처 문서화 |
| 3.0.0 | 2026-02-24 | Quadruple Workflow System — WF4 (Multi&Global-News, 43개 사이트, 11개 언어) 추가. 인간 체크포인트 7→9개. Agent-Teams 5 members 통합. 33개 Python 모듈, ~40개 에이전트 스펙, 12개 설정 파일 |
