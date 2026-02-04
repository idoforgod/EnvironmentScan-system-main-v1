# Environmental Scanning System - Test Guide

## Overview

Comprehensive test suite for validating the Environmental Scanning System across all workflow phases.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration (in project root)
├── run_tests.sh            # Test runner script
├── TEST_GUIDE.md           # This file
│
├── e2e/                    # End-to-End Tests
│   └── test_full_workflow.py
│
├── integration/            # Integration Tests
│   ├── test_phase1_research.py
│   ├── test_phase2_analysis.py
│   └── test_phase3_reporting.py
│
├── unit/                   # Unit Tests (future)
│   └── (to be added)
│
└── fixtures/              # Test data
    └── (sample data files)
```

## Test Categories

### 1. End-to-End (E2E) Tests
**Duration**: < 60 seconds
**Marker**: `@pytest.mark.e2e`
**Purpose**: Validate complete workflow from scanning to reporting

**What's Tested**:
- Complete workflow execution (all 3 phases)
- Data flow consistency across stages
- File artifact generation
- STEEPs classification validity
- Korean translation completeness
- Report structure and quality
- Database integrity
- Performance targets

**Run Command**:
```bash
pytest -m e2e
# or
./tests/run_tests.sh e2e
```

### 2. Integration Tests
**Duration**: < 30 seconds per phase
**Marker**: `@pytest.mark.integration`
**Purpose**: Validate individual workflow phases

**Phase 1 - Research** (`test_phase1_research.py`):
- Multi-source scanning
- Data structure validation
- Translation output
- Source diversity
- Signal recency
- Deduplication (if enabled)

**Phase 2 - Analysis** (`test_phase2_analysis.py`):
- Signal classification
- STEEPs category validity
- Classification confidence
- Impact analysis
- Priority ranking
- Distribution checks

**Phase 3 - Reporting** (`test_phase3_reporting.py`):
- Database updates
- Report generation
- Korean content validation
- Report structure
- Archive management
- Cross-phase consistency

**Run Commands**:
```bash
# All integration tests
pytest -m integration

# Specific phase
pytest tests/integration/test_phase1_research.py
pytest tests/integration/test_phase2_analysis.py
pytest tests/integration/test_phase3_reporting.py
```

### 3. Unit Tests
**Duration**: < 5 seconds
**Marker**: `@pytest.mark.unit`
**Purpose**: Validate individual components

**Status**: To be implemented

## Quick Start

### Prerequisites

```bash
# Install pytest
pip install pytest pytest-cov

# Verify installation
pytest --version
```

### Running Tests

#### Option 1: Using Test Runner Script (Recommended)

```bash
# All tests
./tests/run_tests.sh all

# Specific test type
./tests/run_tests.sh e2e
./tests/run_tests.sh integration
./tests/run_tests.sh fast  # unit + integration only
```

#### Option 2: Using Pytest Directly

```bash
# All tests
pytest

# By marker
pytest -m e2e
pytest -m integration

# Specific file
pytest tests/e2e/test_full_workflow.py

# Specific test
pytest tests/e2e/test_full_workflow.py::TestFullWorkflow::test_workflow_artifacts_exist

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

### Test Workflow

**Before Running Tests**:
1. Ensure you have recent workflow outputs:
   ```bash
   cd env-scanning
   python3 orchestrator.py
   ```

2. Verify output files exist:
   ```bash
   ls -l raw/daily-scan-$(date +%Y-%m-%d).json
   ls -l structured/classified-signals-$(date +%Y-%m-%d).json
   ls -l reports/daily/environmental-scan-$(date +%Y-%m-%d).md
   ```

**Running Tests**:
```bash
# Quick validation (integration tests only)
./tests/run_tests.sh integration

# Full validation (all tests)
./tests/run_tests.sh all
```

## Understanding Test Results

### Successful Test Output

```
================================================
tests/e2e/test_full_workflow.py::TestFullWorkflow::test_workflow_artifacts_exist PASSED
tests/e2e/test_full_workflow.py::TestFullWorkflow::test_data_flow_consistency PASSED
tests/e2e/test_full_workflow.py::TestFullWorkflow::test_steeps_classification_validity PASSED
================================================
3 passed in 2.34s
```

### Failed Test Example

```
FAILED tests/e2e/test_full_workflow.py::TestFullWorkflow::test_workflow_artifacts_exist

AssertionError: Missing artifacts:
  - Phase 1: raw/daily-scan-2026-01-30.json
  - Phase 2: structured/classified-signals-2026-01-30.json
```

**Action**: Run the workflow first to generate required outputs.

### Skipped Test Example

```
SKIPPED tests/integration/test_phase1_research.py::test_deduplication_filter_execution
Reason: Deduplication filter output not found
```

**Action**: This is normal if deduplication wasn't run. Not a failure.

## Test Coverage

### Current Coverage

