# Environmental Scanning Workflow (Version 1.0 - Enhanced)

미래 연구(Futures Research)를 위한 환경스캐닝 시스템: 변화의 조기 징후(약한 신호, weak signals)를 체계적으로 탐지하고 분석하여 전략적 의사결정을 지원하는 AI 자동화 워크플로우.

## 절대 목표 (Absolute Goal)

> **🎯 제1 목적**: "미래의 트랜드, 중기 변화, 거시 변화, 패러다임 대전환, 변화의 임계점 통과, 싱귤레리티, 급변사태, 뜻밖의 미래 등이 만들어내는 사전 신호를 한국, 아시아, 유럽, 아프리카, 아메리카 대륙 등 전 세계에서 **'가장 빨리' catchup** 하는 것이 가장 중요한 목적이다."

이 목표는 workflow의 모든 단계와 모든 기능에 절대 목표로 고정되어 있습니다.

---

## Overview

- **Input**: 뉴스, 학술DB, 특허, 보고서, RSS 피드, 전문가 네트워크
- **Output**: 일일 환경스캐닝 보고서 (신규 신호 분석 포함)
- **Frequency**: Daily (매일 1회)

### [Advanced] Enhanced Capabilities

**AI/ML 통합 자동화**:
- WISDOM 프레임워크 기반 약한 신호 자동 탐지
- Graph Convolutional Network (GCN)를 활용한 신호 성장 패턴 학습
- Real-Time AI Delphi (RT-AID)를 통한 전문가 의견 수렴 가속화

**처리 속도 향상**:
- Multi-Stage Cascade 필터링으로 중복 탐지 정확도 15% 향상
- 처리 시간 30% 단축
- 신규 신호 탐지 속도 2배 향상 (AI 자동화 적용 시)

**분류 체계**:
- **STEEPs** 절대 기준 카테고리 유지 (고유 분류 체계)
- Social, Technological, Economic, Environmental, Political, spiritual (6개 영역)

---

## 핵심 원칙 (Critical Principles)

> ⚠️ **이 원칙들은 모든 단계에서 반드시 준수되어야 합니다.**

### 원칙 1: 일일 주기적 실행

- 환경스캐닝은 **매일 한 번** 정해진 시간에 실행
- 일관된 모니터링으로 변화의 연속성 추적

### 원칙 2: 과거 보고서 우선 확인

- 새로운 스캐닝 수행 전 **반드시 기존 보고서 DB를 먼저 검토**
- 축적된 신호 히스토리를 기반으로 맥락 파악
- 파일 위치: `reports/archive/` 디렉토리

### 원칙 3: 중복 신호 제외

- 이미 탐지/보고된 신호는 **스캐닝 결과에서 자동 제외**
- 중복 판단 기준: 동일 출처, 유사 내용(의미적 유사도 85% 이상), 동일 행위자
- 기존 신호의 **상태 변화**가 있는 경우에만 업데이트로 포함

### 원칙 4: 신규 신호만 탐지

- 오직 **새롭게 나타난 신호**만 최종 보고서에 포함
- "새로움"의 기준: 지난 7일 내 최초 등장, 기존 DB에 미등록
- 기존 신호의 강화/약화 추세는 별도 섹션에서 추적

### [Advanced] 원칙 5: 과학적 근거 기반 임계값

- 학술 연구 기반 다단계 유사도 임계값 적용
- URL 정확 매칭 (100%) → 문자열 유사도 (90%) → 의미적 유사도 (80%) → 엔티티 매칭 (85%)
- SBERT 모델 활용하여 의미적 뉘앙스 캡처

### [Advanced] 원칙 6: 인간-AI 협업 품질 관리

- 모든 (human) 검토 단계에서 명확한 품질 기준 적용
- AI 출력의 Explainability 보장
- 피드백 루프를 통한 지속적 시스템 학습

---

## Phase 1: Research (정보 수집)

### 1. 기존 보고서 로딩

- **Agent**: `@archive-loader`
- **Task**: 과거 스캐닝 보고서 및 신호 DB 로딩
- **Input**: `reports/archive/*.json`, `signals/database.json`
- **Output**: `context/previous-signals.json`
- **Note**: 최근 90일 데이터 우선 로딩, 중복 체크용 인덱스 생성

### 2. 다중 소스 스캐닝

- **Agent**: `@multi-source-scanner`
- **Task**: 정의된 도메인별 정보 수집
- **Sources**:
  - 학술 논문 (Google Scholar, arXiv, SSRN)
  - 특허 정보 (Google Patents, KIPRIS)
  - 정책/규제 동향 (정부 보도자료, 국제기구)
  - 기술 블로그/리포트 (Medium, TechCrunch, 연구기관)
- **Domains**: STEEPs 분류 (Social, Technological, Economic, Environmental, Political, spiritual)
- **Output**: `raw/daily-scan-{date}.json`

#### [Advanced] AI/ML 기반 자동화 강화

**ML 기반 자동 키워드 추출**:
- TF-IDF + BERT embedding 활용
- 약한 신호 후보 자동 식별

**토픽 모델링 자동 그룹핑**:
- Advanced topic modeling으로 신호 클러스터링
- Automated topic labeling으로 카테고리 제안

**성장 패턴 학습**:
- 10년 히스토리 데이터 기반 신호 성장 예측
- Graph Convolutional Network (GCN) 적용

