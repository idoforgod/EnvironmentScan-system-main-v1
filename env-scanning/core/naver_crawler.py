"""
Naver News Crawler (WF3 Core Module)

Anti-block Naver News crawler for STEEPS Environmental Scanning.
Crawls 6 Naver News sections with 7-strategy CrawlDefender cascade.

Architecture:
    - CrawlDefender: Block detection + automatic strategy rotation
    - NaverNewsCrawler: Section-level crawling + article content fetching
    - Config-driven: reads sources-naver.yaml for selectors and parameters

CLI Usage:
    python3 env-scanning/core/naver_crawler.py \\
        --output env-scanning/wf3-naver/raw/daily-crawl-2026-02-06.json \\
        --config env-scanning/config/sources-naver.yaml

Called by: naver-scan-orchestrator (Step 1.2)
"""

import argparse
import hashlib
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None  # Optional: config can be passed as defaults

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("naver_crawler")


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


@dataclass
class CrawlStats:
    """Crawling statistics for one run."""
    total_articles: int = 0
    sections_crawled: int = 0
    sections_failed: int = 0
    blocks_encountered: int = 0
    strategies_used: list[str] = field(default_factory=list)
    snr_ratio: float = 0.0  # Signal-to-Noise Ratio


@dataclass
class Article:
    """A single crawled news article."""
    title: str
    url: str
    press: str
    pub_time: str
    section: str
    section_id: int = 0
    content: str = ""
    content_hash: str = ""
    crawled_at: str = ""
    word_count: int = 0

    def to_standard_signal(self, idx: int, scan_date: str) -> dict:
        """Convert to standard signal format compatible with shared workers.

        Matches the WF1/WF2 raw signal schema:
        - id, title, source (object), content (object),
          preliminary_category, collected_at
        """
        abstract = self.content[:300] if self.content else self.title
        return {
            "id": f"naver-{scan_date.replace('-', '')}-{self.section_id}-{idx:03d}",
            "title": self.title,
            "source": {
                "name": "NaverNews",
                "type": "news",
                "url": self.url,
                "published_date": scan_date,
                "section": self.section,
                "section_id": self.section_id,
                "press": self.press,
            },
            "content": {
                "abstract": abstract,
                "full_text": self.content,
                "keywords": [],
                "language": "ko",
            },
            "preliminary_category": SECTION_TO_STEEPS.get(self.section_id, "S"),
            "collected_at": self.crawled_at,
            "metadata": {
                "content_hash": self.content_hash,
                "word_count": self.word_count,
                "pub_time_raw": self.pub_time,
            },
        }


# ──────────────────────────────────────────────────────────────────────
# Section → STEEPs Preliminary Mapping
# ──────────────────────────────────────────────────────────────────────

SECTION_TO_STEEPS: dict[int, str] = {
    100: "P",   # 정치 → Political
    101: "E",   # 경제 → Economic
    102: "S",   # 사회 → Social
    103: "S",   # 생활문화 → Social
    104: "P",   # 세계 → Political (international)
    105: "T",   # IT과학 → Technological
}


# ──────────────────────────────────────────────────────────────────────
# User-Agent Pool
# ──────────────────────────────────────────────────────────────────────

UA_POOL = [
    # Chrome on Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    # Chrome on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    # Firefox on Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    # Firefox on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) "
        "Gecko/20100101 Firefox/122.0"
    ),
    # Safari on Mac
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.2 Safari/605.1.15"
    ),
    # Edge on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    ),
]


# ──────────────────────────────────────────────────────────────────────
# CrawlDefender — Block Detection + Strategy Rotation
# ──────────────────────────────────────────────────────────────────────

