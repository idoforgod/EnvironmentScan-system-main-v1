# TDD Test Framework for Environmental Scanning

## Overview

Comprehensive test suite ensuring system quality at three levels:
1. **Unit Tests** - Per-step validation (< 5 seconds)
2. **Integration Tests** - Per-phase validation (< 30 seconds)
3. **End-to-End Tests** - Full workflow validation (< 60 seconds)

## Test Structure

```
tests/
├── unit/
│   ├── test_archive_loader.py
│   ├── test_multi_source_scanner.py
│   ├── test_deduplication_filter.py
│   ├── test_signal_classifier.py
│   ├── test_impact_analyzer.py
│   ├── test_priority_ranker.py
│   ├── test_database_updater.py
│   ├── test_report_generator.py
│   └── test_archive_notifier.py
│
├── integration/
│   ├── test_phase1_research.py
│   ├── test_phase2_planning.py
│   └── test_phase3_implementation.py
│
├── e2e/
│   └── test_full_workflow.py
│
├── fixtures/
│   ├── sample_raw_scan.json
│   ├── sample_signals.json
│   └── sample_config.yaml
│
└── conftest.py
```

## Running Tests

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end test
pytest tests/e2e/

# Specific agent
pytest tests/unit/test_deduplication_filter.py

# With coverage
pytest --cov=env-scanning tests/

# Verbose output
pytest -v tests/
```

## Unit Test Example

### tests/unit/test_deduplication_filter.py

```python
import pytest
import json
from datetime import datetime

def test_deduplication_filter_output():
    """
    Test deduplication filter output structure and quality
    Execution time: < 5 seconds
    """
    # Load output
    output_file = f"filtered/new-signals-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_file) as f:
        output = json.load(f)

    # Test 1: Required fields present
    assert "filter_metadata" in output
    assert "new_signals" in output

    # Test 2: Metadata completeness
    metadata = output["filter_metadata"]
    assert "total_raw" in metadata
    assert "total_duplicates" in metadata
    assert "total_new" in metadata
    assert "filter_rate" in metadata

    # Test 3: Filter rate in expected range
    filter_rate = metadata["filter_rate"]
    assert 0.3 <= filter_rate <= 0.9, f"Filter rate {filter_rate} out of range"

    # Test 4: No duplicate URLs in output
    urls = [s["source"]["url"] for s in output["new_signals"]]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"

    # Test 5: Stage breakdown adds up
    stage_sum = sum(metadata["stage_breakdown"].values())
    assert stage_sum == metadata["total_duplicates"]

    # Test 6: Log file exists
    log_file = f"logs/duplicates-removed-{datetime.now().strftime('%Y-%m-%d')}.log"
    assert os.path.exists(log_file)

    print("✓ Deduplication filter validation passed")


def test_deduplication_4_stages():
    """Test that all 4 stages were executed"""
    output_file = f"filtered/new-signals-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_file) as f:
        output = json.load(f)

    stages = output["filter_metadata"]["stage_breakdown"]

    assert "stage_1_url" in stages
    assert "stage_2_string" in stages
    assert "stage_3_semantic" in stages
    assert "stage_4_entity" in stages


def test_deduplication_quality_metrics():
    """Test that quality metrics meet targets"""
    # This would require ground truth data
    # For now, check that metrics are recorded

    output_file = f"filtered/new-signals-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_file) as f:
        output = json.load(f)

    # Check confidence distribution exists
    assert "confidence_distribution" in output["filter_metadata"]

    # Most should be high confidence
    confidence = output["filter_metadata"]["confidence_distribution"]
    assert confidence.get("high", 0) > confidence.get("low", 0)
```

## Integration Test Example

### tests/integration/test_phase1_research.py

```python
import pytest
import json
import os
from datetime import datetime

def test_phase1_complete_execution():
    """
    Test entire Phase 1 execution and data flow
    Execution time: < 30 seconds
    """
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Verify all Phase 1 outputs exist
    assert os.path.exists("context/previous-signals.json")
    assert os.path.exists(f"raw/daily-scan-{date_str}.json")
    assert os.path.exists(f"filtered/new-signals-{date_str}.json")

    # Test data flow consistency
    with open(f"raw/daily-scan-{date_str}.json") as f:
        raw_data = json.load(f)

    with open(f"filtered/new-signals-{date_str}.json") as f:
        filtered_data = json.load(f)

    # Raw count > filtered count (duplicates removed)
    assert len(raw_data["items"]) > len(filtered_data["new_signals"])

    # Filter rate calculation is consistent
    expected_filter_rate = 1 - (len(filtered_data["new_signals"]) / len(raw_data["items"]))
    actual_filter_rate = filtered_data["filter_metadata"]["filter_rate"]
    assert abs(expected_filter_rate - actual_filter_rate) < 0.01

    print("✓ Phase 1 integration test passed")


