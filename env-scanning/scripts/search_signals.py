#!/usr/bin/env python3
"""
Signal Search Tool
Search and filter signals from the database
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def load_database(db_path: Path) -> Dict[str, Any]:
    """Load signal database"""
    if not db_path.exists():
        print(f"[ERROR] Database not found: {db_path}")
        print("[HELP] Run update_database.py first to create database")
        sys.exit(1)

    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_by_keyword(signals: List[Dict], keyword: str) -> List[Dict]:
    """
    Search signals by keyword in title or abstract

    Args:
        signals: List of signals
        keyword: Search keyword (case-insensitive)

    Returns:
        Filtered signals
    """
    keyword_lower = keyword.lower()
    results = []

    for signal in signals:
        # Search in title
        if keyword_lower in signal.get('title', '').lower():
            results.append(signal)
            continue

        # Search in abstract
        abstract = signal.get('content', {}).get('abstract', '')
        if keyword_lower in abstract.lower():
            results.append(signal)
            continue

        # Search in keywords
        keywords = signal.get('content', {}).get('keywords', [])
        if any(keyword_lower in kw.lower() for kw in keywords):
            results.append(signal)

    return results


def filter_by_date(signals: List[Dict], start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    Filter signals by date range

    Args:
        signals: List of signals
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Filtered signals
    """
    results = []

    for signal in signals:
        # Get publication date
        pub_date = signal.get('source', {}).get('published_date', '')
        if not pub_date:
            continue

        # Filter by start date
        if start_date and pub_date < start_date:
            continue

        # Filter by end date
        if end_date and pub_date > end_date:
            continue

        results.append(signal)

    return results


def filter_by_category(signals: List[Dict], category: str) -> List[Dict]:
    """
    Filter signals by STEEPs category

    Args:
        signals: List of signals
        category: Category (S, T, E, P, s)

    Returns:
        Filtered signals
    """
    return [s for s in signals if s.get('preliminary_category') == category]


def filter_by_source(signals: List[Dict], source: str) -> List[Dict]:
    """
    Filter signals by source name

    Args:
        signals: List of signals
        source: Source name (case-insensitive partial match)

    Returns:
        Filtered signals
    """
    source_lower = source.lower()
    return [
        s for s in signals
        if source_lower in s.get('source', {}).get('name', '').lower()
    ]


def print_results(signals: List[Dict], limit: int = 10):
    """
    Print search results

    Args:
        signals: Signals to print
        limit: Maximum number to print
    """
    if not signals:
        print("\n[RESULT] No signals found")
        return

    print(f"\n[RESULT] Found {len(signals)} signal(s)")
    print(f"[DISPLAY] Showing top {min(limit, len(signals))} result(s)")
    print("\n" + "="*80)

    for i, signal in enumerate(signals[:limit], 1):
        print(f"\n#{i}. {signal.get('title', 'No title')}")
        print("-" * 80)
        print(f"Category:  {signal.get('preliminary_category', 'Unknown')}")
        print(f"Source:    {signal.get('source', {}).get('name', 'Unknown')}")
        print(f"Published: {signal.get('source', {}).get('published_date', 'Unknown')}")
        print(f"URL:       {signal.get('source', {}).get('url', 'N/A')}")

        # Abstract preview
        abstract = signal.get('content', {}).get('abstract', '')
        if abstract:
            preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
            print(f"\nAbstract:  {preview}")

        # Keywords
        keywords = signal.get('content', {}).get('keywords', [])
        if keywords:
            print(f"Keywords:  {', '.join(keywords[:5])}")

    if len(signals) > limit:
        print("\n" + "="*80)
        print(f"[INFO] {len(signals) - limit} more result(s) not shown")
        print(f"[HELP] Use --limit {len(signals)} to see all results")

    print("="*80 + "\n")


def print_summary(signals: List[Dict]):
    """
    Print summary statistics

    Args:
        signals: Signals to summarize
    """
    if not signals:
        return

    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    # Category distribution
    categories = {}
    for signal in signals:
        cat = signal.get('preliminary_category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nCategory distribution:")
    for cat in sorted(categories.keys()):
        count = categories[cat]
        pct = (count / len(signals) * 100)
        print(f"  {cat}: {count:3d} signals ({pct:5.1f}%)")

    # Source distribution
    sources = {}
    for signal in signals:
        source = signal.get('source', {}).get('name', 'Unknown')
        sources[source] = sources.get(source, 0) + 1

    print(f"\nSource distribution:")
    for source in sorted(sources.keys(), key=lambda k: sources[k], reverse=True):
        count = sources[source]
        pct = (count / len(signals) * 100)
        print(f"  {source:30s}: {count:3d} signals ({pct:5.1f}%)")

    # Date range
    dates = [s.get('source', {}).get('published_date', '') for s in signals if s.get('source', {}).get('published_date')]
    if dates:
        print(f"\nDate range:")
        print(f"  Earliest: {min(dates)}")
        print(f"  Latest:   {max(dates)}")

    print("="*80 + "\n")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Search and filter signals from the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for "AI" keyword
  python search_signals.py "AI"

  # Search with filters
  python search_signals.py "climate" --category E --source arXiv

  # Date range search
  python search_signals.py --start-date 2026-01-01 --end-date 2026-01-31

  # Show more results
  python search_signals.py "policy" --limit 50

  # Show summary only
  python search_signals.py --category T --summary-only
        """
    )

    parser.add_argument(
        'keyword',
        type=str,
        nargs='?',
        help='Search keyword (searches in title, abstract, keywords)'
    )

    parser.add_argument(
        '--database',
        type=str,
        default='signals/database.json',
        help='Path to database file (default: signals/database.json)'
    )

    parser.add_argument(
        '--category',
        type=str,
        choices=['S', 'T', 'E', 'P', 's'],
        help='Filter by STEEPs category'
    )

    parser.add_argument(
        '--source',
        type=str,
        help='Filter by source name (partial match)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum results to display (default: 10)'
    )

    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Show summary statistics only'
    )

    args = parser.parse_args()

    try:
        # Load database
        db_path = Path(args.database)
        database = load_database(db_path)

        signals = database['signals']
        total_signals = len(signals)

        print("="*80)
        print("SIGNAL SEARCH")
        print("="*80)
        print(f"\nDatabase: {db_path}")
        print(f"Total signals in database: {total_signals}")

        # Apply filters
        results = signals

        if args.keyword:
            print(f"\n[FILTER] Searching for keyword: '{args.keyword}'")
            results = search_by_keyword(results, args.keyword)
            print(f"[RESULT] {len(results)} signals match keyword")

        if args.category:
            print(f"[FILTER] Category: {args.category}")
            results = filter_by_category(results, args.category)
            print(f"[RESULT] {len(results)} signals in category")

        if args.source:
            print(f"[FILTER] Source: {args.source}")
            results = filter_by_source(results, args.source)
            print(f"[RESULT] {len(results)} signals from source")

        if args.start_date or args.end_date:
            date_range = f"{args.start_date or 'start'} to {args.end_date or 'end'}"
            print(f"[FILTER] Date range: {date_range}")
            results = filter_by_date(results, args.start_date, args.end_date)
            print(f"[RESULT] {len(results)} signals in date range")

        # Show results
        if args.summary_only:
            print_summary(results)
        else:
            print_results(results, args.limit)
            if results:
                print_summary(results)

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Search cancelled")
        return 130

    except Exception as e:
        print(f"\n[ERROR] Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
