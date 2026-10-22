"""
CareerLens In-Process Automated Benchmark Runner
Simulates cold and warm requests against POST /api/v1/resumes/{id}/analyze
Measures latencies, p50, p95, p99, and cache hit ratios.
"""

import time
import jwt
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.db.seed import seed_database
from app.models.models import Resume, ParsedEntities, generate_id, utc_now
from app.services.cache_service import cache_service

SECRET_KEY = "super-secret-careerlens-jwt-key-2026"
ALGORITHM = "HS256"

def setup_benchmark_data():
    Base.metadata.create_all(bind=engine)
    seed_database()
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == "res_bench_test").first()
        if not resume:
            resume = Resume(
                id="res_bench_test",
                user_id="user_bench_123",
                file_path="./uploads/bench_resume.pdf",
                file_name="bench_resume.pdf",
                file_type="pdf",
                status="ready",
                uploaded_at=utc_now(),
                updated_at=utc_now()
            )
            db.add(resume)

        pe = db.query(ParsedEntities).filter(ParsedEntities.resume_id == "res_bench_test").first()
        if not pe:
            pe = ParsedEntities(
                id=generate_id("pe"),
                resume_id="res_bench_test",
                name="Benchmark Candidate",
                email="bench@careerlens.ai",
                education=[{"degree": "B.Tech in CSE", "institution": "SKIT Jaipur", "year": 2024}],
                experience=[{"title": "Backend Engineer", "company": "Tech Corp", "start": "2023", "end": "2024", "bullets": ["Built Python FastAPI services."]}],
                skills=[{"name": "Python", "type": "explicit", "confidence": 0.95, "evidence": "Resume skills section"}],
                sections={"skills": True, "education": True, "experience": True},
                raw_text="Benchmark Candidate. Python, FastAPI, Docker, PostgreSQL. B.Tech in CSE from SKIT Jaipur.",
                created_at=utc_now()
            )
            db.add(pe)
        db.commit()
    finally:
        db.close()


def generate_jwt_token(user_id: str = "user_bench_123") -> str:
    payload = {
        "sub": user_id,
        "email": "bench@careerlens.ai",
        "name": "Benchmark Candidate",
        "role": "user"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def run_benchmark():
    setup_benchmark_data()
    cache_service.clear()

    mock_score = {
        "resume_id": "res_bench_test",
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
            "missing": [{"skill": "Redis", "demand_pct": 78.5}],
            "weak": ["Kubernetes"],
            "trending": ["RAG"]
        }
    }
    mock_resp = httpx.Response(200, json=mock_score, request=httpx.Request("POST", "http://localhost:8003/score"))

    with TestClient(app) as client:
        auth_header = {"Authorization": f"Bearer {generate_jwt_token()}"}
        resume_id = "res_bench_test"

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            print("=" * 70)
            print("CAREERLENS ATS SCORING - AUTOMATED BENCHMARK / LOAD RESULTS")
            print("=" * 70)

            # Cold request (Cache MISS)
            print("\n[Phase 1] Cold Scoring Request (Cache MISS)...")
            t0 = time.perf_counter()
            cold_res = client.post(
                f"/api/v1/resumes/{resume_id}/analyze",
                json={"target_role": "Backend Developer"},
                headers=auth_header
            )
            cold_ms = (time.perf_counter() - t0) * 1000
            print(f"  HTTP Status Code : {cold_res.status_code}")
            print(f"  X-Cache Header   : {cold_res.headers.get('X-Cache')}")
            print(f"  Reported Latency : {cold_res.headers.get('X-Response-Time-Ms')} ms")
            print(f"  Measured Latency : {cold_ms:.2f} ms (Target: < 5000 ms) -> {'PASS' if cold_ms < 5000 else 'FAIL'}")

            # Warm requests (50 iterations of Cache HIT)
            print("\n[Phase 2] Warm Cache Benchmark (50 iterations)...")
            latencies = []
            for i in range(50):
                t_start = time.perf_counter()
                r = client.post(
                    f"/api/v1/resumes/{resume_id}/analyze",
                    json={"target_role": "Backend Developer"},
                    headers=auth_header
                )
                lat = (time.perf_counter() - t_start) * 1000
                latencies.append(lat)
                assert r.status_code == 200
                assert r.headers.get("X-Cache") == "HIT"

            avg_lat = sum(latencies) / len(latencies)
            p50 = sorted(latencies)[int(len(latencies) * 0.5)]
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]

            print(f"  Total Requests   : {len(latencies)}")
            print(f"  Cache Hit Ratio  : 100.0%")
            print(f"  Average Latency  : {avg_lat:.2f} ms")
            print(f"  p50 Latency      : {p50:.2f} ms")
            print(f"  p95 Latency      : {p95:.2f} ms (Target: < 300 ms) -> {'PASS' if p95 < 300 else 'FAIL'}")
            print(f"  p99 Latency      : {p99:.2f} ms")
            print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
