from typing import Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Anomaly
from backend.schemas.anomaly import AnomalyCreate, AnomalyListParams, AnomalyStatusUpdate


async def create_anomaly(db: AsyncSession, anomaly: AnomalyCreate) -> Anomaly:
    db_anomaly = Anomaly(**anomaly.model_dump())
    db.add(db_anomaly)
    await db.flush()
    await db.refresh(db_anomaly)
    return db_anomaly


async def bulk_create_anomalies(db: AsyncSession, anomalies: list[AnomalyCreate]) -> list[Anomaly]:
    db_anomalies = [Anomaly(**a.model_dump()) for a in anomalies]
    db.add_all(db_anomalies)
    await db.flush()
    for a in db_anomalies:
        await db.refresh(a)
    return db_anomalies


async def get_anomalies(
    db: AsyncSession,
    station_id: str,
    params: AnomalyListParams
) -> list[Anomaly]:
    stmt = select(Anomaly).where(Anomaly.station_id == station_id)
    
    if params.status:
        stmt = stmt.where(Anomaly.status == params.status)
    if params.start:
        stmt = stmt.where(Anomaly.ts >= params.start)
    if params.end:
        stmt = stmt.where(Anomaly.ts <= params.end)
    
    stmt = stmt.order_by(desc(Anomaly.ts)).limit(params.limit).offset(params.offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_anomaly_by_id(db: AsyncSession, anomaly_id: int) -> Optional[Anomaly]:
    stmt = select(Anomaly).where(Anomaly.anomaly_id == anomaly_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_anomaly_status(
    db: AsyncSession,
    anomaly_id: int,
    status_update: AnomalyStatusUpdate
) -> Optional[Anomaly]:
    anomaly = await get_anomaly_by_id(db, anomaly_id)
    if anomaly:
        anomaly.status = status_update.status
        if status_update.status in ("reviewed", "dismissed"):
            from datetime import datetime
            anomaly.reviewed_at = datetime.utcnow()
        await db.flush()
        await db.refresh(anomaly)
    return anomaly


async def get_open_anomalies_count(db: AsyncSession, station_id: str) -> int:
    from sqlalchemy import func
    stmt = select(func.count(Anomaly.anomaly_id)).where(
        Anomaly.station_id == station_id,
        Anomaly.status == "open"
    )
    result = await db.execute(stmt)
    return result.scalar() or 0