import jwt
from jwt.exceptions import InvalidTokenError
from typing import Optional, Dict, Any
from app.core.config import settings

class JWTError(Exception):
    """Custom JWT error exception."""
    pass

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verifies the JWT token issued by auth-service using the shared secret.
    Returns the decoded token payload.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except InvalidTokenError as e:
        raise JWTError(f"Invalid or expired token: {str(e)}")
