"""
Unit tests for dedup_gate.py — Deterministic Cross-Scan Duplicate Detection.

Tests cover:
- URL normalization and matching (Stage A)
- Topic fingerprint building and overlap coefficient (Stage B)
- Threshold two-tier classification (definite_duplicate / uncertain / definite_new)
- Previous signals extraction (v2.6.0+ and legacy formats)
- Ambiguous URL exclusion (aggregator page detection)
- New START regression test (the original bug)
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from core.dedup_gate import (
    build_topic_fingerprint,
    entity_overlap,
    extract_entities,
    normalize_text,
    normalize_url,
    overlap_coefficient,
    run_dedup_gate,
    title_similarity,
    _extract_previous_signals,
    _extract_signals,
    _jaro_similarity,
    _jaro_winkler_similarity,
    _run_cascade,
)


# ---------------------------------------------------------------------------
# normalize_url
# ---------------------------------------------------------------------------

class TestNormalizeUrl:
    def test_strips_scheme_and_www(self):
        assert normalize_url("https://www.cfr.org/reports/test") == "cfr.org/reports/test"

    def test_strips_query_params(self):
        assert normalize_url("https://cfr.org/reports/test?ref=rss") == "cfr.org/reports/test"

    def test_strips_fragment(self):
        assert normalize_url("https://example.com/page#section") == "example.com/page"

    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.com/page/") == "example.com/page"

    def test_empty_returns_empty(self):
        assert normalize_url("") == ""
        assert normalize_url(None) == ""

    def test_same_article_different_scheme(self):
        url1 = normalize_url("http://arxiv.org/abs/2601.12345")
        url2 = normalize_url("https://arxiv.org/abs/2601.12345")
        assert url1 == url2


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("OpenAI Releases GPT-5") == "openai releases gpt5"

    def test_removes_punctuation(self):
        assert normalize_text("Hello, World!") == "hello world"

    def test_collapses_whitespace(self):
        assert normalize_text("  multiple   spaces  ") == "multiple spaces"

    def test_empty_returns_empty(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


# ---------------------------------------------------------------------------
# build_topic_fingerprint
# ---------------------------------------------------------------------------

class TestBuildTopicFingerprint:
    def test_extracts_title_words(self):
        signal = {"title": "New START Treaty Expiration Risk"}
        fp = build_topic_fingerprint(signal)
        assert "start" in fp
        assert "treaty" in fp
        assert "expiration" in fp
        assert "risk" in fp

    def test_excludes_short_words(self):
        signal = {"title": "AI is bad for us"}
        fp = build_topic_fingerprint(signal)
        # "ai", "is", "bad", "for", "us" — all ≤3 chars
        assert len(fp) == 0

    def test_excludes_stopwords(self):
        signal = {"title": "This report shows the global study"}
        fp = build_topic_fingerprint(signal)
        assert "this" not in fp
        assert "report" not in fp
        assert "shows" not in fp
        assert "global" not in fp
        assert "study" not in fp

    def test_includes_keywords(self):
        signal = {
            "title": "Quantum Computing Advance",
            "content": {"keywords": ["quantum computing", "error correction"]},
        }
        fp = build_topic_fingerprint(signal)
        assert "quantum" in fp
        assert "computing" in fp
        assert "error" in fp
        assert "correction" in fp

    def test_handles_missing_content(self):
        signal = {"title": "Simple Title Here"}
        fp = build_topic_fingerprint(signal)
        assert "simple" in fp
        assert "title" in fp
        assert "here" in fp

    def test_handles_previous_signal_format(self):
        """Previous-signals have {title, url, category} — no content."""
        signal = {"title": "Climate Change Impact Study", "url": "https://example.com", "category": "E"}
        fp = build_topic_fingerprint(signal)
        assert "climate" in fp
        assert "change" in fp
        assert "impact" in fp


# ---------------------------------------------------------------------------
# overlap_coefficient
# ---------------------------------------------------------------------------

class TestOverlapCoefficient:
    def test_identical_sets(self):
        s = {"nuclear", "treaty", "start"}
        assert overlap_coefficient(s, s) == 1.0

    def test_subset(self):
        a = {"nuclear", "treaty", "start", "arms"}
        b = {"nuclear", "treaty"}
        assert overlap_coefficient(a, b) == 1.0  # 2/min(4,2) = 2/2

    def test_partial_overlap(self):
        a = {"nuclear", "treaty", "start", "arms"}
        b = {"nuclear", "treaty", "expires"}
        assert overlap_coefficient(a, b) == pytest.approx(2 / 3)

    def test_no_overlap(self):
        a = {"nuclear", "treaty"}
        b = {"quantum", "computing"}
        assert overlap_coefficient(a, b) == 0.0

    def test_empty_sets(self):
        assert overlap_coefficient(set(), {"a"}) == 0.0
        assert overlap_coefficient({"a"}, set()) == 0.0
        assert overlap_coefficient(set(), set()) == 0.0


# ---------------------------------------------------------------------------
# New START Regression Test (the original bug)
# ---------------------------------------------------------------------------

class TestNewStartRegression:
    """
    Root cause: "New START Nuclear Treaty" appeared as "new" in 8 consecutive
    daily scans because the LLM dedup-filter couldn't reliably catch it.
    The dedup_gate.py must catch this deterministically.
    """

    def test_new_start_detected_as_duplicate(self):
        new_signal = {
            "title": "New START Treaty Expiration Risk — Nuclear Arms Control Gap",
            "content": {"keywords": ["nuclear arms", "treaty", "arms control"]},
        }
        prev_signal = {
            "id": "wf1-20260210-003",
            "title": "New START Nuclear Treaty Expires",
        }

        fp_new = build_topic_fingerprint(new_signal)
        fp_prev = build_topic_fingerprint(prev_signal)
        score = overlap_coefficient(fp_new, fp_prev)

        # Must be above definite_duplicate threshold (0.60)
        assert score >= 0.60, (
            f"New START regression: overlap {score} < 0.60 threshold. "
            f"New FP: {sorted(fp_new)}, Prev FP: {sorted(fp_prev)}"
        )

    def test_new_start_not_confused_with_quantum(self):
        new_signal = {
            "title": "New START Treaty Expiration Risk — Nuclear Arms Control Gap",
            "content": {"keywords": ["nuclear arms", "treaty"]},
        }
        quantum_signal = {
            "id": "wf1-20260218-001",
            "title": "Iceberg Quantum Breaks RSA-2048 with <100K Qubits",
        }

        fp_new = build_topic_fingerprint(new_signal)
        fp_quantum = build_topic_fingerprint(quantum_signal)
        score = overlap_coefficient(fp_new, fp_quantum)

        # Must be below uncertain threshold (0.30)
        assert score < 0.30, (
            f"False positive: New START vs Quantum scored {score} >= 0.30"
        )


# ---------------------------------------------------------------------------
# _extract_previous_signals
# ---------------------------------------------------------------------------

class TestExtractPreviousSignals:
    def test_v260_format(self):
        """v2.6.0+ format with url_index at top level."""
        data = {
            "url_index": {
                "https://example.com/article1": "sig-001",
                "https://example.com/article2": "sig-002",
            },
            "signals": [
                {"id": "sig-001", "title": "Article 1", "url": "https://example.com/article1"},
                {"id": "sig-002", "title": "Article 2", "url": "https://example.com/article2"},
            ],
        }
        signals, url_index = _extract_previous_signals(data)
        assert len(signals) == 2
        assert "example.com/article1" in url_index
        assert url_index["example.com/article1"] == "sig-001"

    def test_database_format(self):
        """Database format with source.url nested."""
        data = {
            "version": "2.0",
            "signals": [
                {
                    "id": "wf1-001",
                    "title": "Test",
                    "source": {"url": "https://example.com/unique"},
                },
            ],
        }
        signals, url_index = _extract_previous_signals(data)
        assert len(signals) == 1
        assert "example.com/unique" in url_index

    def test_ambiguous_urls_excluded(self):
        """Aggregator page URLs (multiple signals) should be excluded from index."""
        data = {
            "signals": [
                {"id": "sig-001", "title": "Article 1", "source": {"url": "https://nature.com/news"}},
                {"id": "sig-002", "title": "Article 2", "source": {"url": "https://nature.com/news"}},
                {"id": "sig-003", "title": "Article 3", "source": {"url": "https://nature.com/unique"}},
            ],
        }
        signals, url_index = _extract_previous_signals(data)
        assert len(signals) == 3
        # nature.com/news should be EXCLUDED (ambiguous — 2 signals)
        assert "nature.com/news" not in url_index
        # nature.com/unique should be INCLUDED (unique)
        assert "nature.com/unique" in url_index


# ---------------------------------------------------------------------------
# _run_cascade
# ---------------------------------------------------------------------------

class TestRunCascade:
    def setup_method(self):
        """Set up common test signals."""
        self.prev_signals = [
            {"id": "prev-001", "title": "New START Nuclear Treaty Expires"},
            {"id": "prev-002", "title": "Quantum Computing Breakthrough 2026"},
            {"id": "prev-003", "title": "Climate Change Report UN", "url": "https://un.org/climate"},
        ]
        self.prev_url_index = {
            "un.org/climate": "prev-003",
        }
        self.prev_fingerprints = {
            sig["id"]: build_topic_fingerprint(sig) for sig in self.prev_signals
        }
        self.prev_entities = {
            sig["id"]: extract_entities(sig) for sig in self.prev_signals
        }
        # Default thresholds
        self.th_defaults = dict(
            th_url=1.0,
            th_topic_definite=0.60, th_topic_uncertain=0.30,
            th_title_definite=0.90, th_title_uncertain=0.80,
            th_entity_definite=0.85, th_entity_uncertain=0.70,
        )

    def _cascade(self, signal_id, signal_url, signal_title, signal_fp, signal_ent, **overrides):
        kw = dict(
            signal_id=signal_id,
            signal_url=signal_url,
            signal_title=signal_title,
            signal_fingerprint=signal_fp,
            signal_entities=signal_ent,
            prev_signals=self.prev_signals,
            prev_url_index=self.prev_url_index,
            prev_fingerprints=self.prev_fingerprints,
            prev_entities=self.prev_entities,
            **self.th_defaults,
        )
        kw.update(overrides)
        return _run_cascade(**kw)

    def test_stage_a_url_match(self):
        sig = {"title": "Different Title"}
        result = self._cascade(
            "new-001", "https://un.org/climate", "Different Title",
            build_topic_fingerprint(sig), extract_entities(sig),
        )
        assert result["verdict"] == "definite_duplicate"
        assert result["stage"] == "A_url"
        assert result["matched_signal_id"] == "prev-003"

    def test_stage_b_definite_duplicate(self):
        sig = {"title": "New START Treaty Expiration Risk", "content": {"keywords": ["nuclear", "treaty"]}}
        result = self._cascade(
            "new-002", "", sig["title"],
            build_topic_fingerprint(sig), extract_entities(sig),
        )
        assert result["verdict"] == "definite_duplicate"
        assert result["stage"] == "B_topic"
        assert result["score"] >= 0.60

    def test_definite_new(self):
        sig = {"title": "Completely Unrelated Biotechnology Signal"}
        result = self._cascade(
            "new-003", "", sig["title"],
            build_topic_fingerprint(sig), extract_entities(sig),
        )
        assert result["verdict"] == "definite_new"
        assert result["stage"] is None


# ---------------------------------------------------------------------------
# run_dedup_gate (integration)
# ---------------------------------------------------------------------------

class TestRunDedupGate:
    def test_full_gate_with_known_duplicate(self):
        """Integration test: gate correctly identifies known duplicate signal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create new signals file
            new_signals = {
                "items": [
                    {
                        "id": "new-001",
                        "title": "New START Treaty Expiration Risk",
                        "source": {"url": "https://example.com/new-start-2"},
                        "content": {"keywords": ["nuclear arms", "treaty"]},
                    },
                    {
                        "id": "new-002",
                        "title": "Completely Novel Discovery in Marine Biology",
                        "source": {"url": "https://example.com/marine"},
                        "content": {"keywords": ["marine", "biology", "discovery"]},
                    },
                ],
            }
            signals_path = Path(tmpdir) / "daily-scan.json"
            with open(signals_path, "w") as f:
                json.dump(new_signals, f)

            # Create previous signals file
            prev_signals = {
                "signals": [
                    {
                        "id": "prev-001",
                        "title": "New START Nuclear Treaty Expires",
                        "source": {"url": "https://example.com/new-start-1"},
                    },
                ],
            }
            prev_path = Path(tmpdir) / "previous.json"
            with open(prev_path, "w") as f:
                json.dump(prev_signals, f)

            # Run gate
            result = run_dedup_gate(
                signals_path=str(signals_path),
                previous_path=str(prev_path),
                workflow_name="test-wf",
            )

            assert result["gate_status"] == "PASS_WITH_REMOVAL"
            assert result["statistics"]["definite_duplicates"] >= 1
            assert result["statistics"]["definite_new"] >= 1

            # New START should be caught
            dupe_titles = [d["signal_title"] for d in result["duplicates"]]
            assert any("New START" in t for t in dupe_titles)

    def test_no_previous_returns_warn(self):
        """Gate returns WARN when previous signals file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            signals = {"items": [{"id": "s1", "title": "Test Signal"}]}
            sig_path = Path(tmpdir) / "signals.json"
            with open(sig_path, "w") as f:
                json.dump(signals, f)

            result = run_dedup_gate(
                signals_path=str(sig_path),
                previous_path=str(Path(tmpdir) / "nonexistent.json"),
                workflow_name="test-wf",
            )

            assert result["gate_status"] == "WARN"
            assert result["statistics"]["pass_through"] == 1

    def test_empty_signals_returns_pass(self):
        """Gate returns PASS when there are no new signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            signals = {"items": []}
            sig_path = Path(tmpdir) / "signals.json"
            with open(sig_path, "w") as f:
                json.dump(signals, f)

            prev = {"signals": [{"id": "p1", "title": "Previous"}]}
            prev_path = Path(tmpdir) / "prev.json"
            with open(prev_path, "w") as f:
                json.dump(prev, f)

            result = run_dedup_gate(
                signals_path=str(sig_path),
                previous_path=str(prev_path),
                workflow_name="test-wf",
            )

            assert result["gate_status"] == "PASS"
            assert result["statistics"]["total_input"] == 0