**출처**:
- [WISDOM Framework (arXiv 2024)](https://arxiv.org/html/2409.15340v1)
- [Automated weak signal detection using GCN](https://www.sciencedirect.com/science/article/pii/S0016328723001064)

### 3. 중복 필터링

- **Agent**: `@deduplication-filter`
- **Task**: 기존 신호 DB와 비교하여 중복 제거
- **Method**:
  - 출처 URL 정확 매칭
  - 제목/내용 의미적 유사도 분석 (threshold: 85%)
  - 핵심 엔티티(행위자, 기술, 정책명) 매칭
- **Input**: `raw/daily-scan-{date}.json`, `context/previous-signals.json`
- **Output**: `filtered/new-signals-{date}.json`
- **Log**: `logs/duplicates-removed-{date}.log`

#### [Advanced] Multi-Stage Cascade 필터링

**4단계 필터링 프로세스**:

**Stage 1: URL 정확 매칭**
- Threshold: 100%
- Method: URL normalization + exact matching
- Action: 동일 URL → 즉시 중복 판정

**Stage 2: 문자열 유사도**
- Threshold: 90%
- Method: Jaro-Winkler algorithm
- Action: >0.9 → 중복으로 표시

**Stage 3: 의미적 유사도**
- Threshold: 80%
- Method: TF-IDF 또는 SBERT 모델
- Action: >0.8 → 근접 중복(near-duplicate)으로 표시

**Stage 4: 엔티티 매칭**
- Threshold: 85%
- Method: Named Entity Recognition (NER)
- Criteria: 동일 행위자 + 동일 기술명 + 동일 정책명
- Action: >0.85 → 맥락적 중복으로 표시

**과학적 근거**:
- Jaccard Coefficient (Stanford NLP): 0.9
- Cosine Similarity (학술 연구): 0.65-0.8
- SBERT 의미적 분석: 전통적 문자열 유사도를 넘어선 뉘앙스 캡처

**출처**:
- [Near-duplicates and shingling (Stanford)](https://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html)
- [Document Deduplication with LSH](https://mattilyra.github.io/2017/05/23/document-deduplication-with-lsh.html)
- [Evaluating Deduplication Techniques (arXiv)](https://arxiv.org/html/2410.01141)

### 4. (human) 필터링 결과 검토

- **Action**: 자동 필터링 결과 확인 및 예외 처리
- **Display**: 제거된 항목 중 재검토 필요 목록
- **Command**: `/review-filtering`
- **Optional**: 대부분의 경우 자동 진행 가능

#### [Advanced] AI 신뢰도 기반 검토 프로토콜

**AI 출력 정보**:
- 제거된 항목 목록 + 각 항목별 중복 판정 근거
- 신뢰도 점수 (0-1 scale)
- Explainable AI 근거 제시

**인간 검토 프로토콜**:
- ✅ AI 신뢰도 >0.9: 자동 승인
- ⚠️ AI 신뢰도 0.7-0.9: 샘플 검토 (10% 무작위)
- 🔴 AI 신뢰도 <0.7: 전수 검토 필요

**품질 메트릭스**:
- Precision (정밀도) = 올바르게 제거된 중복 / 전체 제거 항목
- Recall (재현율) = 올바르게 제거된 중복 / 실제 중복 총수
- F1 Score = 2 × (Precision × Recall) / (Precision + Recall)

**피드백 루프**:
- 인간이 수정한 항목 → AI 모델 재학습 데이터로 활용
- 주간 단위로 필터링 정확도 추적 및 임계값 재조정

---

## Phase 1.5: Real-Time Expert Validation (선택적)

> **🆕 신규 추가**: 대량 신호 발생 시 전문가 집단지성 활용

### 1.5. 실시간 델파이 검증

- **Agent**: `@realtime-delphi-facilitator`
- **Trigger**: 필터링 후 신규 신호 > 50개일 때 자동 활성화
- **Task**: 전문가 패널을 통한 신호 우선순위 실시간 검증

**프로세스**:
1. AI가 각 신호별 초기 평가 생성 (중요도, 긴급도, 영향도)
2. 전문가 패널에 실시간 피드백 요청 (48시간 응답 창)
3. Real-Time AI Delphi (RT-AID) 기법으로 의견 수렴 촉진
4. 의견 수렴도 자동 측정 및 합의 도출

**방법론**:
- Modified Delphi Technique 구조화된 라운드
- 생성형 AI를 지원 에이전트로 활용하여 수렴 가속화
- 제한된 전문가 샘플에서도 빠른 합의 도달

**Input**: `filtered/new-signals-{date}.json`
**Output**: `validated/expert-validated-signals-{date}.json`

**효과**:
- 전문가 피드백 수렴 시간: 월 단위 → 일 단위 (2-3일)
- AI 단독 판단 대비 의사결정 신뢰도 30% 향상

**출처**:
- [Real-Time AI Delphi (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S0016328725001661)
- [Moving Toward Anticipatory Futures Intelligence](https://www.houstonforesight.org/moving-toward-an-anticipatory-futures-intelligence-system/)

---

## Phase 2: Planning (분석 및 구조화)

### 5. 신호 분류 및 구조화

- **Agent**: `@signal-classifier`
- **Task**: 신규 신호를 표준 템플릿으로 구조화
- **Template Fields**:
  ```
  - ID: 고유 식별자
  - Category: STEEPs 분류
  - Title: 신호 제목
  - Date: 날짜
  - Keyword: 핵심어
  - Fact & Score: 정성적 사실(fact), 정량적 사실(Score)
  - Description: 상세 설명
  - Inference: 가정, 추론
  - Writer Opinion: 저자의 견해
  - Critical thinking: 비판적 사고로 분석
  - Status: 현재 상태 (emerging/developing/mature)
  - Stage of development: 발전 단계
  - Technological architecture: 기술 구조
  - Application area: 적용 영역(가능성)
  - Market size: 시장 규모 가능성
  - Expansion of imagination: 상상력 확장
  - Actors, Stakeholder: 관련 행위자, 이해 관계자
  - First_Detected: 최초 탐지일
  - Source: 출처 정보
  - Leading_Indicator: 선행 지표
  - Significance: 중요도 점수 (1-5)
  - Accuracy: 정확성 점수 (1-5)
  - Confidence: 신뢰도 점수 (1-5)
  - Innovative capacity: 혁신성 점수 (1-5)
  ```
- **Output**: `structured/classified-signals-{date}.json`

#### [Advanced] STEEPs 분류 체계 상세

> **절대 기준**: STEEPs는 고유의 분류 체계이며 변경하지 않음

**STEEPs 6개 카테고리** (절대 유지):

**S - Social (사회)**
- spiritual 항목을 제외한 상식적 사회적 이슈
- 인구통계 변화, 교육/문화 변화, 라이프스타일 트렌드
- 세대 간 격차, 도시화, 이민, 소득 불평등, 사회 운동, 노동 시장

**T - Technological (기술)**
- 신기술 출현, 기술 융합, 디지털 전환, R&D 혁신
- AI, 생명공학, 나노기술, 양자컴퓨팅, 블록체인, 메타버스

**E - Economic (경제)**
- 경제 구조 변화, 시장 역학, 금융/무역 동향, 비즈니스 모델 혁신
- 글로벌 공급망, 통화정책, 인플레이션, 신흥시장, 플랫폼 경제

**E - Environmental (환경)**
- 기후 변화, 자원 고갈, 생태계 파괴, 지속가능성 이슈
- 탄소중립, 재생에너지, 생물다양성, 물 부족, 극단적 기후 현상

**P - Political (정치, 법, 제도)**
- 정책 변화, 규제 동향, 지정학적 리스크, 국제 관계
- **법률, 법제도, 제도적 변화, 입법, 사법, 행정**
- 다자주의/양자주의, 민주주의/권위주의, 무역전쟁, 국제 갈등

**s - spiritual (영적, 윤리, 대중심리)**
- 종교적 변화, 세계관 전환, 의미 추구 경향
- **윤리적 이슈, 대중심리, 집단 정서, 가치관 변화**
- 영성 부활, 탈종교화, 포스트휴먼, 실존적 불안, 의미 위기
- AI 윤리, 생명윤리, 데이터 윤리, 사회적 합의

**카테고리 구분 원칙**:
- **Political (P)**: 정치 + 법 + 제도 (권력, 통치, 법체계)
- **spiritual (s)**: 영적 + 윤리 + 대중심리 (가치, 의미, 윤리)
- **Social (S)**: spiritual 제외한 일반 사회 이슈 (인구, 교육, 노동)
- spiritual(s) 카테고리는 한국/아시아 맥락의 고유 추가
- PEST/PESTLE 등 기존 프레임워크와 차별화

### 6. 영향도(Potential_Impact) 분석

- **Agent**: `@impact-analyzer`
- **Task**: 각 신호의 잠재적 영향 평가 (Futures Wheel 방식)
- **Analysis**:
  - 1차 영향 (직접적 결과)
  - 2차 영향 (파생 효과)
  - 교차 영향 (다른 신호와의 상호작용)
- **Output**: `analysis/impact-assessment-{date}.json`

#### [Advanced] Probabilistic Cross-Impact Analysis

**방법론 강화**: Futures Wheel → **Probabilistic Cross-Impact Matrix + Bayesian Network**

**3단계 분석 프로세스**:

**Step 6.1: Impact Identification**
- 각 신호별 직접 영향 (1차) 식별
- 파생 효과 (2차) 식별
- 기존 Futures Wheel 방식 유지

**Step 6.2: Cross-Impact Matrix 생성**
- N×N 매트릭스 생성 (N = 신호 개수)
- 신호 i가 신호 j 발생 확률에 미치는 영향 점수화
- 점수 범위: -5 (강한 억제) ~ +5 (강한 촉진)
- 불확실성 요인에 대한 확률적 진술 수용

**Step 6.3: Bayesian Network 구축**
- Cross-impact 매트릭스를 베이지안 네트워크로 변환
- 최적화 모델 시리즈 해결
- 시나리오별 발생 확률 계산
- 가장 가능성 높은 미래 경로 식별

**추가 출력**:
- `analysis/cross-impact-matrix-{date}.json` 🆕
- `analysis/scenario-probabilities-{date}.json` 🆕

**원조 방법론**: Theodore J. Gordon & Olaf Helmer (1966)

**출처**:
- [Probabilistic cross-impact methodology (Futures & Foresight Science 2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/ffo2.165)
- [Cross impact analysis - Wikipedia](https://en.wikipedia.org/wiki/Cross_impact_analysis)

### 7. 우선순위 결정

- **Agent**: `@priority-ranker`
- **Task**: 신호 우선순위 산정
- **Criteria**:
  - 영향도 (Impact): 40%
  - 발생 가능성 (Probability): 30%
  - 긴급도 (Urgency): 20%
  - 신규성 (Novelty): 10%
- **Output**: `analysis/priority-ranked-{date}.json`

### 7.5. 시나리오 빌더 (선택적)

> **🆕 신규 추가**: QUEST 방법론 기반 시나리오 자동 생성

- **Agent**: `@scenario-builder`
- **Phase**: Phase 2 (Planning)
- **Position**: Step 7과 Step 8 사이
- **Task**: 우선순위 상위 신호를 조합하여 플러서블 시나리오 자동 생성

**QUEST 프로세스 매핑**:
- QUEST Phase 3 (Option Identification) 구현
- 우선순위 신호 묶음 → 전략적 옵션 시나리오 변환

**방법**:
1. Cross-impact matrix 기반 신호 묶음 식별
2. 각 묶음별 미래 경로 narrative 작성
3. 시나리오별 발생 확률 제시 (베이지안 네트워크 기반)
4. 3-5개의 플러서블 시나리오 생성

**시나리오 유형**:
- Best Case: 긍정적 신호 조합
- Worst Case: 부정적 신호 조합
- Most Likely: 확률이 가장 높은 경로
- Wild Card: 저확률-고영향 조합

**Output**: `scenarios/scenarios-{date}.json`

**QUEST 표준 프로세스**:
1. Preparation Phase → workflow Step 1-2
2. Divergent Planning Phase → workflow Step 5-6
3. Option Identification Phase → **workflow Step 7.5** 🆕
4. Scenario Development Phase → workflow Step 8, 12

**출처**:
- [QUEST analysis process (Studocu)](https://www.studocu.com/in/document/teerthanker-mahaveer-university/innovation-and-entrepreneurship/environmental-scanning-technique/107908397)
- [Using QUEST analysis (Firmbee)](https://firmbee.com/the-quest-analysis)

### 8. (human) 분석 결과 검토

- **Action**: AI 분석 결과의 품질 및 적절성 검토
- **Display**: 상위 10개 우선순위 신호 상세 내용
- **Input**: 분류 오류 수정, 중요도 조정, 추가 코멘트
- **Command**: `/review-analysis`

#### [Advanced] Explainability 기반 검토 프로토콜

**AI 출력 정보**:
- 신호 분류 (STEEPs - 절대 기준)
- 영향도 평가 (1-5)
- 우선순위 점수
- **설명 가능한 근거** (Explainable AI)

**Explainability Check**:
- [ ] 각 신호별 AI의 분류 근거 명시
- [ ] Cross-impact 연결 시각화 제공
- [ ] 우선순위 산정 공식 투명화
- [ ] 베이지안 네트워크 경로 표시

**Disagreement Resolution**:
- 인간과 AI 의견 불일치 항목 하이라이트
- 불일치도 >30%일 경우 전문가 패널 소집 (Phase 1.5 재실행)
- Modified Delphi로 합의 도출

**품질 메트릭스**:
- Classification Accuracy: 분류 정확도
- Inter-rater Reliability: 인간-AI 간 일치도 (Cohen's Kappa)
- Kappa Score: 우연을 초과한 일치도

**출처**:
- [Evaluating Human-AI Collaboration Framework (arXiv)](https://arxiv.org/html/2407.19098v2)

---

## Phase 3: Implementation (보고서 생성)

### 9. 신호 DB 업데이트

- **Agent**: `@database-updater`
- **Task**: 신규 신호를 마스터 DB에 등록
- **Actions**:
  - 신규 신호 추가
  - 기존 신호 상태 업데이트 (발전/약화 추세)
  - 히스토리 로그 기록
- **Output**: `signals/database.json` (업데이트)

### 10. 일일 보고서 생성

- **Agent**: `@report-generator`
- **Task**: 환경스캐닝 일일 보고서 작성
- **Report Sections**:
  ```
  1. Executive Summary
     - 오늘의 핵심 발견 (Top 3 신호)
     - 주요 변화 요약

  2. 신규 탐지 신호 (NEW)
     - STEEPs 카테고리별 신규 신호 목록
     - 각 신호별 상세 분석

  3. 기존 신호 업데이트
     - 상태 변화가 있는 기존 신호
     - 강화/약화 추세 분석

  4. 패턴 및 연결고리
     - 신호 간 교차 영향
     - 떠오르는 패턴/테마

  5. 전략적 시사점
     - 의사결정자를 위한 권고사항
     - 모니터링 강화 필요 영역

  6. 부록
     - 전체 신호 목록
     - 출처 및 참고자료
  ```
- **Output**: `reports/daily/environmental-scan-{date}.md`

#### [Advanced] 시나리오 기반 보고서 확장

**추가 섹션** (Step 7.5 시나리오 빌더 활성화 시):

```
7. 플러서블 시나리오 (선택)
   - Best Case 시나리오 (발생 확률 %)
   - Worst Case 시나리오 (발생 확률 %)
   - Most Likely 시나리오 (발생 확률 %)
   - Wild Card 시나리오 (발생 확률 %)
   - 각 시나리오별 전략적 대응 방안

8. Cross-Impact 분석 (선택)
   - 주요 신호 간 상호작용 매트릭스
   - 베이지안 네트워크 시각화
   - 촉진/억제 관계 분석
```

### 11. 아카이브 및 알림

- **Agent**: `@archive-notifier`
- **Task**: 보고서 아카이빙 및 관련자 알림
- **Actions**:
  - 보고서를 `reports/archive/`로 복사
  - 신호 스냅샷 저장
  - (선택) 이메일/Slack 알림 발송
- **Output**: 아카이브 완료 로그

### 12. (human) 최종 보고서 승인

- **Action**: 최종 보고서 검토 및 배포 승인
- **Display**: 생성된 보고서 전문
- **Command**: `/approve-report` 또는 `/request-revision "피드백"`

#### [Advanced] 체계적 승인 프로토콜

**완전성 체크 (Completeness Check)**:
- [ ] 모든 섹션 포함 확인
- [ ] 신규 신호 개수 검증 (필터링 로그와 대조)
- [ ] 출처 링크 유효성 확인 (자동 링크 검증)
- [ ] 시사점의 실행 가능성 평가

**어조 및 스타일 체크 (Tone & Style Check)**:
- [ ] 객관적 어조 유지 (과장/축소 없음)
- [ ] 사실 기반 서술 (추측성 표현 제거)
- [ ] 의사결정자 수준에 맞는 언어 (전문 용어 적절성)

**승인 기준**:
- ✅ **Approve**: 모든 체크리스트 통과 → 배포
- 🔄 **Request Revision**: 특정 섹션 수정 요청 → Step 10 재실행
- 🔴 **Reject**: 전면 재작성 필요 → Phase 2부터 재시작

**출처**:
- [Complementarity in human-AI collaboration](https://www.tandfonline.com/doi/full/10.1080/0960085X.2025.2475962)

---

## Claude Code Configuration

### Sub-agents

```yaml
agents:
  archive-loader:
    description: "과거 보고서 및 신호 DB 로딩"
    tools: [file-read, json-parser]
    prompt_prefix: |
      기존 환경스캐닝 데이터를 로딩합니다.
      중복 체크를 위한 인덱스를 생성하세요.

  multi-source-scanner:
    description: "다중 소스에서 정보 수집"
    tools: [web-search, web-fetch, rss-reader, news-api]
    max_tokens: 8000
    prompt_prefix: |
      STEEPs 프레임워크에 따라 다양한 소스에서
      미래 변화의 신호를 탐지하세요.

    # [Advanced] AI/ML Enhancement
    enhancement:
      ml_keyword_extraction:
        method: "TF-IDF + BERT embedding"
        purpose: "자동 키워드 추출 및 약한 신호 후보 식별"

      topic_modeling:
        method: "Advanced topic modeling (WISDOM framework)"
        purpose: "신호 자동 그룹핑 및 라벨링"

      growth_pattern_learning:
        method: "Graph Convolutional Network (GCN)"
        data: "10년 히스토리 기반"
        purpose: "신호 성장 패턴 예측"

  deduplication-filter:
    description: "중복 신호 필터링"
    tools: [semantic-similarity, entity-extractor]
    prompt_prefix: |
      핵심 원칙을 준수하세요:
      - 기존 DB에 있는 신호는 반드시 제외
      - 의미적 유사도 85% 이상이면 중복으로 판정
      - 동일 출처 URL은 즉시 제외

    # [Advanced] Multi-Stage Cascade
    enhancement:
      method: "Multi-Stage Cascade Filtering"
      stages:
        stage_1_url_exact:
          threshold: 1.0
          method: "URL normalization + exact matching"

        stage_2_string_similarity:
          threshold: 0.9
          method: "Jaro-Winkler"

        stage_3_semantic_similarity:
          threshold: 0.8
          method: "TF-IDF or SBERT"

        stage_4_entity_matching:
          threshold: 0.85
          method: "Named Entity Recognition (NER)"

      quality_metrics:
        - "Precision, Recall, F1 Score"
        - "주간 정확도 추적"

      feedback_loop:
        - "인간 수정 항목 → AI 재학습 데이터"

  signal-classifier:
    description: "신호 분류 및 구조화"
    prompt_prefix: |
      각 신호를 표준 템플릿에 맞게 구조화하세요.
      STEEPs 분류와 중요도 평가를 포함합니다.

    # [Advanced] STEEPs Framework (절대 기준)
    enhancement:
      category_system: "STEEPs (6개 카테고리 - 고유 분류)"
      categories:
        S_Social: "인구통계, 교육/문화, 라이프스타일, 세대간격차, 노동시장 (spiritual 제외)"
        T_Technological: "신기술, 융합, 디지털전환, R&D, AI/생명공학"
        E_Economic: "경제구조, 시장, 금융/무역, 비즈니스모델, 플랫폼경제"
        E_Environmental: "기후, 자원, 생태계, 지속가능성, 탄소중립"
        P_Political: "정치, 정책, 규제, 법률, 법제도, 제도변화, 지정학, 국제관계"
        s_spiritual: "종교, 세계관, 의미추구, 영성, 윤리(AI윤리/생명윤리), 대중심리, 집단정서"

  impact-analyzer:
    description: "영향도 분석 (Futures Wheel)"
    prompt_prefix: |
      각 신호의 1차, 2차 영향을 분석하고
      다른 신호와의 교차 영향을 평가하세요.

    # [Advanced] Probabilistic Cross-Impact
    enhancement:
      method: "Probabilistic Cross-Impact Matrix + Bayesian Network"
      steps:
        impact_identification:
          - "1차 영향 (직접 결과)"
          - "2차 영향 (파생 효과)"

        cross_impact_matrix:
          - "N×N 매트릭스 생성"
          - "점수 범위: -5 (억제) ~ +5 (촉진)"

        bayesian_network:
          - "매트릭스 → 베이지안 네트워크 변환"
          - "시나리오 확률 계산"

      additional_output:
        - "cross-impact-matrix-{date}.json"
        - "scenario-probabilities-{date}.json"

  priority-ranker:
    description: "우선순위 결정"
    prompt_prefix: |
      영향도(40%), 발생가능성(30%), 긴급도(20%),
      신규성(10%) 기준으로 우선순위를 산정하세요.

  database-updater:
    description: "신호 DB 업데이트"
    tools: [file-write, json-parser]

  report-generator:
    description: "일일 보고서 생성"
    temperature: 0.3

    # [Advanced] Scenario-based Reporting
    enhancement:
      optional_sections:
        - "플러서블 시나리오 (Step 7.5 활성화 시)"
        - "Cross-Impact 분석"

  archive-notifier:
    description: "아카이빙 및 알림"
    tools: [file-copy, notification]

  # [Advanced] New Agents
  realtime-delphi-facilitator:
    description: "실시간 델파이 전문가 검증" # 🆕
    phase: "Phase 1.5"
    trigger: "필터링 후 신규 신호 > 50개"
    tools: [expert-panel-api, consensus-tracker]
    method: "Real-Time AI Delphi (RT-AID)"
    output: "validated/expert-validated-signals-{date}.json"
    prompt_prefix: |
      전문가 패널과 AI를 통합하여 신호 검증을 수행합니다.
      48시간 내 의견 수렴을 목표로 합니다.

  scenario-builder:
    description: "QUEST 기반 시나리오 생성" # 🆕
    phase: "Phase 2"
    position: "Step 7.5"
    method: "QUEST Phase 3 (Option Identification)"
    tools: [cross-impact-matrix, bayesian-network]
    output: "scenarios/scenarios-{date}.json"
    prompt_prefix: |
      우선순위 신호를 조합하여 3-5개의 플러서블 시나리오를 생성합니다.
      Best/Worst/Most Likely/Wild Card 시나리오를 포함하세요.
```

### Slash Commands

```yaml
commands:
  /run-daily-scan:
    description: "일일 환경스캐닝 워크플로우 전체 실행"
    action: |
      1단계부터 순차적으로 실행합니다.
      (human) 단계에서 자동 일시정지합니다.

  /review-filtering:
    description: "중복 필터링 결과 검토"
    action: |
      제거된 항목 목록을 표시하고
      예외 처리가 필요한 항목을 선택할 수 있습니다.

  /review-analysis:
    description: "분석 결과 검토 및 수정"
    action: |
      상위 우선순위 신호를 표시하고
      분류 오류 수정 및 코멘트를 입력받습니다.

  /approve-report:
    description: "최종 보고서 승인 및 배포"

  /request-revision:
    description: "보고서 수정 요청"
    args:
      - name: feedback
        type: string
        required: true

  /show-status:
    description: "현재 워크플로우 진행 상태 확인"

  /force-include:
    description: "중복으로 제외된 신호를 강제 포함"
    args:
      - name: signal_id
        type: string
        required: true

  # [Advanced] New Commands
  /trigger-delphi:
    description: "실시간 델파이 검증 수동 실행" # 🆕
    action: |
      Phase 1.5를 수동으로 활성화합니다.
      전문가 패널에 검증 요청을 발송합니다.

  /generate-scenarios:
    description: "시나리오 빌더 수동 실행" # 🆕
    action: |
      Step 7.5를 수동으로 활성화합니다.
      플러서블 시나리오를 생성합니다.

  /quality-report:
    description: "품질 메트릭스 보고서 생성" # 🆕
    action: |
      AI 모델 성능 지표 추적
      인간-AI 협업 품질 분석
      주간/월간 개선 추이 표시
```

### Required Skills

- `xlsx` - 데이터 분석 스프레드시트 (선택)

### MCP Servers

```yaml
servers:

  scholar-api:
    description: "학술 논문 검색 (Google Scholar, arXiv)"

  patent-api:
    description: "특허 정보 검색"

  notification:
    description: "알림 발송 (Email, Slack)"

  # [Advanced] New MCP Servers
  expert-panel-api:
    description: "전문가 패널 관리 및 실시간 델파이 지원" # 🆕

  ml-models:
    description: "SBERT, GCN, WISDOM 모델 API" # 🆕
```

### Directory Structure

```
environmental-scanning/
├── reports/
│   ├── daily/                    # 일일 보고서
│   │   └── environmental-scan-{date}.md
│   └── archive/                  # 아카이브
│       └── {year}/{month}/
├── signals/
│   ├── database.json             # 마스터 신호 DB
│   └── snapshots/                # 일일 스냅샷
├── raw/                          # 원시 수집 데이터
├── filtered/                     # 필터링된 데이터
├── validated/                    # [Advanced] 전문가 검증 데이터 🆕
├── structured/                   # 구조화된 데이터
├── analysis/                     # 분석 결과
├── scenarios/                    # [Advanced] 시나리오 데이터 🆕
├── context/                      # 컨텍스트 데이터
├── logs/                         # 실행 로그
│   └── quality-metrics/          # [Advanced] 품질 메트릭스 🆕
└── config/
    ├── domains.yaml              # 스캐닝 도메인 설정
    ├── sources.yaml              # 데이터 소스 설정
    ├── thresholds.yaml           # 임계값 설정
    └── ml-models.yaml            # [Advanced] ML 모델 설정 🆕
```

### Execution Pattern

```yaml
execution:
  mode: sequential
  auto_pause_on: human
  schedule: "0 6 * * *"  # 매일 오전 6시

error_handling:
  on_agent_failure:
    action: retry
    max_attempts: 3

  on_source_unavailable:
    action: skip_and_log
    continue: true

  on_validation_failure:
    action: notify_and_pause

# [Advanced] Performance Targets
performance_targets:
  duplicate_detection_accuracy: ">95%"
  processing_time_reduction: "30% vs baseline"
  signal_detection_speed: "2x vs manual"
  expert_feedback_time: "<3 days"
```

---

## 품질 체크리스트

실행 완료 후 다음 항목을 확인:

- [ ] 과거 보고서 DB가 정상 로딩되었는가?
- [ ] 중복 신호가 완전히 제거되었는가?
- [ ] 신규 신호만 최종 보고서에 포함되었는가?
- [ ] STEEP 분류가 정확한가?
- [ ] 영향도 분석이 충분한가?
- [ ] 보고서 포맷이 표준을 따르는가?
- [ ] 신호 DB가 정상 업데이트되었는가?
- [ ] 아카이브가 완료되었는가?

### [Advanced] 확장 품질 체크리스트

**AI/ML 성능**:
- [ ] 중복 필터링 정확도 >95% 달성?
- [ ] 4단계 cascade 필터링 정상 작동?
- [ ] SBERT 의미적 유사도 분석 정상?
- [ ] 피드백 루프 데이터 수집 완료?

**분류 및 분석**:
- [ ] STEEPs 6개 카테고리 모두 커버? (절대 기준 유지)
- [ ] spiritual(s) 신호 적절히 포착?
- [ ] Cross-Impact Matrix 생성 완료?
- [ ] Bayesian Network 시나리오 확률 계산?

**전문가 검증** (Phase 1.5 활성화 시):
- [ ] 전문가 패널 응답률 >70%?
- [ ] 의견 수렴 48시간 내 완료?
- [ ] AI-전문가 일치도 >80%?

**시나리오 생성** (Step 7.5 활성화 시):
- [ ] 3-5개 플러서블 시나리오 생성?
- [ ] 각 시나리오 발생 확률 명시?
- [ ] Best/Worst/Most Likely/Wild Card 포함?

**인간-AI 협업**:
- [ ] AI 출력에 Explainability 근거 포함?
- [ ] 인간 검토 프로토콜 준수?
- [ ] 품질 메트릭스 추적 완료?

---

## [Advanced] AI/ML Integration Framework

### Machine Learning 모델 통합

**WISDOM Framework**:
- Advanced topic modeling
- Automated topic labeling
- Weak signal extraction
- **적용 단계**: Step 2 (@multi-source-scanner)

**Graph Convolutional Network (GCN)**:
- 키워드 네트워크 클러스터링
- 신호 성장 패턴 학습 (10년 히스토리)
- **적용 단계**: Step 2 (@multi-source-scanner)

**SBERT (Sentence-BERT)**:
- 의미적 유사도 분석
- 전통적 문자열 매칭을 넘어선 뉘앙스 캡처
- **적용 단계**: Step 3 (@deduplication-filter)

**Deep Neural Networks**:
- 불규칙 패턴 탐지
- 불연속성 연구
- Outlier distribution 분석
- **적용 단계**: Step 2, Step 6

**참고 문헌**:
- WISDOM: https://arxiv.org/html/2409.15340v1
- GCN-based detection: https://www.sciencedirect.com/science/article/pii/S0016328723001064
- Innovation signals ML: https://pmc.ncbi.nlm.nih.gov/articles/PMC10090756/

---

## [Advanced] Human-AI Collaboration Quality Framework

### 지속적 개선 사이클

**주간 리뷰** (Weekly Review):
- AI 모델 성능 지표 추적
  * 중복 필터링: Precision, Recall, F1
  * 신호 분류: Classification Accuracy
  * 인간-AI 일치도: Cohen's Kappa
- 인간 피드백 패턴 분석
- 오류 유형 카테고리화

**월간 캘리브레이션** (Monthly Calibration):
- AI 임계값 재조정
  * URL 매칭: 1.0 유지
  * 문자열 유사도: 0.9 조정 검토
  * 의미적 유사도: 0.8 조정 검토
  * 엔티티 매칭: 0.85 조정 검토
- 전문가 패널과 케이스 스터디 세션
- 워크플로우 병목 지점 개선

**분기별 감사** (Quarterly Audit):
- 전체 시스템 품질 감사
- 외부 전문가 검증
- 벤치마킹 및 베스트 프랙티스 적용
- 절대 목표 달성도 평가: "가장 빨리 catchup" 성과 측정

**참고 문헌**:
- Human-AI Collaboration Validation: https://www.tandfonline.com/doi/full/10.1080/10447318.2025.2543997
- Evaluation Framework: https://arxiv.org/html/2407.19098v2
- Multiagent Quality Control: https://pmc.ncbi.nlm.nih.gov/articles/PMC12360800/

---

## [Advanced] Implementation Roadmap

### Phase 1 (즉시 구현) - 속도 향상

**우선순위 1: Multi-Stage Duplicate Detection**
- 현재 85% 단일 임계값 → 4단계 cascade
- 예상 효과: 정확도 15% 향상, 처리 시간 30% 단축
- 구현 난이도: 중
- 소요 시간: 2-3주

**우선순위 2: STEEPs 분류 정밀화**
- STEEPs 6개 카테고리 상세 가이드라인 수립
- spiritual(s) 카테고리 탐지 정확도 향상
- 예상 효과: 분류 일관성 15% 향상
- 구현 난이도: 하
- 소요 시간: 1주

### Phase 2 (3개월 내) - 품질 향상

**우선순위 3: AI 기반 약한 신호 자동 탐지**
- WISDOM 프레임워크 또는 GCN 모델 구현
- @multi-source-scanner 자동화 수준 향상
- 예상 효과: 신규 신호 탐지 속도 2배
- 구현 난이도: 상
- 소요 시간: 8-12주

**우선순위 4: Probabilistic Cross-Impact Analysis**
- @impact-analyzer에 베이지안 네트워크 추가
- 시나리오 확률 자동 계산
- 예상 효과: 영향도 평가 신뢰도 25% 향상
- 구현 난이도: 상
- 소요 시간: 6-8주

### Phase 3 (6개월 내) - 집단지성 강화

**우선순위 5: Real-Time AI Delphi 통합**
- 새로운 Phase 1.5 추가
- 전문가 패널 실시간 검증 메커니즘
- 예상 효과: 피드백 수렴 시간 월 → 일 단위
- 구현 난이도: 상
- 소요 시간: 10-12주

**우선순위 6: Human-AI 협업 품질 관리**
- 3개 (human) 단계별 검증 프로토콜
- 피드백 루프 기반 지속적 개선
- 예상 효과: 전체 시스템 신뢰도 30% 향상
- 구현 난이도: 중
- 소요 시간: 6-8주

### Phase 4 (9개월 내) - 시나리오 역량 강화

**우선순위 7: QUEST 기반 시나리오 빌더**
- 새로운 @scenario-builder agent 추가
- Step 7.5 구현
- 예상 효과: 전략적 시사점 구체성 40% 향상
- 구현 난이도: 중
- 소요 시간: 4-6주

---

## 학술 참고문헌 (Academic References)

### Environmental Scanning & Weak Signals
1. [Environmental scanning, futures research, strategic foresight](https://www.researchgate.net/publication/236897718_Environmental_scanning_futures_research_strategic_foresight_and_organizational_future_orientation_a_review_integration_and_future_research_directions)
2. [Environmental Scanning: A Look to the Future - 2025](https://onlinelibrary.wiley.com/doi/full/10.1002/ev.20633)
3. [How to Do Horizon Scanning](https://www.futuresplatform.com/blog/how-to-horizon-scanning-guideline)

### Millennium Project & STEEP
4. [Futures Research Methodology V3.0](https://www.millennium-project.org/publications/futures-research-methodology-version-3-0-2/)
5. [Using STEEP to Frame Horizon Scanning](https://www.insightandforesight.com.au/blog-foresights/using-steep-to-frame-your-horizon-scanning)

### AI & Machine Learning
6. [WISDOM Framework (arXiv 2024)](https://arxiv.org/html/2409.15340v1)
7. [Automated weak signal detection using GCN](https://www.sciencedirect.com/science/article/pii/S0016328723001064)
8. [Innovation signals: leveraging ML](https://pmc.ncbi.nlm.nih.gov/articles/PMC10090756/)

### Real-Time Delphi
9. [Real-Time AI Delphi (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S0016328725001661)
10. [Moving Toward Anticipatory Futures Intelligence](https://www.houstonforesight.org/moving-toward-an-anticipatory-futures-intelligence-system/)

### Cross-Impact Analysis
11. [Probabilistic cross-impact methodology (2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/ffo2.165)
12. [Cross impact analysis - Wikipedia](https://en.wikipedia.org/wiki/Cross_impact_analysis)

### Semantic Similarity
13. [Near-duplicates and shingling - Stanford](https://nlp.stanford.edu/IR-book/html/htmledition/near-duplicates-and-shingling-1.html)
14. [Document Deduplication with LSH](https://mattilyra.github.io/2017/05/23/document-deduplication-with-lsh.html)
15. [Evaluating Deduplication Techniques (arXiv)](https://arxiv.org/html/2410.01141)

### QUEST Methodology
16. [QUEST analysis process](https://www.studocu.com/in/document/teerthanker-mahaveer-university/innovation-and-entrepreneurship/environmental-scanning-technique/107908397)
17. [Using QUEST to study market changes](https://firmbee.com/the-quest-analysis)

### Human-AI Collaboration
18. [Generative AI in Human-AI Collaboration](https://www.tandfonline.com/doi/full/10.1080/10447318.2025.2543997)
19. [Evaluating Human-AI Collaboration](https://arxiv.org/html/2407.19098v2)
20. [Complementarity in human-AI collaboration](https://www.tandfonline.com/doi/full/10.1080/0960085X.2025.2475962)

---

## Version History

**Version 1.0 (Enhanced)** - 2026-01-29
- 기존 workflow.md 기반 (절대 기준 유지)
- 7개 영역 전문가급 보강 추가:
  1. AI/ML 기반 약한 신호 자동 탐지 기술
  2. 실시간 델파이와 집단지성 강화
  3. 의미적 유사도 임계값 과학적 근거
  4. Cross-Impact Analysis 자동화
  5. QUEST 프로세스 정밀화
  6. 인간-AI 협업 품질 관리 체계
- Phase 1.5, Step 7.5 추가
- STEEPs (6개 카테고리) 절대 기준 유지
- 절대 목표 불변 유지

**Base Version** - workflow.md
- 12단계 workflow
- STEEPs (6개 카테고리 - 고유 분류)
- 4개 핵심 원칙
- 7개 sub-agents

---

**📌 Note**: 이 문서는 `workflow.md`의 모든 내용을 보존하면서 최신 학술 연구와 전문가급 방법론을 추가한 확장 버전입니다. 절대 목표인 "전 세계에서 가장 빨리 catchup"은 모든 단계와 기능에 계속 적용됩니다.
