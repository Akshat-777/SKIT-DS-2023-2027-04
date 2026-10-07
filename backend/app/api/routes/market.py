from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.market.market_service import market_service
from app.services.market.scheduler import trigger_manual_market_refresh

router = APIRouter(tags=["Market Intelligence"])


@router.get(
    "/market/demand",
    summary="Get Job Market Demand Analytics and Trending Skills"
)
def get_market_demand(
    role: Optional[str] = Query(None, description="Target role (e.g. Software Engineer, Data Scientist)"),
    location: Optional[str] = Query(None, description="Location (e.g. Bengaluru, Remote, India)"),
    db: Session = Depends(get_db)
):
    """
    Returns top skill demand percentages and trends for a given role/location.
    Includes 'stale': true if serving cached/fallback data during third-party degradation.
    """
    try:
        data = market_service.get_market_demand(db, role=role, location=location)
        return data
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MARKET_DEMAND_ERROR", "message": f"Failed to compute market demand: {str(ex)}"}
        )


@router.get(
    "/market/jobs/similar",
    summary="Vector Search Top-K Similar Jobs for Resume"
)
def get_similar_jobs(
    resume_id: str = Query(..., description="Target resume ID"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top similar jobs to return"),
    db: Session = Depends(get_db)
):
    """
    Performs ChromaDB vector similarity search to find top matching job postings for a candidate resume.
    """
    try:
        result = market_service.get_similar_jobs(db, resume_id=resume_id, top_k=top_k)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESUME_NOT_FOUND", "message": str(ve)}
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "VECTOR_SEARCH_ERROR", "message": f"Failed to query similar jobs: {str(ex)}"}
        )


@router.post(
    "/admin/market/refresh",
    summary="Trigger Manual Refresh of Market Data Pipeline"
)
async def refresh_market_data(
    db: Session = Depends(get_db)
):
    """
    Manual trigger to pull job postings from job-board adapters, deduplicate,
    store structured data in PostgreSQL, and update ChromaDB vector collection.
    """
    try:
        stats = await trigger_manual_market_refresh(db=db)
        return {
            "message": "Market data ingestion pipeline executed successfully.",
            "stats": stats
        }
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INGESTION_FAILED", "message": f"Market ingestion failed: {str(ex)}"}
        )
