from fastapi.testclient import TestClient

from app.main import create_app
from app.services.ocr import OCRResult
from app.services.url_reader import URLReadResult


def test_create_text_import() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "手动粘贴文本",
            "raw_text": "岗位职责：负责算法开发。",
        },
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "text"
    assert response.json()["status"] == "mock_extracted"


def test_create_url_import_fetches_public_page_text(monkeypatch) -> None:
    def fake_read_url_text(url: str) -> URLReadResult:
        assert url == "https://example.com/jobs/1"
        return URLReadResult(
            text="""
            岗位名称：医学影像处理算法工程师
            公司：示例医疗
            薪资：10-15K
            地点：南京
            岗位职责：负责医学影像配准和三维重建算法开发。
            任职要求：熟悉 Python、SimpleITK、Open3D。
            """,
            status="url_fetched",
        )

    monkeypatch.setattr("app.api.imports.read_url_text", fake_read_url_text)

    client = TestClient(create_app())
    response = client.post(
        "/api/imports",
        json={
            "source_type": "url",
            "source_value": "https://example.com/jobs/1",
            "raw_text": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_type"] == "url"
    assert "医学影像处理算法工程师" in payload["raw_text"]
    assert payload["status"] == "mock_extracted"

    jobs_response = client.get("/api/jobs")
    assert jobs_response.status_code == 200
    assert jobs_response.json()[0]["company_name"] == "示例医疗"


def test_create_url_import_marks_protected_page(monkeypatch) -> None:
    def fake_read_url_text(url: str) -> URLReadResult:
        assert url == "https://m.zhipin.com/mpa/html/weijd/weijd-job/example"
        return URLReadResult(
            text=None,
            status="url_fetch_protected",
            error="平台环境校验",
        )

    monkeypatch.setattr("app.api.imports.read_url_text", fake_read_url_text)

    client = TestClient(create_app())
    response = client.post(
        "/api/imports",
        json={
            "source_type": "url",
            "source_value": "https://m.zhipin.com/mpa/html/weijd/weijd-job/example",
            "raw_text": None,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["raw_text"] is None
    assert payload["status"] == "url_fetch_protected"
    assert client.get("/api/jobs").json() == []


def test_create_url_import_uses_manual_backup_text(monkeypatch) -> None:
    def fake_read_url_text(url: str) -> URLReadResult:
        raise AssertionError("manual raw_text should skip URL fetch")

    monkeypatch.setattr("app.api.imports.read_url_text", fake_read_url_text)

    client = TestClient(create_app())
    response = client.post(
        "/api/imports",
        json={
            "source_type": "url",
            "source_value": "https://example.com/jobs/2",
            "raw_text": "岗位名称：嵌入式软件工程师\n岗位职责：负责固件开发。",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "mock_extracted"


def test_delete_import_removes_generated_job_card() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/imports",
        json={
            "source_type": "text",
            "source_value": "手动粘贴文本",
            "raw_text": "岗位名称：嵌入式软件工程师\n岗位职责：负责固件开发。",
        },
    )
    raw_import_id = response.json()["id"]
    assert client.get("/api/jobs").json()

    delete_response = client.delete(f"/api/imports/{raw_import_id}")

    assert delete_response.status_code == 204
    assert client.get("/api/imports").json() == []
    assert client.get("/api/jobs").json() == []


def test_create_screenshot_import() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/imports/screenshot",
        data={"raw_text": "公司：示例科技\n岗位名称：算法工程师"},
        files={"file": ("sample.png", b"fake-png-bytes", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "screenshot"
    assert response.json()["source_value"].endswith(".png")


def test_create_screenshot_import_uses_ocr_when_raw_text_missing(monkeypatch) -> None:
    ocr_text = """
    公司：未来视觉
    岗位名称：医学影像处理算法工程师
    岗位职责：
    负责医学影像分割算法开发
    任职要求：
    熟悉 Python、PyTorch 和图像处理
    """
    called_paths = []

    def fake_extract_text_from_image(path):
        called_paths.append(path)
        return OCRResult(text=ocr_text, status="succeeded")

    monkeypatch.setattr(
        "app.api.imports.extract_text_from_image",
        fake_extract_text_from_image,
    )

    client = TestClient(create_app())
    response = client.post(
        "/api/imports/screenshot",
        files={"file": ("sample.png", b"fake-png-bytes", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert called_paths
    assert payload["raw_text"] == ocr_text.strip()
    assert payload["status"] == "mock_extracted"

    jobs_response = client.get("/api/jobs")
    jobs = jobs_response.json()
    assert jobs_response.status_code == 200
    assert jobs[0]["role_category"] == "医学影像处理算法工程师"


def test_create_screenshot_import_marks_ocr_unavailable(monkeypatch) -> None:
    def fake_extract_text_from_image(path):
        return OCRResult(
            text="",
            status="unavailable",
            error="PaddleOCR 未安装",
        )

    monkeypatch.setattr(
        "app.api.imports.extract_text_from_image",
        fake_extract_text_from_image,
    )

    client = TestClient(create_app())
    response = client.post(
        "/api/imports/screenshot",
        files={"file": ("sample.png", b"fake-png-bytes", "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["raw_text"] is None
    assert payload["status"] == "ocr_unavailable"
    assert client.get("/api/jobs").json() == []
