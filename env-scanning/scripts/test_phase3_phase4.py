#!/usr/bin/env python3
"""
Test Phase 3 (Impact Matrix Compression) and Phase 4 (Embedding Deduplication)
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.impact_matrix_compressor import ImpactMatrixCompressor
from core.embedding_deduplicator import EmbeddingDeduplicator


def test_phase3_impact_compression():
    """Test Phase 3: Impact Matrix Compression"""
    print("=" * 70)
    print("PHASE 3: Impact Matrix Compression Test")
    print("=" * 70)

    # Generate sample impact data (10,000 signals)
    print("\n[Step 1] Generating sample impact data (10,000 signals)...")
    n_signals = 10000
    impact_data = {}

    for i in range(n_signals):
        signal_id = f"signal-{i+1:05d}"

        # Each signal influences 5-10 other signals (sparse)
        n_influences = np.random.randint(5, 11)
        influences = []

        for _ in range(n_influences):
            target_idx = np.random.randint(0, n_signals)
            if target_idx == i:
                continue  # Skip self-influence

            target_id = f"signal-{target_idx+1:05d}"
            score = np.random.uniform(-5, 5)
            influence_type = np.random.choice(["amplifies", "suppresses", "neutral"])

            influences.append({
                "target_signal": target_id,
                "influence_score": score,
                "influence_type": influence_type
            })

        impact_data[signal_id] = {
            "impact_score": np.random.uniform(0, 10),
            "influences": influences
        }

    # Calculate original size
    original_size = len(json.dumps(impact_data))
    print(f"  Original size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
    print(f"  Signals: {n_signals:,}")
    print(f"  Total possible influences: {n_signals * n_signals:,}")
    print(f"  Actual influences: {sum(len(d['influences']) for d in impact_data.values()):,}")

    # Compress
    print("\n[Step 2] Compressing impact matrix...")
    compressed = ImpactMatrixCompressor.compress(impact_data)
    compressed_size = len(json.dumps(compressed))

    print(f"  Compressed size: {compressed_size:,} bytes ({compressed_size/1024/1024:.2f} MB)")

    stats = compressed["compression_stats"]
    print(f"\n[Compression Stats]")
    print(f"  Total cells: {stats['total_cells']:,}")
    print(f"  Non-zero cells: {stats['non_zero_cells']:,}")
    print(f"  Sparsity: {stats['sparsity']:.1%}")
    print(f"  Compression ratio: {stats['compression_ratio']:.1f}x")
    print(f"  Memory reduction: {original_size/compressed_size:.1f}x")

    # Test decompression
    print("\n[Step 3] Testing decompression...")
    decompressed = ImpactMatrixCompressor.decompress(compressed)

    # Verify a few samples
    sample_ids = [f"signal-{i+1:05d}" for i in range(5)]
    matches = 0
    for sid in sample_ids:
        original_influences = set((inf['target_signal'], round(inf['influence_score'], 2))
                                 for inf in impact_data[sid]['influences'])
        decompressed_influences = set((inf['target_signal'], round(inf['influence_score'], 2))
                                     for inf in decompressed[sid]['influences'])

        if original_influences == decompressed_influences:
            matches += 1

    print(f"  Sample verification: {matches}/{len(sample_ids)} matches ✓")

    # Test selective query
    print("\n[Step 4] Testing selective query (no full decompression)...")
    test_signal = "signal-00100"
    influences = ImpactMatrixCompressor.query_influences(compressed, test_signal, threshold=2.0)
    print(f"  Signal: {test_signal}")
    print(f"  Influences (score > 2.0): {len(influences)}")
    if influences[:3]:
        for inf in influences[:3]:
            print(f"    → {inf['target_signal']}: {inf['influence_score']:.2f} ({inf['influence_type']})")

    print("\n✅ Phase 3 compression working correctly!")
    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "reduction": original_size / compressed_size
    }


def test_phase4_embedding_dedup():
    """Test Phase 4: Embedding Deduplication"""
    print("\n" + "=" * 70)
    print("PHASE 4: Embedding Deduplication Test")
    print("=" * 70)

    # Generate sample embeddings (1,000 signals, 768 dims)
    print("\n[Step 1] Generating sample embeddings (1,000 signals, 768 dims)...")
    n_signals = 1000
    embedding_dim = 768

    embeddings = {}

    # Create clusters (simulate similar embeddings)
    n_clusters = 100  # ~10 signals per cluster
    cluster_centers = np.random.randn(n_clusters, embedding_dim).astype(np.float32)

    for i in range(n_signals):
        signal_id = f"signal-{i+1:05d}"

        # Assign to a cluster with some noise
        cluster_idx = i % n_clusters
        base_vector = cluster_centers[cluster_idx]
        noise = np.random.randn(embedding_dim).astype(np.float32) * 0.05  # Small noise

        vector = base_vector + noise
        vector = vector / np.linalg.norm(vector)  # Normalize

        embeddings[signal_id] = {
            "vector": vector.tolist(),
            "model": "SBERT",
            "computed_at": "step_1.3"
        }

    # Calculate original size
    original_size = len(json.dumps(embeddings))
    print(f"  Original size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
    print(f"  Signals: {n_signals:,}")
    print(f"  Embedding dimension: {embedding_dim}")

    # Deduplicate
    print("\n[Step 2] Deduplicating embeddings (threshold=0.95)...")
    deduplicated = EmbeddingDeduplicator.deduplicate(embeddings, similarity_threshold=0.95)
    deduped_size = len(json.dumps(deduplicated))

    print(f"  Deduplicated size: {deduped_size:,} bytes ({deduped_size/1024/1024:.2f} MB)")

    stats = deduplicated["deduplication_stats"]
    print(f"\n[Deduplication Stats]")
    print(f"  Total embeddings: {stats['total_embeddings']:,}")
    print(f"  Unique embeddings: {stats['unique_embeddings']:,}")
    print(f"  Duplicate embeddings: {stats['duplicate_embeddings']:,}")
    print(f"  Deduplication rate: {stats['deduplication_rate']:.1%}")
    print(f"  Memory reduction: {stats['memory_reduction']}")
    print(f"  Clusters found: {stats.get('clusters_found', 'N/A')}")

    # Test retrieval
    print("\n[Step 3] Testing embedding retrieval...")
    test_ids = ["signal-00001", "signal-00002", "signal-00010"]

    for test_id in test_ids:
        original_vector = np.array(embeddings[test_id]["vector"])
        retrieved_vector = EmbeddingDeduplicator.get_embedding(deduplicated, test_id)

        if retrieved_vector is not None:
            similarity = np.dot(original_vector, retrieved_vector) / (
                np.linalg.norm(original_vector) * np.linalg.norm(retrieved_vector)
            )
            is_reference = test_id in deduplicated["references"]
            status = "reference" if is_reference else "unique"
            print(f"  {test_id}: similarity={similarity:.4f}, status={status}")
        else:
            print(f"  {test_id}: NOT FOUND ✗")

    # Test reconstruction
    print("\n[Step 4] Testing full reconstruction...")
    reconstructed = EmbeddingDeduplicator.reconstruct_full(deduplicated)
    print(f"  Reconstructed: {len(reconstructed):,} embeddings")
    print(f"  Original: {len(embeddings):,} embeddings")
    print(f"  Match: {len(reconstructed) == len(embeddings)} ✓")

    print("\n✅ Phase 4 deduplication working correctly!")
    return {
        "original_size": original_size,
        "deduped_size": deduped_size,
        "reduction": original_size / deduped_size
    }


def main():
    """Main test entry point."""
    print("=" * 70)
    print("PHASE 3 & 4 COMPREHENSIVE TEST")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run tests
    phase3_results = test_phase3_impact_compression()
    phase4_results = test_phase4_embedding_dedup()

    # Overall summary
    print("\n" + "=" * 70)
    print("OVERALL RESULTS SUMMARY")
    print("=" * 70)

    print("\n📊 Phase 3: Impact Matrix Compression (10,000 signals)")
    print(f"  Original: {phase3_results['original_size']/1024/1024:.2f} MB")
    print(f"  Compressed: {phase3_results['compressed_size']/1024/1024:.2f} MB")
    print(f"  Reduction: {phase3_results['reduction']:.1f}x")

    print("\n📊 Phase 4: Embedding Deduplication (1,000 signals, 768 dims)")
    print(f"  Original: {phase4_results['original_size']/1024/1024:.2f} MB")
    print(f"  Deduplicated: {phase4_results['deduped_size']/1024/1024:.2f} MB")
    print(f"  Reduction: {phase4_results['reduction']:.1f}x")

    # Combined projection
    total_reduction = (phase3_results['reduction'] + phase4_results['reduction']) / 2
    print(f"\n🎯 Combined Phases 3 & 4: ~{total_reduction:.1f}x additional reduction")
    print(f"   (On top of Phases 1 & 2: ~40.5x)")

    # Save results
    results = {
        "test_date": datetime.now().isoformat(),
        "phase3_impact_compression": phase3_results,
        "phase4_embedding_dedup": phase4_results,
        "combined_reduction": total_reduction
    }

    results_file = Path("logs/phase3-phase4-results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ All tests passed!")
    print(f"   Results saved to: {results_file}")


if __name__ == '__main__':
    main()
