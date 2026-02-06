# 주간 환경스캐닝 모드 기획서 (Weekly Scan Mode Design Proposal)

**문서 버전**: 0.2.0 (성찰 반영 수정본)
**작성일**: 2026-02-06
**상태**: 사용자 검토 대기
**변경 이력**: v0.1.0 → v0.2.0 — SOT 실작동 검증 후 4개 치명적 결함 수정

---

## 0. v0.1.0 성찰 — 발견된 치명적 결함 4가지

초안(v0.1.0)을 실제 코드(`validate_registry.py`, `validate_report.py`,
`validate_state_consistency.py`, `master-orchestrator.md`)와 대조한 결과,
**SOT에 정의만 하고 실제로 작동하지 않는** 결함 4개를 발견했습니다.

### 결함 1: `validate_registry.py`가 `integration.weekly` 블록을 모른다

**문제**: `validate_registry.py`는 `integration` 섹션에서 `integrated_skeleton`,
`merger_agent`, `output_root`, `paths`만 읽습니다(라인 248-267, 294-302).
`integration.weekly` 블록을 추가해도 **검증 스크립트가 이를 전혀 파싱하지 않으므로**
weekly skeleton 파일이 없어도 SOT 검증을 통과합니다.

**해결**: `validate_registry.py`에 SOT-017~SOT-019 검증 규칙을 추가하고,
`startup_validation.rules`에도 해당 규칙을 정의해야 합니다.

### 결함 2: `validate_report.py`에 `weekly` 프로파일이 없다

**문제**: `validate_report.py`의 `PROFILES` 딕셔너리(라인 74-105)에는
`standard`, `integrated`, `arxiv_fallback` 3개만 있습니다.
기획서에서 `validate_profile: "weekly"`를 SOT에 정의해도, 실제 `validate_report.py`에
해당 프로파일을 추가하지 않으면 `Unknown profile 'weekly'` 에러로 **런타임 크래시**합니다.

**해결**: `PROFILES["weekly"]`를 추가하고, 주간 보고서의 섹션 헤더가 일일 보고서와
다르므로 `REQUIRED_SECTION_HEADERS`를 프로파일별로 분기해야 합니다.

### 결함 3: `validate_state_consistency.py`의 `CHECK_FUNCTIONS` 매핑에 주간 체크가 없다

**문제**: `validate_state_consistency.py`의 `CHECK_FUNCTIONS` 딕셔너리(라인 338-351)는
SOT의 `check.name` 값을 Python 함수에 매핑합니다. 기획서의 SCG-L5 체크 이름
(`daily_report_count_match`, `signal_count_consistency`, `date_range_valid`)에 대응하는
함수가 없으면 **`passed=True, detail="Check function not implemented"`로 조용히 통과**합니다(라인 410).
즉, 검증이 있는 척하지만 실제로는 아무것도 검증하지 않습니다.

**해결**: SCG-L5 체크 각각에 대응하는 Python 함수를 구현하고 `CHECK_FUNCTIONS`에 등록해야 합니다.

### 결함 4: `master-orchestrator.md`의 Variable Definitions 테이블에 주간 변수가 없다

**문제**: `master-orchestrator.md`의 Step 0.1(라인 49-86)은 SOT에서 읽는 변수를
명시적 테이블로 정의합니다. **SOT BINDING RULE**(라인 39-43)에 의해 "이 테이블에 없는
변수는 사용할 수 없다"고 명시되어 있습니다. 주간 모드의 `WEEKLY_SKELETON`,
`WEEKLY_OUTPUT_ROOT` 등이 이 테이블에 없으면 master-orchestrator가
이 값들을 SOT에서 읽을 수 없습니다.

**해결**: Variable Definitions 테이블에 주간 관련 변수를 추가해야 합니다.

---

## 1. 설계 원칙 — 불변 조건 확인

이 기획은 아래 불변 조건을 **절대 위반하지 않습니다**.

