# Getting Started Guide

## Prerequisites

Ensure you have the following installed:

```bash
# Check versions
docker --version      # >= 24.0
docker-compose --version  # >= 2.20
kind --version        # >= 0.20
kubectl version       # >= 1.28
helm version          # >= 3.13
python --version      # >= 3.11
node --version        # >= 20.0
```

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd pea-re-forecast-platform
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your local settings
nano .env
```

### 3. Start Local Development

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| TimescaleDB | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | - |
| Grafana | http://localhost:3001 | admin/admin |

### 5. Load Sample Data

```bash
# Run data loader
docker-compose exec backend python scripts/load_poc_data.py
```

### 6. Run Tests

```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test
```

## Development Workflow

### Using Claude Code Commands

```bash
# Analyze POC data
/analyze-poc-data

# Generate simulation data
/simulate-solar
/simulate-voltage

# Validate ML models
/validate-model

# Deploy to Kind cluster
/deploy-local

# Research latest library versions
/research-latest
```

### Standard Workflow

1. **Before coding**: Run `/research-latest` for dependencies
2. **During development**: Test locally with Docker Compose
3. **Before commit**: Ensure all tests pass
4. **After completing task**: Run `/update-plan`
5. **Commit**: Include updated plan files

## Local Kubernetes (Kind)

### Create Cluster

```bash
# Create Kind cluster
kind create cluster --name pea-forecast --config infrastructure/kind/kind-config.yaml

# Verify
kubectl cluster-info --context kind-pea-forecast
```

### Deploy Services

```bash
# Install with Helm
helm install pea-forecast ./infrastructure/helm/pea-re-forecast \
  -f ./infrastructure/helm/pea-re-forecast/values.yaml \
  -n pea-forecast --create-namespace

# Check status
kubectl get pods -n pea-forecast
```

### Cleanup

```bash
# Delete cluster
kind delete cluster --name pea-forecast
```

## Troubleshooting

### Common Issues

**Docker not starting:**

```bash
# Restart Docker daemon
sudo systemctl restart docker
```

**Database connection failed:**

```bash
# Check TimescaleDB is running
docker-compose ps timescaledb
docker-compose logs timescaledb
```

**Port already in use:**

```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

### Getting Help

- Check [docs/architecture/](./docs/architecture/) for system design
- Check [docs/specs/](./docs/specs/) for technical details
- Run `/help` in Claude Code for available commands
