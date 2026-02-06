# STEEPS Environmental Scanning Workflow v3.0

네이버 뉴스 전체 크롤링 기반 STEEPS 환경스캐닝 시스템.
The Millennium Project 방법론 + FSSF(Futures Signals Sense-Making Framework) 통합.

> **절대 목표**: 미래의 트렌드, 중기 변화, 거시 변화, 패러다임 대전환, 변화의 임계점 통과, 싱귤래리티, 급변사태, 뜻밖의 미래 등이 만들어내는 사전 신호를 한국, 아시아, 유럽, 아프리카, 아메리카 대륙 등 전 세계에서 **'가장 빨리' catchup** 하는 것.

> **시스템 범위**: 이 워크플로우는 **네이버 뉴스 크롤링**만을 환경스캐닝 대상으로 한다. 다른 데이터 소스(글로벌 뉴스, 학술DB, 특허, 소셜미디어 등)는 별도 시스템으로 구축한다.

> **시스템 경계**: 이 워크플로우는 **순수 환경스캐닝(수집→전처리→분류→탐지→평가→출력→학습)**만 수행한다. 환경분석(Futures Wheel, Cross-Impact 등), 전략 수립, 보고서 생성, 지식관리(CI DB)는 별도 후속 시스템에서 처리한다.

## Overview

- **Input**: 네이버 뉴스 전체 섹션 (정치/경제/사회/생활문화/IT과학/세계)
- **Output**: 구조화된 스캐닝 데이터 JSON (후속 시스템 연계용)
- **Frequency**: Daily (긴급 신호 발견 시 실시간 Alert)
- **Critical**: 크롤링 차단 실시간 탐지 및 자동 우회 (최우선 과제)
- **Core Principle**: Feedback Loop 기반 분류 모델 재학습 시스템

---

## STEEPS Framework

| Code | Domain | 한글명 | 스캐닝 대상 |
|------|--------|-------|------------|
| S | Social | 사회 | 인구구조, 라이프스타일, 교육, 건강, 가족, 세대, 이민, 도시화 |
| T | Technological | 기술 | AI, 바이오, 에너지, 통신, 신소재, 우주, 로봇, 양자, 나노 |
| E | Economic | 경제 | 산업, 금융, 무역, 고용, 부동산, 소비, 투자, 암호화폐 |
| E | Environmental | 환경 | 기후, 자원, 오염, 생태계, 재난, 탄소중립, 생물다양성 |
| P | Political | 정치 | 정책, 규제, 국제관계, 거버넌스, 법률, 안보, 선거, 갈등 |
| S | Spiritual | 영성/심리 | 종교, 대중심리, 가치관, 윤리, 집단심리, 사회불안, 세대갈등 |

---

## FSSF Signal Taxonomy (Kuosa, 2010)

환경스캐닝에서 포착하는 모든 정보는 다음 **8가지 신호 유형**으로 분류한다.
Weak Signal과 Precursor Event만이 아니라, 완전한 신호 분류 체계를 적용한다.

| 유형 | 정의 | 탐지 기준 | 절대 목표 관련성 |
|------|------|----------|----------------|
| **Weak Signal** | 변화의 최초 불완전한 지표. 소수 소스, 모호, 단편적 | 출현 빈도 낮음 + 기존 패러다임과 불일치 | **CRITICAL** - 가장 빨리 포착해야 할 핵심 대상 |
| **Emerging Issue** | 형성 초기 단계의 이슈. 아직 주류 담론 아님 | 관련 기사 2-5건/주 수준, 전문 매체에서 시작 | **HIGH** - Weak Signal의 다음 단계 |
| **Trend** | 과거 데이터로 확인 가능한 방향성 | 지속적 증가/감소 패턴, 다수 매체 보도 | MEDIUM |
| **Megatrend** | 장기 거시 변환 과정 (10년+) | 다수 STEEPS 영역에 걸친 복합 패턴 | MEDIUM - 배경 맥락으로 활용 |
| **Driver** | 변화를 추동하는 근본 동인 | 다수 트렌드의 공통 원인으로 식별 | HIGH - 구조적 변화 신호 |
| **Wild Card** | 저확률-고영향 돌발 이벤트 (Known Unknown) | 선례 희소, 발생 시 급격한 변화 예상 | **CRITICAL** - 급변사태/뜻밖의 미래 |
| **Discontinuity** | 연속성 단절, 예측 가능하나 영향 극대 | 기존 트렌드의 급격한 방향 전환 징후 | **CRITICAL** - 패러다임 대전환 |
| **Precursor Event** | 더 큰 변화를 예고하는 선행 사건 | 이전 유사 패턴 존재, 후속 변화 역사적 선례 | HIGH |