| 불변 조건 | 보존 방법 |
|-----------|----------|
| 3-Phase 워크플로우 (Research → Planning → Implementation) | 주간 모드도 동일한 3-Phase 사용. 새로운 Phase 없음 |
| 단일 SOT (workflow-registry.yaml) | 주간 모드 설정을 기존 SOT에 `integration.weekly` 블록으로 추가 |
| Dual Workflow 독립성 (DW-001~DW-007) | WF1/WF2 구조 변경 없음. 주간 모드는 통합 레이어에서만 동작 |
| 5개 Human Checkpoint (2+2+1) | 일일 스캔의 5개 체크포인트 변경 없음 |
| 4-Layer Report Quality Defense (L1~L4) | 주간 전용 스켈레톤 + weekly 프로파일로 동일 방어 적용 |
| VEV Protocol | 변경 없음 |
| Pipeline Gates (6+6+6) | 변경 없음 |
| STEEPs 6분류 체계 | 변경 없음 |
| 이중언어 프로토콜 (내부 EN, 외부 KO) | 변경 없음 |
| Database Atomicity | 주간 모드는 DB에 쓰기하지 않음. 읽기 전용 |
| SCG/PoE 실행 무결성 | 주간 상태 파일 패턴 + SCG-L5 체크 함수를 SOT와 코드 양쪽에 추가 |

---

## 2. 핵심 질문: 주간 스캔은 일일 스캔과 무엇이 다른가?

### 2.1 본질적 차이

```
일일(Daily):  소스 → 수집 → 필터 → 분류 → 분석 → 보고  (신호 발견 — 미시적)
주간(Weekly): 일일 데이터들 → 집계 → 추세 분석 → 메타분석 → 전략 보고  (패턴 발견 — 거시적)
```

| 차원 | 일일 보고서 | 주간 보고서 |
|------|-----------|-----------|
| 질문 | "오늘 무엇이 새로 나타났는가?" | "이번 주에 숲은 어떻게 변했는가?" |
| 시간 범위 | 최근 1~7일 | 지난 7일간의 일일 스캔 전체 |
| 데이터 소스 | **외부** 웹/API 스캐닝 | **내부** 축적 데이터 (읽기 전용) |
| 분석 단위 | 개별 신호 10~15개 상세 | 추세/클러스터 5~7개 상세 |
| 교차 분석 | 신호 간 교차 영향 (정적) | 교차 영향의 **진화** (동적) |
| 전략 시야 | 0-6개월, 6-18개월 | 0-6개월, 6-18개월, **18개월+** |
| 고유 지표 | pSST (개별 신호 신뢰도) | **TIS** (추세 강도 점수) |
| 시스템 리뷰 | 없음 | 주간 품질 지표 + 캘리브레이션 권고 |

**결정적 차이**: 주간 스캔은 **새로운 소스 스캐닝을 하지 않습니다**.
이미 축적된 일일 데이터를 더 높은 추상화 수준에서 재분석합니다.

---

## 3. 아키텍처 설계: Integration 레이어 확장

### 3.1 왜 새로운 워크플로우(WF3)가 아닌가

- `core-invariants.yaml`의 `dual_workflow_system.immutable: true` 위반
- `validate_registry.py` SOT-007이 `execution_order`의 순차성을 검증 → WF3 추가 시 재작성 필요
- DW-001(워크플로우 독립성) 위반 — 주간 모드는 WF1+WF2 데이터를 모두 읽어야 함

따라서 주간 모드는 **기존 통합(Integration) 레이어의 확장**으로 설계합니다.

```
현재:
  WF1 (daily) ──┐
                 ├── Integration (daily merge) ── 통합 일일 보고서
  WF2 (daily) ──┘

확장:
  WF1 (daily) ──┐
                 ├── Integration (daily merge) ── 통합 일일 보고서
  WF2 (daily) ──┘
                              │
                              └── [weekly trigger] ── 주간 메타분석 보고서
                                  (7일치 통합 보고서 + ranked JSON 읽기 전용)
```

### 3.2 설계 원칙

1. **읽기 전용 접근**: 주간 분석은 일일 데이터를 읽기만 하고, 수정하지 않음
2. **통합 레이어 확장**: `integration` 섹션에 `weekly` 서브모드로 추가
3. **독립 출력 경로**: `env-scanning/integrated/weekly/`에 별도 저장
4. **기존 파이프라인 무간섭**: 일일 스캔 실행에 어떤 영향도 없음

