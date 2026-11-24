"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./app.db"
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440
    inactivity_timeout_seconds: int = 1800
    cors_origins: str = "http://localhost:5173"
    rate_limit_enabled: bool = True
    rate_limit_max_attempts: int = 10
    rate_limit_window_minutes: int = 15
    customer_context_stale_seconds: int = 3600
    debug: bool = False
    load_seed_data: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