### 신호 성숙도 생명주기

```
Noise ──→ Weak Signal ──→ Emerging Issue ──→ Trend ──→ Megatrend
                │                                         │
                ├──→ Wild Card (돌발 전환)                  │
                │                                         │
                └──→ Discontinuity (연속성 단절) ──────────┘
                     ↑
              Precursor Event (선행 징후)
```

이 생명주기를 추적하여 **신호의 성장/소멸/전환을 모니터링**한다.

---

## Three Horizons Time Classification

스캐닝된 모든 신호에 시간 지평 태그를 부여한다.

| Horizon | 시간 범위 | 특성 | 스캐닝 우선순위 |
|---------|----------|------|--------------|
| **H1** | 0-2년 | 현재 시스템의 점진적 변화. 주류 뉴스 대부분 | LOW (이미 알려진 것) |
| **H2** | 2-7년 | 전환기 혁신과 실험. 니치에서 성장 중 | HIGH |
| **H3** | 7년+ | 패러다임 전환의 씨앗. 극소수만 인지 | **CRITICAL** |

> **절대 목표 연계**: 제1 목적은 **H3 수준의 신호를 H1 시점에서 포착**하는 것이다. 따라서 스캐닝 시 H3 태그 후보를 최우선으로 식별한다.

---

## Scanning Pipeline (7 Phase)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SCANNING PIPELINE v3.0                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: COLLECTION (수집)                                         │
│  [1] 크롤링 전략 수립 → [2] 뉴스 크롤링 ←─ [3] 차단 대응             │
│       ↓                                                             │
│  Phase 2: PREPROCESSING (전처리)                                     │
│  [4] 중복 제거 + Noise 필터링 → [5] (human) 수집 확인                 │
│       ↓                                                             │
│  Phase 3: CLASSIFICATION (분류)                                      │
│  [6] FSSF 신호 유형 분류 → [7] STEEPS 도메인 분류                    │
│       ↓                                                             │
│  [8] 환경스캐닝 템플릿 적용 (13필드 + H1/H2/H3 태깅)                 │
│       ↓                                                             │
│  Phase 4: DETECTION (탐지)                                           │
│  [9] Pattern Analysis + Precursor Detection                         │
│  [10] Tipping Point 접근 신호 탐지                                   │
│  [11] Anomaly Detection (이상치 탐지)                                │
│       ↓                                                             │
│  Phase 5: ASSESSMENT (평가)                                          │
│  [12] 핵심 행위자 식별                                               │
│  [13] 간이 우선순위 태깅 + Source Credibility Score                   │
│  [14] (human) 스캐닝 결과 검토 & 피드백                               │
│       ↓                                                             │
│  Phase 6: OUTPUT (출력)                                              │
│  [15] 구조화된 스캐닝 데이터 출력 (후속 시스템 연계용)                  │
│  [16] 실시간 Alert 발송 (긴급 신호)                                   │
│       ↓                                                             │
│  Phase 7: LEARNING (학습)                                            │
│  [17] 피드백 학습 & 분류 모델 재학습                                   │
│       ↓                                                             │
│  ════════════════════════════════════════════════════════════════    │
│       ↓ 학습 내용 자동 반영                                          │
│   [다음 스캐닝 사이클 Step 1]                                        │
│                                                                     │
│  ──→ 후속 시스템 연계 ──→                                            │
│       • 환경분석 시스템 (Futures Wheel, Cross-Impact, CLA)            │
│       • 보고서 시스템 (Report Generation)                             │
│       • 지식관리 시스템 (Collective Intelligence DB)                   │
│       • 전략 시스템 (Scenario, Backcasting)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: COLLECTION (수집)

### 1. 크롤링 전략 수립
- **Agent**: `@crawl-defender`
- **Task**:
  - 현재 IP/네트워크 환경 점검
  - 이전 차단 이력 분석 및 **학습된 성공 패턴 로드**
  - 네이버 현재 방어 패턴 탐지
  - 프록시 풀/User-Agent 풀 준비
  - 최적 크롤링 전략 결정
- **Output**: `crawl-strategy.json`
- **Skills**: `[anti-block-crawler]`

### 2. 네이버 뉴스 전체 크롤링
- **Agent**: `@news-crawler`
- **Task**:
  - 6개 섹션 순회 크롤링
    - 정치(100), 경제(101), 사회(102)
    - 생활문화(103), 세계(104), IT과학(105)
  - 기사 메타데이터 수집 (제목, URL, 언론사, 시간, 기자명)
  - 기사 본문 전체 수집
  - 실시간 차단 모니터링 (403/429/Captcha/빈응답)
