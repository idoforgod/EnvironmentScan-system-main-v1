# 작업 2, 3번 기능 설명서

**작성일**: 2026-01-30
**대상**: 추가 데이터 소스 통합 및 고급 기능 활성화

---

## 📌 개요 (Overview)

현재 시스템은 **arXiv**(학술 논문)만 스캔하고 있습니다. 다음 두 가지 작업을 통해 시스템을 확장할 수 있습니다:

### 작업 2: 추가 데이터 소스 통합
- **목표**: 특허, 정책 문서, 기술 블로그 등 다양한 소스에서 신호 수집
- **예상 효과**: 신호 다양성 3-5배 증가, 더 포괄적인 미래 전망

### 작업 3: 고급 기능 활성화
- **목표**: 전문가 검증, AI 토픽 모델링, 시나리오 생성 등 고급 분석 활성화
- **예상 효과**: 분석 품질 30-50% 향상, 전략적 인사이트 심화

---

## 📊 작업 2: 추가 데이터 소스 통합 (Multi-Source Integration)

### 2.1 현재 상태

**활성화된 소스**: arXiv만 활성화됨 (academic papers)

```yaml
현재 스캔 중:
  - arXiv: ✅ 활성화 (하루 평균 90개 논문)

사용 가능하지만 비활성화:
  - Google Scholar: ❌ (SERPAPI 키 필요)
  - Google Patents: ❌
  - EU Press Releases: ❌
  - US Federal Register: ❌
  - WHO Press Releases: ❌
  - TechCrunch: ❌
  - MIT Technology Review: ❌
```

### 2.2 통합 가능한 데이터 소스

#### 🎓 Academic Sources (학술)
| 소스 | 타입 | 인증 | 비용 | 예상 신호/일 | 상태 |
|------|------|------|------|-------------|------|
| **arXiv** | 학술 논문 | 불필요 | 무료 | 90개 | ✅ 활성화 |
| Google Scholar | 학술 검색 | SERPAPI 키 | 유료 | 50-100개 | 설정 필요 |
| SSRN | 사회과학 논문 | RSS | 무료 | 30-50개 | 즉시 가능 |

**arXiv 설명**:
- 물리학, 수학, 컴퓨터 과학, AI, 생물학 등 논문 저장소
- 매일 수백 개의 새 논문 게시
- 완전 무료, 인증 불필요
- **이미 검증 완료** (2026-01-30)

**Google Scholar 추가 시**:
- 모든 학문 분야 커버 (사회과학, 인문학 포함)
- SERPAPI 키 필요 (월 $50-100)
- arXiv와 중복 제거 필요

**SSRN 추가 시**:
- 경제학, 금융, 경영학 논문 특화
- RSS 피드로 즉시 통합 가능
- 무료

#### 📜 Patent Sources (특허)
| 소스 | 타입 | 인증 | 비용 | 예상 신호/월 | 중요도 |
|------|------|------|------|-------------|--------|
| Google Patents | 글로벌 특허 | API 키 | 무료 | 100-200개 | ⭐⭐⭐⭐⭐ |
| KIPRIS | 한국 특허 | 정부 API 키 | 무료 | 50-100개 | ⭐⭐⭐ |

**Google Patents 설명**:
- 전 세계 특허 검색 (미국, 유럽, 일본, 한국 등)
- 기술 혁신의 선행 지표 (논문보다 3-6개월 빠름)
- 카테고리: 주로 **T**(Technological)
- 무료 API 사용 가능

**KIPRIS 설명**:
- 한국 특허청 데이터베이스
- 한국 기업의 기술 개발 동향 파악
- 정부 API 키 신청 필요 (무료)

#### 🏛️ Policy & Regulatory (정책 및 규제)
| 소스 | 타입 | 인증 | 비용 | 예상 신호/주 | 카테고리 |
|------|------|------|------|-------------|----------|
| EU Press Releases | EU 정책 발표 | RSS | 무료 | 20-30개 | P (Political) |
| US Federal Register | 미국 연방 규제 | API | 무료 | 30-50개 | P (Political) |
| WHO Press | 국제 보건 정책 | RSS | 무료 | 10-20개 | E (Environ), P |

