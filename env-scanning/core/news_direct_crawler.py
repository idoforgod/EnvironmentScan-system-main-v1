"""
Multi & Global News Direct Crawler (WF4 Core Module)

Direct news website crawler for 43 individual news sites across multiple
countries and languages. Provides RSS-first crawling with web-crawl fallback
and a Total War stub for paywall/heavy-JS sites.

Architecture:
    - NetworkGuard: Level-1 retry with UA rotation (5 retries per request)
    - CrawlDefender: 7-strategy cascade for anti-blocking
    - NewsDirectCrawler: Site-level orchestration, RSS→Web→TotalWar fallback
    - Config-driven: reads sources-multiglobal-news.yaml for site definitions

3-Level Retry Architecture:
    Level 1 — NetworkGuard: per-request retry with UA rotation (max 5)
    Level 2 — CrawlDefender: strategy cascade (7 strategies)
    Level 3 — Pipeline retry: caller retries entire site crawl (max 3)

CLI Usage:
    python3 env-scanning/core/news_direct_crawler.py \\
        --sources-config env-scanning/config/sources-multiglobal-news.yaml \\
        --scan-window-start "2026-02-23T00:00:00+00:00" \\
        --scan-window-end "2026-02-24T00:00:00+00:00" \\
        --output env-scanning/wf4-multiglobal-news/raw/daily-crawl-2026-02-24.json

Called by: multiglobal-news-scan-orchestrator (Step 1.2)
"""

import argparse
import hashlib
import json
import logging
import os
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None  # Optional: config can be passed programmatically

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("news_direct_crawler")


# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

CRAWLER_VERSION = "1.0.0"

# Signal ID prefix for WF4
SIGNAL_ID_PREFIX = "news"


# ──────────────────────────────────────────────────────────────────────
# User-Agent Pool (20+ entries for rotation)
# ──────────────────────────────────────────────────────────────────────

UA_POOL = [
    # Chrome on Mac (various versions)
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    # Chrome on Windows (various versions)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    # Chrome on Linux
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    # Firefox on Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
        "Gecko/20100101 Firefox/121.0"
    ),
    # Firefox on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
        "Gecko/20100101 Firefox/121.0"
    ),
    # Firefox on Linux
    (
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    # Safari on Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.2 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.1 Safari/605.1.15"
    ),
    # Edge on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ),
    # Opera on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0"
    ),
    # Chrome on Android
    (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Mobile Safari/537.36"
    ),
    # Safari on iOS
    (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.2 Mobile/15E148 Safari/604.1"
    ),
    # Samsung Browser
    (
        "Mozilla/5.0 (Linux; Android 14; SM-S928B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36"
    ),
    # Brave Browser
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Brave/121"
    ),
    # Vivaldi
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Vivaldi/6.5"
    ),
]


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class BlockEvent:
    """Record of a single block encounter."""
    timestamp: str
    block_type: str
    url: str
    strategy: str
    status_code: int | None = None
    site_name: str = ""


@dataclass
class StrategyRecord:
    """Track per-site strategy success/failure counts."""
    successes: int = 0
    failures: int = 0
    last_block_type: str = ""


@dataclass
class LearnedPattern:
    """Learned crawl pattern for a site, persisted between runs."""
    site_name: str
    best_strategy: str = "default"
    rss_available: bool = True
    last_success_at: str = ""
    success_count: int = 0
    failure_count: int = 0
    avg_articles_per_crawl: float = 0.0


# ──────────────────────────────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────────────────────────────

def validate_required_fields(article: dict) -> bool:
    """Check that an article dict has all required fields for signal conversion.

    Required: title, published_date (or pub_date), content (non-empty), source_url.

    Args:
        article: Dictionary with article data.

    Returns:
        True if all required fields are present and non-empty.
    """
    title = article.get("title", "").strip()
    pub_date = article.get("published_date", article.get("pub_date", "")).strip()
    content = article.get("content", article.get("abstract", "")).strip()
    source_url = article.get("source_url", article.get("url", "")).strip()

    if not title:
        return False
    if not pub_date:
        return False
    if not content:
        return False
    if not source_url:
        return False
    return True


def compute_content_hash(article: dict) -> str:
    """Compute MD5 hash of article title + content for deduplication.

    Uses title + first 500 chars of content to produce a stable hash.

    Args:
        article: Dictionary with 'title' and 'content' keys.

    Returns:
        MD5 hex digest string.
    """
    title = article.get("title", "")
    content = article.get("content", article.get("abstract", ""))
    combined = (title + content[:500]).encode("utf-8")
    return hashlib.md5(combined).hexdigest()


def calculate_crawl_stats(results: dict) -> dict:
    """Calculate aggregate crawl statistics from the results dict.

    Computes per-site, per-language, and per-strategy breakdowns.

    Args:
        results: The full crawl results dict containing 'items' and 'site_results'.

    Returns:
        Dictionary with statistics breakdowns.
    """
    items = results.get("items", [])
    site_results = results.get("site_results", {})

    # Per-site counts
    per_site: dict[str, int] = {}
    for item in items:
        site = item.get("scan_metadata", {}).get("site_name", "unknown")
        per_site[site] = per_site.get(site, 0) + 1

    # Per-language counts
    per_language: dict[str, int] = {}
    for item in items:
        lang = item.get("content", {}).get("language", "unknown")
        per_language[lang] = per_language.get(lang, 0) + 1

    # Per-strategy counts
    per_strategy: dict[str, int] = {}
    for item in items:
        strategy = item.get("scan_metadata", {}).get("crawl_strategy_used", "unknown")
        per_strategy[strategy] = per_strategy.get(strategy, 0) + 1

    # Site success/failure
    sites_succeeded = sum(1 for r in site_results.values() if r.get("status") == "success")
    sites_failed = sum(1 for r in site_results.values() if r.get("status") == "failed")

    return {
        "total_articles": len(items),
        "per_site": per_site,
        "per_language": per_language,
        "per_strategy": per_strategy,
        "sites_attempted": len(site_results),
        "sites_succeeded": sites_succeeded,
        "sites_failed": sites_failed,
    }


def evaluate_retry_decision(
    block_type: str, attempt: int, strategy: str
) -> tuple[bool, str]:
    """Decide whether to retry a failed request or move to the next strategy.

    Args:
        block_type: Type of block encountered (e.g. 'rate_limit', 'captcha').
        attempt: Current attempt number (1-based).
        strategy: Current CrawlDefender strategy name.

    Returns:
        Tuple of (should_retry: bool, reason: str).
    """
    # Non-retryable blocks
    if block_type in ("captcha", "ip_ban"):
        return False, f"{block_type} detected — escalate strategy"

    # Rate limiting: retry with delay
    if block_type == "rate_limit":
        if attempt <= 3:
            return True, "rate_limit — retry with backoff"
        return False, "rate_limit persists — escalate strategy"

    # Timeouts: retry a couple times
    if block_type == "timeout":
        if attempt <= 2:
            return True, "timeout — retry"
        return False, "persistent timeout — escalate strategy"

    # Connection errors: retry once
    if block_type == "connection_blocked":
        if attempt <= 1:
            return True, "connection error — retry once"
        return False, "connection error persists — escalate"

    # Service unavailable: retry with backoff
    if block_type == "service_unavailable":
        if attempt <= 2:
            return True, "503 — retry with backoff"
        return False, "service unavailable persists — escalate"

    # Unknown: retry once
    if attempt <= 1:
        return True, f"unknown block ({block_type}) — retry once"
    return False, f"unknown block ({block_type}) — escalate"


