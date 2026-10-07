import pytest
import asyncio
from app.db.database import SessionLocal
from app.db.repositories import JobPostingRepository
from app.services.market.job_boards import MockJobBoardClient, LinkedInJobBoardAdapter
from app.services.market.ingestion_pipeline import MarketIngestionPipeline, ingestion_pipeline

@pytest.mark.asyncio
async def test_mock_job_board_adapter():
    """Verify MockJobBoardClient returns realistic job postings."""
    client = MockJobBoardClient()
    jobs = await client.fetch_jobs(role="Software Engineer", limit=5)
    assert len(jobs) > 0
    first = jobs[0]
    assert "title" in first
    assert "company" in first
    assert "skills" in first
    assert "dedup_hash" in first
    assert first["target_role"] == "Software Engineer"

@pytest.mark.asyncio
async def test_linkedin_adapter_graceful_skip():
    """Verify LinkedInJobBoardAdapter skips gracefully without throwing an exception when disabled."""
    adapter = LinkedInJobBoardAdapter()
    jobs = await adapter.fetch_jobs(role="Software Engineer")
    assert isinstance(jobs, list)
    assert len(jobs) == 0

@pytest.mark.asyncio
async def test_market_ingestion_pipeline():
    """Verify ingestion pipeline deduplication, DB insertion, and vector store indexing."""
    db = SessionLocal()
    try:
        pipeline = MarketIngestionPipeline(adapters=[MockJobBoardClient()])
        stats = await pipeline.run_ingestion(db=db, roles=["Software Engineer", "Data Scientist"])
        
        assert stats["status"] == "completed"
        assert stats["fetched"] > 0
        assert stats["new"] >= 0
        assert "duplicates" in stats

        # Re-run pipeline to verify deduplication
        stats_rerun = await pipeline.run_ingestion(db=db, roles=["Software Engineer"])
        assert stats_rerun["duplicates"] > 0
        assert stats_rerun["new"] == 0

        # Query database to confirm stored records
        postings, total = JobPostingRepository.list_job_postings(db, role="Software Engineer")
        assert total > 0
        assert postings[0].title is not None
        assert isinstance(postings[0].skills, list)
    finally:
        db.close()