- **Output**: `raw-news.json`
- **Skills**: `[anti-block-crawler]`
- **On-Block**: 즉시 Step 3 실행

### 3. 차단 대응 (조건부)
- **Agent**: `@crawl-defender`
- **Trigger**: 차단 탐지 시 자동 실행
- **Task**:
  - 차단 유형 즉시 분석
  - 우회 전략 실시간 생성
  - Python 코드 동적 생성/실행
  - 성공까지 전략 변경 반복
  - **성공 패턴 학습 DB 저장**
- **Output**: `defense-log.json`, `learned-crawl-patterns.json`
- **Skills**: `[anti-block-crawler]`
- **Priority**: CRITICAL - 반드시 성공

---

## Phase 2: PREPROCESSING (전처리)

### 4. 중복 제거 + Noise 필터링
- **Agent**: `@dedup-filter`
- **Task**:
  - **중복 제거**:
    - 제목 유사도 분석 (Jaccard >= 0.7)
    - 본문 SimHash 비교
    - 동일 사건 클러스터링
    - 대표 기사 선정 (가장 상세한 버전)
  - **Noise 필터링**:
    - 광고성/홍보성 기사 제거 (code-level 키워드 필터)
    - 단신/속보 중 정보량 부족 기사 마킹
    - 연예/스포츠 결과 등 스캐닝 무관 기사 제거
  - **Source Credibility 기초 데이터**:
    - 언론사별 보도 경향 패턴 기록
    - 언론사별 기사 품질 메타데이터 수집
  - **Signal-to-Noise Ratio 산출**:
    - 전체 수집 대비 유효 기사 비율 기록
    - 섹션별 S/N 비율 추적
- **Output**: `unique-news.json`, `media-patterns.json`, `snr-metrics.json`

### 5. (human) 수집 결과 확인
- **Action**: 수집 통계, 차단 대응 결과, S/N 비율 확인
- **Command**: `/check-crawl`
- **Feedback**: 크롤링 품질 평가, 필터링 기준 조정 입력 가능

---

## Phase 3: CLASSIFICATION (분류)

### 6. FSSF 신호 유형 분류
- **Agent**: `@signal-classifier`
- **Task**:
  - 각 기사를 **FSSF 8가지 신호 유형**으로 분류:
    ```
    1. Weak Signal (약한 신호)
    2. Emerging Issue (신생 이슈)
    3. Trend (트렌드)
    4. Megatrend (메가트렌드)
    5. Driver (변화 동인)
    6. Wild Card (돌발 이벤트)
    7. Discontinuity (연속성 단절)
    8. Precursor Event (선행 사건)
    ```
  - **분류 기준** (code-level 전처리 후 AI 판단):
    - 출현 빈도 (Python: 최근 7/30/90일 키워드 빈도 계산)
    - 기존 패턴과의 일치/불일치 정도
    - 복수 신호 유형 태깅 가능 (최대 2개)
  - 분류 신뢰도 점수 부여 (0.0-1.0)
  - **학습된 분류 모델 적용** (이전 피드백 반영)
- **Output**: `signal-typed-news.json`
- **Model**: `signal-classifier-model-current.json`

### 7. STEEPS 도메인 분류
- **Agent**: `@signal-classifier`
- **Task**:
  - 각 기사 STEEPS 6영역 분류
  - 복합 영역 다중 태깅 (최대 3개)
  - 분류 신뢰도 점수 부여 (0.0-1.0)
  - **학습된 분류 모델 적용** (이전 피드백 반영)
- **Output**: `classified-news.json`
- **Model**: `steeps-classifier-model-current.json`
- **Note**: Step 6의 신호 유형 분류와 병렬 실행 가능

### 8. 환경스캐닝 템플릿 적용
- **Agent**: `@issue-scanner`
- **Task**:
  - **Kuwait Oil + UNDP 통합 13필드 + 확장 3필드 템플릿**:
    ```
    === 원본 13필드 ===
    1. Item: 트렌드/이벤트/이슈 식별
    2. Description: 상세 설명
    3. Significance: 미래 관점 의의
    4. Importance: H/M/L (High/Medium/Low)
    5. Consequences: 잠재적 영향/파급효과
    6. Current Status: 현재 발전 단계
    7. Future Status: 향후 예정 이벤트/일정
    8. Actors: 관련 행위자 (글로벌 범위)
    9. Leading Indicators: 선행 지표
    10. Classification: STEEPS 영역
    11. Source: 출처 URL
    12. Date: 스캔 일자
    13. Scanner: AI Environmental Scanner v3.0

    === 확장 3필드 (v3.0 추가) ===
    14. Signal Type: FSSF 신호 유형 (Step 6 결과)
    15. Time Horizon: H1/H2/H3 (Three Horizons 분류)
    16. Uncertainty Level: 불확실성 수준 (Low/Medium/High/Radical)
    ```
  - **Three Horizons 태깅 기준**:
    - H1 (0-2년): 현재 정책/법안, 당장의 시장 변화, 진행 중인 사건
    - H2 (2-7년): 실험적 기술/정책, 니치 시장 성장, 규제 논의 초기
    - H3 (7년+): 근본적 가치관 전환, 기술 패러다임 변화의 씨앗, 문명 수준 변화
  - **불확실성 수준 기준**:
    - Low: 명확한 데이터, 높은 예측 가능성
    - Medium: 일부 불확실, 복수 시나리오 가능
    - High: 매우 불확실, 방향성 미정
    - Radical: 존재론적 불확실성 (무엇이 일어날지 자체가 불명)
