#!/usr/bin/env python3
"""
Generate demo data for stakeholder demonstrations.

This script creates realistic-looking data for:
- Solar power forecasts with good accuracy
- Voltage readings with some violations for alerts
- Audit log entries showing system activity
- Sample alerts across different severity levels
"""

import os
import random
from datetime import datetime, timedelta

import numpy as np
import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    """Get database connection from environment."""
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pea_forecast"
    )
    return psycopg2.connect(database_url)


def generate_solar_demo_data(conn, days: int = 7):
    """Generate solar measurement data for demo."""
    print(f"Generating {days} days of solar demo data...")

    cursor = conn.cursor()
    now = datetime.now()
    data = []

    for day in range(days):
        date = now - timedelta(days=day)
        for hour in range(6, 19):  # 6 AM to 6 PM (daylight hours)
            for minute in [0, 15, 30, 45]:  # 15-minute intervals
                timestamp = date.replace(hour=hour, minute=minute, second=0)

                # Simulate solar irradiance curve (peaks at noon)
                hour_factor = 1 - abs(hour - 12) / 6
                cloud_factor = random.uniform(0.7, 1.0)
                base_irradiance = 1000 * hour_factor * cloud_factor

                # Add some noise
                pyrano1 = base_irradiance + random.gauss(0, 20)
                pyrano2 = base_irradiance + random.gauss(0, 20)

                # Temperature correlates with irradiance
                ambtemp = 25 + hour_factor * 10 + random.gauss(0, 2)
                pvtemp1 = ambtemp + pyrano1 / 50 + random.gauss(0, 1)
                pvtemp2 = ambtemp + pyrano2 / 50 + random.gauss(0, 1)

                # Wind speed
                windspeed = random.uniform(0.5, 5.0)

                # Power output (correlates with irradiance)
                power_kw = max(0, base_irradiance * 4.5 / 1000 + random.gauss(0, 50))

                data.append(
                    (
                        timestamp,
                        "DEMO_STATION_1",
                        max(0, pvtemp1),
                        max(0, pvtemp2),
                        max(0, ambtemp),
                        max(0, pyrano1),
                        max(0, pyrano2),
                        max(0, windspeed),
                        max(0, power_kw),
                    )
                )

    # Insert data
    execute_values(
        cursor,
        """
        INSERT INTO solar_measurements
        (time, station_id, pvtemp1, pvtemp2, ambtemp, pyrano1, pyrano2, windspeed, power_kw)
        VALUES %s
        ON CONFLICT (time, station_id) DO NOTHING
        """,
        data,
    )
    conn.commit()
    print(f"  Inserted {len(data)} solar measurements")


def generate_voltage_demo_data(conn, days: int = 7):
    """Generate voltage reading data for demo with some violations."""
    print(f"Generating {days} days of voltage demo data...")

    cursor = conn.cursor()
    now = datetime.now()
    prosumers = [
        "prosumer1",
        "prosumer2",
        "prosumer3",
        "prosumer4",
        "prosumer5",
        "prosumer6",
        "prosumer7",
    ]
    data = []

    for day in range(days):
        date = now - timedelta(days=day)
        for hour in range(24):
            for minute in [0, 15, 30, 45]:
                timestamp = date.replace(hour=hour, minute=minute, second=0)

                for prosumer_id in prosumers:
                    # Base voltage around 230V (nominal)
                    base_voltage = 230

                    # Add time-of-day variation
                    if 10 <= hour <= 14:  # Peak solar hours - voltage rises
                        base_voltage += random.uniform(3, 8)
                    elif 18 <= hour <= 21:  # Evening peak demand - voltage drops
                        base_voltage -= random.uniform(2, 5)

                    # Add some violations (5% chance)
                    if random.random() < 0.05:
                        if random.random() < 0.5:
                            base_voltage += random.uniform(10, 15)  # Over-voltage
                        else:
                            base_voltage -= random.uniform(10, 15)  # Under-voltage

                    voltage = base_voltage + random.gauss(0, 1)
                    current = random.uniform(5, 25)
                    active_power = voltage * current / 1000
                    reactive_power = active_power * random.uniform(0.1, 0.3)

                    data.append(
                        (
                            timestamp,
                            prosumer_id,
                            active_power,
                            reactive_power,
                            active_power,
                            current,
                            voltage,
                            reactive_power,
                        )
                    )

    # Insert data
    execute_values(
        cursor,
        """
        INSERT INTO single_phase_meters
        (time, prosumer_id, active_power, reactive_power,
         energy_meter_active_power, energy_meter_current,
         energy_meter_voltage, energy_meter_reactive_power)
        VALUES %s
        ON CONFLICT (time, prosumer_id) DO NOTHING
        """,
        data,
    )
    conn.commit()
    print(f"  Inserted {len(data)} voltage readings")


