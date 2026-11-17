from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_seconds: int = 3600
    session_inactivity_seconds: int = 900
    rate_limit_enabled: bool = True
    cors_origins: str = "http://localhost:5173"
    debug: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}

    def validate_required(self) -> None:
        if not self.jwt_secret or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")


import os
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
_dev_env = _backend_dir / "dev.env"

if _dev_env.exists() and not os.path.exists(_backend_dir / ".env"):
    for _line in _dev_env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _value = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _value.strip())

settings = Settings()
if settings.jwt_secret and len(settings.jwt_secret) >= 32:
    pass
else:
    raise ValueError("JWT_SECRET must be set and at least 32 characters")
