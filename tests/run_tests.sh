#!/bin/bash
# Test runner script for Environmental Scanning System
# Usage: ./tests/run_tests.sh [test-type]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Environmental Scanning System - Test Suite"
echo "=================================================="
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Function to run tests
run_tests() {
    local test_type=$1
    local description=$2
    local marker=$3

    echo -e "${YELLOW}Running $description...${NC}"

    if [ -z "$marker" ]; then
        pytest tests/ -v
    else
        pytest -m "$marker" -v
    fi

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $description passed${NC}"
    else
        echo -e "${RED}✗ $description failed${NC}"
        return $exit_code
    fi

    echo ""
}

# Parse command line argument
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        echo "Running UNIT tests only..."
        run_tests "unit" "Unit Tests" "unit"
        ;;

    integration)
        echo "Running INTEGRATION tests only..."
        run_tests "integration" "Integration Tests" "integration"
        ;;

    e2e)
        echo "Running E2E tests only..."
        run_tests "e2e" "End-to-End Tests" "e2e"
        ;;

    smoke)
        echo "Running SMOKE tests only..."
        run_tests "smoke" "Smoke Tests" "smoke"
        ;;

    fast)
        echo "Running FAST tests (unit + integration)..."
        run_tests "fast" "Unit Tests" "unit"
        run_tests "fast" "Integration Tests" "integration"
        ;;

    all)
        echo "Running ALL tests..."
        run_tests "all" "All Tests" ""
        ;;

    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [test-type]"
        echo ""
        echo "Available test types:"
        echo "  unit         - Unit tests only (< 5 seconds)"
        echo "  integration  - Integration tests only (< 30 seconds)"
        echo "  e2e          - End-to-end tests only (< 60 seconds)"
        echo "  smoke        - Quick smoke tests"
        echo "  fast         - Unit + Integration (no E2E)"
        echo "  all          - All tests (default)"
        exit 1
        ;;
esac

echo "=================================================="
echo -e "${GREEN}Test suite completed successfully!${NC}"
echo "=================================================="
