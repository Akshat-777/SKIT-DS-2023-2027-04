import io
import time
import warnings
from fastapi import status


def _make_minimal_pdf(text: str) -> bytes:
    """
    Build a real, parseable PDF containing the given resume text.
    Uses PyMuPDF (pymupdf/fitz) which is already a project dependency.
    """
    # Suppress the fitz→pymupdf deprecation warning in test output
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            import pymupdf as fitz  # type: ignore
        except ImportError:
            import fitz  # type: ignore  # older alias

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 50), text, fontsize=11, fontname="Helvetica")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return buf.read()


# Rich resume text used in the end-to-end test
_SAMPLE_RESUME_TEXT = """\
John Doe
john.doe@gmail.com | +91 98765 43210

SUMMARY
Passionate software engineer with 2 years of experience building scalable Python
and cloud-native backend services.

SKILLS
Python, FastAPI, Docker, PostgreSQL, Redis, AWS, Git, React, TypeScript, SQL

EDUCATION
B.Tech in Computer Science
Delhi Technological University  2020-2024

EXPERIENCE
Backend Software Engineer
Startup XYZ  |  June 2024 - Present
- Built REST APIs using FastAPI serving 50k+ daily active users
- Reduced latency by 40% by optimising PostgreSQL indexes
- Containerised 8 services with Docker, reducing deployment time by 3x
- Automated CI/CD pipelines cutting release cycle by 50%

PROJECTS
CareerMatch: Built a job-matching system using ChromaDB and LangChain with 1000+ users
"""

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_resume_unauthorized(client):
    file_data = ("resume.pdf", b"%PDF-1.4 Mock PDF content", "application/pdf")
    response = client.post("/api/v1/resumes/upload", files={"file": file_data})
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

def test_upload_resume_invalid_file_type(client, valid_auth_headers):
    file_data = ("resume.txt", b"Plain text content", "text/plain")
    response = client.post("/api/v1/resumes/upload", headers=valid_auth_headers, files={"file": file_data})
    assert response.status_code == 422
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "INVALID_FILE_TYPE"

def test_upload_and_fetch_end_to_end(client, valid_auth_headers):
    # 1. Upload a real minimal PDF that the NLP pipeline can parse
    pdf_bytes = _make_minimal_pdf(_SAMPLE_RESUME_TEXT)
    file_data = ("sample_resume.pdf", pdf_bytes, "application/pdf")
    upload_res = client.post("/api/v1/resumes/upload", headers=valid_auth_headers, files={"file": file_data})
    assert upload_res.status_code == 202
    data = upload_res.json()
    assert "resume_id" in data
    assert data["status"] in ["uploaded", "extracting", "parsing", "scoring", "ready"]
    resume_id = data["resume_id"]

    # Allow background task to complete
    time.sleep(1.6)

    # 2. Check Status
    status_res = client.get(f"/api/v1/resumes/{resume_id}", headers=valid_auth_headers)
    assert status_res.status_code == 200
    assert status_res.json()["resume_id"] == resume_id
    assert status_res.json()["status"] == "ready"

    # 3. Fetch Analysis (ParsedResume & ScoreResult)
    analysis_res = client.get(f"/api/v1/resumes/{resume_id}/analysis", headers=valid_auth_headers)
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    assert "parsed_resume" in analysis_data
    assert "score_result" in analysis_data
    assert analysis_data["parsed_resume"]["resume_id"] == resume_id
    # ATS score is computed dynamically from the real resume content; accept any reasonable value
    assert 1 <= analysis_data["score_result"]["ats_score"] <= 100
    assert "breakdown" in analysis_data["score_result"]
    assert "skill_gap" in analysis_data["score_result"]

    # 4. Fetch Market Fit
    market_res = client.get(f"/api/v1/resumes/{resume_id}/market-fit", headers=valid_auth_headers)
    assert market_res.status_code == 200
    market_data = market_res.json()
    assert market_data["resume_id"] == resume_id
    assert market_data["currency"] == "INR"
    assert market_data["unit"] == "LPA"
    # fit_score is derived from the real NLP output; accept any reasonable value
    assert 1 <= market_data["fit_score"] <= 100

    # 5. Fetch Roadmap
    roadmap_res = client.get(f"/api/v1/resumes/{resume_id}/roadmap", headers=valid_auth_headers)
    assert roadmap_res.status_code == 200
    roadmap_data = roadmap_res.json()
    assert roadmap_data["resume_id"] == resume_id
    assert len(roadmap_data["phases"]) > 0
    assert "linked_gap_skill" in roadmap_data["phases"][0]

    # 6. Fetch Critique
    critique_res = client.get(f"/api/v1/resumes/{resume_id}/critique", headers=valid_auth_headers)
    assert critique_res.status_code == 200
    critique_data = critique_res.json()
    assert critique_data["resume_id"] == resume_id
    assert len(critique_data["agents"]) > 0
    assert "merged" in critique_data
