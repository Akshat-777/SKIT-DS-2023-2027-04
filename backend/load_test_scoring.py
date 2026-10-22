"""
CareerLens Load Testing Script for ATS Scoring & Analysis Pipeline
Framework: Locust
Target: POST /api/v1/resumes/{id}/analyze & GET /api/v1/resumes/{id}/analysis

Performance Targets:
  - Cold End-to-End Scoring: < 5000 ms
  - Warm Cache Hit Scoring: < 300 ms
  - Error Rate: 0.0% under normal load

Run with:
  locust -f load_test_scoring.py --headless -u 10 -r 2 --run-time 15s --host http://localhost:8000
"""

import jwt
import random
import time
from locust import HttpUser, task, between

SECRET_KEY = "super-secret-careerlens-jwt-key-2026"
ALGORITHM = "HS256"

ROLES = [
    "Backend Developer",
    "Data Scientist",
    "Full Stack Developer",
    "ML Engineer",
    "DevOps Engineer"
]

def generate_jwt_token(user_id: str = "user_test_123") -> str:
    payload = {
        "sub": user_id,
        "email": "testuser@example.com",
        "name": "Load Test Candidate",
        "role": "user"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class CareerLensScoringUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Prepares authorization header and test resume."""
        self.token = generate_jwt_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.resume_id = "res_ready_test_1"

    @task(3)
    def analyze_resume_cache_hit(self):
        """Simulates warm cache hit request (target: < 300ms)."""
        target_role = "Backend Developer"
        start_time = time.perf_counter()
        with self.client.post(
            f"/api/v1/resumes/{self.resume_id}/analyze",
            json={"target_role": target_role},
            headers=self.headers,
            catch_response=True,
            name="/api/v1/resumes/[id]/analyze [cache-hit]"
        ) as response:
            latency_ms = (time.perf_counter() - start_time) * 1000
            if response.status_code == 200:
                cache_header = response.headers.get("X-Cache", "")
                if cache_header == "HIT" and latency_ms > 300:
                    response.failure(f"Cache hit latency exceeded 300ms target ({latency_ms:.1f}ms)")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")

    @task(1)
    def get_latest_analysis(self):
        """Fetches the latest stored analysis result."""
        with self.client.get(
            f"/api/v1/resumes/{self.resume_id}/analysis",
            headers=self.headers,
            catch_response=True,
            name="/api/v1/resumes/[id]/analysis"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")