- **Output**: `scanned-issues.json`

---

## Phase 4: DETECTION (탐지)

### 9. Pattern Analysis & Precursor Detection
- **Agent**: `@pattern-detector`
- **Task**:
  - 시계열 이슈 패턴 분석 (**다중 시계열**: 7일/30일/90일)
  - 반복 출현 키워드/주제 탐지
  - 이슈 간 상관관계 발견
  - **Precursor Events 후보 식별**:
    - 역사적 유사 패턴 매칭
    - "이전에 X가 발생한 후 Y가 뒤따랐다" 패턴 DB 참조
  - 트렌드 가속/감속 패턴 분석
  - **Weak Signal → Strong Signal 전환 모니터링**:
    - 신호 성숙도 생명주기 추적
    - 빈도 증가율, 매체 확산 속도, 영역 교차 여부
- **Output**: `pattern-analysis.json`, `precursor-candidates.json`

### 10. Tipping Point 접근 신호 탐지
- **Agent**: `@pattern-detector`
- **Task**:
  - **Critical Slowing Down 지표 모니터링**:
    - 특정 이슈 관련 뉴스 빈도의 분산(variance) 증가 추적
    - 자기상관(autocorrelation) 계수 변화 추적 (lag-1)
    - 급격한 빈도 변화(지수적 증가/감소) 패턴 감지
  - **Flickering 탐지**:
    - 동일 이슈에 대한 상반된 보도의 불규칙적 교차 빈도
    - 긍정/부정 논조의 급변 패턴
  - **Discontinuity 선행 지표**:
    - 기존 Megatrend 내 이탈 기사 빈도 증가
    - "역사적 최초", "전례 없는", "예상 밖" 등 키워드 급증 (code-level 전처리)
  - **임계점 접근 경보 레벨**:
    ```
    GREEN: 정상 패턴
    YELLOW: 분산/자기상관 상승 추세 (관찰 강화)
    ORANGE: 명확한 Critical Slowing Down 징후 (인간 검토 요청)
    RED: 임계점 통과 임박 또는 통과 (즉시 Alert 발송)
    ```
- **Output**: `tipping-point-indicators.json`
- **Alert**: RED 레벨 시 Step 16 즉시 트리거

### 11. Anomaly Detection (이상치 탐지)
- **Agent**: `@pattern-detector`
- **Task**:
  - **통계적 이상치 탐지** (code-level Python 전처리):
    - 섹션별 일일 기사 수 이상 (평균 ± 2σ 이탈)
    - 특정 키워드 빈도 급변 (z-score > 3)
    - 새로운 키워드 클러스터 출현 (이전 30일 미등장)
  - **구조적 이상치 탐지**:
    - 통상적으로 연결되지 않는 STEEPS 영역 간 기사 교차 증가
    - 특정 언론사만 보도하는 이슈 (단독 보도 감시)
    - 해외 세계 섹션에서만 출현하는 비정상 패턴
  - **이상치 분류**:
    - Noise: 데이터 오류 또는 일시적 변동
    - Signal: 의미있는 변화의 초기 징후
    - Wild Card Candidate: 돌발 이벤트 후보
- **Output**: `anomaly-detection.json`

---

## Phase 5: ASSESSMENT (평가)

### 12. 핵심 행위자 식별
- **Agent**: `@actor-identifier`
- **Task**:
  - **기사 내 핵심 인물/기관 추출** (NER 기반):
    - 국내: 정치인, 기업인, 학자, 종교지도자
    - 해외: 국가원수, 글로벌 CEO, 국제기구 수장
  - **기관/조직 추출**:
    - 국내: 정부부처, 대기업, 주요 단체
    - 해외: UN, WEF, IMF, WHO, 주요국 정부, 글로벌 기업
  - **행위자별 관련 이슈 태깅** (이 이슈에 누가 관련되는가)
  - **Leading Indicator 행위자 식별**: 특정 행위자의 발언/행동이 후속 변화를 예고한 패턴
  - **범위**: 식별(identification)까지만. 네트워크 매핑/추적 분석은 후속 시스템에서 수행
