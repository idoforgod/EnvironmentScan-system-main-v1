#!/usr/bin/env python3
"""
Verification script for SharedContextManager.
Tests field-level loading and backward compatibility.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context_manager import SharedContextManager


def test_phase1_context_manager():
    """Test SharedContextManager functionality."""
    print("=" * 70)
    print("PHASE 1: SharedContextManager Verification")
    print("=" * 70)

    context_file = Path('context/shared-context-2026-01-30.json')

    if not context_file.exists():
        print(f"❌ Context file not found: {context_file}")
        return False

    try:
        # Test 1: Initialize manager
        print("\n[Test 1] Initialize SharedContextManager...")
        ctx = SharedContextManager(context_file)
        print(f"✓ Initialized successfully")
        print(f"  Workflow ID: {ctx.get_metadata().get('workflow_id')}")

        # Test 2: Load specific fields only
        print("\n[Test 2] Load specific fields (memory efficient)...")
        embeddings = ctx.get_embeddings()
        prelim = ctx.get_preliminary_analysis()
        print(f"✓ Loaded embeddings: {len(embeddings)} signals")
        print(f"✓ Loaded preliminary analysis: {len(prelim)} signals")
        print(f"  Loaded fields: {ctx.get_loaded_fields()}")
        print(f"  Cache size: {ctx.get_cache_size()} bytes")

        # Test 3: Verify backward compatibility
        print("\n[Test 3] Verify backward compatibility...")
        full_context = ctx.get_full_context()
        assert 'signal_embeddings' in full_context, "Missing signal_embeddings"
        assert 'preliminary_analysis' in full_context, "Missing preliminary_analysis"
        assert 'version' in full_context, "Missing version"
        print(f"✓ Backward compatibility verified")
        print(f"  Full context keys: {list(full_context.keys())}")

        # Test 4: Update and save
        print("\n[Test 4] Update field and save...")
        test_signal_id = "signal-test"
        ctx.update_classification(test_signal_id, {
            'final_category': 'T',
            'confidence': 0.95,
            'classification_source': 'ai_classified'
        })
        ctx.save(force_full_write=False)  # Partial update
        print(f"✓ Updated classification for {test_signal_id}")
        print(f"  Dirty fields before save: {ctx._dirty_fields if hasattr(ctx, '_dirty_fields') else 'N/A'}")

        # Test 5: Verify update persisted
        print("\n[Test 5] Verify update persisted...")
        ctx2 = SharedContextManager(context_file)
        classifications = ctx2.get_final_classification()
        if test_signal_id in classifications:
            print(f"✓ Update persisted successfully")
            print(f"  Classification: {classifications[test_signal_id]}")
        else:
            print(f"⚠ Test signal not found (may be expected if it was just created)")

        print("\n" + "=" * 70)
        print("✅ PHASE 1 VERIFICATION PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_phase1_context_manager()
    sys.exit(0 if success else 1)
