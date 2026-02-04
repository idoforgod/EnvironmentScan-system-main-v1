#!/usr/bin/env python3
"""
Workflow Registry Validator
============================
Validates workflow-registry.yaml (SOT) at startup.
Ensures all referenced files exist, directories are ready,
and workflow configurations are consistent.

Usage:
    python3 validate_registry.py [registry_path]
    python3 validate_registry.py env-scanning/config/workflow-registry.yaml

Exit codes:
    0 = PASS (all checks passed, directories created as needed)
    1 = HALT (one or more HALT-severity checks failed)
    2 = WARN (no HALT failures, but warnings present)
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

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
    severity: str  # HALT | CREATE | WARN
    description: str
    passed: bool
    detail: str = ""
    action_taken: str = ""


@dataclass
class RegistryValidation:
    registry_path: str
    results: list = field(default_factory=list)

    @property
    def halt_failures(self) -> list:
        return [r for r in self.results if not r.passed and r.severity == "HALT"]

    @property
    def warnings(self) -> list:
        return [r for r in self.results if not r.passed and r.severity == "WARN"]

    @property
    def creates(self) -> list:
        return [r for r in self.results if r.severity == "CREATE" and r.action_taken]

    @property
    def overall_status(self) -> str:
        if self.halt_failures:
            return "HALT"
        if self.warnings:
            return "WARN"
        return "PASS"

    def human_summary(self) -> str:
        lines = []
        lines.append(f"{'=' * 65}")
        lines.append(f"  SOT Registry Validation: {self.overall_status}")
        lines.append(f"  File: {self.registry_path}")
        lines.append(f"{'=' * 65}")
        passed_count = sum(1 for r in self.results if r.passed)
        lines.append(
            f"  Passed: {passed_count}/{len(self.results)}  "
            f"| HALT fails: {len(self.halt_failures)}  "
            f"| Warnings: {len(self.warnings)}  "
            f"| Dirs created: {len(self.creates)}"
        )
        lines.append(f"{'-' * 65}")

        for r in self.results:
            if r.passed:
                icon = "PASS"
            elif r.severity == "HALT":
                icon = "HALT"
            elif r.severity == "CREATE":
                icon = "CREA"
            else:
                icon = "WARN"
            status = "OK" if r.passed else "FAIL"
            lines.append(f"  [{r.check_id}] {r.severity:6s} {status:4s} | {r.description}")
            if not r.passed and r.detail:
                for detail_line in r.detail.split("\n"):
                    lines.append(f"      -> {detail_line}")
            if r.action_taken:
                lines.append(f"      ** {r.action_taken}")

        lines.append(f"{'=' * 65}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(base: Path, rel_path: str) -> Path:
    """Resolve a relative path against the project root."""
    return base / rel_path


def _file_exists(base: Path, rel_path: str) -> bool:
    return _resolve(base, rel_path).exists()


def _dir_exists(base: Path, rel_path: str) -> bool:
    return _resolve(base, rel_path).is_dir()


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_enabled_sources(base: Path, sources_config_path: str) -> list:
    """Return list of enabled source names from a sources.yaml file."""
    full_path = _resolve(base, sources_config_path)
    if not full_path.exists():
        return []
    data = _load_yaml(full_path)
    sources = data.get("sources", [])
    return [s["name"] for s in sources if s.get("enabled", False)]


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def validate_registry(registry_path: str) -> RegistryValidation:
    """Run all startup validation checks."""
    vr = RegistryValidation(registry_path=registry_path)
    reg_path = Path(registry_path)

    if not reg_path.exists():
        vr.results.append(CheckResult(
            "SOT-000", "HALT", "Registry file exists",
            False, f"Not found: {registry_path}"
        ))
        return vr

    registry = _load_yaml(reg_path)

    # Project root: walk up from registry file to find .claude/ directory
    # Registry is at env-scanning/config/workflow-registry.yaml
    # Project root is 3 levels up
    project_root = reg_path.parent.parent.parent
    if not (project_root / ".claude").exists():
        # Try one more level
        project_root = reg_path.parent.parent.parent.parent
    if not (project_root / ".claude").exists():
        vr.results.append(CheckResult(
            "SOT-000", "HALT", "Project root detection",
            False, f"Cannot find .claude/ directory from {reg_path}"
        ))
        return vr

    system = registry.get("system", {})
    workflows = registry.get("workflows", {})
    integration = registry.get("integration", {})
    rules = registry.get("startup_validation", {}).get("rules", [])

    # ── SOT-001: All shared invariants exist ──
    shared = system.get("shared_invariants", {})
    missing = [k for k, v in shared.items() if not _file_exists(project_root, v)]
    vr.results.append(CheckResult(
        "SOT-001", "HALT",
        "All shared invariant files exist",
        len(missing) == 0,
        f"Missing: {missing}" if missing else ""
    ))

    # ── SOT-002: All orchestrator files exist ──
    missing_orch = []
    for wf_id, wf in workflows.items():
        orch = wf.get("orchestrator", "")
        if not _file_exists(project_root, orch):
            missing_orch.append(f"{wf_id}: {orch}")
    master = system.get("execution", {}).get("master_orchestrator", "")
    if master and not _file_exists(project_root, master):
        missing_orch.append(f"master: {master}")
    vr.results.append(CheckResult(
        "SOT-002", "HALT",
        "All orchestrator files exist",
        len(missing_orch) == 0,
        f"Missing: {missing_orch}" if missing_orch else ""
    ))

    # ── SOT-003: All sources config files exist ──
    missing_src = []
    for wf_id, wf in workflows.items():
        src = wf.get("sources_config", "")
        if not _file_exists(project_root, src):
            missing_src.append(f"{wf_id}: {src}")
    vr.results.append(CheckResult(
        "SOT-003", "HALT",
        "All sources config files exist",
        len(missing_src) == 0,
        f"Missing: {missing_src}" if missing_src else ""
    ))

    # ── SOT-004: All shared workers exist ──
    workers = system.get("shared_workers", [])
    missing_w = [w for w in workers if not _file_exists(project_root, w)]
    vr.results.append(CheckResult(
        "SOT-004", "HALT",
        "All shared worker agent files exist",
        len(missing_w) == 0,
        f"Missing: {missing_w}" if missing_w else ""
    ))

    # ── SOT-005: All data root directories exist (create if missing) ──
    created_dirs = []
    for wf_id, wf in workflows.items():
        data_root = wf.get("data_root", "")
        root_path = _resolve(project_root, data_root)
        paths = wf.get("paths", {})
        for path_key, rel in paths.items():
            full = root_path / rel
            if not full.exists():
                full.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full.relative_to(project_root)))
    vr.results.append(CheckResult(
        "SOT-005", "CREATE",
        "All workflow data directories exist",
        True,  # Always passes (creates missing dirs)
        "",
        f"Created {len(created_dirs)} directories" if created_dirs else ""
    ))

    # ── SOT-006: Integration output root exists ──
    int_created = []
    int_root = integration.get("output_root", "")
    if int_root:
        int_root_path = _resolve(project_root, int_root)
        for path_key, rel in integration.get("paths", {}).items():
            full = int_root_path / rel
            if not full.exists():
                full.mkdir(parents=True, exist_ok=True)
                int_created.append(str(full.relative_to(project_root)))
        # Also create signals/ for integrated
        signals_dir = int_root_path / "signals"
        if not signals_dir.exists():
            signals_dir.mkdir(parents=True, exist_ok=True)
            int_created.append(str(signals_dir.relative_to(project_root)))
    vr.results.append(CheckResult(
        "SOT-006", "CREATE",
        "Integration output directories exist",
        True,
        "",
        f"Created {len(int_created)} directories" if int_created else ""
    ))

    # ── SOT-007: Execution order unique and sequential ──
    orders = []
    for wf_id, wf in workflows.items():
        if wf.get("enabled", False):
            orders.append(wf.get("execution_order", 0))
    orders_sorted = sorted(orders)
    is_sequential = orders_sorted == list(range(1, len(orders_sorted) + 1))
    is_unique = len(orders) == len(set(orders))
    vr.results.append(CheckResult(
        "SOT-007", "HALT",
        "Execution order values are unique and sequential",
        is_sequential and is_unique,
        f"Orders: {orders}" if not (is_sequential and is_unique) else ""
    ))

    # ── SOT-008: Protocol file exists ──
    protocol = system.get("execution", {}).get("protocol", "")
    proto_exists = _file_exists(project_root, protocol) if protocol else False
    vr.results.append(CheckResult(
        "SOT-008", "HALT",
        "Orchestrator protocol file exists",
        proto_exists,
        f"Missing: {protocol}" if not proto_exists else ""
    ))

    # ── SOT-009: Integrated skeleton exists ──
    int_skel = integration.get("integrated_skeleton", "")
    skel_exists = _file_exists(project_root, int_skel) if int_skel else False
    vr.results.append(CheckResult(
        "SOT-009", "HALT",
        "Integrated report skeleton exists",
        skel_exists,
        f"Missing: {int_skel}" if not skel_exists else ""
    ))

    # ── SOT-010: arXiv disabled in WF1 ──
    wf1_src = workflows.get("wf1-general", {}).get("sources_config", "")
    wf1_enabled = _get_enabled_sources(project_root, wf1_src) if wf1_src else []
    arxiv_in_wf1 = "arXiv" in wf1_enabled
    vr.results.append(CheckResult(
        "SOT-010", "HALT",
        "arXiv source is disabled in WF1 sources config",
        not arxiv_in_wf1,
        "arXiv is still enabled in WF1 sources.yaml" if arxiv_in_wf1 else ""
    ))

    # ── SOT-011: arXiv enabled in WF2 ──
    wf2_src = workflows.get("wf2-arxiv", {}).get("sources_config", "")
    wf2_enabled = _get_enabled_sources(project_root, wf2_src) if wf2_src else []
    arxiv_in_wf2 = "arXiv" in wf2_enabled
    vr.results.append(CheckResult(
        "SOT-011", "HALT",
        "arXiv source is enabled in WF2 sources config",
        arxiv_in_wf2,
        f"arXiv not found as enabled in WF2 (found: {wf2_enabled})" if not arxiv_in_wf2 else ""
    ))

    # ── SOT-012: No source overlap ──
    overlap = set(wf1_enabled) & set(wf2_enabled)
    vr.results.append(CheckResult(
        "SOT-012", "HALT",
        "No enabled source overlap between WF1 and WF2",
        len(overlap) == 0,
        f"Overlapping sources: {overlap}" if overlap else ""
    ))

    # ── SOT-013: Merger agent exists ──
    merger = integration.get("merger_agent", "")
    merger_exists = _file_exists(project_root, merger) if merger else False
    vr.results.append(CheckResult(
        "SOT-013", "HALT",
        "Integration merger agent file exists",
        merger_exists,
        f"Missing: {merger}" if not merger_exists else ""
    ))

    return vr


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validate workflow registry (SOT) at startup"
    )
    parser.add_argument(
        "registry_path",
        nargs="?",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output as JSON",
    )
    args = parser.parse_args()

    result = validate_registry(args.registry_path)

    if args.json_output:
        data = {
            "registry_path": result.registry_path,
            "overall_status": result.overall_status,
            "summary": {
                "total_checks": len(result.results),
                "passed": sum(1 for r in result.results if r.passed),
                "halt_failures": len(result.halt_failures),
                "warnings": len(result.warnings),
                "dirs_created": len(result.creates),
            },
            "checks": [
                {
                    "check_id": r.check_id,
                    "severity": r.severity,
                    "passed": r.passed,
                    "description": r.description,
                    "detail": r.detail,
                    "action_taken": r.action_taken,
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
