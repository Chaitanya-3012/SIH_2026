from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class WSAlertPayload(BaseModel):
    station_id: str
    ts: datetime
    anomaly_type: str
    confidence: float = Field(..., ge=0, le=1)
    severity: Literal["low", "medium", "high"]
    shap_summary: dict[str, float]


class WSHealthPayload(BaseModel):
    station_id: str
    label: Literal["healthy", "degrading", "faulty"]
    composite_score: float = Field(..., ge=0, le=1)
    ts: datetime