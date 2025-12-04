# PEA RE Forecast Platform

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/hx-natthawat/pea-poc-renewal-energy-forecast-platform/releases/tag/v1.0.0)
[![Tests](https://img.shields.io/badge/tests-214%20passed-green.svg)]()
[![TOR](https://img.shields.io/badge/TOR-compliant-success.svg)]()

Renewable Energy Forecast Platform for the Provincial Electricity Authority of Thailand (PEA).

## Overview

This platform provides:

- **RE Forecast Module** - Solar PV power prediction from environmental parameters
- **Voltage Prediction Module** - LV network voltage forecasting for prosumers
- **Real-time Monitoring** - WebSocket-based live updates
- **Alert Management** - Proactive voltage violation alerts

## TOR Compliance

| Requirement | Target | Actual | Status |
|-------------|--------|--------|--------|
| Solar MAPE | < 10% | 9.74% | PASS |
| Voltage MAE | < 2V | 0.036V | PASS |
| API Latency | < 500ms | P95=38ms | PASS |
| Scale | 300K users | Validated | PASS |

## Quick Start

### Prerequisites

- Docker 24.x+
- Node.js 20.x (for frontend development)
- Python 3.11+ (for backend development)

### Run with Docker

```bash
# Clone repository
git clone https://github.com/hx-natthawat/pea-poc-renewal-energy-forecast-platform.git
cd pea-poc-renewal-energy-forecast-platform

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Verify
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
pnpm install
pnpm dev
```

## Architecture

```
pea-re-forecast-platform/
├── backend/          # FastAPI + Python 3.11
├── frontend/         # React + TypeScript + Next.js
├── ml/               # XGBoost + TensorFlow models
├── infrastructure/   # Kubernetes + Helm charts
└── docker/           # Docker Compose configs
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Next.js, Recharts, ReactFlow |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Pydantic |
| Database | TimescaleDB (PostgreSQL), Redis |
| ML | XGBoost, scikit-learn, pandas |
| Infrastructure | Kubernetes, Helm, Docker |
| Observability | Prometheus, Grafana, Jaeger |
| Security | Keycloak, Trivy, SonarQube |

## API Documentation

Once running, access the API docs at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

```
GET  /api/v1/health              # Health check
POST /api/v1/forecast/solar      # Solar power prediction
GET  /api/v1/forecast/voltage/{id}  # Voltage prediction
GET  /api/v1/alerts              # Active alerts
WS   /api/v1/ws/realtime         # Real-time updates
```

## Testing

```bash
# Run all tests
cd backend
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html
```

**Test Results**: 214 passed, 4 skipped

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Helm Deployment

```bash
helm upgrade --install pea-forecast ./infrastructure/helm/pea-forecast \
  --namespace pea-forecast \
  --create-namespace \
  -f infrastructure/helm/pea-forecast/values-prod.yaml
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Security, config
│   ├── models/          # Database & Pydantic models
│   ├── services/        # Business logic
│   └── ml/              # ML inference
└── tests/               # Unit tests

frontend/
├── src/
│   ├── app/             # Next.js pages
│   ├── components/      # React components
│   ├── hooks/           # Custom hooks
│   └── stores/          # State management
```

## Configuration

Environment variables:

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
KEYCLOAK_URL=https://auth.example.com
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Proprietary - Provincial Electricity Authority of Thailand

## Contact

- Platform Team: platform@pea.co.th
- DevOps: devops@pea.co.th

---

**Version**: 1.0.0 | **Last Updated**: December 2024
