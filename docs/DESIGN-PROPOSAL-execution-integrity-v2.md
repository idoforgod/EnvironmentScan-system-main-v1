# 설계 개선안 v2: 실행 무결성 검증 시스템
# DESIGN PROPOSAL v2: Execution Integrity Verification System

**문서 버전**: 2.0.0
**작성일**: 2026-02-06
**상태**: 사용자 승인 대기
**이전 버전에서 변경**: SOT 정의 누락 문제 해결

---

## 1. v1 설계안의 결함 및 성찰

### 1.1 발견된 결함

v1 설계안은 **검증 코드(validate_state_consistency.py)만 추가**하고
**SOT 정의를 누락**했습니다. 이는 다음과 같은 문제를 야기합니다:

```
❌ v1 설계안의 문제:
   validate_state_consistency.py (신규)
   └── SCG 규칙이 Python 코드에 하드코딩
   └── PoE 스키마가 Python 코드에 하드코딩
   └── 상태 파일 패턴이 Python 코드에 하드코딩

   → workflow-registry.yaml (SOT)에 정의 없음
   → SOT 원칙 위반
```

### 1.2 현재 시스템의 SOT 작동 방식

```yaml
# 현재 패턴 (validate_registry.py)
workflow-registry.yaml:
  startup_validation:
    rules:
      - id: "SOT-001"
        check: "all_shared_invariants_exist"
        description: "All files must exist"
        severity: "HALT"

# Python 코드가 이 규칙 ID를 사용하여 검증 로직 구현
# → SOT가 "권위 있는 정의", 코드가 "실행"
```

### 1.3 v2에서 수정된 접근

```
✅ v2 설계안:
   workflow-registry.yaml (SOT)
   ├── execution_integrity: (신규 섹션)
   │   ├── state_file_patterns: 상태 파일 경로 패턴 정의
   │   ├── proof_of_execution: PoE 스키마 정의
   │   └── state_consistency_gate: SCG 규칙 정의
   │
   validate_state_consistency.py
   └── SOT에서 규칙/스키마를 읽어서 검증 실행
```

---

## 2. SOT 확장: workflow-registry.yaml 추가 섹션

### 2.1 추가할 섹션: `execution_integrity`

