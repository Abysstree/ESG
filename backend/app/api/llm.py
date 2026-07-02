from dataclasses import asdict

from pydantic import BaseModel, Field, ValidationError
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import LLMProviderConfig
from app.extraction.llm_schema import LLMExtractedJobCard, build_job_extraction_prompt
from app.llm.providers import (
    LLMProvider,
    build_llm_provider,
    get_llm_provider,
    get_llm_status,
    provider_settings_from_config,
)
from app.schemas.llm import (
    LLMProviderConfigCreate,
    LLMProviderConfigRead,
    LLMProviderConfigUpdate,
    LLMStatusRead,
)
from app.services.llm_configs import (
    activate_llm_provider_config,
    create_llm_provider_config,
    ensure_default_llm_configs,
    get_active_llm_provider_config,
    to_llm_provider_config_read,
)
from app.services.api_keys import encrypt_api_key

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMExtractPreviewRequest(BaseModel):
    raw_text: str = Field(min_length=1)


IMPORTANT_JOB_CARD_FIELDS = (
    "title",
    "company_name",
    "role_category",
    "salary_range",
    "salary_period",
    "base_location",
    "education_requirement",
    "experience_requirement",
    "responsibilities",
    "requirements",
    "bonus_points",
    "skills",
)


@router.get("/status", response_model=LLMStatusRead)
def llm_status(session: Session = Depends(get_session)) -> LLMStatusRead:
    active_config = get_active_llm_provider_config(session)
    if active_config:
        return LLMStatusRead(
            provider=active_config.provider_type,
            configured=bool(active_config.api_key),
            model=active_config.model,
            base_url=active_config.base_url,
            active_provider_id=active_config.id,
        )

    return LLMStatusRead(**get_llm_status(), active_provider_id=None)


@router.get("/providers", response_model=list[LLMProviderConfigRead])
def list_llm_provider_configs(
    session: Session = Depends(get_session),
) -> list[LLMProviderConfigRead]:
    ensure_default_llm_configs(session)
    provider_priority = case(
        (LLMProviderConfig.provider_type == "deepseek", 0),
        (LLMProviderConfig.provider_type == "openai_compatible", 1),
        (LLMProviderConfig.provider_type == "anthropic", 2),
        (LLMProviderConfig.provider_type == "google", 3),
        else_=100,
    )
    statement = select(LLMProviderConfig).order_by(
        provider_priority,
        LLMProviderConfig.created_at.asc(),
    )
    return [
        to_llm_provider_config_read(config)
        for config in session.scalars(statement)
    ]


@router.post("/providers", response_model=LLMProviderConfigRead)
def create_provider_config(
    payload: LLMProviderConfigCreate,
    session: Session = Depends(get_session),
) -> LLMProviderConfigRead:
    config = create_llm_provider_config(payload, session)
    return to_llm_provider_config_read(config)


@router.patch("/providers/{provider_id}", response_model=LLMProviderConfigRead)
def update_provider_config(
    provider_id: int,
    payload: LLMProviderConfigUpdate,
    session: Session = Depends(get_session),
) -> LLMProviderConfigRead:
    config = session.get(LLMProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM provider config not found.")

    update_data = payload.model_dump(exclude_unset=True)
    activate_after_update = bool(update_data.pop("is_active", False))
    if "api_key" in update_data:
        update_data["api_key"] = encrypt_api_key(update_data["api_key"])

    for field_name, value in update_data.items():
        setattr(config, field_name, value)

    session.add(config)
    session.commit()
    session.refresh(config)

    if activate_after_update:
        activated_config = activate_llm_provider_config(config.id, session)
        if activated_config:
            config = activated_config

    return to_llm_provider_config_read(config)


@router.post("/providers/{provider_id}/activate", response_model=LLMProviderConfigRead)
def activate_provider_config(
    provider_id: int,
    session: Session = Depends(get_session),
) -> LLMProviderConfigRead:
    config = activate_llm_provider_config(provider_id, session)
    if not config:
        raise HTTPException(status_code=404, detail="LLM provider config not found.")
    return to_llm_provider_config_read(config)


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_config(
    provider_id: int,
    session: Session = Depends(get_session),
) -> Response:
    config = session.get(LLMProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM provider config not found.")

    session.delete(config)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/extract-preview")
def llm_extract_preview(
    payload: LLMExtractPreviewRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    try:
        active_config = get_active_llm_provider_config(session)
        provider = (
            build_llm_provider(provider_settings_from_config(active_config))
            if active_config
            else get_llm_provider()
        )
        return _build_extract_preview_response(
            provider=provider,
            raw_text=payload.raw_text,
            config=active_config,
        )
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/providers/{provider_id}/extract-preview")
def provider_extract_preview(
    provider_id: int,
    payload: LLMExtractPreviewRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    config = session.get(LLMProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM provider config not found.")

    try:
        provider = build_llm_provider(provider_settings_from_config(config))
        return _build_extract_preview_response(
            provider=provider,
            raw_text=payload.raw_text,
            config=config,
        )
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _build_extract_preview_response(
    provider: LLMProvider,
    raw_text: str,
    config: LLMProviderConfig | None,
) -> dict[str, object]:
    prompt = build_job_extraction_prompt(raw_text)
    result = provider.extract_job_card(raw_text)
    extracted_payload = result.get("job_card")
    extracted = LLMExtractedJobCard.model_validate(extracted_payload)
    normalized = extracted.to_extracted_job_card()

    return {
        "provider": result.get("provider", provider.name),
        "mode": result.get("mode", "cloud"),
        "model": config.model if config else None,
        "base_url": config.base_url if config else None,
        "prompt": prompt,
        "extracted_schema": extracted.model_dump(),
        "normalized_job_card": asdict(normalized),
        "quality_checks": _build_quality_checks(extracted),
        "raw_model_response": result.get("raw_response"),
        "provider_result": result,
    }


def _build_quality_checks(extracted: LLMExtractedJobCard) -> dict[str, object]:
    field_sources = extracted.field_sources
    missing_fields = [
        field_name
        for field_name in IMPORTANT_JOB_CARD_FIELDS
        if field_sources.get(field_name) == "missing"
        or getattr(extracted, field_name, None) in (None, "", [])
    ]
    inferred_fields = [
        field_name
        for field_name, source in field_sources.items()
        if source == "model_inference"
    ]
    original_fields = [
        field_name
        for field_name, source in field_sources.items()
        if source == "original_posting"
    ]
    evidence_fields = [
        field_name
        for field_name, evidence in extracted.evidence.items()
        if evidence
    ]

    return {
        "missing_fields": missing_fields,
        "inferred_fields": inferred_fields,
        "original_posting_fields": original_fields,
        "evidence_fields": evidence_fields,
        "field_source_coverage": len(
            [field_name for field_name in IMPORTANT_JOB_CARD_FIELDS if field_name in field_sources]
        ),
        "required_field_count": len(IMPORTANT_JOB_CARD_FIELDS),
        "confidence": extracted.confidence,
    }
