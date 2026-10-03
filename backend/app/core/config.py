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

    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
