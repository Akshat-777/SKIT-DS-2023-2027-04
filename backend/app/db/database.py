from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger("careerlens.db")

DATABASE_URL = settings.DATABASE_URL

def get_engine():
    """Initializes database engine with automatic SQLite file fallback if PostgreSQL is unavailable."""
    if DATABASE_URL.startswith("postgresql"):
        try:
            test_engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
            # Test actual connection
            with test_engine.connect() as conn:
                pass
            return test_engine
        except Exception as e:
            logger.warning(f"Failed to connect to primary DB ({DATABASE_URL}), using SQLite file fallback: {str(e)}")
            fallback_url = "sqlite:///./careerlens_dev.db"
            return create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True
            )
    else:
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        return create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
