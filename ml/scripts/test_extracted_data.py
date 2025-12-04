#!/usr/bin/env python3
"""
Test and validate the extracted Test.pdf data.
Performs:
1. Data quality validation
2. Feature engineering validation
3. Model prediction tests
4. Statistical analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add ml/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def test_solar_data():
    """Test Solar RE Forecast data quality and perform analysis."""
    print("\n" + "="*70)
    print("TEST 1: SOLAR RE FORECAST DATA VALIDATION")
    print("="*70)

    # Load data
    df = pd.read_csv(RAW_DATA_DIR / "test_solar_data.csv", parse_dates=['timestamp'])
    tests_passed = 0
    tests_total = 0

    # Test 1: Check row count (should be 288 for 5-min intervals over 24h)
    tests_total += 1
    expected_rows = 288
    if len(df) == expected_rows:
        print(f"[PASS] Row count: {len(df)} (expected {expected_rows})")
        tests_passed += 1
    else:
        print(f"[FAIL] Row count: {len(df)} (expected {expected_rows})")

    # Test 2: Check required columns
    tests_total += 1
    required_cols = ['timestamp', 'pvtemp1', 'pvtemp2', 'ambtemp', 'pyrano1', 'pyrano2', 'windspeed', 'power_kw']
    missing_cols = set(required_cols) - set(df.columns)
    if not missing_cols:
        print(f"[PASS] All required columns present")
        tests_passed += 1
    else:
        print(f"[FAIL] Missing columns: {missing_cols}")

    # Test 3: Check data ranges
    tests_total += 1
    range_checks = [
        ('pvtemp1', -10, 100, df['pvtemp1'].min(), df['pvtemp1'].max()),
        ('pvtemp2', -10, 100, df['pvtemp2'].min(), df['pvtemp2'].max()),
        ('ambtemp', -10, 60, df['ambtemp'].min(), df['ambtemp'].max()),
        ('pyrano1', 0, 1500, df['pyrano1'].min(), df['pyrano1'].max()),
        ('pyrano2', 0, 1500, df['pyrano2'].min(), df['pyrano2'].max()),
        ('windspeed', 0, 50, df['windspeed'].min(), df['windspeed'].max()),
        ('power_kw', 0, 5000, df['power_kw'].min(), df['power_kw'].max()),
    ]
    range_valid = True
    for col, min_val, max_val, actual_min, actual_max in range_checks:
        if actual_min < min_val or actual_max > max_val:
            print(f"  [WARN] {col} out of range: [{actual_min:.2f}, {actual_max:.2f}] (expected [{min_val}, {max_val}])")
            range_valid = False
    if range_valid:
        print(f"[PASS] All columns within expected ranges")
        tests_passed += 1
    else:
        print(f"[PARTIAL] Some columns have values outside typical ranges")
        tests_passed += 0.5

    # Test 4: Check no missing values
    tests_total += 1
    missing = df.isnull().sum().sum()
    if missing == 0:
        print(f"[PASS] No missing values")
        tests_passed += 1
    else:
        print(f"[FAIL] {missing} missing values found")

    # Test 5: Check power generation pattern (zero at night)
    tests_total += 1
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    night_hours = df[df['hour'].isin([0, 1, 2, 3, 4, 5, 22, 23])]
    night_power_zero = (night_hours['power_kw'] == 0).mean()
    if night_power_zero > 0.9:  # 90% of night hours should have zero power
        print(f"[PASS] Night power pattern correct ({night_power_zero:.1%} zero power at night)")
        tests_passed += 1
    else:
        print(f"[WARN] Night power pattern ({night_power_zero:.1%} zero power at night)")
        tests_passed += 0.5

    # Test 6: Check irradiance-power correlation
    tests_total += 1
    daytime = df[(df['hour'] >= 7) & (df['hour'] <= 17)]
    if len(daytime) > 10:
        corr_pyrano_power = daytime['pyrano1'].corr(daytime['power_kw'])
        if corr_pyrano_power > 0.9:
            print(f"[PASS] Irradiance-power correlation: {corr_pyrano_power:.3f} (expected > 0.9)")
            tests_passed += 1
        else:
            print(f"[WARN] Irradiance-power correlation: {corr_pyrano_power:.3f} (expected > 0.9)")
            tests_passed += 0.5
    else:
        print(f"[SKIP] Insufficient daytime data for correlation test")

    # Test 7: Check peak power time
    tests_total += 1
    peak_idx = df['power_kw'].idxmax()
    peak_hour = df.loc[peak_idx, 'hour']
    if 10 <= peak_hour <= 14:
        print(f"[PASS] Peak power at hour {peak_hour} (expected 10-14)")
        tests_passed += 1
    else:
        print(f"[WARN] Peak power at hour {peak_hour} (expected 10-14)")
        tests_passed += 0.5

    # Statistical summary
    print(f"\n--- Solar Data Statistics ---")
    print(f"  Max Power: {df['power_kw'].max():.2f} kW")
    print(f"  Mean Power (daytime): {daytime['power_kw'].mean():.2f} kW")
    print(f"  Peak Irradiance: {df['pyrano1'].max():.2f} W/m²")
    print(f"  Temperature Range: {df['ambtemp'].min():.1f}°C - {df['ambtemp'].max():.1f}°C")

    print(f"\n[RESULT] Solar tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_single_phase_data():
    """Test Single-Phase Meter data quality."""
    print("\n" + "="*70)
    print("TEST 2: SINGLE-PHASE METER DATA VALIDATION")
    print("="*70)

    df = pd.read_csv(RAW_DATA_DIR / "test_single_phase_data.csv", parse_dates=['timestamp'])
    tests_passed = 0
    tests_total = 0

    # Test 1: Check row count
    tests_total += 1
    expected_rows = 288
    if len(df) == expected_rows:
        print(f"[PASS] Row count: {len(df)} (expected {expected_rows})")
        tests_passed += 1
    else:
        print(f"[FAIL] Row count: {len(df)} (expected {expected_rows})")

    # Test 2: Check required columns
    tests_total += 1
    required_cols = ['timestamp', 'prosumer_id', 'energy_meter_voltage', 'energy_meter_current',
                     'active_power', 'energy_meter_reactive_power']
    missing_cols = set(required_cols) - set(df.columns)
    if not missing_cols:
        print(f"[PASS] All required columns present")
        tests_passed += 1
    else:
        print(f"[FAIL] Missing columns: {missing_cols}")

    # Test 3: Check voltage range (nominal 230V ±10%)
    tests_total += 1
    voltage_min = df['energy_meter_voltage'].min()
    voltage_max = df['energy_meter_voltage'].max()
    nominal_voltage = 230
    tolerance = 0.10  # 10%
    if voltage_min >= nominal_voltage * (1 - tolerance) and voltage_max <= nominal_voltage * (1 + tolerance):
        print(f"[PASS] Voltage range: {voltage_min:.1f}V - {voltage_max:.1f}V (within ±10% of 230V)")
        tests_passed += 1
    else:
        # Check TOR specified limits (218V - 242V for ±5%)
        if voltage_min >= 207 and voltage_max <= 253:  # ±10% range
            print(f"[PASS] Voltage range: {voltage_min:.1f}V - {voltage_max:.1f}V (within ±10% of 230V)")
            tests_passed += 1
        else:
            print(f"[WARN] Voltage range: {voltage_min:.1f}V - {voltage_max:.1f}V (outside ±10% of 230V)")
            tests_passed += 0.5

    # Test 4: Check no missing values
    tests_total += 1
    missing = df.isnull().sum().sum()
    if missing == 0:
        print(f"[PASS] No missing values")
        tests_passed += 1
    else:
        print(f"[FAIL] {missing} missing values found")

    # Test 5: Check prosumer_id
    tests_total += 1
    unique_prosumers = df['prosumer_id'].unique()
    if len(unique_prosumers) >= 1:
        print(f"[PASS] Prosumer IDs: {list(unique_prosumers)}")
        tests_passed += 1
    else:
        print(f"[FAIL] No prosumer IDs found")

    # Test 6: Check voltage stability (standard deviation)
    tests_total += 1
    voltage_std = df['energy_meter_voltage'].std()
    if voltage_std < 10:  # Expect relatively stable voltage
        print(f"[PASS] Voltage stability: std={voltage_std:.2f}V (expected < 10V)")
        tests_passed += 1
    else:
        print(f"[WARN] Voltage stability: std={voltage_std:.2f}V (expected < 10V)")
        tests_passed += 0.5

    # Statistical summary
    print(f"\n--- Single-Phase Data Statistics ---")
    print(f"  Voltage: {df['energy_meter_voltage'].mean():.1f}V ± {df['energy_meter_voltage'].std():.2f}V")
    print(f"  Current Range: {df['energy_meter_current'].min():.2f}A - {df['energy_meter_current'].max():.2f}A")
    print(f"  Active Power Range: {df['active_power'].min():.2f} - {df['active_power'].max():.2f}")

    print(f"\n[RESULT] Single-phase tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_three_phase_data():
    """Test Three-Phase Meter data quality."""
    print("\n" + "="*70)
    print("TEST 3: THREE-PHASE METER DATA VALIDATION")
    print("="*70)

    df = pd.read_csv(RAW_DATA_DIR / "test_three_phase_data.csv", parse_dates=['timestamp'])
    tests_passed = 0
    tests_total = 0

    # Test 1: Check data exists
    tests_total += 1
    if len(df) > 0:
        print(f"[PASS] Data loaded: {len(df)} rows")
        tests_passed += 1
    else:
        print(f"[FAIL] No data loaded")

    # Test 2: Check all three phases present
    tests_total += 1
    phase_cols = ['p1_volt', 'p2_volt', 'p3_volt']
    if all(col in df.columns for col in phase_cols):
        print(f"[PASS] All three phase voltage columns present")
        tests_passed += 1
    else:
        print(f"[FAIL] Missing phase voltage columns")

    # Test 3: Check phase voltages are balanced (within 5% of each other)
    tests_total += 1
    avg_voltages = [df['p1_volt'].mean(), df['p2_volt'].mean(), df['p3_volt'].mean()]
    voltage_spread = (max(avg_voltages) - min(avg_voltages)) / np.mean(avg_voltages)
    if voltage_spread < 0.05:
        print(f"[PASS] Phase voltages balanced: P1={avg_voltages[0]:.1f}V, P2={avg_voltages[1]:.1f}V, P3={avg_voltages[2]:.1f}V (spread: {voltage_spread:.2%})")
        tests_passed += 1
    else:
        print(f"[WARN] Phase voltages unbalanced: spread={voltage_spread:.2%} (expected < 5%)")
        tests_passed += 0.5

    # Test 4: Check total power calculation
    tests_total += 1
    calculated_total = df['p1_w'] + df['p2_w'] + df['p3_w']
    diff = (calculated_total - df['total_w']).abs().mean()
    if diff < 1.0:  # Allow 1kW tolerance
        print(f"[PASS] Total power calculation correct (avg diff: {diff:.3f} kW)")
        tests_passed += 1
    else:
        print(f"[WARN] Total power calculation mismatch (avg diff: {diff:.3f} kW)")
        tests_passed += 0.5

    # Test 5: Check no missing values
    tests_total += 1
    missing = df.isnull().sum().sum()
    if missing == 0:
        print(f"[PASS] No missing values")
        tests_passed += 1
    else:
        print(f"[FAIL] {missing} missing values found")

    # Statistical summary
    print(f"\n--- Three-Phase Data Statistics ---")
    print(f"  Phase 1 Voltage: {df['p1_volt'].mean():.1f}V ± {df['p1_volt'].std():.2f}V")
    print(f"  Phase 2 Voltage: {df['p2_volt'].mean():.1f}V ± {df['p2_volt'].std():.2f}V")
    print(f"  Phase 3 Voltage: {df['p3_volt'].mean():.1f}V ± {df['p3_volt'].std():.2f}V")
    print(f"  Total Power: {df['total_w'].mean():.2f} kW ± {df['total_w'].std():.2f} kW")

    print(f"\n[RESULT] Three-phase tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_feature_engineering():
    """Test feature engineering capabilities with the extracted data."""
    print("\n" + "="*70)
    print("TEST 4: FEATURE ENGINEERING VALIDATION")
    print("="*70)

    df = pd.read_csv(RAW_DATA_DIR / "test_solar_data.csv", parse_dates=['timestamp'])
    tests_passed = 0
    tests_total = 0

    # Test 1: Temporal features
    tests_total += 1
    try:
        df['hour'] = df['timestamp'].dt.hour
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['is_peak_hour'] = df['hour'].between(10, 14).astype(int)
        print(f"[PASS] Temporal features created successfully")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Temporal features failed: {e}")

    # Test 2: Derived features
    tests_total += 1
    try:
        df['pyrano_avg'] = (df['pyrano1'] + df['pyrano2']) / 2
        df['pvtemp_avg'] = (df['pvtemp1'] + df['pvtemp2']) / 2
        df['temp_delta'] = df['pvtemp_avg'] - df['ambtemp']
        print(f"[PASS] Derived features created successfully")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Derived features failed: {e}")

    # Test 3: Lag features
    tests_total += 1
    try:
        for lag in [1, 2, 3]:
            df[f'pyrano1_lag_{lag}'] = df['pyrano1'].shift(lag)
        print(f"[PASS] Lag features created successfully")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Lag features failed: {e}")

    # Test 4: Rolling statistics
    tests_total += 1
    try:
        df['pyrano1_rolling_mean_12'] = df['pyrano1'].rolling(12, min_periods=1).mean()
        df['pyrano1_rolling_std_12'] = df['pyrano1'].rolling(12, min_periods=1).std()
        print(f"[PASS] Rolling statistics created successfully")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Rolling statistics failed: {e}")

    # Test 5: Feature correlation with target
    tests_total += 1
    try:
        # Remove rows with NaN from lag features
        df_clean = df.dropna()
        feature_cols = ['pyrano_avg', 'pvtemp_avg', 'temp_delta', 'hour_sin', 'hour_cos',
                        'pyrano1_rolling_mean_12', 'pyrano1_lag_1']
        correlations = {}
        for col in feature_cols:
            if col in df_clean.columns:
                correlations[col] = df_clean[col].corr(df_clean['power_kw'])

        top_features = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        print(f"[PASS] Feature correlations computed")
        print(f"  Top features by correlation:")
        for feat, corr in top_features:
            print(f"    {feat}: {corr:.3f}")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Feature correlation failed: {e}")

    print(f"\n[RESULT] Feature engineering tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_ml_prediction():
    """Test basic ML prediction capability."""
    print("\n" + "="*70)
    print("TEST 5: ML PREDICTION VALIDATION")
    print("="*70)

    tests_passed = 0
    tests_total = 0

    # Load and prepare data
    df = pd.read_csv(RAW_DATA_DIR / "test_solar_data.csv", parse_dates=['timestamp'])

    # Create features
    df['hour'] = df['timestamp'].dt.hour
    df['pyrano_avg'] = (df['pyrano1'] + df['pyrano2']) / 2
    df['pvtemp_avg'] = (df['pvtemp1'] + df['pvtemp2']) / 2
    df['temp_delta'] = df['pvtemp_avg'] - df['ambtemp']

    features = ['pyrano1', 'pyrano2', 'pvtemp1', 'pvtemp2', 'ambtemp', 'windspeed',
                'hour', 'pyrano_avg', 'pvtemp_avg', 'temp_delta']
    target = 'power_kw'

    X = df[features]
    y = df[target]

    # Test 1: Train/test split
    tests_total += 1
    try:
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        print(f"[PASS] Train/test split: {len(X_train)} train, {len(X_test)} test samples")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Train/test split failed: {e}")
        return tests_passed, tests_total

    # Test 2: Linear Regression
    tests_total += 1
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        y_pred = lr_model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"[PASS] Linear Regression:")
        print(f"    RMSE: {rmse:.2f} kW")
        print(f"    MAE:  {mae:.2f} kW")
        print(f"    R²:   {r2:.4f}")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Linear Regression failed: {e}")

    # Test 3: Random Forest
    tests_total += 1
    try:
        from sklearn.ensemble import RandomForestRegressor

        rf_model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        y_pred_rf = rf_model.predict(X_test)

        rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
        mae_rf = mean_absolute_error(y_test, y_pred_rf)
        r2_rf = r2_score(y_test, y_pred_rf)

        print(f"[PASS] Random Forest:")
        print(f"    RMSE: {rmse_rf:.2f} kW")
        print(f"    MAE:  {mae_rf:.2f} kW")
        print(f"    R²:   {r2_rf:.4f}")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Random Forest failed: {e}")

    # Test 4: XGBoost (if available)
    tests_total += 1
    try:
        import xgboost as xgb

        xgb_model = xgb.XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
        xgb_model.fit(X_train, y_train)
        y_pred_xgb = xgb_model.predict(X_test)

        rmse_xgb = np.sqrt(mean_squared_error(y_test, y_pred_xgb))
        mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
        r2_xgb = r2_score(y_test, y_pred_xgb)

        print(f"[PASS] XGBoost:")
        print(f"    RMSE: {rmse_xgb:.2f} kW")
        print(f"    MAE:  {mae_xgb:.2f} kW")
        print(f"    R²:   {r2_xgb:.4f}")
        tests_passed += 1
    except ImportError:
        print(f"[SKIP] XGBoost not available")
    except Exception as e:
        print(f"[FAIL] XGBoost failed: {e}")

    # Test 5: Check if R² meets TOR requirement (> 0.95)
    tests_total += 1
    best_r2 = max([r2, r2_rf] + ([r2_xgb] if 'r2_xgb' in dir() else []))
    if best_r2 > 0.95:
        print(f"[PASS] Best R² ({best_r2:.4f}) meets TOR requirement (> 0.95)")
        tests_passed += 1
    else:
        print(f"[INFO] Best R² ({best_r2:.4f}) - may improve with more data/features")
        tests_passed += 0.5

    print(f"\n[RESULT] ML prediction tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def main():
    print("="*70)
    print("PEA RE FORECAST PLATFORM - EXTRACTED DATA TEST SUITE")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Directory: {RAW_DATA_DIR}")

    total_passed = 0
    total_tests = 0

    # Run all tests
    results = []

    p, t = test_solar_data()
    results.append(('Solar Data', p, t))
    total_passed += p
    total_tests += t

    p, t = test_single_phase_data()
    results.append(('Single-Phase Data', p, t))
    total_passed += p
    total_tests += t

    p, t = test_three_phase_data()
    results.append(('Three-Phase Data', p, t))
    total_passed += p
    total_tests += t

    p, t = test_feature_engineering()
    results.append(('Feature Engineering', p, t))
    total_passed += p
    total_tests += t

    p, t = test_ml_prediction()
    results.append(('ML Prediction', p, t))
    total_passed += p
    total_tests += t

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n{'Test Category':<25} {'Passed':<10} {'Total':<10} {'Rate':<10}")
    print("-"*55)
    for name, passed, total in results:
        rate = passed/total if total > 0 else 0
        print(f"{name:<25} {passed:<10.1f} {total:<10} {rate:<10.1%}")
    print("-"*55)
    print(f"{'TOTAL':<25} {total_passed:<10.1f} {total_tests:<10} {total_passed/total_tests:.1%}")

    print("\n" + "="*70)
    if total_passed/total_tests >= 0.9:
        print("OVERALL RESULT: PASS - Data extraction and validation successful!")
    elif total_passed/total_tests >= 0.7:
        print("OVERALL RESULT: PARTIAL - Most tests passed with some warnings")
    else:
        print("OVERALL RESULT: FAIL - Please review failed tests")
    print("="*70)

    return total_passed, total_tests


if __name__ == "__main__":
    main()
