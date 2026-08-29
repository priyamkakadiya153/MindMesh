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
from app.intelligence.service import ProactiveIntelligenceService
from app.models.intelligence_signal import IntelligenceSignal
from app.ai.reasoner.engine import MindMeshReasoner

async def test_proactive_intelligence_e2e():
    print("=== Starting MindMesh Phase 3.3 Proactive Knowledge & Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Proactive Org A", slug=f"pro-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"pro-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"pro_usera_{uA_id}@mindmesh.com",
            username=f"pro_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"pro_userb_{uB_id}@mindmesh.com",
            username=f"pro_userb_{uB_id}",
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
        orgB = Organization(name="Proactive Org B", slug=f"pro-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"pro-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"pro_userc_{uC_id}@mindmesh.com",
            username=f"pro_userc_{uC_id}",
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
        # Section 89 Master E2E Seeding
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
        docA = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJWT expiry is 15 minutes.",
            filename="auth_spec_a.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture Specification",
            visibility="private"
        )
        docA.project_id = project.id

        docB = await doc_service.upload_document(
            file_content=b"Authentication Update Specification\n\nJWT expiry is now 30 minutes.",
            filename="auth_spec_b.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Update Specification",
            visibility="private"
        )
        docB.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(docA.id)
        await proc_job.process_document(docB.id)

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

        # Task 1: Overdue Task
        t1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Update deployment configuration",
            description="Update deployment configuration by Friday.",
            status="TODO",
            due_date=datetime.utcnow() - timedelta(days=2),
            assignee_id=userA.id,
            decision_id=conv_mem.id
        )
        # Task 2: Blocked Task
        t2 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Deploy authentication service",
            description="Deploy auth service to prod cluster.",
            status="BLOCKED",
            blocked_reason="Waiting for API specification."
        )
        session.add(t1)
        session.add(t2)
        await session.commit()

        # Instantiate ProactiveIntelligenceService
        intel_service = ProactiveIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 89 Verification Checks
        # -------------------------------------------------------------

        # 1. SIGNAL SCANNING & GENERATION TEST
        signals = await intel_service.get_important_signals_for_user(userA, orgA.id, wsA.id)
        print("--> [1. PROACTIVE SIGNALS PASS] Active Count:", len(signals))
        for s in signals:
            print(f"    - [{s['signal_type']}] Priority: {s['priority']} | Title: {s['title']}")

        assert len(signals) >= 3
        signal_types = [s["signal_type"] for s in signals]
        assert "OVERDUE_TASK" in signal_types
        assert "BLOCKED_TASK" in signal_types
        assert "NEW_DECISION" in signal_types

        # 2. IDEMPOTENCY & DEDUPLICATION TEST
        count_before = len(signals)
        await intel_service.scan_and_generate_signals(orgA.id, wsA.id)
        signals_after = await intel_service.get_important_signals_for_user(userA, orgA.id, wsA.id)
        print("--> [2. DEDUPLICATION PASS] Before:", count_before, "| After:", len(signals_after))
        assert len(signals_after) == count_before

        # 3. SIGNAL RESOLUTION TEST (Unblock Task 2)
        t2.status = "IN_PROGRESS"
        await session.commit()
        signals_resolved = await intel_service.get_important_signals_for_user(userA, orgA.id, wsA.id)
        res_types = [s["signal_type"] for s in signals_resolved]
        print("--> [3. SIGNAL RESOLUTION PASS] Remaining active types:", res_types)
        assert "BLOCKED_TASK" not in res_types

        # 4. ASK MINDSMESH REASONING TEST
        reasoner = MindMeshReasoner(session)
        ai_res = await reasoner.reason_and_answer(userA.id, orgA.id, "Why is the authentication project receiving attention?", wsA.id)
        print("--> [4. ASK MINDSMESH PROACTIVE PASS] Answer:", ai_res["answer"])
        assert len(ai_res["answer"]) > 0

        # 5. SECURITY ISOLATION TEST (Org B User C)
        sec_signals = await intel_service.get_important_signals_for_user(userC, orgB.id, wsB.id)
        print("--> [5. SECURITY PASS] Org B Signal Count:", len(sec_signals))
        assert len(sec_signals) == 0

    print("=== MindMesh Phase 3.3 Proactive Knowledge & Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_proactive_intelligence_e2e())
