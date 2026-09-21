from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class StationBase(BaseModel):
    station_id: str
    usaf: str
    wban: str
    name: str
    country: str
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: float
    longitude: float
    is_metro: bool
    deployment_tier: Literal["metro", "central"]


class StationResponse(StationBase):
    current_health_label: Literal["healthy", "degrading", "faulty"]
    current_health_score: float
    last_reading_ts: Optional[datetime] = None

    class Config:
        from_attributes = True


class StationListResponse(BaseModel):
    stations: list[StationResponse]
    total: int


class StationListParams(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)