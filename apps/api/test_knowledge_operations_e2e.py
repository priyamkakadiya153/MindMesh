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
from app.governance.service import GovernanceService
from app.operations.service import KnowledgeOperationsService

async def test_knowledge_operations_e2e():
    print("=== Starting MindMesh Phase 3.7 Knowledge Operations & Memory Insights E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Ops Org A", slug=f"ops-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Ops Workspace", slug=f"ops-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"ops_usera_{uA_id}@mindmesh.com",
            username=f"ops_usera_{uA_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Ops Org B", slug=f"ops-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"ops-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"ops_userc_{uC_id}@mindmesh.com",
            username=f"ops_userc_{uC_id}",
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
        # Section 86 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-ops-{uuid.uuid4().hex[:6]}",
            description="Core authentication ops project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc1 = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJWT expiry set to 30m.",
            filename="auth_arch.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture Specification",
            visibility="private"
        )
        doc1.project_id = project.id

        doc2 = await doc_service.upload_document(
            file_content=b"Deployment Guide\n\nDeployment procedures for authentication microservices.",
            filename="deploy_guide.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Deployment Guide",
            visibility="private"
        )
        doc2.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc1.id)
        await proc_job.process_document(doc2.id)

        chat1 = Chat(organization_id=orgA.id, workspace_id=wsA.id, user_id=userA.id, title="Chat 1")
        chat2 = Chat(organization_id=orgA.id, workspace_id=wsA.id, user_id=userA.id, title="Chat 2")
        session.add(chat1)
        session.add(chat2)
        await session.commit()

        dec1 = ConversationMemory(
            chat_id=chat1.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            memory_type="decision",
            content="PostgreSQL selected for production DB",
            importance=5
        )
        dec2 = ConversationMemory(
            chat_id=chat2.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            memory_type="decision",
            content="JWT expiry selected as 30 minutes",
            importance=5
        )
        session.add(dec1)
        session.add(dec2)
        await session.commit()

        # Seed 5 Tasks
        tasks = []
        for i in range(1, 6):
            t = Task(
                organization_id=orgA.id,
                workspace_id=wsA.id,
                project_id=project.id,
                title=f"Ops Task {i}",
                description=f"Description for Ops Task {i}",
                status="BLOCKED" if i == 1 else "OPEN",
                priority="HIGH" if i == 1 else "NORMAL"
            )
            tasks.append(t)
            session.add(t)
        await session.commit()

        gov_service = GovernanceService(session)
        await gov_service.verify_knowledge("DECISION", dec1.id, userA, orgA.id)

        ops_service = KnowledgeOperationsService(session)

        # -------------------------------------------------------------
        # Section 86 Verification Checks
        # -------------------------------------------------------------

        # 1. KNOWLEDGE HEALTH TEST
        health = await ops_service.get_knowledge_health(orgA.id, wsA.id)
        print("--> [1. KNOWLEDGE HEALTH PASS]", health)
        assert health["total_documents"] == 2
        assert health["total_tasks"] == 5
        assert health["verified_knowledge"] == 1

        # 2. PROJECT COVERAGE TEST
        coverage = await ops_service.get_project_coverage(orgA.id, wsA.id)
        print("--> [2. PROJECT COVERAGE PASS]", coverage)
        assert len(coverage) == 1
        assert coverage[0]["document_count"] == 2
        assert coverage[0]["decision_count"] == 2
        assert coverage[0]["task_count"] == 5

        # 3. KNOWLEDGE GAP DETECTION TEST
        gaps = await ops_service.detect_knowledge_gaps(orgA.id, wsA.id)
        print("--> [3. KNOWLEDGE GAPS PASS] Count:", len(gaps), "| Gaps:", [g["title"] for g in gaps])
        assert len(gaps) >= 1

        # 4. PROJECT HANDOFF BRIEF TEST
        handoff = await ops_service.generate_project_handoff(project.id, userA, orgA.id)
        print("--> [4. PROJECT HANDOFF PASS] Project Name:", handoff["project_name"], "| Key Decisions:", len(handoff["key_decisions"]))
        assert handoff["project_name"] == "Authentication System"
        assert len(handoff["key_decisions"]) == 2
        assert len(handoff["active_tasks"]) == 5
        assert len(handoff["reference_documents"]) == 2

        # 5. SECURITY ISOLATION TEST (Org B User C)
        handoff_orgB = await ops_service.generate_project_handoff(project.id, userC, orgB.id)
        print("--> [5. SECURITY ISOLATION PASS] Org B Handoff:", handoff_orgB)
        assert handoff_orgB is None

        # 6. ANTI-SURVEILLANCE DEFENSE TEST
        assert "employee_scores" not in health
        assert "productivity_rankings" not in health
        print("--> [6. ANTI-SURVEILLANCE PASS] Zero employee tracking metrics present.")

    print("=== MindMesh Phase 3.7 Knowledge Operations & Memory Insights E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_operations_e2e())
