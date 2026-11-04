from app.core.config import Settings


def test_render_postgres_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(database_url="postgres://user:secret@db.example.com:5432/space")

    assert settings.database_url == (
        "postgresql+asyncpg://user:secret@db.example.com:5432/space"
    )
