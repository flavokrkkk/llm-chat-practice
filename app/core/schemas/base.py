from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

BaseId = UUID
T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationResponse(BaseModel, Generic[T]):
    items: list[T] = Field(description="Список элементов для текущей страницы")
    total: int = Field(
        description="Общее количество элементов в базе данных по данному фильтру", ge=0
    )
    offset: int = Field(description="Отступ, который использовался в запросе", ge=0)
    limit: int = Field(
        description="Лимит элементов на страницу, который использовался в запросе", gt=0
    )


class CursorPaginationResponse(BaseModel, Generic[T]):
    items: list[T] = Field(description="Список элементов текущей страницы")
    next_created_at: Optional[datetime] = Field(
        None, description="created_at последнего элемента (передать в следующий запрос)"
    )
    next_id: Optional[UUID] = Field(
        None, description="id последнего элемента (передать в следующий запрос)"
    )
    limit: int = Field(description="Количество запрошенных элементов", gt=0)