```yaml
# ================================================================
# EXECUTION INTEGRITY (v1.0.0)
# ================================================================
# 이 섹션은 워크플로우 실행의 무결성을 보장하기 위한
# 상태 관리, 실행 증명, 일관성 검증 규칙을 정의합니다.
#
# RULES:
#   1. validate_state_consistency.py MUST read this section at execution
#   2. 모든 상태 파일 경로는 이 섹션의 패턴을 따라야 함
#   3. 실행 증명(PoE)은 이 섹션의 스키마를 준수해야 함
#   4. SCG 검증은 이 섹션의 규칙을 따라야 함
# ================================================================

execution_integrity:
  version: "1.0.0"

  # ── 상태 파일 패턴 정의 ──
  # 모든 오케스트레이터는 이 패턴을 사용해야 함
  state_file_patterns:
    # 날짜별 상태 파일 (신규)
    workflow_status_dated: "{data_root}/logs/workflow-status-{date}.json"
    # 최신 상태 파일 (기존 호환)
    workflow_status_latest: "{data_root}/logs/workflow-status-latest.json"
    # 마스터 상태 파일 (날짜별)
    master_status_dated: "{integration_root}/logs/master-status-{date}.json"
    # 마스터 최신 상태 파일
    master_status_latest: "{integration_root}/logs/master-status-latest.json"

  # ── 실행 증명 (Proof of Execution) 스키마 ──
  proof_of_execution:
    enabled: true
    location: "scan_metadata.execution_proof"  # raw 파일 내 위치

    required_fields:
      - name: "execution_id"
        type: "string"
        format: "{workflow_id}-{date}-{time}-{random4}"
        example: "wf1-scan-2026-02-06-09-15-42-a3f2"

      - name: "started_at"
        type: "string"
        format: "ISO8601"
        example: "2026-02-06T09:15:42+09:00"

      - name: "completed_at"
        type: "string"
        format: "ISO8601"
        example: "2026-02-06T09:45:23+09:00"

      - name: "actual_api_calls"
        type: "object"
        required_keys: ["web_search", "arxiv_api"]
        example: { "web_search": 18, "arxiv_api": 0 }

      - name: "actual_sources_scanned"
        type: "array"
        min_length: 1
        example: ["TechCrunch", "MIT Tech Review"]

      - name: "file_created_at"
        type: "string"
        format: "ISO8601"

    validation_rules:
      # 파일 생성 시간과 내부 타임스탬프 차이 허용 범위
      timestamp_tolerance_minutes: 5
      # 최소 API 호출 수 (0이면 실제 실행 안 됨)
      min_total_api_calls: 1
      # execution_id 형식 검증 활성화
      validate_execution_id_format: true

  # ── 상태 일관성 검증 게이트 (SCG) ──
  state_consistency_gate:
    enabled: true
    execute_at:
      - "startup"           # 워크플로우 시작 시
      - "phase_transition"  # Phase 간 전환 시
      - "completion"        # 워크플로우 완료 시

    layers:
      - id: "SCG-L1"
        name: "SOT ↔ Master Status"
        description: "SOT와 마스터 상태 파일 간 일관성 검증"
        severity: "HALT"
        checks:
          - id: "SCG-L1-001"
            name: "registry_version_match"
            description: "SOT version과 master_status.registry_version 일치"
          - id: "SCG-L1-002"
            name: "workflow_list_match"
            description: "SOT workflows 목록과 master_status.workflow_results 키 일치"

      - id: "SCG-L2"
        name: "Master Status ↔ WF Status"
        description: "마스터 상태와 개별 워크플로우 상태 간 일관성 검증"
        severity: "HALT"
        checks:
          - id: "SCG-L2-001"
            name: "wf_status_match"
            description: "master.workflow_results[wf].status == wf_status.status"
          - id: "SCG-L2-002"
            name: "date_match"
            description: "모든 상태 파일의 날짜가 오늘 날짜와 일치"
          - id: "SCG-L2-003"
            name: "execution_id_prefix_match"
            description: "master.execution_id 접미사와 wf_status.execution_id 접미사 일치"

      - id: "SCG-L3"
        name: "WF Status ↔ Raw Data"
        description: "워크플로우 상태와 실제 데이터 파일 간 일관성 검증"
        severity: "HALT"
        checks:
          - id: "SCG-L3-001"
            name: "raw_file_exists"
            description: "wf_status.status=completed → raw 파일 존재"
          - id: "SCG-L3-002"
            name: "poe_valid"
            description: "raw 파일의 execution_proof가 스키마 준수"
          - id: "SCG-L3-003"
            name: "poe_execution_id_match"
            description: "wf_status.execution_id == raw.execution_proof.execution_id"
          - id: "SCG-L3-004"
            name: "poe_timestamp_valid"
            description: "파일 mtime과 poe.file_created_at 차이 < tolerance"
          - id: "SCG-L3-005"
            name: "poe_min_api_calls"
            description: "actual_api_calls 합계 >= min_total_api_calls"

      - id: "SCG-L4"
        name: "Raw Data ↔ Report"
        description: "데이터 파일과 보고서 간 일관성 검증"
        severity: "WARN"
        checks:
          - id: "SCG-L4-001"
            name: "signal_count_consistent"
            description: "raw.items.length >= report.signal_count"
          - id: "SCG-L4-002"
            name: "report_date_match"
            description: "report 파일명 날짜 == raw 파일 날짜"

    failure_actions:
      HALT: "워크플로우 즉시 중단, 사용자에게 불일치 보고, 수동 해결 요청"
      WARN: "경고 로그 기록, 사용자에게 알림, 워크플로우 계속 진행"

  # ── 사전 실행 검증 (Pre-Execution Check) ──
  pre_execution_check:
    enabled: true
    checks:
      - id: "PEC-001"
        name: "today_status_exists"
        description: "오늘 날짜 상태 파일 존재 여부 확인"
        on_exists:
          completed: "이미 완료됨. 재실행 확인 요청"
          in_progress: "진행 중. 이어서 실행 또는 재시작 확인 요청"
          failed: "실패 상태. 재시도 확인 요청"
        on_not_exists: "신규 실행 시작"

      - id: "PEC-002"
        name: "previous_day_completed"
        description: "전일 상태 확인 (경고용)"
        severity: "WARN"
```

### 2.2 startup_validation에 SCG 규칙 참조 추가

```yaml
# 기존 startup_validation.rules에 추가

startup_validation:
  rules:
    # ... 기존 SOT-001 ~ SOT-013 유지 ...

    - id: "SOT-014"
      check: "execution_integrity_section_exists"
      description: "execution_integrity section must exist in registry"
      severity: "HALT"

    - id: "SOT-015"
      check: "scg_rules_valid"
      description: "All SCG rules have required fields (id, name, severity, checks)"
      severity: "HALT"

    - id: "SOT-016"
      check: "poe_schema_valid"
      description: "PoE schema has all required_fields defined"
      severity: "HALT"
```

---

## 3. 수정된 구현 계획

### 3.1 변경 파일 목록 (수정됨)

