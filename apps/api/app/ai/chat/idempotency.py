import time
import logging
from typing import Dict, Any, Optional
from app.ai.gateway.models import AIResponse, AIResponseStatus

logger = logging.getLogger(__name__)

class IdempotencyManager:
    """
    Idempotency & Duplicate Prevention Manager.
    
    Prevents duplicate message creation and AI request duplication caused by:
    - Rapid double clicks on Send button
    - Pressing Enter and clicking Send simultaneously
    - Network retries from client HTTP layers
    """

    _cache: Dict[str, Dict[str, Any]] = {}
    _in_flight: Dict[str, float] = {}

    TTL_SECONDS = 60.0

    @classmethod
    def _clean_expired(cls):
        now = time.time()
        expired_keys = [k for k, v in cls._cache.items() if now - v["timestamp"] > cls.TTL_SECONDS]
        for k in expired_keys:
            cls._cache.pop(k, None)

        expired_inflight = [k for k, t in cls._in_flight.items() if now - t > cls.TTL_SECONDS]
        for k in expired_inflight:
            cls._in_flight.pop(k, None)

    @classmethod
    def make_key(cls, user_id: str, idempotency_key: str, conversation_id: Optional[str] = None) -> str:
        conv_part = conversation_id or "global"
        return f"{conv_part}:{user_id}:{idempotency_key}"

    @classmethod
    def register_in_flight(cls, key: str) -> bool:
        """
        Registers a request key as currently processing.
        Returns True if newly registered, False if ALREADY in-flight (duplicate submit blocked).
        """
        cls._clean_expired()
        now = time.time()
        if key in cls._in_flight:
            logger.warning(f"[IdempotencyManager] Blocked in-flight duplicate submit for key '{key}'")
            return False

        cls._in_flight[key] = now
        return True

    @classmethod
    def release_in_flight(cls, key: str) -> None:
        cls._in_flight.pop(key, None)

    @classmethod
    def get_cached_response(cls, key: str) -> Optional[AIResponse]:
        cls._clean_expired()
        item = cls._cache.get(key)
        if item:
            logger.info(f"[IdempotencyManager] Returning cached idempotent response for key '{key}'")
            return item["response"]
        return None

    @classmethod
    def cache_response(cls, key: str, response: AIResponse) -> None:
        cls.release_in_flight(key)
        if response.status == AIResponseStatus.COMPLETED:
            cls._cache[key] = {
                "response": response,
                "timestamp": time.time()
            }
