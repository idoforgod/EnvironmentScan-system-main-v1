#!/usr/bin/env python3
"""
Frontier Selector — Deterministic Weighted-Random Keyword Selection
====================================================================
Selects frontier keywords for discovery-beta using Python's random module
for TRUE randomness, not LLM pattern completion.

Applies success-based weights from exploration history and respects
cooldown_after_failure to avoid repeatedly selecting failed keywords.

Design Principle:
    "LLM이 '무작위로 선택하라'는 지시를 받으면, 패턴 완성으로 편향된 선택을 한다.
     Python random.choices()는 진정한 가중 무작위를 보장한다."

Pipeline Position:
    exploration-history.json ──┐
    exploration-frontiers.yaml ─┤→ frontier_selector.py → frontier-selection-{date}.json
                                │                              ↓
                                │                 discovery-beta reads selection file
                                │                 (does NOT select keywords itself)

Usage (CLI):
    python3 env-scanning/core/frontier_selector.py select \\
        --frontiers env-scanning/config/exploration-frontiers.yaml \\
        --history env-scanning/wf1-general/exploration/history/exploration-history.json \\
        --samples 3 \\
        --output env-scanning/wf1-general/exploration/frontier-selection-2026-02-10.json

Usage (importable):
    from core.frontier_selector import select_frontier_keywords

Exit codes:
    0 = SUCCESS (selection file written)
    1 = ERROR (missing files, invalid config)
"""

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERSION = "1.0.0"
SELECTOR_ID = "frontier_selector.py"

# Frontier categories in exploration-frontiers.yaml
FRONTIER_CATEGORIES = ["geographic", "interdisciplinary", "emerging_domains", "paradigm_shifts"]

# Default weight for keywords with no history
DEFAULT_WEIGHT = 1.0

# Minimum weight floor (prevent any keyword from being completely excluded by weights)
MIN_WEIGHT = 0.1

# Maximum weight ceiling (prevent runaway success bias)
MAX_WEIGHT = 5.0


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------

