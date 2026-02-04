# Environmental Scanning System - 운영 가이드

**버전**: 3.0 (2026-01-31)
**대상**: 시스템 운영자 / 인수인계 대상

---

## 목차

1. [시스템 소개](#1-시스템-소개)
2. [빠른 시작](#2-빠른-시작)
3. [일일 운영 절차](#3-일일-운영-절차)
4. [마라톤 모드](#4-마라톤-모드)
5. [보고서 읽기 가이드](#5-보고서-읽기-가이드)
6. [신호 검색 및 활용](#6-신호-검색-및-활용)
7. [설정 변경](#7-설정-변경)
8. [자동화 설정](#8-자동화-설정)
9. [문제 해결](#9-문제-해결)
- [부록 A: 커맨드 레퍼런스](#부록-a-커맨드-레퍼런스)
- [부록 B: 문서 안내도](#부록-b-문서-안내도)

---

## 1. 시스템 소개

### 이 시스템은 무엇을 하는가

전 세계의 학술 논문, 특허, 정책 문서, 기술 블로그 등을 AI로 자동 스캔하여 **미래 변화의 초기 신호(weak signals)**를 탐지하고, 분류하고, 우선순위를 매기고, 보고서를 생성하는 시스템이다.

> **절대 목표**: 미래 트렌드, 중기 변화, 거시적 전환, 패러다임 변화, 임계 전환, 특이점, 돌발 사건, 예측 불가능한 미래의 초기 신호를 전 세계에서 가능한 한 빠르게 포착한다.

### STEEPs 분류 체계

모든 신호는 6개 카테고리로 분류된다 (변경 불가):

| 코드 | 카테고리 | 범위 |
|------|---------|------|
| **S** | Social (사회) | 인구, 교육, 노동, 문화 변화 |
| **T** | Technological (기술) | AI, 양자컴퓨팅, 바이오, 디지털 전환 |
| **E** | Economic (경제) | 시장, 금융, 무역, 플랫폼 경제 |
| **E** | Environmental (환경) | 기후, 지속가능성, 자원, 생물다양성 |
| **P** | Political (정치) | 정책, 법률, 규제, 지정학 |
| **s** | spiritual (영성) | 윤리, 심리, 가치관, 의미, AI 윤리 |

### 두 가지 사용 방식

| 방식 | 인터페이스 | 기능 범위 | 용도 |
|------|-----------|----------|------|
| **Claude Code (주)** | 슬래시 커맨드 | 3-Phase 전체 워크플로우 + 인간 검토 | 일일 정규 운영 |
| **CLI 스크립트 (보조)** | bash 터미널 | 스캔 + DB 업데이트만 | 빠른 데이터 수집 |

**중요**: 인간 검토 체크포인트, 영향 분석, 보고서 생성 등 시스템의 핵심 기능은 Claude Code를 통해서만 작동한다. CLI 스크립트는 데이터 수집 축소판이다.

### 시스템 구조 한눈에 보기

```
┌─ 오케스트레이터 (마스터 AI) ───────────────────────────────┐
│                                                           │
│  Phase 1: Research (정보 수집)                              │
│    소스 스캔 → 중복 제거 → [사용자 검토 선택]                    │
│                                                           │
│  Phase 2: Planning (분석)                                   │
│    분류 검증 → 영향 분석 → 우선순위 → [사용자 검토 필수]          │
│                                                           │
│  Phase 3: Implementation (보고서)                            │
│    DB 업데이트 → 보고서 생성 → 아카이브 → [사용자 승인 필수]       │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

18개의 전문 AI 워커 에이전트가 각 단계를 실행하며, 시스템은 매 단계마다 자동으로 품질을 검증한다 (VEV 프로토콜). 기술 상세는 [WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md](WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md)를 참조한다.

---

## 2. 빠른 시작

### 사전 요구사항

- Python 3.8 이상
- Claude Code CLI 설치
- 인터넷 연결

### 방법 A: Claude Code에서 실행 (권장)

```bash
# 1. 프로젝트 디렉토리에서 Claude Code 실행
cd EnvironmentScan-system-main
claude

# 2. 스캔 시작
/run-daily-scan

# 3. 이후 시스템이 안내하는 체크포인트를 따라간다
#    - Phase 2 완료 시: /review-analysis 로 분석 결과 검토
#    - Phase 3 완료 시: /approve 로 최종 보고서 승인
```

첫 실행 시 시스템이 자동으로:
- 설정 파일을 로드하고
- 활성화된 소스에서 신호를 수집하고
- 중복을 제거하고
- 각 체크포인트에서 사용자에게 검토를 요청한다

### 방법 B: 터미널에서 빠른 스캔 (보조)

3-Phase 워크플로우 없이 데이터 수집만 하려면:

```bash
cd env-scanning
bash scripts/run_daily_scan.sh
```

이 방법은 소스 스캔 + DB 업데이트만 수행한다. 분류, 영향 분석, 보고서 생성은 포함되지 않는다.

### 첫 실행 후 확인

```bash
# 데이터베이스 생성 확인
ls -la env-scanning/signals/database.json

# 보고서 생성 확인 (Claude Code로 실행한 경우)
ls -la env-scanning/reports/daily/

# 신호 검색 테스트
cd env-scanning
python3 scripts/search_signals.py "AI"
```

---

## 3. 일일 운영 절차

이 장은 Claude Code를 사용한 정규 운영 절차를 단계별로 설명한다.

### 3.1 스캔 실행

```bash
/run-daily-scan
```

시스템이 Phase 1을 시작한다:

1. **Step 1.1** - 기존 데이터베이스와 과거 보고서를 로드
2. **Step 1.2** - 활성화된 소스에서 신호 수집 (현재 6개 소스: arXiv, Google Patents, Federal Register, WHO, TechCrunch, MIT Tech Review)
3. **Step 1.3** - 4단계 중복 제거 (URL → 문자열 → 의미적 → 엔터티)
4. **Step 1.5** (조건부) - 수집된 신호가 50개를 초과하면 전문가 패널(Real-Time AI Delphi)이 자동 활성화된다. 해당되면 시스템이 안내한다

### 3.2 진행 확인

```bash
# 현재 워크플로우 상태 확인
/status

# 또는 Ctrl+T 로 실시간 태스크 진행률 확인
```

`/status`는 현재 Phase, Step, 수집된 신호 수, 소요 시간 등을 표시한다.

### 3.3 Phase 1 완료 후: 중복 필터링 검토 (선택)

Phase 1이 끝나면 시스템이 물어본다. 중복 제거 결과를 검토하려면:

```bash
/review-filter
```

**확인할 것**:
- 제거된 중복 신호 목록이 합리적인가
- 실제로 다른 신호가 잘못 제거되지 않았는가
- 중복 제거율이 극단적이지 않은가 (30~90% 범위가 정상)

검토 없이 넘어가도 된다. 이 체크포인트는 선택 사항이다.

### 3.4 Phase 2 완료 후: 분석 결과 검토 (필수)

이 체크포인트는 **반드시 거쳐야** 한다.

```bash
/review-analysis
```

**확인할 것**:

1. **STEEPs 분류가 맞는가**
   - 각 신호의 카테고리(S/T/E/E/P/s)가 내용과 일치하는지 훑어본다
   - 명백히 잘못된 분류가 있으면 수정을 지시한다

2. **우선순위가 합리적인가**
   - 상위 10개 신호가 실제로 중요한 신호인가
   - 중요한 신호가 하위로 밀려나지 않았는가

3. **영향 분석이 타당한가**
   - 교차 영향 관계가 논리적인가
   - 영향도 점수가 극단적이지 않은가

**진행 방식**: `/review-analysis`를 실행하면 시스템이 다음 질문을 순서대로 제시한다:

1. 분류 정확도가 수용 가능한가?
2. 우선순위를 조정할 신호가 있는가?
3. 추가 코멘트가 있는가?

각 질문에 응답하면 시스템이 자동으로 Phase 3으로 진행한다. 별도의 "승인" 명령은 필요 없다.

### 3.5 Phase 3 완료 후: 보고서 승인 (필수)

보고서가 생성되면 시스템이 **최종 승인**을 요청한다.

**보고서가 좋으면**:
```bash
/approve
```

**수정이 필요하면**:
```bash
/revision "Executive Summary를 좀 더 구체적으로, 상위 3개 신호의 전략적 시사점을 강화해주세요"
```

- 수정 요청 시 피드백을 따옴표 안에 작성한다
- 최대 **3회**까지 수정 가능
- 수정 후 다시 `/approve` 또는 `/revision`을 선택한다

### 3.6 워크플로우 완료 후

승인이 완료되면 시스템이 자동으로:
- 보고서를 `reports/archive/{year}/{month}/`에 아카이브
- 데이터베이스 스냅샷 생성 (`signals/snapshots/`)
- 품질 메트릭 생성 (`logs/quality-metrics/`)
- 자기개선 분석 실행 (임계값 미세 조정)

**확인할 파일**:

| 파일 | 위치 | 내용 |
|------|------|------|
| 영문 보고서 | `reports/daily/environmental-scan-{date}.md` | 원본 보고서 |
| 한국어 보고서 | `reports/daily/environmental-scan-{date}-ko.md` | 번역본 |
| 워크플로우 상태 | `logs/workflow-status.json` | 실행 결과 요약 |

### 전체 흐름 요약

```
/run-daily-scan
    │
    ▼
Phase 1: Research ─────────────────────────────
    1.1 아카이브 로드
    1.2 6개 소스 스캔 + 분류
    1.3 4단계 중복 제거
    1.4 [선택] /review-filter
    1.5 [조건부] 50+ 신호 시 전문가 패널
    │
    ▼
Phase 2: Planning ─────────────────────────────
    2.1 분류 품질 검증
    2.2 영향 분석 (Futures Wheel + 교차영향 매트릭스)
    2.3 우선순위 산출
    2.5 [필수] /review-analysis
    │
    ▼
Phase 3: Implementation ───────────────────────
    3.1 데이터베이스 업데이트 (자동 백업)
    3.2 보고서 생성 (EN + KR)
    3.3 아카이브 저장
    3.4 [필수] /approve 또는 /revision "피드백"
    │
    ▼
완료: 품질 메트릭 + 자기개선 분석
```

---

## 4. 마라톤 모드

### 마라톤 모드란

마라톤 모드는 **기본 스캔 모드**다. Base 소스 6개 + Expansion 소스 18개를 모두 스캔하여 최대 범위의 신호를 수집한다. Base 소스만 빠르게 스캔하려면 `--base-only` 플래그를 사용한다.

**`--base-only`는 언제 쓰는가**:
- 빠른 스캔이 필요할 때 (Expansion 소스 생략)
- 특정 Base 소스의 결과만 확인하고 싶을 때
- 네트워크 환경이 불안정할 때

### 실행

```bash
# 마라톤 모드가 기본이므로 별도 플래그 없이 실행
/run-daily-scan

# Base 소스만 스캔하려면:
/run-daily-scan --base-only
```

이후 절차는 동일하다 (체크포인트 3개소 포함).

### 소스 구성

**Base 소스** (항상 스캔, 6개 활성):

| 소스 | 유형 | 설명 |
|------|------|------|
| arXiv | 학술 | 오픈 학술 논문 |
| Google Patents | 특허 | 특허 문서 |
| US Federal Register | 정책 | 미국 연방 관보 |
| WHO Press Releases | 정책 | 세계보건기구 보도자료 |
| TechCrunch | 블로그 | 기술 뉴스 |
| MIT Technology Review | 블로그 | 기술 리뷰 |

**Expansion 소스** (기본 스캔, `--base-only` 시 생략, 18개):

| 카테고리 | 소스 |
|---------|------|
| 학술 | PubMed Central, Nature News, Science Magazine, IEEE Spectrum |
| 정책 | OECD Newsroom, World Bank Blogs, UN News, EUR-Lex |
| 싱크탱크 | Brookings Institution, World Economic Forum, Pew Research |
| 기술 | Hacker News, Wired, Ars Technica |
| 환경 | NASA Climate Change, Carbon Brief |
| 경제 | IMF Blog, BIS Speeches |

### 시간 제한

- 전체 Step 1.2 시간 상한: **30분**
- 이것은 상한선이다. 모든 소스 스캔이 끝나면 조기 종료한다
- 시간이 남아도 억지로 채우지 않는다

### 결과물 구분

Expansion 소스에서 온 신호에는 `source.tier: "expansion"` 태그가 붙는다. 보고서에서 Base 신호와 Expansion 신호를 구분할 수 있다.

---

## 5. 보고서 읽기 가이드

### 5.1 보고서 위치와 파일명

```
env-scanning/reports/
├── daily/
│   ├── environmental-scan-2026-01-30.md        ← 영문 원본
│   └── environmental-scan-2026-01-30-ko.md     ← 한국어 번역
└── archive/
    └── 2026/01/
        └── environmental-scan-2026-01-30.md    ← 아카이브 복사본
```

- **한국어 보고서** (`-ko.md`): 일상적인 검토 및 의사결정용
- **영문 보고서** (`.md`): 기술적 검증, 국제 공유, AI 처리용

### 5.2 보고서 7개 섹션

| 섹션 | 내용 | 주목할 것 |
|------|------|----------|
| **1. Executive Summary** | 핵심 발견 요약 (500단어 이하) | 가장 중요한 신호 1~3개, 전략적 시사점 |
| **2. New Signals Detected** | STEEPs별 신규 신호 목록 | 카테고리 분포, 신호 제목과 출처 |
| **3. Existing Signal Updates** | 기존 추적 신호의 상태 변화 | 상태 전환 (emerging → developing 등) |
| **4. Patterns and Connections** | 신호 간 교차 관계 | 여러 카테고리에 걸친 패턴 |
| **5. Strategic Implications** | 의사결정자를 위한 시사점 | 행동 가능한 인사이트 |
| **6. Scenarios** *(조건부)* | 복잡한 교차영향이 있을 때 자동 생성 | 시나리오별 핵심 동인과 경로 |
| **7. Appendix** | 전체 신호 목록, 소스, 참조 | 원본 데이터 확인용 |

> **참고**: 6번 Scenarios 섹션은 신호 간 복잡한 상호작용이 탐지될 때만 포함된다. 매번 생성되지 않으며, 없으면 5번 뒤에 바로 Appendix가 온다.

### 5.3 pSST 신뢰도 뱃지 읽기

각 신호에는 **pSST (predicted Signal Scanning Trust)** 점수가 붙는다. 이는 해당 신호를 얼마나 신뢰할 수 있는지를 나타낸다.

**등급과 의미**:

| 뱃지 | 등급 | 점수 | 의미 | 행동 |
|------|------|------|------|------|
| 🟢 | A (very high) | 90~100 | 매우 높은 신뢰도 | 자동 승인 수준 |
| 🔵 | B (confident) | 70~89 | 신뢰할 만함 | 표준 처리 |
| 🟡 | C (low) | 50~69 | 낮은 신뢰도 | 주의 깊게 검토 |
| 🔴 | D (very low) | 0~49 | 매우 낮은 신뢰도 | 반드시 인간 검토 |

**6개 차원** (각 차원이 pSST 점수에 기여한다):

| 차원 | 약어 | 측정 대상 | 예시 |
|------|------|----------|------|
| 소스 신뢰성 | SR | 출처의 권위 | 학술(85) > 특허(80) > 블로그(45) |
| 증거 강도 | ES | 정량적 데이터 보유 여부 | 수치 데이터 있으면 높음 |
| 분류 확신도 | CC | 카테고리 분류의 명확성 | 한 카테고리가 압도적이면 높음 |
| 시간 확신도 | TC | 발행일 신선도 | 7일 이내(100) → 90일+(30) |
| 독특성 확신도 | DC | 중복제거 통과 수준 | 4단계 모두 통과하면 100 |
| 영향 확신도 | IC | 영향 분석의 안정성 | 분석 결과가 일관적이면 높음 |

**보고서에서의 해석 예시**:

```
[T] 양자 컴퓨팅 오류 보정 돌파  pSST: 87 🔵 B
  SR: 85 (arXiv 학술) | TC: 100 (3일 전) | DC: 100 (고유) | ES: 70 | CC: 80 | IC: 75
```

→ "학술 출처에서 온 최근 고유 신호이며, 전체적으로 신뢰할 수 있다."

### 5.4 우선순위 점수 해석

각 신호의 우선순위는 4가지 요소의 가중 합이다:

| 요소 | 가중치 | 의미 |
|------|--------|------|
| Impact (영향도) | 40% | 이 신호가 실현되면 얼마나 큰 영향을 미치는가 |
| Probability (실현 가능성) | 30% | 이 신호가 실현될 가능성은 얼마인가 |
| Urgency (긴급성) | 20% | 얼마나 빠르게 대응해야 하는가 |
| Novelty (새로움) | 10% | 이 신호가 얼마나 새로운 정보인가 |

점수 범위: 0~10. 높을수록 높은 우선순위.

---

## 6. 신호 검색 및 활용

### 키워드 검색

```bash
cd env-scanning

# "AI" 관련 신호
python3 scripts/search_signals.py "AI"

# 더 많은 결과
python3 scripts/search_signals.py "climate" --limit 20
```

### 카테고리 필터

```bash
# 기술(T) 카테고리만
python3 scripts/search_signals.py --category T

# 정책(P) 카테고리만
python3 scripts/search_signals.py --category P
```

### 소스 필터

```bash
# arXiv 논문만
python3 scripts/search_signals.py --source arXiv

# TechCrunch 기사만
python3 scripts/search_signals.py --source TechCrunch
```

### 날짜 범위 검색

```bash
# 2026년 1월 신호
python3 scripts/search_signals.py --start-date 2026-01-01 --end-date 2026-01-31

# 최근 3일
python3 scripts/search_signals.py --start-date 2026-01-28
```

### 복합 검색

```bash
# "AI" + 기술 카테고리 + arXiv + 최대 10개
python3 scripts/search_signals.py "AI" --category T --source arXiv --limit 10
```

### 실전 예제

**AI 트렌드 파악**:
```bash
python3 scripts/search_signals.py "AI" --category T --limit 10
python3 scripts/search_signals.py "AI" --source arXiv
```

**정책 변화 모니터링**:
```bash
python3 scripts/search_signals.py --category P
python3 scripts/search_signals.py "regulation" --category P
```

**기후 신호 추적**:
```bash
python3 scripts/search_signals.py "climate" --category E
```

---

## 7. 설정 변경

모든 설정 파일은 `env-scanning/config/` 디렉토리에 있다.

### 7.1 소스 관리 (`config/sources.yaml`)

**소스 활성화/비활성화**:

```yaml
# 소스를 끄려면:
- name: "TechCrunch"
  enabled: false    # true → false로 변경

# 소스를 켜려면:
- name: "The Economist - Technology"
  enabled: true     # false → true로 변경
```

**주요 필드 설명**:

| 필드 | 의미 |
|------|------|
| `tier` | `base` (항상 스캔) 또는 `expansion` (기본 스캔, `--base-only` 시 생략) |
| `enabled` | `true`/`false` — 스캔 여부 |
| `critical` | `true`면 이 소스 실패 시 워크플로우 중단 |
| `max_results` | 한 번에 수집할 최대 항목 수 |
| `reliability` | `high`/`medium` — pSST SR 점수에 영향 |

**주의**: 새로운 소스를 추가하는 것은 시스템의 MAJOR 변경에 해당한다. 자기개선엔진(SIE)이 경고를 표시하며, 사용자 승인이 필요하다.

### 7.2 STEEPs 키워드 (`config/domains.yaml`)

각 카테고리의 검색 키워드를 수정할 수 있다:

```yaml
T_Technological:
  keywords:
    - "artificial intelligence"
    - "quantum computing"
    - "새로 추가할 키워드"    # ← 여기에 추가
  search_terms:
    - "AI breakthrough"
    - "새 검색어"             # ← 여기에 추가
```

**주의**: STEEPs 6개 카테고리 자체(S, T, E, E, P, s)는 불변이다. 카테고리 내의 키워드만 수정할 수 있다.

### 7.3 임계값 조정 (`config/thresholds.yaml`)

**중복제거 임계값** (높일수록 엄격):

| 단계 | 현재값 | 범위 | 의미 |
|------|--------|------|------|
| Stage 2 문자열 유사도 | 0.9 | 0.7~0.98 | 제목 기반 매칭 |
| Stage 3 의미적 유사도 | 0.8 | 0.6~0.95 | 의미 기반 매칭 |
| Stage 4 엔터티 매칭 | 0.85 | 0.7~0.98 | 고유명사 기반 매칭 |

**우선순위 가중치** (합계 반드시 1.0):

```yaml
priority_scoring:
  impact: 0.40       # 영향도
  probability: 0.30  # 실현 가능성
  urgency: 0.20      # 긴급성
  novelty: 0.10      # 새로움
```

이 값들은 자기개선엔진(SIE)이 주기당 매개변수별 **±0.05 절대값**씩 자동 조정할 수 있다 (예: 0.40 → 0.35~0.45). 대폭 변경은 사용자 승인이 필요하다.

### 7.4 번역 용어 (`config/translation-terms.yaml`)

기술 용어의 영한 매핑을 관리한다. 새로운 전문 용어가 잘못 번역되면 여기에 추가한다:

```yaml
# 추가 예시:
terms:
  "quantum computing": "양자 컴퓨팅"
  "새 영어 용어": "정확한 한국어 번역"
```

---

## 8. 자동화 설정

### cron 자동화 (CLI 스크립트용)

```bash
cd env-scanning
bash scripts/setup_automation.sh
```

대화형 메뉴에서 실행 시간을 선택한다:
1. 9:00 AM (권장)
2. 12:00 PM
3. 6:00 PM
4. Custom time

**해제**:
```bash
bash scripts/setup_automation.sh
# → "Disable automation" 선택
```

**주의**: cron 자동화는 CLI 스크립트(스캔 + DB 업데이트)만 실행한다. 3-Phase 전체 워크플로우는 Claude Code에서 수동으로 실행해야 한다.

### 자기개선엔진 (SIE)

시스템은 매 워크플로우 완료 후(Step 3.6) 자동으로 성능을 분석하고 매개변수를 미세 조정한다.

**자동 적용 (MINOR)**: 중복제거 임계값 ±5%, 타임아웃 조정 등 — 주기당 최대 3개
**사용자 승인 필요 (MAJOR)**: 소스 추가/제거, 보고서 구조 변경 등
**절대 변경 불가 (CRITICAL)**: 3-Phase 구조, STEEPs 카테고리, 인간 체크포인트 등

자기개선의 상세 메커니즘은 [WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md](WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) 제8장을 참조한다.

### 로그 확인

| 로그 | 위치 | 내용 |
|------|------|------|
| 워크플로우 상태 | `logs/workflow-status.json` | 현재/최근 워크플로우 진행 상태 |
| 품질 메트릭 | `logs/quality-metrics/workflow-{date}.json` | 정확도, 실행 시간 등 |
| 검증 보고서 | `logs/verification-report-{date}.json` | 각 단계별 검증 결과 |
| 벤치마크 | `logs/benchmark-results.json` | 성능 벤치마크 |

---

## 9. 문제 해결

### 9.1 일반 문제

**Q: "Database not found" 에러**
```bash
# raw 데이터로 데이터베이스 생성
python3 scripts/update_database.py raw/daily-scan-YYYY-MM-DD.json
```

**Q: 검색 결과가 너무 많음**
```bash
# 필터 추가
python3 scripts/search_signals.py "keyword" --category T --limit 5
```

**Q: 신호가 수집되지 않음**
```bash
# 1. 인터넷 연결 확인
ping google.com

# 2. 소스별 활성 상태 확인
# config/sources.yaml에서 enabled: true인 소스 확인
```

**Q: 비용이 드나요?**

모든 Base 소스는 무료(API 키 불필요)이다. 일부 비활성 소스(Google Scholar 등)는 별도 API 키가 필요하다.

### 9.2 워크플로우 중단 시

**Case A: 워크플로우가 체크포인트에서 멈춘 경우**

```bash
# 1. 현재 상태 확인
/status

# 2. 마지막 체크포인트부터 재개
#    시스템이 안내하는 다음 행동을 따른다
```

워크플로우 상태는 `logs/workflow-status.json`에 기록되어 있다. `current_step`과 `blocked_on` 필드를 확인한다.

**Case B: Claude Code 세션 자체가 끊긴 경우**

Claude Code를 종료했거나 세션이 만료된 경우:

```bash
# 1. Claude Code 다시 시작
cd EnvironmentScan-system-main
claude

# 2. 마지막 워크플로우 상태 확인
/status

# 3. 상태에 따라 대응:
#    - "waiting_for_review" → 해당 체크포인트 커맨드 실행 (/review-analysis 등)
#    - "in_progress" → 워크플로우를 처음부터 재실행 (/run-daily-scan)
#    - "completed" → 이미 완료됨, 보고서 확인
```

이전 세션의 수집 데이터(`raw/`, `structured/`)는 파일로 저장되어 있으므로 유실되지 않는다. 다만 Phase 도중에 세션이 끊기면 해당 Phase는 처음부터 재실행된다.

### 9.3 데이터베이스 복원

데이터베이스에 문제가 생기면 스냅샷에서 복원한다:

```bash
# 사용 가능한 스냅샷 확인
ls env-scanning/signals/snapshots/

# 최근 스냅샷으로 복원
cp env-scanning/signals/snapshots/database-2026-01-30.json \
   env-scanning/signals/database.json
```

데이터베이스 업데이트(Step 3.1)는 항상 자동으로 스냅샷을 먼저 생성한 후 원자적으로 업데이트한다. 실패 시 자동으로 이전 상태로 복원된다.

### 9.4 번역 품질 문제

한국어 번역이 부자연스럽거나 용어가 잘못 번역되면:

1. `config/translation-terms.yaml`에 정확한 번역 매핑 추가
2. 다음 스캔 시 적용됨
3. 번역 실패는 워크플로우를 중단시키지 않는다 (영문 보고서가 항상 존재)

### 9.5 검증 실패 시

시스템은 매 단계마다 자동으로 품질을 검증한다 (VEV 프로토콜):
- **구조적 검증 실패** (파일 없음 등): 자동 재시도 (최대 2회)
- **기능적 검증 실패** (데이터 오류): 실패 항목만 재실행
- **품질 검증 경고**: 경고 로그 후 다음 체크포인트에서 사용자 확인

2회 재시도 후에도 실패하면 워크플로우가 일시정지된다. `/status`로 상태를 확인하고, 문제를 해결한 뒤 재실행한다.

---

## 부록 A: 커맨드 레퍼런스

### 슬래시 커맨드 (Claude Code 전용)

| 커맨드 | 설명 | 필수 시점 |
|--------|------|----------|
| `/run-daily-scan` | 마라톤 모드 (기본, Base + Expansion 소스) | 시작 |
| `/run-daily-scan --base-only` | Base 소스만 스캔 (Expansion 생략) | 시작 |
| `/status` | 현재 워크플로우 진행 상태 확인 | 언제든 |
| `/review-filter` | 중복 필터링 결과 검토 (Step 1.4) | 선택 |
| `/review-analysis` | 분석 결과 검토 (Step 2.5) | **필수** |
| `/approve` | 최종 보고서 승인 (Step 3.4) | **필수** |
| `/revision "피드백"` | 보고서 수정 요청 (최대 3회) | 필요 시 |

### CLI 스크립트 (터미널)

| 명령 | 설명 |
|------|------|
| `bash scripts/run_daily_scan.sh` | 스캔 + DB 업데이트 (축소판) |
| `python3 scripts/search_signals.py` | 신호 검색 |
| `python3 scripts/run_multi_source_scan.py` | 소스 스캔만 실행 |
| `python3 scripts/update_database.py <file>` | 수동 DB 업데이트 |
| `bash scripts/setup_automation.sh` | cron 자동화 설정 |

---

## 부록 B: 문서 안내도

이 프로젝트에는 여러 문서가 있다. 목적별로 정리하면:

| 문서 | 내용 | 언제 읽나 |
|------|------|----------|
| **이 문서** (`USER_GUIDE.md`) | 일일 운영 절차, 커맨드 사용법, 설정 변경 | 운영 중 항상 |
| `README.md` | 시스템 개요, 설치 안내, 아키텍처 요약 | 처음 한 번 |
| `WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md` | 전체 기술 명세 (VEV, pSST, SIE, 에이전트 상세) | 시스템 깊이 이해할 때 |
| `CHANGELOG.md` | 버전별 변경 이력 | 업데이트 확인 시 |
| `env-scanning/config/*.yaml` | 소스, 키워드, 임계값 등 설정 | 설정 변경 시 |
| `docs/cc/` | Claude Code 훅, 슬래시 커맨드, 서브에이전트 참고 | 시스템 확장 시 |

### 디렉토리 맵

```
EnvironmentScan-system-main/
├── USER_GUIDE.md              ← 이 문서 (운영 가이드)
├── README.md                  ← 시스템 개요
├── WORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md  ← 기술 명세
│
├── .claude/                   ← Claude Code 설정
│   ├── agents/                  에이전트 정의 (1 오케스트레이터 + 18 워커)
│   ├── commands/env-scan/       슬래시 커맨드 (6개)
│   └── skills/                  스킬 (6개)
│
├── env-scanning/              ← 메인 애플리케이션
│   ├── config/                  설정 파일 (7개 yaml)
│   ├── raw/                     원본 스캔 데이터
│   ├── structured/              분류된 신호
│   ├── filtered/                중복 제거 후 데이터
│   ├── analysis/                영향 분석, 우선순위 결과
│   ├── reports/daily/           일일 보고서 (EN + KR)
│   ├── reports/archive/         아카이브 (연/월별)
│   ├── signals/                 신호 데이터베이스 + 스냅샷
│   ├── logs/                    워크플로우 로그, 품질 메트릭
│   └── scripts/                 CLI 스크립트
│
└── tests/                     ← 테스트 스위트
```

---

**문서 버전**: 3.1
**최종 갱신**: 2026-02-01
**시스템 버전**: 2.1.0 (Bilingual EN-KR + Marathon Default)
**오케스트레이터**: v3.1.0 (VEV + SIE + Marathon Default)
