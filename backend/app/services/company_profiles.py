import json
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CompanyProfile, JobCard
from app.llm.providers import (
    build_llm_provider,
    get_llm_provider,
    provider_settings_from_config,
)
from app.services.llm_configs import get_active_llm_provider_config
from app.services.search_configs import get_active_search_provider_config
from app.services.search_providers import (
    build_search_provider,
    provider_settings_from_search_config,
)


def list_company_profiles(session: Session) -> list[CompanyProfile]:
    statement = select(CompanyProfile).order_by(CompanyProfile.updated_at.desc())
    return list(session.scalars(statement))


def enrich_company_profile(company_name: str, session: Session) -> CompanyProfile:
    normalized_name = company_name.strip()
    if not normalized_name:
        raise RuntimeError("Company name is required.")

    active_config = get_active_llm_provider_config(session)
    provider = (
        build_llm_provider(provider_settings_from_config(active_config))
        if active_config
        else get_llm_provider()
    )
    payload = build_company_profile_payload(normalized_name, session)
    search_results = _search_company_context(normalized_name, session)
    if search_results:
        payload["search_results"] = search_results
        payload["instruction"] = (
            str(payload.get("instruction") or "")
            + " 已提供联网检索结果时，只能基于 search_results 和岗位原文上下文输出公司事实；"
            + "这些字段来源必须标为 external_search，并把来源 URL 放入 source_urls。"
        )
    result = provider.generate_company_profile(payload)
    profile_payload = result.get("company_profile")
    if not isinstance(profile_payload, dict):
        raise RuntimeError("LLM company profile response did not contain company_profile.")

    existing_profile = session.scalar(
        select(CompanyProfile).where(CompanyProfile.company_name == normalized_name)
    )
    profile = existing_profile or CompanyProfile(company_name=normalized_name)
    company_meta = payload.get("company_meta")
    if isinstance(company_meta, dict):
        profile_payload = _merge_original_company_meta(profile_payload, company_meta)
    if search_results:
        profile_payload = _mark_external_search_fields(profile_payload, search_results)

    apply_company_profile_payload(
        profile,
        {
            **profile_payload,
            "company_name": profile_payload.get("company_name") or normalized_name,
        },
        status=(
            "external_search_enriched"
            if search_results
            else "llm_enriched"
            if result.get("mode") != "mock"
            else "mock_enriched"
        ),
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def _search_company_context(company_name: str, session: Session) -> list[dict[str, str]]:
    active_search_config = get_active_search_provider_config(session)
    if not active_search_config or not active_search_config.api_key:
        return []

    try:
        provider = build_search_provider(
            provider_settings_from_search_config(active_search_config)
        )
        results = provider.search_company(company_name)
    except RuntimeError:
        return []

    return [result.to_dict() for result in results if result.url][:6]


def build_company_profile_payload(company_name: str, session: Session) -> dict[str, Any]:
    statement = (
        select(JobCard)
        .where(JobCard.company_name == company_name)
        .order_by(JobCard.created_at.desc())
        .limit(6)
    )
    jobs = list(session.scalars(statement))
    context_snippets = _company_context_snippets(company_name, jobs)
    company_meta = _extract_company_meta(company_name, context_snippets)
    return {
        "company_name": company_name,
        "company_meta": company_meta,
        "company_context_snippets": context_snippets,
        "job_samples": [
            {
                "title": job.title,
                "role_category": job.role_category,
                "base_location": job.base_location,
                "company_evidence": job.evidence.get("company_name"),
            }
            for job in jobs
        ],
        "instruction": (
            "请补全公司本身的信息，不要输出岗位职责、岗位大类或岗位地址。"
            "没有可靠事实时保持 null，并明确标记 missing 或 model_inference。"
            "如果输入里有 search_results，请优先使用搜索结果，并把对应字段标记为 external_search。"
        ),
    }


def _company_context_snippets(company_name: str, jobs: list[JobCard]) -> list[str]:
    snippets: list[str] = []
    for job in jobs:
        raw_text = job.raw_import.raw_text if job.raw_import else None
        if not raw_text:
            continue
        lines = [
            line.strip()
            for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            if line.strip()
        ]
        for index, line in enumerate(lines):
            if line == "所在公司":
                snippet = "\n".join(lines[index : index + 6]).strip()
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
                break
            if company_name in line:
                start_index = max(0, index - 1)
                snippet = "\n".join(lines[start_index : index + 6]).strip()
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
                break
    return snippets[:4]


def _extract_company_meta(company_name: str, snippets: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    financing_pattern = re.compile(
        r"(未融资|不需要融资|已上市|天使轮|种子轮|战略融资|[A-D][轮輪])",
    )
    scale_pattern = re.compile(r"(\d+\s*-\s*\d+人|\d+人以上|\d+人以下)")
    for snippet in snippets:
        financing_match = financing_pattern.search(snippet)
        if financing_match and "financing_stage" not in meta:
            meta["financing_stage"] = financing_match.group(1).replace("輪", "轮")

        scale_match = scale_pattern.search(snippet)
        if scale_match and "scale" not in meta:
            meta["scale"] = re.sub(r"\s+", "", scale_match.group(1))

        if "industry" not in meta:
            for part in re.split(r"[·\n|｜,，]", snippet):
                candidate = part.strip()
                if not candidate or candidate == "所在公司" or candidate == meta.get("financing_stage"):
                    continue
                if scale_pattern.fullmatch(candidate) or financing_pattern.fullmatch(candidate):
                    continue
                if company_name_like(candidate):
                    continue
                if 2 <= len(candidate) <= 16 and not re.search(r"\d", candidate):
                    meta["industry"] = candidate
                    break
    return meta


def company_name_like(value: str) -> bool:
    return any(keyword in value for keyword in ("公司", "集团", "科技", "技术", "有限公司"))


def _merge_original_company_meta(
    profile_payload: dict[str, Any],
    company_meta: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(profile_payload)
    field_sources = dict(merged.get("field_sources") or {})
    evidence = dict(merged.get("evidence") or {})
    for field_name in ("industry", "financing_stage", "scale"):
        value = company_meta.get(field_name)
        if not value or merged.get(field_name):
            continue
        merged[field_name] = value
        field_sources[field_name] = "original_posting"
        evidence[field_name] = str(value)
    merged["field_sources"] = field_sources
    merged["evidence"] = evidence
    return merged


def _mark_external_search_fields(
    profile_payload: dict[str, Any],
    search_results: list[dict[str, str]],
) -> dict[str, Any]:
    merged = dict(profile_payload)
    field_sources = dict(merged.get("field_sources") or {})
    evidence = dict(merged.get("evidence") or {})
    source_urls = _string_list(merged.get("source_urls"))
    search_urls = [result["url"] for result in search_results if result.get("url")]
    source_urls = _unique(source_urls + search_urls)
    fallback_evidence = _best_search_evidence(search_results)

    for field_name in (
        "summary",
        "industry",
        "financing_stage",
        "scale",
        "headquarters",
        "official_website",
        "official_careers_url",
    ):
        if not _optional_text(merged.get(field_name)):
            field_sources[field_name] = field_sources.get(field_name) or "missing"
            continue
        field_sources[field_name] = "external_search"
        if not evidence.get(field_name):
            evidence[field_name] = fallback_evidence

    if _optional_text(merged.get("company_name")):
        field_sources["company_name"] = field_sources.get("company_name") or "original_posting"

    merged["source_urls"] = source_urls
    merged["field_sources"] = field_sources
    merged["evidence"] = evidence
    return merged


def apply_company_profile_payload(
    profile: CompanyProfile,
    payload: dict[str, Any],
    status: str,
) -> None:
    profile.company_name = str(payload.get("company_name") or profile.company_name).strip()
    profile.summary = _optional_text(payload.get("summary"))
    profile.industry = _optional_text(payload.get("industry"))
    profile.financing_stage = _optional_text(payload.get("financing_stage"))
    profile.scale = _optional_text(payload.get("scale"))
    profile.headquarters = _optional_text(payload.get("headquarters"))
    profile.official_website = _optional_text(payload.get("official_website"))
    profile.official_careers_url = _optional_text(payload.get("official_careers_url"))
    profile.source_urls_json = json.dumps(
        _string_list(payload.get("source_urls")),
        ensure_ascii=False,
    )
    profile.field_sources_json = json.dumps(
        _string_dict(payload.get("field_sources")),
        ensure_ascii=False,
    )
    profile.evidence_json = json.dumps(
        _nullable_string_dict(payload.get("evidence")),
        ensure_ascii=False,
    )
    profile.inference_notes_json = json.dumps(
        _string_list(payload.get("inference_notes")),
        ensure_ascii=False,
    )
    profile.confidence = str(payload.get("confidence") or "medium")
    profile.status = status


def _best_search_evidence(search_results: list[dict[str, str]]) -> str | None:
    for result in search_results:
        title = _optional_text(result.get("title"))
        snippet = _optional_text(result.get("snippet"))
        url = _optional_text(result.get("url"))
        evidence_parts = [part for part in (title, snippet, url) if part]
        if evidence_parts:
            return "；".join(evidence_parts)[:500]
    return None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _string_dict(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if item is not None}


def _nullable_string_dict(value: object) -> dict[str, str | None]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): None if item is None else str(item)
        for key, item in value.items()
    }
