from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


OCRStatus = Literal["succeeded", "empty", "unavailable", "failed"]
PADDLEOCR_ENGINE = "paddleocr"

_cached_paddle_ocr: Any | None = None


@dataclass(frozen=True)
class OCRResult:
    text: str
    status: OCRStatus
    engine: str = PADDLEOCR_ENGINE
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == "succeeded" and bool(self.text.strip())


class OCRUnavailableError(RuntimeError):
    pass


def extract_text_from_image(path: Path) -> OCRResult:
    image_path = Path(path)
    if not image_path.exists():
        return OCRResult(
            text="",
            status="failed",
            error=f"图片文件不存在：{image_path}",
        )

    try:
        paddle_ocr = _get_paddle_ocr()
    except OCRUnavailableError as exc:
        return OCRResult(text="", status="unavailable", error=str(exc))

    try:
        raw_result = _run_paddle_ocr(paddle_ocr, image_path)
    except Exception as exc:
        return OCRResult(
            text="",
            status="failed",
            error=f"PaddleOCR 识别失败：{exc}",
        )

    text = "\n".join(_extract_text_lines(raw_result)).strip()
    if not text:
        return OCRResult(
            text="",
            status="empty",
            error="PaddleOCR 未识别到文字。",
        )

    return OCRResult(text=text, status="succeeded")


def _get_paddle_ocr() -> Any:
    global _cached_paddle_ocr

    if _cached_paddle_ocr is not None:
        return _cached_paddle_ocr

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OCRUnavailableError(
            "PaddleOCR 未安装；安装 paddleocr 和匹配版本的 paddlepaddle 后可启用截图 OCR。"
        ) from exc
    except Exception as exc:
        raise OCRUnavailableError(f"PaddleOCR 加载失败：{exc}") from exc

    try:
        _cached_paddle_ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    except TypeError:
        try:
            _cached_paddle_ocr = PaddleOCR(lang="ch")
        except Exception as exc:
            raise OCRUnavailableError(f"PaddleOCR 初始化失败：{exc}") from exc
    except Exception as exc:
        raise OCRUnavailableError(f"PaddleOCR 初始化失败：{exc}") from exc

    return _cached_paddle_ocr


def _run_paddle_ocr(paddle_ocr: Any, image_path: Path) -> Any:
    if hasattr(paddle_ocr, "ocr"):
        try:
            return paddle_ocr.ocr(str(image_path), cls=True)
        except TypeError:
            return paddle_ocr.ocr(str(image_path))

    if hasattr(paddle_ocr, "predict"):
        return paddle_ocr.predict(str(image_path))

    raise RuntimeError("PaddleOCR 实例缺少 ocr 或 predict 方法。")


def _extract_text_lines(raw_result: Any) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()

    def add_line(value: Any) -> None:
        if not isinstance(value, str):
            return
        line = value.strip()
        if line and line not in seen:
            seen.add(line)
            lines.append(line)

    def walk(node: Any) -> None:
        if node is None:
            return

        for attr_name in ("rec_texts", "texts"):
            if hasattr(node, attr_name):
                walk(getattr(node, attr_name))
                return

        if isinstance(node, dict):
            for key in ("rec_texts", "texts"):
                if key in node:
                    walk(node[key])
                    return

            for key in ("text", "transcription"):
                add_line(node.get(key))

            for value in node.values():
                walk(value)
            return

        if isinstance(node, str):
            add_line(node)
            return

        if isinstance(node, tuple):
            if node and isinstance(node[0], str):
                add_line(node[0])
                return
            for item in node:
                walk(item)
            return

        if isinstance(node, list):
            if len(node) >= 2 and isinstance(node[1], tuple):
                tuple_value = node[1]
                if tuple_value and isinstance(tuple_value[0], str):
                    add_line(tuple_value[0])
                    return

            for item in node:
                walk(item)

    walk(raw_result)
    return lines
