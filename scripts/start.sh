#!/bin/bash
# =============================================================================
# PEA RE Forecast Platform - Quick Start Script
# =============================================================================

set -e

echo "Starting PEA RE Forecast Platform..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Start services
docker-compose -f docker/docker-compose.yml up -d

echo ""
echo "Services started!"
echo ""
echo "Access points:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Backend:   http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "View logs: docker-compose -f docker/docker-compose.yml logs -f"
echo "Stop:      docker-compose -f docker/docker-compose.yml down"
