from pydantic import BaseModel, Field, ValidationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.services.role_profiles import generate_role_profile

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleProfileRequest(BaseModel):
    role_category: str = Field(min_length=1)


@router.post("/profile")
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
