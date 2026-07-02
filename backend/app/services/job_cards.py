import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.models import JobCard, RawImport
from app.extraction.llm_schema import LLMExtractedJobCard
from app.extraction.mock_extractor import ExtractedJobCard, extract_job_card
from app.llm.providers import build_llm_provider, provider_settings_from_config
from app.services.llm_configs import get_active_llm_provider_config


def create_job_card_for_import(raw_import: RawImport, session: Session) -> JobCard | None:
    if not raw_import.raw_text:
        return None

    active_config = get_active_llm_provider_config(session)
    if not active_config or not active_config.api_key:
        return create_mock_job_card(raw_import, session)

    try:
        return create_llm_job_card(raw_import, session)
    except (RuntimeError, ValidationError) as exc:
        return create_mock_job_card(
            raw_import,
            session,
            status="llm_failed_mock_extracted",
            inference_note=f"LLM extraction failed, rule fallback used: {exc}",
        )


def create_mock_job_card(
    raw_import: RawImport,
    session: Session,
    status: str = "mock_extracted",
    inference_note: str | None = None,
) -> JobCard | None:
    if not raw_import.raw_text:
        return None

    extracted = extract_job_card(raw_import.raw_text)
    if inference_note:
        extracted.inference_notes.append(inference_note)
    job_card = raw_import.job_cards[0] if raw_import.job_cards else JobCard(raw_import_id=raw_import.id)
    apply_extracted_job_card(
        job_card,
        extracted,
        status=status,
        raw_text=raw_import.raw_text or "",
    )
    raw_import.status = status
    session.add(job_card)
    session.commit()
    session.refresh(job_card)
    session.refresh(raw_import)
    return job_card


def create_llm_job_card(raw_import: RawImport, session: Session) -> JobCard | None:
    if not raw_import.raw_text:
        return None

    active_config = get_active_llm_provider_config(session)
    if not active_config:
        return create_mock_job_card(raw_import, session)

    provider = build_llm_provider(provider_settings_from_config(active_config))
    result = provider.extract_job_card(raw_import.raw_text)
    extracted_payload = result.get("job_card")
    extracted = LLMExtractedJobCard.model_validate(extracted_payload).to_extracted_job_card()
    job_card = raw_import.job_cards[0] if raw_import.job_cards else JobCard(raw_import_id=raw_import.id)
    apply_extracted_job_card(
        job_card,
        extracted,
        status="llm_extracted",
        raw_text=raw_import.raw_text or "",
    )
    raw_import.status = "llm_extracted"
    session.add(job_card)
    session.commit()
    session.refresh(job_card)
    session.refresh(raw_import)
    return job_card


def rebuild_llm_job_cards(session: Session) -> list[JobCard]:
    active_config = get_active_llm_provider_config(session)
    if not active_config or not active_config.api_key:
        raise RuntimeError("Active LLM provider with API key is required.")

    raw_imports = list(
        session.scalars(
            select(RawImport)
            .where(RawImport.raw_text.is_not(None))
            .order_by(RawImport.created_at.desc())
        )
    )
    rebuilt_cards = []

    for raw_import in raw_imports:
        job_card = create_llm_job_card(raw_import, session)
        if job_card:
            rebuilt_cards.append(job_card)

    return rebuilt_cards


def reextract_job_card_with_llm(job_id: int, session: Session) -> JobCard:
    job_card = session.get(JobCard, job_id)
    if not job_card:
        raise ValueError("Job card not found.")
    if not job_card.raw_import or not job_card.raw_import.raw_text:
        raise ValueError("Job card has no raw import text.")

    rebuilt = create_llm_job_card(job_card.raw_import, session)
    if not rebuilt:
        raise RuntimeError("LLM did not return a job card.")
    return rebuilt


def rebuild_mock_job_cards(session: Session) -> list[JobCard]:
    raw_imports = list(
        session.scalars(
            select(RawImport)
            .where(RawImport.raw_text.is_not(None))
            .order_by(RawImport.created_at.desc())
        )
    )
    rebuilt_cards = []

    for raw_import in raw_imports:
        job_card = create_mock_job_card(raw_import, session)
        if job_card:
            rebuilt_cards.append(job_card)

    return rebuilt_cards


def apply_extracted_job_card(
    job_card: JobCard,
    extracted: ExtractedJobCard,
    status: str = "mock_extracted",
    raw_text: str = "",
) -> None:
    if not raw_text and job_card.raw_import:
        raw_text = job_card.raw_import.raw_text or ""
    normalize_extracted_job_card(extracted, raw_text)
    job_card.title = extracted.title
    job_card.company_name = extracted.company_name
    job_card.role_category = extracted.role_category
    job_card.salary_range = extracted.salary_range
    job_card.salary_period = extracted.salary_period
    job_card.base_location = extracted.base_location
    job_card.education_requirement = extracted.education_requirement
    job_card.experience_requirement = extracted.experience_requirement
    job_card.responsibilities_json = json.dumps(
        extracted.responsibilities,
        ensure_ascii=False,
    )
    job_card.requirements_json = json.dumps(extracted.requirements, ensure_ascii=False)
    job_card.bonus_points_json = json.dumps(extracted.bonus_points, ensure_ascii=False)
    job_card.skills_json = json.dumps(extracted.skills, ensure_ascii=False)
    job_card.field_sources_json = json.dumps(extracted.field_sources, ensure_ascii=False)
    job_card.evidence_json = json.dumps(extracted.evidence, ensure_ascii=False)
    job_card.confidence = extracted.confidence
    job_card.status = status


