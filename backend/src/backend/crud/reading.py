from typing import Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Reading, Station
from backend.schemas.reading import ReadingCreate, ReadingListParams


async def create_reading(db: AsyncSession, reading: ReadingCreate) -> Reading:
    db_reading = Reading(**reading.model_dump())
    db.add(db_reading)
    await db.flush()
    await db.refresh(db_reading)
    return db_reading


async def bulk_create_readings(db: AsyncSession, readings: list[ReadingCreate]) -> list[Reading]:
    db_readings = [Reading(**r.model_dump()) for r in readings]
    db.add_all(db_readings)
    await db.flush()
    for r in db_readings:
        await db.refresh(r)
    return db_readings


async def get_readings(
    db: AsyncSession,
    station_id: str,
    params: ReadingListParams
) -> list[Reading]:
    stmt = select(Reading).where(Reading.station_id == station_id)
    
    if params.start:
        stmt = stmt.where(Reading.ts >= params.start)
    if params.end:
        stmt = stmt.where(Reading.ts <= params.end)
    
    stmt = stmt.order_by(desc(Reading.ts)).limit(params.limit).offset(params.offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_latest_reading(db: AsyncSession, station_id: str) -> Optional[Reading]:
    stmt = (
        select(Reading)
        .where(Reading.station_id == station_id)
        .order_by(desc(Reading.ts))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()