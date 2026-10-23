"""Domain errors.

The business code raises these and never imports anything from the web framework. One handler in
`main.py` turns any of them into an HTTP response, so the same classes work in the API, scripts and tests.
"""


class AppError(Exception):
    """Base class. Each subclass carries the HTTP status it should become."""

    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ImageRejected(AppError):
    """The uploaded file failed a quality check (wrong type, too big, unreadable, too small, too blurry)."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


class InvalidInput(AppError):
    status_code = 422


class AuthenticationFailed(AppError):
    status_code = 401


class Conflict(AppError):
    status_code = 409


class NotFound(AppError):
    status_code = 404


class ModelNotReady(AppError):
    status_code = 503