# ---------------------------------------------------------------------------
# False positive prevention
# ---------------------------------------------------------------------------

class TestFalsePositivePrevention:
    """Ensure geographic/domain word overlap doesn't cause false duplicates."""

    def test_hong_kong_geographic_not_false_positive(self):
        """Two signals about Hong Kong but different topics should NOT be definite_duplicate."""
        fp_fintech = build_topic_fingerprint(
            {"title": "Hong Kong HKMA Fintech 2030 Blueprint: Quantum and AI Focus",
             "content": {"keywords": ["fintech", "quantum computing"]}}
        )
        fp_trial = build_topic_fingerprint(
            {"title": "Jimmy Lai Sentenced to 20 Years (Hong Kong)"}
        )
        score = overlap_coefficient(fp_fintech, fp_trial)
        assert score < 0.60, f"Geographic false positive: Hong Kong scored {score}"

    def test_same_domain_different_events(self):
        """Two fintech breaches from different companies should NOT be definite_duplicate."""
        fp_figure = build_topic_fingerprint(
            {"title": "Figure Fintech Data Breach Affects ~1M Customers"}
        )
        fp_marquis = build_topic_fingerprint(
            {"title": "Fintech firm Marquis blames hack at firewall provider SonicWall"}
        )
        score = overlap_coefficient(fp_figure, fp_marquis)
        assert score < 0.60, f"Same-domain false positive: scored {score}"


