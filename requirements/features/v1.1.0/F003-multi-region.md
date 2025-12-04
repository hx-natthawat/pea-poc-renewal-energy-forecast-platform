# F003: Multi-Region Support

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F003 |
| Version | v1.1.0 |
| Status | ✅ Core Completed |
| Priority | P1 - Important |

## Description

Support multiple PEA regions with proper data isolation, region-specific dashboards, and role-based region access. Enables scaling from POC single-region to production multi-region deployment.

**Reference**: v1.1.0 Roadmap - Multi-Region Support
**TOR Reference**: Section 7.1.7 - Support ≥2,000 RE power plants across regions

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F003-R01 | Region domain model with hierarchy | ✅ Done |
| F003-R02 | Region CRUD operations | ✅ Done |
| F003-R03 | User access control per region | ✅ Done |
| F003-R04 | Region hierarchy navigation | ✅ Done |
| F003-R05 | Region statistics and comparison | ✅ Done |
| F003-R06 | Region-specific dashboard data | ✅ Done |
| F003-R07 | Pre-defined PEA region structure | ✅ Done |
| F003-R08 | Database schema migrations | 📋 Planned |

### Non-Functional Requirements

| ID | Requirement | Target | Actual |
|----|-------------|--------|--------|
| F003-NF01 | Query isolation | No cross-region leaks | ✅ In-memory |
| F003-NF02 | Dashboard load time | < 3 seconds | ✅ Instant |
| F003-NF03 | Scalability | ≥ 2,000 power plants | ✅ Model ready |

## Region Hierarchy

```
PEA (Provincial Electricity Authority)
├── Zone 1 (ภาค 1) - Central & East
│   ├── Central Thailand (ภาคกลาง)
│   │   └── POC Station (สถานีทดสอบสาธิต)
│   └── Eastern Thailand (ภาคตะวันออก)
├── Zone 2 (ภาค 2) - North & Northeast
│   ├── Northern Thailand (ภาคเหนือ)
│   └── Northeastern Thailand (ภาคตะวันออกเฉียงเหนือ)
└── Zone 3 (ภาค 3) - South & West
    ├── Southern Thailand (ภาคใต้)
    └── Western Thailand (ภาคตะวันตก)
```

## API Specification

### GET /api/v1/regions

List all regions with optional filtering.

**Query Parameters:**
- `region_type`: Filter by type (zone, region, district, station)
- `parent_id`: Filter by parent region
- `include_inactive`: Include inactive regions

### GET /api/v1/regions/hierarchy

Get complete region hierarchy tree.

### GET /api/v1/regions/{region_id}

Get specific region details.

### POST /api/v1/regions

Create a new region (admin only).

### PUT /api/v1/regions/{region_id}

Update a region (admin only).

### DELETE /api/v1/regions/{region_id}

Deactivate a region (admin only).

### GET /api/v1/regions/{region_id}/stats

Get region statistics with child aggregation.

### GET /api/v1/regions/{region_id}/dashboard

Get region-specific dashboard data.

### POST /api/v1/regions/compare

Compare multiple regions by metric.

### POST /api/v1/regions/{region_id}/access

Grant user access to region (admin only).

### DELETE /api/v1/regions/{region_id}/access/{user_id}

Revoke user access (admin only).

### GET /api/v1/regions/access/me

Get current user's accessible regions.

### GET /api/v1/regions/{region_id}/access/check

Check if current user has access.

## Access Control

| Level | Description |
|-------|-------------|
| READ | View region data and dashboards |
| WRITE | Modify region data (forecasts, alerts) |
| ADMIN | Full control including user access |

## Implementation

| Component | File | Status |
|-----------|------|--------|
| Region Domain Model | `backend/app/models/domain/region.py` | ✅ |
| Region Schemas | `backend/app/models/schemas/region.py` | ✅ |
| Region Service | `backend/app/services/region_service.py` | ✅ |
| Region API | `backend/app/api/v1/endpoints/regions.py` | ✅ |
| Unit Tests | `backend/tests/unit/test_region_service.py` | ✅ |
| DB Migrations | `backend/app/db/migrations/` | 📋 |

## Pre-Defined Regions

| ID | Name | Type | Parent |
|----|------|------|--------|
| zone1 | Zone 1 - Central & East | zone | - |
| zone2 | Zone 2 - North & Northeast | zone | - |
| zone3 | Zone 3 - South & West | zone | - |
| central | Central Thailand | region | zone1 |
| east | Eastern Thailand | region | zone1 |
| north | Northern Thailand | region | zone2 |
| northeast | Northeastern Thailand | region | zone2 |
| south | Southern Thailand | region | zone3 |
| west | Western Thailand | region | zone3 |
| poc_station | POC Station | station | central |

## Acceptance Criteria

- [x] Region domain model with hierarchy support
- [x] Region CRUD via API
- [x] User access control (grant/revoke)
- [x] Access level checking (read/write/admin)
- [x] Region hierarchy navigation
- [x] Region statistics with child aggregation
- [x] Region comparison endpoint
- [x] Dashboard data endpoint
- [x] Pre-defined PEA regions loaded
- [x] Unit tests pass (44 tests)
- [ ] Database migrations applied
- [ ] Region filter on existing queries

---

*Feature Version: 1.0*
*Created: December 2024*
*Updated: December 2024 - Core implementation completed*
