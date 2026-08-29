import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.me.service import UserContextService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_user_context_e2e():
    print("=== Starting MindMesh Phase 3.4 Personal Knowledge Memory & User Context E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Organization & Workspaces
        orgA = Organization(name="UserContext Org", slug=f"uc-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsEng = Workspace(organization_id=orgA.id, name="Engineering", slug=f"eng-{uuid.uuid4().hex[:6]}")
        wsMkt = Workspace(organization_id=orgA.id, name="Marketing", slug=f"mkt-{uuid.uuid4().hex[:6]}")
        session.add(wsEng)
        session.add(wsMkt)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"priyam_{uA_id}@mindmesh.com",
            username=f"priyam_{uA_id}",
            first_name="Priyam",
            last_name="Patel",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"userb_{uB_id}@mindmesh.com",
            username=f"userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=orgA.id, user_id=userB.id, role="member", is_active=True))

        session.add(WorkspaceMember(workspace_id=wsEng.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsEng.id, user_id=userB.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsMkt.id, user_id=userA.id, role="member", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 83 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsEng.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Core authentication project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJWT access tokens configured for 15 minutes.",
            filename="auth_architecture.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsEng.id,
            user_id=userA.id,
            title="Authentication Architecture",
            visibility="private"
        )
        doc.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc.id)

        chat = Chat(
            organization_id=orgA.id,
            workspace_id=wsEng.id,
            user_id=userA.id,
            title="Architecture Discussion"
        )
        session.add(chat)
        await session.commit()

        conv_mem = ConversationMemory(
            chat_id=chat.id,
            organization_id=orgA.id,
            workspace_id=wsEng.id,
            project_id=project.id,
            memory_type="decision",
            content="PostgreSQL selected for production",
            importance=5
        )
        session.add(conv_mem)
        await session.commit()

        # Task 1 assigned to User A (Priyam)
        t1 = Task(
            organization_id=orgA.id,
            workspace_id=wsEng.id,
            project_id=project.id,
            title="Update deployment configuration",
            description="Priyam, please update the deployment configuration by Friday.",
            status="TODO",
            due_date=datetime.utcnow() - timedelta(days=1),
            assignee_id=userA.id,
            decision_id=conv_mem.id
        )
        session.add(t1)
        await session.commit()

        ctx_service = UserContextService(session)

        # -------------------------------------------------------------
        # Section 83 Verification Checks
        # -------------------------------------------------------------

        # 1. MY WORK USER CONTEXT TEST (User A)
        ctxA = await ctx_service.get_user_context(userA, orgA.id, wsEng.id)
        print("--> [1. MY WORK PASS - User A] Tasks count:", len(ctxA["my_tasks"]), "| Projects count:", len(ctxA["my_projects"]))
        assert len(ctxA["my_tasks"]) >= 1
        assert ctxA["my_tasks"][0]["title"] == "Update deployment configuration"
        assert len(ctxA["my_projects"]) >= 1
        assert ctxA["my_projects"][0]["name"] == "Authentication System"

        # 2. ZERO LEAKAGE TEST (User B Context)
        ctxB = await ctx_service.get_user_context(userB, orgA.id, wsEng.id)
        print("--> [2. ZERO LEAKAGE PASS - User B] Tasks count:", len(ctxB["my_tasks"]))
        assert len(ctxB["my_tasks"]) == 0

        # 3. CATCH ME UP SUMMARY TEST
        catch_up = await ctx_service.get_catch_up_summary(userA, orgA.id, wsEng.id, project.id)
        print("--> [3. CATCH ME UP PASS] Summary:", catch_up["summary"])
        assert len(catch_up["summary"]) > 0

        # 4. WORKSPACE SWITCH TEST (User A in Marketing workspace)
        ctx_mkt = await ctx_service.get_user_context(userA, orgA.id, wsMkt.id)
        print("--> [4. WORKSPACE SWITCH PASS] Marketing Tasks count:", len(ctx_mkt["my_tasks"]))
        assert len(ctx_mkt["my_tasks"]) == 0

        # 5. ASK MINDSMESH GROUNDED PERSONAL REASONING TEST
        reasoner = MindMeshReasoner(session)
        ai_res1 = await reasoner.reason_and_answer(userA.id, orgA.id, "What should I work on next?", wsEng.id)
        print("--> [5. ASK MINDSMESH NEXT WORK PASS] Answer:", ai_res1["answer"])
        assert len(ai_res1["answer"]) > 0

        ai_res2 = await reasoner.reason_and_answer(userA.id, orgA.id, "Why is the deployment task relevant to me?", wsEng.id)
        print("--> [5. ASK MINDSMESH RELEVANCE PASS] Answer:", ai_res2["answer"])
        assert len(ai_res2["answer"]) > 0

    print("=== MindMesh Phase 3.4 Personal Knowledge Memory & User Context E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_user_context_e2e())