class CrawlDefender:
    """
    Crawling block detection and automatic strategy escalation.

    7-strategy cascade:
        1. default           — plain requests with humanized headers
        2. httpx_h2          — httpx with HTTP/2
        3. rotate_headers    — aggressive header randomization
        4. delay_increase    — exponential backoff
        5. proxy_rotation    — proxy support (if configured)
        6. session_reset     — fresh session per request
        7. browser_emulation — placeholder for Selenium/Playwright
    """

    STRATEGIES = [
        "default",
        "httpx_h2",
        "rotate_headers",
        "delay_increase",
        "proxy_rotation",
        "session_reset",
        "browser_emulation",
    ]

    def __init__(self):
        self.strategy_index = 0
        self.current_strategy = self.STRATEGIES[0]
        self.block_history: list[BlockEvent] = []
        self.success_count = 0
        self.consecutive_successes = 0

    def detect_block(
        self,
        response: Optional[requests.Response] = None,
        error: Optional[Exception] = None,
    ) -> str:
        """Classify the type of block encountered. Returns 'none' if not blocked."""
        if error:
            err_str = str(error).lower()
            if "timeout" in err_str:
                return "timeout"
            if "connection" in err_str:
                return "connection_blocked"
            return "unknown_error"

        if response is None:
            return "no_response"

        code = response.status_code
        if code == 403:
            return "ip_blocked"
        if code == 429:
            return "rate_limited"
        if code == 503:
            return "service_unavailable"
        if code >= 400:
            return f"http_{code}"

        text = response.text.lower()
        if "captcha" in text or "보안문자" in text:
            return "captcha"
        if len(response.text) < 500:
            return "empty_response"

        return "none"

    def escalate(self) -> str:
        """Move to the next strategy in the cascade. Wraps around."""
        self.strategy_index = (self.strategy_index + 1) % len(self.STRATEGIES)
        self.current_strategy = self.STRATEGIES[self.strategy_index]
        self.consecutive_successes = 0
        logger.info(f"[DEFENDER] Strategy → {self.current_strategy}")
        return self.current_strategy

    def record_block(self, block_type: str, url: str, status_code: int | None = None):
        self.block_history.append(BlockEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            block_type=block_type,
            url=url,
            strategy=self.current_strategy,
            status_code=status_code,
        ))

    def record_success(self):
        self.success_count += 1
        self.consecutive_successes += 1
        # After 5 consecutive successes, reset to fastest strategy
        if self.consecutive_successes >= 5 and self.strategy_index > 0:
            self.strategy_index = 0
            self.current_strategy = self.STRATEGIES[0]
            logger.info("[DEFENDER] 5 consecutive successes → resetting to default")

    def get_headers(self) -> dict:
        """Generate humanized browser headers."""
        ua = random.choice(UA_POOL)
        headers = {
            "User-Agent": ua,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        # Strategy-specific header variations
        if self.current_strategy == "rotate_headers":
            # More aggressive randomization
            if random.random() > 0.5:
                headers["Referer"] = "https://www.naver.com/"
            if random.random() > 0.5:
                headers["DNT"] = "1"
            # Shuffle Accept-Language variants
            lang_variants = [
                "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "ko-KR,ko;q=0.8,en;q=0.5",
                "ko,en-US;q=0.9,en;q=0.8",
            ]
            headers["Accept-Language"] = random.choice(lang_variants)
        else:
            headers["Referer"] = "https://www.naver.com/"

        return headers

    def summary(self) -> dict:
        """Return defense summary for output JSON."""
        strategy_counts: dict[str, int] = {}
        for event in self.block_history:
            strategy_counts[event.strategy] = strategy_counts.get(event.strategy, 0) + 1
        return {
            "total_blocks": len(self.block_history),
            "total_successes": self.success_count,
            "blocks_by_type": _count_by(self.block_history, "block_type"),
            "blocks_by_strategy": strategy_counts,
            "final_strategy": self.current_strategy,
        }


def _count_by(events: list[BlockEvent], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in events:
        key = getattr(e, attr)
        counts[key] = counts.get(key, 0) + 1
    return counts


# ──────────────────────────────────────────────────────────────────────
# NaverNewsCrawler
# ──────────────────────────────────────────────────────────────────────

class NaverNewsCrawler:
    """
    Naver News crawler with CrawlDefender anti-block.

    Crawls 6 sections, fetches article metadata + full body content.
    Produces a structured JSON output for the WF3 pipeline.
    """

    DEFAULT_SECTIONS = {
        "정치": 100,
        "경제": 101,
        "사회": 102,
        "생활문화": 103,
        "세계": 104,
        "IT과학": 105,
    }

    BASE_URL = "https://news.naver.com/section/"

    def __init__(
        self,
        sections: dict[str, int] | None = None,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        section_delay: float = 5.0,
        max_retries: int = 10,
        fetch_content: bool = True,
        content_selectors: dict | None = None,
    ):
        self.sections = sections or self.DEFAULT_SECTIONS
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.section_delay = section_delay
        self.max_retries = max_retries
        self.fetch_content = fetch_content

        # CSS selectors for parsing (config-driven)
        self.selectors = content_selectors or {
            "article_list": "li.sa_item, div.news_area",
            "title": "a.sa_text_title, a.news_tit",
            "press": ".sa_text_press, .info_group .press",
            "time": ".sa_text_datetime, .info_group span",
            "content": "#dic_area, #newsct_article, article",
        }

        self.defender = CrawlDefender()
        self.articles: list[Article] = []
        self.failed_urls: list[str] = []
        self.noise_filtered: int = 0

        self._bs4_available = False
        try:
            from bs4 import BeautifulSoup  # noqa: F401
            self._bs4_available = True
        except ImportError:
            logger.warning(
                "BeautifulSoup4 not installed — HTML parsing will be limited. "
                "Install: pip install beautifulsoup4 lxml"
            )

    # ── HTTP Request with Auto-Retry ──

    def _request(self, url: str) -> Optional[requests.Response]:
        """Make an HTTP request with CrawlDefender strategy rotation."""
        for attempt in range(self.max_retries):
            try:
                headers = self.defender.get_headers()
                strategy = self.defender.current_strategy

                if strategy == "httpx_h2":
                    try:
                        import httpx
                        resp = httpx.get(
                            url, headers=headers, timeout=15, follow_redirects=True
                        )
                        # Convert httpx response to match requests interface
                        mock_resp = requests.Response()
                        mock_resp.status_code = resp.status_code
                        mock_resp._content = resp.content
                        mock_resp.encoding = resp.encoding or "utf-8"
                        response = mock_resp
                    except ImportError:
                        response = requests.get(url, headers=headers, timeout=15)
                elif strategy == "session_reset":
                    session = requests.Session()
                    response = session.get(url, headers=headers, timeout=15)
                    session.close()
                elif strategy == "delay_increase":
                    time.sleep(random.uniform(self.max_delay, self.max_delay * 2))
                    response = requests.get(url, headers=headers, timeout=20)
                else:
                    response = requests.get(url, headers=headers, timeout=15)

                block_type = self.defender.detect_block(response=response)

                if block_type == "none":
                    self.defender.record_success()
                    return response

                logger.warning(
                    f"[BLOCK] {block_type} (HTTP {response.status_code}) "
                    f"strategy={strategy} attempt={attempt + 1}/{self.max_retries}"
                )
                self.defender.record_block(block_type, url, response.status_code)
                self.defender.escalate()
                self._jitter_delay()

            except Exception as e:
                block_type = self.defender.detect_block(error=e)
                logger.error(f"[ERROR] {block_type}: {e}")
                self.defender.record_block(block_type, url)
                self.defender.escalate()
                self._jitter_delay()

        logger.error(f"[FAIL] Max retries exhausted: {url}")
        self.failed_urls.append(url)
        return None

    def _jitter_delay(self):
        """Random delay with jitter."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    # ── HTML Parsing ──

    def _parse_article_list(self, html: str, section_name: str, section_id: int = 0) -> list[Article]:
        """Parse article list from section HTML."""
        if not self._bs4_available:
            logger.error("Cannot parse HTML without BeautifulSoup4")
            return []

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml" if _lxml_available() else "html.parser")
        articles: list[Article] = []

        items = soup.select(self.selectors["article_list"])
        for item in items:
            try:
                title_elem = item.select_one(self.selectors["title"])
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                if not url or not title:
                    continue

                # Resolve relative URLs
                if url.startswith("/"):
                    url = urljoin("https://news.naver.com", url)

                press_elem = item.select_one(self.selectors["press"])
                press = press_elem.get_text(strip=True) if press_elem else "Unknown"

                time_elem = item.select_one(self.selectors["time"])
                pub_time = time_elem.get_text(strip=True) if time_elem else ""

                # Noise filter: skip ads and low-info items
                if self._is_noise(title):
                    self.noise_filtered += 1
                    continue

                articles.append(Article(
                    title=title,
                    url=url,
                    press=press,
                    pub_time=pub_time,
                    section=section_name,
                    section_id=section_id,
                    crawled_at=datetime.now(timezone.utc).isoformat(),
                ))

            except Exception as e:
                logger.debug(f"Parse error in article item: {e}")
                continue

        return articles

    def _fetch_article_content(self, url: str) -> str:
        """Fetch full article body text."""
        response = self._request(url)
        if not response:
            return ""

        if not self._bs4_available:
            return ""

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            response.text, "lxml" if _lxml_available() else "html.parser"
        )
        content_elem = soup.select_one(self.selectors["content"])
        if content_elem:
            return content_elem.get_text(strip=True)
        return ""

    @staticmethod
    def _is_noise(title: str) -> bool:
        """Basic noise filter for ad/promo articles."""
        noise_keywords = [
            "[광고]", "[AD]", "[후원]", "[제휴]",
            "포토뉴스", "화보", "움짤",
        ]
        return any(kw in title for kw in noise_keywords)

    @staticmethod
    def _content_hash(title: str, content: str) -> str:
        """Generate MD5 hash for deduplication."""
        combined = (title + content).encode("utf-8")
        return hashlib.md5(combined).hexdigest()

    # ── Section & Full Crawl ──

    def crawl_section(self, section_name: str, section_id: int) -> list[Article]:
        """Crawl a single Naver News section."""
        logger.info(f"[CRAWL] Section start: {section_name} (sid={section_id})")

        url = f"{self.BASE_URL}{section_id}"
        response = self._request(url)

        if not response:
            logger.error(f"[FAIL] Section crawl failed: {section_name}")
            return []

        articles = self._parse_article_list(response.text, section_name, section_id)
        logger.info(f"[CRAWL] {section_name}: {len(articles)} articles found")

        if self.fetch_content:
            for article in articles:
                self._jitter_delay()
                content = self._fetch_article_content(article.url)
                article.content = content
                article.content_hash = self._content_hash(article.title, content)
                article.word_count = len(content)

        return articles

    def crawl_all(self) -> dict:
        """
        Crawl all configured sections and return structured output.

        Returns a dict matching the WF3 pipeline's expected raw output format.
        """
        start_time = datetime.now(timezone.utc)
        logger.info("[START] Naver News full crawl starting")

        all_articles: list[Article] = []
        section_stats: dict[str, int] = {}

        for section_name, section_id in self.sections.items():
            articles = self.crawl_section(section_name, section_id)
            all_articles.extend(articles)
            section_stats[section_name] = len(articles)

            # Inter-section delay
            time.sleep(random.uniform(
                self.section_delay * 0.8,
                self.section_delay * 1.2,
            ))

        end_time = datetime.now(timezone.utc)
        scan_date = datetime.now().strftime("%Y-%m-%d")
        total = len(all_articles)
        total_raw = total + self.noise_filtered
        snr = total / total_raw if total_raw > 0 else 0.0

        # Generate execution ID for PoE (Proof of Execution)
        exec_id = (
            f"wf3-crawl-{scan_date}-"
            f"{start_time.strftime('%H-%M-%S')}-"
            f"{hashlib.md5(start_time.isoformat().encode()).hexdigest()[:4]}"
        )

        # Convert articles to standard signal format
        items = []
        for idx, article in enumerate(all_articles, start=1):
            items.append(article.to_standard_signal(idx, scan_date))

        result = {
            "scan_metadata": {
                "date": scan_date,
                "workflow": "wf3-naver",
                "source": "NaverNews",
                "total_items": total,
                "execution_time": round((end_time - start_time).total_seconds(), 1),
                "execution_proof": {
                    "execution_id": exec_id,
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                    "actual_api_calls": {
                        "web_search": 0,
                        "arxiv_api": 0,
                        "naver_crawl": self.defender.success_count,
                    },
                    "actual_sources_scanned": ["NaverNews"],
                    "file_created_at": end_time.isoformat(),
                },
                "crawler_version": "1.0.0",
            },
            "crawl_stats": {
                "total_articles": total,
                "total_raw_before_noise_filter": total_raw,
                "noise_filtered": self.noise_filtered,
                "signal_to_noise_ratio": round(snr, 4),
                "sections_crawled": len(section_stats),
                "section_stats": section_stats,
                "failed_urls_count": len(self.failed_urls),
            },
            "defense_summary": self.defender.summary(),
            "items": items,
            "failed_urls": self.failed_urls,
        }

        logger.info(
            f"[DONE] Crawl complete: {total} items "
            f"({self.noise_filtered} noise filtered, S/N={snr:.2%})"
        )
        return result


# ──────────────────────────────────────────────────────────────────────
# Config Loader
# ──────────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    """Load sources-naver.yaml and extract crawl parameters."""
    if yaml is None:
        logger.warning("PyYAML not available — using default config")
        return {}

    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config not found: {config_path} — using defaults")
        return {}

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sources = data.get("sources", [])
    if not sources:
        return {}

    naver_src = sources[0]  # Single source in WF3
    return {
        "sections": naver_src.get("sections", {}),
        "crawl_config": naver_src.get("crawl_config", {}),
        "anti_block": naver_src.get("anti_block", {}),
    }


def _lxml_available() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False


# ──────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Naver News Crawler for WF3 Environmental Scanning"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output JSON file path (e.g. env-scanning/wf3-naver/raw/daily-crawl-2026-02-06.json)",
    )
    parser.add_argument(
        "--config", "-c",
        default="env-scanning/config/sources-naver.yaml",
        help="Path to sources-naver.yaml",
    )
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="Skip fetching article body content (faster, metadata only)",
    )
    parser.add_argument(
        "--sections",
        nargs="*",
        help="Specific sections to crawl (e.g. 정치 경제). Default: all 6 sections",
    )
    parser.add_argument(
        "--json-stats",
        action="store_true",
        help="Print crawl stats as JSON to stdout after completion",
    )
    # ── Temporal Consistency (v2.2.0) ──
    parser.add_argument(
        "--lookback-hours", type=int, default=24,
        help="Scan window lookback in hours (default: 24)",
    )
    parser.add_argument(
        "--scan-window-start",
        help="Explicit scan window start (ISO8601, from orchestrator T₀ - lookback)",
    )
    parser.add_argument(
        "--scan-window-end",
        help="Explicit scan window end (ISO8601, from orchestrator T₀)",
    )
    parser.add_argument(
        "--scan-tolerance-min", type=int, default=30,
        help="Tolerance in minutes for temporal filtering (default: 30)",
    )
    args = parser.parse_args()

    # Load config
    cfg = load_config(args.config)
    crawl_cfg = cfg.get("crawl_config", {})

    # Determine sections
    sections = cfg.get("sections", NaverNewsCrawler.DEFAULT_SECTIONS)
    if args.sections:
        sections = {k: v for k, v in sections.items() if k in args.sections}
        if not sections:
            logger.error(f"No matching sections found for: {args.sections}")
            sys.exit(1)

    # Build crawler
    crawler = NaverNewsCrawler(
        sections=sections,
        min_delay=crawl_cfg.get("min_delay", 2.0),
        max_delay=crawl_cfg.get("max_delay", 5.0),
        section_delay=crawl_cfg.get("section_delay", 5.0),
        max_retries=crawl_cfg.get("max_retries", 10),
        fetch_content=not args.no_content,
        content_selectors=crawl_cfg.get("content_selectors"),
    )

    # Execute crawl
    result = crawler.crawl_all()

    # ── TC-003: Post-collection temporal filter (v2.2.0) ──
    if args.scan_window_start and args.scan_window_end:
        window_start = datetime.fromisoformat(args.scan_window_start)
        window_end = datetime.fromisoformat(args.scan_window_end)
    else:
        window_end = datetime.now(timezone.utc)
        window_start = window_end - timedelta(hours=args.lookback_hours)

    tolerance = timedelta(minutes=args.scan_tolerance_min)
    effective_start = window_start - tolerance
    tc_removed = 0
    tc_kept_items = []

    for item in result.get("items", []):
        pub_raw = item.get("metadata", {}).get("pub_time_raw", "")
        pub_date_str = item.get("source", {}).get("published_date", "")
        # Naver articles have pub_time_raw which may include time info
        # If not parseable, keep the signal (fail-open for crawled data)
        keep = True
        try:
            if pub_raw and any(c.isdigit() for c in pub_raw):
                # Try to parse Korean-format time like "2026.02.10. 오전 9:30"
                # For now, rely on published_date (date-level)
                pass
            if pub_date_str:
                if 'T' in pub_date_str:
                    pub_dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    pub_dt = pub_dt.replace(tzinfo=None)
                else:
                    pub_dt = datetime.strptime(pub_date_str[:10], '%Y-%m-%d')
                # Normalize window to naive if needed
                ws = effective_start.replace(tzinfo=None) if effective_start.tzinfo else effective_start
                we = window_end.replace(tzinfo=None) if window_end.tzinfo else window_end
                if pub_dt < ws or pub_dt > we:
                    keep = False
        except (ValueError, TypeError):
            pass  # Unparseable → keep

        if keep:
            tc_kept_items.append(item)
        else:
            tc_removed += 1
            logger.info(f"TC-003 filtered: {item.get('id', '?')} (pub: {pub_date_str})")

    if tc_removed > 0:
        logger.info(f"TC-003: {tc_removed} signals removed, {len(tc_kept_items)} within window")
        result["items"] = tc_kept_items
        result["scan_metadata"]["total_items"] = len(tc_kept_items)
        result["scan_metadata"]["tc_filter"] = {
            "window_start": str(window_start),
            "window_end": str(window_end),
            "tolerance_minutes": args.scan_tolerance_min,
            "removed_count": tc_removed,
            "remaining_count": len(tc_kept_items),
        }

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"[SAVE] Output written: {output_path}")

    # Print stats if requested
    if args.json_stats:
        stats = {
            "output_path": str(output_path),
            "total_articles": result["crawl_stats"]["total_articles"],
            "sections_crawled": result["crawl_stats"]["sections_crawled"],
            "section_stats": result["crawl_stats"]["section_stats"],
            "noise_filtered": result["crawl_stats"]["noise_filtered"],
            "snr": result["crawl_stats"]["signal_to_noise_ratio"],
            "blocks": result["defense_summary"]["total_blocks"],
            "failed_urls": result["crawl_stats"]["failed_urls_count"],
        }
        print(json.dumps(stats, ensure_ascii=False, indent=2))

    # Exit code: 0 = OK, 1 = all sections failed
    if result["scan_metadata"]["total_items"] == 0:
        logger.error("[EXIT] No articles crawled — all sections failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
