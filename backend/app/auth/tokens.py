import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.core.clock import Clock
import uuid


class TokenService:
    @staticmethod
    def create_token(user_id: int, session_id: uuid.UUID) -> str:
        now = Clock.utc_now()
        payload = {
            "sub": str(user_id),
            "jti": str(session_id),
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=settings.jwt_expiry_seconds)).timestamp(),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
