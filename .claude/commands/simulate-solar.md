# Generate Solar Simulation Data

You are a renewable energy data simulation expert for the PEA RE Forecast Platform.

## Task
Generate realistic solar power generation simulation data for Thailand conditions.

## Context
- Location: Thailand (13-20°N latitude)
- Climate: Tropical monsoon
- Peak sun hours: 4-5 hours/day average
- Rainy season: May-October
- Dry season: November-April

## Instructions

1. **Research Latest Libraries**:
   - Check pvlib (latest version) for solar modeling
   - Check pandas, numpy versions
   - Verify Thailand TMY (Typical Meteorological Year) data availability

2. **Generate Realistic Data**:
   - Solar irradiance (GHI, DNI, DHI) with cloud cover effects
   - Panel temperature based on ambient + irradiance
   - Wind speed variations
   - Power output using PV system model

3. **Validation Criteria**:
   - MAPE patterns should be achievable < 10%
   - Daily/seasonal patterns must be realistic for Thailand
   - Include weather anomalies (storms, haze from burning season)

4. **Output**:
   - Python script at `ml/scripts/generate_solar_data.py`
   - Sample dataset at `ml/data/simulated/solar_simulation.parquet`
   - Documentation at `docs/data-dictionary/solar-simulation-methodology.md`

5. **Test Locally**:
   - Run in Docker container
   - Validate output statistics
   - Ensure reproducibility with seed

## Thailand Solar Characteristics

| Month | Avg GHI (kWh/m²/day) | Cloud Cover |
|-------|---------------------|-------------|
| Jan   | 5.2                 | Low         |
| Feb   | 5.5                 | Low         |
| Mar   | 5.8                 | Low         |
| Apr   | 5.6                 | Medium      |
| May   | 4.8                 | High        |
| Jun   | 4.5                 | High        |
| Jul   | 4.3                 | High        |
| Aug   | 4.2                 | High        |
| Sep   | 4.4                 | High        |
| Oct   | 4.6                 | Medium      |
| Nov   | 5.0                 | Low         |
| Dec   | 5.1                 | Low         |
