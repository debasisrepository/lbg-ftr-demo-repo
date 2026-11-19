import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: int, expiry_minutes: int | None = None) -> str:
    """Create a JWT access token."""
    if expiry_minutes is None:
        expiry_minutes = settings.jwt_expiry_minutes

    expire = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.InvalidTokenError:
        return None


def hash_token(token: str) -> str:
    """Hash a token for storage using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_dynamic_link_hash(payee_id: int, amount_minor: int, currency: str, profile_id: int) -> str:
    """Generate dynamic linking hash for SCA approval."""
    data = f"{payee_id}:{amount_minor}:{currency}:{profile_id}"
    return hashlib.sha256(data.encode()).hexdigest()
