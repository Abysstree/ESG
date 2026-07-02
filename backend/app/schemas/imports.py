from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["url", "text", "screenshot"]


class RawImportCreate(BaseModel):
    source_type: SourceType
    source_value: str = Field(min_length=1)
    raw_text: str | None = None


class RawImportRead(BaseModel):
    id: int
    source_type: str
    source_value: str
    raw_text: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

