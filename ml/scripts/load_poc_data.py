#!/usr/bin/env python3
"""
POC Data Loading Script for PEA RE Forecast Platform.

This script:
1. Loads POC Data.xlsx as reference data
2. Generates 1 year of simulated data for ML training
3. Loads data into TimescaleDB

Usage:
    python scripts/load_poc_data.py --mode poc       # Load POC data only
    python scripts/load_poc_data.py --mode simulate  # Generate simulation data
    python scripts/load_poc_data.py --mode all       # Both POC + simulation
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pea_forecast"
)

POC_DATA_PATH = Path(__file__).parent.parent.parent / "requirements" / "POC Data.xlsx"

# Prosumer configuration from TOR
PROSUMERS = {
    "prosumer1": {"phase": "A", "position": 3, "has_ev": True},
    "prosumer2": {"phase": "A", "position": 2, "has_ev": False},
    "prosumer3": {"phase": "A", "position": 1, "has_ev": False},
    "prosumer4": {"phase": "B", "position": 2, "has_ev": False},
    "prosumer5": {"phase": "B", "position": 3, "has_ev": True},
    "prosumer6": {"phase": "B", "position": 1, "has_ev": False},
    "prosumer7": {"phase": "C", "position": 1, "has_ev": True},
}


def load_poc_solar_data(engine) -> int:
    """Load POC solar data from Excel into TimescaleDB."""
    print("\n📊 Loading POC Solar Data...")

    df = pd.read_excel(POC_DATA_PATH, sheet_name="Solar", header=2, usecols="B:I")
    df.columns = ["timestamp", "pvtemp1", "pvtemp2", "ambtemp", "pyrano1", "pyrano2", "windspeed", "power_kw"]
    df = df.dropna(how="all")

    # Add date (use a reference date since POC only has time)
    base_date = datetime(2024, 6, 15)  # Mid-year date for Thailand
    df["time"] = df["timestamp"].apply(
        lambda t: base_date + timedelta(hours=t.hour, minutes=t.minute, seconds=t.second) if pd.notna(t) else None
    )
    df["station_id"] = "POC_STATION_1"

    # Select columns for DB
    db_cols = ["time", "station_id", "pvtemp1", "pvtemp2", "ambtemp", "pyrano1", "pyrano2", "windspeed", "power_kw"]
    df_db = df[db_cols].dropna(subset=["time"])

    # Insert to DB
    df_db.to_sql("solar_measurements", engine, if_exists="append", index=False, method="multi")

    print(f"   ✅ Loaded {len(df_db)} solar records")
    return len(df_db)


def load_poc_1phase_data(engine) -> int:
    """Load POC 1-phase data from Excel into TimescaleDB."""
    print("\n📊 Loading POC 1-Phase Data...")

    df = pd.read_excel(POC_DATA_PATH, sheet_name="1 Phase", header=2, usecols="B:H")
    df.columns = [
        "timestamp", "active_power", "energy_meter_active_power", "energy_meter_current",
        "energy_meter_reactive_power", "energy_meter_voltage", "reactive_power"
    ]
    df = df.dropna(how="all")

    # Add date and prosumer_id (POC data is for prosumer1)
    base_date = datetime(2024, 6, 15)
    df["time"] = df["timestamp"].apply(
        lambda t: base_date + timedelta(hours=t.hour, minutes=t.minute, seconds=t.second) if pd.notna(t) else None
    )
    df["prosumer_id"] = "prosumer1"

    # Select columns for DB
    db_cols = [
        "time", "prosumer_id", "active_power", "reactive_power",
        "energy_meter_active_power", "energy_meter_current",
        "energy_meter_voltage", "energy_meter_reactive_power"
    ]
    df_db = df[db_cols].dropna(subset=["time"])

    # Insert to DB
    df_db.to_sql("single_phase_meters", engine, if_exists="append", index=False, method="multi")

    print(f"   ✅ Loaded {len(df_db)} 1-phase records")
    return len(df_db)


def load_poc_3phase_data(engine) -> int:
    """Load POC 3-phase data from Excel into TimescaleDB."""
    print("\n📊 Loading POC 3-Phase Data...")

    df = pd.read_excel(POC_DATA_PATH, sheet_name="3 Phase", header=2, usecols="A:N")
    df.columns = [
        "timestamp", "p1_amp", "p1_volt", "p1_w", "p2_amp", "p2_volt", "p2_w",
        "p3_amp", "p3_volt", "p3_w", "q1_var", "q2_var", "q3_var", "total_w"
    ]
    df = df.dropna(how="all")

    # Add date and meter_id
    base_date = datetime(2024, 6, 15)
    df["time"] = df["timestamp"].apply(
        lambda t: base_date + timedelta(hours=t.hour, minutes=t.minute, seconds=t.second) if pd.notna(t) else None
    )
    df["meter_id"] = "TX_METER_01"

    # Select columns for DB
    db_cols = [
        "time", "meter_id", "p1_amp", "p1_volt", "p1_w",
        "p2_amp", "p2_volt", "p2_w", "p3_amp", "p3_volt", "p3_w",
        "q1_var", "q2_var", "q3_var", "total_w"
    ]
    df_db = df[db_cols].dropna(subset=["time"])

    # Insert to DB
    df_db.to_sql("three_phase_meters", engine, if_exists="append", index=False, method="multi")

    print(f"   ✅ Loaded {len(df_db)} 3-phase records")
    return len(df_db)


def generate_solar_simulation(engine, days: int = 365) -> int:
    """
    Generate simulated solar data for ML training.

    Based on Thailand solar patterns:
    - Peak irradiance: ~1000 W/m² at noon
    - Sunrise: ~6:00, Sunset: ~18:00
    - Seasonal variation: ±10%
    - Random cloud cover effects
    """
    print(f"\n🌞 Generating {days} days of solar simulation data...")

    np.random.seed(42)
    start_date = datetime(2024, 1, 1)
    records = []

    for day in range(days):
        current_date = start_date + timedelta(days=day)
        day_of_year = current_date.timetuple().tm_yday

        # Seasonal factor (Thailand has mild seasons)
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * (day_of_year - 80) / 365)

        # Cloud cover factor for the day (random)
        cloud_base = np.random.uniform(0.7, 1.0)

        # Generate 5-minute intervals
        for minute in range(0, 1440, 5):
            hour = minute / 60
            timestamp = current_date + timedelta(minutes=minute)

            # Solar irradiance model (sunrise at 6, sunset at 18)
            if 6 <= hour <= 18:
                # Gaussian-like curve centered at noon
                hour_factor = np.exp(-0.5 * ((hour - 12) / 2.5) ** 2)

                # Add random cloud effects
                cloud_factor = cloud_base * np.random.uniform(0.8, 1.0)

                # Base irradiance
                irradiance = 1000 * hour_factor * seasonal_factor * cloud_factor
                irradiance = max(0, irradiance + np.random.normal(0, 20))
            else:
                irradiance = 0

            # Temperature model
            # Ambient temp: 25-35°C with daily cycle
            ambtemp = 30 + 5 * np.sin(2 * np.pi * (hour - 6) / 24) + np.random.normal(0, 1)

            # PV panel temp: higher than ambient when sun is up
            pvtemp_delta = 0.03 * irradiance + np.random.normal(0, 2)
            pvtemp1 = ambtemp + pvtemp_delta
            pvtemp2 = ambtemp + pvtemp_delta + np.random.normal(0, 1)

            # Wind speed: 0-5 m/s typically
            windspeed = abs(np.random.normal(1.5, 1.0))

            # Power output model
            # Base conversion efficiency ~16%, degraded by temperature
            if irradiance > 0:
                temp_factor = 1 - 0.004 * max(0, (pvtemp1 + pvtemp2) / 2 - 25)
                # 5 kW system assumed
                power_kw = 5.0 * (irradiance / 1000) * 0.16 * temp_factor * 1000
                power_kw = max(0, power_kw + np.random.normal(0, 50))
            else:
                power_kw = 0

            records.append({
                "time": timestamp,
                "station_id": "POC_STATION_1",
                "pvtemp1": round(pvtemp1, 2),
                "pvtemp2": round(pvtemp2, 2),
                "ambtemp": round(ambtemp, 2),
                "pyrano1": round(irradiance, 2),
                "pyrano2": round(irradiance + np.random.normal(0, 10), 2),
                "windspeed": round(windspeed, 2),
                "power_kw": round(power_kw, 2),
            })

    # Convert to DataFrame and insert
    df = pd.DataFrame(records)

    # Insert in chunks to avoid memory issues
    chunk_size = 10000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        chunk.to_sql("solar_measurements", engine, if_exists="append", index=False, method="multi")
        print(f"   Inserted {min(i+chunk_size, len(df))}/{len(df)} records...")

    print(f"   ✅ Generated {len(df)} solar simulation records")
    return len(df)


def generate_voltage_simulation(engine, days: int = 365) -> int:
    """
    Generate simulated voltage data for all 7 prosumers.

    Voltage characteristics:
    - Nominal: 230V (single-phase)
    - Acceptable range: 218V - 242V (±5%)
    - Variations based on:
      - Time of day (load patterns)
      - PV generation (reverse power flow)
      - Position from transformer
      - EV charging
    """
    print(f"\n⚡ Generating {days} days of voltage simulation data...")

    np.random.seed(43)
    start_date = datetime(2024, 1, 1)
    records = []

    for day in range(days):
        current_date = start_date + timedelta(days=day)
        is_weekday = current_date.weekday() < 5

        for minute in range(0, 1440, 5):
            hour = minute / 60
            timestamp = current_date + timedelta(minutes=minute)

            # Base voltage at transformer
            base_voltage = 230.0 + np.random.normal(0, 1)

            # Load factor by time of day
            if is_weekday:
                # Morning peak (7-9), evening peak (18-21)
                if 7 <= hour <= 9:
                    load_factor = 1.2
                elif 18 <= hour <= 21:
                    load_factor = 1.4
                elif 0 <= hour <= 6:
                    load_factor = 0.6
                else:
                    load_factor = 1.0
            else:
                # Weekend: more uniform load
                if 10 <= hour <= 20:
                    load_factor = 1.1
                else:
                    load_factor = 0.7

            # PV generation factor (raises voltage during day)
            if 9 <= hour <= 15:
                pv_factor = 0.5 * np.sin(np.pi * (hour - 9) / 6)
            else:
                pv_factor = 0

            for prosumer_id, config in PROSUMERS.items():
                phase = config["phase"]
                position = config["position"]
                has_ev = config["has_ev"]

                # Voltage drop based on position (farther = lower voltage)
                voltage_drop = position * 1.5 * load_factor

                # PV boost (reverse power flow raises voltage)
                pv_boost = pv_factor * (4 - position)  # More effect at end of line

                # EV charging effect (drops voltage when charging)
                ev_effect = 0
                if has_ev and 18 <= hour <= 23:
                    ev_charging_prob = 0.3  # 30% chance of EV charging
                    if np.random.random() < ev_charging_prob:
                        ev_effect = -3.0

                # Phase-specific variation
                phase_offset = {"A": 0, "B": -0.5, "C": 0.5}[phase]

                # Calculate final voltage
                voltage = (
                    base_voltage
                    - voltage_drop
                    + pv_boost
                    + ev_effect
                    + phase_offset
                    + np.random.normal(0, 0.5)
                )

                # Calculate associated electrical values
                current = load_factor * 5 + np.random.normal(0, 0.5)
                active_power = voltage * current / 1000  # kW
                reactive_power = active_power * 0.1 * np.random.uniform(0.8, 1.2)

                records.append({
                    "time": timestamp,
                    "prosumer_id": prosumer_id,
                    "active_power": round(active_power, 2),
                    "reactive_power": round(reactive_power, 2),
                    "energy_meter_active_power": round(active_power, 2),
                    "energy_meter_current": round(current, 2),
                    "energy_meter_voltage": round(voltage, 2),
                    "energy_meter_reactive_power": round(reactive_power, 2),
                })

    # Convert to DataFrame and insert
    df = pd.DataFrame(records)

    # Insert in chunks
    chunk_size = 50000
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        chunk.to_sql("single_phase_meters", engine, if_exists="append", index=False, method="multi")
        print(f"   Inserted {min(i+chunk_size, len(df))}/{len(df)} records...")

    print(f"   ✅ Generated {len(df)} voltage simulation records")
    return len(df)


def clear_existing_data(engine):
    """Clear existing data from tables (for fresh start)."""
    print("\n🗑️  Clearing existing data...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE solar_measurements CASCADE"))
        conn.execute(text("TRUNCATE single_phase_meters CASCADE"))
        conn.execute(text("TRUNCATE three_phase_meters CASCADE"))
        conn.commit()
    print("   ✅ Data cleared")


def verify_data(engine):
    """Verify loaded data."""
    print("\n📋 Data Verification:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM solar_measurements"))
        solar_count = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM single_phase_meters"))
        voltage_count = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM three_phase_meters"))
        three_phase_count = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM prosumers"))
        prosumer_count = result.scalar()

    print(f"   Solar measurements: {solar_count:,} records")
    print(f"   Voltage measurements: {voltage_count:,} records")
    print(f"   3-Phase measurements: {three_phase_count:,} records")
    print(f"   Prosumers: {prosumer_count} records")


def main():
    parser = argparse.ArgumentParser(description="Load POC data and generate simulations")
    parser.add_argument(
        "--mode",
        choices=["poc", "simulate", "all"],
        default="all",
        help="Loading mode: poc (POC data only), simulate (simulation only), all (both)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Number of days to simulate (default: 365)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before loading"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("PEA RE Forecast Platform - Data Loading Script")
    print("=" * 70)
    print(f"Mode: {args.mode}")
    print(f"Database: {DATABASE_URL}")

    # Create database engine
    engine = create_engine(DATABASE_URL)

    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Clear data if requested
    if args.clear:
        clear_existing_data(engine)

    # Load data based on mode
    if args.mode in ["poc", "all"]:
        if POC_DATA_PATH.exists():
            load_poc_solar_data(engine)
            load_poc_1phase_data(engine)
            load_poc_3phase_data(engine)
        else:
            print(f"⚠️  POC Data not found at: {POC_DATA_PATH}")

    if args.mode in ["simulate", "all"]:
        generate_solar_simulation(engine, days=args.days)
        generate_voltage_simulation(engine, days=args.days)

    # Verify loaded data
    verify_data(engine)

    print("\n" + "=" * 70)
    print("✅ Data loading complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
