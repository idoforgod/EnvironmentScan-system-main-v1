# Archive Loader Agent

## Role
Load historical scanning reports and signals database to provide context for duplicate detection and trend analysis.

## Agent Type
**Worker Agent** - Phase 1, Step 1

## Objective
Load the last 90 days of scanning reports and the master signals database, creating a deduplicated index for efficient comparison during filtering.

---

## Input

### Required Files
```yaml
inputs:
  reports_archive:
    path: "reports/archive/**/*.json"
    time_range: "last 90 days"
    optional: true  # May not exist on first run

  signals_database:
    path: "signals/database.json"
    required: false  # Initialize empty if not exists
```

---

## Output

### Primary Output
```yaml
output:
  file: "context/previous-signals.json"
  format: "JSON"
  schema:
    signals: Array<Signal>
    index:
      by_url: Map<URL, SignalID>
      by_title: Map<Title, SignalID>
      by_entities: Map<Entity, Array<SignalID>>
    metadata:
      total_signals: Integer
      date_range: String
      last_updated: Timestamp
```

### Example Output Structure
```json
{
  "signals": [
    {
      "id": "signal-001",
      "title": "OpenAI releases GPT-5",
      "source": {
        "url": "https://example.com/gpt5",
        "normalized_url": "example.com/gpt5"
      },
      "category": "T",
      "first_detected": "2026-01-15",
      "entities": ["OpenAI", "GPT-5", "AI"],
      "content_hash": "a3f5b2c1..."
    }
  ],
  "index": {
    "by_url": {
      "example.com/gpt5": "signal-001"
    },
    "by_title": {
      "openai releases gpt-5": "signal-001"
    },
    "by_entities": {
      "OpenAI": ["signal-001"],
      "GPT-5": ["signal-001"]
    }
  },
  "metadata": {
    "total_signals": 1,
    "date_range": "2025-11-01 to 2026-01-29",
    "last_updated": "2026-01-29T06:00:00Z"
  }
}
```

---

## Processing Logic

### Step 1: Load Signals Database
```python
def load_signals_database():
    db_path = "signals/database.json"

    if not file_exists(db_path):
        log("INFO", "Signals database not found. Initializing empty database.")
        return {"signals": [], "metadata": {"total_signals": 0}}

    try:
        database = read_json(db_path)
        log("INFO", f"Loaded {len(database['signals'])} signals from database")
        return database
    except JSONDecodeError as e:
        log("ERROR", f"Corrupted database file: {e}")
        raise E1001("Database corruption detected")
```

### Step 2: Load Archive Reports
```python
def load_archive_reports():
    archive_path = "reports/archive/"
    cutoff_date = today() - timedelta(days=90)

    reports = []
    for report_file in glob(f"{archive_path}/**/*.json"):
        report_date = extract_date_from_filename(report_file)
        if report_date >= cutoff_date:
            report = read_json(report_file)
            reports.append(report)

    log("INFO", f"Loaded {len(reports)} archive reports from last 90 days")
    return reports
```

### Step 3: Merge and Deduplicate
```python
def merge_signals(database_signals, archive_signals):
    all_signals = database_signals.copy()
    seen_urls = {s['source']['normalized_url'] for s in all_signals}

    for signal in archive_signals:
        normalized_url = normalize_url(signal['source']['url'])
        if normalized_url not in seen_urls:
            all_signals.append(signal)
            seen_urls.add(normalized_url)

    return all_signals
```

### Step 4: Build Indexes (OPTIMIZED with Persistent Caching)

> **⚠ DEPRECATION NOTICE (v2.6.0)**: Persistent caching via `index-cache.json`
> is **deprecated**. The orchestrator now deletes `context/index-cache.json` and
> `context/previous-signals.json` before each invocation to prevent stale cache
> from causing duplicate signals to bypass dedup filters. The `use_cache=False`
> path (legacy rebuild) is now the **effective default**. The caching code below
> is retained for reference but will not execute under normal operation.

