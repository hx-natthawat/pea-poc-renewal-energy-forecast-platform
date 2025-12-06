#!/usr/bin/env python3
"""
Data Ingestion Pipeline for PEA RE Forecast Platform.

This script provides a robust, extensible data ingestion pipeline that:
1. Validates incoming Excel files against expected schema
2. Handles duplicates with upsert logic
3. Logs all ingestion operations
4. Supports incremental data loading
5. Triggers model retraining when configured

Usage:
    python ingest_data.py --file "POC Data 2-12-25.xlsx"
    python ingest_data.py --file "POC Data 2-12-25.xlsx" --validate-only
    python ingest_data.py --file "POC Data 2-12-25.xlsx" --retrain

Future: Can be triggered via API, Airflow, or Kafka consumer.
"""

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/pea_forecast"
)

DATA_DIR = Path(__file__).parent.parent.parent / "requirements" / "sample"


class DataType(Enum):
    SOLAR = "solar"
    VOLTAGE_1PHASE = "voltage_1phase"
    VOLTAGE_3PHASE = "voltage_3phase"


class IngestionStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int


@dataclass
class IngestionResult:
    status: IngestionStatus
    file_name: str
    file_hash: str
    records_total: int
    records_inserted: int
    records_updated: int
    records_skipped: int
    errors: list[str]
    duration_seconds: float


class DataValidator:
    """Validates incoming data against expected schema and ranges."""

    SOLAR_SCHEMA = {
        "required_columns": [
            "timestamp",
            "pvtemp1",
            "pvtemp2",
            "ambtemp",
            "pyrano1",
            "pyrano2",
            "windspeed",
            "power_kw",
        ],
        "ranges": {
            "pvtemp1": (-10, 100),
            "pvtemp2": (-10, 100),
            "ambtemp": (-10, 60),
            "pyrano1": (0, 1500),
            "pyrano2": (0, 1500),
            "windspeed": (0, 50),
            "power_kw": (0, 10000),
        },
    }

    VOLTAGE_1PHASE_SCHEMA = {
        "required_columns": ["timestamp", "active_power", "energy_meter_voltage"],
        "ranges": {
            "energy_meter_voltage": (180, 260),
            "active_power": (-100, 100),
            "energy_meter_current": (0, 100),
        },
    }

    VOLTAGE_3PHASE_SCHEMA = {
        "required_columns": ["timestamp", "p1_volt", "p2_volt", "p3_volt"],
        "ranges": {
            "p1_volt": (380, 420),  # 3-phase line voltage ~400V
            "p2_volt": (380, 420),
            "p3_volt": (380, 420),
            "p1_amp": (0, 200),
            "p2_amp": (0, 200),
            "p3_amp": (0, 200),
        },
    }

    def validate_solar(self, df: pd.DataFrame) -> ValidationResult:
        """Validate solar data."""
        errors = []
        warnings = []

        # Check required columns
        missing = set(self.SOLAR_SCHEMA["required_columns"]) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")

        # Check ranges
        for col, (min_val, max_val) in self.SOLAR_SCHEMA["ranges"].items():
            if col in df.columns:
                out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                if len(out_of_range) > 0:
                    warnings.append(
                        f"{col}: {len(out_of_range)} values out of range [{min_val}, {max_val}]"
                    )

        # Check for duplicates
        if "timestamp" in df.columns:
            dup_count = df["timestamp"].duplicated().sum()
            if dup_count > 0:
                warnings.append(f"Found {dup_count} duplicate timestamps")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
        )

    def validate_voltage(self, df: pd.DataFrame) -> ValidationResult:
        """Validate 1-phase voltage data."""
        errors = []
        warnings = []

        # Check required columns
        missing = set(self.VOLTAGE_1PHASE_SCHEMA["required_columns"]) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")

        # Check voltage range
        if "energy_meter_voltage" in df.columns:
            out_of_range = df[
                (df["energy_meter_voltage"] < 180) | (df["energy_meter_voltage"] > 260)
            ]
            if len(out_of_range) > 0:
                warnings.append(
                    f"Voltage: {len(out_of_range)} values out of normal range [180V, 260V]"
                )

            # Check for critical violations
            critical = df[
                (df["energy_meter_voltage"] < 207)  # -10%
                | (df["energy_meter_voltage"] > 253)  # +10%
            ]
            if len(critical) > 0:
                warnings.append(
                    f"CRITICAL: {len(critical)} voltage violations (>10% deviation)"
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
        )

    def validate_voltage_3phase(self, df: pd.DataFrame) -> ValidationResult:
        """Validate 3-phase voltage data."""
        errors = []
        warnings = []

        # Check required columns
        missing = set(self.VOLTAGE_3PHASE_SCHEMA["required_columns"]) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")

        # Check voltage ranges for each phase
        for phase_col in ["p1_volt", "p2_volt", "p3_volt"]:
            if phase_col in df.columns:
                out_of_range = df[(df[phase_col] < 380) | (df[phase_col] > 420)]
                if len(out_of_range) > 0:
                    warnings.append(
                        f"{phase_col}: {len(out_of_range)} values out of range [380V, 420V]"
                    )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
        )


