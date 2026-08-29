import json
import logging
from typing import Optional, Any
import redis.asyncio as redis
from ..core.config import settings

import time
import fnmatch

logger = logging.getLogger("dashboard_cache")

class DashboardCache:
    def __init__(self):
        self.redis_client = None
        self._memory_cache = {}
        if settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")

    async def get(self, key: str) -> Optional[Any]:
        if self.redis_client:
            try:
                val = await self.redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Error fetching from Redis cache: {e}")

        # In-memory fallback check
        if key in self._memory_cache:
            data, expires_at = self._memory_cache[key]
            if time.time() < expires_at:
                return data
            else:
                del self._memory_cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        self._memory_cache[key] = (value, time.time() + ttl)
        if not self.redis_client:
            return
        try:
            await self.redis_client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Error setting Redis cache: {e}")

    async def invalidate(self, key_pattern: str) -> None:
        # Invalidate in-memory matching keys
        pattern = key_pattern.replace("*", ".*")
        to_del = [k for k in self._memory_cache if fnmatch.fnmatch(k, key_pattern)]
        for k in to_del:
            self._memory_cache.pop(k, None)

        if not self.redis_client:
            return
        try:
            keys = await self.redis_client.keys(key_pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Error invalidating Redis cache pattern {key_pattern}: {e}")

export_cache = DashboardCache()
