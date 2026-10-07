import pytest
from app.db.database import SessionLocal
from app.models.models import Resume, User
from app.db.repositories import ResumeRepository, UserRepository

def test_admin_market_refresh_endpoint(client):
    """Verify POST /admin/market/refresh triggers ingestion pipeline successfully."""
    response = client.post("/admin/market/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "stats" in data
    assert data["stats"]["status"] == "completed"

def test_market_demand_endpoint(client):
    """Verify GET /market/demand returns role top skills, demand_pct, trend, and stale indicator."""
    response = client.get("/market/demand?role=Software%20Engineer")
    assert response.status_code == 200
    data = response.json()
    assert "target_role" in data
    assert "stale" in data
    assert "top_skills" in data
    assert isinstance(data["top_skills"], list)
    if data["top_skills"]:
        first = data["top_skills"][0]
        assert "skill" in first
        assert "demand_pct" in first
        assert "trend" in first

def test_market_jobs_similar_endpoint(client):
    """Verify GET /market/jobs/similar returns top-k similar jobs via vector search."""
    db = SessionLocal()
    try:
        # Create a test user & resume
        user = UserRepository.create(db, name="Market Test", email="markettest@example.com", password_hash="pass")
        resume = ResumeRepository.create(db, user_id=user.id, file_name="resume.pdf", file_type="pdf", file_path="./uploads/test.pdf")
        resume_id = resume.id
    finally:
        db.close()

    response = client.get(f"/market/jobs/similar?resume_id={resume_id}&top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert data["resume_id"] == resume_id
    assert "jobs" in data
    assert "stale" in data
    assert isinstance(data["jobs"], list)
    if data["jobs"]:
        first_job = data["jobs"][0]
        assert "job_id" in first_job
        assert "similarity_score" in first_job
        assert "match_percentage" in first_job

def test_graceful_degradation_stale_flag(client):
    """Verify GET /market/demand flags 'stale': true when fallback dataset is served."""
    response = client.get("/market/demand?role=NonExistentRole999")
    assert response.status_code == 200
    data = response.json()
    assert data["stale"] is True
    assert len(data["top_skills"]) > 0
