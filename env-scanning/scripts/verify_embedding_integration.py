#!/usr/bin/env python3
"""
Verify Phase 4 EmbeddingDeduplicator Integration
Tests that embeddings are properly deduplicated and can be retrieved
"""

import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embedding_deduplicator import EmbeddingDeduplicator


def test_embedding_deduplication():
    """Test embedding deduplication with sample data"""
    print("=" * 70)
    print("EMBEDDING DEDUPLICATION INTEGRATION TEST")
    print("=" * 70)

    # Step 1: Generate sample embeddings (simulating multi-source-scanner output)
    print("\n[Step 1] Generating sample embeddings...")

    n_signals = 100
    embedding_dim = 768

    # Create sample embeddings (simulate SBERT output)
    embeddings = {}

    # Create 10 clusters of similar signals (10 signals per cluster)
    n_clusters = 10
    cluster_centers = np.random.randn(n_clusters, embedding_dim).astype(np.float32)

    for i in range(n_signals):
        signal_id = f"raw-{i+1:03d}"

        # Assign to cluster with noise
        cluster_idx = i % n_clusters
        base_vector = cluster_centers[cluster_idx]
        noise = np.random.randn(embedding_dim).astype(np.float32) * 0.02  # 2% noise

        vector = base_vector + noise
        vector = vector / np.linalg.norm(vector)  # Normalize

        embeddings[signal_id] = {
            "vector": vector.tolist(),
            "model": "SBERT",
            "computed_at": "step_1.2",
            "text_source": f"Sample text for signal {i+1}"
        }

    original_size = len(json.dumps(embeddings))
    print(f"  Generated {n_signals} embeddings ({embedding_dim} dims)")
    print(f"  Original size: {original_size:,} bytes ({original_size/1024:.2f} KB)")

    # Step 2: Apply deduplication
    print("\n[Step 2] Applying embedding deduplication...")

    deduplicated = EmbeddingDeduplicator.deduplicate(
        embeddings,
        similarity_threshold=0.95  # 95% similarity = duplicate
    )

    deduped_size = len(json.dumps(deduplicated))
    print(f"  Deduplicated size: {deduped_size:,} bytes ({deduped_size/1024:.2f} KB)")

    stats = deduplicated["deduplication_stats"]
    print(f"\n  Deduplication Stats:")
    print(f"    Total embeddings:     {stats['total_embeddings']}")
    print(f"    Unique embeddings:    {stats['unique_embeddings']}")
    print(f"    Duplicate embeddings: {stats['duplicate_embeddings']}")
    print(f"    Deduplication rate:   {stats['deduplication_rate']:.1%}")
    print(f"    Memory reduction:     {stats['memory_reduction']}")

    # Step 3: Verify retrieval (simulating deduplication-filter usage)
    print("\n[Step 3] Verifying embedding retrieval...")

    test_signals = ["raw-001", "raw-002", "raw-010", "raw-050"]

    retrieval_success = 0
    for signal_id in test_signals:
        # Original embedding
        original_vector = np.array(embeddings[signal_id]["vector"])

        # Retrieved embedding (may be reference to representative)
        retrieved_vector = EmbeddingDeduplicator.get_embedding(deduplicated, signal_id)

        if retrieved_vector is not None:
            # Calculate similarity
            similarity = np.dot(original_vector, retrieved_vector) / (
                np.linalg.norm(original_vector) * np.linalg.norm(retrieved_vector)
            )

            is_reference = signal_id in deduplicated["references"]
            status = "reference" if is_reference else "unique"

            print(f"  {signal_id}: similarity={similarity:.4f}, status={status}")

            if similarity > 0.95:
                retrieval_success += 1
        else:
            print(f"  {signal_id}: NOT FOUND ✗")

    print(f"\n  Retrieval test: {retrieval_success}/{len(test_signals)} passed")

    # Step 4: Test format compatibility (shared-context structure)
    print("\n[Step 4] Testing shared-context format compatibility...")

    # Simulate shared-context structure
    shared_context = {
        "version": "1.0",
        "workflow_id": f"test-{datetime.now().strftime('%Y-%m-%d')}",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "signal_embeddings": deduplicated,  # Deduplicated format
        "preliminary_analysis": {},
        "metadata": {
            "total_signals_processed": n_signals,
            "embedding_optimization": "phase4_deduplication"
        }
    }

    # Verify structure
    assert "signal_embeddings" in shared_context
    assert "version" in shared_context["signal_embeddings"]
    assert "unique_embeddings" in shared_context["signal_embeddings"]
    assert "references" in shared_context["signal_embeddings"]

    print("  ✓ Shared-context structure valid")
    print(f"  ✓ Embeddings field: {len(json.dumps(shared_context['signal_embeddings'])):,} bytes")

    # Step 5: Test deduplication-filter compatibility
    print("\n[Step 5] Testing deduplication-filter compatibility...")

    # Simulate retrieval from shared-context (as dedup-filter would do)
    signal_embeddings = shared_context["signal_embeddings"]

    # Test different retrieval patterns
    test_cases = [
        ("raw-001", "unique embedding"),
        ("raw-002", "potentially referenced"),
        ("raw-050", "mid-range signal")
    ]

    for signal_id, description in test_cases:
        # Handle both deduplicated and regular formats
        if "version" in signal_embeddings and signal_embeddings.get("version") == "1.0":
            # Phase 4 deduplicated format
            embedding = EmbeddingDeduplicator.get_embedding(signal_embeddings, signal_id)
        else:
            # Legacy format
            emb_data = signal_embeddings.get(signal_id)
            embedding = np.array(emb_data["vector"]) if emb_data else None

        if embedding is not None:
            print(f"  ✓ {signal_id}: Retrieved successfully ({description})")
        else:
            print(f"  ✗ {signal_id}: Retrieval failed")

    # Step 6: Performance comparison
    print("\n[Step 6] Performance comparison...")

    print(f"  Original size:      {original_size/1024:.2f} KB")
    print(f"  Deduplicated size:  {deduped_size/1024:.2f} KB")
    print(f"  Reduction:          {original_size/deduped_size:.2f}x")

    expected_reduction = 1.2  # Minimum 20% reduction
    actual_reduction = original_size / deduped_size

    if actual_reduction >= expected_reduction:
        print(f"  ✓ Achieved target reduction (>= {expected_reduction:.1f}x)")
    else:
        print(f"  ⚠️  Below target reduction (expected >= {expected_reduction:.1f}x)")

    # Final verdict
    print("\n" + "=" * 70)

    if retrieval_success == len(test_signals) and actual_reduction >= expected_reduction:
        print("✅ ALL TESTS PASSED")
        print("   Embedding deduplication integration verified")
        return 0
    else:
        print("⚠️  TESTS COMPLETED WITH WARNINGS")
        return 1


def main():
    """Main test execution"""
    return test_embedding_deduplication()


if __name__ == "__main__":
    exit(main())
