from datetime import datetime

from pydantic import BaseModel, Field


class JobCardRead(BaseModel):
    id: int
    raw_import_id: int | None
    title: str
    company_name: str | None
    role_category: str | None
    salary_range: str | None
    salary_period: str | None
    base_location: str | None
    education_requirement: str | None
    experience_requirement: str | None
    responsibilities: list[str]
    requirements: list[str]
    bonus_points: list[str]
    skills: list[str]
    field_sources: dict[str, str]
    evidence: dict[str, str | None]
    confidence: str
    status: str
    is_pinned: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class JobCardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    company_name: str | None = None
    role_category: str | None = None
    salary_range: str | None = None
    salary_period: str | None = None
    base_location: str | None = None
    education_requirement: str | None = None
    experience_requirement: str | None = None
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    bonus_points: list[str] | None = None
    skills: list[str] | None = None
    confidence: str | None = None
    is_pinned: bool | None = None
    sort_order: int | None = None


class JobCardReorder(BaseModel):
    job_ids: list[int] = Field(min_length=1)
