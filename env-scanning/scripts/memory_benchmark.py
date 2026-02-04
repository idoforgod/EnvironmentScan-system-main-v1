#!/usr/bin/env python3
"""
Memory Benchmark - RLM Optimization Performance Test

Tests memory usage with and without optimization on 10K signals.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context_manager import SharedContextManager
from loaders.recursive_archive_loader import RecursiveArchiveLoader


def get_memory_usage():
    """Get current process memory usage in MB."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        print("⚠️  psutil not installed. Install with: pip install psutil")
        return None


def format_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def benchmark_archive_loader(test_db_path: Path):
    """Benchmark RecursiveArchiveLoader with different configurations."""
    print("=" * 70)
    print("BENCHMARK 1: RecursiveArchiveLoader")
    print("=" * 70)

    loader = RecursiveArchiveLoader(test_db_path, Path("reports/archive/"))

    # Test 1: Load full archive (traditional)
    print("\n[Test 1] Full Archive Loading (Traditional)")
    mem_before = get_memory_usage()
    start = time.time()

    full_data = loader.load_full_archive()
    full_size = len(json.dumps(full_data))

    elapsed = time.time() - start
    mem_after = get_memory_usage()

    print(f"  Time: {elapsed:.3f}s")
    print(f"  Data size: {format_size(full_size)}")
    print(f"  Signals loaded: {full_data['metadata']['total_signals']:,}")
    if mem_before and mem_after:
        print(f"  Memory used: {mem_after - mem_before:.2f} MB")

    # Test 2: Load 7-day window (optimized)
    print("\n[Test 2] 7-Day Window Loading (Optimized)")
    mem_before = get_memory_usage()
    start = time.time()

    recent_7d = loader.load_recent_index(days=7)
    recent_7d_size = len(json.dumps(recent_7d))

    elapsed = time.time() - start
    mem_after = get_memory_usage()

    print(f"  Time: {elapsed:.3f}s")
    print(f"  Data size: {format_size(recent_7d_size)}")
    print(f"  Signals loaded: {recent_7d['metadata']['total_signals']:,}")
    print(f"  Filter ratio: {recent_7d['metadata']['filter_ratio']:.1%}")
    if mem_before and mem_after:
        print(f"  Memory used: {mem_after - mem_before:.2f} MB")

    # Test 3: Load 30-day window
    print("\n[Test 3] 30-Day Window Loading")
    recent_30d = loader.load_recent_index(days=30)
    recent_30d_size = len(json.dumps(recent_30d))

    print(f"  Data size: {format_size(recent_30d_size)}")
    print(f"  Signals loaded: {recent_30d['metadata']['total_signals']:,}")
    print(f"  Filter ratio: {recent_30d['metadata']['filter_ratio']:.1%}")

    # Calculate reductions
    print("\n[Results Summary]")
    print(f"  Full archive size: {format_size(full_size)}")
    print(f"  7-day window size: {format_size(recent_7d_size)}")
    print(f"  30-day window size: {format_size(recent_30d_size)}")
    print(f"\n  Memory reduction (7d): {full_size/recent_7d_size:.1f}x")
    print(f"  Memory reduction (30d): {full_size/recent_30d_size:.1f}x")

    return {
        "full_size": full_size,
        "7d_size": recent_7d_size,
        "30d_size": recent_30d_size,
        "7d_reduction": full_size / recent_7d_size,
        "30d_reduction": full_size / recent_30d_size
    }


