# Technical Specification

> **Project**: PEA RE Forecast Platform
> **Version**: 1.0.0
> **Status**: Draft
> **Last Updated**: 2025-12-01

## 1. Introduction

### 1.1 Purpose

This document specifies the technical requirements and implementation details for the PEA RE Forecast Platform, a renewable energy forecasting system for the Provincial Electricity Authority of Thailand (กฟภ.).

### 1.2 Scope

The platform provides:

- Solar power generation forecasting
- Voltage prediction for low-voltage distribution networks
- Real-time monitoring dashboard
- Alert management system

### 1.3 References

- TOR: Terms of Reference แพลตฟอร์มสำหรับศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียนของ กฟภ.
- POC Data: POC_Data.xlsx
- Network Diagram: Appendix 6

---

## 2. System Requirements

### 2.1 Functional Requirements

#### FR-001: Solar Power Forecasting

| ID | Requirement |
|----|-------------|
| FR-001.1 | System SHALL predict solar power output for registered plants |
| FR-001.2 | System SHALL support day-ahead forecasting (24 hours) |
| FR-001.3 | System SHALL support intraday forecasting (1-6 hours) |
| FR-001.4 | System SHALL provide confidence intervals for predictions |

#### FR-002: Voltage Prediction

| ID | Requirement |
|----|-------------|
| FR-002.1 | System SHALL predict voltage for each prosumer connection |
| FR-002.2 | System SHALL identify potential voltage violations |
| FR-002.3 | System SHALL support three-phase networks |
| FR-002.4 | System SHALL track voltage by phase (A, B, C) |

#### FR-003: Data Ingestion

| ID | Requirement |
|----|-------------|
| FR-003.1 | System SHALL ingest solar measurement data |
| FR-003.2 | System SHALL ingest single-phase meter data |
| FR-003.3 | System SHALL ingest three-phase meter data |
| FR-003.4 | System SHALL support batch and streaming ingestion |

#### FR-004: Alerting

| ID | Requirement |
|----|-------------|
| FR-004.1 | System SHALL generate alerts for predicted violations |
| FR-004.2 | System SHALL support alert acknowledgment |
| FR-004.3 | System SHALL maintain alert history |

### 2.2 Non-Functional Requirements

#### NFR-001: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-001.1 | API response time (p99) | < 500ms |
| NFR-001.2 | Batch prediction throughput | > 100/second |
| NFR-001.3 | Dashboard load time | < 3 seconds |

#### NFR-002: Accuracy

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-002.1 | Solar forecast MAPE | < 10% |
| NFR-002.2 | Solar forecast RMSE | < 100 kW |
| NFR-002.3 | Solar forecast R² | > 0.95 |
| NFR-002.4 | Voltage prediction MAE | < 2V |
| NFR-002.5 | Voltage prediction RMSE | < 3V |
| NFR-002.6 | Voltage prediction R² | > 0.90 |

#### NFR-003: Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-003.1 | RE power plants supported | ≥ 2,000 |
| NFR-003.2 | Electricity consumers supported | ≥ 300,000 |
| NFR-003.3 | Concurrent dashboard users | ≥ 100 |

#### NFR-004: Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-004.1 | System uptime | ≥ 99.5% |
| NFR-004.2 | Recovery time objective (RTO) | < 1 hour |
| NFR-004.3 | Recovery point objective (RPO) | < 15 minutes |

---

## 3. Data Specifications

### 3.1 Solar Measurements

```json
{
  "timestamp": "2025-01-15T10:00:00+07:00",
  "station_id": "PLANT_001",
  "measurements": {
    "pvtemp1": 45.2,
    "pvtemp2": 44.8,
    "ambtemp": 32.5,
    "pyrano1": 850.5,
    "pyrano2": 842.3,
    "windspeed": 2.3,
    "power_kw": 3542.5
  }
}
```

### 3.2 Single-Phase Meter Data

```json
{
  "timestamp": "2025-01-15T10:00:00+07:00",
  "prosumer_id": "PROSUMER_001",
  "measurements": {
    "active_power": 2.5,
    "reactive_power": 0.8,
    "voltage": 232.5,
    "current": 10.8
  }
}
```

### 3.3 Three-Phase Meter Data

