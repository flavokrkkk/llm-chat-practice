from pydantic import BaseModel, ConfigDict, model_validator
from uuid import UUID
from typing import Any
import asyncpg

BaseId = UUID


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def convert_asyncpg_record(cls, data: Any) -> Any:
        if isinstance(data, asyncpg.Record):
            return dict(data)
        return data
