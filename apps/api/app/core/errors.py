"""Typed application errors mapped to HTTP status codes."""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    INVALID_ACTION_STATE = "INVALID_ACTION_STATE"
    HABITAT_ACCESS_DENIED = "HABITAT_ACCESS_DENIED"
    AI_PROVIDER_ERROR = "AI_PROVIDER_ERROR"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.PERMISSION_DENIED: 403,
    ErrorCode.CAPABILITY_DENIED: 403,
    ErrorCode.ACTION_NOT_FOUND: 404,
    ErrorCode.INVALID_ACTION_STATE: 409,
    ErrorCode.HABITAT_ACCESS_DENIED: 403,
    ErrorCode.AI_PROVIDER_ERROR: 502,
    ErrorCode.DATABASE_UNAVAILABLE: 503,
    ErrorCode.INTERNAL_ERROR: 500,
}


class AppError(Exception):
    """Application-level error that maps to a structured API response.

    Raise this anywhere in the service/repository layer.
    The exception handler in main.py converts it to the response envelope.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details
        self.status_code = _STATUS_MAP.get(code, 500)
        super().__init__(message)
