from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database import get_db
from backend.crud.benchmark import get_latest_model, get_benchmarks_for_model
from backend.schemas.benchmark import LatestBenchmarkResponse, BenchmarkResultResponse

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/latest", response_model=LatestBenchmarkResponse)
async def get_latest_benchmarks(
    model_type: str = "ensemble",
    db: AsyncSession = Depends(get_db)
):
    """Get latest evaluation results for the active model."""
    model = await get_latest_model(db, model_type)
    if not model:
        raise HTTPException(status_code=404, detail="No active model found")
    
    benchmarks = await get_benchmarks_for_model(db, model.model_id)
    
    # Calculate overall metrics (average across stations)
    if benchmarks:
        overall_precision = sum(b.precision_score or 0 for b in benchmarks) / len(benchmarks)
        overall_recall = sum(b.recall_score or 0 for b in benchmarks) / len(benchmarks)
        overall_f1 = sum(b.f1_score or 0 for b in benchmarks) / len(benchmarks)
    else:
        overall_precision = overall_recall = overall_f1 = None
    
    return LatestBenchmarkResponse(
        model_type=model.model_type,
        version_tag=model.version_tag,
        overall_precision=overall_precision,
        overall_recall=overall_recall,
        overall_f1=overall_f1,
        station_benchmarks=[
            BenchmarkResultResponse(
                benchmark_id=b.benchmark_id,
                model_id=b.model_id,
                station_id=b.station_id,
                precision_score=b.precision_score,
                recall_score=b.recall_score,
                f1_score=b.f1_score,
                false_positive_rate=b.false_positive_rate,
                evaluated_at=b.evaluated_at,
            )
            for b in benchmarks
        ],
    )