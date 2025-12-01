#!/bin/bash
# =============================================================================
# PEA RE Forecast Platform - Stop Script
# =============================================================================

cd "$(dirname "$0")/.."

echo "Stopping PEA RE Forecast Platform..."
docker-compose -f docker/docker-compose.yml down

echo "All services stopped."
