import time
import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class ProviderHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    RATE_LIMITED = "RATE_LIMITED"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"

class AIMetricsTracker:
    """
    Lightweight internal observability tracker for AI requests, rate limits, latency, and health state.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIMetricsTracker, cls).__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        self.ai_requests_total = 0
        self.ai_rate_limited_total = 0
        self.ai_errors_total = 0
        self.ai_generation_latency_sum_ms = 0
        self.provider_health: Dict[str, ProviderHealthState] = {
            "gemini": ProviderHealthState.HEALTHY
        }
        self.last_rate_limit_timestamp: Dict[str, float] = {}

    def record_request(self, provider: str = "gemini"):
        self.ai_requests_total += 1

    def record_success(self, provider: str, latency_ms: int):
        self.ai_generation_latency_sum_ms += latency_ms
        # If cooldown period of 60s has passed since last rate limit, reset to HEALTHY
        last_rl = self.last_rate_limit_timestamp.get(provider, 0.0)
        if time.time() - last_rl > 60.0:
            self.provider_health[provider] = ProviderHealthState.HEALTHY

    def record_rate_limit(self, provider: str = "gemini"):
        self.ai_rate_limited_total += 1
        self.ai_errors_total += 1
        self.last_rate_limit_timestamp[provider] = time.time()
        self.provider_health[provider] = ProviderHealthState.RATE_LIMITED

    def record_error(self, provider: str = "gemini", is_degraded: bool = False):
        self.ai_errors_total += 1
        if is_degraded:
            self.provider_health[provider] = ProviderHealthState.DEGRADED
        else:
            self.provider_health[provider] = ProviderHealthState.UNAVAILABLE

    def get_health_status(self, provider: str = "gemini") -> Dict[str, Any]:
        last_rl = self.last_rate_limit_timestamp.get(provider, 0.0)
        if self.provider_health.get(provider) == ProviderHealthState.RATE_LIMITED and time.time() - last_rl > 60.0:
            self.provider_health[provider] = ProviderHealthState.HEALTHY

        avg_latency = (
            int(self.ai_generation_latency_sum_ms / max(1, self.ai_requests_total))
            if self.ai_requests_total > 0
            else 0
        )
        return {
            "provider": provider,
            "status": self.provider_health.get(provider, ProviderHealthState.HEALTHY).value,
            "metrics": {
                "ai_requests_total": self.ai_requests_total,
                "ai_rate_limited_total": self.ai_rate_limited_total,
                "ai_errors_total": self.ai_errors_total,
                "ai_generation_latency_avg_ms": avg_latency
            }
        }

metrics_tracker = AIMetricsTracker()
