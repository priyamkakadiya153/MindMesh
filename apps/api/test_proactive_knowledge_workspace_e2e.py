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
from app.projects.models import Project
from app.models.task import Task
from app.proactive.workspace_service import ProactiveWorkspaceService

async def test_proactive_knowledge_workspace_e2e():
    print("=== Starting MindMesh Phase 5.9 Proactive Workspace Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Proactive Org A", slug=f"pro-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Proactive Workspace", slug=f"pro-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"pro_usera_{uA_id}@mindmesh.com",
            username=f"pro_usera_{uA_id}",
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

        # -------------------------------------------------------------
        # Section 146 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-pro-{uuid.uuid4().hex[:6]}",
            description="Proactive workspace test project"
        )
        session.add(project)
        await session.commit()

        doc1 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v1",
            filename="auth_arch_v1.md",
            original_filename="auth_arch_v1.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_pro_1",
            storage_path="/path/pro1.md",
            uploaded_by=userA.id
        )
        doc2 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch_v2.md",
            original_filename="auth_arch_v2.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_pro_2",
            storage_path="/path/pro2.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2])
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task)
        await session.commit()

        proactive_service = ProactiveWorkspaceService(session)

        # -------------------------------------------------------------
        # Section 146 Verification Checks
        # -------------------------------------------------------------

        # 1. PROACTIVE FEED EVALUATION TEST
        feed = await proactive_service.get_proactive_feed(userA, orgA.id, project.id, "UNREAD")
        print("--> [1. PROACTIVE FEED EVALUATION PASS] Insight Items Count:", len(feed))
        assert len(feed) >= 3

        # 2. REASON & EVIDENCE EXPLANATION TEST
        top_ins = feed[0]
        print("--> [2. REASON & EVIDENCE PASS] Top Title:", top_ins["title"], "| Priority:", top_ins["priority"], "| Reason:", top_ins["reason"][:50], "...")
        assert top_ins["priority"] in ["CRITICAL", "IMPORTANT"]
        assert len(top_ins["evidence"]) >= 2

        # 3. INBOX LIFECYCLE (Snooze, Dismiss, Follow) TEST
        snooze_res = await proactive_service.snooze_insight(top_ins["insight_id"], "1d", userA)
        print("--> [3a. SNOOZE PASS] Message:", snooze_res["message"])
        assert snooze_res["success"] is True

        dismiss_res = await proactive_service.dismiss_insight("ins-doc-conflict-1", "Already Handled", userA)
        print("--> [3b. DISMISS PASS] Message:", dismiss_res["message"])
        assert dismiss_res["success"] is True

        follow_res = await proactive_service.follow_entity("Decision #D-102", userA)
        print("--> [3c. FOLLOW PASS] Followed Entities:", follow_res["followed_entities"])
        assert "Decision #D-102" in follow_res["followed_entities"]

        # 4. INTELLIGENCE INBOX RETRIEVAL TEST
        inbox_res = await proactive_service.get_inbox(userA, orgA.id)
        print("--> [4. INTELLIGENCE INBOX PASS] Unread Count:", inbox_res["unread_count"], "| Critical Count:", inbox_res["critical_count"])
        assert inbox_res["unread_count"] >= 1

        # 5. IDEMPOTENT INSIGHT REBUILD TEST
        rebuild_res = await proactive_service.rebuild_proactive_insights(orgA.id)
        print("--> [5. INSIGHT REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 5.9 Proactive Workspace Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_proactive_knowledge_workspace_e2e())
