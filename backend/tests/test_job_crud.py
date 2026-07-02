from fastapi.testclient import TestClient

from app.main import create_app


def test_update_and_delete_job_card() -> None:
    client = TestClient(create_app())
    client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "manual pasted text",
            "raw_text": "岗位名称：嵌入式软件工程师\n10-15K\n南京·1-3年·本科\n岗位职责\n负责驱动开发",
        },
    )
    jobs = client.get("/api/jobs").json()
    job = next(job for job in jobs if job["title"] == "嵌入式软件工程师")

    update_response = client.patch(
        f"/api/jobs/{job['id']}",
        json={
            "company_name": "用户修正公司",
            "salary_range": "12-18K",
            "salary_period": "monthly",
            "skills": ["C++", "Linux"],
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["company_name"] == "用户修正公司"
    assert updated["salary_range"] == "12-18K"
    assert updated["status"] == "user_edited"
    assert updated["field_sources"]["company_name"] == "user_edit"

    delete_response = client.delete(f"/api/jobs/{job['id']}")

    assert delete_response.status_code == 204
    remaining_jobs = client.get("/api/jobs").json()
    assert all(item["id"] != job["id"] for item in remaining_jobs)
