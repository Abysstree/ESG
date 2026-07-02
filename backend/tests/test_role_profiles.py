from fastapi.testclient import TestClient

from app.main import create_app


class FakeRoleProfileProvider:
    name = "fake"

    def generate_role_profile(self, role_payload: dict[str, object]) -> dict[str, object]:
        role_category = str(role_payload["role_category"])
        return {
            "provider": self.name,
            "mode": "cloud",
            "role_profile": {
                "role_category": role_category,
                "summary": f"{role_category} 的测试画像",
                "job_count": role_payload["job_count"],
                "representative_titles": role_payload["representative_titles"],
                "core_responsibilities": role_payload["core_responsibilities"],
                "common_requirements": role_payload["common_requirements"],
                "high_frequency_skills": role_payload["high_frequency_skills"],
                "bonus_signals": role_payload["bonus_signals"],
                "learning_map": {
                    "center_title": role_category,
                    "center_subtitle": "1 个岗位样本",
                    "branches": [
                        {
                            "id": "core_skills",
                            "title": "核心技能",
                            "focus": "核心技能",
                            "source_fields": ["skills"],
                            "evidence": ["Python"],
                            "nodes": [
                                {
                                    "id": "skill.python",
                                    "title": "Python",
                                    "node_type": "skill",
                                    "level": "foundation",
                                    "source_fields": ["skills"],
                                    "evidence": ["Python"],
                                    "children": [],
                                }
                            ],
                        }
                    ],
                },
                "field_sources": {"learning_map": "model_inference"},
                "evidence": {"learning_map": ["Python"]},
                "inference_notes": ["测试生成"],
                "confidence": "medium",
            },
            "raw_response": {"ok": True},
        }


def test_role_profile_endpoint_generates_learning_map(monkeypatch) -> None:
    client = TestClient(create_app())
    import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": (
                "岗位名称：医学影像处理算法工程师\n"
                "岗位职责：负责医学影像算法开发\n"
                "任职要求：熟悉 Python"
            ),
        },
    )
    assert import_response.status_code == 200

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
        "app.services.role_profiles.build_llm_provider",
        lambda _: FakeRoleProfileProvider(),
    )

    response = client.post(
        "/api/roles/profile",
        json={"role_category": "医学影像处理算法工程师"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "fake"
    assert payload["status"] == "fresh"
    assert payload["role_profile"]["learning_map"]["branches"][0]["title"] == "核心技能"

    profiles_response = client.get("/api/roles/profiles")
    assert profiles_response.status_code == 200
    profiles = profiles_response.json()
    assert len(profiles) == 1
    assert profiles[0]["role_category"] == "医学影像处理算法工程师"
    assert profiles[0]["status"] == "fresh"
    assert profiles[0]["role_profile"]["learning_map"]["branches"][0]["nodes"][0]["title"] == "Python"


def test_role_profile_is_marked_stale_when_matching_job_import_changes(monkeypatch) -> None:
    client = TestClient(create_app())
    for raw_text in (
        "岗位名称：医学影像处理算法工程师\n岗位职责：负责医学影像算法开发\n任职要求：熟悉 Python",
    ):
        response = client.post(
            "/api/imports",
            json={
                "source_type": "text",
                "source_value": "manual pasted text",
                "raw_text": raw_text,
            },
        )
        assert response.status_code == 200

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
        "app.services.role_profiles.build_llm_provider",
        lambda _: FakeRoleProfileProvider(),
    )

    generate_response = client.post(
        "/api/roles/profile",
        json={"role_category": "医学影像处理算法工程师"},
    )
    assert generate_response.status_code == 200
    assert generate_response.json()["status"] == "fresh"

    second_import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": (
                "岗位名称：医学影像处理算法工程师\n"
                "岗位职责：负责三维重建算法开发\n"
                "任职要求：熟悉 SimpleITK"
            ),
        },
    )
    assert second_import_response.status_code == 200

    profiles_response = client.get("/api/roles/profiles")
    assert profiles_response.status_code == 200
    profiles = profiles_response.json()
    assert profiles[0]["role_category"] == "医学影像处理算法工程师"
    assert profiles[0]["status"] == "stale"
    assert profiles[0]["input"]["stale_reason"] in {
        "mock_extracted",
        "llm_failed_mock_extracted",
    }
