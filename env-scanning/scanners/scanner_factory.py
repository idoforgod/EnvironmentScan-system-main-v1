"""
Scanner Factory
Creates scanner instances based on configuration
"""

from typing import Dict, Any, List, Optional
from .base_scanner import BaseScanner


class ScannerFactory:
    """
    Factory class for creating scanner instances

    Usage:
        # Single scanner
        config = {"name": "arXiv", "type": "academic", ...}
        scanner = ScannerFactory.create_scanner(config)

        # All scanners from sources.yaml
        sources_config = [{"name": "arXiv", ...}, {"name": "Google Scholar", ...}]
        scanners = ScannerFactory.create_all_scanners(sources_config)
    """

    # Registry: source_type -> {source_name -> ScannerClass}
    SCANNER_REGISTRY: Dict[str, Dict[str, type]] = {}

    @classmethod
    def register_scanner(cls, source_type: str, source_name: str, scanner_class: type):
        """
        Register a scanner class

        Args:
            source_type: Source type (academic, patent, policy, blog)
            source_name: Source name (arXiv, Google Scholar, etc.)
            scanner_class: Scanner class (must inherit from BaseScanner)
        """
        if source_type not in cls.SCANNER_REGISTRY:
            cls.SCANNER_REGISTRY[source_type] = {}

        cls.SCANNER_REGISTRY[source_type][source_name] = scanner_class

    @classmethod
    def create_scanner(cls, config: Dict[str, Any]) -> BaseScanner:
        """
        Create a scanner instance from configuration

        Args:
            config: Scanner configuration
                Required: name, type
                Optional: enabled, rate_limit, timeout, etc.

        Returns:
            Scanner instance (BaseScanner subclass)

        Raises:
            ValueError: If source type or name is not supported
        """
        source_type = config.get('type')
        source_name = config.get('name')

        if not source_type or not source_name:
            raise ValueError("Configuration must include 'type' and 'name'")

        # Check if source type is registered
        if source_type not in cls.SCANNER_REGISTRY:
            raise ValueError(f"Unsupported source type: {source_type}")

        # Check if source name is registered
        type_scanners = cls.SCANNER_REGISTRY[source_type]
        if source_name not in type_scanners:
            raise ValueError(
                f"Unsupported source: {source_name} (type: {source_type})\n"
                f"Available {source_type} scanners: {list(type_scanners.keys())}"
            )

        # Create scanner instance
        scanner_class = type_scanners[source_name]
        scanner = scanner_class(config)

        return scanner

    @classmethod
    def create_all_scanners(
        cls,
        sources_config: List[Dict[str, Any]],
        skip_sources: Optional[List[str]] = None,
    ) -> List[BaseScanner]:
        """
        Create all enabled scanners from sources configuration

        Args:
            sources_config: List of source configurations from sources.yaml
            skip_sources: Optional list of source names to skip
                (e.g. unhealthy sources from health check)

        Returns:
            List of enabled scanner instances

        Note:
            - Disabled scanners are skipped
            - Sources in skip_sources are skipped (runtime health disabling)
            - Invalid configurations are logged and skipped
            - Unsupported sources are logged and skipped
        """
        scanners = []
        skip_set = set(skip_sources or [])

        for source_config in sources_config:
            name = source_config.get('name', 'unknown')

            # Skip disabled sources
            if not source_config.get('enabled', True):
                print(f"[INFO] Skipping disabled source: {name}")
                continue

            # Skip sources flagged as unhealthy by health checker
            if name in skip_set:
                print(f"[HEALTH] Skipping unhealthy source: {name}")
                continue

            try:
                # Create scanner
                scanner = cls.create_scanner(source_config)

                # Validate configuration
                if not scanner.validate_config():
                    print(f"[WARNING] Invalid configuration for {scanner.get_name()}, skipping")
                    continue

                scanners.append(scanner)

            except ValueError as e:
                print(f"[WARNING] {e}")
                continue

            except Exception as e:
                print(f"[ERROR] Failed to create scanner for {name}: {e}")
                continue

        return scanners

    @classmethod
    def get_registered_scanners(cls) -> Dict[str, List[str]]:
        """
        Get list of all registered scanners

        Returns:
            Dictionary mapping source types to available scanner names
        """
        return {
            source_type: list(scanners.keys())
            for source_type, scanners in cls.SCANNER_REGISTRY.items()
        }

    @classmethod
    def is_source_supported(cls, source_type: str, source_name: str) -> bool:
        """
        Check if a source is supported

        Args:
            source_type: Source type (academic, patent, etc.)
            source_name: Source name (arXiv, etc.)

        Returns:
            True if source is supported
        """
        return (source_type in cls.SCANNER_REGISTRY and
                source_name in cls.SCANNER_REGISTRY[source_type])


