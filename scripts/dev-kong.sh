#!/bin/bash
# =============================================================================
# PEA RE Forecast Platform - Kong Development Mode
# Start all services with Kong API Gateway for unified access
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PEA RE Forecast Platform - Kong Development Mode       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Kong is running
check_kong() {
    if curl -s http://localhost:8888/backend/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Kong Gateway is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Kong Gateway not detected on port 8888${NC}"
        return 1
    fi
}

# Check if Backend is running
check_backend() {
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is running on port 8000${NC}"
        return 0
    else
        echo -e "${RED}✗ Backend not running on port 8000${NC}"
        return 1
    fi
}

# Check if Frontend is running
check_frontend() {
    if curl -s http://localhost:3000/console > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is running on port 3000${NC}"
        return 0
    else
        echo -e "${RED}✗ Frontend not running on port 3000${NC}"
        return 1
    fi
}

# Start Kong
start_kong() {
    echo -e "${BLUE}Starting Kong Gateway...${NC}"
    cd "$PROJECT_ROOT/docker"
    docker-compose -f docker-compose.kong.yml up -d kong
    sleep 3
}

# Start Backend
start_backend() {
    echo -e "${BLUE}Starting Backend...${NC}"
    cd "$PROJECT_ROOT/backend"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/pea_forecast" \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    sleep 3
}

# Start Frontend
start_frontend() {
    echo -e "${BLUE}Starting Frontend...${NC}"
    cd "$PROJECT_ROOT/frontend"
    pnpm dev &
    sleep 5
}

# Main
echo "Checking services..."
echo ""

check_kong || start_kong
check_backend || echo -e "${YELLOW}Please start backend manually: cd backend && ./venv/bin/uvicorn app.main:app --reload${NC}"
check_frontend || echo -e "${YELLOW}Please start frontend manually: cd frontend && pnpm dev${NC}"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Access URLs:${NC}"
echo -e "  ${BLUE}Kong Gateway:${NC}  http://localhost:8888"
echo -e "  ${BLUE}Console (UI):${NC}  http://localhost:8888/console"
echo -e "  ${BLUE}Backend API:${NC}   http://localhost:8888/backend/api/v1/health"
echo -e ""
echo -e "${GREEN}Direct Access (for debugging):${NC}"
echo -e "  ${BLUE}Frontend:${NC}      http://localhost:3000/console"
echo -e "  ${BLUE}Backend:${NC}       http://localhost:8000/api/v1/health"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
