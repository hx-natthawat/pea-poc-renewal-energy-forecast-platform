# F006: Historical Analysis

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F006 |
| Version | v1.0.0 |
| Status | ✅ Completed |
| Priority | P1 - Important |

## Description

Query and analyze historical solar and voltage data with export capabilities.

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F006-R01 | Date range picker for queries | ✅ Done |
| F006-R02 | Hourly and daily aggregations | ✅ Done |
| F006-R03 | Solar power history charts | ✅ Done |
| F006-R04 | Voltage history by prosumer | ✅ Done |
| F006-R05 | Export to CSV/JSON | ✅ Done |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | datetime | Range start |
| end_date | datetime | Range end |
| interval | string | 5m, 15m, 1h, 1d |
| prosumer_id | string | Optional filter |

## API Specification

### GET /api/v1/history/solar

**Response:**
```json
{
  "status": "success",
  "data": {
    "measurements": [
      {
        "timestamp": "2025-01-15T10:00:00Z",
        "power_kw": 3542.5,
        "irradiance": 850.2,
        "temperature": 32.5
      }
    ],
    "aggregation": "hourly",
    "count": 24
  }
}
```

### GET /api/v1/history/voltage

### GET /api/v1/history/export

**Query Parameters:**
- `format`: csv | json
- `type`: solar | voltage

## Implementation

| Component | File | Status |
|-----------|------|--------|
| API Endpoints | `backend/app/api/v1/endpoints/history.py` | ✅ |
| Service | `backend/app/services/history_service.py` | ✅ |
| UI Component | `frontend/src/components/dashboard/HistoricalAnalysis.tsx` | ✅ |
| Tests | `backend/tests/unit/test_history.py` | ✅ |

## Acceptance Criteria

- [x] Date range queries return within 2 seconds
- [x] Aggregations calculated correctly
- [x] CSV export includes all selected fields
- [x] Charts render up to 30 days of data
- [x] Empty state shown when no data available
