from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db.models import SearchProviderConfig
from app.main import create_app


def test_default_search_provider_configs_include_exa_and_tavily() -> None:
    client = TestClient(create_app())

    response = client.get("/api/search/providers")

    assert response.status_code == 200
    providers = response.json()
    assert providers[0]["provider_type"] == "exa"
    provider_types = {provider["provider_type"] for provider in providers}
    assert {"exa", "tavily"}.issubset(provider_types)
    assert all("api_key" not in provider for provider in providers)


def test_create_and_activate_search_provider_config_updates_status() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/api/search/providers",
        json={
            "name": "Exa Test",
            "provider_type": "exa",
            "api_key": "test-search-key",
            "base_url": "https://api.exa.ai",
            "enabled": True,
            "is_active": False,
        },
    )

    assert create_response.status_code == 200
    provider = create_response.json()
    assert provider["api_key_set"] is True
    assert "api_key" not in provider
    with SessionLocal() as session:
        stored_provider = session.get(SearchProviderConfig, provider["id"])
        assert stored_provider is not None
        assert stored_provider.api_key is not None
        assert stored_provider.api_key.startswith("enc:v1:")
        assert "test-search-key" not in stored_provider.api_key

    activate_response = client.post(f"/api/search/providers/{provider['id']}/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True

    status_response = client.get("/api/search/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["provider"] == "exa"
    assert status["configured"] is True
    assert status["active_provider_id"] == provider["id"]
