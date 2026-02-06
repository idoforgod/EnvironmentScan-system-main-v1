# 설계 개선안: 실행 무결성 검증 시스템
# DESIGN PROPOSAL: Execution Integrity Verification System

**문서 버전**: 1.0.0
**작성일**: 2026-02-06
**상태**: 사용자 승인 대기

---

## 1. 문제 진단 요약 (Root Cause Analysis)

### 1.1 발생한 문제

2026-02-06 환경 스캐닝 실행 시:
- `master-status.json`: "completed" (완료 표시)
- `workflow-status.json`: "in_progress", step 1.1 (초기화 단계에서 멈춤)
- `raw-signals-2026-02-06.json`: 파일 존재하지만 실제 웹 검색 없이 생성된 것으로 의심
- **결과**: 실제 스캔 없이 "완료"로 잘못 보고됨

### 1.2 근본 원인 (5 Why 분석)

```
Why 1: 왜 실제 스캔 없이 완료로 표시되었는가?
  → 상태 파일(master-status.json)과 실행 상태(workflow-status.json)가 불일치했지만 감지되지 않음

Why 2: 왜 불일치가 감지되지 않았는가?
  → 상태 파일 간 일관성 검증 메커니즘이 없음

Why 3: 왜 raw 데이터 파일이 실제 실행 없이 존재했는가?
  → 이전 실행의 파일이 남아있었고, 날짜별 상태 격리가 없었음

Why 4: 왜 실제 웹 검색/API 호출 여부를 알 수 없었는가?
  → 실행 증명(Proof of Execution) 메커니즘이 없음

Why 5: 왜 이런 설계 결함이 발생했는가?
  → 상태 관리가 "파일 존재 = 완료"로 암묵적으로 가정되어 있었음
```

### 1.3 발견된 설계 결함 (6개)

| ID | 결함 | 현재 상태 | 영향 |
|----|------|----------|------|
| D1 | 날짜별 상태 격리 부재 | `workflow-status.json` 단일 파일 | 이전 날짜 상태와 혼동 |
| D2 | 상태 일관성 검증 부재 | SOT ↔ Master ↔ WF ↔ Raw 간 검증 없음 | 불일치 미감지 |
| D3 | 실행 증명(PoE) 부재 | 파일 존재 = 완료로 가정 | 미실행 감지 불가 |
| D4 | 날짜별 raw 파일 검증 부재 | 파일명만 확인, 내용 미검증 | 오래된 데이터 사용 |
| D5 | 스킬 실행 시 사전 검증 부재 | `/env-scan:run` 즉시 실행 | 중복 실행/미완료 미감지 |
| D6 | 실행 ID 추적 부재 | 개별 실행 식별 불가 | 실행 추적 불가 |

---

## 2. 설계 원칙 확인 (보존해야 할 핵심)

### 2.1 기존 철학 (IMMUTABLE - 절대 변경 불가)

```yaml
보존_원칙:
  - 단일 파일 SOT (workflow-registry.yaml)
  - 계층적 메모리 구조 (SOT → Config → Data → Logs)
  - WF1/WF2 완전 독립성 (no shared runtime data)
  - 3-Phase 워크플로우 구조
  - VEV 프로토콜 (Verify-Execute-Verify)
  - 5개 Human Checkpoint (2+2+1)
  - 순차 실행 (WF1 → WF2 → Integration)
  - Report-only Integration (raw data 미공유)
```

### 2.2 core-invariants.yaml 준수 사항

```yaml
절대_불변:
  - workflow_phases: [Research, Planning, Implementation]
  - human_checkpoints: [1.4(opt), 2.5(req), 3.4(req)]
  - steeps_categories: [S, T, E, E, P, s]
  - vev_protocol: [PRE-VERIFY, EXECUTE, POST-VERIFY, RETRY, RECORD]
  - pipeline_gates: [gate_1, gate_2, gate_3]
  - dual_workflow_system: [DW-001 ~ DW-007]
```

