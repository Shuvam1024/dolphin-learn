"""Runtime settings. Environment variables override the defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", Path(".env")),
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://dolphin:dolphin@localhost:5432/dolphin"
    environment: str = "development"


settings = Settings()
