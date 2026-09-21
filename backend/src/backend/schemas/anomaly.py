from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AnomalyBase(BaseModel):
    anomaly_type: Literal["spike", "drift", "frozen", "dropout", "multivariate", "unknown"]
    confidence_score: float = Field(..., ge=0, le=1)
    severity: Literal["low", "medium", "high"]
    root_cause_tag: Optional[str] = None
    shap_values: Optional[dict[str, float]] = None
    component_scores: Optional[dict[str, float]] = None


class AnomalyCreate(AnomalyBase):
    reading_id: int
    station_id: str


class AnomalyResponse(AnomalyBase):
    anomaly_id: int
    reading_id: int
    station_id: str
    ts: datetime
    status: Literal["open", "reviewed", "dismissed"]
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

    class Config:
        from_attributes = True


class AnomalyStatusUpdate(BaseModel):
    status: Literal["reviewed", "dismissed"]


class AnomalyListParams(BaseModel):
    status: Optional[Literal["open", "reviewed", "dismissed"]] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)