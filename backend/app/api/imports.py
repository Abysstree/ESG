from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import DATA_DIR, get_session
from app.db.models import JobCard, RawImport
from app.schemas.imports import RawImportCreate, RawImportRead
from app.services.job_cards import create_job_card_for_import
from app.services.ocr import OCRResult, extract_text_from_image
from app.services.role_profiles import mark_role_profiles_stale
from app.services.url_reader import read_url_text

router = APIRouter(prefix="/imports", tags=["imports"])

SCREENSHOTS_DIR = DATA_DIR / "screenshots"
ALLOWED_IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".webp"}
MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024
OCR_PENDING_TEXTS = {"OCR 待识别"}


@router.post("", response_model=RawImportRead)
def create_import(
    payload: RawImportCreate,
    session: Session = Depends(get_session),
) -> RawImport:
    raw_text = _normalize_raw_text(payload.raw_text)
    import_status = "created"

    if payload.source_type == "url" and raw_text is None:
        url_result = read_url_text(payload.source_value)
        raw_text = url_result.text
        import_status = url_result.status

    raw_import = RawImport(
        source_type=payload.source_type,
        source_value=payload.source_value,
        raw_text=raw_text,
        status=import_status,
    )
    session.add(raw_import)
    session.commit()
    session.refresh(raw_import)
    create_job_card_for_import(raw_import, session)
    return raw_import


@router.post("/screenshot", response_model=RawImportRead)
async def create_screenshot_import(
    file: UploadFile = File(...),
    raw_text: str | None = Form(default=None),
    session: Session = Depends(get_session),
) -> RawImport:
    suffix = Path(file.filename or "").suffix.lower() or ".png"
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only image files are supported.")

    contents = await file.read()
    if len(contents) > MAX_SCREENSHOT_BYTES:
        raise HTTPException(status_code=400, detail="Screenshot must be 10 MB or smaller.")

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"screenshot-{uuid4().hex}{suffix}"
    saved_path = SCREENSHOTS_DIR / saved_name
    saved_path.write_bytes(contents)

    normalized_raw_text = _normalize_screenshot_raw_text(raw_text)
    import_status = "created"
    if normalized_raw_text is None:
        ocr_result = extract_text_from_image(saved_path)
        if ocr_result.is_success:
            normalized_raw_text = ocr_result.text.strip()
            import_status = "ocr_extracted"
        else:
            import_status = _import_status_from_ocr_result(ocr_result)

    raw_import = RawImport(
        source_type="screenshot",
        source_value=saved_name,
        raw_text=normalized_raw_text,
        status=import_status,
    )
    session.add(raw_import)
    session.commit()
    session.refresh(raw_import)
    create_job_card_for_import(raw_import, session)
    return raw_import


@router.get("", response_model=list[RawImportRead])
def list_imports(session: Session = Depends(get_session)) -> list[RawImport]:
    statement = select(RawImport).order_by(RawImport.created_at.desc())
    return list(session.scalars(statement))


@router.delete("/{raw_import_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_import(
    raw_import_id: int,
    session: Session = Depends(get_session),
) -> Response:
    raw_import = session.get(RawImport, raw_import_id)
    if not raw_import:
        raise HTTPException(status_code=404, detail="Import record not found.")

    role_categories: list[str | None] = []
    for job_card in session.scalars(
        select(JobCard).where(JobCard.raw_import_id == raw_import_id),
    ):
        role_categories.append(job_card.role_category)
        session.delete(job_card)
    mark_role_profiles_stale(
        role_categories,
        session,
        reason="raw_import_deleted",
    )
    _delete_screenshot_file(raw_import)
    session.delete(raw_import)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _normalize_screenshot_raw_text(raw_text: str | None) -> str | None:
    normalized = _normalize_raw_text(raw_text)
    if normalized is None:
        return None

    if normalized in OCR_PENDING_TEXTS:
        return None

    return normalized


def _delete_screenshot_file(raw_import: RawImport) -> None:
    if raw_import.source_type != "screenshot":
        return
    screenshot_path = SCREENSHOTS_DIR / Path(raw_import.source_value).name
    if screenshot_path.exists() and screenshot_path.is_file():
        screenshot_path.unlink()


def _normalize_raw_text(raw_text: str | None) -> str | None:
    if raw_text is None:
        return None

    normalized = raw_text.strip()
    if not normalized:
        return None

    return normalized


def _import_status_from_ocr_result(result: OCRResult) -> str:
    if result.status == "unavailable":
        return "ocr_unavailable"
    if result.status == "empty":
        return "ocr_empty"
    if result.status == "failed":
        return "ocr_failed"

    return "ocr_failed"