def benchmark_context_manager(context_path: Path):
    """Benchmark SharedContextManager field-level loading."""
    print("\n" + "=" * 70)
    print("BENCHMARK 2: SharedContextManager")
    print("=" * 70)

    # Create test context with multiple fields
    if not context_path.exists():
        print("\n  Creating test context file...")
        test_context = {
            "version": "1.0",
            "workflow_id": "test-benchmark",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "signal_embeddings": {f"signal-{i}": {"vector": [0.1] * 768, "model": "SBERT"} for i in range(1000)},
            "preliminary_analysis": {f"signal-{i}": {"category_guess": "T", "confidence": 0.9} for i in range(1000)},
            "final_classification": {f"signal-{i}": {"final_category": "T", "confidence": 0.95} for i in range(1000)},
            "impact_analysis": {f"signal-{i}": {"impact_score": 7.5} for i in range(1000)},
            "priority_ranking": {f"signal-{i}": {"priority_score": 8.0, "rank": i} for i in range(1000)},
            "deduplication_analysis": {},
            "validated_by_experts": {},
            "translation_status": {"translations_completed": []},
            "metadata": {"total_signals_processed": 1000}
        }

        context_path.parent.mkdir(parents=True, exist_ok=True)
        with open(context_path, 'w') as f:
            json.dump(test_context, f, indent=2)

        print(f"  ✓ Created: {context_path}")
        print(f"  ✓ Size: {format_size(context_path.stat().st_size)}")

    # Test 1: Load full context (traditional)
    print("\n[Test 1] Full Context Loading (Traditional)")
    mem_before = get_memory_usage()
    start = time.time()

    ctx = SharedContextManager(context_path)
    full_context = ctx.get_full_context()
    full_size = sys.getsizeof(json.dumps(full_context))

    elapsed = time.time() - start
    mem_after = get_memory_usage()

    print(f"  Time: {elapsed:.3f}s")
    print(f"  Data size: {format_size(full_size)}")
    print(f"  Fields: {len([k for k in full_context.keys() if not k.startswith('_')])}")
    if mem_before and mem_after:
        print(f"  Memory used: {mem_after - mem_before:.2f} MB")

    # Test 2: Load single field (optimized)
    print("\n[Test 2] Single Field Loading (Optimized)")
    ctx2 = SharedContextManager(context_path)
    mem_before = get_memory_usage()
    start = time.time()

    classifications = ctx2.get_final_classification()
    field_size = sys.getsizeof(json.dumps(classifications))

    elapsed = time.time() - start
    mem_after = get_memory_usage()

    print(f"  Time: {elapsed:.3f}s")
    print(f"  Data size: {format_size(field_size)}")
    print(f"  Loaded fields: {ctx2.get_loaded_fields()}")
    print(f"  Cache size: {format_size(ctx2.get_cache_size())}")
    if mem_before and mem_after:
        print(f"  Memory used: {mem_after - mem_before:.2f} MB")

    # Test 3: Load 2 fields
    print("\n[Test 3] Two Fields Loading")
    ctx3 = SharedContextManager(context_path)

    classifications = ctx3.get_final_classification()
    impact = ctx3.get_impact_analysis()
    two_fields_size = ctx3.get_cache_size()

    print(f"  Cache size: {format_size(two_fields_size)}")
    print(f"  Loaded fields: {ctx3.get_loaded_fields()}")

    # Calculate reductions
    print("\n[Results Summary]")
    print(f"  Full context size: {format_size(full_size)}")
    print(f"  Single field size: {format_size(field_size)}")
    print(f"  Two fields size: {format_size(two_fields_size)}")
    print(f"\n  Memory reduction (1 field): {full_size/field_size:.1f}x")
    print(f"  Memory reduction (2 fields): {full_size/two_fields_size:.1f}x")

    return {
        "full_size": full_size,
        "1_field_size": field_size,
        "2_fields_size": two_fields_size,
        "1_field_reduction": full_size / field_size,
        "2_fields_reduction": full_size / two_fields_size
    }


def main():
    """Main benchmark entry point."""
    print("=" * 70)
    print("RLM MEMORY OPTIMIZATION - PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")

    # Check if psutil available
    mem = get_memory_usage()
    if mem:
        print(f"Initial Memory: {mem:.2f} MB")
    else:
        print("Memory profiling disabled (install psutil)")

    # Test paths
    test_db = Path("signals/database-test-10k.json")
    test_context = Path("context/test-context-benchmark.json")

    if not test_db.exists():
        print(f"\n❌ Test database not found: {test_db}")
        print("   Run: python3 scripts/generate_test_data.py")
        return

    # Run benchmarks
    print("\n")
    results_loader = benchmark_archive_loader(test_db)
    results_context = benchmark_context_manager(test_context)

    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL PERFORMANCE SUMMARY")
    print("=" * 70)

    print("\n📊 RecursiveArchiveLoader (10,000 signals, 90-day archive):")
    print(f"  - 7-day window reduction: {results_loader['7d_reduction']:.1f}x")
    print(f"  - 30-day window reduction: {results_loader['30d_reduction']:.1f}x")
    print(f"  - Recommended: 7-day window for deduplication")

    print("\n📊 SharedContextManager (1,000 signals, 8 fields):")
    print(f"  - Single field reduction: {results_context['1_field_reduction']:.1f}x")
    print(f"  - Two fields reduction: {results_context['2_fields_reduction']:.1f}x")
    print(f"  - Recommended: Load only needed fields per agent")

    # Combined estimate
    combined_reduction = (results_loader['7d_reduction'] + results_context['1_field_reduction']) / 2
    print(f"\n🎯 Combined Optimization: ~{combined_reduction:.1f}x memory reduction")

    # Save results
    results_file = Path("logs/benchmark-results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    results = {
        "benchmark_date": datetime.now().isoformat(),
        "test_dataset": {
            "signals": 10000,
            "date_range": "90 days"
        },
        "recursive_archive_loader": results_loader,
        "shared_context_manager": results_context,
        "combined_reduction_estimate": combined_reduction
    }

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Benchmark complete!")
    print(f"   Results saved to: {results_file}")


if __name__ == '__main__':
    main()
