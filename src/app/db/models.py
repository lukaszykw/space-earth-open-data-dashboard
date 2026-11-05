from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SpaceObservation(Base):
    __tablename__ = "space_observations"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_observation_source_external"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    external_id: Mapped[str | None] = mapped_column(String(120), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    media_type: Mapped[str | None] = mapped_column(String(40))
    media_url: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    is_hazardous: Mapped[bool | None] = mapped_column(Boolean)
    estimated_diameter_meters: Mapped[float | None] = mapped_column(Float)
    relative_velocity_kps: Mapped[float | None] = mapped_column(Float)
    miss_distance_km: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