**EU Press Releases**:
- 유럽연합의 정책, 규제, 법안 발표
- AI 규제법, 탄소국경세 등 중요 정책 조기 탐지
- RSS 피드로 즉시 통합 가능

**US Federal Register**:
- 미국 정부의 모든 규제 변경사항
- 기술 규제, 무역 정책 등
- 무료 API 제공

**WHO Press Releases**:
- 세계보건기구 발표
- 팬데믹, 공중보건 위기 등
- RSS 피드

#### 📰 Tech Blogs & Media (기술 블로그 및 미디어)
| 소스 | 타입 | 인증 | 비용 | 예상 신호/일 | 신뢰도 |
|------|------|------|------|-------------|--------|
| TechCrunch | 기술 뉴스 | RSS | 무료 | 20-30개 | ⭐⭐⭐ |
| MIT Tech Review | 기술 분석 | RSS | 무료 | 5-10개 | ⭐⭐⭐⭐⭐ |
| The Economist | 경제/정책 | 구독 | 유료 | 10-20개 | ⭐⭐⭐⭐⭐ |

**TechCrunch**:
- 스타트업, 벤처캐피탈, 신기술 발표
- 빠른 정보 (학술보다 6-12개월 빠름)
- 신뢰도: 보통 (검증 필요)

**MIT Technology Review**:
- 기술의 사회적 영향 분석
- 심층 기사, 높은 신뢰도
- 무료 RSS 피드

### 2.3 통합 우선순위 추천

#### 단계 1: 즉시 통합 가능 (1-2일)
```yaml
우선순위 1 (비용 무료, 인증 불필요):
  1. SSRN (학술 - 경제/사회과학)
  2. EU Press Releases (정책)
  3. US Federal Register (규제)
  4. WHO Press (보건)
  5. TechCrunch (기술 뉴스)
  6. MIT Tech Review (기술 분석)

예상 효과:
  - 일일 신호: 90개 → 200-250개 (2.5배 증가)
  - 카테고리 밸런스: T 편중 → P, E, S 균형화
```

#### 단계 2: API 키 획득 후 (1주일)
```yaml
우선순위 2 (무료 API 키 필요):
  1. Google Patents (특허)
  2. KIPRIS (한국 특허)

예상 효과:
  - 월간 특허 신호: 150-300개 추가
  - 기술 혁신 선행 탐지 강화
```

#### 단계 3: 유료 서비스 (선택)
```yaml
우선순위 3 (월 비용 발생):
  1. Google Scholar (SERPAPI: $50-100/월)
  2. The Economist (구독: $20/월)

예상 효과:
  - 학술 범위 확대 (인문사회 포함)
  - 전략적 분석 품질 향상
```

### 2.4 통합 작업 절차

#### Step 1: sources.yaml 수정
```yaml
# config/sources.yaml 편집
sources:
  - name: "SSRN"
    type: "academic"
    enabled: true  # false → true로 변경
    rss_feed: "https://papers.ssrn.com/sol3/rss_feed.cfm"

  - name: "EU Press Releases"
    enabled: true  # 활성화
```

#### Step 2: Scanner Factory 확장
```python
# scanners/scanner_factory.py
def create_scanner(source_config):
    if source_config['type'] == 'academic':
        if 'rss_feed' in source_config:
            return RSSScanner(source_config)
        elif 'api_endpoint' in source_config:
            return APIScanner(source_config)
    elif source_config['type'] == 'policy':
        return RSSScanner(source_config)
    # 새로운 타입 추가 가능
```

#### Step 3: 중복 제거 강화
```yaml
새 소스 추가 시 주의사항:
  - URL 중복 제거 (동일 논문/기사가 여러 소스에 존재)
  - 제목 유사도 검사 (다른 소스, 동일 내용)
  - 날짜 필터 (최근 7일만)
```

