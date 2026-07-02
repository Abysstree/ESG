from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RoleProfileRequest(BaseModel):
    role_category: str = Field(min_length=1)


class RoleProfileRead(BaseModel):
    id: int
    role_category: str
    provider: str | None
    mode: str | None
    input: dict[str, Any]
    role_profile: dict[str, Any]
    raw_model_response: Any
    status: str
    job_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoleProfileResult(BaseModel):
    provider: str
    mode: str
    input: dict[str, Any]
    role_profile: dict[str, Any]
    raw_model_response: Any = None
    status: str = "fresh"
    updated_at: datetime | None = None
