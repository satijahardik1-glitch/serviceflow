"""Field-level encryption (Fernet / AES-128-CBC + HMAC) for sensitive values such as ID numbers."""
import base64
import hashlib
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

TOKEN_PREFIX = "gAAAA"  # every Fernet token starts with this


@lru_cache
def _fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.strip()
    if not key:  # development/test convenience only - production requires ENCRYPTION_KEY
        key = base64.urlsafe_b64encode(hashlib.sha256(("sf-enc:" + settings.SECRET_KEY).encode()).digest()).decode()
    return Fernet(key.encode())


def encrypt(value: Optional[str]) -> Optional[str]:
    return _fernet().encrypt(value.encode()).decode() if value else None


def decrypt(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if not value.startswith(TOKEN_PREFIX):  # legacy plaintext
        return value
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None


def mask(value: Optional[str]) -> Optional[str]:
    plain = decrypt(value)
    return f"•••• {plain[-4:]}" if plain else None