- **Output**: `identified-actors.json`

### 13. 간이 우선순위 태깅 + Source Credibility Score
- **Agent**: `@issue-scanner`
- **Task**:
  - **긴급도 3단계 태깅**:
    ```
    URGENT: 즉시 인간 검토 필요 (Wild Card, RED Tipping Point, H3+Weak Signal)
    WATCH: 지속 모니터링 필요 (Emerging Issue, ORANGE Tipping Point, H2)
    ARCHIVE: 기록용 (Trend, H1, 일반 뉴스)
    ```
  - **Source Credibility Score 부여**:
    - 언론사 신뢰도 (code-level: 과거 정확도 데이터 기반)
    - 기사 깊이 (본문 길이, 인용 수, 전문가 의견 포함 여부)
    - 독립 확인 가능성 (다른 언론사 보도 여부)
    - 점수: 0.0-1.0
  - **False Positive 추적 메타데이터**:
    - 이전 사이클 대비 신호 유형 변경 이력
    - 인간 피드백에서 오탐 판정된 유사 패턴 참조
- **Output**: `prioritized-scan.json`, `credibility-scores.json`

### 14. (human) 스캐닝 결과 검토 & 피드백
- **Action**:
  - FSSF 신호 유형 분류 검토 및 **수정**
  - STEEPS 분류 검토 및 **수정**
  - Three Horizons 태깅 검토
  - 우선순위 태깅 검토
  - **오분류 케이스 명시적 피드백**
  - **놓친 신호(False Negative) 지적**
  - **잘못된 경보(False Positive) 지적**
- **Command**: `/review-scan`
- **Feedback Output**: `human-feedback-{date}.json`
- **Critical**: 이 피드백은 Step 17에서 모델 재학습에 사용됨

---

## Phase 6: OUTPUT (출력)

### 15. 구조화된 스캐닝 데이터 출력
- **Agent**: `@scan-outputter`
- **Task**:
  - **통합 스캐닝 결과 JSON 생성**:
    - 모든 식별된 이슈 (16필드 템플릿 데이터 포함)
    - FSSF 신호 유형 + STEEPS 분류 + Three Horizons 태깅
    - 패턴 분석 결과
    - Tipping Point 지표
    - 이상치 탐지 결과
    - 핵심 행위자 목록
    - 우선순위 태그 + Credibility Score
    - 인간 피드백 반영 결과
  - **후속 시스템 연계 인터페이스**:
    - `scan-output-{date}.json` → 환경분석 시스템 input
    - `actors-{date}.json` → 행위자분석 시스템 input
    - `urgent-signals-{date}.json` → 전략 시스템 input
  - **일일 스캐닝 요약 통계**:
    - 총 수집/유효/분류 기사 수
    - 신호 유형별 분포
    - STEEPS 영역별 분포
    - Three Horizons 분포
    - S/N Ratio
    - Tipping Point 경보 현황
- **Output**: `scan-output-{date}.json`, `scan-summary-{date}.json`

### 16. 실시간 Alert 발송 (긴급 신호)
- **Agent**: `@alert-dispatcher`
- **Trigger**: 다음 조건 중 하나 충족 시 자동 실행
  ```
  조건 1: Tipping Point 경보 RED 레벨
  조건 2: Wild Card 유형 + Importance H 분류
  조건 3: Discontinuity 유형 + 신뢰도 >= 0.7
  조건 4: H3 + Weak Signal + 복수 STEEPS 영역 교차
  조건 5: Anomaly Detection에서 Wild Card Candidate 식별
  ```
- **Task**:
  - 긴급 신호 요약 메시지 생성
  - 관련 원본 기사 URL 첨부
  - 신호 유형, 시간 지평, 불확실성 레벨 포함
  - **Alert 이력 기록** (오알람 추적용)
- **Output**: `alert-log-{date}.json`
- **Channel**: console 출력 (추후 Slack/Telegram 연동 가능)

---

## Phase 7: LEARNING (학습)

