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
from app.models.conversation import ConversationMemory
from app.models.search import SearchIndex
from app.me_context.adaptive_service import PersonalContextAdaptiveService

async def test_personal_context_adaptive_e2e():
    print("=== Starting MindMesh Phase 4.4 Personal Context & Adaptive E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Adaptive Org A", slug=f"adp-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Adaptive Workspace", slug=f"adp-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"adp_usera_{uA_id}@mindmesh.com",
            username=f"adp_usera_{uA_id}",
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
        # Section 118 Master E2E Seeding
        # -------------------------------------------------------------
        proj_auth = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-adp-{uuid.uuid4().hex[:6]}",
            description="Core authentication project"
        )
        proj_bill = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Billing System",
            slug=f"bill-adp-{uuid.uuid4().hex[:6]}",
            description="Billing project"
        )
        session.add_all([proj_auth, proj_bill])
        await session.commit()

        task1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=proj_auth.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task1)
        await session.commit()

        adaptive_service = PersonalContextAdaptiveService(session)

        # -------------------------------------------------------------
        # Section 118 Verification Checks
        # -------------------------------------------------------------

        # 1. CURRENT PROJECT & FOCUS TEST
        context_res = await adaptive_service.get_user_personal_context(userA, orgA.id, wsA.id, proj_auth.id)
        print("--> [1. USER CONTEXT PASS] Active Project:", context_res["active_project_name"], "| Assigned Tasks:", context_res["assigned_tasks_count"])
        assert context_res["assigned_tasks_count"] >= 1

        recs = await adaptive_service.get_focus_recommendations(userA, orgA.id, proj_auth.id)
        print("--> [2. FOCUS RECOMMENDATIONS PASS] Focus Items Count:", len(recs), "| Top Priority:", recs[0]["priority"])
        assert len(recs) >= 1
        assert recs[0]["priority"] == "HIGH"

        # 2. WAITING & COMMITMENTS TEST
        waiting = await adaptive_service.get_user_waiting_items(userA, orgA.id)
        commitments = await adaptive_service.get_user_commitments(userA, orgA.id)
        print("--> [3. WAITING & COMMITMENTS PASS] Waiting Count:", len(waiting), "| Commitments Count:", len(commitments))
        assert len(waiting) >= 1
        assert len(commitments) >= 1

        # 3. AWAY SUMMARY TEST
        away = await adaptive_service.get_away_summary(userA, orgA.id, proj_auth.id)
        print("--> [4. AWAY SUMMARY PASS] Summary Items Count:", len(away["summary_items"]))
        assert len(away["summary_items"]) >= 1

        # 4. PIN & UNPIN PROJECT TEST
        pin_res = await adaptive_service.pin_project(userA.id, proj_auth.id)
        print("--> [5. PIN PROJECT PASS] Pinned Project IDs:", pin_res["pinned_project_ids"])
        assert str(proj_auth.id) in pin_res["pinned_project_ids"]

        unpin_res = await adaptive_service.unpin_project(userA.id, proj_auth.id)
        print("--> [6. UNPIN PROJECT PASS] Remaining Pinned Project IDs:", unpin_res["pinned_project_ids"])
        assert str(proj_auth.id) not in unpin_res["pinned_project_ids"]

    print("=== MindMesh Phase 4.4 Personal Context & Adaptive E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_personal_context_adaptive_e2e())
