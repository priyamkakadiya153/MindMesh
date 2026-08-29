import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.ai.chat.session import ChatSessionManager
from app.copilot.grounded_service import GroundedAnswerEngineService

async def test_ai_chat_intelligence_master_e2e():
    print("=== Starting MindMesh AI Chat Intelligence Hardening & Response Quality E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="AI Chat Org", slug=f"chat-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="AI Chat Workspace", slug=f"chat-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"chat_user_{u_id}@mindmesh.com",
            username=f"chat_user_{u_id}",
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
        copilot_service = GroundedAnswerEngineService(session)

        # -------------------------------------------------------------
        # TEST 1: GREETING INTENT (Natural response, zero debug text)
        # -------------------------------------------------------------
        chat = await ChatSessionManager.create_conversation(session, org.id, user.id, ws.id, "Greeting Test")
        await session.commit()

        chunks = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="hi",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            chunks.append(chunk)

        greeting_tokens = [c["content"] for c in chunks if c.get("type") == "token"]
        greeting_text = "".join(greeting_tokens).strip()

        print("--> [1. GREETING INTENT PASS] Response:", greeting_text)
        assert "RETRIEVED KNOWLEDGE CONTEXT" not in greeting_text
        assert "Verified against PostgreSQL document chunks" not in greeting_text
        assert "Hi!" in greeting_text or "help" in greeting_text

        # -------------------------------------------------------------
        # TEST 2: IDEMPOTENCY & ZERO MESSAGE DUPLICATION
        # -------------------------------------------------------------
        # Save user message first (simulating frontend createMessage)
        await ChatSessionManager.save_user_message(session, chat.id, user.id, org.id, "What is the project deadline?")
        await session.commit()

        # Execute stream (simulating frontend streamChatMessage)
        async for _ in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the project deadline?",
            conversation_id=chat.id,
            workspace_id=ws.id
        ):
            pass

        messages = await ChatSessionManager.list_messages(session, chat.id, org.id)
        user_msgs = [m for m in messages if m.role == "user" and m.content == "What is the project deadline?"]

        print(f"--> [2. ZERO MESSAGE DUPLICATION PASS] Total identical user messages in DB: {len(user_msgs)}")
        assert len(user_msgs) == 1

        # -------------------------------------------------------------
        # TEST 3: NO-CONTEXT NATURAL ANSWER
        # -------------------------------------------------------------
        no_ctx_resp = await copilot_service.ask_mindmesh(
            question="What is the status of non-existent project XYZ?",
            user=user,
            organization_id=org.id,
            workspace_id=ws.id
        )

        print("--> [3. NO-CONTEXT NATURAL ANSWER PASS] Direct Answer:", no_ctx_resp["direct_answer"])
        assert "RETRIEVED KNOWLEDGE CONTEXT" not in no_ctx_resp["direct_answer"]
        assert "PostgreSQL" not in no_ctx_resp["direct_answer"]
        assert "couldn't find" in no_ctx_resp["direct_answer"].lower() or "insufficient" in no_ctx_resp["direct_answer"].lower()

        # -------------------------------------------------------------
        # TEST 4: CONVERSATION RELOAD CONSISTENCY
        # -------------------------------------------------------------
        reloaded_messages = await ChatSessionManager.list_messages(session, chat.id, org.id)
        print("--> [4. CONVERSATION RELOAD PASS] Total messages loaded:", len(reloaded_messages))
        assert len(reloaded_messages) > 1

    print("=== MindMesh AI Chat Intelligence Hardening E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_ai_chat_intelligence_master_e2e())