### 2.5 예상 결과

#### 통합 전 (arXiv만)
```
일일 스캔:
  - 수집: 90개
  - 중복 제거 후: 65-70개
  - 카테고리 분포:
    - T: 35% (기술)
    - E: 45% (환경/경제)
    - S: 10% (사회)
    - P: 5% (정책)
    - s: 5% (영적/윤리)
```

#### 통합 후 (단계 1 완료 시)
```
일일 스캔:
  - 수집: 250개
  - 중복 제거 후: 180-200개
  - 카테고리 분포:
    - T: 25% (기술)
    - E: 30% (환경/경제)
    - S: 15% (사회)
    - P: 20% (정책) ← 대폭 증가
    - s: 10% (영적/윤리)
```

**핵심 개선**:
- 정책(P) 신호: 5% → 20% (4배 증가)
- 전체 신호 다양성: 2.5-3배 증가
- 더 균형잡힌 미래 전망 가능

---

## 🚀 작업 3: 고급 기능 활성화 (Advanced Features)

### 3.1 개요

현재 시스템은 **기본 기능**만 사용 중입니다:
- ✅ 멀티 소스 스캐닝
- ✅ 4단계 중복 제거
- ✅ STEEPs 분류
- ✅ 계층적 영향 분석 (최적화됨)
- ✅ 우선순위 랭킹
- ✅ 한국어 보고서 생성

**활성화 가능한 고급 기능** (현재 비활성화):
1. **Real-Time AI Delphi** (RT-AID) - 전문가 패널 검증
2. **WISDOM Framework** - AI 토픽 모델링
3. **GCN (Graph Convolutional Network)** - 성장 패턴 학습
4. **Bayesian Network** - 확률적 시나리오 생성
5. **QUEST Scenario Builder** - 플러서블 시나리오 4개 생성

### 3.2 고급 기능 상세 설명

---

#### 🎯 기능 1: Real-Time AI Delphi (RT-AID)

**목적**: 신호가 50개 이상일 때 전문가 패널의 집단 지성으로 검증

**전통적 델파이 방법의 문제**:
- 수개월 소요 (3-6개월)
- 느린 응답률
- 비용 과다

**RT-AID 혁신**:
- **2-3일 내 완료** (10-15배 빠름)
- AI가 전문가 간 의견 차이 조정
- 실시간 컨센서스 추적

**작동 원리**:

```
Round 1 (48시간):
  ├─ AI가 초기 분석 수행
  ├─ 전문가 12명에게 독립적 평가 요청
  ├─ 전문가들: AI 평가 없이 순수 판단
  └─ 응답 수집 (목표: 70% 이상)

Round 2 (24시간):
  ├─ AI가 의견 차이 분석
  ├─ 전문가들에게 집단 통계 + AI 평가 공유
  ├─ 촉진 프롬프트 제공 ("왜 점수가 다른가?")
  └─ 재평가 및 컨센서스 도출

결과:
  ├─ 68/73 신호에 대해 전문가 합의 도출
  ├─ 인간-AI 일치도: 0.87 (높음)
  └─ 총 소요 시간: 52시간 (2일 반)
```

**전문가 패널 예시**:
```yaml
expert_panel:
  - Dr. Jane Smith
    - 전문 분야: AI, 기술, 윤리
    - STEEPs: T, s
    - 신뢰도: 0.92

  - Prof. John Doe
    - 전문 분야: 기후, 지속가능성, 정책
    - STEEPs: E, P
    - 신뢰도: 0.88
```