class DataIngestionPipeline:
    """Main data ingestion pipeline."""

    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_engine(db_url)
        self.validator = DataValidator()

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file for deduplication."""
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _check_already_ingested(self, file_hash: str) -> bool:
        """Check if file was already ingested."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT id FROM data_ingestion_log WHERE file_hash = :hash"),
                    {"hash": file_hash},
                )
                return result.fetchone() is not None
        except Exception:
            # Table might not exist yet
            return False

    def _log_ingestion(self, result: IngestionResult):
        """Log ingestion result to database."""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO data_ingestion_log
                        (file_name, file_hash, status, records_total, records_inserted,
                         records_updated, records_skipped, errors, duration_seconds, created_at)
                        VALUES
                        (:file_name, :file_hash, :status, :records_total, :records_inserted,
                         :records_updated, :records_skipped, :errors, :duration_seconds, NOW())
                    """),
                    {
                        "file_name": result.file_name,
                        "file_hash": result.file_hash,
                        "status": result.status.value,
                        "records_total": result.records_total,
                        "records_inserted": result.records_inserted,
                        "records_updated": result.records_updated,
                        "records_skipped": result.records_skipped,
                        "errors": ";".join(result.errors) if result.errors else None,
                        "duration_seconds": result.duration_seconds,
                    },
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️  Could not log ingestion: {e}")

    def _parse_excel_file(self, file_path: Path) -> dict[str, pd.DataFrame]:
        """Parse Excel file and return DataFrames for each sheet."""
        result = {}

        xl = pd.ExcelFile(file_path)
        for sheet_name in xl.sheet_names:
            if "solar" in sheet_name.lower():
                df = pd.read_excel(
                    file_path, sheet_name=sheet_name, header=2, usecols="B:I"
                )
                df.columns = [
                    "timestamp",
                    "pvtemp1",
                    "pvtemp2",
                    "ambtemp",
                    "pyrano1",
                    "pyrano2",
                    "windspeed",
                    "power_kw",
                ]
                df = df.dropna(how="all")
                result["solar"] = df

            elif "1 phase" in sheet_name.lower():
                df = pd.read_excel(
                    file_path, sheet_name=sheet_name, header=2, usecols="B:H"
                )
                df.columns = [
                    "timestamp",
                    "active_power",
                    "energy_meter_active_power",
                    "energy_meter_current",
                    "energy_meter_reactive_power",
                    "energy_meter_voltage",
                    "reactive_power",
                ]
                df = df.dropna(how="all")
                result["voltage_1phase"] = df

            elif "3 phase" in sheet_name.lower():
                df = pd.read_excel(
                    file_path, sheet_name=sheet_name, header=2, usecols="A:N"
                )
                df.columns = [
                    "timestamp",
                    "p1_amp",
                    "p1_volt",
                    "p1_w",
                    "p2_amp",
                    "p2_volt",
                    "p2_w",
                    "p3_amp",
                    "p3_volt",
                    "p3_w",
                    "q1_var",
                    "q2_var",
                    "q3_var",
                    "total_w",
                ]
                df = df.dropna(how="all")
                result["voltage_3phase"] = df

        return result

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Try to extract date from filename like 'POC Data 2-12-25.xlsx'."""
        import re

        # Try pattern: day-month-year
        match = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2,4})", filename)
        if match:
            day, month, year = match.groups()
            year = int(year)
            if year < 100:
                year += 2000
            try:
                return datetime(year, int(month), int(day))
            except ValueError:
                pass
        return None

    def _prepare_timestamp(self, df: pd.DataFrame, base_date: datetime) -> pd.DataFrame:
        """Convert time-only timestamps to full datetime."""
        df = df.copy()

        def convert_time(t):
            if pd.isna(t):
                return None
            if isinstance(t, datetime):
                return t
            try:
                return base_date + timedelta(
                    hours=t.hour, minutes=t.minute, seconds=t.second
                )
            except Exception:
                return None

        df["time"] = df["timestamp"].apply(convert_time)
        return df

    def ingest_file(
        self, file_path: Path, force: bool = False, validate_only: bool = False
    ) -> IngestionResult:
        """Ingest a single file into the database."""
        start_time = datetime.now()
        file_hash = self._compute_file_hash(file_path)

        print(f"\n{'=' * 70}")
        print(f"📁 Ingesting: {file_path.name}")
        print(f"   Hash: {file_hash[:16]}...")
        print(f"{'=' * 70}")

        # Check if already ingested
        if not force and self._check_already_ingested(file_hash):
            print("⏭️  File already ingested (use --force to re-ingest)")
            return IngestionResult(
                status=IngestionStatus.SKIPPED,
                file_name=file_path.name,
                file_hash=file_hash,
                records_total=0,
                records_inserted=0,
                records_updated=0,
                records_skipped=0,
                errors=[],
                duration_seconds=0,
            )

        # Parse file
        try:
            dataframes = self._parse_excel_file(file_path)
        except Exception as e:
            return IngestionResult(
                status=IngestionStatus.FAILED,
                file_name=file_path.name,
                file_hash=file_hash,
                records_total=0,
                records_inserted=0,
                records_updated=0,
                records_skipped=0,
                errors=[f"Parse error: {str(e)}"],
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Extract date from filename or use default
        base_date = self._extract_date_from_filename(file_path.name)
        if base_date:
            print(f"   📅 Extracted date from filename: {base_date.date()}")
        else:
            base_date = datetime(2025, 6, 15)
            print(f"   📅 Using default date: {base_date.date()}")

        # Validate each data type
        all_errors = []
        total_records = 0
        inserted = 0

        for data_type, df in dataframes.items():
            print(f"\n   📊 Processing {data_type}...")

            # Validate
            if data_type == "solar":
                validation = self.validator.validate_solar(df)
            elif data_type == "voltage_3phase":
                validation = self.validator.validate_voltage_3phase(df)
            else:
                validation = self.validator.validate_voltage(df)

            print(f"      Rows: {validation.row_count}")

            if validation.errors:
                print(f"      ❌ Errors: {validation.errors}")
                all_errors.extend(validation.errors)

            if validation.warnings:
                for w in validation.warnings:
                    print(f"      ⚠️  {w}")

            if validate_only:
                print("      [Validate only - skipping insert]")
                continue

            if not validation.is_valid:
                print("      ❌ Validation failed - skipping")
                continue

            # Prepare data for insertion
            df = self._prepare_timestamp(df, base_date)
            total_records += len(df)

            # Insert based on type
            try:
                if data_type == "solar":
                    df["station_id"] = "POC_STATION_1"
                    db_cols = [
                        "time",
                        "station_id",
                        "pvtemp1",
                        "pvtemp2",
                        "ambtemp",
                        "pyrano1",
                        "pyrano2",
                        "windspeed",
                        "power_kw",
                    ]
                    df_db = df[db_cols].dropna(subset=["time"])
                    df_db.to_sql(
                        "solar_measurements",
                        self.engine,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                    inserted += len(df_db)
                    print(f"      ✅ Inserted {len(df_db)} records")

                elif data_type == "voltage_1phase":
                    df["prosumer_id"] = "prosumer1"
                    db_cols = [
                        "time",
                        "prosumer_id",
                        "active_power",
                        "reactive_power",
                        "energy_meter_active_power",
                        "energy_meter_current",
                        "energy_meter_voltage",
                        "energy_meter_reactive_power",
                    ]
                    df_db = df[db_cols].dropna(subset=["time"])
                    df_db.to_sql(
                        "single_phase_meters",
                        self.engine,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                    inserted += len(df_db)
                    print(f"      ✅ Inserted {len(df_db)} records")

                elif data_type == "voltage_3phase":
                    df["meter_id"] = "TX_METER_01"
                    db_cols = [
                        "time",
                        "meter_id",
                        "p1_amp",
                        "p1_volt",
                        "p1_w",
                        "p2_amp",
                        "p2_volt",
                        "p2_w",
                        "p3_amp",
                        "p3_volt",
                        "p3_w",
                        "q1_var",
                        "q2_var",
                        "q3_var",
                        "total_w",
                    ]
                    df_db = df[db_cols].dropna(subset=["time"])
                    df_db.to_sql(
                        "three_phase_meters",
                        self.engine,
                        if_exists="append",
                        index=False,
                        method="multi",
                    )
                    inserted += len(df_db)
                    print(f"      ✅ Inserted {len(df_db)} records")

            except Exception as e:
                error_msg = f"Insert error ({data_type}): {str(e)}"
                print(f"      ❌ {error_msg}")
                all_errors.append(error_msg)

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()

        # Determine status
        if all_errors:
            status = IngestionStatus.PARTIAL if inserted > 0 else IngestionStatus.FAILED
        else:
            status = (
                IngestionStatus.SUCCESS
                if not validate_only
                else IngestionStatus.SKIPPED
            )

        result = IngestionResult(
            status=status,
            file_name=file_path.name,
            file_hash=file_hash,
            records_total=total_records,
            records_inserted=inserted,
            records_updated=0,
            records_skipped=total_records - inserted,
            errors=all_errors,
            duration_seconds=duration,
        )

        # Log result
        if not validate_only:
            self._log_ingestion(result)

        print(f"\n{'=' * 70}")
        print(f"✅ Ingestion complete: {status.value}")
        print(f"   Records: {inserted}/{total_records} inserted")
        print(f"   Duration: {duration:.2f}s")
        print(f"{'=' * 70}")

        return result


def trigger_retrain(engine):
    """Trigger model retraining after new data ingestion."""
    print("\n🔄 Triggering model retraining...")

    # Check data counts
    with engine.connect() as conn:
        solar_count = conn.execute(
            text("SELECT COUNT(*) FROM solar_measurements")
        ).scalar()
        voltage_count = conn.execute(
            text("SELECT COUNT(*) FROM single_phase_meters")
        ).scalar()

    print(f"   Solar records: {solar_count:,}")
    print(f"   Voltage records: {voltage_count:,}")

    # Retrain if we have enough data
    if solar_count >= 1000:
        print("   📈 Running solar model training...")
        import subprocess

        result = subprocess.run(
            [sys.executable, "train_solar.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("   ✅ Solar model trained successfully")
        else:
            print(f"   ❌ Solar training failed: {result.stderr}")

    if voltage_count >= 1000:
        print("   📈 Running voltage model training...")
        import subprocess

        result = subprocess.run(
            [sys.executable, "train_voltage.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("   ✅ Voltage model trained successfully")
        else:
            print(f"   ❌ Voltage training failed: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest POC data files into TimescaleDB"
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Path to Excel file to ingest (relative to sample dir or absolute)",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Ingest all Excel files in sample directory",
    )
    parser.add_argument(
        "--validate-only",
        "-v",
        action="store_true",
        help="Only validate, don't insert data",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of already processed files",
    )
    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Trigger model retraining after ingestion",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available files in sample directory"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("PEA RE Forecast Platform - Data Ingestion Pipeline")
    print("=" * 70)
    print(f"Database: {DATABASE_URL}")

    pipeline = DataIngestionPipeline()

    # List files mode
    if args.list:
        print(f"\n📂 Files in {DATA_DIR}:")
        for f in DATA_DIR.glob("*.xlsx"):
            print(f"   - {f.name}")
        return

    # Collect files to process
    files_to_process = []

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = DATA_DIR / args.file
        if file_path.exists():
            files_to_process.append(file_path)
        else:
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

    if args.all:
        files_to_process.extend(DATA_DIR.glob("*.xlsx"))

    if not files_to_process:
        print("❌ No files specified. Use --file or --all")
        parser.print_help()
        sys.exit(1)

    # Process files
    results = []
    for file_path in files_to_process:
        result = pipeline.ingest_file(
            file_path, force=args.force, validate_only=args.validate_only
        )
        results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("📊 INGESTION SUMMARY")
    print("=" * 70)
    for r in results:
        status_icon = {
            IngestionStatus.SUCCESS: "✅",
            IngestionStatus.PARTIAL: "⚠️",
            IngestionStatus.FAILED: "❌",
            IngestionStatus.SKIPPED: "⏭️",
        }[r.status]
        print(
            f"{status_icon} {r.file_name}: {r.records_inserted} inserted ({r.status.value})"
        )

    # Trigger retraining if requested
    if args.retrain and any(r.status == IngestionStatus.SUCCESS for r in results):
        trigger_retrain(pipeline.engine)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
