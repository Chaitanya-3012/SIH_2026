"""Stream simulator replays historical Bombay weather data with optional synthetic anomaly injection.

Acts as the production real-time architecture data source (per TRD §3.6), configurable to:
- Read raw historical readings from CSV
- Inject synthetic anomalies (spike, frozen, drift, dropout) at multiple severity levels
- Push readings to FastAPI backend via REST or direct DB session
- APScheduler-based configurable replay interval

Usage:
    python simulator.py --csv data/bombay_2024_2025.csv --interval 1.0
"""

import argparse
import csv
import json
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi import FastAPI

app = FastAPI()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "bombay_2024_2025.csv"
INTERVAL_SECONDS = 1  # 1 reading per second simulates live AWS feed
SEVERITY_LEVELS = ["low", "medium", "high"]
ANOMALY_TYPES = ["spike", "frozen", "drift", "dropout"]

# ---------------------------------------------------------------------------
# Helpers: synthetic anomaly injectors
# ---------------------------------------------------------------------------


def inject_spike(readings_row, severity="medium"):
    """Add a sudden spike to one parameter based on severity."""
    factor = {"low": 3.0, "medium": 5.0, "high": 10.0}[severity]
    param = random.choice(["temperature_c", "pressure_hpa", "humidity_pct"])
    row = dict(readings_row)
    row[param] += factor
    return row, f"spike_{param}"


def inject_frozen(readings_row, severity="medium"):
    """Freeze one parameter to its last value based on severity."""
    duration = {"low": 1, "medium": 3, "high": 5}[severity]
    param = random.choice(["temperature_c", "pressure_hpa", "humidity_pct"])
    row = dict(readings_row)
    row[param] = row.get(param, 0)  # keep value, but mark as stagnant
    return row, f"frozen_{param}_{duration}h"


def inject_drift(readings_row, severity="medium"):
    """Gradual drift over several readings based on severity."""
    increment = {"low": 0.2, "medium": 0.5, "high": 1.0}[severity]
    param = random.choice(["temperature_c", "pressure_hpa", "humidity_pct"])
    row = dict(readings_row)
    row[param] = row.get(param, 0) + increment
    return row, f"drift_{param}"


def inject_dropout(readings_row, severity="medium"):
    """Replace one parameter with NaN/missing based on severity."""
    row = dict(readings_row)
    param = random.choice(["temperature_c", "pressure_hpa", "humidity_pct"])
    row[param] = None
    return row, f"dropout_{param}"


ANOMALY_INJECTORS = {
    "spike": inject_spike,
    "frozen": inject_frozen,
    "drift": inject_drift,
    "dropout": inject_dropout,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_csv_data(csv_path: Path) -> list[dict]:
    """Load historical readings from CSV into a list of dicts."""
    if not csv_path.exists():
        print(f"⚠ CSV not found at {csv_path}. Using empty dataset.")
        return []

    df = pd.read_csv(csv_path)
    # Normalize column names: lowercase, underscore-separated
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_")
    )

    readings = df.to_dict(orient="records")
    print(f"📂 Loaded {len(readings)} readings from {csv_path}")
    return readings


# ---------------------------------------------------------------------------
# Simulator generator
# ---------------------------------------------------------------------------


def generate_reading(
    base_reading: dict, inject_anomaly: bool = False
) -> dict:
    """Produce a reading, optionally with a synthetic anomaly injected."""
    row = dict(base_reading)

    if inject_anomaly and random.random() < 0.15:  # ~15% anomaly rate
        injector_type = random.choice(list(ANOMALY_INJECTORS.keys()))
        severity = random.choice(SEVERITY_LEVELS)
        injector = ANOMALY_INJECTORS[injector_type]
        row, root_cause_tag = injector(row, severity)
        row["anomaly_type"] = injector_type
        row["severity"] = severity
        row["root_cause_tag"] = root_cause_tag
        row["is_anomaly"] = True
    else:
        row["is_anomaly"] = False
        row["anomaly_type"] = None
        row["severity"] = None
        row["root_cause_tag"] = None

    # Ensure timestamptz format
    if "ts" in row and isinstance(row["ts"], str):
        try:
            row["ts"] = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
        except Exception:
            row["ts"] = datetime.utcnow()

    # Ensure numeric types
    for col in ["temperature_c", "pressure_hpa", "humidity_pct"]:
        if col in row and row[col] is not None:
            try:
                row[col] = float(row[col])
            except (ValueError, TypeError):
                row[col] = 0.0

    return row


# ---------------------------------------------------------------------------
# FastAPI integration helper
# ---------------------------------------------------------------------------

def push_reading_to_backend reading: dict):
    """Send a single reading to the FastAPI backend via REST.

    In production this would use the /readings endpoint. For prototype we
    post to a local dev endpoint; if it fails we just print so the
    simulator never crashes on network hiccups.
    """
    import httpx

    try:
        with httpx.Client(timeout=5.0) as client:
            client.post("http://localhost:8000/readings", json=reading)
    except Exception as e:
        # Print but don't crash the scheduler loop
        print(f"[simulator] could not POST reading: {e}")


# ---------------------------------------------------------------------------
# Scheduler job
# ---------------------------------------------------------------------------


def stream_job(
    readings: list[dict],
    interval: float,
    inject_anomalies: bool,
    client: object,  # FastAPI test client or httpx.Client
):
    """APScheduler job: emit one reading, then schedule the next."""
    global _idx  # noqa: PLC0001

    if not readings:
        print("⚠ No readings loaded — skipping stream.")
        return

    # Cycle through readings indefinitely
    reading = generate_reading(readings[_idx % len(readings)], inject_anomalies)
    _idx += 1

    # Push to backend
    push_reading_to_backend(reading)

    # Log every 10th reading for observability
    if _idx % 10 == 0:
        is_anom = reading.get("is_anomaly", False)
        print(
            f"[simulator] pushed reading #{_idx} "
            f"(ts={reading.get('ts')}, anomaly={is_anom})"
        )


# ---------------------------------------------------------------------------
# Application entrypoint
# ---------------------------------------------------------------------------

_idx = 0  # global index into the readings list


def main():
    parser = argparse.ArgumentParser(description="SkyGuard Stream Simulator")
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="Path to Bombay 2024-2025 CSV file",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=INTERVAL_SECONDS,
        help="Replay interval in seconds (default=1s per reading)",
    )
    parser.add_argument(
        "--inject",
        action="store_true",
        help="Inject synthetic anomalies (spike/frozen/drift/dropout)",
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Don't try POSTing to FastAPI (use for DB-only setups)",
    )
    args = parser.parse_args()

    # Load data
    readings = load_csv_data(args.csv)

    if not readings:
        print(
            "⚠ No readings loaded — create a CSV with columns: "
            "station_id, ts, temperature_c, pressure_hpa, humidity_pct"
        )
        return

    print(f"▶ Starting stream simulator @ {args.interval}s interval")
    if args.inject:
        print(f"   Anomaly injection enabled ({', '.join(ANOMALY_TYPES)} at {', '.join(SEVERITY_LEVELS)})")

    scheduler = BlockingScheduler()

    # Wrap the job so we capture the readings/interval/inject args
    def job_wrapper():
        stream_job(readings, args.inject, args.no_api)

    scheduler.add_job(job_wrapper, "interval", seconds=args.interval)
    scheduler.start()


if __name__ == "__main__":
    main()