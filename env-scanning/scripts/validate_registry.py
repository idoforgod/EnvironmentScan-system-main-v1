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
from datetime import datetime, timezone
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

    # ── SOT-012: No source overlap between any workflow pair ──
    # Generalized: check all enabled workflow pairs for source overlap
    all_wf_sources = {}
    for wf_id, wf in workflows.items():
        if wf.get("enabled", False):
            src_cfg = wf.get("sources_config", "")
            all_wf_sources[wf_id] = set(_get_enabled_sources(project_root, src_cfg))

    overlap_found = False
    overlap_details = []
    wf_ids = sorted(all_wf_sources.keys())
    for i in range(len(wf_ids)):
        for j in range(i + 1, len(wf_ids)):
            pair_overlap = all_wf_sources[wf_ids[i]] & all_wf_sources[wf_ids[j]]
            if pair_overlap:
                overlap_found = True
                overlap_details.append(
                    f"{wf_ids[i]}↔{wf_ids[j]}: {pair_overlap}"
                )
    vr.results.append(CheckResult(
        "SOT-012", "HALT",
        "No enabled source overlap between any workflow pair",
        not overlap_found,
        "; ".join(overlap_details) if overlap_details else ""
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

    # ── SOT-029: Integration method is valid (v2.1.0) ──
    valid_methods = {"agent-team", "single-agent"}
    int_method = integration.get("integration_method", "")
    method_valid = int_method in valid_methods
    vr.results.append(CheckResult(
        "SOT-029", "HALT",
        "Integration method is a valid value",
        method_valid,
        f"Got '{int_method}', expected one of {valid_methods}" if not method_valid else ""
    ))

    # ── SOT-014: execution_integrity section exists ──
    exec_integrity = registry.get("execution_integrity", {})
    ei_exists = bool(exec_integrity) and exec_integrity.get("version") is not None
    vr.results.append(CheckResult(
        "SOT-014", "HALT",
        "execution_integrity section exists in registry",
        ei_exists,
        "Missing execution_integrity section or version" if not ei_exists else ""
    ))

    # ── SOT-015: SCG rules valid ──
    scg = exec_integrity.get("state_consistency_gate", {})
    scg_layers = scg.get("layers", [])
    scg_valid = True
    scg_errors = []
    for layer in scg_layers:
        if not all(k in layer for k in ["id", "name", "severity", "checks"]):
            scg_valid = False
            scg_errors.append(f"Layer {layer.get('id', 'unknown')} missing required fields")
        for check in layer.get("checks", []):
            if not all(k in check for k in ["id", "name", "description"]):
                scg_valid = False
                scg_errors.append(f"Check {check.get('id', 'unknown')} missing required fields")
    vr.results.append(CheckResult(
        "SOT-015", "HALT",
        "All SCG rules have required fields (id, name, severity, checks)",
        scg_valid,
        "; ".join(scg_errors) if scg_errors else ""
    ))

    # ── SOT-016: PoE schema valid ──
    poe = exec_integrity.get("proof_of_execution", {})
    poe_fields = poe.get("required_fields", [])
    required_poe_names = {"execution_id", "started_at", "completed_at", "actual_api_calls", "actual_sources_scanned", "file_created_at"}
    actual_poe_names = {f.get("name") for f in poe_fields if isinstance(f, dict)}
    poe_valid = required_poe_names.issubset(actual_poe_names)
    missing_poe = required_poe_names - actual_poe_names
    vr.results.append(CheckResult(
        "SOT-016", "HALT",
        "PoE schema has all required_fields defined",
        poe_valid,
        f"Missing PoE fields: {missing_poe}" if missing_poe else ""
    ))

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

    # ── SOT-018: Weekly output directories exist (create if missing) ──
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

    # ── SOT-019: Weekly validate_profile is defined ──
    if weekly_cfg.get("enabled", False):
        weekly_profile = weekly_cfg.get("validate_profile", "")
        vr.results.append(CheckResult(
            "SOT-019", "HALT",
            "Weekly validate_profile is defined",
            bool(weekly_profile),
            "Missing validate_profile in integration.weekly" if not weekly_profile else ""
        ))

    # ── SOT-020: WF3 Naver source exclusive (conditional) ──
    wf3_cfg = workflows.get("wf3-naver", {})
    if wf3_cfg.get("enabled", False):
        wf3_src = wf3_cfg.get("sources_config", "")
        wf3_enabled = _get_enabled_sources(project_root, wf3_src) if wf3_src else []
        naver_in_wf3 = "NaverNews" in wf3_enabled
        vr.results.append(CheckResult(
            "SOT-020", "HALT",
            "NaverNews source is enabled in WF3 sources config",
            naver_in_wf3,
            f"NaverNews not found as enabled in WF3 (found: {wf3_enabled})" if not naver_in_wf3 else ""
        ))

    # ── SOT-021: WF3 orchestrator exists (conditional) ──
    if wf3_cfg.get("enabled", False):
        wf3_orch = wf3_cfg.get("orchestrator", "")
        wf3_orch_exists = _file_exists(project_root, wf3_orch) if wf3_orch else False
        vr.results.append(CheckResult(
            "SOT-021", "HALT",
            "WF3 orchestrator file exists",
            wf3_orch_exists,
            f"Missing: {wf3_orch}" if not wf3_orch_exists else ""
        ))

    # ── SOT-022: WF3 data root exists (create if missing, conditional) ──
    if wf3_cfg.get("enabled", False):
        wf3_root = wf3_cfg.get("data_root", "")
        wf3_created = []
        if wf3_root:
            wf3_root_path = _resolve(project_root, wf3_root)
            for path_key, rel in wf3_cfg.get("paths", {}).items():
                full = wf3_root_path / rel
                if not full.exists():
                    full.mkdir(parents=True, exist_ok=True)
                    wf3_created.append(str(full.relative_to(project_root)))
        vr.results.append(CheckResult(
            "SOT-022", "CREATE",
            "WF3 data directories exist",
            True,
            "",
            f"Created {len(wf3_created)} directories" if wf3_created else ""
        ))

    # ── SOT-023: WF3 sources config exists (conditional) ──
    if wf3_cfg.get("enabled", False):
        wf3_src_cfg = wf3_cfg.get("sources_config", "")
        wf3_src_exists = _file_exists(project_root, wf3_src_cfg) if wf3_src_cfg else False
        vr.results.append(CheckResult(
            "SOT-023", "HALT",
            "WF3 sources config file exists",
            wf3_src_exists,
            f"Missing: {wf3_src_cfg}" if not wf3_src_exists else ""
        ))

    # ================================================================
    # SOT-051 ~ SOT-054: WF4 Multi&Global-News Validation (v2.10.0)
    # ================================================================
    wf4_cfg = workflows.get("wf4-multiglobal-news", {})

    # ── SOT-051: WF4 exclusive source exists (conditional) ──
    if wf4_cfg.get("enabled", False):
        wf4_src = wf4_cfg.get("sources_config", "")
        wf4_enabled = _get_enabled_sources(project_root, wf4_src) if wf4_src else []
        multiglobal_in_wf4 = "MultiGlobalNews" in wf4_enabled
        vr.results.append(CheckResult(
            "SOT-051", "HALT",
            "MultiGlobalNews source is enabled in WF4 sources config",
            multiglobal_in_wf4,
            f"MultiGlobalNews not found as enabled in WF4 (found: {wf4_enabled})" if not multiglobal_in_wf4 else ""
        ))

    # ── SOT-052: WF4 orchestrator exists (conditional) ──
    if wf4_cfg.get("enabled", False):
        wf4_orch = wf4_cfg.get("orchestrator", "")
        wf4_orch_exists = _file_exists(project_root, wf4_orch) if wf4_orch else False
        vr.results.append(CheckResult(
            "SOT-052", "HALT",
            "WF4 orchestrator file exists",
            wf4_orch_exists,
            f"Missing: {wf4_orch}" if not wf4_orch_exists else ""
        ))

    # ── SOT-053: WF4 data root exists (create if missing, conditional) ──
    if wf4_cfg.get("enabled", False):
        wf4_root = wf4_cfg.get("data_root", "")
        wf4_created = []
        if wf4_root:
            wf4_root_path = _resolve(project_root, wf4_root)
            for path_key, rel in wf4_cfg.get("paths", {}).items():
                full = wf4_root_path / rel
                if not full.exists():
                    full.mkdir(parents=True, exist_ok=True)
                    wf4_created.append(str(full.relative_to(project_root)))
        vr.results.append(CheckResult(
            "SOT-053", "CREATE",
            "WF4 data directories exist",
            True,
            "",
            f"Created {len(wf4_created)} directories" if wf4_created else ""
        ))

    # ── SOT-054: WF4 sources config exists (conditional) ──
    if wf4_cfg.get("enabled", False):
        wf4_src_cfg = wf4_cfg.get("sources_config", "")
        wf4_src_exists = _file_exists(project_root, wf4_src_cfg) if wf4_src_cfg else False
        vr.results.append(CheckResult(
            "SOT-054", "HALT",
            "WF4 sources config file exists",
            wf4_src_exists,
            f"Missing: {wf4_src_cfg}" if not wf4_src_exists else ""
        ))

    # ================================================================
    # SOT-024 ~ SOT-028: Cross-Platform System Prompt Validation
    # ================================================================
    sys_prompts = registry.get("system_prompts", {})

    # ── SOT-024: Canonical system prompt file (AGENTS.md) exists ──
    canonical = sys_prompts.get("canonical", "")
    canonical_exists = _file_exists(project_root, canonical) if canonical else False
    vr.results.append(CheckResult(
        "SOT-024", "HALT",
        "Canonical system prompt file (AGENTS.md) exists",
        canonical_exists,
        f"Missing: {canonical}" if not canonical_exists else ""
    ))

    # ── SOT-025: AGENTS.md contains all required SOT references ──
    if canonical_exists:
        canonical_path = _resolve(project_root, canonical)
        canonical_content = canonical_path.read_text(encoding="utf-8")
        required_refs = sys_prompts.get("required_references", [])
        missing_refs = [ref for ref in required_refs if ref not in canonical_content]
        vr.results.append(CheckResult(
            "SOT-025", "HALT",
            "AGENTS.md contains all required SOT file references",
            len(missing_refs) == 0,
            f"Missing references: {missing_refs}" if missing_refs else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-025", "HALT",
            "AGENTS.md contains all required SOT file references",
            False,
            "Cannot check — AGENTS.md does not exist (SOT-024 failed)"
        ))

    # ── SOT-026: AGENTS.md contains required immutable section keywords ──
    # Case-insensitive matching: keywords like "bilingual" match "Bilingual" in text
    if canonical_exists:
        canonical_content_lower = canonical_content.lower()
        inline_sections = sys_prompts.get("required_inline_sections", [])
        missing_kw = []
        for section in inline_sections:
            section_id = section.get("id", "")
            keywords = section.get("keywords", [])
            absent = [kw for kw in keywords if kw.lower() not in canonical_content_lower]
            if absent:
                missing_kw.append(f"{section_id}: {absent}")
        vr.results.append(CheckResult(
            "SOT-026", "HALT",
            "AGENTS.md contains all required immutable rule keywords",
            len(missing_kw) == 0,
            f"Missing keywords: {'; '.join(missing_kw)}" if missing_kw else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-026", "HALT",
            "AGENTS.md contains all required immutable rule keywords",
            False,
            "Cannot check — AGENTS.md does not exist (SOT-024 failed)"
        ))

    # ── SOT-026b: Structural value check — AGENTS.md Tier 1 vs core-invariants ──
    # Goes beyond keyword presence: verifies that specific immutable VALUES match.
    immutable_src = sys_prompts.get("immutable_source", "")
    struct_errors = []
    if canonical_exists and immutable_src:
        inv_path = _resolve(project_root, immutable_src)
        if inv_path.exists():
            core_inv = _load_yaml(inv_path)
            ci = core_inv.get("core_invariants", {})

            # Check 1: STEEPs category count matches
            steeps = ci.get("steeps_categories", {}).get("categories", [])
            expected_count = len(steeps)
            if expected_count > 0:
                # AGENTS.md should mention "exactly N categories" or "N categories"
                if f"{expected_count} categories" not in canonical_content_lower:
                    struct_errors.append(
                        f"STEEPs count: core-invariants has {expected_count} categories, "
                        f"but '{expected_count} categories' not found in AGENTS.md"
                    )

            # Check 2: Each STEEPs category name appears in AGENTS.md
            for cat in steeps:
                cat_name = cat.get("name", "")
                if cat_name and cat_name.lower() not in canonical_content_lower:
                    struct_errors.append(f"STEEPs category '{cat_name}' not found in AGENTS.md")

            # Check 3: VEV stages match
            vev_stages = ci.get("vev_protocol", {}).get("stages", [])
            for stage in vev_stages:
                if stage.lower() not in canonical_content_lower:
                    struct_errors.append(f"VEV stage '{stage}' not found in AGENTS.md")

            # Check 4: Phase names match
            phases = ci.get("workflow_phases", {}).get("phases", [])
            for phase in phases:
                phase_name = phase.get("name", "")
                if phase_name and phase_name.lower() not in canonical_content_lower:
                    struct_errors.append(f"Phase name '{phase_name}' not found in AGENTS.md")

    vr.results.append(CheckResult(
        "SOT-026b", "HALT",
        "AGENTS.md Tier 1 values match core-invariants.yaml",
        len(struct_errors) == 0,
        "; ".join(struct_errors) if struct_errors else ""
    ))

    # ── SOT-027: Tool-specific wrapper files exist ──
    tool_specific = sys_prompts.get("tool_specific", {})
    missing_tools = []
    for tool_name, tool_cfg in tool_specific.items():
        tool_file = tool_cfg.get("file", "") if isinstance(tool_cfg, dict) else ""
        if tool_file and not _file_exists(project_root, tool_file):
            missing_tools.append(f"{tool_name}: {tool_file}")
    vr.results.append(CheckResult(
        "SOT-027", "WARN",
        "Tool-specific system prompt files exist",
        len(missing_tools) == 0,
        f"Missing: {missing_tools}" if missing_tools else ""
    ))

    # ── SOT-028: Tool-specific files contain @import of AGENTS.md ──
    import_errors = []
    for tool_name, tool_cfg in tool_specific.items():
        tool_file = tool_cfg.get("file", "") if isinstance(tool_cfg, dict) else ""
        import_target = tool_cfg.get("import_target", "") if isinstance(tool_cfg, dict) else ""
        if tool_file and import_target:
            tool_path = _resolve(project_root, tool_file)
            if tool_path.exists():
                tool_content = tool_path.read_text(encoding="utf-8")
                # Check for @import pattern: @AGENTS.md or @./AGENTS.md
                if f"@{import_target}" not in tool_content and f"@./{import_target}" not in tool_content:
                    import_errors.append(f"{tool_name} ({tool_file}) missing @{import_target}")
    vr.results.append(CheckResult(
        "SOT-028", "WARN",
        "Tool-specific files contain @import of canonical file",
        len(import_errors) == 0,
        f"Missing imports: {import_errors}" if import_errors else ""
    ))

    # ================================================================
    # SOT-030 ~ SOT-031: Temporal Consistency Validation (v2.2.0)
    # ================================================================

    # ── SOT-030: scan_window valid for each enabled workflow ──
    sw_errors = []
    for wf_id, wf in workflows.items():
        if not wf.get("enabled", False):
            continue
        params = wf.get("parameters", {})
        sw = params.get("scan_window")
        if sw is None:
            sw_errors.append(f"{wf_id}: scan_window parameter missing")
            continue
        lh = sw.get("lookback_hours")
        if lh is None:
            sw_errors.append(f"{wf_id}: scan_window.lookback_hours missing")
        elif not isinstance(lh, (int, float)) or not (1 <= lh <= 168):
            sw_errors.append(f"{wf_id}: lookback_hours={lh} out of range [1, 168]")
        enforce = sw.get("enforce")
        if enforce not in ("strict", "lenient"):
            sw_errors.append(f"{wf_id}: scan_window.enforce='{enforce}' must be 'strict' or 'lenient'")
        if sw.get("post_filter") is None:
            sw_errors.append(f"{wf_id}: scan_window.post_filter missing")
    vr.results.append(CheckResult(
        "SOT-030", "HALT",
        "Each enabled workflow has valid scan_window parameters",
        len(sw_errors) == 0,
        "; ".join(sw_errors) if sw_errors else ""
    ))

    # ── SOT-031: system.temporal_consistency section exists ──
    tc = system.get("temporal_consistency", {})
    tc_errors = []
    if not tc:
        tc_errors.append("system.temporal_consistency section missing")
    else:
        if tc.get("enabled") is None:
            tc_errors.append("temporal_consistency.enabled missing")
        if not tc.get("anchor"):
            tc_errors.append("temporal_consistency.anchor missing")
        if tc.get("default_lookback_hours") is None:
            tc_errors.append("temporal_consistency.default_lookback_hours missing")
        elif not isinstance(tc.get("default_lookback_hours"), (int, float)):
            tc_errors.append("temporal_consistency.default_lookback_hours must be numeric")
    vr.results.append(CheckResult(
        "SOT-031", "HALT",
        "system.temporal_consistency section exists with required fields",
        len(tc_errors) == 0,
        "; ".join(tc_errors) if tc_errors else ""
    ))

    # ── SOT-032: Temporal Python enforcement scripts exist (v2.2.1) ──
    tc_scripts = {}
    tc_script_keys = ["anchor_script", "gate_script", "metadata_injector_script", "statistics_engine_script"]
    for key in tc_script_keys:
        script_path = tc.get(key, "")
        if script_path:
            tc_scripts[key] = script_path
    tc_script_errors = []
    for key, path in tc_scripts.items():
        if not _file_exists(project_root, path):
            tc_script_errors.append(f"{key}: {path}")
    # Also fail if none of the script keys are defined at all
    if not tc_scripts:
        tc_script_errors.append("No temporal script paths defined in system.temporal_consistency")
    vr.results.append(CheckResult(
        "SOT-032", "HALT",
        "Temporal/statistical Python enforcement scripts (anchor, gate, injector, statistics) exist",
        len(tc_script_errors) == 0,
        "; ".join(tc_script_errors) if tc_script_errors else ""
    ))

    # ================================================================
    # SOT-034 ~ SOT-035: Signal Evolution Validation (v2.3.0)
    # ================================================================
    sig_evo = system.get("signal_evolution", {})

    # ── SOT-034: signal_evolution section valid (conditional on enabled) ──
    if sig_evo.get("enabled", False):
        evo_errors = []
        # Tracker script must exist
        tracker_script = sig_evo.get("tracker_script", "")
        if not tracker_script:
            evo_errors.append("signal_evolution.tracker_script not defined")
        elif not _file_exists(project_root, tracker_script):
            evo_errors.append(f"tracker_script not found: {tracker_script}")
        # Matching thresholds must be in [0, 1]
        matching = sig_evo.get("matching", {})
        for key in ["title_similarity_threshold", "semantic_similarity_threshold", "high_confidence_threshold"]:
            val = matching.get(key)
            if val is not None:
                if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
                    evo_errors.append(f"matching.{key}={val} out of range [0.0, 1.0]")
            else:
                evo_errors.append(f"matching.{key} not defined")
        # Lifecycle thresholds (all 3 fields must exist and be valid)
        lifecycle = sig_evo.get("lifecycle", {})
        fade_days = lifecycle.get("fade_threshold_days")
        if fade_days is None:
            evo_errors.append("lifecycle.fade_threshold_days not defined")
        elif not isinstance(fade_days, int) or fade_days < 1:
            evo_errors.append(f"lifecycle.fade_threshold_days={fade_days} must be integer >= 1")
        max_age = lifecycle.get("max_thread_age_days")
        if max_age is None:
            evo_errors.append("lifecycle.max_thread_age_days not defined")
        elif not isinstance(max_age, int) or max_age < 1:
            evo_errors.append(f"lifecycle.max_thread_age_days={max_age} must be integer >= 1")
        min_vel = lifecycle.get("min_appearances_for_velocity")
        if min_vel is None:
            evo_errors.append("lifecycle.min_appearances_for_velocity not defined")
        elif not isinstance(min_vel, int) or min_vel < 1:
            evo_errors.append(f"lifecycle.min_appearances_for_velocity={min_vel} must be integer >= 1")
        # State detection thresholds
        state_det = sig_evo.get("state_detection", {})
        str_delta = state_det.get("strengthening_psst_delta")
        if str_delta is None:
            evo_errors.append("state_detection.strengthening_psst_delta not defined")
        elif not isinstance(str_delta, (int, float)):
            evo_errors.append(f"state_detection.strengthening_psst_delta must be numeric, got {type(str_delta).__name__}")
        weak_delta = state_det.get("weakening_psst_delta")
        if weak_delta is None:
            evo_errors.append("state_detection.weakening_psst_delta not defined")
        elif not isinstance(weak_delta, (int, float)):
            evo_errors.append(f"state_detection.weakening_psst_delta must be numeric, got {type(weak_delta).__name__}")
        # Cross-workflow correlation subsection validation
        cross_wf_corr = sig_evo.get("cross_workflow_correlation", {})
        if "cross_workflow_correlation" in sig_evo:
            cwc_enabled = cross_wf_corr.get("enabled")
            if cwc_enabled is None:
                evo_errors.append("cross_workflow_correlation.enabled not defined")
            elif not isinstance(cwc_enabled, bool):
                evo_errors.append(f"cross_workflow_correlation.enabled must be boolean, got {type(cwc_enabled).__name__}")
            cwc_output = cross_wf_corr.get("output_path", "")
            if cwc_enabled and not cwc_output:
                evo_errors.append("cross_workflow_correlation.output_path not defined (required when enabled)")
            # Cross-correlation matching thresholds (v2.3.1)
            cwc_matching = cross_wf_corr.get("matching", {})
            if cwc_enabled:
                for key in ["title_similarity_threshold", "semantic_similarity_threshold"]:
                    val = cwc_matching.get(key)
                    if val is not None:
                        if not isinstance(val, (int, float)) or not (0.0 <= val <= 1.0):
                            evo_errors.append(f"cross_workflow_correlation.matching.{key}={val} out of range [0.0, 1.0]")
                    else:
                        evo_errors.append(f"cross_workflow_correlation.matching.{key} not defined")
                # v1.3.0 L2 fix: Optional new fields (backward-compatible — tracker has defaults)
                hct = cwc_matching.get("high_confidence_threshold")
                if hct is not None:
                    if not isinstance(hct, (int, float)) or not (0.0 <= hct <= 1.0):
                        evo_errors.append(f"cross_workflow_correlation.matching.high_confidence_threshold={hct} out of range [0.0, 1.0]")
                cfe = cwc_matching.get("category_filter_enabled")
                if cfe is not None:
                    if not isinstance(cfe, bool):
                        evo_errors.append(f"cross_workflow_correlation.matching.category_filter_enabled must be boolean, got {type(cfe).__name__}")

        vr.results.append(CheckResult(
            "SOT-034", "HALT",
            "signal_evolution section valid (thresholds, tracker_script, cross_workflow_correlation)",
            len(evo_errors) == 0,
            "; ".join(evo_errors) if evo_errors else ""
        ))

        # ── SOT-035: evolution paths exist in enabled workflows ──
        evo_path_created = []
        for wf_id, wf in workflows.items():
            if not wf.get("enabled", False):
                continue
            wf_paths = wf.get("paths", {})
            data_root = wf.get("data_root", "")
            for path_key in ["evolution_index", "evolution_maps"]:
                rel = wf_paths.get(path_key, "")
                if not rel:
                    # Missing path declaration is noted but directories are created
                    continue
                full = _resolve(project_root, data_root) / rel
                parent = full.parent if path_key == "evolution_index" else full
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                    evo_path_created.append(str(parent.relative_to(project_root)))
        # Also create integration evolution output
        cross_wf = sig_evo.get("cross_workflow_correlation", {})
        if cross_wf.get("enabled", False):
            cross_path = cross_wf.get("output_path", "")
            if cross_path:
                int_root = integration.get("output_root", "")
                if int_root:
                    full = _resolve(project_root, int_root) / cross_path.replace("integrated/", "")
                    if not full.exists():
                        full.mkdir(parents=True, exist_ok=True)
                        evo_path_created.append(str(full.relative_to(project_root)))
        vr.results.append(CheckResult(
            "SOT-035", "CREATE",
            "Evolution paths exist in enabled workflows",
            True,
            "",
            f"Created {len(evo_path_created)} directories" if evo_path_created else ""
        ))

    # ── SOT-036: timeline_map configuration (optional, WARN level) ──
    # Timeline map is supplementary output — config errors should WARN, not HALT.
    tl_errors = []
    timeline_map = sig_evo.get("timeline_map", {})
    if timeline_map:
        tl_enabled = timeline_map.get("enabled")
        if tl_enabled is not None and not isinstance(tl_enabled, bool):
            tl_errors.append(f"timeline_map.enabled must be boolean, got {type(tl_enabled).__name__}")
        tl_script = timeline_map.get("generator_script", "")
        if tl_enabled and tl_script:
            script_path = _resolve(project_root, tl_script)
            if not script_path.exists():
                tl_errors.append(f"timeline_map.generator_script not found: {tl_script}")
        lookback = timeline_map.get("lookback_days")
        if lookback is not None:
            if not isinstance(lookback, int) or lookback < 1 or lookback > 90:
                tl_errors.append(f"timeline_map.lookback_days={lookback} out of range [1, 90]")
        min_sig = timeline_map.get("min_signals_for_theme")
        if min_sig is not None:
            if not isinstance(min_sig, int) or min_sig < 1:
                tl_errors.append(f"timeline_map.min_signals_for_theme={min_sig} must be int >= 1")
        top_n = timeline_map.get("top_n_psst")
        if top_n is not None:
            if not isinstance(top_n, int) or top_n < 1:
                tl_errors.append(f"timeline_map.top_n_psst={top_n} must be int >= 1")

    vr.results.append(CheckResult(
        "SOT-036", "WARN",
        "timeline_map configuration valid (optional, supplementary output)",
        len(tl_errors) == 0,
        "; ".join(tl_errors) if tl_errors else ""
    ))

    # ================================================================
    # SOT-037 ~ SOT-040: Source Exploration Validation (v2.5.0)
    # ================================================================
    wf1_cfg = workflows.get("wf1-general", {})
    wf1_params = wf1_cfg.get("parameters", {})
    exploration_cfg = wf1_params.get("source_exploration", {})
    exploration_enabled = exploration_cfg.get("enabled", False) and wf1_cfg.get("enabled", False)

    # ── SOT-037: exploration_config_valid ──
    if exploration_enabled:
        exp_errors = []
        # exploration_method enum check
        valid_exp_methods = {"agent-team", "single-agent"}
        exp_method = exploration_cfg.get("exploration_method", "")
        if exp_method not in valid_exp_methods:
            exp_errors.append(f"exploration_method='{exp_method}' not in {valid_exp_methods}")
        # enforcement enum check
        valid_enforcement = {"mandatory", "optional"}
        enforcement_val = exploration_cfg.get("enforcement", "")
        if enforcement_val not in valid_enforcement:
            exp_errors.append(f"enforcement='{enforcement_val}' not in {valid_enforcement}")
        # Range checks
        range_checks = {
            "max_candidates_per_scan": (1, 20),
            "time_budget_minutes": (1, 60),
            "coverage_gap_threshold": (0.05, 0.50),
            "min_signals_for_viable": (1, 10),
            "auto_promotion_scans": (3, 20),
            "candidate_retention_days": (7, 90),
            "max_test_signals_per_candidate": (1, 50),
        }
        for field_name, (lo, hi) in range_checks.items():
            val = exploration_cfg.get(field_name)
            if val is None:
                exp_errors.append(f"source_exploration.{field_name} missing")
            elif not isinstance(val, (int, float)) or not (lo <= val <= hi):
                exp_errors.append(f"source_exploration.{field_name}={val} out of range [{lo}, {hi}]")
        # frontiers_config must be defined
        if not exploration_cfg.get("frontiers_config"):
            exp_errors.append("source_exploration.frontiers_config not defined")

        # Generate excluded sources list for workflow independence
        wf1_data_root = wf1_cfg.get("data_root", "")
        if wf1_data_root:
            try:
                wf1_sources_list = _get_enabled_sources(
                    project_root, wf1_cfg.get("sources_config", ""))
                wf2_sources_list = _get_enabled_sources(
                    project_root, workflows.get("wf2-arxiv", {}).get("sources_config", ""))
                wf3_sources_list = _get_enabled_sources(
                    project_root, workflows.get("wf3-naver", {}).get("sources_config", ""))
                excluded_all = sorted(set(wf1_sources_list + wf2_sources_list + wf3_sources_list))
                excluded_path = _resolve(project_root, wf1_data_root) / "exploration" / "excluded-sources.json"
                excluded_path.parent.mkdir(parents=True, exist_ok=True)
                with open(excluded_path, "w", encoding="utf-8") as ef:
                    json.dump({
                        "generated_by": "validate_registry.py SOT-037",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "excluded_sources": excluded_all,
                        "reason": "Workflow independence: WF1 + WF2 + WF3 existing sources"
                    }, ef, indent=2, ensure_ascii=False)
            except Exception as e:
                exp_errors.append(f"Failed to generate excluded-sources.json: {e}")

        vr.results.append(CheckResult(
            "SOT-037", "HALT",
            "source_exploration parameters valid if enabled",
            len(exp_errors) == 0,
            "; ".join(exp_errors) if exp_errors else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-037", "HALT",
            "source_exploration parameters valid if enabled",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-038: exploration_paths_exist (create if missing) ──
    if exploration_enabled:
        exp_created = []
        wf1_data_root = wf1_cfg.get("data_root", "")
        wf1_paths = wf1_cfg.get("paths", {})
        for path_key in ["exploration", "exploration_candidates", "exploration_history"]:
            rel = wf1_paths.get(path_key, "")
            if rel:
                full = _resolve(project_root, wf1_data_root) / rel
                if not full.exists():
                    full.mkdir(parents=True, exist_ok=True)
                    exp_created.append(str(full.relative_to(project_root)))
        vr.results.append(CheckResult(
            "SOT-038", "CREATE",
            "WF1 exploration directories exist",
            True,
            "",
            f"Created {len(exp_created)} directories" if exp_created else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-038", "CREATE",
            "WF1 exploration directories exist",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-039: exploration_agents_exist ──
    if exploration_enabled:
        exp_agent_files = [
            ".claude/agents/exploration-orchestrator.md",
            ".claude/agents/workers/discovery-alpha.md",
            ".claude/agents/workers/discovery-beta.md",
            ".claude/agents/workers/discovery-evaluator.md",
            ".claude/agents/workers/source-explorer.md",
        ]
        missing_exp_agents = [f for f in exp_agent_files if not _file_exists(project_root, f)]
        vr.results.append(CheckResult(
            "SOT-039", "HALT",
            "Exploration orchestrator and worker agent files exist",
            len(missing_exp_agents) == 0,
            f"Missing: {missing_exp_agents}" if missing_exp_agents else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-039", "HALT",
            "Exploration orchestrator and worker agent files exist",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-040: exploration_frontiers_config_exists ──
    if exploration_enabled:
        frontiers_path = exploration_cfg.get("frontiers_config", "")
        frontiers_errors = []
        if not frontiers_path:
            frontiers_errors.append("frontiers_config path not defined")
        elif not _file_exists(project_root, frontiers_path):
            frontiers_errors.append(f"File not found: {frontiers_path}")
        else:
            try:
                frontiers_data = _load_yaml(_resolve(project_root, frontiers_path))
                if not frontiers_data.get("frontiers"):
                    frontiers_errors.append("frontiers section missing in YAML")
                selection = frontiers_data.get("selection", {})
                sps = selection.get("samples_per_scan")
                if sps is not None:
                    if not isinstance(sps, int) or not (1 <= sps <= 10):
                        frontiers_errors.append(
                            f"selection.samples_per_scan={sps} out of range [1, 10]")
                else:
                    frontiers_errors.append("selection.samples_per_scan not defined")
            except Exception as e:
                frontiers_errors.append(f"Failed to parse YAML: {e}")
        vr.results.append(CheckResult(
            "SOT-040", "HALT",
            "exploration-frontiers.yaml exists and is valid",
            len(frontiers_errors) == 0,
            "; ".join(frontiers_errors) if frontiers_errors else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-040", "HALT",
            "exploration-frontiers.yaml exists and is valid",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-041: exploration_gate_script_exists ──
    if exploration_enabled:
        gate_script = exploration_cfg.get("gate_script", "")
        gate_errors = []
        if not gate_script:
            gate_errors.append("source_exploration.gate_script not defined")
        elif not _file_exists(project_root, gate_script):
            gate_errors.append(f"gate_script file not found: {gate_script}")
        vr.results.append(CheckResult(
            "SOT-041", "HALT",
            "exploration gate_script Python file exists",
            len(gate_errors) == 0,
            "; ".join(gate_errors) if gate_errors else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-041", "HALT",
            "exploration gate_script Python file exists",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-050: frontier_selector_script_exists (v2.5.2) ──
    # VP-5 in exploration_gate.py verify checks for frontier-selection-{date}.json,
    # which is created exclusively by frontier_selector.py. If this script is missing,
    # VP-5 will always FAIL at PG1 with a misleading "file not found" error.
    # SOT-050 catches the infrastructure problem at startup (same pattern as SOT-041).
    if exploration_enabled:
        fs_script = exploration_cfg.get("frontier_selector_script", "")
        fs_errors = []
        if not fs_script:
            fs_errors.append("source_exploration.frontier_selector_script not defined")
        elif not _file_exists(project_root, fs_script):
            fs_errors.append(f"frontier_selector_script not found: {fs_script}")
        vr.results.append(CheckResult(
            "SOT-050", "HALT",
            "frontier_selector_script Python file exists (VP-5 dependency)",
            len(fs_errors) == 0,
            "; ".join(fs_errors) if fs_errors else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-050", "HALT",
            "frontier_selector_script Python file exists (VP-5 dependency)",
            True,
            "Exploration disabled — skipped"
        ))

    # ── SOT-042: previous-signals.json freshness (v2.6.0) ──
    # Stale dedup index causes duplicate signals to bypass all 4 dedup stages.
    # This check warns at startup if any enabled workflow's context/previous-signals.json
    # is older than 48 hours.  The file will be rebuilt during execution (Step 1.1),
    # so this is advisory only (WARN, not HALT).
    freshness_issues = []
    for wf_name, wf_cfg in workflows.items():
        if not wf_cfg.get("enabled", False):
            continue
        data_root = wf_cfg.get("data_root", "")
        prev_signals_path = _resolve(project_root, data_root) / "context" / "previous-signals.json"
        if prev_signals_path.exists():
            age_hours = (datetime.now(timezone.utc).timestamp() - prev_signals_path.stat().st_mtime) / 3600
            if age_hours > 48:
                freshness_issues.append(f"{wf_name}: previous-signals.json is {age_hours:.0f}h old (>48h)")
        # Not existing is OK — will be created during execution
    vr.results.append(CheckResult(
        "SOT-042", "WARN",
        "Dedup index files are recent (<48h) for enabled workflows",
        len(freshness_issues) == 0,
        "; ".join(freshness_issues) if freshness_issues else ""
    ))

    # ── SOT-043: STEEPs source base coverage (WARN, not HALT) ──
    # Checks that all 6 STEEPs categories have at least 1 enabled source
    # with matching steeps_focus. Only applies to workflows whose sources
    # actually define steeps_focus fields (skips WF2/WF3 to avoid noise).
    all_steeps = {"S_Social", "T_Technological", "E_Economic", "E_Environmental", "P_Political", "s_spiritual"}
    coverage_issues = []
    for wf_name, wf_cfg in workflows.items():
        if not wf_cfg.get("enabled", False):
            continue
        src_cfg_path = wf_cfg.get("sources_config", "")
        if not src_cfg_path:
            continue
        full_src_path = _resolve(project_root, src_cfg_path)
        if not full_src_path.exists():
            continue
        src_data = _load_yaml(full_src_path)
        src_list = src_data.get("sources", [])
        # Skip workflows whose sources don't use steeps_focus at all
        has_steeps_focus = any(
            s.get("steeps_focus") for s in src_list if s.get("enabled", False)
        )
        if not has_steeps_focus:
            continue
        # Collect all covered categories from enabled sources
        covered = set()
        for s in src_list:
            if s.get("enabled", False):
                for cat in s.get("steeps_focus", []):
                    covered.add(cat)
        missing = sorted(all_steeps - covered)
        if missing:
            coverage_issues.append(f"{wf_name}: missing {missing}")
    vr.results.append(CheckResult(
        "SOT-043", "WARN",
        "All 6 STEEPs categories have at least 1 enabled source with matching steeps_focus",
        len(coverage_issues) == 0,
        "; ".join(coverage_issues) if coverage_issues else ""
    ))

    # ── SOT-044: dedup_gate section exists with required fields (v2.6.0→v2.9.0) ──
    # "Unvalidated SOT Is Not SOT" — the dedup_gate section controls deterministic
    # cross-scan duplicate detection. Missing fields → gate silently disabled.
    dedup_gate_cfg = system.get("dedup_gate", {})
    dedup_gate_issues = []
    if not dedup_gate_cfg:
        dedup_gate_issues.append("system.dedup_gate section missing")
    else:
        required_fields = ["enabled", "gate_script", "thresholds", "enforce", "lookback_days"]
        for f in required_fields:
            if f not in dedup_gate_cfg:
                dedup_gate_issues.append(f"missing field: dedup_gate.{f}")
        th = dedup_gate_cfg.get("thresholds", {})
        # Stage A/B thresholds (v2.6.0)
        for tf in ["topic_fingerprint_definite", "topic_fingerprint_uncertain"]:
            if tf not in th:
                dedup_gate_issues.append(f"missing threshold: {tf}")
        # Stage C/D thresholds (v2.9.0)
        for tf in ["title_similarity_definite", "title_similarity_uncertain",
                    "entity_overlap_definite", "entity_overlap_uncertain"]:
            if tf not in th:
                dedup_gate_issues.append(f"missing threshold: {tf}")
        # Validate threshold ordering: definite > uncertain (all stage pairs)
        threshold_pairs = [
            ("topic_fingerprint_definite", "topic_fingerprint_uncertain", "Stage B"),
            ("title_similarity_definite", "title_similarity_uncertain", "Stage C"),
            ("entity_overlap_definite", "entity_overlap_uncertain", "Stage D"),
        ]
        for def_key, unc_key, stage_label in threshold_pairs:
            td = th.get(def_key, 0)
            tu = th.get(unc_key, 0)
            if td and tu and td <= tu:
                dedup_gate_issues.append(
                    f"{stage_label} threshold ordering violated: {def_key} ({td}) must be > {unc_key} ({tu})"
                )
        # Validate lookback_days range [1, 365]
        lookback = dedup_gate_cfg.get("lookback_days", None)
        if lookback is not None:
            if not isinstance(lookback, (int, float)) or lookback < 1 or lookback > 365:
                dedup_gate_issues.append(
                    f"lookback_days must be an integer in [1, 365], got {lookback}"
                )
        enforce_val = dedup_gate_cfg.get("enforce", "")
        if enforce_val not in ("strict", "lenient"):
            dedup_gate_issues.append(f"enforce must be 'strict' or 'lenient', got '{enforce_val}'")
    vr.results.append(CheckResult(
        "SOT-044", "HALT",
        "dedup_gate section valid (thresholds [A/B/C/D], lookback_days, gate_script, enforce)",
        len(dedup_gate_issues) == 0,
        "; ".join(dedup_gate_issues) if dedup_gate_issues else ""
    ))

    # ── SOT-045: dedup_gate Python script exists (v2.6.0) ──
    dg_script = dedup_gate_cfg.get("gate_script", "")
    if dg_script:
        dg_path = _resolve(project_root, dg_script)
        vr.results.append(CheckResult(
            "SOT-045", "HALT",
            "Dedup gate Python script exists",
            dg_path.exists(),
            f"not found: {dg_script}" if not dg_path.exists() else ""
        ))
    else:
        vr.results.append(CheckResult(
            "SOT-045", "HALT",
            "Dedup gate Python script exists",
            False,
            "dedup_gate.gate_script not configured"
        ))

    # ================================================================
    # SOT-046 ~ SOT-048: Bilingual System Validation (v2.8.0)
    # ================================================================
    bilingual_cfg = system.get("bilingual", {})
    bilingual_enabled = bilingual_cfg.get("enabled", False)

    # ── SOT-046: bilingual section exists with required fields ──
    bi_errors = []
    if bilingual_enabled:
        for req_field in ["internal_language", "external_language",
                          "skeleton_mirror_script", "translation_validator_script"]:
            if not bilingual_cfg.get(req_field):
                bi_errors.append(f"bilingual.{req_field} missing or empty")
        il = bilingual_cfg.get("internal_language", "")
        el = bilingual_cfg.get("external_language", "")
        if il and il not in ("en", "ko"):
            bi_errors.append(f"bilingual.internal_language='{il}' must be 'en' or 'ko'")
        if el and el not in ("en", "ko"):
            bi_errors.append(f"bilingual.external_language='{el}' must be 'en' or 'ko'")
        if il and el and il == el:
            bi_errors.append(f"internal_language and external_language must differ (both are '{il}')")
    vr.results.append(CheckResult(
        "SOT-046", "HALT",
        "Bilingual section valid (languages, scripts defined)",
        len(bi_errors) == 0 if bilingual_enabled else True,
        "; ".join(bi_errors) if bi_errors else ("Bilingual disabled — skipped" if not bilingual_enabled else "")
    ))

    # ── SOT-047: bilingual Python scripts exist ──
    bi_script_errors = []
    if bilingual_enabled:
        for script_key in ["resolver_script", "skeleton_mirror_script", "translation_validator_script"]:
            script_path = bilingual_cfg.get(script_key, "")
            if script_path and not _file_exists(project_root, script_path):
                bi_script_errors.append(f"{script_key}: {script_path}")
    vr.results.append(CheckResult(
        "SOT-047", "HALT",
        "Bilingual Python scripts (resolver, skeleton_mirror, translation_validator) exist",
        len(bi_script_errors) == 0 if bilingual_enabled else True,
        "; ".join(bi_script_errors) if bi_script_errors else ("Bilingual disabled — skipped" if not bilingual_enabled else "")
    ))

    # ── SOT-048: English skeleton files exist ──
    bi_skel_errors = []
    if bilingual_enabled:
        en_skeletons = bilingual_cfg.get("skeletons_en", {})
        if not en_skeletons:
            bi_skel_errors.append("bilingual.skeletons_en section missing or empty")
        else:
            for skel_key, skel_path in en_skeletons.items():
                if not _file_exists(project_root, skel_path):
                    bi_skel_errors.append(f"{skel_key}: {skel_path}")
    vr.results.append(CheckResult(
        "SOT-048", "HALT",
        "All English skeleton files referenced in bilingual.skeletons_en exist",
        len(bi_skel_errors) == 0 if bilingual_enabled else True,
        "; ".join(bi_skel_errors) if bi_skel_errors else ("Bilingual disabled — skipped" if not bilingual_enabled else "")
    ))

    # ── SOT-049: EN validate_profiles exist in validate_report.py (v2.8.0) ──
    # When bilingual is enabled and internal_language=="en", bilingual_resolver.py
    # derives EN profiles as "{base_profile}_en" for each workflow. This check
    # verifies that all derived EN profiles actually exist in validate_report.py.
    # "Unvalidated SOT Is Not SOT" — a derived profile that doesn't exist in
    # validate_report.py will cause CRITICAL failures at report generation time.
    en_profile_errors = []
    if bilingual_enabled and bilingual_cfg.get("internal_language") == "en":
        # Import validate_report.py PROFILES early (reused by SOT-033 below)
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from validate_report import PROFILES as _REPORT_PROFILES
            _valid_profiles = set(_REPORT_PROFILES.keys())
        except ImportError:
            _valid_profiles = {"standard", "integrated", "naver", "arxiv_fallback", "weekly",
                               "standard_en", "integrated_en", "naver_en", "weekly_en"}

        # Derive EN profiles from base profiles (same logic as bilingual_resolver.py)
        profile_sources = []
        for wf_name, wf_cfg_item in workflows.items():
            if wf_cfg_item.get("enabled", False):
                base = wf_cfg_item.get("validate_profile", "standard")
                profile_sources.append((wf_name, base))
        # Also check integrated and weekly
        if integration.get("enabled", False):
            base = integration.get("validate_profile", "integrated")
            profile_sources.append(("integrated", base))
        if weekly_cfg.get("enabled", False):
            base = weekly_cfg.get("validate_profile", "weekly")
            profile_sources.append(("weekly", base))

        for source_id, base_profile in profile_sources:
            en_profile = f"{base_profile}_en"
            if en_profile not in _valid_profiles:
                en_profile_errors.append(
                    f"{source_id}: derived EN profile '{en_profile}' "
                    f"not in validate_report.py PROFILES"
                )
    vr.results.append(CheckResult(
        "SOT-049", "HALT",
        "All EN validate_profiles derived by bilingual_resolver exist in validate_report.py",
        len(en_profile_errors) == 0 if (bilingual_enabled and bilingual_cfg.get("internal_language") == "en") else True,
        "; ".join(en_profile_errors) if en_profile_errors else (
            "Bilingual disabled or not EN-first — skipped"
            if not (bilingual_enabled and bilingual_cfg.get("internal_language") == "en") else ""
        )
    ))

    # ── SOT-033: All validate_profile values reference implemented profiles ──
    # "Unvalidated SOT Is Not SOT" — every validate_profile in SOT must map
    # to an actually implemented profile in validate_report.py.
    # Import the authoritative profile list from validate_report.py (single source).
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from validate_report import PROFILES as _REPORT_PROFILES
        valid_profiles = set(_REPORT_PROFILES.keys())
    except ImportError:
        # Fallback: if validate_report.py can't be imported, use static list
        valid_profiles = {"standard", "integrated", "naver", "arxiv_fallback", "weekly"}
    invalid_profiles = []
    for wf_name, wf_cfg in workflows.items():
        if wf_cfg.get("enabled", False):
            vp = wf_cfg.get("validate_profile", "standard")
            if vp not in valid_profiles:
                invalid_profiles.append(f"{wf_name}: '{vp}' not in {sorted(valid_profiles)}")
    # Also check weekly profile
    if weekly_cfg.get("enabled", False):
        wp = weekly_cfg.get("validate_profile", "")
        if wp and wp not in valid_profiles:
            invalid_profiles.append(f"weekly: '{wp}' not in {sorted(valid_profiles)}")
    vr.results.append(CheckResult(
        "SOT-033", "HALT",
        "All validate_profile values reference implemented profiles",
        len(invalid_profiles) == 0,
        "; ".join(invalid_profiles) if invalid_profiles else ""
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
