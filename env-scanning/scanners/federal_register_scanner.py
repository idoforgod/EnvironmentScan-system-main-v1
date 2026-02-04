"""
US Federal Register API Scanner
Scans federal regulations and policy documents
"""

import requests
from typing import List, Dict, Any
from datetime import datetime
from .base_scanner import BaseScanner
import hashlib


class FederalRegisterScanner(BaseScanner):
    """
    US Federal Register API scanner

    Scans regulatory documents from federalregister.gov API

    Configuration:
        name: "US Federal Register"
        type: "policy"
        api_endpoint: "https://www.federalregister.gov/api/v1/documents"
        rate_limit: 1000  # per hour
        timeout: 20
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Federal Register scanner"""
        super().__init__(config)

        self.api_endpoint = config.get('api_endpoint', 'https://www.federalregister.gov/api/v1/documents')

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Scan Federal Register for policy signals

        Args:
            steeps_domains: STEEPs category definitions
            days_back: How many days back to scan

        Returns:
            List of signals in standard format
        """
        self.log_info(f"Scanning Federal Register API")

        try:
            # Calculate date range
            start_date, end_date = self.calculate_date_range(days_back)

            # Query API
            params = {
                'conditions[publication_date][gte]': self.format_date(start_date),
                'conditions[publication_date][lte]': self.format_date(end_date),
                'per_page': min(self.max_results, 100),  # API limit: 100 per page
                'fields[]': ['title', 'abstract', 'html_url', 'publication_date',
                            'type', 'agencies', 'topics'],
                'order': 'newest'
            }

            response = requests.get(
                self.api_endpoint,
                params=params,
                timeout=self.timeout,
                headers={'User-Agent': 'Environmental-Scanning-Bot/1.0'}
            )
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            if not results:
                self.log_warning("No documents found")
                return []

            # Process documents
            signals = []
            for doc in results:
                try:
                    signal = self._process_document(doc, steeps_domains)
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    self.log_warning(f"Failed to process document: {e}")
                    continue

            self.log_success(f"Found {len(signals)} signals from last {days_back} days")
            return signals

        except requests.RequestException as e:
            self.log_error(f"API request failed: {e}")
            raise
        except Exception as e:
            self.log_error(f"Federal Register scan failed: {e}")
            raise

    def _process_document(self,
                         doc: Dict[str, Any],
                         steeps_domains: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Process a single Federal Register document

        Args:
            doc: Document data from API
            steeps_domains: STEEPs category definitions

        Returns:
            Signal in standard format
        """
        # Extract fields
        title = doc.get('title', 'Untitled Document').strip()
        abstract = doc.get('abstract', '')
        url = doc.get('html_url', '')
        published_date = doc.get('publication_date', '')

        # If no abstract, create one from metadata
        if not abstract:
            doc_type = doc.get('type', 'Document')
            agencies = doc.get('agencies', [])
            agency_names = [a.get('name', '') for a in agencies if isinstance(a, dict)]
            abstract = f"{doc_type} by {', '.join(agency_names) if agency_names else 'Federal Government'}"

        # Extract keywords
        keywords = self._extract_keywords(doc, title, abstract)

        # Determine category (most Federal Register docs are Political)
        preliminary_category = self._determine_category(
            title, abstract, keywords, steeps_domains
        )

        # Generate ID
        signal_id = self._generate_id(url, title)

        # Get agencies
        agencies = doc.get('agencies', [])
        agency_names = [a.get('name', '') for a in agencies if isinstance(a, dict)]

        # Create signal
        signal = self.create_standard_signal(
            signal_id=signal_id,
            title=title,
            source_url=url,
            published_date=published_date,
            abstract=abstract,
            keywords=keywords,
            preliminary_category=preliminary_category,
            metadata={
                'document_type': doc.get('type', 'Unknown'),
                'agencies': agency_names,
                'topics': doc.get('topics', [])
            }
        )

        return signal

    def _extract_keywords(self, doc: Dict[str, Any], title: str, abstract: str) -> List[str]:
        """
        Extract keywords from document

        Args:
            doc: Document data
            title: Document title
            abstract: Document abstract

        Returns:
            List of keywords
        """
        keywords = []

        # Add topics as keywords
        topics = doc.get('topics', [])
        for topic in topics:
            if isinstance(topic, dict):
                keywords.append(topic.get('name', '').lower())
            elif isinstance(topic, str):
                keywords.append(topic.lower())

        # Add agencies as keywords
        agencies = doc.get('agencies', [])
        for agency in agencies:
            if isinstance(agency, dict):
                name = agency.get('name', '')
                if name:
                    keywords.append(name.lower())

        # If still no keywords, extract from text
        if not keywords:
            text = f"{title} {abstract}".lower()
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
            words = [w for w in text.split() if len(w) > 3 and w not in stopwords][:10]
            keywords.extend(words)

        return keywords[:10]  # Limit to 10

    def _determine_category(self,
                           title: str,
                           abstract: str,
                           keywords: List[str],
                           steeps_domains: Dict[str, List[str]]) -> str:
        """
        Determine preliminary STEEPs category

        Federal Register documents are typically Political (P),
        but can also be Environmental (E), Economic (E), or Social (S)

        Args:
            title: Document title
            abstract: Document abstract
            keywords: Document keywords
            steeps_domains: STEEPs category definitions

        Returns:
            STEEPs category
        """
        # Combine all text
        text = f"{title} {abstract} {' '.join(keywords)}".lower()

        # Score each category
        category_scores = {}

        for category_key, category_keywords in steeps_domains.items():
            category = category_key.split('_')[0]
            score = sum(1 for kw in category_keywords if kw.lower() in text)
            category_scores[category] = score

        # Get best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category

        # Default: P (Political) - most Federal Register docs are regulatory/policy
        return 'P'

    def _generate_id(self, url: str, title: str) -> str:
        """
        Generate unique signal ID

        Args:
            url: Document URL
            title: Document title

        Returns:
            Unique ID
        """
        unique_string = url if url else title
        hash_obj = hashlib.md5(unique_string.encode())
        return f"federal-register-{hash_obj.hexdigest()[:12]}"
