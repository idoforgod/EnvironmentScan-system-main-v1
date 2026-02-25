"""
Unit tests for exploration_gate.py

Tests the three gate commands (check, post, verify) covering:
- Normal flow (exploration enabled, MUST_RUN)
- Disabled flow (SKIP_DISABLED)
- Base-only flow (SKIP_BASE_ONLY)
- Gap analysis preview
- History recording with duplicate prevention
- Proof verification checks (VP-1 through VP-5)
- VP-5: Frontier selection file existence (Python-enforced anti-hallucination guard)
- Edge cases (missing files, malformed JSON)
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add core/ to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning" / "core"))
from exploration_gate import (
    gate_check,
    gate_post,
    gate_verify,
    DECISION_MUST_RUN,
    DECISION_SKIP_DISABLED,
    DECISION_SKIP_BASE_ONLY,
    VERSION,
    GATE_ID,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path):
    """Create a temporary directory structure for tests."""
    return tmp_path


def _make_sot(tmp_dir, *, exploration_enabled=True, base_only=False,
              wf1_enabled=True, method="agent-team"):
    """Create a minimal workflow-registry.yaml for testing."""
    sot = {
        "workflows": {
            "wf1-general": {
                "enabled": wf1_enabled,
                "data_root": str(tmp_dir / "wf1-general"),
                "parameters": {
                    "base_only_flag": base_only,
                    "source_exploration": {
                        "enabled": exploration_enabled,
                        "exploration_method": method,
                        "max_candidates_per_scan": 5,
                        "coverage_gap_threshold": 0.15,
                    },
                },
            }
        }
    }
    sot_path = tmp_dir / "workflow-registry.yaml"
    try:
        import yaml
        with open(sot_path, "w") as f:
            yaml.dump(sot, f)
    except ImportError:
        # Fallback: write as JSON (gate_check uses yaml.safe_load)
        pytest.skip("PyYAML required for this test")
    return str(sot_path)


def _make_classified_signals(tmp_dir, signals=None):
    """Create a classified signals JSON file."""
    if signals is None:
        signals = [
            {"id": "sig-001", "category": "T_Technological"},
            {"id": "sig-002", "category": "T_Technological"},
            {"id": "sig-003", "category": "E_Economic"},
            {"id": "sig-004", "category": "P_Political"},
            {"id": "sig-005", "category": "E_Environmental"},
        ]
    data = {"classified_signals": signals}
    path = tmp_dir / "classified-signals.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


def _make_gate_decision(tmp_dir, decision=DECISION_MUST_RUN, date="2026-02-13"):
    """Create a gate decision JSON file."""
    data = {
        "gate_id": GATE_ID,
        "decision": decision,
        "date": date,
        "exploration_config": {
            "enabled": True,
            "method": "agent-team",
        },
    }
    path = tmp_dir / f"gate-decision-{date}.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


def _make_candidates(tmp_dir, date="2026-02-13", viable=2, non_viable=1):
    """Create a candidates JSON file."""
    viable_list = [{"name": f"Source{i}", "scan_status": "viable"} for i in range(viable)]
    non_viable_list = [{"name": f"BadSource{i}", "scan_status": "insufficient"} for i in range(non_viable)]
    data = {
        "total_candidates_discovered": viable + non_viable,
        "viable_candidates": viable_list,
        "non_viable_candidates": non_viable_list,
        "gap_analysis_result": {
            "pre_exploration_gaps": ["S_Social (12%)", "s_spiritual (8%)"],
        },
    }
    path = tmp_dir / f"exploration-candidates-{date}.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


def _make_signals(tmp_dir, date="2026-02-13", count=4):
    """Create an exploration signals JSON file."""
    signals = [
        {"id": f"explore-{date.replace('-', '')}-test-{i:03d}", "title": f"Signal {i}"}
        for i in range(1, count + 1)
    ]
    data = {"items": signals}
    path = tmp_dir / f"exploration-signals-{date}.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


def _make_frontier_selection(tmp_dir, date="2026-02-13"):
    """Create a frontier-selection file (written by frontier_selector.py)."""
    data = {
        "status": "SUCCESS",
        "selected_at": f"{date}T00:00:00+00:00",
        "keywords": ["AI governance", "quantum computing", "climate tech"],
        "date": date,
    }
    path = tmp_dir / f"frontier-selection-{date}.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


def _make_proof(tmp_dir, date="2026-02-13", *,
                gate_decision=DECISION_MUST_RUN,
                execution_status="executed",
                signals_collected=4,
                frontier_selection_path="auto"):
    """Create an exploration proof JSON file.

    frontier_selection_path:
        "auto" (default) — creates a real frontier-selection file and points to it
        None             — sets frontier_selection to null (simulates skipped Step 2.5)
        str path         — uses the given path directly (file must exist externally)
    """
    # Resolve frontier_selection
    if frontier_selection_path == "auto" and gate_decision == DECISION_MUST_RUN:
        fs_path = _make_frontier_selection(tmp_dir, date)
    elif frontier_selection_path == "auto":
        fs_path = None
    else:
        fs_path = frontier_selection_path

    data = {
        "gate_id": GATE_ID,
        "gate_version": VERSION,
        "command": "post",
        "date": date,
        "gate_decision": gate_decision,
        "execution_status": execution_status,
        "method_used": "single-agent" if gate_decision == DECISION_MUST_RUN else "n/a",
        "results": {
            "candidates_discovered": 3,
            "viable_count": 2,
            "signals_collected": signals_collected,
            "gaps_analyzed": [],
        },
        "files": {
            "decision": None,
            "candidates": None,
            "signals": None,
            "frontier_selection": fs_path,
        },
    }
    path = tmp_dir / f"exploration-proof-{date}.json"
    with open(path, "w") as f:
        json.dump(data, f)
    return str(path)


# ---------------------------------------------------------------------------
# Test: CHECK command
# ---------------------------------------------------------------------------

class TestGateCheck:
    """Tests for the check command."""

    def test_exploration_enabled_must_run(self, tmp_dir):
        """Exploration enabled + base_only=false → MUST_RUN."""
        sot_path = _make_sot(tmp_dir, exploration_enabled=True, base_only=False)
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        assert result["decision"] == DECISION_MUST_RUN
        assert result["date"] == "2026-02-13"
        assert result["gate_id"] == GATE_ID

    def test_exploration_disabled_skip(self, tmp_dir):
        """Exploration disabled → SKIP_DISABLED."""
        sot_path = _make_sot(tmp_dir, exploration_enabled=False)
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        assert result["decision"] == DECISION_SKIP_DISABLED

    def test_wf1_disabled_skip(self, tmp_dir):
        """WF1 disabled → SKIP_DISABLED."""
        sot_path = _make_sot(tmp_dir, wf1_enabled=False)
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        assert result["decision"] == DECISION_SKIP_DISABLED

    def test_base_only_skip(self, tmp_dir):
        """base_only_flag=true → SKIP_BASE_ONLY."""
        sot_path = _make_sot(tmp_dir, base_only=True)
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        assert result["decision"] == DECISION_SKIP_BASE_ONLY

    def test_gap_preview_generated(self, tmp_dir):
        """Gap analysis preview is generated when classified signals provided."""
        sot_path = _make_sot(tmp_dir)
        cls_path = _make_classified_signals(tmp_dir)
        result = gate_check(sot_path=sot_path, classified_path=cls_path, date="2026-02-13")
        assert result["decision"] == DECISION_MUST_RUN
        gap = result["gap_preview"]
        assert gap is not None
        assert "gaps" in gap
        assert gap["total_signals"] == 5
        # S_Social and s_spiritual have 0%, should be gaps
        assert "S_Social" in gap["gaps"]
        assert "s_spiritual" in gap["gaps"]

    def test_gap_preview_not_generated_when_skip(self, tmp_dir):
        """Gap preview is None when decision is SKIP."""
        sot_path = _make_sot(tmp_dir, exploration_enabled=False)
        cls_path = _make_classified_signals(tmp_dir)
        result = gate_check(sot_path=sot_path, classified_path=cls_path, date="2026-02-13")
        assert result["gap_preview"] is None

    def test_output_file_written(self, tmp_dir):
        """Output file is created when --output specified."""
        sot_path = _make_sot(tmp_dir)
        output = str(tmp_dir / "gate-decision.json")
        result = gate_check(sot_path=sot_path, date="2026-02-13", output_path=output)
        assert Path(output).exists()
        with open(output) as f:
            saved = json.load(f)
        assert saved["decision"] == DECISION_MUST_RUN

    def test_default_date_used(self, tmp_dir):
        """Date defaults to today when not specified."""
        sot_path = _make_sot(tmp_dir)
        result = gate_check(sot_path=sot_path)
        assert result["date"]  # Non-empty string

    def test_exploration_config_in_result(self, tmp_dir):
        """Result includes exploration config summary."""
        sot_path = _make_sot(tmp_dir, method="single-agent")
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        assert result["exploration_config"]["method"] == "single-agent"
        assert result["exploration_config"]["max_candidates"] == 5


# ---------------------------------------------------------------------------
# Test: POST command
# ---------------------------------------------------------------------------

class TestGatePost:
    """Tests for the post command."""

    def test_post_after_must_run(self, tmp_dir):
        """Post after MUST_RUN records executed status with results."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN)
        cand_path = _make_candidates(tmp_dir)
        sig_path = _make_signals(tmp_dir, count=4)
        data_root = str(tmp_dir / "wf1-general")
        os.makedirs(os.path.join(data_root, "exploration", "history"), exist_ok=True)
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            candidates_path=cand_path,
            signals_path=sig_path,
            method_used="single-agent",
            output_path=output,
        )

        assert result["gate_decision"] == DECISION_MUST_RUN
        assert result["execution_status"] == "executed"
        assert result["method_used"] == "single-agent"
        assert result["results"]["candidates_discovered"] == 3
        assert result["results"]["viable_count"] == 2
        assert result["results"]["signals_collected"] == 4
        assert Path(output).exists()

    def test_post_after_skip_disabled(self, tmp_dir):
        """Post after SKIP_DISABLED records skipped status."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_SKIP_DISABLED)
        data_root = str(tmp_dir / "wf1-general")
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            method_used="unknown",
            output_path=output,
        )

        assert result["gate_decision"] == DECISION_SKIP_DISABLED
        assert result["execution_status"] == "skipped"
        assert result["method_used"] == "n/a"
        assert result["results"]["signals_collected"] == 0

    def test_post_after_skip_base_only(self, tmp_dir):
        """Post after SKIP_BASE_ONLY records skipped status."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_SKIP_BASE_ONLY)
        data_root = str(tmp_dir / "wf1-general")
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            output_path=output,
        )

        assert result["execution_status"] == "skipped"
        assert result["method_used"] == "n/a"

    def test_history_updated_on_first_run(self, tmp_dir):
        """History file is created on first exploration run."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN)
        data_root = str(tmp_dir / "wf1-general")
        hist_dir = os.path.join(data_root, "exploration", "history")
        os.makedirs(hist_dir, exist_ok=True)
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            method_used="agent-team",
            output_path=output,
        )

        assert result.get("history_updated") is True
        hist_file = Path(hist_dir) / "exploration-history.json"
        assert hist_file.exists()
        with open(hist_file) as f:
            hist = json.load(f)
        assert len(hist["scans"]) == 1
        assert hist["scans"][0]["date"] == "2026-02-13"

    def test_history_duplicate_prevention(self, tmp_dir):
        """Second post for same date does not duplicate history entry."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN)
        data_root = str(tmp_dir / "wf1-general")
        hist_dir = os.path.join(data_root, "exploration", "history")
        os.makedirs(hist_dir, exist_ok=True)

        # Pre-populate history with same date
        hist_file = Path(hist_dir) / "exploration-history.json"
        existing_hist = {
            "version": "1.0.0",
            "scans": [{"date": "2026-02-13", "timestamp": "earlier"}],
            "approved": [], "discarded": [], "deferred": [], "learning": {},
        }
        with open(hist_file, "w") as f:
            json.dump(existing_hist, f)

        output = str(tmp_dir / "proof.json")
        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            method_used="single-agent",
            output_path=output,
        )

        assert result.get("history_updated") is False
        with open(hist_file) as f:
            hist = json.load(f)
        assert len(hist["scans"]) == 1  # Still just 1

    def test_missing_candidates_file_ok(self, tmp_dir):
        """Post succeeds even if candidates file doesn't exist."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN)
        data_root = str(tmp_dir / "wf1-general")
        os.makedirs(os.path.join(data_root, "exploration", "history"), exist_ok=True)
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            candidates_path="/nonexistent/candidates.json",
            method_used="single-agent",
            output_path=output,
        )

        assert result["execution_status"] == "executed"
        assert result["results"]["candidates_discovered"] == 0


# ---------------------------------------------------------------------------
# Test: VERIFY command
# ---------------------------------------------------------------------------

class TestGateVerify:
    """Tests for the verify command."""

    def test_valid_proof_passes(self, tmp_dir):
        """Valid proof file passes all VP checks (VP-1 through VP-5)."""
        proof_path = _make_proof(tmp_dir)  # frontier_selection_path="auto" creates real file
        decision_path = _make_gate_decision(tmp_dir)
        result = gate_verify(proof_path=proof_path, decision_path=decision_path)
        assert result["status"] == "PASS"
        assert result["all_passed"] is True
        assert len(result["checks"]) == 5

    def test_missing_proof_fails(self, tmp_dir):
        """Missing proof file fails VP-1."""
        result = gate_verify(proof_path=str(tmp_dir / "nonexistent.json"))
        assert result["status"] == "FAIL"
        assert not result["all_passed"]
        assert result["checks"][0]["id"] == "VP-1"
        assert not result["checks"][0]["passed"]

    def test_invalid_json_proof_fails(self, tmp_dir):
        """Invalid JSON in proof file fails VP-1."""
        bad_file = tmp_dir / "bad-proof.json"
        bad_file.write_text("not valid json {{{")
        result = gate_verify(proof_path=str(bad_file))
        assert result["status"] == "FAIL"

    def test_decision_mismatch_fails_vp2(self, tmp_dir):
        """Proof decision != decision file → VP-2 fails."""
        proof_path = _make_proof(tmp_dir, gate_decision=DECISION_MUST_RUN)
        # Make a decision file with SKIP_DISABLED
        decision_path = _make_gate_decision(tmp_dir, decision=DECISION_SKIP_DISABLED)
        result = gate_verify(proof_path=proof_path, decision_path=decision_path)
        vp2 = [c for c in result["checks"] if c["id"] == "VP-2"][0]
        assert not vp2["passed"]

    def test_must_run_but_skipped_fails_vp3(self, tmp_dir):
        """MUST_RUN with execution_status='skipped' → VP-3 fails."""
        proof_path = _make_proof(tmp_dir,
                                  gate_decision=DECISION_MUST_RUN,
                                  execution_status="skipped")
        result = gate_verify(proof_path=proof_path)
        vp3 = [c for c in result["checks"] if c["id"] == "VP-3"][0]
        assert not vp3["passed"]

    def test_skip_but_executed_fails_vp3(self, tmp_dir):
        """SKIP_DISABLED with execution_status='executed' → VP-3 fails."""
        proof_path = _make_proof(tmp_dir,
                                  gate_decision=DECISION_SKIP_DISABLED,
                                  execution_status="executed")
        result = gate_verify(proof_path=proof_path)
        vp3 = [c for c in result["checks"] if c["id"] == "VP-3"][0]
        assert not vp3["passed"]

    def test_executed_negative_signals_fails_vp4(self, tmp_dir):
        """Executed with signals_collected=-1 → VP-4 fails."""
        proof_path = _make_proof(tmp_dir, signals_collected=-1)
        result = gate_verify(proof_path=proof_path)
        vp4 = [c for c in result["checks"] if c["id"] == "VP-4"][0]
        assert not vp4["passed"]

    def test_skipped_proof_passes_all(self, tmp_dir):
        """Skipped exploration (SKIP_DISABLED) passes all checks."""
        proof_path = _make_proof(tmp_dir,
                                  gate_decision=DECISION_SKIP_DISABLED,
                                  execution_status="skipped")
        decision_path = _make_gate_decision(tmp_dir, decision=DECISION_SKIP_DISABLED)
        result = gate_verify(proof_path=proof_path, decision_path=decision_path)
        assert result["status"] == "PASS"
        assert result["all_passed"] is True

    def test_no_decision_file_skips_vp2(self, tmp_dir):
        """No decision file → VP-2 is auto-passed (skipped)."""
        proof_path = _make_proof(tmp_dir)
        result = gate_verify(proof_path=proof_path, decision_path=None)
        vp2 = [c for c in result["checks"] if c["id"] == "VP-2"][0]
        assert vp2["passed"] is True
        assert "skipped" in vp2.get("detail", "").lower()


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_classified_signals_error_handled(self, tmp_dir):
        """Malformed classified signals file produces error in gap_preview."""
        sot_path = _make_sot(tmp_dir)
        bad_cls = tmp_dir / "bad-classified.json"
        bad_cls.write_text("not json")
        result = gate_check(sot_path=sot_path, classified_path=str(bad_cls), date="2026-02-13")
        assert result["decision"] == DECISION_MUST_RUN
        assert "error" in result["gap_preview"]

    def test_empty_classified_signals(self, tmp_dir):
        """Empty classified signals → all categories are gaps."""
        sot_path = _make_sot(tmp_dir)
        cls_path = _make_classified_signals(tmp_dir, signals=[])
        result = gate_check(sot_path=sot_path, classified_path=cls_path, date="2026-02-13")
        gap = result["gap_preview"]
        assert gap["total_signals"] == 0
        assert len(gap["gaps"]) == 6  # All 6 STEEPs are gaps

    def test_proof_file_atomic_write(self, tmp_dir):
        """Proof file is written atomically (no partial writes)."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_SKIP_DISABLED)
        data_root = str(tmp_dir / "wf1-general")
        output = str(tmp_dir / "proof.json")

        gate_post(
            decision_path=decision_path,
            data_root=data_root,
            output_path=output,
        )

        # Verify the file is valid JSON
        with open(output) as f:
            data = json.load(f)
        assert data["gate_id"] == GATE_ID

        # No .tmp file should remain
        assert not Path(output + ".tmp").exists()
        assert not Path(output).with_suffix(".tmp").exists()

    def test_check_result_has_all_required_fields(self, tmp_dir):
        """Check result contains all required fields for downstream use."""
        sot_path = _make_sot(tmp_dir)
        result = gate_check(sot_path=sot_path, date="2026-02-13")
        required = ["gate_id", "gate_version", "command", "checked_at",
                     "date", "decision", "reason", "exploration_config",
                     "base_only_flag"]
        for field in required:
            assert field in result, f"Missing field: {field}"

    def test_post_result_has_all_required_fields(self, tmp_dir):
        """Post result contains all required fields for proof verification."""
        decision_path = _make_gate_decision(tmp_dir, DECISION_SKIP_DISABLED)
        data_root = str(tmp_dir / "wf1-general")
        output = str(tmp_dir / "proof.json")

        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            output_path=output,
        )
        required = ["gate_id", "gate_version", "command", "recorded_at",
                     "date", "gate_decision", "execution_status", "method_used",
                     "results", "files"]
        for field in required:
            assert field in result, f"Missing field: {field}"
        # VP-5: files dict must include frontier_selection key
        assert "frontier_selection" in result["files"], "files.frontier_selection missing"