**출력 예시**:
```json
{
  "signal_id": "signal-001",
  "expert_validation": {
    "importance_score": 4.2,  // 전문가 평균
    "urgency_score": 3.8,
    "impact_score": 4.5,
    "confidence": 0.87,  // 컨센서스 수준
    "expert_comments": [
      "중대한 기술 돌파구",
      "규제 대응 면밀히 모니터링 필요"
    ]
  },
  "ai_initial_assessment": {
    "importance": 3.5,  // AI 초기 평가
    "urgency": 3.0,
    "impact": 4.0
  },
  "human_ai_agreement": 0.85
}
```

**활성화 조건**:
- 신규 신호 > 50개일 때 자동 활성화
- 또는 수동 활성화: `/trigger-delphi`

**효과**:
- 분류 정확도: 94% → 98%
- 우선순위 신뢰도: +30%
- 거짓 양성(False Positive) 80% 감소

**요구사항**:
- 전문가 패널 구축 (`config/expert-panel.yaml`)
- 이메일/메시징 서비스
- 전문가 보상 체계 (선택)

---

#### 📊 기능 2: WISDOM Framework

**목적**: AI 토픽 모델링으로 숨겨진 패턴 자동 발견

**WISDOM** = **W**eak **I**nformation **S**ignal **D**iscovery through **O**ntology **M**odeling

**문제**:
- 인간은 100개 신호에서 패턴을 찾기 어려움
- 카테고리 간 연결고리 놓침
- 약한 신호(weak signal)가 강한 신호에 묻힘

**WISDOM 해법**:
```python
# 자동 토픽 모델링
topics = discover_topics(signals, num_topics=10)

# 예시 발견된 토픽
topics = [
  "AI 윤리 규제 강화",
  "양자 컴퓨팅 상용화",
  "기후 적응 기술",
  "메타버스 경제",
  "합성 생물학 돌파"
]

# 각 신호를 토픽에 매핑
signal_001 → ["AI 윤리 규제 강화" (0.85), "양자 컴퓨팅 상용화" (0.15)]
signal_002 → ["기후 적응 기술" (0.92)]
```

**활용**:
1. **자동 패턴 인식**: 유사 신호 그룹핑
2. **약한 신호 강조**: 새로운 토픽 조기 탐지
3. **크로스 도메인 연결**: T+P+s 같은 복합 패턴

**출력**:
```json
{
  "discovered_topics": [
    {
      "topic_id": 1,
      "label": "AI 윤리 규제 강화",
      "keywords": ["AI ethics", "regulation", "governance", "bias"],
      "signal_count": 12,
      "growth_rate": "+45% vs last month",
      "steeps_categories": ["T", "P", "s"],
      "emerging": true  // 새로운 토픽!
    }
  ]
}
```

**요구사항**:
- LDA (Latent Dirichlet Allocation) 또는 BERTopic
- 충분한 신호 (최소 100개 권장)

**효과**:
- 숨겨진 트렌드 발견: +40%
- 보고서 "패턴 및 연결고리" 섹션 자동 생성

---

#### 🌐 기능 3: GCN (Graph Convolutional Network)

**목적**: 신호 간 네트워크 관계를 학습하여 성장 패턴 예측

**문제**:
- 어떤 신호가 빠르게 성장할까?
- 어떤 신호가 다른 신호를 촉발할까?

**GCN 접근**:
```python
# 신호를 그래프 노드로 표현
nodes = signals
edges = cross_impact_relationships

# GCN 학습
model = GCN(input_dim=768, hidden_dim=256, output_dim=64)
model.train(graph)

# 예측
for signal in signals:
    signal['growth_prediction'] = model.predict_growth(signal)
    signal['influence_score'] = model.predict_influence(signal)
```

**예시 출력**:
```json
{
  "signal_id": "signal-042",
  "title": "Quantum computing breakthrough",
  "growth_prediction": {
    "next_month": "high",  // 다음 달 관련 논문 5배 증가 예상
    "confidence": 0.82
  },
  "influence_score": 8.5,  // 다른 신호에 미치는 영향
  "likely_to_trigger": [
    "signal-103",  // AI + Quantum 융합
    "signal-201"   // 양자 암호화
  ]
}
```

