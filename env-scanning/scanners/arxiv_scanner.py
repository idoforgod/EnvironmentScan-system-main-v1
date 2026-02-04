"""
arXiv Academic Paper Scanner
Collects research papers from arXiv.org API
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import time
import re
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for entity extractor
sys.path.insert(0, str(Path(__file__).parent.parent))

from .base_scanner import BaseScanner
from utils.entity_extractor import EntityExtractor


class ArXivScanner(BaseScanner):
    """
    arXiv academic paper scanner

    API: http://export.arxiv.org/api/query
    Documentation: https://arxiv.org/help/api/user-manual
    Rate Limit: 1 request per 3 seconds (respectful usage)
    Authentication: Not required (open access)
    """

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 3  # seconds between requests

    # Map STEEPs categories to arXiv categories
    CATEGORY_MAPPING = {
        'T_Technological': [
            'cs.AI',  # Artificial Intelligence
            'cs.RO',  # Robotics
            'cs.CV',  # Computer Vision
            'cs.CL',  # Computation and Language
            'quant-ph',  # Quantum Physics
            'physics.bio-ph',  # Biological Physics
        ],
        'E_Economic': [
            'econ.EM',  # Econometrics
            'econ.GN',  # General Economics
            'q-fin.EC',  # Economics
            'q-fin.TR',  # Trading and Market Microstructure
        ],
        'E_Environmental': [
            'physics.ao-ph',  # Atmospheric and Oceanic Physics
            'physics.geo-ph',  # Geophysics
            'q-bio.PE',  # Populations and Evolution
        ],
        'S_Social': [
            'cs.CY',  # Computers and Society
            'cs.HC',  # Human-Computer Interaction
            'stat.AP',  # Applications (often social sciences)
        ],
        'P_Political': [
            'cs.CY',  # Computers and Society (policy aspects)
        ],
        's_spiritual': [
            'cs.CY',  # Ethical AI, societal impact
            'physics.soc-ph',  # Physics and Society
        ]
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize arXiv scanner

        Args:
            config: Configuration from sources.yaml
        """
        super().__init__(config)
        self.last_request_time = 0

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Scan arXiv for recent papers across all STEEPs categories

        Args:
            steeps_domains: STEEPs category definitions (not used - we use arXiv categories)
            days_back: Number of days to look back (not enforced by API)

        Returns:
            List of papers in standard signal format
        """
        self.log_info(f"Starting scan (last {days_back} days, max {self.max_results} per category)")

        all_papers = []

        # Scan each STEEPs category
        for steeps_category in self.CATEGORY_MAPPING.keys():
            papers = self._scan_category(steeps_category)
            all_papers.extend(papers)

            self.log_info(f"{steeps_category}: {len(papers)} papers collected")

        self.log_success(f"Total papers collected: {len(all_papers)}")

        return all_papers

    def _respect_rate_limit(self):
        """Enforce 3-second delay between API requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _scan_category(self, steeps_category: str) -> List[Dict[str, Any]]:
        """
        Scan arXiv for a specific STEEPs category

        Args:
            steeps_category: STEEPs category (T_Technological, E_Economic, etc.)

        Returns:
            List of papers in standard format
        """
        # Get arXiv categories for this STEEPs category
        arxiv_cats = self.CATEGORY_MAPPING.get(steeps_category, [])
        if not arxiv_cats:
            self.log_warning(f"No arXiv mapping for {steeps_category}")
            return []

        # Build query
        query = self._build_query(arxiv_cats)

        # Fetch papers
        papers = self._fetch_papers(query, self.max_results)

        # Convert to standard format
        return [self._to_standard_format(p, steeps_category) for p in papers]

    def _build_query(self, arxiv_categories: List[str]) -> str:
        """
        Build arXiv API query string

        Args:
            arxiv_categories: List of arXiv category codes

        Returns:
            URL-encoded query string
        """
        # Build category query (OR of all categories)
        cat_query = ' OR '.join([f'cat:{cat}' for cat in arxiv_categories])

        return urllib.parse.quote(cat_query)

    def _fetch_papers(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Fetch papers from arXiv API

        Args:
            query: URL-encoded query string
            max_results: Maximum number of results

        Returns:
            List of paper dictionaries
        """
        # Respect rate limit
        self._respect_rate_limit()

        # Build URL
        url = f"{self.BASE_URL}?search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

        try:
            # Create SSL context that doesn't verify certificates
            # arXiv is a trusted source, this is safe for our use case
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Make request
            with urllib.request.urlopen(url, timeout=self.timeout, context=ssl_context) as response:
                xml_content = response.read()

            # Parse XML
            root = ET.fromstring(xml_content)

            # Extract namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}

            papers = []
            entries = root.findall('atom:entry', ns)

            for entry in entries:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            self.log_error(f"API request failed: {e}")
            raise

    def _parse_entry(self, entry, ns) -> Dict[str, Any]:
        """
        Parse XML entry into paper dictionary

        Args:
            entry: XML entry element
            ns: XML namespaces

        Returns:
            Paper dictionary or None if parsing fails
        """
        try:
            # Required fields
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            id_elem = entry.find('atom:id', ns)

            # Check if all required elements exist
            if title_elem is None or summary_elem is None or published_elem is None or id_elem is None:
                return None

            if not title_elem.text or not summary_elem.text or not published_elem.text or not id_elem.text:
                return None

            # Clean title and abstract (remove extra whitespace)
            title = re.sub(r'\s+', ' ', title_elem.text.strip())
            abstract = re.sub(r'\s+', ' ', summary_elem.text.strip())

            # Extract arXiv ID from URL
            arxiv_url = id_elem.text
            arxiv_id = arxiv_url.split('/')[-1]

            # Parse publication date
            pub_date = published_elem.text[:10]  # YYYY-MM-DD

            # Extract categories
            categories = []
            for cat_elem in entry.findall('arxiv:primary_category', ns):
                categories.append(cat_elem.get('term'))
            for cat_elem in entry.findall('atom:category', ns):
                categories.append(cat_elem.get('term'))

            # Extract authors
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
                "categories": list(set(categories))[:5],  # Deduplicate, max 5
                "authors": authors[:3],  # Max 3 authors
            }

        except Exception as e:
            self.log_warning(f"Failed to parse entry: {e}")
            return None

    def _to_standard_format(self, paper: Dict[str, Any], steeps_category: str) -> Dict[str, Any]:
        """
        Convert arXiv paper to standard signal format

        Args:
            paper: Raw paper data from arXiv
            steeps_category: STEEPs category (T_Technological, E_Economic, etc.)

        Returns:
            Signal in standard format
        """
        # Extract entities from title and abstract
        combined_text = f"{paper['title']} {paper['abstract']}"
        entities = EntityExtractor.extract(combined_text, max_entities=15)

        return self.create_standard_signal(
            signal_id=f"arxiv-{paper['arxiv_id']}",
            title=paper['title'],
            source_url=paper['url'],
            published_date=paper['published_date'],
            abstract=paper['abstract'],
            keywords=paper['categories'],
            entities=entities,  # Add extracted entities
            preliminary_category=steeps_category[0],  # First letter (T, E, S, P, s)
            metadata={
                "arxiv_id": paper['arxiv_id'],
                "authors": paper['authors'],
                "arxiv_categories": paper['categories']
            }
        )
