"""Application-specific exceptions."""


class DomainError(Exception):
    """Base exception for domain-level errors."""

    pass


class NotFoundError(DomainError):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    pass


class AuthorizationError(DomainError):
    """Raised when user is not authorized for an action."""

    pass


class ConcurrencyError(DomainError):
    """Raised when optimistic locking or concurrency conflict occurs."""

    pass


class DependencyUnavailable(DomainError):
    """External dependency unavailable error."""

    pass
