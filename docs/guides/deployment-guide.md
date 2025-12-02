# PEA RE Forecast Platform - Deployment Guide

> **Version**: 1.0.0
> **Last Updated**: 2025-12-03
> **Environment**: Local Development (Kind Kubernetes)

## Prerequisites

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| Docker Desktop | Latest | [docker.com](https://www.docker.com/products/docker-desktop) |
| Kind | v0.20+ | `brew install kind` |
| kubectl | v1.28+ | `brew install kubectl` |
| Node.js | v20 LTS | `brew install node@20` |
| Python | v3.11+ | `brew install python@3.11` |

### Verify Prerequisites

```bash
docker --version
kind version
kubectl version --client
node --version
python3 --version
```

---

## Quick Start (5 minutes)

### 1. Create Kind Cluster

```bash
# Create cluster with port mappings
kind create cluster --name pea-forecast --config infrastructure/kind-config.yaml

# Verify cluster
kubectl cluster-info --context kind-pea-forecast
```

### 2. Create Namespace and Base Resources

```bash
# Create namespace
kubectl apply -f infrastructure/kubernetes/base/namespace.yaml

# Apply ConfigMaps and Secrets
kubectl apply -f infrastructure/kubernetes/base/
```

### 3. Deploy Databases

```bash
# Deploy TimescaleDB
kubectl apply -f infrastructure/kubernetes/databases/timescaledb/

# Deploy Redis
kubectl apply -f infrastructure/kubernetes/databases/redis/

# Wait for databases to be ready
kubectl wait --for=condition=ready pod -l app=timescaledb -n pea-forecast --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n pea-forecast --timeout=60s
```

### 4. Build and Deploy Applications

```bash
# Build Docker images
docker build -t pea-forecast/backend:latest ./backend
docker build -t pea-forecast/frontend:latest ./frontend

# Load images to Kind
kind load docker-image pea-forecast/backend:latest --name pea-forecast
kind load docker-image pea-forecast/frontend:latest --name pea-forecast

# Deploy applications
kubectl apply -f infrastructure/kubernetes/apps/backend/
kubectl apply -f infrastructure/kubernetes/apps/frontend/

# Wait for deployments
kubectl rollout status deployment/backend -n pea-forecast --timeout=120s
kubectl rollout status deployment/frontend -n pea-forecast --timeout=120s
```

### 5. Setup Port Forwarding

```bash
# Terminal 1: Backend API
kubectl port-forward -n pea-forecast svc/backend 8000:8000

# Terminal 2: Frontend
kubectl port-forward -n pea-forecast svc/frontend 3000:3000

# Terminal 3 (optional): Database direct access
kubectl port-forward -n pea-forecast svc/timescaledb 5433:5432
```

### 6. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n pea-forecast

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# backend-xxx                    1/1     Running   0          2m
# frontend-xxx                   1/1     Running   0          2m
# redis-xxx                      1/1     Running   0          3m
# timescaledb-xxx                1/1     Running   0          3m

# Test endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

---

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend Dashboard | http://localhost:3000 | Main user interface |
| Backend API | http://localhost:8000/api/v1 | REST API endpoints |
| API Documentation | http://localhost:8000/api/v1/docs | Swagger UI |
| WebSocket | ws://localhost:8000/api/v1/ws | Real-time updates |
| Database | localhost:5433 | TimescaleDB (via port-forward) |

---

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Solar Forecast Data
```bash
curl "http://localhost:8000/api/v1/data/solar/latest?hours=24"
```

### Voltage Monitoring Data
```bash
curl "http://localhost:8000/api/v1/data/voltage/latest?hours=2"
```

### Solar Power Prediction
```bash
curl -X POST http://localhost:8000/api/v1/forecast/solar \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-06-01T12:00:00",
    "pyrano1": 800,
    "pyrano2": 795,
    "pvtemp1": 45,
    "pvtemp2": 44,
    "ambtemp": 32,
    "windspeed": 2.5
  }'
```

### Voltage Prediction
```bash
curl -X POST http://localhost:8000/api/v1/forecast/voltage \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-06-01T12:00:00",
    "prosumer_id": "prosumer1"
  }'
```

### WebSocket Connection Test
```bash
# Using Python
python3 -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/api/v1/ws?channels=all') as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        print('Connected:', msg)

asyncio.run(test())
"
```

---

## Common Operations

### Restart Deployments

```bash
# Restart backend
kubectl rollout restart deployment/backend -n pea-forecast

# Restart frontend
kubectl rollout restart deployment/frontend -n pea-forecast
```

### View Logs

```bash
# Backend logs
kubectl logs -f -l app=backend -n pea-forecast

# Frontend logs
kubectl logs -f -l app=frontend -n pea-forecast

# Database logs
kubectl logs -f -l app=timescaledb -n pea-forecast
```

### Rebuild and Redeploy

```bash
# Rebuild backend
docker build -t pea-forecast/backend:latest ./backend
kind load docker-image pea-forecast/backend:latest --name pea-forecast
kubectl rollout restart deployment/backend -n pea-forecast

# Rebuild frontend
docker build -t pea-forecast/frontend:latest ./frontend
kind load docker-image pea-forecast/frontend:latest --name pea-forecast
kubectl rollout restart deployment/frontend -n pea-forecast
```

### Load/Reload POC Data

```bash
# Port-forward database first
kubectl port-forward -n pea-forecast svc/timescaledb 5433:5432 &

# Run data loading script
cd ml
DATABASE_URL="postgresql://postgres:postgres@localhost:5433/pea_forecast" \
  ./venv/bin/python scripts/load_poc_data.py
```

---

## Cleanup

### Stop Port Forwards
```bash
pkill -f "port-forward"
```

### Delete Cluster
```bash
kind delete cluster --name pea-forecast
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n pea-forecast

# Check events
kubectl get events -n pea-forecast --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test database connectivity from backend pod
kubectl exec -it deployment/backend -n pea-forecast -- \
  python -c "from app.db.session import engine; print(engine.url)"
```

### Frontend Not Loading Data

1. Check backend is accessible: `curl http://localhost:8000/api/v1/health`
2. Check browser console for CORS errors
3. Verify port-forwards are running: `lsof -i :3000` and `lsof -i :8000`

### WebSocket Not Connecting

1. Check backend WebSocket endpoint: `curl -v http://localhost:8000/api/v1/ws`
2. Verify browser is using `ws://localhost:8000/api/v1/ws` (not internal K8s URL)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kind Kubernetes Cluster                     │
│                     (pea-forecast namespace)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Frontend   │    │   Backend   │    │    TimescaleDB      │ │
│  │  (Next.js)  │───▶│  (FastAPI)  │───▶│   (PostgreSQL)      │ │
│  │   :3000     │    │   :8000     │    │      :5432          │ │
│  └─────────────┘    └──────┬──────┘    └─────────────────────┘ │
│                            │                                    │
│                            │           ┌─────────────────────┐ │
│                            └──────────▶│       Redis         │ │
│                                        │      :6379          │ │
│                                        └─────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
   localhost:3000         localhost:8000
   (port-forward)         (port-forward)
```

---

## Performance Metrics (POC)

| Metric | Value | Target |
|--------|-------|--------|
| Solar MAPE | 9.74% | < 10% |
| Solar RMSE | 35.60 kW | < 100 kW |
| Voltage MAE | 0.036 V | < 2 V |
| Voltage R² | 0.9949 | > 0.90 |
| API P95 Latency | 371ms (voltage) | < 500ms |

---

*Document Version: 1.0.0*
*Last Updated: 2025-12-03*
