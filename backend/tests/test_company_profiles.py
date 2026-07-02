from fastapi.testclient import TestClient

from app.main import create_app


class FakeCompanyLLMProvider:
    name = "fake"

    def generate_company_profile(self, company_payload: dict[str, object]) -> dict[str, object]:
        company_name = str(company_payload["company_name"])
        return {
            "provider": self.name,
            "mode": "cloud",
            "company_profile": {
                "company_name": company_name,
                "summary": "一家专注三维医学影像处理算法的医疗健康技术公司。",
                "industry": "医疗健康",
                "financing_stage": "未融资",
                "scale": "0-20人",
                "headquarters": "南京",
                "official_website": None,
                "official_careers_url": None,
                "source_urls": [],
                "field_sources": {
                    "company_name": "original_posting",
                    "summary": "model_inference",
                    "industry": "model_inference",
                    "financing_stage": "original_posting",
                    "scale": "original_posting",
                    "headquarters": "model_inference",
                    "official_website": "missing",
                    "official_careers_url": "missing",
                },
                "evidence": {
                    "company_name": company_name,
                    "financing_stage": "未融资",
                    "scale": "0-20人",
                },
                "inference_notes": ["简介和行业由岗位上下文推断。"],
                "confidence": "medium",
            },
        }


def test_company_profile_enriches_and_persists(monkeypatch) -> None:
    client = TestClient(create_app())
    provider_response = client.post(
        "/api/llm/providers",
        json={
            "name": "Test LLM",
            "provider_type": "openai_compatible",
            "api_key": "test-key",
            "base_url": "https://example.test/v1",
            "model": "test-model",
            "enabled": True,
            "is_active": True,
        },
    )
    assert provider_response.status_code == 200
    monkeypatch.setattr(
        "app.services.company_profiles.build_llm_provider",
        lambda _: FakeCompanyLLMProvider(),
    )

    enrich_response = client.post(
        "/api/companies/enrich",
        json={"company_name": "南京芯动云图技术有限公司"},
    )

    assert enrich_response.status_code == 200
    profile = enrich_response.json()
    assert profile["company_name"] == "南京芯动云图技术有限公司"
    assert profile["industry"] == "医疗健康"
    assert profile["scale"] == "0-20人"
    assert profile["status"] == "llm_enriched"

    profiles = client.get("/api/companies").json()
    assert len(profiles) == 1
    assert profiles[0]["company_name"] == "南京芯动云图技术有限公司"


def test_company_profile_marks_search_results_as_external_search(monkeypatch) -> None:
    client = TestClient(create_app())
    provider_response = client.post(
        "/api/llm/providers",
        json={
            "name": "Test LLM",
            "provider_type": "openai_compatible",
            "api_key": "test-key",
            "base_url": "https://example.test/v1",
            "model": "test-model",
            "enabled": True,
            "is_active": True,
        },
    )
    assert provider_response.status_code == 200
    search_response = client.post(
        "/api/search/providers",
        json={
            "name": "Exa Test",
            "provider_type": "exa",
            "api_key": "test-search-key",
            "base_url": "https://api.exa.ai",
            "enabled": True,
            "is_active": True,
        },
    )
    assert search_response.status_code == 200
    monkeypatch.setattr(
        "app.services.company_profiles.build_llm_provider",
        lambda _: FakeCompanyLLMProvider(),
    )
    monkeypatch.setattr(
        "app.services.company_profiles._search_company_context",
        lambda *_: [
            {
                "title": "南京芯动云图技术有限公司",
                "url": "https://example.com/company",
                "snippet": "南京芯动云图技术有限公司是一家医疗健康技术公司。",
                "source": "exa",
            }
        ],
    )

    enrich_response = client.post(
        "/api/companies/enrich",
        json={"company_name": "南京芯动云图技术有限公司"},
    )

    assert enrich_response.status_code == 200
    profile = enrich_response.json()
    assert profile["status"] == "external_search_enriched"
    assert profile["source_urls"] == ["https://example.com/company"]
    assert profile["field_sources"]["industry"] == "external_search"
    assert profile["field_sources"]["scale"] == "external_search"
