from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    DailySummaryRead,
    IngestionRunRead,
    NeoAnalyticsRead,
    SpaceObservationRead,
)
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.ingestion.jobs import run_apod_ingestion, run_iss_ingestion, run_neo_ingestion
from app.ingestion.nasa_client import NasaClient
from app.ingestion.open_notify_client import OpenNotifyClient
from app.repositories.ingestion_runs import list_ingestion_runs
from app.repositories.neo_analytics import get_neo_analytics
from app.repositories.space_observations import (
    get_daily_summary,
    list_observations,
)

router = APIRouter()


def _validate_neo_date_range(start_date: date, end_date: date | None) -> date:
    effective_end = end_date or start_date
    if effective_end < start_date:
        raise HTTPException(status_code=422, detail="end_date must not be earlier than start_date")
    if (effective_end - start_date).days > 7:
        raise HTTPException(status_code=422, detail="NASA NeoWs accepts ranges of at most 8 days")
    return effective_end


@router.get("/apod")
async def get_apod(
    target_date: date | None = None,
    settings: Settings = Depends(get_settings),
) -> dict:
    async with NasaClient(settings.nasa_api_key) as client:
        return await client.get_apod(target_date)


@router.get("/iss-position")
async def get_iss_position() -> dict:
    async with OpenNotifyClient() as client:
        return await client.get_iss_position()


@router.get("/neo")
async def get_near_earth_objects(
    start_date: date,
    end_date: date | None = None,
    settings: Settings = Depends(get_settings),
) -> dict:
    effective_end = _validate_neo_date_range(start_date, end_date)
    async with NasaClient(settings.nasa_api_key) as client:
        return await client.get_neo_feed(start_date, effective_end)


@router.post("/ingest/apod", response_model=SpaceObservationRead)
async def ingest_apod(
    target_date: date | None = None,
) -> SpaceObservationRead:
    observation = await run_apod_ingestion(target_date)
    return SpaceObservationRead.model_validate(observation)


@router.post("/ingest/iss-position", response_model=SpaceObservationRead)
async def ingest_iss_position(
) -> SpaceObservationRead:
    observation = await run_iss_ingestion()
    return SpaceObservationRead.model_validate(observation)


@router.post("/ingest/neo", response_model=list[SpaceObservationRead])
async def ingest_near_earth_objects(
    start_date: date,
    end_date: date | None = None,
) -> list[SpaceObservationRead]:
    effective_end = _validate_neo_date_range(start_date, end_date)
    observations = await run_neo_ingestion(start_date, effective_end)
    return [SpaceObservationRead.model_validate(observation) for observation in observations]


@router.get("/ingestion-runs", response_model=list[IngestionRunRead])
async def get_ingestion_runs(
    status: str | None = Query(default=None, pattern="^(running|succeeded|failed)$"),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[IngestionRunRead]:
    runs = await list_ingestion_runs(session, limit=limit, status=status)
    return [IngestionRunRead.model_validate(run) for run in runs]


@router.get("/analytics/neo", response_model=NeoAnalyticsRead)
async def get_near_earth_object_analytics(
    start_date: date | None = None,
    end_date: date | None = None,
    session: AsyncSession = Depends(get_session),
) -> NeoAnalyticsRead:
    effective_end = end_date or date.today()
    effective_start = start_date or effective_end - timedelta(days=29)
    if effective_end < effective_start:
        raise HTTPException(status_code=422, detail="end_date must not be earlier than start_date")
    if (effective_end - effective_start).days > 365:
        raise HTTPException(status_code=422, detail="Analytics range cannot exceed 366 days")
    analytics = await get_neo_analytics(session, effective_start, effective_end)
    return NeoAnalyticsRead.model_validate(analytics)


@router.get("/observations", response_model=list[SpaceObservationRead])
async def get_observations(
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[SpaceObservationRead]:
    observations = await list_observations(session, source=source, limit=limit)
    return [SpaceObservationRead.model_validate(observation) for observation in observations]


@router.get("/daily-summary", response_model=DailySummaryRead)
async def get_daily_space_summary(
    target_date: date | None = None,
    session: AsyncSession = Depends(get_session),
) -> DailySummaryRead:
    summary = await get_daily_summary(session, target_date or date.today())
    latest_observation = summary["latest_observation"]
    return DailySummaryRead(
        date=summary["date"],
        total_observations=summary["total_observations"],
        apod_count=summary["apod_count"],
        iss_position_count=summary["iss_position_count"],
        neo_count=summary["neo_count"],
        latest_observation=(
            SpaceObservationRead.model_validate(latest_observation)
            if latest_observation is not None
            else None
        ),
    )