| 파일 | 변경 유형 | 변경 내용 |
|------|----------|----------|
| **`workflow-registry.yaml`** | **수정 (핵심)** | `execution_integrity` 섹션 추가 |
| `core-invariants.yaml` | 수정 | `execution_integrity` invariant 추가 |
| `validate_registry.py` | 수정 | SOT-014~016 검증 추가 |
| `validate_state_consistency.py` | **신규** | **SOT에서 규칙 읽어서** SCG 실행 |
| `master-orchestrator.md` | 수정 | SCG 호출, 날짜별 상태 파일 |
| `env-scan-orchestrator.md` | 수정 | PoE 생성, 날짜별 상태 파일 |
| `arxiv-scan-orchestrator.md` | 수정 | PoE 생성, 날짜별 상태 파일 |
| `multi-source-scanner.md` | 수정 | PoE 메타데이터 생성 |
| `SKILL.md` | 수정 | Pre-Execution Check 추가 |

### 3.2 validate_state_consistency.py 설계 (수정됨)

```python
#!/usr/bin/env python3
"""
State Consistency Gate (SCG) Validator
======================================
SOT(workflow-registry.yaml)에서 SCG 규칙을 읽어 실행합니다.

핵심 원칙: 모든 규칙은 SOT에 정의되어 있으며,
이 스크립트는 SOT를 읽고 실행할 뿐입니다.
"""

def load_scg_rules_from_sot(registry_path: str) -> dict:
    """SOT에서 SCG 규칙을 동적으로 로드"""
    registry = load_yaml(registry_path)
    return registry.get("execution_integrity", {}).get("state_consistency_gate", {})

def load_poe_schema_from_sot(registry_path: str) -> dict:
    """SOT에서 PoE 스키마를 동적으로 로드"""
    registry = load_yaml(registry_path)
    return registry.get("execution_integrity", {}).get("proof_of_execution", {})

def validate_layer(layer_config: dict, context: dict) -> list:
    """SOT에 정의된 layer 규칙을 순회하며 검증"""
    results = []
    for check in layer_config.get("checks", []):
        check_id = check["id"]
        check_name = check["name"]
        # check_name에 해당하는 검증 함수 호출
        # 검증 함수는 SOT의 check 정의에 맞춰 구현
        result = execute_check(check_name, context)
        results.append(CheckResult(check_id, result))
    return results

def main():
    # 1. SOT 로드
    registry_path = "env-scanning/config/workflow-registry.yaml"
    scg_config = load_scg_rules_from_sot(registry_path)
    poe_schema = load_poe_schema_from_sot(registry_path)

    # 2. SOT에 정의된 각 layer 순회
    for layer in scg_config.get("layers", []):
        layer_id = layer["id"]
        severity = layer["severity"]
        results = validate_layer(layer, context)

        # 3. SOT에 정의된 severity에 따라 처리
        if any(not r.passed for r in results):
            if severity == "HALT":
                # SOT의 failure_actions.HALT 정의에 따라 처리
                halt_and_report(layer_id, results)
            elif severity == "WARN":
                warn_and_continue(layer_id, results)
```

### 3.3 구현 순서 (수정됨)

```
Phase A: SOT 확장 (가장 먼저)
  1. workflow-registry.yaml에 execution_integrity 섹션 추가
  2. startup_validation에 SOT-014~016 추가
  3. core-invariants.yaml에 execution_integrity invariant 추가

Phase B: 검증 스크립트
  4. validate_registry.py 수정 (SOT-014~016 검증)
  5. validate_state_consistency.py 생성 (SOT에서 규칙 로드)

Phase C: 오케스트레이터 수정
  6. master-orchestrator.md 수정
  7. env-scan-orchestrator.md 수정
  8. arxiv-scan-orchestrator.md 수정

Phase D: 워커 및 스킬
  9. multi-source-scanner.md 수정 (PoE 생성)
  10. SKILL.md 수정 (Pre-Execution Check)

Phase E: 테스트
  11. validate_registry.py 실행 (SOT-014~016 통과 확인)
  12. 마라톤 모드 테스트 실행
```

---

## 4. SOT 작동 보장 메커니즘

### 4.1 SOT → 코드 바인딩 규칙

```yaml
# core-invariants.yaml에 추가

execution_integrity_invariant:
  description: >
    실행 무결성 시스템(SCG, PoE, 상태 파일 패턴)의 모든 규칙은
    workflow-registry.yaml의 execution_integrity 섹션에 정의되어야 한다.
    validate_state_consistency.py는 이 섹션에서 규칙을 동적으로 읽어야 하며,
    하드코딩된 규칙을 가질 수 없다.
  immutable: true

  enforcement:
    - "validate_state_consistency.py MUST call load_scg_rules_from_sot()"
    - "PoE 스키마는 SOT의 proof_of_execution.required_fields에서 읽어야 함"
    - "상태 파일 경로는 SOT의 state_file_patterns에서 읽어야 함"

  violation_check:
    method: "코드 리뷰 시 SOT 로드 함수 호출 확인"
    automated: false  # 향후 정적 분석 도구 추가 가능
```

