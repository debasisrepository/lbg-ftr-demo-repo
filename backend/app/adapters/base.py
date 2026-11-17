"""Base adapter interface and circuit breaker."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class AdapterHealth:
    """Health status of an adapter."""
    available: bool
    message: str
    last_check: datetime


class CircuitBreaker:
    """Circuit breaker for adapter calls."""
    
    def __init__(self, threshold: int = 5, timeout_seconds: int = 30):
        self.threshold = threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.is_open = False
    
    def record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.is_open = False
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.threshold:
            self.is_open = True
    
    def can_attempt(self) -> bool:
        """Check if a call can be attempted."""
        if not self.is_open:
            return True
        
        # Check if timeout has passed (half-open state)
        if self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            if elapsed >= self.timeout_seconds:
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


class Adapter(ABC):
    """Base adapter interface."""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
    
    @abstractmethod
    def health(self) -> AdapterHealth:
        """Check adapter health."""
        pass
