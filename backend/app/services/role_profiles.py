from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import JobCard
from app.llm.providers import build_llm_provider, provider_settings_from_config
from app.services.llm_configs import get_active_llm_provider_config


def build_role_payload(role_category: str, session: Session) -> dict[str, Any]:
    jobs = list(
        session.scalars(
            select(JobCard)
            .where(JobCard.role_category == role_category)
            .order_by(JobCard.created_at.desc())
        )
    )
    return {
        "role_category": role_category,
        "job_count": len(jobs),
        "representative_titles": _unique([job.title for job in jobs], 8),
        "companies": _unique([job.company_name for job in jobs if job.company_name], 8),
        "base_locations": _unique([job.base_location for job in jobs if job.base_location], 8),
        "salary_samples": _unique([job.salary_range for job in jobs if job.salary_range], 6),
        "education_requirements": _unique(
            [job.education_requirement for job in jobs if job.education_requirement],
            6,
        ),
        "experience_requirements": _unique(
            [job.experience_requirement for job in jobs if job.experience_requirement],
            6,
        ),
        "core_responsibilities": _top_values(
            [item for job in jobs for item in job.responsibilities],
            10,
        ),
        "common_requirements": _top_values(
            [item for job in jobs for item in job.requirements],
            12,
        ),
        "high_frequency_skills": _top_values(
            [item for job in jobs for item in job.skills],
            16,
        ),
        "bonus_signals": _top_values(
            [item for job in jobs for item in job.bonus_points],
            8,
        ),
    }


def generate_role_profile(role_category: str, session: Session) -> dict[str, Any]:
    payload = build_role_payload(role_category, session)
    if payload["job_count"] == 0:
        raise ValueError("No job cards found for this role category.")

    active_config = get_active_llm_provider_config(session)
    if not active_config or not active_config.api_key:
        raise RuntimeError("Active LLM provider with API key is required.")

    provider = build_llm_provider(provider_settings_from_config(active_config))
    result = provider.generate_role_profile(payload)
    return {
        "provider": result.get("provider", provider.name),
        "mode": result.get("mode", "cloud"),
        "input": payload,
        "role_profile": result.get("role_profile"),
        "raw_model_response": result.get("raw_response"),
    }


def _unique(values: list[str], limit: int) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _top_values(values: list[str], limit: int) -> list[str]:
    counts: dict[str, int] = {}
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        counts[cleaned] = counts.get(cleaned, 0) + 1
    return [
        value
        for value, _count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]
    ]
