import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from asyncpg import (
    DeadlockDetectedError,
    PostgresError,
    UniqueViolationError,
)

from app.core.exceptions import AppException
from app.schemas.error import ErrorDetail, ErrorResponse, ValidationErrorItem

logger = logging.getLogger(__name__)

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
DATABASE_ERROR_CODE = "DATABASE_ERROR"
SERVICE_UNAVAILABLE_CODE = "SERVICE_UNAVAILABLE"


def _build_error_detail(
    code: str, message: str, details: list[ValidationErrorItem] | None = None
) -> ErrorDetail:
    return ErrorDetail(code=code, message=message, details=details or [])


def _error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: list[ValidationErrorItem] | None = None,
) -> JSONResponse:
    error_detail = _build_error_detail(error_code, message, details)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(detail=error_detail).model_dump(mode="json"),
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
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


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Нормализация ошибок FastAPI (HTTPException) в единый формат ответа."""

    logger.warning("HTTPException: status=%s, detail=%s", exc.status_code, exc.detail)

    error_code = _error_code_by_status(exc.status_code)

    return _error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail) if exc.detail is not None else "Request error",
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


async def database_exception_handler(
    request: Request, exc: PostgresError
) -> JSONResponse:
    """Обработка ошибок PostgreSQL, нормализация в единый формат ответа."""

    logger.error("Database error: code=%s, message=%s", exc.sqlstate, exc.message)

    return _error_response(
        status_code=500,
        error_code=DATABASE_ERROR_CODE,
        message="Database error occurred",
    )


async def deadlock_exception_handler(
    request: Request, exc: DeadlockDetectedError
) -> JSONResponse:
    """Ошибки взаимной блокировки транзакций (Deadlock)."""

    logger.error("Deadlock detected: code=%s, message=%s", exc.sqlstate, exc.message)

    return _error_response(
        status_code=503,
        error_code=SERVICE_UNAVAILABLE_CODE,
        message="Database deadlock detected, operation could be retried",
    )


async def unique_violation_exception_handler(
    request: Request, exc: UniqueViolationError
) -> JSONResponse:
    """Повторная вставка строки, нарушающая UNIQUE-ограничение."""

    logger.warning(
        "Unique violation: code=%s, constraint=%s", exc.sqlstate, exc.constraint_name
    )

    return _error_response(
        status_code=409,
        error_code="CONFLICT",
        message="Resource already exists",
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Fallback-обработчик: любая непредвиденная ошибка -> 500."""

    logger.exception("Unhandled exception: %s", exc)

    return _error_response(
        status_code=500,
        error_code=INTERNAL_ERROR_CODE,
        message="Internal server error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрация глобальных обработчиков ошибок в FastAPI-приложении."""

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DeadlockDetectedError, deadlock_exception_handler)
    app.add_exception_handler(UniqueViolationError, unique_violation_exception_handler)
    app.add_exception_handler(PostgresError, database_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