---

## 4. SOT (workflow-registry.yaml) 변경 사항

> **SOT 실작동 원칙**: SOT에 정의하는 모든 것은 반드시
> (1) 검증 스크립트가 파싱하고, (2) 오케스트레이터가 런타임에 참조하고,
> (3) 누락 시 검증이 실패하여 실행을 차단해야 한다.

### 4.1 `integration` 섹션에 `weekly` 블록 추가

```yaml
integration:
  # ... (기존 daily 설정 전부 유지 — 한 글자도 수정하지 않음) ...

  weekly:
    enabled: true
    description: "주간 메타분석 - 7일간 일일 스캔 결과의 거시적 패턴 분석"

    # ── 트리거 조건 ──
    trigger:
      type: "manual"           # /env-scan:weekly로 수동 실행
      min_daily_scans: 5       # 최소 5일치 일일 스캔 필요
      lookback_days: 7         # 분석 대상: 최근 7일

    # ── 입력 (읽기 전용) ──
    inputs:
      wf1_reports: "wf1-general/reports/daily/"
      wf2_reports: "wf2-arxiv/reports/daily/"
      integrated_reports: "integrated/reports/daily/"
      wf1_signals_db: "wf1-general/signals/database.json"
      wf2_signals_db: "wf2-arxiv/signals/database.json"
      wf1_ranked: "wf1-general/analysis/"
      wf2_ranked: "wf2-arxiv/analysis/"
      integrated_rankings: "integrated/"

    access_policy:
      wf1_data: "READ_ONLY"
      wf2_data: "READ_ONLY"
      integrated_daily: "READ_ONLY"
      weekly_output: "READ_WRITE"

    # ── 출력 ──
    output_root: "env-scanning/integrated/weekly"
    paths:
      reports: "reports/"
      reports_archive: "reports/archive/"
      analysis: "analysis/"
      logs: "logs/"

    # ── 스켈레톤 ──
    skeleton: ".claude/skills/env-scanner/references/weekly-report-skeleton.md"

    # ── 체크포인트 ──
    checkpoints:
      analysis_review: "required"
      report_approval: "required"

    # ── 검증 프로파일 ──
    validate_profile: "weekly"
```

### 4.2 `execution_integrity.state_file_patterns`에 주간 패턴 추가

```yaml
execution_integrity:
  state_file_patterns:
    # ... (기존 4개 패턴 유지) ...
    weekly_status: "{integration_root}/weekly/logs/weekly-status-{week_id}.json"
```

### 4.3 `startup_validation.rules`에 주간 검증 규칙 추가

```yaml
startup_validation:
  rules:
    # ... (기존 SOT-001 ~ SOT-016 전부 유지) ...

    - id: "SOT-017"
      check: "weekly_skeleton_exists"
      description: "Weekly report skeleton file must exist if weekly enabled"
      severity: "HALT"
      condition: "integration.weekly.enabled == true"

    - id: "SOT-018"
      check: "weekly_output_root_exists"
      description: "Weekly output directories must exist (create if missing)"
      severity: "CREATE"
      condition: "integration.weekly.enabled == true"

    - id: "SOT-019"
      check: "weekly_validate_profile_exists"
      description: "Weekly validate_profile must exist in validate_report.py PROFILES"
      severity: "HALT"
      condition: "integration.weekly.enabled == true"
```

### 4.4 `pre_execution_check`에 주간 충분성 검사 추가

```yaml
pre_execution_check:
  checks:
    # ... (기존 PEC-001, PEC-002 유지) ...
    - id: "PEC-003"
      name: "weekly_data_sufficiency"
      description: "주간 분석에 필요한 최소 일일 스캔 수 확인"
      applies_to: "weekly"
      min_daily_scans: 5
      lookback_days: 7
      on_insufficient: "경고 표시 후 사용자 확인 요청"
```

### 4.5 `execution_integrity.state_consistency_gate.layers`에 SCG-L5 추가

