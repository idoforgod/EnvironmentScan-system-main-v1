"""
Unit tests for news_direct_crawler.py — WF4 Multi & Global News Direct Crawler.

Tests cover:
- validate_required_fields(): presence/absence of 4 required fields
- compute_content_hash(): determinism and collision resistance
- calculate_crawl_stats(): per-site, per-language aggregate counts
- NetworkGuard.__init__: max_retries configuration
- CrawlDefender.__init__: initialization and default strategy
- CrawlDefender.detect_block_type(): HTTP status → block type mapping
- CrawlDefender.get_next_strategy(): strategy escalation logic
- NewsDirectCrawler._make_short_name(): short site name generation
- Signal ID format: regex pattern news-YYYYMMDD-site-NNN
- evaluate_retry_decision(): retry/escalation logic per block type
"""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "env-scanning"))

from core.news_direct_crawler import (
    CrawlDefender,
    NetworkGuard,
    NewsDirectCrawler,
    calculate_crawl_stats,
    compute_content_hash,
    evaluate_retry_decision,
    validate_required_fields,
)


# ---------------------------------------------------------------------------
# validate_required_fields
# ---------------------------------------------------------------------------

class TestValidateRequiredFields:
    """Tests for validate_required_fields() — 4 required fields check."""

    def test_all_four_fields_present_returns_true(self):
        """Article with title, published_date, content, source_url → True."""
        article = {
            "title": "AI Breakthrough in Quantum Computing",
            "published_date": "2026-02-24",
            "content": "Researchers announced a major breakthrough...",
            "source_url": "https://example.com/article/123",
        }
        assert validate_required_fields(article) is True

    def test_alternative_field_names_accepted(self):
        """Article with pub_date, abstract, url (alternative names) → True."""
        article = {
            "title": "Climate Policy Update",
            "pub_date": "2026-02-24",
            "abstract": "The EU announced new carbon pricing rules...",
            "url": "https://example.com/article/456",
        }
        assert validate_required_fields(article) is True

    def test_missing_title_returns_false(self):
        article = {
            "published_date": "2026-02-24",
            "content": "Some content here",
            "source_url": "https://example.com/article",
        }
        assert validate_required_fields(article) is False

    def test_missing_date_returns_false(self):
        article = {
            "title": "Test Title",
            "content": "Some content",
            "source_url": "https://example.com",
        }
        assert validate_required_fields(article) is False

    def test_missing_content_returns_false(self):
        article = {
            "title": "Test Title",
            "published_date": "2026-02-24",
            "source_url": "https://example.com",
        }
        assert validate_required_fields(article) is False

    def test_missing_source_url_returns_false(self):
        article = {
            "title": "Test Title",
            "published_date": "2026-02-24",
            "content": "Some content here",
        }
        assert validate_required_fields(article) is False

    def test_empty_title_returns_false(self):
        article = {
            "title": "",
            "published_date": "2026-02-24",
            "content": "Some content",
            "source_url": "https://example.com",
        }
        assert validate_required_fields(article) is False

    def test_whitespace_only_title_returns_false(self):
        article = {
            "title": "   ",
            "published_date": "2026-02-24",
            "content": "Some content",
            "source_url": "https://example.com",
        }
        assert validate_required_fields(article) is False

    def test_empty_dict_returns_false(self):
        assert validate_required_fields({}) is False

    def test_all_fields_whitespace_returns_false(self):
        article = {
            "title": "  ",
            "published_date": "  ",
            "content": "  ",
            "source_url": "  ",
        }
        assert validate_required_fields(article) is False


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------

