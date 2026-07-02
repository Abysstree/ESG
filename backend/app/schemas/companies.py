from datetime import datetime

from pydantic import BaseModel, Field


class CompanyProfileRead(BaseModel):
    id: int
    company_name: str
    summary: str | None
    industry: str | None
    financing_stage: str | None
    scale: str | None
    headquarters: str | None
    official_website: str | None
    official_careers_url: str | None
    source_urls: list[str]
    field_sources: dict[str, str]
    evidence: dict[str, str | None]
    inference_notes: list[str]
    confidence: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyProfileEnrichRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