---

## 3. 설계 개선안

### 3.1 개요

```
┌─────────────────────────────────────────────────────────────────┐
│  기존 설계                          개선 설계                     │
├─────────────────────────────────────────────────────────────────┤
│  workflow-status.json (단일)  →  workflow-status-{date}.json    │
│  파일 존재 = 완료             →  실행 증명(PoE) 메타데이터 검증   │
│  상태 파일 독립 관리          →  계층적 일관성 검증 게이트        │
│  즉시 실행                    →  사전 상태 검증 후 실행           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 개선 항목 상세

---

#### 개선 1: 날짜별 상태 파일 분리

**현재**:
```
env-scanning/wf1-general/logs/workflow-status.json  (단일 파일, 덮어쓰기)
```

**개선**:
```
env-scanning/wf1-general/logs/
├── workflow-status-2026-02-04.json
├── workflow-status-2026-02-05.json
├── workflow-status-2026-02-06.json
└── workflow-status-latest.json  (→ 최신 날짜 파일의 symlink/copy)
```

**변경 범위**:
- `master-orchestrator.md`: Step 0.3 상태 파일 생성 로직
- `env-scan-orchestrator.md`: 상태 파일 경로 생성 로직
- `arxiv-scan-orchestrator.md`: 상태 파일 경로 생성 로직

**SOT 변경**: 없음 (경로 패턴만 변경, registry 구조 유지)

---

#### 개선 2: 실행 증명(Proof of Execution) 메타데이터

**현재 raw 파일 구조**:
```json
{
  "scan_metadata": {
    "date": "2026-02-06",
    "total_items": 52
  },
  "items": [...]
}
```

**개선된 raw 파일 구조**:
```json
{
  "scan_metadata": {
    "date": "2026-02-06",
    "total_items": 52
  },
  "execution_proof": {
    "execution_id": "exec-2026-02-06-09-15-42-a3f2",
    "started_at": "2026-02-06T09:15:42+09:00",
    "completed_at": "2026-02-06T09:45:23+09:00",
    "actual_api_calls": {
      "web_search": 18,
      "arxiv_api": 0
    },
    "actual_sources_scanned": ["TechCrunch", "MIT Tech Review", ...],
    "file_created_at": "2026-02-06T09:45:23+09:00",
    "checksum": "sha256:a1b2c3d4..."
  },
  "items": [...]
}
```

**검증 규칙**:
```yaml
PoE_validation:
  - file_created_at와 시스템 파일 mtime 일치 (±5분 허용)
  - actual_api_calls > 0 (최소 1회 이상 실제 호출)
  - execution_id 형식 검증 (exec-{date}-{time}-{random})
  - checksum 검증 (items 배열의 SHA256)
```

**변경 범위**:
- `multi-source-scanner.md`: PoE 메타데이터 생성
- `env-scan-orchestrator.md`: PoE 검증 로직 추가

---

#### 개선 3: 계층적 상태 일관성 검증 게이트

**새로운 검증 게이트**: `State Consistency Gate (SCG)`

```
┌─────────────────────────────────────────────────────────────┐
│  State Consistency Gate (SCG)                                │
│  실행 시점: Step 0.2 (SOT 검증 직후), 각 Phase 전환 시        │
├─────────────────────────────────────────────────────────────┤
│  검증 계층:                                                  │
│                                                              │
│  Layer 1: SOT ↔ Master Status                               │
│    - registry_version 일치                                   │
│    - workflow 목록 일치                                      │
│                                                              │
│  Layer 2: Master Status ↔ WF Status                         │
│    - 각 WF의 status 일치                                     │
│    - completed_steps 일치                                    │
│    - 날짜 일치                                               │
│                                                              │
│  Layer 3: WF Status ↔ Raw Data                              │
│    - status=completed → raw 파일 존재 + PoE 검증 통과        │
│    - raw 파일 날짜 = 오늘 날짜                               │
│    - raw 파일 PoE.execution_id = WF Status.execution_id      │
│                                                              │
│  Layer 4: Raw Data ↔ Report                                 │
│    - raw items 수 ≥ report signals 수                       │
│    - report 날짜 = raw 날짜                                  │
└─────────────────────────────────────────────────────────────┘
```

**실패 시 동작**:
```yaml
SCG_failure:
  layer_1_fail: HALT - "SOT와 Master Status 불일치"
  layer_2_fail: HALT - "Master Status와 WF Status 불일치"
  layer_3_fail: HALT - "WF Status와 Raw Data 불일치 (실행 증명 실패)"
  layer_4_fail: WARN - "Raw Data와 Report 불일치 (재생성 권장)"
