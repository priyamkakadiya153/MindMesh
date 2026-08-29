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
from app.execution.execution_intelligence_service import ExecutionIntelligenceService

async def test_execution_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.6 Execution Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Execution Org A", slug=f"exec-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Execution Workspace", slug=f"exec-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"exec_usera_{uA_id}@mindmesh.com",
            username=f"exec_usera_{uA_id}",
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
        # Section 173 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-exec-{uuid.uuid4().hex[:6]}",
            description="Execution intelligence test project"
        )
        session.add(project)
        await session.commit()

        exec_service = ExecutionIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 173 Verification Checks
        # -------------------------------------------------------------

        # 1. DECISION-TO-ACTION PLAN CREATION TEST
        plan_res = await exec_service.create_action_plan("dec-102", project.id, "Migrate API Auth System to JWT 30m", "Zero downtime migration with JWT 30m expiry", ["JWT 30m active", "Zero production downtime"], userA)
        plan_id = plan_res["plan_id"]
        print("--> [1. ACTION PLAN CREATED PASS] Plan ID:", plan_id, "| Objective:", plan_res["objective"])
        assert plan_res["status"] == "READY"

        # 2. SUGGESTED TASK GENERATION & HUMAN CONFIRMATION TEST
        sug_tasks = await exec_service.suggest_tasks(plan_id, userA)
        print("--> [2. SUGGESTED TASKS PASS] Total Tasks:", len(sug_tasks), "| First Status:", sug_tasks[0]["status"])
        assert len(sug_tasks) >= 2
        assert sug_tasks[0]["status"] == "SUGGESTED"

        conf_res = await exec_service.confirm_task(sug_tasks[0]["task_id"], userA)
        print("--> [2b. TASK CONFIRMATION PASS] Message:", conf_res["message"], "| Status:", conf_res["task"]["status"])
        assert conf_res["success"] is True
        assert conf_res["task"]["status"] == "CONFIRMED"

        # 3. ACTION DEPENDENCY & CRITICAL PATH ANALYSIS TEST
        cp_res = await exec_service.get_critical_path(project.id, userA)
        print("--> [3. CRITICAL PATH PASS] Health:", cp_res["execution_health"], "| Tasks in Path:", len(cp_res["critical_path_tasks"]))
        assert cp_res["execution_health"] == "AT_RISK"

        # 4. BLOCKER DETECTION & EXECUTION HEALTH TEST
        blk_res = await exec_service.detect_blockers(project.id, userA)
        print("--> [4. BLOCKER DETECTED PASS] Blocker Count:", len(blk_res), "| Title:", blk_res[0]["title"])
        assert len(blk_res) >= 1
        assert blk_res[0]["classification"] == "DETECTED_BLOCKER"

        # 5. CLOSED-LOOP OUTCOME TRACKING & LESSON EXTRACTION TEST
        out_res = await exec_service.record_closed_loop_outcome(plan_id, "Zero downtime migration", "5-minute downtime recorded during DB failover", userA)
        print("--> [5. CLOSED-LOOP OUTCOME PASS] Discrepancy:", out_res["outcome_record"]["discrepancy_status"], "| Lesson Candidate:", out_res["outcome_record"]["lesson_candidate"])
        assert out_res["success"] is True
        assert out_res["outcome_record"]["discrepancy_status"] == "NOT_MET"

        # 6. PREPARED ACTION QUEUE & CONFIRMATION SAFEGUARDS TEST
        pa_res = await exec_service.get_pending_actions(project.id, userA)
        print("--> [6. PENDING ACTIONS PASS] Actions Count:", len(pa_res), "| Confirmation Level:", pa_res[0]["confirmation_level"])
        assert len(pa_res) >= 1
        assert pa_res[0]["confirmation_level"] == "HUMAN_CONFIRMATION_REQUIRED"

    print("=== MindMesh Phase 6.6 Execution Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_execution_intelligence_master_e2e())