class TestComputeContentHash:
    """Tests for compute_content_hash() — MD5-based dedup hash."""

    def test_same_input_same_hash(self):
        """Identical title + content must produce identical hashes."""
        article = {"title": "Test Title", "content": "Test content body"}
        hash1 = compute_content_hash(article)
        hash2 = compute_content_hash(article)
        assert hash1 == hash2

    def test_different_title_different_hash(self):
        """Different titles must produce different hashes."""
        a1 = {"title": "Title A", "content": "Same content"}
        a2 = {"title": "Title B", "content": "Same content"}
        assert compute_content_hash(a1) != compute_content_hash(a2)

    def test_different_content_different_hash(self):
        """Different content must produce different hashes."""
        a1 = {"title": "Same Title", "content": "Content Alpha"}
        a2 = {"title": "Same Title", "content": "Content Beta"}
        assert compute_content_hash(a1) != compute_content_hash(a2)

    def test_hash_is_32_char_hex(self):
        """MD5 hex digest must be exactly 32 hex characters."""
        h = compute_content_hash({"title": "X", "content": "Y"})
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)

    def test_uses_abstract_fallback(self):
        """When 'content' key is missing, 'abstract' is used as fallback."""
        a1 = {"title": "T", "content": "Body text"}
        a2 = {"title": "T", "abstract": "Body text"}
        assert compute_content_hash(a1) == compute_content_hash(a2)

    def test_content_truncated_at_500_chars(self):
        """Content beyond 500 characters should not affect the hash."""
        base_content = "A" * 500
        a1 = {"title": "T", "content": base_content + "EXTRA"}
        a2 = {"title": "T", "content": base_content + "DIFFERENT"}
        assert compute_content_hash(a1) == compute_content_hash(a2)

    def test_empty_article_returns_hash(self):
        """Empty dict should still return a valid hash (of empty strings)."""
        h = compute_content_hash({})
        assert len(h) == 32

    def test_korean_content_produces_stable_hash(self):
        """Korean UTF-8 content should produce a stable hash."""
        article = {"title": "한국어 제목", "content": "한국어 내용 테스트"}
        h1 = compute_content_hash(article)
        h2 = compute_content_hash(article)
        assert h1 == h2
        assert len(h1) == 32


# ---------------------------------------------------------------------------
# calculate_crawl_stats
# ---------------------------------------------------------------------------

class TestCalculateCrawlStats:
    """Tests for calculate_crawl_stats() — aggregate crawl statistics."""

    def test_per_site_counts(self):
        """Per-site article counts are correct."""
        results = {
            "items": [
                {"scan_metadata": {"site_name": "bbc", "crawl_strategy_used": "rss"},
                 "content": {"language": "en"}},
                {"scan_metadata": {"site_name": "bbc", "crawl_strategy_used": "rss"},
                 "content": {"language": "en"}},
                {"scan_metadata": {"site_name": "reuters", "crawl_strategy_used": "web"},
                 "content": {"language": "en"}},
            ],
            "site_results": {
                "bbc": {"status": "success"},
                "reuters": {"status": "success"},
            },
        }
        stats = calculate_crawl_stats(results)
        assert stats["per_site"]["bbc"] == 2
        assert stats["per_site"]["reuters"] == 1
        assert stats["total_articles"] == 3

    def test_per_language_counts(self):
        """Per-language article counts are correct."""
        results = {
            "items": [
                {"scan_metadata": {"site_name": "a", "crawl_strategy_used": "rss"},
                 "content": {"language": "en"}},
                {"scan_metadata": {"site_name": "b", "crawl_strategy_used": "rss"},
                 "content": {"language": "ko"}},
                {"scan_metadata": {"site_name": "c", "crawl_strategy_used": "web"},
                 "content": {"language": "ko"}},
                {"scan_metadata": {"site_name": "d", "crawl_strategy_used": "web"},
                 "content": {"language": "ja"}},
            ],
            "site_results": {},
        }
        stats = calculate_crawl_stats(results)
        assert stats["per_language"]["en"] == 1
        assert stats["per_language"]["ko"] == 2
        assert stats["per_language"]["ja"] == 1

    def test_per_strategy_counts(self):
        """Per-strategy counts are correct."""
        results = {
            "items": [
                {"scan_metadata": {"site_name": "a", "crawl_strategy_used": "rss"},
                 "content": {"language": "en"}},
                {"scan_metadata": {"site_name": "b", "crawl_strategy_used": "rss"},
                 "content": {"language": "en"}},
                {"scan_metadata": {"site_name": "c", "crawl_strategy_used": "web"},
                 "content": {"language": "en"}},
            ],
            "site_results": {},
        }
        stats = calculate_crawl_stats(results)
        assert stats["per_strategy"]["rss"] == 2
        assert stats["per_strategy"]["web"] == 1

    def test_sites_succeeded_and_failed(self):
        """Site success/failure counts are correct."""
        results = {
            "items": [],
            "site_results": {
                "bbc": {"status": "success"},
                "reuters": {"status": "success"},
                "nyt": {"status": "failed"},
            },
        }
        stats = calculate_crawl_stats(results)
        assert stats["sites_attempted"] == 3
        assert stats["sites_succeeded"] == 2
        assert stats["sites_failed"] == 1

    def test_empty_results(self):
        """Empty results dict produces zero counts."""
        stats = calculate_crawl_stats({"items": [], "site_results": {}})
        assert stats["total_articles"] == 0
        assert stats["per_site"] == {}
        assert stats["per_language"] == {}
        assert stats["sites_attempted"] == 0

    def test_missing_keys_handled_gracefully(self):
        """Missing metadata keys default to 'unknown'."""
        results = {
            "items": [
                {"scan_metadata": {}, "content": {}},
            ],
            "site_results": {},
        }
        stats = calculate_crawl_stats(results)
        assert stats["per_site"].get("unknown", 0) == 1
        assert stats["per_language"].get("unknown", 0) == 1


