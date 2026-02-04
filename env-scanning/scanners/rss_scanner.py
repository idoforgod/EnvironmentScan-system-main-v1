"""
RSS Feed Scanner
Generic scanner for RSS/Atom feeds
"""

import feedparser
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base_scanner import BaseScanner
import hashlib


class RSSScanner(BaseScanner):
    """
    Generic RSS/Atom feed scanner

    Supports any RSS/Atom feed URL

    Configuration:
        name: Source name
        type: Source type (academic, policy, blog)
        rss_feed: RSS/Atom feed URL
        timeout: Request timeout (default: 15)
        max_results: Maximum number of results (default: 50)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize RSS scanner"""
        super().__init__(config)

        # Get RSS feed URL
        self.rss_feed = config.get('rss_feed')
        if not self.rss_feed:
            raise ValueError(f"RSS feed URL not provided for {self.name}")

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Scan RSS feed for signals

        Args:
            steeps_domains: STEEPs category definitions
            days_back: How many days back to scan

        Returns:
            List of signals in standard format
        """
        self.log_info(f"Scanning RSS feed: {self.rss_feed}")

        try:
            # Phase 1: Resolve URL through redirect tracker (System 2)
            feed_url = self._resolve_feed_url()

            # Phase 2: Fetch the resolved feed (with System 3 fallback)
            response = self._fetch_feed(feed_url)

            # Parse feed
            feed = feedparser.parse(response.content)

            if not feed.entries:
                self.log_warning("No entries found in feed")
                return []

            # Calculate date range
            start_date, end_date = self.calculate_date_range(days_back)

            # Process entries
            signals = []
            for entry in feed.entries[:self.max_results]:
                try:
                    signal = self._process_entry(entry, start_date, end_date, steeps_domains)
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    self.log_warning(f"Failed to process entry: {e}")
                    continue

            self.log_success(f"Found {len(signals)} signals from last {days_back} days")
            return signals

        except requests.RequestException as e:
            self.log_error(f"Failed to fetch RSS feed: {e}")
            raise
        except Exception as e:
            self.log_error(f"RSS scan failed: {e}")
            raise

    def _resolve_feed_url(self) -> str:
        """
        Use RedirectResolver (System 2) to find the actual RSS feed URL.
        Falls back to the original URL if resolution fails.
        """
        try:
            from core.redirect_resolver import RedirectResolver

            resolver = RedirectResolver(cache_path='health/redirect-cache.json')
            result = resolver.resolve(self.rss_feed, timeout=self.timeout)

            if result.status == "rss_found":
                if result.resolved_url != self.rss_feed:
                    self.log_info(f"Resolved URL: {result.resolved_url}")
                return result.resolved_url

            if result.status == "html_with_alternate" and result.alternate_feeds:
                feed_url = result.alternate_feeds[0]
                self.log_info(f"Auto-discovered RSS feed: {feed_url}")
                return feed_url

            if result.status == "error":
                self.log_warning(f"URL resolution failed: {result.error}")

        except ImportError:
            self.log_warning("RedirectResolver not available, using original URL")
        except Exception as e:
            self.log_warning(f"URL resolution error: {e}")

        return self.rss_feed

    def _fetch_feed(self, url: str) -> requests.Response:
        """
        Fetch RSS feed with System 3 adaptive fallback.

        1st attempt: Standard request
        2nd attempt (on 403): AdaptiveFetcher strategy chain
        """
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={'User-Agent': 'Environmental-Scanning-Bot/1.0'}
            )
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                self.log_warning("403 Forbidden — activating adaptive fetcher")
                return self._adaptive_fetch(url)
            raise

    def _adaptive_fetch(self, url: str) -> requests.Response:
        """
        Delegate to AdaptiveFetcher (System 3) for anti-bot bypass.
        """
        try:
            from core.adaptive_fetcher import AdaptiveFetcher

            fetcher = AdaptiveFetcher(
                strategy_cache_path='health/strategy-cache.json'
            )
            result = fetcher.fetch(
                url=url,
                timeout=self.timeout * 2,
                source_name=self.name,
            )

            if result.success:
                self.log_success(
                    f"Adaptive fetch succeeded with {result.strategy_used} "
                    f"after {result.attempts} attempts"
                )
                mock_response = requests.models.Response()
                mock_response.status_code = result.status_code
                mock_response._content = result.content
                return mock_response

            self.log_error(
                f"All adaptive strategies failed after "
                f"{result.attempts} attempts"
            )
            raise requests.exceptions.HTTPError(
                f"Adaptive fetch failed for {url}",
                response=requests.models.Response(),
            )

        except ImportError:
            self.log_warning("AdaptiveFetcher not available")
            raise requests.exceptions.HTTPError(
                f"403 Forbidden and no adaptive fetcher available for {url}",
                response=requests.models.Response(),
            )

    def _process_entry(self,
                       entry,
                       start_date: datetime,
                       end_date: datetime,
                       steeps_domains: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Process a single RSS entry

        Args:
            entry: feedparser entry object
            start_date: Filter start date
            end_date: Filter end date
            steeps_domains: STEEPs category definitions

        Returns:
            Signal in standard format, or None if entry should be filtered
        """
        # Get publication date
        published_date = self._parse_date(entry)
        if not published_date:
            return None

        # Filter by date
        if published_date < start_date or published_date > end_date:
            return None

        # Extract fields
        title = entry.get('title', 'No title').strip()
        link = entry.get('link', '')

        # Get description (try multiple fields)
        abstract = (
            entry.get('summary', '') or
            entry.get('description', '') or
            entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
        )
        abstract = self._clean_html(abstract).strip()

        # If no abstract, use title
        if not abstract:
            abstract = title

        # Extract keywords (from tags if available)
        keywords = self._extract_keywords(entry, title, abstract)

        # Determine preliminary category
        preliminary_category = self._determine_category(
            title, abstract, keywords, steeps_domains
        )

        # Create unique ID
        signal_id = self._generate_id(link, title, published_date)

        # Create signal
        signal = self.create_standard_signal(
            signal_id=signal_id,
            title=title,
            source_url=link,
            published_date=self.format_date(published_date),
            abstract=abstract,
            keywords=keywords,
            preliminary_category=preliminary_category,
            metadata={
                'feed_source': self.rss_feed,
                'author': entry.get('author', 'Unknown')
            }
        )

        return signal

    def _parse_date(self, entry) -> datetime:
        """
        Parse publication date from entry

        Args:
            entry: feedparser entry

        Returns:
            datetime object or None
        """
        # Try multiple date fields
        date_struct = (
            entry.get('published_parsed') or
            entry.get('updated_parsed') or
            entry.get('created_parsed')
        )

        if date_struct:
            try:
                return datetime(*date_struct[:6])
            except:
                pass

        # Fallback: use current date
        return datetime.now()

    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text

        Args:
            text: Text with HTML tags

        Returns:
            Clean text
        """
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_keywords(self, entry, title: str, abstract: str) -> List[str]:
        """
        Extract keywords from entry

        Args:
            entry: feedparser entry
            title: Entry title
            abstract: Entry abstract

        Returns:
            List of keywords
        """
        keywords = []

        # Get tags if available
        if 'tags' in entry:
            for tag in entry.tags:
                if 'term' in tag:
                    keywords.append(tag['term'].lower())

        # If no tags, extract from title/abstract
        if not keywords:
            # Simple keyword extraction (can be improved with NLP)
            text = f"{title} {abstract}".lower()
            # Remove common words
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
            words = text.split()
            keywords = [w for w in words if len(w) > 3 and w not in stopwords][:10]

        return keywords

    def _determine_category(self,
                           title: str,
                           abstract: str,
                           keywords: List[str],
                           steeps_domains: Dict[str, List[str]]) -> str:
        """
        Determine preliminary STEEPs category

        Args:
            title: Signal title
            abstract: Signal abstract
            keywords: Signal keywords
            steeps_domains: STEEPs category definitions

        Returns:
            STEEPs category (S, T, E, P, s)
        """
        # Combine all text
        text = f"{title} {abstract} {' '.join(keywords)}".lower()

        # Score each category
        category_scores = {}

        for category_key, category_keywords in steeps_domains.items():
            # Extract category letter (e.g., "S" from "S_Social")
            category = category_key.split('_')[0]

            # Count keyword matches
            score = sum(1 for kw in category_keywords if kw.lower() in text)
            category_scores[category] = score

        # Get category with highest score
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category

        # Default: T (Technological) for tech sources, P (Political) for policy sources
        if self.source_type == 'policy':
            return 'P'
        elif self.source_type == 'blog':
            return 'T'
        else:
            return 'E'  # Default to E (Economic/Environmental)

    def _generate_id(self, url: str, title: str, date: datetime) -> str:
        """
        Generate unique signal ID

        Args:
            url: Source URL
            title: Signal title
            date: Publication date

        Returns:
            Unique ID string
        """
        # Use URL if available, otherwise use title + date
        if url:
            unique_string = url
        else:
            unique_string = f"{title}_{date.isoformat()}"

        # Create hash
        hash_obj = hashlib.md5(unique_string.encode())
        return f"{self.name.lower().replace(' ', '-')}-{hash_obj.hexdigest()[:12]}"

    def validate_config(self) -> bool:
        """Validate RSS scanner configuration"""
        if not super().validate_config():
            return False

        if not self.rss_feed:
            self.log_error("RSS feed URL is required")
            return False

        return True
