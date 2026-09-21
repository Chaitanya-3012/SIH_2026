from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.crud.reading import get_readings, get_latest_reading
from backend.crud.station import get_station
from backend.schemas.reading import ReadingResponse, ReadingListParams

router = APIRouter(prefix="/stations", tags=["readings"])


@router.get("/{station_id}/readings", response_model=list[ReadingResponse])
async def get_station_readings(
    station_id: str,
    params: ReadingListParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Get historical readings for a station with pagination."""
    station = await get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    readings = await get_readings(db, station_id, params)
    return [
        ReadingResponse(
            reading_id=r.reading_id,
            station_id=r.station_id,
            ts=r.ts,
            temperature_c=r.temperature_c,
            pressure_hpa=r.pressure_hpa,
            humidity_pct=r.humidity_pct,
            source=r.source,
        )
        for r in readings
    ]