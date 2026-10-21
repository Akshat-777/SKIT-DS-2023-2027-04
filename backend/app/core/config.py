from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerLens API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security & JWT
    SECRET_KEY: str = "super-secret-careerlens-jwt-key-2026"
    ALGORITHM: str = "HS256"

    # Database & Storage
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/careerlens"
    STORAGE_PATH: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Upstream Services
    NLP_SERVICE_URL: str = "http://localhost:8001"
    EMBEDDING_SERVICE_URL: str = "http://localhost:8002"
    SCORING_SERVICE_URL: str = "http://localhost:8003"

    # Aryan's Scoring Service Client & Circuit Breaker Config
    SCORING_TIMEOUT_SEC: float = 4.5
    SCORING_RETRY_ATTEMPTS: int = 3
    SCORING_RETRY_BACKOFF_FACTOR: float = 0.5
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SEC: float = 30.0

    # Redis & Performance Caching
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600
    MARKET_DATA_VERSION: str = "2026.10"

    # Vector Store & Market Ingestion Configuration
    CHROMA_DB_DIR: str = "./chroma_db"
    JOB_BOARD_API_KEY: str = ""
    JOB_BOARD_APP_ID: str = ""
    JOB_BOARD_API_URL: str = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    LINKEDIN_ENABLED: bool = False
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""
    MARKET_REFRESH_INTERVAL_HOURS: int = 6

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

