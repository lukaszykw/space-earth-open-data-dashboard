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
    is_hazardous: bool | None = None
    estimated_diameter_meters: float | None = None
    relative_velocity_kps: float | None = None
    miss_distance_km: float | None = None
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


class NeoDailyMetric(BaseModel):
    date: date_type
    total: int
    hazardous: int


class NeoAnalyticsRead(BaseModel):
    start_date: date_type
    end_date: date_type
    total_objects: int
    hazardous_objects: int
    average_velocity_kps: float | None
    largest_diameter_meters: float | None
    closest_miss_distance_km: float | None
    daily: list[NeoDailyMetric]
    closest_approaches: list[SpaceObservationRead]
