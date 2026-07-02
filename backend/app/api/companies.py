from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.schemas.companies import CompanyProfileEnrichRequest, CompanyProfileRead
from app.services.company_profiles import enrich_company_profile, list_company_profiles

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyProfileRead])
def list_companies(session: Session = Depends(get_session)) -> list[object]:
    return list_company_profiles(session)


@router.post("/enrich", response_model=CompanyProfileRead)
def enrich_company(
    payload: CompanyProfileEnrichRequest,
    session: Session = Depends(get_session),
) -> object:
    try:
        return enrich_company_profile(payload.company_name, session)
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