### 17. 피드백 학습 & 분류 모델 재학습
- **Agent**: `@learning-engine`
- **Trigger**: 일일 스캐닝 사이클 종료 시 자동 실행
- **Task**:
  - **금일 수집된 모든 피드백 통합**
  - **FSSF 신호 유형 분류 모델 재학습**:
    ```
    1. 오분류 케이스 수집
    2. 분류 규칙 가중치 조정 (오분류 -20%, 정분류 +20%)
    3. 새로운 키워드-신호유형 매핑 추가
    4. 모델 버전 업데이트 (v1 → v2 → v3...)
    5. 정확도 변화 기록
    ```
  - **STEEPS 분류 모델 재학습** (동일 방식)
  - **Tipping Point 탐지 기준 조정**:
    - 놓친 임계점 신호 → 탐지 임계값 하향
    - 오알람 → 탐지 임계값 상향
  - **Anomaly Detection 기준 조정**:
    - 놓친 이상치 → z-score 기준 조정
    - Noise로 판명된 이상치 → 필터 규칙 추가
  - **Weak Signal 탐지 기준 조정**:
    - 놓친 신호 빈도 기반 임계값 조정
  - **크롤링 전략 최적화** (성공률 기반)
  - **다음 사이클에 학습 내용 자동 반영**
- **Output**:
  - `signal-classifier-model-v{n}.json`
  - `steeps-classifier-model-v{n}.json`
  - `learning-log-{date}.json`

---

## Learning Engine

### 분류 모델 재학습 로직

```python
def retrain_classifiers(feedback_data):
    """
    FSSF + STEEPS 분류 모델 자동 재학습
    트리거: 일일 스캐닝 사이클 종료 시
    """
    # === FSSF 신호 유형 분류 모델 ===
    signal_model = load_current_model("signal-classifier")

    for correction in feedback_data['signal_type_corrections']:
        keyword = extract_keywords(correction['article'])
        signal_model.weights[keyword][correction['from']] *= 0.8   # -20%
        signal_model.weights[keyword][correction['to']] *= 1.2     # +20%

    new_signal_mappings = extract_new_patterns(feedback_data, 'signal_type')
    signal_model.add_mappings(new_signal_mappings)
    save_model(signal_model, f"signal-classifier-model-v{signal_model.version + 1}.json")

    # === STEEPS 도메인 분류 모델 ===
    steeps_model = load_current_model("steeps-classifier")

    for correction in feedback_data['steeps_corrections']:
        keyword = extract_keywords(correction['article'])
        steeps_model.weights[keyword][correction['from']] *= 0.8
        steeps_model.weights[keyword][correction['to']] *= 1.2

    new_steeps_mappings = extract_new_patterns(feedback_data, 'steeps')
    steeps_model.add_mappings(new_steeps_mappings)
    save_model(steeps_model, f"steeps-classifier-model-v{steeps_model.version + 1}.json")

    # === Tipping Point 임계값 조정 ===
    tp_config = load_config("tipping-point-thresholds")
    for missed in feedback_data.get('missed_tipping_points', []):
        tp_config.lower_threshold(missed['indicator'], factor=0.9)
    for false_alarm in feedback_data.get('false_tipping_alarms', []):
        tp_config.raise_threshold(false_alarm['indicator'], factor=1.1)
    save_config(tp_config)

    # === Anomaly Detection 기준 조정 ===
    ad_config = load_config("anomaly-thresholds")
    for missed in feedback_data.get('missed_anomalies', []):
        ad_config.adjust_zscore(missed['metric'], delta=-0.2)
    for noise in feedback_data.get('noise_anomalies', []):
        ad_config.add_filter_rule(noise['pattern'])
    save_config(ad_config)

    # === 학습 기록 ===
    log_learning(signal_model, steeps_model, tp_config, ad_config, feedback_data)
```

### 학습 대상

| 대상 | 조정 항목 | 방식 |
|-----|---------|-----|
| FSSF 신호 유형 분류 | 키워드-신호유형 가중치 | 오분류 -20%, 정분류 +20% |
| STEEPS 분류 | 키워드-영역 가중치 | 오분류 -20%, 정분류 +20% |
| Tipping Point 탐지 | 분산/자기상관 임계값 | 놓친 신호 → 하향, 오알람 → 상향 |
| Anomaly Detection | z-score 기준, 필터 규칙 | 놓친 이상치 → 하향, Noise → 필터 추가 |
| Weak Signal | 탐지 임계값 | 놓친 신호 빈도 기반 |
| 크롤링 | 전략 선호도 | 성공률 기반 |

---

## Claude Code Configuration

### Sub-agents