# ---------------------------------------------------------------------------
# NetworkGuard
# ---------------------------------------------------------------------------

class TestNetworkGuard:
    """Tests for NetworkGuard — Level 1 retry with UA rotation."""

    def test_default_max_retries(self):
        """Default max_retries should be 5."""
        guard = NetworkGuard()
        assert guard.max_retries == 5

    def test_custom_max_retries(self):
        """Custom max_retries is correctly set."""
        guard = NetworkGuard(max_retries=10)
        assert guard.max_retries == 10

    def test_max_retries_one(self):
        """max_retries=1 should only attempt once."""
        guard = NetworkGuard(max_retries=1)
        assert guard.max_retries == 1

    def test_initial_attempt_count_is_zero(self):
        """Before execute(), attempt_count should be 0."""
        guard = NetworkGuard()
        assert guard.attempt_count == 0


# ---------------------------------------------------------------------------
# CrawlDefender
# ---------------------------------------------------------------------------

class TestCrawlDefender:
    """Tests for CrawlDefender — 7-strategy cascade for anti-blocking."""

    def test_initialization_succeeds(self):
        """CrawlDefender initializes with default strategy."""
        defender = CrawlDefender()
        assert defender.current_strategy == "default"
        assert defender.strategy_index == 0
        assert defender.success_count == 0
        assert defender.consecutive_successes == 0
        assert len(defender.block_history) == 0

    def test_seven_strategies_defined(self):
        """Exactly 7 strategies in the cascade."""
        assert len(CrawlDefender.STRATEGIES) == 7

    def test_detect_block_type_403_is_ip_ban(self):
        """HTTP 403 should be detected as ip_ban."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 403
        result = defender.detect_block_type(response=mock_response)
        assert result == "ip_ban"

    def test_detect_block_type_429_is_rate_limit(self):
        """HTTP 429 should be detected as rate_limit."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 429
        result = defender.detect_block_type(response=mock_response)
        assert result == "rate_limit"

    def test_detect_block_type_503_is_service_unavailable(self):
        """HTTP 503 should be detected as service_unavailable."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 503
        result = defender.detect_block_type(response=mock_response)
        assert result == "service_unavailable"

    def test_detect_block_type_200_no_captcha_is_none(self):
        """HTTP 200 with normal content should be 'none'."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Normal article content " * 50  # Enough text to not be 'empty_response'
        result = defender.detect_block_type(response=mock_response)
        assert result == "none"

    def test_detect_block_type_200_captcha_detected(self):
        """HTTP 200 with 'captcha' in body should be 'captcha'."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Please complete the captcha to continue.</html>" + " " * 200
        result = defender.detect_block_type(response=mock_response)
        assert result == "captcha"

    def test_detect_block_type_none_response_is_no_response(self):
        """None response should return 'no_response'."""
        defender = CrawlDefender()
        result = defender.detect_block_type(response=None)
        assert result == "no_response"

    def test_detect_block_type_timeout_error(self):
        """Timeout exception should be detected."""
        defender = CrawlDefender()
        result = defender.detect_block_type(error=Exception("Connection timeout"))
        assert result == "timeout"

    def test_detect_block_type_connection_error(self):
        """Connection exception should be detected."""
        defender = CrawlDefender()
        result = defender.detect_block_type(error=Exception("Connection refused"))
        assert result == "connection_blocked"

    def test_detect_block_type_ssl_error(self):
        """SSL error should be detected."""
        defender = CrawlDefender()
        result = defender.detect_block_type(error=Exception("SSL certificate verify failed"))
        assert result == "ssl_error"

    def test_detect_block_type_451_is_geo_blocked(self):
        """HTTP 451 should be detected as geo_blocked."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 451
        result = defender.detect_block_type(response=mock_response)
        assert result == "geo_blocked"

    def test_detect_block_type_empty_response(self):
        """HTTP 200 with very short body should be 'empty_response'."""
        defender = CrawlDefender()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        result = defender.detect_block_type(response=mock_response)
        assert result == "empty_response"

    def test_get_next_strategy_captcha_goes_to_browser(self):
        """Captcha block should jump directly to browser_emulation."""
        defender = CrawlDefender()
        result = defender.get_next_strategy("default", "captcha")
        assert result == "browser_emulation"

    def test_get_next_strategy_rate_limit_goes_to_delay(self):
        """Rate limit should jump to delay_increase."""
        defender = CrawlDefender()
        result = defender.get_next_strategy("default", "rate_limit")
        assert result == "delay_increase"

    def test_get_next_strategy_ip_ban_goes_to_proxy(self):
        """IP ban should jump to proxy_rotation."""
        defender = CrawlDefender()
        result = defender.get_next_strategy("default", "ip_ban")
        assert result == "proxy_rotation"

    def test_get_next_strategy_returns_valid_strategy(self):
        """Any return value must be from the STRATEGIES list."""
        defender = CrawlDefender()
        for strategy in CrawlDefender.STRATEGIES:
            for block_type in ["none", "timeout", "rate_limit", "captcha", "ip_ban"]:
                result = defender.get_next_strategy(strategy, block_type)
                assert result in CrawlDefender.STRATEGIES, \
                    f"Invalid strategy '{result}' for ({strategy}, {block_type})"

    def test_get_next_strategy_linear_advance(self):
        """Unknown block type should advance to the next strategy linearly."""
        defender = CrawlDefender()
        result = defender.get_next_strategy("default", "unknown")
        assert result == "httpx_async"

    def test_get_next_strategy_wraps_around(self):
        """Last strategy should wrap around to the first."""
        defender = CrawlDefender()
        result = defender.get_next_strategy("browser_emulation", "unknown")
        assert result == "default"

    def test_escalate_changes_strategy(self):
        """escalate() should update current_strategy."""
        defender = CrawlDefender()
        assert defender.current_strategy == "default"
        new_strategy = defender.escalate(block_type="timeout")
        assert new_strategy != "default"
        assert defender.current_strategy == new_strategy

    def test_record_success_increments_count(self):
        """record_success() should increment success_count."""
        defender = CrawlDefender()
        defender.record_success("bbc", "default")
        assert defender.success_count == 1
        assert defender.consecutive_successes == 1

    def test_record_success_resets_after_5_consecutive(self):
        """After 5 consecutive successes at a non-default strategy, reset to default."""
        defender = CrawlDefender()
        defender.strategy_index = 2
        defender.current_strategy = "rotate_headers"
        for _ in range(5):
            defender.record_success("bbc", "rotate_headers")
        assert defender.current_strategy == "default"
        assert defender.strategy_index == 0


