from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.crud.health import get_health_history, get_latest_health
from backend.crud.station import get_station
from backend.schemas.health import HealthSnapshot, HealthHistoryParams

router = APIRouter(prefix="/stations", tags=["health"])


@router.get("/{station_id}/health-history", response_model=list[HealthSnapshot])
async def get_station_health_history(
    station_id: str,
    params: HealthHistoryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Get health score trend for a station."""
    station = await get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    health_snapshots = await get_health_history(db, station_id, params)
    return [
        HealthSnapshot(
            station_id=h.station_id,
            ts=h.ts,
            composite_score=h.composite_score,
            label=h.label,
            anomaly_frequency=h.anomaly_frequency,
            drift_trend=h.drift_trend,
            data_completeness=h.data_completeness,
            reconstruction_error_trend=h.reconstruction_error_trend,
            variance_behavior=h.variance_behavior,
        )
        for h in health_snapshots
    ]


@router.get("/{station_id}/health", response_model=HealthSnapshot)
async def get_station_current_health(
    station_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current health status for a station."""
    station = await get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    health = await get_latest_health(db, station_id)
    if not health:
        # Return default healthy if no health data yet
        return HealthSnapshot(
            station_id=station_id,
            ts=datetime.utcnow(),
            composite_score=0.0,
            label="healthy",
        )
    
    return HealthSnapshot(
        station_id=health.station_id,
        ts=health.ts,
        composite_score=health.composite_score,
        label=health.label,
        anomaly_frequency=health.anomaly_frequency,
        drift_trend=health.drift_trend,
        data_completeness=health.data_completeness,
        reconstruction_error_trend=health.reconstruction_error_trend,
        variance_behavior=health.variance_behavior,
    )