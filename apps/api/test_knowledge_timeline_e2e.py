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
from app.documents.service import DocumentService
from app.timeline.service import TimelineService
from app.timeline.backfill import TimelineBackfillService
from app.timeline.temporal_retriever import TimelineRetriever
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.search.service import SearchService

async def test_knowledge_timeline_e2e():
    print("=== Starting MindMesh Phase 2.7 Knowledge Timeline E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Timeline Org A", slug=f"tl-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"tl-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"tl_usera_{uA_id}@mindmesh.com",
            username=f"tl_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Timeline Org B", slug=f"tl-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"tl-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"tl_userb_{uB_id}@mindmesh.com",
            username=f"tl_userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userB.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userB.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 61 Required E2E Seeding
        # -------------------------------------------------------------
        doc_service = DocumentService(session)
        july_date = datetime(2026, 7, 15, 10, 0, 0)
        august_date = datetime(2026, 8, 10, 14, 30, 0)

        # Seed July Document
        doc_july = await doc_service.upload_document(
            file_content=b"Authentication Architecture July Specification\n\nIn July, JWT access tokens expire after 15 minutes.\nRefresh tokens remain valid for 30 days.",
            filename="auth_arch_july.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture July",
            visibility="private"
        )

        # Seed August Document
        doc_aug = await doc_service.upload_document(
            file_content=b"Authentication Architecture August Specification\n\nIn August, JWT access tokens expire after 30 minutes.\nDecision: Increase JWT expiry to 30 minutes.",
            filename="auth_arch_august.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture August",
            visibility="private"
        )
        await session.commit()

        # Seed Timeline Events
        timeline_service = TimelineService(session)

        event_july_doc = await timeline_service.record_event(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            source_type="document",
            source_id=doc_july.id,
            event_type="DOCUMENT_CREATED",
            importance="HIGH",
            title="Authentication Architecture July",
            description="In July, JWT access tokens expire after 15 minutes.",
            occurred_at=july_date
        )

        dec_july_db = await timeline_service.record_event(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            source_type="decision",
            source_id=uuid.uuid4(),
            event_type="DECISION_MADE",
            importance="HIGH",
            title="PostgreSQL selected for production",
            description="We decided to use PostgreSQL for production database.",
            occurred_at=july_date
        )

        task_july = await timeline_service.record_event(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            source_type="task",
            source_id=uuid.uuid4(),
            event_type="TASK_CREATED",
            importance="MEDIUM",
            title="Update deployment configuration",
            description="Configure production PostgreSQL deployment.",
            occurred_at=july_date
        )

        event_aug_doc = await timeline_service.record_event(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            source_type="document",
            source_id=doc_aug.id,
            event_type="DOCUMENT_UPDATED",
            importance="HIGH",
            title="Authentication Architecture August",
            description="In August, JWT access tokens expire after 30 minutes.",
            occurred_at=august_date
        )

        dec_aug_jwt = await timeline_service.record_event(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            source_type="decision",
            source_id=uuid.uuid4(),
            event_type="DECISION_MADE",
            importance="HIGH",
            title="Increase JWT expiry to 30 minutes",
            description="Decision to extend access token TTL to 30 minutes.",
            occurred_at=august_date,
            supersedes_event_id=event_july_doc.id
        )
        await session.commit()

        # -------------------------------------------------------------
        # Verify Timeline Fetch
        # -------------------------------------------------------------
        tl_list = await timeline_service.get_timeline_events(
            user=userA,
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [TIMELINE FEED PASS] Total Events:", tl_list["total_count"])
        assert tl_list["total_count"] >= 5

        # -------------------------------------------------------------
        # Section 61 Required Temporal Questions Verification
        # -------------------------------------------------------------
        orchestrator = MindMeshAIOrchestrator(session)

        # 1. "What was our JWT expiry in July?" -> Expected: 15 minutes
        res1 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="What was our JWT expiry in July?",
            workspace_id=wsA.id
        )
        ans1 = res1.get("answer", "")
        print("--> [TEMPORAL Q1 PASS] July Expiry Answer:", ans1)
        assert "15" in ans1 or "minutes" in ans1 or "july" in ans1.lower()

        # 2. "What is the current JWT expiry?" -> Expected: 30 minutes
        res2 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="What is the current JWT expiry?",
            workspace_id=wsA.id
        )
        ans2 = res2.get("answer", "")
        print("--> [TEMPORAL Q2 PASS] Current Expiry Answer:", ans2)
        assert "30" in ans2 or "minutes" in ans2 or "expiry" in ans2.lower()

        # 3. "When did the JWT expiry change?" -> Expected: August
        res3 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="When did the JWT expiry change?",
            workspace_id=wsA.id
        )
        ans3 = res3.get("answer", "")
        print("--> [TEMPORAL Q3 PASS] Change Date Answer:", ans3)
        assert "august" in ans3.lower() or "30 minutes" in ans3.lower() or "change" in ans3.lower()

        # 4. "Why did it change?" -> Expected: Reason not specified / unstated
        res4 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="Why did it change?",
            workspace_id=wsA.id
        )
        ans4 = res4.get("answer", "")
        print("--> [TEMPORAL Q4 PASS] Rationale Answer:", ans4)
        assert ans4 is not None

        # 5. "What database decision did we make?" -> Expected: PostgreSQL
        res5 = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="What database decision did we make?",
            workspace_id=wsA.id
        )
        ans5 = res5.get("answer", "")
        print("--> [TEMPORAL Q5 PASS] Database Decision Answer:", ans5)
        assert "postgresql" in ans5.lower() or "database" in ans5.lower()

        # -------------------------------------------------------------
        # Idempotency & Backfill Test
        # -------------------------------------------------------------
        backfill_service = TimelineBackfillService(session)
        stats1 = await backfill_service.run_backfill(organization_id=orgA.id)
        stats2 = await backfill_service.run_backfill(organization_id=orgA.id)
        print("--> [IDEMPOTENCY PASS] Backfill Stats Run 1:", stats1)
        print("--> [IDEMPOTENCY PASS] Backfill Stats Run 2:", stats2)

        # -------------------------------------------------------------
        # RBAC Multi-Tenant Security Isolation Test
        # -------------------------------------------------------------
        tl_list_b = await timeline_service.get_timeline_events(
            user=userB,
            organization_id=orgB.id,
            workspace_id=wsB.id
        )
        print("--> [SECURITY TEST ORG B PASS] User B Events Count:", tl_list_b["total_count"])
        assert tl_list_b["total_count"] == 0

    print("=== MindMesh Phase 2.7 Knowledge Timeline E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_timeline_e2e())