```yaml
agents:
  crawl-defender:
    description: "크롤링 차단 방어/우회 전문 에이전트"
    priority: CRITICAL
    skills: [anti-block-crawler]
    tools: [bash, file-system]
    capabilities:
      - 차단 유형 실시간 분석
      - 우회 Python 코드 동적 생성
      - 프록시/UA 로테이션
      - Selenium/Playwright 전환
      - 성공 패턴 학습 저장
    error_handling:
      on_block: retry_with_new_strategy
      max_retries: unlimited
      success_required: true

  news-crawler:
    description: "네이버 뉴스 크롤링 실행"
    skills: [anti-block-crawler]
    tools: [bash]
    rate_limit:
      base_delay: 2-5s
      randomize: true
    on_failure:
      call: crawl-defender
      mode: immediate

  dedup-filter:
    description: "중복 제거 + Noise 필터링 + S/N 비율 산출"
    tools: [bash]
    algorithms: [jaccard_similarity, simhash, hierarchical_clustering]
    noise_filters: [ad_detection, info_density, relevance_check]

  signal-classifier:
    description: "FSSF 신호 유형 + STEEPS 도메인 이중 분류 (학습 가능)"
    temperature: 0.3
    learning_enabled: true
    models:
      signal_type: "models/signal-classifier-model-current.json"
      steeps: "models/steeps-classifier-model-current.json"
    classification_targets:
      signal_types: [weak_signal, emerging_issue, trend, megatrend, driver, wild_card, discontinuity, precursor_event]
      steeps_domains: [S_social, T_technological, E_economic, E_environmental, P_political, S_spiritual]

  issue-scanner:
    description: "환경스캐닝 템플릿 적용 + 간이 우선순위 태깅"
    template: "Kuwait Oil + UNDP 13필드 + 확장 3필드 (16필드)"

  pattern-detector:
    description: "패턴 분석, 선조 이벤트 탐지, Tipping Point 신호, 이상치 탐지"
    tools: [bash]
    lookback_days: [7, 30, 90]
    tipping_point_indicators:
      - variance_tracking
      - autocorrelation_lag1
      - exponential_frequency_change
      - flickering_detection
      - discontinuity_keywords
    anomaly_methods:
      - zscore_threshold: 3
      - new_cluster_detection: 30d_window
      - cross_domain_anomaly

  actor-identifier:
    description: "핵심 인물/기관 식별 (identification만, 네트워크 분석은 별도 시스템)"
    scope: global
    extraction_targets:
      domestic: [politicians, business_leaders, academics, religious_leaders]
      international: [heads_of_state, global_ceos, intl_org_leaders, experts]

  alert-dispatcher:
    description: "긴급 신호 실시간 Alert 발송"
    trigger_conditions:
      - tipping_point_red
      - wild_card_high_importance
      - discontinuity_high_confidence
      - h3_weak_signal_cross_steeps
      - wild_card_candidate_anomaly
    channels: [console]

  learning-engine:
    description: "피드백 학습 및 분류 모델 재학습"
    trigger: end_of_daily_cycle
    learning_targets:
      - fssf_signal_classification
      - steeps_classification
      - tipping_point_detection
      - anomaly_detection
      - weak_signal_detection
      - crawl_strategy
```

### Slash Commands

```yaml
commands:
  /run-scan:
    description: "전체 환경스캐닝 파이프라인 실행 (Phase 1-7)"

  /check-crawl:
    description: "크롤링 결과, 차단 대응, S/N 비율 확인"
    feedback_enabled: true

  /review-scan:
    description: "FSSF/STEEPS 분류, Three Horizons, 우선순위 검토"
    feedback_enabled: true
    feedback_triggers_learning: true

  /defense-status:
    description: "차단 대응 상세 로그 확인"

  /view-patterns:
    description: "발견된 패턴 및 선조 이벤트 확인"

  /view-tipping:
    description: "Tipping Point 경보 레벨 및 지표 확인"

  /view-anomalies:
    description: "이상치 탐지 결과 확인"

  /view-actors:
    description: "식별된 핵심 행위자 확인"
    scope: [domestic, international, all]

  /learning-status:
    description: "분류 모델 학습 현황 및 정확도 확인"

  /feedback:
    description: "피드백 직접 입력"
    args: [category, content]
    categories: [signal_type, steeps, tipping_point, anomaly, missed_signal, false_alarm]
```

### Required Skills

```yaml
skills:
  - anti-block-crawler  # 최우선 - 크롤링 핵심
```

---

## Output Structure

