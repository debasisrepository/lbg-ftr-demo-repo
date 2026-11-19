class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class ValidationError(Exception):
    """Raised when business validation fails."""
    pass


class ExternalServiceError(Exception):
    """Raised when external service call fails."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass
