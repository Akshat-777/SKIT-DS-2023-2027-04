from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Health Check")
async def health_check():
    """Returns operational status of the FastAPI backend."""
    return {"status": "ok"}
