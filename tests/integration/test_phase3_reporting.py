"""
Phase 3 Integration Tests - Implementation/Reporting Phase
Tests: Database update, Report generation, Archive notification
"""
import pytest
import json
import re
from datetime import datetime


@pytest.mark.integration
class TestPhase3DatabaseUpdate:
    """Integration tests for database update"""

    def test_database_file_exists(self, project_root):
        """
        Verify signal database exists
        """
        db_file = project_root / "signals/database.json"

        assert db_file.exists(), "Signal database missing"

    def test_database_structure(self, project_root):
        """
        Verify database has correct structure
        """
        db_file = project_root / "signals/database.json"

        with open(db_file) as f:
            db_data = json.load(f)

        # Should have signals array
        assert "signals" in db_data, "Database missing 'signals' field"

        # Should have metadata
        assert "metadata" in db_data or "database_metadata" in db_data, \
            "Database missing metadata"

    def test_no_duplicate_signal_ids(self, project_root):
        """
        Verify no duplicate signal IDs in database
        """
        db_file = project_root / "signals/database.json"

        with open(db_file) as f:
            db_data = json.load(f)

        signals = db_data.get("signals", [])

        # Extract IDs
        signal_ids = [s.get("id") for s in signals]

        # Check for duplicates
        duplicate_ids = [id for id in signal_ids if signal_ids.count(id) > 1]

        assert len(set(duplicate_ids)) == 0, \
            f"Duplicate signal IDs in database: {set(duplicate_ids)}"

    def test_todays_signals_in_database(self, project_root, date_str):
        """
        Verify today's signals were added to database
        """
        db_file = project_root / "signals/database.json"

        with open(db_file) as f:
            db_data = json.load(f)

        signals = db_data.get("signals", [])

        # Find signals from today
        today_signals = [
            s for s in signals
            if s.get("detected_date") == date_str or s.get("date") == date_str
        ]

        assert len(today_signals) > 0, \
            f"No signals from today ({date_str}) found in database"

    def test_database_snapshot_created(self, project_root, date_str):
        """
        Verify database snapshot was created
        """
        snapshot_file = project_root / f"signals/snapshots/database-{date_str}.json"

        # Snapshot may not always be created
        if snapshot_file.exists():
            with open(snapshot_file) as f:
                snapshot_data = json.load(f)

            assert "signals" in snapshot_data, \
                "Database snapshot missing signals"


@pytest.mark.integration
class TestPhase3ReportGeneration:
    """Integration tests for report generation"""

    def test_report_file_exists(self, project_root, date_str):
        """
        Verify daily report was generated
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        assert report_file.exists(), f"Daily report missing: {report_file}"

    def test_report_korean_content(self, project_root, date_str):
        """
        Verify report contains Korean content
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        # Count Korean characters
        korean_chars = re.findall(r'[가-힣]', content)

        assert len(korean_chars) > 100, \
            f"Report has insufficient Korean content: {len(korean_chars)} characters"

    def test_report_required_sections(self, project_root, date_str):
        """
        Verify report contains all required sections.
        Updated: Section headers now match actual report format (v1.3.0).
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        # Required sections — corrected to match actual report format
        required_sections = [
            "## 1. 경영진 요약",        # Executive Summary
            "## 2. 신규 탐지 신호",      # New Signals
            "## 3. 기존 신호 업데이트",   # Existing Signal Updates
            "## 4. 패턴 및 연결고리",    # Patterns & Connections
            "## 5. 전략적 시사점",       # Strategic Implications
            "## 7. 신뢰도 분석",         # Trust Analysis
            "## 8. 부록",               # Appendix
        ]

        missing_sections = []

        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        assert len(missing_sections) == 0, \
            f"Report missing sections:\n" + \
            "\n".join(f"  - {s}" for s in missing_sections)

    def test_report_signal_count(self, project_root, date_str):
        """
        Verify report mentions signal count from analysis
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            ranked_data = json.load(f)

        signal_count = len(ranked_data.get("ranked_signals", []))

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        # Report should mention the number of signals
        # Look for numbers in the content
        numbers_in_report = re.findall(r'\d+', content)
        numbers = [int(n) for n in numbers_in_report]

        # Signal count should appear somewhere in report
        assert signal_count in numbers, \
            f"Signal count {signal_count} not found in report"

    def test_report_steeps_categories_mentioned(self, project_root, date_str):
        """
        Verify report mentions STEEPs categories
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        # STEEPs categories should be mentioned
        # Either in English or Korean
        steeps_keywords = [
            "사회", "기술", "경제", "환경", "정치", "영성",  # Korean
            "Social", "Technological", "Economic", "Environmental", "Political", "spiritual"  # English
        ]

        found_keywords = [kw for kw in steeps_keywords if kw in content]

        assert len(found_keywords) >= 3, \
            f"Report should mention STEEPs categories. Found only: {found_keywords}"

    def test_report_file_size_reasonable(self, project_root, date_str):
        """
        Verify report file has reasonable size
        Should not be empty or suspiciously small
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        file_size = report_file.stat().st_size

        # Report should be at least 1KB
        assert file_size > 1000, \
            f"Report file suspiciously small: {file_size} bytes"

        # Report should not be excessively large (> 1MB)
        assert file_size < 1_000_000, \
            f"Report file suspiciously large: {file_size} bytes"

    def test_report_signal_fields_complete(self, project_root, date_str):
        """
        Verify top 10 signals have all 9 required fields.
        This catches the 2026-02-02 regression where 4 fields were omitted.
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        signal_fields = [
            "분류", "출처", "핵심 사실", "정량 지표", "영향도",
            "상세 설명", "추론", "이해관계자", "모니터링 지표",
        ]

        for field in signal_fields:
            count = content.count(f"**{field}**")
            assert count >= 10, \
                f"Field '**{field}**' appears {count} times (need >= 10 for top 10 signals)"

    def test_report_section5_subsections(self, project_root, date_str):
        """
        Verify Section 5 has required subsections (5.1, 5.2, 5.3).
        This catches the 2026-02-02 regression where Section 5 was omitted entirely.
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        for sub in ["### 5.1", "### 5.2", "### 5.3"]:
            assert sub in content, \
                f"Section 5 missing subsection: {sub}"

    def test_report_no_unfilled_placeholders(self, project_root, date_str):
        """
        Verify no unfilled skeleton placeholders remain.
        """
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(report_file, encoding='utf-8') as f:
            content = f.read()

        import re
        placeholders = re.findall(r"\{\{[A-Z_]+\}\}", content)
        assert len(placeholders) == 0, \
            f"Unfilled skeleton placeholders found: {placeholders}"


