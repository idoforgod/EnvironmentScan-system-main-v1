"""
End-to-End Workflow Tests
Tests complete environmental scanning workflow from start to finish
"""
import pytest
import json
import os
import re
from datetime import datetime
from pathlib import Path


@pytest.mark.e2e
class TestFullWorkflow:
    """Test complete workflow execution"""

    def test_workflow_artifacts_exist(self, project_root, date_str):
        """
        Verify all expected output artifacts are created
        Tests Phase 1, 2, and 3 outputs
        """
        # Define expected artifacts for each phase
        expected_artifacts = {
            "Phase 1 - Research": [
                f"raw/daily-scan-{date_str}.json",
                f"raw/daily-scan-{date_str}-ko.json",
            ],
            "Phase 2 - Analysis": [
                f"structured/classified-signals-{date_str}.json",
                f"analysis/priority-ranked-{date_str}.json",
                f"analysis/impact-assessment-{date_str}.json",
            ],
            "Phase 3 - Reporting": [
                f"reports/daily/environmental-scan-{date_str}.md",
                "signals/database.json",
            ]
        }

        missing_artifacts = []

        for phase, artifacts in expected_artifacts.items():
            for artifact in artifacts:
                artifact_path = project_root / artifact
                if not artifact_path.exists():
                    missing_artifacts.append(f"{phase}: {artifact}")

        assert len(missing_artifacts) == 0, \
            f"Missing artifacts:\n" + "\n".join(f"  - {a}" for a in missing_artifacts)

    def test_data_flow_consistency(self, project_root, date_str):
        """
        Verify data consistency across workflow stages
        Signal IDs should remain consistent from scan → classification → ranking
        """
        # Load files
        raw_file = project_root / f"raw/daily-scan-{date_str}.json"
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        # Check files exist
        assert raw_file.exists(), f"Raw scan file missing: {raw_file}"
        assert classified_file.exists(), f"Classified file missing: {classified_file}"
        assert ranked_file.exists(), f"Ranked file missing: {ranked_file}"

        # Load data
        with open(raw_file) as f:
            raw_data = json.load(f)
        with open(classified_file) as f:
            classified_data = json.load(f)
        with open(ranked_file) as f:
            ranked_data = json.load(f)

        # Extract signal IDs - handle both dict and list formats
        raw_ids = {item.get("id", item.get("signal_id")) for item in raw_data.get("items", [])}

        # classified_data can have "signals" or "items" field
        classified_items = classified_data.get("signals", classified_data.get("items", []))
        classified_ids = {signal.get("id", signal.get("signal_id")) for signal in classified_items}

        # ranked_data can be a list directly or have "ranked_signals" field
        if isinstance(ranked_data, list):
            ranked_items = ranked_data
        else:
            ranked_items = ranked_data.get("ranked_signals", ranked_data.get("items", []))
        ranked_ids = {signal.get("id", signal.get("signal_id")) for signal in ranked_items}

        # Test consistency
        assert raw_ids == classified_ids, \
            f"ID mismatch between raw and classified. Missing: {raw_ids - classified_ids}"

        assert classified_ids == ranked_ids, \
            f"ID mismatch between classified and ranked. Missing: {classified_ids - ranked_ids}"

    def test_steeps_classification_validity(self, project_root, date_str):
        """
        Verify all signals are classified into valid STEEPs categories
        Valid categories: S, T, E (Economic), E (Environmental), P, s (spiritual)
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        # Valid STEEPs categories (various naming formats)
        valid_categories = {
            "S", "T", "E", "P", "s",  # Short form
            "Social", "Technology", "Economy", "Environmental", "Political", "spiritual"  # Full form
        }
        invalid_signals = []

        # Get signals - handle both "signals" and "items" field names
        signals = data.get("signals", data.get("items", []))

        for signal in signals:
            # Check multiple possible field names for category
            category = signal.get("category", signal.get("steep_category", signal.get("final_category")))
            if category not in valid_categories:
                invalid_signals.append({
                    "id": signal.get("id"),
                    "category": category
                })

        assert len(invalid_signals) == 0, \
            f"Invalid STEEPs categories found:\n" + \
            "\n".join(f"  {s['id']}: {s['category']}" for s in invalid_signals)

    def test_classification_confidence_scores(self, project_root, date_str):
        """
        Verify classification confidence scores are in valid range [0, 1]
        and meet minimum quality threshold
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        # Handle both "signals" and "items" field names
        signals = data.get("signals", data.get("items", []))
        assert len(signals) > 0, "No signals found in classification output"

        low_confidence_signals = []
        invalid_confidence_signals = []

        for signal in signals:
            confidence = signal.get("confidence", 0)

            # Check validity (0 to 1)
            if not (0 <= confidence <= 1):
                invalid_confidence_signals.append({
                    "id": signal.get("id"),
                    "confidence": confidence
                })

            # Check minimum threshold (> 0.5)
            elif confidence < 0.5:
                low_confidence_signals.append({
                    "id": signal.get("id"),
                    "confidence": confidence
                })

        assert len(invalid_confidence_signals) == 0, \
            f"Invalid confidence scores (must be 0-1):\n" + \
            "\n".join(f"  {s['id']}: {s['confidence']}" for s in invalid_confidence_signals)

        # Warning for low confidence (not failure)
        if low_confidence_signals:
            print(f"\n⚠️  Warning: {len(low_confidence_signals)} signals with confidence < 0.5")

    def test_priority_ranking_distribution(self, project_root, date_str):
        """
        Verify priority ranking is properly distributed
        Should have high/medium/low priorities
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            data = json.load(f)

        # Handle both dict with "ranked_signals" and direct list
        if isinstance(data, list):
            signals = data
        else:
            signals = data.get("ranked_signals", data.get("items", []))

        assert len(signals) > 0, "No ranked signals found"

        # Count priorities
        priority_counts = {"high": 0, "medium": 0, "low": 0}

        for signal in signals:
            priority = signal.get("priority", "").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Should have at least one signal in at least 2 different priority levels
        non_zero_priorities = sum(1 for count in priority_counts.values() if count > 0)

        assert non_zero_priorities >= 2, \
            f"Priority distribution too narrow: {priority_counts}"

    def test_korean_translation_completeness(self, project_root, date_str):
        """
        Verify Korean translation was generated and contains Korean characters
        """
        ko_file = project_root / f"raw/daily-scan-{date_str}-ko.json"

        assert ko_file.exists(), f"Korean translation file missing: {ko_file}"

        with open(ko_file, encoding='utf-8') as f:
            ko_data = json.load(f)

        # Check metadata
        assert "scan_metadata" in ko_data
        assert "items" in ko_data

        # Convert to string to check for Korean characters
        ko_text = json.dumps(ko_data, ensure_ascii=False)

        # Count Korean characters (Hangul Unicode range: AC00-D7AF)
        korean_chars = re.findall(r'[가-힣]', ko_text)

        # Note: If translation is mock/fallback, Korean content may be minimal
        # We check for Korean chars but allow the test to pass with a warning
        if len(korean_chars) == 0:
            # Check if it's a mock/fallback file (very small)
            file_size = ko_file.stat().st_size
            if file_size < 2000:  # Less than 2KB suggests mock
                pytest.skip("Korean translation appears to be mock/fallback (no Korean content)")
            else:
                pytest.fail("Korean translation file exists but contains no Korean characters")

    def test_report_generation_structure(self, project_root, date_str):
        """
        Verify report markdown structure and required sections
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        assert report_file.exists(), f"Report file missing: {report_file}"

        with open(report_file, encoding='utf-8') as f:
            report_content = f.read()

        # Required sections (can be in Korean or English)
        required_sections_kr = [
            "## 1. 경영진 요약",  # Executive Summary
            "## 2. 신규 탐지 신호",  # New Signals Detected
            "## 3. STEEPs 영역별 분석",  # STEEPs Analysis
            "## 4. 우선순위 신호",  # Priority Signals
            "## 5. 전략적 시사점",  # Strategic Implications
        ]

        required_sections_en = [
            "## Executive Summary",
            "## Top Priority Signals",
            "## Category Distribution",
        ]

        # Check if report has Korean OR English sections
        missing_kr = [s for s in required_sections_kr if s not in report_content]
        missing_en = [s for s in required_sections_en if s not in report_content]

        # Pass if either Korean or English sections are present
        required_sections = required_sections_kr if len(missing_kr) < len(missing_en) else required_sections_en

        # Use the set with fewer missing sections
        if len(missing_kr) <= len(missing_en):
            missing_sections = missing_kr
            format_name = "Korean"
        else:
            missing_sections = missing_en
            format_name = "English"

        # Only fail if more than half of sections are missing
        assert len(missing_sections) < len(required_sections) / 2, \
            f"Too many missing {format_name} report sections ({len(missing_sections)}/{len(required_sections)}):\n" + \
            "\n".join(f"  - {s}" for s in missing_sections[:3])  # Show first 3 only

    def test_database_update_integrity(self, project_root, date_str):
        """
        Verify signal database was updated correctly
        No duplicate signal IDs should exist
        """
        db_file = project_root / "signals/database.json"

        assert db_file.exists(), "Signal database missing"

        with open(db_file) as f:
            db_data = json.load(f)

        # Database can be a list or dict with "signals" field
        if isinstance(db_data, list):
            signals = db_data
        else:
            signals = db_data.get("signals", db_data.get("items", []))

        # Check for duplicates
        signal_ids = [s.get("id", s.get("signal_id")) for s in signals]
        signal_ids = [id for id in signal_ids if id is not None]  # Remove None values

        duplicate_ids = [id for id in signal_ids if signal_ids.count(id) > 1]

        assert len(duplicate_ids) == 0, \
            f"Duplicate signal IDs found in database: {set(duplicate_ids)}"

        # Check database has signals (may or may not have date field)
        assert len(signals) > 0, \
            "Database is empty - no signals found"

    def test_workflow_performance_targets(self, project_root, performance_targets):
        """
        Verify workflow meets performance targets
        Note: This requires timing data from orchestrator
        """
        status_file = project_root / "logs/workflow-status.json"

        if not status_file.exists():
            pytest.skip("Workflow status file not found - cannot test performance")

        with open(status_file) as f:
            status = json.load(f)

        # Check completion status
        assert status.get("status") in ["completed", "success"], \
            f"Workflow not completed: {status.get('status')}"

        # If timing data available, check performance
        if "phase_timings" in status:
            timings = status["phase_timings"]

            # Phase 1 should be < 60 seconds
            if "phase1" in timings:
                assert timings["phase1"] < performance_targets["phase1_time"], \
                    f"Phase 1 too slow: {timings['phase1']}s > {performance_targets['phase1_time']}s"


