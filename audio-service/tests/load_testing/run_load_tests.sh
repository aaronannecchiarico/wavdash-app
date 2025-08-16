#!/bin/bash

# Load Testing Script for Tempo Processing API
# Runs comprehensive load tests and generates performance reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL=${API_URL:-"http://localhost:8001"}
API_KEY=${API_KEY:-"test-key"}
OUTPUT_DIR="load_test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}Tempo Processing API Load Testing Suite${NC}"
echo -e "${BLUE}=======================================${NC}"
echo "API URL: $API_URL"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to check if API is available
check_api_availability() {
    echo -e "${YELLOW}Checking API availability...${NC}"
    
    if curl -s --fail "$API_URL/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is accessible${NC}"
    else
        echo -e "${RED}✗ API is not accessible at $API_URL${NC}"
        echo "Please ensure the API is running and accessible"
        exit 1
    fi
    
    # Check tempo endpoints specifically
    if curl -s --fail -H "Authorization: Bearer $API_KEY" "$API_URL/tempo/presets" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Tempo endpoints are accessible${NC}"
    else
        echo -e "${RED}✗ Tempo endpoints are not accessible${NC}"
        echo "Please check authentication and endpoint availability"
        exit 1
    fi
    
    echo ""
}

# Function to run rate limit tests
run_rate_limit_tests() {
    echo -e "${YELLOW}Running Rate Limit Tests...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --rate-limit-test \
        2>&1 | tee "$OUTPUT_DIR/rate_limit_test_$TIMESTAMP.log"
    
    echo -e "${GREEN}✓ Rate limit tests completed${NC}"
    echo ""
}

