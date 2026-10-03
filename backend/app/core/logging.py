import logging
import uuid
import re
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

# Setup structured logger
logger = logging.getLogger("careerlens")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [ReqID: %(request_id)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# PII Sanitizer regex patterns (Email, Phone)
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')

def sanitize_pii(message: str) -> str:
    """Masks PII like email and phone numbers in logs to satisfy NFR-004."""
    sanitized = EMAIL_PATTERN.sub('[EMAIL_REDACTED]', message)
    sanitized = PHONE_PATTERN.sub('[PHONE_REDACTED]', sanitized)
    return sanitized

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID header to requests and responses for distributed tracing."""
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
