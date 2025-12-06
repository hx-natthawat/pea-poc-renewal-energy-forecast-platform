# F001: Model Retraining Pipeline

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F001 |
| Version | v1.1.0 |
| Status | ✅ Completed |
| Priority | P0 - Critical |

## Description

Automated model retraining pipeline with drift detection, A/B testing, and model lifecycle management. Enables automatic detection of model performance degradation and triggers retraining when needed.

**Reference**: v1.1.0 Roadmap - Model Retraining Pipeline

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F001-R01 | Detect data drift using KS-test | ✅ Done |
| F001-R02 | Calculate Population Stability Index (PSI) | ✅ Done |
| F001-R03 | Detect performance drift (MAPE/MAE degradation) | ✅ Done |
| F001-R04 | Evaluate retraining need with configurable thresholds | ✅ Done |
| F001-R05 | Trigger manual retraining via API | ✅ Done |
| F001-R06 | A/B testing setup for champion vs challenger | ✅ Done |
| F001-R07 | Model promotion and rollback capability | ✅ Done |
| F001-R08 | Model version history tracking | ✅ Done |
| F001-R09 | Configurable retraining thresholds | ✅ Done |

### Non-Functional Requirements

| ID | Requirement | Target | Actual |
|----|-------------|--------|--------|
| F001-NF01 | Drift detection latency | < 1s | ~100ms ✅ |
| F001-NF02 | PSI calculation accuracy | Standard bins | 10 bins ✅ |
| F001-NF03 | Role-based access control | Admin/Analyst | ✅ |

## Drift Detection Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| mape_threshold | 12.0% | MAPE threshold for solar models |
| mae_threshold_voltage | 2.5V | MAE threshold for voltage models |
| drift_score_threshold | 2.0 | Z-score threshold for statistical drift |
| max_days_without_retrain | 30 | Force retrain after this period |
| min_days_between_retrains | 7 | Cooldown period |
| consecutive_violations | 3 | Violations needed to trigger |

## API Specification

### POST /api/v1/retraining/drift/analyze

**Request:**
```json
{
  "model_type": "solar",
  "baseline_days": 30,
  "current_days": 7,
  "features": ["power_kw", "pyrano1", "pyrano2", "ambtemp"]
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "model_type": "solar",
    "data_drift": {
      "overall_detected": true,
      "features": [
        {
          "feature": "pyrano1",
          "drift_type": "data",
          "drift_score": 2.45,
          "threshold": 2.0,
          "drift_detected": true,
          "severity": "moderate",
          "p_value": 0.012
        }
      ]
    },
    "performance_drift": {
      "drift_detected": false,
      "severity": "none"
    }
  }
}
```

### POST /api/v1/retraining/evaluate

Evaluate whether model retraining is needed based on all triggers.

### POST /api/v1/retraining/trigger

Manually trigger model retraining (admin only).

### POST /api/v1/retraining/ab-test/setup

Set up A/B test between champion and challenger models.

### POST /api/v1/retraining/ab-test/promote

Promote challenger to champion or rollback to previous version.

### GET /api/v1/retraining/models/history

Get model version history for a model type.

### GET/PUT /api/v1/retraining/config

View or update retraining configuration.

## Implementation

| Component | File | Status |
|-----------|------|--------|
| Drift Detection Service | `backend/app/services/drift_detection_service.py` | ✅ |
| Model Registry Service | `backend/app/services/drift_detection_service.py` | ✅ |
| Retraining API | `backend/app/api/v1/endpoints/retraining.py` | ✅ |
| Unit Tests | `backend/tests/unit/test_drift_detection.py` | ✅ |

## Drift Detection Algorithm

```python
# KS-Test for data drift
from scipy import stats

def detect_data_drift(baseline_data, current_data):
    statistic, p_value = stats.ks_2samp(baseline_data, current_data)
    drift_detected = p_value < 0.05  # 95% confidence
    return DriftResult(drift_score=statistic, p_value=p_value)

# Population Stability Index (PSI)
def calculate_psi(baseline, current, buckets=10):
    # Bin data into buckets
    # PSI = sum((current_pct - baseline_pct) * ln(current_pct / baseline_pct))
    # PSI < 0.1: No drift, 0.1-0.25: Moderate, > 0.25: Significant
```

## Acceptance Criteria

- [x] KS-test drift detection with configurable significance level
- [x] PSI calculation for distribution stability
- [x] Performance drift detection based on MAPE/MAE thresholds
- [x] Retraining evaluation with multiple trigger conditions
- [x] A/B testing framework for model comparison
- [x] Model promotion and rollback capability
- [x] Role-based access (admin for modifications, analyst for read)
- [x] Unit tests pass (23 tests)

---

*Feature Version: 1.0*
*Created: December 2025*