# ---------------------------------------------------------------------------
# NewsDirectCrawler._make_short_name
# ---------------------------------------------------------------------------

class TestMakeShortName:
    """Tests for NewsDirectCrawler._make_short_name() — short site name generation."""

    def test_basic_name(self):
        """Simple name is lowercased."""
        result = NewsDirectCrawler._make_short_name("BBC")
        assert result == "bbc"

    def test_removes_spaces_and_special(self):
        """Spaces and special characters are removed."""
        result = NewsDirectCrawler._make_short_name("The New York Times")
        assert result == "thenewyorktimes"

    def test_truncates_to_15_chars(self):
        """Long names are truncated to 15 characters."""
        result = NewsDirectCrawler._make_short_name("VeryLongSiteNameThatExceedsFifteen")
        assert len(result) <= 15

    def test_empty_name_returns_unknown(self):
        """Empty/all-special input returns 'unknown'."""
        result = NewsDirectCrawler._make_short_name("---")
        assert result == "unknown"

    def test_korean_name_removed(self):
        """Korean characters (non-alphanumeric ASCII) are removed."""
        result = NewsDirectCrawler._make_short_name("한겨레 Hankyoreh")
        assert result == "hankyoreh"

    def test_alphanumeric_preserved(self):
        """Digits are preserved in the short name."""
        result = NewsDirectCrawler._make_short_name("BBC24")
        assert "24" in result