### 4.2 SOT 변경 시 자동 반영

```
SOT 변경 흐름:

1. workflow-registry.yaml 수정 (예: SCG 규칙 추가)
2. validate_registry.py 실행 → SOT-014~016 검증
3. 워크플로우 실행 시:
   - validate_state_consistency.py가 SOT를 다시 읽음
   - 새로운 규칙이 자동으로 적용됨
   - 코드 수정 없이 규칙 변경 가능 (일부 케이스)

주의: 새로운 check_name 추가 시 해당 검증 함수 구현 필요
```

### 4.3 SOT 작동 검증 체크리스트

| 검증 항목 | 방법 |
|----------|------|
| execution_integrity 섹션 존재 | SOT-014 자동 검증 |
| SCG 규칙 구조 유효 | SOT-015 자동 검증 |
| PoE 스키마 구조 유효 | SOT-016 자동 검증 |
| 코드가 SOT를 읽는가 | 코드 리뷰 (load_*_from_sot 함수 호출 확인) |
| 하드코딩된 규칙 없는가 | 코드 리뷰 |

---

## 5. 기존 설계와의 호환성 (재확인)

### 5.1 기존 SOT 구조 보존

```yaml
workflow-registry.yaml:
  system:          # 기존 유지
  workflows:       # 기존 유지
  integration:     # 기존 유지
  startup_validation:  # 기존 유지 + 3개 규칙 추가
  execution_integrity: # 신규 추가 (기존 섹션과 독립)
```

### 5.2 기존 core-invariants 보존

```yaml
core_invariants:
  workflow_phases:      # 기존 유지
  human_checkpoints:    # 기존 유지
  steeps_categories:    # 기존 유지
  vev_protocol:         # 기존 유지
  pipeline_gates:       # 기존 유지
  dual_workflow_system: # 기존 유지
  execution_integrity_invariant:  # 신규 추가
```

### 5.3 기존 validate_registry.py 패턴 준수

```python
# 기존 패턴 유지
vr.results.append(CheckResult(
    "SOT-014", "HALT",
    "execution_integrity section exists",
    ...
))

# 신규 검증도 같은 패턴
vr.results.append(CheckResult(
    "SOT-015", "HALT",
    "SCG rules structure valid",
    ...
))
```

---

## 6. 최종 승인 요청

### 6.1 v2 변경 요약

| 항목 | v1 | v2 |
|------|----|----|
| SOT 확장 | 없음 | `execution_integrity` 섹션 추가 |
| SCG 규칙 정의 | 코드 하드코딩 | **SOT에 정의** |
| PoE 스키마 정의 | 코드 하드코딩 | **SOT에 정의** |
| 상태 파일 패턴 | 코드 하드코딩 | **SOT에 정의** |
| 검증 스크립트 | 독립 실행 | **SOT 로드 후 실행** |

### 6.2 SOT 원칙 준수 확인

| 원칙 | 준수 여부 |
|------|----------|
| 단일 SOT (workflow-registry.yaml) | ✅ 모든 규칙이 SOT에 정의됨 |
| 코드는 SOT를 읽고 실행 | ✅ load_*_from_sot() 함수 사용 |
| 하드코딩 금지 | ✅ 규칙 ID, severity, checks 모두 SOT에서 로드 |
| 기존 구조 보존 | ✅ 기존 섹션 미변경, 신규 섹션만 추가 |

### 6.3 리스크 평가

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| SOT 확장 시 파싱 오류 | 낮음 | 높음 | SOT-014~016 사전 검증 |
| 기존 워크플로우 중단 | 낮음 | 높음 | 기존 섹션 미변경 |
| 검증 스크립트 SOT 로드 실패 | 낮음 | 높음 | validate_registry.py로 SOT 무결성 사전 검증 |

### 6.4 승인 후 다음 단계

```
1. 사용자 승인
2. Phase A: SOT 확장 (workflow-registry.yaml)
3. Phase B: 검증 스크립트
4. Phase C: 오케스트레이터 수정
5. Phase D: 워커 및 스킬
6. Phase E: 마라톤 모드 테스트 실행
```

---

## 7. 결론

v2 설계안은:

1. **SOT 원칙 완전 준수**: 모든 규칙이 workflow-registry.yaml에 정의됨
2. **실제 작동하는 SOT**: 검증 스크립트가 SOT에서 규칙을 동적으로 로드
3. **기존 설계 100% 보존**: 새로운 섹션 추가만, 기존 구조 미변경
4. **근본 원인 해결**: 상태 일관성 + 실행 증명으로 "미실행 완료" 방지

**승인을 요청드립니다.**

---

*문서 끝*
