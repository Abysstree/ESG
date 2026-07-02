from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LLMProviderConfig
from app.schemas.llm import LLMProviderConfigCreate, LLMProviderConfigRead
from app.services.api_keys import encrypt_api_key, is_encrypted_api_key


DEFAULT_PROVIDER_CONFIGS = (
    {
        "name": "DeepSeek",
        "provider_type": "deepseek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-v4-flash",
    },
    {
        "name": "OpenAI",
        "provider_type": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
    },
    {
        "name": "Anthropic",
        "provider_type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "model": "claude-sonnet-4-6",
    },
    {
        "name": "Google Gemini",
        "provider_type": "google",
        "base_url": "https://generativelanguage.googleapis.com",
        "model": "gemini-3.5-flash",
    },
    {
        "name": "自定义 OpenAI 兼容",
        "provider_type": "openai_compatible",
        "base_url": "",
        "model": "",
    },
)


def ensure_default_llm_configs(session: Session) -> None:
    existing_configs = list(session.scalars(select(LLMProviderConfig)))
    existing_names = {config.name for config in existing_configs}

    for config in DEFAULT_PROVIDER_CONFIGS:
        if config["name"] not in existing_names:
            session.add(LLMProviderConfig(**config, enabled=True, is_active=False))

    for config in existing_configs:
        if config.api_key and not is_encrypted_api_key(config.api_key):
            config.api_key = encrypt_api_key(config.api_key)
            session.add(config)

    session.commit()


def to_llm_provider_config_read(
    config: LLMProviderConfig,
) -> LLMProviderConfigRead:
    return LLMProviderConfigRead(
        id=config.id,
        name=config.name,
        provider_type=config.provider_type,
        api_key_set=bool(config.api_key),
        base_url=config.base_url,
        model=config.model,
        enabled=config.enabled,
        is_active=config.is_active,
        created_at=config.created_at,
    )


def create_llm_provider_config(
    payload: LLMProviderConfigCreate,
    session: Session,
) -> LLMProviderConfig:
    data = payload.model_dump()
    data["api_key"] = encrypt_api_key(data.get("api_key"))
    config = LLMProviderConfig(**data)
    session.add(config)
    session.commit()
    session.refresh(config)

    if config.is_active:
        activate_llm_provider_config(config.id, session)
        session.refresh(config)

    return config


def activate_llm_provider_config(
    provider_id: int,
    session: Session,
) -> LLMProviderConfig | None:
    config = session.get(LLMProviderConfig, provider_id)
    if not config:
        return None

    all_configs = list(session.scalars(select(LLMProviderConfig)))
    for item in all_configs:
        item.is_active = item.id == provider_id
        if item.id == provider_id:
            item.enabled = True
        session.add(item)

    session.commit()
    session.refresh(config)
    return config


def get_active_llm_provider_config(session: Session) -> LLMProviderConfig | None:
    ensure_default_llm_configs(session)
    return session.scalar(
        select(LLMProviderConfig).where(
            LLMProviderConfig.enabled.is_(True),
            LLMProviderConfig.is_active.is_(True),
        )
    )
