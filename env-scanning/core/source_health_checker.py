"""
Source Health Checker (System 1)

Step 1.1.5: Pre-scan URL validation.
Sends HEAD requests to all enabled sources to verify availability,
classify health status, and disable unhealthy sources at runtime.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests


@dataclass
class HealthCheckResult:
    """Result of a single source health check."""

    name: str
    url: str
    status_code: int | None = None
    health: str = "unknown"  # healthy | unhealthy | suspect
    reason: str = "unchecked"
    response_time_ms: float = 0.0
    content_type: str | None = None
    redirect_chain: list[str] = field(default_factory=list)
    error: str | None = None


class SourceHealthChecker:
    """
    Step 1.1.5: Source URL pre-validation.

    Sends HEAD requests to all enabled sources before scanning begins.
    Unhealthy sources are flagged for runtime disabling to prevent
    wasted time and cascading errors in the scan pipeline.
    """

    HEAD_TIMEOUT = 10  # seconds
    RSS_CONTENT_TYPES = (
        "application/rss+xml",
        "application/atom+xml",
        "application/xml",
        "text/xml",
    )

    def __init__(self, sources_config: list[dict], health_dir: str):
        self.sources = sources_config
        self.health_dir = Path(health_dir)
        self.health_dir.mkdir(parents=True, exist_ok=True)
        (self.health_dir / "reports").mkdir(parents=True, exist_ok=True)

    def check_all_sources(self) -> dict:
        """
        Validate all enabled sources via HEAD requests.

        Returns:
            Report dict with per-source health status and summary counts.
        """
        results: dict[str, dict] = {}
        healthy_count = 0
        unhealthy_count = 0
        suspect_count = 0

        enabled_sources = [
            s for s in self.sources
            if s.get("enabled", False)
            and (s.get("rss_feed") or s.get("api_endpoint"))
        ]

        print(f"[HEALTH] Checking {len(enabled_sources)} enabled sources...")

        for source in enabled_sources:
            name = source.get("name", "Unknown")
            result = self._check_single_source(source)
            results[name] = asdict(result)

            if result.health == "healthy":
                healthy_count += 1
            elif result.health == "unhealthy":
                unhealthy_count += 1
                print(f"  [UNHEALTHY] {name}: {result.reason} (HTTP {result.status_code})")
            else:
                suspect_count += 1
                print(f"  [SUSPECT]   {name}: {result.reason}")

        report = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total": len(enabled_sources),
            "healthy": healthy_count,
            "unhealthy": unhealthy_count,
            "suspect": suspect_count,
            "sources": results,
        }

        print(
            f"[HEALTH] Result: {healthy_count} healthy, "
            f"{suspect_count} suspect, {unhealthy_count} unhealthy "
            f"/ {len(enabled_sources)} total"
        )

        return report

    def _check_single_source(self, source: dict) -> HealthCheckResult:
        """
        Validate a single source URL.

        1. HEAD request (allow_redirects=True)
        2. Classify by status code and content type
        3. Track redirect chain
        """
        url = source.get("rss_feed") or source.get("api_endpoint", "")
        name = source.get("name", "Unknown")

        result = HealthCheckResult(name=name, url=url)

        try:
            start = time.monotonic()
            resp = requests.head(
                url,
                timeout=self.HEAD_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": "Environmental-Scanning-HealthCheck/1.0"},
            )
            elapsed_ms = (time.monotonic() - start) * 1000

            result.status_code = resp.status_code
            result.response_time_ms = round(elapsed_ms, 1)
            result.content_type = resp.headers.get("Content-Type", "")

            # Track redirect chain
            if resp.history:
                result.redirect_chain = [r.url for r in resp.history] + [resp.url]

            # Classify health
            result.health, result.reason = self._classify_health(
                resp.status_code,
                result.content_type or "",
                result.redirect_chain,
            )

        except requests.exceptions.Timeout:
            result.health = "unhealthy"
            result.reason = "timeout"
            result.error = f"HEAD request timed out after {self.HEAD_TIMEOUT}s"

        except requests.exceptions.ConnectionError as e:
            result.health = "unhealthy"
            result.reason = "connection_error"
            result.error = str(e)[:200]

        except requests.exceptions.RequestException as e:
            result.health = "unhealthy"
            result.reason = "request_error"
            result.error = str(e)[:200]

        return result

    def _classify_health(
        self,
        status_code: int,
        content_type: str,
        redirect_chain: list[str],
    ) -> tuple[str, str]:
        """
        Classify source health based on HTTP response characteristics.

        Returns:
            (health_status, reason) tuple.
        """
        ct_lower = content_type.lower()

        if status_code == 200:
            # Check content type
            if any(rss_ct in ct_lower for rss_ct in self.RSS_CONTENT_TYPES):
                return ("healthy", "ok")
            if "text/html" in ct_lower:
                # HTML response — might be a redirect to a webpage
                return ("suspect", "redirect_to_html")
            # Unknown content type but 200 — give benefit of the doubt
            return ("healthy", "ok")

        if status_code in (301, 302, 307, 308):
            # Redirect that wasn't followed (shouldn't happen with allow_redirects)
            return ("suspect", "redirect_unresolved")

        if status_code == 403:
            return ("unhealthy", "bot_blocked")

        if status_code == 404:
            return ("unhealthy", "url_moved")

        if status_code == 410:
            return ("unhealthy", "url_gone")

        if 500 <= status_code < 600:
            return ("unhealthy", "server_error")

        if status_code == 429:
            return ("suspect", "rate_limited")

        # Other status codes
        if 400 <= status_code < 500:
            return ("unhealthy", f"client_error_{status_code}")

        return ("suspect", f"unexpected_status_{status_code}")

    def save_report(self, report: dict) -> str:
        """Save health report to health/reports/health-{date}.json."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_path = self.health_dir / "reports" / f"health-{date_str}.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(report_path)

    def append_history(self, report: dict) -> None:
        """Append a one-line summary to health/health-history.jsonl for time-series tracking."""
        history_path = self.health_dir / "health-history.jsonl"

        # Compact per-source record
        compact = {
            "checked_at": report["checked_at"],
            "healthy": report["healthy"],
            "unhealthy": report["unhealthy"],
            "suspect": report.get("suspect", 0),
            "total": report["total"],
            "sources": {
                name: {
                    "health": info["health"],
                    "reason": info["reason"],
                    "status_code": info.get("status_code"),
                }
                for name, info in report.get("sources", {}).items()
            },
        }

        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(compact, ensure_ascii=False) + "\n")

    def get_disabled_sources(self, report: dict) -> list[str]:
        """Return names of unhealthy sources (to be skipped at runtime)."""
        disabled = []
        for name, info in report.get("sources", {}).items():
            if info.get("health") == "unhealthy":
                disabled.append(name)
        return disabled
