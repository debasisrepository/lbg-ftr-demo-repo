"""Application configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = Field(default="sqlite:///./app.db")
    status_database_url: str = Field(default="")

    # Application role
    app_role: str = Field(default="case")

    # JWT
    jwt_secret: str = Field(default="change-me")
    jwt_algorithm: str = Field(default="HS256")

    # Session management
    session_lifetime_minutes: int = Field(default=30)
    session_inactivity_minutes: int = Field(default=15)
    session_max_minutes: int = Field(default=480)

    # Login security
    login_failure_threshold: int = Field(default=5)
    login_lock_minutes: int = Field(default=15)

    # CORS
    cors_allow_origins: str = Field(default="http://localhost:5173")

    # External integrations
    adapter_mode: str = Field(default="sandbox")
    gateway_base_url: str = Field(default="http://localhost:8080")

    # Timeouts and intervals
    ai_timeout_seconds: int = Field(default=5)
    tool_credential_ttl_seconds: int = Field(default=900)
    notification_link_ttl_hours: int = Field(default=24)
    incident_poll_seconds: int = Field(default=20)
    sweep_interval_seconds: int = Field(default=15)
    status_max_age_seconds: int = Field(default=60)

    # Defaults
    default_redirect_journey_code: str = Field(default="existing_support")
    intake_default_owner_team_code: str = Field(default="INTAKE_DEFAULT")
    status_resolved_tail_minutes: int = Field(default=30)

    # Observability
    log_level: str = Field(default="INFO")
    otel_exporter_otlp_endpoint: str = Field(default="")

    # Feature flags
    docs_enabled: bool = Field(default=True)
    rate_limit_enabled: bool = Field(default=True)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
