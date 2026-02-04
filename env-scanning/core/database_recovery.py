#!/usr/bin/env python3
"""
Database Recovery

Restores signals/database.json from a pre-update snapshot.
Fulfills core-invariants.yaml requirement: "Restore capability on failure".

Called by the orchestrator's RESTORE_AND_HALT action when Step 3.1
(database update) fails after a critical VEV verification failure.

Usage:
    python -m env_scanning.core.database_recovery restore --date 2026-01-30
    python -m env_scanning.core.database_recovery list
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List


def list_snapshots(db_path: Path) -> List[Path]:
    """
    List available database snapshots sorted by date (newest first).

    Args:
        db_path: Path to database.json

    Returns:
        List of snapshot file paths
    """
    snapshot_dir = db_path.parent / "snapshots"
    if not snapshot_dir.exists():
        return []

    snapshots = sorted(snapshot_dir.glob("database-*.json"), reverse=True)
    return snapshots


def restore_from_snapshot(db_path: Path, scan_date: str) -> bool:
    """
    Restore database.json from a pre-update snapshot.

    Args:
        db_path: Path to database.json
        scan_date: Date string (YYYY-MM-DD) identifying the snapshot

    Returns:
        True if restoration succeeded, False otherwise
    """
    snapshot_path = db_path.parent / "snapshots" / f"database-{scan_date}.json"

    if not snapshot_path.exists():
        print(f"[ERROR] Snapshot not found: {snapshot_path}")
        available = list_snapshots(db_path)
        if available:
            print("[INFO] Available snapshots:")
            for s in available[:5]:
                print(f"  - {s.name}")
        return False

    # Validate snapshot is readable JSON before restoring
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'signals' not in data or 'version' not in data:
            print(f"[ERROR] Snapshot is not a valid database file: {snapshot_path}")
            return False
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR] Snapshot is corrupted: {e}")
        return False

    # Restore via file copy (byte-identical to original pre-update state)
    shutil.copy2(snapshot_path, db_path)
    print(f"[RESTORED] database.json restored from: {snapshot_path}")
    print(f"[INFO] Restored state: {data.get('total_signals', '?')} signals, "
          f"last updated {data.get('last_updated', '?')}")
    return True


def restore_latest(db_path: Path) -> bool:
    """
    Restore from the most recent snapshot.

    Args:
        db_path: Path to database.json

    Returns:
        True if restoration succeeded, False otherwise
    """
    snapshots = list_snapshots(db_path)
    if not snapshots:
        print("[ERROR] No snapshots available")
        return False

    latest = snapshots[0]
    # Extract date from filename: database-YYYY-MM-DD.json
    date_str = latest.stem.replace("database-", "")
    print(f"[INFO] Restoring from latest snapshot: {latest.name}")
    return restore_from_snapshot(db_path, date_str)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Database recovery from snapshots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available snapshots
  python database_recovery.py list

  # Restore from a specific date
  python database_recovery.py restore --date 2026-01-30

  # Restore from the latest snapshot
  python database_recovery.py restore --latest
        """
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # list command
    subparsers.add_parser('list', help='List available snapshots')

    # restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from snapshot')
    restore_group = restore_parser.add_mutually_exclusive_group(required=True)
    restore_group.add_argument('--date', type=str, help='Snapshot date (YYYY-MM-DD)')
    restore_group.add_argument('--latest', action='store_true', help='Use most recent snapshot')

    parser.add_argument(
        '--database',
        type=str,
        default='signals/database.json',
        help='Path to database file (default: signals/database.json)'
    )

    args = parser.parse_args()
    db_path = Path(args.database)

    if args.command == 'list':
        snapshots = list_snapshots(db_path)
        if not snapshots:
            print("[INFO] No snapshots found")
            return 0
        print(f"[INFO] {len(snapshots)} snapshot(s) available:")
        for s in snapshots:
            size_kb = s.stat().st_size / 1024
            mtime = datetime.fromtimestamp(s.stat().st_mtime).isoformat()
            print(f"  {s.name}  ({size_kb:.1f} KB, modified {mtime})")
        return 0

    elif args.command == 'restore':
        if args.latest:
            success = restore_latest(db_path)
        else:
            success = restore_from_snapshot(db_path, args.date)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
