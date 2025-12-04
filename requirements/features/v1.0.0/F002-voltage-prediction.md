# F002: Voltage Prediction

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F002 |
| Version | v1.0.0 |
| Status | ✅ Completed |
| Priority | P0 - Critical |

## Description

Predict voltage levels across low-voltage distribution networks for prosumer connections.

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F002-R01 | Predict voltage for individual prosumers | ✅ Done |
| F002-R02 | Support all three phases (A, B, C) | ✅ Done |
| F002-R03 | Return voltage status (normal/warning/critical) | ✅ Done |
| F002-R04 | Detect voltage violations before they occur | ✅ Done |
| F002-R05 | Consider prosumer position in network | ✅ Done |

### Non-Functional Requirements

| ID | Requirement | Target | Actual |
|----|-------------|--------|--------|
| F002-NF01 | Voltage MAE | < 2V | 0.036V ✅ |
| F002-NF02 | API response time | < 500ms | P95=25ms ✅ |
| F002-NF03 | Violation detection accuracy | > 95% | 98% ✅ |

## API Specification

### GET /api/v1/forecast/voltage/{prosumer_id}

**Response:**
```json
{
  "status": "success",
  "data": {
    "prosumer_id": "prosumer1",
    "phase": "A",
    "predicted_voltage": 232.5,
    "confidence_lower": 230.5,
    "confidence_upper": 234.5,
    "status": "normal",
    "model_version": "voltage-xgb-v1.0.0"
  }
}
```

### Voltage Limits

| Status | Range |
|--------|-------|
| Normal | 222V - 238V |
| Warning | 218V - 222V or 238V - 242V |
| Critical | < 218V or > 242V |

## Network Topology

```
Transformer (50kVA)
    │
    ├── Phase A ── Prosumer3 ── Prosumer2 ── Prosumer1
    │
    ├── Phase B ── Prosumer6 ── Prosumer4 ── Prosumer5
    │
    └── Phase C ── Prosumer7
```

## Implementation

| Component | File | Status |
|-----------|------|--------|
| API Endpoint | `backend/app/api/v1/endpoints/forecast.py` | ✅ |
| Service | `backend/app/services/voltage_service.py` | ✅ |
| ML Model | `ml/models/voltage_xgboost.joblib` | ✅ |
| Tests | `backend/tests/unit/test_forecast.py` | ✅ |

## Acceptance Criteria

- [x] Voltage predictions for all 7 prosumers
- [x] MAE < 2V on test dataset
- [x] Correct phase assignment for each prosumer
- [x] Status classification based on voltage limits
- [x] Position-aware predictions (near vs far from transformer)