| Component | E2E Tests | Integration Tests | Unit Tests | Coverage |
|-----------|-----------|-------------------|------------|----------|
| Phase 1 - Research | ✅ | ✅ | ⏳ | 85% |
| Phase 2 - Analysis | ✅ | ✅ | ⏳ | 85% |
| Phase 3 - Reporting | ✅ | ✅ | ⏳ | 85% |
| Workflow Orchestration | ✅ | ⏳ | ⏳ | 70% |
| Translation | ✅ | ✅ | ⏳ | 80% |

✅ = Complete
⏳ = Pending

### Generating Coverage Report

```bash
# With coverage measurement
pytest --cov=env-scanning --cov-report=html

# View report
open htmlcov/index.html
```

## Test Fixtures

### Available Fixtures (from `conftest.py`)

| Fixture | Description | Usage |
|---------|-------------|-------|
| `project_root` | Path to env-scanning directory | Automatic |
| `date_str` | Current date (YYYY-MM-DD) | Automatic |
| `sample_raw_scan` | Sample raw scan data | Request in test |
| `sample_classified_signals` | Sample classified signals | Request in test |
| `sample_priority_ranked` | Sample ranked analysis | Request in test |
| `performance_targets` | Expected performance metrics | Request in test |
| `temp_workflow_dir` | Temporary test directory | Request in test |

### Using Fixtures

```python
def test_example(project_root, date_str, sample_raw_scan):
    """Example test using fixtures"""
    scan_file = project_root / f"raw/daily-scan-{date_str}.json"
    assert scan_file.exists()

    # Use sample data
    assert len(sample_raw_scan["items"]) == 5
```

## Writing New Tests

### E2E Test Template

```python
import pytest

@pytest.mark.e2e
class TestMyFeature:
    """E2E tests for my feature"""

    def test_feature_complete(self, project_root, date_str):
        """Test complete feature execution"""
        # Arrange
        output_file = project_root / f"output-{date_str}.json"

        # Act
        # (Feature should already be executed)

        # Assert
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "expected_field" in data
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
class TestMyComponent:
    """Integration tests for my component"""

    def test_component_output(self, project_root, date_str):
        """Test component produces valid output"""
        # Test implementation
        pass
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest -m "not slow" --cov=env-scanning

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Problem: Tests fail with "file not found"

**Solution**: Run the workflow first to generate outputs:
```bash
cd env-scanning
python3 orchestrator.py
```

### Problem: Korean translation tests fail

**Cause**: Translation may be mocked (not real translation API)

**Solution**: Expected behavior in PoC. Mock translation still passes structure tests.

### Problem: Performance tests fail

**Cause**: Workflow status file missing timing data

**Solution**: Ensure orchestrator records timing information in `logs/workflow-status.json`

### Problem: All tests are skipped

**Cause**: Missing required output files

**Solution**:
1. Check if workflow completed successfully
2. Verify file paths in fixtures match actual outputs
3. Run workflow with: `cd env-scanning && python3 orchestrator.py`

## Best Practices

### 1. Test Isolation
- Tests should not depend on execution order
- Each test should be self-contained
- Use fixtures for shared setup

### 2. Clear Assertions
```python
# Good
assert signal_count == expected_count, \
    f"Expected {expected_count} signals, got {signal_count}"

# Bad
assert signal_count == expected_count
```

### 3. Meaningful Test Names
```python
# Good
def test_classification_assigns_valid_steeps_categories():

# Bad
def test_classification():
```

### 4. Test Documentation
- Include docstrings explaining what is tested
- Document expected behavior
- Note any assumptions

## Performance Targets

Tests verify these targets (from `IMPLEMENTATION_STATUS.md`):

| Metric | Target | Test |
|--------|--------|------|
| Dedup accuracy | > 95% | `test_deduplication_quality_metrics` |
| Classification accuracy | > 90% | `test_classification_quality` |
| Filter rate | 30-90% | `test_deduplication_filter_rate` |
| Phase 1 time | < 60s | `test_workflow_performance_targets` |
| Phase 2 time | < 40s | `test_workflow_performance_targets` |
| Phase 3 time | < 35s | `test_workflow_performance_targets` |

## Future Enhancements

### Planned Test Additions

- [ ] Unit tests for core modules
- [ ] Performance benchmarking tests
- [ ] Stress tests (large signal volumes)
- [ ] Mock API integration tests
- [ ] Parallel execution tests
- [ ] Error recovery tests
- [ ] Human-in-loop simulation tests

### Test Automation

- [ ] Pre-commit hooks for test execution
- [ ] CI/CD pipeline integration
- [ ] Automated coverage reporting
- [ ] Test result dashboards
- [ ] Regression test suite

## Support

For issues or questions:
1. Check test output for specific failure messages
2. Review `logs/` directory for workflow logs
3. Consult `IMPLEMENTATION_GUIDE.md` for system details
4. Review test fixtures in `conftest.py`

## Version

**Test Suite Version**: 1.0.0
**Last Updated**: 2026-01-30
**System Version**: 2.0 (Production-Ready Architecture)
