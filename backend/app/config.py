"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_inactivity_timeout_minutes: int = 15
    bcrypt_cost_factor: int = 12
    
    # CORS
    cors_origins: str = "http://localhost:5173"
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_login_per_address_window_seconds: int = 300
    rate_limit_login_per_address_max_attempts: int = 5
    rate_limit_login_per_customer_window_seconds: int = 300
    rate_limit_login_per_customer_max_attempts: int = 10
    
    # Business Rules
    payment_limit_minor: int = 100000000
    freshness_target_seconds: int = 60
    scam_check_budget_ms: int = 300
    hold_decision_business_days: int = 4
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()  # type: ignore[call-arg]
