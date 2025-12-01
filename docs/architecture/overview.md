# PEA RE Forecast Platform - Architecture Overview

## System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SYSTEMS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  RE Plants   │  │   Weather    │  │  Smart       │  │   Grid       │    │
│  │  (2,000+)    │  │   API        │  │  Meters      │  │   Control    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                  PEA RE FORECAST PLATFORM                           │    │
│  │                                                                     │    │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │    │
│  │   │   Ingest    │───▶│   Process   │───▶│   Predict   │            │    │
│  │   │   Layer     │    │   Layer     │    │   Layer     │            │    │
│  │   └─────────────┘    └─────────────┘    └─────────────┘            │    │
│  │                                                │                    │    │
│  │                                                ▼                    │    │
│  │                             ┌─────────────────────────────┐        │    │
│  │                             │      Dashboard & Alerts     │        │    │
│  │                             └─────────────────────────────┘        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │  Operators   │  │  Analysts    │  │  Managers    │                       │
│  │  (กฟภ.)      │  │              │  │              │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          KUBERNETES CLUSTER                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        INGRESS LAYER                                │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│  │  │   Nginx     │───▶│    Kong     │───▶│  Keycloak   │             │   │
│  │  │   Ingress   │    │   Gateway   │    │   Auth      │             │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      APPLICATION LAYER                              │   │
│  │                                                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│  │  │  Frontend   │    │   Backend   │    │ ML Service  │             │   │
│  │  │  (React)    │    │  (FastAPI)  │    │ (Inference) │             │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA LAYER                                   │   │
│  │                                                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│  │  │ TimescaleDB │    │    Redis    │    │    Kafka    │             │   │
│  │  │  (Primary)  │    │   (Cache)   │    │ (Streaming) │             │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OBSERVABILITY LAYER                              │   │
│  │                                                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │   │
│  │  │ Prometheus  │    │   Grafana   │    │   Jaeger    │             │   │
│  │  │  (Metrics)  │    │  (Dashbd)   │    │  (Tracing)  │             │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘             │   │
│  │                                                                     │   │
│  │  ┌─────────────┐    ┌─────────────┐                                │   │
│  │  │  Fluentbit  │───▶│ OpenSearch  │                                │   │
│  │  │  (Logging)  │    │  (Storage)  │                                │   │
│  │  └─────────────┘    └─────────────┘                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend (React + Next.js)

- Dashboard for RE forecast visualization
- Voltage monitoring with phase diagrams
- Alert management interface
- Real-time updates via WebSocket

### Backend (FastAPI)

- RESTful API for predictions
- Data ingestion endpoints
- WebSocket for real-time updates
- Integration with ML models

### ML Service

- Solar power prediction (XGBoost)
- Voltage prediction (Neural Network)
- Model versioning via MLflow
- Batch and real-time inference

### TimescaleDB

- Time-series data storage
- Hypertables for measurements
- Continuous aggregates
- Data retention policies

### Kafka

- Real-time data streaming
- Decoupled data ingestion
- Event-driven architecture

### Redis

- Prediction caching
- Session management
- Rate limiting

## Data Flow

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│  Sensors  │────▶│   Kafka   │────▶│  Backend  │────▶│TimescaleDB│
│  Meters   │     │           │     │           │     │           │
└───────────┘     └───────────┘     └─────┬─────┘     └───────────┘
                                          │
                                          ▼
┌───────────┐     ┌───────────┐     ┌───────────┐
│  Frontend │◀────│   Redis   │◀────│ML Service │
│           │     │  (Cache)  │     │           │
└───────────┘     └───────────┘     └───────────┘
```

## Security Architecture

- **Keycloak**: OAuth2/OIDC authentication
- **Kong**: API rate limiting, JWT validation
- **Vault**: Secrets management
- **Cilium**: Network policies
- **Trivy**: Container scanning
- **SonarQube**: Code quality

## Scalability Considerations

| Component | Scaling Strategy | Target |
|-----------|-----------------|--------|
| Frontend | Horizontal (replicas) | 10 pods |
| Backend | Horizontal (replicas) | 20 pods |
| ML Service | Horizontal (replicas) | 10 pods |
| TimescaleDB | Vertical + Read replicas | 1 primary + 2 replicas |
| Redis | Cluster mode | 3 nodes |
| Kafka | Cluster mode | 3 brokers |
