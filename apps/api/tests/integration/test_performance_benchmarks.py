import time
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.service import MemoryService
from app.governance.policy_engine import PolicyEngine
from app.governance.trust import TrustScorer
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_memory_retrieval_performance_benchmarks(db_session: AsyncSession):
    """Measures retrieval latency to guarantee speed targets are hit."""
    user, org = await seed_agent_test_data(db_session)

    # Pre-populate 5 preference records
    for i in range(5):
        await MemoryService.add_memory(
            db=db_session,
            organization_id=org.id,
            memory_type="User",
            scope_key=str(user.id),
            key=f"perf_key_{i}",
            value={"data": f"value_{i}"}
        )
    await db_session.commit()

    # Time context search assembly
    start = time.perf_counter()
    results = await MemoryService.search_memories(
        db=db_session,
        organization_id=org.id,
        user_id=user.id,
        query_key="perf_key_0"
    )
    end = time.perf_counter()
    latency_ms = (end - start) * 1000.0

    print(f"Memory context retrieval completed in: {latency_ms:.2f} ms")
    # Target: under 200 ms
    assert latency_ms < 200.0

@pytest.mark.asyncio
async def test_policy_validation_performance_benchmarks(db_session: AsyncSession):
    """Measures validation checking rules run latency."""
    user, org = await seed_agent_test_data(db_session)

    start = time.perf_counter()
    allowed, violations = await PolicyEngine.validate_policy(
        db=db_session,
        organization_id=org.id,
        category="Security",
        context_data={"text": "Hello clean statement."}
    )
    end = time.perf_counter()
    latency_ms = (end - start) * 1000.0

    print(f"Policy engine check rules completed in: {latency_ms:.2f} ms")
    # Target: under 50 ms
    assert latency_ms < 50.0

def test_trust_scorer_performance_benchmarks():
    """Measures calculation complexity throughput."""
    start = time.perf_counter()
    for _ in range(100):
        TrustScorer.calculate_trust_score(
            knowledge_quality=0.9,
            retrieval_confidence=0.85,
            policy_compliance=1.0,
            tool_reliability=0.9,
            workflow_success=0.95
        )
    end = time.perf_counter()
    total_ms = (end - start) * 1000.0
    avg_latency_ms = total_ms / 100.0

    print(f"Composite trust score calculated (average): {avg_latency_ms:.4f} ms")
    # Target: under 100 ms
    assert avg_latency_ms < 10.0
