# Environmental Scanning Workflow

미래 연구(Futures Research)를 위한 환경스캐닝 시스템: 변화의 조기 징후(약한 신호, weak signals)를 체계적으로 탐지하고 분석하여 전략적 의사결정을 지원하는 AI 자동화 워크플로우.

## Overview

- **Input**: 뉴스, 학술DB, 특허, 보고서, RSS 피드, 전문가 네트워크
- **Output**: 일일 환경스캐닝 보고서 (신규 신호 분석 포함)
- **Frequency**: Daily (매일 1회)

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

### 4. (human) 필터링 결과 검토

- **Action**: 자동 필터링 결과 확인 및 예외 처리
- **Display**: 제거된 항목 중 재검토 필요 목록
- **Command**: `/review-filtering`
- **Optional**: 대부분의 경우 자동 진행 가능

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

### 6. 영향도(Potential_Impact) 분석

- **Agent**: `@impact-analyzer`
- **Task**: 각 신호의 잠재적 영향 평가 (Futures Wheel 방식)
- **Analysis**:
  - 1차 영향 (직접적 결과)
  - 2차 영향 (파생 효과)
  - 교차 영향 (다른 신호와의 상호작용)
- **Output**: `analysis/impact-assessment-{date}.json`

### 7. 우선순위 결정

- **Agent**: `@priority-ranker`
- **Task**: 신호 우선순위 산정
- **Criteria**:
  - 영향도 (Impact): 40%
  - 발생 가능성 (Probability): 30%
  - 긴급도 (Urgency): 20%
  - 신규성 (Novelty): 10%
- **Output**: `analysis/priority-ranked-{date}.json`

### 8. (human) 분석 결과 검토

- **Action**: AI 분석 결과의 품질 및 적절성 검토
- **Display**: 상위 10개 우선순위 신호 상세 내용
- **Input**: 분류 오류 수정, 중요도 조정, 추가 코멘트
- **Command**: `/review-analysis`

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

  deduplication-filter:
    description: "중복 신호 필터링"
    tools: [semantic-similarity, entity-extractor]
    prompt_prefix: |
      핵심 원칙을 준수하세요:
      - 기존 DB에 있는 신호는 반드시 제외
      - 의미적 유사도 85% 이상이면 중복으로 판정
      - 동일 출처 URL은 즉시 제외

  signal-classifier:
    description: "신호 분류 및 구조화"
    prompt_prefix: |
      각 신호를 표준 템플릿에 맞게 구조화하세요.
      STEEPs 분류와 중요도 평가를 포함합니다.

  impact-analyzer:
    description: "영향도 분석 (Futures Wheel)"
    prompt_prefix: |
      각 신호의 1차, 2차 영향을 분석하고
      다른 신호와의 교차 영향을 평가하세요.

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

  archive-notifier:
    description: "아카이빙 및 알림"
    tools: [file-copy, notification]
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
├── structured/                   # 구조화된 데이터
├── analysis/                     # 분석 결과
├── context/                      # 컨텍스트 데이터
├── logs/                         # 실행 로그
└── config/
    ├── domains.yaml              # 스캐닝 도메인 설정
    ├── sources.yaml              # 데이터 소스 설정
    └── thresholds.yaml           # 임계값 설정
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

### 작업 검증 프로토콜 (v2.2.0)

위 체크리스트는 이제 **VEV (Verify-Execute-Verify) 프로토콜**에 의해 자동 검증됩니다:

- 모든 Step에 **사전 검증(Pre-Verify)** + **사후 검증(Post-Verify 3-Layer)** 적용
- 실패 시 **자동 재실행** (최대 2회)
- Phase 간 전환 시 **Pipeline Gate** 검증
- 결과는 `logs/verification-report-{date}.json`에 기록
- 상세 스펙: `env-scan-orchestrator.md` 참조
