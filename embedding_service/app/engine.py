"""Sentence-transformer engine with token chunking, LRU caching, and metrics."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import Settings, settings


@dataclass
class Timing:
    duration_ms: float
    text_count: int


class EmbeddingEngine:
    """Loads one encoder and pools token-window embeddings into L2-unit vectors."""

    def __init__(self, model: Any | None = None, config: Settings = settings):
        self.config = config
        self.device = self._choose_device(config.device) if model is None else getattr(model, "device", "test")
        if model is None:
            if self.device == "cpu":
                import torch
                torch.set_num_threads(config.cpu_threads)
                try:
                    torch.set_num_interop_threads(config.cpu_threads)
                except RuntimeError:
                    pass
            # Import here so unit tests and API tooling can inject a small test model.
            # This service is PyTorch-based; an installed but broken TensorFlow backend
            # must not be imported by Transformers' optional-backend discovery.
            os.environ.setdefault("USE_TF", "0")
            os.environ.setdefault("USE_FLAX", "0")
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(config.model_name, device=self.device, cache_folder=config.hf_home)
        self.model = model
        self.tokenizer = model.tokenizer
        self.model_name = config.model_name
        self.max_tokens = int(getattr(model, "max_seq_length", 256))
        if hasattr(self.tokenizer, "model_max_length"):
            # Tokenize the full input, then apply our own explicit token windows.
            self.tokenizer.model_max_length = max(self.max_tokens, 1_000_000)
        get_dimension = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
        self.dimension = int(get_dimension())
        if self.max_tokens < 4:
            raise ValueError("The embedding model max_seq_length must be at least 4 tokens")
        if config.chunk_overlap >= self.max_tokens - 2:
            raise ValueError("EMBEDDING_CHUNK_OVERLAP must be smaller than the model token window")
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._encode_lock = threading.Lock()
        self._metrics_lock = threading.Lock()
        self._metrics: deque[Timing] = deque(maxlen=500)

    @staticmethod
    def _choose_device(preference: str) -> str:
        import torch

        if preference == "auto":
            if torch.cuda.is_available():
                return "cuda"
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        if preference == "cuda":
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError("EMBEDDING_DEVICE=cuda was requested but CUDA is unavailable")
        if preference == "mps":
            if not getattr(torch.backends, "mps", None) or not torch.backends.mps.is_available():
                raise RuntimeError("EMBEDDING_DEVICE=mps was requested but MPS is unavailable")
        return preference

    def warmup(self) -> None:
        self.embed_texts(["CareerLens sentence embedding warmup."])

    def _chunks(self, text: str) -> list[str]:
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        if not token_ids:
            raise ValueError("Text must contain at least one non-whitespace token")
        content_window = self.max_tokens - 2  # Reserve room for tokenizer special tokens.
        stride = content_window - self.config.chunk_overlap
        chunks = []
        for start in range(0, len(token_ids), stride):
            chunk_ids = token_ids[start:start + content_window]
            if not chunk_ids:
                break
            chunk = self.tokenizer.decode(chunk_ids, skip_special_tokens=True,
                                          clean_up_tokenization_spaces=True).strip()
            if chunk:
                chunks.append(chunk)
            if start + content_window >= len(token_ids):
                break
        if not chunks:
            raise ValueError("Text could not be split into model tokens")
        return chunks

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256((self.model_name + "\0" + text).encode("utf-8")).hexdigest()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed input strings, pooling token chunks and returning normalized vectors."""
        if not texts:
            return []
        start_time = time.perf_counter()
        results: list[list[float] | None] = [None] * len(texts)
        missing: dict[str, tuple[str, list[int]]] = {}
        for index, text in enumerate(texts):
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Text must be a non-empty string")
            key = self._cache_key(text)
            with self._cache_lock:
                cached = self._cache.get(key)
                if cached is not None:
                    self._cache.move_to_end(key)
                    results[index] = cached
                    continue
            if key not in missing:
                missing[key] = (text, [])
            missing[key][1].append(index)

        if missing:
            keys = list(missing)
            chunk_texts: list[str] = []
            chunk_ranges: list[tuple[int, int]] = []
            with self._encode_lock:
                for key in keys:
                    chunks = self._chunks(missing[key][0])
                    start = len(chunk_texts)
                    chunk_texts.extend(chunks)
                    chunk_ranges.append((start, len(chunk_texts)))
                chunk_vectors = self.model.encode(
                    chunk_texts,
                    batch_size=self.config.encoder_batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=False,
                    show_progress_bar=False,
                )
            chunk_vectors = np.asarray(chunk_vectors, dtype=np.float32)
            if chunk_vectors.ndim == 1:
                chunk_vectors = chunk_vectors.reshape(1, -1)
            vectors_by_key = {}
            for key, (start, end) in zip(keys, chunk_ranges):
                pooled = np.mean(chunk_vectors[start:end], axis=0)
                norm = float(np.linalg.norm(pooled))
                if not np.isfinite(norm) or norm == 0:
                    raise RuntimeError("The embedding model returned a zero or non-finite vector")
                vector = (pooled / norm).astype(np.float32).tolist()
                if len(vector) != self.dimension:
                    raise RuntimeError(f"Model returned dimension {len(vector)}; expected {self.dimension}")
                vectors_by_key[key] = vector
                with self._cache_lock:
                    if self.config.cache_size:
                        self._cache[key] = vector
                        self._cache.move_to_end(key)
                        while len(self._cache) > self.config.cache_size:
                            self._cache.popitem(last=False)
            for key, (_, indexes) in missing.items():
                for index in indexes:
                    results[index] = vectors_by_key[key]

        output = [vector for vector in results if vector is not None]
        duration = (time.perf_counter() - start_time) * 1000
        with self._metrics_lock:
            self._metrics.append(Timing(duration, len(texts)))
        return output

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def model_info(self) -> dict[str, Any]:
        return {"name": self.model_name, "dimension": self.dimension,
                "max_tokens": self.max_tokens, "device": str(self.device),
                "chunk_overlap_tokens": self.config.chunk_overlap}

    def performance_info(self) -> dict[str, Any]:
        with self._metrics_lock:
            rows = list(self._metrics)
        if not rows:
            return {"requests_measured": 0, "mean_latency_ms": None,
                    "p95_latency_ms": None, "texts_per_second": None}
        durations = np.asarray([row.duration_ms for row in rows], dtype=np.float64)
        elapsed_seconds = float(durations.sum()) / 1000
        texts = sum(row.text_count for row in rows)
        return {"requests_measured": len(rows), "mean_latency_ms": round(float(durations.mean()), 2),
                "p95_latency_ms": round(float(np.percentile(durations, 95)), 2),
                "texts_per_second": round(texts / elapsed_seconds, 2) if elapsed_seconds else None}
