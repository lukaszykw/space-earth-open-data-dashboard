from datetime import UTC, date, datetime, time
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SpaceObservation


def _parse_observed_at(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _build_observation(data: dict[str, Any]) -> SpaceObservation:
    return SpaceObservation(
        source=data["source"],
        external_id=data.get("external_id"),
        title=data.get("title"),
        description=data.get("description"),
        media_type=data.get("media_type"),
        media_url=data.get("media_url"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        observed_at=_parse_observed_at(data.get("observed_at")),
        raw=data["raw"],
    )


async def save_observation(session: AsyncSession, data: dict[str, Any]) -> SpaceObservation:
    external_id = data.get("external_id")
    if external_id is None:
        observation = _build_observation(data)
        session.add(observation)
        await session.commit()
        await session.refresh(observation)
        return observation

    values = {
        "source": data["source"],
        "external_id": external_id,
        "title": data.get("title"),
        "description": data.get("description"),
        "media_type": data.get("media_type"),
        "media_url": data.get("media_url"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "observed_at": _parse_observed_at(data.get("observed_at")),
        "raw": data["raw"],
    }
    statement = (
        insert(SpaceObservation)
        .values(**values)
        .on_conflict_do_update(
            constraint="uq_observation_source_external",
            set_={
                key: value
                for key, value in values.items()
                if key not in {"source", "external_id"}
            },
        )
        .returning(SpaceObservation.id)
    )
    observation_id = (await session.execute(statement)).scalar_one()
    await session.commit()
    return await session.get_one(SpaceObservation, observation_id, populate_existing=True)


async def save_observations(
    session: AsyncSession,
    observations_data: list[dict[str, Any]],
) -> list[SpaceObservation]:
    if not observations_data:
        return []

    observations: list[SpaceObservation] = []
    for data in observations_data:
        observations.append(await save_observation(session, data))
    return observations


async def list_observations(
    session: AsyncSession,
    source: str | None = None,
    limit: int = 50,
) -> list[SpaceObservation]:
    statement: Select[tuple[SpaceObservation]] = select(SpaceObservation).order_by(
        SpaceObservation.created_at.desc()
    )
    if source:
        statement = statement.where(SpaceObservation.source == source)

    result = await session.execute(statement.limit(limit))
    return list(result.scalars().all())


async def list_observations_for_day(
    session: AsyncSession,
    source: str,
    target_date: date,
) -> list[SpaceObservation]:
    start_at = datetime.combine(target_date, time.min, tzinfo=UTC)
    end_at = datetime.combine(target_date, time.max, tzinfo=UTC)
    statement = (
        select(SpaceObservation)
        .where(SpaceObservation.source == source)
        .where(SpaceObservation.observed_at >= start_at)
        .where(SpaceObservation.observed_at <= end_at)
        .order_by(SpaceObservation.created_at.desc())
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_daily_summary(session: AsyncSession, target_date: date) -> dict[str, Any]:
    start_at = datetime.combine(target_date, time.min, tzinfo=UTC)
    end_at = datetime.combine(target_date, time.max, tzinfo=UTC)

    counts_statement = (
        select(SpaceObservation.source, func.count(SpaceObservation.id))
        .where(SpaceObservation.observed_at >= start_at)
        .where(SpaceObservation.observed_at <= end_at)
        .group_by(SpaceObservation.source)
    )
    counts_result = await session.execute(counts_statement)
    counts_by_source = {source: count for source, count in counts_result.all()}

    latest_statement = (
        select(SpaceObservation)
        .where(SpaceObservation.observed_at >= start_at)
        .where(SpaceObservation.observed_at <= end_at)
        .order_by(SpaceObservation.created_at.desc())
        .limit(1)
    )
    latest_result = await session.execute(latest_statement)
    latest_observation = latest_result.scalars().first()

    total = sum(counts_by_source.values())
    return {
        "date": target_date,
        "total_observations": total,
        "apod_count": counts_by_source.get("nasa_apod", 0),
        "iss_position_count": counts_by_source.get("open_notify_iss", 0),
        "neo_count": counts_by_source.get("nasa_neows", 0),
        "latest_observation": latest_observation,
    }
