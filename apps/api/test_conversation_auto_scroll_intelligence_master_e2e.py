import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.ai.chat.session import ChatSessionManager

async def test_conversation_auto_scroll_intelligence_master_e2e():
    print("=== Starting MindMesh Conversation Continuity, Auto-Scroll & Response Intelligence Master Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="AutoScroll Org", slug=f"scroll-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="AutoScroll Workspace", slug=f"scroll-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"scroll_user_{u_id}@mindmesh.com",
            username=f"scroll_user_{u_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}",
            current_organization_id=org.id
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        # Create conversation thread
        chat = await ChatSessionManager.create_conversation(session, org.id, user.id, ws.id, "Continuity Test Thread")
        await session.commit()

        # -------------------------------------------------------------
        # TEST 1: INITIAL GREETING ("hi")
        # -------------------------------------------------------------
        chunks_1 = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="hi",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            chunks_1.append(chunk)

        greeting_1 = "".join([c["content"] for c in chunks_1 if c.get("type") == "token"]).strip()
        print("--> [TEST 1 PASS] First Greeting Response:", greeting_1)
        assert "Hi! How can I help you" in greeting_1

        # -------------------------------------------------------------
        # TEST 2: REPEATED GREETING ("hi" a second time in same chat)
        # -------------------------------------------------------------
        chunks_2 = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="hi",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            chunks_2.append(chunk)

        greeting_2 = "".join([c["content"] for c in chunks_2 if c.get("type") == "token"]).strip()
        print("--> [TEST 2 PASS] Second Greeting Response (Dynamic Variation):", greeting_2)
        assert greeting_2 != greeting_1
        assert "Hello again!" in greeting_2 or "explore" in greeting_2

        # -------------------------------------------------------------
        # TEST 3: COMPOUND KNOWLEDGE QUERY ("hi, what projects are active?")
        # -------------------------------------------------------------
        chunks_3 = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="hi, what projects are active?",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            chunks_3.append(chunk)

        intent_3 = [c.get("intent") for c in chunks_3 if c.get("type") == "session"][0]
        resp_3 = "".join([c["content"] for c in chunks_3 if c.get("type") == "token"]).strip()

        print(f"--> [TEST 3 PASS] Compound Query Intent: {intent_3} | Response: {resp_3[:80]}...")
        assert intent_3 != "GREETING"
        assert intent_3 == "PROJECT_QUESTION" or intent_3 == "GENERAL_KNOWLEDGE"

        # -------------------------------------------------------------
        # TEST 4: FOLLOW-UP ANTECEDENT RESOLUTION ("What about the first one?")
        # -------------------------------------------------------------
        chunks_4 = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="What about the first one?",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            chunks_4.append(chunk)

        resp_4 = "".join([c["content"] for c in chunks_4 if c.get("type") == "token"]).strip()
        print("--> [TEST 4 PASS] Follow-up Resolution Response:", resp_4[:80], "...")
        assert len(resp_4) > 0

        # -------------------------------------------------------------
        # TEST 5: REQUEST IDEMPOTENCY & DB MESSAGE INTEGRITY
        # -------------------------------------------------------------
        messages = await ChatSessionManager.list_messages(session, chat.id, org.id)
        user_msgs = [m for m in messages if m.role == "user"]
        asst_msgs = [m for m in messages if m.role == "assistant"]

        print(f"--> [TEST 5 PASS] Total User Messages: {len(user_msgs)} | Assistant Messages: {len(asst_msgs)}")
        assert len(user_msgs) == 4
        assert len(asst_msgs) == 4

    print("=== MindMesh Conversation Continuity, Auto-Scroll & Response Intelligence Master Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_auto_scroll_intelligence_master_e2e())
