from functools import lru_cache

from pydantic import SecretStr, field_validator
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
    admin_api_token: SecretStr | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