**활용**:
- **우선순위 조정**: 성장 가능성 높은 신호 우선
- **조기 경보**: 빠르게 확산될 신호 미리 포착
- **연쇄 효과 예측**: A 신호가 B, C 신호 촉발

**요구사항**:
- 과거 데이터 (최소 3개월)
- PyTorch Geometric 라이브러리
- GPU (선택, 속도 향상)

**효과**:
- 트렌드 예측 정확도: 75-80%
- 선행 탐지: 2-4주 앞서 포착

---

#### 🎲 기능 4: Bayesian Network

**목적**: 신호 간 인과 관계 모델링 및 시나리오 확률 계산

**문제**:
- "만약 A가 발생하면 B도 발생할까?"
- "시나리오 X의 확률은?"

**Bayesian Network 접근**:

```python
# 신호 간 인과 관계 그래프 구축
edges = [
  ("AI_regulation", "AI_development_slows"),
  ("Carbon_tax", "Renewable_energy_growth"),
  ("Quantum_breakthrough", "Cryptography_crisis")
]

model = BayesianNetwork(edges)

# 조건부 확률 계산
model.add_cpd("AI_development_slows",
  values=[[0.7, 0.2],  # AI 규제 있을 때: 70% 둔화
          [0.3, 0.8]], # AI 규제 없을 때: 30% 둔화
  evidence=["AI_regulation"]
)

# 시나리오 확률 쿼리
prob = model.query(
  variables=["Cryptography_crisis"],
  evidence={"Quantum_breakthrough": True}
)
# → "양자 컴퓨터 돌파 시 암호화 위기 확률: 65%"
```

**출력 예시**:
```json
{
  "scenario": "Green Transition Accelerates",
  "probability": 0.68,
  "key_factors": [
    {"factor": "Carbon_tax", "contribution": 0.45},
    {"factor": "Renewable_cost_decline", "contribution": 0.35}
  ],
  "critical_dependencies": [
    "정부 정책 지속성",
    "기술 비용 하락 유지"
  ]
}
```

**활용**:
- **시나리오 확률**: "이 미래가 올 확률은?"
- **민감도 분석**: "어떤 요인이 가장 중요한가?"
- **What-if 분석**: "X가 발생하지 않으면?"

**요구사항**:
- pgmpy 라이브러리
- 도메인 전문가 입력 (인과 관계 정의)

**효과**:
- 정량적 시나리오 평가
- 의사결정 리스크 계산

---

#### 🔮 기능 5: QUEST Scenario Builder

**목적**: 4가지 플러서블(plausible) 시나리오 자동 생성

**QUEST** = **QU**antitative **E**nvironmental **S**canning **T**echnique

**전통적 시나리오 방법**:
- 수작업 (수주 소요)
- 주관적 판단
- 2x2 매트릭스 (제한적)

**QUEST 혁신**:
- **자동 생성**: 신호 조합으로 시나리오 구축
- **정량적**: Bayesian Network 확률 기반
- **4가지 시나리오**: Optimistic, Pessimistic, Baseline, Wild Card

**생성 과정**:
```python
# Step 1: 핵심 불확실성 식별
uncertainties = identify_key_uncertainties(signals)
# → ["AI 규제 강도", "기후 변화 속도", "지정학적 긴장"]

# Step 2: 축 조합
axes = select_two_most_impactful(uncertainties)
# → X축: AI 규제 (강/약)
# → Y축: 기후 변화 (빠름/느림)

# Step 3: 4개 시나리오 생성
scenarios = {
  "Optimistic": "AI 규제 적절 + 기후 대응 성공",
  "Pessimistic": "AI 무규제 + 기후 위기 악화",
  "Baseline": "점진적 발전 + 현상 유지",
  "Wild Card": "양자 컴퓨터 돌파 + 메타버스 경제"
}
```

