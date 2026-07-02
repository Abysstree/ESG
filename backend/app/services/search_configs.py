from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SearchProviderConfig
from app.schemas.search import SearchProviderConfigCreate, SearchProviderConfigRead
from app.services.api_keys import encrypt_api_key, is_encrypted_api_key


DEFAULT_SEARCH_PROVIDER_CONFIGS = (
    {
        "name": "Exa",
        "provider_type": "exa",
        "base_url": "https://api.exa.ai",
    },
    {
        "name": "Tavily",
        "provider_type": "tavily",
        "base_url": "https://api.tavily.com",
    },
)


def ensure_default_search_configs(session: Session) -> None:
    existing_configs = list(session.scalars(select(SearchProviderConfig)))
    existing_names = {config.name for config in existing_configs}

    for config in DEFAULT_SEARCH_PROVIDER_CONFIGS:
        if config["name"] not in existing_names:
            session.add(SearchProviderConfig(**config, enabled=True, is_active=False))

    for config in existing_configs:
        if config.api_key and not is_encrypted_api_key(config.api_key):
            config.api_key = encrypt_api_key(config.api_key)
            session.add(config)

    session.commit()


def to_search_provider_config_read(
    config: SearchProviderConfig,
) -> SearchProviderConfigRead:
    return SearchProviderConfigRead(
        id=config.id,
        name=config.name,
        provider_type=config.provider_type,
        api_key_set=bool(config.api_key),
        base_url=config.base_url,
        enabled=config.enabled,
        is_active=config.is_active,
        created_at=config.created_at,
    )


def create_search_provider_config(
    payload: SearchProviderConfigCreate,
    session: Session,
) -> SearchProviderConfig:
    data = payload.model_dump()
    data["api_key"] = encrypt_api_key(data.get("api_key"))
    config = SearchProviderConfig(**data)
    session.add(config)
    session.commit()
    session.refresh(config)

    if config.is_active:
        activate_search_provider_config(config.id, session)
        session.refresh(config)

    return config


def activate_search_provider_config(
    provider_id: int,
    session: Session,
) -> SearchProviderConfig | None:
    config = session.get(SearchProviderConfig, provider_id)
    if not config:
        return None

    all_configs = list(session.scalars(select(SearchProviderConfig)))
    for item in all_configs:
        item.is_active = item.id == provider_id
        if item.id == provider_id:
            item.enabled = True
        session.add(item)

    session.commit()
    session.refresh(config)
    return config


def get_active_search_provider_config(
    session: Session,
) -> SearchProviderConfig | None:
    ensure_default_search_configs(session)
    return session.scalar(
        select(SearchProviderConfig).where(
            SearchProviderConfig.enabled.is_(True),
            SearchProviderConfig.is_active.is_(True),
        )
    )
