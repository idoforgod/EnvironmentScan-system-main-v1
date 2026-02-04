"""
Redirect Resolver (System 2)

Intelligently tracks HTTP redirects and verifies whether the final
destination serves RSS/Atom content. When the destination is HTML,
automatically discovers alternate RSS feed links.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests


@dataclass
class ResolveResult:
    """Result of URL resolution."""

    original_url: str
    resolved_url: str | None = None
    status: str = "error"  # rss_found | html_with_alternate | html_no_feed | error
    redirect_chain: list[str] = field(default_factory=list)
    content_type: str | None = None
    alternate_feeds: list[str] = field(default_factory=list)
    error: str | None = None


class RedirectResolver:
    """
    Smart redirect tracker with RSS auto-discovery.

    Follows redirect chains, verifies content types, and discovers
    alternate RSS/Atom feeds from HTML pages. Results are cached
    per-domain to avoid redundant network calls.
    """

    CACHE_TTL_DAYS = 7
    MAX_REDIRECTS = 5
    RSS_CONTENT_TYPES = (
        "application/rss+xml",
        "application/atom+xml",
        "application/xml",
        "text/xml",
    )
    ALTERNATE_LINK_PATTERN = re.compile(
        r'<link[^>]+rel=["\']alternate["\'][^>]+'
        r'type=["\']application/(rss|atom)\+xml["\'][^>]*>',
        re.IGNORECASE,
    )
    HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

    def __init__(self, cache_path: str):
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    def resolve(self, url: str, timeout: int = 15) -> ResolveResult:
        """
        Resolve a URL to its final RSS feed location.

        Steps:
            1. Check cache (return immediately if TTL-valid)
            2. Follow redirects with requests.get()
            3. Verify Content-Type of final destination
            4. If HTML, discover alternate RSS/Atom links
            5. Cache and return result

        Args:
            url: Source URL to resolve
            timeout: Request timeout in seconds

        Returns:
            ResolveResult with resolved URL, status, and discovered feeds
        """
        # Check cache first
        cached = self._get_cached(url)
        if cached is not None:
            return cached

        result = ResolveResult(original_url=url)

        try:
            resp = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": (
                        "application/rss+xml, application/atom+xml, "
                        "application/xml, text/xml, text/html;q=0.9, */*;q=0.8"
                    ),
                },
                stream=True,  # Don't download full body yet
            )

            # Record redirect chain
            if resp.history:
                result.redirect_chain = [r.url for r in resp.history] + [resp.url]

            content_type = resp.headers.get("Content-Type", "")
            result.content_type = content_type

            # Read limited content for inspection
            content = resp.content[:100_000]  # Max 100KB

            if self._is_rss_content(content_type, content):
                result.status = "rss_found"
                result.resolved_url = resp.url
            else:
                # HTML or unknown — try to discover alternate feeds
                try:
                    html_text = content.decode("utf-8", errors="replace")
                except Exception:
                    html_text = ""

                alternates = self._discover_alternate_feeds(html_text, resp.url)
                if alternates:
                    result.status = "html_with_alternate"
                    result.alternate_feeds = alternates
                    result.resolved_url = alternates[0]
                else:
                    result.status = "html_no_feed"

        except requests.exceptions.Timeout:
            result.status = "error"
            result.error = f"Request timed out after {timeout}s"

        except requests.exceptions.RequestException as e:
            result.status = "error"
            result.error = str(e)[:300]

        # Cache the result
        self._cache_result(url, result)

        return result

    def _discover_alternate_feeds(self, html_content: str, base_url: str) -> list[str]:
        """
        Discover RSS/Atom feed links from HTML <link rel="alternate"> tags.

        Relative URLs are resolved against the base URL.
        """
        feeds = []

        for link_match in self.ALTERNATE_LINK_PATTERN.finditer(html_content):
            link_tag = link_match.group()
            href_match = self.HREF_PATTERN.search(link_tag)
            if href_match:
                href = href_match.group(1)
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                if absolute_url not in feeds:
                    feeds.append(absolute_url)

        # Also try regex for reversed attribute order:
        # <link type="..." rel="alternate" ...>
        alt_pattern = re.compile(
            r'<link[^>]+type=["\']application/(rss|atom)\+xml["\'][^>]+'
            r'rel=["\']alternate["\'][^>]*>',
            re.IGNORECASE,
        )
        for link_match in alt_pattern.finditer(html_content):
            link_tag = link_match.group()
            href_match = self.HREF_PATTERN.search(link_tag)
            if href_match:
                href = href_match.group(1)
                absolute_url = urljoin(base_url, href)
                if absolute_url not in feeds:
                    feeds.append(absolute_url)

        return feeds

    def _is_rss_content(self, content_type: str, content: bytes) -> bool:
        """
        Determine if content is RSS/Atom by checking both Content-Type
        header and actual content bytes.

        Some servers serve RSS with text/html content type, so we also
        inspect the first bytes for XML/RSS/Atom markers.
        """
        ct_lower = content_type.lower()

        # Content-Type check
        if any(rss_ct in ct_lower for rss_ct in self.RSS_CONTENT_TYPES):
            return True

        # Content inspection (handles servers that lie about Content-Type)
        try:
            start = content[:500].decode("utf-8", errors="replace").strip()
        except Exception:
            return False

        start_lower = start.lower()
        if start_lower.startswith("<?xml") or "<rss" in start_lower or "<feed" in start_lower:
            return True

        return False

    # ── Cache Management ──

    def _load_cache(self) -> dict:
        """Load redirect cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_cache(self) -> None:
        """Persist redirect cache to disk."""
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _get_cached(self, url: str) -> ResolveResult | None:
        """Return cached result if within TTL, else None."""
        entry = self.cache.get(url)
        if entry is None:
            return None

        if not self._is_cache_valid(entry):
            del self.cache[url]
            return None

        return ResolveResult(
            original_url=url,
            resolved_url=entry.get("resolved_url"),
            status=entry.get("status", "error"),
            redirect_chain=entry.get("redirect_chain", []),
            content_type=entry.get("content_type"),
            alternate_feeds=entry.get("alternate_feeds", []),
            error=entry.get("error"),
        )

    def _cache_result(self, url: str, result: ResolveResult) -> None:
        """Cache a resolve result."""
        self.cache[url] = {
            "resolved_url": result.resolved_url,
            "status": result.status,
            "redirect_chain": result.redirect_chain,
            "content_type": result.content_type,
            "alternate_feeds": result.alternate_feeds,
            "error": result.error,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_cache()

    def _is_cache_valid(self, entry: dict) -> bool:
        """Check if a cache entry is still within its TTL."""
        cached_at = entry.get("cached_at")
        if not cached_at:
            return False
        try:
            cached_time = datetime.fromisoformat(cached_at)
            age_days = (datetime.now(timezone.utc) - cached_time).total_seconds() / 86400
            return age_days < self.CACHE_TTL_DAYS
        except (ValueError, TypeError):
            return False
