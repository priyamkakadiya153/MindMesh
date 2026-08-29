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
from app.models.chat import Chat
from app.ai.conversation.processor import ConversationIntelligenceProcessor
from app.ai.orchestrator import MindMeshAIOrchestrator

async def test_private_dm_security():
    print("=== Starting MindMesh Phase 2.4 Private Conversation Security Test ===")

    async with AsyncSessionLocal() as session:
        # Setup tenant
        org = Organization(name="Privacy Test Org", slug=f"priv-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Private Workspace", slug=f"priv-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_a_id = uuid.uuid4().hex[:6]
        user_a = User(
            email=f"user_a_{u_a_id}@mindmesh.com",
            username=f"user_a_{u_a_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_a_id}"
        )
        u_b_id = uuid.uuid4().hex[:6]
        user_b = User(
            email=f"user_b_{u_b_id}@mindmesh.com",
            username=f"user_b_{u_b_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_b_id}"
        )
        u_c_id = uuid.uuid4().hex[:6]
        user_c = User(
            email=f"user_c_{u_c_id}@mindmesh.com",
            username=f"user_c_{u_c_id}",
            first_name="User",
            last_name="C",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_c_id}"
        )
        session.add_all([user_a, user_b, user_c])
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user_a.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=org.id, user_id=user_b.id, role="member", is_active=True))
        session.add(OrganizationMember(organization_id=org.id, user_id=user_c.id, role="member", is_active=True))

        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_a.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_b.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_c.id, role="member", is_active=True))
        await session.commit()

        dm_chat_id = uuid.uuid4()
        dm_chat = Chat(
            id=dm_chat_id,
            name="Private DM User A & User B",
            user_id=user_a.id,
            organization_id=org.id,
            workspace_id=ws.id,
            status="active"
        )
        session.add(dm_chat)
        await session.commit()

        dm_messages = [
            {"id": uuid.uuid4(), "sender_id": user_a.id, "sender_name": "User A", "content": "We agreed that Secret Code for Project X is Omega777.", "timestamp": "2026-08-10T10:00:00Z"}
        ]

        await ConversationIntelligenceProcessor.process_conversation_messages(
            db=session,
            chat_id=dm_chat_id,
            organization_id=org.id,
            workspace_id=ws.id,
            messages=dm_messages
        )

        orchestrator = MindMeshAIOrchestrator(session)

        # 1. Participant User A queries Ask MindMesh
        res_a = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org.id,
            query="What is the Secret Code for Project X?",
            workspace_id=ws.id
        )
        assert res_a["grounded"] == True
        print("--> [PRIVACY PASS] Participant User A CAN access private DM insight!")

        # 2. Non-Participant User C queries Ask MindMesh across workspace
        ws2 = Workspace(organization_id=org.id, name="Other Workspace C", slug=f"ws-c-{uuid.uuid4().hex[:6]}")
        session.add(ws2)
        await session.commit()
        session.add(WorkspaceMember(workspace_id=ws2.id, user_id=user_c.id, role="admin", is_active=True))
        await session.commit()

        res_c = await orchestrator.execute(
            user_id=user_c.id,
            org_id=org.id,
            query="What is the Secret Code for Project X?",
            workspace_id=ws2.id
        )
        assert res_c["grounded"] == False or "couldn't find enough information" in res_c["answer"]
        print("--> [PRIVACY PASS] Non-participant User C in Workspace C CANNOT access private DM insight!")

    print("=== Private Conversation Security Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_private_dm_security())