# ---------------------------------------------------------------------------
# Stage C: Jaro-Winkler Title Similarity
# ---------------------------------------------------------------------------

class TestJaroSimilarity:
    def test_identical(self):
        assert _jaro_similarity("hello", "hello") == 1.0

    def test_empty(self):
        assert _jaro_similarity("", "hello") == 0.0
        assert _jaro_similarity("hello", "") == 0.0

    def test_completely_different(self):
        score = _jaro_similarity("abc", "xyz")
        assert score == 0.0

    def test_partial_match(self):
        score = _jaro_similarity("martha", "marhta")
        assert score > 0.9  # Known Jaro score ≈ 0.944


class TestJaroWinklerSimilarity:
    def test_identical(self):
        assert _jaro_winkler_similarity("test", "test") == 1.0

    def test_common_prefix_bonus(self):
        """Jaro-Winkler gives bonus for common prefix."""
        jaro = _jaro_similarity("martha", "marhta")
        jw = _jaro_winkler_similarity("martha", "marhta")
        assert jw >= jaro  # JW is always >= Jaro

    def test_no_prefix_bonus(self):
        """No common prefix → JW equals Jaro."""
        jaro = _jaro_similarity("abc", "cab")
        jw = _jaro_winkler_similarity("abc", "cab")
        assert jw == jaro  # No common prefix


