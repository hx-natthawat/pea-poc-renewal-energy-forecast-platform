#!/bin/bash
# Security Scanning Script for PEA RE Forecast Platform
# Runs Trivy, Bandit, and npm audit for local security checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="${PROJECT_ROOT}/reports/security"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== PEA RE Forecast Platform Security Scan ===${NC}"
echo "Report directory: ${REPORTS_DIR}"

# Create reports directory
mkdir -p "${REPORTS_DIR}"

# Check if Trivy is installed
check_trivy() {
    if command -v trivy &> /dev/null; then
        echo -e "${GREEN}Trivy found: $(trivy --version | head -1)${NC}"
        return 0
    else
        echo -e "${YELLOW}Trivy not installed. Install with: brew install trivy${NC}"
        return 1
    fi
}

# Check if Bandit is installed
check_bandit() {
    if command -v bandit &> /dev/null; then
        echo -e "${GREEN}Bandit found: $(bandit --version 2>&1 | head -1)${NC}"
        return 0
    else
        echo -e "${YELLOW}Bandit not installed. Install with: pip install bandit${NC}"
        return 1
    fi
}

# Run Trivy filesystem scan
run_trivy_fs() {
    echo -e "\n${GREEN}=== Running Trivy Filesystem Scan ===${NC}"

    if check_trivy; then
        echo "Scanning backend..."
        trivy fs "${PROJECT_ROOT}/backend" \
            --severity HIGH,CRITICAL \
            --format table \
            --output "${REPORTS_DIR}/trivy-backend.txt" 2>&1 || true

        echo "Scanning frontend..."
        trivy fs "${PROJECT_ROOT}/frontend" \
            --severity HIGH,CRITICAL \
            --format table \
            --output "${REPORTS_DIR}/trivy-frontend.txt" 2>&1 || true

        # JSON reports for CI
        trivy fs "${PROJECT_ROOT}/backend" \
            --severity HIGH,CRITICAL \
            --format json \
            --output "${REPORTS_DIR}/trivy-backend.json" 2>&1 || true

        trivy fs "${PROJECT_ROOT}/frontend" \
            --severity HIGH,CRITICAL \
            --format json \
            --output "${REPORTS_DIR}/trivy-frontend.json" 2>&1 || true

        echo -e "${GREEN}Trivy reports saved to ${REPORTS_DIR}${NC}"
    fi
}

# Run Trivy secret scan
run_trivy_secrets() {
    echo -e "\n${GREEN}=== Running Trivy Secret Scan ===${NC}"

    if check_trivy; then
        trivy fs "${PROJECT_ROOT}" \
            --security-checks secret \
            --format table \
            --output "${REPORTS_DIR}/trivy-secrets.txt" 2>&1 || true

        trivy fs "${PROJECT_ROOT}" \
            --security-checks secret \
            --format json \
            --output "${REPORTS_DIR}/trivy-secrets.json" 2>&1 || true

        echo -e "${GREEN}Secret scan completed${NC}"
    fi
}

# Run Bandit for Python security
run_bandit() {
    echo -e "\n${GREEN}=== Running Bandit (Python Security) ===${NC}"

    if check_bandit; then
        cd "${PROJECT_ROOT}/backend"
        bandit -r app \
            -f txt \
            -o "${REPORTS_DIR}/bandit-report.txt" 2>&1 || true

        bandit -r app \
            -f json \
            -o "${REPORTS_DIR}/bandit-report.json" 2>&1 || true

        # Show summary
        echo "Bandit Summary:"
        bandit -r app -f txt 2>&1 | tail -20 || true

        echo -e "${GREEN}Bandit report saved${NC}"
    fi
}

