from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict

from backend.ml.detector_manager import DetectorManager, DetectionResult as MLDetectionResult
from backend.schemas.internal import IngestReading, DetectionResultSummary


@dataclass
class BatchDetectionResult:
    station_id: str
    ts: datetime
    is_anomaly: bool
    status: str
    confidence_score: float
    severity: Optional[str] = None
    root_cause_tag: Optional[str] = None
    component_scores: dict = field(default_factory=dict)


class DetectionService:
    def __init__(self, artifact_dir: str = "ml_artifacts"):
        self.manager = DetectorManager(artifact_dir=artifact_dir)

    def process_batch(self, readings: list[IngestReading]) -> list[BatchDetectionResult]:
        """Process a batch of readings, grouped by station_id.
        
        For each station, readings are processed in temporal order to maintain
        the detector's rolling history correctly.
        """
        # Group readings by station_id
        by_station: dict[str, list[IngestReading]] = defaultdict(list)
        for r in readings:
            by_station[r.station_id].append(r)
        
        results: list[BatchDetectionResult] = []
        
        for station_id, station_readings in by_station.items():
            # Sort by timestamp to maintain temporal order
            station_readings.sort(key=lambda x: x.ts)
            
            for reading in station_readings:
                # Handle None values - use 0.0 as fallback for detection
                temp = reading.temperature_c if reading.temperature_c is not None else 0.0
                pressure = reading.pressure_hpa if reading.pressure_hpa is not None else 0.0
                humidity = reading.humidity_pct if reading.humidity_pct is not None else 0.0
                
                ml_result = self.manager.process(
                    station_id=station_id,
                    ts=reading.ts,
                    temperature_c=temp,
                    pressure_hpa=pressure,
                    humidity_pct=humidity,
                    is_dropout=reading.is_dropout,
                )
                
                results.append(BatchDetectionResult(
                    station_id=ml_result.station_id,
                    ts=ml_result.ts,
                    is_anomaly=ml_result.is_anomaly,
                    status=ml_result.status,
                    confidence_score=ml_result.confidence_score,
                    severity=ml_result.severity,
                    root_cause_tag=ml_result.root_cause_tag,
                    component_scores=ml_result.component_scores,
                ))
        
        return results

    def to_summary(self, results: list[BatchDetectionResult]) -> list[DetectionResultSummary]:
        """Convert internal results to API response summaries."""
        return [
            DetectionResultSummary(
                station_id=r.station_id,
                ts=r.ts,
                is_anomaly=r.is_anomaly,
                anomaly_type=None,  # Not directly available, could be derived from root_cause_tag
                confidence_score=r.confidence_score,
                severity=r.severity,
                root_cause_tag=r.root_cause_tag,
            )
            for r in results
        ]

    def get_anomalies_only(self, results: list[BatchDetectionResult]) -> list[BatchDetectionResult]:
        """Filter results to only anomalies."""
        return [r for r in results if r.is_anomaly]