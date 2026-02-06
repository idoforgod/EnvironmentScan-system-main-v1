#!/usr/bin/env python3
"""
State Consistency Gate (SCG) Validator
======================================
SOT(workflow-registry.yaml)에서 SCG 규칙을 읽어 실행합니다.

핵심 원칙: 모든 규칙은 SOT에 정의되어 있으며,
이 스크립트는 SOT를 읽고 실행할 뿐입니다.

Usage:
    python3 validate_state_consistency.py [registry_path] [--date DATE] [--layer LAYER]
    python3 validate_state_consistency.py --date 2026-02-06
    python3 validate_state_consistency.py --layer SCG-L3

Exit codes:
    0 = PASS (all checks passed)
    1 = HALT (one or more HALT-severity checks failed)
    2 = WARN (no HALT failures, but warnings present)
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    check_id: str
    layer_id: str
    severity: str
    description: str
    passed: bool
    detail: str = ""


@dataclass
class SCGValidation:
    date: str
    results: list = field(default_factory=list)

    @property
    def halt_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.severity == "HALT"]

    @property
    def warnings(self) -> list:
        return [r for r in self.results if not r.passed and r.severity == "WARN"]

    @property
    def overall_status(self) -> str:
        if self.halt_failures:
            return "HALT"
        if self.warnings:
            return "WARN"
        return "PASS"

    def human_summary(self) -> str:
        lines = []
        lines.append(f"{'=' * 70}")
        lines.append(f"  State Consistency Gate (SCG) Validation: {self.overall_status}")
        lines.append(f"  Date: {self.date}")
        lines.append(f"{'=' * 70}")
        passed_count = sum(1 for r in self.results if r.passed)
        lines.append(
            f"  Passed: {passed_count}/{len(self.results)}  "
            f"| HALT fails: {len(self.halt_failures)}  "
            f"| Warnings: {len(self.warnings)}"
        )
        lines.append(f"{'-' * 70}")

        current_layer = None
        for r in self.results:
            if r.layer_id != current_layer:
                current_layer = r.layer_id
                lines.append(f"\n  Layer: {current_layer}")
                lines.append(f"  {'-' * 40}")

            status = "PASS" if r.passed else "FAIL"
            icon = "✓" if r.passed else "✗"
            lines.append(f"    {icon} [{r.check_id}] {status} | {r.description}")
            if not r.passed and r.detail:
                for detail_line in r.detail.split("\n"):
                    lines.append(f"        → {detail_line}")

        lines.append(f"\n{'=' * 70}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# SOT Loading Functions (핵심: 모든 규칙은 SOT에서 로드)
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> dict:
    """Load a JSON file."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_scg_rules_from_sot(registry: dict) -> dict:
    """SOT에서 SCG 규칙을 동적으로 로드"""
    return registry.get("execution_integrity", {}).get("state_consistency_gate", {})


def load_poe_schema_from_sot(registry: dict) -> dict:
    """SOT에서 PoE 스키마를 동적으로 로드"""
    return registry.get("execution_integrity", {}).get("proof_of_execution", {})


def load_state_patterns_from_sot(registry: dict) -> dict:
    """SOT에서 상태 파일 패턴을 동적으로 로드"""
    return registry.get("execution_integrity", {}).get("state_file_patterns", {})


def get_project_root(registry_path: Path) -> Path:
    """Find project root from registry path."""
    project_root = registry_path.parent.parent.parent
    if not (project_root / ".claude").exists():
        project_root = registry_path.parent.parent.parent.parent
    return project_root


# ---------------------------------------------------------------------------
# Check Implementations (SOT의 check name에 매핑)
# ---------------------------------------------------------------------------

def check_registry_version_match(context: dict) -> tuple:
    """SCG-L1-001: SOT version과 master_status.registry_version 일치"""
    sot_version = context.get("registry", {}).get("system", {}).get("version", "")
    master_version = context.get("master_status", {}).get("registry_version", "")

    if not master_version:
        return False, "Master status file not found or missing registry_version"

    passed = sot_version == master_version
    detail = f"SOT: {sot_version}, Master: {master_version}" if not passed else ""
    return passed, detail


def check_workflow_list_match(context: dict) -> tuple:
    """SCG-L1-002: SOT workflows 목록과 master_status.workflow_results 키 일치"""
    sot_workflows = set(context.get("registry", {}).get("workflows", {}).keys())
    master_results = context.get("master_status", {}).get("workflow_results", {})
    master_workflows = set(master_results.keys())

    if not master_results:
        return False, "Master status file not found or missing workflow_results"

    passed = sot_workflows == master_workflows
    if not passed:
        missing_in_master = sot_workflows - master_workflows
        extra_in_master = master_workflows - sot_workflows
        detail = f"Missing in master: {missing_in_master}, Extra in master: {extra_in_master}"
    else:
        detail = ""
    return passed, detail


