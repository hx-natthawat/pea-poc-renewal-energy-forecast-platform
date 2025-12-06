# Phase 2b: DOE (Dynamic Operating Envelope) Implementation Plan

**TOR Reference**: 7.5.1.6
**Status**: Planning Complete
**Created**: December 6, 2025
**Blocked By**: Network model data from กฟภ. GIS system

---

## Executive Summary

DOE (Dynamic Operating Envelope) provides real-time, time-varying export/import limits for Distributed Energy Resources (DER) that maintain all network constraints without compromising power quality or reliability.

**Key Difference from Static Limits:**
| Aspect | Traditional Static | DOE Dynamic |
|--------|-------------------|-------------|
| Export Limit | Fixed (worst-case) | Time-varying |
| Update Frequency | Annual | Every 5-15 minutes |
| RE Utilization | Conservative | Optimized (10-30% more) |

---

## Dependencies

### Required Inputs

| Input | Status | Blocker |
|-------|--------|---------|
| Network Model (topology, impedances) | ❌ Missing | Requires GIS data from กฟภ. |
| Voltage Predictions (Function 5) | ✅ Ready | - |
| Load Forecasts (Function 3) | ✅ Phase 2a | - |
| RE Forecasts (Function 1) | ✅ Ready | MAPE 9.74% |
| Real-time Measurements | ⚠️ Partial | SCADA integration needed |

### Downstream Dependencies

| Function | Depends On DOE |
|----------|----------------|
| Hosting Capacity (TOR 7.5.1.7) | Yes - aggregates DOE limits |

---

## Technical Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              DOE Calculation Service                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Inputs:                                                     │
│  • Network Model (from DB/config)                           │
│  • Voltage Predictions (from Function 5)                    │
│  • Load Forecasts (from Function 3)                         │
│  • RE Forecasts (from Function 1)                           │
│  • Real-time Measurements (from SCADA)                      │
│          ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Power Flow Calculation Engine                       │   │
│  │  • Pandapower (recommended) or OpenDSS               │   │
│  │  • AC Power Flow for LV networks                     │   │
│  └──────────────────────────────────────────────────────┘   │
│          ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Constraint Checking                                 │   │
│  │  • Voltage: 218-242V (LV), ±5%                       │   │
│  │  • Thermal: Line/transformer ampacity                │   │
│  │  • Protection: Relay settings                        │   │
│  └──────────────────────────────────────────────────────┘   │
│          ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Limit Determination                                 │   │
│  │  • Binary search for max export/import               │   │
│  │  • Apply 5-10% safety margin                         │   │
│  │  • Output confidence scores                          │   │
│  └──────────────────────────────────────────────────────┘   │
│          ↓                                                   │
│  Outputs:                                                    │
│  • DOE per connection point (export/import kW)              │
│  • Limiting factor (voltage/thermal/protection)            │
│  • Valid time window (5-15 minutes)                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Required

### Network Model Management
```
POST   /api/v1/network/topology/upload    # Upload GIS data
GET    /api/v1/network/topology           # Get network model
GET    /api/v1/network/branches           # Line/cable parameters
GET    /api/v1/network/constraints        # Operating limits
```

### DOE Calculation
```
POST   /api/v1/doe/calculate              # Single prosumer
POST   /api/v1/doe/calculate/batch        # All prosumers
GET    /api/v1/doe/limits/{prosumer_id}   # Current limits
GET    /api/v1/doe/history                # Historical DOE
WS     /ws/doe/live                       # Real-time updates
```

---

## Output Format

```json
{
  "connection_point": "prosumer1",
  "timestamp": "2025-03-15T10:00:00Z",
  "valid_until": "2025-03-15T10:15:00Z",
  "export_limit_kw": 8.5,
  "import_limit_kw": 15.0,
  "limiting_factor": "voltage_rise",
  "confidence": 0.95,
  "details": {
    "voltage_prediction": 239.2,
    "voltage_limit": 242.0,
    "thermal_headroom_pct": 35,
    "binding_constraint": "overvoltage_risk"
  }
}
```

---

## Implementation Roadmap

| Step | Task | Duration | Status |
|------|------|----------|--------|
| 1 | Obtain network model from กฟภ. GIS | - | ⏳ BLOCKED |
| 2 | Define network data schema | 1 week | Pending |
| 3 | Integrate Pandapower solver | 2 weeks | Pending |
| 4 | Implement constraint validators | 2 weeks | Pending |
| 5 | Build DOE calculator (incremental search) | 2 weeks | Pending |
| 6 | Integrate with voltage/load/RE forecasts | 2 weeks | Pending |
| 7 | Add uncertainty propagation (Monte Carlo) | 2 weeks | Pending |
| 8 | Create API endpoints | 1 week | Pending |
| 9 | Build UI components | 2 weeks | Pending |
| 10 | Integration testing | 2 weeks | Pending |
| 11 | Performance optimization | 1 week | Pending |

**Estimated Total**: 17 weeks (after network model available)

---

## UI Components Required

1. **DOE Dashboard**
   - Real-time limits for all prosumers
   - Color-coded capacity indicators
   - 24-hour forecast timeline

2. **Network Visualization**
   - Topology with DOE overlay
   - Power flow animation
   - Click-to-inspect nodes

3. **Prosumer Portal**
   - Individual DOE limits
   - Optimization recommendations
   - EV charging scheduling

4. **Alerts**
   - DOE violation warnings
   - Curtailment recommendations
   - Fair access indicators

---

## Success Criteria (TOR 7.5.1.6)

| Criterion | Target |
|-----------|--------|
| Violation Rate | < 1% |
| Update Frequency | 5-15 minutes |
| Forecast Horizon | 15min - 48h |
| Confidence | > 95% |
| Computation Time | < 30 sec (all prosumers) |
| Utilization Gain | 10-30% vs static |

---

## Blockers & Risks

### Critical Blocker
- **Network Model Data**: Requires GIS export from กฟภ. system
  - Topology structure
  - Line/cable impedances
  - Transformer ratings
  - Protection settings

### Technical Risks
1. **Scalability**: 300K+ prosumers in real-time
2. **Forecast Accuracy**: Cascading errors from voltage/load predictions
3. **Integration**: SCADA/real-time measurement connectivity

---

## Recommended Actions

1. **Request กฟภ. GIS Data**
   - Formal request to IT department
   - Define data format requirements
   - Establish data refresh schedule

2. **Evaluate Power Flow Solvers**
   - Pandapower (Python, open-source)
   - OpenDSS (industry standard)
   - PyPower (simplified)

3. **Prototype with POC Network**
   - Use existing 7-prosumer model
   - Generate synthetic impedance data
   - Validate methodology

---

*Document Version: 1.0*
*Last Updated: December 6, 2025*
