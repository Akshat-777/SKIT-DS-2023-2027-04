import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.market.ingestion_pipeline import ingestion_pipeline

logger = logging.getLogger("careerlens.market_scheduler")

_scheduler: AsyncIOScheduler = None


async def scheduled_market_refresh():
    """Async background task executed by APScheduler every N hours."""
    logger.info("APScheduler executing scheduled market data refresh job...")
    try:
        stats = await ingestion_pipeline.run_ingestion()
        logger.info(f"Scheduled market data refresh finished: {stats.get('new')} new records created.")
    except Exception as ex:
        logger.error(f"Scheduled market data refresh failed: {ex}")


def start_market_scheduler():
    """Starts APScheduler background interval scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.warning("Market refresh scheduler is already running.")
        return

    interval_hours = getattr(settings, "MARKET_REFRESH_INTERVAL_HOURS", 6)
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        scheduled_market_refresh,
        trigger=IntervalTrigger(hours=interval_hours),
        id="market_refresh_job",
        replace_existing=True
    )
    _scheduler.start()
    logger.info(f"APScheduler market data refresh scheduler started (interval: every {interval_hours} hours).")


def stop_market_scheduler():
    """Stops the market refresh scheduler cleanly on app shutdown."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler market data refresh scheduler stopped.")


async def trigger_manual_market_refresh(db: Session = None):
    """Triggers an immediate manual market refresh execution."""
    logger.info("Manual market refresh triggered via admin endpoint.")
    return await ingestion_pipeline.run_ingestion(db=db)
