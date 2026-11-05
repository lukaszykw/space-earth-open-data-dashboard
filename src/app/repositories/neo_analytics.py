from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SpaceObservation


def _neo_range(start_date: date, end_date: date):
    start_at = datetime.combine(start_date, time.min, tzinfo=UTC)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
    return (
        SpaceObservation.source == "nasa_neows",
        SpaceObservation.observed_at >= start_at,
        SpaceObservation.observed_at < end_at,
    )


async def get_neo_analytics(
    session: AsyncSession,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    filters = _neo_range(start_date, end_date)
    summary_statement = select(
        func.count(SpaceObservation.id),
        func.count(SpaceObservation.id).filter(SpaceObservation.is_hazardous.is_(True)),
        func.avg(SpaceObservation.relative_velocity_kps),
        func.max(SpaceObservation.estimated_diameter_meters),
        func.min(SpaceObservation.miss_distance_km),
    ).where(*filters)
    summary = (await session.execute(summary_statement)).one()

    observed_date = func.date(SpaceObservation.observed_at).label("date")
    daily_statement = (
        select(
            observed_date,
            func.count(SpaceObservation.id).label("total"),
            func.count(SpaceObservation.id)
            .filter(SpaceObservation.is_hazardous.is_(True))
            .label("hazardous"),
        )
        .where(*filters)
        .group_by(observed_date)
        .order_by(observed_date)
    )
    daily = (await session.execute(daily_statement)).mappings().all()

    closest_statement = (
        select(SpaceObservation)
        .where(*filters, SpaceObservation.miss_distance_km.is_not(None))
        .order_by(SpaceObservation.miss_distance_km.asc())
        .limit(5)
    )
    closest = list((await session.execute(closest_statement)).scalars().all())

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_objects": summary[0],
        "hazardous_objects": summary[1],
        "average_velocity_kps": float(summary[2]) if summary[2] is not None else None,
        "largest_diameter_meters": summary[3],
        "closest_miss_distance_km": summary[4],
        "daily": [dict(row) for row in daily],
        "closest_approaches": closest,
    }
