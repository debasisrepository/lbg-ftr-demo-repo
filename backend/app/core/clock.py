"""Clock abstraction for testable time-dependent logic."""
from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Protocol for clock implementations."""

    def now(self) -> datetime:
        """Return current UTC datetime."""
        ...


class SystemClock:
    """Production clock using system time."""

    def now(self) -> datetime:
        """Return current UTC datetime."""
        return datetime.now(timezone.utc)


class FixedClock:
    """Test clock with fixed time."""

    def __init__(self, fixed_time: datetime):
        """Initialize with fixed time."""
        self._time = fixed_time

    def now(self) -> datetime:
        """Return fixed UTC datetime."""
        return self._time

    def set_time(self, new_time: datetime) -> None:
        """Update fixed time."""
        self._time = new_time


# Global clock instance for dependency injection
clock: Clock = SystemClock()
