from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProviderType = Literal["deepseek", "openai_compatible", "anthropic", "google"]


class LLMProviderConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider_type: ProviderType
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool = True
    is_active: bool = False


class LLMProviderConfigCreate(LLMProviderConfigBase):
    pass


class LLMProviderConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    provider_type: ProviderType | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool | None = None
    is_active: bool | None = None


class LLMProviderConfigRead(BaseModel):
    id: int
    name: str
    provider_type: str
    api_key_set: bool
    base_url: str | None
    model: str | None
    enabled: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMStatusRead(BaseModel):
    provider: str
    configured: bool
    model: str | None
    base_url: str | None
    active_provider_id: int | None = None
