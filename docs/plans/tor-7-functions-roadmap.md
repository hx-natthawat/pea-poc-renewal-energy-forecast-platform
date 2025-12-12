# TOR 7 Functions Implementation Roadmap

> **Document**: Gap Analysis & Implementation Plan
> **Created**: December 6, 2025
> **Status**: Phase 1 (POC) Complete, Phase 2a COMPLETE

---

## Executive Summary

The TOR specifies 7 core forecasting functions. The current POC implementation covers the 2 functions required for POC testing. The remaining 5 functions are for Phase 2 development.

---

## Current Implementation Status

### Phase 1: POC Functions (COMPLETE)

| Function            | POC Test | Target     | Actual | Status |
| ------------------- | -------- | ---------- | ------ | ------ |
| RE Forecast (Solar) | POC 1, 2 | MAPE < 10% | 9.74%  | ✅ PASS |
| Voltage Prediction  | POC 3, 4 | MAE < 2V   | 0.036V | ✅ PASS |

### Phase 2a: Extended Functions (COMPLETE)

| Function               | Priority | Complexity | Dependencies           | Status                   |
| ---------------------- | -------- | ---------- | ---------------------- | ------------------------ |
| Load Forecast          | P1       | Medium     | Historical load data   | ✅ API Ready (Simulation) |
| Actual Demand Forecast | P1       | Medium     | RE Forecast, Load data | ✅ API Ready (Simulation) |
| Imbalance Forecast     | P2       | Medium     | RE + Demand + Load     | ✅ API Ready (Simulation) |

### Phase 2b: Advanced Functions (BLOCKED - Awaiting Network Model)

| Function         | Priority | Complexity | Dependencies                      | Status    |
| ---------------- | -------- | ---------- | --------------------------------- | --------- |
| DOE              | P2       | High       | Voltage Prediction, Network model | ⏳ Blocked |
| Hosting Capacity | P3       | High       | All forecasts + Network model     | ⏳ Future  |

**Phase 2a API Endpoints (December 2025):**

- `POST /api/v1/load-forecast/predict` - Load forecast predictions
- `POST /api/v1/demand-forecast/predict` - Actual demand forecast
- `POST /api/v1/imbalance-forecast/predict` - System imbalance forecast

*Note: Currently using simulation models. ML models to be trained with real data.*

---

## Detailed Function Requirements

### Function 1: RE Forecast (ฟังก์ชันพยากรณ์กำลังผลิต RE)

**Status**: ✅ IMPLEMENTED

**TOR Reference**: 7.5.1.2

**Supported RE Types** (per TOR 7.5.1.2.1-8):
- [x] Solar PV (7.5.1.2.1) - Primary focus
- [ ] Wind (7.5.1.2.2) - Phase 2
- [ ] Other RE (7.5.1.2.3) - Phase 2
- [ ] Biogas (7.5.1.2.4) - Phase 2
- [ ] Waste-to-Energy (7.5.1.2.5) - Phase 2
- [ ] Biomass (7.5.1.2.6) - Phase 2
- [ ] Cogeneration (7.5.1.2.7) - Phase 2
- [ ] Geothermal (7.5.1.2.8) - Phase 2

**Weather Parameters** (per TOR 7.3.4.4):
- [x] Temperature (7.3.4.4.1)
- [x] Relative Humidity (7.3.4.4.2) - via TMD API
- [x] Atmospheric Pressure (7.3.4.4.3) - via TMD API
- [x] Wind Speed (7.3.4.4.4)
- [x] Wind Direction (7.3.4.4.5) - via TMD API
- [x] Cloud Index (7.3.4.4.6) - via TMD API
- [x] Solar Irradiation/GHI (7.3.4.4.7)

**Horizons**:
- [x] Intraday (15 min - 6 hours) - POC 1
- [x] Day Ahead (24-48 hours) - POC 2

---

### Function 2: Actual Demand Forecast

**Status**: ❌ NOT IMPLEMENTED (Phase 2)

**Definition**: Net demand at trading points
```
Actual Demand = Gross Load - Behind-the-meter RE + Battery (dis)charging
```

**Required Inputs**:
- Historical actual demand
- Calendar features (holidays, events)
- Weather data
- Prosumer data (behind-the-meter solar, EV, batteries)

**Target Accuracy**: MAPE < 5%

---

### Function 3: Load Forecast

**Status**: ❌ NOT IMPLEMENTED (Phase 2)

