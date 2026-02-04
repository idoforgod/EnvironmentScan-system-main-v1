"""
Base Scanner Abstract Class
Defines the interface for all source scanners
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging


class BaseScanner(ABC):
    """
    Abstract base class for all source scanners

    Each scanner must implement:
    - scan(): Collect signals from the source
    - to_standard_format(): Convert source-specific data to standard signal format

    Standard Signal Format:
    {
        "id": "source-identifier",
        "title": "Signal title",
        "source": {
            "name": "Source name",
            "type": "academic|patent|policy|blog",
            "url": "https://...",
            "published_date": "YYYY-MM-DD"
        },
        "content": {
            "abstract": "Signal description...",
            "keywords": ["keyword1", "keyword2"],
            "language": "en"
        },
        "metadata": {
            # Source-specific additional fields
        },
        "preliminary_category": "S|T|E|P|s",
        "collected_at": "2026-01-30T09:00:00Z"
    }
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize scanner with configuration

        Args:
            config: Configuration dictionary from sources.yaml
                Required fields: name, type
                Optional fields: enabled, rate_limit, timeout, critical, etc.
        """
        self.config = config
        self.name = config['name']
        self.source_type = config['type']
        self.enabled = config.get('enabled', True)
        self.rate_limit = config.get('rate_limit', None)
        self.timeout = config.get('timeout', 30)
        self.critical = config.get('critical', False)
        self.max_results = config.get('max_results', 50)

        # Setup logging
        self.logger = logging.getLogger(f"scanner.{self.name}")

    @abstractmethod
    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Scan the source for signals

        Args:
            steeps_domains: STEEPs category definitions from domains.yaml
                Format: {"S_Social": ["keyword1", ...], "T_Technological": [...], ...}
            days_back: How many days back to scan (default: 7)

        Returns:
            List of signals in standard format

        Raises:
            Exception: Source-specific errors (network, API, etc.)
        """
        pass

    def is_enabled(self) -> bool:
        """Check if scanner is enabled"""
        return self.enabled

    def is_critical(self) -> bool:
        """Check if scanner is critical (failure should halt workflow)"""
        return self.critical

    def get_name(self) -> str:
        """Get scanner name"""
        return self.name

    def get_source_type(self) -> str:
        """Get source type (academic, patent, policy, blog)"""
        return self.source_type

    def validate_config(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid
        """
        required_fields = ['name', 'type']

        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"Missing required field: {field}")
                return False

        # Validate source type
        valid_types = ['academic', 'patent', 'policy', 'blog']
        if self.source_type not in valid_types:
            self.logger.error(f"Invalid source type: {self.source_type}")
            return False

        return True

    def log_info(self, message: str):
        """Log info message"""
        print(f"[INFO] {self.name}: {message}")

    def log_warning(self, message: str):
        """Log warning message"""
        print(f"[WARNING] {self.name}: {message}")

    def log_error(self, message: str):
        """Log error message"""
        print(f"[ERROR] {self.name}: {message}")

    def log_success(self, message: str):
        """Log success message"""
        print(f"[SUCCESS] {self.name}: {message}")

    def calculate_date_range(self, days_back: int) -> tuple:
        """
        Calculate date range for scanning

        Args:
            days_back: Number of days to go back

        Returns:
            Tuple of (start_date, end_date) as datetime objects
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return start_date, end_date

    def format_date(self, date: datetime, format_str: str = "%Y-%m-%d") -> str:
        """
        Format datetime to string

        Args:
            date: datetime object
            format_str: Format string (default: YYYY-MM-DD)

        Returns:
            Formatted date string
        """
        return date.strftime(format_str)

    def create_standard_signal(self,
                              signal_id: str,
                              title: str,
                              source_url: str,
                              published_date: str,
                              abstract: str,
                              keywords: List[str],
                              preliminary_category: str,
                              entities: Optional[List[str]] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to create a standard signal format

        Args:
            signal_id: Unique identifier
            title: Signal title
            source_url: URL to the source
            published_date: Publication date (YYYY-MM-DD)
            abstract: Signal description/abstract
            keywords: List of keywords
            preliminary_category: STEEPs category (S, T, E, P, s)
            entities: Optional list of named entities (organizations, technologies, etc.)
            metadata: Optional source-specific metadata

        Returns:
            Signal in standard format
        """
        signal = {
            "id": signal_id,
            "title": title,
            "source": {
                "name": self.name,
                "type": self.source_type,
                "url": source_url,
                "published_date": published_date
            },
            "content": {
                "abstract": abstract,
                "keywords": keywords[:10],  # Limit to 10 keywords
                "language": "en"  # Default to English, override in subclass if needed
            },
            "metadata": metadata or {},
            "preliminary_category": preliminary_category,
            "collected_at": datetime.now().isoformat()
        }

        # Add entities if provided
        if entities:
            signal["entities"] = entities

        return signal

    def __repr__(self) -> str:
        """String representation"""
        status = "enabled" if self.enabled else "disabled"
        critical = "critical" if self.critical else "non-critical"
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.source_type}', {status}, {critical})>"