class TestTitleSimilarity:
    def test_identical_titles(self):
        assert title_similarity("Hello World", "Hello World") == 1.0

    def test_case_insensitive(self):
        assert title_similarity("NEW START TREATY", "new start treaty") == 1.0

    def test_similar_titles(self):
        score = title_similarity(
            "New START Treaty Expiration Risk",
            "New START Treaty Expiration Danger"
        )
        assert score >= 0.80, f"Similar titles scored {score}"

    def test_different_titles(self):
        score = title_similarity(
            "Quantum Computing Breakthrough",
            "Climate Change Policy Update"
        )
        assert score < 0.60, f"Different titles scored {score}"

    def test_empty_titles(self):
        assert title_similarity("", "something") == 0.0
        assert title_similarity("something", "") == 0.0

    def test_near_duplicate_titles(self):
        """Titles differing by one word should be very similar."""
        score = title_similarity(
            "NATO Expansion: Finland Joins Alliance",
            "NATO Expansion: Sweden Joins Alliance"
        )
        assert score >= 0.85, f"Near-duplicate titles scored {score}"


# ---------------------------------------------------------------------------
# Stage D: Entity Extraction + Overlap
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_extracts_acronyms(self):
        signal = {"title": "NATO and BRICS Discuss RSA-2048 Protocol"}
        entities = extract_entities(signal)
        assert "nato" in entities
        assert "brics" in entities
        assert "rsa" in entities or "rsa-2048" in entities

    def test_extracts_proper_nouns(self):
        signal = {"title": "Hong Kong HKMA Fintech 2030 Blueprint"}
        entities = extract_entities(signal)
        assert "hkma" in entities
        assert "hong" in entities or "hong kong" in entities

    def test_extracts_keywords(self):
        signal = {
            "title": "Test Signal",
            "content": {"keywords": ["nuclear arms", "treaty verification"]},
        }
        entities = extract_entities(signal)
        assert "nuclear arms" in entities
        assert "treaty verification" in entities

    def test_empty_signal(self):
        entities = extract_entities({})
        assert len(entities) == 0

    def test_does_not_extract_stopwords(self):
        signal = {"title": "The Global Report Shows Major Impact"}
        entities = extract_entities(signal)
        # "The", "Global", "Report", "Shows", "Major" are stopwords
        assert "the" not in entities
        assert "global" not in entities
        assert "report" not in entities


