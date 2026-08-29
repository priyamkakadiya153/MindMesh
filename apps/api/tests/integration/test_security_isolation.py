import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.service import MemoryService
from app.governance.policy_store import PolicyStore
from app.governance.enforcement import PolicyEnforcement
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_cross_tenant_memory_leakage_prevention(db_session: AsyncSession):
    """Enforces strict tenant isolation: Org B user cannot search/leak Org A user memory."""
    user_a, org_a = await seed_agent_test_data(db_session)
    user_b, org_b = await seed_agent_test_data(db_session)

    # Org A User saves private memory preference
    await MemoryService.add_memory(
        db=db_session,
        organization_id=org_a.id,
        memory_type="User",
        scope_key=str(user_a.id),
        key="api_key",
        value={"secret": "org_a_secret_token"}
    )
    await db_session.commit()

    # Org B User searches for "api_key" under Org B context
    results = await MemoryService.search_memories(
        db=db_session,
        organization_id=org_b.id,
        user_id=user_b.id,
        query_key="api_key"
    )

    # Must be completely isolated: empty list returned
    assert len(results) == 0

@pytest.mark.asyncio
async def test_tool_calling_governed_enforcement(db_session: AsyncSession):
    """Verifies that blacklisted tools are rejected by policy enforcement middleware."""
    user, org = await seed_agent_test_data(db_session)

    # Establish tool blacklist governance policy
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="Security Policy Tools Blacklist",
        category="Tool",
        rules={"blacklisted_tools": ["execute_terminal_shell"]}
    )
    await db_session.commit()

    # Enforce prompt injection of tool calling
    with pytest.raises(ValueError) as exc:
        await PolicyEnforcement.enforce_tool_execution(
            db=db_session,
            organization_id=org.id,
            tool_name="execute_terminal_shell"
        )
    assert "Tool execution blocked by Tool Policy" in str(exc.value)

@pytest.mark.asyncio
async def test_pii_data_leakage_prevention(db_session: AsyncSession):
    """Verifies that PII leakages (e.g. emails) in prompts are blocked by Privacy policy."""
    user, org = await seed_agent_test_data(db_session)

    # Establish privacy protection policy
    await PolicyStore.create_policy(
        db=db_session,
        organization_id=org.id,
        name="PII Shield Policy",
        category="Privacy",
        rules={"pii_protection": True}
    )
    await db_session.commit()

    # Check prompt containing sensitive email address PII
    with pytest.raises(ValueError) as exc:
        await PolicyEnforcement.enforce_prompt(
            db=db_session,
            organization_id=org.id,
            text="Hello my email address is developer@domain.com"
        )
    assert "Prompt blocked by Privacy Policy" in str(exc.value)
