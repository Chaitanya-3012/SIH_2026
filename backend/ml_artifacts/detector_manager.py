"""
detector_manager.py
Wraps inference.py's SkyGuardDetector with per-station state, root-cause
tagging, and severity bucketing. Does not modify inference.py or the
trained artifacts -- this is purely the integration layer.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone

from inference import SkyGuardDetector  # unmodified, from the notebook export

# --- DB column <-> model feature name mapping. Keep this the ONLY place
# these two naming conventions meet. ---
FEATURE_MAP = {
    "temperature_c": "temperature",
    "pressure_hpa": "sea_level_pressure",
    "humidity_pct": "relative_humidity",
}

THRESHOLD_ENSEMBLE = 0.4170  # must match inference.py's hardcoded value
SEVERITY_BAND = 0.15         # width of each severity bucket above threshold


@dataclass
class DetectionResult:
    station_id: str
    ts: datetime
    is_anomaly: bool
    status: str                     # "ok" | "warmup" | "anomaly"
    confidence_score: float
    severity: Optional[str] = None          # "low" | "medium" | "high"
    root_cause_tag: Optional[str] = None
    component_scores: dict = field(default_factory=dict)


def _bucket_severity(score: float) -> str:
    if score < THRESHOLD_ENSEMBLE + SEVERITY_BAND:
        return "low"
    if score < THRESHOLD_ENSEMBLE + 2 * SEVERITY_BAND:
        return "medium"
    return "high"


def _tag_root_cause(breakdown: dict, is_dropout: bool) -> str:
    drift = breakdown.get("drift", 0.0)
    stability = breakdown.get("temporal_stability", 0.0)
    physical = breakdown.get("physical_consistency", 0.0)
    lstm = breakdown.get("lstm_score", 0.0)
    isof = breakdown.get("isolation_forest", 0.0)

    scores = {
        "drift": drift,
        "stability": stability,
        "physical": physical,
        "spike": max(lstm, isof),
    }
    dominant = max(scores, key=scores.get)

    if scores[dominant] == 0.0:
        return "unknown"
    if dominant == "stability":
        return "dropout" if is_dropout else "frozen"
    if dominant == "physical":
        return "multivariate"
    if dominant == "spike":
        return "spike"
    return "drift"


class DetectorManager:
    """Owns one SkyGuardDetector per station. Not thread-safe for
    concurrent writes to the SAME station -- call through a single
    asyncio task per station, or add a per-station lock if that
    assumption doesn't hold in your stream simulator design."""

    def __init__(self, artifact_dir: str = "ml_artifacts"):
        self._artifact_dir = artifact_dir
        self._detectors: dict[str, SkyGuardDetector] = {}

    def _get_or_create(self, station_id: str) -> SkyGuardDetector:
        if station_id not in self._detectors:
            self._detectors[station_id] = SkyGuardDetector(
                scaler_path=f"{self._artifact_dir}/scaler.joblib",
                if_path=f"{self._artifact_dir}/isolation_forest.joblib",
                lstm_path=f"{self._artifact_dir}/lstm_autoencoder.pth",
            )
        return self._detectors[station_id]

    def process(
        self,
        station_id: str,
        ts: datetime,
        temperature_c: float,
        pressure_hpa: float,
        humidity_pct: float,
        is_dropout: bool = False,
    ) -> DetectionResult:
        """Synchronous, CPU-bound. Call via run_in_threadpool from the
        async endpoint -- do not call directly inside `async def`."""
        detector = self._get_or_create(station_id)

        record = {
            FEATURE_MAP["temperature_c"]: temperature_c,
            FEATURE_MAP["pressure_hpa"]: pressure_hpa,
            FEATURE_MAP["humidity_pct"]: humidity_pct,
        }

        raw = detector.detect_anomaly(record, is_dropout=is_dropout)

        if raw.get("status") == "Warmup Phase":
            return DetectionResult(
                station_id=station_id,
                ts=ts,
                is_anomaly=False,
                status="warmup",
                confidence_score=0.0,
            )

        score = raw["ensemble_score"]
        is_anomaly = raw["is_anomaly"]

        if not is_anomaly:
            return DetectionResult(
                station_id=station_id,
                ts=ts,
                is_anomaly=False,
                status="ok",
                confidence_score=score,
                component_scores=raw["breakdown"],
            )

        return DetectionResult(
            station_id=station_id,
            ts=ts,
            is_anomaly=True,
            status="anomaly",
            confidence_score=score,
            severity=_bucket_severity(score),
            root_cause_tag=_tag_root_cause(raw["breakdown"], is_dropout),
            component_scores=raw["breakdown"],
        )


# --- Example FastAPI wiring (not a full app -- shows the integration points) ---
#
# from fastapi import FastAPI
# from fastapi.concurrency import run_in_threadpool
#
# app = FastAPI()
# manager = DetectorManager(artifact_dir="ml_artifacts")
#
# @app.post("/internal/ingest")
# async def ingest(reading: ReadingIn):
#     result = await run_in_threadpool(
#         manager.process,
#         station_id=reading.station_id,
#         ts=reading.ts,
#         temperature_c=reading.temperature_c,
#         pressure_hpa=reading.pressure_hpa,
#         humidity_pct=reading.humidity_pct,
#     )
#     await save_reading(reading)  # -> readings table, always
#     if result.status == "anomaly":
#         await save_anomaly(result)        # -> anomalies table
#         await push_alert(result)          # -> /ws/alerts
#     return result
