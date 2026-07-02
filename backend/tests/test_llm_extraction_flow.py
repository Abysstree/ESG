from fastapi.testclient import TestClient

from app.main import create_app


class FakeLLMProvider:
    name = "fake"

    def extract_job_card(self, raw_text: str) -> dict[str, object]:
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": {
                "title": "医学影像处理算法工程师",
                "company_name": "南京芯动云图技术有限公司",
                "role_category": "医学影像处理算法工程师",
                "salary_range": "10-15K",
                "salary_period": "monthly",
                "base_location": "南京",
                "education_requirement": "硕士",
                "experience_requirement": "1-3年",
                "responsibilities": ["负责三维医学影像算法开发"],
                "requirements": ["熟悉 Python 和三维图像处理"],
                "bonus_points": ["做过医学图像配准优先"],
                "skills": ["Python", "医学影像", "配准"],
                "field_sources": {
                    "title": "original_posting",
                    "company_name": "original_posting",
                    "role_category": "model_inference",
                    "salary_range": "original_posting",
                    "salary_period": "model_inference",
                    "base_location": "original_posting",
                    "education_requirement": "original_posting",
                    "experience_requirement": "original_posting",
                    "responsibilities": "original_posting",
                    "requirements": "original_posting",
                    "bonus_points": "original_posting",
                    "skills": "model_inference",
                },
                "evidence": {
                    "title": "医学影像处理算法工程师",
                    "salary_range": "10-15K",
                },
                "inference_notes": ["岗位大类由医学影像关键词推断。"],
                "confidence": "high",
            },
        }


class FakeHuaweiLLMProvider:
    name = "fake"

    def extract_job_card(self, raw_text: str) -> dict[str, object]:
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": {
                "title": "AI算法工程师 应届生 华为",
                "company_name": None,
                "role_category": "AI算法工程师",
                "salary_range": None,
                "salary_period": None,
                "base_location": "东莞",
                "education_requirement": "本科",
                "experience_requirement": "应届生",
                "responsibilities": ["从事多模态算法前沿研究和产品落地工作"],
                "requirements": ["掌握多模态理解、多模态生成和 DeepSpeed"],
                "bonus_points": [],
                "skills": ["多模态理解", "DeepSpeed"],
                "field_sources": {
                    "title": "original_posting",
                    "company_name": "missing",
                    "role_category": "model_inference",
                    "salary_range": "missing",
                    "salary_period": "missing",
                    "base_location": "original_posting",
                    "education_requirement": "model_inference",
                    "experience_requirement": "original_posting",
                    "responsibilities": "original_posting",
                    "requirements": "original_posting",
                    "bonus_points": "missing",
                    "skills": "model_inference",
                },
                "evidence": {},
                "inference_notes": [],
                "confidence": "medium",
            },
        }


class FakeFullAddressLLMProvider:
    name = "fake"

    def extract_job_card(self, raw_text: str) -> dict[str, object]:
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": {
                "title": "医学影像处理算法工程师",
                "company_name": "南京芯动云图技术有限公司",
                "role_category": "医学影像处理算法工程师",
                "salary_range": "10-15K",
                "salary_period": "monthly",
                "base_location": "南京建邺区阿里巴巴江苏总部T5栋905-2、906",
                "education_requirement": "硕士",
                "experience_requirement": "1-3年",
                "responsibilities": ["负责三维医学影像算法开发"],
                "requirements": ["熟悉 Python 和三维图像处理"],
                "bonus_points": [],
                "skills": ["Python", "VTK"],
                "field_sources": {
                    "title": "original_posting",
                    "company_name": "original_posting",
                    "role_category": "model_inference",
                    "salary_range": "original_posting",
                    "salary_period": "model_inference",
                    "base_location": "original_posting",
                    "education_requirement": "original_posting",
                    "experience_requirement": "original_posting",
                    "responsibilities": "original_posting",
                    "requirements": "original_posting",
                    "bonus_points": "missing",
                    "skills": "model_inference",
                },
                "evidence": {},
                "inference_notes": [],
                "confidence": "high",
            },
        }


