from pydantic import BaseModel, ConfigDict
from uuid import UUID

BaseId = UUID


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