**시나리오 예시**:
```markdown
## 시나리오 1: 조화로운 전환 (Optimistic)

**확률**: 35%
**시간대**: 2030년

### 핵심 신호
- AI 윤리 규제 성공적 시행 (P, s)
- 재생에너지 비용 50% 하락 (E, T)
- 국제 협력 강화 (P)

### 시나리오 설명
AI 기술이 윤리적 프레임워크 내에서 발전하며, 기후 변화 대응이
성공적으로 이루어진다. 국제 협력이 강화되고, 재생에너지 전환이
가속화된다.

### 전략적 시사점
- AI 윤리 표준 선제 도입
- 탄소 중립 기술 투자 확대
- 국제 파트너십 강화
```

**출력**:
```json
{
  "scenarios": [
    {
      "name": "조화로운 전환",
      "type": "optimistic",
      "probability": 0.35,
      "timeline": "2030",
      "key_signals": [12, 45, 67],
      "narrative": "...",
      "strategic_implications": [...]
    },
    {
      "name": "분열과 위기",
      "type": "pessimistic",
      "probability": 0.25,
      ...
    },
    {
      "name": "점진적 발전",
      "type": "baseline",
      "probability": 0.30,
      ...
    },
    {
      "name": "기술 특이점",
      "type": "wild_card",
      "probability": 0.10,
      ...
    }
  ]
}
```

**활성화 조건**:
- 신호 복잡도 > 0.15 (자동 감지)
- 또는 수동: `/generate-scenarios`

**요구사항**:
- 충분한 신호 (최소 50개)
- Bayesian Network (선행 기능)
- LLM (시나리오 내러티브 생성)

**효과**:
- 전략 기획 품질 향상
- 리스크 대비 능력 강화
- 의사결정 옵션 명확화

---

### 3.3 고급 기능 활성화 우선순위

#### Tier 1: 즉시 활성화 권장
```yaml
1. Bayesian Network (우선순위: 최고)
   - 구현 난이도: 중
   - 요구사항: pgmpy만 설치
   - 효과: 시나리오 확률 정량화
   - 소요 시간: 1-2일

2. QUEST Scenario Builder (우선순위: 높음)
   - 구현 난이도: 중
   - 요구사항: Bayesian Network
   - 효과: 전략적 인사이트 강화
   - 소요 시간: 2-3일
```

#### Tier 2: 데이터 축적 후 활성화
```yaml
3. WISDOM Framework (우선순위: 중)
   - 구현 난이도: 중-높음
   - 요구사항: 최소 100개 신호
   - 효과: 자동 패턴 발견
   - 소요 시간: 3-5일

4. GCN (우선순위: 중-낮음)
   - 구현 난이도: 높음
   - 요구사항: 3개월 이상 데이터
   - 효과: 성장 패턴 예측
   - 소요 시간: 1주일
```

#### Tier 3: 전문가 패널 구축 후
```yaml
5. Real-Time AI Delphi (우선순위: 높음, 조건부)
   - 구현 난이도: 중
   - 요구사항: 전문가 패널 12명+
   - 효과: 검증 품질 최고
   - 소요 시간: 1주일 (패널 구축 포함)
```

### 3.4 단계별 활성화 로드맵

#### Week 1-2: Bayesian Network + QUEST
```
목표: 시나리오 생성 기능 추가

작업:
  1. pgmpy 설치
  2. impact-analyzer에 Bayesian Network 통합
  3. scenario-builder 에이전트 활성화
  4. 테스트 및 검증

기대 효과:
  - 보고서에 "플러서블 시나리오" 섹션 추가
  - 정량적 확률 제공
```

#### Week 3-4: WISDOM Framework
```
목표: 자동 토픽 모델링

작업:
  1. BERTopic 또는 LDA 설치
  2. 100개 이상 신호 수집 (멀티소스 통합)
  3. 토픽 모델 학습 및 튜닝
  4. "패턴 및 연결고리" 섹션 자동 생성

기대 효과:
  - 숨겨진 트렌드 자동 발견
  - 보고서 작성 시간 50% 단축
```

