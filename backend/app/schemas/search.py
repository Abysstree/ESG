from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SearchProviderType = Literal["exa", "tavily"]


class SearchProviderConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider_type: SearchProviderType
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool = True
    is_active: bool = False


class SearchProviderConfigCreate(SearchProviderConfigBase):
    pass


class SearchProviderConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider_type: SearchProviderType | None = None
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    is_active: bool | None = None


class SearchProviderConfigRead(BaseModel):
    id: int
    name: str
    provider_type: str
    api_key_set: bool
    base_url: str | None
    enabled: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchStatusRead(BaseModel):
    provider: str
    configured: bool
    base_url: str | None
    active_provider_id: int | None = None