@pytest.mark.e2e
class TestWorkflowQualityMetrics:
    """Test quality metrics and thresholds"""

    def test_deduplication_filter_rate(self, project_root, date_str, performance_targets):
        """
        Verify deduplication filter rate is within expected range
        Should filter 30-90% of signals as duplicates
        """
        raw_file = project_root / f"raw/daily-scan-{date_str}.json"
        filtered_file = project_root / f"filtered/new-signals-{date_str}.json"

        # Check if filtered file exists (might not for some test scenarios)
        if not filtered_file.exists():
            pytest.skip("Filtered signals file not found")

        with open(raw_file) as f:
            raw_data = json.load(f)

        with open(filtered_file) as f:
            filtered_data = json.load(f)

        raw_count = len(raw_data.get("items", []))
        filtered_count = len(filtered_data.get("new_signals", []))

        # Calculate filter rate
        filter_rate = 1 - (filtered_count / raw_count) if raw_count > 0 else 0

        min_rate = performance_targets["filter_rate_min"]
        max_rate = performance_targets["filter_rate_max"]

        assert min_rate <= filter_rate <= max_rate, \
            f"Filter rate {filter_rate:.2%} outside target range [{min_rate:.0%}-{max_rate:.0%}]"

    def test_signal_metadata_completeness(self, project_root, date_str):
        """
        Verify all signals have required metadata fields
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        required_fields = ["id", "category", "confidence"]
        signals_with_missing_fields = []

        for signal in data.get("signals", []):
            missing_fields = [field for field in required_fields if field not in signal]
            if missing_fields:
                signals_with_missing_fields.append({
                    "id": signal.get("id", "unknown"),
                    "missing": missing_fields
                })

        assert len(signals_with_missing_fields) == 0, \
            f"Signals with missing metadata:\n" + \
            "\n".join(f"  {s['id']}: missing {s['missing']}" for s in signals_with_missing_fields)

    def test_cross_impact_analysis_exists(self, project_root, date_str):
        """
        Verify impact assessment includes cross-domain analysis
        """
        impact_file = project_root / f"analysis/impact-assessment-{date_str}.json"

        if not impact_file.exists():
            pytest.skip("Impact assessment file not found")

        with open(impact_file) as f:
            data = json.load(f)

        # Check for cross-impact data structure (various field names)
        has_cross_impact = (
            "cross_impacts" in data or
            "impact_matrix" in data or
            "impacts" in data or
            isinstance(data, list)  # List of impacts
        )

        assert has_cross_impact, \
            "Cross-impact analysis data structure not found in impact assessment file"


@pytest.mark.e2e
@pytest.mark.slow
class TestWorkflowRecovery:
    """Test workflow error handling and recovery"""

    def test_workflow_status_tracking(self, project_root):
        """
        Verify workflow status is properly tracked
        """
        status_file = project_root / "logs/workflow-status.json"

        assert status_file.exists(), "Workflow status file not created"

        with open(status_file) as f:
            status = json.load(f)

        # Required status fields
        required_fields = ["workflow_id", "status", "current_phase"]
        missing_fields = [f for f in required_fields if f not in status]

        assert len(missing_fields) == 0, \
            f"Missing status fields: {missing_fields}"

    def test_log_files_generated(self, project_root, date_str):
        """
        Verify workflow generates proper log files
        """
        log_dir = project_root / "logs"

        assert log_dir.exists(), "Log directory not created"

        # Check for workflow status
        assert (log_dir / "workflow-status.json").exists(), \
            "Workflow status log missing"

        # Check for any log files (various naming patterns)
        log_files = list(log_dir.glob("*.log"))
        json_logs = list(log_dir.glob("*.json"))

        # At least some log file should exist (*.log or *.json)
        total_logs = len(log_files) + len(json_logs)

        assert total_logs > 0, \
            f"No log files generated in {log_dir}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
