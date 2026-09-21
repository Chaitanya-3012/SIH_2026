from sqlalchemy import (
    BigInteger,
    Double,
    DateTime,
    ForeignKey,
    String,
    func,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class SensorHealth(Base):
    __tablename__ = "sensor_health"

    health_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False
    )
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    composite_score: Mapped[float] = mapped_column(Double, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    anomaly_frequency: Mapped[float | None] = mapped_column(Double, nullable=True)
    drift_trend: Mapped[float | None] = mapped_column(Double, nullable=True)
    data_completeness: Mapped[float | None] = mapped_column(Double, nullable=True)
    reconstruction_error_trend: Mapped[float | None] = mapped_column(Double, nullable=True)
    variance_behavior: Mapped[float | None] = mapped_column(Double, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped["Station"] = relationship(back_populates="health_snapshots")

    __table_args__ = (
        Index("idx_sensor_health_station_ts_desc", "station_id", "ts.desc()"),
        Index("idx_sensor_health_label", "label"),
        CheckConstraint("composite_score >= 0 AND composite_score <= 1", name="ck_health_composite"),
        CheckConstraint("label IN ('healthy', 'degrading', 'faulty')", name="ck_health_label"),
    )