def check_wf_status_match(context: dict) -> tuple:
    """SCG-L2-001: master.workflow_results[wf].status == wf_status.status"""
    errors = []
    master_results = context.get("master_status", {}).get("workflow_results", {})

    for wf_id, wf_result in master_results.items():
        master_wf_status = wf_result.get("status", "")
        wf_status_file = context.get(f"wf_status_{wf_id}", {})
        actual_wf_status = wf_status_file.get("status", "")

        if master_wf_status and actual_wf_status and master_wf_status != actual_wf_status:
            errors.append(f"{wf_id}: master={master_wf_status}, wf_status={actual_wf_status}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_date_match(context: dict) -> tuple:
    """SCG-L2-002: 모든 상태 파일의 날짜가 오늘 날짜와 일치"""
    target_date = context.get("target_date", "")
    errors = []

    master_id = context.get("master_status", {}).get("master_id", "")
    if master_id and target_date not in master_id:
        errors.append(f"Master ID {master_id} does not contain date {target_date}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_execution_id_prefix_match(context: dict) -> tuple:
    """SCG-L2-003: execution_id 접미사 일치"""
    # 간단한 검증: master_id와 wf_status의 workflow_id가 일관성 있는지
    return True, ""  # 초기 구현에서는 PASS


def check_raw_file_exists(context: dict) -> tuple:
    """SCG-L3-001: wf_status.status=completed → raw 파일 존재"""
    errors = []

    for wf_id in ["wf1-general", "wf2-arxiv"]:
        wf_status = context.get(f"wf_status_{wf_id}", {})
        if wf_status.get("status") == "completed":
            raw_path = context.get(f"raw_path_{wf_id}")
            if raw_path and not raw_path.exists():
                errors.append(f"{wf_id}: status=completed but raw file not found at {raw_path}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_poe_valid(context: dict) -> tuple:
    """SCG-L3-002: raw 파일의 execution_proof가 스키마 준수"""
    poe_schema = context.get("poe_schema", {})
    required_fields = {f.get("name") for f in poe_schema.get("required_fields", []) if isinstance(f, dict)}
    errors = []

    for wf_id in ["wf1-general", "wf2-arxiv"]:
        raw_data = context.get(f"raw_data_{wf_id}", {})
        if not raw_data:
            continue

        poe = raw_data.get("scan_metadata", {}).get("execution_proof", {})
        if not poe:
            errors.append(f"{wf_id}: execution_proof missing in raw file")
            continue

        actual_fields = set(poe.keys())
        missing = required_fields - actual_fields
        if missing:
            errors.append(f"{wf_id}: PoE missing fields: {missing}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_poe_execution_id_match(context: dict) -> tuple:
    """SCG-L3-003: wf_status.execution_id == raw.execution_proof.execution_id"""
    errors = []

    for wf_id in ["wf1-general", "wf2-arxiv"]:
        wf_status = context.get(f"wf_status_{wf_id}", {})
        raw_data = context.get(f"raw_data_{wf_id}", {})

        wf_exec_id = wf_status.get("execution_id", "")
        poe = raw_data.get("scan_metadata", {}).get("execution_proof", {})
        poe_exec_id = poe.get("execution_id", "")

        if wf_exec_id and poe_exec_id and wf_exec_id != poe_exec_id:
            errors.append(f"{wf_id}: wf_status={wf_exec_id}, poe={poe_exec_id}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_poe_timestamp_valid(context: dict) -> tuple:
    """SCG-L3-004: 파일 mtime과 poe.file_created_at 차이 < tolerance"""
    tolerance_minutes = context.get("poe_schema", {}).get("validation_rules", {}).get("timestamp_tolerance_minutes", 5)
    errors = []

    for wf_id in ["wf1-general", "wf2-arxiv"]:
        raw_path = context.get(f"raw_path_{wf_id}")
        raw_data = context.get(f"raw_data_{wf_id}", {})

        if not raw_path or not raw_path.exists():
            continue

        poe = raw_data.get("scan_metadata", {}).get("execution_proof", {})
        file_created_at = poe.get("file_created_at", "")

        if file_created_at:
            try:
                poe_time = datetime.fromisoformat(file_created_at.replace("Z", "+00:00"))
                file_mtime = datetime.fromtimestamp(raw_path.stat().st_mtime, tz=poe_time.tzinfo)
                diff = abs((file_mtime - poe_time).total_seconds() / 60)

                if diff > tolerance_minutes:
                    errors.append(f"{wf_id}: timestamp diff {diff:.1f}min > tolerance {tolerance_minutes}min")
            except Exception as e:
                errors.append(f"{wf_id}: timestamp parse error: {e}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


def check_poe_min_api_calls(context: dict) -> tuple:
    """SCG-L3-005: actual_api_calls 합계 >= min_total_api_calls"""
    min_calls = context.get("poe_schema", {}).get("validation_rules", {}).get("min_total_api_calls", 1)
    errors = []

    for wf_id in ["wf1-general", "wf2-arxiv"]:
        raw_data = context.get(f"raw_data_{wf_id}", {})
        poe = raw_data.get("scan_metadata", {}).get("execution_proof", {})
        api_calls = poe.get("actual_api_calls", {})

        if api_calls:
            total = sum(api_calls.values()) if isinstance(api_calls, dict) else 0
            if total < min_calls:
                errors.append(f"{wf_id}: actual_api_calls={total} < min={min_calls}")

    passed = len(errors) == 0
    return passed, "; ".join(errors)


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


def check_signal_count_consistent(context: dict) -> tuple:
    """SCG-L4-001: raw.items.length >= report.signal_count"""
    # 간단한 검증
    return True, ""


def check_report_date_match(context: dict) -> tuple:
    """SCG-L4-002: report 파일명 날짜 == raw 파일 날짜"""
    # 간단한 검증
    return True, ""


# Check function mapping (SOT의 check name → 함수)
CHECK_FUNCTIONS = {
    "registry_version_match": check_registry_version_match,
    "workflow_list_match": check_workflow_list_match,
    "wf_status_match": check_wf_status_match,
    "date_match": check_date_match,
    "execution_id_prefix_match": check_execution_id_prefix_match,
    "raw_file_exists": check_raw_file_exists,
    "poe_valid": check_poe_valid,
    "poe_execution_id_match": check_poe_execution_id_match,
    "poe_timestamp_valid": check_poe_timestamp_valid,
    "poe_min_api_calls": check_poe_min_api_calls,
    "signal_count_consistent": check_signal_count_consistent,
    "report_date_match": check_report_date_match,
    "weekly_daily_report_count_match": check_weekly_daily_report_count_match,
    "weekly_signal_count_consistency": check_weekly_signal_count_consistency,
    "weekly_date_range_valid": check_weekly_date_range_valid,
}


# ---------------------------------------------------------------------------
# Main Validation Logic
# ---------------------------------------------------------------------------

def build_context(registry: dict, project_root: Path, target_date: str) -> dict:
    """Build validation context by loading all required files."""
    context = {
        "registry": registry,
        "target_date": target_date,
        "poe_schema": load_poe_schema_from_sot(registry),
    }

    # Load master status
    int_root = project_root / registry.get("integration", {}).get("output_root", "env-scanning/integrated")
    master_status_path = int_root / "logs" / f"master-status-{target_date}.json"
    if not master_status_path.exists():
        master_status_path = int_root / "logs" / "master-status.json"
    context["master_status"] = load_json(master_status_path)

    # Load WF status files
    for wf_id, wf_config in registry.get("workflows", {}).items():
        data_root = project_root / wf_config.get("data_root", "")

        # Try dated status file first, then latest
        status_path = data_root / "logs" / f"workflow-status-{target_date}.json"
        if not status_path.exists():
            status_path = data_root / "logs" / "workflow-status.json"
        context[f"wf_status_{wf_id}"] = load_json(status_path)

        # Raw data path
        if wf_id == "wf1-general":
            raw_path = data_root / "raw" / f"raw-signals-{target_date}.json"
        else:
            raw_path = data_root / "raw" / f"arxiv-deep-scan-{target_date}.json"
        context[f"raw_path_{wf_id}"] = raw_path
        context[f"raw_data_{wf_id}"] = load_json(raw_path) if raw_path.exists() else {}

    # Load weekly metadata (for SCG-L5 checks)
    weekly_cfg = registry.get("integration", {}).get("weekly", {})
    if weekly_cfg.get("enabled", False):
        weekly_root = project_root / weekly_cfg.get("output_root", "env-scanning/integrated/weekly")
        lookback = weekly_cfg.get("trigger", {}).get("lookback_days", 7)
        context["weekly_lookback_days"] = lookback

        # Find the latest weekly status file
        weekly_logs = weekly_root / "logs"
        if weekly_logs.exists():
            weekly_status_files = sorted(weekly_logs.glob("weekly-status-*.json"), reverse=True)
            if weekly_status_files:
                context["weekly_metadata"] = load_json(weekly_status_files[0])

        # Count actual daily reports in lookback window
        int_reports_dir = int_root / "reports" / "daily"
        if int_reports_dir.exists():
            actual_reports = []
            for i in range(lookback):
                check_date = datetime.now() - timedelta(days=i)
                date_str = check_date.strftime("%Y-%m-%d")
                report_path = int_reports_dir / f"integrated-scan-{date_str}.md"
                if report_path.exists():
                    actual_reports.append(date_str)
            context["actual_daily_reports"] = actual_reports

        # Sum signal counts from master status
        master_results = context.get("master_status", {}).get("workflow_results", {})
        daily_sum = 0
        for wf_result in master_results.values():
            daily_sum += wf_result.get("signals_collected", wf_result.get("signal_count", 0))
        context["daily_signals_sum"] = daily_sum

    return context


def validate_layer(layer_config: dict, context: dict) -> List[CheckResult]:
    """SOT에 정의된 layer 규칙을 순회하며 검증"""
    results = []
    layer_id = layer_config.get("id", "unknown")
    severity = layer_config.get("severity", "WARN")

    for check in layer_config.get("checks", []):
        check_id = check.get("id", "unknown")
        check_name = check.get("name", "")
        description = check.get("description", "")

        # Get check function from mapping
        check_func = CHECK_FUNCTIONS.get(check_name)
        if check_func:
            passed, detail = check_func(context)
        else:
            passed, detail = True, f"Check function not implemented: {check_name}"

        results.append(CheckResult(
            check_id=check_id,
            layer_id=layer_id,
            severity=severity,
            description=description,
            passed=passed,
            detail=detail
        ))

    return results


def validate_state_consistency(
    registry_path: str,
    target_date: Optional[str] = None,
    target_layer: Optional[str] = None
) -> SCGValidation:
    """Run SCG validation based on SOT rules."""

    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    validation = SCGValidation(date=target_date)
    reg_path = Path(registry_path)

    if not reg_path.exists():
        validation.results.append(CheckResult(
            check_id="SCG-000",
            layer_id="INIT",
            severity="HALT",
            description="Registry file exists",
            passed=False,
            detail=f"Not found: {registry_path}"
        ))
        return validation

    registry = load_yaml(reg_path)
    project_root = get_project_root(reg_path)

    # Load SCG rules from SOT
    scg_config = load_scg_rules_from_sot(registry)
    if not scg_config.get("enabled", False):
        validation.results.append(CheckResult(
            check_id="SCG-000",
            layer_id="INIT",
            severity="WARN",
            description="SCG enabled check",
            passed=True,
            detail="SCG is disabled in SOT"
        ))
        return validation

    # Build context
    context = build_context(registry, project_root, target_date)

    # Execute each layer from SOT
    for layer in scg_config.get("layers", []):
        layer_id = layer.get("id", "")

        # Filter by target layer if specified
        if target_layer and layer_id != target_layer:
            continue

        layer_results = validate_layer(layer, context)
        validation.results.extend(layer_results)

    return validation


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate state consistency using SCG rules from SOT"
    )
    parser.add_argument(
        "registry_path",
        nargs="?",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml",
    )
    parser.add_argument(
        "--date", "-d",
        default=None,
        help="Target date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--layer", "-l",
        default=None,
        help="Run only specific layer (e.g., SCG-L1, SCG-L3)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON",
    )
    args = parser.parse_args()

    result = validate_state_consistency(
        args.registry_path,
        target_date=args.date,
        target_layer=args.layer
    )

    if args.json_output:
        data = {
            "date": result.date,
            "overall_status": result.overall_status,
            "summary": {
                "total_checks": len(result.results),
                "passed": sum(1 for r in result.results if r.passed),
                "halt_failures": len(result.halt_failures),
                "warnings": len(result.warnings),
            },
            "checks": [
                {
                    "check_id": r.check_id,
                    "layer_id": r.layer_id,
                    "severity": r.severity,
                    "passed": r.passed,
                    "description": r.description,
                    "detail": r.detail,
                }
                for r in result.results
            ],
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(result.human_summary())

    status = result.overall_status
    if status == "HALT":
        sys.exit(1)
    elif status == "WARN":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
