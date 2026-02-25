# 환경 스캐닝 시스템 v2.5.0 — 사용자 매뉴얼

**버전**: 5.0 (2026-02-24)
**대상**: 시스템 운영자 / 인수인계 대상
**시스템**: Quadruple Workflow Environmental Scanning System v2.5.0

---

## 목차

- [Part 1: 시스템 개요](#part-1-시스템-개요)
- [Part 2: 빠른 시작](#part-2-빠른-시작)
- [Part 3: 일일 운영 절차](#part-3-일일-운영-절차)
- [Part 4: 보고서 읽기 가이드](#part-4-보고서-읽기-가이드)
- [Part 5: 설정 변경](#part-5-설정-변경)
- [Part 6: 에이전트 카탈로그](#part-6-에이전트-카탈로그)
- [Part 7: 자동화 및 고급 기능](#part-7-자동화-및-고급-기능)
- [Part 8: 문제 해결](#part-8-문제-해결)
- [Part 9: 부록](#part-9-부록)

---

# Part 1: 시스템 개요

## 1.1 시스템이 하는 일

전 세계의 학술 논문, 특허, 정책 문서, 기술 블로그, 한국 뉴스, 전 세계 43개 주요 뉴스 사이트를 AI로 자동 스캔하여 **미래 변화의 초기 신호(weak signals)**를 탐지하고, 분류하고, 우선순위를 매기고, 보고서를 생성하는 시스템이다.

> **절대 목표**: 미래 트렌드, 중기 변화, 거시적 전환, 패러다임 변화, 임계 전환, 특이점, 돌발 사건, 예측 불가능한 미래의 초기 신호를 전 세계에서 가능한 한 빠르게 포착한다.

시스템은 **4개의 독립 워크플로우**가 각자의 소스를 스캔하고, 결과를 통합 보고서로 병합하는 구조다.

## 1.2 Quadruple Workflow 아키텍처

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    마스터 오케스트레이터                                      │
│            (SOT 읽기 → 검증 → 순차 실행 → 통합)                              │
└───────┬──────────────┬──────────────┬──────────────┬─────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
 ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
 │  WF1 일반     │ │  WF2 arXiv   │ │  WF3 네이버   │ │  WF4 Multi&      │
 │  환경스캐닝    │ │  학술 심층     │ │  뉴스스캐닝    │ │  Global-News     │
 │              │ │              │ │              │ │                  │
 │ 25+ 글로벌   │ │ arXiv 단독    │ │ 네이버 뉴스   │ │ 43개 글로벌 뉴스  │
 │ 소스 스캔     │ │ 42개 카테고리  │ │ 6개 섹션     │ │ 11개 언어        │
 └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └───────┬──────────┘
        │              │              │                  │
        └──────┬───────┴──────────────┴──────────────────┘
               ▼
      ┌──────────────────┐
      │   통합 보고서      │
      │  (pSST 통합 랭킹)  │
      │  Agent-Teams 5명  │
      └──────────────────┘
```

**핵심 원칙**: 4개 워크플로우는 **완전히 독립적**이다.
- WF1은 WF2, WF3, WF4의 데이터를 읽지 않는다
- WF2는 WF1, WF3, WF4의 데이터를 읽지 않는다
- WF3는 WF1, WF2, WF4의 데이터를 읽지 않는다
- WF4는 WF1, WF2, WF3의 데이터를 읽지 않는다
- 통합은 **최종 보고서만** 병합한다 (원시 데이터 교환 없음)

**실행 순서**: WF1 → WF2 → WF3 → WF4 → 통합 (순차)

### 각 워크플로우 요약

| 항목 | WF1 일반 환경스캐닝 | WF2 arXiv 학술 심층 | WF3 네이버 뉴스 | WF4 Multi&Global-News |
|------|---------------------|---------------------|----------------|----------------------|
| **소스** | 25+ 글로벌 소스 (arXiv 제외) | arXiv 단독 (42개 카테고리) | 네이버 뉴스 (6개 섹션) | 43개 글로벌 뉴스 사이트 |
| **언어** | 영어 | 영어 | 한국어 | 11개 언어 (영/한/중/일/독/불/서/포/아/힌/인니) |
| **룩백 기간** | 7일 | 14일 | 당일 | 당일 |
| **결과/카테고리** | 20개 | 50개 | 전체 수집 | 전체 수집 |
| **고유 분석** | STEEPs + pSST | STEEPs + pSST | STEEPs + FSSF + Tipping Point | STEEPs + FSSF + 3H + Tipping Point |
| **보고서** | 일반 보고서 (Top 10) | 학술 보고서 (Top 10) | 네이버 보고서 (Top 10) | 글로벌 뉴스 보고서 (Top 10) |
| **데이터 경로** | `wf1-general/` | `wf2-arxiv/` | `wf3-naver/` | `wf4-multiglobal-news/` |

### 각 워크플로우의 3-Phase 구조

모든 워크플로우는 동일한 3단계 파이프라인을 따른다:

```
Phase 1: Research (정보 수집)
  소스 스캔 → 중복 제거 → [사용자 검토 선택]

Phase 2: Planning (분석)
  분류 검증 → 영향 분석 → 우선순위 → [사용자 검토 필수]

Phase 3: Implementation (보고서)
  DB 업데이트 → 보고서 생성 → 아카이브 → [사용자 승인 필수]
```

## 1.3 STEEPs 분류 체계

모든 신호는 6개 카테고리로 분류된다 (변경 불가):

| 코드 | 카테고리 | 범위 |
|------|---------|------|
| **S** | Social (사회) | 인구, 교육, 노동, 도시화, 문화 변화 |
| **T** | Technological (기술) | AI, 양자컴퓨팅, 바이오, 블록체인, 디지털 전환 |
| **E** | Economic (경제) | 시장, 금융, 무역, 공급망, 플랫폼 경제 |
| **E** | Environmental (환경) | 기후, 지속가능성, 자원, 생물다양성 |
| **P** | Political (정치) | 정책, 법률, 규제, 지정학, 제도 변화 |
| **s** | spiritual (영성) | 윤리, 심리, 가치관, 의미, AI 윤리 |

## 1.4 FSSF 8유형 분류 (WF3/WF4 공통)

WF3 네이버 뉴스와 WF4 Multi&Global-News 워크플로우에서는 STEEPs 분류에 더해 **FSSF(Future Signal Scanning Framework)** 8유형 분류가 추가된다:

| 유형 | 한국어 | 설명 | 우선순위 |
|------|--------|------|----------|
| Weak Signal | 약신호 | 아직 가시성이 낮은 초기 지표 | CRITICAL |
| Wild Card | 와일드카드 | 낮은 확률, 높은 영향 | CRITICAL |
| Discontinuity | 단절 | 기존 패턴과의 급격한 단절 | CRITICAL |
| Driver | 동인 | 변화를 이끄는 인과적 힘 | HIGH |
| Emerging Issue | 부상 이슈 | 관심이 증가하지만 아직 주류 아님 | HIGH |
| Precursor Event | 전조 사건 | 더 큰 변화를 예고하는 구체적 사건 | HIGH |
| Trend | 추세 | 데이터로 확인된 방향성 | MEDIUM |
| Megatrend | 메가트렌드 | 대규모, 장기적 거시 흐름 | MEDIUM |

**Three Horizons (3개 시간 지평)**:
- **H1** (0~2년): 단기 발전, 현재 체제 내 변화
- **H2** (2~7년): 중기 전환, 새로운 시스템 등장
- **H3** (7년+): 장기 변혁, 패러다임 전환

**Tipping Point (임계점) 탐지**:
- **Critical Slowing Down**: 회복 속도 감소 → 임계점 접근 징후
- **Flickering**: 감정/입장이 급격히 오가는 진동 패턴
- 경고 수준: GREEN → YELLOW → ORANGE → RED

## 1.5 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **SOT** | Source of Truth. `workflow-registry.yaml` 파일. 시스템의 모든 설정이 여기서 파생된다 |
| **pSST** | predicted Signal Scanning Trust. 6차원 신뢰도 점수 (0~100) |
| **VEV** | Verify-Execute-Verify. 모든 단계에서 사전/사후 검증을 수행하는 품질 보증 프로토콜 |
| **SCG** | State Consistency Gate. 4계층 데이터 일관성 검증 |
| **PoE** | Proof of Execution. 실행 증명 (타임스탬프, API 호출 기록 포함) |
| **TIS** | Trend Intensity Score. 주간 추세 강도 점수 |
| **FSSF** | Future Signal Scanning Framework. WF3/WF4 공용 8유형 분류 체계 |
| **SIE** | Self-Improvement Engine. 자기개선엔진 (자동 매개변수 미세 조정) |
| **CrawlDefender** | WF3 네이버 차단 우회 7단계 전략 캐스케이드 |
| **Agent-Teams** | 통합 보고서 생성을 위한 5인 에이전트 팀 |

---

# Part 2: 빠른 시작

## 2.1 사전 요구사항

- Python 3.8 이상
- Claude Code CLI 설치
- 인터넷 연결

## 2.2 첫 스캔 실행

```bash
# 1. 프로젝트 디렉토리에서 Claude Code 실행
cd EnvironmentScan-system-main-v4
claude

# 2. 전체 스캔 시작 (WF1 + WF2 + WF3 + WF4 + 통합)
/env-scan:run

# 3. 이후 시스템이 안내하는 체크포인트를 따라간다
```

첫 실행 시 시스템이 자동으로:
1. SOT(workflow-registry.yaml) 검증 (55개 규칙)
2. WF1: 25+ 소스에서 신호 수집 → 분석 → 보고서 생성
3. WF2: arXiv 42개 카테고리에서 학술 논문 수집 → 분석 → 보고서 생성
4. WF3: 네이버 뉴스 6개 섹션 크롤링 → FSSF 분류 → 보고서 생성
5. WF4: 43개 글로벌 뉴스 사이트 11개 언어 크롤링 → FSSF 분류 → 보고서 생성
6. 통합: 4개 워크플로우 결과를 Agent-Teams 5인이 pSST 통합 랭킹으로 병합

**체크포인트 흐름**:

```
WF1 Phase 2 → /env-scan:review-analysis   (필수)
WF1 Phase 3 → /env-scan:approve           (필수)
WF2 Phase 2 → /env-scan:review-analysis   (필수)
WF2 Phase 3 → /env-scan:approve           (필수)
WF3 Phase 2 → /env-scan:review-analysis   (필수)
WF3 Phase 3 → /env-scan:approve           (필수)
WF4 Phase 2 → /env-scan:review-analysis   (필수)
WF4 Phase 3 → /env-scan:approve           (필수)
통합 보고서  → /env-scan:approve           (필수)
```

## 2.3 체크포인트 따라하기

시스템이 체크포인트에 도달하면 사용자에게 검토를 요청한다. 안내에 따라 응답하면 된다:

1. **분석 검토** (Phase 2, 각 WF별): STEEPs 분류와 우선순위를 확인한다
2. **보고서 승인** (Phase 3, 각 WF별): 보고서가 좋으면 `/env-scan:approve`, 수정이 필요하면 `/env-scan:revision "피드백"`

## 2.4 보고서 확인

실행 완료 후 다음 위치에서 보고서를 확인한다:

| 보고서 | 위치 |
|--------|------|
| WF1 일반 보고서 | `env-scanning/wf1-general/reports/daily/environmental-scan-{date}.md` |
| WF2 arXiv 보고서 | `env-scanning/wf2-arxiv/reports/daily/environmental-scan-{date}.md` |
| WF3 네이버 보고서 | `env-scanning/wf3-naver/reports/daily/environmental-scan-{date}.md` |
| WF4 글로벌 뉴스 보고서 | `env-scanning/wf4-multiglobal-news/reports/daily/environmental-scan-{date}.md` |
| **통합 보고서** | `env-scanning/integrated/reports/daily/integrated-scan-{date}.md` |
| 주간 보고서 | `env-scanning/integrated/weekly/reports/weekly-scan-{week-id}.md` |

---

# Part 3: 일일 운영 절차

## 3.1 전체 스캔 (`/env-scan:run`)

4개 워크플로우 + 통합 보고서를 한 번에 실행한다.

```bash
/env-scan:run
```

**실행 흐름**:

```
/env-scan:run
    │
    ├─ SOT 검증 (55개 규칙) ──────────────────────────────
    │
    ├─ WF1: 일반 환경스캐닝 ──────────────────────────────
    │   Phase 1: 25+ 소스 스캔 → 4단계 중복 제거
    │     1.4 [선택] /env-scan:review-filter
    │   Phase 2: STEEPs 분류 → 영향 분석 → pSST 랭킹
    │     2.5 [필수] /env-scan:review-analysis
    │   Phase 3: DB 업데이트 → 보고서 생성
    │     3.4 [필수] /env-scan:approve
    │
    ├─ WF2: arXiv 학술 심층 ──────────────────────────────
    │   Phase 1: arXiv 42개 카테고리 스캔 (14일, 50/카테고리)
    │     1.4 [선택] /env-scan:review-filter
    │   Phase 2: STEEPs 분류 → 영향 분석 → pSST 랭킹
    │     2.5 [필수] /env-scan:review-analysis
    │   Phase 3: DB 업데이트 → 보고서 생성
    │     3.4 [필수] /env-scan:approve
    │
    ├─ WF3: 네이버 뉴스 스캐닝 ───────────────────────────
    │   Phase 1: 6개 섹션 크롤링 → 중복 제거
    │     1.4 [선택] /env-scan:review-filter
    │   Phase 2: STEEPs + FSSF 분류 → Tipping Point 탐지 → 랭킹
    │     2.5 [필수] /env-scan:review-analysis
    │   Phase 3: DB 업데이트 → 보고서 생성 → 알림
    │     3.4 [필수] /env-scan:approve
    │
    ├─ WF4: Multi&Global-News 스캐닝 ────────────────────
    │   Phase 1: 43개 글로벌 뉴스 사이트 크롤링 (11개 언어) → 중복 제거
    │     1.4 [선택] /env-scan:review-filter
    │   Phase 2: STEEPs + FSSF 분류 → Tipping Point 탐지 → 랭킹
    │     2.5 [필수] /env-scan:review-analysis
    │   Phase 3: DB 업데이트 → 보고서 생성 → 알림
    │     3.4 [필수] /env-scan:approve
    │
    └─ 통합 ──────────────────────────────────────────────
        4개 보고서 병합 → Agent-Teams 5인 → pSST 통합 랭킹 → Top 20 선정
        [필수] /env-scan:approve (통합 보고서)
```

**플래그 옵션**:

| 옵션 | 설명 |
|------|------|
| `(없음)` | 전체 스캔: WF1 + WF2 + WF3 + WF4 + 통합 |
| `--base-only` | WF1을 Base 소스만 스캔 (Expansion 생략), WF2+WF3+WF4는 동일 |
| `--multiglobal-news-only` | WF4만 단독 실행 (글로벌 뉴스만) |

## 3.2 arXiv 단독 스캔 (`/env-scan:run-arxiv`)

WF2만 실행한다. WF1, WF3, WF4, 통합은 생략된다.

```bash
/env-scan:run-arxiv
```

**사용 시기**:
- 학술 논문 중심 신호만 필요할 때
- WF1이 이미 실행된 상태에서 arXiv 보충이 필요할 때
- 이전 실행에서 arXiv API 장애로 WF2가 실패한 경우 재시도

**파라미터**:
- 룩백 기간: 14일 (WF1의 7일보다 확장)
- 카테고리당 최대 결과: 50개 (WF1의 20개보다 확장)
- 타임아웃: 60초
- 체크포인트: 2개 (Step 2.5, Step 3.4)

## 3.3 네이버 단독 스캔 (`/env-scan:run-naver`)

WF3만 실행한다. WF1, WF2, WF4, 통합은 생략된다.

```bash
/env-scan:run-naver
```

**사용 시기**:
- 한국 뉴스 동향만 빠르게 파악할 때
- FSSF 분류, Tipping Point 탐지가 목적일 때
- 네이버 차단으로 이전 실행이 실패한 경우 재시도

**네이버 뉴스 6개 섹션**:

| 섹션 | 코드 | STEEPs 매핑 |
|------|------|-------------|
| 정치 | 100 | P (Political) |
| 경제 | 101 | E (Economic) |
| 사회 | 102 | S (Social) |
| 생활문화 | 103 | S (Social) |
| 세계 | 104 | P (Political) |
| IT과학 | 105 | T (Technological) |

**WF3 전용 분석**:
- FSSF 8유형 분류 (약신호 ~ 전조사건)
- Three Horizons 태깅 (H1/H2/H3)
- Tipping Point 탐지 (Critical Slowing Down + Flickering)
- 이상 탐지 (통계적 + 구조적)
- 긴급 알림 생성 (RED 수준 시)

## 3.4 Multi&Global-News 단독 스캔 (`/env-scan:run --multiglobal-news-only`)

WF4만 실행한다. WF1, WF2, WF3, 통합은 생략된다.

```bash
/env-scan:run --multiglobal-news-only
```

**사용 시기**:
- 전 세계 다국어 뉴스 동향을 빠르게 파악할 때
- 특정 지역(유럽, 중동, 아시아 등)의 뉴스 신호가 필요할 때
- WF3(네이버)과의 한국 뉴스 교차 검증이 목적일 때

**WF4 소스 (43개 글로벌 뉴스 사이트, 11개 언어)**:
- 영어: NYT, WSJ, FT, Bloomberg, Reuters, AP, BBC, The Guardian, The Economist, Al Jazeera English 등
- 한국어: 조선일보, 중앙일보, 한겨레 등
- 일본어: 日本経済新聞, NHK 등
- 중국어: 新华网, South China Morning Post 등
- 독일어: Der Spiegel, FAZ 등
- 프랑스어: Le Monde 등
- 기타: El Pais (스페인어), Folha de S.Paulo (포르투갈어), Al Jazeera Arabic (아랍어), NDTV (힌디어), Kompas (인도네시아어)

**WF4 전용 분석**:
- FSSF 8유형 분류 + Three Horizons 태깅
- Tipping Point 탐지
- 크롤링 통계 (사이트별 성공/실패/차단 현황)
- 번역 통계 (언어별 번역 품질 점수)
- 페이월 돌파 로그 (Total War 전략: NYT/FT/WSJ/Bloomberg)

## 3.5 주간 메타분석 (`/env-scan:run-weekly`)

지난 7일간의 일일 스캔 데이터를 종합 분석한다. **새로운 소스 스캔은 하지 않는다** (READ-ONLY).

```bash
/env-scan:run-weekly
```

**사전 조건**:
- 최근 7일 내 일일 통합 보고서가 최소 5개 이상 존재해야 한다
- 같은 ISO 8601 주(YYYY-W##)에 이미 주간 보고서가 있으면 중복 방지 경고

**분석 내용**:
- TIS (Trend Intensity Score) 계산으로 추세 강도 측정
- 가속/감속/신규 등장/소멸 신호 분류
- 신호 수렴 클러스터 탐지 (여러 신호가 하나의 테마로 모이는 현상)
- STEEPs 도메인별 주간 추세 변화

**TIS 계산 공식**:
```
TIS = 0.30 x 소스 수 + 0.30 x pSST 변화량 + 0.20 x 언급 빈도 + 0.20 x 도메인 다양성
```

**TIS 등급**:

| 등급 | 점수 | 의미 |
|------|------|------|
| Surging | 0.8 이상 | 급부상 |
| Rising | 0.6~0.8 | 상승세 |
| Stable | 0.4~0.6 | 안정적 |
| Declining | 0.2~0.4 | 하락세 |
| Fading | 0.2 미만 | 소멸 중 |

## 3.6 체크포인트 운영

### `/env-scan:review-filter` (Phase 1, 선택)

중복 제거 결과를 검토한다. AI 확신도가 0.9 미만인 경우에만 시스템이 요청한다.

**확인할 것**:
- 제거된 중복 신호 목록이 합리적인가
- 실제로 다른 신호가 잘못 제거되지 않았는가
- 중복 제거율이 극단적이지 않은가 (30~70%가 정상)

**결정**:
- 중복 확인 (제거 유지)
- 강제 포함 (다시 포함시킴)

검토 없이 넘어가도 된다. 이 체크포인트는 선택 사항이다.

### `/env-scan:review-analysis` (Phase 2, 필수)

이 체크포인트는 **반드시 거쳐야** 한다.

**확인할 것**:

1. **STEEPs 분류가 맞는가**
   - 각 신호의 카테고리(S/T/E/E/P/s)가 내용과 일치하는지 훑어본다
   - 명백히 잘못된 분류가 있으면 수정을 지시한다

2. **우선순위가 합리적인가**
   - 상위 10개 신호가 실제로 중요한 신호인가
   - 중요한 신호가 하위로 밀려나지 않았는가
   - 우선순위 올리기(+1/+2) 또는 내리기(-1/-2) 가능

3. **WF3/WF4의 경우 추가 확인**
   - FSSF 분류가 적절한가 (약신호인지, 추세인지)
   - Tipping Point 경고 수준이 합리적인가
   - Three Horizons 배정이 타당한가

### `/env-scan:approve` (Phase 3, 필수)

보고서가 좋으면 승인한다.

```bash
/env-scan:approve
```

**승인 전 확인 체크리스트**:
- [ ] 섹션 1: 경영진 요약 (Top 3 신호 + 통계)
- [ ] 섹션 2: 신규 탐지 신호 (Top 10, 9개 필드)
- [ ] 섹션 3: 기존 신호 업데이트 (강화/약화)
- [ ] 섹션 4: 패턴 및 연결고리
- [ ] 섹션 5: 전략적 시사점 (즉시/중기/모니터링)
- [ ] 섹션 7: 신뢰도 분석
- [ ] 섹션 8: 부록

### `/env-scan:revision` (수정 요청)

보고서에 수정이 필요하면 피드백과 함께 수정을 요청한다.

```bash
/env-scan:revision "상위 5개 신호에 대해 더 상세한 분석 추가"
/env-scan:revision "경영진 요약을 더 간결하게 수정"
/env-scan:revision "지정학적 리스크 부분을 더 강조하고 구체적 대응 방안 추가"
```

수정 후 다시 `/env-scan:approve` 또는 `/env-scan:revision`을 선택한다. 수정 횟수 제한은 없다.

## 3.7 진행 상태 확인 (`/env-scan:status`)

```bash
/env-scan:status
```

현재 워크플로우의 상태를 표시한다:
- 워크플로우 ID, 시작 시간, 현재 Phase/Step
- 각 Phase 진행률 (완료 / 진행 중 / 대기)
- 생성된 아티팩트(파일) 목록
- 오류/경고/재시도 기록
- 다음 행동 안내

---

# Part 4: 보고서 읽기 가이드

## 4.1 일일 보고서 구조 (8개 섹션)

WF1과 WF2 보고서는 동일한 8개 섹션으로 구성된다:

| 섹션 | 내용 | 주목할 것 |
|------|------|----------|
| **1. 경영진 요약** | Top 3 신호 + 전체 통계 | 가장 중요한 신호와 전략적 시사점 |
| **2. 신규 탐지 신호** | Top 10 신호 (각 9개 필드) | STEEPs 분포, 핵심 사실, 정량 지표 |
| **3. 기존 신호 업데이트** | 추적 중인 신호의 상태 변화 | 강화/약화 추세 |
| **4. 패턴 및 연결고리** | 교차 영향, 떠오르는 테마 | 여러 카테고리에 걸친 패턴 |
| **5. 전략적 시사점** | 즉시/중기/모니터링 조치 | 행동 가능한 인사이트 |
| **6. Plausible Scenarios** | 조건부 (교차영향 복잡 시) | 시나리오별 핵심 동인 |
| **7. 신뢰도 분석** | pSST 등급 분포 | Grade A~D 분포 |
| **8. 부록** | 전체 신호 목록, 소스, 방법론 | 원본 데이터 확인 |

**각 신호의 9개 필수 필드**:

| # | 필드 | 내용 |
|---|------|------|
| 1 | 분류 | STEEPs 카테고리 |
| 2 | 출처 | 소스명, 날짜, URL |
| 3 | 핵심 사실 | 핵심 정성적 발견 |
| 4 | 정량 지표 | 수치 데이터 |
| 5 | 영향도 | 별점 + 점수 |
| 6 | 상세 설명 | 상세 분석 |
| 7 | 추론 | 전략적 추론 |
| 8 | 이해관계자 | 주요 행위자 |
| 9 | 모니터링 지표 | 선행 지표 |

## 4.2 통합 보고서 읽기

통합 보고서(`integrated-scan-{date}.md`)는 4개 워크플로우의 결과를 하나로 병합한다.

**일반 보고서와의 차이점**:

| 항목 | 일반 보고서 | 통합 보고서 |
|------|-----------|-----------|
| Top 신호 수 (요약) | 3개 | **5개** |
| 신호 상세 수 | 10개 | **15~20개** |
| 소스 태그 | 없음 | **[WF1] [WF2] [WF3] [WF4]** |
| 교차 분석 | 단일 워크플로우 내 | **워크플로우 간 교차 분석** |
| 랭킹 기준 | 워크플로우 내 pSST | **통합 pSST** |

**소스 태그 읽기**:

```
[WF1] DeepSeek V4 Launch — Chinese AI Global 30% Share (Technology)
      → 일반 환경스캐닝(글로벌 소스)에서 수집된 신호

[WF2] Being-H0.5: Cross-embodiment VLA Foundation Model (Technology)
      → arXiv 학술 심층스캐닝에서 수집된 신호

[WF3] 한국은행 기준금리 동결 결정 (Economic)
      → 네이버 뉴스 스캐닝에서 수집된 신호

[WF4] EU Carbon Border Tax Implementation Accelerated (Political)
      → 글로벌 뉴스 스캐닝에서 수집된 신호
```

**워크플로우 교차 분석 섹션** (4.3):
- **상호 강화 신호**: 복수 WF에서 동시에 감지된 같은 주제
- **학술 선행 신호**: WF2에서 먼저 감지되고 다른 WF에서 아직 나타나지 않은 신호
- **미디어 선행 신호**: WF1/WF3/WF4에서 먼저 감지되고 WF2에서 아직 나타나지 않은 신호
- **지역 교차 검증**: WF3(한국)과 WF4(글로벌)에서 동일 이슈의 지역별 관점 비교

## 4.3 주간 보고서 읽기

주간 보고서(`weekly-scan-{week-id}.md`)는 7일간의 추세를 종합한다.

**핵심 지표: TIS (Trend Intensity Score)**

각 주요 추세에 TIS 점수가 매겨진다. 높을수록 해당 추세가 강하다.

```
[AI 규제 강화 추세]  TIS: 0.85 (Surging)
  - 소스: 8개 (WF1: 3, WF2: 2, WF3: 1, WF4: 2)
  - pSST 변화: +12 (70 → 82)
  - 언급 빈도: 주 3회 → 주 7회
  - 도메인: T, P, E (3개 STEEPs에 걸침)
```

**주간 보고서 고유 섹션**:
- 가속 추세 (TIS 상승)
- 감속 추세 (TIS 하락)
- 신규 등장 신호 (이번 주 첫 탐지)
- 소멸 신호 (더 이상 언급 없음)
- 신호 수렴 클러스터 (여러 신호가 하나의 테마로 수렴)

## 4.4 네이버 보고서 특수 섹션

WF3 보고서에는 일반 8개 섹션에 더해 다음이 추가된다:

**FSSF 유형별 분포**:
```
약신호: 3개 | 부상 이슈: 5개 | 추세: 8개 | 메가트렌드: 1개
동인: 2개 | 와일드카드: 1개 | 단절: 0개 | 전조 사건: 2개
```

**Three Horizons 분포**:
```
H1 (0-2년): 12개 | H2 (2-7년): 7개 | H3 (7년+): 3개
```

**Tipping Point 알림 요약**:
```
RED:    0건 (즉시 대응 불필요)
ORANGE: 1건 — "반도체 공급망 재편" (Flickering 감지)
YELLOW: 3건
GREEN:  나머지
```

**긴급 알림 조건** (자동 트리거):
- Tipping Point RED 수준
- Wild Card + High Importance
- Discontinuity + Confidence 0.7 이상
- H3 + Weak Signal + 복수 STEEPs 도메인에 걸침

## 4.5 WF4 글로벌 뉴스 보고서 읽기 가이드

WF4 보고서는 WF3의 FSSF 체계를 공유하면서도 고유한 섹션이 추가된다:

**크롤링 통계 (Crawling Stats)**:
```
총 43개 사이트 | 성공: 40 | 실패: 2 | 차단(paywall): 1
NYT: 성공 (Total War 3차 시도) | FT: 실패 (paywall 돌파 불가)
평균 응답 시간: 2.3초 | 총 수집 기사: 287건
```

**번역 통계 (Translation Stats)**:
```
원문 언어 분포: EN 45% | KO 12% | JA 10% | ZH 8% | DE 7% | FR 6% | 기타 12%
번역 품질 (평균): 0.93 | 최저: 0.87 (아랍어) | 최고: 0.98 (영어→한국어)
STEEPs 용어 보존율: 100%
```

**방어 로그 (Defense Log)**:
```
페이월 전략 실행 로그:
  NYT — Total War: 1차 시도 실패 → 2차 시도 실패 → 3차 시도 성공
  WSJ — Total War: 1차 시도 성공
  Bloomberg — Total War: 접속 불가 (스킵)
  FT — Total War: 전략 소진 (대체 소스 사용)
```

WF4 보고서를 읽을 때 특히 주목할 점:
- **지역 교차 패턴**: 같은 이슈가 여러 지역 뉴스에서 동시에 보도되는 패턴
- **언어별 관점 차이**: 같은 사건에 대한 영어/중국어/아랍어 매체의 프레이밍 차이
- **페이월 누락**: 페이월 돌파 실패로 수집하지 못한 소스가 있으면, 해당 지역/주제의 커버리지 공백 확인

## 4.6 pSST 신뢰도 등급 해석

각 신호에는 **pSST (predicted Signal Scanning Trust)** 점수가 붙는다:

| 뱃지 | 등급 | 점수 | 의미 | 행동 |
|------|------|------|------|------|
| A | A (very high) | 90~100 | 매우 높은 신뢰도 | 자동 승인 수준 |
| B | B (confident) | 70~89 | 신뢰할 만함 | 표준 처리 |
| C | C (low) | 50~69 | 낮은 신뢰도 | 주의 깊게 검토 |
| D | D (very low) | 0~49 | 매우 낮은 신뢰도 | 반드시 인간 검토 |

**6개 차원**:

| 차원 | 약어 | 가중치 | 측정 대상 |
|------|------|--------|----------|
| 소스 신뢰성 | SR | 0.20 | 출처의 권위와 신뢰도 |
| 증거 강도 | ES | 0.20 | 정량적 데이터 보유 여부 |
| 분류 확신도 | CC | 0.15 | STEEPs 분류의 명확성 |
| 시간 확신도 | TC | 0.15 | 발행일 신선도 |
| 독특성 확신도 | DC | 0.15 | 중복제거 통과 수준 |
| 영향 확신도 | IC | 0.15 | 영향 분석의 안정성 |

**보고서에서의 해석 예시**:

```
[T] 양자 컴퓨팅 오류 보정 돌파  pSST: 87 B
  SR: 85 (arXiv 학술) | TC: 100 (3일 전) | DC: 100 (고유) | ES: 70 | CC: 80 | IC: 75
```

→ "학술 출처에서 온 최근 고유 신호이며, 전체적으로 신뢰할 수 있다."

**우선순위 점수** (pSST와 별개):

| 요소 | 가중치 | 의미 |
|------|--------|------|
| Impact (영향도) | 40% | 실현 시 영향 규모 |
| Probability (실현 가능성) | 30% | 실현 확률 |
| Urgency (긴급성) | 20% | 대응 시급성 |
| Novelty (새로움) | 10% | 정보의 새로움 |

---

# Part 5: 설정 변경

모든 설정 파일은 `env-scanning/config/` 디렉토리에 있다.

## 5.1 소스 관리

### WF1 소스 (`config/sources.yaml`)

25+ 소스를 관리한다. arXiv는 WF2로 이관되어 여기에 없다.

**Base 소스** (항상 스캔, 5개):

| 소스 | 유형 |
|------|------|
| Google Patents | 특허 |
| US Federal Register | 정책 |
| WHO Press Releases | 정책 |
| TechCrunch | 기술 뉴스 |
| MIT Technology Review | 기술 리뷰 |

**Expansion 소스** (기본 포함, `--base-only` 시 생략, 20개):

| 카테고리 | 소스 |
|---------|------|
| 학술 | PubMed Central, Nature News, Science Magazine, IEEE Spectrum |
| 정책 | OECD Newsroom, World Bank Blogs, UN News, EUR-Lex |
| 싱크탱크 | Brookings Institution, World Economic Forum, Pew Research |
| 기술 | Hacker News, Wired, Ars Technica |
| 환경 | NASA Climate Change, Carbon Brief |
| 경제 | IMF Blog, BIS Speeches |

**소스 활성화/비활성화**:

```yaml
- name: "TechCrunch"
  enabled: false    # true → false로 변경하면 스캔에서 제외
```

**주요 필드**:

| 필드 | 의미 |
|------|------|
| `tier` | `base` (항상) 또는 `expansion` (`--base-only` 시 생략) |
| `enabled` | `true`/`false` — 스캔 여부 |
| `critical` | `true`면 이 소스 실패 시 워크플로우 중단 |
| `max_results` | 한 번에 수집할 최대 항목 수 |
| `reliability` | `high`/`medium` — pSST SR 점수에 영향 |

### WF2 소스 (`config/sources-arxiv.yaml`)

arXiv 단독 소스 설정. 42개 arXiv 카테고리를 STEEPs에 매핑한다.

```yaml
# STEEPs별 arXiv 카테고리 예시
T_Technological:  # 13개 카테고리
  - cs.AI      # 인공지능
  - cs.RO      # 로보틱스
  - cs.CL      # 자연어처리
  - cs.CV      # 컴퓨터 비전
  - cs.LG      # 기계학습
  - quant-ph   # 양자물리
  # ... 등

E_Economic:  # 9개 카테고리
  - econ.EM    # 계량경제학
  - q-fin.EC   # 금융경제
  # ... 등
```

**파라미터**:
- `timeout`: 60초 (WF1의 30초보다 확장)
- `max_results`: 카테고리당 50개
- `days_back`: 14일

### WF3 소스 (`config/sources-naver.yaml`)

네이버 뉴스 크롤링 설정.

```yaml
sections:
  정치: 100
  경제: 101
  사회: 102
  생활문화: 103
  세계: 104
  IT과학: 105

crawling:
  min_delay: 2.0     # 요청 간 최소 대기 (초)
  max_delay: 5.0     # 요청 간 최대 대기 (초)
  section_delay: 5.0  # 섹션 전환 시 대기 (초)
  max_retries: 10    # URL당 최대 재시도
  fetch_content: true # 기사 본문 수집 여부
```

### WF4 소스 (`config/sources-multiglobal-news.yaml`)

43개 글로벌 뉴스 사이트 크롤링 설정. 11개 언어를 지원한다.

**페이월 전략**:
- NYT, FT, WSJ, Bloomberg: **Total War** (무한 재시도, 다중 우회 전략)
- 기타 유료 사이트: 표준 재시도 후 대체 소스 사용

## 5.2 임계값 조정 (`config/thresholds.yaml`)

**중복제거 임계값** (높일수록 엄격):

| 단계 | 현재값 | 범위 | 의미 |
|------|--------|------|------|
| Stage 1 URL 매칭 | 1.0 | 고정 | 완전 일치만 |
| Stage 2 문자열 유사도 | 0.9 | 0.7~0.98 | 제목 기반 매칭 |
| Stage 3 의미적 유사도 | 0.8 | 0.6~0.95 | SBERT 임베딩 비교 |
| Stage 4 엔터티 매칭 | 0.85 | 0.7~0.98 | 고유명사 기반 매칭 |

**우선순위 가중치** (합계 반드시 1.0):

```yaml
priority_scoring:
  impact: 0.40
  probability: 0.30
  urgency: 0.20
  novelty: 0.10
```

**pSST 차원 가중치** (합계 반드시 1.0):

```yaml
psst_weights:
  SR: 0.20   # 소스 신뢰성
  ES: 0.20   # 증거 강도
  CC: 0.15   # 분류 확신도
  TC: 0.15   # 시간 확신도
  DC: 0.15   # 독특성 확신도
  IC: 0.15   # 영향 확신도
```

## 5.3 도메인 키워드 (`config/domains.yaml`)

각 STEEPs 카테고리의 검색 키워드를 수정할 수 있다:

```yaml
T_Technological:
  keywords:
    - "artificial intelligence"
    - "quantum computing"
    - "새로 추가할 키워드"    # <- 여기에 추가
```

**주의**: STEEPs 6개 카테고리 자체(S, T, E, E, P, s)는 불변이다. 카테고리 내의 키워드만 수정할 수 있다.

## 5.4 SOT 구조 이해 (`config/workflow-registry.yaml`)

**workflow-registry.yaml**은 시스템의 **단일 진실 소스(Source of Truth)**다. 모든 워크플로우, 에이전트, 경로, 매개변수가 이 파일에서 정의된다.

**주요 섹션**:

| 섹션 | 내용 |
|------|------|
| `system` | 시스템명, 실행 모드(sequential), 프로토콜 경로 |
| `workflows.wf1-general` | WF1 설정: 소스, 데이터 경로, 파라미터, 체크포인트 |
| `workflows.wf2-arxiv` | WF2 설정: arXiv 전용 매개변수 |
| `workflows.wf3-naver` | WF3 설정: 네이버 전용 매개변수, FSSF, Tipping Point |
| `workflows.wf4-multiglobal-news` | WF4 설정: 글로벌 뉴스 전용 매개변수, 페이월 전략, 번역 |
| `integration` | 통합 설정: Agent-Teams 5인, 병합 전략, Top 신호 수, 교차 분석 |
| `integration.weekly` | 주간 분석 설정: TIS 가중치, 최소 일일 스캔 수 |
| `execution_integrity` | PoE 스키마, SCG 규칙, 상태 파일 패턴 |

**수정 후에는 반드시 검증을 실행한다**:

```bash
python3 env-scanning/scripts/validate_registry.py
```

55개 검증 규칙(SOT-001 ~ SOT-055)이 통과해야 시스템이 정상 실행된다.

## 5.5 자기개선엔진 설정 (`config/self-improvement-config.yaml`)

SIE의 작동 범위를 제어한다:

| 변경 유형 | 수준 | 동작 | 예시 |
|-----------|------|------|------|
| **MINOR** | 자동 적용 | 사용자 개입 없이 적용 | 임계값 +/-10%, 타임아웃 조정, pSST 가중치 미세 조정 |
| **MAJOR** | 사용자 승인 필요 | 제안 후 승인 시 적용 | 소스 추가/제거, 중복제거 전략 변경, 보고서 구조 변경 |
| **CRITICAL** | 항상 차단 | 절대 변경 불가 | 3-Phase 구조, STEEPs 카테고리, 인간 체크포인트, VEV 프로토콜 |

---

# Part 6: 에이전트 카탈로그

## 6.1 오케스트레이터 (5개)

| 에이전트 | 역할 | 위치 |
|----------|------|------|
| **master-orchestrator** | 전체 시스템 조율. SOT 검증 → WF1→WF2→WF3→WF4→통합 순차 실행 | `.claude/agents/master-orchestrator.md` |
| **env-scan-orchestrator** | WF1 일반 환경스캐닝 3-Phase 실행 | `.claude/agents/env-scan-orchestrator.md` |
| **arxiv-scan-orchestrator** | WF2 arXiv 학술 심층 3-Phase 실행 | `.claude/agents/arxiv-scan-orchestrator.md` |
| **naver-scan-orchestrator** | WF3 네이버 뉴스 3-Phase 실행 (FSSF/Tipping Point 포함) | `.claude/agents/naver-scan-orchestrator.md` |
| **multiglobal-news-orchestrator** | WF4 Multi&Global-News 3-Phase 실행 (다국어/페이월/FSSF) | `.claude/agents/multiglobal-news-orchestrator.md` |

## 6.2 공유 워커 에이전트 (11개)

모든 워크플로우에서 공통으로 사용하는 에이전트:

| 에이전트 | Phase | Step | 역할 |
|----------|-------|------|------|
| **archive-loader** | 1 | 1.1 | 기존 DB + 과거 보고서 로드 |
| **multi-source-scanner** | 1 | 1.2 | 다수 소스 병렬 스캔 (WF1/WF2 사용) |
| **deduplication-filter** | 1 | 1.3 | 4단계 중복 제거 (URL→문자열→의미적→엔터티) |
| **signal-classifier** | 2 | 2.1 | STEEPs 분류 + 메타데이터 생성 |
| **impact-analyzer** | 2 | 2.2 | Futures Wheel + 교차영향 매트릭스 |
| **priority-ranker** | 2 | 2.3 | 우선순위 산출 (pSST 통합 점수) |
| **database-updater** | 3 | 3.1 | 신호 DB 원자적 업데이트 (자동 백업) |
| **report-generator** | 3 | 3.2 | 스켈레톤 기반 보고서 생성 |
| **archive-notifier** | 3 | 3.3 | 보고서 아카이브 + 알림 |
| **translation-agent** | - | - | 영한 번역 (구조 보존) |
| **self-improvement-analyzer** | 3 | 3.6 | 매개변수 자동 미세 조정 |

## 6.3 WF3 전용 에이전트 (4개)

네이버 뉴스 워크플로우에서만 사용하는 에이전트:

| 에이전트 | Phase | Step | 역할 |
|----------|-------|------|------|
| **naver-news-crawler** | 1 | 1.2 | 네이버 뉴스 6개 섹션 크롤링 (CrawlDefender 탑재) |
| **naver-signal-detector** | 2 | 2.1 | FSSF 8유형 분류 + Three Horizons 태깅 |
| **naver-pattern-detector** | 2 | 2.2 | Tipping Point 탐지 + 이상 탐지 |
| **naver-alert-dispatcher** | 3 | 3.3 | 긴급 알림 발송 + 피드백 학습 |

## 6.4 WF4 전용 에이전트 (5개)

Multi&Global-News 워크플로우에서만 사용하는 에이전트:

| 에이전트 | Phase | Step | 역할 |
|----------|-------|------|------|
| **multiglobal-news-crawler** | 1 | 1.2 | 43개 글로벌 뉴스 사이트 크롤링 (Total War 페이월 전략) |
| **multiglobal-translator** | 1 | 1.2b | 11개 언어 → 영어 실시간 번역 |
| **multiglobal-signal-detector** | 2 | 2.1 | FSSF 8유형 분류 + Three Horizons 태깅 |
| **multiglobal-pattern-detector** | 2 | 2.2 | Tipping Point 탐지 + 지역 교차 패턴 분석 |
| **multiglobal-alert-dispatcher** | 3 | 3.3 | 긴급 알림 발송 + 지역별 경보 |

## 6.5 통합 Agent-Teams (5인)

통합 보고서 생성을 위한 Agent-Teams:

| 에이전트 | 역할 |
|----------|------|
| **report-merger** | 4개 WF 보고서 병합 총괄 |
| **wf1-analyst** | WF1 일반 신호 분석 대표 |
| **wf2-analyst** | WF2 학술 신호 분석 대표 |
| **wf3-analyst** | WF3 네이버 뉴스 분석 대표 |
| **wf4-analyst** | WF4 글로벌 뉴스 분석 대표 |

## 6.6 선택적 에이전트 (5개)

조건부로 활성화되는 에이전트:

| 에이전트 | 활성화 조건 | 역할 |
|----------|------------|------|
| **realtime-delphi-facilitator** | 신규 신호 50+개 | AI 전문가 패널 검증 |
| **scenario-builder** | 교차영향 복잡도 > 임계값 | QUEST 시나리오 생성 |
| **patent-agent** | 미구현 | 특허 DB 전용 스캔 (계획) |
| **policy-agent** | 미구현 | 정책 문서 전용 스캔 (계획) |

## 6.7 에이전트 의존성 다이어그램

```
마스터 오케스트레이터
│
├─ WF1 오케스트레이터
│   ├─ Phase 1: archive-loader → multi-source-scanner → deduplication-filter
│   ├─ Phase 2: signal-classifier → impact-analyzer → priority-ranker
│   └─ Phase 3: database-updater → report-generator → archive-notifier
│               → self-improvement-analyzer
│
├─ WF2 오케스트레이터 (WF1과 동일 구조, arXiv 전용)
│   ├─ Phase 1: archive-loader → multi-source-scanner → deduplication-filter
│   ├─ Phase 2: signal-classifier → impact-analyzer → priority-ranker
│   └─ Phase 3: database-updater → report-generator → archive-notifier
│               → self-improvement-analyzer
│
├─ WF3 오케스트레이터 (확장 구조)
│   ├─ Phase 1: archive-loader → naver-news-crawler → deduplication-filter
│   ├─ Phase 2: signal-classifier + naver-signal-detector (병렬)
│   │           → impact-analyzer + naver-pattern-detector (병렬)
│   │           → priority-ranker
│   └─ Phase 3: database-updater → report-generator
│               → archive-notifier + naver-alert-dispatcher (병렬)
│               → self-improvement-analyzer
│
├─ WF4 오케스트레이터 (다국어 확장 구조)
│   ├─ Phase 1: archive-loader → multiglobal-news-crawler
│   │           → multiglobal-translator → deduplication-filter
│   ├─ Phase 2: signal-classifier + multiglobal-signal-detector (병렬)
│   │           → impact-analyzer + multiglobal-pattern-detector (병렬)
│   │           → priority-ranker
│   └─ Phase 3: database-updater → report-generator
│               → archive-notifier + multiglobal-alert-dispatcher (병렬)
│               → self-improvement-analyzer
│
└─ Agent-Teams 5인 (통합 보고서)
    report-merger + wf1-analyst + wf2-analyst + wf3-analyst + wf4-analyst
```

---

# Part 7: 자동화 및 고급 기능

## 7.1 자동화 설정

### CLI 자동화 (데이터 수집만)

```bash
cd env-scanning
bash scripts/setup_automation.sh
```

대화형 메뉴에서 실행 시간을 선택한다 (9AM / 12PM / 6PM / Custom).

**주의**: CLI 자동화는 스캔 + DB 업데이트만 수행한다. 3-Phase 전체 워크플로우(분류, 영향 분석, 보고서 생성)는 Claude Code에서 수동으로 실행해야 한다.

### 주간 분석 스케줄

주간 메타분석은 수동 트리거만 지원한다:

```bash
/env-scan:run-weekly
```

매주 월요일 아침에 실행하는 것을 권장한다.

## 7.2 Context Preservation 훅

Claude Code 세션이 토큰 한계에 도달하면 자동으로 컨텍스트가 압축된다. 이때 진행 중인 작업 상태가 유실될 수 있다. **Context Preservation 훅**이 이를 방지한다.

**동작 방식**:

```
작업 중 (PostToolUse 훅)
  → 모든 Edit/Write/Bash 작업을 work-log.jsonl에 기록

응답 완료 시 (Stop 훅)
  → latest-context.md에 현재 상태 업데이트

토큰 75% 도달 시 (PreCompact 훅)
  → 완전한 스냅샷을 latest-context.md에 저장
  → 타임스탬프 백업 생성

세션 시작 시 (SessionStart 훅)
  → latest-context.md 감지 → "컨텍스트 복원 필요" 알림
```

**설치** (최초 1회):

```bash
python3 .claude/hooks/scripts/test_hooks.py    # 테스트
python3 .claude/hooks/scripts/setup_hooks.py   # 설치
# Claude Code 재시작
```

**저장되는 정보**: 파일 경로, 도구명, 커맨드 요약, Git 상태, 타임스탬프
**저장되지 않는 정보**: 파일 내용, 대화 텍스트, API 키, 민감 정보

## 7.3 Longform Journalism 변환

환경 스캐닝 보고서를 Foreign Affairs/The Atlantic 스타일의 장편 저널리즘으로 변환할 수 있다.

**사용법**: Claude Code에서 longform-journalism 스킬을 호출한다.

**변환 특징**:
- 모든 핵심 사실이 보존되는 무손실 변환
- 내러티브 중심 구조 (시간순/인과/비교)
- 내부 코드(WF1, WF2, pSST 등) 제거
- 메타데이터는 미주(endnotes)로 분리

## 7.4 자기개선엔진 (SIE)

매 워크플로우 완료 후(Step 3.6) 자동으로 성능을 분석하고 매개변수를 미세 조정한다.

**5개 분석 영역**:
1. 중복제거 정확도
2. 분류 성능
3. 영향 분석 품질
4. 보고서 완성도
5. 실행 시간 효율

**안전 장치**:
- MINOR 변경만 자동 적용 (주기당 최대 3개)
- MAJOR 변경은 사용자 승인 후 적용
- CRITICAL 항목은 절대 변경 불가
- 변경 이력이 `improvement-log.json`에 기록

## 7.5 State Consistency Gate (SCG)

4계층 데이터 일관성 검증 시스템:

| 계층 | 범위 | 검증 내용 |
|------|------|----------|
| L1 | SOT ↔ 마스터 상태 | 버전 일치, 워크플로우 목록 일치 |
| L2 | 마스터 ↔ WF 상태 | 상태값 일치, 날짜 일치, 실행ID 일치 |
| L3 | WF 상태 ↔ 원시 데이터 | 파일 존재, PoE 유효, 타임스탬프 유효 |
| L4 | 원시 데이터 ↔ 보고서 | 신호 수 일관, 보고서 날짜 일치 |

SCG 검증이 실패하면 워크플로우가 일시정지된다.

## 7.6 Execution Integrity (PoE)

모든 스캔에는 실행 증명(Proof of Execution)이 포함된다:

```json
{
  "execution_id": "wf1-scan-2026-02-06-07-15-42-a3f2",
  "started_at": "2026-02-06T07:15:42Z",
  "completed_at": "2026-02-06T07:35:58Z",
  "actual_api_calls": {"web_search": 17, "arxiv_api": 0},
  "actual_sources_scanned": ["Google Patents", "Federal Register"],
  "file_created_at": "2026-02-06T07:35:58Z"
}
```

PoE는 해당 스캔이 실제로 실행되었음을 증명하며, SCG L3 검증에서 확인된다.

---

# Part 8: 문제 해결

## 8.1 SOT 검증 실패

```bash
# 검증 실행
python3 env-scanning/scripts/validate_registry.py
```

**실패 시 대응**:

| 심각도 | 의미 | 대응 |
|--------|------|------|
| HALT | 워크플로우 실행 불가 | 해당 규칙의 원인을 수정해야 함 |
| CREATE | 디렉토리 자동 생성 | 자동 해결됨 |
| WARN | 경고 (실행 가능) | 확인 후 필요시 수정 |

**자주 발생하는 검증 실패**:

| 규칙 | 원인 | 해결 |
|------|------|------|
| SOT-001 | 공유 파일(skeleton 등) 경로 오류 | 파일 존재 확인, 경로 수정 |
| SOT-005 | 데이터 디렉토리 미존재 | 자동 생성됨 (CREATE) |
| SOT-010 | WF1에 arXiv가 포함됨 | sources.yaml에서 arXiv 비활성화 |
| SOT-012 | 워크플로우 간 소스 중복 | 각 소스가 정확히 하나의 WF에만 속하는지 확인 |

## 8.2 보고서 검증 실패

보고서 생성 후 자동으로 14개 검증이 실행된다:

```bash
# 수동 검증 실행
python3 env-scanning/scripts/validate_report.py <보고서파일경로>
```

**주요 검증 규칙**:

| 규칙 | 검증 내용 | 실패 시 |
|------|----------|---------|
| FILE-001 | 파일 존재 | 보고서 재생성 |
| SEC-001 | 8개 섹션 헤더 존재 | 누락 섹션 보완 |
| SIG-001 | 10개 이상 신호 블록 | 신호 추가 |
| SIG-002 | 각 신호에 9개 필드 | 누락 필드 보완 |
| QUAL-001 | 5000단어 이상 | 내용 보강 |
| KOR-001 | 한국어 100자 이상 | 한국어 콘텐츠 확인 |
| SKEL-001 | `{{PLACEHOLDER}}` 미잔류 | 미채워진 플레이스홀더 채우기 |

검증 실패 시 시스템이 자동으로 최대 2회 재생성을 시도한다 (3단계 점진적 에스컬레이션).

## 8.3 WF2 arXiv API 장애

arXiv API에 접근할 수 없는 경우:

1. 시스템이 자동으로 지수적 백오프 재시도 (3초, 9초, 27초)
2. 모든 재시도 실패 시 워크플로우 일시정지
3. 사용자에게 WF2 건너뛰기 옵션 제공

**수동 재시도**:
```bash
/env-scan:run-arxiv
```

## 8.4 WF3 네이버 차단 (CrawlDefender)

네이버가 크롤링을 차단하면 **CrawlDefender**가 자동으로 7단계 전략을 순차 적용한다:

| 단계 | 전략 | 설명 |
|------|------|------|
| 1 | default | 기본 HTTP 헤더 |
| 2 | httpx_h2 | HTTP/2 비동기 요청 |
| 3 | rotate_headers | 랜덤 User-Agent 회전 |
| 4 | delay_increase | 요청 간격 점진적 증가 |
| 5 | proxy_rotation | 프록시 전환 |
| 6 | session_reset | 세션 재생성 |
| 7 | browser_emulation | 브라우저 에뮬레이션 |

모든 전략 소진 시 워크플로우가 일시정지되며, 시간을 두고 재시도하거나 WF3를 건너뛸 수 있다.

## 8.5 WF4 페이월 장애 (Total War)

WF4의 유료 뉴스 사이트(NYT, FT, WSJ, Bloomberg)에 접근할 수 없는 경우:

1. **Total War** 전략이 자동으로 무한 재시도
2. 모든 우회 전략 소진 시 해당 사이트 스킵 (워크플로우는 계속)
3. 방어 로그에 실패 기록
4. 다음 실행 시 성공한 전략부터 시도

**수동 재시도**:
```bash
/env-scan:run --multiglobal-news-only
```

## 8.6 데이터베이스 복구

각 워크플로우의 데이터베이스(`signals/database.json`)에 문제가 생기면 스냅샷에서 복원한다:

```bash
# WF1 스냅샷 확인
ls env-scanning/wf1-general/signals/snapshots/

# WF2 스냅샷 확인
ls env-scanning/wf2-arxiv/signals/snapshots/

# WF3 스냅샷 확인
ls env-scanning/wf3-naver/signals/snapshots/

# WF4 스냅샷 확인
ls env-scanning/wf4-multiglobal-news/signals/snapshots/
```

**Python으로 복원**:
```python
from env_scanning.core import restore_latest

# WF1 최신 스냅샷으로 복원
restore_latest(Path("env-scanning/wf1-general/signals/database.json"))
```

데이터베이스 업데이트(Step 3.1)는 항상 자동으로 스냅샷을 먼저 생성한 후 원자적으로 업데이트한다. 실패 시 자동으로 이전 상태로 복원된다.

## 8.7 Context 손실 복원

Claude Code 세션이 끊기거나 컨텍스트가 압축된 경우:

```bash
# 1. Claude Code 재시작
cd EnvironmentScan-system-main-v4
claude

# 2. Context Preservation 훅이 자동으로 복원 안내를 표시함
# "CONTEXT RESTORATION REQUIRED" 메시지 확인

# 3. 워크플로우 상태 확인
/env-scan:status

# 4. 상태에 따라 대응:
#    - "waiting_for_review" → 해당 체크포인트 커맨드 실행
#    - "in_progress" → 워크플로우 재실행
#    - "completed" → 이미 완료됨, 보고서 확인
```

이전 세션의 수집 데이터(`raw/`, `structured/`)는 파일로 저장되어 있으므로 유실되지 않는다.

---

# Part 9: 부록

## 부록 A: 커맨드 레퍼런스

### 슬래시 커맨드 (Claude Code 전용)

| 커맨드 | 설명 | 필수 시점 |
|--------|------|----------|
| `/env-scan:run` | 전체 스캔 (WF1+WF2+WF3+WF4+통합) | 시작 |
| `/env-scan:run --base-only` | WF1 Base 소스만 + WF2 + WF3 + WF4 + 통합 | 시작 |
| `/env-scan:run --multiglobal-news-only` | WF4 단독 (글로벌 뉴스만) | 시작 |
| `/env-scan:run-arxiv` | WF2 단독 (arXiv만) | 시작 |
| `/env-scan:run-naver` | WF3 단독 (네이버만) | 시작 |
| `/env-scan:run-multiglobal-news` | WF4 단독 (글로벌 뉴스만) | 시작 |
| `/env-scan:run-weekly` | 주간 메타분석 (새 스캔 없음, READ-ONLY) | 주 1회 |
| `/env-scan:status` | 현재 워크플로우 상태 확인 | 언제든 |
| `/env-scan:review-filter` | 중복 필터링 결과 검토 (Step 1.4) | 선택 |
| `/env-scan:review-analysis` | 분석 결과 검토 (Step 2.5) | **필수** |
| `/env-scan:approve` | 최종 보고서 승인 (Step 3.4) | **필수** |
| `/env-scan:revision "피드백"` | 보고서 수정 요청 | 필요 시 |

### CLI 스크립트 (터미널)

| 명령 | 설명 |
|------|------|
| `bash scripts/run_daily_scan.sh` | 스캔 + DB 업데이트 (축소판) |
| `python3 scripts/search_signals.py "키워드"` | 신호 검색 |
| `python3 scripts/search_signals.py --category T` | 카테고리별 검색 |
| `python3 scripts/search_signals.py --source arXiv` | 소스별 검색 |
| `python3 scripts/update_database.py <file>` | 수동 DB 업데이트 |
| `python3 scripts/validate_registry.py` | SOT 검증 (55개 규칙) |
| `python3 scripts/validate_report.py <file>` | 보고서 검증 (14개 규칙) |
| `python3 scripts/validate_state_consistency.py` | SCG 일관성 검증 |
| `bash scripts/setup_automation.sh` | cron 자동화 설정 |

## 부록 B: 파일 경로 참조표

### 설정 파일

| 파일 | 경로 | 설명 |
|------|------|------|
| SOT | `env-scanning/config/workflow-registry.yaml` | 시스템 단일 진실 소스 |
| WF1 소스 | `env-scanning/config/sources.yaml` | 일반 소스 (25+, arXiv 제외) |
| WF2 소스 | `env-scanning/config/sources-arxiv.yaml` | arXiv 전용 (42 카테고리) |
| WF3 소스 | `env-scanning/config/sources-naver.yaml` | 네이버 전용 (6 섹션) |
| WF4 소스 | `env-scanning/config/sources-multiglobal-news.yaml` | 글로벌 뉴스 (43 사이트, 11 언어) |
| 도메인 | `env-scanning/config/domains.yaml` | STEEPs 키워드 |
| 임계값 | `env-scanning/config/thresholds.yaml` | 필터링/스코어링 임계값 |
| 불변량 | `env-scanning/config/core-invariants.yaml` | 핵심 시스템 불변 규칙 |
| SIE | `env-scanning/config/self-improvement-config.yaml` | 자기개선엔진 설정 |
| 번역 | `env-scanning/config/translation-terms.yaml` | 영한 번역 용어집 |
| ML | `env-scanning/config/ml-models.yaml` | ML 모델 설정 |

### 데이터 디렉토리

| 경로 | 내용 |
|------|------|
| `env-scanning/wf1-general/raw/` | WF1 원시 스캔 데이터 (JSON) |
| `env-scanning/wf1-general/structured/` | WF1 분류된 신호 |
| `env-scanning/wf1-general/filtered/` | WF1 중복 제거 후 |
| `env-scanning/wf1-general/analysis/` | WF1 영향/우선순위 분석 |
| `env-scanning/wf1-general/signals/database.json` | WF1 신호 데이터베이스 |
| `env-scanning/wf1-general/signals/snapshots/` | WF1 DB 스냅샷 |
| `env-scanning/wf1-general/reports/daily/` | WF1 일일 보고서 |
| `env-scanning/wf1-general/reports/archive/` | WF1 아카이브 (연/월) |
| `env-scanning/wf1-general/logs/` | WF1 실행 로그 |
| `env-scanning/wf2-arxiv/` | WF2 (위와 동일 구조) |
| `env-scanning/wf3-naver/` | WF3 (위와 동일 구조) |
| `env-scanning/wf4-multiglobal-news/` | WF4 (위와 동일 구조 + 번역 로그) |
| `env-scanning/integrated/reports/daily/` | 통합 일일 보고서 |
| `env-scanning/integrated/reports/archive/` | 통합 아카이브 |
| `env-scanning/integrated/weekly/reports/` | 주간 보고서 |

### 보고서 스켈레톤

| 용도 | 경로 |
|------|------|
| WF1/WF2 보고서 | `.claude/skills/env-scanner/references/report-skeleton.md` |
| WF3 네이버 보고서 | `.claude/skills/env-scanner/references/naver-report-skeleton.md` |
| WF4 글로벌 뉴스 보고서 | `.claude/skills/env-scanner/references/multiglobal-news-report-skeleton.md` |
| 통합 보고서 | `.claude/skills/env-scanner/references/integrated-report-skeleton.md` |
| 주간 보고서 | `.claude/skills/env-scanner/references/weekly-report-skeleton.md` |
| 스타일 가이드 | `.claude/skills/env-scanner/references/final-report-style-guide.md` |
| STEEPs 정의 | `.claude/skills/env-scanner/references/steep-framework.md` |
| 신호 템플릿 | `.claude/skills/env-scanner/references/signal-template.md` |

## 부록 C: 설정 파일 스키마 참조

### workflow-registry.yaml 핵심 구조

```yaml
system:
  name: "Quadruple Environmental Scanning System"
  version: "2.5.0"
  execution:
    mode: "sequential"    # WF1 → WF2 → WF3 → WF4 → 통합
  master_orchestrator: ".claude/agents/master-orchestrator.md"
  protocol: ".claude/agents/protocols/orchestrator-protocol.md"
  checkpoints_total: 9

workflows:
  wf1-general:
    enabled: true
    execution_order: 1
    sources_config: "env-scanning/config/sources.yaml"
    excluded_sources: ["arXiv"]
    validate_profile: "standard"

  wf2-arxiv:
    enabled: true
    execution_order: 2
    sources_config: "env-scanning/config/sources-arxiv.yaml"
    exclusive_sources: ["arXiv"]
    validate_profile: "standard"
    parameters:
      days_back: 14
      max_results_per_category: 50

  wf3-naver:
    enabled: true
    execution_order: 3
    sources_config: "env-scanning/config/sources-naver.yaml"
    exclusive_sources: ["NaverNews"]
    validate_profile: "naver"
    parameters:
      fssf_classification: true
      three_horizons_tagging: true
      tipping_point_detection: true
      anomaly_detection: true

  wf4-multiglobal-news:
    enabled: true
    execution_order: 4
    sources_config: "env-scanning/config/sources-multiglobal-news.yaml"
    exclusive_sources: ["MultiGlobalNews"]
    validate_profile: "multiglobal-news"
    parameters:
      fssf_classification: true
      three_horizons_tagging: true
      tipping_point_detection: true
      languages: 11
      paywall_strategy: "total_war"

integration:
  enabled: true
  agent_teams: 5
  merge_strategy:
    signal_dedup: false
    ranking_method: "pSST_unified"
    integrated_top_signals: 20
    cross_workflow_analysis: true
  validate_profile: "integrated"

  weekly:
    enabled: true
    trigger:
      type: "manual"
      min_daily_scans: 5
      lookback_days: 7
    validate_profile: "weekly"
```

## 부록 D: 보고서 검증 규칙표 (14개)

| 규칙 | 검증 내용 | 실패 시 |
|------|----------|---------|
| FILE-001 | 파일 존재 | FAIL |
| FILE-002 | 파일 크기 1KB 이상 | FAIL |
| SEC-001 | 8개 섹션 헤더 존재 | FAIL |
| SIG-001 | 10개 이상 신호 블록 | FAIL |
| SIG-002 | 각 신호에 9개 필드 | FAIL |
| S3-001 | 3.1/3.2/3.3 서브섹션 | FAIL |
| S4-001 | 4.1/4.2 서브섹션, 1개 이상 테마 | FAIL |
| S4-002 | 교차영향 쌍 기호 | WARN |
| S5-001 | 5.1/5.2/5.3 서브섹션 | FAIL |
| S5-002 | 3개 이상 행동 항목 | WARN |
| S7-001 | pSST 신뢰도 분포표 | WARN |
| WC-001 | 2500단어 이상 | FAIL |
| KOR-001 | 한국어 100자 이상 | FAIL |
| SKEL-001 | `{{PLACEHOLDER}}` 미잔류 | FAIL |

## 부록 E: SOT 검증 규칙표 (55개, 주요 규칙)

| 규칙 | 검증 내용 | 심각도 |
|------|----------|--------|
| SOT-001 | 공유 불변 파일 존재 | HALT |
| SOT-002 | 오케스트레이터 파일 존재 | HALT |
| SOT-003 | 소스 설정 파일 존재 | HALT |
| SOT-004 | 공유 워커 파일 존재 | HALT |
| SOT-005 | 데이터 루트 디렉토리 존재 | CREATE |
| SOT-006 | 통합 출력 디렉토리 존재 | CREATE |
| SOT-007 | 실행 순서 고유 및 순차 | HALT |
| SOT-008 | 프로토콜 파일 존재 | HALT |
| SOT-009 | 통합 스켈레톤 존재 | HALT |
| SOT-010 | WF1에서 arXiv 비활성 | HALT |
| SOT-011 | WF2에서 arXiv 활성 | HALT |
| SOT-012 | 워크플로우 간 소스 중복 없음 | HALT |
| SOT-013 | 병합 에이전트 존재 | HALT |
| SOT-020 | WF3에서 NaverNews 활성 | HALT |
| SOT-021 | WF3 오케스트레이터 존재 | HALT |
| SOT-030 | WF4 오케스트레이터 존재 | HALT |
| SOT-031 | WF4 소스 설정 파일 존재 | HALT |
| SOT-032 | WF4 데이터 디렉토리 존재 | CREATE |
| SOT-033 | WF4 전용 워커 파일 존재 | HALT |
| SOT-034 | WF4에서 MultiGlobalNews 활성 | HALT |

(전체 55개 규칙은 `validate_registry.py` 소스 코드 참조)

## 부록 F: 문서 안내도

| 문서 | 내용 | 언제 읽나 |
|------|------|----------|
| **이 문서** (`USER-MANUAL.md`) | 일일 운영 절차, 커맨드 사용법, 설정 변경 | 운영 중 항상 |
| `AGENTICWORKFLOW-USER-MANUAL.md` | 영문 간결 운영 가이드 | 영어 환경에서 운영 시 |
| `WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | 전체 기술 명세 (VEV, pSST, SIE, 에이전트 상세) | 시스템 깊이 이해할 때 |
| `AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | 영문 간결 기술 명세 | 영어 환경에서 참조 시 |
| `decision-log.md` | WF4 구현 관련 아키텍처 결정 기록 | WF4 설계 근거 파악 시 |
| `CHANGELOG.md` | 버전별 변경 이력 | 업데이트 확인 시 |

### 디렉토리 맵

```
EnvironmentScan-system-main-v4/
├── USER-MANUAL.md                 ← 이 문서 (운영 가이드)
├── AGENTICWORKFLOW-USER-MANUAL.md ← 영문 운영 가이드
├── WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md  ← 기술 명세
├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md ← 영문 기술 명세
├── decision-log.md                ← WF4 아키텍처 결정 기록
│
├── .claude/                       ← Claude Code 설정
│   ├── agents/                      오케스트레이터 5 + 워커 36+
│   │   ├── master-orchestrator.md
│   │   ├── env-scan-orchestrator.md
│   │   ├── arxiv-scan-orchestrator.md
│   │   ├── naver-scan-orchestrator.md
│   │   ├── multiglobal-news-orchestrator.md
│   │   ├── workers/                 워커 에이전트 (36+)
│   │   └── protocols/               실행 프로토콜
│   ├── commands/env-scan/           슬래시 커맨드 (10개)
│   ├── skills/                      스킬 (6개)
│   │   ├── env-scanner/             환경 스캐닝 스킬 + 참조 문서
│   │   └── longform-journalism/     장편 저널리즘 변환
│   └── hooks/                       Context Preservation 훅
│
├── env-scanning/                  ← 메인 애플리케이션
│   ├── config/                      설정 파일 (11개 YAML)
│   ├── core/                        핵심 Python 모듈 (33개)
│   ├── scanners/                    소스 스캐너 (6개)
│   ├── scripts/                     운영 스크립트 (17개)
│   ├── wf1-general/                 WF1 데이터 (raw/structured/analysis/reports/signals)
│   ├── wf2-arxiv/                   WF2 데이터 (동일 구조)
│   ├── wf3-naver/                   WF3 데이터 (동일 구조)
│   ├── wf4-multiglobal-news/        WF4 데이터 (동일 구조 + 번역 로그)
│   └── integrated/                  통합 데이터 (reports/weekly/signals)
│
└── tests/                         ← 테스트 스위트
    ├── unit/                        단위 테스트
    ├── integration/                 통합 테스트
    └── e2e/                         종단간 테스트
```

---

**문서 버전**: 5.0
**최종 갱신**: 2026-02-24
**시스템 버전**: Quadruple Workflow System v2.5.0
**SOT 버전**: 2.5.0
