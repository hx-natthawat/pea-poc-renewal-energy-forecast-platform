#!/bin/bash
# =============================================================================
# PEA RE Forecast Platform - Development Setup Script
# =============================================================================

set -e

echo "========================================"
echo "PEA RE Forecast Platform - Dev Setup"
echo "========================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
echo -e "${YELLOW}Checking Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Copy environment file
echo -e "${YELLOW}Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from .env.example${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Copy POC data to ml/data/raw if exists
echo -e "${YELLOW}Checking POC data...${NC}"
if [ -f "requirements/POC Data.xlsx" ]; then
    cp "requirements/POC Data.xlsx" "ml/data/raw/"
    echo -e "${GREEN}✓ Copied POC Data.xlsx to ml/data/raw/${NC}"
fi

# Start Docker services
echo -e "${YELLOW}Starting Docker services...${NC}"
docker-compose -f docker/docker-compose.yml up -d timescaledb redis

# Wait for database
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 10

echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Start all services:  docker-compose -f docker/docker-compose.yml up -d"
echo "2. View logs:           docker-compose -f docker/docker-compose.yml logs -f"
echo "3. API docs:            http://localhost:8000/api/v1/docs"
echo "4. Frontend:            http://localhost:3000"
echo ""
