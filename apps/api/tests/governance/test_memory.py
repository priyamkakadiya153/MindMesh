import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import LongTermMemory
from app.memory.service import MemoryService
from app.memory.repository import MemoryRepository
from app.memory.retrieval import MemoryRetrieval
from app.memory.ranking import MemoryRanker
from app.memory.retention import MemoryRetentionManager
from app.memory.analytics import MemoryAnalytics
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_memory_scope_isolation_and_retrieval(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    user2, org2 = await seed_agent_test_data(db_session)  # different tenant org

    # 1. Add memories for Org 1
    m_user = await MemoryService.add_memory(
        db=db_session,
        organization_id=org.id,
        memory_type="User",
        scope_key=str(user.id),
        key="theme_pref",
        value={"theme": "dark"},
        importance_score=0.9
    )

    m_org = await MemoryService.add_memory(
        db=db_session,
        organization_id=org.id,
        memory_type="Organization",
        scope_key=str(org.id),
        key="org_standard",
        value={"guidelines": "use Python 3.12"},
        importance_score=0.7
    )

    # 2. Add memories for Org 2
    m_org2 = await MemoryService.add_memory(
        db=db_session,
        organization_id=org2.id,
        memory_type="Organization",
        scope_key=str(org2.id),
        key="org_standard",
        value={"guidelines": "use Next.js"},
        importance_score=0.8
    )

    # 3. Retrieve context for User 1 under Org 1 (should NOT see Org 2's memory)
    context = await MemoryService.search_memories(
        db=db_session,
        organization_id=org.id,
        user_id=user.id
    )

    assert len(context) == 2
    theme_mem = next(c for c in context if c["key"] == "theme_pref")
    org_mem = next(c for c in context if c["key"] == "org_standard")
    assert theme_mem["value"]["theme"] == "dark"
    assert org_mem["value"]["guidelines"] == "use Python 3.12"

    # Theme preference is ranked higher due to importance score (0.9 vs 0.7)
    assert context[0]["key"] == "theme_pref"

    # 4. Try retrieving for User 1 under Org 2 (should see Org 2's memories but not User 1's theme pref from Org 1)
    context2 = await MemoryService.search_memories(
        db=db_session,
        organization_id=org2.id,
        user_id=user.id
    )
    assert len(context2) == 1
    assert context2[0]["key"] == "org_standard"
    assert context2[0]["value"]["guidelines"] == "use Next.js"

@pytest.mark.asyncio
async def test_memory_retention_and_expiration(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # Expired memory
    await MemoryService.add_memory(
        db=db_session,
        organization_id=org.id,
        memory_type="User",
        scope_key=str(user.id),
        key="temp_pref",
        value={"temp": "value"},
        retention_days=-1  # Expired yesterday
    )

    # Active memory
    await MemoryService.add_memory(
        db=db_session,
        organization_id=org.id,
        memory_type="User",
        scope_key=str(user.id),
        key="long_pref",
        value={"long": "value"},
        retention_days=10  # Expires in 10 days
    )

    await db_session.commit()

    # 1. Search memories (should exclude expired memory automatically)
    context = await MemoryService.search_memories(
        db=db_session,
        organization_id=org.id,
        user_id=user.id
    )
    assert len(context) == 1
    assert context[0]["key"] == "long_pref"

    # 2. Run retention purge sweep
    purged_count = await MemoryRetentionManager.purge_expired_memories(db_session)
    assert purged_count == 1

    # 3. GDPR Force forget user memories
    forgot_count = await MemoryRetentionManager.force_forget_user_memory(db_session, org.id, user.id)
    assert forgot_count == 1

    # Empty context
    context_purged = await MemoryService.search_memories(
        db=db_session,
        organization_id=org.id,
        user_id=user.id
    )
    assert len(context_purged) == 0
