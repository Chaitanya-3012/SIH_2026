from sqlalchemy import (
    BigInteger,
    String,
    Double,
    DateTime,
    ForeignKey,
    func,
    Index,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    anomaly_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reading_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    station_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False
    )
    ts: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Double, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    root_cause_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shap_values: Mapped[dict] = mapped_column(JSON, nullable=True)
    component_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    station: Mapped["Station"] = relationship(back_populates="anomalies")

    __table_args__ = (
        Index("idx_anomalies_station_ts_desc", "station_id", "ts"),
        Index("idx_anomalies_status_open", "status", postgresql_where=(status == "open")),
        Index("idx_anomalies_reading_id", "reading_id"),
        Index("idx_anomalies_ts", "ts"),
        CheckConstraint(
            "anomaly_type IN ('spike', 'drift', 'frozen', 'dropout', 'multivariate', 'unknown')",
            name="ck_anomalies_type"
        ),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_anomalies_confidence"),
        CheckConstraint("severity IN ('low', 'medium', 'high')", name="ck_anomalies_severity"),
        CheckConstraint("status IN ('open', 'reviewed', 'dismissed')", name="ck_anomalies_status"),
    )