# DOE Implementation Research Report

**Date**: December 13, 2025
**Purpose**: Technical research for Phase 2b DOE (Dynamic Operating Envelope) implementation

---

## Executive Summary

Dynamic Operating Envelopes (DOEs) provide time-varying export/import limits for Distributed Energy Resources (DERs) based on actual network conditions, enabling 10-30% more DER capacity compared to static limits.

### Key Findings for PEA Implementation

| Aspect | Finding | Implication |
|--------|---------|-------------|
| **Voltage Standard** | Thailand: ±5% (218-242V for 230V) | Stricter than international ±10% |
| **PV Penetration** | 30% baseline without controls | POC at 50-100% capacity needs DOE |
| **With RPC+OLTC** | 50-90% additional capacity | Active control essential |
| **Update Frequency** | 5-15 minutes typical | Align with existing forecast intervals |
| **Recommended Tool** | Pandapower (Python) | Best fit for existing stack |

---

## 1. What is DOE?

A **Dynamic Operating Envelope (DOE)** specifies the available capacity to import/export power for DERs at customer connection points without violating physical and operational network constraints.

**Key Distinction:**
- **Static Operating Envelopes**: Fixed conservative limits (worst-case)
- **Dynamic Operating Envelopes**: Real-time limits (5-30 min intervals) based on actual network conditions

### Core Components

1. **Real Power Bounds** (P_min, P_max): Active power import/export limits
2. **Reactive Power Bounds** (Q_min, Q_max): For voltage support
3. **Time Intervals**: Typically 5-30 minute periods
4. **Constraint Basis**: Voltage limits, thermal limits, operational security

### Benefits

- **Cost-Effective**: Avoid expensive infrastructure upgrades
- **Increased DER Hosting**: 10-30% more capacity than static limits
- **Network Flexibility**: Respond dynamically to changing conditions
- **Voltage/Thermal Management**: Prevent violations before they occur

---

## 2. Global Standards & Implementations

### Australia: ARENA/AEMO (Leading Implementation)

**Project EDGE** (2020-present):
- Collaboration: AusNet Services, AEMO, University of Melbourne
- "Gold Standard" approach with full LV network visibility
- Results: DOE resolved 50-80% of voltage violations

**Key Features:**
- Operating envelopes calculated by DNSPs at customer meter point
- Integration with market mechanisms
- Violation probability < 5% with chance-constrained OPF

### IEEE 1547-2018 Standard

**Key Requirements Enabling DOE:**
1. **Voltage Regulation**: Four control modes (constant PF, volt-VAR, etc.)
2. **Ride-Through**: Category II/III classifications
3. **Interoperability**: Modbus, DNP3, IEEE 2030.5, SunSpec protocols
4. **Abnormal Conditions**: Anti-islanding, frequency ride-through

### European ENTSO-E

- TSO-DSO coordination requirements
- Cooperative voltage and reactive power management
- Smart grid models for demand and generation support

---

## 3. Thailand PEA Grid Context

### Distribution Voltage Levels

- **Medium Voltage (MV)**: 22 kV standard
- **Low Voltage (LV)**: 400V/230V three-phase (50 Hz)
- **Voltage Tolerance**: ±5% (218V-242V) - stricter than international

### Network Topology

- **Radial configuration**: Single source, branching feeders
- **Rural areas**: Overhead lines, longer spans, higher impedance
- **POC Network**: 50 kVA transformer serving 7 prosumers

### Regulatory Context

**Key Bodies:**
- Energy Regulatory Commission (ERC): Tariffs, grid codes
- EGAT: Generation and transmission
- PEA: Distribution in 74 provinces
- MEA: Distribution in Bangkok

**RE Integration Programs:**
- VSPP (Very Small Power Producer): ≤ 10 MW
- SPP (Small Power Producer): 10-90 MW
- Zero Export Controllers required for certain systems

### DER Integration Challenges

**Voltage Rise Issues:**
- Reverse power flow from rooftop solar
- Rural LV networks more severely affected
- End-of-feeder prosumers most vulnerable