```yaml
- id: "SCG-L5"
  name: "Weekly ↔ Daily Consistency"
  description: "주간 분석이 참조한 일일 데이터와의 일관성 검증"
  severity: "WARN"
  applies_to: "weekly"
  checks:
    - id: "SCG-L5-001"
      name: "weekly_daily_report_count_match"
      description: "주간 분석에서 참조한 일일 보고서 수 == 실제 존재하는 보고서 수"
    - id: "SCG-L5-002"
      name: "weekly_signal_count_consistency"
      description: "주간 통계의 총 신호 수 ≤ 일일 보고서들의 신호 수 합계"
    - id: "SCG-L5-003"
      name: "weekly_date_range_valid"
      description: "주간 분석 대상 날짜 범위가 lookback_days 이내"
```

---

## 5. 검증 스크립트 변경사항 (SOT 실작동 보장)

> 이 섹션이 v0.2.0의 핵심입니다. SOT에 정의만 하고 코드를 수정하지 않으면,
> 검증이 형식적으로만 존재하고 실제로는 아무것도 보호하지 못합니다.

### 5.1 `validate_registry.py` — SOT-017~019 추가

```python
# ── SOT-017: Weekly skeleton exists (conditional) ──
weekly_cfg = integration.get("weekly", {})
if weekly_cfg.get("enabled", False):
    weekly_skel = weekly_cfg.get("skeleton", "")
    weekly_skel_exists = _file_exists(project_root, weekly_skel) if weekly_skel else False
    vr.results.append(CheckResult(
        "SOT-017", "HALT",
        "Weekly report skeleton file exists",
        weekly_skel_exists,
        f"Missing: {weekly_skel}" if not weekly_skel_exists else ""
    ))

# ── SOT-018: Weekly output directories exist ──
if weekly_cfg.get("enabled", False):
    weekly_root = weekly_cfg.get("output_root", "")
    weekly_created = []
    if weekly_root:
        weekly_root_path = _resolve(project_root, weekly_root)
        for path_key, rel in weekly_cfg.get("paths", {}).items():
            full = weekly_root_path / rel
            if not full.exists():
                full.mkdir(parents=True, exist_ok=True)
                weekly_created.append(str(full.relative_to(project_root)))
    vr.results.append(CheckResult(
        "SOT-018", "CREATE",
        "Weekly output directories exist",
        True,
        "",
        f"Created {len(weekly_created)} directories" if weekly_created else ""
    ))

# ── SOT-019: Weekly validate profile check ──
# (실제 validate_report.py를 임포트하지 않고, 프로파일 이름만 기록)
if weekly_cfg.get("enabled", False):
    weekly_profile = weekly_cfg.get("validate_profile", "")
    vr.results.append(CheckResult(
        "SOT-019", "HALT",
        "Weekly validate_profile is defined",
        bool(weekly_profile),
        f"Missing validate_profile in integration.weekly" if not weekly_profile else ""
    ))
```

### 5.2 `validate_report.py` — `weekly` 프로파일 + 주간 섹션 헤더

```python
# 주간 보고서의 필수 섹션 헤더 (일일과 다름)
WEEKLY_REQUIRED_SECTION_HEADERS = [
    "## 1. 경영진 요약",
    "## 2. 주간 추세 분석",           # 일일의 "신규 탐지 신호" 대신
    "## 3. 신호 수렴 분석",           # 일일의 "기존 신호 업데이트" 대신
    "## 4. 신호 진화 타임라인",        # 일일의 "패턴 및 연결고리" 대신
    "## 5. 전략적 시사점",
    "## 7. 신뢰도 분석",
    "## 8. 시스템 성능 리뷰",          # 일일의 "부록" 대신
    "## 9. 부록",
]

PROFILES["weekly"] = {
    "min_total_words": 6000,
    "min_korean_ratio": 0.30,
    "min_signal_blocks": 0,           # 주간은 개별 신호 블록이 아닌 추세 블록
    "min_fields_per_signal": 0,       # 9-field 규칙 적용 안 함
    "min_field_global_count": 0,
    "min_cross_impact_pairs": 3,
    "require_cross_workflow": True,    # WF1↔WF2 교차 분석 필수
    "require_source_tags": True,       # [WF1]/[WF2] 태그 필수
    "section_headers": WEEKLY_REQUIRED_SECTION_HEADERS,  # 주간 전용 헤더
    "min_trend_blocks": 5,            # 추세 블록 최소 5개 (주간 고유)
}
```

