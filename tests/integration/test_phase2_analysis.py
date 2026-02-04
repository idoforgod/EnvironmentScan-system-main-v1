"""
Phase 2 Integration Tests - Planning/Analysis Phase
Tests: Signal classification, Impact analysis, Priority ranking
"""
import pytest
import json
from datetime import datetime


@pytest.mark.integration
class TestPhase2Classification:
    """Integration tests for signal classification"""

    def test_classification_output_exists(self, project_root, date_str):
        """
        Verify classification output was generated
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        assert classified_file.exists(), f"Classification output missing: {classified_file}"

    def test_classification_metadata(self, project_root, date_str):
        """
        Verify classification metadata is complete
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        # Check metadata structure
        assert "classification_metadata" in data or "signals" in data, \
            "Classification output missing required fields"

        if "classification_metadata" in data:
            metadata = data["classification_metadata"]

            # Expected metadata fields
            assert "date" in metadata
            assert metadata["date"] == date_str

            if "total_signals" in metadata:
                assert metadata["total_signals"] == len(data.get("signals", []))

    def test_all_signals_classified(self, project_root, date_str):
        """
        Verify all input signals received classification
        Compare with raw scan count
        """
        raw_file = project_root / f"raw/daily-scan-{date_str}.json"
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(raw_file) as f:
            raw_data = json.load(f)

        with open(classified_file) as f:
            classified_data = json.load(f)

        raw_count = len(raw_data.get("items", []))
        classified_count = len(classified_data.get("signals", []))

        assert raw_count == classified_count, \
            f"Signal count mismatch: {raw_count} raw vs {classified_count} classified"

    def test_steeps_categories_valid(self, project_root, date_str):
        """
        Verify all classifications use valid STEEPs categories
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        valid_categories = {"S", "T", "E", "P", "s"}
        signals = data.get("signals", [])

        invalid_categories = []

        for signal in signals:
            category = signal.get("category")
            if category not in valid_categories:
                invalid_categories.append({
                    "id": signal.get("id"),
                    "category": category
                })

        assert len(invalid_categories) == 0, \
            f"Invalid STEEPs categories:\n" + \
            "\n".join(f"  {s['id']}: {s['category']}" for s in invalid_categories)

    def test_steeps_distribution(self, project_root, date_str):
        """
        Verify STEEPs categories are reasonably distributed
        Should not all be in one category
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        signals = data.get("signals", [])

        # Count categories
        category_counts = {"S": 0, "T": 0, "E": 0, "P": 0, "s": 0}

        for signal in signals:
            category = signal.get("category")
            if category in category_counts:
                category_counts[category] += 1

        # Should have signals in at least 2 categories
        non_zero_categories = sum(1 for count in category_counts.values() if count > 0)

        assert non_zero_categories >= 2, \
            f"All signals in same category: {category_counts}"

    def test_confidence_scores_valid(self, project_root, date_str):
        """
        Verify all confidence scores are in valid range [0, 1]
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        signals = data.get("signals", [])

        invalid_confidence = []

        for signal in signals:
            confidence = signal.get("confidence", 0)

            if not (0 <= confidence <= 1):
                invalid_confidence.append({
                    "id": signal.get("id"),
                    "confidence": confidence
                })

        assert len(invalid_confidence) == 0, \
            f"Invalid confidence scores (must be 0-1):\n" + \
            "\n".join(f"  {s['id']}: {s['confidence']}" for s in invalid_confidence)


@pytest.mark.integration
class TestPhase2ImpactAnalysis:
    """Integration tests for impact analysis"""

    def test_impact_analysis_output_exists(self, project_root, date_str):
        """
        Verify impact analysis output was generated
        """
        impact_file = project_root / f"analysis/impact-assessment-{date_str}.json"

        assert impact_file.exists(), f"Impact analysis output missing: {impact_file}"

    def test_impact_analysis_structure(self, project_root, date_str):
        """
        Verify impact analysis has expected structure
        """
        impact_file = project_root / f"analysis/impact-assessment-{date_str}.json"

        with open(impact_file) as f:
            data = json.load(f)

        # Should have analysis metadata
        assert "analysis_metadata" in data or "impacts" in data or "cross_impacts" in data, \
            "Impact analysis missing expected structure"


@pytest.mark.integration
class TestPhase2PriorityRanking:
    """Integration tests for priority ranking"""

    def test_priority_ranking_output_exists(self, project_root, date_str):
        """
        Verify priority ranking output was generated
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        assert ranked_file.exists(), f"Priority ranking output missing: {ranked_file}"

    def test_priority_ranking_metadata(self, project_root, date_str):
        """
        Verify priority ranking metadata
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            data = json.load(f)

        # Check for metadata
        assert "analysis_metadata" in data or "ranked_signals" in data, \
            "Priority ranking output missing required fields"

    def test_all_signals_ranked(self, project_root, date_str):
        """
        Verify all classified signals received priority ranking
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(classified_file) as f:
            classified_data = json.load(f)

        with open(ranked_file) as f:
            ranked_data = json.load(f)

        classified_count = len(classified_data.get("signals", []))
        ranked_count = len(ranked_data.get("ranked_signals", []))

        assert classified_count == ranked_count, \
            f"Signal count mismatch: {classified_count} classified vs {ranked_count} ranked"

    def test_priority_levels_assigned(self, project_root, date_str):
        """
        Verify priority levels are properly assigned
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            data = json.load(f)

        signals = data.get("ranked_signals", [])

        # All signals should have priority
        signals_without_priority = [
            s.get("id") for s in signals if "priority" not in s
        ]

        assert len(signals_without_priority) == 0, \
            f"Signals missing priority: {signals_without_priority}"

    def test_priority_scores_valid(self, project_root, date_str):
        """
        Verify priority scores are in valid range
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            data = json.load(f)

        signals = data.get("ranked_signals", [])

        invalid_scores = []

        for signal in signals:
            if "priority_score" in signal:
                score = signal["priority_score"]

                # Score should be 0-10 range typically
                if not (0 <= score <= 10):
                    invalid_scores.append({
                        "id": signal.get("id"),
                        "score": score
                    })

        assert len(invalid_scores) == 0, \
            f"Invalid priority scores:\n" + \
            "\n".join(f"  {s['id']}: {s['score']}" for s in invalid_scores)

    def test_priority_distribution(self, project_root, date_str):
        """
        Verify priority distribution is reasonable
        Should have high, medium, and low priorities
        """
        ranked_file = project_root / f"analysis/priority-ranked-{date_str}.json"

        with open(ranked_file) as f:
            data = json.load(f)

        signals = data.get("ranked_signals", [])

        # Count priority levels
        priority_counts = {"high": 0, "medium": 0, "low": 0}

        for signal in signals:
            priority = signal.get("priority", "").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Should have diversity (at least 2 levels)
        non_zero = sum(1 for count in priority_counts.values() if count > 0)

        assert non_zero >= 2, \
            f"Priority distribution too narrow: {priority_counts}"


@pytest.mark.integration
class TestPhase2Performance:
    """Performance tests for Phase 2"""

    def test_classification_quality(self, project_root, date_str):
        """
        Verify classification quality metrics
        """
        classified_file = project_root / f"structured/classified-signals-{date_str}.json"

        with open(classified_file) as f:
            data = json.load(f)

        signals = data.get("signals", [])

        # Calculate average confidence
        confidences = [s.get("confidence", 0) for s in signals if "confidence" in s]

        if confidences:
            avg_confidence = sum(confidences) / len(confidences)

            # Average confidence should be reasonable (> 0.5)
            assert avg_confidence > 0.5, \
                f"Average classification confidence too low: {avg_confidence:.2f}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
