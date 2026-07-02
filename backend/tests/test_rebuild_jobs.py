from fastapi.testclient import TestClient

from app.main import create_app


def test_rebuild_mock_jobs_updates_existing_card() -> None:
    client = TestClient(create_app())
    client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": """
            医学影像处理算法工程师
            芯动云图 未融资
            岗位职责
            负责医学影像算法开发
            任职要求
            熟悉 Python 和 VTK
            所在公司
            南京芯动云图技术有限公司
            """,
        },
    )

    response = client.post("/api/jobs/rebuild-mock")

    assert response.status_code == 200
    matching_jobs = [
        job
        for job in response.json()
        if job["company_name"] == "南京芯动云图技术有限公司"
    ]
    assert matching_jobs