**핵심 변경**: `validate_report()` 함수의 `SEC-001` 체크에서 프로파일별 섹션 헤더를 분기:

```python
# SEC-001 수정: 프로파일별 섹션 헤더
headers = prof.get("section_headers", REQUIRED_SECTION_HEADERS)
missing_sections = [h for h in headers if h not in content]
```

### 5.3 `validate_state_consistency.py` — SCG-L5 체크 함수 구현

```python
# 주간 전용 체크 함수

def check_weekly_daily_report_count_match(context: dict) -> tuple:
    """SCG-L5-001: 주간 분석에서 참조한 보고서 수 == 실제 존재"""
    weekly_meta = context.get("weekly_metadata", {})
    claimed_count = weekly_meta.get("daily_reports_analyzed", 0)
    actual_reports = context.get("actual_daily_reports", [])
    actual_count = len(actual_reports)

    if claimed_count == 0:
        return True, "No weekly metadata to validate"

    passed = claimed_count == actual_count
    detail = f"Claimed: {claimed_count}, Actual: {actual_count}" if not passed else ""
    return passed, detail


def check_weekly_signal_count_consistency(context: dict) -> tuple:
    """SCG-L5-002: 주간 신호 수 ≤ 일일 합계"""
    weekly_meta = context.get("weekly_metadata", {})
    weekly_total = weekly_meta.get("total_signals_analyzed", 0)
    daily_sum = context.get("daily_signals_sum", 0)

    if weekly_total == 0:
        return True, "No weekly metadata to validate"

    passed = weekly_total <= daily_sum
    detail = f"Weekly: {weekly_total} > Daily sum: {daily_sum}" if not passed else ""
    return passed, detail


def check_weekly_date_range_valid(context: dict) -> tuple:
    """SCG-L5-003: 날짜 범위가 lookback_days 이내"""
    weekly_meta = context.get("weekly_metadata", {})
    start_date = weekly_meta.get("analysis_start_date", "")
    end_date = weekly_meta.get("analysis_end_date", "")
    lookback = context.get("weekly_lookback_days", 7)

    if not start_date or not end_date:
        return True, "No weekly date range to validate"

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = (end - start).days
        passed = delta <= lookback
        detail = f"Range: {delta} days > lookback: {lookback}" if not passed else ""
        return passed, detail
    except ValueError as e:
        return False, f"Date parse error: {e}"


# CHECK_FUNCTIONS에 등록
CHECK_FUNCTIONS.update({
    "weekly_daily_report_count_match": check_weekly_daily_report_count_match,
    "weekly_signal_count_consistency": check_weekly_signal_count_consistency,
    "weekly_date_range_valid": check_weekly_date_range_valid,
})
```

**핵심**: `build_context()` 함수도 주간 모드일 때 `weekly_metadata`, `actual_daily_reports`,
`daily_signals_sum`, `weekly_lookback_days`를 context에 로드하도록 확장해야 합니다.

---

## 6. `master-orchestrator.md` 변경사항

### 6.1 Variable Definitions 테이블 확장

Step 0.1의 변수 테이블에 다음을 추가:

| Variable | SOT Field | Typical Value |
|----------|-----------|---------------|
| `WEEKLY_ENABLED` | `integration.weekly.enabled` | `true` |
| `WEEKLY_OUTPUT_ROOT` | `integration.weekly.output_root` | `env-scanning/integrated/weekly` |
| `WEEKLY_SKELETON` | `integration.weekly.skeleton` | `.claude/skills/env-scanner/references/weekly-report-skeleton.md` |
| `WEEKLY_PROFILE` | `integration.weekly.validate_profile` | `weekly` |
| `WEEKLY_MIN_SCANS` | `integration.weekly.trigger.min_daily_scans` | `5` |
| `WEEKLY_LOOKBACK` | `integration.weekly.trigger.lookback_days` | `7` |
| `WEEKLY_INPUTS` | `integration.weekly.inputs` | (object — 8 paths) |

