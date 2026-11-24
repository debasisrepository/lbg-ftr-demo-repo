"""Application error hierarchy."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        """Initialize with message and optional error code."""
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class AuthenticationError(AppError):
    """Authentication failed."""

    pass


class AuthorizationError(AppError):
    """Authorization failed."""

    pass


class ValidationError(AppError):
    """Validation failed."""

    pass


class NotFoundError(AppError):
    """Resource not found."""

    pass


class ConflictError(AppError):
    """Resource conflict."""

    pass


class RateLimitError(AppError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        """Initialize with message and optional retry-after seconds."""
        super().__init__(message, code="rate_limited")
        self.retry_after = retry_after


class SapUnavailableError(AppError):
    """SAP adapter unavailable."""

    pass


class PolicyFailureError(AppError):
    """Policy validation failed."""

    def __init__(self, message: str, failed_conditions: list[dict], policy_evaluation_id: str | None = None):
        """Initialize with message, failed conditions, and optional evaluation ID."""
        super().__init__(message, code="policy_validation_failed")
        self.failed_conditions = failed_conditions
        self.policy_evaluation_id = policy_evaluation_id
