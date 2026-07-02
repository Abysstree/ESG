from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import SearchProviderConfig
from app.schemas.search import (
    SearchProviderConfigCreate,
    SearchProviderConfigRead,
    SearchProviderConfigUpdate,
    SearchStatusRead,
)
from app.services.api_keys import encrypt_api_key
from app.services.search_configs import (
    activate_search_provider_config,
    create_search_provider_config,
    ensure_default_search_configs,
    get_active_search_provider_config,
    to_search_provider_config_read,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/status", response_model=SearchStatusRead)
def search_status(session: Session = Depends(get_session)) -> SearchStatusRead:
    active_config = get_active_search_provider_config(session)
    if active_config:
        return SearchStatusRead(
            provider=active_config.provider_type,
            configured=bool(active_config.api_key),
            base_url=active_config.base_url,
            active_provider_id=active_config.id,
        )

    return SearchStatusRead(
        provider="none",
        configured=False,
        base_url=None,
        active_provider_id=None,
    )


@router.get("/providers", response_model=list[SearchProviderConfigRead])
def list_search_provider_configs(
    session: Session = Depends(get_session),
) -> list[SearchProviderConfigRead]:
    ensure_default_search_configs(session)
    provider_priority = case(
        (SearchProviderConfig.provider_type == "exa", 0),
        (SearchProviderConfig.provider_type == "tavily", 1),
        else_=100,
    )
    statement = select(SearchProviderConfig).order_by(
        provider_priority,
        SearchProviderConfig.created_at.asc(),
    )
    return [
        to_search_provider_config_read(config)
        for config in session.scalars(statement)
    ]


@router.post("/providers", response_model=SearchProviderConfigRead)
def create_provider_config(
    payload: SearchProviderConfigCreate,
    session: Session = Depends(get_session),
) -> SearchProviderConfigRead:
    config = create_search_provider_config(payload, session)
    return to_search_provider_config_read(config)


@router.patch("/providers/{provider_id}", response_model=SearchProviderConfigRead)
def update_provider_config(
    provider_id: int,
    payload: SearchProviderConfigUpdate,
    session: Session = Depends(get_session),
) -> SearchProviderConfigRead:
    config = session.get(SearchProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search provider config not found.")

    update_data = payload.model_dump(exclude_unset=True)
    activate_after_update = bool(update_data.pop("is_active", False))
    if "api_key" in update_data:
        update_data["api_key"] = encrypt_api_key(update_data["api_key"])

    for field_name, value in update_data.items():
        setattr(config, field_name, value)

    session.add(config)
    session.commit()
    session.refresh(config)

    if activate_after_update:
        activated_config = activate_search_provider_config(config.id, session)
        if activated_config:
            config = activated_config

    return to_search_provider_config_read(config)


@router.post("/providers/{provider_id}/activate", response_model=SearchProviderConfigRead)
def activate_provider_config(
    provider_id: int,
    session: Session = Depends(get_session),
) -> SearchProviderConfigRead:
    config = activate_search_provider_config(provider_id, session)
    if not config:
        raise HTTPException(status_code=404, detail="Search provider config not found.")
    return to_search_provider_config_read(config)


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_config(
    provider_id: int,
    session: Session = Depends(get_session),
) -> Response:
    config = session.get(SearchProviderConfig, provider_id)
    if not config:
        raise HTTPException(status_code=404, detail="Search provider config not found.")

    session.delete(config)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