class TestEntityOverlap:
    def test_identical_sets(self):
        s = {"nato", "nuclear", "treaty"}
        assert entity_overlap(s, s) == 1.0

    def test_no_overlap(self):
        a = {"nato", "nuclear"}
        b = {"quantum", "computing"}
        assert entity_overlap(a, b) == 0.0

    def test_partial_overlap(self):
        a = {"nato", "nuclear", "treaty", "arms"}
        b = {"nato", "nuclear", "computing"}
        # Intersection: {nato, nuclear} = 2
        # Union: {nato, nuclear, treaty, arms, computing} = 5
        # Jaccard = 2/5 = 0.4
        assert entity_overlap(a, b) == pytest.approx(2 / 5)

    def test_empty_sets(self):
        assert entity_overlap(set(), set()) == 0.0
        assert entity_overlap({"a"}, set()) == 0.0
        assert entity_overlap(set(), {"b"}) == 0.0

    def test_full_overlap(self):
        a = {"nato", "nuclear"}
        b = {"nato", "nuclear"}
        assert entity_overlap(a, b) == 1.0


# ---------------------------------------------------------------------------
# Regression: Stage C/D catch what A/B might miss
# ---------------------------------------------------------------------------

class TestStageCDRegression:
    """
    Test that Stage C (title similarity) and Stage D (entity overlap) can
    catch duplicates that Stage B (topic fingerprint) might miss due to
    different wording but same underlying topic.
    """

    def test_title_variant_caught_by_stage_c(self):
        """Same event described with slightly different wording →
        Stage C (Jaro-Winkler on full title) should catch it."""
        title_a = "European Central Bank Raises Interest Rates to 4.5%"
        title_b = "European Central Bank Raises Interest Rate to 4.50%"
        score = title_similarity(title_a, title_b)
        assert score >= 0.90, f"Title variant scored {score} (expected ≥0.90)"

    def test_entity_overlap_catches_reworded_signal(self):
        """Same entities with matching keywords → Stage D should flag.
        Entity overlap uses Jaccard, which is diluted by noisy title words.
        The primary matching power comes from explicit keywords."""
        sig_a = {
            "title": "NATO Summit on Ukraine",
            "content": {"keywords": ["nato", "ukraine", "membership", "alliance expansion"]},
        }
        sig_b = {
            "title": "NATO Expansion for Ukraine",
            "content": {"keywords": ["nato", "ukraine", "membership", "alliance expansion"]},
        }
        ent_a = extract_entities(sig_a)
        ent_b = extract_entities(sig_b)
        score = entity_overlap(ent_a, ent_b)
        # With 4 identical keywords + some shared title entities,
        # Jaccard should be above 0.60 (some noise from differing title words
        # like "summit" vs "expansion" slightly dilutes the score)
        assert score >= 0.60, (
            f"Entity overlap {score} for keyword-matching signals. "
            f"A entities: {sorted(ent_a)}, B entities: {sorted(ent_b)}"
        )


