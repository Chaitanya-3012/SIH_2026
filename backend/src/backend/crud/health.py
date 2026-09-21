from typing import Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SensorHealth
from backend.schemas.health import HealthHistoryParams


async def create_health_snapshot(db: AsyncSession, **kwargs) -> SensorHealth:
    health = SensorHealth(**kwargs)
    db.add(health)
    await db.flush()
    await db.refresh(health)
    return health


async def get_health_history(
    db: AsyncSession,
    station_id: str,
    params: HealthHistoryParams
) -> list[SensorHealth]:
    stmt = select(SensorHealth).where(SensorHealth.station_id == station_id)
    
    if params.start:
        stmt = stmt.where(SensorHealth.ts >= params.start)
    if params.end:
        stmt = stmt.where(SensorHealth.ts <= params.end)
    
    stmt = stmt.order_by(desc(SensorHealth.ts)).limit(params.limit).offset(params.offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_latest_health(db: AsyncSession, station_id: str) -> Optional[SensorHealth]:
    stmt = (
        select(SensorHealth)
        .where(SensorHealth.station_id == station_id)
        .order_by(desc(SensorHealth.ts))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()