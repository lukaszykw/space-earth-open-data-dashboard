from datetime import UTC, datetime
from typing import Any


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _date_to_utc_iso(value: str | None) -> str | None:
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=UTC).isoformat()


def normalize_apod(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "nasa_apod",
        "external_id": payload.get("date"),
        "title": payload.get("title"),
        "description": payload.get("explanation"),
        "media_type": payload.get("media_type"),
        "media_url": payload.get("url"),
        "observed_at": _date_to_utc_iso(payload.get("date")),
        "raw": payload,
    }


def normalize_iss_position(payload: dict[str, Any]) -> dict[str, Any]:
    position = payload.get("iss_position", {})
    timestamp = payload.get("timestamp")
    observed_at = datetime.fromtimestamp(timestamp, UTC).isoformat() if timestamp else None
    return {
        "source": "open_notify_iss",
        "external_id": str(timestamp) if timestamp else None,
        "latitude": _to_float(position.get("latitude")),
        "longitude": _to_float(position.get("longitude")),
        "observed_at": observed_at,
        "raw": payload,
    }


def normalize_neo_feed(payload: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    near_earth_objects = payload.get("near_earth_objects", {})

    for observed_date, objects in near_earth_objects.items():
        for item in objects:
            diameter = item.get("estimated_diameter", {}).get("meters", {})
            approaches = item.get("close_approach_data") or []
            approach = approaches[0] if approaches else {}
            observations.append(
                {
                    "source": "nasa_neows",
                    "external_id": item.get("id"),
                    "title": item.get("name"),
                    "description": item.get("nasa_jpl_url"),
                    "is_hazardous": item.get("is_potentially_hazardous_asteroid"),
                    "estimated_diameter_meters": _to_float(
                        diameter.get("estimated_diameter_max")
                    ),
                    "relative_velocity_kps": _to_float(
                        approach.get("relative_velocity", {}).get("kilometers_per_second")
                    ),
                    "miss_distance_km": _to_float(
                        approach.get("miss_distance", {}).get("kilometers")
                    ),
                    "observed_at": _date_to_utc_iso(observed_date),
                    "raw": item,
                }
            )

    return observations
