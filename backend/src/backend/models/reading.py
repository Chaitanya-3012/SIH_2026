from sqlalchemy import (
    BigInteger,
    String,
    Double,
    DateTime,
    ForeignKey,
    func,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Reading(Base):
    __tablename__ = "readings"

    reading_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False
    )
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Double, nullable=True)
    pressure_hpa: Mapped[float | None] = mapped_column(Double, nullable=True)
    humidity_pct: Mapped[float | None] = mapped_column(Double, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="live")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped["Station"] = relationship(back_populates="readings")
    anomaly: Mapped["Anomaly"] = relationship(back_populates="reading", uselist=False)

    __table_args__ = (
        Index("idx_readings_station_ts_desc", "station_id", "ts.desc()"),
        Index("idx_readings_source", "source"),
        Index("idx_readings_ts", "ts.desc()"),
        CheckConstraint("source IN ('live', 'simulator', 'historical')", name="ck_readings_source"),
    )