def select_frontier_keywords(
    frontiers_path: str,
    history_path: str | None = None,
    samples: int = 3,
    avoid_patterns: list[str] | None = None,
    output_path: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Select frontier keywords using true weighted-random selection.

    Process:
        1. Load all keywords from exploration-frontiers.yaml
        2. Load success/failure history from exploration-history.json
        3. Compute weights: base weight * success_multiplier / failure_penalty
        4. Apply cooldown: exclude keywords that failed recently
        5. Remove keywords matching avoid_patterns
        6. Use random.choices() with computed weights for TRUE randomness
        7. Write selection result to JSON file

    Args:
        frontiers_path: Path to exploration-frontiers.yaml
        history_path: Optional path to exploration-history.json
        samples: Number of keywords to select
        avoid_patterns: Keywords/patterns to exclude
        output_path: Optional path to write selection JSON
        seed: Optional random seed for reproducible testing

    Returns:
        Selection result dictionary
    """
    if seed is not None:
        random.seed(seed)

    # 1. Load frontiers config
    f_path = Path(frontiers_path)
    if not f_path.exists():
        raise FileNotFoundError(f"Frontiers config not found: {frontiers_path}")

    with open(f_path, "r", encoding="utf-8") as f:
        frontiers_config = yaml.safe_load(f)

    frontiers = frontiers_config.get("frontiers", {})
    selection_config = frontiers_config.get("selection", {})

    method = selection_config.get("method", "weighted_random")
    configured_samples = selection_config.get("samples_per_scan", samples)
    samples = min(samples, configured_samples)  # Use the smaller of the two
    weight_by_success = selection_config.get("weight_by_success", True)
    cooldown_after_failure = selection_config.get("cooldown_after_failure", 3)

    # 2. Collect all keywords with category metadata
    all_keywords: list[dict[str, str]] = []
    for category in FRONTIER_CATEGORIES:
        keywords = frontiers.get(category, [])
        for kw in keywords:
            if isinstance(kw, str) and kw.strip():
                all_keywords.append({
                    "keyword": kw.strip(),
                    "category": category,
                })

    if not all_keywords:
        return _build_result("NO_KEYWORDS", "No frontier keywords found", [], method)

    # 3. Load history for weight computation
    history_data: dict = {}
    if history_path:
        h_path = Path(history_path)
        if h_path.exists():
            try:
                with open(h_path, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                history_data = {}

    keyword_successes = history_data.get("learning", {}).get("keyword_successes", {})
    keyword_failures = history_data.get("learning", {}).get("keyword_failures", {})
    keyword_last_failure_scan = history_data.get("learning", {}).get("keyword_last_failure_scan", {})
    total_scans = len(history_data.get("scans", []))

    # 4. Apply avoid_patterns filter
    avoid_set = set()
    if avoid_patterns:
        avoid_set = {p.lower() for p in avoid_patterns}

    # 5. Compute weights and filter
    eligible_keywords: list[dict] = []
    excluded_keywords: list[dict] = []

    for kw_info in all_keywords:
        kw = kw_info["keyword"]
        kw_lower = kw.lower()

        # Check avoid patterns
        if any(pattern in kw_lower for pattern in avoid_set):
            excluded_keywords.append({**kw_info, "reason": "avoid_pattern"})
            continue

        # Check cooldown
        last_fail_scan = keyword_last_failure_scan.get(kw, -999)
        scans_since_failure = total_scans - last_fail_scan
        if 0 < scans_since_failure < cooldown_after_failure:
            excluded_keywords.append({
                **kw_info,
                "reason": f"cooldown ({scans_since_failure}/{cooldown_after_failure})",
            })
            continue

        # Compute weight
        if method == "weighted_random" and weight_by_success:
            successes = keyword_successes.get(kw, 0)
            failures = keyword_failures.get(kw, 0)
            # Weight formula: base + success_bonus - failure_penalty
            weight = DEFAULT_WEIGHT + (successes * 0.5) - (failures * 0.3)
            weight = max(MIN_WEIGHT, min(MAX_WEIGHT, weight))
        else:
            weight = DEFAULT_WEIGHT

        eligible_keywords.append({**kw_info, "weight": weight})

    if not eligible_keywords:
        return _build_result(
            "NO_ELIGIBLE", "All keywords excluded by filters/cooldown",
            [], method, excluded=excluded_keywords,
        )

    # 6. Select using TRUE randomness
    actual_samples = min(samples, len(eligible_keywords))

    if method == "random":
        selected_items = random.sample(eligible_keywords, actual_samples)
    else:  # weighted_random (default)
        weights = [kw["weight"] for kw in eligible_keywords]
        # random.choices allows duplicates; use a loop to ensure unique selection
        selected_items = _weighted_sample_unique(eligible_keywords, weights, actual_samples)

    # 7. Build selection list
    selected = []
    for item in selected_items:
        selected.append({
            "keyword": item["keyword"],
            "category": item["category"],
            "weight": round(item["weight"], 3),
        })

    result = _build_result(
        "SUCCESS",
        f"Selected {len(selected)} keywords from {len(eligible_keywords)} eligible",
        selected,
        method,
        excluded=excluded_keywords,
        total_keywords=len(all_keywords),
        eligible_keywords=len(eligible_keywords),
    )

    if output_path:
        _write_json(output_path, result)

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weighted_sample_unique(
    items: list[dict], weights: list[float], k: int
) -> list[dict]:
    """Select k unique items using weighted random without replacement."""
    if k >= len(items):
        return list(items)

    selected: list[dict] = []
    remaining_items = list(items)
    remaining_weights = list(weights)

    for _ in range(k):
        if not remaining_items:
            break
        chosen = random.choices(remaining_items, weights=remaining_weights, k=1)[0]
        idx = remaining_items.index(chosen)
        selected.append(chosen)
        remaining_items.pop(idx)
        remaining_weights.pop(idx)

    return selected


def _build_result(
    status: str,
    message: str,
    selected: list[dict],
    method: str,
    excluded: list[dict] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build selection result dictionary."""
    result = {
        "selector": SELECTOR_ID,
        "selector_version": VERSION,
        "selected_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "message": message,
        "method": method,
        "selected_keywords": selected,
        "selected_count": len(selected),
        "statistics": {
            "total_keywords": kwargs.get("total_keywords", 0),
            "eligible_keywords": kwargs.get("eligible_keywords", 0),
            "excluded_count": len(excluded) if excluded else 0,
        },
    }
    if excluded:
        result["excluded_keywords"] = excluded
    return result


def _write_json(path: str, data: Any) -> None:
    """Write JSON with proper encoding."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Frontier Selector — deterministic weighted-random keyword selection"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- select ---
    sel_parser = subparsers.add_parser("select", help="Select frontier keywords")
    sel_parser.add_argument("--frontiers", required=True,
                            help="Path to exploration-frontiers.yaml")
    sel_parser.add_argument("--history", default=None,
                            help="Path to exploration-history.json")
    sel_parser.add_argument("--samples", type=int, default=3,
                            help="Number of keywords to select")
    sel_parser.add_argument("--avoid", nargs="*", default=None,
                            help="Keywords/patterns to avoid")
    sel_parser.add_argument("--output", default=None,
                            help="Output path for selection JSON")
    sel_parser.add_argument("--seed", type=int, default=None,
                            help="Random seed for reproducible testing")
    sel_parser.add_argument("--json", action="store_true", dest="json_output",
                            help="Print result as JSON to stdout")

    args = parser.parse_args()

    try:
        if args.command == "select":
            result = select_frontier_keywords(
                frontiers_path=args.frontiers,
                history_path=args.history,
                samples=args.samples,
                avoid_patterns=args.avoid,
                output_path=args.output,
                seed=args.seed,
            )
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        if args.json_output:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status = result["status"]
            icon = "PASS" if status == "SUCCESS" else "WARN"
            print("=" * 60)
            print(f"  [{icon}] Frontier Selector: {args.command}")
            print(f"  Method: {result['method']}")
            print(f"  {result['message']}")
            if result["selected_keywords"]:
                print("  Selected:")
                for kw in result["selected_keywords"]:
                    print(f"    - [{kw['category']}] {kw['keyword']} (w={kw['weight']})")
            print("=" * 60)

        sys.exit(0 if status == "SUCCESS" else 1)

    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
