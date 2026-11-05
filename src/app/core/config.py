from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_name: str = "Space Earth Dashboard"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://space:space@localhost:5432/space_dashboard"
    nasa_api_key: str = "DEMO_KEY"
    log_level: str = "INFO"
    scheduler_timezone: str = "UTC"
    iss_ingestion_interval_minutes: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