class FakeInferredHardFactsLLMProvider:
    name = "fake"

    def extract_job_card(self, raw_text: str) -> dict[str, object]:
        return {
            "provider": self.name,
            "mode": "cloud",
            "job_card": {
                "title": "算法工程师",
                "company_name": "示例科技",
                "role_category": "算法工程师",
                "salary_range": "20-30K",
                "salary_period": "monthly",
                "base_location": "北京",
                "education_requirement": "硕士",
                "experience_requirement": "3-5年",
                "responsibilities": ["负责算法研发"],
                "requirements": ["熟悉深度学习"],
                "bonus_points": ["有顶会论文优先", "有工程落地经验优先"],
                "skills": ["Python", "PyTorch"],
                "field_sources": {
                    "title": "original_posting",
                    "company_name": "original_posting",
                    "role_category": "model_inference",
                    "salary_range": "model_inference",
                    "salary_period": "model_inference",
                    "base_location": "model_inference",
                    "education_requirement": "model_inference",
                    "experience_requirement": "model_inference",
                    "responsibilities": "model_inference",
                    "requirements": "model_inference",
                    "bonus_points": "model_inference",
                    "skills": "model_inference",
                },
                "evidence": {},
                "inference_notes": ["加分项和技能由模型推测。"],
                "confidence": "medium",
            },
        }


def test_import_uses_active_llm_provider_to_create_job_card(monkeypatch) -> None:
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
        "app.services.job_cards.build_llm_provider",
        lambda _: FakeLLMProvider(),
    )

    import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": "医学影像处理算法工程师\n南京·1-3年·硕士\n10-15K",
        },
    )

    assert import_response.status_code == 200
    assert import_response.json()["status"] == "llm_extracted"

    jobs = client.get("/api/jobs").json()
    assert jobs[0]["title"] == "医学影像处理算法工程师"
    assert jobs[0]["status"] == "llm_extracted"
    assert jobs[0]["confidence"] == "high"
    assert jobs[0]["evidence"]["salary_range"] == "10-15K"


def test_import_normalizes_huawei_campus_title_company_and_locations(monkeypatch) -> None:
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
        "app.services.job_cards.build_llm_provider",
        lambda _: FakeHuaweiLLMProvider(),
    )

    raw_text = "\n".join(
        [
            "AI算法工程师 应届生 华为",
            "研发类",
            "深圳/上海/东莞/北京",
            "岗位职责",
            "1、从事多模态算法前沿研究和产品落地工作",
            "岗位要求",
            "1、计算机科学、电子信息、人工智能等相关专业",
            "2、掌握多模态理解、多模态生成和 DeepSpeed",
            "工作地点",
            "东莞/上海/北京/南京/深圳/杭州/西安/武汉/成都/苏州/长沙/济南",
        ]
    )
    import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": raw_text,
        },
    )

    assert import_response.status_code == 200
    job = client.get("/api/jobs").json()[0]
    assert job["title"] == "AI算法工程师（应届生）"
    assert job["company_name"] == "华为"
    assert job["base_location"] == "东莞/上海/北京/南京/深圳/杭州/西安/武汉/成都/苏州/长沙/济南"
    assert job["education_requirement"] is None
    assert job["field_sources"]["company_name"] == "original_posting"
    assert job["field_sources"]["education_requirement"] == "missing"


def test_import_summarizes_full_work_address_to_city_district(monkeypatch) -> None:
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
        "app.services.job_cards.build_llm_provider",
        lambda _: FakeFullAddressLLMProvider(),
    )

    full_address = "南京建邺区阿里巴巴江苏总部T5栋905-2、906"
    import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": "\n".join(
                [
                    "医学影像处理算法工程师",
                    "南京·1-3年·硕士",
                    "10-15K",
                    "工作地点",
                    full_address,
                ]
            ),
        },
    )

    assert import_response.status_code == 200
    job = client.get("/api/jobs").json()[0]
    assert job["base_location"] == "南京建邺区"
    assert job["evidence"]["base_location"] == full_address


def test_import_drops_inferred_hard_facts_but_keeps_inferred_bonus_and_skills(
    monkeypatch,
) -> None:
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
        "app.services.job_cards.build_llm_provider",
        lambda _: FakeInferredHardFactsLLMProvider(),
    )

    import_response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": "算法工程师\n示例科技",
        },
    )

    assert import_response.status_code == 200
    job = client.get("/api/jobs").json()[0]
    assert job["salary_range"] is None
    assert job["base_location"] is None
    assert job["education_requirement"] is None
    assert job["experience_requirement"] is None
    assert job["responsibilities"] == []
    assert job["requirements"] == []
    assert job["field_sources"]["salary_range"] == "missing"
    assert job["field_sources"]["responsibilities"] == "missing"
    assert job["bonus_points"] == ["有顶会论文优先", "有工程落地经验优先"]
    assert job["skills"] == ["Python", "PyTorch"]
    assert job["field_sources"]["bonus_points"] == "model_inference"
    assert job["field_sources"]["skills"] == "model_inference"
