"""Security utilities."""
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_jwt(user_id: str, session_id: str, scope: str) -> tuple[str, datetime]:
    """Create a JWT token."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.session_lifetime_minutes)

    payload = {
        "sub": user_id,
        "sid": str(session_id),
        "scope": scope,
        "iat": now.timestamp(),
        "exp": expires_at.timestamp(),
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_jwt(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return {}
