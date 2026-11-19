"""Base adapter infrastructure with circuit breaker pattern"""
from abc import ABC
from datetime import UTC, datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Optional


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker for adapter calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 30,
        half_open_timeout_seconds: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_timeout = timedelta(seconds=half_open_timeout_seconds)

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._opened_at: Optional[datetime] = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            # Check if open circuit should transition to half-open
            if self._state == CircuitState.OPEN and self._opened_at:
                elapsed = datetime.now(UTC) - self._opened_at
                if elapsed >= self.half_open_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._failure_count = 0
            return self._state

    def record_success(self) -> None:
        """Record successful call"""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._opened_at = None

    def record_failure(self) -> None:
        """Record failed call"""
        with self._lock:
            now = datetime.now(UTC)

            # Reset count if outside window
            if self._last_failure_time and (now - self._last_failure_time) > self.timeout:
                self._failure_count = 0

            self._failure_count += 1
            self._last_failure_time = now

            # Open circuit if threshold exceeded
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = now

    def allow_request(self) -> bool:
        """Check if request should be allowed"""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return True  # Allow one probe request
        else:
            return False


class AdapterBase(ABC):
    """Base class for external system adapters"""

    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        self.circuit_breaker = CircuitBreaker()