```

**변경 범위**:
- `master-orchestrator.md`: SCG 검증 로직 추가 (Step 0.2 확장)
- 신규 파일: `scripts/validate_state_consistency.py`

---

#### 개선 4: 스킬 실행 시 사전 검증 강화

**현재 `/env-scan:run` 실행 흐름**:
```
사용자 → /env-scan:run → 즉시 master-orchestrator 실행
```

**개선된 실행 흐름**:
```
사용자 → /env-scan:run
         ↓
       Pre-Execution Check
         ├─ 오늘 날짜 상태 파일 존재 확인
         │   ├─ 없음 → 신규 실행 시작
         │   └─ 있음 → 이전 실행 상태 확인
         │       ├─ completed → "이미 완료. 재실행하시겠습니까?"
         │       ├─ in_progress → "진행 중. 이어서 실행하시겠습니까?"
         │       └─ failed → "실패 상태. 재시도하시겠습니까?"
         ↓
       SCG (State Consistency Gate) 실행
         ├─ PASS → master-orchestrator 실행
         └─ FAIL → 불일치 보고 + 수동 해결 요청
```

**변경 범위**:
- `.claude/skills/env-scanner/SKILL.md`: Pre-Execution Check 로직 추가
- `master-orchestrator.md`: SCG 호출 추가

---

#### 개선 5: 실행 ID 기반 추적

**execution_id 생성 규칙**:
```
exec-{date}-{time}-{random4}
예: exec-2026-02-06-09-15-42-a3f2
```

**추적 범위**:
```yaml
execution_id_propagation:
  master_status.execution_id: "dual-scan-2026-02-06-a3f2"
  wf1_status.execution_id: "wf1-scan-2026-02-06-a3f2"
  wf2_status.execution_id: "wf2-scan-2026-02-06-a3f2"
  raw_data.execution_proof.execution_id: "wf1-scan-2026-02-06-a3f2"
  report_metadata.execution_id: "wf1-scan-2026-02-06-a3f2"
```

**검증**: 모든 계층에서 execution_id suffix (a3f2) 일치 확인

---

## 4. 구현 계획

### 4.1 변경 파일 목록

| 파일 | 변경 유형 | 변경 내용 |
|------|----------|----------|
| `master-orchestrator.md` | 수정 | Step 0.2 SCG 추가, Step 0.3 날짜별 상태 파일 |
| `env-scan-orchestrator.md` | 수정 | 날짜별 상태 파일, PoE 검증 |
| `arxiv-scan-orchestrator.md` | 수정 | 날짜별 상태 파일, PoE 검증 |
| `multi-source-scanner.md` | 수정 | PoE 메타데이터 생성 |
| `SKILL.md` | 수정 | Pre-Execution Check 추가 |
| `validate_state_consistency.py` | **신규** | SCG 검증 스크립트 |
| `core-invariants.yaml` | 수정 | SCG 규칙 추가 (invariant) |

### 4.2 구현 순서

```
Phase A: 기반 구조 (영향 최소)
  1. validate_state_consistency.py 생성
  2. core-invariants.yaml에 SCG 규칙 추가

