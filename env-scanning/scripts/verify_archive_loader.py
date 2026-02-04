#!/usr/bin/env python3
"""
Verification script for RecursiveArchiveLoader.
Tests time-based filtering and index compatibility.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loaders.recursive_archive_loader import RecursiveArchiveLoader


def test_phase2_archive_loader():
    """Test RecursiveArchiveLoader functionality."""
    print("=" * 70)
    print("PHASE 2: RecursiveArchiveLoader Verification")
    print("=" * 70)

    database_path = Path('signals/database.json')
    archive_dir = Path('reports/archive/')

    if not database_path.exists():
        print(f"❌ Database file not found: {database_path}")
        return False

    try:
        # Test 1: Initialize loader
        print("\n[Test 1] Initialize RecursiveArchiveLoader...")
        loader = RecursiveArchiveLoader(database_path, archive_dir)
        print(f"✓ Initialized successfully")

        # Test 2: Load recent index (7 days)
        print("\n[Test 2] Load recent index (7-day window)...")
        recent = loader.load_recent_index(days=7)
        print(f"✓ Loaded recent signals")
        print(f"  Total signals in window: {recent['metadata']['total_signals']}")
        print(f"  Total in database: {recent['metadata']['total_in_database']}")
        print(f"  Filter ratio: {recent['metadata']['filter_ratio']:.2%}")
        print(f"  Date range: {recent['metadata']['date_range']}")

        # Test 3: Verify index format compatibility
        print("\n[Test 3] Verify index format compatibility...")
        assert 'by_url' in recent['index'], "Missing by_url index"
        assert 'by_title' in recent['index'], "Missing by_title index"
        assert 'by_entities' in recent['index'], "Missing by_entities index"
        print(f"✓ Index format compatible with deduplication-filter")
        print(f"  Index sizes: {len(recent['index']['by_url'])} URLs, "
              f"{len(recent['index']['by_title'])} titles, "
              f"{len(recent['index']['by_entities'])} entities")

        # Test 4: Verify backward compatibility (full archive)
        print("\n[Test 4] Verify backward compatibility (full archive mode)...")
        full = loader.load_full_archive()
        print(f"✓ Full archive loaded")
        print(f"  Total signals: {full['metadata']['total_signals']}")
        print(f"  Date range: {full['metadata']['date_range']}")
        print(f"  Filter ratio: {full['metadata']['filter_ratio']:.2%}")

        # Test 5: Memory reduction statistics
        print("\n[Test 5] Calculate memory reduction statistics...")
        stats = loader.get_statistics(days=7)
        print(f"✓ Statistics calculated")
        print(f"  Memory reduction factor: {stats['memory_reduction_factor']:.1f}x")
        print(f"  Signals in filter window: {stats['signals_in_filter_window']}")
        print(f"  Total signals: {stats['total_signals_in_database']}")

        # Test 6: Verify signal data integrity
        print("\n[Test 6] Verify signal data integrity...")
        if recent['signals']:
            sample_signal = recent['signals'][0]
            required_fields = ['id', 'title', 'source']
            for field in required_fields:
                assert field in sample_signal, f"Missing required field: {field}"
            print(f"✓ Signal data integrity verified")
            print(f"  Sample signal ID: {sample_signal.get('id')}")
            print(f"  Sample signal title: {sample_signal.get('title', '')[:60]}...")
        else:
            print(f"⚠ No signals in recent window (expected if database is empty or old)")

        print("\n" + "=" * 70)
        print("✅ PHASE 2 VERIFICATION PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_phase2_archive_loader()
    sys.exit(0 if success else 1)