# ---------------------------------------------------------------------------
# Signal ID Format
# ---------------------------------------------------------------------------

class TestSignalIdFormat:
    """Tests for WF4 signal ID format: news-YYYYMMDD-site-NNN."""

    SIGNAL_ID_PATTERN = re.compile(r"^news-\d{8}-\w+-\d{3}$")

    def test_valid_signal_id_matches(self):
        """Standard signal IDs should match the pattern."""
        valid_ids = [
            "news-20260224-bbc-001",
            "news-20260224-reuters-012",
            "news-20260224-nytimes-100",
            "news-20260101-guardian-999",
        ]
        for sid in valid_ids:
            assert self.SIGNAL_ID_PATTERN.match(sid), f"Should match: {sid}"

    def test_invalid_signal_ids_rejected(self):
        """Malformed signal IDs should NOT match."""
        invalid_ids = [
            "naver-20260224-001",        # Wrong prefix
            "news-2026022-bbc-001",      # Date too short
            "news-20260224-bbc-01",      # Sequence too short
            "news-20260224--001",         # Missing site
            "NEWS-20260224-bbc-001",     # Uppercase prefix
        ]
        for sid in invalid_ids:
            assert not self.SIGNAL_ID_PATTERN.match(sid), f"Should NOT match: {sid}"


# ---------------------------------------------------------------------------
# evaluate_retry_decision
# ---------------------------------------------------------------------------

class TestEvaluateRetryDecision:
    """Tests for evaluate_retry_decision() — retry/escalation logic."""

    def test_captcha_never_retries(self):
        """Captcha blocks are non-retryable."""
        should_retry, reason = evaluate_retry_decision("captcha", 1, "default")
        assert should_retry is False
        assert "captcha" in reason

    def test_ip_ban_never_retries(self):
        """IP ban blocks are non-retryable."""
        should_retry, reason = evaluate_retry_decision("ip_ban", 1, "default")
        assert should_retry is False
        assert "ip_ban" in reason

    def test_rate_limit_retries_first_3(self):
        """Rate limit should retry on attempts 1-3."""
        for attempt in [1, 2, 3]:
            should_retry, _ = evaluate_retry_decision("rate_limit", attempt, "default")
            assert should_retry is True, f"Should retry at attempt {attempt}"

    def test_rate_limit_escalates_after_3(self):
        """Rate limit should escalate after attempt 3."""
        should_retry, _ = evaluate_retry_decision("rate_limit", 4, "default")
        assert should_retry is False

    def test_timeout_retries_first_2(self):
        """Timeout should retry on attempts 1-2."""
        for attempt in [1, 2]:
            should_retry, _ = evaluate_retry_decision("timeout", attempt, "default")
            assert should_retry is True

    def test_timeout_escalates_after_2(self):
        """Timeout should escalate after attempt 2."""
        should_retry, _ = evaluate_retry_decision("timeout", 3, "default")
        assert should_retry is False

    def test_connection_blocked_retries_once(self):
        """Connection blocked should retry only once."""
        should_retry, _ = evaluate_retry_decision("connection_blocked", 1, "default")
        assert should_retry is True
        should_retry, _ = evaluate_retry_decision("connection_blocked", 2, "default")
        assert should_retry is False

    def test_service_unavailable_retries_twice(self):
        """Service unavailable (503) should retry up to 2 times."""
        should_retry, _ = evaluate_retry_decision("service_unavailable", 1, "default")
        assert should_retry is True
        should_retry, _ = evaluate_retry_decision("service_unavailable", 2, "default")
        assert should_retry is True
        should_retry, _ = evaluate_retry_decision("service_unavailable", 3, "default")
        assert should_retry is False

    def test_unknown_block_retries_once(self):
        """Unknown block types should retry only once."""
        should_retry, _ = evaluate_retry_decision("something_weird", 1, "default")
        assert should_retry is True
        should_retry, _ = evaluate_retry_decision("something_weird", 2, "default")
        assert should_retry is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
