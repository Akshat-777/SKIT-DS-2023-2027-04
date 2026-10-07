import pytest
import jwt
import io
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.repositories import UserRepository

client = TestClient(app)

def make_token(user_id: str, email: str = "test@example.com", name: str = "Test User") -> dict:
    """Generate a short-lived JWT and return auth headers."""
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


# ─── Test 1: User profile CRUD ──────────────────────────────────────────────

def test_user_me_get_and_update():
    """
    Proves: GET /users/me returns own profile.
             PUT /users/me updates name field.
    The first upload on behalf of user will auto-create the DB row pinned to the JWT sub.
    """
    db = SessionLocal()
    try:
        # Ensure the user exists in DB, seeded by seed_database()
        user = UserRepository.get_by_email(db, "akshat@example.com")
        assert user is not None, "Seed should have created akshat@example.com"
        user_id = user.id
    finally:
        db.close()

    headers = make_token(user_id, "akshat@example.com", "Akshat Agarwal")

    # GET /users/me – user exists and name is non-empty
    res = client.get("/api/v1/users/me", headers=headers)
    assert res.status_code == 200, res.json()
    original_name = res.json()["name"]
    assert isinstance(original_name, str) and len(original_name) > 0

    # PUT /users/me – name update works
    update_res = client.put("/api/v1/users/me", headers=headers, json={"name": "Akshat Agarwal (Lead)"})
    assert update_res.status_code == 200, update_res.json()
    assert update_res.json()["name"] == "Akshat Agarwal (Lead)"

    # Restore original name so state is consistent for other runs
    client.put("/api/v1/users/me", headers=headers, json={"name": original_name})



# ─── Test 2: Resume ownership isolation + soft & hard delete ─────────────────

def test_resume_ownership_isolation_and_delete():
    """
    Proves:
      - A user can upload and view their own resume.
      - Another user's token returns 403 Forbidden on the same resume.
      - Soft delete marks it deleted.
      - Hard delete purges the DB row and file.
    """
    headers1 = make_token("usr_owner_Alice", "alice@careerlens.test")
    headers2 = make_token("usr_owner_Bob",   "bob@careerlens.test")

    # Upload resume as Alice
    file_obj = io.BytesIO(b"%PDF-1.4 Mock resume content for Alice.")
    upload_res = client.post(
        "/api/v1/resumes/upload",
        headers=headers1,
        files={"file": ("alice_resume.pdf", file_obj, "application/pdf")}
    )
    assert upload_res.status_code == 202, upload_res.json()
    resume_id = upload_res.json()["resume_id"]

    # Alice can view her own resume
    status_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers1)
    assert status_res.status_code == 200, status_res.json()

    # Bob is FORBIDDEN
    forbidden_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers2)
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "FORBIDDEN"

    # Alice soft deletes
    soft_del = client.delete(f"/api/v1/resumes/{resume_id}", headers=headers1)
    assert soft_del.status_code == 200

    # Alice hard deletes
    hard_del = client.delete(f"/api/v1/resumes/{resume_id}/hard", headers=headers1)
    assert hard_del.status_code == 200

    # Resume truly gone
    gone_res = client.get(f"/api/v1/resumes/{resume_id}", headers=headers1)
    assert gone_res.status_code == 404


# ─── Test 3: Skills master CRUD ──────────────────────────────────────────────

def test_skills_crud():
    """Proves: create / list / get / delete on master skills table."""
    headers = make_token("usr_admin", "admin@careerlens.ai")

    # Create a brand-new skill
    create_res = client.post(
        "/api/v1/skills",
        headers=headers,
        json={"name": "GraphQL API Test", "category": "API Architectures", "aliases": ["gql-test"]}
    )
    assert create_res.status_code == 201, create_res.json()
    skill_id = create_res.json()["id"]

    # List with name filter
    list_res = client.get("/api/v1/skills?q=GraphQL+API+Test")
    assert list_res.status_code == 200
    assert list_res.json()["meta"]["total"] >= 1

    # Get by id
    get_res = client.get(f"/api/v1/skills/{skill_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "GraphQL API Test"

    # Delete
    del_res = client.delete(f"/api/v1/skills/{skill_id}", headers=headers)
    assert del_res.status_code == 200

    # Gone
    gone_res = client.get(f"/api/v1/skills/{skill_id}")
    assert gone_res.status_code == 404


# ─── Test 4: Job postings – filtering / sorting / pagination ─────────────────

def test_job_postings_filtering_sorting_pagination():
    """Proves: create / list (role filter, date sort, paginate) / update / delete on job_postings."""
    headers = make_token("usr_market_intel", "market@careerlens.ai")

    create_res = client.post(
        "/api/v1/job-postings",
        headers=headers,
        json={
            "title": "Lead FastAPI Data Engineer – CRUD Test",
            "company": "Jaipur Tech Labs",
            "target_role": "Full Stack Data Engineer",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "salary_min": 14.0,
            "salary_max": 22.0,
            "location": "Jaipur, RJ"
        }
    )
    assert create_res.status_code == 201, create_res.json()
    job_id = create_res.json()["id"]

    # Filtering by role
    list_res = client.get("/api/v1/job-postings?role=Full+Stack+Data+Engineer&sort_by=posted_at&order=desc&page=1&page_size=10")
    assert list_res.status_code == 200
    assert list_res.json()["meta"]["total"] >= 1
    assert "items" in list_res.json()

    # Update
    update_res = client.put(
        f"/api/v1/job-postings/{job_id}",
        headers=headers,
        json={"salary_max": 25.0}
    )
    assert update_res.status_code == 200
    assert update_res.json()["salary_max"] == 25.0

    # Delete
    del_res = client.delete(f"/api/v1/job-postings/{job_id}", headers=headers)
    assert del_res.status_code == 200


# ─── Test 5: Audit logs ───────────────────────────────────────────────────────

def test_audit_logs_are_returned():
    """Proves: audit logs are created automatically and listable via API."""
    headers = make_token("usr_audit_check", "audit@careerlens.test")

    # Trigger an upload which creates a RESUME_UPLOAD audit log
    file_obj = io.BytesIO(b"%PDF-1.4 Audit log test resume.")
    client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("audit_test.pdf", file_obj, "application/pdf")}
    )

    audit_res = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    data = audit_res.json()
    assert "items" in data
    # There should be at least the RESUME_UPLOAD log
    assert data["meta"]["total"] >= 1
