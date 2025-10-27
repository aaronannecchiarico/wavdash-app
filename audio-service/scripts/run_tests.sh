#!/bin/bash
#
# Test runner script for Audio Processing Microservice
# Ensures tests are run in the virtual environment
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Audio Processing Microservice Test Runner${NC}"
echo "==========================================="

# Check if virtual environment exists
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_DIR${NC}"
    echo "Please run: python install.py"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found in virtual environment${NC}"
    echo "Installing pytest..."
    pip install pytest pytest-asyncio pytest-mock
fi

# Function to run tests with error handling
run_tests() {
    local test_type="$1"
    local test_path="$2"
    local description="$3"
    
    echo ""
    echo -e "${BLUE}🔍 Running $description...${NC}"
    echo "Path: $test_path"
    echo "----------------------------------------"
    
    if pytest "$test_path" -v --tb=short; then
        echo -e "${GREEN}✅ $description passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Initialize test results
unit_tests_passed=false
feature_tests_passed=false
all_tests_passed=false

# Parse command line arguments
case "${1:-all}" in
    "unit")
        echo -e "${YELLOW}Running unit tests only...${NC}"
        if run_tests "unit" "tests/unit" "Unit Tests"; then
            unit_tests_passed=true
        fi
        ;;
    "feature")
        echo -e "${YELLOW}Running feature tests only...${NC}"
        if run_tests "feature" "tests/feature" "Feature Tests"; then
            feature_tests_passed=true
        fi
        ;;
    "all"|*)
        echo -e "${YELLOW}Running all tests...${NC}"
        
        # Run unit tests
        if run_tests "unit" "tests/unit" "Unit Tests"; then
            unit_tests_passed=true
        fi
        
        # Run feature tests
        if run_tests "feature" "tests/feature" "Feature Tests"; then
            feature_tests_passed=true
        fi
        
        # Overall results
        if $unit_tests_passed && $feature_tests_passed; then
            all_tests_passed=true
        fi
        ;;
esac

# Generate test report
echo ""
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "======================="

if [ "${1:-all}" = "all" ]; then
    echo -e "Unit Tests:    $([ "$unit_tests_passed" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo -e "Feature Tests: $([ "$feature_tests_passed" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo ""
    
    if [ "$all_tests_passed" = true ]; then
        echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
        echo ""
        echo -e "${GREEN}✅ Ready for production deployment${NC}"
        exit 0
    else
        echo -e "${RED}💥 Some tests failed${NC}"
        echo ""
        echo -e "${YELLOW}📋 Troubleshooting:${NC}"
        echo "• Check error messages above"
        echo "• Ensure Redis is running for feature tests"
        echo "• Verify all dependencies are installed"
        echo "• Check log files in logs/ directory"
        exit 1
    fi
elif [ "${1}" = "unit" ]; then
    if [ "$unit_tests_passed" = true ]; then
        echo -e "${GREEN}🎉 Unit tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}💥 Unit tests failed${NC}"
        exit 1
    fi
elif [ "${1}" = "feature" ]; then
    if [ "$feature_tests_passed" = true ]; then
        echo -e "${GREEN}🎉 Feature tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}💥 Feature tests failed${NC}"
        echo ""
        echo -e "${YELLOW}📋 Feature test requirements:${NC}"
        echo "• Redis server running"
        echo "• Celery worker running"
        echo "• All audio dependencies installed"
        exit 1
    fi
fi