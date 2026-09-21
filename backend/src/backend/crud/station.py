from typing import Optional
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Station
from backend.schemas.station import StationListParams


async def get_station(db: AsyncSession, station_id: str) -> Optional[Station]:
    stmt = select(Station).where(Station.station_id == station_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_stations(
    db: AsyncSession,
    params: StationListParams
) -> tuple[list[Station], int]:
    stmt = select(Station).limit(params.limit).offset(params.offset)
    count_stmt = select(func.count(Station.station_id))
    
    result = await db.execute(stmt)
    count_result = await db.execute(count_stmt)
    
    stations = list(result.scalars().all())
    total = count_result.scalar() or 0
    
    return stations, total


async def create_station(db: AsyncSession, **kwargs) -> Station:
    station = Station(**kwargs)
    db.add(station)
    await db.flush()
    await db.refresh(station)
    return station