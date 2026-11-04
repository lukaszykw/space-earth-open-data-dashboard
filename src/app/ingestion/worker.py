import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.logging import configure_logging
from app.ingestion.jobs import run_apod_ingestion, run_iss_ingestion, run_neo_ingestion

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(
        timezone=settings.scheduler_timezone,
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 300},
    )
    scheduler.add_job(run_apod_ingestion, "cron", hour=6, minute=0, id="daily-apod")
    scheduler.add_job(run_neo_ingestion, "cron", hour=6, minute=5, id="daily-neo")
    scheduler.add_job(
        run_iss_ingestion,
        "interval",
        minutes=settings.iss_ingestion_interval_minutes,
        id="iss-position",
    )
    return scheduler


async def serve() -> None:
    configure_logging()
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Ingestion scheduler started with %d jobs", len(scheduler.get_jobs()))
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(serve())
