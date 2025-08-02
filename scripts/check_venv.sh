#!/bin/bash
# Check if virtual environment is active
# Usage: source scripts/check_venv.sh

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_venv_status() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${GREEN}✓ Virtual environment is active${NC}"
        echo -e "  Path: ${VIRTUAL_ENV}"
        echo -e "  Python: $(which python)"
        return 0
    else
        echo -e "${RED}✗ Virtual environment is not active${NC}"
        
        if [ -d "venv" ]; then
            echo -e "${YELLOW}  Virtual environment exists but not activated${NC}"
            echo -e "  Run: ${GREEN}source venv/bin/activate${NC}"
        else
            echo -e "${YELLOW}  Virtual environment not found${NC}"
            echo -e "  Run: ${GREEN}make setup${NC}"
        fi
        return 1
    fi
}

# Auto-activate if not active and venv exists
auto_activate_venv() {
    if [ -z "$VIRTUAL_ENV" ] && [ -d "venv" ]; then
        echo -e "${YELLOW}Auto-activating virtual environment...${NC}"
        source venv/bin/activate
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Virtual environment activated${NC}"
            return 0
        else
            echo -e "${RED}✗ Failed to activate virtual environment${NC}"
            return 1
        fi
    fi
}

# Main function
main() {
    case "${1:-status}" in
        "status")
            check_venv_status
            ;;
        "auto")
            auto_activate_venv || check_venv_status
            ;;
        "activate")
            if [ -d "venv" ]; then
                echo -e "${GREEN}Activating virtual environment...${NC}"
                source venv/bin/activate
            else
                echo -e "${RED}Virtual environment not found. Run 'make setup' first.${NC}"
                return 1
            fi
            ;;
        *)
            echo "Usage: source scripts/check_venv.sh [status|auto|activate]"
            echo "  status   - Check current status (default)"
            echo "  auto     - Auto-activate if venv exists"
            echo "  activate - Activate virtual environment"
            ;;
    esac
}

# Only run if script is sourced directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "This script should be sourced, not executed directly."
    echo "Usage: source scripts/check_venv.sh"
    exit 1
fi

main "$@"