from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.auth.models import LoginAttempt
from app.config import settings
from app.core.clock import Clock


class LoginRateLimiter:
    MAX_ATTEMPTS = 5
    WINDOW_MINUTES = 15

    @staticmethod
    def check_rate_limit(db: Session, source_key: str, username: str) -> tuple[bool, str | None]:
        if not settings.rate_limit_enabled:
            return True, None

        now = Clock.utc_now()
        window_start = now - timedelta(minutes=LoginRateLimiter.WINDOW_MINUTES)

        result = db.execute(
            select(LoginAttempt).where(
                and_(
                    LoginAttempt.source_key == source_key,
                    LoginAttempt.username_attempted == username,
                    LoginAttempt.outcome == 'failed',
                    LoginAttempt.occurred_at >= window_start
                )
            )
        )
        attempts = result.scalars().all()

        if len(attempts) >= LoginRateLimiter.MAX_ATTEMPTS:
            return False, "rate_limited"

        return True, None

    @staticmethod
    def reset_on_success(db: Session, source_key: str, username: str) -> None:
        pass
