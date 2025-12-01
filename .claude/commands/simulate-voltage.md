# Generate Voltage Simulation Data

You are a power systems simulation expert for the PEA RE Forecast Platform.

## Task
Generate realistic low-voltage distribution network simulation data.

## Context
- Network: 22kV/400V distribution transformer (50 kVA)
- Prosumers: 7 households with solar PV
- Phases: 3-phase, 4-wire system
- Voltage nominal: 230V single-phase, 400V three-phase
- Voltage limits: ±5% (218V - 242V)

## Instructions

1. **Research Latest Libraries**:
   - Check pandapower (latest) for power flow simulation
   - Check OpenDSS Python interface
   - Verify IEEE test case compatibility

2. **Network Modeling**:
   - Model transformer impedance
   - Model line impedances per phase
   - Include prosumer load profiles (Thai residential patterns)
   - Include PV generation profiles (from solar simulation)
   - Include EV charging patterns

3. **Simulation Scenarios**:
   - Normal operation (voltage within limits)
   - High PV penetration (overvoltage at feeder end)
   - Peak load (undervoltage conditions)
   - Unbalanced loading (phase imbalance)

4. **Output**:
   - Python script at `ml/scripts/generate_voltage_data.py`
   - Sample dataset at `ml/data/simulated/voltage_simulation.parquet`
   - Documentation at `docs/data-dictionary/voltage-simulation-methodology.md`

5. **Validation**:
   - Voltage profiles must be physically realistic
   - Phase relationships must be correct (120° apart)
   - Power flow must balance at transformer

## Thai Residential Load Profile

| Hour | Load Factor | Description |
|------|-------------|-------------|
| 0-6  | 0.3-0.4     | Night (AC, refrigerator) |
| 7-8  | 0.6-0.7     | Morning peak |
| 9-11 | 0.4-0.5     | Work hours |
| 12-13| 0.5-0.6     | Lunch |
| 14-17| 0.4-0.5     | Afternoon |
| 18-21| 0.8-1.0     | Evening peak |
| 22-24| 0.5-0.6     | Late evening |
