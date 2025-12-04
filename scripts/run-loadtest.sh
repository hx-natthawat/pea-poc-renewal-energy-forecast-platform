#!/bin/bash
# PEA RE Forecast Platform - Load Test Runner
# TOR Requirement: Support 2,000+ RE plants and 300,000+ users

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="${PROJECT_ROOT}/reports/loadtest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default configuration
HOST="${HOST:-http://localhost:8000}"
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
RUN_TIME="${RUN_TIME:-2m}"
WORKERS="${WORKERS:-4}"

# TOR compliance targets
TARGET_LATENCY_P95=500  # ms
TARGET_ERROR_RATE=1     # %
TARGET_RPS=100          # requests per second

echo -e "${GREEN}=== PEA RE Forecast Platform - Load Test ===${NC}"
echo "TOR Requirement: Support 2,000+ RE plants and 300,000+ users"
echo ""

show_help() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  quick       Quick smoke test (100 users, 1 minute)"
    echo "  standard    Standard load test (500 users, 5 minutes)"
    echo "  stress      Stress test (1000 users, 10 minutes)"
    echo "  scale       Scale test for TOR validation (max capacity)"
    echo "  distributed Run distributed load test with Docker"
    echo "  report      Generate HTML report from last run"
    echo ""
    echo "Options:"
    echo "  -h, --host       Target host (default: http://localhost:8000)"
    echo "  -u, --users      Number of concurrent users (default: 100)"
    echo "  -r, --rate       Spawn rate per second (default: 10)"
    echo "  -t, --time       Test duration (default: 2m)"
    echo "  -w, --workers    Number of worker processes (default: 4)"
    echo ""
    echo "Environment variables:"
    echo "  HOST         Target host URL"
    echo "  USERS        Number of concurrent users"
    echo "  SPAWN_RATE   Users spawned per second"
    echo "  RUN_TIME     Test duration (e.g., 5m, 1h)"
    echo ""
}

check_locust() {
    if command -v locust &> /dev/null; then
        echo -e "${GREEN}Locust found: $(locust --version)${NC}"
        return 0
    else
        echo -e "${YELLOW}Locust not installed. Install with: pip install locust${NC}"
        return 1
    fi
}

check_api_health() {
    echo "Checking API health at ${HOST}..."
    if curl -sf "${HOST}/api/v1/health" > /dev/null 2>&1; then
        echo -e "${GREEN}API is healthy${NC}"
        return 0
    else
        echo -e "${RED}API is not responding at ${HOST}${NC}"
        echo "Please start the backend server first."
        return 1
    fi
}

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        quick|standard|stress|scale|distributed|report)
            COMMAND="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

run_locust() {
    local users="$1"
    local rate="$2"
    local time="$3"
    local name="$4"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local csv_prefix="${REPORTS_DIR}/${name}_${timestamp}"

    echo -e "\n${BLUE}Running ${name} load test...${NC}"
    echo "  Users: ${users}"
    echo "  Spawn Rate: ${rate}/s"
    echo "  Duration: ${time}"
    echo "  Target: ${HOST}"
    echo ""

    cd "${PROJECT_ROOT}/tests/load"

    locust -f locustfile.py \
        --host="${HOST}" \
        --headless \
        --users="${users}" \
        --spawn-rate="${rate}" \
        --run-time="${time}" \
        --csv="${csv_prefix}" \
        --html="${csv_prefix}_report.html" \
        --only-summary \
        2>&1 | tee "${csv_prefix}.log"

    echo -e "\n${GREEN}Reports saved to:${NC}"
    echo "  ${csv_prefix}_stats.csv"
    echo "  ${csv_prefix}_stats_history.csv"
    echo "  ${csv_prefix}_report.html"

    # Check TOR compliance
    check_tor_compliance "${csv_prefix}_stats.csv"
}

check_tor_compliance() {
    local stats_file="$1"

    if [ ! -f "$stats_file" ]; then
        echo -e "${YELLOW}Stats file not found, skipping compliance check${NC}"
        return
    fi

    echo -e "\n${BLUE}=== TOR Compliance Check ===${NC}"

    # Parse the stats file (CSV format)
    local p95=$(tail -1 "$stats_file" | cut -d',' -f8)
    local error_pct=$(tail -1 "$stats_file" | cut -d',' -f4)
    local rps=$(tail -1 "$stats_file" | cut -d',' -f10)

    # Check P95 latency
    if (( $(echo "$p95 < $TARGET_LATENCY_P95" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "  P95 Latency: ${GREEN}PASS${NC} (${p95}ms < ${TARGET_LATENCY_P95}ms)"
    else
        echo -e "  P95 Latency: ${RED}FAIL${NC} (${p95}ms > ${TARGET_LATENCY_P95}ms)"
    fi

    # Check error rate
    if (( $(echo "$error_pct < $TARGET_ERROR_RATE" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "  Error Rate:  ${GREEN}PASS${NC} (${error_pct}% < ${TARGET_ERROR_RATE}%)"
    else
        echo -e "  Error Rate:  ${RED}FAIL${NC} (${error_pct}% > ${TARGET_ERROR_RATE}%)"
    fi

    echo ""
}

run_distributed() {
    echo -e "${BLUE}Starting distributed load test with Docker...${NC}"

    cd "${PROJECT_ROOT}/docker"

    # Start Locust cluster
    docker-compose -f docker-compose.loadtest.yml up -d --scale locust-worker=${WORKERS}

    echo -e "\n${GREEN}Locust Web UI available at: http://localhost:8089${NC}"
    echo "Configure and start the test from the web interface."
    echo ""
    echo "To stop: docker-compose -f docker-compose.loadtest.yml down"
}

# Main execution
case "${COMMAND:-quick}" in
    quick)
        check_locust || exit 1
        check_api_health || exit 1
        run_locust 100 10 "1m" "quick"
        ;;
    standard)
        check_locust || exit 1
        check_api_health || exit 1
        run_locust 500 50 "5m" "standard"
        ;;
    stress)
        check_locust || exit 1
        check_api_health || exit 1
        run_locust 1000 100 "10m" "stress"
        ;;
    scale)
        check_locust || exit 1
        check_api_health || exit 1
        echo -e "${YELLOW}Running TOR scale validation test...${NC}"
        echo "This simulates 300K user load pattern over 15 minutes"
        run_locust 2000 200 "15m" "scale"
        ;;
    distributed)
        run_distributed
        ;;
    report)
        echo "Generating report from latest test..."
        latest=$(ls -t "${REPORTS_DIR}"/*_stats.csv 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            echo "Latest: ${latest}"
            check_tor_compliance "$latest"
        else
            echo "No test results found in ${REPORTS_DIR}"
        fi
        ;;
    *)
        check_locust || exit 1
        check_api_health || exit 1
        run_locust "${USERS}" "${SPAWN_RATE}" "${RUN_TIME}" "custom"
        ;;
esac

echo -e "\n${GREEN}Load test completed.${NC}"
