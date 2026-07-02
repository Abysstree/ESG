from pathlib import Path

from app.services import ocr


def test_extract_text_from_image_reports_unavailable(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-png-bytes")

    def fake_get_paddle_ocr():
        raise ocr.OCRUnavailableError("PaddleOCR 未安装")

    monkeypatch.setattr(ocr, "_get_paddle_ocr", fake_get_paddle_ocr)

    result = ocr.extract_text_from_image(image_path)

    assert result.text == ""
    assert result.status == "unavailable"
    assert result.engine == "paddleocr"
    assert result.error == "PaddleOCR 未安装"


def test_extract_text_from_image_parses_paddle_ocr_result(monkeypatch, tmp_path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake-png-bytes")

    class FakePaddleOCR:
        def ocr(self, path: str, cls: bool = True):
            assert Path(path) == image_path
            assert cls is True
            return [
                [
                    [[[0, 0], [1, 0], [1, 1], [0, 1]], ("公司：示例科技", 0.99)],
                    [[[0, 2], [1, 2], [1, 3], [0, 3]], ("岗位名称：算法工程师", 0.98)],
                ]
            ]

    monkeypatch.setattr(ocr, "_get_paddle_ocr", lambda: FakePaddleOCR())

    result = ocr.extract_text_from_image(image_path)

    assert result.status == "succeeded"
    assert result.text == "公司：示例科技\n岗位名称：算法工程师"
    assert result.error is None
