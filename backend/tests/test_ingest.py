import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import os
import shutil
from careerlens.ingest.router import router, STORAGE_DIR

app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup
    os.makedirs(STORAGE_DIR, exist_ok=True)
    yield
    # Teardown: we don't necessarily delete the folder, but we could clean it up
    # for test isolation if needed.

# Note: In a real test suite, you'd provide actual test files (PDF, DOCX)
# For the purpose of this assignment, we will simulate the file upload
# and test the validation logic and the API endpoint structure.

def test_no_file():
    response = client.post("/ingest/extract")
    assert response.status_code == 422 # FastAPI validation error for missing body

def test_invalid_extension():
    # Create a dummy text file
    test_file_path = "dummy.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test.")
    
    with open(test_file_path, "rb") as f:
        response = client.post("/ingest/extract", files={"file": ("dummy.txt", f, "text/plain")})
        
    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"
    assert "Unsupported file extension" in response.json()["detail"]["error"]["message"]
    
    os.remove(test_file_path)

def test_file_too_large(monkeypatch):
    from careerlens.ingest import validators
    monkeypatch.setattr(validators, "MAX_FILE_SIZE_BYTES", 10) # 10 bytes limit
    
    test_file_path = "dummy.pdf"
    with open(test_file_path, "w") as f:
        f.write("This is a dummy PDF file that is larger than 10 bytes.")
        
    with open(test_file_path, "rb") as f:
        response = client.post("/ingest/extract", files={"file": ("dummy.pdf", f, "application/pdf")})
        
    assert response.status_code == 400
    assert "exceeds limit of" in response.json()["detail"]["error"]["message"]
    
    os.remove(test_file_path)