# Auto-register scanners when module is imported
def _register_default_scanners():
    """Register default scanners"""
    # Academic sources
    try:
        from .arxiv_scanner import ArXivScanner
        ScannerFactory.register_scanner('academic', 'arXiv', ArXivScanner)
    except ImportError as e:
        print(f"[WARNING] Failed to register arXiv scanner: {e}")

    # RSS-based sources (academic, policy, blog)
    try:
        from .rss_scanner import RSSScanner

        # Academic RSS — Base
        ScannerFactory.register_scanner('academic', 'SSRN', RSSScanner)
        # Academic RSS — Expansion
        ScannerFactory.register_scanner('academic', 'PubMed Central', RSSScanner)
        ScannerFactory.register_scanner('academic', 'Nature News', RSSScanner)
        ScannerFactory.register_scanner('academic', 'Science Magazine', RSSScanner)
        ScannerFactory.register_scanner('academic', 'IEEE Spectrum', RSSScanner)

        # Policy RSS — Base
        ScannerFactory.register_scanner('policy', 'EU Press Releases', RSSScanner)
        ScannerFactory.register_scanner('policy', 'WHO Press Releases', RSSScanner)
        # Policy RSS — Expansion
        ScannerFactory.register_scanner('policy', 'OECD Newsroom', RSSScanner)
        ScannerFactory.register_scanner('policy', 'World Bank Blogs', RSSScanner)
        ScannerFactory.register_scanner('policy', 'UN News', RSSScanner)
        ScannerFactory.register_scanner('policy', 'EUR-Lex Recent Acts', RSSScanner)
        ScannerFactory.register_scanner('policy', 'NASA Climate Change', RSSScanner)
        ScannerFactory.register_scanner('policy', 'BIS Speeches', RSSScanner)

        # Blog RSS — Base
        ScannerFactory.register_scanner('blog', 'TechCrunch', RSSScanner)
        ScannerFactory.register_scanner('blog', 'MIT Technology Review', RSSScanner)
        ScannerFactory.register_scanner('blog', 'The Economist - Technology', RSSScanner)
        # Blog RSS — Expansion
        ScannerFactory.register_scanner('blog', 'Brookings Institution', RSSScanner)
        ScannerFactory.register_scanner('blog', 'World Economic Forum', RSSScanner)
        ScannerFactory.register_scanner('blog', 'Pew Research Center', RSSScanner)
        ScannerFactory.register_scanner('blog', 'Hacker News', RSSScanner)
        ScannerFactory.register_scanner('blog', 'Wired', RSSScanner)
        ScannerFactory.register_scanner('blog', 'Ars Technica', RSSScanner)
        ScannerFactory.register_scanner('blog', 'Carbon Brief', RSSScanner)
        ScannerFactory.register_scanner('blog', 'IMF Blog', RSSScanner)

    except ImportError as e:
        print(f"[WARNING] Failed to register RSS scanners: {e}")

    # API-based policy sources
    try:
        from .federal_register_scanner import FederalRegisterScanner
        ScannerFactory.register_scanner('policy', 'US Federal Register', FederalRegisterScanner)
    except ImportError as e:
        print(f"[WARNING] Failed to register Federal Register scanner: {e}")

    # Future scanners
    # from .scholar_scanner import GoogleScholarScanner
    # ScannerFactory.register_scanner('academic', 'Google Scholar', GoogleScholarScanner)

    # from .patent_scanner import GooglePatentsScanner
    # ScannerFactory.register_scanner('patent', 'Google Patents', GooglePatentsScanner)


# Register scanners on module import
_register_default_scanners()
