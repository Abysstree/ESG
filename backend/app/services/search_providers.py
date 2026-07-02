from dataclasses import asdict, dataclass
from typing import Any, Protocol

import httpx

from app.db.models import SearchProviderConfig
from app.services.api_keys import decrypt_api_key


@dataclass
class SearchProviderSettings:
    provider_type: str
    api_key: str | None
    base_url: str | None


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class SearchProvider(Protocol):
    name: str

    def search_company(self, company_name: str, max_results: int = 6) -> list[SearchResult]:
        """Return public search results that can support company enrichment."""


class ExaSearchProvider:
    name = "exa"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.exa.ai",
        timeout_seconds: float = 30,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_company(self, company_name: str, max_results: int = 6) -> list[SearchResult]:
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/search",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "query": _company_search_query(company_name),
                "type": "auto",
                "numResults": max_results,
                "contents": {"text": {"maxCharacters": 1200}},
            },
            timeout=self.timeout_seconds,
        )
        data = response.json()
        results = data.get("results")
        if not isinstance(results, list):
            return []

        return [
            SearchResult(
                title=str(item.get("title") or item.get("url") or "").strip(),
                url=str(item.get("url") or "").strip(),
                snippet=_compact_snippet(
                    item.get("text")
                    or item.get("summary")
                    or " ".join(
                        str(highlight)
                        for highlight in item.get("highlights", [])
                        if str(highlight).strip()
                    )
                ),
                source=self.name,
            )
            for item in results
            if isinstance(item, dict) and item.get("url")
        ]


class TavilySearchProvider:
    name = "tavily"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tavily.com",
        timeout_seconds: float = 30,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_company(self, company_name: str, max_results: int = 6) -> list[SearchResult]:
        response = _post_json(
            provider_name=self.name,
            url=f"{self.base_url}/search",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": _company_search_query(company_name),
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=self.timeout_seconds,
        )
        data = response.json()
        results = data.get("results")
        if not isinstance(results, list):
            return []

        return [
            SearchResult(
                title=str(item.get("title") or item.get("url") or "").strip(),
                url=str(item.get("url") or "").strip(),
                snippet=_compact_snippet(item.get("content") or item.get("raw_content")),
                source=self.name,
            )
            for item in results
            if isinstance(item, dict) and item.get("url")
        ]


def provider_settings_from_search_config(
    config: SearchProviderConfig,
) -> SearchProviderSettings:
    return SearchProviderSettings(
        provider_type=config.provider_type,
        api_key=decrypt_api_key(config.api_key),
        base_url=config.base_url,
    )


def build_search_provider(settings: SearchProviderSettings) -> SearchProvider:
    provider_type = settings.provider_type.lower()
    if not settings.api_key:
        raise RuntimeError("API key is required for this search provider.")

    if provider_type == "exa":
        return ExaSearchProvider(
            api_key=settings.api_key,
            base_url=settings.base_url or "https://api.exa.ai",
        )

    if provider_type == "tavily":
        return TavilySearchProvider(
            api_key=settings.api_key,
            base_url=settings.base_url or "https://api.tavily.com",
        )

    raise RuntimeError(f"Unsupported search provider type: {settings.provider_type}")


def _company_search_query(company_name: str) -> str:
    return f"{company_name} 官网 招聘 公司介绍 行业 融资 规模 总部"


def _post_json(
    provider_name: str,
    url: str,
    headers: dict[str, str],
    json: dict[str, Any],
    timeout: float,
) -> httpx.Response:
    try:
        response = httpx.post(url, headers=headers, json=json, timeout=timeout)
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as exc:
        body = _compact_snippet(exc.response.text, limit=800)
        raise RuntimeError(
            f"{provider_name} search request failed with HTTP "
            f"{exc.response.status_code}: {body or 'empty response body'}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"{provider_name} search request failed: {exc}") from exc


def _compact_snippet(value: object, limit: int = 1600) -> str:
    compacted = " ".join(str(value or "").split())
    if len(compacted) <= limit:
        return compacted
    return f"{compacted[:limit]}..."
