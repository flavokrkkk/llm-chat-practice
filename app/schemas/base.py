from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

import asyncpg
from pydantic import BaseModel, ConfigDict, Field, model_validator

BaseId = UUID
T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def convert_asyncpg_record(cls, data: Any) -> Any:
        if isinstance(data, asyncpg.Record):
            return dict(data)
        return data


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