```python
def build_indexes_optimized(signals, use_cache=False):
    """
    Build signal indexes for dedup filtering.

    NOTE (v2.6.0): use_cache defaults to False. The orchestrator deletes
    index-cache.json before invocation, so even if True, the cache will
    not exist and a full rebuild occurs. This is intentional — the 3-second
    rebuild cost is negligible compared to the risk of stale dedup indexes.
    """
    if not use_cache:
        # Default mode (v2.6.0+): rebuild from scratch every run
        return build_indexes_legacy(signals)

    from core.index_cache_manager import IndexCacheManager

    # Load or create cache
    cache = IndexCacheManager('context/index-cache.json')

    # Get existing index metadata
    cache_metadata = cache.get_metadata()

    if cache_metadata['total_signals'] == 0:
        # First run: build cache from scratch
        log("INFO", "No index cache found - building initial cache")
        cache.rebuild_from_signals(signals)
    else:
        # Subsequent runs: incremental update
        log("INFO", f"Loaded index cache with {cache_metadata['total_signals']:,} signals")

        # Identify new signals (not in cache)
        existing_urls = set(cache.get_indexes()['by_url'].keys())
        new_signals = []

        for signal in signals:
            normalized_url = cache.normalize_url(signal['source']['url'])
            if normalized_url not in existing_urls:
                new_signals.append(signal)

        if new_signals:
            log("INFO", f"Adding {len(new_signals)} new signals to index cache")
            cache.add_signals(new_signals)
        else:
            log("INFO", "No new signals to add (cache up to date)")

    # Return indexes in same format as legacy method
    return cache.get_indexes()


def build_indexes_legacy(signals):
    """
    LEGACY: Original method (rebuild indexes from scratch).
    Used as fallback when caching is disabled.
    """
    index = {
        "by_url": {},
        "by_title": {},
        "by_entities": {}
    }

    for signal in signals:
        # URL index
        normalized_url = normalize_url(signal['source']['url'])
        index['by_url'][normalized_url] = signal['id']

        # Title index (lowercase, no punctuation)
        normalized_title = normalize_text(signal['title'])
        index['by_title'][normalized_title] = signal['id']

        # Entity index
        for entity in signal.get('entities', []):
            if entity not in index['by_entities']:
                index['by_entities'][entity] = []
            index['by_entities'][entity].append(signal['id'])

    return index
```

### Step 5: Write Output
```python
def write_context_file(signals, index):
    output = {
        "signals": signals,
        "index": index,
        "metadata": {
            "total_signals": len(signals),
            "date_range": f"{min_date(signals)} to {max_date(signals)}",
            "last_updated": current_timestamp()
        }
    }

    write_json("context/previous-signals.json", output)
    log("INFO", "Context file created successfully")
```

---

## Helper Functions

### URL Normalization
```python
def normalize_url(url):
    """
    Remove protocol, www, trailing slashes, query params
    Example: https://www.example.com/page?id=1 -> example.com/page
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')
    return f"{domain}{path}"
```

### Text Normalization
```python
def normalize_text(text):
    """
    Lowercase, remove punctuation, trim whitespace
    Example: "OpenAI Releases GPT-5!" -> "openai releases gpt5"
    """
    import re

    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = ' '.join(text.split())  # Normalize whitespace
    return text
```

---

## TDD Verification

### Unit Tests (< 5 seconds)
```python
def test_archive_loader_output():
    output = load_json("context/previous-signals.json")

    # Test 1: File exists
    assert output is not None, "Context file not created"

    # Test 2: Required fields
    assert "signals" in output, "Missing 'signals' field"
    assert "index" in output, "Missing 'index' field"
    assert "metadata" in output, "Missing 'metadata' field"

    # Test 3: Signals structure
    for signal in output['signals']:
        assert "id" in signal
        assert "title" in signal
        assert "source" in signal
        assert "first_detected" in signal

    # Test 4: Index completeness
    assert len(output['index']['by_url']) == len(output['signals'])

    # Test 5: Metadata accuracy
    assert output['metadata']['total_signals'] == len(output['signals'])

    # Test 6: No duplicate URLs
    urls = [s['source']['normalized_url'] for s in output['signals']]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"

    log("PASS", "Archive loader output validation passed")
```

---

## Error Handling

