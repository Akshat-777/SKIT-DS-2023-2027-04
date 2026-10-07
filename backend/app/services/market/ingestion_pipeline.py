import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.repositories import JobPostingRepository
from app.services.vector_store import vector_store_service
from app.services.embedding_client import embedding_client
from app.services.market.job_boards import (
    JobBoardClient, MockJobBoardClient, AdzunaJobBoardAdapter, LinkedInJobBoardAdapter, generate_job_dedup_hash
)

logger = logging.getLogger("careerlens.ingestion_pipeline")

DEFAULT_TARGET_ROLES = [
    "Software Engineer",
    "Data Scientist",
    "Full Stack Developer",
    "DevOps Engineer",
    "Data Analyst"
]


class MarketIngestionPipeline:
    """
    Market Data Ingestion Pipeline.
    Pulls job postings from adapters, handles pagination & rate limits,
    de-duplicates records, normalizes fields, and stores data in PostgreSQL & ChromaDB.
    """

    def __init__(self, adapters: Optional[List[JobBoardClient]] = None):
        if adapters is not None:
            self.adapters = adapters
        else:
            # Default sequence of adapters: Real Adzuna API, LinkedIn API (config-driven), and Mock fallback
            self.adapters = [
                AdzunaJobBoardAdapter(),
                LinkedInJobBoardAdapter(),
                MockJobBoardClient()
            ]
        self.last_run_stats: Dict[str, Any] = {
            "status": "idle",
            "last_run": None,
            "fetched": 0,
            "new": 0,
            "duplicates": 0,
            "failed": 0,
            "details": []
        }

    async def run_ingestion(self, db: Optional[Session] = None, roles: Optional[List[str]] = None) -> Dict[str, Any]:
        """Runs full market data ingestion and updates PostgreSQL + ChromaDB."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        target_roles = roles or DEFAULT_TARGET_ROLES
        stats = {
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "fetched": 0,
            "new": 0,
            "duplicates": 0,
            "failed": 0,
            "details": []
        }

        logger.info(f"Starting Market Ingestion Pipeline for roles: {target_roles}")

        try:
            seen_hashes_in_run = set()
            new_job_records = []
            
            for role in target_roles:
                role_fetched = 0
                role_new = 0
                role_dups = 0

                for adapter in self.adapters:
                    try:
                        raw_jobs = await adapter.fetch_jobs(role=role, limit=10)
                        role_fetched += len(raw_jobs)

                        for job in raw_jobs:
                            dedup_hash = job.get("dedup_hash") or generate_job_dedup_hash(
                                job["title"], job["company"], str(job["posted_at"])[:10]
                            )

                            # 1. In-memory run deduplication
                            if dedup_hash in seen_hashes_in_run:
                                role_dups += 1
                                continue
                            seen_hashes_in_run.add(dedup_hash)

                            # 2. PostgreSQL database deduplication
                            existing = JobPostingRepository.get_by_dedup_hash(db, dedup_hash)
                            if not existing and job.get("external_id"):
                                existing = JobPostingRepository.get_by_external_id(
                                    db, job["external_id"], job.get("source", "live_api")
                                )

                            if existing:
                                role_dups += 1
                                continue

                            # 3. Create record in PostgreSQL
                            posting = JobPostingRepository.create(
                                db=db,
                                title=job["title"],
                                company=job["company"],
                                target_role=job["target_role"],
                                skills=job["skills"],
                                location=job.get("location"),
                                experience=job.get("experience"),
                                salary_min=job.get("salary_min"),
                                salary_max=job.get("salary_max"),
                                currency=job.get("currency", "INR"),
                                unit=job.get("unit", "LPA"),
                                description=job.get("description"),
                                source=job.get("source", "live_api"),
                                external_id=job.get("external_id"),
                                dedup_hash=dedup_hash,
                                posted_at=job.get("posted_at")
                            )

                            new_job_records.append(posting)
                            role_new += 1

                    except Exception as adapter_err:
                        logger.error(f"Adapter {adapter.__class__.__name__} failed for role '{role}': {adapter_err}")
                        stats["failed"] += 1

                stats["fetched"] += role_fetched
                stats["new"] += role_new
                stats["duplicates"] += role_dups
                stats["details"].append({
                    "role": role,
                    "fetched": role_fetched,
                    "new": role_new,
                    "duplicates": role_dups
                })

            # 4. Batch Embed & Vector Store Ingestion into ChromaDB 'job_embeddings'
            if new_job_records:
                ids = [p.id for p in new_job_records]
                documents = [
                    f"Job Title: {p.title}. Role: {p.target_role}. Company: {p.company}. "
                    f"Location: {p.location or 'N/A'}. Required Skills: {', '.join(p.skills)}. "
                    f"Description: {p.description or ''}"
                    for p in new_job_records
                ]
                metadatas = [
                    {
                        "job_id": p.id,
                        "title": p.title,
                        "company": p.company,
                        "role": p.target_role,
                        "location": p.location or "",
                        "skills": ",".join(p.skills),
                        "posted_at": p.posted_at.isoformat() if p.posted_at else ""
                    }
                    for p in new_job_records
                ]

                # Compute vector embeddings & upsert into ChromaDB
                embeddings = embedding_client.get_embeddings_batch(documents)
                vector_store_service.upsert(
                    collection_name=vector_store_service.JOB_COLLECTION,
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings
                )
                logger.info(f"Successfully upserted {len(new_job_records)} new job embeddings into ChromaDB.")

            stats["status"] = "completed"
            stats["finished_at"] = datetime.now(timezone.utc).isoformat()
            self.last_run_stats = stats
            logger.info(f"Market Ingestion Pipeline completed: {stats['new']} new, {stats['duplicates']} duplicates, {stats['fetched']} total fetched.")
            return stats

        except Exception as pipeline_err:
            logger.error(f"Market Ingestion Pipeline failed: {pipeline_err}")
            stats["status"] = "failed"
            stats["error"] = str(pipeline_err)
            self.last_run_stats = stats
            return stats
        finally:
            if close_db and db:
                db.close()


ingestion_pipeline = MarketIngestionPipeline()
