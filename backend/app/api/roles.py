from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import RoleCategoryProfile
from app.schemas.roles import RoleProfileRead, RoleProfileRequest, RoleProfileResult
from app.services.role_profiles import generate_role_profile, list_role_profiles

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/profiles", response_model=list[RoleProfileRead])
def get_role_profiles(
    session: Session = Depends(get_session),
) -> list[RoleCategoryProfile]:
    return list_role_profiles(session)


@router.post("/profile", response_model=RoleProfileResult)
def create_role_profile(
    payload: RoleProfileRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    try:
        return generate_role_profile(payload.role_category.strip(), session)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (RuntimeError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