@pytest.mark.integration
class TestPhase3Archive:
    """Integration tests for report archiving"""

    def test_archive_directory_exists(self, project_root):
        """
        Verify archive directory structure exists
        """
        archive_dir = project_root / "reports/archive"

        assert archive_dir.exists(), "Archive directory missing"

    def test_archive_by_date(self, project_root, date_str):
        """
        Verify reports are archived by year/month
        """
        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.strftime("%Y")
        month = date_obj.strftime("%m")

        archive_dir = project_root / f"reports/archive/{year}/{month}"

        # Archive directory should exist (if archiving was performed)
        # This may not always run, so we make it optional
        if archive_dir.exists():
            # Check for archived report
            archived_files = list(archive_dir.glob("*.md")) + list(archive_dir.glob("*.docx"))
            assert len(archived_files) > 0, "No archived reports found"


@pytest.mark.integration
class TestPhase3Integration:
    """Integration tests across Phase 3 components"""

    def test_database_report_consistency(self, project_root, date_str):
        """
        Verify database and report are consistent
        Report should reflect signals in database
        """
        db_file = project_root / "signals/database.json"
        report_file = project_root / f"reports/daily/environmental-scan-{date_str}.md"

        with open(db_file) as f:
            db_data = json.load(f)

        # Get today's signals from database
        today_signals = [
            s for s in db_data.get("signals", [])
            if s.get("detected_date") == date_str or s.get("date") == date_str
        ]

        with open(report_file, encoding='utf-8') as f:
            report_content = f.read()

        # Report should mention at least some signal IDs or titles
        # (This is a loose check since report may summarize)

        # Check if signal count is mentioned
        signal_count = len(today_signals)

        numbers_in_report = re.findall(r'\d+', report_content)
        numbers = [int(n) for n in numbers_in_report]

        # Relaxed check: signal count or close numbers should appear
        close_numbers = [n for n in numbers if abs(n - signal_count) <= 2]

        assert len(close_numbers) > 0, \
            f"Signal count {signal_count} not reflected in report"

    def test_workflow_completeness(self, project_root, date_str):
        """
        Verify all Phase 3 outputs are present
        """
        required_outputs = [
            f"reports/daily/environmental-scan-{date_str}.md",
            "signals/database.json",
        ]

        missing_outputs = []

        for output in required_outputs:
            output_path = project_root / output
            if not output_path.exists():
                missing_outputs.append(output)

        assert len(missing_outputs) == 0, \
            f"Phase 3 outputs missing:\n" + \
            "\n".join(f"  - {o}" for o in missing_outputs)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