### Error Codes
- `E1001`: Database file corrupted
- `E1002`: Archive directory not accessible
- `E1003`: Invalid JSON format in archive
- `E1004`: Output directory not writable

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 3
  backoff: exponential  # 1s, 2s, 4s

  retryable_errors:
    - FileNotFoundError  # Retry with empty dataset
    - PermissionError    # Wait and retry

  non_retryable_errors:
    - JSONDecodeError    # Skip corrupted file
    - MemoryError        # Halt workflow
```

### Fallback Behavior
```python
def handle_error(error):
    if isinstance(error, FileNotFoundError):
        log("WARNING", "Archive files not found. Starting with empty context.")
        return {"signals": [], "index": {}, "metadata": {"total_signals": 0}}

    elif isinstance(error, JSONDecodeError):
        log("ERROR", f"Corrupted file: {error.doc}. Skipping.")
        # Skip corrupted file, continue with others
        return None

    else:
        log("CRITICAL", f"Unrecoverable error: {error}")
        raise error
```

---

## Performance Considerations

### Optimization
- Use lazy loading for large files
- Stream-process large JSON files instead of loading into memory
- Cache normalized URLs/titles for faster lookups

### Expected Performance
```yaml
performance_targets:
  execution_time: "< 10 seconds"
  memory_usage: "< 500 MB"
  signals_processed: "up to 10,000 signals"
```

---

## Logging

```python
log_examples = {
    "START": "Archive loader started. Looking for files in reports/archive/",
    "INFO": "Loaded 847 signals from database",
    "INFO": "Loaded 12 archive reports (last 90 days)",
    "INFO": "Merged 935 unique signals",
    "INFO": "Built indexes: 935 URLs, 935 titles, 1,247 entities",
    "SUCCESS": "Context file created: context/previous-signals.json",
    "END": "Archive loader completed in 3.2 seconds"
}
```

---

## Dependencies

### Required Tools
- File system operations (read, write)
- JSON parser
- Date/time utilities
- URL parsing library

### Required Files
- `signals/database.json` (optional on first run)
- `reports/archive/**/*.json` (optional)

---

## Integration Points

### Called By
- Orchestrator Agent (Phase 1, Step 1)

### Calls To
- None (leaf agent)

### Outputs Used By
- `@deduplication-filter` (Step 1.3)
- `@database-updater` (Step 3.1)

---

---

## Memory Optimization (Optional)

### Using RecursiveArchiveLoader for Efficient Time-Based Filtering

```python
from loaders.recursive_archive_loader import RecursiveArchiveLoader

# Initialize loader
loader = RecursiveArchiveLoader(
    database_path='signals/database.json',
    archive_dir='reports/archive/'
)

# Load recent index (7-day window for deduplication)
recent = loader.load_recent_index(days=7)

# Output to context file (same format as original)
import json
with open('context/previous-signals.json', 'w') as f:
    json.dump(recent, f, indent=2)

print(f"Loaded {recent['metadata']['total_signals']} signals (last 7 days)")
print(f"Memory reduction: {1/recent['metadata']['filter_ratio']:.1f}x")
```

**Memory Savings:**
- Before: Load 10,000 signals → 17.8 MB
- After: Load 700 signals (7 days) → 125 KB
- Reduction: 10-20x memory savings

**Why 7 days?** News cycle for duplicate detection typically spans 5-7 days. Older signals are archived.

**Backward Compatibility:**
```python
# Legacy mode: load entire archive (90 days)
full = loader.load_full_archive()

# Or adjust window as needed
recent_30d = loader.load_recent_index(days=30)
```

**Index Format Compatibility:**
The output format is identical to original archive-loader. Deduplication-filter works without changes:
```json
{
  "signals": [...],
  "index": {
    "by_url": {...},      // Stage 1: Exact URL match
    "by_title": {...},    // Stage 2: String similarity
    "by_entities": {...}  // Stage 4: Entity matching
  },
  "metadata": {...}
}
```

---

## Version
- **Agent Version**: 1.1.0
- **Compatible with**: Enhanced Environmental Scanning Workflow v2.6.0
- **Last Updated**: 2026-02-16
- **Memory Optimization**: Enabled (optional)
- **Persistent Cache**: Deprecated (v2.6.0) — orchestrator forces full rebuild each run