**Hosting Capacity (Chiang Mai Case Study):**
- Maximum acceptable PV penetration without mitigation: **30%**
- With combined RPC + OLTC: **50-90% additional possible**

### Similar Projects in Thailand

1. **EGAT Renewable Energy Forecast Centre (REFC)**
   - AI/ML-based solar and wind forecasting
   - 11 additional REFC planned at regional substations

2. **MEA Smart Metro Grid Project**
   - 33,265 household smart meters
   - Two-way data flow enabling dynamic control
   - 1.5 billion baht budget

3. **Mae Hong Son Smart Grid Pilot (2018)**
   - First smart grid pilot in Thailand
   - BESS for renewable integration
   - EGAT + PEA collaboration

---

## 4. Technical Implementation

### Power Flow Calculation Methods

| Network Type | Primary Algorithm | Advantages |
|--------------|-------------------|------------|
| LV Radial Distribution | Forward-Backward Sweep | Fast, stable for unbalanced |
| MV Meshed Distribution | Newton-Raphson | Handles interconnections |
| Unbalanced Networks | Three-Phase Newton | Captures phase variations |
| Optimization (OPF) | AC-OPF (Conic/SOCP) | Optimal resource allocation |

### Newton-Raphson Method (Core Equations)

```
Real Power: P_i = Σ V_i V_k [G_ik cos(θ_i - θ_k) + B_ik sin(θ_i - θ_k)]
Reactive Power: Q_i = Σ V_i V_k [G_ik sin(θ_i - θ_k) - B_ik cos(θ_i - θ_k)]
```

### Voltage Rise Calculation

```
ΔV = (P·R + Q·X) / V_source

Where:
- P: active power (kW)
- Q: reactive power (kVAR)
- R: line resistance (Ω/km)
- X: line reactance (Ω/km)
```

### Thermal Limits

**Typical LV Distribution Cables:**
- 25 mm²: ~50-75A
- 35 mm²: ~65-95A
- 95 mm² (POC): ~200A

**Transformer Loading:**
- Continuous: 80-90% rated capacity
- 4-hour emergency: up to 110%
- 30-minute emergency: up to 120%

### DOE Success Metrics (TOR 7.5.1.6)

| Criterion | Target |
|-----------|--------|
| Violation Rate | < 1% |
| Update Frequency | 5-15 minutes |
| Forecast Horizon | 15min - 48h |
| Confidence | > 95% |
| Computation Time | < 30 sec (all prosumers) |
| Utilization Gain | 10-30% vs static |

---

## 5. Recommended Tools

### Pandapower (RECOMMENDED for PEA)

**Capabilities:**
- AC Power Flow (Newton-Raphson, Gauss-Seidel, Fast-Decoupled)
- Optimal Power Flow (linear and non-linear)
- Three-phase unbalanced analysis
- Python native - easy integration with existing ML stack

**Example:**
```python
import pandapower as pp

# Create network
net = pp.create_empty_network()
pp.create_transformer(net, hv_bus=..., lv_bus=..., sn_mva=0.05, vn_hv_kv=22, vn_lv_kv=0.4)
pp.create_line(net, from_bus=..., to_bus=..., length_km=0.2, std_type="NAYY 4x10")

# Run power flow
pp.runpp(net, max_iteration=20, tolerance_mva=1e-6)

# Get voltage violations
violations = net.res_bus[net.res_bus.vm_pu > 1.05]  # > 105%
```

### OpenDSS
- Comprehensive DER modeling, harmonics analysis
- Python/MATLAB integration
- Best for: Complex distribution networks

### GridLAB-D
- Demand response integration
- Residential load modeling
- Best for: Smart grid simulation

---

## 6. Implementation Roadmap for PEA POC

### Phase 1: Foundation (Current Sprint)

1. **Network Data Schema** ✅ Created (`03-network-model.sql`)
   - Transformers, nodes, branches tables
   - Mock GIS data for 7-prosumer POC network