### 6.2 Standalone Execution Modes 섹션에 주간 모드 추가

```markdown
### Weekly Meta-Analysis (주간)
- Command: `/env-scan:weekly`
- Executes: 주간 메타분석 (WF1/WF2 일일 스캔을 새로 실행하지 않음)
- Pre-check: PEC-003 (최소 WEEKLY_MIN_SCANS일치 일일 데이터 확인)
- Output: 주간 메타분석 보고서 (WEEKLY_OUTPUT_ROOT/reports/)
- Checkpoints: 2 (분석 리뷰 + 보고서 승인)
```

### 6.3 주간 실행 플로우 (Step 5 추가)

```
┌─────────────────────────────────────────────────────────┐
│  Step 5: Weekly Meta-Analysis (주간 모드일 때만 실행)      │
│                                                          │
│  5.0 Pre-Check                                          │
│    - PEC-003: 최근 WEEKLY_LOOKBACK일 내 일일 보고서 확인   │
│    - 이번 주 이미 실행했는지 weekly-status-{week_id} 확인  │
│                                                          │
│  5.1 Phase 1: Data Loading (데이터 로딩)                  │
│    - 7일치 통합 일일 보고서 로딩 (READ-ONLY)               │
│    - 7일치 priority-ranked JSON 로딩 (READ-ONLY)          │
│    - 신호 DB 통계 스냅샷 (READ-ONLY)                      │
│    Human checkpoint: 없음 (데이터 로딩만)                  │
│                                                          │
│  5.2 Phase 2: Meta-Analysis (메타분석)                    │
│    - 추세 분석 (상승/하락/신규/소멸)                        │
│    - 수렴 클러스터 탐지                                    │
│    - TIS (추세 강도 점수) 산출                              │
│    - 시나리오 확률 재조정                                   │
│    Human checkpoint: **분석 리뷰 (required)**              │
│                                                          │
│  5.3 Phase 3: Report Generation (보고서 생성)              │
│    - WEEKLY_SKELETON 기반 보고서 생성 (L1 방어)            │
│    - validate_report.py --profile WEEKLY_PROFILE (L2)    │
│    - 실패 시 L3 재시도 프로토콜                             │
│    - 아카이빙 (WEEKLY_OUTPUT_ROOT/reports/archive/)        │
│    Human checkpoint: **보고서 승인 (required)**             │
│                                                          │
│  5.4 Finalization                                       │
│    - weekly-status-{week_id}.json 생성                   │
│    - master-status에 weekly 결과 기록                     │
│    - SCG-L5 검증 실행                                    │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 주간 보고서 스켈레톤 구조

주간 보고서는 일일 보고서와 **섹션 구조가 다릅니다**.
이는 `validate_report.py`의 `WEEKLY_REQUIRED_SECTION_HEADERS`와 정확히 일치해야 합니다.

```markdown
# 주간 환경 스캐닝 보고서

{{REPORT_HEADER_METADATA}}

---

## 1. 경영진 요약
### 금주의 3대 핵심 추세
{{TOP_3_TRENDS}}
### 주간 신호 통계 요약
{{WEEKLY_STATS_SUMMARY}}

---

## 2. 주간 추세 분석
### 2.1 STEEPs별 주간 동향
{{STEEPS_WEEKLY_TRENDS}}
### 2.2 상승 추세 (Accelerating)
{{ACCELERATING_TRENDS}}
### 2.3 하락 추세 (Decelerating)
{{DECELERATING_TRENDS}}
### 2.4 신규 등장 (Newly Emerged)
{{NEWLY_EMERGED}}
### 2.5 소멸/해소 (Faded)
{{FADED_SIGNALS}}

---

## 3. 신호 수렴 분석
### 3.1 수렴 클러스터
{{CONVERGENCE_CLUSTERS}}
### 3.2 발산 신호
{{DIVERGING_SIGNALS}}
### 3.3 WF1↔WF2 교차 검증
{{WF1_WF2_CROSS_VALIDATION}}

---