def _lxml_available() -> bool:
    """Check if lxml parser is available for BeautifulSoup."""
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False


def _feedparser_available() -> bool:
    """Check if feedparser library is installed."""
    try:
        import feedparser  # noqa: F401
        return True
    except ImportError:
        return False


def _bs4_available() -> bool:
    """Check if BeautifulSoup4 is installed."""
    try:
        from bs4 import BeautifulSoup  # noqa: F401
        return True
    except ImportError:
        return False


def _parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """Parse an ISO 8601 datetime string to a datetime object.

    Handles common variations including Z suffix and missing timezone.

    Args:
        dt_str: ISO 8601 datetime string.

    Returns:
        datetime object or None if parsing fails.
    """
    if not dt_str:
        return None
    try:
        cleaned = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def _normalize_datetime_to_utc(dt: datetime) -> datetime:
    """Normalize a datetime to UTC. If naive, assume UTC.

    Args:
        dt: datetime object, possibly timezone-aware or naive.

    Returns:
        UTC datetime (timezone-aware).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ──────────────────────────────────────────────────────────────────────
# NetworkGuard — Level 1 Retry with UA Rotation
# ──────────────────────────────────────────────────────────────────────

class NetworkGuard:
    """Level 1 retry mechanism with User-Agent rotation.

    Wraps a request function and retries with a fresh UA on each attempt.
    Provides the innermost retry layer in the 3-level architecture.

    Attributes:
        max_retries: Maximum number of retry attempts (default 5).
    """

    def __init__(self, max_retries: int = 5):
        """Initialize NetworkGuard.

        Args:
            max_retries: Maximum retry attempts per request.
        """
        self.max_retries = max_retries
        self._attempt_count = 0

    def execute(self, request_func: Callable[..., requests.Response]) -> Optional[requests.Response]:
        """Execute a request function with automatic UA-rotation retries.

        On each retry, a new User-Agent is selected from UA_POOL and a brief
        jitter delay is applied.

        Args:
            request_func: Callable that accepts a 'headers' keyword argument
                         and returns a requests.Response.

        Returns:
            The Response object on success, or None if all retries exhausted.
        """
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            self._attempt_count = attempt
            ua = random.choice(UA_POOL)
            headers = {
                "User-Agent": ua,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7,ja;q=0.6",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            try:
                response = request_func(headers=headers)
                if response is not None and response.status_code < 400:
                    return response
                if response is not None:
                    logger.debug(
                        f"[NetworkGuard] HTTP {response.status_code} "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    # Return the response for caller to handle block detection
                    return response
            except requests.exceptions.Timeout:
                logger.debug(
                    f"[NetworkGuard] Timeout (attempt {attempt}/{self.max_retries})"
                )
                last_error = requests.exceptions.Timeout("Request timed out")
            except requests.exceptions.ConnectionError as e:
                logger.debug(
                    f"[NetworkGuard] Connection error (attempt {attempt}/{self.max_retries}): {e}"
                )
                last_error = e
            except Exception as e:
                logger.debug(
                    f"[NetworkGuard] Error (attempt {attempt}/{self.max_retries}): {e}"
                )
                last_error = e

            # Jitter before retry
            if attempt < self.max_retries:
                time.sleep(random.uniform(0.5, 1.5) * attempt)

        if last_error:
            logger.warning(
                f"[NetworkGuard] All {self.max_retries} retries exhausted: {last_error}"
            )
        return None

    @property
    def attempt_count(self) -> int:
        """Number of attempts used in the last execute() call."""
        return self._attempt_count


# ──────────────────────────────────────────────────────────────────────
# CrawlDefender — 7-Strategy Cascade for Anti-Blocking
# ──────────────────────────────────────────────────────────────────────

class CrawlDefender:
    """Block detection and automatic 7-strategy escalation for anti-blocking.

    Strategies (in escalation order):
        1. default          — plain requests with humanized headers
        2. httpx_async      — httpx with HTTP/2 support
        3. rotate_headers   — aggressive header randomization
        4. delay_increase   — exponential backoff between requests
        5. proxy_rotation   — proxy support (if configured)
        6. session_reset    — fresh session per request
        7. browser_emulation — placeholder for Selenium/undetected-chromedriver

    Tracks per-site strategy success/failure to learn optimal approaches.
    """

    STRATEGIES = [
        "default",
        "httpx_async",
        "rotate_headers",
        "delay_increase",
        "proxy_rotation",
        "session_reset",
        "browser_emulation",
    ]

    def __init__(self):
        """Initialize CrawlDefender with default strategy."""
        self.strategy_index: int = 0
        self.current_strategy: str = self.STRATEGIES[0]
        self.block_history: list[BlockEvent] = []
        self.success_count: int = 0
        self.consecutive_successes: int = 0
        # Per-site strategy records: {site_name: {strategy: StrategyRecord}}
        self._site_records: dict[str, dict[str, StrategyRecord]] = {}

    def detect_block_type(self, response: Optional[requests.Response] = None,
                          error: Optional[Exception] = None) -> str:
        """Identify the type of block from a response or exception.

        Args:
            response: The HTTP response (may be None).
            error: An exception that occurred (may be None).

        Returns:
            Block type string: 'none', 'captcha', 'rate_limit', 'ip_ban',
            'timeout', 'connection_blocked', 'empty_response', 'service_unavailable',
            'http_NNN', or 'unknown_error'.
        """
        if error:
            err_str = str(error).lower()
            if "timeout" in err_str:
                return "timeout"
            if "connection" in err_str:
                return "connection_blocked"
            if "ssl" in err_str:
                return "ssl_error"
            return "unknown_error"

        if response is None:
            return "no_response"

        code = response.status_code
        if code == 403:
            return "ip_ban"
        if code == 429:
            return "rate_limit"
        if code == 451:
            return "geo_blocked"
        if code == 503:
            return "service_unavailable"
        if code >= 400:
            return f"http_{code}"

        # Content-based detection
        text = response.text[:5000].lower()
        if "captcha" in text or "recaptcha" in text or "보안문자" in text:
            return "captcha"
        if "access denied" in text or "403 forbidden" in text:
            return "ip_ban"
        if "rate limit" in text or "too many requests" in text:
            return "rate_limit"
        if len(response.text) < 200:
            return "empty_response"

        return "none"

    def get_next_strategy(self, current: str, block_type: str) -> str:
        """Determine the next strategy based on block type and current strategy.

        For certain block types, specific strategies are preferred:
        - captcha → browser_emulation
        - rate_limit → delay_increase
        - ip_ban → proxy_rotation or session_reset

        Args:
            current: Current strategy name.
            block_type: Type of block encountered.

        Returns:
            Next strategy name.
        """
        # Direct mapping for known block types
        if block_type == "captcha":
            return "browser_emulation"
        if block_type == "rate_limit" and current != "delay_increase":
            return "delay_increase"
        if block_type == "ip_ban" and current not in ("proxy_rotation", "session_reset"):
            return "proxy_rotation"

        # Default: advance linearly
        try:
            idx = self.STRATEGIES.index(current)
        except ValueError:
            idx = 0
        next_idx = (idx + 1) % len(self.STRATEGIES)
        return self.STRATEGIES[next_idx]

    def escalate(self, block_type: str = "") -> str:
        """Move to the next strategy in the cascade.

        Uses block_type to make intelligent strategy selection when possible.

        Args:
            block_type: Type of block that triggered escalation.

        Returns:
            The new current strategy name.
        """
        new_strategy = self.get_next_strategy(self.current_strategy, block_type)
        self.strategy_index = self.STRATEGIES.index(new_strategy)
        self.current_strategy = new_strategy
        self.consecutive_successes = 0
        logger.info(f"[DEFENDER] Strategy escalated → {self.current_strategy}")
        return self.current_strategy

    def record_success(self, site: str, strategy: str) -> None:
        """Record a successful request for a site/strategy pair.

        After 5 consecutive successes, resets to the fastest strategy.

        Args:
            site: Site short name.
            strategy: Strategy that succeeded.
        """
        self.success_count += 1
        self.consecutive_successes += 1

        # Track per-site
        if site not in self._site_records:
            self._site_records[site] = {}
        if strategy not in self._site_records[site]:
            self._site_records[site][strategy] = StrategyRecord()
        self._site_records[site][strategy].successes += 1

        # Reset to default after 5 consecutive successes
        if self.consecutive_successes >= 5 and self.strategy_index > 0:
            self.strategy_index = 0
            self.current_strategy = self.STRATEGIES[0]
            logger.info("[DEFENDER] 5 consecutive successes → resetting to default")

    def record_failure(self, site: str, strategy: str, block_type: str) -> None:
        """Record a failed request for a site/strategy pair.

        Args:
            site: Site short name.
            strategy: Strategy that failed.
            block_type: Type of block encountered.
        """
        if site not in self._site_records:
            self._site_records[site] = {}
        if strategy not in self._site_records[site]:
            self._site_records[site][strategy] = StrategyRecord()
        self._site_records[site][strategy].failures += 1
        self._site_records[site][strategy].last_block_type = block_type

    def record_block(self, block_type: str, url: str,
                     status_code: int | None = None, site_name: str = "") -> None:
        """Record a block event in the history.

        Args:
            block_type: Type of block.
            url: URL that was blocked.
            status_code: HTTP status code if available.
            site_name: Short name of the site.
        """
        self.block_history.append(BlockEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            block_type=block_type,
            url=url,
            strategy=self.current_strategy,
            status_code=status_code,
            site_name=site_name,
        ))

    def get_headers(self, site_language: str = "en") -> dict:
        """Generate humanized browser headers for the current strategy.

        Args:
            site_language: Primary language of the target site (e.g. 'ko', 'en', 'ja').

        Returns:
            Dictionary of HTTP headers.
        """
        ua = random.choice(UA_POOL)

        # Language-aware Accept-Language
        lang_map = {
            "ko": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "ja": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
            "zh": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "de": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "fr": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "en": "en-US,en;q=0.9,ko-KR;q=0.5",
        }
        accept_lang = lang_map.get(site_language, lang_map["en"])

        headers = {
            "User-Agent": ua,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": accept_lang,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        # Strategy-specific variations
        if self.current_strategy == "rotate_headers":
            # Aggressive randomization
            if random.random() > 0.4:
                headers["DNT"] = "1"
            if random.random() > 0.5:
                # Randomize accept-language variants
                extra_langs = [
                    accept_lang,
                    "en-US,en;q=0.9",
                    "en-GB,en;q=0.9,en-US;q=0.8",
                ]
                headers["Accept-Language"] = random.choice(extra_langs)
            # Sometimes drop Sec-Fetch headers (older browsers)
            if random.random() > 0.7:
                for key in ["Sec-Fetch-Dest", "Sec-Fetch-Mode", "Sec-Fetch-Site", "Sec-Fetch-User"]:
                    headers.pop(key, None)
        else:
            # Default: add a plausible referer
            headers["Referer"] = "https://www.google.com/"

        return headers

    def get_best_strategy_for_site(self, site: str) -> str:
        """Return the strategy with the highest success rate for a site.

        Args:
            site: Site short name.

        Returns:
            Best strategy name, or 'default' if no data.
        """
        records = self._site_records.get(site, {})
        if not records:
            return "default"

        best_strategy = "default"
        best_ratio = -1.0
        for strategy, record in records.items():
            total = record.successes + record.failures
            if total == 0:
                continue
            ratio = record.successes / total
            if ratio > best_ratio:
                best_ratio = ratio
                best_strategy = strategy
        return best_strategy

    def reset_for_site(self, site: str) -> None:
        """Reset strategy to the best known for a given site.

        Args:
            site: Site short name.
        """
        best = self.get_best_strategy_for_site(site)
        try:
            self.strategy_index = self.STRATEGIES.index(best)
        except ValueError:
            self.strategy_index = 0
        self.current_strategy = self.STRATEGIES[self.strategy_index]
        self.consecutive_successes = 0

    def summary(self) -> dict:
        """Return defense summary for output JSON.

        Returns:
            Dictionary with block counts, strategy usage, and per-site records.
        """
        block_type_counts: dict[str, int] = {}
        strategy_counts: dict[str, int] = {}
        for event in self.block_history:
            block_type_counts[event.block_type] = block_type_counts.get(event.block_type, 0) + 1
            strategy_counts[event.strategy] = strategy_counts.get(event.strategy, 0) + 1

        return {
            "total_blocks": len(self.block_history),
            "total_successes": self.success_count,
            "blocks_by_type": block_type_counts,
            "blocks_by_strategy": strategy_counts,
            "final_strategy": self.current_strategy,
        }


# ──────────────────────────────────────────────────────────────────────
# Learned Patterns — Persistence Between Runs
# ──────────────────────────────────────────────────────────────────────

def load_learned_patterns(path: str) -> dict[str, LearnedPattern]:
    """Load learned crawl patterns from JSON file.

    Args:
        path: File path to learned-crawl-patterns.json.

    Returns:
        Dictionary mapping site_name to LearnedPattern.
    """
    p = Path(path)
    if not p.exists():
        logger.info(f"[LEARN] No learned patterns file: {path}")
        return {}

    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        patterns: dict[str, LearnedPattern] = {}
        for site_name, vals in data.items():
            patterns[site_name] = LearnedPattern(
                site_name=site_name,
                best_strategy=vals.get("best_strategy", "default"),
                rss_available=vals.get("rss_available", True),
                last_success_at=vals.get("last_success_at", ""),
                success_count=vals.get("success_count", 0),
                failure_count=vals.get("failure_count", 0),
                avg_articles_per_crawl=vals.get("avg_articles_per_crawl", 0.0),
            )
        logger.info(f"[LEARN] Loaded patterns for {len(patterns)} sites")
        return patterns
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"[LEARN] Error loading patterns: {e}")
        return {}


def save_learned_patterns(patterns: dict[str, LearnedPattern], path: str) -> None:
    """Save learned crawl patterns to JSON file.

    Args:
        patterns: Dictionary of site patterns to save.
        path: File path for output.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    for site_name, pattern in patterns.items():
        data[site_name] = {
            "best_strategy": pattern.best_strategy,
            "rss_available": pattern.rss_available,
            "last_success_at": pattern.last_success_at,
            "success_count": pattern.success_count,
            "failure_count": pattern.failure_count,
            "avg_articles_per_crawl": pattern.avg_articles_per_crawl,
        }

    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"[LEARN] Saved patterns for {len(data)} sites → {path}")