```json
{
  "timestamp": "2025-01-15T10:00:00+07:00",
  "meter_id": "TX_METER_001",
  "phase_a": {
    "voltage": 231.5,
    "current": 45.2,
    "power": 10.4,
    "reactive_power": 3.2
  },
  "phase_b": {
    "voltage": 230.8,
    "current": 42.1,
    "power": 9.7,
    "reactive_power": 2.9
  },
  "phase_c": {
    "voltage": 232.1,
    "current": 38.5,
    "power": 8.9,
    "reactive_power": 2.6
  },
  "total_power": 29.0
}
```

---

## 4. API Specifications

### 4.1 Authentication

All API calls require Bearer token authentication via Keycloak.

```
Authorization: Bearer <access_token>
```

### 4.2 Endpoints

#### POST /api/v1/forecast/solar

Predict solar power output.

**Request:**

```json
{
  "timestamp": "2025-01-15T10:00:00+07:00",
  "station_id": "PLANT_001",
  "horizon_minutes": 60,
  "features": {
    "pyrano1": 850.5,
    "pyrano2": 842.3,
    "pvtemp1": 45.2,
    "pvtemp2": 44.8,
    "ambtemp": 32.5,
    "windspeed": 2.3
  }
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-01-15T11:00:00+07:00",
    "station_id": "PLANT_001",
    "prediction": {
      "power_kw": 3650.0,
      "confidence_lower": 3500.0,
      "confidence_upper": 3800.0
    },
    "model_version": "solar-xgb-v1.0.0"
  },
  "meta": {
    "prediction_time_ms": 45,
    "cached": false
  }
}
```

#### POST /api/v1/forecast/voltage

Predict voltage levels for prosumers.

**Request:**

```json
{
  "timestamp": "2025-01-15T10:00:00+07:00",
  "prosumer_ids": ["PROSUMER_001", "PROSUMER_002"],
  "horizon_minutes": 15
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "predictions": [
      {
        "prosumer_id": "PROSUMER_001",
        "phase": "A",
        "predicted_voltage": 232.5,
        "confidence_lower": 230.5,
        "confidence_upper": 234.5,
        "status": "normal",
        "violation_probability": 0.02
      }
    ]
  }
}
```

---

## 5. ML Model Specifications

### 5.1 Solar Forecast Model

| Attribute | Value |
|-----------|-------|
| Algorithm | XGBoost Regressor |
| Input Features | 15 features (see CLAUDE.md) |
| Output | Power (kW) |
| Training Data | Min 1 year of 5-min data |
| Validation | Time-series cross-validation |

### 5.2 Voltage Prediction Model

| Attribute | Value |
|-----------|-------|
| Algorithm | Neural Network (MLP) |
| Input Features | Power, reactive power, historical voltage |
| Output | Voltage (V) |
| Training Data | Min 3 months of 1-min data |
| Validation | Time-series cross-validation |

---

## 6. Security Specifications

### 6.1 Authentication

- OAuth2/OIDC via Keycloak
- JWT token validation
- Token expiry: 15 minutes
- Refresh token expiry: 24 hours

### 6.2 Authorization

| Role | Permissions |
|------|-------------|
| Admin | Full access |
| Operator | View dashboards, acknowledge alerts |
| Analyst | View dashboards, export data |
| API | Prediction endpoints only |

### 6.3 Audit Logging

All actions logged with:

- Timestamp
- User ID
- Action
- Resource
- IP Address
- User Agent

---

## 7. Deployment Specifications

### 7.1 Container Images

| Service | Base Image | Size Limit |
|---------|------------|------------|
| Backend | python:3.11-slim | 500MB |
| Frontend | node:20-alpine | 200MB |
| ML Service | python:3.11-slim | 1GB |

### 7.2 Resource Limits

| Service | CPU | Memory |
|---------|-----|--------|
| Backend | 2 cores | 3GB |
| Frontend | 0.5 cores | 512MB |
| ML Service | 4 cores | 8GB |
| TimescaleDB | 6 cores | 24GB |
| Redis | 2 cores | 8GB |

---

## 8. Testing Specifications

### 8.1 Unit Tests

- Coverage target: ≥ 80%
- Framework: pytest (Python), Jest (TypeScript)

### 8.2 Integration Tests

- API endpoint tests
- Database integration
- Cache integration

### 8.3 Load Tests

- Tool: k6 or Locust
- Scenarios:
  - Normal load: 100 concurrent users
  - Peak load: 500 concurrent users
  - Stress test: 1000 concurrent users
