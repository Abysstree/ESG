from fastapi.testclient import TestClient

from app.main import create_app


def test_import_with_text_creates_job_card() -> None:
    client = TestClient(create_app())
    client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "手动粘贴文本",
            "raw_text": """
            公司：未来视觉
            岗位名称：医学影像处理算法工程师
            岗位职责：
            负责医学影像分割算法开发
            任职要求：
            熟悉 Python、PyTorch 和图像处理
            加分项：
            有医疗图像项目经验优先
            """,
        },
    )

    response = client.get("/api/jobs")
    assert response.status_code == 200
    jobs = response.json()
    matching_jobs = [
        job for job in jobs if job["role_category"] == "医学影像处理算法工程师"
    ]

    assert matching_jobs
    assert "图像处理" in matching_jobs[0]["skills"]
