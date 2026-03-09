#!/usr/bin/env python3
"""
Priority Score Calculator — Deterministic Priority Ranking
=========================================================
"계산은 Python이, 판단은 LLM이" — Phase 2, Step 2.3 완전 Python 원천봉쇄.

phase2-analyst (LLM)이 결정:
  - STEEPs 분류, 신호 상태(emerging/developing/mature)
  - innovative_capacity (novelty: 1–5)
  - pSST 차원값: ES (Evidence Strength), CC (Classification Confidence)
  - 영향도 평가: IC (Impact Confidence), impact_score (1–5), probability (1–5)

이 모듈(Python)이 처리하는 모든 공식 기반 계산:
  1. SR (Source Reliability): source_type 룩업 (psst_calculator 사용)
  2. TC (Temporal Currency): 날짜 산술 (psst_calculator 사용)
  3. DC (Distinctiveness Confidence): dedup_stage_passed 룩업
  4. pSST 집계: PSSTCalculator.calculate_psst(6 차원)
  5. 긴급도 룩업: {emerging: 3, developing: 4, mature: 2}
  6. 우선순위 점수 공식: weighted(impact, probability, urgency, novelty)
  7. 정렬 및 순위 부여

파이프라인 위치:
    phase2-analyst (LLM) → classified-signals.json + impact-assessment.json
                         ↓
    priority_score_calculator.py (THIS) → priority-ranked.json
                         ↓
    report-generator (LLM) reads priority-ranked.json

Usage (CLI):
    python3 env-scanning/core/priority_score_calculator.py \\
        --classified env-scanning/wf1-general/structured/classified-signals-{date}.json \\
        --impact     env-scanning/wf1-general/analysis/impact-assessment-{date}.json \\
        --filtered   env-scanning/wf1-general/filtered/new-signals-{date}.json \\
        --thresholds env-scanning/config/thresholds.yaml \\
        --workflow   wf1-general \\
        --date       2026-03-02 \\
        --output     env-scanning/wf1-general/analysis/priority-ranked-{date}.json

Usage (importable):
    from core.priority_score_calculator import PriorityScoreCalculator
    calc = PriorityScoreCalculator(thresholds_path="env-scanning/config/thresholds.yaml")
    ranked = calc.compute(classified_data, impact_data, filtered_signals, date="2026-03-02")

Exit codes:
    0 = SUCCESS
    1 = ERROR (missing required files)
    2 = WARN (partial computation — some signals used fallback values)
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from core.psst_calculator import PSSTCalculator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("priority_score_calculator")

VERSION = "1.0.0"
ENGINE_ID = "priority_score_calculator.py"

# ---------------------------------------------------------------------------
# Constants — deterministic lookup tables (never LLM)
# ---------------------------------------------------------------------------

# Priority formula weights (from priority-ranker.md constraints; tunable via thresholds.yaml)
DEFAULT_PRIORITY_WEIGHTS = {
    "impact":      0.40,
    "probability": 0.30,
    "urgency":     0.20,
    "novelty":     0.10,
}

# Urgency lookup: signal lifecycle status → urgency score (1–5)
# Rule: developing is most urgent (time-bound change), emerging second, mature lowest.
URGENCY_LOOKUP: dict[str, float] = {
    "emerging":   3.0,
    "developing": 4.0,
    "mature":     2.0,
}
URGENCY_DEFAULT = 3.0  # Fallback when status is absent or unrecognised

# DC lookup: dedup cascade stage → Distinctiveness Confidence score (0–100)
DC_STAGE_SCORES: dict[str, int] = {
    "passed_all_4": 100,
    "passed_3":     85,
    "passed_2":     70,
    "passed_1":     60,
    "duplicate":     0,
}
DC_DEFAULT = 85  # Assume passed 4-stage if field absent (conservative)

# Score bounds
PRIORITY_SCORE_MIN = 1.0
PRIORITY_SCORE_MAX = 5.0


# ---------------------------------------------------------------------------
# Core Calculator Class
# ---------------------------------------------------------------------------

class PriorityScoreCalculator:
    """Deterministic priority scoring and ranking for environmental scan signals."""

    def __init__(self, thresholds_path: Optional[str] = None):
        """
        Initialise calculator with optional thresholds.yaml for live weights.

        Args:
            thresholds_path: Path to env-scanning/config/thresholds.yaml.
                             If None or unreadable, uses DEFAULT_PRIORITY_WEIGHTS.
        """
        self.weights = dict(DEFAULT_PRIORITY_WEIGHTS)
        self.psst_config: dict[str, Any] = {}

        if thresholds_path:
            cfg = self._load_thresholds(thresholds_path)
            if cfg:
                # Override weights from SOT if present
                w = cfg.get("priority_ranking", {}).get("component_weights", {})
                for k in ("impact", "probability", "urgency", "novelty"):
                    if k in w:
                        self.weights[k] = float(w[k])
                self.psst_config = cfg.get("psst_scoring_config", {})

        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Priority weights sum to {total:.3f} (expected 1.0). "
                "Using normalised weights."
            )
            self.weights = {k: v / total for k, v in self.weights.items()}

        self.psst_calc = PSSTCalculator(self.psst_config)
        self._warn_count = 0

    # ── Public API ──────────────────────────────────────────────────────────

    def compute(
        self,
        classified_data: dict,
        impact_data: Optional[dict],
        filtered_signals: Optional[dict],
        date: str = "",
        workflow: str = "",
    ) -> dict:
        """
        Compute priority scores for all signals and return ranked output.

        Args:
            classified_data:  Contents of classified-signals-{date}.json
            impact_data:      Contents of impact-assessment-{date}.json (may be None)
            filtered_signals: Contents of new-signals-{date}.json for SR/TC source metadata
            date:             Scan date string (YYYY-MM-DD) for TC computation
            workflow:         Workflow name for output metadata

        Returns:
            Dict in priority-ranked-{date}.json format:
              {ranking_metadata: {...}, ranked_signals: [...]}
        """
        # Build signal lookup maps
        classified_map = self._build_classified_map(classified_data)
        impact_map = self._build_impact_map(impact_data)
        source_map = self._build_source_map(filtered_signals)

        all_ids = list(classified_map.keys())
        # Merge any IDs that only appear in impact-assessment
        for sid in list(impact_map.keys()):
            if sid not in all_ids:
                all_ids.append(sid)

        scored: list[dict] = []
        for signal_id in all_ids:
            entry = self._score_signal(
                signal_id,
                classified_map.get(signal_id, {}),
                impact_map.get(signal_id, {}),
                source_map.get(signal_id, {}),
                date,
            )
            scored.append(entry)

        # Sort descending by priority_score, then psst_score as tiebreaker
        scored.sort(key=lambda s: (s["priority_score"], s["psst_score"]), reverse=True)

        # Assign ranks
        for rank_idx, entry in enumerate(scored, start=1):
            entry["rank"] = rank_idx

        return {
            "ranking_metadata": {
                "engine": ENGINE_ID,
                "engine_version": VERSION,
                "workflow": workflow,
                "date": date,
                "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "method": "priority_formula_v1",
                "weights": self.weights,
                "total_ranked": len(scored),
                "warn_count": self._warn_count,
            },
            "ranked_signals": scored,
        }

    # ── Internal — per-signal scoring ───────────────────────────────────────

    def _score_signal(
        self,
        signal_id: str,
        classified: dict,
        impact: dict,
        source: dict,
        date: str,
    ) -> dict:
        """Compute all scores for a single signal. Returns the full scored dict."""

        # ── pSST dimensions ──────────────────────────────────────────────
        # Python-computable from structured data
        sr = self._compute_sr(source, classified)
        tc = self._compute_tc(source, classified, date)
        dc = self._compute_dc(classified, source)
        # LLM-assigned (from psst_dimensions field; fallback to 0)
        psst_dims_classified = classified.get("psst_dimensions", {})
        psst_dims_impact = impact.get("psst_dimensions", {})
        es = self._get_dim("ES", psst_dims_classified, psst_dims_impact)
        cc = self._get_dim("CC", psst_dims_classified, psst_dims_impact)
        ic = self._get_dim("IC", psst_dims_classified, psst_dims_impact)

        dimensions: dict[str, int] = {}
        for dim, val in [("SR", sr), ("TC", tc), ("DC", dc), ("ES", es), ("CC", cc), ("IC", ic)]:
            if val is not None:
                dimensions[dim] = int(max(0, min(100, val)))

        psst_result = self.psst_calc.calculate_psst(dimensions)
        psst_score: float = psst_result["psst_score"]
        psst_grade: str = psst_result["psst_grade"]

        # ── Priority components ──────────────────────────────────────────
        impact_score   = self._get_impact_score(impact, classified, psst_score)
        probability    = self._get_probability(classified, source)
        urgency        = self._get_urgency(classified, impact)
        novelty        = self._get_novelty(classified, impact)

        priority_score = (
            impact_score   * self.weights["impact"]
            + probability  * self.weights["probability"]
            + urgency      * self.weights["urgency"]
            + novelty      * self.weights["novelty"]
        )
        priority_score = round(
            max(PRIORITY_SCORE_MIN, min(PRIORITY_SCORE_MAX, priority_score)), 3
        )

        return {
            "rank": None,  # assigned after sorting
            "id": signal_id,
            "title": classified.get("title", impact.get("title", "")),
            "steeps": classified.get("steeps", impact.get("steeps", "")),
            "fssf_type": classified.get("fssf_type", ""),
            "three_horizons": classified.get("three_horizons", ""),
            # Core scoring
            "priority_score": priority_score,
            "psst_score": round(psst_score, 1),
            "psst_grade": psst_grade,
            # Component breakdown (for transparency / L3 review)
            "component_scores": {
                "impact":      round(impact_score, 3),
                "probability": round(probability, 3),
                "urgency":     round(urgency, 3),
                "novelty":     round(novelty, 3),
            },
            "psst_dimensions": dimensions,
        }

    # ── pSST dimension computation (Python 원천봉쇄) ─────────────────────

    def _compute_sr(self, source: dict, classified: dict) -> Optional[int]:
        """SR — Source Reliability: lookup by source type (deterministic table)."""
        source_type = (
            source.get("source", {}).get("type")
            or classified.get("source_type")
            or "unknown"
        )
        peer_reviewed = bool(
            source.get("source", {}).get("peer_reviewed")
            or classified.get("peer_reviewed", False)
        )
        return self.psst_calc.calculate_sr(
            source_type=source_type,
            peer_reviewed=peer_reviewed,
        )

    def _compute_tc(self, source: dict, classified: dict, date: str) -> Optional[int]:
        """TC — Temporal Currency: date arithmetic (deterministic formula)."""
        published_date = (
            source.get("source", {}).get("published_date")
            or classified.get("published_date")
        )
        signal_status = (
            classified.get("status")
            or classified.get("signal_status")
            or "developing"
        )
        return self.psst_calc.calculate_tc(
            published_date=published_date,
            signal_status=signal_status,
            reference_date=date or None,
        )

    def _compute_dc(self, classified: dict, source: dict) -> Optional[int]:
        """DC — Distinctiveness Confidence: dedup stage lookup (deterministic table)."""
        stage = (
            classified.get("dedup_stage_passed")
            or source.get("dedup_stage_passed")
        )
        if stage:
            score = DC_STAGE_SCORES.get(stage, DC_DEFAULT)
        else:
            # Fall back to dedup_confidence float (0–1 → 0–100)
            conf = classified.get("dedup_confidence") or source.get("dedup_confidence")
            if conf is not None:
                score = int(float(conf) * 100)
            else:
                self._warn("DC", classified.get("id", "?"))
                score = DC_DEFAULT
        return self.psst_calc.calculate_dc(
            dedup_stage_passed=stage or ("passed_all_4" if score >= 100 else "passed_3")
        )

    # ── Priority component getters (fallback chains) ─────────────────────

    def _get_dim(self, dim: str, *dicts: dict) -> Optional[int]:
        """Read a pSST dimension value from any of the provided dicts."""
        for d in dicts:
            val = d.get(dim)
            if val is not None:
                return int(val)
        return None

    def _get_impact_score(
        self, impact: dict, classified: dict, psst_score: float
    ) -> float:
        """
        Impact component (1–5).

        Priority:
          1. impact.impact_score (LLM-assigned in impact-assessment; native 1–5)
          2. Computed from impact_assessment fields (domain_diversity formula)
          3. Proxy from psst_score (0–100 → 0–5 rescale)
        """
        # Direct LLM-assigned score
        raw = impact.get("impact_score") or classified.get("impact_score")
        if raw is not None:
            return float(max(1.0, min(5.0, float(raw))))

        # Formula from affected_domains + first/second order impacts
        affected = impact.get("affected_domains", [])
        first_order = impact.get("first_order", [])
        second_order = impact.get("second_order", [])
        cross_impacts = impact.get("cross_impacts", [])
        if affected or first_order or second_order:
            domain_diversity = len(affected) / 6.0  # max 6 STEEPs
            impact_count = len(first_order) + len(second_order)
            influence = (
                sum(abs(float(i.get("influence_score", 0))) for i in cross_impacts) / 10.0
            )
            raw_score = (domain_diversity + impact_count / 10.0 + influence) / 3.0 * 5.0
            return max(1.0, min(5.0, raw_score))

        # Last resort proxy
        self._warn("impact", impact.get("id", classified.get("id", "?")))
        return max(1.0, min(5.0, psst_score / 20.0))

    def _get_probability(self, classified: dict, source: dict) -> float:
        """
        Probability component (1–5): (source_accuracy + confidence) / 2.

        - source_accuracy proxied from signal.accuracy or source reliability tier
        - confidence from classified.confidence (0–1 → 0–5)
        """
        # Direct LLM-assigned field
        prob = classified.get("probability") or classified.get("probability_score")
        if prob is not None:
            return float(max(1.0, min(5.0, float(prob))))

        accuracy = classified.get("accuracy")
        confidence_raw = classified.get("confidence")

        if accuracy is not None:
            acc_score = float(max(1.0, min(5.0, float(accuracy))))
        else:
            # Proxy from source type reliability (matches psst SR base scores / 20)
            source_type = source.get("source", {}).get("type", "")
            _sr_proxy = {
                "academic": 4.3, "patent": 4.0, "government": 4.0,
                "policy": 3.8, "news_major": 3.3, "news_minor": 2.5,
                "blog": 2.3, "social_media": 1.5,
            }
            acc_score = _sr_proxy.get(source_type, 3.0)

        if confidence_raw is not None:
            conf_score = float(confidence_raw) * 5.0
            conf_score = max(1.0, min(5.0, conf_score))
        else:
            conf_score = 3.0

        return (acc_score + conf_score) / 2.0

    def _get_urgency(self, classified: dict, impact: dict) -> float:
        """
        Urgency component (1–5): deterministic lookup from signal_status.

        URGENCY_LOOKUP = {emerging: 3, developing: 4, mature: 2}
        This is a pure lookup table — LLM determines the STATUS,
        Python maps it to a numeric score.
        """
        # Direct LLM-assigned urgency score
        raw = classified.get("urgency") or impact.get("urgency")
        if raw is not None:
            return float(max(1.0, min(5.0, float(raw))))

        status = (
            classified.get("status")
            or classified.get("signal_status")
            or impact.get("status")
            or ""
        )
        return URGENCY_LOOKUP.get(status.lower(), URGENCY_DEFAULT)

    def _get_novelty(self, classified: dict, impact: dict) -> float:
        """
        Novelty component (1–5): direct from innovative_capacity field.
        """
        for key in ("innovative_capacity", "novelty", "novelty_score"):
            val = classified.get(key) or impact.get(key)
            if val is not None:
                return float(max(1.0, min(5.0, float(val))))
        return 3.0  # neutral fallback

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _warn(self, field: str, signal_id: str) -> None:
        self._warn_count += 1
        logger.warning(f"Signal {signal_id}: {field} missing, using fallback")

    # ── Data loading ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_classified_map(classified_data: dict) -> dict[str, dict]:
        """Build {signal_id: signal_dict} from classified-signals JSON."""
        result: dict[str, dict] = {}
        for sig in classified_data.get("signals", classified_data.get("items", [])):
            sid = sig.get("id")
            if sid:
                result[sid] = sig
        return result

    @staticmethod
    def _build_impact_map(impact_data: Optional[dict]) -> dict[str, dict]:
        """Build {signal_id: signal_dict} from impact-assessment JSON."""
        if not impact_data:
            return {}
        result: dict[str, dict] = {}
        for sig in impact_data.get("signals", impact_data.get("assessments", impact_data.get("items", []))):
            sid = sig.get("id")
            if sid:
                result[sid] = sig
        return result

    @staticmethod
    def _build_source_map(filtered_signals: Optional[dict]) -> dict[str, dict]:
        """Build {signal_id: signal_dict} from filtered/new-signals JSON (for SR/TC metadata)."""
        if not filtered_signals:
            return {}
        result: dict[str, dict] = {}
        for item in filtered_signals.get("items", filtered_signals.get("signals", [])):
            sid = item.get("id")
            if sid:
                result[sid] = item
        return result

    @staticmethod
    def _load_thresholds(path: str) -> dict:
        p = Path(path)
        if not p.exists():
            logger.warning(f"thresholds.yaml not found: {path}. Using defaults.")
            return {}
        try:
            if _YAML_AVAILABLE:
                with open(p, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning("PyYAML not available. Using default weights.")
                return {}
        except Exception as exc:
            logger.warning(f"Failed to load thresholds: {exc}. Using defaults.")
            return {}


# ---------------------------------------------------------------------------
# Convenience function (importable)
# ---------------------------------------------------------------------------

def compute_priority_ranking(
    classified_path: str,
    impact_path: Optional[str],
    filtered_path: Optional[str],
    thresholds_path: Optional[str],
    workflow: str,
    date: str,
) -> dict:
    """
    High-level wrapper: load files → compute → return ranked dict.

    Returns:
        priority-ranked dict (same format as priority-ranked-{date}.json)
    """
    def _load(path: Optional[str], label: str) -> Optional[dict]:
        if not path:
            return None
        p = Path(path)
        if not p.exists():
            logger.warning(f"{label} not found: {path}")
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    classified = _load(classified_path, "classified-signals")
    if not classified:
        raise FileNotFoundError(f"classified-signals file not found: {classified_path}")

    impact   = _load(impact_path,   "impact-assessment")
    filtered = _load(filtered_path, "filtered-signals")

    calc = PriorityScoreCalculator(thresholds_path=thresholds_path)
    return calc.compute(classified, impact, filtered, date=date, workflow=workflow)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Priority Score Calculator — deterministic Phase 2 Step 2.3"
    )
    parser.add_argument(
        "--classified", required=True,
        help="Path to classified-signals-{date}.json",
    )
    parser.add_argument(
        "--impact", default=None,
        help="Path to impact-assessment-{date}.json (optional)",
    )
    parser.add_argument(
        "--filtered", default=None,
        help="Path to new-signals-{date}.json for SR/TC source metadata (optional)",
    )
    parser.add_argument(
        "--thresholds", default=None,
        help="Path to thresholds.yaml (optional — uses defaults if absent)",
    )
    parser.add_argument(
        "--workflow", default="",
        help="Workflow name for output metadata (e.g., wf1-general)",
    )
    parser.add_argument(
        "--date", default="",
        help="Scan date (YYYY-MM-DD) for TC computation",
    )
    parser.add_argument(
        "--output", required=True,
        help="Output path for priority-ranked-{date}.json",
    )
    args = parser.parse_args()

    try:
        result = compute_priority_ranking(
            classified_path=args.classified,
            impact_path=args.impact,
            filtered_path=args.filtered,
            thresholds_path=args.thresholds,
            workflow=args.workflow,
            date=args.date,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    meta = result["ranking_metadata"]
    warn = meta["warn_count"]
    print("=" * 60)
    print(f"  Priority Score Calculator v{VERSION}")
    print(f"  Workflow: {meta['workflow'] or '(unset)'}")
    print(f"  Signals ranked: {meta['total_ranked']}")
    print(f"  Weights: impact={meta['weights']['impact']:.0%}  "
          f"prob={meta['weights']['probability']:.0%}  "
          f"urg={meta['weights']['urgency']:.0%}  "
          f"nov={meta['weights']['novelty']:.0%}")
    if warn:
        print(f"  ⚠️  Fallback warnings: {warn} (fields missing — check agent output schema)")
    else:
        print("  ✅ All component scores computed without fallback")
    print(f"  Output: {args.output}")
    print("=" * 60)

    sys.exit(2 if warn else 0)


if __name__ == "__main__":
    main()