# ---------------------------------------------------------------------------
# Test: VP-5 — Frontier Selection Enforcement
# ---------------------------------------------------------------------------

class TestVP5FrontierSelection:
    """
    Tests for VP-5: Python-enforced proof that frontier_selector.py ran.

    Design rationale: Removing the 'no_gaps → early return' LLM instruction
    is necessary but not sufficient. VP-5 makes the 'always run' policy
    machine-verifiable — a missing frontier-selection file at PG1 = HALT.
    """

    def test_must_run_with_frontier_file_passes_vp5(self, tmp_dir):
        """MUST_RUN + executed + frontier-selection file exists → VP-5 PASS."""
        proof_path = _make_proof(tmp_dir)  # "auto" creates frontier-selection file
        result = gate_verify(proof_path=proof_path)
        vp5 = [c for c in result["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is True
        assert result["status"] == "PASS"

    def test_must_run_frontier_selection_null_fails_vp5(self, tmp_dir):
        """MUST_RUN + executed + frontier_selection=null in proof → VP-5 FAIL."""
        proof_path = _make_proof(tmp_dir, frontier_selection_path=None)
        result = gate_verify(proof_path=proof_path)
        vp5 = [c for c in result["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is False
        assert "frontier_selection not recorded" in vp5["detail"]
        assert result["status"] == "FAIL"

    def test_must_run_frontier_file_not_on_disk_fails_vp5(self, tmp_dir):
        """MUST_RUN + executed + frontier_selection path recorded but file deleted → VP-5 FAIL."""
        proof_path = _make_proof(tmp_dir, frontier_selection_path="/nonexistent/frontier.json")
        result = gate_verify(proof_path=proof_path)
        vp5 = [c for c in result["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is False
        assert "not found on disk" in vp5["detail"]

    def test_skip_disabled_auto_passes_vp5(self, tmp_dir):
        """SKIP_DISABLED → VP-5 auto-passes (no frontier selection expected)."""
        proof_path = _make_proof(tmp_dir,
                                  gate_decision=DECISION_SKIP_DISABLED,
                                  execution_status="skipped",
                                  frontier_selection_path=None)
        decision_path = _make_gate_decision(tmp_dir, decision=DECISION_SKIP_DISABLED)
        result = gate_verify(proof_path=proof_path, decision_path=decision_path)
        vp5 = [c for c in result["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is True
        assert result["status"] == "PASS"

    def test_skip_base_only_auto_passes_vp5(self, tmp_dir):
        """SKIP_BASE_ONLY → VP-5 auto-passes."""
        proof_path = _make_proof(tmp_dir,
                                  gate_decision=DECISION_SKIP_BASE_ONLY,
                                  execution_status="skipped",
                                  frontier_selection_path=None)
        result = gate_verify(proof_path=proof_path)
        vp5 = [c for c in result["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is True

    def test_post_records_frontier_selection_when_file_exists(self, tmp_dir):
        """gate_post records frontier_selection in proof when file is present."""
        date = "2026-02-13"
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN, date=date)
        data_root = str(tmp_dir / "wf1-general")
        # Create exploration dir and frontier-selection file
        exp_dir = Path(data_root) / "exploration"
        exp_dir.mkdir(parents=True, exist_ok=True)
        (Path(data_root) / "exploration" / "history").mkdir(exist_ok=True)
        fs_file = exp_dir / f"frontier-selection-{date}.json"
        fs_file.write_text(json.dumps({"status": "SUCCESS", "keywords": ["AI"]}))

        output = str(tmp_dir / "proof.json")
        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            method_used="agent-team",
            output_path=output,
        )

        assert result["files"]["frontier_selection"] == str(fs_file)
        # Verify VP-5 passes in the generated proof
        verify = gate_verify(proof_path=output)
        vp5 = [c for c in verify["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is True

    def test_post_records_null_when_frontier_file_absent(self, tmp_dir):
        """gate_post records frontier_selection=null when file was not created."""
        date = "2026-02-13"
        decision_path = _make_gate_decision(tmp_dir, DECISION_MUST_RUN, date=date)
        data_root = str(tmp_dir / "wf1-general")
        (Path(data_root) / "exploration" / "history").mkdir(parents=True, exist_ok=True)
        # Deliberately do NOT create frontier-selection file

        output = str(tmp_dir / "proof.json")
        result = gate_post(
            decision_path=decision_path,
            data_root=data_root,
            method_used="agent-team",
            output_path=output,
        )

        assert result["files"]["frontier_selection"] is None
        # VP-5 must fail for this proof
        verify = gate_verify(proof_path=output)
        vp5 = [c for c in verify["checks"] if c["id"] == "VP-5"][0]
        assert vp5["passed"] is False

    def test_all_5_vp_checks_present(self, tmp_dir):
        """Verify result always contains exactly 5 VP checks."""
        proof_path = _make_proof(tmp_dir)
        result = gate_verify(proof_path=proof_path)
        ids = [c["id"] for c in result["checks"]]
        assert ids == ["VP-1", "VP-2", "VP-3", "VP-4", "VP-5"]
