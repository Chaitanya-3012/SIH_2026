from sqlalchemy import (
    BigInteger,
    String,
    Double,
    DateTime,
    ForeignKey,
    Boolean,
    func,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class DriftEvent(Base):
    __tablename__ = "drift_events"

    drift_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False
    )
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    parameter: Mapped[str] = mapped_column(String(30), nullable=False)
    trend_value: Mapped[float] = mapped_column(Double, nullable=False)
    degradation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped["Station"] = relationship(back_populates="drift_events")

    __table_args__ = (
        Index("idx_drift_events_station_ts", "station_id", "ts.desc()"),
        Index("idx_drift_events_degradation", "degradation_flag", postgresql_where=(degradation_flag == True)),
        CheckConstraint("parameter IN ('temperature', 'pressure', 'humidity')", name="ck_drift_parameter"),
    )