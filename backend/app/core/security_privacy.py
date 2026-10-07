import os
import base64
import logging
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger("careerlens.security")

# Derive a consistent 32-byte URL-safe base64 key for Fernet from SECRET_KEY
def _get_fernet_key() -> bytes:
    key_src = (settings.SECRET_KEY * 4)[:32].encode("utf-8")
    return base64.urlsafe_b64encode(key_src)

fernet = Fernet(_get_fernet_key())

def encrypt_pii(data: str) -> str:
    """Encrypt sensitive PII string using application-level Fernet symmetric encryption."""
    if not data:
        return data
    try:
        return fernet.encrypt(data.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encrypting PII: {e}")
        return data

def decrypt_pii(token: str) -> str:
    """Decrypt sensitive PII string."""
    if not token:
        return token
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        # If string is not encrypted (plain text during dev), return as-is
        return token
