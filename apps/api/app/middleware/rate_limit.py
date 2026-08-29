import time
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Only rate limit sensitive authentication and OTP endpoints
        if any(endpoint in path for endpoint in ["/auth/login", "/auth/mobile/send-otp", "/auth/mobile/resend-otp", "/auth/password/forgot"]):
            client_ip = request.client.host if request.client else "unknown"
            key = f"{client_ip}:{path}"
            now = time.time()

            # Clean expired timestamps
            timestamps = [ts for ts in self.request_history[key] if now - ts < self.window_seconds]
            self.request_history[key] = timestamps

            if len(timestamps) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Please wait a minute before trying again."}
                )

            self.request_history[key].append(now)

        response = await call_next(request)
        return response
