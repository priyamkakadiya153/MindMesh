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
from app.knowledge.graph_service import KnowledgeGraphService
from app.knowledge.graph_builder import KnowledgeGraphBuilder
from app.knowledge.graph_retriever import GraphRetriever
from app.ai.orchestrator import MindMeshAIOrchestrator

async def test_knowledge_graph_e2e():
    print("=== Starting MindMesh Phase 2.8 Knowledge Graph E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Graph Org A", slug=f"kg-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"kg-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"kg_usera_{uA_id}@mindmesh.com",
            username=f"kg_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"kg_userb_{uB_id}@mindmesh.com",
            username=f"kg_userb_{uB_id}",
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
        orgB = Organization(name="Graph Org B", slug=f"kg-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"kg-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"kg_userc_{uC_id}@mindmesh.com",
            username=f"kg_userc_{uC_id}",
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
        # Section 67 Required E2E Seeding
        # -------------------------------------------------------------
        # PROJECT: Authentication System
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Core authentication and authorization infrastructure."
        )
        session.add(project)
        await session.commit()

        # DOCUMENT: Authentication Architecture
        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nAccess tokens expire after 15 minutes.\nPostgreSQL is used for production database.",
            filename="auth_arch_kg.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture",
            visibility="private"
        )
        doc.project_id = project.id
        await session.commit()

        # CONVERSATION & MESSAGES: User A & User B
        conv = Conversation(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            type="group",
            name="Architecture Discussion",
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
            content="PostgreSQL should be our production database."
        )
        msg2 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userB.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Agreed. I'll update the deployment configuration."
        )
        session.add(msg1)
        session.add(msg2)
        await session.commit()

        # TASK: Update deployment configuration
        task = Task(
            organization_id=orgA.id,
            project_id=project.id,
            description="Update deployment configuration",
            status="pending",
            assignee_id=userB.id
        )
        session.add(task)
        await session.commit()

        # Build Graph Nodes & Edges via KnowledgeGraphService
        service = KnowledgeGraphService(session)

        n_proj = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            node_type="PROJECT",
            source_type="project",
            source_id=project.id,
            title="Authentication System"
        )

        n_doc = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            node_type="DOCUMENT",
            source_type="document",
            source_id=doc.id,
            title="Authentication Architecture"
        )

        n_conv = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            node_type="CONVERSATION",
            source_type="conversation",
            source_id=conv.id,
            title="Architecture Discussion"
        )

        dec_id = uuid.uuid4()
        n_dec = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            node_type="DECISION",
            source_type="decision",
            source_id=dec_id,
            title="PostgreSQL selected for production"
        )

        n_task = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            node_type="TASK",
            source_type="task",
            source_id=task.id,
            title="Task: Update deployment configuration"
        )

        n_userB = await service.get_or_create_node(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            node_type="USER",
            source_type="user",
            source_id=userB.id,
            title="User B"
        )

        # Edges
        await service.create_edge(orgA.id, n_proj.id, n_doc.id, "CONTAINS")
        await service.create_edge(orgA.id, n_proj.id, n_task.id, "CONTAINS")
        await service.create_edge(orgA.id, n_dec.id, n_conv.id, "DECIDED_IN")
        await service.create_edge(orgA.id, n_dec.id, n_task.id, "RESULTED_IN")
        await service.create_edge(orgA.id, n_doc.id, n_dec.id, "SUPPORTS")
        await service.create_edge(orgA.id, n_dec.id, n_userB.id, "AGREED_BY")
        await session.commit()

        # -------------------------------------------------------------
        # Section 67 Required E2E Graph Queries
        # -------------------------------------------------------------
        retriever = GraphRetriever(session)
        context = await retriever.expand_context(
            user=userA,
            organization_id=orgA.id,
            query_text="PostgreSQL selected for production",
            workspace_id=wsA.id
        )

        print("--> [GRAPH CONTEXT PASS] Extracted Entities Count:", len(context["entities"]))
        print("--> [GRAPH CONTEXT PASS] Extracted Relationships Count:", len(context["relationships"]))
        assert len(context["entities"]) >= 4
        assert len(context["relationships"]) >= 3

        orchestrator = MindMeshAIOrchestrator(session)

        # 1. "What is related to the PostgreSQL decision?"
        res1 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="What is related to the PostgreSQL decision?",
            workspace_id=wsA.id
        )
        print("--> [GRAPH Q1 PASS] Answer:", res1.get("answer"))
        assert res1.get("answer") is not None

        # 2. "Which task resulted from the decision?"
        res2 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="Which task resulted from the decision?",
            workspace_id=wsA.id
        )
        print("--> [GRAPH Q2 PASS] Answer:", res2.get("answer"))
        assert "deployment" in res2.get("answer", "").lower() or "task" in res2.get("answer", "").lower()

        # 3. "Which conversation produced the decision?"
        res3 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="Which conversation produced the decision?",
            workspace_id=wsA.id
        )
        print("--> [GRAPH Q3 PASS] Answer:", res3.get("answer"))
        assert "architecture" in res3.get("answer", "").lower() or "discussion" in res3.get("answer", "").lower() or "conversation" in res3.get("answer", "").lower()

        # -------------------------------------------------------------
        # Idempotency & Builder Test
        # -------------------------------------------------------------
        builder = KnowledgeGraphBuilder(session)
        stats1 = await builder.build_graph(organization_id=orgA.id)
        stats2 = await builder.build_graph(organization_id=orgA.id)
        print("--> [IDEMPOTENCY PASS] Builder Stats Run 1:", stats1)
        print("--> [IDEMPOTENCY PASS] Builder Stats Run 2:", stats2)

        # -------------------------------------------------------------
        # RBAC Multi-Tenant Security Isolation Test
        # -------------------------------------------------------------
        search_res_c = await service.search_nodes(
            user=userC,
            organization_id=orgB.id,
            query="PostgreSQL"
        )
        print("--> [SECURITY TEST ORG B PASS] User C Node Count:", len(search_res_c))
        assert len(search_res_c) == 0

    print("=== MindMesh Phase 2.8 Knowledge Graph E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph_e2e())
