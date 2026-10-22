"""
CareerLens High-Performance Caching Service
Provides two-tier caching:
  1. Primary: Redis (TTL: 1 hour)
  2. Fallback: In-memory dictionary with TTL eviction if Redis is unavailable or unconfigured

Cache key is computed from:
  hash(resume_text + target_role + market_data_version)
"""

import hashlib
import json
import logging
import time
import threading
from typing import Optional, Tuple, Dict, Any, Set
from app.core.config import settings
from app.schemas.resume import ScoreResult

logger = logging.getLogger("careerlens.cache")

# Attempt importing redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class InMemoryCache:
    """Thread-safe in-memory cache with TTL expiration."""

    def __init__(self):
        self._store: Dict[str, Tuple[float, str]] = {}  # key -> (expires_at, payload)
        self._resume_keys: Dict[str, Set[str]] = {}     # resume_id -> set of keys
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, val = entry
            if now > expires_at:
                # Expired
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: str, ttl_seconds: int, resume_id: Optional[str] = None) -> None:
        expires_at = time.time() + ttl_seconds
        with self._lock:
            self._store[key] = (expires_at, value)
            if resume_id:
                if resume_id not in self._resume_keys:
                    self._resume_keys[resume_id] = set()
                self._resume_keys[resume_id].add(key)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def invalidate_resume(self, resume_id: str) -> int:
        count = 0
        with self._lock:
            keys = self._resume_keys.pop(resume_id, set())
            for k in keys:
                if self._store.pop(k, None) is not None:
                    count += 1
        return count

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._resume_keys.clear()


class RedisCacheWrapper:
    """Redis client wrapper with automatic error handling and fallback detection."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[Any] = None
        self._is_connected = False
        self._init_client()

    def _init_client(self):
        if not REDIS_AVAILABLE:
            self._is_connected = False
            return
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
                decode_responses=True
            )
            # Test connection
            self._client.ping()
            self._is_connected = True
            logger.info("Connected to Redis cache server.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis at {self.redis_url} ({e}). Falling back to in-memory cache.")
            self._is_connected = False
            self._client = None

    def is_available(self) -> bool:
        if not self._is_connected or not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            self._is_connected = False
            return False

    def get(self, key: str) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    def set(self, key: str, value: str, ttl_seconds: int, resume_id: Optional[str] = None) -> bool:
        if not self.is_available():
            return False
        try:
            self._client.setex(key, ttl_seconds, value)
            if resume_id:
                # Track resume keys in a Redis set for invalidation
                tag_key = f"careerlens:resume_tags:{resume_id}"
                self._client.sadd(tag_key, key)
                self._client.expire(tag_key, ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            return False

    def delete(self, key: str) -> None:
        if not self.is_available():
            return
        try:
            self._client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

    def invalidate_resume(self, resume_id: str) -> int:
        if not self.is_available():
            return 0
        try:
            tag_key = f"careerlens:resume_tags:{resume_id}"
            keys = self._client.smembers(tag_key)
            count = 0
            if keys:
                count = self._client.delete(*keys)
            self._client.delete(tag_key)
            return count
        except Exception as e:
            logger.warning(f"Redis invalidate_resume failed: {e}")
            return 0

    def clear(self) -> None:
        if not self.is_available():
            return
        try:
            keys = self._client.keys("careerlens:score:*")
            if keys:
                self._client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")


class CacheService:
    """
    Unified Caching Layer for CareerLens.
    Supports Redis with automatic in-memory fallback.
    """

    def __init__(self):
        self.in_memory = InMemoryCache()
        self.redis = RedisCacheWrapper(settings.REDIS_URL)

    @staticmethod
    def compute_cache_key(resume_text: str, target_role: str, market_version: Optional[str] = None) -> str:
        """
        Computes SHA-256 hash: hash(resume text + target_role + market data version).
        """
        version = market_version or settings.MARKET_DATA_VERSION
        normalized_role = target_role.strip().lower()
        content = f"{resume_text.strip()}::{normalized_role}::{version}"
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return f"careerlens:score:{digest}"

    def get_cached_score(
        self,
        resume_text: str,
        target_role: str,
        market_version: Optional[str] = None
    ) -> Tuple[Optional[ScoreResult], bool]:
        """
        Fetches ScoreResult from Redis, then InMemory fallback.
        Returns: (ScoreResult | None, is_hit: bool)
        """
        key = self.compute_cache_key(resume_text, target_role, market_version)

        # 1. Try Redis
        raw_val = self.redis.get(key)
        if raw_val is not None:
            try:
                data = json.loads(raw_val)
                score_result = ScoreResult(**data)
                return score_result, True
            except Exception as e:
                logger.warning(f"Failed to deserialize Redis cached ScoreResult: {e}")

        # 2. Try In-Memory Fallback
        raw_mem = self.in_memory.get(key)
        if raw_mem is not None:
            try:
                data = json.loads(raw_mem)
                score_result = ScoreResult(**data)
                return score_result, True
            except Exception as e:
                logger.warning(f"Failed to deserialize InMemory cached ScoreResult: {e}")

        return None, False

    def set_cached_score(
        self,
        resume_text: str,
        target_role: str,
        result: ScoreResult,
        market_version: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        resume_id: Optional[str] = None
    ) -> None:
        """
        Stores ScoreResult in both Redis (if available) and In-Memory cache.
        """
        key = self.compute_cache_key(resume_text, target_role, market_version)
        ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        json_str = result.model_dump_json()

        # Write to in-memory cache
        self.in_memory.set(key, json_str, ttl_seconds=ttl, resume_id=resume_id or result.resume_id)

        # Write to Redis if online
        self.redis.set(key, json_str, ttl_seconds=ttl, resume_id=resume_id or result.resume_id)

    def invalidate_resume(self, resume_id: str) -> None:
        """
        Invalidates cached entries when resume is re-uploaded.
        """
        mem_count = self.in_memory.invalidate_resume(resume_id)
        redis_count = self.redis.invalidate_resume(resume_id)
        logger.info(f"Invalidated cache for resume {resume_id} (mem={mem_count}, redis={redis_count})")

    def invalidate_market_refresh(self) -> None:
        """
        Invalidates cached entries when market data is refreshed.
        """
        self.in_memory.clear()
        self.redis.clear()
        logger.info("Invalidated all scoring caches due to market data refresh.")

    def clear(self) -> None:
        """Clears all caches (useful for test isolation)."""
        self.in_memory.clear()
        self.redis.clear()


# Global cache service instance
cache_service = CacheService()
