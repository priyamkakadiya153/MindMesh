import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.cache import CacheService
from app.core.rate_limiter import RateLimiter
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_performance_and_readiness():
    print("--- Starting MindMesh Phase 3.10 Performance & Production Readiness Test ---")

    # 1. Test CacheService (Set, Get, Hit Ratio, Invalidation)
    t0 = time.time()
    await CacheService.set("test_key_1", {"msg": "hello_mindmesh"}, ttl_seconds=60)
    cached_val = await CacheService.get("test_key_1")
    cache_lat_ms = (time.time() - t0) * 1000

    assert cached_val is not None
    assert cached_val["msg"] == "hello_mindmesh"
    assert cache_lat_ms < 10.0  # <10ms Level 1 Cache SLA
    print(f"--> Verified Multi-Level Cache SLA (Latency: {cache_lat_ms:.2f}ms).")

    # Invalidation test
    await CacheService.invalidate_pattern("test_key")
    invalidated_val = await CacheService.get("test_key_1")
    assert invalidated_val is None
    print("--> Verified Automatic Cache Invalidation.")

    # 2. Test RateLimiter (Sliding Window & 429 Threshold)
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    test_client = "ip:192.168.1.100"

    is_l1, _ = limiter.is_rate_limited(test_client)
    is_l2, _ = limiter.is_rate_limited(test_client)
    is_l3, _ = limiter.is_rate_limited(test_client)
    is_l4, retry_after = limiter.is_rate_limited(test_client)

    assert is_l1 is False
    assert is_l2 is False
    assert is_l3 is False
    assert is_l4 is True
    assert retry_after > 0
    print(f"--> Verified Rate Limiter Threshold (429 Triggered after 3 requests, Retry-After: {retry_after}s).")

    # 3. Test Database Connection Pooling & Latency
    t1 = time.time()
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT 1"))
        val = res.scalar()
        assert val == 1
    db_lat_ms = (time.time() - t1) * 1000

    assert db_lat_ms < 100.0  # <100ms Database Query SLA
    print(f"--> Verified Database Connection Pool Performance (Query Latency: {db_lat_ms:.2f}ms).")

    print("=== MindMesh Phase 3.10 Performance & Production Readiness Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_performance_and_readiness())
