from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.models import LLMProviderConfig
from app.main import create_app


def test_default_llm_provider_configs_include_major_cloud_providers() -> None:
    client = TestClient(create_app())

    response = client.get("/api/llm/providers")

    assert response.status_code == 200
    providers = response.json()
    assert providers[0]["provider_type"] == "deepseek"
    provider_types = {provider["provider_type"] for provider in providers}
    assert {"deepseek", "openai_compatible", "anthropic", "google"}.issubset(
        provider_types
    )
    assert all("api_key" not in provider for provider in providers)


def test_create_and_activate_llm_provider_config_updates_status() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/api/llm/providers",
        json={
            "name": "SiliconFlow",
            "provider_type": "openai_compatible",
            "api_key": "test-key",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Qwen/Qwen3-8B",
            "enabled": True,
            "is_active": False,
        },
    )
    assert create_response.status_code == 200
    provider = create_response.json()
    assert provider["api_key_set"] is True
    assert "api_key" not in provider
    with SessionLocal() as session:
        stored_provider = session.get(LLMProviderConfig, provider["id"])
        assert stored_provider is not None
        assert stored_provider.api_key is not None
        assert stored_provider.api_key.startswith("enc:v1:")
        assert "test-key" not in stored_provider.api_key

    activate_response = client.post(f"/api/llm/providers/{provider['id']}/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True

    status_response = client.get("/api/llm/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["provider"] == "openai_compatible"
    assert status["configured"] is True
    assert status["base_url"] == "https://api.siliconflow.cn/v1"
    assert status["model"] == "Qwen/Qwen3-8B"
    assert status["active_provider_id"] == provider["id"]


def test_extract_preview_uses_active_saved_provider_config() -> None:
    client = TestClient(create_app())

    providers = client.get("/api/llm/providers").json()
    openai_provider = next(
        provider
        for provider in providers
        if provider["provider_type"] == "openai_compatible"
    )
    activate_response = client.post(
        f"/api/llm/providers/{openai_provider['id']}/activate",
    )
    assert activate_response.status_code == 200

    response = client.post(
        "/api/llm/extract-preview",
        json={"raw_text": "岗位职责：负责算法开发"},
    )

    assert response.status_code == 400
    assert "API key is required" in response.json()["detail"]


def test_extract_preview_returns_debug_payload_without_saving_job_card() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/llm/extract-preview",
        json={
            "raw_text": (
                "岗位名称：医学影像处理算法工程师\n"
                "南京·1-3年·硕士\n"
                "10-15K\n"
                "岗位职责：负责 CT、MRI 医学影像配准和三维重建算法开发\n"
                "任职要求：熟悉 Python、VTK、SimpleITK"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert "JSON Schema" in payload["prompt"]
    assert payload["extracted_schema"]["title"] == "医学影像处理算法工程师"
    assert payload["normalized_job_card"]["role_category"] == "医学影像处理算法工程师"
    assert payload["quality_checks"]["required_field_count"] >= 10
    assert client.get("/api/jobs").json() == []
