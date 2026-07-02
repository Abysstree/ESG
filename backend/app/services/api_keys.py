from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.db.database import DATA_DIR


ENCRYPTED_PREFIX = "enc:v1:"
KEY_FILE = DATA_DIR / "secrets" / "api-key-fernet.key"


def encrypt_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if api_key.startswith(ENCRYPTED_PREFIX):
        return api_key

    encrypted = _cipher().encrypt(api_key.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{encrypted}"


def decrypt_api_key(value: str | None) -> str | None:
    if not value:
        return None
    if not value.startswith(ENCRYPTED_PREFIX):
        return value

    encrypted_value = value.removeprefix(ENCRYPTED_PREFIX)
    try:
        return _cipher().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Stored API key cannot be decrypted. Check ESG_API_KEY_ENCRYPTION_KEY "
            "or data/secrets/api-key-fernet.key."
        ) from exc


def is_encrypted_api_key(value: str | None) -> bool:
    return bool(value and value.startswith(ENCRYPTED_PREFIX))


def _cipher() -> Fernet:
    key = _load_or_create_key()
    return Fernet(key)


def _load_or_create_key() -> bytes:
    env_key = _read_env_key()
    if env_key:
        return env_key

    if KEY_FILE.exists():
        return KEY_FILE.read_bytes().strip()

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    return key


def _read_env_key() -> bytes | None:
    import os

    value = os.getenv("ESG_API_KEY_ENCRYPTION_KEY")
    if not value:
        return None
    return value.encode("utf-8")
