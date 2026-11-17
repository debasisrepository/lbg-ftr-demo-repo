class AppError(Exception):
    pass


class AuthenticationError(AppError):
    pass


class AuthorizationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


class RateLimitError(AppError):
    pass