# ──────────────────────────────────────────────────────────────────────
# NewsDirectCrawler — Main Orchestrator
# ──────────────────────────────────────────────────────────────────────

class NewsDirectCrawler:
    """Main orchestrator for crawling 43+ individual news sites.

    Implements RSS-first crawling with web-crawl and Total War fallbacks.
    Produces standard signal format output for the WF4 pipeline.

    The 3-level retry architecture:
        - Level 1 (NetworkGuard): Per-HTTP-request retry with UA rotation (5x)
        - Level 2 (CrawlDefender): Strategy cascade on block detection (7 strategies)
        - Level 3 (Pipeline): Entire site crawl retry (3x)

    Attributes:
        sources_config_path: Path to the YAML config with site definitions.
        scan_window_start: Start of the temporal scan window (ISO 8601).
        scan_window_end: End of the temporal scan window (ISO 8601).
    """

    # Default delay parameters
    DEFAULT_MIN_DELAY: float = 1.5
    DEFAULT_MAX_DELAY: float = 4.0
    DEFAULT_SITE_DELAY: float = 3.0
    DEFAULT_PIPELINE_RETRIES: int = 3

    def __init__(
        self,
        sources_config_path: str,
        scan_window_start: Optional[str] = None,
        scan_window_end: Optional[str] = None,
    ):
        """Initialize NewsDirectCrawler.

        Args:
            sources_config_path: Path to sources-multiglobal-news.yaml.
            scan_window_start: ISO 8601 start of scan window. If None, defaults
                              to now - 24 hours.
            scan_window_end: ISO 8601 end of scan window. If None, defaults to now.
        """
        self.sources_config_path = sources_config_path
        self.sites: list[dict] = []
        self.defender = CrawlDefender()
        self.network_guard = NetworkGuard(max_retries=5)
        self.learned_patterns: dict[str, LearnedPattern] = {}
        self.learned_patterns_path: str = ""

        # Scan window
        if scan_window_end:
            self.scan_window_end = _parse_iso_datetime(scan_window_end) or datetime.now(timezone.utc)
        else:
            self.scan_window_end = datetime.now(timezone.utc)

        if scan_window_start:
            self.scan_window_start = _parse_iso_datetime(scan_window_start) or (
                self.scan_window_end - timedelta(hours=24)
            )
        else:
            self.scan_window_start = self.scan_window_end - timedelta(hours=24)

        # Content hash set for intra-session dedup
        self._seen_hashes: set[str] = set()

        # Track per-site results
        self._site_results: dict[str, dict] = {}

        # Noise filter counts
        self._noise_filtered: int = 0

        # Failed URLs
        self._failed_urls: list[str] = []

        # Load config
        self._load_sources_config()

    def _load_sources_config(self) -> None:
        """Load site definitions from the sources config YAML.

        Populates self.sites with site configuration dictionaries.
        Also loads learned patterns if a path is configured.
        """
        if yaml is None:
            logger.warning("[CONFIG] PyYAML not available — no sites loaded from config")
            return

        path = Path(self.sources_config_path)
        if not path.exists():
            logger.warning(f"[CONFIG] Config not found: {self.sources_config_path}")
            return

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.sites = data.get("sources", [])
        logger.info(f"[CONFIG] Loaded {len(self.sites)} site definitions")

        # Extract learned patterns path if specified
        crawl_settings = data.get("crawl_settings", {})
        self.learned_patterns_path = crawl_settings.get(
            "learned_patterns_path",
            "env-scanning/wf4-multiglobal-news/logs/learned-crawl-patterns.json",
        )

        # Load learned patterns
        if self.learned_patterns_path:
            self.learned_patterns = load_learned_patterns(self.learned_patterns_path)

        # Apply crawl settings
        self.DEFAULT_MIN_DELAY = crawl_settings.get("min_delay", self.DEFAULT_MIN_DELAY)
        self.DEFAULT_MAX_DELAY = crawl_settings.get("max_delay", self.DEFAULT_MAX_DELAY)
        self.DEFAULT_SITE_DELAY = crawl_settings.get("site_delay", self.DEFAULT_SITE_DELAY)

    # ── HTTP Request with Defender + NetworkGuard ──

    def _request(self, url: str, site_name: str = "",
                 site_language: str = "en") -> Optional[requests.Response]:
        """Make an HTTP request using CrawlDefender strategy and NetworkGuard retries.

        This is the unified request method that layers Level 1 (NetworkGuard)
        retry inside Level 2 (CrawlDefender) strategy rotation.

        Args:
            url: Target URL.
            site_name: Short name of the site (for logging and pattern tracking).
            site_language: Language code for Accept-Language header.

        Returns:
            Response object on success, or None on failure.
        """
        max_strategy_attempts = len(CrawlDefender.STRATEGIES)

        for strategy_attempt in range(max_strategy_attempts):
            strategy = self.defender.current_strategy
            headers = self.defender.get_headers(site_language)

            # Use NetworkGuard for the actual request with UA rotation
            def make_request(headers: dict = headers) -> Optional[requests.Response]:
                """Inner request function for NetworkGuard."""
                if strategy == "httpx_async":
                    try:
                        import httpx
                        resp = httpx.get(
                            url, headers=headers, timeout=15.0,
                            follow_redirects=True,
                        )
                        # Convert to requests.Response interface
                        mock_resp = requests.Response()
                        mock_resp.status_code = resp.status_code
                        mock_resp._content = resp.content
                        mock_resp.encoding = resp.encoding or "utf-8"
                        mock_resp.headers.update(dict(resp.headers))
                        return mock_resp
                    except ImportError:
                        return requests.get(url, headers=headers, timeout=15)
                elif strategy == "session_reset":
                    session = requests.Session()
                    try:
                        return session.get(url, headers=headers, timeout=15)
                    finally:
                        session.close()
                elif strategy == "delay_increase":
                    delay = random.uniform(3.0, 8.0)
                    time.sleep(delay)
                    return requests.get(url, headers=headers, timeout=20)
                elif strategy == "browser_emulation":
                    # Stub: falls back to requests with browser-like headers
                    logger.debug(
                        f"[DEFENDER] browser_emulation strategy — using requests fallback "
                        f"(actual browser automation deferred)"
                    )
                    headers["Sec-CH-UA"] = (
                        '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"'
                    )
                    headers["Sec-CH-UA-Mobile"] = "?0"
                    headers["Sec-CH-UA-Platform"] = '"macOS"'
                    return requests.get(url, headers=headers, timeout=20)
                else:
                    # default, rotate_headers, proxy_rotation
                    return requests.get(url, headers=headers, timeout=15)

            response = self.network_guard.execute(make_request)

            if response is None:
                # NetworkGuard exhausted all retries with no response
                self.defender.record_block("no_response", url, site_name=site_name)
                self.defender.record_failure(site_name, strategy, "no_response")
                self.defender.escalate("no_response")
                continue

            block_type = self.defender.detect_block_type(response=response)

            if block_type == "none":
                self.defender.record_success(site_name, strategy)
                return response

            # Blocked — record and decide
            logger.warning(
                f"[BLOCK] {block_type} (HTTP {response.status_code}) "
                f"site={site_name} strategy={strategy} "
                f"attempt={strategy_attempt + 1}/{max_strategy_attempts}"
            )
            self.defender.record_block(
                block_type, url, response.status_code, site_name=site_name,
            )
            self.defender.record_failure(site_name, strategy, block_type)

            should_retry, reason = evaluate_retry_decision(
                block_type, strategy_attempt + 1, strategy,
            )
            if not should_retry:
                self.defender.escalate(block_type)

            self._jitter_delay()

        logger.error(f"[FAIL] All strategies exhausted for: {url}")
        self._failed_urls.append(url)
        return None

    def _jitter_delay(self) -> None:
        """Apply a random delay with jitter between requests."""
        delay = random.uniform(self.DEFAULT_MIN_DELAY, self.DEFAULT_MAX_DELAY)
        time.sleep(delay)

    # ── RSS Crawling ──

    def _try_rss(self, site_config: dict) -> list[dict]:
        """Attempt to crawl a site via its RSS feed.

        Tries feedparser first if available; falls back to manual XML parsing.

        Args:
            site_config: Site configuration dict with 'rss_url', 'name', etc.

        Returns:
            List of article dicts in intermediate format, or empty list on failure.
        """
        rss_url = site_config.get("rss_url", "")
        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        site_language = site_config.get("language", "en")

        if not rss_url:
            logger.debug(f"[RSS] No RSS URL configured for {site_name}")
            return []

        # Check learned patterns — skip RSS if known to be unavailable
        learned = self.learned_patterns.get(site_name)
        if learned and not learned.rss_available:
            logger.debug(f"[RSS] Skipping RSS for {site_name} — learned: rss_available=False")
            return []

        logger.info(f"[RSS] Attempting RSS feed: {site_name} → {rss_url}")

        response = self._request(rss_url, site_name=site_name, site_language=site_language)
        if not response:
            # Update learned patterns
            if site_name in self.learned_patterns:
                self.learned_patterns[site_name].rss_available = False
            return []

        articles = []

        # Try feedparser first
        if _feedparser_available():
            articles = self._parse_rss_feedparser(response.content, site_config)
        else:
            # Fallback: manual XML parsing
            articles = self._parse_rss_xml(response.text, site_config)

        if articles:
            logger.info(f"[RSS] {site_name}: {len(articles)} articles from RSS")
            # Update learned patterns on success
            if site_name not in self.learned_patterns:
                self.learned_patterns[site_name] = LearnedPattern(site_name=site_name)
            self.learned_patterns[site_name].rss_available = True
        else:
            logger.info(f"[RSS] {site_name}: No articles from RSS feed")
            if site_name in self.learned_patterns:
                self.learned_patterns[site_name].rss_available = False

        return articles

    def _parse_rss_feedparser(self, content: bytes, site_config: dict) -> list[dict]:
        """Parse RSS feed using feedparser library.

        Args:
            content: Raw feed content bytes.
            site_config: Site configuration dict.

        Returns:
            List of article dicts.
        """
        import feedparser

        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        site_language = site_config.get("language", "en")
        site_type = site_config.get("type", "news")

        feed = feedparser.parse(content)
        articles = []

        for entry in feed.entries:
            try:
                title = entry.get("title", "").strip()
                if not title:
                    continue

                link = entry.get("link", "")
                if not link:
                    continue

                # Extract publication date
                pub_date = ""
                for date_field in ("published", "updated", "created"):
                    raw = entry.get(date_field, "")
                    if raw:
                        pub_date = raw
                        break
                # Try parsed date
                if not pub_date:
                    for date_parsed_field in ("published_parsed", "updated_parsed"):
                        parsed = entry.get(date_parsed_field)
                        if parsed:
                            try:
                                from time import mktime
                                dt = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
                                pub_date = dt.isoformat()
                            except (TypeError, ValueError, OverflowError):
                                pass
                            break

                # Extract content/summary
                abstract = ""
                if "summary" in entry:
                    abstract = entry.summary
                elif "content" in entry and entry.content:
                    abstract = entry.content[0].get("value", "")
                elif "description" in entry:
                    abstract = entry.description

                # Strip HTML tags from abstract
                abstract = self._strip_html(abstract)

                # Keywords from categories/tags
                keywords = []
                for tag in entry.get("tags", []):
                    term = tag.get("term", "")
                    if term:
                        keywords.append(term)

                # Noise filter
                if self._is_noise(title):
                    self._noise_filtered += 1
                    continue

                article = {
                    "title": title,
                    "url": link,
                    "published_date": pub_date,
                    "content": abstract,
                    "keywords": keywords,
                    "site_name": site_name,
                    "site_type": site_type,
                    "language": site_language,
                    "crawl_strategy": "rss",
                }
                articles.append(article)

            except Exception as e:
                logger.debug(f"[RSS] Parse error in entry: {e}")
                continue

        return articles

    def _parse_rss_xml(self, xml_text: str, site_config: dict) -> list[dict]:
        """Parse RSS/Atom feed using stdlib XML parsing (fallback).

        Handles both RSS 2.0 (<item>) and Atom (<entry>) formats.

        Args:
            xml_text: Raw XML text of the feed.
            site_config: Site configuration dict.

        Returns:
            List of article dicts.
        """
        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        site_language = site_config.get("language", "en")
        site_type = site_config.get("type", "news")

        articles = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning(f"[RSS-XML] Parse error for {site_name}: {e}")
            return []

        # Detect RSS vs Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item")  # RSS 2.0
        if not items:
            items = root.findall(".//atom:entry", ns)  # Atom

        for item in items:
            try:
                # Title
                title_elem = item.find("title") or item.find("atom:title", ns)
                title = (title_elem.text or "").strip() if title_elem is not None else ""
                if not title:
                    continue

                # Link
                link_elem = item.find("link") or item.find("atom:link", ns)
                link = ""
                if link_elem is not None:
                    link = link_elem.text or link_elem.get("href", "")
                link = link.strip()
                if not link:
                    continue

                # Publication date
                pub_date = ""
                for tag in ("pubDate", "published", "updated", "dc:date",
                            "atom:published", "atom:updated"):
                    date_elem = item.find(tag) if ":" not in tag else item.find(tag, ns)
                    if date_elem is not None and date_elem.text:
                        pub_date = date_elem.text.strip()
                        break

                # Description/content
                abstract = ""
                for tag in ("description", "content:encoded", "atom:content", "atom:summary"):
                    content_elem = item.find(tag) if ":" not in tag else item.find(tag, ns)
                    if content_elem is not None and content_elem.text:
                        abstract = self._strip_html(content_elem.text.strip())
                        break

                # Noise filter
                if self._is_noise(title):
                    self._noise_filtered += 1
                    continue

                article = {
                    "title": title,
                    "url": link,
                    "published_date": pub_date,
                    "content": abstract,
                    "keywords": [],
                    "site_name": site_name,
                    "site_type": site_type,
                    "language": site_language,
                    "crawl_strategy": "rss",
                }
                articles.append(article)

            except Exception as e:
                logger.debug(f"[RSS-XML] Parse error in item: {e}")
                continue

        return articles

    # ── Web Crawling (requests + BeautifulSoup) ──

    def _try_web_crawl(self, site_config: dict) -> list[dict]:
        """Crawl a site using requests + BeautifulSoup with CSS selectors.

        Uses site-specific selectors from the config. Falls back to generic
        heuristics if specific selectors are not provided.

        Args:
            site_config: Site configuration dict with 'url', 'selectors', etc.

        Returns:
            List of article dicts.
        """
        if not _bs4_available():
            logger.error("[WEB] BeautifulSoup4 not installed — cannot web crawl")
            return []

        from bs4 import BeautifulSoup

        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        site_url = site_config.get("url", "")
        site_language = site_config.get("language", "en")
        site_type = site_config.get("type", "news")
        selectors = site_config.get("selectors", {})

        if not site_url:
            logger.warning(f"[WEB] No URL configured for {site_name}")
            return []

        logger.info(f"[WEB] Attempting web crawl: {site_name} → {site_url}")

        response = self._request(site_url, site_name=site_name, site_language=site_language)
        if not response:
            return []

        parser = "lxml" if _lxml_available() else "html.parser"
        soup = BeautifulSoup(response.text, parser)

        articles = []

        # Use configured selectors or generic fallbacks
        article_selector = selectors.get(
            "article_list",
            "article, .article-item, .news-item, .story-item, "
            ".headline-item, li.article, div.article",
        )
        title_selector = selectors.get(
            "title",
            "h2 a, h3 a, .headline a, .title a, a.article-title, a.story-link",
        )
        time_selector = selectors.get(
            "time",
            "time, .date, .timestamp, .pub-date, .article-date, span.time",
        )
        summary_selector = selectors.get(
            "summary",
            ".summary, .excerpt, .description, .article-summary, p.lead",
        )

        # Strategy 1: Find article containers
        items = soup.select(article_selector)
        if items:
            for item in items:
                try:
                    article = self._extract_article_from_container(
                        item, title_selector, time_selector, summary_selector,
                        site_name, site_url, site_type, site_language,
                    )
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"[WEB] Parse error in article container: {e}")
                    continue

        # Strategy 2: If no containers found, try direct headline links
        if not articles:
            headline_links = soup.select(title_selector)
            for link in headline_links:
                try:
                    title = link.get_text(strip=True)
                    href = link.get("href", "")
                    if not title or not href:
                        continue
                    # Resolve relative URLs
                    if href.startswith("/"):
                        href = urljoin(site_url, href)
                    elif not href.startswith("http"):
                        href = urljoin(site_url, href)

                    if self._is_noise(title):
                        self._noise_filtered += 1
                        continue

                    article = {
                        "title": title,
                        "url": href,
                        "published_date": "",
                        "content": "",
                        "keywords": [],
                        "site_name": site_name,
                        "site_type": site_type,
                        "language": site_language,
                        "crawl_strategy": "web_crawl",
                    }
                    articles.append(article)
                except Exception as e:
                    logger.debug(f"[WEB] Error extracting headline link: {e}")
                    continue

        logger.info(f"[WEB] {site_name}: {len(articles)} articles from web crawl")
        return articles

    def _extract_article_from_container(
        self,
        container,
        title_selector: str,
        time_selector: str,
        summary_selector: str,
        site_name: str,
        site_url: str,
        site_type: str,
        site_language: str,
    ) -> Optional[dict]:
        """Extract article data from a BS4 container element.

        Args:
            container: BeautifulSoup element containing the article.
            title_selector: CSS selector for title.
            time_selector: CSS selector for publication time.
            summary_selector: CSS selector for summary/description.
            site_name: Short name of the site.
            site_url: Base URL for resolving relative links.
            site_type: Type of the news source.
            site_language: Language code.

        Returns:
            Article dict or None if extraction fails.
        """
        # Title and URL
        title_elem = container.select_one(title_selector)
        if not title_elem:
            # Fallback: any anchor with substantial text
            for a_tag in container.find_all("a"):
                text = a_tag.get_text(strip=True)
                if len(text) > 15:
                    title_elem = a_tag
                    break
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        href = title_elem.get("href", "")
        if not title or not href:
            return None

        # Resolve relative URLs
        if href.startswith("/"):
            href = urljoin(site_url, href)
        elif not href.startswith("http"):
            href = urljoin(site_url, href)

        # Noise filter
        if self._is_noise(title):
            self._noise_filtered += 1
            return None

        # Publication time
        pub_date = ""
        time_elem = container.select_one(time_selector)
        if time_elem:
            pub_date = time_elem.get("datetime", "") or time_elem.get_text(strip=True)

        # Summary
        summary = ""
        summary_elem = container.select_one(summary_selector)
        if summary_elem:
            summary = summary_elem.get_text(strip=True)

        return {
            "title": title,
            "url": href,
            "published_date": pub_date,
            "content": summary,
            "keywords": [],
            "site_name": site_name,
            "site_type": site_type,
            "language": site_language,
            "crawl_strategy": "web_crawl",
        }

    # ── Total War — Browser-Based Crawling (Stub) ──

    def _try_total_war(self, site_config: dict) -> list[dict]:
        """Attempt browser-based crawling for paywall/heavy-JS sites.

        This is a stub implementation. Actual browser automation via
        undetected-chromedriver or Playwright is deferred to a future version.

        Currently logs a warning and returns an empty list.

        Args:
            site_config: Site configuration dict.

        Returns:
            Empty list (stub). Future: list of article dicts.
        """
        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        logger.warning(
            f"[TOTAL_WAR] Browser-based crawling not yet implemented for {site_name}. "
            f"Requires undetected-chromedriver or Playwright integration. "
            f"Skipping this site."
        )

        # Future implementation would:
        # 1. Launch headless browser (undetected-chromedriver)
        # 2. Navigate to site URL
        # 3. Wait for JS rendering
        # 4. Extract article elements from rendered DOM
        # 5. Handle cookie consent dialogs
        # 6. Handle paywall detection and bypass attempts

        return []

    # ── Single Site Crawl ──

    def crawl_single_site(self, site_config: dict) -> list[dict]:
        """Crawl a single site using RSS → Web → TotalWar fallback cascade.

        Implements Level 3 (Pipeline) retry: retries the entire site crawl
        up to DEFAULT_PIPELINE_RETRIES times.

        Args:
            site_config: Site configuration dict with at minimum 'name' and
                        either 'rss_url' or 'url'.

        Returns:
            List of article dicts in intermediate format.
        """
        site_name = site_config.get("short_name", site_config.get("name", "unknown"))
        logger.info(f"[SITE] ── Starting crawl: {site_name} ──")

        # Reset defender strategy for this site
        self.defender.reset_for_site(site_name)

        for pipeline_attempt in range(1, self.DEFAULT_PIPELINE_RETRIES + 1):
            articles = []

            # Step 1: Try RSS first
            articles = self._try_rss(site_config)
            if articles:
                self._site_results[site_name] = {
                    "status": "success",
                    "strategy": "rss",
                    "article_count": len(articles),
                    "pipeline_attempt": pipeline_attempt,
                }
                return articles

            # Step 2: Try web crawling
            articles = self._try_web_crawl(site_config)
            if articles:
                self._site_results[site_name] = {
                    "status": "success",
                    "strategy": "web_crawl",
                    "article_count": len(articles),
                    "pipeline_attempt": pipeline_attempt,
                }
                return articles

            # Step 3: Try Total War (browser-based — stub)
            requires_browser = site_config.get("requires_browser", False)
            if requires_browser:
                articles = self._try_total_war(site_config)
                if articles:
                    self._site_results[site_name] = {
                        "status": "success",
                        "strategy": "total_war",
                        "article_count": len(articles),
                        "pipeline_attempt": pipeline_attempt,
                    }
                    return articles

            # All methods failed — pipeline retry
            if pipeline_attempt < self.DEFAULT_PIPELINE_RETRIES:
                logger.warning(
                    f"[SITE] {site_name}: Pipeline retry {pipeline_attempt}/{self.DEFAULT_PIPELINE_RETRIES}"
                )
                # Back off before retrying
                time.sleep(random.uniform(2.0, 5.0) * pipeline_attempt)

        # All pipeline retries exhausted
        logger.error(f"[SITE] {site_name}: All crawl methods failed after {self.DEFAULT_PIPELINE_RETRIES} attempts")
        self._site_results[site_name] = {
            "status": "failed",
            "strategy": "none",
            "article_count": 0,
            "pipeline_attempt": self.DEFAULT_PIPELINE_RETRIES,
        }

        # Update learned patterns
        if site_name not in self.learned_patterns:
            self.learned_patterns[site_name] = LearnedPattern(site_name=site_name)
        self.learned_patterns[site_name].failure_count += 1

        return []

    # ── Full Crawl Orchestration ──

    def crawl_all_sites(self) -> dict:
        """Crawl all configured sites and return standard signal format output.

        Iterates through all sites in self.sites, applies per-session dedup,
        temporal filtering, and produces the final structured result.

        Returns:
            Dictionary with scan_metadata, crawl_stats, defense_summary, items,
            site_results, and failed_urls.
        """
        start_time = datetime.now(timezone.utc)
        scan_date = start_time.strftime("%Y-%m-%d")
        scan_date_compact = scan_date.replace("-", "")

        logger.info(f"[START] Multi-Global News crawl starting — {len(self.sites)} sites")
        logger.info(
            f"[WINDOW] Scan window: {self.scan_window_start.isoformat()} "
            f"→ {self.scan_window_end.isoformat()}"
        )

        all_articles: list[dict] = []

        for idx, site_config in enumerate(self.sites, start=1):
            site_name = site_config.get("short_name", site_config.get("name", f"site_{idx}"))
            enabled = site_config.get("enabled", True)

            if not enabled:
                logger.info(f"[SKIP] {site_name} — disabled in config")
                self._site_results[site_name] = {
                    "status": "skipped",
                    "strategy": "none",
                    "article_count": 0,
                    "pipeline_attempt": 0,
                }
                continue

            logger.info(f"[PROGRESS] Site {idx}/{len(self.sites)}: {site_name}")

            articles = self.crawl_single_site(site_config)
            all_articles.extend(articles)

            # Inter-site delay
            if idx < len(self.sites):
                delay = random.uniform(
                    self.DEFAULT_SITE_DELAY * 0.8,
                    self.DEFAULT_SITE_DELAY * 1.2,
                )
                time.sleep(delay)

        # ── Post-processing ──

        # Content-hash dedup within session
        deduped_articles = []
        dup_count = 0
        for article in all_articles:
            content_hash = compute_content_hash(article)
            if content_hash in self._seen_hashes:
                dup_count += 1
                continue
            self._seen_hashes.add(content_hash)
            article["content_hash"] = content_hash
            deduped_articles.append(article)

        if dup_count > 0:
            logger.info(f"[DEDUP] Removed {dup_count} duplicate articles within session")

        # Temporal filtering
        tc_removed = 0
        tc_kept = []
        tolerance = timedelta(minutes=30)
        effective_start = self.scan_window_start - tolerance

        for article in deduped_articles:
            pub_date_str = article.get("published_date", "")
            keep = True

            if pub_date_str:
                pub_dt = _parse_iso_datetime(pub_date_str)
                if pub_dt:
                    pub_dt_utc = _normalize_datetime_to_utc(pub_dt)
                    ws = _normalize_datetime_to_utc(effective_start)
                    we = _normalize_datetime_to_utc(self.scan_window_end)
                    if pub_dt_utc < ws or pub_dt_utc > we:
                        keep = False
                        tc_removed += 1

            if keep:
                tc_kept.append(article)

        if tc_removed > 0:
            logger.info(
                f"[TC] Temporal filter: {tc_removed} articles outside window, "
                f"{len(tc_kept)} kept"
            )

        # ── Convert to standard signal format ──

        end_time = datetime.now(timezone.utc)
        exec_id = (
            f"wf4-crawl-{scan_date}-"
            f"{start_time.strftime('%H-%M-%S')}-"
            f"{hashlib.md5(start_time.isoformat().encode()).hexdigest()[:4]}"
        )

        items = []
        # Group by site for sequential numbering
        site_counters: dict[str, int] = {}
        for article in tc_kept:
            site_name = article.get("site_name", "unknown")
            site_short = self._make_short_name(site_name)
            site_counters[site_short] = site_counters.get(site_short, 0) + 1
            seq = site_counters[site_short]

            signal = self._article_to_signal(
                article=article,
                signal_idx=seq,
                scan_date_compact=scan_date_compact,
                site_short=site_short,
                exec_id=exec_id,
                start_time=start_time,
                end_time=end_time,
            )
            items.append(signal)

        # Collect actual sources scanned
        actual_sources = [
            name for name, result in self._site_results.items()
            if result.get("status") == "success"
        ]

        # Update execution proof
        total_web_requests = self.defender.success_count + len(self.defender.block_history)

        # SNR
        total_raw = len(all_articles) + self._noise_filtered
        snr = len(items) / total_raw if total_raw > 0 else 0.0

        result = {
            "scan_metadata": {
                "date": scan_date,
                "workflow": "wf4-multiglobal-news",
                "source": "MultiGlobalNews",
                "total_items": len(items),
                "execution_time": round((end_time - start_time).total_seconds(), 1),
                "execution_proof": {
                    "execution_id": exec_id,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                    "actual_api_calls": {
                        "web_requests": total_web_requests,
                    },
                    "actual_sources_scanned": actual_sources,
                    "file_created_at": end_time.isoformat(),
                },
                "crawler_version": CRAWLER_VERSION,
                "scan_window": {
                    "start": self.scan_window_start.isoformat(),
                    "end": self.scan_window_end.isoformat(),
                },
            },
            "crawl_stats": {
                "total_articles": len(items),
                "total_raw_before_filters": total_raw,
                "noise_filtered": self._noise_filtered,
                "duplicates_removed": dup_count,
                "temporal_filtered": tc_removed,
                "signal_to_noise_ratio": round(snr, 4),
                "sites_configured": len(self.sites),
                "sites_crawled": len([
                    r for r in self._site_results.values() if r.get("status") == "success"
                ]),
                "sites_failed": len([
                    r for r in self._site_results.values() if r.get("status") == "failed"
                ]),
                "sites_skipped": len([
                    r for r in self._site_results.values() if r.get("status") == "skipped"
                ]),
                "failed_urls_count": len(self._failed_urls),
            },
            "defense_summary": self.defender.summary(),
            "site_results": self._site_results,
            "items": items,
            "failed_urls": self._failed_urls,
        }

        # Update and save learned patterns
        for site_name, site_result in self._site_results.items():
            if site_result.get("status") == "success":
                if site_name not in self.learned_patterns:
                    self.learned_patterns[site_name] = LearnedPattern(site_name=site_name)
                pattern = self.learned_patterns[site_name]
                pattern.best_strategy = site_result.get("strategy", "default")
                pattern.last_success_at = end_time.isoformat()
                pattern.success_count += 1
                # Running average
                count = site_result.get("article_count", 0)
                total = pattern.success_count
                if total <= 1:
                    pattern.avg_articles_per_crawl = float(count)
                else:
                    pattern.avg_articles_per_crawl = (
                        pattern.avg_articles_per_crawl * (total - 1) + count
                    ) / total

        if self.learned_patterns_path:
            save_learned_patterns(self.learned_patterns, self.learned_patterns_path)

        # Final stats
        stats = calculate_crawl_stats(result)
        logger.info(
            f"[DONE] Crawl complete: {len(items)} signals from "
            f"{stats['sites_succeeded']}/{stats['sites_attempted']} sites "
            f"(noise={self._noise_filtered}, dup={dup_count}, tc={tc_removed}, "
            f"S/N={snr:.2%})"
        )

        return result

    # ── Signal Conversion ──

    def _article_to_signal(
        self,
        article: dict,
        signal_idx: int,
        scan_date_compact: str,
        site_short: str,
        exec_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict:
        """Convert an intermediate article dict to standard signal format.

        Args:
            article: Intermediate article dict from RSS/web crawl.
            signal_idx: Sequential number for this site.
            scan_date_compact: Date in YYYYMMDD format.
            site_short: Short site identifier for signal ID.
            exec_id: Execution ID for proof of execution.
            start_time: Crawl start time.
            end_time: Crawl end time.

        Returns:
            Standard signal format dict.
        """
        signal_id = f"{SIGNAL_ID_PREFIX}-{scan_date_compact}-{site_short}-{signal_idx:03d}"
        language = article.get("language", "en")
        abstract = article.get("content", "")
        if not abstract:
            abstract = article.get("title", "")

        return {
            "id": signal_id,
            "title": article.get("title", ""),
            "source": {
                "name": article.get("site_name", "unknown"),
                "type": article.get("site_type", "news"),
                "url": article.get("url", ""),
                "published_date": article.get("published_date", ""),
            },
            "content": {
                "abstract": abstract,
                "original_abstract": None,  # Set by translation agent later
                "keywords": article.get("keywords", []),
                "language": language,
                "original_language": language,
            },
            "preliminary_category": "",
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "scan_metadata": {
                "execution_proof": {
                    "execution_id": exec_id,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                    "actual_api_calls": {"web_requests": 1},
                    "actual_sources_scanned": [article.get("site_name", "unknown")],
                    "file_created_at": end_time.isoformat(),
                },
                "crawl_strategy_used": article.get("crawl_strategy", "unknown"),
                "crawl_attempt": 1,
                "site_name": article.get("site_name", "unknown"),
                "content_hash": article.get("content_hash", ""),
            },
        }

    # ── Helper Methods ──

    @staticmethod
    def _is_noise(title: str) -> bool:
        """Basic noise filter for ad/promo/irrelevant articles.

        Filters out content with ad markers, photo galleries, sponsored content,
        and other low-information items across multiple languages.

        Args:
            title: Article title string.

        Returns:
            True if the title matches a noise pattern.
        """
        noise_keywords = [
            # Korean
            "[광고]", "[AD]", "[후원]", "[제휴]", "[홍보]",
            "포토뉴스", "화보", "움짤", "[스폰서]",
            # English
            "[Sponsored]", "[Ad]", "[Advertisement]", "[Promoted]",
            "Photo Gallery", "Slideshow", "In Pictures",
            # Japanese
            "[PR]", "[広告]", "写真特集", "フォトギャラリー",
            # General
            "[SPONSORED]", "[ADVERTORIAL]",
        ]
        title_lower = title.lower()
        for kw in noise_keywords:
            if kw.lower() in title_lower:
                return True

        # Filter very short titles (likely navigation elements)
        if len(title.strip()) < 5:
            return True

        return False

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text.

        Uses BeautifulSoup if available, otherwise falls back to regex.

        Args:
            text: HTML string to strip.

        Returns:
            Plain text with HTML tags removed.
        """
        if not text:
            return ""

        if _bs4_available():
            from bs4 import BeautifulSoup
            return BeautifulSoup(text, "html.parser").get_text(strip=True)

        # Regex fallback
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    @staticmethod
    def _make_short_name(site_name: str) -> str:
        """Convert a site name to a short identifier for signal IDs.

        Removes spaces, special characters, and truncates to 15 chars.

        Args:
            site_name: Full site name.

        Returns:
            Short alphanumeric identifier.
        """
        # Remove non-alphanumeric, convert to lowercase
        short = re.sub(r'[^a-zA-Z0-9]', '', site_name).lower()
        return short[:15] if short else "unknown"


# ──────────────────────────────────────────────────────────────────────
# Config Loader (standalone function)
# ──────────────────────────────────────────────────────────────────────

def load_sources_config(config_path: str) -> dict:
    """Load sources-multiglobal-news.yaml configuration.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Parsed configuration dictionary. Empty dict on failure.
    """
    if yaml is None:
        logger.warning("[CONFIG] PyYAML not available — cannot load config")
        return {}

    path = Path(config_path)
    if not path.exists():
        logger.warning(f"[CONFIG] Config not found: {config_path}")
        return {}

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data or {}


# ──────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for the Multi & Global News Direct Crawler."""
    parser = argparse.ArgumentParser(
        description="Multi & Global News Direct Crawler for WF4 Environmental Scanning",
    )
    parser.add_argument(
        "--sources-config", "-c",
        required=True,
        help="Path to sources-multiglobal-news.yaml",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help=(
            "Output JSON file path "
            "(e.g. env-scanning/wf4-multiglobal-news/raw/daily-crawl-2026-02-24.json)"
        ),
    )
    parser.add_argument(
        "--scan-window-start",
        help="Scan window start (ISO 8601). Default: now - 24h",
    )
    parser.add_argument(
        "--scan-window-end",
        help="Scan window end (ISO 8601). Default: now",
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Scan window lookback in hours if --scan-window-start not given (default: 24)",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        help="Specific site short_names to crawl (default: all enabled sites)",
    )
    parser.add_argument(
        "--json-stats",
        action="store_true",
        help="Print crawl stats as JSON to stdout after completion",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger("news_direct_crawler").setLevel(logging.DEBUG)

    # Resolve scan window
    scan_window_end = args.scan_window_end
    scan_window_start = args.scan_window_start

    if not scan_window_end:
        scan_window_end = datetime.now(timezone.utc).isoformat()
    if not scan_window_start:
        end_dt = _parse_iso_datetime(scan_window_end) or datetime.now(timezone.utc)
        scan_window_start = (end_dt - timedelta(hours=args.lookback_hours)).isoformat()

    # Build crawler
    crawler = NewsDirectCrawler(
        sources_config_path=args.sources_config,
        scan_window_start=scan_window_start,
        scan_window_end=scan_window_end,
    )

    # Filter sites if specified
    if args.sites:
        original_count = len(crawler.sites)
        crawler.sites = [
            s for s in crawler.sites
            if s.get("short_name", s.get("name", "")) in args.sites
        ]
        filtered_count = len(crawler.sites)
        logger.info(f"[FILTER] Site filter: {filtered_count}/{original_count} sites selected")
        if not crawler.sites:
            logger.error(f"[FILTER] No matching sites for: {args.sites}")
            sys.exit(1)

    # Execute crawl
    result = crawler.crawl_all_sites()

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"[SAVE] Output written: {output_path}")

    # Print stats if requested
    if args.json_stats:
        stats = calculate_crawl_stats(result)
        stats["output_path"] = str(output_path)
        stats["scan_window"] = {
            "start": scan_window_start,
            "end": scan_window_end,
        }
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    # Exit code: 0 = OK, 1 = all sites failed
    if result["scan_metadata"]["total_items"] == 0:
        logger.error("[EXIT] No articles crawled — all sites failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
