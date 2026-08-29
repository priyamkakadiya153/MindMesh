import time
import json
import logging
from typing import Any, Optional, Dict
import os

logger = logging.getLogger(__name__)

# Level 1 In-Memory Cache with TTL
_in_memory_cache: Dict[str, Dict[str, Any]] = {}

class CacheService:
    """Enterprise Multi-Level Caching Service (Level 1: In-Memory, Level 2: Redis)."""

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_client = None
    _redis_disabled = False

    @classmethod
    async def get_redis(cls):
        """Returns initialized async Redis client or None if unreachable."""
        if cls._redis_disabled:
            return None
        if cls._redis_client is None:
            try:
                import redis.asyncio as aioredis
                cls._redis_client = aioredis.from_url(cls.REDIS_URL, decode_responses=True)
                await cls._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed ({e}). Falling back to Level 1 In-Memory Cache.")
                cls._redis_disabled = True
                cls._redis_client = None
        return cls._redis_client

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Gets cached value from Level 1 In-Memory or Level 2 Redis."""
        now = time.time()
        
        # Level 1 check
        if key in _in_memory_cache:
            entry = _in_memory_cache[key]
            if entry["expires_at"] > now:
                return entry["value"]
            else:
                del _in_memory_cache[key]

        # Level 2 Redis check
        r = await cls.get_redis()
        if r:
            try:
                val = await r.get(key)
                if val:
                    data = json.loads(val)
                    # Sync back to Level 1
                    _in_memory_cache[key] = {"value": data, "expires_at": now + 60}
                    return data
            except Exception as e:
                logger.debug(f"Redis GET failed for key {key}: {e}")

        return None

    @classmethod
    async def set(cls, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Sets cached value across Level 1 and Level 2."""
        now = time.time()
        _in_memory_cache[key] = {
            "value": value,
            "expires_at": now + ttl_seconds
        }

        r = await cls.get_redis()
        if r:
            try:
                serialized = json.dumps(value)
                await r.set(key, serialized, ex=ttl_seconds)
                return True
            except Exception as e:
                logger.debug(f"Redis SET failed for key {key}: {e}")

        return True

    @classmethod
    async def delete(cls, key: str) -> bool:
        """Deletes cached key across all levels."""
        if key in _in_memory_cache:
            del _in_memory_cache[key]

        r = await cls.get_redis()
        if r:
            try:
                await r.delete(key)
            except Exception as e:
                logger.debug(f"Redis DELETE failed for key {key}: {e}")

        return True

    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """Invalidates keys matching pattern."""
        count = 0
        keys_to_del = [k for k in _in_memory_cache.keys() if pattern in k]
        for k in keys_to_del:
            del _in_memory_cache[k]
            count += 1

        r = await cls.get_redis()
        if r:
            try:
                keys = await r.keys(f"*{pattern}*")
                if keys:
                    await r.delete(*keys)
                    count += len(keys)
            except Exception as e:
                logger.debug(f"Redis pattern invalidation failed for {pattern}: {e}")

        return count