Phase B: 상태 관리 개선
  3. master-orchestrator.md 수정 (날짜별 상태 파일)
  4. env-scan-orchestrator.md 수정
  5. arxiv-scan-orchestrator.md 수정

Phase C: 실행 증명 추가
  6. multi-source-scanner.md 수정 (PoE 메타데이터)
  7. SCG Layer 3 검증 활성화

Phase D: 스킬 통합
  8. SKILL.md 수정 (Pre-Execution Check)
  9. 전체 테스트 실행
```

### 4.3 롤백 계획

```yaml
rollback_strategy:
  - 모든 변경은 기존 파일 구조와 호환 유지
  - workflow-status-latest.json이 기존 workflow-status.json 역할 대체
  - PoE 메타데이터는 optional 필드로 시작 (누락 시 WARN, HALT 아님)
  - 2주 안정화 기간 후 PoE 필수화 (HALT 활성화)
```

---

## 5. 기존 설계와의 호환성 검증

### 5.1 SOT 영향

```yaml
workflow-registry.yaml 변경사항: 없음
  - paths 구조 유지
  - execution.mode 유지
  - checkpoints 구조 유지
```

### 5.2 core-invariants.yaml 영향

```yaml
추가 항목 (기존 invariant 미변경):
  state_consistency_gate:
    description: "계층적 상태 일관성 검증 게이트"
    immutable: true
    layers: [SOT-Master, Master-WF, WF-Raw, Raw-Report]
    failure_severity: [HALT, HALT, HALT, WARN]
```

### 5.3 WF1/WF2 독립성 영향

```yaml
독립성_유지:
  - WF1과 WF2는 각각 별도의 날짜별 상태 파일 생성
  - WF1의 PoE와 WF2의 PoE는 완전 독립
  - SCG는 각 WF를 개별적으로 검증 (cross-WF 검증 없음)
  - Integration은 여전히 report-only merge
```

### 5.4 다중 에이전트 동시 실행 안전성

```yaml
concurrency_safety:
  - 날짜별 상태 파일로 날짜 간 충돌 방지
  - execution_id로 동일 날짜 중복 실행 감지
  - SCG가 상태 불일치 시 HALT → 자동 복구 시도 차단
  - 수동 해결 후 재실행 필요 (명시적 인간 개입)
```

---

## 6. 승인 요청

### 6.1 변경 요약

| 항목 | 변경 |
|------|------|
| 신규 파일 | 1개 (`validate_state_consistency.py`) |
| 수정 파일 | 7개 (orchestrator 3, worker 1, skill 1, config 1, invariants 1) |
| SOT 변경 | 없음 |
| core-invariants 변경 | 1개 섹션 추가 (기존 불변) |
| 기존 기능 영향 | 없음 (추가 검증만) |

### 6.2 리스크 평가

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| 기존 워크플로우 중단 | 낮음 | 높음 | 롤백 계획, 호환 유지 |
| 성능 저하 | 낮음 | 낮음 | 검증은 가벼운 파일 체크만 |
| 복잡도 증가 | 중간 | 중간 | 명확한 계층 분리 |

### 6.3 승인 후 다음 단계

```
1. 사용자 승인
2. Phase A-D 순차 구현
3. 테스트 실행 (마라톤 모드 1회)
4. 결과 검증 및 안정화
5. 문서 업데이트
```

---

## 7. 결론

이 설계 개선안은:

1. **기존 철학 100% 보존**: SOT, 계층적 메모리, WF 독립성, VEV 프로토콜 모두 유지
2. **근본 원인 해결**: 상태 일관성 검증 + 실행 증명으로 "미실행 완료 표시" 문제 방지
3. **최소 침습적 변경**: 기존 구조에 검증 계층만 추가, 핵심 로직 미변경
4. **다중 에이전트 안전**: 날짜별 격리 + execution_id로 동시 실행 충돌 방지

**승인을 요청드립니다.**

---

*문서 끝*
