"""
Embedding Deduplicator - Phase 4 Memory Optimization

Deduplicates similar embeddings using clustering and representative selection.
Reduces memory for N×768-dimensional embeddings by identifying similar signals.

Memory savings:
- 10,000 signals × 768 dims × 4 bytes = 30.7 MB
- After deduplication (assuming 20% similar): 8,000 unique + 2,000 references = 24.6 MB
- Reduction: ~20-30%

Usage:
    from core.embedding_deduplicator import EmbeddingDeduplicator

    # Deduplicate embeddings
    deduped = EmbeddingDeduplicator.deduplicate(embeddings, threshold=0.95)

    # Retrieve embedding (with fallback to representative)
    vector = EmbeddingDeduplicator.get_embedding(deduped, 'signal-001')
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import json

# Note: sklearn not required - using custom implementations


class EmbeddingDeduplicator:
    """
    Deduplicate similar embeddings using clustering.

    Strategy:
    1. Group highly similar embeddings (cosine similarity > threshold)
    2. Keep one representative per group
    3. Store references for duplicates
    4. Memory reduction proportional to similarity rate
    """

    @classmethod
    def deduplicate(cls,
                    embeddings: Dict[str, Any],
                    similarity_threshold: float = 0.95,
                    method: str = "clustering") -> Dict[str, Any]:
        """
        Deduplicate similar embeddings.

        Args:
            embeddings: Dictionary mapping signal IDs to embedding data
                {
                    "signal-001": {
                        "vector": [0.1, 0.2, ...],  # 768 dims
                        "model": "SBERT",
                        "computed_at": "step_1.3"
                    },
                    ...
                }
            similarity_threshold: Cosine similarity threshold (0.95 = 95% similar)
            method: Deduplication method ("clustering" or "pairwise")

        Returns:
            Deduplicated embeddings
                {
                    "version": "1.0",
                    "unique_embeddings": {
                        "signal-001": {"vector": [...], "model": "SBERT", ...},
                        "signal-050": {"vector": [...], "model": "SBERT", ...},
                    },
                    "references": {
                        "signal-002": "signal-001",  # Points to representative
                        "signal-003": "signal-001",
                    },
                    "deduplication_stats": {
                        "total_embeddings": 1000,
                        "unique_embeddings": 850,
                        "duplicate_embeddings": 150,
                        "deduplication_rate": 0.15,
                        "memory_reduction": "1.18x"
                    }
                }
        """
        if not embeddings:
            return {
                "version": "1.0",
                "unique_embeddings": {},
                "references": {},
                "deduplication_stats": {}
            }

        if method == "clustering":
            return cls._deduplicate_clustering(embeddings, similarity_threshold)
        else:
            return cls._deduplicate_pairwise(embeddings, similarity_threshold)

    @classmethod
    def _deduplicate_clustering(cls, embeddings: Dict[str, Any], threshold: float) -> Dict[str, Any]:
        """Deduplicate using simple greedy clustering (no sklearn needed)."""
        # Extract signal IDs and vectors
        signal_ids = list(embeddings.keys())
        vectors = np.array([emb["vector"] for emb in embeddings.values()], dtype=np.float32)

        if len(vectors) == 0:
            return cls._empty_result()

        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors_normalized = vectors / (norms + 1e-8)

        # Greedy clustering
        unique_embeddings = {}
        references = {}
        assigned = set()
        cluster_count = 0

        for i, signal_id in enumerate(signal_ids):
            if i in assigned:
                continue

            # This becomes a cluster representative
            unique_embeddings[signal_id] = embeddings[signal_id]
            assigned.add(i)
            cluster_members = [i]

            # Find similar vectors
            for j in range(i + 1, len(signal_ids)):
                if j in assigned:
                    continue

                # Compute cosine similarity
                similarity = np.dot(vectors_normalized[i], vectors_normalized[j])

                if similarity >= threshold:
                    # Add to cluster
                    references[signal_ids[j]] = signal_id
                    assigned.add(j)
                    cluster_members.append(j)

            if len(cluster_members) > 1:
                cluster_count += 1

        # Calculate stats
        total = len(embeddings)
        unique = len(unique_embeddings)
        duplicates = len(references)
        dedup_rate = duplicates / total if total > 0 else 0
        memory_reduction = total / unique if unique > 0 else 1.0

        return {
            "version": "1.0",
            "method": "clustering",
            "threshold": threshold,
            "unique_embeddings": unique_embeddings,
            "references": references,
            "deduplication_stats": {
                "total_embeddings": total,
                "unique_embeddings": unique,
                "duplicate_embeddings": duplicates,
                "deduplication_rate": dedup_rate,
                "memory_reduction": f"{memory_reduction:.2f}x",
                "clusters_found": cluster_count
            }
        }

    @classmethod
    def _deduplicate_pairwise(cls, embeddings: Dict[str, Any], threshold: float) -> Dict[str, Any]:
        """Deduplicate using pairwise similarity (custom implementation)."""
        signal_ids = list(embeddings.keys())
        vectors = np.array([emb["vector"] for emb in embeddings.values()], dtype=np.float32)

        if len(vectors) == 0:
            return cls._empty_result()

        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors_normalized = vectors / (norms + 1e-8)

        # Find duplicates
        unique_embeddings = {}
        references = {}
        processed = set()

        for i, signal_id in enumerate(signal_ids):
            if signal_id in processed:
                continue

            # This is a unique embedding
            unique_embeddings[signal_id] = embeddings[signal_id]
            processed.add(signal_id)

            # Find all similar signals
            for j in range(i + 1, len(signal_ids)):
                if signal_ids[j] in processed:
                    continue

                # Cosine similarity
                similarity = np.dot(vectors_normalized[i], vectors_normalized[j])

                if similarity >= threshold:
                    # Mark as duplicate
                    references[signal_ids[j]] = signal_id
                    processed.add(signal_ids[j])

        # Calculate stats
        total = len(embeddings)
        unique = len(unique_embeddings)
        duplicates = len(references)
        dedup_rate = duplicates / total if total > 0 else 0
        memory_reduction = total / unique if unique > 0 else 1.0

        return {
            "version": "1.0",
            "method": "pairwise",
            "threshold": threshold,
            "unique_embeddings": unique_embeddings,
            "references": references,
            "deduplication_stats": {
                "total_embeddings": total,
                "unique_embeddings": unique,
                "duplicate_embeddings": duplicates,
                "deduplication_rate": dedup_rate,
                "memory_reduction": f"{memory_reduction:.2f}x"
            }
        }

    @classmethod
    def _empty_result(cls) -> Dict[str, Any]:
        """Return empty deduplication result."""
        return {
            "version": "1.0",
            "unique_embeddings": {},
            "references": {},
            "deduplication_stats": {
                "total_embeddings": 0,
                "unique_embeddings": 0,
                "duplicate_embeddings": 0,
                "deduplication_rate": 0.0,
                "memory_reduction": "1.00x"
            }
        }

    @classmethod
    def get_embedding(cls, deduplicated: Dict[str, Any], signal_id: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for a signal (resolves references).

        Args:
            deduplicated: Deduplicated embeddings
            signal_id: Signal ID

        Returns:
            Embedding vector or None if not found
        """
        # Check if it's a unique embedding
        if signal_id in deduplicated["unique_embeddings"]:
            return np.array(deduplicated["unique_embeddings"][signal_id]["vector"])

        # Check if it's a reference
        if signal_id in deduplicated["references"]:
            representative = deduplicated["references"][signal_id]
            return np.array(deduplicated["unique_embeddings"][representative]["vector"])

        return None

    @classmethod
    def get_stats(cls, deduplicated: Dict[str, Any]) -> Dict[str, Any]:
        """Get deduplication statistics."""
        return deduplicated.get("deduplication_stats", {})

    @classmethod
    def reconstruct_full(cls, deduplicated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconstruct full embeddings dictionary (resolve all references).

        Args:
            deduplicated: Deduplicated embeddings

        Returns:
            Full embeddings dictionary
        """
        full_embeddings = {}

        # Copy unique embeddings
        full_embeddings.update(deduplicated["unique_embeddings"])

        # Resolve references
        for signal_id, representative in deduplicated["references"].items():
            full_embeddings[signal_id] = deduplicated["unique_embeddings"][representative]

        return full_embeddings


# Convenience functions
def deduplicate_embeddings(embeddings: Dict[str, Any],
                          similarity_threshold: float = 0.95) -> Dict[str, Any]:
    """Deduplicate embeddings. Convenience wrapper."""
    return EmbeddingDeduplicator.deduplicate(embeddings, similarity_threshold)


def get_embedding(deduplicated: Dict[str, Any], signal_id: str) -> Optional[np.ndarray]:
    """Get embedding vector. Convenience wrapper."""
    return EmbeddingDeduplicator.get_embedding(deduplicated, signal_id)
