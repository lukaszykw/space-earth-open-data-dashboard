import os
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import IngestionRun, SpaceObservation
from app.repositories.ingestion_runs import (
    finish_ingestion_run,
    list_ingestion_runs,
    start_ingestion_run,
)
from app.repositories.space_observations import get_daily_summary, save_observation

pytestmark = pytest.mark.skipif(
    "TEST_DATABASE_URL" not in os.environ,
    reason="TEST_DATABASE_URL is required for PostgreSQL integration tests",
)


@pytest.mark.asyncio
async def test_upsert_is_idempotent_and_updates_daily_summary() -> None:
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    external_id = "integration-apod-2026-11-04"

    try:
        async with session_factory() as session:
            payload = {
                "source": "nasa_apod",
                "external_id": external_id,
                "title": "First title",
                "observed_at": datetime(2026, 11, 4, tzinfo=UTC),
                "raw": {"version": 1},
            }
            first = await save_observation(session, payload)
            payload["title"] = "Updated title"
            payload["raw"] = {"version": 2}
            second = await save_observation(session, payload)

            assert second.id == first.id
            assert second.title == "Updated title"

            summary = await get_daily_summary(session, date(2026, 11, 4))
            assert summary["apod_count"] >= 1

            await session.execute(
                delete(SpaceObservation).where(SpaceObservation.external_id == external_id)
            )
            await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ingestion_run_lifecycle_is_persisted() -> None:
    engine = create_async_engine(os.environ["TEST_DATABASE_URL"])
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            run = await start_ingestion_run(session, "integration-test")
            completed = await finish_ingestion_run(
                session,
                run,
                status="succeeded",
                records_processed=3,
            )

            assert completed.finished_at is not None
            assert completed.records_processed == 3
            runs = await list_ingestion_runs(session, status="succeeded")
            assert completed.id in {item.id for item in runs}

            await session.execute(delete(IngestionRun).where(IngestionRun.id == completed.id))
            await session.commit()
    finally:
        await engine.dispose()
