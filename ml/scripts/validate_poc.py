#!/usr/bin/env python3
"""
POC Model Validation Script for PEA RE Forecast Platform.

Validates trained models against TOR accuracy requirements:
- POC 1 & 2: Solar MAPE < 10%
- POC 3 & 4: Voltage MAE < 2V

Usage:
    python scripts/validate_poc.py
    python scripts/validate_poc.py --solar-only
    python scripts/validate_poc.py --voltage-only
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sqlalchemy import create_engine, text

# Add src to path for feature engineers
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Try importing feature engineers
try:
    from features.solar_features import SolarFeatureEngineer
    from features.voltage_features import VoltageFeatureEngineer
except ImportError:
    # Fallback: define inline if not available
    SolarFeatureEngineer = None
    VoltageFeatureEngineer = None

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pea_forecast"
)

# TOR Requirements
TOR_SOLAR_MAPE = 10.0  # %
TOR_SOLAR_RMSE = 100.0  # kW
TOR_SOLAR_R2 = 0.95
TOR_VOLTAGE_MAE = 2.0  # V


def create_solar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features for solar prediction."""
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])

    # Temporal features
    df["hour"] = df["time"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["is_peak_hour"] = df["hour"].between(10, 14).astype(int)

    # Derived features
    df["pyrano_avg"] = (df["pyrano1"] + df["pyrano2"]) / 2
    df["pvtemp_avg"] = (df["pvtemp1"] + df["pvtemp2"]) / 2
    df["temp_delta"] = df["pvtemp_avg"] - df["ambtemp"]

    return df


def create_voltage_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features for voltage prediction."""
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])

    # Temporal features
    df["hour"] = df["time"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["is_weekday"] = df["time"].dt.dayofweek < 5

    # Load features
    df["apparent_power"] = np.sqrt(
        df["active_power"] ** 2 + df["reactive_power"].fillna(0) ** 2
    )
    df["power_factor"] = df["active_power"] / (df["apparent_power"] + 0.001)

    return df


def validate_solar_model(engine, model_path: Path) -> tuple[bool, dict]:
    """Validate solar model against TOR requirements."""
    print("\n" + "=" * 60)
    print("🌞 SOLAR MODEL VALIDATION (POC 1 & 2)")
    print("=" * 60)

    # Load data
    query = text("""
        SELECT time, pyrano1, pyrano2, pvtemp1, pvtemp2, ambtemp, windspeed, power_kw
        FROM solar_measurements
        WHERE station_id = 'POC_STATION_1'
          AND power_kw > 10
          AND pyrano1 > 50
        ORDER BY time ASC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if len(df) < 50:
        print(f"❌ Insufficient data: {len(df)} records (need 50+)")
        return False, {"error": "insufficient_data", "count": len(df)}

    print(f"📊 Data loaded: {len(df):,} records")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
    print(f"   Power range: {df['power_kw'].min():.1f} - {df['power_kw'].max():.1f} kW")

    # Load model
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return False, {"error": "model_not_found"}

    model = joblib.load(model_path)
    print(f"✅ Model loaded: {model_path.name}")

    # Feature engineering
    if SolarFeatureEngineer:
        fe = SolarFeatureEngineer()
        df_feat = fe.transform(df.copy())
        feature_cols = fe.get_feature_columns()
    else:
        df_feat = create_solar_features(df)
        feature_cols = [
            "pyrano1",
            "pyrano2",
            "pyrano_avg",
            "pvtemp1",
            "pvtemp2",
            "pvtemp_avg",
            "ambtemp",
            "temp_delta",
            "windspeed",
            "hour_sin",
            "hour_cos",
            "is_peak_hour",
        ]

    df_feat = df_feat.dropna(subset=feature_cols + ["power_kw"])

    # Ensure features exist
    available_features = [c for c in feature_cols if c in df_feat.columns]
    X = df_feat[available_features]
    y_true = df_feat["power_kw"]

    print(f"   Features used: {len(available_features)}")

    # Predict
    try:
        y_pred = model.predict(X)
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False, {"error": str(e)}

    # Calculate metrics
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    metrics = {"mape": mape, "rmse": rmse, "mae": mae, "r2": r2, "n_samples": len(y_true)}

    # Results
    print(f"\n📈 RESULTS:")
    print(f"   MAPE:     {mape:.2f}% (Target: < {TOR_SOLAR_MAPE}%)")
    print(f"   RMSE:     {rmse:.2f} kW (Target: < {TOR_SOLAR_RMSE} kW)")
    print(f"   MAE:      {mae:.2f} kW")
    print(f"   R²:       {r2:.4f} (Target: > {TOR_SOLAR_R2})")
    print(f"   Samples:  {len(y_true):,}")

    passed = mape < TOR_SOLAR_MAPE
    if passed:
        print(f"\n✅ POC 1 & 2: PASS - MAPE {mape:.2f}% < {TOR_SOLAR_MAPE}%")
    else:
        print(f"\n❌ POC 1 & 2: FAIL - MAPE {mape:.2f}% >= {TOR_SOLAR_MAPE}%")

    return passed, metrics


def validate_voltage_model(engine, model_path: Path) -> tuple[bool, dict]:
    """Validate voltage model against TOR requirements."""
    print("\n" + "=" * 60)
    print("⚡ VOLTAGE MODEL VALIDATION (POC 3 & 4)")
    print("=" * 60)

    # Load data
    query = text("""
        SELECT time, prosumer_id, active_power, reactive_power,
               energy_meter_current, energy_meter_voltage
        FROM single_phase_meters
        WHERE energy_meter_voltage IS NOT NULL
          AND energy_meter_voltage BETWEEN 200 AND 260
        ORDER BY time ASC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if len(df) < 50:
        print(f"❌ Insufficient data: {len(df)} records (need 50+)")
        return False, {"error": "insufficient_data", "count": len(df)}

    print(f"📊 Data loaded: {len(df):,} records")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
    print(
        f"   Voltage range: {df['energy_meter_voltage'].min():.1f}V - {df['energy_meter_voltage'].max():.1f}V"
    )
    print(f"   Prosumers: {df['prosumer_id'].nunique()}")

    # Load model
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        return False, {"error": "model_not_found"}

    model = joblib.load(model_path)
    print(f"✅ Model loaded: {model_path.name}")

    # Feature engineering
    if VoltageFeatureEngineer:
        fe = VoltageFeatureEngineer()
        df_feat = fe.transform(df.copy())
        feature_cols = fe.get_feature_columns()
    else:
        df_feat = create_voltage_features(df)
        feature_cols = [
            "active_power",
            "reactive_power",
            "energy_meter_current",
            "hour_sin",
            "hour_cos",
            "apparent_power",
            "power_factor",
        ]

    df_feat = df_feat.dropna(subset=["energy_meter_voltage"])

    # Ensure features exist
    available_features = [c for c in feature_cols if c in df_feat.columns]
    X = df_feat[available_features].fillna(0)
    y_true = df_feat["energy_meter_voltage"]

    print(f"   Features used: {len(available_features)}")

    # Predict
    try:
        y_pred = model.predict(X)
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False, {"error": str(e)}

    # Calculate metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    r2 = r2_score(y_true, y_pred)

    metrics = {"mae": mae, "rmse": rmse, "mape": mape, "r2": r2, "n_samples": len(y_true)}

    # Results
    print(f"\n📈 RESULTS:")
    print(f"   MAE:      {mae:.4f} V (Target: < {TOR_VOLTAGE_MAE} V)")
    print(f"   RMSE:     {rmse:.4f} V")
    print(f"   MAPE:     {mape:.2f}%")
    print(f"   R²:       {r2:.4f}")
    print(f"   Samples:  {len(y_true):,}")

    passed = mae < TOR_VOLTAGE_MAE
    if passed:
        print(f"\n✅ POC 3 & 4: PASS - MAE {mae:.4f}V < {TOR_VOLTAGE_MAE}V")
    else:
        print(f"\n❌ POC 3 & 4: FAIL - MAE {mae:.4f}V >= {TOR_VOLTAGE_MAE}V")

    return passed, metrics


def main():
    parser = argparse.ArgumentParser(description="Validate POC models against TOR requirements")
    parser.add_argument("--solar-only", action="store_true", help="Validate solar model only")
    parser.add_argument("--voltage-only", action="store_true", help="Validate voltage model only")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🔬 PEA RE FORECAST PLATFORM - POC VALIDATION")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Database: {DATABASE_URL.split('@')[-1]}")
    print("=" * 60)

    # Create database engine
    engine = create_engine(DATABASE_URL)

    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Model paths
    models_dir = Path(__file__).parent.parent / "models"
    solar_model_path = models_dir / "solar_model.joblib"
    voltage_model_path = models_dir / "voltage_model.joblib"

    results = {
        "timestamp": datetime.now().isoformat(),
        "database": DATABASE_URL.split("@")[-1],
        "solar": None,
        "voltage": None,
        "overall_passed": False,
    }

    # Validate models
    solar_passed = True
    voltage_passed = True

    if not args.voltage_only:
        solar_passed, solar_metrics = validate_solar_model(engine, solar_model_path)
        results["solar"] = {"passed": solar_passed, "metrics": solar_metrics}

    if not args.solar_only:
        voltage_passed, voltage_metrics = validate_voltage_model(engine, voltage_model_path)
        results["voltage"] = {"passed": voltage_passed, "metrics": voltage_metrics}

    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL POC VALIDATION SUMMARY")
    print("=" * 60)

    if not args.voltage_only:
        status = "✅ PASS" if solar_passed else "❌ FAIL"
        print(f"   POC 1 (RE Intraday):     {status}")
        print(f"   POC 2 (RE Day-Ahead):    {status}")

    if not args.solar_only:
        status = "✅ PASS" if voltage_passed else "❌ FAIL"
        print(f"   POC 3 (Voltage Intra):   {status}")
        print(f"   POC 4 (Voltage DA):      {status}")

    all_passed = solar_passed and voltage_passed
    results["overall_passed"] = all_passed

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL POC TESTS PASSED - PLATFORM READY FOR ACCEPTANCE")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
    print("=" * 60)

    # Save results
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Results saved to: {output_path}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
