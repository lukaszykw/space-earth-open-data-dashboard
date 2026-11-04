import logging
from collections.abc import Awaitable, Callable
from datetime import date
from typing import TypeVar

from app.core.config import settings
from app.db.models import SpaceObservation
from app.db.session import AsyncSessionLocal
from app.ingestion.nasa_client import NasaClient
from app.ingestion.normalizers import normalize_apod, normalize_iss_position, normalize_neo_feed
from app.ingestion.open_notify_client import OpenNotifyClient
from app.repositories.ingestion_runs import finish_ingestion_run, start_ingestion_run
from app.repositories.space_observations import (
    list_observations_for_day,
    save_observation,
    save_observations,
)

logger = logging.getLogger(__name__)
ResultT = TypeVar("ResultT")


async def _tracked_run(
    job_name: str,
    operation: Callable[[], Awaitable[tuple[ResultT, int]]],
) -> ResultT:
    async with AsyncSessionLocal() as session:
        run = await start_ingestion_run(session, job_name)
        try:
            result, processed = await operation()
        except Exception as exc:
            await finish_ingestion_run(
                session,
                run,
                status="failed",
                error_message=str(exc)[:2000],
            )
            logger.exception("Ingestion job %s failed", job_name)
            raise
        await finish_ingestion_run(
            session,
            run,
            status="succeeded",
            records_processed=processed,
        )
        return result


async def run_apod_ingestion(target_date: date | None = None) -> SpaceObservation:
    effective_date = target_date or date.today()

    async def operation() -> tuple[SpaceObservation, int]:
        async with AsyncSessionLocal() as session:
            cached = await list_observations_for_day(session, "nasa_apod", effective_date)
            if cached:
                return cached[0], 0
            async with NasaClient(settings.nasa_api_key) as client:
                payload = await client.get_apod(effective_date)
            return await save_observation(session, normalize_apod(payload)), 1

    return await _tracked_run("apod", operation)


async def run_iss_ingestion() -> SpaceObservation:
    async def operation() -> tuple[SpaceObservation, int]:
        async with OpenNotifyClient() as client:
            payload = await client.get_iss_position()
        async with AsyncSessionLocal() as session:
            return await save_observation(session, normalize_iss_position(payload)), 1

    return await _tracked_run("iss_position", operation)


async def run_neo_ingestion(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[SpaceObservation]:
    effective_start = start_date or date.today()
    effective_end = end_date or effective_start

    async def operation() -> tuple[list[SpaceObservation], int]:
        async with NasaClient(settings.nasa_api_key) as client:
            payload = await client.get_neo_feed(effective_start, effective_end)
        async with AsyncSessionLocal() as session:
            observations = await save_observations(session, normalize_neo_feed(payload))
            return observations, len(observations)

    return await _tracked_run("neo", operation)