## 4. 신호 진화 타임라인
### 4.1 주간 신호 진화 흐름
{{SIGNAL_EVOLUTION_FLOW}}
### 4.2 pSST 점수 변동 추적
{{PSST_CHANGES}}
### 4.3 신호 성숙도 변화
{{MATURITY_TRANSITIONS}}

---

## 5. 전략적 시사점
### 5.1 즉시 조치 필요 (0-6개월)
{{IMMEDIATE_ACTIONS}}
### 5.2 중기 모니터링 (6-18개월)
{{MIDTERM_MONITORING}}
### 5.3 장기 관찰 필요 (18개월+)
{{LONGTERM_WATCH}}
### 5.4 이전 주 대비 변화
{{WEEK_OVER_WEEK_CHANGES}}

---

## 6. 플러서블 시나리오
{{WEEKLY_SCENARIOS}}

---

## 7. 신뢰도 분석
### 7.1 주간 pSST 등급 분포 추이
{{PSST_DISTRIBUTION_TREND}}
### 7.2 소스별 신뢰도 주간 평균
{{SOURCE_RELIABILITY_WEEKLY}}
### 7.3 STEEPs별 평균 pSST 변동
{{STEEPS_PSST_CHANGES}}

---

## 8. 시스템 성능 리뷰
### 8.1 주간 스캐닝 품질 지표
{{QUALITY_METRICS}}
### 8.2 소스 건강 현황
{{SOURCE_HEALTH}}
### 8.3 캘리브레이션 권고
{{CALIBRATION_RECOMMENDATIONS}}

---

## 9. 부록
{{APPENDIX}}
```

---

## 8. 주간 전용 분석: TIS (추세 강도 점수)

일일 스캔에 없는 주간 전용 지표입니다.

```
TIS = (N_sources × 0.3) + (pSST_delta × 0.3) + (frequency × 0.2) + (cross_domain × 0.2)

N_sources:    7일간 해당 주제를 보도한 독립 소스 수 (정규화 0~1)
pSST_delta:   7일간 해당 주제 관련 신호의 평균 pSST 변화량 (정규화 0~1)
frequency:    7일간 해당 주제 관련 신호 출현 빈도 (정규화 0~1)
cross_domain: STEEPs 카테고리 교차 출현 수 (정규화 0~1)
```

등급:
- **급상승 (Surging)**: TIS ≥ 0.8
- **상승 (Rising)**: 0.6 ≤ TIS < 0.8
- **안정 (Stable)**: 0.4 ≤ TIS < 0.6
- **하락 (Declining)**: 0.2 ≤ TIS < 0.4
- **소멸 (Fading)**: TIS < 0.2

TIS 가중치는 `core-invariants.yaml`의 `tunable_parameters`에 등록하여 SIE가 조정 가능하도록 합니다.

---

## 9. 전체 변경 목록 (SOT 실작동 보장 체크리스트)

### 수정해야 할 기존 파일 (6개)

| # | 파일 | 변경 내용 | SOT 실작동 검증 |
|---|------|----------|----------------|
| 1 | `workflow-registry.yaml` | `integration.weekly` 블록 + SOT-017~019 규칙 + PEC-003 + SCG-L5 + state_file_patterns 추가 | `validate_registry.py` 실행으로 검증 |
| 2 | `validate_registry.py` | SOT-017~019 체크 함수 추가 | 주간 skeleton 누락 시 HALT 확인 |
| 3 | `validate_report.py` | `PROFILES["weekly"]` + `WEEKLY_REQUIRED_SECTION_HEADERS` + 프로파일별 헤더 분기 | `--profile weekly` 실행으로 검증 |
| 4 | `validate_state_consistency.py` | SCG-L5 체크 3개 함수 + `CHECK_FUNCTIONS` 등록 + `build_context()` 주간 데이터 로딩 | `--layer SCG-L5` 실행으로 검증 |
| 5 | `master-orchestrator.md` | Variable Definitions 테이블 7개 추가 + Step 5 주간 실행 플로우 + Standalone Modes에 weekly 추가 | 수동 검토 |
| 6 | `core-invariants.yaml` | `tunable_parameters`에 TIS 가중치 추가 | SIE 범위 내 확인 |

### 새로 생성해야 할 파일 (4개)

| # | 파일 | 용도 | SOT 참조 |
|---|------|------|---------|
| 1 | `references/weekly-report-skeleton.md` | 주간 보고서 L1 스켈레톤 | SOT-017이 존재 확인 |
| 2 | `skills/env-scanner/env-scan-weekly.md` | `/env-scan:weekly` 슬래시 커맨드 정의 | 사용자 진입점 |
| 3 | `env-scanning/integrated/weekly/` 디렉터리 | 주간 데이터 저장소 | SOT-018이 생성 |
| 4 | `translation-terms.yaml` 에 주간 용어 추가 | 주간 관련 한국어 번역 | 보고서 품질 |

### 변경하지 않는 파일 (무간섭 보장)

- `env-scan-orchestrator.md` (WF1) — 변경 없음
- `arxiv-scan-orchestrator.md` (WF2) — 변경 없음
- `report-skeleton.md` (일일 스켈레톤) — 변경 없음
- `integrated-report-skeleton.md` (통합 일일 스켈레톤) — 변경 없음
- `sources.yaml`, `sources-arxiv.yaml` — 변경 없음
- `orchestrator-protocol.md` — 변경 없음 (VEV/Pipeline Gates 그대로)
- WF1/WF2 `data_root` 하위 모든 파일 — 쓰기 접근 없음

---

## 10. 구현 검증 프로토콜

구현 완료 후 아래 명령이 모두 성공해야 합니다:

```bash
# 1. SOT 검증 (SOT-017~019 포함, weekly skeleton 없으면 HALT)
python3 env-scanning/scripts/validate_registry.py env-scanning/config/workflow-registry.yaml

