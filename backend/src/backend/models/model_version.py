from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    Boolean,
    func,
    Index,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    model_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    benchmarks: Mapped[list["BenchmarkResult"]] = relationship(back_populates="model", lazy="dynamic")

    __table_args__ = (
        Index("idx_model_versions_type_tag", "model_type", "version_tag", unique=True),
        Index("idx_model_versions_active", "is_active", postgresql_where=(is_active == True)),
    )