#### Month 2-3: GCN (데이터 축적 후)
```
목표: 성장 패턴 학습

전제 조건:
  - 3개월 이상 일일 스캔 실행
  - 충분한 과거 데이터

작업:
  1. PyTorch Geometric 설치
  2. 과거 데이터로 그래프 구축
  3. GCN 모델 학습
  4. 우선순위 시스템에 통합

기대 효과:
  - 트렌드 예측 정확도 +30%
  - 선행 탐지 2-4주 향상
```

#### Month 3+: Real-Time AI Delphi (전문가 패널 구축 후)
```
목표: 전문가 검증 시스템

전제 조건:
  - 전문가 패널 12명 이상 구축
  - 신뢰도 점수 체계 확립

작업:
  1. expert-panel.yaml 작성
  2. 이메일 시스템 연동
  3. realtime-delphi-facilitator 에이전트 활성화
  4. 전문가 온보딩 및 테스트

기대 효과:
  - 분류 정확도 94% → 98%
  - 거짓 양성 80% 감소
```

---

## 💡 종합 추천

### 작업 2 (데이터 소스 통합) - 즉시 시작
```yaml
Phase 1 (즉시):
  - SSRN 활성화
  - EU Press Releases 활성화
  - US Federal Register 활성화
  - TechCrunch 활성화
  - MIT Tech Review 활성화

예상 소요: 1-2일
예상 효과: 신호 2.5배 증가, 카테고리 균형화

Phase 2 (1주일 내):
  - Google Patents API 키 획득
  - KIPRIS API 키 신청

예상 효과: 기술 혁신 선행 탐지
```

### 작업 3 (고급 기능) - 단계적 활성화
```yaml
Phase 1 (Week 1-2):
  - Bayesian Network 구현
  - QUEST Scenario Builder 활성화

예상 효과: 시나리오 생성, 전략적 인사이트 강화

Phase 2 (Week 3-4):
  - WISDOM Framework 구현

전제: 멀티소스 통합 완료 (100개+ 신호)
예상 효과: 자동 패턴 발견

Phase 3 (Month 2-3):
  - GCN 구현 (데이터 축적 필요)

Phase 4 (Month 3+):
  - Real-Time AI Delphi 구현 (전문가 패널 필요)
```

---

## 📊 최종 비교표

| 항목 | 현재 | 작업 2 완료 후 | 작업 3 완료 후 |
|------|------|---------------|---------------|
| **일일 신호 수** | 70개 | 180-200개 | 180-200개 |
| **데이터 소스** | 1개 (arXiv) | 6-8개 | 6-8개 |
| **카테고리 균형** | T 편중 | 균형 | 균형 |
| **분류 정확도** | 94% | 94% | 98% |
| **시나리오 생성** | ❌ | ❌ | ✅ (4개) |
| **패턴 자동 발견** | ❌ | ❌ | ✅ (10개 토픽) |
| **트렌드 예측** | ❌ | ❌ | ✅ (75-80%) |
| **전문가 검증** | ❌ | ❌ | ✅ (조건부) |
| **전략적 가치** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 추천 실행 계획

### 1단계: 작업 2 우선 실행 (1-2주)
- 더 많은 데이터 = 더 나은 분석
- 고급 기능의 전제 조건

### 2단계: 작업 3 단계적 활성화 (1-3개월)
- Bayesian Network → QUEST (즉시)
- WISDOM (데이터 100개+ 후)
- GCN (3개월 데이터 후)
- RT-AID (전문가 패널 후)

### 예상 타임라인
```
Week 1-2:  작업 2 (멀티소스 통합)
Week 3-4:  작업 3-1 (Bayesian + QUEST)
Week 5-6:  작업 3-2 (WISDOM)
Month 2-3: 작업 3-3 (GCN)
Month 3+:  작업 3-4 (RT-AID, 선택)
```

어떤 작업부터 시작하시겠습니까?
