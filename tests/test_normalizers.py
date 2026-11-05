from app.ingestion.normalizers import normalize_apod, normalize_iss_position, normalize_neo_feed


def test_normalize_apod_keeps_needed_fields() -> None:
    payload = {
        "date": "2026-05-21",
        "title": "Earth",
        "explanation": "Blue planet",
        "media_type": "image",
        "url": "https://example.com/earth.jpg",
        "unused": "ignored by consumers",
    }

    result = normalize_apod(payload)

    assert result["source"] == "nasa_apod"
    assert result["external_id"] == "2026-05-21"
    assert result["title"] == "Earth"
    assert result["observed_at"] == "2026-05-21T00:00:00+00:00"
    assert result["raw"] == payload


def test_normalize_iss_position_extracts_coordinates() -> None:
    result = normalize_iss_position(
        {
            "timestamp": 1_800_000_000,
            "iss_position": {"latitude": "51.1", "longitude": "17.0"},
        }
    )

    assert result["source"] == "open_notify_iss"
    assert result["external_id"] == "1800000000"
    assert result["latitude"] == 51.1
    assert result["longitude"] == 17.0


def test_normalize_neo_feed_flattens_objects() -> None:
    result = normalize_neo_feed(
        {
            "near_earth_objects": {
                "2026-05-21": [
                    {
                        "id": "1",
                        "name": "Asteroid 1",
                        "nasa_jpl_url": "https://example.com/neo/1",
                        "is_potentially_hazardous_asteroid": True,
                        "estimated_diameter": {
                            "meters": {"estimated_diameter_max": 142.5}
                        },
                        "close_approach_data": [
                            {
                                "relative_velocity": {"kilometers_per_second": "12.75"},
                                "miss_distance": {"kilometers": "750000.5"},
                            }
                        ],
                    }
                ]
            }
        }
    )

    assert result == [
        {
            "source": "nasa_neows",
            "external_id": "1",
            "title": "Asteroid 1",
            "description": "https://example.com/neo/1",
            "is_hazardous": True,
            "estimated_diameter_meters": 142.5,
            "relative_velocity_kps": 12.75,
            "miss_distance_km": 750000.5,
            "observed_at": "2026-05-21T00:00:00+00:00",
            "raw": {
                "id": "1",
                "name": "Asteroid 1",
                "nasa_jpl_url": "https://example.com/neo/1",
                "is_potentially_hazardous_asteroid": True,
                "estimated_diameter": {"meters": {"estimated_diameter_max": 142.5}},
                "close_approach_data": [
                    {
                        "relative_velocity": {"kilometers_per_second": "12.75"},
                        "miss_distance": {"kilometers": "750000.5"},
                    }
                ],
            },
        }
    ]
