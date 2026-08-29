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
from app.proactive.anticipatory_service import ProactiveAnticipatoryEngineService

async def test_proactive_anticipatory_e2e():
    print("=== Starting MindMesh Phase 4.5 Proactive Knowledge & Anticipatory E2E Test Suite ===")

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
        # Section 121 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-pro-{uuid.uuid4().hex[:6]}",
            description="Core authentication proactive project"
        )
        session.add(project)
        await session.commit()

        task1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task1)
        await session.commit()

        proactive_service = ProactiveAnticipatoryEngineService(session)

        # -------------------------------------------------------------
        # Section 121 Verification Checks
        # -------------------------------------------------------------

        # 1. TASK ASSIGNMENT SIGNAL TEST
        ins1 = await proactive_service.emit_proactive_event(
            event_type="TASK_ASSIGNED",
            organization_id=orgA.id,
            workspace_id=wsA.id,
            target_user_id=userA.id,
            title="New Task Assigned: Update deployment configuration",
            description="You were assigned to update the deployment configuration for Authentication System.",
            source_type="task",
            source_id=task1.id,
            project_id=project.id,
            project_name=project.name,
            importance="IMPORTANT"
        )
        print("--> [1. TASK ASSIGNMENT PASS] Insight Title:", ins1["title"], "| Status:", ins1["status"])
        assert ins1 is not None

        # 2. BLOCKER SIGNAL TEST
        ins2 = await proactive_service.emit_proactive_event(
            event_type="BLOCKER_CREATED",
            organization_id=orgA.id,
            workspace_id=wsA.id,
            target_user_id=userA.id,
            title="Task Blocked: Update deployment configuration",
            description="Your deployment task is blocked by a missing environment variable.",
            source_type="task",
            source_id=task1.id,
            project_id=project.id,
            project_name=project.name,
            importance="CRITICAL"
        )
        print("--> [2. BLOCKER SIGNAL PASS] Importance:", ins2["importance"], "| Explanation:", ins2["context_explanation"])
        assert ins2["importance"] == "CRITICAL"

        # 3. DECISION CHANGE & TASK IMPACT TEST
        ins3 = await proactive_service.emit_proactive_event(
            event_type="DECISION_UPDATED",
            organization_id=orgA.id,
            workspace_id=wsA.id,
            target_user_id=userA.id,
            title="Decision Changed: JWT Expiry set to 30 minutes",
            description="JWT expiry updated from 15 to 30 minutes. Affects 1 assigned task.",
            source_type="decision",
            source_id=uuid.uuid4(),
            project_id=project.id,
            project_name=project.name,
            importance="IMPORTANT"
        )
        print("--> [3. DECISION CHANGE & TASK IMPACT PASS] Event Type:", ins3["event_type"])
        assert ins3["event_type"] == "DECISION_UPDATED"

        # 4. KNOWLEDGE CONFLICT ALERT TEST
        ins4 = await proactive_service.emit_proactive_event(
            event_type="KNOWLEDGE_CONFLICT",
            organization_id=orgA.id,
            workspace_id=wsA.id,
            target_user_id=userA.id,
            title="Knowledge Conflict: Architecture Doc vs Decision",
            description="Document specifies 15m JWT expiry, decision specifies 30m.",
            source_type="conflict",
            source_id=uuid.uuid4(),
            project_id=project.id,
            project_name=project.name,
            importance="IMPORTANT"
        )
        print("--> [4. KNOWLEDGE CONFLICT PASS] Title:", ins4["title"])
        assert "Conflict" in ins4["title"]

        # 5. DEDUPLICATION TEST (100% Idempotency)
        ins_dup = await proactive_service.emit_proactive_event(
            event_type="TASK_ASSIGNED",
            organization_id=orgA.id,
            workspace_id=wsA.id,
            target_user_id=userA.id,
            title="New Task Assigned: Update deployment configuration",
            description="You were assigned to update the deployment configuration.",
            source_type="task",
            source_id=task1.id,
            project_id=project.id,
            project_name=project.name
        )
        print("--> [5. DEDUPLICATION PASS] Duplicate Insight ID matches original:", ins_dup["id"] == ins1["id"])
        assert ins_dup["id"] == ins1["id"]

        # 6. USER RETRIEVAL & UNREAD COUNTER TEST
        user_insights = await proactive_service.get_user_proactive_insights(userA, orgA.id, wsA.id)
        print("--> [6. INSIGHTS RETRIEVAL PASS] Total Insights:", user_insights["total_insights"], "| Unread Count:", user_insights["unread_count"])
        assert user_insights["unread_count"] >= 3

        # 7. SECURITY & PRIVACY ISOLATION TEST (User C in Org B)
        userC_insights = await proactive_service.get_user_proactive_insights(userC, orgB.id, wsB.id)
        print("--> [7. SECURITY PASS] Org B Insights Count:", userC_insights["total_insights"])
        assert userC_insights["total_insights"] == 0

    print("=== MindMesh Phase 4.5 Proactive Knowledge & Anticipatory E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_proactive_anticipatory_e2e())
