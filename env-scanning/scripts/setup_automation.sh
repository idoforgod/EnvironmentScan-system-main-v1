#!/bin/bash
#
# Setup Automation for Daily Scan
# Enable or disable automatic daily scans via cron
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_SCRIPT="$SCRIPT_DIR/run_daily_scan.sh"

# Make script executable
chmod +x "$DAILY_SCRIPT"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}   Environmental Scanning - Automation Setup${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Function to check if cron job exists
check_cron() {
    crontab -l 2>/dev/null | grep -q "run_daily_scan.sh"
    return $?
}

# Function to add cron job
enable_automation() {
    echo -e "${YELLOW}Setting up automatic daily scan...${NC}"
    echo ""

    # Ask for preferred time
    echo "At what time should the scan run daily?"
    echo -e "  ${GREEN}1)${NC} 9:00 AM  (recommended)"
    echo -e "  ${GREEN}2)${NC} 12:00 PM (noon)"
    echo -e "  ${GREEN}3)${NC} 6:00 PM  (evening)"
    echo -e "  ${GREEN}4)${NC} Custom time"
    echo ""
    read -p "Enter choice [1-4]: " choice

    case $choice in
        1)
            HOUR=9
            MINUTE=0
            TIME_DESC="9:00 AM"
            ;;
        2)
            HOUR=12
            MINUTE=0
            TIME_DESC="12:00 PM"
            ;;
        3)
            HOUR=18
            MINUTE=0
            TIME_DESC="6:00 PM"
            ;;
        4)
            read -p "Enter hour (0-23): " HOUR
            read -p "Enter minute (0-59): " MINUTE
            TIME_DESC="${HOUR}:${MINUTE}"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    # Create cron entry
    CRON_ENTRY="$MINUTE $HOUR * * * cd $PROJECT_DIR && bash $DAILY_SCRIPT >> logs/cron.log 2>&1"

    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "run_daily_scan.sh"; echo "$CRON_ENTRY") | crontab -

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Automation enabled!${NC}"
        echo ""
        echo -e "Daily scan will run automatically at ${GREEN}${TIME_DESC}${NC} every day"
        echo ""
        echo -e "${YELLOW}Important notes:${NC}"
        echo -e "  • Your computer must be ON at the scheduled time"
        echo -e "  • Logs will be saved to: logs/cron.log"
        echo -e "  • To disable automation, run this script again"
        echo ""
        echo -e "${BLUE}Manual run is still available:${NC}"
        echo -e "  bash scripts/run_daily_scan.sh"
    else
        echo -e "${RED}✗ Failed to enable automation${NC}"
        exit 1
    fi
}

# Function to disable cron job
disable_automation() {
    echo -e "${YELLOW}Disabling automatic daily scan...${NC}"
    echo ""

    # Remove from crontab
    crontab -l 2>/dev/null | grep -v "run_daily_scan.sh" | crontab -

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Automation disabled${NC}"
        echo ""
        echo -e "Daily scan will no longer run automatically"
        echo ""
        echo -e "${BLUE}You can still run manually:${NC}"
        echo -e "  bash scripts/run_daily_scan.sh"
    else
        echo -e "${RED}✗ Failed to disable automation${NC}"
        exit 1
    fi
}

# Check current status
if check_cron; then
    echo -e "${GREEN}Status:${NC} Automation is currently ${GREEN}ENABLED${NC}"
    echo ""

    # Show current schedule
    CURRENT_CRON=$(crontab -l 2>/dev/null | grep "run_daily_scan.sh")
    echo -e "Current schedule:"
    echo -e "  ${CURRENT_CRON}"
    echo ""

    # Ask what to do
    echo "What would you like to do?"
    echo -e "  ${GREEN}1)${NC} Disable automation"
    echo -e "  ${GREEN}2)${NC} Change schedule (disable & re-enable)"
    echo -e "  ${GREEN}3)${NC} Keep as is (exit)"
    echo ""
    read -p "Enter choice [1-3]: " action

    case $action in
        1)
            disable_automation
            ;;
        2)
            disable_automation
            echo ""
            enable_automation
            ;;
        3)
            echo -e "${BLUE}No changes made${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
else
    echo -e "${YELLOW}Status:${NC} Automation is currently ${YELLOW}DISABLED${NC}"
    echo ""
    echo "Would you like to enable automatic daily scans?"
    echo -e "  ${GREEN}1)${NC} Yes, enable automation"
    echo -e "  ${GREEN}2)${NC} No, I'll run manually"
    echo ""
    read -p "Enter choice [1-2]: " action

    case $action in
        1)
            enable_automation
            ;;
        2)
            echo ""
            echo -e "${BLUE}Automation not enabled${NC}"
            echo ""
            echo -e "You can run scans manually:"
            echo -e "  ${GREEN}bash scripts/run_daily_scan.sh${NC}"
            echo ""
            echo -e "To enable automation later, run:"
            echo -e "  ${GREEN}bash scripts/setup_automation.sh${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo ""
