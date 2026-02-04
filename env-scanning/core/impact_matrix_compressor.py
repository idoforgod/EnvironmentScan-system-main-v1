"""
Impact Matrix Compressor - Phase 3 Memory Optimization

Compresses cross-impact influence matrices using sparse representation.
Reduces memory for N×N impact matrices from O(N²) to O(k) where k = non-zero influences.

Usage:
    from core.impact_matrix_compressor import ImpactMatrixCompressor

    # Compress impact matrix
    compressed = ImpactMatrixCompressor.compress(impact_data)

    # Decompress for analysis
    full_matrix = ImpactMatrixCompressor.decompress(compressed)
"""

import numpy as np
from typing import Dict, List, Any, Tuple
import json

# Note: scipy not required - using custom sparse representation


class ImpactMatrixCompressor:
    """
    Sparse matrix representation for cross-impact influences.

    Memory savings example:
    - 1,000 signals: 1M entries → ~10K non-zero (99% sparse) → 100x reduction
    - 10,000 signals: 100M entries → ~100K non-zero (99.9% sparse) → 1000x reduction
    """

    @classmethod
    def compress(cls, impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress impact analysis data using sparse matrix.

        Args:
            impact_data: Dictionary mapping signal IDs to impact analysis
                {
                    "signal-001": {
                        "impact_score": 7.5,
                        "influences": [
                            {"target_signal": "signal-002", "influence_score": 2.5, "influence_type": "amplifies"},
                            {"target_signal": "signal-015", "influence_score": -1.2, "influence_type": "suppresses"},
                        ]
                    },
                    ...
                }

        Returns:
            Compressed representation with sparse matrix
                {
                    "signal_ids": [...],  # ID to index mapping
                    "impact_scores": {...},  # Signal-level scores
                    "influence_matrix": {
                        "data": [...],      # Non-zero values
                        "row": [...],       # Row indices
                        "col": [...],       # Column indices
                        "shape": (N, N)     # Matrix dimensions
                    },
                    "influence_types": {...},  # Influence type mapping
                    "compression_stats": {...}
                }
        """
        # Extract signal IDs
        signal_ids = sorted(impact_data.keys())
        n_signals = len(signal_ids)

        # Create ID to index mapping
        id_to_idx = {sid: idx for idx, sid in enumerate(signal_ids)}

        # Extract impact scores (not compressed)
        impact_scores = {
            sid: data.get('impact_score', 0.0)
            for sid, data in impact_data.items()
        }

        # Build influence matrix
        row_indices = []
        col_indices = []
        values = []
        influence_types_map = {}  # (row, col) -> type

        for source_id, data in impact_data.items():
            source_idx = id_to_idx[source_id]

            influences = data.get('influences', [])
            for influence in influences:
                target_id = influence.get('target_signal')
                if target_id not in id_to_idx:
                    continue  # Skip if target not in dataset

                target_idx = id_to_idx[target_id]
                score = influence.get('influence_score', 0.0)

                if abs(score) > 0.01:  # Only store non-negligible influences
                    row_indices.append(source_idx)
                    col_indices.append(target_idx)
                    values.append(score)

                    # Store influence type
                    influence_type = influence.get('influence_type', 'neutral')
                    influence_types_map[f"{source_idx},{target_idx}"] = influence_type

        # Create custom sparse representation (no scipy needed)
        # Store as triplet format (row, col, value)

        # Calculate compression stats
        total_cells = n_signals * n_signals
        non_zero_cells = len(values)
        sparsity = 1.0 - (non_zero_cells / total_cells if total_cells > 0 else 0)
        compression_ratio = total_cells / max(non_zero_cells, 1)

        compressed = {
            "version": "1.0",
            "signal_ids": signal_ids,
            "impact_scores": impact_scores,
            "influence_matrix": {
                "row_indices": row_indices,
                "col_indices": col_indices,
                "values": values,
                "shape": (n_signals, n_signals),
                "nnz": len(values),
                "format": "triplet"  # Custom sparse format
            },
            "influence_types": influence_types_map,
            "compression_stats": {
                "total_cells": total_cells,
                "non_zero_cells": non_zero_cells,
                "sparsity": sparsity,
                "compression_ratio": compression_ratio,
                "memory_reduction": f"{compression_ratio:.1f}x"
            }
        }

        return compressed

    @classmethod
    def decompress(cls, compressed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress impact data back to original format.

        Args:
            compressed: Compressed impact data

        Returns:
            Original impact data format
        """
        signal_ids = compressed["signal_ids"]
        impact_scores = compressed["impact_scores"]
        matrix_data = compressed["influence_matrix"]
        influence_types = compressed.get("influence_types", {})

        # Reconstruct from triplet format
        row_indices = matrix_data["row_indices"]
        col_indices = matrix_data["col_indices"]
        values = matrix_data["values"]

        # Build influence map
        influence_map = {}  # row_idx -> [(col_idx, value), ...]
        for row_idx, col_idx, value in zip(row_indices, col_indices, values):
            if row_idx not in influence_map:
                influence_map[row_idx] = []
            influence_map[row_idx].append((col_idx, value))

        # Convert to dictionary format
        impact_data = {}

        for idx, signal_id in enumerate(signal_ids):
            influences = []

            # Get influences for this signal
            if idx in influence_map:
                for target_idx, score in influence_map[idx]:
                    target_id = signal_ids[target_idx]

                    # Get influence type
                    key = f"{idx},{target_idx}"
                    influence_type = influence_types.get(key, "neutral")

                    influences.append({
                        "target_signal": target_id,
                        "influence_score": float(score),
                        "influence_type": influence_type
                    })

            impact_data[signal_id] = {
                "impact_score": impact_scores.get(signal_id, 0.0),
                "influences": influences
            }

        return impact_data

    @classmethod
    def get_compression_stats(cls, compressed: Dict[str, Any]) -> Dict[str, Any]:
        """Get compression statistics."""
        return compressed.get("compression_stats", {})

    @classmethod
    def query_influences(cls, compressed: Dict[str, Any], signal_id: str, threshold: float = 0.5) -> List[Dict]:
        """
        Query influences for a specific signal without full decompression.

        Args:
            compressed: Compressed impact data
            signal_id: Signal ID to query
            threshold: Minimum influence score to return

        Returns:
            List of influences for this signal
        """
        signal_ids = compressed["signal_ids"]
        if signal_id not in signal_ids:
            return []

        idx = signal_ids.index(signal_id)

        matrix_data = compressed["influence_matrix"]
        row_indices = matrix_data["row_indices"]
        col_indices = matrix_data["col_indices"]
        values = matrix_data["values"]

        # Find influences for this signal
        influences = []
        for row_idx, col_idx, value in zip(row_indices, col_indices, values):
            if row_idx == idx and abs(value) >= threshold:
                target_id = signal_ids[col_idx]

                # Get influence type
                key = f"{idx},{col_idx}"
                influence_type = compressed.get("influence_types", {}).get(key, "neutral")

                influences.append({
                    "target_signal": target_id,
                    "influence_score": float(value),
                    "influence_type": influence_type
                })

        return influences


# Convenience functions
def compress_impact_matrix(impact_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compress impact analysis data. Convenience wrapper."""
    return ImpactMatrixCompressor.compress(impact_data)


def decompress_impact_matrix(compressed: Dict[str, Any]) -> Dict[str, Any]:
    """Decompress impact analysis data. Convenience wrapper."""
    return ImpactMatrixCompressor.decompress(compressed)
