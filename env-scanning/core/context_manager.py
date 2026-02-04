"""
SharedContextManager - Field-level selective loading for shared context store.

Memory Optimization: Loads only required fields instead of entire context file.
Backward Compatible: Provides legacy get_full_context() method.

Usage Example:
    from env_scanning.core import SharedContextManager

    # Initialize
    ctx = SharedContextManager(Path('env-scanning/context/shared-context-2026-01-30.json'))

    # Load specific fields only (memory efficient)
    embeddings = ctx.get_embeddings(['signal-001', 'signal-002'])
    classifications = ctx.get_final_classification()

    # Update specific fields
    ctx.update_classification('signal-001', {
        'final_category': 'T',
        'confidence': 0.95
    })

    # Save changes (partial update by default)
    ctx.save()

    # Legacy mode (backward compatibility)
    full_context = ctx.get_full_context()
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import tempfile
import shutil


class SharedContextManager:
    """
    Selective field loader for shared context store.
    Provides backward-compatible interface with lazy loading.
    """

    # Field names from schema
    FIELD_NAMES = [
        'signal_embeddings',
        'preliminary_analysis',
        'deduplication_analysis',
        'validated_by_experts',
        'final_classification',
        'impact_analysis',
        'priority_ranking',
        'psst_scores',
        'translation_status'
    ]

    def __init__(self, context_file_path: Path):
        """
        Initialize SharedContextManager.

        Args:
            context_file_path: Path to shared context JSON file
        """
        self.context_file = Path(context_file_path)
        self._cache: Dict[str, Any] = {}  # In-memory cache for loaded fields
        self._dirty_fields: Set[str] = set()  # Track modified fields
        self._metadata: Dict[str, Any] = {}  # Workflow metadata

        # Load metadata on initialization (lightweight)
        if self.context_file.exists():
            self._load_metadata()

    def _load_metadata(self):
        """Load only metadata fields (version, workflow_id, timestamps)."""
        with open(self.context_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._metadata = {
                'version': data.get('version', '1.0'),
                'workflow_id': data.get('workflow_id', ''),
                'created_at': data.get('created_at', ''),
                'last_updated': data.get('last_updated', ''),
                'metadata': data.get('metadata', {})
            }

    def _get_field(self, field_name: str, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Load a specific field from context file.

        Args:
            field_name: Name of field to load (e.g., 'signal_embeddings')
            signal_ids: Optional list of signal IDs to filter. If None, load all.

        Returns:
            Dictionary mapping signal IDs to field data
        """
        if field_name not in self.FIELD_NAMES:
            raise ValueError(f"Invalid field name: {field_name}. Must be one of {self.FIELD_NAMES}")

        # Check cache first
        if field_name in self._cache:
            cached_data = self._cache[field_name]
            if signal_ids is None:
                return cached_data
            else:
                return {sid: cached_data[sid] for sid in signal_ids if sid in cached_data}

        # Load from file
        if not self.context_file.exists():
            return {}

        with open(self.context_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            field_data = data.get(field_name, {})

        # Cache the loaded field
        self._cache[field_name] = field_data

        # Filter by signal IDs if provided
        if signal_ids is not None:
            return {sid: field_data[sid] for sid in signal_ids if sid in field_data}

        return field_data

    def _update_field(self, field_name: str, signal_id: str, field_data: Dict[str, Any]):
        """
        Update a specific field for a signal.

        Args:
            field_name: Name of field to update
            signal_id: Signal ID
            field_data: Data to store
        """
        if field_name not in self.FIELD_NAMES:
            raise ValueError(f"Invalid field name: {field_name}")

        # Load field into cache if not already loaded
        if field_name not in self._cache:
            self._cache[field_name] = self._get_field(field_name)

        # Update in cache
        self._cache[field_name][signal_id] = field_data

        # Mark as dirty
        self._dirty_fields.add(field_name)

    # Field-specific getters (load only when needed)

    def get_embeddings(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get signal embeddings (6.6 KB per signal). Load on demand.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to embedding data
        """
        return self._get_field('signal_embeddings', signal_ids)

    def get_preliminary_analysis(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get preliminary analysis from scanner.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to preliminary analysis
        """
        return self._get_field('preliminary_analysis', signal_ids)

    def get_deduplication_analysis(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get deduplication results.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to deduplication analysis
        """
        return self._get_field('deduplication_analysis', signal_ids)

    def get_validated_by_experts(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get expert validation results from RT-AID.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to expert validation
        """
        return self._get_field('validated_by_experts', signal_ids)

    def get_final_classification(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get final classification from @signal-classifier.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to final classification
        """
        return self._get_field('final_classification', signal_ids)

    def get_impact_analysis(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get impact scores and cross-influences.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to impact analysis
        """
        return self._get_field('impact_analysis', signal_ids)

    def get_priority_ranking(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get priority scores and rankings.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to priority ranking
        """
        return self._get_field('priority_ranking', signal_ids)

    def get_psst_scores(self, signal_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get pSST (predicted Signal Scanning Trust) scores.

        Args:
            signal_ids: Optional list of signal IDs to filter

        Returns:
            Dictionary mapping signal IDs to pSST score data
        """
        return self._get_field('psst_scores', signal_ids)

    def get_translation_status(self) -> Dict[str, Any]:
        """
        Get translation status for bilingual workflow.

        Returns:
            Translation status dictionary
        """
        return self._get_field('translation_status')

    # Update methods (mark fields as dirty)

    def update_embeddings(self, signal_id: str, embedding_data: Dict[str, Any]):
        """
        Update embeddings for a signal.

        Args:
            signal_id: Signal ID
            embedding_data: Embedding data (vector, model, computed_at, etc.)
        """
        self._update_field('signal_embeddings', signal_id, embedding_data)

    def update_preliminary_analysis(self, signal_id: str, analysis_data: Dict[str, Any]):
        """
        Update preliminary analysis for a signal.

        Args:
            signal_id: Signal ID
            analysis_data: Preliminary analysis data
        """
        self._update_field('preliminary_analysis', signal_id, analysis_data)

    def update_deduplication_analysis(self, signal_id: str, dedup_data: Dict[str, Any]):
        """
        Update deduplication analysis for a signal.

        Args:
            signal_id: Signal ID
            dedup_data: Deduplication analysis data
        """
        self._update_field('deduplication_analysis', signal_id, dedup_data)

    def update_classification(self, signal_id: str, classification_data: Dict[str, Any]):
        """
        Update final classification for a signal.

        Args:
            signal_id: Signal ID
            classification_data: Classification data (final_category, confidence, etc.)
        """
        self._update_field('final_classification', signal_id, classification_data)

    def update_impact_analysis(self, signal_id: str, impact_data: Dict[str, Any]):
        """
        Update impact analysis for a signal.

        Args:
            signal_id: Signal ID
            impact_data: Impact analysis data
        """
        self._update_field('impact_analysis', signal_id, impact_data)

    def update_priority_ranking(self, signal_id: str, priority_data: Dict[str, Any]):
        """
        Update priority ranking for a signal.

        Args:
            signal_id: Signal ID
            priority_data: Priority ranking data
        """
        self._update_field('priority_ranking', signal_id, priority_data)

    def update_psst_scores(self, signal_id: str, psst_data: Dict[str, Any]):
        """
        Update pSST scores for a signal.

        Args:
            signal_id: Signal ID
            psst_data: pSST score data (psst_score, psst_grade, dimensions, etc.)
        """
        self._update_field('psst_scores', signal_id, psst_data)

    def update_metadata(self, metadata_updates: Dict[str, Any]):
        """
        Update workflow metadata.

        Args:
            metadata_updates: Metadata updates to merge
        """
        self._metadata['metadata'].update(metadata_updates)
        self._metadata['last_updated'] = datetime.now().isoformat()
        self._dirty_fields.add('metadata')

    # Persistence (only write dirty fields)

    def _write_dirty_fields(self):
        """Save only modified fields to disk (partial update)."""
        if not self._dirty_fields:
            return  # Nothing to save

        # Load existing file
        if self.context_file.exists():
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'version': '1.0',
                'workflow_id': self._metadata.get('workflow_id', ''),
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }

        # Update dirty fields
        for field_name in self._dirty_fields:
            if field_name == 'metadata':
                data['metadata'] = self._metadata['metadata']
                data['last_updated'] = self._metadata['last_updated']
            else:
                data[field_name] = self._cache.get(field_name, {})

        # Atomic write using temporary file
        self._atomic_write(data)

        # Clear dirty flags
        self._dirty_fields.clear()

    def _write_full_context(self):
        """Save entire context to disk (full write)."""
        # Load all fields into cache if not already loaded
        for field_name in self.FIELD_NAMES:
            if field_name not in self._cache:
                self._cache[field_name] = self._get_field(field_name)

        # Build complete context
        data = {
            'version': self._metadata.get('version', '1.0'),
            'workflow_id': self._metadata.get('workflow_id', ''),
            'created_at': self._metadata.get('created_at', datetime.now().isoformat()),
            'last_updated': datetime.now().isoformat()
        }

        # Add all field data
        for field_name in self.FIELD_NAMES:
            data[field_name] = self._cache.get(field_name, {})

        # Add metadata
        data['metadata'] = self._metadata.get('metadata', {})

        # Atomic write
        self._atomic_write(data)

        # Clear dirty flags
        self._dirty_fields.clear()

    def _atomic_write(self, data: Dict[str, Any]):
        """
        Write data to file atomically (prevents corruption).

        Args:
            data: Data to write
        """
        # Create parent directory if not exists
        self.context_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=self.context_file.parent,
            delete=False,
            suffix='.tmp'
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = tmp_file.name

        # Atomic move (replace original file)
        shutil.move(tmp_path, self.context_file)

    def save(self, force_full_write: bool = False):
        """
        Save modified fields to disk.

        Args:
            force_full_write: If True, write entire context (legacy mode).
                             If False (default), write only dirty fields (optimized).
        """
        if force_full_write:
            self._write_full_context()
        else:
            self._write_dirty_fields()

    # Backward compatibility

    def get_full_context(self) -> Dict[str, Any]:
        """
        Load entire context file (legacy mode for backward compatibility).

        Returns:
            Complete context dictionary

        Note: This method loads the entire file into memory. For memory efficiency,
              use field-specific getters instead (get_embeddings(), etc.).
        """
        if not self.context_file.exists():
            return {
                'version': '1.0',
                'workflow_id': '',
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'metadata': {}
            }

        with open(self.context_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Utility methods

    def get_metadata(self) -> Dict[str, Any]:
        """Get workflow metadata."""
        return self._metadata.copy()

    def clear_cache(self):
        """Clear in-memory cache (useful for freeing memory)."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """Get approximate size of cached data in bytes."""
        import sys
        return sys.getsizeof(self._cache)

    def get_loaded_fields(self) -> List[str]:
        """Get list of fields currently loaded in cache."""
        return list(self._cache.keys())
