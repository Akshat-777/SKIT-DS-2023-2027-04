"""
CareerLens Scoring Service HTTP Client
Connects FastAPI backend to Aryan's ATS scoring and skill-gap service (POST /score).

Features:
  - Async HTTP client via httpx
  - Configurable timeouts
  - Exponential backoff retries with jitter
  - Circuit Breaker pattern (CLOSED -> OPEN -> HALF-OPEN)
  - Pydantic validation on ScoreResult response
  - Structured logging with Request-ID tracking
"""

import asyncio
import enum
import logging
import time
from typing import Dict, Any, Optional, Union
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.resume import ParsedResume, ScoreResult

logger = logging.getLogger("careerlens.scoring_client")


# ── Custom Exceptions ──────────────────────────────────────────────────────────

class ScoringClientError(Exception):
    """Base exception for scoring client errors."""
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ScoringTimeoutException(ScoringClientError):
    """Raised when the scoring service times out (maps to 504)."""
    def __init__(self, message: str = "Scoring service timed out while evaluating resume."):
        super().__init__(code="SCORING_SERVICE_TIMEOUT", message=message, status_code=504)


class ScoringServiceException(ScoringClientError):
    """Raised when scoring service is unreachable or returns a server error (maps to 502)."""
    def __init__(self, message: str = "Scoring service is currently unavailable."):
        super().__init__(code="SCORING_SERVICE_UNAVAILABLE", message=message, status_code=502)


class ScoringMalformedResponseException(ScoringClientError):
    """Raised when scoring service returns a response that violates ScoreResult contract (maps to 502)."""
    def __init__(self, message: str = "Scoring service returned an invalid response structure."):
        super().__init__(code="SCORING_MALFORMED_RESPONSE", message=message, status_code=502)


class CircuitBreakerOpenException(ScoringClientError):
    """Raised when the circuit breaker is OPEN, preventing cascading failures (maps to 502)."""
    def __init__(self, message: str = "Scoring service circuit breaker is OPEN. Upstream service is failing."):
        super().__init__(code="CIRCUIT_BREAKER_OPEN", message=message, status_code=502)


# ── Circuit Breaker Implementation ─────────────────────────────────────────────

class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Standard 3-state Circuit Breaker.
      - CLOSED: Normal operation. Errors increment failure count.
      - OPEN: Trips after N consecutive failures. Fast-fails requests without calling upstream.
      - HALF_OPEN: After recovery timeout, allows probe request. Success resets to CLOSED, failure trips to OPEN.
    """

    def __init__(
        self,
        failure_threshold: int = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout_sec: float = settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SEC,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        now = time.monotonic()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout_sec:
                logger.info("Circuit breaker transitioning from OPEN to HALF_OPEN (probing upstream).")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return True

    def record_success(self):
        if self.state != CircuitState.CLOSED:
            logger.info("Circuit breaker successfully recovered. Transitioning to CLOSED.")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker tripped to OPEN! (failures={self.failure_count}/{self.failure_threshold}, "
                f"recovery_timeout={self.recovery_timeout_sec}s)"
            )
            self.state = CircuitState.OPEN

    def reset(self):
        """Reset breaker to clean initial state (for testing)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0


# ── Scoring Service Client ─────────────────────────────────────────────────────

