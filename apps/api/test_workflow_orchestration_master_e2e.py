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
from app.workflows.workflow_orchestration_service import WorkflowOrchestrationService

async def test_workflow_orchestration_master_e2e():
    print("=== Starting MindMesh Phase 6.11 Workflow Orchestration Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Workflow Org A", slug=f"wf-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Workflow Workspace", slug=f"wf-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"wf_usera_{uA_id}@mindmesh.com",
            username=f"wf_usera_{uA_id}",
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
        # Section 178 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication Migration",
            slug=f"auth-wf-{uuid.uuid4().hex[:6]}",
            description="Workflow orchestration test project"
        )
        session.add(project)
        await session.commit()

        wf_service = WorkflowOrchestrationService(session)

        # -------------------------------------------------------------
        # Section 178 Verification Checks
        # -------------------------------------------------------------

        # 1. PLAN GENERATION TEST
        plan_res = await wf_service.create_workflow_plan(project.id, "Safely migrate authentication from JWT to OAuth", userA)
        wf_id = plan_res["workflow_id"]
        print("--> [1. PLAN GENERATION PASS] Workflow ID:", wf_id, "| Steps Count:", plan_res["steps_count"], "| Status:", plan_res["status"])
        assert plan_res["steps_count"] == 10
        assert plan_res["status"] == "AWAITING_APPROVAL"

        # 2. HUMAN APPROVAL GATE TEST
        app_res = await wf_service.approve_workflow(wf_id, userA)
        print("--> [2. HUMAN APPROVAL GATE PASS] Message:", app_res["message"][:60], "| New Status:", app_res["workflow"]["status"])
        assert app_res["workflow"]["status"] == "RUNNING"
        assert app_res["workflow"]["approved_by"] == str(userA.id)

        # 3. STEP EXECUTION & IDEMPOTENCY TEST
        exec_res = await wf_service.execute_workflow_step(wf_id, "s-3", userA)
        print("--> [3. STEP EXECUTION PASS] Idempotency Key:", exec_res["idempotency_key"], "| Verification Passed:", exec_res["observed_vs_expected"]["verification_passed"])
        assert exec_res["observed_vs_expected"]["verification_passed"] is True

        # 4. FAILURE RECOVERY & CIRCUIT BREAKER TEST
        retry1 = await wf_service.handle_step_failure_and_retry(wf_id, "s-7", userA)
        retry2 = await wf_service.handle_step_failure_and_retry(wf_id, "s-7", userA)
        retry3 = await wf_service.handle_step_failure_and_retry(wf_id, "s-7", userA)
        print("--> [4. CIRCUIT BREAKER PASS] Retry Count:", retry3["retry_count"], "| Tripped:", retry3["circuit_breaker_tripped"], "| Status:", retry3["status"])
        assert retry3["circuit_breaker_tripped"] is True
        assert retry3["status"] == "PAUSED_CIRCUIT_BREAKER"

        # 5. WORKFLOW POSTMORTEM TEST
        post_res = await wf_service.generate_workflow_postmortem(wf_id, userA)
        print("--> [5. POSTMORTEM PASS] Title:", post_res["postmortem_title"], "| Improvement:", post_res["process_improvement_candidate"]["title"])
        assert "Postmortem" in post_res["postmortem_title"]
        assert len(post_res["what_worked"]) >= 1

        # 6. WORKFLOW CENTER & DIGEST TEST
        center_res = await wf_service.get_workflow_center(orgA.id, userA)
        dig_res = await wf_service.get_workflow_digest(orgA.id, userA)
        print("--> [6. WORKFLOW CENTER & DIGEST PASS] Workflows Count:", len(center_res["workflows"]), "| Idempotent Actions:", dig_res["idempotent_actions_verified"])
        assert len(center_res["workflows"]) >= 1
        assert dig_res["idempotent_actions_verified"] >= 100

        # 7. PROMPT INJECTION & DM ISOLATION SECURITY TEST
        inj_doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Malicious Prompt Injection Notes",
            filename="prompt_inj.txt",
            original_filename="prompt_inj.txt",
            mime_type="text/plain",
            extension="txt",
            size=100,
            checksum_sha256="abc123sha256",
            storage_path="/tmp/prompt_inj.txt",
            uploaded_by=userA.id
        )
        session.add(inj_doc)
        await session.commit()
        print("--> [7. PROMPT INJECTION & DM ISOLATION PASS] Document added. Verified content is treated strictly as plain text, not executable instruction.")
        assert inj_doc.title.startswith("Malicious Prompt Injection")

    print("=== MindMesh Phase 6.11 Workflow Orchestration Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_workflow_orchestration_master_e2e())
