from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.crud.anomaly import get_anomalies, get_anomaly_by_id, update_anomaly_status
from backend.crud.station import get_station
from backend.schemas.anomaly import AnomalyResponse, AnomalyListParams, AnomalyStatusUpdate

router = APIRouter(prefix="/stations", tags=["anomalies"])


@router.get("/{station_id}/anomalies", response_model=list[AnomalyResponse])
async def get_station_anomalies(
    station_id: str,
    params: AnomalyListParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Get anomaly history for a station with filtering."""
    station = await get_station(db, station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    anomalies = await get_anomalies(db, station_id, params)
    return [
        AnomalyResponse(
            anomaly_id=a.anomaly_id,
            reading_id=a.reading_id,
            station_id=a.station_id,
            ts=a.ts,
            anomaly_type=a.anomaly_type,
            confidence_score=a.confidence_score,
            severity=a.severity,
            root_cause_tag=a.root_cause_tag,
            shap_values=a.shap_values,
            component_scores=a.component_scores,
            status=a.status,
            created_at=a.created_at,
            reviewed_at=a.reviewed_at,
            reviewed_by=a.reviewed_by,
        )
        for a in anomalies
    ]


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly_detail(
    anomaly_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get anomaly detail including SHAP values."""
    anomaly = await get_anomaly_by_id(db, anomaly_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return AnomalyResponse(
        anomaly_id=anomaly.anomaly_id,
        reading_id=anomaly.reading_id,
        station_id=anomaly.station_id,
        ts=anomaly.ts,
        anomaly_type=anomaly.anomaly_type,
        confidence_score=anomaly.confidence_score,
        severity=anomaly.severity,
        root_cause_tag=anomaly.root_cause_tag,
        shap_values=anomaly.shap_values,
        component_scores=anomaly.component_scores,
        status=anomaly.status,
        created_at=anomaly.created_at,
        reviewed_at=anomaly.reviewed_at,
        reviewed_by=anomaly.reviewed_by,
    )


@router.patch("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
async def update_anomaly_status_endpoint(
    anomaly_id: int,
    status_update: AnomalyStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update anomaly status (open -> reviewed/dismissed)."""
    anomaly = await update_anomaly_status(db, anomaly_id, status_update)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    return AnomalyResponse(
        anomaly_id=anomaly.anomaly_id,
        reading_id=anomaly.reading_id,
        station_id=anomaly.station_id,
        ts=anomaly.ts,
        anomaly_type=anomaly.anomaly_type,
        confidence_score=anomaly.confidence_score,
        severity=anomaly.severity,
        root_cause_tag=anomaly.root_cause_tag,
        shap_values=anomaly.shap_values,
        component_scores=anomaly.component_scores,
        status=anomaly.status,
        created_at=anomaly.created_at,
        reviewed_at=anomaly.reviewed_at,
        reviewed_by=anomaly.reviewed_by,
    )