def normalize_extracted_job_card(extracted: ExtractedJobCard, raw_text: str) -> None:
    lines = _normalize_lines(raw_text)
    first_line = lines[0] if lines else ""
    original_title = extracted.title
    stage = _detect_stage(original_title, extracted.experience_requirement, raw_text)

    company_candidate = extracted.company_name or _infer_company_name(lines, original_title)
    cleaned_title = _clean_title(original_title, company_candidate, stage, first_line)
    if stage and f"（{stage}）" not in cleaned_title:
        cleaned_title = f"{cleaned_title}（{stage}）"

    if cleaned_title and cleaned_title != extracted.title:
        extracted.title = cleaned_title
        extracted.evidence.setdefault("title", first_line or original_title)
        if first_line:
            extracted.field_sources["title"] = "original_posting"

    if company_candidate and not extracted.company_name:
        extracted.company_name = company_candidate
        extracted.field_sources["company_name"] = "original_posting"
        extracted.evidence["company_name"] = _find_line_containing(lines, company_candidate) or first_line

    raw_base_location = _extract_full_base_location(lines)
    base_candidate = raw_base_location or extracted.base_location
    base_summary = _summarize_base_location(base_candidate)
    if base_summary:
        if base_summary != extracted.base_location:
            extracted.base_location = base_summary
        if raw_base_location:
            extracted.field_sources["base_location"] = "original_posting"
            extracted.evidence["base_location"] = raw_base_location
        elif base_candidate and base_candidate != base_summary:
            extracted.evidence.setdefault("base_location", base_candidate)

    if extracted.education_requirement and not _has_explicit_education(raw_text):
        extracted.education_requirement = None
        extracted.field_sources["education_requirement"] = "missing"
        extracted.evidence["education_requirement"] = None
        extracted.inference_notes.append(
            "学历要求未在原文中明确出现，已从岗位卡中移除。",
        )

    _clear_inferred_hard_facts(extracted)

    for field_name in (
        "title",
        "company_name",
        "role_category",
        "salary_range",
        "base_location",
        "education_requirement",
        "experience_requirement",
    ):
        value = getattr(extracted, field_name, None)
        if (
            value
            and extracted.field_sources.get(field_name) == "original_posting"
            and not extracted.evidence.get(field_name)
        ):
            extracted.evidence[field_name] = _find_line_containing(lines, str(value)) or str(value)


HARD_FACT_SCALAR_FIELDS = (
    "salary_range",
    "base_location",
    "education_requirement",
    "experience_requirement",
)
HARD_FACT_LIST_FIELDS = ("responsibilities", "requirements")


def _clear_inferred_hard_facts(extracted: ExtractedJobCard) -> None:
    for field_name in HARD_FACT_SCALAR_FIELDS:
        if extracted.field_sources.get(field_name) != "model_inference":
            continue
        if getattr(extracted, field_name, None):
            extracted.inference_notes.append(
                f"{field_name} 是硬事实字段，不能使用模型推测值，已标记为缺失。",
            )
        setattr(extracted, field_name, None)
        extracted.field_sources[field_name] = "missing"
        extracted.evidence[field_name] = None

    for field_name in HARD_FACT_LIST_FIELDS:
        if extracted.field_sources.get(field_name) != "model_inference":
            continue
        if getattr(extracted, field_name, None):
            extracted.inference_notes.append(
                f"{field_name} 是硬事实字段，不能使用模型推测值，已标记为缺失。",
            )
        setattr(extracted, field_name, [])
        extracted.field_sources[field_name] = "missing"
        extracted.evidence[field_name] = None


def _normalize_lines(raw_text: str) -> list[str]:
    return [
        line.strip()
        for line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.strip()
    ]


def _detect_stage(title: str | None, experience: str | None, raw_text: str) -> str | None:
    haystack = " ".join(value for value in (title, experience, raw_text[:160]) if value)
    if "实习" in haystack:
        return "实习生"
    if "应届" in haystack or "校招" in haystack:
        return "应届生"
    return None


