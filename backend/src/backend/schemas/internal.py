from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IngestReading(BaseModel):
    station_id: str = Field(..., min_length=1)
    ts: datetime
    temperature_c: Optional[float] = None
    pressure_hpa: Optional[float] = None
    humidity_pct: Optional[float] = None
    is_dropout: bool = False


class DetectionResultSummary(BaseModel):
    station_id: str
    ts: datetime
    is_anomaly: bool
    anomaly_type: Optional[str] = None
    confidence_score: float
    severity: Optional[str] = None
    root_cause_tag: Optional[str] = None


class IngestBatchResponse(BaseModel):
    processed: int
    anomalies_detected: int
    results: list[DetectionResultSummary]