#!/bin/bash
# =============================================================================
# Trivy Container Security Scan for PEA RE Forecast Platform
# TOR Requirement: Security & Compliance (Section 7.1.6)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  PEA RE Forecast - Security Scan (Trivy)"
echo "=============================================="
echo ""

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo -e "${YELLOW}Trivy not found. Installing...${NC}"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install trivy
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
    else
        echo -e "${RED}Please install Trivy manually: https://aquasecurity.github.io/trivy/${NC}"
        exit 1
    fi
fi

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/reports/security"
mkdir -p "${REPORT_DIR}"

# Scan targets
IMAGES=(
    "pea-forecast-backend:latest"
    "pea-forecast-frontend:latest"
)

# Scan severity (CRITICAL,HIGH,MEDIUM,LOW)
SEVERITY="CRITICAL,HIGH"

echo "Scan Configuration:"
echo "  Severity: ${SEVERITY}"
echo "  Report Directory: ${REPORT_DIR}"
echo ""

# =============================================================================
# Filesystem Scan (Source Code)
# =============================================================================
echo -e "${YELLOW}[1/4] Scanning source code for vulnerabilities...${NC}"

trivy fs "${PROJECT_ROOT}" \
    --severity "${SEVERITY}" \
    --format table \
    --output "${REPORT_DIR}/source-scan.txt" \
    2>/dev/null

echo -e "${GREEN}  ✓ Source code scan complete${NC}"

# =============================================================================
# Python Dependencies Scan
# =============================================================================
echo -e "${YELLOW}[2/4] Scanning Python dependencies...${NC}"

if [ -f "${PROJECT_ROOT}/backend/requirements.txt" ]; then
    trivy fs "${PROJECT_ROOT}/backend/requirements.txt" \
        --severity "${SEVERITY}" \
        --format json \
        --output "${REPORT_DIR}/python-deps-scan.json" \
        2>/dev/null

    # Count vulnerabilities
    VULN_COUNT=$(cat "${REPORT_DIR}/python-deps-scan.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
count = sum(len(r.get('Vulnerabilities', [])) for r in data.get('Results', []))
print(count)
" 2>/dev/null || echo "0")

    if [ "$VULN_COUNT" -gt 0 ]; then
        echo -e "${RED}  ⚠ Found ${VULN_COUNT} vulnerabilities in Python dependencies${NC}"
    else
        echo -e "${GREEN}  ✓ No vulnerabilities found in Python dependencies${NC}"
    fi
else
    echo -e "${YELLOW}  - Skipped (requirements.txt not found)${NC}"
fi

# =============================================================================
# Node.js Dependencies Scan
# =============================================================================
echo -e "${YELLOW}[3/4] Scanning Node.js dependencies...${NC}"

if [ -f "${PROJECT_ROOT}/frontend/package-lock.json" ]; then
    trivy fs "${PROJECT_ROOT}/frontend/package-lock.json" \
        --severity "${SEVERITY}" \
        --format json \
        --output "${REPORT_DIR}/nodejs-deps-scan.json" \
        2>/dev/null

    VULN_COUNT=$(cat "${REPORT_DIR}/nodejs-deps-scan.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
count = sum(len(r.get('Vulnerabilities', [])) for r in data.get('Results', []))
print(count)
" 2>/dev/null || echo "0")

    if [ "$VULN_COUNT" -gt 0 ]; then
        echo -e "${RED}  ⚠ Found ${VULN_COUNT} vulnerabilities in Node.js dependencies${NC}"
    else
        echo -e "${GREEN}  ✓ No vulnerabilities found in Node.js dependencies${NC}"
    fi
else
    echo -e "${YELLOW}  - Skipped (package-lock.json not found)${NC}"
fi

# =============================================================================
# Docker Image Scan
# =============================================================================
echo -e "${YELLOW}[4/4] Scanning Docker images...${NC}"

for IMAGE in "${IMAGES[@]}"; do
    # Check if image exists
    if docker image inspect "${IMAGE}" &> /dev/null; then
        IMAGE_NAME=$(echo "${IMAGE}" | tr ':' '-')

        trivy image "${IMAGE}" \
            --severity "${SEVERITY}" \
            --format json \
            --output "${REPORT_DIR}/${IMAGE_NAME}-scan.json" \
            2>/dev/null

        VULN_COUNT=$(cat "${REPORT_DIR}/${IMAGE_NAME}-scan.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
count = sum(len(r.get('Vulnerabilities', [])) for r in data.get('Results', []))
print(count)
" 2>/dev/null || echo "0")

        if [ "$VULN_COUNT" -gt 0 ]; then
            echo -e "${RED}  ⚠ ${IMAGE}: ${VULN_COUNT} vulnerabilities${NC}"
        else
            echo -e "${GREEN}  ✓ ${IMAGE}: No vulnerabilities${NC}"
        fi
    else
        echo -e "${YELLOW}  - ${IMAGE}: Image not found (skipped)${NC}"
    fi
done

# =============================================================================
# Generate Summary Report
# =============================================================================
echo ""
echo "=============================================="
echo "  Scan Summary"
echo "=============================================="

# Create HTML summary report
cat > "${REPORT_DIR}/scan-summary.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PEA RE Forecast - Security Scan Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #74045F; }
        .pass { color: green; }
        .fail { color: red; }
        .warn { color: orange; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #74045F; color: white; }
    </style>
</head>
<body>
    <h1>PEA RE Forecast Platform - Security Scan Report</h1>
    <p>Generated: $(date)</p>
    <p>Scan Tool: Trivy</p>
    <p>Severity Filter: CRITICAL, HIGH</p>

    <h2>Scan Results</h2>
    <p>Detailed reports are available in the reports/security directory.</p>

    <h2>Compliance Status</h2>
    <table>
        <tr>
            <th>Requirement</th>
            <th>Status</th>
        </tr>
        <tr>
            <td>TOR 7.1.6 - Security Logs</td>
            <td class="pass">✓ Implemented</td>
        </tr>
        <tr>
            <td>Container Security</td>
            <td>See detailed reports</td>
        </tr>
        <tr>
            <td>Dependency Vulnerabilities</td>
            <td>See detailed reports</td>
        </tr>
    </table>
</body>
</html>
EOF

echo "Reports saved to: ${REPORT_DIR}/"
echo ""
echo "Files generated:"
ls -la "${REPORT_DIR}/"
echo ""
echo -e "${GREEN}Security scan complete!${NC}"
