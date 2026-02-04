#!/usr/bin/env python3
"""
Database Updater
Updates the central signal database with new daily scan results
"""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def load_database(db_path: Path) -> Dict[str, Any]:
    """
    Load existing database or create new one

    Returns:
        Database dictionary with metadata and signals
    """
    if db_path.exists():
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Create new database
    return {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_signals": 0,
        "first_scan_date": None,
        "latest_scan_date": None,
        "statistics": {
            "total_scans": 0,
            "total_duplicates_prevented": 0,
            "sources": {},
            "categories": {}
        },
        "signals": []
    }


def load_daily_scan(scan_path: Path) -> Dict[str, Any]:
    """
    Load daily scan results

    Args:
        scan_path: Path to daily scan JSON file

    Returns:
        Scan data dictionary
    """
    with open(scan_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_signals(database: Dict[str, Any], new_signals: List[Dict[str, Any]], scan_date: str) -> int:
    """
    Merge new signals into database, preventing duplicates

    Args:
        database: Existing database
        new_signals: New signals to add
        scan_date: Date of the scan

    Returns:
        Number of new signals added (excluding duplicates)
    """
    # Build index of existing signal IDs for fast lookup
    existing_ids = {signal['id'] for signal in database['signals']}

    added_count = 0
    duplicate_count = 0

    for signal in new_signals:
        signal_id = signal.get('id')

        if not signal_id:
            print(f"[WARNING] Signal without ID: {signal.get('title', 'Unknown')[:50]}...")
            continue

        # Check for duplicates
        if signal_id in existing_ids:
            duplicate_count += 1
            continue

        # Add metadata
        signal['added_to_db_at'] = datetime.now().isoformat()
        signal['scan_date'] = scan_date

        # Add to database
        database['signals'].append(signal)
        existing_ids.add(signal_id)
        added_count += 1

        # Update statistics
        source_name = signal.get('source', {}).get('name', 'Unknown')
        category = signal.get('preliminary_category', 'Unknown')

        if source_name not in database['statistics']['sources']:
            database['statistics']['sources'][source_name] = 0
        database['statistics']['sources'][source_name] += 1

        if category not in database['statistics']['categories']:
            database['statistics']['categories'][category] = 0
        database['statistics']['categories'][category] += 1

    print(f"[INFO] Added {added_count} new signals")
    if duplicate_count > 0:
        print(f"[INFO] Prevented {duplicate_count} duplicates")

    return added_count


def update_metadata(database: Dict[str, Any], scan_date: str, added_count: int):
    """
    Update database metadata

    Args:
        database: Database to update
        scan_date: Date of the scan
        added_count: Number of signals added
    """
    database['last_updated'] = datetime.now().isoformat()
    database['total_signals'] = len(database['signals'])
    database['latest_scan_date'] = scan_date
    database['statistics']['total_scans'] += 1

    if database['first_scan_date'] is None:
        database['first_scan_date'] = scan_date


def save_database(database: Dict[str, Any], db_path: Path):
    """
    Save database to file atomically.

    Uses tempfile + shutil.move pattern to prevent corruption on mid-write crash.
    Fulfills core-invariants.yaml requirement: "Atomic write with backup".

    Args:
        database: Database to save
        db_path: Path to save to
    """
    # Create directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file first, then atomically replace
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        dir=db_path.parent,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        json.dump(database, tmp_file, indent=2, ensure_ascii=False)
        tmp_path = tmp_file.name

    # Atomic move: replaces target file in one OS operation
    shutil.move(tmp_path, db_path)

    file_size = os.path.getsize(db_path)
    print(f"[SAVED] Database updated: {db_path}")
    print(f"[SIZE] {file_size:,} bytes ({file_size/1024:.1f} KB)")


def save_snapshot(database: Dict[str, Any], snapshot_path: Path):
    """
    Save database snapshot

    Args:
        database: Database to snapshot
        snapshot_path: Path to save snapshot
    """
    # Create directory if needed
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    # Save snapshot
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    print(f"[SNAPSHOT] Saved to: {snapshot_path}")


def print_statistics(database: Dict[str, Any]):
    """
    Print database statistics

    Args:
        database: Database to print stats for
    """
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    print(f"\nTotal signals: {database['total_signals']}")
    print(f"First scan: {database['first_scan_date']}")
    print(f"Latest scan: {database['latest_scan_date']}")
    print(f"Total scans: {database['statistics']['total_scans']}")

    # Category distribution
    print(f"\nCategory distribution:")
    categories = database['statistics']['categories']
    for cat in sorted(categories.keys()):
        count = categories[cat]
        pct = (count / database['total_signals'] * 100) if database['total_signals'] > 0 else 0
        print(f"  {cat}: {count:4d} signals ({pct:5.1f}%)")

    # Source distribution
    print(f"\nSource distribution:")
    sources = database['statistics']['sources']
    for source in sorted(sources.keys(), key=lambda k: sources[k], reverse=True)[:10]:
        count = sources[source]
        pct = (count / database['total_signals'] * 100) if database['total_signals'] > 0 else 0
        print(f"  {source:30s}: {count:4d} signals ({pct:5.1f}%)")

    print("="*60 + "\n")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Update signal database with daily scan results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update with latest scan
  python update_database.py raw/daily-scan-2026-01-30.json

  # Update with custom database path
  python update_database.py raw/daily-scan-2026-01-30.json --database signals/custom-db.json

  # Skip snapshot
  python update_database.py raw/daily-scan-2026-01-30.json --no-snapshot
        """
    )

    parser.add_argument(
        'scan_file',
        type=str,
        help='Path to daily scan JSON file'
    )

    parser.add_argument(
        '--database',
        type=str,
        default='signals/database.json',
        help='Path to database file (default: signals/database.json)'
    )

    parser.add_argument(
        '--no-snapshot',
        action='store_true',
        help='Skip saving snapshot'
    )

    args = parser.parse_args()

    # Paths
    scan_path = Path(args.scan_file)
    db_path = Path(args.database)

    if not scan_path.exists():
        print(f"[ERROR] Scan file not found: {scan_path}")
        return 1

    try:
        print("="*60)
        print("DATABASE UPDATER")
        print("="*60)

        # Load database
        print(f"\n[LOAD] Loading database: {db_path}")
        database = load_database(db_path)

        if database['total_signals'] > 0:
            print(f"[INFO] Current signals: {database['total_signals']}")
        else:
            print("[INFO] Creating new database")

        # Load daily scan
        print(f"\n[LOAD] Loading scan: {scan_path}")
        scan_data = load_daily_scan(scan_path)

        scan_date = scan_data.get('scan_metadata', {}).get('date')
        if not scan_date:
            print("[WARNING] Scan date not found, using today")
            scan_date = datetime.now().strftime('%Y-%m-%d')

        new_signals = scan_data.get('items', [])
        print(f"[INFO] New signals to process: {len(new_signals)}")

        # Pre-update snapshot: backup current DB BEFORE merge
        # Fulfills core-invariants.yaml: "Pre-update snapshot creation"
        if not args.no_snapshot and db_path.exists():
            snapshot_dir = db_path.parent / "snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot_path = snapshot_dir / f"database-{scan_date}.json"
            shutil.copy2(db_path, snapshot_path)
            print(f"[SNAPSHOT] Pre-update backup: {snapshot_path}")

        # Merge signals (mutates database in-place)
        print(f"\n[MERGE] Merging new signals...")
        added_count = merge_signals(database, new_signals, scan_date)

        # Update metadata
        update_metadata(database, scan_date, added_count)

        # Save database (atomic write via tempfile + move)
        print(f"\n[SAVE] Saving database...")
        save_database(database, db_path)

        # Print statistics
        print_statistics(database)

        print("[SUCCESS] Database updated successfully")
        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Update cancelled by user")
        return 130

    except Exception as e:
        print(f"\n[ERROR] Database update failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
