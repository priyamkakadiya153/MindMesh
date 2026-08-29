import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.ai.orchestrator import MindMeshAIOrchestrator

async def test_casual_routing():
    print("=== Starting MindMesh Phase 2.3 Casual Query Routing Test ===")

    async with AsyncSessionLocal() as session:
        org = Organization(name="Casual Test Org", slug=f"cas-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Casual Workspace", slug=f"cas-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"cas_user_{u_id}@mindmesh.com",
            username=f"cas_user_{u_id}",
            first_name="Casual",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        # 1. Casual Query "Hello"
        res_casual = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="Hello",
            workspace_id=ws.id
        )

        assert res_casual["intent"] == "CASUAL"
        assert len(res_casual["sources"]) == 0
        print(f"--> [CASUAL ROUTING PASS] 'Hello' correctly detected as CASUAL (Sources: {len(res_casual['sources'])})")

    print("=== Casual Query Routing Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_casual_routing())
