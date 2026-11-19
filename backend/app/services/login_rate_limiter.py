"""Login rate limiter service"""
from datetime import UTC, datetime, timedelta

from ..config import settings
from ..core.errors import RateLimitError


class LoginRateLimiter:
    """
    Rate limiter for authentication endpoints.
    In-process implementation for single-instance deployment.
    For production with multiple instances, replace with Redis-backed implementation.
    """

    def __init__(self):
        # identifier_hash -> list of attempt timestamps
        self._identifier_attempts: dict[str, list[datetime]] = {}
        # ip_hash -> list of attempt timestamps
        self._ip_attempts: dict[str, list[datetime]] = {}
        self._window_seconds = 15 * 60  # 15 minutes
        self._max_identifier_attempts = 5
        self._max_ip_attempts = 20

    def check_identifier(self, identifier_hash: str) -> None:
        """
        Check if identifier is within rate limit.
        Raises RateLimitError if limit exceeded.
        """
        if not settings.rate_limit_enabled:
            return

        self._cleanup_old_attempts()

        attempts = self._identifier_attempts.get(identifier_hash, [])
        cutoff = datetime.now(UTC) - timedelta(seconds=self._window_seconds)
        recent_attempts = [t for t in attempts if t >= cutoff]

        if len(recent_attempts) >= self._max_identifier_attempts:
            raise RateLimitError(
                "Too many login attempts. Please try again later."
            )

    def check_ip(self, ip_hash: str) -> None:
        """
        Check if IP is within rate limit.
        Raises RateLimitError if limit exceeded.
        """
        if not settings.rate_limit_enabled:
            return

        self._cleanup_old_attempts()

        attempts = self._ip_attempts.get(ip_hash, [])
        cutoff = datetime.now(UTC) - timedelta(seconds=self._window_seconds)
        recent_attempts = [t for t in attempts if t >= cutoff]

        if len(recent_attempts) >= self._max_ip_attempts:
            raise RateLimitError(
                "Too many requests from your location. Please try again later."
            )

    def record_attempt(self, identifier_hash: str, ip_hash: str | None) -> None:
        """Record an authentication attempt"""
        if not settings.rate_limit_enabled:
            return

        now = datetime.now(UTC)

        if identifier_hash not in self._identifier_attempts:
            self._identifier_attempts[identifier_hash] = []
        self._identifier_attempts[identifier_hash].append(now)

        if ip_hash:
            if ip_hash not in self._ip_attempts:
                self._ip_attempts[ip_hash] = []
            self._ip_attempts[ip_hash].append(now)

    def _cleanup_old_attempts(self) -> None:
        """Remove old attempts outside the window"""
        cutoff = datetime.now(UTC) - timedelta(seconds=self._window_seconds)

        # Clean identifier attempts
        for key in list(self._identifier_attempts.keys()):
            self._identifier_attempts[key] = [
                t for t in self._identifier_attempts[key] if t >= cutoff
            ]
            if not self._identifier_attempts[key]:
                del self._identifier_attempts[key]

        # Clean IP attempts
        for key in list(self._ip_attempts.keys()):
            self._ip_attempts[key] = [
                t for t in self._ip_attempts[key] if t >= cutoff
            ]
            if not self._ip_attempts[key]:
                del self._ip_attempts[key]

    def reset(self) -> None:
        """Reset all rate limit counters (for testing)"""
        self._identifier_attempts.clear()
        self._ip_attempts.clear()


# Global instance
_rate_limiter: LoginRateLimiter | None = None


def get_rate_limiter() -> LoginRateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = LoginRateLimiter()
    return _rate_limiter