class ScoringClient:
    """
    Async client for Aryan's ATS scoring service.
    Exposes `score_resume(parsed_resume, target_role, request_id)` -> ScoreResult.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_sec: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self.base_url = (base_url or settings.SCORING_SERVICE_URL).rstrip("/")
        self.timeout_sec = timeout_sec or settings.SCORING_TIMEOUT_SEC
        self.max_retries = max_retries or settings.SCORING_RETRY_ATTEMPTS
        self.backoff_factor = backoff_factor or settings.SCORING_RETRY_BACKOFF_FACTOR
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def score_resume(
        self,
        parsed_resume: Union[ParsedResume, Dict[str, Any]],
        target_role: str,
        request_id: Optional[str] = None,
    ) -> ScoreResult:
        """
        Calls POST {base_url}/score with {parsed_resume, target_role}.
        Enforces circuit breaker, timeouts, backoff retries, and Pydantic validation.
        """
        # 1. Circuit Breaker pre-flight check
        if not self.circuit_breaker.can_execute():
            logger.error(
                f"[{request_id or 'internal'}] Upstream scoring call rejected: Circuit Breaker is OPEN."
            )
            raise CircuitBreakerOpenException(
                "Scoring service circuit breaker is OPEN due to repeated upstream failures. "
                "Please retry after upstream service recovers."
            )

        # 2. Prepare payload conforming to shared contract
        resume_dict = (
            parsed_resume.model_dump()
            if isinstance(parsed_resume, ParsedResume)
            else parsed_resume
        )
        payload = {
            "parsed_resume": resume_dict,
            "target_role": target_role,
        }

        endpoint_url = f"{self.base_url}/score"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if request_id:
            headers["X-Request-ID"] = request_id

        last_exception: Optional[Exception] = None

        # 3. Retries with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"[{request_id or 'internal'}] Calling scoring service attempt {attempt + 1}/{self.max_retries} "
                    f"at {endpoint_url} (timeout={self.timeout_sec}s)"
                )
                start_time = time.perf_counter()

                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    response = await client.post(endpoint_url, json=payload, headers=headers)

                elapsed_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"[{request_id or 'internal'}] Scoring service responded with HTTP {response.status_code} "
                    f"in {elapsed_ms:.1f}ms"
                )

                # Upstream error status code check
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}: {response.text}",
                        request=response.request,
                        response=response,
                    )
                elif response.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"Client error {response.status_code}: {response.text}",
                        request=response.request,
                        response=response,
                    )

                # Parse JSON response
                try:
                    data = response.json()
                except Exception as json_err:
                    self.circuit_breaker.record_failure()
                    raise ScoringMalformedResponseException(
                        f"Scoring service returned non-JSON response: {json_err}"
                    )

                # Validate with ScoreResult contract
                try:
                    score_result = ScoreResult.model_validate(data)
                except ValidationError as val_err:
                    self.circuit_breaker.record_failure()
                    logger.error(
                        f"[{request_id or 'internal'}] ScoreResult validation failed on upstream response: {val_err}"
                    )
                    raise ScoringMalformedResponseException(
                        f"Scoring service response rejected by contract validation: {val_err.errors()}"
                    )

                # Successful call -> record in circuit breaker
                self.circuit_breaker.record_success()
                return score_result

            except httpx.TimeoutException as te:
                last_exception = te
                logger.warning(
                    f"[{request_id or 'internal'}] Attempt {attempt + 1} timed out after {self.timeout_sec}s."
                )
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    raise ScoringTimeoutException(
                        f"Scoring service timed out after {self.max_retries} attempts ({self.timeout_sec}s limit)."
                    )

            except httpx.HTTPStatusError as hse:
                last_exception = hse
                logger.warning(
                    f"[{request_id or 'internal'}] Attempt {attempt + 1} received HTTP {hse.response.status_code}: {hse.response.text}"
                )
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    raise ScoringServiceException(
                        f"Scoring service returned error status {hse.response.status_code}."
                    )

            except (httpx.ConnectError, httpx.NetworkError) as ne:
                last_exception = ne
                logger.warning(
                    f"[{request_id or 'internal'}] Attempt {attempt + 1} network connection failed: {ne}"
                )
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    raise ScoringServiceException(
                        f"Unable to connect to scoring service at {self.base_url}: {ne}"
                    )

            except (ScoringMalformedResponseException, ScoringTimeoutException, ScoringServiceException):
                # Pre-formatted domain exceptions should propagate directly
                raise

            except Exception as e:
                last_exception = e
                logger.error(f"[{request_id or 'internal'}] Unexpected error contacting scoring service: {e}")
                if attempt == self.max_retries - 1:
                    self.circuit_breaker.record_failure()
                    raise ScoringServiceException(f"Scoring service invocation failed: {str(e)}")

            # Exponential backoff before next retry
            backoff_delay = self.backoff_factor * (2 ** attempt)
            logger.info(f"Retrying in {backoff_delay:.2f}s...")
            await asyncio.sleep(backoff_delay)

        # Fallback if loop ends unexpectedly
        self.circuit_breaker.record_failure()
        raise ScoringServiceException(f"Scoring service failed: {last_exception}")


# Global default instance
scoring_client = ScoringClient()