# Function to run light load test
run_light_load_test() {
    echo -e "${YELLOW}Running Light Load Test (2 users, 5 requests each)...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --users 2 \
        --requests 5 \
        --ramp-up 5 \
        --duration 3 \
        --output "$OUTPUT_DIR/light_load_$TIMESTAMP.json" \
        2>&1 | tee "$OUTPUT_DIR/light_load_$TIMESTAMP.log"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Light load test passed${NC}"
    else
        echo -e "${RED}✗ Light load test failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run medium load test
run_medium_load_test() {
    echo -e "${YELLOW}Running Medium Load Test (5 users, 10 requests each)...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --users 5 \
        --requests 10 \
        --ramp-up 10 \
        --duration 5 \
        --output "$OUTPUT_DIR/medium_load_$TIMESTAMP.json" \
        2>&1 | tee "$OUTPUT_DIR/medium_load_$TIMESTAMP.log"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Medium load test passed${NC}"
    else
        echo -e "${RED}✗ Medium load test failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run heavy load test
run_heavy_load_test() {
    echo -e "${YELLOW}Running Heavy Load Test (10 users, 15 requests each)...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --users 10 \
        --requests 15 \
        --ramp-up 20 \
        --duration 10 \
        --output "$OUTPUT_DIR/heavy_load_$TIMESTAMP.json" \
        2>&1 | tee "$OUTPUT_DIR/heavy_load_$TIMESTAMP.log"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Heavy load test passed${NC}"
    else
        echo -e "${YELLOW}⚠ Heavy load test had issues (check logs)${NC}"
        return 1
    fi
    echo ""
}

# Function to run storage-only tests
run_storage_only_test() {
    echo -e "${YELLOW}Running Storage-Only Test (recommended path)...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --users 8 \
        --requests 12 \
        --ramp-up 15 \
        --duration 8 \
        --no-direct \
        --output "$OUTPUT_DIR/storage_only_$TIMESTAMP.json" \
        2>&1 | tee "$OUTPUT_DIR/storage_only_$TIMESTAMP.log"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Storage-only test passed${NC}"
    else
        echo -e "${RED}✗ Storage-only test failed${NC}"
        return 1
    fi
    echo ""
}

# Function to run direct-only tests
run_direct_only_test() {
    echo -e "${YELLOW}Running Direct Upload Test...${NC}"
    
    python3 tempo_load_test.py \
        --url "$API_URL" \
        --api-key "$API_KEY" \
        --users 3 \
        --requests 8 \
        --ramp-up 10 \
        --duration 6 \
        --no-storage \
        --output "$OUTPUT_DIR/direct_only_$TIMESTAMP.json" \
        2>&1 | tee "$OUTPUT_DIR/direct_only_$TIMESTAMP.log"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Direct upload test passed${NC}"
    else
        echo -e "${RED}✗ Direct upload test failed${NC}"
        return 1
    fi
    echo ""
}

# Function to analyze results
analyze_results() {
    echo -e "${YELLOW}Analyzing Test Results...${NC}"
    
    # Count test files
    json_files=$(ls "$OUTPUT_DIR"/*.json 2>/dev/null | wc -l)
    log_files=$(ls "$OUTPUT_DIR"/*.log 2>/dev/null | wc -l)
    
    echo "Generated $json_files JSON result files and $log_files log files"
    
    # Create summary report
    cat > "$OUTPUT_DIR/test_summary_$TIMESTAMP.md" << EOF
# Load Test Summary Report

**Test Date:** $(date)
**API URL:** $API_URL
**Test Suite:** Tempo Processing API Load Tests

## Test Results

### Files Generated
- JSON Results: $json_files files
- Log Files: $log_files files

### Test Categories Run
EOF

    # Add test results to summary
    if [ -f "$OUTPUT_DIR/light_load_$TIMESTAMP.json" ]; then
        echo "- ✅ Light Load Test (2 users, 5 requests)" >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    fi
    
    if [ -f "$OUTPUT_DIR/medium_load_$TIMESTAMP.json" ]; then
        echo "- ✅ Medium Load Test (5 users, 10 requests)" >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    fi
    
    if [ -f "$OUTPUT_DIR/heavy_load_$TIMESTAMP.json" ]; then
        echo "- ✅ Heavy Load Test (10 users, 15 requests)" >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    fi
    
    if [ -f "$OUTPUT_DIR/storage_only_$TIMESTAMP.json" ]; then
        echo "- ✅ Storage-Only Test (8 users, 12 requests)" >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    fi
    
    if [ -f "$OUTPUT_DIR/direct_only_$TIMESTAMP.json" ]; then
        echo "- ✅ Direct Upload Test (3 users, 8 requests)" >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    fi

    cat >> "$OUTPUT_DIR/test_summary_$TIMESTAMP.md" << EOF

## Key Metrics to Review

1. **Success Rate**: Should be >95% for production readiness
2. **Response Times**: 
   - Average: <30 seconds for good UX
   - 95th percentile: <60 seconds
3. **Rate Limiting**: Should kick in appropriately without false positives
4. **Cache Hit Rate**: Should be >20% for optimized performance

## Next Steps

1. Review individual test logs for any errors
2. Check API server logs for resource usage patterns
3. Validate rate limiting behavior matches expectations
4. Consider adjusting rate limits based on results

## Files Location

All test results are stored in: $OUTPUT_DIR/
EOF

    echo -e "${GREEN}✓ Test analysis completed${NC}"
    echo "Summary report: $OUTPUT_DIR/test_summary_$TIMESTAMP.md"
    echo ""
}

# Function to cleanup old test results
cleanup_old_results() {
    echo -e "${YELLOW}Cleaning up old test results (keeping last 10)...${NC}"
    
    # Keep only the 10 most recent result files
    ls -t "$OUTPUT_DIR"/*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    ls -t "$OUTPUT_DIR"/*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    ls -t "$OUTPUT_DIR"/*.md 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
    echo ""
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --light         Run only light load test"
    echo "  --medium        Run only medium load test"
    echo "  --heavy         Run only heavy load test"
    echo "  --storage-only  Run only storage-based tests"
    echo "  --direct-only   Run only direct upload tests"
    echo "  --rate-limits   Run only rate limit tests"
    echo "  --all           Run all tests (default)"
    echo "  --skip-cleanup  Skip cleanup of old results"
    echo "  --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  API_URL         API base URL (default: http://localhost:8001)"
    echo "  API_KEY         API authentication key (default: test-key)"
    echo ""
    echo "Examples:"
    echo "  $0 --light                    # Run only light load test"
    echo "  $0 --storage-only             # Test storage endpoints only"
    echo "  API_URL=https://prod.api.com $0 --all  # Test production API"
}

# Main execution
main() {
    local run_light=false
    local run_medium=false
    local run_heavy=false
    local run_storage_only=false
    local run_direct_only=false
    local run_rate_limits=false
    local run_all=true
    local skip_cleanup=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --light)
                run_light=true
                run_all=false
                shift
                ;;
            --medium)
                run_medium=true
                run_all=false
                shift
                ;;
            --heavy)
                run_heavy=true
                run_all=false
                shift
                ;;
            --storage-only)
                run_storage_only=true
                run_all=false
                shift
                ;;
            --direct-only)
                run_direct_only=true
                run_all=false
                shift
                ;;
            --rate-limits)
                run_rate_limits=true
                run_all=false
                shift
                ;;
            --all)
                run_all=true
                shift
                ;;
            --skip-cleanup)
                skip_cleanup=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_api_availability
    
    # Cleanup old results unless skipped
    if [ "$skip_cleanup" = false ]; then
        cleanup_old_results
    fi
    
    # Track overall success
    overall_success=true
    
    # Run selected tests
    if [ "$run_all" = true ]; then
        echo -e "${BLUE}Running Full Test Suite...${NC}"
        echo ""
        
        run_rate_limit_tests || overall_success=false
        run_light_load_test || overall_success=false
        run_medium_load_test || overall_success=false
        run_storage_only_test || overall_success=false
        run_direct_only_test || overall_success=false
        run_heavy_load_test || overall_success=false
        
    else
        # Run individual tests as requested
        [ "$run_rate_limits" = true ] && (run_rate_limit_tests || overall_success=false)
        [ "$run_light" = true ] && (run_light_load_test || overall_success=false)
        [ "$run_medium" = true ] && (run_medium_load_test || overall_success=false)
        [ "$run_heavy" = true ] && (run_heavy_load_test || overall_success=false)
        [ "$run_storage_only" = true ] && (run_storage_only_test || overall_success=false)
        [ "$run_direct_only" = true ] && (run_direct_only_test || overall_success=false)
    fi
    
    # Analyze results
    analyze_results
    
    # Final summary
    echo -e "${BLUE}Load Testing Complete${NC}"
    echo -e "${BLUE}====================${NC}"
    
    if [ "$overall_success" = true ]; then
        echo -e "${GREEN}✓ All tests completed successfully${NC}"
        echo -e "${GREEN}API appears ready for production load${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Some tests had issues - review logs for details${NC}"
        echo -e "${YELLOW}Consider optimizing performance before production deployment${NC}"
        exit 1
    fi
}

# Check if script is being run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi