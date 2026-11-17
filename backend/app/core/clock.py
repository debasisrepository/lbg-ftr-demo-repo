"""Clock abstraction for testable time operations."""
from datetime import datetime, timezone


class Clock:
    """Provides current UTC time."""

    @staticmethod
    def utcnow() -> datetime:
        """Get current UTC time with timezone info."""
        return datetime.now(timezone.utc)
