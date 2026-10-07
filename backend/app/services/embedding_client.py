import httpx
import logging
import time
import math
import hashlib
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger("careerlens.embedding_client")

# Optional sentence-transformers local fallback
try:
    from sentence_transformers import SentenceTransformer
    _LOCAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("Local SentenceTransformer fallback initialized successfully.")
except Exception as e:
    logger.info(f"SentenceTransformer local model fallback using deterministic vector generator.")
    _LOCAL_MODEL = None


def _deterministic_hash_vector(text: str, dim: int = 384) -> List[float]:
    """Generates a normalized deterministic vector for fallback when ML models are unavailable."""
    vector = []
    text_bytes = text.lower().strip().encode('utf-8')
    for i in range(dim):
        h = hashlib.sha256(text_bytes + str(i).encode('utf-8')).hexdigest()
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
        vector.append(val)
    # Normalize vector to unit length
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


class EmbeddingClient:
    """
    Embedding Client with HTTP connection to Aryan's embedding microservice,
    including fast timeout, fallback retry, and local deterministic fallback.
    """
    def __init__(self, base_url: Optional[str] = None, timeout: float = 1.0, max_retries: int = 1):
        self.base_url = (base_url or settings.EMBEDDING_SERVICE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def _fallback_embedding(self, text: str) -> List[float]:
        """Local fallback using SentenceTransformers or deterministic vector hashing."""
        if _LOCAL_MODEL is not None:
            try:
                emb = _LOCAL_MODEL.encode(text).tolist()
                return [float(x) for x in emb]
            except Exception as ex:
                logger.warning(f"Local SentenceTransformer encode failed: {ex}. Using hash fallback.")
        return _deterministic_hash_vector(text)

    def _fallback_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Local batch fallback using SentenceTransformers or deterministic vector hashing."""
        if _LOCAL_MODEL is not None:
            try:
                embs = _LOCAL_MODEL.encode(texts).tolist()
                return [[float(x) for x in emb] for emb in embs]
            except Exception as ex:
                logger.warning(f"Local SentenceTransformer batch encode failed: {ex}. Using hash fallback.")
        return [_deterministic_hash_vector(t) for t in texts]

    def get_embedding(self, text: str) -> List[float]:
        """Fetches embedding for a single text string."""
        url = f"{self.base_url}/embed"
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json={"text": text})
                    if resp.status_code == 200:
                        data = resp.json()
                        if "embedding" in data:
                            return data["embedding"]
            except Exception:
                pass
        
        return self._fallback_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Fetches embeddings for a list of text strings."""
        if not texts:
            return []
        
        url = f"{self.base_url}/embed/batch"
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json={"texts": texts})
                    if resp.status_code == 200:
                        data = resp.json()
                        if "embeddings" in data:
                            return data["embeddings"]
            except Exception:
                pass

        return self._fallback_embeddings_batch(texts)

embedding_client = EmbeddingClient()
