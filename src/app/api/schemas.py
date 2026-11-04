from datetime import date as date_type
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SpaceObservationRead(BaseModel):
    id: int
    source: str
    external_id: str | None = None
    title: str | None = None
    description: str | None = None
    media_type: str | None = None
    media_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    observed_at: datetime | None = None
    raw: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailySummaryRead(BaseModel):
    date: date_type
    total_observations: int
    apod_count: int
    iss_position_count: int
    neo_count: int
    latest_observation: SpaceObservationRead | None = None


class IngestionRunRead(BaseModel):
    id: int
    job_name: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    records_processed: int
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