def generate_demo_alerts(conn, count: int = 50):
    """Generate sample alerts for demo."""
    print(f"Generating {count} demo alerts...")

    cursor = conn.cursor()
    now = datetime.now()

    alert_types = [
        ("voltage_high", "critical", "Voltage exceeded upper limit (242V)"),
        ("voltage_low", "warning", "Voltage below lower limit (218V)"),
        ("forecast_deviation", "warning", "Solar forecast deviation > 15%"),
        ("ramp_rate", "info", "Ramp rate approaching limit"),
        ("model_drift", "warning", "Model performance degradation detected"),
        ("communication_loss", "critical", "Communication lost with meter"),
    ]

    prosumers = [
        "prosumer1",
        "prosumer2",
        "prosumer3",
        "prosumer4",
        "prosumer5",
        "prosumer6",
        "prosumer7",
    ]

    data = []
    for i in range(count):
        alert_type, severity, message = random.choice(alert_types)
        target_id = random.choice(prosumers)
        timestamp = now - timedelta(hours=random.randint(0, 168))  # Last 7 days

        current_value = 230 + random.uniform(-20, 20)
        threshold_value = 242 if "high" in alert_type else 218

        # Some alerts are acknowledged/resolved
        acknowledged = random.random() < 0.6
        resolved = acknowledged and random.random() < 0.7

        data.append(
            (
                timestamp,
                alert_type,
                severity,
                target_id,
                f"{message} at {target_id}",
                current_value,
                threshold_value,
                acknowledged,
                resolved,
            )
        )

    execute_values(
        cursor,
        """
        INSERT INTO alerts
        (time, alert_type, severity, target_id, message,
         current_value, threshold_value, acknowledged, resolved)
        VALUES %s
        """,
        data,
    )
    conn.commit()
    print(f"  Inserted {count} demo alerts")


def generate_demo_audit_logs(conn, count: int = 200):
    """Generate sample audit log entries for demo."""
    print(f"Generating {count} demo audit logs...")

    cursor = conn.cursor()
    now = datetime.now()

    users = [
        ("user1@pea.co.th", "admin"),
        ("user2@pea.co.th", "operator"),
        ("user3@pea.co.th", "viewer"),
        ("demo@pea.co.th", "admin"),
    ]

    actions = [
        ("read", "GET", "/api/v1/forecast/solar"),
        ("read", "GET", "/api/v1/forecast/voltage"),
        ("read", "GET", "/api/v1/alerts"),
        ("create", "POST", "/api/v1/alerts/acknowledge"),
        ("update", "PUT", "/api/v1/settings"),
        ("read", "GET", "/api/v1/topology/network"),
        ("export", "POST", "/api/v1/audit/export"),
        ("login", "POST", "/api/v1/auth/login"),
        ("logout", "POST", "/api/v1/auth/logout"),
    ]

    resources = ["forecast", "voltage", "alert", "settings", "topology", "audit", "auth"]

    data = []
    for i in range(count):
        user_email, user_id = random.choice(users)
        action, method, path = random.choice(actions)
        timestamp = now - timedelta(minutes=random.randint(0, 10080))  # Last 7 days

        # Most requests succeed
        status = 200 if random.random() < 0.95 else random.choice([400, 401, 403, 500])

        data.append(
            (
                timestamp,
                user_id,
                user_email,
                f"192.168.1.{random.randint(1, 254)}",
                action,
                random.choice(resources),
                str(random.randint(1, 1000)),
                method,
                path,
                status,
                "Mozilla/5.0 Demo Browser",
                f"session_{random.randint(1000, 9999)}",
            )
        )

    execute_values(
        cursor,
        """
        INSERT INTO audit_log
        (time, user_id, user_email, user_ip, action, resource_type,
         resource_id, request_method, request_path, response_status,
         user_agent, session_id)
        VALUES %s
        """,
        data,
    )
    conn.commit()
    print(f"  Inserted {count} audit log entries")


def generate_predictions(conn, days: int = 3):
    """Generate sample predictions for demo."""
    print(f"Generating {days} days of predictions...")

    cursor = conn.cursor()
    now = datetime.now()
    data = []

    for day in range(days):
        date = now - timedelta(days=day)
        for hour in range(6, 19):
            timestamp = date.replace(hour=hour, minute=0, second=0)

            # Solar prediction
            hour_factor = 1 - abs(hour - 12) / 6
            predicted = 4500 * hour_factor + random.gauss(0, 100)
            actual = predicted + random.gauss(0, predicted * 0.08)  # ~8% error

            data.append(
                (
                    timestamp,
                    "solar",
                    "xgb-v1.0.0",
                    "DEMO_STATION_1",
                    60,
                    max(0, predicted),
                    max(0, predicted * 0.9),
                    predicted * 1.1,
                    max(0, actual),
                )
            )

    execute_values(
        cursor,
        """
        INSERT INTO predictions
        (time, model_type, model_version, target_id, horizon_minutes,
         predicted_value, confidence_lower, confidence_upper, actual_value)
        VALUES %s
        """,
        data,
    )
    conn.commit()
    print(f"  Inserted {len(data)} predictions")


def main():
    """Main entry point."""
    print("=" * 60)
    print("PEA RE Forecast Platform - Demo Data Generator")
    print("=" * 60)

    try:
        conn = get_connection()
        print(f"Connected to database")

        # Generate demo data
        generate_solar_demo_data(conn, days=7)
        generate_voltage_demo_data(conn, days=7)
        generate_demo_alerts(conn, count=50)
        generate_demo_audit_logs(conn, count=200)
        generate_predictions(conn, days=3)

        conn.close()

        print("=" * 60)
        print("Demo data generation complete!")
        print("=" * 60)
        print("\nDemo URLs:")
        print("  Frontend:  http://localhost:3000")
        print("  Backend:   http://localhost:8000/docs")
        print("  Audit Log: http://localhost:3000/audit")
        print("\nDemo Credentials:")
        print("  Email:    demo@pea.co.th")
        print("  Password: demo123")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
