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
    auth_client_id: str = ""
    auth_client_secret: str = ""
    auth_authorize_url: str = ""
    auth_token_url: str = ""
    retention_days: int = 30
    metrics_user: str = "metrics"
    metrics_password: str = "changeme"

    # AI gateway — off by default; FakeProvider in CI via AI_PROVIDER=fake
    ai_gateway_enabled: bool = False
    ai_provider: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4.1-mini"
    ai_daily_cap: int = 50
    ai_timeout_s: float = 12.0


settings = Settings()
