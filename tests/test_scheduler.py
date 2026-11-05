from app.ingestion.worker import create_scheduler


def test_scheduler_registers_expected_jobs() -> None:
    scheduler = create_scheduler()

    assert {job.id for job in scheduler.get_jobs()} == {
        "daily-apod",
        "daily-neo",
        "iss-position",
    }
