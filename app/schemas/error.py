from pydantic import BaseModel, Field
from typing import Any, Optional


class ValidationErrorItem(BaseModel):
    """Отдельная ошибка валидации входных данных (Pydantic / FastAPI)."""

    loc: list[Any] = Field(default_factory=list, description="Путь к ошибке валидации")
    msg: str = Field(..., description="Читаемое описание ошибки")
    type: str = Field(..., description="Тип ошибки валидации")


class ErrorDetail(BaseModel):
    """Детали ошибки в формате тела ответа: {"detail": {...}}."""

    code: str = Field(..., description="Код ошибки: NOT_FOUND, VALIDATION_ERROR и т.д.")
    message: str = Field(..., description="Человекочитаемое сообщение об ошибке")
    details: list[ValidationErrorItem] = Field(
        default_factory=list, description="Дополнительные детали ошибки"
    )


class ErrorResponse(BaseModel):
    """Единый формат ошибок во всех endpoint'ах проекта."""

    detail: ErrorDetail
