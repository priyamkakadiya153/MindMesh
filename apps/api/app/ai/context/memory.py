import time
from typing import Dict, Any, Optional

class TemporaryContextCache:
    """A thread-safe in-memory cache to store built contexts temporarily."""
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + self._ttl
        }

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
            
        return entry["value"]

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

# Global cache instance
context_cache = TemporaryContextCache()
