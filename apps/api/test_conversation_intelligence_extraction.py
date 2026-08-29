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
from app.ai.conversation.processor import ConversationIntelligenceProcessor
from app.ai.orchestrator import MindMeshAIOrchestrator

async def test_conversation_intelligence_extraction():
    print("=== Starting MindMesh Phase 2.4 Section 49 Required E2E Conversation Intelligence Test ===")

    async with AsyncSessionLocal() as session:
        # Setup tenant
        org = Organization(name="Conv Intel Org", slug=f"ci-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Architecture Workspace", slug=f"ci-ws-{uuid.uuid4().hex[:6]}")
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
        session.add_all([user_a, user_b])
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user_a.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=org.id, user_id=user_b.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_a.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_b.id, role="member", is_active=True))
        await session.commit()

        chat_id = uuid.uuid4()
        from app.models.chat import Chat
        chat = Chat(
            id=chat_id,
            name="Architecture Team",
            user_id=user_a.id,
            organization_id=org.id,
            workspace_id=ws.id,
            status="active"
        )
        session.add(chat)
        await session.commit()

        messages = [
            {"id": uuid.uuid4(), "sender_id": user_a.id, "sender_name": "User A", "content": "Should we use PostgreSQL for production?", "timestamp": "2026-08-10T10:00:00Z"},
            {"id": uuid.uuid4(), "sender_id": user_b.id, "sender_name": "User B", "content": "Yes, I agree. We decided that production database is PostgreSQL.", "timestamp": "2026-08-10T10:01:00Z"},
            {"id": uuid.uuid4(), "sender_id": user_a.id, "sender_name": "User A", "content": "User A will update the deployment configuration tomorrow.", "timestamp": "2026-08-10T10:02:00Z"},
            {"id": uuid.uuid4(), "sender_id": user_b.id, "sender_name": "User B", "content": "Great.", "timestamp": "2026-08-10T10:03:00Z"}
        ]

        # Process conversation intelligence
        proc_res = await ConversationIntelligenceProcessor.process_conversation_messages(
            db=session,
            chat_id=chat_id,
            organization_id=org.id,
            workspace_id=ws.id,
            messages=messages
        )
        print("DEBUG proc_res:", proc_res)

        assert proc_res["status"] == "PROCESSED"
        print(f"--> [EXTRACTION PASS] Processed conversation: Extracted {proc_res['extracted_count']} structured insights.")

        orchestrator = MindMeshAIOrchestrator(session)

        # 1. Ask: "What database did the team decide to use?"
        res1 = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org.id,
            query="What database did the team decide to use?",
            workspace_id=ws.id
        )
        assert res1["grounded"] == True
        print("--> [QUESTION 1 PASS] Answer:", res1["answer"])

        # 2. Ask: "Who agreed?"
        res2 = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org.id,
            query="Who agreed on PostgreSQL database decision?",
            workspace_id=ws.id
        )
        assert res2["grounded"] == True
        print("--> [QUESTION 2 PASS] Answer:", res2["answer"])

        # 3. Ask: "What action item was created?"
        res3 = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org.id,
            query="What action item or task was created?",
            workspace_id=ws.id
        )
        print("DEBUG res3 answer:", res3.get("answer"))
        print("DEBUG res3 grounded:", res3.get("grounded"))
        print("DEBUG res3 sources:", res3.get("sources"))
        assert res3["grounded"] == True
        print("--> [QUESTION 3 PASS] Answer:", res3["answer"])

        # 4. Ask: "Did the team decide to use MongoDB?"
        res4 = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org.id,
            query="Did the team decide to use MongoDB?",
            workspace_id=ws.id
        )
        assert res4["grounded"] == False or "couldn't find enough information" in res4["answer"]
        print("--> [QUESTION 4 PASS] Negative query refused correctly without fabrication!")

    print("=== Section 49 Required E2E Conversation Intelligence Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_intelligence_extraction())
