"""
Acceptance Test Suite for ATS Scoring Service Integration (Aryan's Module)
Tests:
  1. Success: 200 OK + valid ScoreResult + DB persistence + X-Cache MISS
  2. Cache Hit: X-Cache HIT + latency < 300ms
  3. Timeout: Upstream timeout -> 504 Gateway Timeout + standard error format
  4. Malformed Response: Invalid schema from scoring service -> 502 Bad Gateway
  5. Invalid Role: Target role not in taxonomy -> 422 Unprocessable Entity
  6. Resume Status Check: Unready resume -> 409 Conflict; Failed resume -> 400
  7. Circuit Breaker: Tripping to OPEN after consecutive failures -> 502
"""

import time
import pytest
import httpx
from unittest.mock import patch, AsyncMock

from app.db.database import SessionLocal
from app.models.models import Resume, ParsedEntities, generate_id, utc_now
from app.services.cache_service import cache_service
from app.services.scoring_client import scoring_client


# Mock payload that conforms to Aryan's ScoreResult contract
MOCK_SCORE_RESULT_PAYLOAD = {
    "resume_id": "res_ready_test_1",
    "target_role": "Backend Developer",
    "ats_score": 88,
    "breakdown": {
        "keyword_match": 85.0,
        "semantic_similarity": 82.5,
        "section_completeness": 90.0,
        "formatting": 92.0,
        "experience_relevance": 88.0,
        "quantified_impact": 80.0
    },
    "skill_gap": {
        "matched": ["Python", "FastAPI", "PostgreSQL"],
        "missing": [
            {"skill": "Redis", "demand_pct": 78.5},
            {"skill": "Docker", "demand_pct": 82.0}
        ],
        "weak": ["Kubernetes"],
        "trending": ["RAG", "LangChain"]
    }
}


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Reset circuit breaker and caches before each test."""
    cache_service.clear()
    scoring_client.circuit_breaker.reset()
    yield
    cache_service.clear()
    scoring_client.circuit_breaker.reset()


@pytest.fixture
def seed_test_resumes():
    """Seeds test resumes in different states for user_test_123."""
    db = SessionLocal()
    try:
        # 1. Ready resume
        ready_resume = db.query(Resume).filter(Resume.id == "res_ready_test_1").first()
        if not ready_resume:
            ready_resume = Resume(
                id="res_ready_test_1",
                user_id="user_test_123",
                file_path="./uploads/ready_resume.pdf",
                file_name="ready_resume.pdf",
                file_type="pdf",
                status="ready",
                uploaded_at=utc_now(),
                updated_at=utc_now()
            )
            db.add(ready_resume)

        pe = db.query(ParsedEntities).filter(ParsedEntities.resume_id == "res_ready_test_1").first()
        if not pe:
            pe = ParsedEntities(
                id=generate_id("pe"),
                resume_id="res_ready_test_1",
                name="Jane Doe",
                email="jane.doe@example.com",
                education=[{"degree": "B.Tech in CSE", "institution": "SKIT Jaipur", "year": 2024}],
                experience=[{"title": "Backend Intern", "company": "Tech Labs", "start": "2023", "end": "2024", "bullets": ["Built FastAPI microservices."]}],
                skills=[{"name": "Python", "type": "explicit", "confidence": 0.95, "evidence": "Extracted via NER"}],
                sections={"skills": True, "education": True, "experience": True},
                raw_text="Jane Doe. Python, FastAPI, Docker, PostgreSQL. B.Tech in CSE from SKIT Jaipur.",
                created_at=utc_now()
            )
            db.add(pe)

        # 2. Parsing (unready) resume
        parsing_resume = db.query(Resume).filter(Resume.id == "res_parsing_test_2").first()
        if not parsing_resume:
            parsing_resume = Resume(
                id="res_parsing_test_2",
                user_id="user_test_123",
                file_path="./uploads/parsing_resume.pdf",
                file_name="parsing_resume.pdf",
                file_type="pdf",
                status="parsing",
                uploaded_at=utc_now(),
                updated_at=utc_now()
            )
            db.add(parsing_resume)

        # 3. Failed resume
        failed_resume = db.query(Resume).filter(Resume.id == "res_failed_test_3").first()
        if not failed_resume:
            failed_resume = Resume(
                id="res_failed_test_3",
                user_id="user_test_123",
                file_path="./uploads/failed_resume.pdf",
                file_name="failed_resume.pdf",
                file_type="pdf",
                status="failed",
                failed_step="extract/OCR",
                error_message="Image resolution too low for OCR engine.",
                uploaded_at=utc_now(),
                updated_at=utc_now()
            )
            db.add(failed_resume)

        db.commit()
    finally:
        db.close()


# ── 1. Success Scenario ────────────────────────────────────────────────────────

def test_analyze_resume_success(client, valid_auth_headers, seed_test_resumes):
    """
    Tests successful resume analysis:
      - Upstream scoring service returns 200 with valid ScoreResult
      - Returns 200 OK with correct ScoreResult JSON
      - Header X-Cache is MISS
      - Result is persisted in database and queryable via GET /resumes/{id}/analysis
    """
    mock_response = httpx.Response(
        status_code=200,
        json=MOCK_SCORE_RESULT_PAYLOAD,
        request=httpx.Request("POST", "http://localhost:8003/score")
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )

        assert response.status_code == 200
        assert response.headers["X-Cache"] == "MISS"
        assert "X-Response-Time-Ms" in response.headers

        data = response.json()
        assert data["resume_id"] == "res_ready_test_1"
        assert data["target_role"] == "Backend Developer"
        assert data["ats_score"] == 88
        assert data["breakdown"]["keyword_match"] == 85.0
        assert len(data["skill_gap"]["missing"]) == 2

        # Verify GET /resumes/{id}/analysis retrieves the stored analysis
        get_res = client.get("/api/v1/resumes/res_ready_test_1/analysis", headers=valid_auth_headers)
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["resume_id"] == "res_ready_test_1"
        assert get_data["ats_score"] == 88


# ── 2. Cache Hit Scenario ──────────────────────────────────────────────────────

def test_analyze_resume_cache_hit(client, valid_auth_headers, seed_test_resumes):
    """
    Tests warm-cache performance:
      - First call is MISS
      - Second identical call is HIT
      - Warm cache latency is well under 300 ms
      - Upstream HTTP client called only once
    """
    mock_response = httpx.Response(
        status_code=200,
        json=MOCK_SCORE_RESULT_PAYLOAD,
        request=httpx.Request("POST", "http://localhost:8003/score")
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # Call 1 (Warm up cache)
        res1 = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )
        assert res1.status_code == 200
        assert res1.headers["X-Cache"] == "MISS"
        assert mock_post.call_count == 1

        # Call 2 (Cache HIT)
        start_t = time.perf_counter()
        res2 = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )
        warm_latency_ms = (time.perf_counter() - start_t) * 1000

        assert res2.status_code == 200
        assert res2.headers["X-Cache"] == "HIT"
        # Upstream service must NOT be called again
        assert mock_post.call_count == 1
        # Warm cache must be well under 300 ms
        assert warm_latency_ms < 300.0


# ── 3. Timeout Scenario ────────────────────────────────────────────────────────

def test_analyze_resume_timeout(client, valid_auth_headers, seed_test_resumes):
    """
    Tests upstream scoring service timeout:
      - Scoring service times out across retries
      - Returns 504 Gateway Timeout
      - Error response format conforms strictly to {"error": {"code": str, "message": str}}
    """
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Upstream connection timed out")

        response = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )

        assert response.status_code == 504
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SCORING_SERVICE_TIMEOUT"
        assert "timed out" in data["error"]["message"].lower()


# ── 4. Malformed Response Scenario ─────────────────────────────────────────────

def test_analyze_resume_malformed_response(client, valid_auth_headers, seed_test_resumes):
    """
    Tests response schema validation rejection:
      - Upstream scoring service returns broken/incomplete ScoreResult
      - Pydantic validation rejects it
      - Returns 502 Bad Gateway
      - Error response conforms strictly to {"error": {"code": str, "message": str}}
    """
    malformed_payload = {
        "resume_id": "res_ready_test_1",
        "ats_score": "not_a_number",  # Invalid type
        # Missing target_role, breakdown, and skill_gap
    }
    mock_response = httpx.Response(
        status_code=200,
        json=malformed_payload,
        request=httpx.Request("POST", "http://localhost:8003/score")
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )

        assert response.status_code == 502
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SCORING_MALFORMED_RESPONSE"


# ── 5. Invalid Role Scenario ───────────────────────────────────────────────────

def test_analyze_resume_invalid_role(client, valid_auth_headers, seed_test_resumes):
    """
    Tests Role Taxonomy validation:
      - User submits a role that does not exist in taxonomy
      - Rejection occurs before calling scoring service
      - Returns 422 Unprocessable Entity
      - Error response conforms to {"error": {"code": str, "message": str}}
    """
    response = client.post(
        "/api/v1/resumes/res_ready_test_1/analyze",
        headers=valid_auth_headers,
        json={"target_role": "Underwater Basket Weaver"}
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_TARGET_ROLE"
    assert "does not exist in the role taxonomy" in data["error"]["message"]


# ── 6. Resume Status Checks ────────────────────────────────────────────────────

def test_analyze_resume_unready_status(client, valid_auth_headers, seed_test_resumes):
    """
    Tests resume status check:
      - Resume is still in 'parsing' state
      - Returns 409 Conflict
      - Error response explains that parsing is still in progress
    """
    response = client.post(
        "/api/v1/resumes/res_parsing_test_2/analyze",
        headers=valid_auth_headers,
        json={"target_role": "Backend Developer"}
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "RESUME_NOT_READY"


def test_analyze_resume_failed_status(client, valid_auth_headers, seed_test_resumes):
    """
    Tests resume status check on previously failed resume:
      - Returns 400 Bad Request
      - Error response provides failed_step and error message for user visibility
    """
    response = client.post(
        "/api/v1/resumes/res_failed_test_3/analyze",
        headers=valid_auth_headers,
        json={"target_role": "Backend Developer"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "RESUME_PARSE_FAILED"
    assert "extract/OCR" in data["error"]["message"]


# ── 7. Circuit Breaker Behavior ────────────────────────────────────────────────

def test_circuit_breaker_tripping(client, valid_auth_headers, seed_test_resumes):
    """
    Tests Circuit Breaker protection:
      - 3 consecutive failures trip the circuit breaker from CLOSED to OPEN
      - 4th call fast-fails immediately with 502 CIRCUIT_BREAKER_OPEN without calling upstream
    """
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused by upstream")

        # First 3 attempts trigger retries and fail
        for _ in range(3):
            res = client.post(
                "/api/v1/resumes/res_ready_test_1/analyze",
                headers=valid_auth_headers,
                json={"target_role": "Backend Developer"}
            )
            assert res.status_code == 502

        # 4th call: Circuit Breaker is now OPEN -> immediate fast-fail
        res_tripped = client.post(
            "/api/v1/resumes/res_ready_test_1/analyze",
            headers=valid_auth_headers,
            json={"target_role": "Backend Developer"}
        )
        assert res_tripped.status_code == 502
        data = res_tripped.json()
        assert data["error"]["code"] == "CIRCUIT_BREAKER_OPEN"
