from sqlalchemy import (
    BigInteger,
    Double,
    DateTime,
    ForeignKey,
    String,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    benchmark_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("model_versions.model_id", ondelete="CASCADE"),
        nullable=False
    )
    station_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("stations.station_id", ondelete="SET NULL"),
        nullable=True
    )
    precision_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    recall_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    false_positive_rate: Mapped[float | None] = mapped_column(Double, nullable=True)
    evaluated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    model: Mapped["ModelVersion"] = relationship(back_populates="benchmarks")
    station: Mapped["Station"] = relationship(back_populates="benchmarks")

    __table_args__ = (
        Index("idx_benchmark_model", "model_id"),
        Index("idx_benchmark_station", "station_id"),
    )