# ---------------------------------------------------------------------------
# Lookback Days Filtering
# ---------------------------------------------------------------------------

class TestLookbackDaysFiltering:
    def test_recent_signals_kept(self):
        """Signals within lookback window are kept."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        data = {
            "signals": [
                {"id": "s1", "title": "Recent", "collected_at": (now - timedelta(days=5)).isoformat()},
                {"id": "s2", "title": "Old", "collected_at": (now - timedelta(days=40)).isoformat()},
            ]
        }
        signals, _ = _extract_previous_signals(data, lookback_days=30)
        ids = [s["id"] for s in signals]
        assert "s1" in ids
        assert "s2" not in ids

    def test_no_lookback_keeps_all(self):
        """No lookback_days → all signals kept."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        data = {
            "signals": [
                {"id": "s1", "title": "Recent", "collected_at": (now - timedelta(days=5)).isoformat()},
                {"id": "s2", "title": "Old", "collected_at": (now - timedelta(days=400)).isoformat()},
            ]
        }
        signals, _ = _extract_previous_signals(data, lookback_days=None)
        assert len(signals) == 2

    def test_missing_date_kept(self):
        """Signals without collected_at are kept (conservative)."""
        data = {
            "signals": [
                {"id": "s1", "title": "No date"},
                {"id": "s2", "title": "Has date", "collected_at": "1990-01-01T00:00:00Z"},
            ]
        }
        signals, _ = _extract_previous_signals(data, lookback_days=30)
        ids = [s["id"] for s in signals]
        assert "s1" in ids  # No date → kept
        assert "s2" not in ids  # Very old → filtered out


# ---------------------------------------------------------------------------
# 4-Stage Cascade Integration
# ---------------------------------------------------------------------------

class TestRunCascadeFourStages:
    """Integration test for the full 4-stage cascade."""

    def test_all_stages_with_known_signals(self):
        """Integration: run full gate with signals designed for each stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from datetime import datetime, timezone

            # Create new signals targeting each stage
            new_signals = {
                "items": [
                    {
                        "id": "url-dup",
                        "title": "URL Duplicate Test",
                        "source": {"url": "https://example.com/existing-article"},
                        "content": {"keywords": ["unrelated"]},
                    },
                    {
                        "id": "topic-dup",
                        "title": "New START Treaty Expiration Risk",
                        "source": {"url": "https://other.com/new-start-2"},
                        "content": {"keywords": ["nuclear arms", "treaty"]},
                    },
                    {
                        "id": "novel-signal",
                        "title": "Completely Novel Deep Sea Mining Discovery",
                        "source": {"url": "https://other.com/novel"},
                        "content": {"keywords": ["deep sea", "mining", "discovery"]},
                    },
                ],
            }
            sig_path = Path(tmpdir) / "daily-scan.json"
            with open(sig_path, "w") as f:
                json.dump(new_signals, f)

            # Previous signals
            prev = {
                "signals": [
                    {
                        "id": "prev-001",
                        "title": "Existing Article About AI",
                        "source": {"url": "https://example.com/existing-article"},
                    },
                    {
                        "id": "prev-002",
                        "title": "New START Nuclear Treaty Expires",
                        "source": {"url": "https://example.com/new-start-1"},
                    },
                ],
            }
            prev_path = Path(tmpdir) / "prev.json"
            with open(prev_path, "w") as f:
                json.dump(prev, f)

            result = run_dedup_gate(
                signals_path=str(sig_path),
                previous_path=str(prev_path),
                workflow_name="test-wf",
            )

            assert result["gate_status"] == "PASS_WITH_REMOVAL"
            # URL dup + topic dup = 2 duplicates
            assert result["statistics"]["definite_duplicates"] >= 2
            # Novel signal should pass
            assert result["statistics"]["definite_new"] >= 1
            # Stage breakdown should have keys for all 4 stages
            sb = result["stage_breakdown"]
            assert "A_url" in sb
            assert "B_topic" in sb
            assert "C_title" in sb
            assert "D_entity" in sb
            # Version should be 2.0.0
            assert result["gate_version"] == "2.0.0"
