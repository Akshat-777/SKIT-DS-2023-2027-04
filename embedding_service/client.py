"""Synchronous backend client for the CareerLens embedding microservice."""

import time
from typing import Any

import requests


class EmbeddingClient:
    """Small requests-based client with retry/backoff for transient service failures."""

    def __init__(self, base_url: str = "http://embedding-service:8000", timeout: float = 10.0,
                 retries: int = 3, backoff_seconds: float = 0.25, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.session = session or requests.Session()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                return response.json()
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_error = exc
                status = getattr(getattr(exc, "response", None), "status_code", None)
                retryable = status is None or status == 429 or status >= 500
                if not retryable or attempt >= self.retries:
                    raise
                delay = self.backoff_seconds * (2 ** attempt)
                time.sleep(delay)
        raise RuntimeError("Embedding service retries exhausted") from last_error

    def embed_text(self, text: str) -> dict[str, Any]:
        return self._post("/embed", {"text": text})

    def embed_batch(self, texts: list[str]) -> dict[str, Any]:
        return self._post("/embed/batch", {"texts": texts})

    def embed_resume(self, parsed_resume: dict[str, Any]) -> dict[str, Any]:
        return self._post("/embed/resume", parsed_resume)

    def embed_job(self, job: dict[str, Any]) -> dict[str, Any]:
        return self._post("/embed/job", job)

    def similarity(self, text_a: str, text_b: str) -> dict[str, Any]:
        return self._post("/similarity", {"text_a": text_a, "text_b": text_b})
