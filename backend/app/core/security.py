"""Security utilities for password hashing and token generation."""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, session_id: str, expires_delta: timedelta) -> str:
    """Create JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = {
        "sub": user_id,
        "jti": session_id,
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def hash_token(token: str) -> str:
    """Hash token using SHA-256 for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
