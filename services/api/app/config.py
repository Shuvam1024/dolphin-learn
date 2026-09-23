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
    # Local stand-in for a managed OIDC issuer. Production sets ENVIRONMENT=production
    # and AUTH_JWKS_URL; the dev secret is never a user password.
    auth_issuer_url: str = "https://dolphin.local/dev"
    auth_audience: str = "dolphin-api"
    auth_jwks_url: str = ""
    auth_dev_secret: str = "dev-only-not-a-password"


settings = Settings()
