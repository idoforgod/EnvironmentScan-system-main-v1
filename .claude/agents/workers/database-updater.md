# Database Updater Agent

## Role
Update master signals database with new signals and track signal evolution over time.

## Agent Type
**Worker Agent** - Phase 3, Step 1 (**CRITICAL**)

## Objective
Safely update signals database with comprehensive backup and integrity verification.

---

## Input
- `structured/classified-signals-{date}.json` (from @signal-classifier)
- `signals/database.json` (existing master database)

## Output
- `signals/database.json` (updated)
- `signals/snapshots/database-{date}.json` (backup)

---

## Critical Operations

### 1. Backup First (MANDATORY)
```python
def backup_database():
    """
    ALWAYS create backup before any modification
    """
    source = "signals/database.json"
    backup = f"signals/snapshots/database-{today()}.json"

    if file_exists(source):
        copy_file(source, backup)
        verify_backup_integrity(source, backup)
        log("INFO", f"Backup created: {backup}")
    else:
        log("WARNING", "No existing database. Initializing new one.")
```

### 2. Load and Validate
```python
def load_database():
    db_path = "signals/database.json"

    if not file_exists(db_path):
        return initialize_empty_database()

    database = read_json(db_path)

    # Validate structure
    assert "signals" in database
    assert "metadata" in database

    return database


def initialize_empty_database():
    return {
        "signals": [],
        "metadata": {
            "created_date": today(),
            "last_updated": today(),
            "total_signals": 0,
            "version": "1.0"
        }
    }
```

### 3. Merge New Signals
```python
def merge_new_signals(database, new_signals):
    """
    Add new signals and update status of existing ones
    """
    existing_ids = {s['id'] for s in database['signals']}

    added_count = 0
    updated_count = 0

    for signal in new_signals:
        if signal['id'] not in existing_ids:
            # New signal - add to database
            database['signals'].append(signal)
            added_count += 1
        else:
            # Existing signal - update status
            update_signal_status(database, signal)
            updated_count += 1

    log("INFO", f"Added {added_count} new signals, updated {updated_count} existing")

    return database


def update_signal_status(database, new_signal):
    """
    If signal already exists, update its status (emerging → developing → mature)
    Track trend: strengthening or weakening
    """
    for i, existing_signal in enumerate(database['signals']):
        if existing_signal['id'] == new_signal['id']:
            # Update status evolution
            status_progression = {
                "emerging": "developing",
                "developing": "mature",
                "mature": "mature"
            }

            old_status = existing_signal['status']
            new_status = status_progression.get(old_status, old_status)

            database['signals'][i]['status'] = new_status
            database['signals'][i]['last_seen'] = today()
            database['signals'][i]['trend'] = calculate_trend(existing_signal, new_signal)

            log("INFO", f"Updated signal {new_signal['id']}: {old_status} → {new_status}")
            break
```

### 4. Integrity Check
```python
def verify_database_integrity(database):
    """
    Check for:
    - Duplicate IDs
    - Missing required fields
    - Invalid values
    """
    signal_ids = [s['id'] for s in database['signals']]

    # Check 1: No duplicates
    assert len(signal_ids) == len(set(signal_ids)), "Duplicate signal IDs detected!"

    # Check 2: All signals have required fields
    required_fields = ["id", "category", "title", "date"]
    for signal in database['signals']:
        for field in required_fields:
            assert field in signal, f"Signal {signal.get('id', 'unknown')} missing field: {field}"

    # Check 3: Valid categories
    valid_categories = ['S', 'T', 'E', 'P', 's']
    for signal in database['signals']:
        assert signal['category'] in valid_categories

    log("PASS", "Database integrity verified")
```

### 5. Write with Atomic Operation
```python
def save_database_atomic(database):
    """
    Write to temp file first, then atomic rename
    Prevents corruption if write fails
    """
    temp_path = "signals/database.json.tmp"
    final_path = "signals/database.json"

    # Update metadata
    database['metadata']['last_updated'] = today()
    database['metadata']['total_signals'] = len(database['signals'])

    # Write to temp
    write_json(temp_path, database)

    # Verify temp file
    verify_json_valid(temp_path)

    # Atomic rename (OS-level atomic operation)
    os.rename(temp_path, final_path)

    log("SUCCESS", f"Database updated: {len(database['signals'])} total signals")
```

---

## TDD Verification

```python
def test_database_update():
    # Test 1: Backup exists
    backup_path = f"signals/snapshots/database-{today()}.json"
    assert file_exists(backup_path), "Backup not created"

    # Test 2: Updated database exists
    assert file_exists("signals/database.json")

    # Test 3: Database integrity
    database = load_json("signals/database.json")
    verify_database_integrity(database)

    # Test 4: New signals added
    # (Compare with input file count)

    log("PASS", "Database update validation passed")
```

---

## Error Handling (CRITICAL)

```yaml
error_handling:
  on_any_error:
    action: "HALT workflow immediately"
    reason: "Database corruption is unacceptable"

  recovery_procedure:
    1. "Restore from backup"
    2. "Investigate failure cause"
    3. "Fix issue"
    4. "Retry update"

max_attempts: 5  # Retry more than usual due to criticality
```

---

## Performance Targets
- Execution time: < 5 seconds
- Data loss risk: 0% (via backup + atomic write)
- Integrity guarantee: 100%

## Version
**Agent Version**: 1.0.0
**Criticality**: CRITICAL - Failure stops workflow
**Last Updated**: 2026-01-29
