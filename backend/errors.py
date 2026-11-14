"""LUNARIS common error format (F20 / F33). Owner: M1.

Every error the API returns has exactly this shape (docs/conventions.md):

    {"error": {"code": "INVALID_COORDINATE", "message": "...", "details": {}}}

HTTP status codes:
    400 invalid input   404 site not found
    501 feature not available yet   503 data / service unavailable
    500 unexpected bug (not part of the contract; we never leak a traceback)

How M1 / M2 / M3 use this:
    raise InvalidCoordinate("Latitude must be between -90 and 90.", {"lat": 95})
    raise SiteNotFound("zzz")
    raise ServiceUnavailable("Horizon file missing for site shackleton_rim")

Rule from the master guide: if M2/M3 have no data they return None fields +
warnings. They only `raise ServiceUnavailable` on a real failure.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("lunaris")


# --------------------------------------------------------------------------- #
# Error codes (single list, so frontend and tests use the same strings)
# --------------------------------------------------------------------------- #
class ErrorCode:
    INVALID_REQUEST = "INVALID_REQUEST"          # generic bad input
    INVALID_COORDINATE = "INVALID_COORDINATE"    # lat/lon out of range
    INVALID_DATE = "INVALID_DATE"                # bad or out-of-range time
    EMPTY_SCENARIO = "EMPTY_SCENARIO"            # compare/assessment with no scenarios
    SITE_NOT_FOUND = "SITE_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"                      # unknown route
    FEATURE_NOT_AVAILABLE = "FEATURE_NOT_AVAILABLE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class LunarisError(Exception):
    """Base class. Handlers turn it into the standard error JSON."""

    status_code: int = 500
    default_code: str = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.code = code or self.default_code


class InvalidInput(LunarisError):
    status_code = 400
    default_code = ErrorCode.INVALID_REQUEST


class InvalidCoordinate(InvalidInput):
    default_code = ErrorCode.INVALID_COORDINATE


class InvalidDate(InvalidInput):
    default_code = ErrorCode.INVALID_DATE


class SiteNotFound(LunarisError):
    status_code = 404
    default_code = ErrorCode.SITE_NOT_FOUND

    def __init__(self, site_id: str) -> None:
        super().__init__(f"Site '{site_id}' was not found.", {"site_id": site_id})


class FeatureNotAvailable(LunarisError):
    """501. Used for Tier 4 features (thermal) and anything not built yet."""

    status_code = 501
    default_code = ErrorCode.FEATURE_NOT_AVAILABLE


class ServiceUnavailable(LunarisError):
    """503. Data or an internal service (M2/M3 module) really failed."""

    status_code = 503
    default_code = ErrorCode.SERVICE_UNAVAILABLE


# --------------------------------------------------------------------------- #
# Response builder
# --------------------------------------------------------------------------- #
def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def error_response(
    status_code: int, code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(code, message, details))


# Fields whose validation failure maps to a specific error code.
_COORD_FIELDS = {"lat", "lon"}
_DATE_FIELDS = {"time_utc", "start_utc", "start_dates"}


def _classify_validation_error(errors: list[dict[str, Any]]) -> tuple[str, str]:
    """Pick the most specific code + a readable message from pydantic errors."""
    for err in errors:
        loc = [str(x) for x in err.get("loc", ())]
        if loc and loc[-1] in _COORD_FIELDS:
            return ErrorCode.INVALID_COORDINATE, (
                "Invalid coordinate: latitude must be -90..90 (south negative), "
                "longitude must be -180..180 (east positive)."
            )
    for err in errors:
        loc = [str(x) for x in err.get("loc", ())]
        if any(part in _DATE_FIELDS for part in loc):
            return ErrorCode.INVALID_DATE, (
                "Invalid date: use UTC ISO 8601, e.g. 2027-03-14T06:00:00Z, "
                "inside the supported date window."
            )
    for err in errors:
        loc = [str(x) for x in err.get("loc", ())]
        if "scenarios" in loc and err.get("type") == "too_short":
            return ErrorCode.EMPTY_SCENARIO, "At least one scenario is required (maximum 3)."
    return ErrorCode.INVALID_REQUEST, "The request body is not valid. See details."


def _clean_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only JSON-safe fields (pydantic's `ctx` can hold exception objects)."""
    return [
        {
            "field": ".".join(str(x) for x in e.get("loc", ()) if x != "body"),
            "message": e.get("msg", ""),
            "type": e.get("type", ""),
        }
        for e in errors
    ]


# --------------------------------------------------------------------------- #
# Handlers: call register_exception_handlers(app) once in main.py
# --------------------------------------------------------------------------- #
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LunarisError)
    async def _lunaris_error(_: Request, exc: LunarisError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        code, message = _classify_validation_error(errors)
        return error_response(400, code, message, {"errors": _clean_errors(errors)})

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error_response(404, ErrorCode.NOT_FOUND, "Route not found.")
        if exc.status_code == 405:
            return error_response(405, ErrorCode.INVALID_REQUEST, "Method not allowed.")
        return error_response(exc.status_code, ErrorCode.INTERNAL_ERROR, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return error_response(
            500, ErrorCode.INTERNAL_ERROR, "Unexpected server error. Please try again."
        )
