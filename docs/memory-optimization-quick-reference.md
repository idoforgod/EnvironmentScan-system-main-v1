# Memory Optimization Quick Reference

## TL;DR

Two classes for memory optimization:
1. **SharedContextManager** - Load only needed fields (3-5x savings)
2. **RecursiveArchiveLoader** - Load only recent signals (10-20x savings)

Both are 100% backward compatible.

---

## Quick Start

### SharedContextManager

```python
from core.context_manager import SharedContextManager

# Initialize
ctx = SharedContextManager('context/shared-context-2026-01-30.json')

# Load what you need
classifications = ctx.get_final_classification()  # Only this field

# Update
ctx.update_classification('signal-001', {'final_category': 'T', 'confidence': 0.95})

# Save
ctx.save()  # Partial update (fast)
```

**When to use:** Agents that process shared context (classifier, analyzer, ranker)

---

### RecursiveArchiveLoader

```python
from loaders.recursive_archive_loader import RecursiveArchiveLoader

# Initialize
loader = RecursiveArchiveLoader('signals/database.json', 'reports/archive/')

# Load recent (7 days)
recent = loader.load_recent_index(days=7)

# Output (same format as original)
import json
with open('context/previous-signals.json', 'w') as f:
    json.dump(recent, f)
```

**When to use:** Archive loading for deduplication (Step 1.1)

---

## API Cheat Sheet

### SharedContextManager Methods

```python
# Getters (all accept optional signal_ids=[...])
.get_embeddings()              # SBERT vectors
.get_preliminary_analysis()    # Scanner output
.get_deduplication_analysis()  # Dedup results
.get_final_classification()    # STEEPs categories
.get_impact_analysis()         # Impact scores
.get_priority_ranking()        # Priority scores
.get_translation_status()      # Bilingual workflow

# Updaters
.update_embeddings(signal_id, data)
.update_preliminary_analysis(signal_id, data)
.update_classification(signal_id, data)
.update_impact_analysis(signal_id, data)
.update_priority_ranking(signal_id, data)

# Save & Utilities
.save(force_full_write=False)  # Partial update by default
.get_full_context()            # Legacy mode
.clear_cache()                 # Free memory
.get_cache_size()              # Monitor usage
```

### RecursiveArchiveLoader Methods

```python
# Primary
.load_recent_index(days=7)     # Load recent signals
.load_full_archive()           # Legacy mode

# Utilities
.get_statistics(days=7)        # Memory reduction stats
.load_archive_reports(days=90) # Load reports
.merge_signals(db, archive)    # Merge and deduplicate
```

---

## Common Patterns

### Pattern 1: Load → Process → Update

```python
ctx = SharedContextManager('context/shared-context.json')

# Load only what you need
prelim = ctx.get_preliminary_analysis()

# Process
for signal_id, data in signals.items():
    result = process(data, prelim.get(signal_id))
    ctx.update_classification(signal_id, result)

# Save
ctx.save()
```

### Pattern 2: Filter Recent Signals

```python
loader = RecursiveArchiveLoader('signals/database.json', 'reports/archive/')

# Load recent
recent = loader.load_recent_index(days=7)

print(f"Loaded {recent['metadata']['total_signals']} signals")
print(f"Memory saved: {1/recent['metadata']['filter_ratio']:.1f}x")
```

### Pattern 3: Backward Compatible Fallback

```python
ctx = SharedContextManager('context/shared-context.json')

# Try optimized
try:
    data = ctx.get_final_classification()
except Exception:
    # Fallback to legacy
    data = ctx.get_full_context()['final_classification']
```

---

## Memory Savings Calculator

```python
# Signals: N
# Fields loaded: F (out of 8)
# Time window: T days (out of 90)

Savings = (8/F) × (90/T)

# Examples:
# F=1, T=7:  Savings = 8 × 12.9 = 103x
# F=2, T=7:  Savings = 4 × 12.9 = 52x
# F=1, T=30: Savings = 8 × 3 = 24x
```

---

## Integration Checklist

### For Any Agent

- [ ] Import SharedContextManager from `core.context_manager`
- [ ] Replace `json.load()` with field-specific getters
- [ ] Use update methods instead of direct dict assignment
- [ ] Call `save()` at end
- [ ] Test with verification script

### For @archive-loader

- [ ] Import RecursiveArchiveLoader from `loaders.recursive_archive_loader`
- [ ] Replace database loading with `load_recent_index(days=7)`
- [ ] Output to `context/previous-signals.json` as before
- [ ] Verify deduplication still works
- [ ] Monitor filter ratio in logs

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import error | Use relative import: `from core.context_manager import ...` |
| No signals in window | Increase window: `load_recent_index(days=30)` |
| Corruption after save | Already prevented (atomic writes) |
| Memory still high | Call `clear_cache()` after processing |
| Need legacy behavior | Use `get_full_context()` or `load_full_archive()` |

---

## Verification

```bash
cd env-scanning

# Test SharedContextManager
python3 scripts/verify_context_manager.py

# Test RecursiveArchiveLoader
python3 scripts/verify_archive_loader.py

# Both should print: ✅ VERIFICATION PASSED
```

---

## When NOT to Use

**SharedContextManager:**
- Agent needs all fields anyway
- File is small (<100 KB)
- Only run once per workflow

**RecursiveArchiveLoader:**
- Need complete historical analysis
- Signals span >30 days
- Archive is small (<1000 signals)

---

## Performance Tips

1. **Load once per agent run** - Don't re-initialize in loops
2. **Clear cache when done** - Call `clear_cache()` to free memory
3. **Use partial saves** - Default `save()` is faster than `save(force_full_write=True)`
4. **Monitor filter ratio** - Log `filter_ratio` to track savings
5. **Adjust time window** - Increase `days` if missing duplicates

---

## Example: Complete Agent Integration

```python
#!/usr/bin/env python3
"""
Example: Signal Classifier with Memory Optimization
"""

from core.context_manager import SharedContextManager
from pathlib import Path
import json

def classify_signals():
    # Initialize context manager
    ctx = SharedContextManager(Path('context/shared-context-2026-01-30.json'))

    # Load only preliminary analysis (not all 8 fields)
    prelim = ctx.get_preliminary_analysis()

    # Load signals to classify
    with open('filtered/new-signals-2026-01-30.json', 'r') as f:
        signals = json.load(f)['signals']

    results = []
    for signal in signals:
        signal_id = signal['id']

        # Use preliminary analysis for hints
        prelim_data = prelim.get(signal_id, {})

        # Classify (simplified)
        classification = {
            'final_category': prelim_data.get('category_guess', 'T'),
            'confidence': 0.95,
            'classification_source': 'ai_classified',
            'computed_at': 'step_2.1'
        }

        # Update context (in-memory)
        ctx.update_classification(signal_id, classification)

        results.append({**signal, **classification})

    # Save all updates (partial write - fast)
    ctx.save()

    # Output results
    with open('structured/classified-signals-2026-01-30.json', 'w') as f:
        json.dump({'signals': results}, f, indent=2)

    # Log stats
    print(f"Processed {len(results)} signals")
    print(f"Cache size: {ctx.get_cache_size()} bytes")
    print(f"Loaded fields: {ctx.get_loaded_fields()}")

if __name__ == '__main__':
    classify_signals()
```

---

## Further Reading

- **Full Guide:** `docs/memory-optimization-guide.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **Agent Examples:** `.claude/agents/workers/*.md`

---

**Version:** 1.0.0
**Last Updated:** 2026-01-30
