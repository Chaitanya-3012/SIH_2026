from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class HealthSnapshot(BaseModel):
    station_id: str
    ts: datetime
    composite_score: float = Field(..., ge=0, le=1)
    label: Literal["healthy", "degrading", "faulty"]
    anomaly_frequency: Optional[float] = None
    drift_trend: Optional[float] = None
    data_completeness: Optional[float] = None
    reconstruction_error_trend: Optional[float] = None
    variance_behavior: Optional[float] = None

    class Config:
        from_attributes = True


class HealthHistoryParams(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)