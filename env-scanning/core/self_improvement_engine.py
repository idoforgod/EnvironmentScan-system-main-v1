"""
Self-Improvement Engine (SIE) for Environmental Scanning Workflow.

Analyzes performance metrics after each workflow run, identifies improvement
opportunities, and safely applies MINOR parameter changes while proposing
MAJOR changes for user approval and blocking CRITICAL invariant violations.

Design Principle: "Improve the tuning, never break the machine"

Version: 1.0.0
"""

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ChangeClassification:
    """Safety classification levels for proposed changes."""

    MINOR = "MINOR"      # Auto-apply: tunable parameters only
    MAJOR = "MAJOR"      # User approval required: behavioral changes
    CRITICAL = "CRITICAL"  # Always blocked: core invariant violations


class ImprovementStatus:
    """Status values for improvement records."""

    APPLIED = "applied"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    BLOCKED = "blocked_critical"
    ROLLED_BACK = "rolled_back"


class SelfImprovementEngine:
    """
    Core engine for autonomous self-improvement of workflow parameters.

    Operates after Step 3.5 (Quality Metrics) to analyze performance,
    identify improvements, and safely apply or propose changes.
    """

    def __init__(self, base_path: str):
        """
        Initialize the SIE with paths to all required files.

        Args:
            base_path: Root path to env-scanning/ directory.
        """
        self.base_path = Path(base_path)
        self.config = self._load_yaml_as_dict(
            self.base_path / "config" / "self-improvement-config.yaml"
        ) or {}
        self.invariants = self._load_yaml_as_dict(
            self.base_path / "config" / "core-invariants.yaml"
        ) or {}
        self.thresholds = self._load_yaml_as_dict(
            self.base_path / "config" / "thresholds.yaml"
        ) or {}
        self.improvement_log = self._load_improvement_log()
        self._applied_changes: list[dict] = []
        self._cycle_change_count = 0

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def run_cycle(self, current_metrics_path: str) -> dict:
        """
        Execute a full self-improvement cycle.

        Steps:
            1. Collect current + historical metrics
            2. Analyze deltas and patterns
            3. Generate improvement proposals
            4. Classify each proposal (MINOR/MAJOR/CRITICAL)
            5. Apply MINOR, stage MAJOR, block CRITICAL
            6. Record all actions

        Args:
            current_metrics_path: Path to the current workflow's
                quality-metrics JSON file.

        Returns:
            Cycle result dict with applied, proposed, and blocked changes.
        """
        sie_config = self.config.get("self_improvement", {})
        if not sie_config.get("enabled", False):
            return {"status": "disabled", "changes": []}

        safety = sie_config.get("safety", {})
        max_minor = safety.get("max_minor_changes_per_cycle", 3)

        # Phase A: Collect & Compare
        current_metrics = self._load_json(current_metrics_path)
        historical_metrics = self._load_historical_metrics()

        if len(historical_metrics) < safety.get("min_workflow_history", 3):
            return {
                "status": "insufficient_history",
                "history_count": len(historical_metrics),
                "required": safety.get("min_workflow_history", 3),
                "changes": [],
            }

        # Phase B: Analyze & Propose
        proposals = []
        analysis_areas = sie_config.get("analysis_areas", {})

        if analysis_areas.get("threshold_tuning", {}).get("enabled", False):
            proposals.extend(
                self._analyze_threshold_tuning(current_metrics, historical_metrics)
            )

        if analysis_areas.get("agent_performance", {}).get("enabled", False):
            proposals.extend(
                self._analyze_agent_performance(current_metrics, historical_metrics)
            )

        if analysis_areas.get("classification_quality", {}).get("enabled", False):
            proposals.extend(
                self._analyze_classification_quality(current_metrics, historical_metrics)
            )

        if analysis_areas.get("workflow_efficiency", {}).get("enabled", False):
            proposals.extend(
                self._analyze_workflow_efficiency(current_metrics, historical_metrics)
            )

        if analysis_areas.get("hallucination_tracking", {}).get("enabled", False):
            proposals.extend(
                self._analyze_hallucination_tracking(current_metrics, historical_metrics)
            )

        if analysis_areas.get("source_health", {}).get("enabled", False):
            proposals.extend(
                self._analyze_source_health(current_metrics, historical_metrics)
            )

        # Phase C: Classify and Execute
        results = {
            "status": "completed",
            "cycle_timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_id": current_metrics.get("workflow_id", "unknown"),
            "applied": [],
            "proposed": [],
            "blocked": [],
        }

        for proposal in proposals:
            classification = self._classify_change(proposal)
            proposal["type"] = classification

            if classification == ChangeClassification.CRITICAL:
                proposal["status"] = ImprovementStatus.BLOCKED
                proposal["reason_blocked"] = "Core invariant violation detected"
                results["blocked"].append(proposal)

            elif classification == ChangeClassification.MAJOR:
                proposal["status"] = ImprovementStatus.PROPOSED
                self._save_proposal(proposal)
                results["proposed"].append(proposal)

            elif classification == ChangeClassification.MINOR:
                if self._cycle_change_count >= max_minor:
                    proposal["status"] = ImprovementStatus.PROPOSED
                    proposal["reason_deferred"] = (
                        f"Max minor changes ({max_minor}) reached this cycle"
                    )
                    self._save_proposal(proposal)
                    results["proposed"].append(proposal)
                else:
                    success = self._apply_minor_change(proposal)
                    if success:
                        proposal["status"] = ImprovementStatus.APPLIED
                        proposal["applied_at"] = datetime.now(timezone.utc).isoformat()
                        proposal["rollback_available"] = True
                        self._applied_changes.append(proposal)
                        self._cycle_change_count += 1
                        results["applied"].append(proposal)
                    else:
                        proposal["status"] = ImprovementStatus.REJECTED
                        proposal["reason_rejected"] = "Validation failed during apply"
                        results["blocked"].append(proposal)

        # Phase D: Record
        self._record_improvements(results)

        return results

    def rollback_last_cycle(self) -> dict:
        """
        Roll back all changes applied in the most recent SIE cycle.

        Returns:
            Rollback result with list of reverted changes.
        """
        log = self.improvement_log
        improvements = log.get("improvements", [])

        # Find the most recent cycle's applied changes
        if not improvements:
            return {"status": "nothing_to_rollback", "reverted": []}

        last_cycle_id = None
        to_rollback = []

        for imp in reversed(improvements):
            if imp.get("status") == ImprovementStatus.APPLIED and imp.get("rollback_available"):
                if last_cycle_id is None:
                    last_cycle_id = imp.get("workflow_id")
                if imp.get("workflow_id") == last_cycle_id:
                    to_rollback.append(imp)
                else:
                    break

        reverted = []
        for change in to_rollback:
            success = self._revert_change(change)
            if success:
                change["status"] = ImprovementStatus.ROLLED_BACK
                change["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
                change["rollback_available"] = False
                reverted.append(change)

        # Update log
        self._save_improvement_log()

        stats = log.get("stats", {})
        stats["total_rolled_back"] = stats.get("total_rolled_back", 0) + len(reverted)
        stats["total_applied"] = max(0, stats.get("total_applied", 0) - len(reverted))

        self._save_improvement_log()

        return {"status": "rolled_back", "reverted": reverted}

    def check_regression(self, current_metrics: dict, previous_metrics: dict) -> bool:
        """
        Check if performance regressed after SIE changes.

        Args:
            current_metrics: Latest workflow metrics.
            previous_metrics: Metrics from before SIE changes.

        Returns:
            True if regression detected (should trigger rollback).
        """
        threshold = (
            self.config.get("self_improvement", {})
            .get("rollback", {})
            .get("regression_threshold", 0.05)
        )

        quality_current = current_metrics.get("quality_scores", {})
        quality_previous = previous_metrics.get("quality_scores", {})

        for metric_key in ["dedup_accuracy", "classification_accuracy", "human_ai_agreement"]:
            curr = quality_current.get(metric_key, 0)
            prev = quality_previous.get(metric_key, 0)
            if prev > 0 and (prev - curr) / prev > threshold:
                return True

        return False

    # ─────────────────────────────────────────────
    # Analysis Methods (5 Areas)
    # ─────────────────────────────────────────────

    def _analyze_threshold_tuning(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """Area 1: Analyze dedup/confidence thresholds for tuning opportunities."""
        proposals = []
        quality = current.get("quality_scores", {})
        targets = current.get("performance_targets", {})
        min_sample = (
            self.config.get("self_improvement", {})
            .get("safety", {})
            .get("min_evidence_sample_size", 10)
        )
        signals = current.get("signals_processed", {})
        sample_size = signals.get("collected", 0)

        if sample_size < min_sample:
            return proposals

        # Check dedup accuracy vs target
        dedup_target = targets.get("dedup_accuracy", {})
        if isinstance(dedup_target, dict):
            actual = dedup_target.get("actual", 0)
            target = dedup_target.get("target", 0.95)

            if actual < target:
                # Dedup accuracy below target — consider tightening semantic threshold
                current_threshold = self._get_nested_value(
                    self.thresholds,
                    "deduplication.stage_3_semantic_similarity.threshold",
                )
                if current_threshold is not None:
                    delta = min(0.02, current_threshold * 0.05)
                    new_value = round(current_threshold + delta, 4)
                    proposals.append({
                        "id": self._generate_id("threshold"),
                        "category": "threshold_tuning",
                        "target_file": "config/thresholds.yaml",
                        "target_field": "deduplication.stage_3_semantic_similarity.threshold",
                        "old_value": current_threshold,
                        "new_value": new_value,
                        "reason": (
                            f"Dedup accuracy {actual:.2%} below target {target:.2%}. "
                            f"Tightening semantic similarity threshold to reduce false positives."
                        ),
                        "evidence": {
                            "dedup_accuracy": actual,
                            "target": target,
                            "sample_size": sample_size,
                        },
                    })

            elif actual > target + 0.03:
                # Significantly above target — could loosen slightly for recall
                current_threshold = self._get_nested_value(
                    self.thresholds,
                    "deduplication.stage_3_semantic_similarity.threshold",
                )
                if current_threshold is not None and current_threshold > 0.65:
                    delta = min(0.02, current_threshold * 0.03)
                    new_value = round(current_threshold - delta, 4)
                    proposals.append({
                        "id": self._generate_id("threshold"),
                        "category": "threshold_tuning",
                        "target_file": "config/thresholds.yaml",
                        "target_field": "deduplication.stage_3_semantic_similarity.threshold",
                        "old_value": current_threshold,
                        "new_value": new_value,
                        "reason": (
                            f"Dedup accuracy {actual:.2%} well above target {target:.2%}. "
                            f"Loosening threshold slightly to improve recall."
                        ),
                        "evidence": {
                            "dedup_accuracy": actual,
                            "target": target,
                            "sample_size": sample_size,
                        },
                    })

        return proposals

    def _analyze_agent_performance(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """Area 2: Analyze agent execution times and error rates."""
        proposals = []
        agent_perf = current.get("agent_performance", {})
        phase_times = current.get("phase_times", {})

        # Calculate average historical phase times
        avg_phase_times = {}
        for hist in history:
            for phase, time_val in hist.get("phase_times", {}).items():
                if phase not in avg_phase_times:
                    avg_phase_times[phase] = []
                avg_phase_times[phase].append(time_val)

        for phase, times in avg_phase_times.items():
            if times:
                avg_phase_times[phase] = sum(times) / len(times)

        # Check if current phase times consistently exceed targets
        perf_config = self.thresholds.get("performance", {})
        phase_target_map = {
            "phase_1": perf_config.get("execution_time_phase_1", 60),
            "phase_2": perf_config.get("execution_time_phase_2", 40),
            "phase_3": perf_config.get("execution_time_phase_3", 35),
        }

        for phase, target in phase_target_map.items():
            current_time = phase_times.get(phase, 0)
            avg_historical = avg_phase_times.get(phase, target)

            # If consistently exceeding target by >20%, suggest timeout increase
            if (
                current_time > target * 1.2
                and isinstance(avg_historical, (int, float))
                and avg_historical > target * 1.1
            ):
                field_map = {
                    "phase_1": "performance.execution_time_phase_1",
                    "phase_2": "performance.execution_time_phase_2",
                    "phase_3": "performance.execution_time_phase_3",
                }
                new_target = round(min(target * 1.1, current_time * 0.95))
                proposals.append({
                    "id": self._generate_id("agent_perf"),
                    "category": "agent_performance",
                    "target_file": "config/thresholds.yaml",
                    "target_field": field_map[phase],
                    "old_value": target,
                    "new_value": new_target,
                    "reason": (
                        f"{phase} average time {avg_historical:.0f}s exceeds target {target}s. "
                        f"Adjusting target to realistic level."
                    ),
                    "evidence": {
                        "current_time": current_time,
                        "average_historical": avg_historical,
                        "target": target,
                        "history_count": len(history),
                    },
                })

        return proposals

    def _analyze_classification_quality(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """Area 3: Analyze classification accuracy and confidence distribution."""
        proposals = []
        quality = current.get("quality_scores", {})
        classification_acc = quality.get("classification_accuracy", 0)
        target_acc = self._get_nested_value(
            self.thresholds, "quality_targets.classification_accuracy"
        )

        if target_acc is None:
            return proposals

        # Check if classification accuracy trending downward
        historical_accs = [
            h.get("quality_scores", {}).get("classification_accuracy", 0)
            for h in history
            if h.get("quality_scores", {}).get("classification_accuracy", 0) > 0
        ]

        if len(historical_accs) >= 3:
            trend = self._calculate_trend(historical_accs)
            if trend < -0.01 and classification_acc < target_acc:
                # Declining classification accuracy — suggest confidence threshold tightening
                current_high = self._get_nested_value(
                    self.thresholds, "ai_confidence.high"
                )
                if current_high is not None and current_high < 0.95:
                    proposals.append({
                        "id": self._generate_id("classification"),
                        "category": "classification_quality",
                        "target_file": "config/thresholds.yaml",
                        "target_field": "ai_confidence.high",
                        "old_value": current_high,
                        "new_value": round(min(current_high + 0.02, 0.95), 4),
                        "reason": (
                            f"Classification accuracy declining (trend: {trend:.4f}/run). "
                            f"Current {classification_acc:.2%} below target {target_acc:.2%}. "
                            f"Raising auto-approve threshold to require higher confidence."
                        ),
                        "evidence": {
                            "classification_accuracy": classification_acc,
                            "target": target_acc,
                            "trend": trend,
                            "historical_values": historical_accs[-3:],
                        },
                    })

        return proposals

    def _analyze_workflow_efficiency(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """Area 4: Identify bottlenecks and timing improvements."""
        proposals = []
        agent_perf = current.get("agent_performance", {})

        # Identify slowest agent as bottleneck
        slowest_agent = None
        slowest_time = 0
        for agent_name, perf in agent_perf.items():
            t = perf.get("time", 0)
            if t > slowest_time:
                slowest_time = t
                slowest_agent = agent_name

        if slowest_agent and slowest_time > 0:
            # Check if this agent is consistently the bottleneck
            bottleneck_count = 0
            for hist in history:
                hist_perf = hist.get("agent_performance", {})
                hist_slowest = max(
                    hist_perf.items(),
                    key=lambda x: x[1].get("time", 0),
                    default=(None, {}),
                )
                if hist_slowest[0] == slowest_agent:
                    bottleneck_count += 1

            if bottleneck_count >= len(history) * 0.6:
                # This is a MAJOR proposal — workflow restructuring suggestion
                proposals.append({
                    "id": self._generate_id("efficiency"),
                    "category": "workflow_efficiency",
                    "target_file": None,
                    "target_field": None,
                    "old_value": None,
                    "new_value": None,
                    "reason": (
                        f"Agent '{slowest_agent}' is the consistent bottleneck "
                        f"({bottleneck_count}/{len(history)} runs, current: {slowest_time}s). "
                        f"Consider investigating optimization opportunities."
                    ),
                    "evidence": {
                        "bottleneck_agent": slowest_agent,
                        "current_time": slowest_time,
                        "bottleneck_frequency": f"{bottleneck_count}/{len(history)}",
                    },
                    "suggestion_type": "investigation",
                })

        return proposals

    def _analyze_hallucination_tracking(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """Area 5: Detect fabrication patterns and tighten validation."""
        proposals = []
        errors = current.get("errors", [])
        verification = current.get("verification_summary", {})

        # Count verification warnings as potential hallucination indicators
        warned = verification.get("warned", 0)
        total_checks = verification.get("total_checks", 1)

        if total_checks > 0:
            warn_rate = warned / total_checks
        else:
            warn_rate = 0

        # Track historical warn rates
        historical_warn_rates = []
        for hist in history:
            v = hist.get("verification_summary", {})
            h_warned = v.get("warned", 0)
            h_total = v.get("total_checks", 1)
            if h_total > 0:
                historical_warn_rates.append(h_warned / h_total)

        if len(historical_warn_rates) >= 3:
            trend = self._calculate_trend(historical_warn_rates)
            if trend > 0.005:
                # Warning rate increasing — hallucination controls may need tightening
                # This is a MAJOR change (tightening verification is behavioral)
                proposals.append({
                    "id": self._generate_id("hallucination"),
                    "category": "hallucination_tracking",
                    "target_file": None,
                    "target_field": None,
                    "old_value": None,
                    "new_value": None,
                    "reason": (
                        f"Verification warning rate trending upward "
                        f"(trend: +{trend:.4f}/run, current: {warn_rate:.2%}). "
                        f"Recommend reviewing verification strictness."
                    ),
                    "evidence": {
                        "current_warn_rate": warn_rate,
                        "trend": trend,
                        "historical_rates": historical_warn_rates[-3:],
                    },
                    "suggestion_type": "investigation",
                })

        return proposals

    def _analyze_source_health(
        self, current: dict, history: list[dict]
    ) -> list[dict]:
        """
        Area 6: Source health analysis.

        Reads health-history.jsonl to detect:
        1. Sources that failed consecutively (3+ times) — recommends URL replacement
        2. Strategy cache effectiveness — tracks adaptive fetch hit rates
        3. Redirect patterns — identifies persistent URL drift
        """
        proposals = []
        health_config = (
            self.config.get("self_improvement", {})
            .get("analysis_areas", {})
            .get("source_health", {})
        )
        failure_threshold = health_config.get("consecutive_failure_threshold", 3)
        auto_disable_threshold = health_config.get("auto_disable_threshold", 5)

        health_history = self._load_health_history()
        if not health_history:
            return proposals

        # Build per-source timeline from history
        source_timelines: dict[str, list[dict]] = {}
        for record in health_history:
            for source_name, info in record.get("sources", {}).items():
                source_timelines.setdefault(source_name, []).append(info)

        # Detect consecutive failures (count from end of timeline)
        for source_name, records in source_timelines.items():
            # Count actual consecutive unhealthy records from the tail
            consecutive_failures = 0
            for r in reversed(records):
                if r.get("health") == "unhealthy":
                    consecutive_failures += 1
                else:
                    break

            if consecutive_failures >= failure_threshold:
                recent = records[-consecutive_failures:]
                error_pattern = [r.get("reason", "unknown") for r in recent]
                reason = (
                    f"Source '{source_name}' failed {consecutive_failures} consecutive scans. "
                    f"Error pattern: {error_pattern}. "
                    f"Recommend URL replacement or disabling."
                )

                # If beyond auto-disable threshold, suggest disabling
                if consecutive_failures >= auto_disable_threshold:
                    reason += (
                        f" Exceeded auto-disable threshold ({auto_disable_threshold}). "
                        f"Strongly recommend disabling this source."
                    )

                proposals.append({
                    "id": self._generate_id("source_health"),
                    "category": "source_health",
                    "target_file": "config/sources.yaml",
                    "target_field": None,
                    "old_value": None,
                    "new_value": None,
                    "reason": reason,
                    "evidence": {
                        "source_name": source_name,
                        "consecutive_failures": consecutive_failures,
                        "error_pattern": error_pattern,
                    },
                    "suggestion_type": "investigation",
                })

        return proposals

    def _load_health_history(self) -> list[dict]:
        """Load health check history from health/health-history.jsonl."""
        history_path = self.base_path / "health" / "health-history.jsonl"
        if not history_path.exists():
            return []

        records = []
        try:
            with open(history_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except OSError:
            return []

        return records

    # ─────────────────────────────────────────────
    # Classification & Safety
    # ─────────────────────────────────────────────

    def _classify_change(self, proposal: dict) -> str:
        """
        Classify a proposed change as MINOR, MAJOR, or CRITICAL.

        Checks:
            1. Does it touch a core invariant? → CRITICAL
            2. Is it a tunable parameter within bounds? → MINOR
            3. Everything else → MAJOR
        """
        target_field = proposal.get("target_field")
        target_file = proposal.get("target_file")
        suggestion_type = proposal.get("suggestion_type")

        # Investigation-only suggestions are always MAJOR
        if suggestion_type == "investigation":
            return ChangeClassification.MAJOR

        # No target field means no concrete change — MAJOR (informational)
        if not target_field:
            return ChangeClassification.MAJOR

        # Check against core invariants
        if self._touches_core_invariant(target_field, target_file):
            return ChangeClassification.CRITICAL

        # Check if it's a known tunable parameter within bounds
        if self._is_tunable_within_bounds(proposal):
            return ChangeClassification.MINOR

        # Default: MAJOR (requires user approval)
        return ChangeClassification.MAJOR

    def _touches_core_invariant(self, target_field: str, target_file: str | None) -> bool:
        """Check if a change target touches any core invariant."""
        invariants = self.invariants.get("core_invariants", {})

        # Fields that are absolutely immutable
        immutable_keywords = [
            "workflow_phases", "human_checkpoints", "steeps_categories",
            "vev_protocol", "pipeline_gates", "database_atomicity",
            "phase_ordering", "bilingual_protocol",
            "report_quality_defense",
        ]

        field_lower = target_field.lower()
        for keyword in immutable_keywords:
            if keyword in field_lower:
                return True

        # Check specific field patterns
        if any(
            pattern in field_lower
            for pattern in [
                "stage_1_url_exact.threshold",  # URL exact match must stay at 1.0
                "phase_order", "checkpoint", "steeps",
                "validate_report", "skeleton", "golden_reference",
                "report_quality", "min_signal_blocks", "required_fields",
                "min_total_words", "min_korean_char_ratio",
            ]
        ):
            return True

        return False

    def _is_tunable_within_bounds(self, proposal: dict) -> bool:
        """Verify a proposed change is a known tunable parameter within bounds."""
        target_field = proposal.get("target_field", "")
        old_value = proposal.get("old_value")
        new_value = proposal.get("new_value")

        if old_value is None or new_value is None:
            return False

        # Find matching tunable parameter definition
        tunables = self.invariants.get("tunable_parameters", {})
        for category_key, category in tunables.items():
            if not isinstance(category, dict) or "fields" not in category:
                continue
            for field_def in category["fields"]:
                if field_def.get("path") == target_field:
                    # Found the definition — validate bounds
                    min_val = field_def.get("min_value")
                    max_val = field_def.get("max_value")
                    max_delta = field_def.get("max_delta_per_cycle")

                    if min_val is not None and new_value < min_val:
                        return False
                    if max_val is not None and new_value > max_val:
                        return False
                    if max_delta is not None and abs(new_value - old_value) > max_delta:
                        return False

                    # Check global max_threshold_delta_percent
                    max_pct = (
                        self.config.get("self_improvement", {})
                        .get("safety", {})
                        .get("max_threshold_delta_percent", 10)
                    )
                    if old_value != 0:
                        pct_change = abs(new_value - old_value) / abs(old_value) * 100
                        if pct_change > max_pct:
                            return False

                    return True

        return False

    # ─────────────────────────────────────────────
    # Apply & Rollback
    # ─────────────────────────────────────────────

    def _apply_minor_change(self, proposal: dict) -> bool:
        """
        Apply a MINOR change to the target config file.

        Returns True on success, False on validation failure.
        """
        target_file = proposal.get("target_file")
        target_field = proposal.get("target_field")
        new_value = proposal.get("new_value")

        if not all([target_file, target_field, new_value is not None]):
            return False

        file_path = self.base_path / target_file

        try:
            config = self._load_yaml_as_dict(file_path)
            if config is None:
                return False

            # Check sum constraints (e.g., weights must sum to 1.0)
            constraint = self._find_field_constraint(target_field)
            if constraint and "sum_of_all_weights_must_equal_1.0" in constraint:
                if not self._validate_sum_constraint(config, target_field, new_value):
                    return False

            # Apply the change
            old_config = copy.deepcopy(config)
            success = self._set_nested_value(config, target_field, new_value)
            if not success:
                return False

            # Validate the modified config is still parseable
            self._save_yaml(file_path, config)

            # Verify it can be re-loaded
            verification = self._load_yaml_as_dict(file_path)
            if verification is None:
                # Rollback — restore old config
                self._save_yaml(file_path, old_config)
                return False

            # Reload thresholds if that's what we changed
            if "thresholds" in target_file:
                self.thresholds = verification

            return True

        except Exception:
            return False

    def _revert_change(self, change: dict) -> bool:
        """Revert a previously applied change."""
        target_file = change.get("target_file")
        target_field = change.get("target_field")
        old_value = change.get("old_value")

        if not all([target_file, target_field, old_value is not None]):
            return False

        file_path = self.base_path / target_file

        try:
            config = self._load_yaml_as_dict(file_path)
            if config is None:
                return False

            success = self._set_nested_value(config, target_field, old_value)
            if not success:
                return False

            self._save_yaml(file_path, config)
            return True

        except Exception:
            return False

    # ─────────────────────────────────────────────
    # Recording & Persistence
    # ─────────────────────────────────────────────

    def _record_improvements(self, results: dict) -> None:
        """Record all improvement actions to the improvement log."""
        log = self.improvement_log
        improvements = log.get("improvements", [])
        stats = log.get("stats", {})

        all_changes = results.get("applied", []) + results.get("proposed", []) + results.get("blocked", [])

        for change in all_changes:
            record = {
                "id": change.get("id", self._generate_id("unknown")),
                "workflow_id": results.get("workflow_id", "unknown"),
                "type": change.get("type", "UNKNOWN"),
                "category": change.get("category", "unknown"),
                "target_file": change.get("target_file"),
                "target_field": change.get("target_field"),
                "old_value": change.get("old_value"),
                "new_value": change.get("new_value"),
                "reason": change.get("reason", ""),
                "evidence": change.get("evidence", {}),
                "status": change.get("status", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if change.get("applied_at"):
                record["applied_at"] = change["applied_at"]
            if change.get("rollback_available"):
                record["rollback_available"] = True
            improvements.append(record)

        stats["total_applied"] = stats.get("total_applied", 0) + len(results.get("applied", []))
        stats["total_proposed"] = stats.get("total_proposed", 0) + len(results.get("proposed", []))
        stats["total_rejected"] = stats.get("total_rejected", 0) + len(
            [b for b in results.get("blocked", []) if b.get("type") != ChangeClassification.CRITICAL]
        )
        stats["total_blocked_critical"] = stats.get("total_blocked_critical", 0) + len(
            [b for b in results.get("blocked", []) if b.get("type") == ChangeClassification.CRITICAL]
        )

        log["improvements"] = improvements
        log["stats"] = stats
        log["last_cycle"] = results.get("cycle_timestamp")

        self.improvement_log = log
        self._save_improvement_log()

    def _save_proposal(self, proposal: dict) -> None:
        """Save a MAJOR proposal to the proposals directory for user review."""
        proposals_dir = self.base_path / "self-improvement" / "proposals"
        proposals_dir.mkdir(parents=True, exist_ok=True)

        proposal_id = proposal.get("id", self._generate_id("proposal"))
        file_path = proposals_dir / f"{proposal_id}.json"

        proposal_doc = {
            "id": proposal_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review",
            "proposal": proposal,
            "review_instructions": (
                "이 개선 제안을 검토해 주세요. "
                "승인하면 적용되고, 거절하면 기록만 남습니다."
            ),
        }

        self._save_json(file_path, proposal_doc)

    # ─────────────────────────────────────────────
    # Utility Methods
    # ─────────────────────────────────────────────

    def _load_json(self, path: str | Path) -> dict:
        """Load a JSON file, returning empty dict on failure."""
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_json(self, path: str | Path, data: dict) -> None:
        """Save data as JSON with pretty printing."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_yaml_as_dict(self, path: str | Path) -> dict | None:
        """Load a YAML file as a dictionary."""
        try:
            import yaml

            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback: parse simple YAML manually for basic key-value configs
            return self._simple_yaml_parse(path)
        except (FileNotFoundError, Exception):
            return None

    def _save_yaml(self, path: str | Path, data: dict) -> None:
        """Save data as YAML."""
        try:
            import yaml

            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        except ImportError:
            # If PyYAML not available, save as JSON (safe fallback)
            self._save_json(Path(str(path) + ".json"), data)

    def _simple_yaml_parse(self, path: str | Path) -> dict | None:
        """Minimal YAML parser for flat key-value files when PyYAML unavailable."""
        try:
            result = {}
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        key, _, value = line.partition(":")
                        value = value.strip().strip('"').strip("'")
                        if value:
                            try:
                                result[key.strip()] = json.loads(value)
                            except (json.JSONDecodeError, ValueError):
                                result[key.strip()] = value
            return result
        except FileNotFoundError:
            return None

    def _load_improvement_log(self) -> dict:
        """Load the improvement log, creating initial structure if missing."""
        log_path = self.base_path / "self-improvement" / "improvement-log.json"
        if log_path.exists():
            return self._load_json(log_path)
        return {
            "version": "1.0.0",
            "improvements": [],
            "stats": {
                "total_applied": 0,
                "total_proposed": 0,
                "total_rejected": 0,
                "total_blocked_critical": 0,
                "total_rolled_back": 0,
            },
            "last_cycle": None,
        }

    def _save_improvement_log(self) -> None:
        """Persist the improvement log to disk."""
        log_path = self.base_path / "self-improvement" / "improvement-log.json"
        self._save_json(log_path, self.improvement_log)

    def _load_historical_metrics(self) -> list[dict]:
        """Load the last N workflow metrics for comparison."""
        window = (
            self.config.get("self_improvement", {})
            .get("comparison", {})
            .get("history_window", 5)
        )
        metrics_dir = self.base_path / "logs" / "quality-metrics"

        if not metrics_dir.exists():
            return []

        # Find all workflow-*.json files (excluding -ko translations)
        metric_files = sorted(
            [
                f
                for f in metrics_dir.glob("workflow-*.json")
                if not f.stem.endswith("-ko")
            ],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        # Skip the most recent (current run) and take the next N
        historical = []
        for f in metric_files[1 : window + 1]:
            data = self._load_json(f)
            if data:
                historical.append(data)

        return historical

    def _get_nested_value(self, d: dict, path: str) -> Any:
        """Get a value from a nested dict using dot-notation path."""
        keys = path.split(".")
        current = d
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _set_nested_value(self, d: dict, path: str, value: Any) -> bool:
        """Set a value in a nested dict using dot-notation path."""
        keys = path.split(".")
        current = d
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        if isinstance(current, dict):
            current[keys[-1]] = value
            return True
        return False

    def _find_field_constraint(self, target_field: str) -> str | None:
        """Find any constraint defined for a tunable parameter."""
        tunables = self.invariants.get("tunable_parameters", {})
        for category_key, category in tunables.items():
            if not isinstance(category, dict) or "fields" not in category:
                continue
            for field_def in category["fields"]:
                if field_def.get("path") == target_field:
                    return field_def.get("constraint")
        return None

    def _validate_sum_constraint(
        self, config: dict, target_field: str, new_value: float
    ) -> bool:
        """Validate that weight fields still sum to 1.0 after change."""
        # Determine the parent path to find sibling weights
        parts = target_field.rsplit(".", 1)
        if len(parts) < 2:
            return True

        parent_path = parts[0]
        parent = self._get_nested_value(config, parent_path)
        if not isinstance(parent, dict):
            return True

        # Calculate new sum
        changed_key = parts[1]
        total = 0.0
        for key, val in parent.items():
            if isinstance(val, (int, float)):
                if key == changed_key:
                    total += new_value
                else:
                    total += val

        return abs(total - 1.0) < 0.001

    def _calculate_trend(self, values: list[float]) -> float:
        """Calculate simple linear trend (slope) from a list of values."""
        n = len(values)
        if n < 2:
            return 0.0

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _generate_id(self, category: str) -> str:
        """Generate a unique improvement ID."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing = len(self.improvement_log.get("improvements", []))
        return f"imp-{date_str}-{category}-{existing + 1:03d}"
