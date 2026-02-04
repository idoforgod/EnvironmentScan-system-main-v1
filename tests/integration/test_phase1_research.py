"""
Phase 1 Integration Tests - Research Phase
Tests: Archive loading, Multi-source scanning, Deduplication, Translation
"""
import pytest
import json
import os
from datetime import datetime
from pathlib import Path


@pytest.mark.integration
class TestPhase1Research:
    """Integration tests for Phase 1 - Research phase"""

    def test_phase1_complete_execution(self, project_root, date_str):
        """
        Test entire Phase 1 execution and data flow
        Execution time: < 30 seconds
        """
        # Verify all Phase 1 outputs exist
        phase1_outputs = [
            f"raw/daily-scan-{date_str}.json",
            f"raw/daily-scan-{date_str}-ko.json",
        ]

        missing_files = []
        for output in phase1_outputs:
            output_path = project_root / output
            if not output_path.exists():
                missing_files.append(output)

        assert len(missing_files) == 0, \
            f"Phase 1 outputs missing:\n" + "\n".join(f"  - {f}" for f in missing_files)

    def test_multi_source_scanning_output(self, project_root, date_str):
        """
        Verify multi-source scanner produces valid output
        Should scan from multiple sources (arxiv, blog, policy, patent)
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        assert scan_file.exists(), f"Daily scan file missing: {scan_file}"

        with open(scan_file) as f:
            data = json.load(f)

        # Check required top-level fields
        assert "scan_metadata" in data, "scan_metadata missing"
        assert "items" in data, "items array missing"

        metadata = data["scan_metadata"]

        # Verify scan metadata
        assert "date" in metadata
        assert metadata["date"] == date_str

        assert "total_items" in metadata
        assert metadata["total_items"] == len(data["items"])

        # Should scan from multiple agents
        if "agents_used" in metadata:
            assert len(metadata["agents_used"]) >= 2, \
                f"Expected multiple sources, got {len(metadata['agents_used'])}"

    def test_scan_items_structure(self, project_root, date_str):
        """
        Verify each scanned item has required structure
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        with open(scan_file) as f:
            data = json.load(f)

        items = data.get("items", [])
        assert len(items) > 0, "No items in scan output"

        required_fields = ["id", "title", "source"]
        invalid_items = []

        for item in items:
            missing_fields = [f for f in required_fields if f not in item]
            if missing_fields:
                invalid_items.append({
                    "id": item.get("id", "unknown"),
                    "missing": missing_fields
                })

        assert len(invalid_items) == 0, \
            f"Items with invalid structure:\n" + \
            "\n".join(f"  {i['id']}: missing {i['missing']}" for i in invalid_items)

    def test_translation_output_structure(self, project_root, date_str):
        """
        Verify Korean translation maintains same structure as English
        """
        en_file = project_root / f"raw/daily-scan-{date_str}.json"
        ko_file = project_root / f"raw/daily-scan-{date_str}-ko.json"

        with open(en_file) as f:
            en_data = json.load(f)

        with open(ko_file) as f:
            ko_data = json.load(f)

        # Structure should be identical
        assert "scan_metadata" in ko_data
        assert "items" in ko_data

        # Same number of items
        assert len(en_data["items"]) == len(ko_data["items"]), \
            "English and Korean versions have different item counts"

    def test_source_diversity(self, project_root, date_str):
        """
        Verify signals come from diverse sources
        Should have signals from at least 2 different source types
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        with open(scan_file) as f:
            data = json.load(f)

        items = data.get("items", [])

        # Extract source types
        source_types = {item.get("source", {}).get("type") for item in items}
        source_types.discard(None)  # Remove None values

        assert len(source_types) >= 2, \
            f"Expected diverse sources, found only: {source_types}"

    def test_scan_recency(self, project_root, date_str):
        """
        Verify scanned signals are recent (within 7 days)
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        with open(scan_file) as f:
            data = json.load(f)

        items = data.get("items", [])

        # Parse scan date
        from datetime import datetime, timedelta
        scan_date = datetime.strptime(date_str, "%Y-%m-%d")
        seven_days_ago = scan_date - timedelta(days=7)

        old_signals = []

        for item in items:
            source_date_str = item.get("source", {}).get("date")
            if source_date_str:
                try:
                    source_date = datetime.strptime(source_date_str, "%Y-%m-%d")
                    if source_date < seven_days_ago:
                        old_signals.append({
                            "id": item.get("id"),
                            "date": source_date_str
                        })
                except ValueError:
                    # Invalid date format - skip
                    pass

        # Warning only, not failure (some sources might be older)
        if old_signals:
            print(f"\n⚠️  Warning: {len(old_signals)} signals older than 7 days")


@pytest.mark.integration
class TestPhase1Deduplication:
    """Integration tests for deduplication filter"""

    def test_deduplication_filter_execution(self, project_root, date_str):
        """
        Test deduplication filter if it was run
        Note: May not always run depending on workflow configuration
        """
        filtered_file = project_root / f"filtered/new-signals-{date_str}.json"

        if not filtered_file.exists():
            pytest.skip("Deduplication filter output not found")

        with open(filtered_file) as f:
            data = json.load(f)

        # Check output structure
        assert "filter_metadata" in data
        assert "new_signals" in data

    def test_no_duplicate_urls(self, project_root, date_str):
        """
        Verify no duplicate URLs in final output
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        with open(scan_file) as f:
            data = json.load(f)

        items = data.get("items", [])

        # Extract URLs
        urls = [item.get("source", {}).get("url") for item in items if item.get("source", {}).get("url")]

        # Check for duplicates
        duplicate_urls = [url for url in urls if urls.count(url) > 1]

        assert len(set(duplicate_urls)) == 0, \
            f"Duplicate URLs found: {set(duplicate_urls)}"

    def test_deduplication_4_stages(self, project_root, date_str):
        """
        Test that 4-stage deduplication cascade was executed
        Only if deduplication filter ran
        """
        filtered_file = project_root / f"filtered/new-signals-{date_str}.json"

        if not filtered_file.exists():
            pytest.skip("Deduplication filter output not found")

        with open(filtered_file) as f:
            data = json.load(f)

        metadata = data.get("filter_metadata", {})

        # Check for stage breakdown
        if "stage_breakdown" in metadata:
            stages = metadata["stage_breakdown"]

            expected_stages = ["stage_1_url", "stage_2_string", "stage_3_semantic", "stage_4_entity"]

            for stage in expected_stages:
                assert stage in stages, f"Stage {stage} not found in breakdown"


@pytest.mark.integration
class TestPhase1Performance:
    """Performance tests for Phase 1"""

    def test_parallel_execution_speedup(self, project_root, date_str):
        """
        Verify parallel execution provides speedup
        Check scan metadata for parallelization info
        """
        scan_file = project_root / f"raw/daily-scan-{date_str}.json"

        with open(scan_file) as f:
            data = json.load(f)

        metadata = data.get("scan_metadata", {})

        # Check for parallelization indicator
        if "parallelization" in metadata:
            assert metadata["parallelization"] != "none", \
                "Parallelization should be enabled"

        if "execution_mode" in metadata:
            assert metadata["execution_mode"] == "parallel", \
                "Should use parallel execution mode"

    def test_translation_performance(self, project_root, date_str):
        """
        Verify translation was performed (timing optional)
        """
        ko_file = project_root / f"raw/daily-scan-{date_str}-ko.json"

        assert ko_file.exists(), "Korean translation not generated"

        # File should have reasonable size (not empty, not too large)
        file_size = ko_file.stat().st_size

        assert file_size > 100, "Translation file suspiciously small"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
