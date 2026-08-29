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
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.projects.intelligence_service import ProjectIntelligenceService
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_project_intelligence_e2e():
    print("=== Starting MindMesh Phase 3.2 Project Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS title VARCHAR;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR DEFAULT 'TASK';"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR DEFAULT 'MEDIUM';"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workspace_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_type VARCHAR;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS decision_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS conversation_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS message_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS document_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_by UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_ai_extracted BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blocked_reason VARCHAR;"))

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Proj Org A", slug=f"proj-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"proj-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"proj_usera_{uA_id}@mindmesh.com",
            username=f"proj_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"proj_userb_{uB_id}@mindmesh.com",
            username=f"proj_userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=orgA.id, user_id=userB.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userB.id, role="member", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Proj Org B", slug=f"proj-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"proj-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"proj_userc_{uC_id}@mindmesh.com",
            username=f"proj_userc_{uC_id}",
            first_name="User",
            last_name="C",
            hashed_password="mockpassword",
            phone_number=f"+1555{uC_id}"
        )
        session.add(userC)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userC.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userC.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 74 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Core authentication project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJWT access tokens were initially configured for 15 minutes.\nPostgreSQL is used for production.",
            filename="auth_proj_spec.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
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
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Architecture Discussion"
        )
        session.add(chat)
        await session.commit()

        conv_mem = ConversationMemory(
            chat_id=chat.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            memory_type="decision",
            content="PostgreSQL selected for production",
            importance=5
        )
        session.add(conv_mem)
        await session.commit()

        conv = Conversation(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            type="group",
            name="Architecture Team",
            visibility="private"
        )
        session.add(conv)
        await session.commit()

        session.add(ConversationMember(conversation_id=conv.id, user_id=userA.id, role="admin"))
        session.add(ConversationMember(conversation_id=conv.id, user_id=userB.id, role="member"))
        await session.commit()

        msg1 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userA.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Let's use PostgreSQL for production."
        )
        msg2 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userB.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Agreed."
        )
        msg3 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userA.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Priyam, update the deployment configuration by Friday."
        )
        session.add(msg1)
        session.add(msg2)
        session.add(msg3)
        await session.commit()

        # Task 1: Open
        t1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Update deployment configuration",
            description="Update deployment configuration by Friday.",
            status="TODO",
            assignee_id=userA.id,
            decision_id=conv_mem.id
        )
        # Task 2: Blocked
        t2 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Implement token rotation",
            description="Implement refresh token rotation.",
            status="BLOCKED",
            blocked_reason="Waiting for API specification."
        )
        # Task 3: Completed
        t3 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Update authentication documentation",
            description="Update architecture docs.",
            status="COMPLETED",
            completed_at=datetime.utcnow()
        )
        session.add(t1)
        session.add(t2)
        session.add(t3)
        await session.commit()

        # Timeline Event
        tl_service = TimelineService(session)
        await tl_service.record_event(
            organization_id=orgA.id,
            event_type="DECISION_MADE",
            title="PostgreSQL selected for production",
            description="Architecture decision",
            source_type="conversation",
            source_id=conv.id,
            workspace_id=wsA.id,
            project_id=project.id,
            occurred_at=datetime.utcnow()
        )

        # Knowledge Graph
        kg_service = KnowledgeGraphService(session)
        n_proj = await kg_service.get_or_create_node(orgA.id, "PROJECT", "project", project.id, "Authentication System", workspace_id=wsA.id, project_id=project.id)
        n_doc = await kg_service.get_or_create_node(orgA.id, "DOCUMENT", "document", doc.id, "Authentication Architecture", workspace_id=wsA.id, project_id=project.id)
        n_dec = await kg_service.get_or_create_node(orgA.id, "DECISION", "decision", conv_mem.id, "PostgreSQL selected for production", workspace_id=wsA.id, project_id=project.id)
        n_t1 = await kg_service.get_or_create_node(orgA.id, "TASK", "task", t1.id, "Task: Update deployment configuration", workspace_id=wsA.id, project_id=project.id)

        await kg_service.create_edge(orgA.id, n_proj.id, n_doc.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_proj.id, n_t1.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_dec.id, n_t1.id, "RESULTED_IN")
        await session.commit()

        # Instantiate ProjectIntelligenceService
        intel_service = ProjectIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 74 Verification Checks
        # -------------------------------------------------------------

        # 1. PROJECT INTELLIGENCE TEST
        res = await intel_service.get_project_intelligence(project.id, orgA.id, userA)
        print("--> [PROJECT INTEL PASS] Health:", res["health"])
        print("--> [PROJECT INTEL PASS] Task Summary:", res["task_summary"])
        print("--> [PROJECT INTEL PASS] Current State:", res["current_state"])

        assert res["name"] == "Authentication System"
        assert res["health"]["status"] in ["ATTENTION", "AT_RISK"]
        assert "blocked" in res["health"]["explanation"].lower()
        assert res["task_summary"]["blocked"] == 1
        assert res["task_summary"]["completed"] == 1
        assert len(res["key_decisions"]) >= 1

        # 2. ASK MINDSMESH REASONING TEST
        reasoner = MindMeshReasoner(session)
        ai_res1 = await reasoner.reason_and_answer(userA.id, orgA.id, "Why is the authentication project flagged for attention?", wsA.id)
        print("--> [ASK MINDSMESH ATTENTION PASS] Answer:", ai_res1["answer"])
        assert len(ai_res1["answer"]) > 0

        ai_res2 = await reasoner.reason_and_answer(userA.id, orgA.id, "What should we focus on next in authentication?", wsA.id)
        print("--> [ASK MINDSMESH NEXT FOCUS PASS] Answer:", ai_res2["answer"])
        assert len(ai_res2["answer"]) > 0

        # 3. SECURITY ISOLATION TEST (Org B User C)
        sec_res = await intel_service.get_project_intelligence(project.id, orgB.id, userC)
        print("--> [SECURITY PASS] Org B result:", sec_res)
        assert "error" in sec_res

    print("=== MindMesh Phase 3.2 Project Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_project_intelligence_e2e())