def _clean_title(
    title: str | None,
    company_name: str | None,
    stage: str | None,
    first_line: str,
) -> str:
    cleaned = str(title or "").strip() or first_line.strip() or "未命名岗位"
    cleaned = re.sub(r"[（(]\s*(应届生|实习生|校招)\s*[)）]", "", cleaned)
    for token in ("应届生", "实习生", "校招"):
        cleaned = re.sub(rf"(^|\s+){token}(\s+|$)", " ", cleaned).strip()
    if company_name:
        cleaned = re.sub(rf"(^|\s+){re.escape(company_name)}(\s+|$)", " ", cleaned).strip()
    if first_line and cleaned == first_line:
        parts = [part for part in re.split(r"\s+", first_line) if part]
        parts = [
            part
            for part in parts
            if part not in {stage, company_name, "应届生", "实习生", "校招"}
        ]
        if parts:
            cleaned = parts[0]
    return re.sub(r"\s+", " ", cleaned).strip(" -·|") or "未命名岗位"


def _infer_company_name(lines: list[str], title: str | None) -> str | None:
    for index, line in enumerate(lines):
        match = re.search(r"(?:公司名称|所在公司|公司|企业)\s*[:：]\s*(.+)", line)
        if match:
            return _clean_company_candidate(match.group(1))
        if line == "所在公司" and index + 1 < len(lines):
            return _clean_company_candidate(lines[index + 1])

    for line in lines[:6]:
        parts = [part for part in re.split(r"\s+", line) if part]
        if len(parts) >= 3 and any(part in {"应届生", "实习生", "校招"} for part in parts):
            candidate = parts[-1]
            if candidate != title and _looks_like_company_candidate(candidate):
                return _clean_company_candidate(candidate)

    for line in lines[:12]:
        candidate = _clean_company_candidate(line)
        if _looks_like_company_candidate(candidate) and candidate != title:
            return candidate
    return None


def _clean_company_candidate(value: str) -> str:
    cleaned = re.split(r"\s+|·|，|,|\|", value.strip())[0]
    cleaned = re.sub(r"(未融资|已上市|融资|[0-9]+-[0-9]+人).*", "", cleaned)
    return cleaned.strip()


def _looks_like_company_candidate(value: str) -> bool:
    if not value or len(value) > 40:
        return False
    company_keywords = ("公司", "集团", "科技", "技术", "华为", "腾讯", "阿里", "字节", "百度", "美团")
    blocked_keywords = ("岗位", "职位", "职责", "要求", "工作地点", "薪资", "研发类")
    return any(keyword in value for keyword in company_keywords) and not any(
        keyword in value for keyword in blocked_keywords
    )


def _extract_full_base_location(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if line.startswith(("工作地点", "工作城市", "Base", "base")):
            remainder = re.sub(r"^(工作地点|工作城市|Base|base)\s*[:：]?\s*", "", line).strip()
            if remainder and _contains_known_location(remainder):
                return remainder
            if index + 1 < len(lines) and _contains_known_location(lines[index + 1]):
                return lines[index + 1].strip()

    for line in lines[:8]:
        if _looks_like_location_list(line):
            return line.strip()
    return None


def _looks_like_location_list(value: str) -> bool:
    city_count = len([city for city in CITY_NAMES if city in value])
    return city_count >= 2 and bool(re.search(r"[/、,，\s]", value))


CITY_NAMES = (
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "南京",
    "苏州",
    "西安",
    "成都",
    "武汉",
    "合肥",
    "长沙",
    "济南",
    "东莞",
)
SPECIAL_BASE_NAMES = ("全国", "远程", "居家", "不限")


def _contains_known_location(value: str) -> bool:
    return any(city in value for city in CITY_NAMES) or any(
        keyword in value for keyword in SPECIAL_BASE_NAMES
    )


def _summarize_base_location(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"^(工作地点|工作城市|Base|base)\s*[:：]?\s*", "", value.strip())
    if not cleaned:
        return None
    if _looks_like_location_list(cleaned):
        return _summarize_location_list(cleaned)
    city_district = _extract_city_district(cleaned)
    if city_district:
        return city_district
    for keyword in SPECIAL_BASE_NAMES:
        if keyword in cleaned:
            return keyword
    return cleaned if len(cleaned) <= 12 else None


def _summarize_location_list(value: str) -> str:
    parts = [part.strip() for part in re.split(r"[/、,，\s]+", value) if part.strip()]
    summarized_parts: list[str] = []
    seen: set[str] = set()
    for part in parts:
        summary = _extract_city_district(part)
        if not summary:
            continue
        if summary in seen:
            continue
        summarized_parts.append(summary)
        seen.add(summary)
    return "/".join(summarized_parts) or value.strip()


def _extract_city_district(value: str) -> str | None:
    for city in CITY_NAMES:
        if city not in value:
            continue
        suffix = value.split(city, 1)[1]
        suffix = suffix.removeprefix("市")
        district_match = re.match(
            r"(?P<district>[\u4e00-\u9fa5]{1,8}(?:区|县|市|新区|开发区|高新区))",
            suffix,
        )
        if district_match:
            return f"{city}{district_match.group('district')}"
        return city
    return None


def _has_explicit_education(raw_text: str) -> bool:
    return bool(re.search(r"(本科|硕士|博士|大专|学历不限|不限学历)", raw_text))


def _find_line_containing(lines: list[str], value: str) -> str | None:
    if not value:
        return None
    for line in lines:
        if value in line or line in value:
            return line
    return None
