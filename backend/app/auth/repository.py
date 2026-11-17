from sqlalchemy.orm import Session
from sqlalchemy import select
from app.auth.models import AppUser, AuthSession, LoginAttempt
import uuid
from datetime import datetime


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> AppUser | None:
        result = self.db.execute(select(AppUser).where(AppUser.email == email))
        return result.scalar_one_or_none()

    def get_user_by_id(self, user_id: int) -> AppUser | None:
        result = self.db.execute(select(AppUser).where(AppUser.id == user_id))
        return result.scalar_one_or_none()

    def create_session(self, session: AuthSession) -> AuthSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        result = self.db.execute(
            select(AuthSession).where(AuthSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    def revoke_session(self, session_id: uuid.UUID) -> None:
        result = self.db.execute(
            select(AuthSession).where(AuthSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked = True
            self.db.commit()

    def record_login_attempt(self, attempt: LoginAttempt) -> LoginAttempt:
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def update_user_login_success(self, user: AppUser, now: datetime) -> None:
        user.failed_login_count = 0
        user.account_locked_until = None
        user.last_login_at = now
        self.db.commit()

    def increment_failed_login(self, user: AppUser) -> None:
        user.failed_login_count += 1
        self.db.commit()
