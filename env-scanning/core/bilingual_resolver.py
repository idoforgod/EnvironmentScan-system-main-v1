#!/usr/bin/env python3
"""
Bilingual Resolver — Deterministic Language Routing from SOT
=============================================================
Eliminates LLM hallucination in skeleton path selection, validation profile
selection, and translation workflow triggering by producing a pre-computed
JSON config file.

This module follows the exact same pattern as temporal_anchor.py:
    SOT (workflow-registry.yaml) → Python reads → deterministic JSON output
    → downstream agents/scripts consume the JSON (no LLM interpretation needed)

Design Principle:
    "계산은 Python이, 판단은 LLM이."
    Routing decisions (which skeleton, which profile, which language) = Python.
    Content generation (report writing, translation) = LLM.

What this module decides (deterministically):
    - Which skeleton template to use (EN or KO) per workflow
    - Which validation profile to use (EN or KO) per workflow
    - Which language flag to pass to statistics_engine and metadata_injector
    - Whether translation is needed after report generation
    - File naming conventions for EN/KO report pairs

What this module does NOT decide (LLM territory):
    - Report content, signal analysis, strategic implications
    - Translation quality, terminology choices
    - Priority ranking, cross-impact analysis

Usage (CLI):
    python3 env-scanning/core/bilingual_resolver.py \\
        --registry env-scanning/config/workflow-registry.yaml \\
        --output env-scanning/integrated/logs/bilingual-config-2026-02-18.json

Usage (importable):
    from core.bilingual_resolver import resolve_bilingual_config
    config = resolve_bilingual_config("env-scanning/config/workflow-registry.yaml")

Exit codes:
    0 = SUCCESS (config file written)
    1 = ERROR (SOT read failure, missing fields, invalid config)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
RESOLVER_ID = "bilingual_resolver.py"

# Valid internal languages
VALID_INTERNAL_LANGUAGES = {"en", "ko"}

# Mapping: workflow_id → skeletons_en key in SOT
# This maps each workflow to its corresponding EN skeleton key in
# system.bilingual.skeletons_en
WORKFLOW_SKELETON_MAP = {
    "wf1-general": "report_skeleton",
    "wf2-arxiv": "report_skeleton",       # WF1 and WF2 share the same skeleton
    "wf3-naver": "naver_report_skeleton",
    "wf4-multiglobal-news": "multiglobal_news_report_skeleton",
    "integrated": "integrated_report_skeleton",
    "weekly": "weekly_report_skeleton",
}

# Mapping: workflow_id → KO skeleton SOT path
# Where to find the KO skeleton for each workflow
WORKFLOW_KO_SKELETON_MAP = {
    "wf1-general": ("system", "shared_invariants", "report_skeleton"),
    "wf2-arxiv": ("system", "shared_invariants", "report_skeleton"),
    "wf3-naver": None,  # Uses naver-specific skeleton (from WF3_SKELETON variable)
    "wf4-multiglobal-news": None,  # Uses multiglobal-news-specific skeleton (from WF4_SKELETON variable)
    "integrated": ("integration", "integrated_skeleton"),
    "weekly": ("integration", "weekly", "skeleton"),
}

# Naver KO skeleton — hardcoded because SOT stores it differently
NAVER_KO_SKELETON = ".claude/skills/env-scanner/references/naver-report-skeleton.md"

# Multi&Global-News KO skeleton — same pattern as Naver
MULTIGLOBAL_NEWS_KO_SKELETON = ".claude/skills/env-scanner/references/multiglobal-news-report-skeleton.md"


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------

def resolve_bilingual_config(
    registry_path: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolve all bilingual routing parameters from the SOT.

    This function:
    1. Reads workflow-registry.yaml (SOT)
    2. Checks system.bilingual.enabled
    3. For each enabled workflow, deterministically resolves:
       - report_skeleton: EN or KO skeleton path
       - validate_profile: EN or KO profile name
       - statistics_language: "en" or "ko"
       - translation_needed: True or False
       - ko_skeleton / ko_validate_profile: for translation validation
    4. Optionally writes the result to a JSON config file

    Args:
        registry_path: Path to workflow-registry.yaml (SOT)
        output_path: Where to write the bilingual config JSON (optional)

    Returns:
        Bilingual config dictionary

    Raises:
        FileNotFoundError: If registry_path does not exist
        KeyError: If required SOT fields are missing
        ValueError: If SOT values are invalid
    """
    registry_file = Path(registry_path)
    if not registry_file.exists():
        raise FileNotFoundError(f"SOT not found: {registry_path}")

    # 1. Read SOT
    with open(registry_file, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    # 2. Read bilingual config from SOT
    system = registry.get("system", {})
    bilingual = system.get("bilingual", {})
    bilingual_enabled = bilingual.get("enabled", False)
    internal_language = bilingual.get("internal_language", "ko")
    external_language = bilingual.get("external_language", "ko")

    # Validate internal_language
    if internal_language not in VALID_INTERNAL_LANGUAGES:
        raise ValueError(
            f"system.bilingual.internal_language='{internal_language}' "
            f"not in {VALID_INTERNAL_LANGUAGES}"
        )

    # 3. Read EN skeleton paths (only needed if bilingual enabled + EN)
    skeletons_en = bilingual.get("skeletons_en", {})

    # 4. Read shared invariants (KO skeleton paths)
    shared_invariants = system.get("shared_invariants", {})
    integration = registry.get("integration", {})
    workflows_config = registry.get("workflows", {})

    # 5. Read translation scripts
    skeleton_mirror_script = bilingual.get("skeleton_mirror_script", "")
    translation_validator_script = bilingual.get(
        "translation_validator_script", ""
    )
    resolver_script = bilingual.get(
        "resolver_script", "env-scanning/core/bilingual_resolver.py"
    )

    # 6. Determine if English-first mode is active
    english_first = bilingual_enabled and internal_language == "en"

    # 7. Resolve per-workflow routing
    wf_configs: Dict[str, Dict[str, Any]] = {}

    for wf_id, skeleton_key in WORKFLOW_SKELETON_MAP.items():
        # Get base validate_profile from SOT
        base_profile = _get_base_profile(wf_id, workflows_config, integration)

        if english_first:
            # EN skeleton from bilingual.skeletons_en
            en_skeleton = skeletons_en.get(skeleton_key)
            if not en_skeleton:
                raise KeyError(
                    f"system.bilingual.skeletons_en.{skeleton_key} not found "
                    f"in SOT (required for workflow '{wf_id}')"
                )

            # EN profile = base + "_en"
            en_profile = f"{base_profile}_en"

            # KO skeleton for translation validation
            ko_skeleton = _get_ko_skeleton(
                wf_id, shared_invariants, integration
            )

            wf_configs[wf_id] = {
                "report_skeleton": en_skeleton,
                "validate_profile": en_profile,
                "statistics_language": "en",
                "metadata_injector_language": "en",
                "translation_needed": True,
                "ko_skeleton": ko_skeleton,
                "ko_validate_profile": base_profile,
            }
        else:
            # KO-only mode (legacy behavior)
            ko_skeleton = _get_ko_skeleton(
                wf_id, shared_invariants, integration
            )

            wf_configs[wf_id] = {
                "report_skeleton": ko_skeleton,
                "validate_profile": base_profile,
                "statistics_language": "ko",
                "metadata_injector_language": "ko",
                "translation_needed": False,
                "ko_skeleton": ko_skeleton,
                "ko_validate_profile": base_profile,
            }

    # 8. Build result
    result = {
        "resolver": RESOLVER_ID,
        "resolver_version": VERSION,
        "bilingual_enabled": bilingual_enabled,
        "english_first": english_first,
        "internal_language": internal_language,
        "external_language": external_language,
        "workflows": wf_configs,
        "scripts": {
            "skeleton_mirror": skeleton_mirror_script,
            "translation_validator": translation_validator_script,
            "bilingual_resolver": resolver_script,
        },
        "registry_path": str(registry_path),
        "registry_version": system.get("version", "unknown"),
    }

    # 9. Write to file if output_path given
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def load_bilingual_config(config_path: str) -> Dict[str, Any]:
    """
    Load a previously generated bilingual config file.

    This is the function that downstream agents/scripts should call
    to get bilingual routing parameters — NOT SOT interpretation.

    Args:
        config_path: Path to the bilingual-config JSON file

    Returns:
        Bilingual config dictionary

    Raises:
        FileNotFoundError: If config file does not exist
        json.JSONDecodeError: If config file is malformed
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Bilingual config not found: {config_path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_workflow_config(
    config: Dict[str, Any], workflow_id: str
) -> Dict[str, Any]:
    """
    Extract a specific workflow's bilingual config.

    Args:
        config: Loaded bilingual config dictionary
        workflow_id: e.g., "wf1-general", "wf2-arxiv", "integrated"

    Returns:
        Workflow-specific bilingual config dictionary

    Raises:
        KeyError: If workflow not found in config
    """
    wf = config.get("workflows", {}).get(workflow_id)
    if wf is None:
        available = list(config.get("workflows", {}).keys())
        raise KeyError(
            f"Workflow '{workflow_id}' not in bilingual config. "
            f"Available: {available}"
        )
    return wf


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _get_base_profile(
    wf_id: str,
    workflows_config: Dict[str, Any],
    integration: Dict[str, Any],
) -> str:
    """Get the base (KO) validate_profile for a workflow from SOT."""
    if wf_id in workflows_config:
        return workflows_config[wf_id].get("validate_profile", "standard")
    elif wf_id == "integrated":
        return integration.get("validate_profile", "integrated")
    elif wf_id == "weekly":
        return integration.get("weekly", {}).get("validate_profile", "weekly")
    else:
        return "standard"


def _get_ko_skeleton(
    wf_id: str,
    shared_invariants: Dict[str, Any],
    integration: Dict[str, Any],
) -> str:
    """Get the KO skeleton path for a workflow from SOT."""
    path_keys = WORKFLOW_KO_SKELETON_MAP.get(wf_id)

    if wf_id == "wf3-naver":
        # Naver uses its own dedicated skeleton
        return NAVER_KO_SKELETON

    if wf_id == "wf4-multiglobal-news":
        # Multi&Global-News uses its own dedicated skeleton
        return MULTIGLOBAL_NEWS_KO_SKELETON

    if path_keys is None:
        return shared_invariants.get(
            "report_skeleton",
            ".claude/skills/env-scanner/references/report-skeleton.md",
        )

    # Navigate nested dict using path_keys
    if path_keys[0] == "system":
        # shared_invariants.report_skeleton
        return shared_invariants.get(
            path_keys[-1],
            ".claude/skills/env-scanner/references/report-skeleton.md",
        )
    elif path_keys[0] == "integration":
        obj = integration
        for key in path_keys[1:]:
            obj = obj.get(key, {}) if isinstance(obj, dict) else {}
        if isinstance(obj, str):
            return obj
        return ".claude/skills/env-scanner/references/integrated-report-skeleton.md"

    return ".claude/skills/env-scanner/references/report-skeleton.md"


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Resolve bilingual routing config from SOT "
            "(bilingual_resolver.py)"
        )
    )
    parser.add_argument(
        "--registry",
        default="env-scanning/config/workflow-registry.yaml",
        help="Path to workflow-registry.yaml (SOT)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for bilingual config JSON",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print result as JSON to stdout",
    )
    args = parser.parse_args()

    try:
        result = resolve_bilingual_config(
            registry_path=args.registry,
            output_path=args.output,
        )

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Human-readable summary
            ef = result["english_first"]
            icon = "EN" if ef else "KO"
            print("=" * 60)
            print(f"  Bilingual Resolver: SUCCESS [{icon}-first]")
            print(f"  Bilingual enabled: {result['bilingual_enabled']}")
            print(f"  Internal language: {result['internal_language']}")
            print(f"  External language: {result['external_language']}")
            print(f"  Registry: {result['registry_path']} "
                  f"(v{result['registry_version']})")
            print("-" * 60)
            for wf_id, wf_cfg in result["workflows"].items():
                skel = Path(wf_cfg["report_skeleton"]).name
                prof = wf_cfg["validate_profile"]
                lang = wf_cfg["statistics_language"]
                tr = "YES" if wf_cfg["translation_needed"] else "no"
                print(f"  {wf_id:15s}: skel={skel:40s} "
                      f"profile={prof:15s} lang={lang} translate={tr}")
            print("=" * 60)
            if args.output:
                print(f"  Output: {args.output}")

        sys.exit(0)

    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
