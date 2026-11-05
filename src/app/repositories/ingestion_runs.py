from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IngestionRun


async def start_ingestion_run(session: AsyncSession, job_name: str) -> IngestionRun:
    run = IngestionRun(job_name=job_name, status="running", records_processed=0)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def finish_ingestion_run(
    session: AsyncSession,
    run: IngestionRun,
    *,
    status: str,
    records_processed: int = 0,
    error_message: str | None = None,
) -> IngestionRun:
    run.status = status
    run.records_processed = records_processed
    run.error_message = error_message
    run.finished_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(run)
    return run


async def list_ingestion_runs(
    session: AsyncSession,
    limit: int = 20,
    status: str | None = None,
) -> list[IngestionRun]:
    statement: Select[tuple[IngestionRun]] = select(IngestionRun).order_by(
        IngestionRun.started_at.desc()
    )
    if status:
        statement = statement.where(IngestionRun.status == status)
    result = await session.execute(statement.limit(limit))
    return list(result.scalars().all())
