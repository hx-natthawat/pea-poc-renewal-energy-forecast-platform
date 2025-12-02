#!/usr/bin/env python3
"""
Voltage Prediction Model Training Script.

Trains a model for voltage level prediction across prosumers.
Target metrics (per TOR):
- MAE < 2V
- RMSE < 3V
- R² > 0.90

Usage:
    python scripts/train_voltage.py
    python scripts/train_voltage.py --output models/voltage_model.joblib
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
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sqlalchemy import create_engine, text

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.voltage_features import VoltageFeatureEngineer


# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/pea_forecast"
)

# TOR Target Metrics
TARGET_MAE = 2.0  # V
TARGET_RMSE = 3.0  # V
TARGET_R2 = 0.90


def load_voltage_data(engine) -> pd.DataFrame:
    """Load voltage measurements from TimescaleDB."""
    print("\n📊 Loading voltage data from database...")

    query = text("""
        SELECT
            time,
            prosumer_id,
            active_power,
            reactive_power,
            energy_meter_current,
            energy_meter_voltage
        FROM single_phase_meters
        ORDER BY prosumer_id, time ASC
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    print(f"   Loaded {len(df):,} records")
    print(f"   Prosumers: {df['prosumer_id'].nunique()}")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")

    return df


def train_model(X_train: pd.DataFrame, y_train: pd.Series):
    """Train model with optimized hyperparameters."""
    print("\n🎯 Training RandomForestRegressor...")

    # Use RandomForest for voltage prediction (handles non-linear patterns well)
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_leaf=5,
        min_samples_split=10,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    return model


def evaluate_model(model, X: pd.DataFrame, y: pd.Series, split_name: str = "Test") -> dict:
    """Evaluate model and return metrics."""
    y_pred = model.predict(X)

    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)

    metrics = {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 4),
        "samples": len(y),
    }

    print(f"\n📈 {split_name} Metrics:")
    print(f"   MAE:   {metrics['mae']:.3f} V (target: <{TARGET_MAE} V)")
    print(f"   RMSE:  {metrics['rmse']:.3f} V (target: <{TARGET_RMSE} V)")
    print(f"   R²:    {metrics['r2']:.4f} (target: >{TARGET_R2})")

    return metrics


def cross_validate(X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> tuple[list, dict]:
    """Perform time-series cross-validation."""
    print(f"\n🔄 Time-Series Cross-Validation ({n_splits} splits)...")

    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_results = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_val, y_val, f"Fold {fold}")
        cv_results.append(metrics)

    # Calculate average metrics
    avg_metrics = {
        "mae": round(np.mean([r["mae"] for r in cv_results]), 3),
        "rmse": round(np.mean([r["rmse"] for r in cv_results]), 3),
        "r2": round(np.mean([r["r2"] for r in cv_results]), 4),
    }

    print(f"\n📊 Cross-Validation Average:")
    print(f"   MAE:   {avg_metrics['mae']:.3f} V")
    print(f"   RMSE:  {avg_metrics['rmse']:.3f} V")
    print(f"   R²:    {avg_metrics['r2']:.4f}")

    return cv_results, avg_metrics


def get_feature_importance(model, feature_names: list[str]) -> pd.DataFrame:
    """Get feature importance from trained model."""
    importance = model.feature_importances_

    df = pd.DataFrame({
        "feature": feature_names,
        "importance": importance
    }).sort_values("importance", ascending=False)

    return df


def check_targets(metrics: dict) -> bool:
    """Check if model meets TOR target metrics."""
    meets_mae = metrics["mae"] < TARGET_MAE
    meets_rmse = metrics["rmse"] < TARGET_RMSE
    meets_r2 = metrics["r2"] > TARGET_R2

    print("\n✅ Target Check:")
    print(f"   MAE < {TARGET_MAE} V: {'✓ PASS' if meets_mae else '✗ FAIL'}")
    print(f"   RMSE < {TARGET_RMSE} V: {'✓ PASS' if meets_rmse else '✗ FAIL'}")
    print(f"   R² > {TARGET_R2}: {'✓ PASS' if meets_r2 else '✗ FAIL'}")

    return meets_mae and meets_rmse and meets_r2


def save_model(model, feature_engineer: VoltageFeatureEngineer, metrics: dict, output_path: Path):
    """Save model and metadata."""
    print(f"\n💾 Saving model to {output_path}...")

    # Create model artifact
    artifact = {
        "model": model,
        "feature_columns": feature_engineer.get_feature_columns(),
        "lag_periods": feature_engineer.lag_periods,
        "rolling_windows": feature_engineer.rolling_windows,
        "metrics": metrics,
        "trained_at": datetime.now().isoformat(),
        "version": "v1.0.0",
    }

    # Save with joblib
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)

    # Save metadata as JSON
    metadata_path = output_path.with_suffix(".json")
    metadata = {
        "model_type": "random_forest",
        "task": "voltage_prediction",
        "feature_columns": feature_engineer.get_feature_columns(),
        "metrics": metrics,
        "trained_at": artifact["trained_at"],
        "version": artifact["version"],
        "target_requirements": {
            "mae": f"< {TARGET_MAE} V",
            "rmse": f"< {TARGET_RMSE} V",
            "r2": f"> {TARGET_R2}",
        },
        "meets_requirements": bool(check_targets(metrics)),
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"   ✅ Model saved: {output_path}")
    print(f"   ✅ Metadata saved: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description="Train voltage prediction model")
    parser.add_argument(
        "--output",
        type=str,
        default="models/voltage_rf_v1.joblib",
        help="Output path for trained model"
    )
    parser.add_argument(
        "--cv-splits",
        type=int,
        default=5,
        help="Number of cross-validation splits"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("PEA RE Forecast Platform - Voltage Model Training")
    print("=" * 70)
    print(f"Target: MAE < {TARGET_MAE} V, RMSE < {TARGET_RMSE} V, R² > {TARGET_R2}")

    # Connect to database
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    # Load data
    df = load_voltage_data(engine)

    if len(df) < 100:
        print("❌ Insufficient data for training (need at least 100 samples)")
        sys.exit(1)

    # Feature engineering
    print("\n🔧 Applying feature engineering...")
    feature_engineer = VoltageFeatureEngineer(
        lag_periods=[1, 2, 3, 6],
        rolling_windows=[6, 12]
    )

    X, y = feature_engineer.prepare_train_data(df)
    print(f"   Features: {len(feature_engineer.get_feature_columns())}")
    print(f"   Samples after cleaning: {len(X):,}")

    # Cross-validation
    cv_results, avg_metrics = cross_validate(X, y, n_splits=args.cv_splits)

    # Train final model on all data
    print("\n🎯 Training final model on all data...")
    final_model = train_model(X, y)

    # Final evaluation
    final_metrics = evaluate_model(final_model, X, y, "Final (All Data)")

    # Feature importance
    importance_df = get_feature_importance(final_model, feature_engineer.get_feature_columns())
    print("\n📊 Top 10 Features:")
    for _, row in importance_df.head(10).iterrows():
        print(f"   {row['feature']}: {row['importance']:.4f}")

    # Check targets
    meets_targets = check_targets(avg_metrics)

    # Save model
    output_path = Path(__file__).parent.parent / args.output
    save_model(final_model, feature_engineer, avg_metrics, output_path)

    print("\n" + "=" * 70)
    if meets_targets:
        print("✅ Model training complete - ALL TARGETS MET!")
    else:
        print("⚠️  Model training complete - Some targets not met")
    print("=" * 70)

    return 0 if meets_targets else 1


if __name__ == "__main__":
    sys.exit(main())
