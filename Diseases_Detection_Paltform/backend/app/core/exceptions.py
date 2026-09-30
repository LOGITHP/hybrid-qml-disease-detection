"""Centralized application exception classes and standard error responses."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with standardized code and response details."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An unexpected error occurred. Please try again later.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details or {},
            },
        )
        self.code = code
        self.message = message
        self.details = details or {}


class AuthenticationError(AppException):
    """Raised when authentication fails or token is invalid."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when an access or refresh token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            details={"reason": "token_expired"},
        )


class PermissionDeniedError(AppException):
    """Raised when an authenticated user does not have permission for an action."""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message,
            details=details,
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource_type} not found." if not resource_id else f"{resource_type} with ID '{resource_id}' not found."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=message,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceConflictError(AppException):
    """Raised when creating a resource conflicts with an existing one (e.g. duplicate email)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            message=message,
            details=details,
        )


class ValidationError(AppException):
    """Raised for domain validation failures."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class CrossUserAccessError(PermissionDeniedError):
    """Raised when a user attempts to access a resource belonging to another tenant/user."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"Access to {resource_type} is denied. Resource belongs to another user.",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )
