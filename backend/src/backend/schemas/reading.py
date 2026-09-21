from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ReadingBase(BaseModel):
    station_id: str
    ts: datetime
    temperature_c: Optional[float] = None
    pressure_hpa: Optional[float] = None
    humidity_pct: Optional[float] = None
    source: Literal["live", "simulator", "historical"] = "live"


class ReadingCreate(ReadingBase):
    pass


class ReadingResponse(ReadingBase):
    reading_id: int

    class Config:
        from_attributes = True


class ReadingListParams(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)