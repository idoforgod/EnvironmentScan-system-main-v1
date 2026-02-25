"""
arXiv Academic Paper Scanner (v2.0.0)
Collects research papers from arXiv.org API with full taxonomy coverage.

v2.0.0 Changes:
  - Reads query_groups and category_steeps_mapping from config (sources-arxiv.yaml)
  - Removes hardcoded CATEGORY_MAPPING
  - Adds submittedDate range filtering to API query
  - Supports dynamic max_results per query group
  - Cross-group deduplication by arxiv_id
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import time
import re
import sys
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for entity extractor
sys.path.insert(0, str(Path(__file__).parent.parent))

from .base_scanner import BaseScanner
from utils.entity_extractor import EntityExtractor


class ArXivScanner(BaseScanner):
    """
    arXiv academic paper scanner with full taxonomy coverage.

    API: http://export.arxiv.org/api/query
    Documentation: https://arxiv.org/help/api/user-manual
    Rate Limit: 1 request per 3 seconds (respectful usage)
    Authentication: Not required (open access)

    v2.0.0: Reads query groups from config, covers all ~180 arXiv categories.
    """

    BASE_URL = "https://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 3  # seconds between requests

    # Fallback mapping used ONLY if config has no query_groups (backward compat)
    _FALLBACK_CATEGORY_MAPPING = {
        'T_Technological': ['cs.AI', 'cs.RO', 'cs.CV', 'cs.CL', 'quant-ph', 'physics.bio-ph'],
        'E_Economic': ['econ.EM', 'econ.GN', 'q-fin.EC', 'q-fin.TR'],
        'E_Environmental': ['physics.ao-ph', 'physics.geo-ph', 'q-bio.PE'],
        'S_Social': ['cs.CY', 'cs.HC', 'stat.AP'],
        'P_Political': ['cs.CY'],
        's_spiritual': ['cs.CY', 'physics.soc-ph'],
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.last_request_time = 0
        self.use_date_filter = config.get('use_date_filter_in_query', False)
        self._query_groups = config.get('query_groups', None)
        self._steeps_mapping = config.get('category_steeps_mapping', {})

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7,
             lookback_hours: int = None,
             scan_window_start: datetime = None,
             scan_window_end: datetime = None) -> List[Dict[str, Any]]:
        """
        Scan arXiv for recent papers across all categories.

        If config provides query_groups, uses group-based scanning (v2.0.0).
        Otherwise falls back to legacy CATEGORY_MAPPING.
        """
        window_start, window_end = self.calculate_date_range(
            days_back=days_back,
            lookback_hours=lookback_hours,
            scan_window_start=scan_window_start,
            scan_window_end=scan_window_end
        )
        self.log_info(f"Starting scan (window: {window_start} to {window_end})")

        if self._query_groups:
            all_papers = self._scan_by_query_groups(window_start, window_end)
        else:
            self.log_warning("No query_groups in config — using fallback CATEGORY_MAPPING")
            all_papers = self._scan_by_legacy_mapping()

        self.log_info(f"Pre-filter total: {len(all_papers)} papers")

        # TC-003: Post-collection temporal filter (mandatory even with API date filter)
        all_papers = self.filter_by_scan_window(
            all_papers,
            window_start=window_start,
            window_end=window_end,
            tolerance_minutes=60  # arXiv: wider tolerance due to batch posting
        )

        self.log_success(f"Post-filter total: {len(all_papers)} papers (within scan window)")
        return all_papers

    # ─── v2.0.0: Config-driven query group scanning ───

    def _scan_by_query_groups(self, window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
        """Scan using query_groups from config. Each group = 1 API call."""
        all_papers = []
        seen_arxiv_ids = set()
        total_groups = len(self._query_groups)

        for i, group in enumerate(self._query_groups, 1):
            group_name = group.get('name', f'group-{i}')
            categories = group.get('categories', [])
            max_results = group.get('max_results', self.max_results)

            if not categories:
                self.log_warning(f"[{group_name}] No categories defined, skipping")
                continue

            self.log_info(f"[{i}/{total_groups}] {group_name}: {len(categories)} categories, max={max_results}")

            query = self._build_query(categories, window_start, window_end)
            raw_papers = self._fetch_papers(query, max_results)

            # Dedup across groups by arxiv_id
            new_count = 0
            for paper in raw_papers:
                arxiv_id = paper.get('arxiv_id', '')
                if arxiv_id not in seen_arxiv_ids:
                    seen_arxiv_ids.add(arxiv_id)
                    # Assign primary STEEPs from config mapping
                    steeps = self._resolve_steeps(paper.get('categories', []))
                    signal = self._to_standard_format(paper, steeps)
                    all_papers.append(signal)
                    new_count += 1

            self.log_info(f"[{group_name}] {len(raw_papers)} fetched, {new_count} new (after cross-group dedup)")

        self.log_info(f"Total unique papers from {total_groups} groups: {len(all_papers)}")
        return all_papers

    def _resolve_steeps(self, arxiv_categories: List[str]) -> str:
        """
        Resolve primary STEEPs from paper's arXiv categories using config mapping.
        Uses the first matching category (primary_category is listed first).
        Falls back to 'T' if no mapping found.
        """
        for cat in arxiv_categories:
            if cat in self._steeps_mapping:
                steeps_code = self._steeps_mapping[cat]
                # Normalize to standard STEEPs prefix
                steeps_map = {
                    'T': 'T_Technological',
                    'E': 'E_Economic',
                    'E_Environmental': 'E_Environmental',
                    'S': 'S_Social',
                    'P': 'P_Political',
                    's': 's_spiritual',
                }
                return steeps_map.get(steeps_code, 'T_Technological')
        return 'T_Technological'  # Default for unmapped categories

    # ─── Legacy scanning (backward compatibility) ───

    def _scan_by_legacy_mapping(self) -> List[Dict[str, Any]]:
        """Fallback: scan using hardcoded CATEGORY_MAPPING."""
        all_papers = []
        for steeps_category, arxiv_cats in self._FALLBACK_CATEGORY_MAPPING.items():
            query = self._build_query(arxiv_cats)
            raw_papers = self._fetch_papers(query, self.max_results)
            papers = [self._to_standard_format(p, steeps_category) for p in raw_papers]
            all_papers.extend(papers)
            self.log_info(f"{steeps_category}: {len(papers)} papers collected")
        return all_papers

    # ─── Query building ───

    def _build_query(self, arxiv_categories: List[str],
                     window_start: datetime = None,
                     window_end: datetime = None) -> str:
        """
        Build arXiv API query string with optional date filtering.

        Args:
            arxiv_categories: List of arXiv category codes
            window_start: Scan window start (for submittedDate filter)
            window_end: Scan window end (for submittedDate filter)

        Returns:
            URL-encoded query string
        """
        # Category filter: OR of all categories
        cat_query = ' OR '.join([f'cat:{cat}' for cat in arxiv_categories])
        full_query = f'({cat_query})'

        # Add date filtering if enabled and window provided
        if self.use_date_filter and window_start and window_end:
            # arXiv API submittedDate format: YYYYMMDDHHMM
            # Use a slightly wider range to account for timezone issues
            date_start = (window_start - timedelta(hours=2)).strftime('%Y%m%d%H%M')
            date_end = (window_end + timedelta(hours=2)).strftime('%Y%m%d%H%M')
            full_query = f'{full_query} AND submittedDate:[{date_start} TO {date_end}]'

        return urllib.parse.quote(full_query)

    # ─── Rate limiting ───

    def _respect_rate_limit(self):
        """Enforce 3-second delay between API requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    # ─── API interaction ───

    def _fetch_papers(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv API."""
        self._respect_rate_limit()

        url = (f"{self.BASE_URL}?search_query={query}"
               f"&start=0&max_results={max_results}"
               f"&sortBy=submittedDate&sortOrder=descending")

        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(url, timeout=self.timeout, context=ssl_context) as response:
                xml_content = response.read()

            root = ET.fromstring(xml_content)
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}

            papers = []
            for entry in root.findall('atom:entry', ns):
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            self.log_error(f"API request failed: {e}")
            raise

    def _parse_entry(self, entry, ns) -> Dict[str, Any]:
        """Parse XML entry into paper dictionary."""
        try:
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            id_elem = entry.find('atom:id', ns)

            if title_elem is None or summary_elem is None or published_elem is None or id_elem is None:
                return None
            if not title_elem.text or not summary_elem.text or not published_elem.text or not id_elem.text:
                return None

            title = re.sub(r'\s+', ' ', title_elem.text.strip())
            abstract = re.sub(r'\s+', ' ', summary_elem.text.strip())

            arxiv_url = id_elem.text.replace('http://arxiv.org/', 'https://arxiv.org/')
            arxiv_id = arxiv_url.split('/')[-1]
            pub_date = published_elem.text[:10]  # YYYY-MM-DD

            # Extract categories — primary_category first
            categories = []
            primary_cat = entry.find('arxiv:primary_category', ns)
            if primary_cat is not None:
                categories.append(primary_cat.get('term'))
            for cat_elem in entry.findall('atom:category', ns):
                term = cat_elem.get('term')
                if term and term not in categories:
                    categories.append(term)

            authors = []
            for author_elem in entry.findall('atom:author', ns):
                name_elem = author_elem.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text)

            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "url": arxiv_url,
                "published_date": pub_date,
                "categories": categories[:10],  # Keep more categories for better mapping
                "authors": authors[:5],
            }

        except Exception as e:
            self.log_warning(f"Failed to parse entry: {e}")
            return None

    def _to_standard_format(self, paper: Dict[str, Any], steeps_category: str) -> Dict[str, Any]:
        """Convert arXiv paper to standard signal format."""
        combined_text = f"{paper['title']} {paper['abstract']}"
        entities = EntityExtractor.extract(combined_text, max_entities=15)

        # Extract first letter for preliminary_category
        # Handle both 'T_Technological' and single-letter 'T' formats
        prelim_cat = steeps_category[0] if steeps_category else 'T'

        return self.create_standard_signal(
            signal_id=f"arxiv-{paper['arxiv_id']}",
            title=paper['title'],
            source_url=paper['url'],
            published_date=paper['published_date'],
            abstract=paper['abstract'],
            keywords=paper['categories'],
            entities=entities,
            preliminary_category=prelim_cat,
            metadata={
                "arxiv_id": paper['arxiv_id'],
                "authors": paper['authors'],
                "arxiv_categories": paper['categories'],
                "steeps_mapping": steeps_category
            }
        )
