"""Security utilities: password hashing, JWT token generation, HMAC digest"""
import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from ..config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Hash a session token using SHA-256 for storage"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def hash_identifier(identifier: str) -> str:
    """Hash an identifier (email, IP) using SHA-256 for privacy"""
    return hashlib.sha256(identifier.encode('utf-8')).hexdigest()


def generate_session_token() -> str:
    """Generate a cryptographically secure session token"""
    return secrets.token_urlsafe(32)


def create_jwt_token(
    customer_id: uuid.UUID,
    session_id: uuid.UUID,
    auth_level: str,
    active_profile_id: uuid.UUID | None = None
) -> str:
    """Create a JWT token for a session"""
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.jwt_expiration_seconds)

    payload = {
        "sub": str(customer_id),
        "session_id": str(session_id),
        "auth_level": auth_level,
        "active_profile_id": str(active_profile_id) if active_profile_id else None,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict[str, object]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def generate_hmac_digest(secret: str, *components: str) -> str:
    """Generate an HMAC digest for dynamic linking or challenge binding"""
    message = "|".join(str(c) for c in components)
    digest = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return digest


def verify_hmac_digest(secret: str, expected_digest: str, *components: str) -> bool:
    """Verify an HMAC digest"""
    actual_digest = generate_hmac_digest(secret, *components)
    return hmac.compare_digest(expected_digest, actual_digest)
