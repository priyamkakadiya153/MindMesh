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
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService
from app.knowledge.hub_service import KnowledgeHubService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_unified_knowledge_hub_e2e():
    print("=== Starting MindMesh Phase 3.0 Unified Knowledge Hub E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Hub Org A", slug=f"hub-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"hub-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"hub_usera_{uA_id}@mindmesh.com",
            username=f"hub_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"hub_userb_{uB_id}@mindmesh.com",
            username=f"hub_userb_{uB_id}",
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
        orgB = Organization(name="Hub Org B", slug=f"hub-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"hub-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"hub_userc_{uC_id}@mindmesh.com",
            username=f"hub_userc_{uC_id}",
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
        # Section 67 Required Master E2E Seeding
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
            file_content=b"Authentication Architecture Specification\n\nAccess tokens expire after 30 minutes.\nPostgreSQL is used for production.",
            filename="auth_hub_spec.txt",
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
            content="We should use PostgreSQL for production."
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
            content="I'll update the deployment configuration."
        )
        session.add(msg1)
        session.add(msg2)
        session.add(msg3)
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            project_id=project.id,
            description="Update deployment configuration",
            status="pending",
            assignee_id=userA.id
        )
        session.add(task)
        await session.commit()

        # Seed Timeline
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

        # Seed Knowledge Graph
        kg_service = KnowledgeGraphService(session)
        n_proj = await kg_service.get_or_create_node(orgA.id, "PROJECT", "project", project.id, "Authentication System", workspace_id=wsA.id, project_id=project.id)
        n_doc = await kg_service.get_or_create_node(orgA.id, "DOCUMENT", "document", doc.id, "Authentication Architecture", workspace_id=wsA.id, project_id=project.id)
        n_dec = await kg_service.get_or_create_node(orgA.id, "DECISION", "decision", conv_mem.id, "PostgreSQL selected for production", workspace_id=wsA.id, project_id=project.id)
        n_task = await kg_service.get_or_create_node(orgA.id, "TASK", "task", task.id, "Task: Update deployment configuration", workspace_id=wsA.id, project_id=project.id)

        await kg_service.create_edge(orgA.id, n_proj.id, n_doc.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_proj.id, n_task.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_dec.id, n_task.id, "RESULTED_IN")
        await session.commit()

        # Instantiate KnowledgeHubService
        hub_service = KnowledgeHubService(session)

        # -------------------------------------------------------------
        # Section 67 Verification Checks
        # -------------------------------------------------------------
        
        # 1. COUNTS & OVERVIEW TEST
        overview = await hub_service.get_hub_overview(userA, orgA.id, wsA.id)
        counts = overview["counts"]
        print("--> [HUB COUNTS PASS]", counts)
        assert counts["documents"] >= 1
        assert counts["decisions"] >= 1
        assert counts["tasks"] >= 1
        assert counts["conversations"] >= 1
        assert counts["projects"] >= 1

        # 2. RECENT KNOWLEDGE TEST
        recent = overview["recent_knowledge"]
        print("--> [HUB RECENT KNOWLEDGE PASS] Count:", len(recent))
        assert len(recent) >= 3

        # 3. PROJECT KNOWLEDGE OVERVIEW TEST
        proj_overview = await hub_service.get_project_knowledge_overview(userA, orgA.id, project.id)
        print("--> [HUB PROJECT OVERVIEW PASS]", proj_overview)
        assert proj_overview["name"] == "Authentication System"
        assert proj_overview["counts"]["documents"] >= 1
        assert proj_overview["counts"]["decisions"] >= 1

        # 4. ASK MINDSMESH REASONING TEST
        reasoner = MindMeshReasoner(session)
        ai_res = await reasoner.reason_and_answer(userA.id, orgA.id, "Why did we choose PostgreSQL?", wsA.id)
        print("--> [HUB ASK MINDSMESH PASS] Answer:", ai_res["answer"])
        assert len(ai_res["answer"]) > 0

        # 5. SECURITY ISOLATION TEST (Org B User C)
        overview_c = await hub_service.get_hub_overview(userC, orgB.id, wsB.id)
        print("--> [HUB SECURITY ORG B PASS] Counts:", overview_c["counts"])
        assert overview_c["counts"]["documents"] == 0
        assert overview_c["counts"]["decisions"] == 0
        assert len(overview_c["recent_knowledge"]) == 0

    print("=== MindMesh Phase 3.0 Unified Knowledge Hub E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_unified_knowledge_hub_e2e())
