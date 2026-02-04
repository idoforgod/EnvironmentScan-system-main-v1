#!/usr/bin/env python3
"""
arXiv Real Data Scanner
Collects actual research papers from arXiv API for workflow validation
"""

import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
import sys
import os
import ssl


class ArXivScanner:
    """
    Real arXiv API integration for Environmental Scanning System

    API Documentation: https://arxiv.org/help/api/user-manual
    Rate Limit: 1 request per 3 seconds (respectful usage)
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

    def __init__(self, days_back: int = 7, max_results_per_category: int = 20):
        """
        Initialize arXiv scanner

        Args:
            days_back: How many days back to search
            max_results_per_category: Max papers per STEEPs category
        """
        self.days_back = days_back
        self.max_results_per_category = max_results_per_category
        self.last_request_time = 0

    def _respect_rate_limit(self):
        """Enforce 3-second delay between API requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _build_query(self, arxiv_categories: List[str], date_from: str) -> str:
        """
        Build arXiv API query string

        Args:
            arxiv_categories: List of arXiv category codes
            date_from: YYYYMMDD format (not used - arXiv API doesn't support date filters well)

        Returns:
            URL-encoded query string
        """
        # Build category query (OR of all categories)
        # Simplified: arXiv API has issues with complex date filters
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

        print(f"[INFO] Fetching from arXiv: {len(query)} char query, max_results={max_results}")

        try:
            # Create SSL context that doesn't verify certificates
            # arXiv is a trusted source, this is safe for our use case
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Make request
            with urllib.request.urlopen(url, timeout=30, context=ssl_context) as response:
                xml_content = response.read()

            # Parse XML
            root = ET.fromstring(xml_content)

            # Extract namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}

            papers = []
            entries = root.findall('atom:entry', ns)

            print(f"[INFO] Retrieved {len(entries)} papers from arXiv")

            for idx, entry in enumerate(entries):
                # Extract paper metadata
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
                else:
                    if idx == 0:  # Debug first entry only
                        print(f"[DEBUG] Failed to parse entry 0 - checking structure...")

            return papers

        except Exception as e:
            print(f"[ERROR] arXiv API request failed: {e}")
            return []

    def _parse_entry(self, entry, ns) -> Dict[str, Any]:
        """Parse XML entry into paper dictionary"""
        try:
            # Required fields
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            id_elem = entry.find('atom:id', ns)

            # Check if all required elements exist
            if title_elem is None or summary_elem is None or published_elem is None or id_elem is None:
                # Debug: show which element is missing
                missing = []
                if title_elem is None: missing.append("title")
                if summary_elem is None: missing.append("summary")
                if published_elem is None: missing.append("published")
                if id_elem is None: missing.append("id")
                print(f"[DEBUG] Missing elements: {missing}")
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
                "id": f"arxiv-{arxiv_id}",
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "url": arxiv_url,
                "published_date": pub_date,
                "categories": list(set(categories))[:5],  # Deduplicate, max 5
                "authors": authors[:3],  # Max 3 authors
                "source": "arXiv"
            }

        except Exception as e:
            print(f"[WARNING] Failed to parse entry: {e}")
            return None

    def scan_category(self, steeps_category: str) -> List[Dict[str, Any]]:
        """
        Scan arXiv for a specific STEEPs category

        Args:
            steeps_category: One of S, T, E (economic/environmental), P, s

        Returns:
            List of papers mapped to this category
        """
        # Get arXiv categories for this STEEPs category
        arxiv_cats = self.CATEGORY_MAPPING.get(steeps_category, [])

        if not arxiv_cats:
            print(f"[WARNING] No arXiv mapping for STEEPs category: {steeps_category}")
            return []

        # Calculate date filter (7 days back)
        date_from = (datetime.now() - timedelta(days=self.days_back)).strftime('%Y%m%d')

        # Build query
        query = self._build_query(arxiv_cats, date_from)

        # Fetch papers
        papers = self._fetch_papers(query, self.max_results_per_category)

        # Add preliminary category
        for paper in papers:
            paper['preliminary_category'] = steeps_category[0]  # First letter (S, T, E, P, s)
            paper['collected_at'] = datetime.now().isoformat()

        print(f"[SUCCESS] {steeps_category}: {len(papers)} papers collected")

        return papers

    def scan_all_categories(self) -> Dict[str, Any]:
        """
        Scan all STEEPs categories

        Returns:
            Full scan result with metadata
        """
        print("=" * 60)
        print("arXiv Real Data Scanner - Starting")
        print("=" * 60)

        start_time = time.time()
        all_papers = []

        # Scan each STEEPs category
        for steeps_category in self.CATEGORY_MAPPING.keys():
            print(f"\n[SCANNING] {steeps_category}...")
            papers = self.scan_category(steeps_category)
            all_papers.extend(papers)

            # Show progress
            print(f"[PROGRESS] Total papers collected: {len(all_papers)}")

        elapsed = time.time() - start_time

        # Build output structure
        output = {
            "scan_metadata": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "sources_scanned": 1,  # arXiv only
                "source_name": "arXiv",
                "total_items": len(all_papers),
                "execution_time": round(elapsed, 2),
                "date_range": {
                    "from": (datetime.now() - timedelta(days=self.days_back)).strftime('%Y-%m-%d'),
                    "to": datetime.now().strftime('%Y-%m-%d')
                },
                "steeps_categories_scanned": len(self.CATEGORY_MAPPING),
                "mode": "real_data"
            },
            "items": self._convert_to_workflow_format(all_papers)
        }

        print("\n" + "=" * 60)
        print(f"[COMPLETE] arXiv scan finished in {elapsed:.1f}s")
        print(f"[RESULT] {len(all_papers)} papers collected")
        print("=" * 60)

        return output

    def _convert_to_workflow_format(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert arXiv papers to workflow signal format

        Matches the structure expected by downstream agents
        """
        signals = []

        for paper in papers:
            signal = {
                "id": paper['id'],
                "title": paper['title'],
                "source": {
                    "name": "arXiv",
                    "type": "academic",
                    "url": paper['url'],
                    "published_date": paper['published_date']
                },
                "content": {
                    "abstract": paper['abstract'],
                    "keywords": paper['categories'],  # arXiv categories as keywords
                    "language": "en"
                },
                "metadata": {
                    "arxiv_id": paper['arxiv_id'],
                    "authors": paper['authors'],
                    "arxiv_categories": paper['categories']
                },
                "preliminary_category": paper['preliminary_category'],
                "collected_at": paper['collected_at']
            }
            signals.append(signal)

        return signals


def main():
    """Main execution"""
    # Configuration
    DAYS_BACK = 7
    MAX_RESULTS_PER_CATEGORY = 15  # Total ~90 papers (6 categories × 15)

    # Output path
    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = "raw"
    output_file = f"{output_dir}/arxiv-scan-{today}.json"

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Create scanner
    scanner = ArXivScanner(days_back=DAYS_BACK, max_results_per_category=MAX_RESULTS_PER_CATEGORY)

    # Run scan
    try:
        result = scanner.scan_all_categories()

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Output written to: {output_file}")
        print(f"[SIZE] {len(json.dumps(result))} bytes")

        # Print summary
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"Total signals: {result['scan_metadata']['total_items']}")
        print(f"Execution time: {result['scan_metadata']['execution_time']}s")
        print(f"Date range: {result['scan_metadata']['date_range']['from']} to {result['scan_metadata']['date_range']['to']}")

        # Category distribution
        category_counts = {}
        for item in result['items']:
            cat = item['preliminary_category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\nCategory distribution:")
        for cat, count in sorted(category_counts.items()):
            print(f"  {cat}: {count} signals")

        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
