#!/bin/bash
#
# Daily Environmental Scan
# Run complete scan: multi-source → database update → report
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}   Environmental Scanning System - Daily Scan${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Date stamp
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)

echo -e "${GREEN}[${TIME}] START${NC} Daily scan started"
echo -e "Date: $DATE"
echo -e "Project: $PROJECT_DIR"
echo ""

# Step 1: Multi-Source Scan
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 1: Multi-Source Scan${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

python3 scripts/run_multi_source_scan.py --days-back 7

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Multi-source scan failed"
    exit 1
fi

echo ""

# Step 2: Update Database
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 2: Update Database${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

SCAN_FILE="raw/daily-scan-${DATE}.json"

if [ ! -f "$SCAN_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} Scan file not found: $SCAN_FILE"
    exit 1
fi

python3 scripts/update_database.py "$SCAN_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR]${NC} Database update failed"
    exit 1
fi

echo ""

# Step 3: Show Quick Summary
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}STEP 3: Quick Summary${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Latest report
REPORT_FILE="reports/daily/environmental-scan-${DATE}.md"

if [ -f "$REPORT_FILE" ]; then
    echo -e "${GREEN}✓${NC} Daily report generated:"
    echo -e "  ${REPORT_FILE}"
else
    echo -e "${YELLOW}⚠${NC} Report not found (run full workflow to generate)"
fi

# Database stats
DB_FILE="signals/database.json"

if [ -f "$DB_FILE" ]; then
    TOTAL_SIGNALS=$(python3 -c "import json; db=json.load(open('$DB_FILE')); print(db.get('total_signals', 0))")
    LATEST_SCAN=$(python3 -c "import json; db=json.load(open('$DB_FILE')); print(db.get('latest_scan_date', 'Unknown'))")

    echo -e "${GREEN}✓${NC} Database updated:"
    echo -e "  Total signals: $TOTAL_SIGNALS"
    echo -e "  Latest scan: $LATEST_SCAN"
fi

echo ""

# Step 4: Next Steps
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Next Steps${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

echo -e "${YELLOW}Search signals:${NC}"
echo -e "  python3 scripts/search_signals.py \"keyword\""
echo -e "  python3 scripts/search_signals.py --category T --limit 20"
echo ""

echo -e "${YELLOW}View latest report:${NC}"
echo -e "  cat reports/daily/environmental-scan-${DATE}.md"
echo -e "  # or open in your editor/browser"
echo ""

echo -e "${YELLOW}Run full workflow (with analysis):${NC}"
echo -e "  python3 scripts/run_real_workflow.py raw/daily-scan-${DATE}.json"
echo ""

TIME=$(date +%H:%M:%S)
echo -e "${GREEN}[${TIME}] COMPLETE${NC} Daily scan completed successfully"
echo ""
