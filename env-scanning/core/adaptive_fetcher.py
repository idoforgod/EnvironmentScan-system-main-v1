"""
Adaptive Fetcher (System 3)

5-strategy chain for overcoming HTTP 403 Forbidden and other
bot-blocking responses. Each strategy escalates in sophistication,
and successful strategies are cached per-domain for future use.
"""

import json
import os
import random
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests


@dataclass
class FetchResult:
    """Result of an adaptive fetch attempt."""

    success: bool
    content: bytes | None = None
    status_code: int | None = None
    strategy_used: str | None = None
    attempts: int = 0
    total_time_seconds: float = 0.0
    attempt_log: list[dict] = field(default_factory=list)


class AdaptiveFetcher:
    """
    Adaptive anti-bot bypass with 5-strategy escalation chain.

    Strategy order:
        1. User-Agent rotation
        2. Full browser header set
        3. Session-based access with cookie collection
        4. httpx with HTTP/2 and different TLS fingerprint
        5. Dynamic code generation (Google Cache, Archive.org, RSS Bridge)

    Successful strategies are cached per-domain for instant reuse.
    """

    MAX_ATTEMPTS_PER_STRATEGY = 2

    UA_POOL = [
        # Chrome on Mac
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        # Firefox on Mac
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
            "Gecko/20100101 Firefox/121.0"
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
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ),
        # Chrome on Linux
        (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    ]

    BROWSER_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    def __init__(self, strategy_cache_path: str):
        self.cache_path = Path(strategy_cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
        self.attempt_log: list[dict] = []

    def fetch(
        self,
        url: str,
        timeout: int = 30,
        source_name: str = "",
    ) -> FetchResult:
        """
        Attempt to fetch URL using escalating strategies.

        If a cached strategy exists for this domain, it is tried first.
        Otherwise strategies 1-5 are tried in order.

        Args:
            url: Target URL
            timeout: Per-request timeout
            source_name: Human-readable source name for logging

        Returns:
            FetchResult with content on success or failure details
        """
        start = time.monotonic()
        domain = urlparse(url).netloc
        self.attempt_log = []
        total_attempts = 0

        # Strategy dispatch table
        strategies = [
            ("strategy_1_useragent", self._strategy_1_rotate_useragent),
            ("strategy_2_browser_headers", self._strategy_2_browser_headers),
            ("strategy_3_session_cookies", self._strategy_3_session_with_cookies),
            ("strategy_4_httpx_http2", self._strategy_4_httpx_http2),
            ("strategy_5_dynamic_code", lambda u, t: self._strategy_5_dynamic_code(u, source_name, t)),
        ]

        # If we have a cached successful strategy, try it first
        cached_strategy = self._get_cached_strategy(domain)
        if cached_strategy:
            # Move cached strategy to front
            strategies = sorted(
                strategies,
                key=lambda s: 0 if s[0] == cached_strategy else 1,
            )

        for strategy_name, strategy_fn in strategies:
            for attempt in range(self.MAX_ATTEMPTS_PER_STRATEGY):
                total_attempts += 1
                attempt_start = time.monotonic()

                try:
                    resp = strategy_fn(url, timeout)
                    attempt_time = time.monotonic() - attempt_start

                    if resp is not None and resp.status_code == 200:
                        # Success
                        self._cache_strategy(domain, strategy_name)
                        self.attempt_log.append({
                            "strategy": strategy_name,
                            "attempt": attempt + 1,
                            "status_code": resp.status_code,
                            "time_seconds": round(attempt_time, 2),
                            "result": "success",
                        })

                        return FetchResult(
                            success=True,
                            content=resp.content if hasattr(resp, "content") else resp.get("content", b""),
                            status_code=resp.status_code if hasattr(resp, "status_code") else 200,
                            strategy_used=strategy_name,
                            attempts=total_attempts,
                            total_time_seconds=round(time.monotonic() - start, 2),
                            attempt_log=self.attempt_log,
                        )

                    status = resp.status_code if resp and hasattr(resp, "status_code") else None
                    self.attempt_log.append({
                        "strategy": strategy_name,
                        "attempt": attempt + 1,
                        "status_code": status,
                        "time_seconds": round(attempt_time, 2),
                        "result": "failed",
                    })

                except Exception as e:
                    attempt_time = time.monotonic() - attempt_start
                    self.attempt_log.append({
                        "strategy": strategy_name,
                        "attempt": attempt + 1,
                        "error": str(e)[:200],
                        "time_seconds": round(attempt_time, 2),
                        "result": "error",
                    })

        # All strategies exhausted
        return FetchResult(
            success=False,
            attempts=total_attempts,
            total_time_seconds=round(time.monotonic() - start, 2),
            attempt_log=self.attempt_log,
        )

    # ── Strategy 1: User-Agent Rotation ──

    def _strategy_1_rotate_useragent(
        self, url: str, timeout: int
    ) -> requests.Response | None:
        """Try fetching with a random browser User-Agent."""
        ua = random.choice(self.UA_POOL)
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": ua},
        )
        if resp.status_code == 200:
            return resp
        return resp  # Return regardless for status tracking

    # ── Strategy 2: Full Browser Headers ──

    def _strategy_2_browser_headers(
        self, url: str, timeout: int
    ) -> requests.Response | None:
        """Emulate a full browser header set including Sec-Fetch headers."""
        headers = {**self.BROWSER_HEADERS, "User-Agent": random.choice(self.UA_POOL)}
        resp = requests.get(url, timeout=timeout, headers=headers)
        return resp

    # ── Strategy 3: Session + Cookie Collection ──

    def _strategy_3_session_with_cookies(
        self, url: str, timeout: int
    ) -> requests.Response | None:
        """
        Visit the domain homepage first to collect cookies,
        then request the target URL with the session.
        """
        parsed = urlparse(url)
        homepage = f"{parsed.scheme}://{parsed.netloc}/"

        session = requests.Session()
        session.headers.update(
            {**self.BROWSER_HEADERS, "User-Agent": random.choice(self.UA_POOL)}
        )

        # Visit homepage to collect cookies
        try:
            session.get(homepage, timeout=timeout)
        except requests.RequestException:
            pass  # Homepage visit is best-effort

        # Human-like delay
        time.sleep(random.uniform(1.0, 3.0))

        # Now request the actual target
        resp = session.get(url, timeout=timeout)
        return resp

    # ── Strategy 4: httpx with HTTP/2 ──

    def _strategy_4_httpx_http2(
        self, url: str, timeout: int
    ) -> requests.Response | None:
        """
        Use httpx library with HTTP/2 for a different TLS fingerprint.
        Returns None if httpx is not installed.
        """
        try:
            import httpx
        except ImportError:
            return None

        headers = {**self.BROWSER_HEADERS, "User-Agent": random.choice(self.UA_POOL)}

        with httpx.Client(http2=True, follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url, headers=headers)

            # Convert to requests.Response-compatible object
            mock = requests.models.Response()
            mock.status_code = resp.status_code
            mock._content = resp.content
            mock.headers.update(dict(resp.headers))
            return mock

    # ── Strategy 5: Dynamic Code Generation ──

    def _strategy_5_dynamic_code(
        self, url: str, source_name: str, timeout: int
    ) -> requests.Response | None:
        """
        Generate and execute a Python script that tries alternative
        access methods: Archive.org, RSS Bridge, direct HTML scraping.
        """
        templates = ["archive_org", "rss_bridge", "google_cache"]
        template = self._select_template(url, self.attempt_log)

        # Reorder to put selected template first
        templates = [template] + [t for t in templates if t != template]

        for tmpl in templates:
            script = self._generate_dynamic_script(url, tmpl)
            result = self._execute_dynamic_script(script, url, timeout)

            if result and result.get("status") == 200 and result.get("content"):
                mock = requests.models.Response()
                mock.status_code = 200
                mock._content = result["content"].encode("utf-8")
                return mock

        return None

    def _generate_dynamic_script(self, url: str, template: str) -> str:
        """Generate a Python script string for the given access template.

        URLs are passed via sys.argv[1] to avoid injection issues.
        """
        scripts = {
            "archive_org": '''
import requests, json, sys
url = sys.argv[1]
api = f"https://web.archive.org/web/2/{url}"
headers = {"User-Agent": "Mozilla/5.0 (compatible; EnvironmentalScan/1.0)"}
try:
    resp = requests.get(api, headers=headers, timeout=30)
    print(json.dumps({"status": resp.status_code, "content": resp.text[:50000]}))
except Exception as e:
    print(json.dumps({"status": 0, "error": str(e)}))
''',
            "rss_bridge": '''
import requests, json, sys
from urllib.parse import quote
url = sys.argv[1]
bridge = f"https://rss-bridge.org/bridge01/?action=display&bridge=FeedMergeBridge&feed_1={quote(url)}&format=Atom"
try:
    resp = requests.get(bridge, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    print(json.dumps({"status": resp.status_code, "content": resp.text[:50000]}))
except Exception as e:
    print(json.dumps({"status": 0, "error": str(e)}))
''',
            "google_cache": '''
import requests, json, sys
url = sys.argv[1]
cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
try:
    resp = requests.get(cache_url, headers=headers, timeout=30)
    print(json.dumps({"status": resp.status_code, "content": resp.text[:50000]}))
except Exception as e:
    print(json.dumps({"status": 0, "error": str(e)}))
''',
        }
        return scripts.get(template, scripts["archive_org"])

    def _execute_dynamic_script(
        self, script: str, url: str, timeout: int
    ) -> dict | None:
        """
        Execute a dynamically generated script in a subprocess.
        Parse JSON from stdout. Auto-clean temp file.
        """
        domain = urlparse(url).netloc.replace(".", "_")
        ts = int(time.time())

        fd, script_path = tempfile.mkstemp(
            prefix=f"adaptive_fetch_{domain}_{ts}_",
            suffix=".py",
        )
        try:
            with os.fdopen(fd, "w") as f:
                f.write(script)

            result = subprocess.run(
                [sys.executable, script_path, url],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout.strip())

        except subprocess.TimeoutExpired:
            return None
        except (json.JSONDecodeError, OSError):
            return None
        finally:
            try:
                os.unlink(script_path)
            except OSError:
                pass

        return None

    def _select_template(self, url: str, previous_errors: list) -> str:
        """
        Select the most promising dynamic script template based on
        the URL domain and previous error patterns.
        """
        domain = urlparse(url).netloc.lower()

        # Count 403s specifically
        has_403 = any(
            a.get("status_code") == 403
            for a in previous_errors
        )

        # Cloudflare-protected sites → try google cache first
        if has_403 and any(kw in domain for kw in ("cloudflare", "cdn")):
            return "google_cache"

        # General 403 → archive.org is usually most reliable
        if has_403:
            return "archive_org"

        # Default: RSS bridge for feed-like URLs
        return "rss_bridge"

    # ── Strategy Cache ──

    def _get_cached_strategy(self, domain: str) -> str | None:
        """Get previously successful strategy for this domain."""
        entry = self.cache.get(domain)
        if entry and isinstance(entry, dict):
            return entry.get("strategy")
        return None

    def _cache_strategy(self, domain: str, strategy: str) -> None:
        """Cache a successful strategy for this domain."""
        self.cache[domain] = {
            "strategy": strategy,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "success_count": self.cache.get(domain, {}).get("success_count", 0) + 1,
        }
        self._save_cache()

    def _load_cache(self) -> dict:
        """Load strategy cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_cache(self) -> None:
        """Persist strategy cache to disk."""
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
