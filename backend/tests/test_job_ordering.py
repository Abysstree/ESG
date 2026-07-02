from fastapi.testclient import TestClient

from app.main import create_app


def _create_job(client: TestClient, title: str) -> int:
    client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": title,
            "raw_text": f"岗位名称：{title}\n岗位职责\n负责测试排序",
        },
    )
    jobs = client.get("/api/jobs").json()
    return next(job["id"] for job in jobs if job["title"] == title)


def test_reorder_and_pin_jobs() -> None:
    client = TestClient(create_app())
    first_id = _create_job(client, "排序岗位A")
    second_id = _create_job(client, "排序岗位B")

    reorder_response = client.post(
        "/api/jobs/reorder",
        json={"job_ids": [first_id, second_id]},
    )

    assert reorder_response.status_code == 200
    reordered_ids = [job["id"] for job in reorder_response.json()]
    assert reordered_ids[:2] == [first_id, second_id]

    pin_response = client.patch(f"/api/jobs/{first_id}", json={"is_pinned": True})

    assert pin_response.status_code == 200
    jobs = client.get("/api/jobs").json()
    assert jobs[0]["id"] == first_id
    assert jobs[0]["is_pinned"] is True
