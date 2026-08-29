import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace
from app.ai.orchestrator import MindMeshAIOrchestrator
from sqlalchemy import select

async def test_orchestrator():
    print("--- Starting MindMesh Phase 2.1 AI Orchestrator Test ---")

    async with AsyncSessionLocal() as session:
        # Create test user, org, workspace
        org = Organization(name="Orchestrator Test Org", slug=f"orch-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Orchestrator Workspace", slug=f"orch-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"orch_user_{u_id}@mindmesh.com",
            username=f"orch_user_{u_id}",
            first_name="Orchestrator",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        from app.models.organization_member import OrganizationMember
        from app.workspace.models import WorkspaceMember
        mem = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="admin"
        )
        session.add(mem)
        ws_mem = WorkspaceMember(
            workspace_id=ws.id,
            user_id=user.id,
            role="admin"
        )
        session.add(ws_mem)
        await session.commit()

        # 1. Test Intent Classification
        orchestrator = MindMeshAIOrchestrator(session)
        assert orchestrator.classify_intent("What did we decide about JWT tokens?") == "DECISION"
        assert orchestrator.classify_intent("Summarize recent discussions") == "SUMMARY"
        assert orchestrator.classify_intent("Where is the architecture document?") == "DOCUMENT_QUESTION"
        assert orchestrator.classify_intent("What tasks are pending?") == "TASK"
        print("--> Verified Intent Classification (DECISION, SUMMARY, DOCUMENT_QUESTION, TASK).")

        # 2. Test Execution Flow
        query = "What is MindMesh Knowledge Engine?"
        res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query=query,
            workspace_id=ws.id,
            provider="gemini",
            model="gemini-2.5-flash"
        )

        assert "answer" in res
        assert "citations" in res
        assert "confidence" in res
        assert "grounded" in res
        assert "intent" in res
        assert res["answer"] != ""
        print(f"--> Verified Orchestrator Execution (Intent: {res['intent']}, Grounded: {res['grounded']}).")

        # 3. Test Streaming Execution Flow
        stream_chunks = []
        async for chunk in orchestrator.stream_execute(
            user_id=user.id,
            org_id=org.id,
            query="Tell me about project decisions",
            workspace_id=ws.id
        ):
            stream_chunks.append(chunk)

        assert len(stream_chunks) > 0
        assert stream_chunks[0]["type"] == "session"
        assert stream_chunks[-1]["type"] == "final"
        print("--> Verified Orchestrator SSE Streaming Flow.")

    print("=== MindMesh Phase 2.1 AI Orchestrator Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
