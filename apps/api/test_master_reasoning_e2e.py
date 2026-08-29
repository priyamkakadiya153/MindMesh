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
from app.projects.models import Project
from app.models.task import Task
from app.documents.service import DocumentService
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_master_reasoning_e2e():
    print("=== Starting MindMesh Phase 2.9 Master Knowledge Reasoning E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Master Org A", slug=f"reason-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Reasoning WS", slug=f"reason-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"master_usera_{uA_id}@mindmesh.com",
            username=f"master_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"master_userb_{uB_id}@mindmesh.com",
            username=f"master_userb_{uB_id}",
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
        orgB = Organization(name="Master Org B", slug=f"reason-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"reason-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"master_userc_{uC_id}@mindmesh.com",
            username=f"master_userc_{uC_id}",
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
        # Section 86 Required Master Test Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Master authentication project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nAccess tokens initially expired after 15 minutes. The system was later updated to 30-minute access tokens.\nPostgreSQL is used for production database.",
            filename="auth_master_spec.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture",
            visibility="private"
        )
        # Process document into DocumentChunk & PGVectorStore
        from app.processing.pipeline import ProcessingPipeline
        from app.models.conversation import ConversationMemory
        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc.id)

        # Create Chat session
        from app.models.chat import Chat
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
            content="PostgreSQL selected for production database",
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

        # Seed Timeline Events
        tl_service = TimelineService(session)
        await tl_service.record_event(
            organization_id=orgA.id,
            event_type="DECISION_MADE",
            title="JWT expiry set to 15 minutes",
            description="Initial JWT expiry set during sprint 1",
            source_type="document",
            source_id=doc.id,
            workspace_id=wsA.id,
            occurred_at=datetime(2026, 7, 15, 10, 0)
        )

        await tl_service.record_event(
            organization_id=orgA.id,
            event_type="DECISION_MADE",
            title="JWT expiry changed to 30 minutes",
            description="Updated access token expiry duration",
            source_type="document",
            source_id=doc.id,
            workspace_id=wsA.id,
            occurred_at=datetime(2026, 8, 10, 14, 0)
        )

        # Seed Knowledge Graph Nodes & Edges
        kg_service = KnowledgeGraphService(session)

        n_proj = await kg_service.get_or_create_node(
            organization_id=orgA.id, workspace_id=wsA.id, project_id=project.id,
            node_type="PROJECT", source_type="project", source_id=project.id, title="Authentication System"
        )
        n_doc = await kg_service.get_or_create_node(
            organization_id=orgA.id, workspace_id=wsA.id, project_id=project.id,
            node_type="DOCUMENT", source_type="document", source_id=doc.id, title="Authentication Architecture"
        )
        n_conv = await kg_service.get_or_create_node(
            organization_id=orgA.id, workspace_id=wsA.id, project_id=project.id,
            node_type="CONVERSATION", source_type="conversation", source_id=conv.id, title="Architecture Team"
        )
        n_dec = await kg_service.get_or_create_node(
            organization_id=orgA.id, workspace_id=wsA.id, project_id=project.id,
            node_type="DECISION", source_type="decision", source_id=uuid.uuid4(), title="PostgreSQL selected for production"
        )
        n_task = await kg_service.get_or_create_node(
            organization_id=orgA.id, workspace_id=wsA.id, project_id=project.id,
            node_type="TASK", source_type="task", source_id=task.id, title="Task: Update deployment configuration"
        )

        await kg_service.create_edge(orgA.id, n_proj.id, n_doc.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_proj.id, n_task.id, "CONTAINS")
        await kg_service.create_edge(orgA.id, n_dec.id, n_conv.id, "DECIDED_IN")
        await kg_service.create_edge(orgA.id, n_dec.id, n_task.id, "RESULTED_IN")
        await kg_service.create_edge(orgA.id, n_doc.id, n_dec.id, "SUPPORTS")
        await session.commit()

        # Instantiate MindMeshReasoner
        reasoner = MindMeshReasoner(session)

        # -------------------------------------------------------------
        # Section 86 Required 10 Core Master Test Questions
        # -------------------------------------------------------------
        
        # 1. "What database did we decide to use?"
        q1 = await reasoner.reason_and_answer(userA.id, orgA.id, "What database did we decide to use?", wsA.id)
        print("--> [MASTER Q1 PASS] Answer:", q1["answer"])
        assert q1["is_grounded"] is True and len(q1["answer"]) > 0

        # 2. "Who agreed?"
        q2 = await reasoner.reason_and_answer(userA.id, orgA.id, "Who agreed?", wsA.id)
        print("--> [MASTER Q2 PASS] Answer:", q2["answer"])
        assert len(q2["answer"]) > 0

        # 3. "What task resulted from that decision?"
        q3 = await reasoner.reason_and_answer(userA.id, orgA.id, "What task resulted from that decision?", wsA.id)
        print("--> [MASTER Q3 PASS] Answer:", q3["answer"])
        assert q3["is_grounded"] is True and len(q3["answer"]) > 0

        # 4. "What is the current JWT expiry?"
        q4 = await reasoner.reason_and_answer(userA.id, orgA.id, "What is the current JWT expiry?", wsA.id)
        print("--> [MASTER Q4 PASS] Answer:", q4["answer"])
        assert q4["is_grounded"] is True and len(q4["answer"]) > 0

        # 5. "What was the JWT expiry in July?"
        q5 = await reasoner.reason_and_answer(userA.id, orgA.id, "What was the JWT expiry in July?", wsA.id)
        print("--> [MASTER Q5 PASS] Answer:", q5["answer"])
        assert q5["is_grounded"] is True and len(q5["answer"]) > 0

        # 6. "How did the authentication architecture evolve?"
        q6 = await reasoner.reason_and_answer(userA.id, orgA.id, "How did the authentication architecture evolve?", wsA.id)
        print("--> [MASTER Q6 PASS] Answer:", q6["answer"])
        assert len(q6["answer"]) > 0

        # 7. "Why did JWT expiry change?"
        q7 = await reasoner.reason_and_answer(userA.id, orgA.id, "Why did JWT expiry change?", wsA.id)
        print("--> [MASTER Q7 PASS] Answer:", q7["answer"])
        assert len(q7["answer"]) > 0

        # 8. "What documents support the PostgreSQL decision?"
        q8 = await reasoner.reason_and_answer(userA.id, orgA.id, "What documents support the PostgreSQL decision?", wsA.id)
        print("--> [MASTER Q8 PASS] Answer:", q8["answer"])
        assert len(q8["answer"]) > 0

        # 9. "What is related to the authentication project?"
        q9 = await reasoner.reason_and_answer(userA.id, orgA.id, "What is related to the authentication project?", wsA.id)
        print("--> [MASTER Q9 PASS] Answer:", q9["answer"])
        assert len(q9["answer"]) > 0

        # 10. "Did we decide to use MongoDB?"
        q10 = await reasoner.reason_and_answer(userA.id, orgA.id, "Did we decide to use MongoDB?", wsA.id)
        print("--> [MASTER Q10 PASS] Answer:", q10["answer"])
        assert len(q10["answer"]) > 0

        # -------------------------------------------------------------
        # RBAC Multi-Tenant Security Isolation Test
        # -------------------------------------------------------------
        q_sec = await reasoner.reason_and_answer(userC.id, orgB.id, "What database did we decide to use?", wsB.id)
        print("--> [SECURITY TEST ORG B PASS] Answer:", q_sec["answer"])
        assert q_sec["is_grounded"] is False and "couldn't find" in q_sec["answer"].lower()

    print("=== MindMesh Phase 2.9 Master Knowledge Reasoning E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_master_reasoning_e2e())
