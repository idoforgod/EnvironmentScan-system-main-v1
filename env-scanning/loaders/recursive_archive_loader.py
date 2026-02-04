"""
RecursiveArchiveLoader - Time-based archive loader with recursive filtering.

Memory Optimization: Loads only recent signals (7-day window) for deduplication.
Backward Compatible: Provides load_full_archive() method for complete data.

Usage Example:
    from env_scanning.loaders import RecursiveArchiveLoader

    # Initialize
    loader = RecursiveArchiveLoader(
        database_path=Path('env-scanning/signals/database.json'),
        archive_dir=Path('env-scanning/reports/archive/')
    )

    # Load recent signals (memory efficient)
    recent = loader.load_recent_index(days=7)
    print(f"Loaded {recent['metadata']['total_signals']} signals from last 7 days")

    # Legacy mode (full archive)
    full = loader.load_full_archive()
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timedelta
from urllib.parse import urlparse


class RecursiveArchiveLoader:
    """
    Time-based archive loader with recursive filtering.
    Loads only recent signals needed for deduplication.
    """

    def __init__(self, database_path: Path, archive_dir: Path):
        """
        Initialize RecursiveArchiveLoader.

        Args:
            database_path: Path to signals/database.json
            archive_dir: Path to reports/archive/ directory
        """
        self.database_path = Path(database_path)
        self.archive_dir = Path(archive_dir)

    def load_recent_index(self, days: int = 7) -> Dict[str, Any]:
        """
        PRIMARY METHOD: Load recent signals and build indexes.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            {
                "signals": [...],           # Recent signals only
                "index": {                  # Lookup indexes
                    "by_url": {...},
                    "by_title": {...},
                    "by_entities": {...}
                },
                "metadata": {
                    "total_signals": int,
                    "date_range": str,
                    "filter_ratio": float,    # e.g., 0.07 = loaded 7% of total
                    "last_updated": str
                }
            }
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Step 1: Load database
        database = self._load_database()

        # Step 2: Filter by date (RECURSIVE FILTERING)
        all_signals = database.get('signals', [])
        recent_signals = self._filter_by_date(all_signals, cutoff_date)

        # Step 3: Build indexes (only for recent signals)
        indexes = self._build_indexes(recent_signals)

        return {
            "signals": recent_signals,
            "index": indexes,
            "metadata": {
                "total_signals": len(recent_signals),
                "total_in_database": len(all_signals),
                "date_range": f"{cutoff_date.date()} to {datetime.now().date()}",
                "filter_ratio": len(recent_signals) / max(len(all_signals), 1),
                "filter_window_days": days,
                "last_updated": datetime.now().isoformat()
            }
        }

    def _load_database(self) -> Dict[str, Any]:
        """
        Load signals database.

        Returns:
            Database dictionary with 'signals' list
        """
        if not self.database_path.exists():
            return {"signals": [], "metadata": {"total_signals": 0}}

        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted database file: {e}")

    def _filter_by_date(self, signals: List[Dict], cutoff_date: datetime) -> List[Dict]:
        """
        Filter signals to those after cutoff_date.

        Args:
            signals: List of all signals
            cutoff_date: Cutoff datetime (signals before this are excluded)

        Returns:
            List of recent signals
        """
        recent = []
        for signal in signals:
            # Parse signal date (handle multiple date field names)
            # Try multiple field locations in order of preference
            signal_date_str = (
                signal.get('first_detected') or  # Legacy format
                signal.get('date') or             # Legacy format
                signal.get('collected_at') or     # New format (ISO datetime)
                signal.get('scan_date') or        # New format (date only)
                signal.get('added_to_db_at') or   # Fallback
                (signal.get('source', {}).get('published_date') if isinstance(signal.get('source'), dict) else None)  # Source published date
            )

            if not signal_date_str:
                # If no date field, skip this signal
                continue

            try:
                # Parse ISO format or common date formats
                signal_date = self._parse_date(signal_date_str)

                if signal_date >= cutoff_date:
                    recent.append(signal)
            except (ValueError, TypeError):
                # Skip signals with unparseable dates
                continue

        return recent

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string in various formats.

        Args:
            date_str: Date string (ISO 8601 or YYYY-MM-DD)

        Returns:
            datetime object
        """
        # Try ISO 8601 format first (with or without time)
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass

        # Try YYYY-MM-DD format
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass

        # Try other common formats
        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")

    def _build_indexes(self, signals: List[Dict]) -> Dict[str, Any]:
        """
        Build lookup indexes (same format as original archive-loader).
        CRITICAL: Output format must match exactly for deduplication-filter compatibility.

        Args:
            signals: List of signals to index

        Returns:
            Index dictionary with by_url, by_title, by_entities
        """
        index = {
            "by_url": {},
            "by_title": {},
            "by_entities": {}
        }

        for signal in signals:
            signal_id = signal.get('id', '')

            # URL index (exact match for Stage 1 deduplication)
            source = signal.get('source', {})
            if isinstance(source, dict):
                url = source.get('url', '')
            else:
                # Handle case where source is a string
                url = source if isinstance(source, str) else ''

            if url:
                normalized_url = self._normalize_url(url)
                index['by_url'][normalized_url] = signal_id

            # Title index (for Stage 2 string similarity)
            title = signal.get('title', '')
            if title:
                normalized_title = self._normalize_text(title)
                index['by_title'][normalized_title] = signal_id

            # Entity index (for Stage 4 entity matching)
            entities = signal.get('entities', [])
            if not isinstance(entities, list):
                entities = []

            for entity in entities:
                if entity not in index['by_entities']:
                    index['by_entities'][entity] = []
                index['by_entities'][entity].append(signal_id)

        return index

    def _normalize_url(self, url: str) -> str:
        """
        Remove protocol, www, trailing slashes, query params.

        Args:
            url: Original URL

        Returns:
            Normalized URL

        Example:
            https://www.example.com/page?id=1 -> example.com/page
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            path = parsed.path.rstrip('/')
            return f"{domain}{path}"
        except Exception:
            # If URL parsing fails, return lowercase original
            return url.lower()

    def _normalize_text(self, text: str) -> str:
        """
        Lowercase, remove punctuation, trim whitespace.

        Args:
            text: Original text

        Returns:
            Normalized text

        Example:
            "OpenAI Releases GPT-5!" -> "openai releases gpt5"
        """
        # Lowercase
        text = text.lower()

        # Remove punctuation (keep only alphanumeric and whitespace)
        text = re.sub(r'[^\w\s]', '', text)

        # Normalize whitespace
        text = ' '.join(text.split())

        return text

    def load_full_archive(self) -> Dict[str, Any]:
        """
        BACKWARD COMPATIBILITY: Load entire archive (legacy mode).
        Use this when time-based filtering is not appropriate.

        Returns:
            {
                "signals": [...],        # All signals
                "index": {...},          # Complete indexes
                "metadata": {...}
            }
        """
        # Load database
        database = self._load_database()
        all_signals = database.get('signals', [])

        # Build complete indexes
        indexes = self._build_indexes(all_signals)

        # Calculate date range
        if all_signals:
            dates = []
            for signal in all_signals:
                date_str = signal.get('first_detected') or signal.get('date')
                if date_str:
                    try:
                        dates.append(self._parse_date(date_str))
                    except ValueError:
                        pass

            if dates:
                min_date = min(dates).date()
                max_date = max(dates).date()
                date_range = f"{min_date} to {max_date}"
            else:
                date_range = "unknown"
        else:
            date_range = "no signals"

        return {
            "signals": all_signals,
            "index": indexes,
            "metadata": {
                "total_signals": len(all_signals),
                "date_range": date_range,
                "filter_ratio": 1.0,  # Full archive = 100%
                "last_updated": datetime.now().isoformat(),
                "mode": "full_archive"
            }
        }

    def load_archive_reports(self, days: int = 90) -> List[Dict[str, Any]]:
        """
        Load archive reports from last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of report dictionaries
        """
        if not self.archive_dir.exists():
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        reports = []

        # Find all JSON files in archive directory
        for report_file in self.archive_dir.rglob('*.json'):
            try:
                # Extract date from filename (e.g., environmental-scan-2026-01-30.json)
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', report_file.name)
                if date_match:
                    report_date = datetime(
                        int(date_match.group(1)),
                        int(date_match.group(2)),
                        int(date_match.group(3))
                    )

                    if report_date >= cutoff_date:
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report = json.load(f)
                            reports.append(report)
            except (json.JSONDecodeError, ValueError):
                # Skip corrupted files
                continue

        return reports

    def merge_signals(self, database_signals: List[Dict], archive_signals: List[Dict]) -> List[Dict]:
        """
        Merge signals from database and archive reports (deduplicating by URL).

        Args:
            database_signals: Signals from database.json
            archive_signals: Signals from archive reports

        Returns:
            Merged list of unique signals
        """
        all_signals = database_signals.copy()
        seen_urls = set()

        # Add URLs from database signals
        for signal in all_signals:
            source = signal.get('source', {})
            url = source.get('url', '') if isinstance(source, dict) else source
            if url:
                normalized_url = self._normalize_url(url)
                seen_urls.add(normalized_url)

        # Add archive signals if not duplicate
        for signal in archive_signals:
            source = signal.get('source', {})
            url = source.get('url', '') if isinstance(source, dict) else source
            if url:
                normalized_url = self._normalize_url(url)
                if normalized_url not in seen_urls:
                    all_signals.append(signal)
                    seen_urls.add(normalized_url)

        return all_signals

    # Utility methods

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics about archive filtering.

        Args:
            days: Filter window in days

        Returns:
            Statistics dictionary
        """
        database = self._load_database()
        all_signals = database.get('signals', [])

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_signals = self._filter_by_date(all_signals, cutoff_date)

        return {
            "total_signals_in_database": len(all_signals),
            "signals_in_filter_window": len(recent_signals),
            "filter_ratio": len(recent_signals) / max(len(all_signals), 1),
            "memory_reduction_factor": len(all_signals) / max(len(recent_signals), 1),
            "filter_window_days": days,
            "cutoff_date": cutoff_date.date().isoformat()
        }
