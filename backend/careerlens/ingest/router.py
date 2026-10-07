from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import os
import asyncio
from typing import Dict, Any

from .validators import validate_file, MAX_FILE_SIZE_BYTES
from .extractor import process_resume

router = APIRouter(
    prefix="/ingest",
    tags=["Ingestion"]
)

STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'resumes'))
os.makedirs(STORAGE_DIR, exist_ok=True)

async def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    # Save file asynchronously
    with open(destination, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):
            buffer.write(chunk)

@router.post("/extract")
async def extract_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Ingest a PDF or DOCX file, validate it, extract text (using OCR if needed),
    and return the text along with extraction metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_FILE", "message": "No filename provided"}})
        
    # Generate safe filename and path
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}{file_ext}"
    file_path = os.path.join(STORAGE_DIR, safe_filename)
    
    try:
        # Save file to disk
        await save_upload_file(file, file_path)
        
        # Validate file (size, mime, extension)
        try:
            validate_file(file_path, file.filename)
        except ValueError as e:
            os.remove(file_path)  # Clean up invalid file
            raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": str(e)}})
            
        # Run extraction in a threadpool so it doesn't block the async loop
        result = await asyncio.to_thread(process_resume, file_path, file.filename, 'eng')
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail={"error": {"code": "PROCESSING_ERROR", "message": f"Failed to process file: {str(e)}"}})