def test_phase1_quality_targets():
    """Test that Phase 1 meets quality targets"""
    date_str = datetime.now().strftime('%Y-%m-%d')

    with open(f"filtered/new-signals-{date_str}.json") as f:
        filtered_data = json.load(f)

    # Target: Filter rate between 30-90%
    filter_rate = filtered_data["filter_metadata"]["filter_rate"]
    assert 0.3 <= filter_rate <= 0.9

    # Target: At least 3 sources scanned
    with open(f"raw/daily-scan-{date_str}.json") as f:
        raw_data = json.load(f)

    sources = {item["source"]["name"] for item in raw_data["items"]}
    assert len(sources) >= 3
```

## End-to-End Test Example

### tests/e2e/test_full_workflow.py

```python
import pytest
import json
import os
from datetime import datetime

def test_full_workflow_execution():
    """
    Test complete workflow from start to finish
    Requires manual human review steps to be automated/mocked
    Execution time: < 60 seconds (excluding human wait time)
    """
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Check workflow status
    with open("logs/workflow-status.json") as f:
        status = json.load(f)

    assert status["status"] == "completed"
    assert status["current_phase"] == 3

    # Verify all major artifacts exist
    artifacts = [
        "context/previous-signals.json",
        f"raw/daily-scan-{date_str}.json",
        f"filtered/new-signals-{date_str}.json",
        f"structured/classified-signals-{date_str}.json",
        f"analysis/priority-ranked-{date_str}.json",
        f"reports/daily/environmental-scan-{date_str}.md",
        "signals/database.json"
    ]

    for artifact in artifacts:
        assert os.path.exists(artifact), f"Missing artifact: {artifact}"

    # Test signal count consistency
    with open(f"filtered/new-signals-{date_str}.json") as f:
        filtered = json.load(f)

    with open(f"structured/classified-signals-{date_str}.json") as f:
        classified = json.load(f)

    assert len(filtered["new_signals"]) == len(classified["signals"])

    # Test STEEPs categories
    for signal in classified["signals"]:
        assert signal["category"] in ["S", "T", "E", "P", "s"]

    # Test report completeness
    with open(f"reports/daily/environmental-scan-{date_str}.md") as f:
        report = f.read()

    required_sections = [
        "## 1. 경영진 요약",
        "## 2. 신규 탐지 신호",
        "## 5. 전략적 시사점"
    ]

    for section in required_sections:
        assert section in report

    # Test Korean language
    import re
    korean_chars = re.findall(r'[가-힣]', report)
    assert len(korean_chars) > 100

    print("✓ End-to-end workflow test passed")


def test_workflow_performance():
    """Test that workflow meets performance targets"""
    with open("logs/workflow-status.json") as f:
        status = json.load(f)

    # Calculate total execution time (excluding human wait)
    # This would need to parse timestamps from logs

    # For now, check that metrics were recorded
    assert "completed_steps" in status
    assert len(status["completed_steps"]) >= 9  # At least 9 main steps
```

## Pytest Configuration

### conftest.py

```python
import pytest
import os
from datetime import datetime

@pytest.fixture
def sample_raw_scan():
    """Load sample raw scan data"""
    with open("tests/fixtures/sample_raw_scan.json") as f:
        return json.load(f)

@pytest.fixture
def sample_signals():
    """Load sample signals database"""
    with open("tests/fixtures/sample_signals.json") as f:
        return json.load(f)

@pytest.fixture
def date_str():
    """Current date string"""
    return datetime.now().strftime('%Y-%m-%d')

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment"""
    # Create test directories if needed
    os.makedirs("tests/fixtures", exist_ok=True)
    yield
    # Cleanup after tests
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    unit: Unit tests (< 5 seconds)
    integration: Integration tests (< 30 seconds)
    e2e: End-to-end tests (< 60 seconds)
    slow: Tests that take longer than 1 minute
```

## Running Tests by Marker

```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Only e2e tests
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Environmental Scanning Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest -m unit --cov=env-scanning

      - name: Run integration tests
        run: pytest -m integration

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Quality Targets

Tests should verify these targets:

- **Duplicate detection**: Precision > 95%, Recall > 90%
- **Classification accuracy**: > 90% for STEEPs
- **Processing time**: Phase 1 < 60s, Phase 2 < 40s, Phase 3 < 35s
- **Report completeness**: All required sections present
- **Database integrity**: No duplicate signal IDs

## Version
**Test Framework Version**: 1.0.0
**Last Updated**: 2026-01-29
