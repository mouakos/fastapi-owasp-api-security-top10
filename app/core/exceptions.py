"""Custom exceptions for the application."""

from typing import Any


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the AppError with a message, status code, error code, and optional details."""
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: Any, message: str | None = None) -> None:  # noqa: ANN401
        """Initialize the NotFoundError with a resource, resource ID, and optional message."""
        super().__init__(
            message=message or f"{resource} with ID {resource_id} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": str(resource_id)},
        )


class ValidationError(AppError):
    """Input validation failed."""

    def __init__(self, field: str, message: str, value: Any = None) -> None:  # noqa: ANN401
        """Initialize the ValidationError with a field, message, and optional value."""
        super().__init__(
            message=f"Validation error on field '{field}': {message}",
            status_code=422,
            error_code="INVALID_INPUT",
            details={"field": field, "value": str(value) if value else None},
        )


class AuthenticationError(AppError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication required") -> None:  # noqa: ANN401
        """Initialize the AuthenticationError with an optional message."""
        super().__init__(message=message, status_code=401, error_code="AUTHENTICATION_FAILED")


class AuthorizationError(AppError):
    """User lacks permission."""

    def __init__(self, action: str, resource: str, message: str | None = None) -> None:  # noqa: ANN401
        """Initialize the AuthorizationError with an action, resource, and optional message."""
        super().__init__(
            message=message or f"Not authorized to {action} {resource}",
            status_code=403,
            error_code="PERMISSION_DENIED",
            details={"action": action, "resource": resource},
        )


class ConflictError(AppError):
    """Resource conflict, like duplicate entries."""

    def __init__(self, resource: str, message: str | None = None) -> None:
        """Initialize the ConflictError with a resource and optional message."""
        super().__init__(
            message=message or f"{resource} already exists",
            status_code=409,
            error_code="RESOURCE_CONFLICT",
            details={"resource": resource},
        )


class ExternalServiceError(AppError):
    """Third-party service failed."""

    def __init__(self, service: str, message: str | None = None) -> None:
        """Initialize the ExternalServiceError with a service and optional message."""
        super().__init__(
            message=message or f"External service '{service}' is unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service},
        )
