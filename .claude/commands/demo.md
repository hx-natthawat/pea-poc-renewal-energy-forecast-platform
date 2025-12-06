# Demo - Stakeholder Demonstration Setup

You are the **Demo Orchestrator** for the PEA RE Forecast Platform. Your role is to prepare the environment for stakeholder demonstrations.

## Purpose

Prepare a complete, working demonstration environment that showcases:
1. Solar power forecasting capabilities
2. Voltage prediction and network monitoring
3. Alert management and notifications
4. Audit logging and compliance features
5. Multi-region support

## Demo Setup Steps

### Step 1: Verify Prerequisites

```bash
# Check Docker is running
docker info > /dev/null 2>&1 || echo "ERROR: Docker not running"

# Check required ports are available
lsof -i :5433 || echo "Port 5433 available (database)"
lsof -i :8000 || echo "Port 8000 available (backend)"
lsof -i :3000 || echo "Port 3000 available (frontend)"
```

### Step 2: Start Infrastructure

```bash
# Start database and cache
cd /Users/fero/Desktop/PEA/pea-re-forecast-platform
docker-compose -f docker/docker-compose.yml up -d timescaledb redis

# Wait for database to be ready
sleep 10
```

### Step 3: Load Demo Data

```bash
# Load POC data with simulation data
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/pea_forecast" \
  ml/venv/bin/python ml/scripts/load_poc_data.py

# Generate additional demo data if needed
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/pea_forecast" \
  ml/venv/bin/python ml/scripts/generate_demo_data.py
```

### Step 4: Start Backend

```bash
cd /Users/fero/Desktop/PEA/pea-re-forecast-platform/backend
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### Step 5: Start Frontend

```bash
cd /Users/fero/Desktop/PEA/pea-re-forecast-platform/frontend
pnpm dev &
```

### Step 6: Verify Services

```bash
# Check backend health
curl -s http://localhost:8000/api/v1/health | jq .

# Check frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```

## Demo Credentials

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Frontend | http://localhost:3000 | demo@pea.co.th | demo123 |
| Backend API | http://localhost:8000/docs | - | - |
| Grafana | http://localhost:3001 | admin | admin |

## Demo Scenarios

### Scenario 1: Solar Forecast Dashboard
1. Navigate to http://localhost:3000
2. View real-time solar power predictions
3. Show historical forecast accuracy (MAPE < 10%)
4. Demonstrate forecast comparison charts

### Scenario 2: Voltage Monitoring
1. Navigate to Network Topology page
2. Show prosumer voltage levels across phases
3. Demonstrate voltage violation alerts
4. Show prediction accuracy (MAE < 2V)

### Scenario 3: Alert Management
1. Navigate to Alerts page
2. Show active alerts with severity levels
3. Demonstrate alert acknowledgment
4. Show notification channels (Email, LINE)

### Scenario 4: Audit Compliance (TOR 7.1.6)
1. Navigate to /audit (Shield icon)
2. Show comprehensive audit trail
3. Demonstrate filtering and export
4. Show security event monitoring

### Scenario 5: Multi-Region Support
1. Show region selector
2. Demonstrate 4 PEA zones
3. Show RBAC permissions
4. Compare regional data

## Cleanup

```bash
# Stop all services
pkill -f "uvicorn"
pkill -f "next"

# Stop Docker containers
docker-compose -f docker/docker-compose.yml down
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check Docker: `docker ps` |
| Backend won't start | Check port 8000: `lsof -i :8000` |
| Frontend errors | Run `pnpm install` |
| No data visible | Run demo data loader |

## Instructions

When this command is invoked:

1. **Check current environment state**
   - Are Docker containers running?
   - Is the database populated?
   - Are services accessible?

2. **Execute setup if needed**
   - Start missing services
   - Load demo data
   - Verify connectivity

3. **Provide demo briefing**
   - List available URLs
   - Describe demo scenarios
   - Provide credentials

4. **Report status**
   - All services running
   - Data loaded
   - Ready for demonstration

Output a clear status report showing:
- Service status (running/stopped)
- URLs for demo
- Available demo scenarios
- Any issues to address
