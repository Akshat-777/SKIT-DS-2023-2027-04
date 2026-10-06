from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel

from careerlens.nlp.cleaner import clean_text_pipeline
from careerlens.nlp.ner import extract_entities, load_ner_pipeline

router = APIRouter(
    prefix="/nlp",
    tags=["NLP Resume Parsing"]
)

class ParseRequest(BaseModel):
    text: str
    resume_id: Optional[str] = None

@router.on_event("startup")
async def startup_event():
    """Warm up and cache the NER model pipeline at server startup."""
    print("[CareerLens NLP] Pre-loading NER model pipeline...")
    load_ner_pipeline()

@router.post("/parse")
async def parse_resume_text(payload: ParseRequest) -> Dict[str, Any]:
    """
    POST /nlp/parse
    Accepts raw resume text, cleans & normalizes it, extracts BIO entities,
    and returns a ParsedResume-compliant JSON payload.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_INPUT", "message": "Text field cannot be empty."}}
        )

    try:
        # Step 1: Clean text pipeline
        cleaning_result = clean_text_pipeline(payload.text)
        clean_text = cleaning_result["clean_text"]

        # Step 2: Extract NER entities & format JSON contract
        parsed_resume = extract_entities(clean_text, resume_id=payload.resume_id)
        
        return parsed_resume

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "NLP_PARSE_ERROR", "message": f"Failed to parse resume NLP: {str(e)}"}}
        )