# 2. 주간 보고서 검증 (weekly 프로파일로, 섹션 헤더 불일치 시 FAIL)
python3 env-scanning/scripts/validate_report.py \
  env-scanning/integrated/weekly/reports/weekly-scan-2026-W06.md \
  --profile weekly

# 3. SCG-L5 검증 (주간 메타데이터 ↔ 일일 데이터 일관성)
python3 env-scanning/scripts/validate_state_consistency.py \
  --date 2026-02-06 --layer SCG-L5

# 4. 역검증: weekly skeleton 삭제 후 SOT 검증이 HALT되는지 확인
mv references/weekly-report-skeleton.md /tmp/
python3 env-scanning/scripts/validate_registry.py  # 반드시 exit code 1
mv /tmp/weekly-report-skeleton.md references/       # 복원
```

---

## 11. 리스크 분석

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 일일 스캔 데이터 부족 (5일 미만) | 중 | 중 | PEC-003이 사전 차단 + 사용자 확인 |
| 주간 보고서가 일일과 내용 중복 | 높음 | 중 | 스켈레톤의 섹션 구조 자체가 다름 → 추세/메타분석 관점 강제 |
| SOT 추가로 기존 검증 깨짐 | 낮음 | 높음 | 기존 블록 수정 없음, 추가만. 구현 후 기존 16개 체크 통과 확인 |
| validate_report.py SEC-001 분기 실수 | 중 | 높음 | 기존 3개 프로파일의 테스트 케이스 회귀 확인 |
| SCG-L5 함수 미등록 → 조용히 PASS | 높음 | 높음 | 역검증: 의도적 불일치 데이터로 FAIL 확인 |

---

## 12. 승인 요청 사항

1. **구현 범위**: 위 6개 파일 수정 + 4개 파일 생성을 한 번에 진행할지?
2. **주간 ID 체계**: ISO 8601 주번호 (`2026-W06`) 사용 동의?
3. **주간 체크포인트**: 2개 (분석 리뷰 + 보고서 승인) 적절?
4. **캘리브레이션 연동**: `thresholds.yaml`의 `calibration.frequency: "weekly"`와
   주간 보고서의 "시스템 성능 리뷰" 섹션을 연동할지?
5. **구현 검증 프로토콜**: 섹션 10의 4개 검증 명령을 모두 통과해야 구현 완료로 인정할지?

---

**작성자**: Claude Code (claude-opus-4-6)
**검토 상태**: 사용자 검토 대기 (v0.2.0 — SOT 실작동 검증 반영)
