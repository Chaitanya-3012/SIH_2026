from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    func,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Station(Base):
    __tablename__ = "stations"

    station_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    usaf: Mapped[str] = mapped_column(String(6), nullable=False)
    wban: Mapped[str] = mapped_column(String(5), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="IN")
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    is_metro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deployment_tier: Mapped[str] = mapped_column(String(10), nullable=False, default="central")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    readings: Mapped[list["Reading"]] = relationship(back_populates="station", lazy="dynamic")
    anomalies: Mapped[list["Anomaly"]] = relationship(back_populates="station", lazy="dynamic")
    drift_events: Mapped[list["DriftEvent"]] = relationship(back_populates="station", lazy="dynamic")
    health_snapshots: Mapped[list["SensorHealth"]] = relationship(back_populates="station", lazy="dynamic")
    benchmarks: Mapped[list["BenchmarkResult"]] = relationship(back_populates="station", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("usaf", "wban", name="uq_stations_usaf_wban"),
        Index("idx_stations_deployment_tier", "deployment_tier"),
        Index("idx_stations_location", "latitude", "longitude"),
    )