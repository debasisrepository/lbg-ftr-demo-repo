"""Application configuration using pydantic-settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "sqlite:///./app.db"

    # Security
    secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 1800

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Session configuration (NFR-001)
    session_max_seconds: int = 1800
    session_inactivity_seconds: int = 300
    session_warn_after_seconds: int = 240
    signin_proof_window_seconds: int = 300

    # Rate limiting
    rate_limit_enabled: bool = False

    # Adapter modes
    adapter_mode_ciam: str = "stub"
    adapter_mode_mandate: str = "stub"
    adapter_mode_core_banking: str = "stub"
    adapter_mode_loan: str = "stub"
    adapter_mode_payee_directory: str = "stub"
    adapter_mode_cop: str = "stub"
    adapter_mode_payment_orchestration: str = "stub"
    adapter_mode_payments_hub: str = "stub"
    adapter_mode_fraud_decision: str = "stub"
    adapter_mode_fraud_case: str = "stub"
    adapter_mode_notification: str = "stub"
    adapter_mode_observability: str = "stub"
    adapter_mode_support_routing: str = "stub"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