```
outputs/
├── daily/{YYYY-MM-DD}/
│   ├── crawl-strategy.json           # Phase 1
│   ├── raw-news.json                 # Phase 1
│   ├── defense-log.json              # Phase 1
│   ├── learned-crawl-patterns.json   # Phase 1
│   ├── unique-news.json              # Phase 2
│   ├── media-patterns.json           # Phase 2
│   ├── snr-metrics.json              # Phase 2
│   ├── signal-typed-news.json        # Phase 3
│   ├── classified-news.json          # Phase 3
│   ├── scanned-issues.json           # Phase 3
│   ├── pattern-analysis.json         # Phase 4
│   ├── precursor-candidates.json     # Phase 4
│   ├── tipping-point-indicators.json # Phase 4
│   ├── anomaly-detection.json        # Phase 4
│   ├── identified-actors.json        # Phase 5
│   ├── prioritized-scan.json         # Phase 5
│   ├── credibility-scores.json       # Phase 5
│   ├── human-feedback.json           # Phase 5
│   ├── scan-output-{date}.json       # Phase 6 (후속 시스템 연계)
│   ├── scan-summary-{date}.json      # Phase 6
│   ├── alert-log-{date}.json         # Phase 6
│   └── learning-log-{date}.json      # Phase 7
│
├── models/
│   ├── signal-classifier-model-v{n}.json     # FSSF 신호 유형 분류
│   ├── signal-classifier-model-current.json  # → v{latest}
│   ├── steeps-classifier-model-v{n}.json     # STEEPS 도메인 분류
│   ├── steeps-classifier-model-current.json  # → v{latest}
│   └── model-history.json
│
├── config/
│   ├── tipping-point-thresholds.json         # Tipping Point 임계값
│   ├── anomaly-thresholds.json               # 이상치 탐지 임계값
│   ├── noise-filter-rules.json               # Noise 필터 규칙
│   └── source-credibility-base.json          # 언론사 기본 신뢰도
│
└── history/
    └── signal-lifecycle-tracking.json         # 신호 성숙도 생명주기 누적
```

---

## v2.0 → v3.0 변경 사항 요약

### 삭제 (별도 시스템으로 분리)

| 항목 | v2.0 Step | 이관 대상 시스템 |
|------|----------|---------------|
| Futures Wheel 분석 (3차 파급) | Step 8 | 환경분석 시스템 |
| Cross-Impact Analysis | Step 11 | 환경분석 시스템 |
| Argument Structure 분석 | Step 13 | 담론분석 시스템 |
| Collective Intelligence DB 업데이트 | Step 15 | 지식관리 시스템 |
| 환경스캐닝 보고서 생성 | Step 16 | 보고서 시스템 |
| (human) 최종 보고서 검토 | Step 17 | 보고서 시스템 |
| 포맷 변환 (docx/pdf) | Step 19 | 보고서 시스템 |
| Global Actor 네트워크 매핑 | Step 10 일부 | 행위자분석 시스템 |
| 정교한 P-I Matrix | Step 12 일부 | 환경분석 시스템 |

### 추가 (환경스캐닝 기술 보강)

| 항목 | v3.0 Step | 근거 |
|------|----------|------|
| FSSF 8가지 신호 유형 분류 | Step 6 | Kuosa (2010) 완전한 신호 분류 체계 |
| Three Horizons 시간 지평 분류 | Step 8 확장 | H3 신호의 H1 시점 포착 (절대 목표 직결) |
| 불확실성 수준 분류 | Step 8 확장 | 신호의 인식론적 상태 구분 |
| Tipping Point 접근 신호 탐지 | Step 10 신규 | Critical Slowing Down 이론 적용 |
| Anomaly Detection | Step 11 신규 | 통계적 이상치 = Weak Signal 후보 |
| 실시간 Alert 시스템 | Step 16 신규 | "가장 빨리" 목표 직결 |
| Noise 필터링 | Step 4 강화 | Signal-to-Noise Ratio 관리 |
| Source Credibility Score | Step 13 강화 | 신호 신뢰도 정량화 |
| 다중 시계열 (7/30/90일) | Step 9 강화 | 패턴 탐지 정밀도 향상 |
| 신호 성숙도 생명주기 추적 | Phase 4 전체 | Noise→Signal→Trend 전환 모니터링 |

### 에이전트 변경

| v2.0 | v3.0 | 변경 |
|------|------|------|
| `@steeps-classifier` | `@signal-classifier` | FSSF + STEEPS 이중 분류로 확장 |
| `@issue-analyzer` | `@issue-scanner` | 분석 제거, 스캐닝 템플릿 적용만 |
| `@deduplicator` | `@dedup-filter` | Noise 필터링 + S/N Ratio 추가 |
| `@global-actor-tracker` | `@actor-identifier` | 네트워크 분석 제거, 식별만 |
| `@futures-analyst` | (삭제) | 환경분석 시스템으로 이관 |
| `@knowledge-manager` | (삭제) | 지식관리 시스템으로 이관 |
| `@report-generator` | (삭제) | 보고서 시스템으로 이관 |
| (없음) | `@alert-dispatcher` | 신규: 실시간 Alert 발송 |
| (없음) | `@scan-outputter` | 신규: 후속 시스템 연계 데이터 출력 |
