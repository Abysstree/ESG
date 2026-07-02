from datetime import datetime
import json
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class RawImport(Base):
    __tablename__ = "raw_imports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_value: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    job_cards: Mapped[list["JobCard"]] = relationship(back_populates="raw_import")


class JobCard(Base):
    __tablename__ = "job_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    raw_import_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_imports.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(120), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    base_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    education_requirement: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experience_requirement: Mapped[str | None] = mapped_column(String(120), nullable=True)
    responsibilities_json: Mapped[str] = mapped_column(Text, default="[]")
    requirements_json: Mapped[str] = mapped_column(Text, default="[]")
    bonus_points_json: Mapped[str] = mapped_column(Text, default="[]")
    skills_json: Mapped[str] = mapped_column(Text, default="[]")
    field_sources_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    confidence: Mapped[str] = mapped_column(String(32), default="low")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    raw_import: Mapped[RawImport | None] = relationship(back_populates="job_cards")

    @property
    def responsibilities(self) -> list[str]:
        return _loads_list(self.responsibilities_json)

    @property
    def requirements(self) -> list[str]:
        return _loads_list(self.requirements_json)

    @property
    def bonus_points(self) -> list[str]:
        return _loads_list(self.bonus_points_json)

    @property
    def skills(self) -> list[str]:
        return _loads_list(self.skills_json)

    @property
    def field_sources(self) -> dict[str, str]:
        value = _loads_json(self.field_sources_json, {})
        return value if isinstance(value, dict) else {}

    @property
    def evidence(self) -> dict[str, str | None]:
        value = _loads_json(self.evidence_json, {})
        return value if isinstance(value, dict) else {}


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    financing_stage: Mapped[str | None] = mapped_column(String(120), nullable=True)
    scale: Mapped[str | None] = mapped_column(String(120), nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    official_website: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_careers_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_urls_json: Mapped[str] = mapped_column(Text, default="[]")
    field_sources_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    inference_notes_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[str] = mapped_column(String(32), default="low")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def source_urls(self) -> list[str]:
        return _loads_list(self.source_urls_json)

    @property
    def field_sources(self) -> dict[str, str]:
        value = _loads_json(self.field_sources_json, {})
        return value if isinstance(value, dict) else {}

    @property
    def evidence(self) -> dict[str, str | None]:
        value = _loads_json(self.evidence_json, {})
        return value if isinstance(value, dict) else {}

    @property
    def inference_notes(self) -> list[str]:
        return _loads_list(self.inference_notes_json)


class RoleCategoryProfile(Base):
    __tablename__ = "role_category_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role_category: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    role_profile_json: Mapped[str] = mapped_column(Text, default="{}")
    raw_model_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="fresh")
    job_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def input(self) -> dict[str, Any]:
        value = _loads_json(self.input_json, {})
        return value if isinstance(value, dict) else {}

    @property
    def role_profile(self) -> dict[str, Any]:
        value = _loads_json(self.role_profile_json, {})
        return value if isinstance(value, dict) else {}

    @property
    def raw_model_response(self) -> Any:
        return _loads_json(self.raw_model_response_json, None)


class LLMProviderConfig(Base):
    __tablename__ = "llm_provider_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(64), index=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class SearchProviderConfig(Base):
    __tablename__ = "search_provider_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(64), index=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


def _loads_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _loads_list(value: str | None) -> list[str]:
    parsed = _loads_json(value, [])
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]
