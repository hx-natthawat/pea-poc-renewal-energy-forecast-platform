# F003: Multi-Region Support

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F003 |
| Version | v1.1.0 |
| Status | 📋 Planned |
| Priority | P1 - Important |

## Description

Support multiple PEA regions with proper data isolation, region-specific dashboards, and role-based region access. Enables scaling from POC single-region to production multi-region deployment.

**Reference**: v1.1.0 Roadmap - Multi-Region Support
**TOR Reference**: Section 7.1.7 - Support ≥2,000 RE power plants across regions

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F003-R01 | Add region dimension to data models | 📋 Planned |
| F003-R02 | Tenant/region isolation in database | 📋 Planned |
| F003-R03 | Region-specific dashboards | 📋 Planned |
| F003-R04 | Cross-region comparison views | 📋 Planned |
| F003-R05 | Role-based region access control | 📋 Planned |
| F003-R06 | Region hierarchy (Zone > Region > District) | 📋 Planned |
| F003-R07 | Region-specific alert routing | 📋 Planned |
| F003-R08 | Aggregate statistics across regions | 📋 Planned |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| F003-NF01 | Query isolation | No cross-region data leaks |
| F003-NF02 | Dashboard load time | < 3 seconds per region |
| F003-NF03 | Scalability | ≥ 2,000 power plants total |

## Region Hierarchy

```
PEA (Provincial Electricity Authority)
├── Zone 1 (ภาค 1)
│   ├── Region Central (ภาคกลาง)
│   │   ├── District A
│   │   └── District B
│   └── Region East (ภาคตะวันออก)
├── Zone 2 (ภาค 2)
│   ├── Region North (ภาคเหนือ)
│   └── Region Northeast (ภาคตะวันออกเฉียงเหนือ)
└── Zone 3 (ภาค 3)
    ├── Region South (ภาคใต้)
    └── Region West (ภาคตะวันตก)
```

## Database Schema Changes

```sql
-- Add region to existing tables
ALTER TABLE solar_measurements ADD COLUMN region_id VARCHAR(50);
ALTER TABLE prosumers ADD COLUMN region_id VARCHAR(50);
ALTER TABLE single_phase_meters ADD COLUMN region_id VARCHAR(50);
ALTER TABLE predictions ADD COLUMN region_id VARCHAR(50);

-- Create region tables
CREATE TABLE regions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_th VARCHAR(100),
    parent_id VARCHAR(50) REFERENCES regions(id),
    region_type VARCHAR(20) CHECK (region_type IN ('zone', 'region', 'district')),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timezone VARCHAR(50) DEFAULT 'Asia/Bangkok',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_region_access (
    user_id VARCHAR(100) NOT NULL,
    region_id VARCHAR(50) NOT NULL REFERENCES regions(id),
    access_level VARCHAR(20) CHECK (access_level IN ('read', 'write', 'admin')),
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, region_id)
);

-- Add indexes for performance
CREATE INDEX idx_solar_region ON solar_measurements(region_id, time DESC);
CREATE INDEX idx_prosumers_region ON prosumers(region_id);
CREATE INDEX idx_predictions_region ON predictions(region_id, time DESC);
```

## API Specification

### GET /api/v1/regions

**Response:**
```json
{
  "status": "success",
  "data": {
    "regions": [
      {
        "id": "central",
        "name": "Central Thailand",
        "name_th": "ภาคกลาง",
        "region_type": "region",
        "parent_id": "zone1",
        "power_plants_count": 450,
        "prosumers_count": 85000
      }
    ]
  }
}
```

### GET /api/v1/regions/{region_id}/dashboard

Region-specific dashboard data.

### GET /api/v1/regions/compare

Cross-region comparison view.

### GET /api/v1/forecast/solar?region_id={region_id}

Region-filtered solar forecast.

## Implementation Plan

| Component | File | Priority |
|-----------|------|----------|
| Region Model | `backend/app/models/domain/region.py` | P1 |
| Region Service | `backend/app/services/region_service.py` | P1 |
| Region API | `backend/app/api/v1/endpoints/regions.py` | P1 |
| Database Migration | `backend/app/db/migrations/add_regions.py` | P1 |
| Region Filter Middleware | `backend/app/core/middleware.py` | P1 |
| Region Dashboard | `frontend/src/app/(dashboard)/regions/` | P2 |
| Region Comparison | `frontend/src/components/dashboard/RegionComparison.tsx` | P2 |

## Access Control Matrix

| Role | Own Region | Other Regions | Cross-Region |
|------|------------|---------------|--------------|
| Operator | Read/Write | None | None |
| Supervisor | Read/Write | Read | Read |
| Admin | Full | Full | Full |

## Acceptance Criteria

- [ ] Region dimension added to all data models
- [ ] Data isolation verified (no cross-region leaks)
- [ ] Region-specific dashboards functional
- [ ] Cross-region comparison working
- [ ] Role-based region access enforced
- [ ] Database migrations applied successfully
- [ ] Performance within targets
- [ ] Unit and integration tests

---

*Feature Version: 1.0*
*Created: December 2024*
