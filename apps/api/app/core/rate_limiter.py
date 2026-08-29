import time
from typing import Dict, List
from fastapi import Request, HTTPException, status

class RateLimiter:
    """Sliding Window Rate Limiter tracking requests per client/workspace."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}

    def is_rate_limited(self, key: str) -> tuple[bool, int]:
        """Checks if key exceeded rate limit. Returns (is_limited, retry_after_seconds)."""
        now = time.time()
        cutoff = now - self.window_seconds

        timestamps = self._history.get(key, [])
        # Filter older timestamps
        valid_timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(valid_timestamps) >= self.max_requests:
            oldest = valid_timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return True, max(1, retry_after)

        valid_timestamps.append(now)
        self._history[key] = valid_timestamps
        return False, 0

# Shared rate limiters
general_rate_limiter = RateLimiter(max_requests=120, window_seconds=60)
ai_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

async def check_rate_limit(request: Request):
    """FastAPI Dependency for general API rate limiting."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"ip:{client_ip}"

    is_limited, retry_after = general_rate_limiter.is_rate_limited(key)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests. Rate limit exceeded.",
            headers={"Retry-After": str(retry_after)}
        )
