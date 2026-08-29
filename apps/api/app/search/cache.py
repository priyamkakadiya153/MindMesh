import time
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class SearchCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieves item from cache if it has not expired yet."""
        if key not in self._cache:
            return None
        val, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key] # cleanup expired item
            return None
        return val

    def set(self, key: str, value: Any) -> None:
        """Saves item to cache with configured TTL expiry."""
        expiry = time.time() + self.ttl
        self._cache[key] = (value, expiry)

    def clear(self) -> None:
        """Clears all cache elements."""
        self._cache.clear()

search_cache = SearchCache()
