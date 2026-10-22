import httpx
import logging
import time
import math
import hashlib
import os
import threading
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger("careerlens.embedding_client")

# Optional local model fallback. Load only if the embedding API is unavailable and
# only on first use; importing the backend should not download a model or block
# startup. Keep this model PyTorch-only because Transformers may otherwise probe
# an optional TensorFlow installation that is broken on some Windows machines.
_LOCAL_MODEL = None
_LOCAL_MODEL_CHECKED = False
_LOCAL_MODEL_LOCK = threading.Lock()


def _get_local_model():
    global _LOCAL_MODEL, _LOCAL_MODEL_CHECKED
    if _LOCAL_MODEL_CHECKED:
        return _LOCAL_MODEL
    with _LOCAL_MODEL_LOCK:
        if _LOCAL_MODEL_CHECKED:
            return _LOCAL_MODEL
        try:
            os.environ.setdefault("USE_TF", "0")
            os.environ.setdefault("USE_FLAX", "0")
            from sentence_transformers import SentenceTransformer

            _LOCAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Local SentenceTransformer fallback initialized on demand.")
        except Exception as exc:
            logger.info("Local model fallback unavailable; using deterministic vectors: %s", exc)
        finally:
            _LOCAL_MODEL_CHECKED = True
    return _LOCAL_MODEL


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
        local_model = _get_local_model()
        if local_model is not None:
            try:
                emb = local_model.encode(text).tolist()
                return [float(x) for x in emb]
            except Exception as ex:
                logger.warning(f"Local SentenceTransformer encode failed: {ex}. Using hash fallback.")
        return _deterministic_hash_vector(text)

    def _fallback_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Local batch fallback using SentenceTransformers or deterministic vector hashing."""
        local_model = _get_local_model()
        if local_model is not None:
            try:
                embs = local_model.encode(texts).tolist()
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
                        vectors = data.get("vectors") or data.get("embeddings")
                        if vectors and isinstance(vectors, list):
                            return vectors[0] if isinstance(vectors[0], list) else vectors[0].get("embedding", [])
                        if "embedding" in data:
                            return data["embedding"]
            except Exception:
                pass
        
        return self._fallback_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Fetches embeddings for a list of text strings."""
        if not texts:
            return []
        
        vectors = self.get_service_embeddings_batch(texts)
        if vectors is not None:
            return vectors

        return self._fallback_embeddings_batch(texts)

    def get_service_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Return vectors only from the embedding service, or None when it is offline.

        ATS scoring uses this method so deterministic offline vectors are never
        mistaken for real semantic similarity.
        """
        if not texts:
            return []
        url = f"{self.base_url}/embed/batch"
        for _attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json={"texts": texts})
                    if response.status_code == 200:
                        data = response.json()
                        vectors = data.get("vectors") or data.get("embeddings")
                        if (isinstance(vectors, list) and len(vectors) == len(texts)
                                and all(isinstance(vector, list) and vector for vector in vectors)):
                            return vectors
            except Exception as exc:
                logger.debug("Embedding service batch request failed: %s", exc)
        return None

embedding_client = EmbeddingClient()
