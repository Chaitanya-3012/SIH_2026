from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import BenchmarkResult, ModelVersion


async def get_latest_model(db: AsyncSession, model_type: str) -> Optional[ModelVersion]:
    stmt = (
        select(ModelVersion)
        .where(ModelVersion.model_type == model_type, ModelVersion.is_active == True)
        .order_by(desc(ModelVersion.activated_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_benchmarks_for_model(
    db: AsyncSession,
    model_id: int,
    station_id: Optional[str] = None
) -> list[BenchmarkResult]:
    stmt = select(BenchmarkResult).where(BenchmarkResult.model_id == model_id)
    if station_id:
        stmt = stmt.where(BenchmarkResult.station_id == station_id)
    stmt = stmt.order_by(desc(BenchmarkResult.evaluated_at))
    result = await db.execute(stmt)
    return list(result.scalars().all())