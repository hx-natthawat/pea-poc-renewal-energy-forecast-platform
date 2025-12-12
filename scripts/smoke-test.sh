#!/bin/bash
# ==============================================================================
# PEA RE Forecast Platform - Smoke Test Script
# ==============================================================================
# Run this script after deployment to validate the system is working correctly.
# Usage: ./scripts/smoke-test.sh [BASE_URL]
# ==============================================================================

set -e

# Configuration
BASE_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:3000}"
TIMEOUT=10
PASSED=0
FAILED=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"
    local data="$5"

    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT \
            -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")
    fi

    if [ "$response" = "$expected_status" ]; then
        log_pass "$name (HTTP $response)"
        return 0
    elif [ "$response" = "000" ]; then
        log_fail "$name - Connection refused or timeout"
        return 1
    else
        log_fail "$name - Expected $expected_status, got $response"
        return 1
    fi
}

check_json_response() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    local expected="$4"

    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null)
    if [ -z "$response" ]; then
        log_fail "$name - No response"
        return 1
    fi

    actual=$(echo "$response" | jq -r "$jq_filter" 2>/dev/null || echo "parse_error")
    if [ "$actual" = "$expected" ]; then
        log_pass "$name ($jq_filter = $expected)"
        return 0
    else
        log_fail "$name - Expected '$expected', got '$actual'"
        return 1
    fi
}

# ==============================================================================
# Main Tests
# ==============================================================================

echo ""
echo "=============================================================="
echo "  PEA RE Forecast Platform - Smoke Tests"
echo "=============================================================="
echo "  Backend URL:  $BASE_URL"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Timeout:      ${TIMEOUT}s"
echo "=============================================================="
echo ""

# ------------------------------------------------------------------------------
# 1. Health Checks
# ------------------------------------------------------------------------------
log_info "Testing health endpoints..."

check_endpoint "Backend Health" "$BASE_URL/api/v1/health"
check_json_response "Health Status" "$BASE_URL/api/v1/health" ".status" "healthy"
check_json_response "Database Status" "$BASE_URL/api/v1/health" ".database" "connected"
check_json_response "Redis Status" "$BASE_URL/api/v1/health" ".redis" "connected"

echo ""

# ------------------------------------------------------------------------------
# 2. API Documentation
# ------------------------------------------------------------------------------
log_info "Testing API documentation..."

check_endpoint "OpenAPI Schema" "$BASE_URL/openapi.json"
check_endpoint "Swagger UI" "$BASE_URL/docs"
check_endpoint "ReDoc" "$BASE_URL/redoc"

echo ""

# ------------------------------------------------------------------------------
# 3. Public Endpoints (No Auth Required)
# ------------------------------------------------------------------------------
log_info "Testing public endpoints..."

check_endpoint "Regions List" "$BASE_URL/api/v1/regions/"
check_endpoint "Public Solar Forecast" "$BASE_URL/api/v1/solar-forecast/predict"
check_endpoint "Public Voltage Forecast" "$BASE_URL/api/v1/voltage-forecast/predict"

echo ""

# ------------------------------------------------------------------------------
# 4. ML Model Inference
# ------------------------------------------------------------------------------
log_info "Testing ML model inference..."

# Solar prediction test
SOLAR_DATA='{
    "timestamp": "2025-01-15T12:00:00+07:00",
    "station_id": "POC_STATION_1",
    "horizon_minutes": 60,
    "features": {
        "pyrano1": 850.0,
        "pyrano2": 840.0,
        "pvtemp1": 45.0,
        "pvtemp2": 44.0,
        "ambtemp": 32.0,
        "windspeed": 2.5
    }
}'

solar_response=$(curl -s --max-time $TIMEOUT -X POST \
    -H "Content-Type: application/json" \
    -d "$SOLAR_DATA" \
    "$BASE_URL/api/v1/solar-forecast/predict" 2>/dev/null)

if echo "$solar_response" | jq -e '.power_kw' > /dev/null 2>&1; then
    power_kw=$(echo "$solar_response" | jq -r '.power_kw')
    log_pass "Solar Prediction (power_kw: $power_kw)"
else
    log_warn "Solar Prediction - Model may not be loaded (fallback mode OK)"
fi

echo ""

# ------------------------------------------------------------------------------
# 5. Frontend
# ------------------------------------------------------------------------------
log_info "Testing frontend..."

frontend_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$frontend_status" = "200" ]; then
    log_pass "Frontend Homepage (HTTP $frontend_status)"
elif [ "$frontend_status" = "000" ]; then
    log_warn "Frontend not accessible (may not be deployed)"
else
    log_fail "Frontend - Unexpected status $frontend_status"
fi

echo ""

# ------------------------------------------------------------------------------
# 6. Database Connectivity (via health)
# ------------------------------------------------------------------------------
log_info "Validating database connectivity..."

db_tables=$(curl -s --max-time $TIMEOUT "$BASE_URL/api/v1/health" 2>/dev/null | jq -r '.database // "unknown"')
if [ "$db_tables" = "connected" ]; then
    log_pass "Database connectivity verified"
else
    log_fail "Database connectivity issue: $db_tables"
fi

echo ""

# ------------------------------------------------------------------------------
# 7. Performance Check
# ------------------------------------------------------------------------------
log_info "Testing response times..."

start_time=$(date +%s%3N)
curl -s -o /dev/null --max-time $TIMEOUT "$BASE_URL/api/v1/health" 2>/dev/null
end_time=$(date +%s%3N)
response_time=$((end_time - start_time))

if [ $response_time -lt 100 ]; then
    log_pass "Health endpoint response time: ${response_time}ms (excellent)"
elif [ $response_time -lt 500 ]; then
    log_pass "Health endpoint response time: ${response_time}ms (good)"
else
    log_warn "Health endpoint response time: ${response_time}ms (slow - target <500ms)"
fi

echo ""

# ==============================================================================
# Summary
# ==============================================================================
echo "=============================================================="
echo "  Smoke Test Summary"
echo "=============================================================="
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo "=============================================================="

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All critical tests passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Review warnings above for potential issues.${NC}"
    fi
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please investigate before proceeding.${NC}"
    exit 1
fi