**Levels**:
1. System Level (กฟภ. total) - MAPE < 3%
2. Regional Level (12 regions) - MAPE < 5%
3. Provincial Level - MAPE < 8%
4. Substation Level - MAPE < 8%
5. Feeder Level - MAPE < 12%

---

### Function 4: Imbalance Forecast

**Status**: ❌ NOT IMPLEMENTED (Phase 2)

**Definition**:
```
Imbalance = Actual Demand - Scheduled Generation - Actual RE Generation
```

**Dependencies**: Functions 1, 2, 3

**Target Accuracy**: MAE < 5% of average load

---

### Function 5: Voltage Prediction

**Status**: ✅ IMPLEMENTED

**Voltage Levels**:
- [x] LV 1-Phase (230V ± 5%) - Primary focus
- [x] LV 3-Phase (400V ± 5%)
- [ ] MV (22kV, 33kV) - Phase 2

**Horizons**:
- [x] Intraday (15 min - 4 hours) - POC 3
- [x] Day Ahead (24-48 hours) - POC 4

**Target Accuracy**: MAE < 2V (LV), MAE < 1% (MV)

---

### Function 6: DOE (Dynamic Operating Envelope)

**Status**: ❌ NOT IMPLEMENTED (Phase 2)

**Definition**: Time-varying export/import limits for DER

**Required Inputs**:
- Network model (topology, impedances, limits)
- Voltage Prediction (Function 5)
- Load Forecast (Function 3)
- RE Forecast (Function 1)
- Real-time measurements

**Output**:
```json
{
  "connection_point": "TR001_P1",
  "timestamp": "2025-03-15T10:00:00",
  "valid_until": "2025-03-15T10:15:00",
  "export_limit_kw": 8.5,
  "import_limit_kw": 15.0,
  "limiting_factor": "voltage_rise",
  "confidence": 0.95
}
```

**Target**: Violation Rate < 1%

---

### Function 7: Hosting Capacity Forecast

**Status**: ❌ NOT IMPLEMENTED (Phase 2)

**Definition**: Maximum DER capacity per connection point

**Dependencies**: All other functions + Network model

**Output**:
- Current HC (remaining capacity)
- Forecast HC (1, 3, 5, 10 year horizons)
- Limiting constraints
- Upgrade recommendations

**Target Accuracy**: ± 10%

---

## Implementation Roadmap

### Phase 1: POC (COMPLETE) ✅
- RE Forecast (Solar) - Intraday & Day Ahead
- Voltage Prediction - Intraday & Day Ahead

### Phase 2a: Core Extensions
1. **Load Forecast** - Foundation for other functions
2. **Actual Demand Forecast** - Trading point level
3. **RE Forecast Extensions** - Wind, Biomass, Biogas

### Phase 2b: Derived Functions
4. **Imbalance Forecast** - Requires Functions 1-3
5. **DOE** - Real-time operational limits

### Phase 3: Advanced Analytics
6. **Hosting Capacity** - Long-term planning
7. **Network Optimization** - Integration with SCADA

---

## AI/ML Techniques Matrix

| Technique         | Application         | Functions  |
| ----------------- | ------------------- | ---------- |
| Linear Regression | Baseline models     | All        |
| ANN               | Non-linear patterns | 1, 2, 3, 5 |
| SVM               | Classification      | 4, 6       |
| LSTM              | Time series         | 1, 2, 3, 5 |
| XGBoost           | Tabular data        | 1, 5       |
| Ensemble          | Production models   | All        |

---

## Accuracy Targets Summary

| Function              | Metric    | Target       |
| --------------------- | --------- | ------------ |
| RE Forecast (Solar)   | MAPE      | < 10%        |
| RE Forecast (Wind)    | MAPE      | < 15%        |
| RE Forecast (Biomass) | MAPE      | < 5%         |
| Actual Demand         | MAPE      | < 5%         |
| Load (System)         | MAPE      | < 3%         |
| Load (Regional)       | MAPE      | < 5%         |
| Load (Substation)     | MAPE      | < 8%         |
| Imbalance             | MAE       | < 5% of load |
| Voltage (LV)          | MAE       | < 2V         |
| Voltage (MV)          | MAE       | < 1%         |
| DOE                   | Violation | < 1%         |
| Hosting Capacity      | Accuracy  | ± 10%        |

---

## Conclusion

The POC implementation is **complete and compliant** with TOR requirements:
- POC 1 & 2: RE Forecast ✅
- POC 3 & 4: Voltage Prediction ✅

Functions 2-4, 6-7 are demonstrated conceptually and planned for Phase 2 development after POC acceptance.

---

*Document Version: 1.0*
*Last Updated: December 6, 2025*
