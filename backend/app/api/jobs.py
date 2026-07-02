import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import JobCard
from app.schemas.jobs import JobCardRead, JobCardReorder, JobCardUpdate
from app.services.job_cards import (
    rebuild_llm_job_cards,
    rebuild_mock_job_cards,
    reextract_job_card_with_llm,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobCardRead])
def list_jobs(session: Session = Depends(get_session)) -> list[JobCard]:
    statement = select(JobCard).order_by(
        JobCard.is_pinned.desc(),
        JobCard.sort_order.asc(),
        JobCard.created_at.desc(),
    )
    return list(session.scalars(statement))


@router.post("/rebuild-mock", response_model=list[JobCardRead])
def rebuild_jobs_with_mock_extractor(
    session: Session = Depends(get_session),
) -> list[JobCard]:
    return rebuild_mock_job_cards(session)


@router.post("/rebuild-llm", response_model=list[JobCardRead])
def rebuild_jobs_with_active_llm(
    session: Session = Depends(get_session),
) -> list[JobCard]:
    try:
        return rebuild_llm_job_cards(session)
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reorder", response_model=list[JobCardRead])
def reorder_jobs(
    payload: JobCardReorder,
    session: Session = Depends(get_session),
) -> list[JobCard]:
    jobs_by_id = {
        job.id: job
        for job in session.scalars(
            select(JobCard).where(JobCard.id.in_(payload.job_ids))
        )
    }

    if len(jobs_by_id) != len(set(payload.job_ids)):
        raise HTTPException(status_code=404, detail="One or more job cards were not found.")

    for index, job_id in enumerate(payload.job_ids):
        jobs_by_id[job_id].sort_order = index
        session.add(jobs_by_id[job_id])

    session.commit()
    return list_jobs(session)


@router.post("/{job_id}/reextract", response_model=JobCardRead)
def reextract_job(
    job_id: int,
    session: Session = Depends(get_session),
) -> JobCard:
    try:
        return reextract_job_card_with_llm(job_id, session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{job_id}", response_model=JobCardRead)
def update_job(
    job_id: int,
    payload: JobCardUpdate,
    session: Session = Depends(get_session),
) -> JobCard:
    job_card = session.get(JobCard, job_id)
    if not job_card:
        raise HTTPException(status_code=404, detail="Job card not found.")

    update_data = payload.model_dump(exclude_unset=True)
    list_fields = {
        "responsibilities": "responsibilities_json",
        "requirements": "requirements_json",
        "bonus_points": "bonus_points_json",
        "skills": "skills_json",
    }

    for field_name, value in update_data.items():
        if field_name in list_fields:
            setattr(
                job_card,
                list_fields[field_name],
                json.dumps(value or [], ensure_ascii=False),
            )
        else:
            setattr(job_card, field_name, value)

    field_sources = job_card.field_sources
    for field_name in update_data:
        field_sources[field_name] = "user_edit"
    job_card.field_sources_json = json.dumps(field_sources, ensure_ascii=False)
    job_card.status = "user_edited"

    session.add(job_card)
    session.commit()
    session.refresh(job_card)
    return job_card


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    session: Session = Depends(get_session),
) -> Response:
    job_card = session.get(JobCard, job_id)
    if not job_card:
        raise HTTPException(status_code=404, detail="Job card not found.")

    session.delete(job_card)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
