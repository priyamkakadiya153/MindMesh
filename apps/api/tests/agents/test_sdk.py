import pytest
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.agents.context import SessionContext
from app.agents.sdk.agent import BaseAgent, agent
from app.agents.registry import agent_registry
from app.agents.sdk.memory import AgentMemory

async def seed_agent_test_data(db: AsyncSession):
    from sqlalchemy import select
    stmt = select(Role).where(Role.name == "TEST_MEMBER")
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name="TEST_MEMBER", description="Test Member Role")
        db.add(role)
        await db.flush()

    import uuid
    suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"test_agent_user_{suffix}",
        email=f"testagent_{suffix}@example.com",
        hashed_password="pwd"
    )
    db.add(user)
    await db.flush()
    org = Organization(
        name=f"Test Agent Org {suffix}",
        slug=f"test-agent-org-{suffix}",
        owner_id=user.id
    )
    db.add(org)
    await db.flush()
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db.add(member)
    await db.commit()
    return user, org

@agent(
    name="DummyAgent",
    description="A dummy agent for verification.",
    version="1.1.0",
    required_permissions=["dummy.perm"]
)
class DummyAgent(BaseAgent):
    async def execute(self, context: SessionContext, input_data: dict, db: AsyncSession) -> dict:
        self.memory.set_short_term("ran", True)
        return {"input": input_data, "short_term_ran": self.memory.get_short_term("ran")}

@pytest.mark.asyncio
async def test_agent_decorator_registration():
    # Verify metadata is attached
    assert "dummy" in agent_registry._agents
    cls = agent_registry.get_agent("dummy")
    assert cls == DummyAgent
    meta = getattr(cls, "_agent_meta", {})
    assert meta["name"] == "DummyAgent"
    assert meta["version"] == "1.1.0"
    assert meta["required_permissions"] == ["dummy.perm"]

@pytest.mark.asyncio
async def test_agent_memory_persistence(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    agent_uuid = uuid4()
    
    # 1. Instantiate memory service
    memory = AgentMemory(agent_uuid, org.id, db_session)
    
    # 2. Short term checks
    memory.set_short_term("temp_key", 42)
    assert memory.get_short_term("temp_key") == 42
    
    # 3. Long term checks
    long_term_data = {"profile": "analyst", "preferences": {"dark_mode": True}}
    await memory.save_long_term(long_term_data)
    
    # Read back
    retrieved = await memory.get_long_term()
    assert retrieved["profile"] == "analyst"
    assert retrieved["preferences"]["dark_mode"] is True