# Run npm audit for frontend
run_npm_audit() {
    echo -e "\n${GREEN}=== Running npm audit (Frontend) ===${NC}"

    cd "${PROJECT_ROOT}/frontend"

    if [ -f "pnpm-lock.yaml" ]; then
        pnpm audit --json > "${REPORTS_DIR}/npm-audit.json" 2>&1 || true
        pnpm audit > "${REPORTS_DIR}/npm-audit.txt" 2>&1 || true
        echo -e "${GREEN}npm audit report saved${NC}"
    else
        echo -e "${YELLOW}No pnpm-lock.yaml found${NC}"
    fi
}

# Run pip-audit for backend
run_pip_audit() {
    echo -e "\n${GREEN}=== Running pip-audit (Backend) ===${NC}"

    if command -v pip-audit &> /dev/null; then
        cd "${PROJECT_ROOT}/backend"
        pip-audit -r requirements.txt --format json > "${REPORTS_DIR}/pip-audit.json" 2>&1 || true
        pip-audit -r requirements.txt > "${REPORTS_DIR}/pip-audit.txt" 2>&1 || true
        echo -e "${GREEN}pip-audit report saved${NC}"
    else
        echo -e "${YELLOW}pip-audit not installed. Install with: pip install pip-audit${NC}"
    fi
}

# Generate summary report
generate_summary() {
    echo -e "\n${GREEN}=== Security Scan Summary ===${NC}"

    SUMMARY_FILE="${REPORTS_DIR}/summary.txt"

    {
        echo "PEA RE Forecast Platform - Security Scan Summary"
        echo "================================================"
        echo "Date: $(date)"
        echo ""

        echo "=== Trivy Backend ==="
        if [ -f "${REPORTS_DIR}/trivy-backend.json" ]; then
            jq -r '.Results[]? | "- \(.Target): \(.Vulnerabilities // [] | length) vulnerabilities"' \
                "${REPORTS_DIR}/trivy-backend.json" 2>/dev/null || echo "No vulnerabilities found or error parsing"
        fi
        echo ""

        echo "=== Trivy Frontend ==="
        if [ -f "${REPORTS_DIR}/trivy-frontend.json" ]; then
            jq -r '.Results[]? | "- \(.Target): \(.Vulnerabilities // [] | length) vulnerabilities"' \
                "${REPORTS_DIR}/trivy-frontend.json" 2>/dev/null || echo "No vulnerabilities found or error parsing"
        fi
        echo ""

        echo "=== Bandit (Python) ==="
        if [ -f "${REPORTS_DIR}/bandit-report.json" ]; then
            jq -r '"- Issues found: \(.metrics._totals.SEVERITY.HIGH // 0) HIGH, \(.metrics._totals.SEVERITY.MEDIUM // 0) MEDIUM"' \
                "${REPORTS_DIR}/bandit-report.json" 2>/dev/null || echo "Error parsing report"
        fi
        echo ""

        echo "=== Secret Scan ==="
        if [ -f "${REPORTS_DIR}/trivy-secrets.json" ]; then
            SECRETS_COUNT=$(jq '[.Results[]?.Secrets // [] | length] | add // 0' "${REPORTS_DIR}/trivy-secrets.json" 2>/dev/null || echo "0")
            echo "- Secrets found: ${SECRETS_COUNT}"
        fi

    } > "${SUMMARY_FILE}"

    cat "${SUMMARY_FILE}"
}

# Main execution
main() {
    case "${1:-all}" in
        trivy)
            run_trivy_fs
            ;;
        secrets)
            run_trivy_secrets
            ;;
        bandit)
            run_bandit
            ;;
        npm)
            run_npm_audit
            ;;
        pip)
            run_pip_audit
            ;;
        all)
            run_trivy_fs
            run_trivy_secrets
            run_bandit
            run_npm_audit
            run_pip_audit
            generate_summary
            ;;
        *)
            echo "Usage: $0 {all|trivy|secrets|bandit|npm|pip}"
            exit 1
            ;;
    esac

    echo -e "\n${GREEN}Security scan completed. Reports saved to: ${REPORTS_DIR}${NC}"
}

main "$@"
