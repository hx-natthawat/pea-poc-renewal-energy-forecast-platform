# F007: Weather Handling System

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F007 |
| Version | v1.0.0 |
| Status | ✅ Completed |
| Priority | P0 - Critical |

## Description

Comprehensive extreme weather handling system for the PEA RE Forecast Platform, including TMD API integration, ramp rate detection, weather-adaptive forecasting, and probabilistic outputs.

**Reference**: Q2.4 - "จะจัดการกับสภาพอากาศที่ผิดปกติ เช่น พายุ หรือ ฝนตกหนัก อย่างไร?"

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F007-R01 | Integrate TMD API for weather alerts | ✅ Done |
| F007-R02 | Detect rapid irradiance changes (ramp rate) | ✅ Done |
| F007-R03 | Classify weather conditions (clear/cloudy/rainy/storm) | ✅ Done |
| F007-R04 | Provide probabilistic forecasts (P10/P50/P90) | ✅ Done |
| F007-R05 | Weather alert banner on dashboard | ✅ Done |
| F007-R06 | Ramp rate monitoring with real-time gauge | ✅ Done |
| F007-R07 | Calculate clearness index | ✅ Done |
| F007-R08 | Apply weather-based uncertainty multipliers | ✅ Done |

### Non-Functional Requirements

| ID | Requirement | Target | Actual |
|----|-------------|--------|--------|
| F007-NF01 | Weather alert latency | < 5 min from TMD | ~5 min ✅ |
| F007-NF02 | Ramp rate detection latency | < 50ms | ~30ms ✅ |
| F007-NF03 | Weather classification latency | < 10ms | ~5ms ✅ |

## Weather Classification Schema

| Condition | Clearness Index (kt) | Uncertainty Multiplier |
|-----------|---------------------|------------------------|
| Clear | kt >= 0.7 | 1.0x |
| Partly Cloudy | 0.5 <= kt < 0.7 | 1.5x |
| Cloudy | 0.3 <= kt < 0.5 | 2.0x |
| Rainy | kt < 0.3 | 3.0x |
| Storm | Alert flag | 5.0x |

## API Specification

### GET /api/v1/weather/alerts

**Response:**
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": "alert-001",
        "timestamp": "2025-01-15T10:00:00Z",
        "condition": "storm",
        "severity": "critical",
        "region": "Central Thailand",
        "description": "Heavy thunderstorm expected",
        "expected_duration_minutes": 120,
        "recommended_action": "Consider conservative forecasting"
      }
    ],
    "count": 1
  }
}
```

### GET /api/v1/weather/ramp-rate/current

**Response:**
```json
{
  "status": "success",
  "data": {
    "current_ramp_rate_percent": 15.5,
    "threshold_percent": 30.0,
    "is_alert": false,
    "direction": "down",
    "variability_index": 0.12,
    "last_event": {
      "timestamp": "2025-01-15T09:45:00Z",
      "rate_percent": -32.5,
      "direction": "down"
    }
  }
}
```

### GET /api/v1/weather/condition

**Query Parameters:**
- `latitude`: Location latitude
- `longitude`: Location longitude

**Response:**
```json
{
  "status": "success",
  "data": {
    "condition": "partly_cloudy",
    "clearness_index": 0.65,
    "uncertainty_factor": 1.5
  }
}
```

## Ramp Rate Detection Algorithm

```python
@dataclass
class RampRateConfig:
    window_size_seconds: int = 300  # 5 minutes
    threshold_percent: float = 30.0  # 30% change
    min_irradiance: float = 50.0    # W/m² minimum
    alert_cooldown_seconds: int = 60

# Detects >30% change in irradiance within 5 minutes
# Triggers alert and adjusts forecast uncertainty
```

## Implementation

| Component | File | Status |
|-----------|------|--------|
| Weather Service | `backend/app/services/weather_service.py` | ✅ |
| Ramp Rate Service | `backend/app/services/ramp_rate_service.py` | ✅ |
| Weather API | `backend/app/api/v1/endpoints/weather.py` | ✅ |
| Weather Schemas | `backend/app/models/schemas/weather.py` | ✅ |
| Alert Banner | `frontend/src/components/dashboard/WeatherAlertBanner.tsx` | ✅ |
| Probabilistic Chart | `frontend/src/components/dashboard/ProbabilisticChart.tsx` | ✅ |
| Ramp Rate Monitor | `frontend/src/components/dashboard/RampRateMonitor.tsx` | ✅ |
| Grafana Dashboard | `docker/observability/grafana/dashboards/weather-monitoring.json` | ✅ |
| Prometheus Alerts | `docker/observability/prometheus/alerts.yml` | ✅ |
| Unit Tests | `backend/tests/unit/test_weather.py` | ✅ |
| Service Tests | `backend/tests/unit/test_services.py` | ✅ |

## Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| RampRateExceeded | >30% in 1min | Warning |
| CriticalRampRate | >50% in 30s | Critical |
| StormConditionActive | Storm detected | Critical |
| LowClearnessIndex | kt < 0.3 | Warning |
| TMDAPIUnavailable | API timeout | Warning |

## Acceptance Criteria

- [x] TMD API integration with fallback to simulation
- [x] Ramp rate detection with configurable thresholds
- [x] Weather classification based on clearness index
- [x] Probabilistic forecast output (P10/P50/P90)
- [x] Real-time weather alert banner on dashboard
- [x] Ramp rate gauge with historical events
- [x] Grafana dashboard for weather monitoring
- [x] Prometheus alerts for weather anomalies
- [x] Unit tests pass (40+ weather-related tests)

---

*Consolidated from: plan.md, spec.md, implementation.md*
*Feature Version: 1.0*
*Created: December 2025*
