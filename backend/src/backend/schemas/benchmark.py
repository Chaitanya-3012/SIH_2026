from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BenchmarkResultResponse(BaseModel):
    benchmark_id: int
    model_id: int
    station_id: Optional[str] = None
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    f1_score: Optional[float] = None
    false_positive_rate: Optional[float] = None
    evaluated_at: datetime

    class Config:
        from_attributes = True


class LatestBenchmarkResponse(BaseModel):
    model_type: str
    version_tag: str
    overall_precision: Optional[float] = None
    overall_recall: Optional[float] = None
    overall_f1: Optional[float] = None
    station_benchmarks: list[BenchmarkResultResponse]