2. **DOE Calculation Engine** (In Progress)
   - Simplified voltage sensitivity method first
   - Binary search for max export/import
   - 15% safety margin for forecast uncertainty

3. **API Endpoints**
   - `POST /api/v1/doe/calculate` - Single prosumer
   - `POST /api/v1/doe/calculate/batch` - All prosumers
   - `GET /api/v1/doe/limits/{prosumer_id}` - Current limits

### Phase 2: Advanced (Post-POC)

1. **Pandapower Integration**
   - Full AC power flow solver
   - Optimal Power Flow for DOE optimization

2. **Reactive Power Control**
   - P-Q envelopes instead of P only
   - Volt-VAR control integration

3. **Machine Learning Acceleration**
   - Neural network surrogate model
   - < 100 ms evaluation time (1000x faster than OPF)

### Phase 3: Production (After GIS Data)

1. **Real GIS Data Integration**
   - Replace mock data with actual PEA network model
   - Validate against measured voltages

2. **SCADA Integration**
   - Real-time measurements
   - Closed-loop control

---

## 7. POC Network Configuration

### Prosumer Distribution

| Prosumer | Phase | Position | Has PV | Has EV | Voltage Risk |
|----------|-------|----------|--------|--------|--------------|
| prosumer1 | A | 3 (far) | Yes | Yes | HIGH |
| prosumer2 | A | 2 (mid) | Yes | No | MEDIUM |
| prosumer3 | A | 1 (near) | Yes | No | LOW |
| prosumer4 | B | 2 (mid) | Yes | No | MEDIUM |
| prosumer5 | B | 3 (far) | Yes | Yes | HIGH |
| prosumer6 | B | 1 (near) | Yes | No | LOW |
| prosumer7 | C | 1 (near) | Yes | Yes | LOW |

### Key Parameters (Mock GIS Data)

- **Transformer**: 50 kVA, 22kV/0.4kV, 4% impedance
- **Cables**: 95mm² Al, R=0.32 Ω/km, X=0.08 Ω/km, Imax=200A
- **Feeder Length**: 50m per segment (150m total per phase)
- **Voltage Limits**: 218V - 242V (±5% of 230V)

---

## 8. Sources

### Global Standards
- [ARENA - Dynamic Operating Envelopes Workstream](https://arena.gov.au/knowledge-innovation/distributed-energy-integration-program/dynamic-operating-envelopes-workstream/)
- [AEMO Dynamic Operating Envelopes](https://www.aemo.com.au/initiatives/major-programs/nem-distributed-energy-resources-der-program/der-demonstrations/project-edge/project-edge-reports/dynamic-operating-envelopes)
- [IEEE 1547-2018 Standard](https://standards.ieee.org/ieee/1547/5915/)

### Technical Research
- [ScienceDirect - DOE-enabled Demand Response (2024)](https://www.sciencedirect.com/science/article/pii/S0306261924025340)
- [MDPI - Data-Driven DOE Calculation (2025)](https://www.mdpi.com/1996-1073/18/10/2529)
- [IEEE - Allocation of DOE in Distribution Networks](https://ieeexplore.ieee.org/document/10123018/)
- [ScienceDirect - Network-aware Control under DOE Framework](https://www.sciencedirect.com/science/article/pii/S1364032125003697)

### Thailand Context
- [Provincial Electricity Authority (PEA)](https://www.pea.co.th/en)
- [PV Hosting Capacity in Chiang Mai - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2352484719311230)
- [EGAT Smart Grid Roadmap](https://www.enlit-asia.com/interview-series/egats-roadmap-drive-energy-transition-thailand)
- [MEA Smart Metro Grid](https://www.bangkokpost.com/thailand/pr/1839829/mea-injects-billions-into-smart-metro-grid-system)

### Tools
- [Pandapower Documentation](https://pandapower.readthedocs.io/)
- [OpenDSS - EPRI](https://opendss.epri.com/)

---

*Document Version: 1.0.0*
*Created: December 13, 2025*
