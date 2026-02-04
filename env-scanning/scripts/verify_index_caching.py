#!/usr/bin/env python3
"""
Verify Index Caching Integration (Task #2)
Tests persistent index caching with incremental updates
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.index_cache_manager import IndexCacheManager


def generate_sample_signals(n: int, prefix: str = "signal") -> list:
    """Generate sample signals for testing."""
    signals = []

    for i in range(n):
        signal = {
            "id": f"{prefix}-{i+1:03d}",
            "title": f"Sample Signal {i+1}: Technology Trend",
            "source": {
                "url": f"https://example.com/article{i+1}",
                "name": "Example Source"
            },
            "entities": ["Technology", "Innovation", f"Topic{i%10}"],
            "category": "T",
            "first_detected": datetime.now().isoformat()
        }
        signals.append(signal)

    return signals


def test_index_caching():
    """Test index caching with incremental updates"""
    print("=" * 70)
    print("INDEX CACHING INTEGRATION TEST")
    print("=" * 70)

    # Cleanup previous test cache
    cache_path = Path("context/test-index-cache.json")
    if cache_path.exists():
        cache_path.unlink()
        print("\n[CLEANUP] Removed previous test cache")

    # Test 1: Initial cache creation
    print("\n[Test 1] Initial cache creation (1,000 signals)")
    signals_batch1 = generate_sample_signals(1000, "signal")

    start_time = time.time()
    cache = IndexCacheManager(str(cache_path))
    cache.rebuild_from_signals(signals_batch1)
    build_time = time.time() - start_time

    print(f"  Cache created in {build_time:.3f}s")
    print(f"  Total signals: {cache.get_metadata()['total_signals']:,}")
    print(f"  Cache file size: {cache.get_cache_size():,} bytes")

    # Verify indexes
    indexes = cache.get_indexes()
    assert len(indexes['by_url']) == 1000
    assert len(indexes['by_title']) == 1000
    print(f"  ✓ URL index: {len(indexes['by_url']):,} entries")
    print(f"  ✓ Title index: {len(indexes['by_title']):,} entries")
    print(f"  ✓ Entity index: {len(indexes['by_entities']):,} unique entities")

    # Test 2: Load existing cache
    print("\n[Test 2] Load existing cache")

    start_time = time.time()
    cache2 = IndexCacheManager(str(cache_path))
    load_time = time.time() - start_time

    print(f"  Cache loaded in {load_time:.3f}s")
    print(f"  Speedup: {build_time/load_time:.1f}x faster than rebuild")

    assert cache2.get_metadata()['total_signals'] == 1000
    print(f"  ✓ Verified: {cache2.get_metadata()['total_signals']:,} signals")

    # Test 3: Incremental update (add 100 new signals)
    print("\n[Test 3] Incremental update (+100 signals)")
    # Generate signals with unique URLs (starting from 1001)
    signals_batch2 = []
    for i in range(100):
        signal = {
            "id": f"new-{i+1:03d}",
            "title": f"New Signal {i+1}: Future Trend",
            "source": {
                "url": f"https://example.com/article{1001+i}",  # Unique URLs
                "name": "Example Source"
            },
            "entities": ["Future", "Technology", f"Topic{i%10}"],
            "category": "T",
            "first_detected": datetime.now().isoformat()
        }
        signals_batch2.append(signal)

    start_time = time.time()
    added_count = cache2.add_signals(signals_batch2)
    update_time = time.time() - start_time

    print(f"  Update completed in {update_time:.3f}s")
    print(f"  New signals added: {added_count:,}")
    print(f"  Total signals now: {cache2.get_metadata()['total_signals']:,}")

    assert cache2.get_metadata()['total_signals'] == 1100
    print(f"  ✓ Cache updated successfully")

    # Test 4: Idempotent update (add same signals again)
    print("\n[Test 4] Idempotent update (duplicate signals)")

    start_time = time.time()
    added_count_dup = cache2.add_signals(signals_batch2)  # Same signals
    dup_time = time.time() - start_time

    print(f"  Duplicate check completed in {dup_time:.3f}s")
    print(f"  New signals added: {added_count_dup} (should be 0)")

    assert cache2.get_metadata()['total_signals'] == 1100  # No change
    print(f"  ✓ Duplicate detection working correctly")

    # Test 5: Performance comparison (rebuild vs cache)
    print("\n[Test 5] Performance comparison")

    # Rebuild from scratch
    start_time = time.time()
    temp_cache = IndexCacheManager(str(cache_path.with_suffix('.tmp')))
    temp_cache.rebuild_from_signals(signals_batch1 + signals_batch2)
    rebuild_time = time.time() - start_time

    # Load from cache
    start_time = time.time()
    cached = IndexCacheManager(str(cache_path))
    load_cache_time = time.time() - start_time

    print(f"  Rebuild from scratch: {rebuild_time:.3f}s")
    print(f"  Load from cache:      {load_cache_time:.3f}s")
    print(f"  Speedup:              {rebuild_time/load_cache_time:.1f}x")

    speedup = rebuild_time / load_cache_time
    assert speedup >= 5.0, f"Expected >= 5x speedup, got {speedup:.1f}x"
    print(f"  ✓ Cache provides significant speedup")

    # Cleanup temp
    if cache_path.with_suffix('.tmp').exists():
        cache_path.with_suffix('.tmp').unlink()

    # Test 6: Index format compatibility
    print("\n[Test 6] Format compatibility with archive-loader")

    indexes = cache2.get_indexes()

    # Verify structure matches archive-loader output
    assert "by_url" in indexes
    assert "by_title" in indexes
    assert "by_entities" in indexes

    # Test URL retrieval
    test_signal = signals_batch1[0]
    normalized_url = cache2.normalize_url(test_signal['source']['url'])
    assert normalized_url in indexes['by_url']
    assert indexes['by_url'][normalized_url] == test_signal['id']

    print(f"  ✓ Index format compatible with archive-loader")
    print(f"  ✓ URL lookup working correctly")

    # Test 7: Remove signal
    print("\n[Test 7] Signal removal")

    signal_to_remove = signals_batch2[0]
    cache2.remove_signal(signal_to_remove['id'], signal_to_remove)

    print(f"  Removed signal: {signal_to_remove['id']}")
    print(f"  Total signals now: {cache2.get_metadata()['total_signals']:,}")

    assert cache2.get_metadata()['total_signals'] == 1099
    print(f"  ✓ Signal removal working correctly")

    # Final summary
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)

    print(f"\nInitial cache creation:  {build_time:.3f}s (1,000 signals)")
    print(f"Cache loading:           {load_time:.3f}s")
    print(f"Incremental update:      {update_time:.3f}s (100 signals)")
    print(f"Duplicate check:         {dup_time:.3f}s (100 signals)")

    print(f"\nOverall speedup:         {build_time/load_time:.1f}x")
    print(f"Cache file size:         {cache2.get_cache_size():,} bytes")

    # Cleanup
    if cache_path.exists():
        cache_path.unlink()
        print(f"\n[CLEANUP] Removed test cache")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("   Index caching integration verified")
    return 0


def main():
    """Main test execution"""
    return test_index_caching()


if __name__ == "__main__":
    exit(main())
