"""Environment-backed service configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    model_name: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    device: str = os.getenv("EMBEDDING_DEVICE", "auto").lower()
    max_batch_size: int = int(os.getenv("EMBEDDING_MAX_BATCH_SIZE", "64"))
    encoder_batch_size: int = int(os.getenv("EMBEDDING_ENCODER_BATCH_SIZE", "32"))
    cpu_threads: int = int(os.getenv("EMBEDDING_CPU_THREADS", "2"))
    cache_size: int = int(os.getenv("EMBEDDING_CACHE_SIZE", "2048"))
    chunk_overlap: int = int(os.getenv("EMBEDDING_CHUNK_OVERLAP", "32"))
    hf_home: str | None = os.getenv("HF_HOME")

    def __post_init__(self):
        if self.max_batch_size < 1:
            raise ValueError("EMBEDDING_MAX_BATCH_SIZE must be at least 1")
        if self.encoder_batch_size < 1:
            raise ValueError("EMBEDDING_ENCODER_BATCH_SIZE must be at least 1")
        if self.cpu_threads < 1:
            raise ValueError("EMBEDDING_CPU_THREADS must be at least 1")
        if self.cache_size < 0:
            raise ValueError("EMBEDDING_CACHE_SIZE cannot be negative")
        if self.chunk_overlap < 0:
            raise ValueError("EMBEDDING_CHUNK_OVERLAP cannot be negative")
        if self.device not in ("auto", "cpu", "cuda", "mps"):
            raise ValueError("EMBEDDING_DEVICE must be auto, cpu, cuda, or mps")


settings = Settings()
