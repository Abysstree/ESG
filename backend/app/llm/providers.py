import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.db.models import LLMProviderConfig
from app.extraction.llm_schema import (
    build_company_profile_prompt,
    build_job_extraction_prompt,
    build_role_learning_map_prompt,
    parse_llm_company_profile,
    parse_llm_extracted_job_card,
    parse_llm_role_category_profile,
)
from app.extraction.mock_extractor import extract_job_card
from app.services.api_keys import decrypt_api_key


class LLMProvider(Protocol):
    name: str

    def extract_job_card(self, raw_text: str) -> dict[str, Any]:
        """Return a provider-specific extraction payload."""

    def generate_role_profile(self, role_payload: dict[str, Any]) -> dict[str, Any]:
        """Return a role-category profile and learning-map payload."""

    def generate_company_profile(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        """Return a company profile payload."""


@dataclass
class LLMProviderSettings:
    provider_type: str
    api_key: str | None
    base_url: str | None
    model: str | None


class MockLLMProvider:
    name = "mock"

    def extract_job_card(self, raw_text: str) -> dict[str, Any]:
        extracted = extract_job_card(raw_text)
        return {
            "provider": self.name,
            "mode": "mock",
            "job_card": extracted.__dict__,
        }

    def generate_role_profile(self, role_payload: dict[str, Any]) -> dict[str, Any]:
        skills = role_payload.get("high_frequency_skills") or []
        requirements = role_payload.get("common_requirements") or []
        responsibilities = role_payload.get("core_responsibilities") or []
        role_category = str(role_payload.get("role_category") or "待分类岗位")
        profile = {
            "role_category": role_category,
            "summary": f"基于本地岗位卡聚合的 {role_category} 初步画像。",
            "job_count": int(role_payload.get("job_count") or 0),
            "representative_titles": role_payload.get("representative_titles") or [],
            "core_responsibilities": responsibilities,
            "common_requirements": requirements,
            "high_frequency_skills": skills,
            "bonus_signals": role_payload.get("bonus_signals") or [],
            "learning_map": {
                "center_title": role_category,
                "center_subtitle": f"{int(role_payload.get('job_count') or 0)} 个岗位样本",
                "branches": [
                    {
                        "id": "core_skills",
                        "title": "核心技能",
                        "focus": "核心技能",
                        "source_fields": ["skills"],
                        "evidence": skills[:3],
                        "nodes": [
                            {
                                "id": f"skill.{index}",
                                "title": skill,
                                "node_type": "skill",
                                "level": "foundation",
                                "source_fields": ["skills"],
                                "evidence": [skill],
                                "children": [],
                            }
                            for index, skill in enumerate(skills[:6])
                        ],
                    },
                    {
                        "id": "project_practice",
                        "title": "项目实践",
                        "focus": "项目实践",
                        "source_fields": ["responsibilities"],
                        "evidence": responsibilities[:3],
                        "nodes": [
                            {
                                "id": f"project.{index}",
                                "title": item,
                                "node_type": "project",
                                "level": "portfolio",
                                "source_fields": ["responsibilities"],
                                "evidence": [item],
                                "children": [],
                            }
                            for index, item in enumerate(responsibilities[:5])
                        ],
                    },
                ],
            },
            "field_sources": {"learning_map": "model_inference"},
            "evidence": {"learning_map": skills[:3] + requirements[:3]},
            "inference_notes": ["当前为本地聚合兜底画像，未调用云端 LLM。"],
            "confidence": "medium",
        }
        return {"provider": self.name, "mode": "mock", "role_profile": profile}

    def generate_company_profile(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        company_name = str(company_payload.get("company_name") or "公司待补全")
        company_meta = company_payload.get("company_meta")
        meta = company_meta if isinstance(company_meta, dict) else {}
        profile = {
            "company_name": company_name,
            "summary": meta.get("summary"),
            "industry": meta.get("industry"),
            "financing_stage": meta.get("financing_stage"),
            "scale": meta.get("scale"),
            "headquarters": meta.get("headquarters"),
            "official_website": meta.get("official_website"),
            "official_careers_url": meta.get("official_careers_url"),
            "source_urls": [],
            "field_sources": {
                "company_name": "original_posting",
                "summary": "missing",
                "industry": "missing",
                "financing_stage": "missing",
                "scale": "missing",
                "headquarters": "missing",
                "official_website": "missing",
                "official_careers_url": "missing",
            },
            "evidence": {"company_name": company_name},
            "inference_notes": ["当前没有启用云端 LLM，仅保存公司名称。"],
            "confidence": "low",
        }
        return {"provider": self.name, "mode": "mock", "company_profile": profile}


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def extract_job_card(self, raw_text: str) -> dict[str, Any]:
        extraction_prompt = build_job_extraction_prompt(raw_text)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是 EmploymentSkillsGuide 的岗位信息抽取器。"
                            "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt,
                    },
                ],
                "temperature": 0,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_openai_message_content(response_data)
        extracted = parse_llm_extracted_job_card(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": extracted.model_dump(),
            "raw_response": response_data,
        }

    def generate_role_profile(self, role_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_role_learning_map_prompt(role_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是 EmploymentSkillsGuide 的岗位大类画像和学习地图生成器。"
                            "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_openai_message_content(response_data)
        profile = parse_llm_role_category_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "role_profile": profile.model_dump(),
            "raw_response": response_data,
        }

    def generate_company_profile(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_company_profile_prompt(company_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是 EmploymentSkillsGuide 的公司事实补全助手。"
                            "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象；"
                            "无法确认的信息不要编造。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_openai_message_content(response_data)
        profile = parse_llm_company_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "company_profile": profile.model_dump(),
            "raw_response": response_data,
        }


class DeepSeekProvider(OpenAICompatibleProvider):
    name = "deepseek"


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def extract_job_card(self, raw_text: str) -> dict[str, Any]:
        extraction_prompt = build_job_extraction_prompt(raw_text)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": (
                    "你是 EmploymentSkillsGuide 的岗位信息抽取器。"
                    "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                ),
                "messages": [{"role": "user", "content": extraction_prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_anthropic_message_content(response_data)
        extracted = parse_llm_extracted_job_card(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": extracted.model_dump(),
            "raw_response": response_data,
        }

    def generate_role_profile(self, role_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_role_learning_map_prompt(role_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": (
                    "你是 EmploymentSkillsGuide 的岗位大类画像和学习地图生成器。"
                    "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_anthropic_message_content(response_data)
        profile = parse_llm_role_category_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "role_profile": profile.model_dump(),
            "raw_response": response_data,
        }

    def generate_company_profile(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_company_profile_prompt(company_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "system": (
                    "你是 EmploymentSkillsGuide 的公司事实补全助手。"
                    "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象；"
                    "无法确认的信息不要编造。"
                ),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_anthropic_message_content(response_data)
        profile = parse_llm_company_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "company_profile": profile.model_dump(),
            "raw_response": response_data,
        }


class GoogleGeminiProvider:
    name = "google"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 60,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def extract_job_card(self, raw_text: str) -> dict[str, Any]:
        extraction_prompt = build_job_extraction_prompt(raw_text)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1beta/models/{self.model}:generateContent",
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {
                    "parts": [
                        {
                            "text": (
                                "你是 EmploymentSkillsGuide 的岗位信息抽取器。"
                                "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                            )
                        }
                    ]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": extraction_prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_gemini_message_content(response_data)
        extracted = parse_llm_extracted_job_card(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": extracted.model_dump(),
            "raw_response": response_data,
        }

    def generate_role_profile(self, role_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_role_learning_map_prompt(role_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1beta/models/{self.model}:generateContent",
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {
                    "parts": [
                        {
                            "text": (
                                "你是 EmploymentSkillsGuide 的岗位大类画像和学习地图生成器。"
                                "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象。"
                            )
                        }
                    ]
                },
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_gemini_message_content(response_data)
        profile = parse_llm_role_category_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "role_profile": profile.model_dump(),
            "raw_response": response_data,
        }

    def generate_company_profile(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = build_company_profile_prompt(company_payload)
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/v1beta/models/{self.model}:generateContent",
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {
                    "parts": [
                        {
                            "text": (
                                "你是 EmploymentSkillsGuide 的公司事实补全助手。"
                                "请严格遵守用户提供的 JSON Schema，只返回 JSON 对象；"
                                "无法确认的信息不要编造。"
                            )
                        }
                    ]
                },
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.timeout_seconds,
        )
        response_data = response.json()
        content = _extract_gemini_message_content(response_data)
        profile = parse_llm_company_profile(content)
        return {
            "provider": self.name,
            "mode": "cloud",
            "company_profile": profile.model_dump(),
            "raw_response": response_data,
        }


def provider_settings_from_config(config: LLMProviderConfig) -> LLMProviderSettings:
    return LLMProviderSettings(
        provider_type=config.provider_type,
        api_key=decrypt_api_key(config.api_key),
        base_url=config.base_url,
        model=config.model,
    )


def build_llm_provider(settings: LLMProviderSettings) -> LLMProvider:
    provider_type = settings.provider_type.lower()
    api_key = settings.api_key
    if provider_type == "mock":
        return MockLLMProvider()

    if not api_key:
        raise RuntimeError("API key is required for this LLM provider.")

    if provider_type == "deepseek":
        return DeepSeekProvider(
            api_key=api_key,
            base_url=settings.base_url or "https://api.deepseek.com",
            model=settings.model or "deepseek-v4-flash",
        )

    if provider_type in {"openai", "openai_compatible"}:
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=settings.base_url or "https://api.openai.com/v1",
            model=settings.model or "gpt-4.1-mini",
        )

    if provider_type == "anthropic":
        return AnthropicProvider(
            api_key=api_key,
            base_url=settings.base_url or "https://api.anthropic.com",
            model=settings.model or "claude-sonnet-4-5",
        )

    if provider_type in {"google", "gemini"}:
        return GoogleGeminiProvider(
            api_key=api_key,
            base_url=settings.base_url or "https://generativelanguage.googleapis.com",
            model=settings.model or "gemini-2.5-flash",
        )

    raise RuntimeError(f"Unsupported LLM provider type: {settings.provider_type}")


def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("ESG_LLM_PROVIDER", "mock").lower()

    if provider_name == "deepseek":
        return build_llm_provider(
            LLMProviderSettings(
                provider_type="deepseek",
                api_key=os.getenv("ESG_LLM_API_KEY"),
                base_url=os.getenv("ESG_LLM_BASE_URL", "https://api.deepseek.com"),
                model=os.getenv("ESG_LLM_MODEL", "deepseek-v4-flash"),
            )
        )

    if provider_name in {"openai", "openai_compatible"}:
        api_key = os.getenv("ESG_LLM_API_KEY")
        if not api_key:
            raise RuntimeError("ESG_LLM_API_KEY is required for cloud LLM provider.")
        return build_llm_provider(
            LLMProviderSettings(
                provider_type="openai_compatible",
                api_key=api_key,
                base_url=os.getenv("ESG_LLM_BASE_URL", "https://api.openai.com/v1"),
                model=os.getenv("ESG_LLM_MODEL", "gpt-4.1-mini"),
            )
        )

    if provider_name == "anthropic":
        return build_llm_provider(
            LLMProviderSettings(
                provider_type="anthropic",
                api_key=os.getenv("ESG_LLM_API_KEY"),
                base_url=os.getenv("ESG_LLM_BASE_URL", "https://api.anthropic.com"),
                model=os.getenv("ESG_LLM_MODEL", "claude-sonnet-4-6"),
            )
        )

    if provider_name in {"google", "gemini"}:
        return build_llm_provider(
            LLMProviderSettings(
                provider_type="google",
                api_key=os.getenv("ESG_LLM_API_KEY"),
                base_url=os.getenv(
                    "ESG_LLM_BASE_URL",
                    "https://generativelanguage.googleapis.com",
                ),
                model=os.getenv("ESG_LLM_MODEL", "gemini-3.5-flash"),
            )
        )

    return MockLLMProvider()


def get_llm_status() -> dict[str, Any]:
    provider_name = os.getenv("ESG_LLM_PROVIDER", "mock").lower()
    return {
        "provider": provider_name,
        "configured": provider_name == "mock" or bool(os.getenv("ESG_LLM_API_KEY")),
        "model": os.getenv("ESG_LLM_MODEL"),
        "base_url": os.getenv("ESG_LLM_BASE_URL"),
    }


def _post_json(
    provider_name: str,
    url: str,
    headers: dict[str, str],
    json: dict[str, Any],
    timeout: float,
) -> httpx.Response:
    try:
        response = httpx.post(
            url,
            headers=headers,
            json=json,
            timeout=timeout,
        )
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as exc:
        body = _compact_error_body(exc.response.text)
        raise RuntimeError(
            f"{provider_name} API request failed with HTTP "
            f"{exc.response.status_code}: {body}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"{provider_name} API request failed: {exc}") from exc


def _compact_error_body(value: str, limit: int = 800) -> str:
    compacted = " ".join(str(value or "").split())
    if len(compacted) <= limit:
        return compacted or "empty response body"
    return f"{compacted[:limit]}..."


def _extract_openai_message_content(response_data: dict[str, Any]) -> str:
    try:
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenAI-compatible response did not contain message content.") from exc

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict)
        )
    raise RuntimeError("OpenAI-compatible message content must be text.")


def _extract_anthropic_message_content(response_data: dict[str, Any]) -> str:
    blocks = response_data.get("content")
    if not isinstance(blocks, list):
        raise RuntimeError("Anthropic response did not contain content blocks.")

    texts = [
        str(block.get("text", ""))
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    content = "\n".join(text for text in texts if text.strip())
    if not content:
        raise RuntimeError("Anthropic response did not contain text content.")
    return content


def _extract_gemini_message_content(response_data: dict[str, Any]) -> str:
    try:
        parts = response_data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini response did not contain candidate content.") from exc

    if not isinstance(parts, list):
        raise RuntimeError("Gemini content parts must be a list.")

    content = "\n".join(
        str(part.get("text", "")) for part in parts if isinstance(part, dict)
    )
    if not content.strip():
        raise RuntimeError("Gemini response did not contain text content.")
    return content
