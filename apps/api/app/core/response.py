"""Consistent API response envelope.

Success:
    {"success": true,  "data": {...}, "error": null,              "meta": {}}

Error:
    {"success": false, "data": null,  "error": {"code": "...", "message": "..."}, "meta": {}}
"""

from typing import Any


def success_response(
    data: Any = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": meta or {},
    }


def error_response(
    code: str,
    message: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
        "meta": meta or {},
    }
