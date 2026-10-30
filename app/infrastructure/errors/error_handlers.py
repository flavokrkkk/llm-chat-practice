import logging
from collections.abc import Mapping
from typing import NamedTuple

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException

from app.core.schemas.error import ErrorDetail, ErrorResponse, ValidationErrorItem
from app.infrastructure.errors.exceptions import AppException

logger = logging.getLogger(__name__)

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
DATABASE_ERROR_CODE = "DATABASE_ERROR"
SERVICE_UNAVAILABLE_CODE = "SERVICE_UNAVAILABLE"


class DbErrorMapping(NamedTuple):
    status_code: int
    error_code: str
    message: str
    log_level: int


DB_ERRORS: dict[str, DbErrorMapping] = {
    "23505": DbErrorMapping(
        409, "CONFLICT", "Resource already exists", logging.WARNING
    ),
    "23503": DbErrorMapping(
        409,
        "REFERENCE_CONFLICT",
        "Referenced resource does not exist or is still in use",
        logging.WARNING,
    ),
    "23514": DbErrorMapping(
        409,
        "CONSTRAINT_VIOLATION",
        "Request violates data constraints",
        logging.WARNING,
    ),
    "40P01": DbErrorMapping(
        503,
        SERVICE_UNAVAILABLE_CODE,
        "Concurrent update conflict, please retry the request",
        logging.ERROR,
    ),
    "40001": DbErrorMapping(
        503,
        SERVICE_UNAVAILABLE_CODE,
        "Concurrent update conflict, please retry the request",
        logging.WARNING,
    ),
}

DEFAULT_DB_ERROR = DbErrorMapping(
    500, DATABASE_ERROR_CODE, "Database error occurred", logging.ERROR
)


def is_transient(exc) -> bool:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    return isinstance(sqlstate, str)


def _build_error_detail(
    code: str,
    message: str,
    details: list[ValidationErrorItem] | None = None,
) -> ErrorDetail:
    return ErrorDetail(code=code, message=message, details=details or [])


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
    details: list[ValidationErrorItem] | None = None,
) -> JSONResponse:
    error_detail = _build_error_detail(error_code, message, details)
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content=ErrorResponse(detail=error_detail).model_dump(mode="json"),
    )


async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    """Обработка ошибок домена и бизнес-логики приложения."""

    logger.warning(
        "AppException: code=%s, status=%s, message=%s",
        exc.error_code,
        exc.status_code,
        exc.message,
    )

    return _error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
    )


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Нормализация ошибок FastAPI (HTTPException) в единый формат ответа."""

    logger.warning("HTTPException: status=%s, detail=%s", exc.status_code, exc.detail)

    error_code = _error_code_by_status(exc.status_code)

    return _error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail) if exc.detail is not None else "Request error",
        headers=exc.headers,
    )


def _error_code_by_status(status_code: int) -> str:
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 405:
        return "METHOD_NOT_ALLOWED"
    if status_code == 429:
        return "RATE_LIMIT_EXCEEDED"
    if status_code == 400:
        return "BAD_REQUEST"
    if status_code == 409:
        return "CONFLICT"
    return "HTTP_ERROR"


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Обработка ошибок валидации входных данных (FastAPI / Pydantic)."""

    errors = [
        ValidationErrorItem(
            loc=list(error.get("loc") or []),
            msg=str(error.get("msg") or "Invalid input"),
            type=str(error.get("type") or "unknown"),
        )
        for error in exc.errors()
    ]

    logger.warning("Validation error: %s, path=%s", errors, request.url.path)

    return _error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Validation error",
        details=errors,
    )


async def database_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    """Обработка ошибок PostgreSQL, нормализация в единый формат ответа."""
    sqlstate = getattr(exc.orig, "sqlstate", None)

    mapping = (
        DB_ERRORS.get(sqlstate, DEFAULT_DB_ERROR)
        if isinstance(sqlstate, str)
        else DEFAULT_DB_ERROR
    )

    logger.log(
        mapping.log_level,
        "Database error: sqlstate=%s, path=%s",
        sqlstate,
        request.url.path,
        exc_info=mapping.status_code >= 500,
    )

    return _error_response(
        status_code=mapping.status_code,
        error_code=mapping.error_code,
        message=mapping.message,
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Fallback-обработчик: любая непредвиденная ошибка -> 500."""

    logger.exception("Unhandled exception: %s", exc)

    return _error_response(
        status_code=500,
        error_code=INTERNAL_ERROR_CODE,
        message="Internal server error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрация глобальных обработчиков ошибок в FastAPI-приложении."""

    app.add_exception_handler(AppException, app_exception_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(HTTPException, http_exception_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(DBAPIError, database_exception_handler)  # pyright: ignore[reportArgumentType]
    app.add_exception_handler(Exception, unhandled_exception_handler)
