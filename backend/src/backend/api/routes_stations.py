from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.crud.station import get_station, get_stations
from backend.crud.health import get_latest_health
from backend.schemas.station import StationResponse, StationListResponse, StationListParams

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=StationListResponse)
async def list_stations(
    params: StationListParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """List all stations with pagination."""
    stations, total = await get_stations(db, params)
    
    # Get latest health for each station
    station_responses = []
    for station in stations:
        health = await get_latest_health(db, station.station_id)
        station_responses.append(StationResponse(
            station_id=station.station_id,
            usaf=station.usaf,
            wban=station.wban,
            name=station.name,
            country=station.country,
            state=station.state,
            district=station.district,
            latitude=station.latitude,
            longitude=station.longitude,
            is_metro=station.is_metro,
            deployment_tier=station.deployment_tier,
            current_health_label=health.label if health else "healthy",
            current_health_score=health.composite_score if health else 0.0,
            last_reading_ts=None,  # Could be fetched if needed
        ))
    
    return StationListResponse(stations=station_responses, total=total)


@router.get("/{station_id}", response_model=StationResponse)
async def get_station_detail(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get station detail with current health."""
    station = await get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    health = await get_latest_health(db, station_id)
    
    return StationResponse(
        station_id=station.station_id,
        usaf=station.usaf,
        wban=station.wban,
        name=station.name,
        country=station.country,
        state=station.state,
        district=station.district,
        latitude=station.latitude,
        longitude=station.longitude,
        is_metro=station.is_metro,
        deployment_tier=station.deployment_tier,
        current_health_label=health.label if health else "healthy",
        current_health_score=health.composite_score if health else 0.0,
        last_reading_ts=None,
    )