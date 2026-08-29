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
from app.workflows.adaptive_workflow_engine_service import AdaptiveWorkflowEngineService

async def test_adaptive_workflow_engine_master_e2e():
    print("=== Starting MindMesh Phase 6.27 Adaptive Workflows Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Adaptive Org", slug=f"wf-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Adaptive Workspace", slug=f"wf-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"wf_user_{u_id}@mindmesh.com",
            username=f"wf_user_{u_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}",
            current_organization_id=org.id
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        proj_id = uuid.uuid4()
        wf_service = AdaptiveWorkflowEngineService(session)

        # -------------------------------------------------------------
        # Section 201 Verification Checks
        # -------------------------------------------------------------

        # 1. WORK OBJECTIVE CREATION
        obj = await wf_service.create_work_objective(
            goal="Release Project Alpha v2.0 with SOC2 Compliance",
            scope="Full Project Alpha codebase & microservices",
            priority="HIGH",
            deadline="2026-09-01T00:00:00Z",
            project_id=proj_id,
            organization_id=org.id,
            user=user
        )
        print("--> [1. OBJECTIVE CREATION PASS] Objective ID:", obj["objective_id"], "| Priority:", obj["priority"], "| Risk:", obj["risk_assessment"])
        assert obj["priority"] == "HIGH"

        # 2. INTENT & PLAN GENERATION
        plan = await wf_service.generate_work_plan(
            objective_id=obj["objective_id"],
            user_intent="Prepare Project Alpha for release.",
            project_id=proj_id,
            organization_id=org.id,
            user=user
        )
        print("--> [2. PLAN GENERATION PASS] Plan ID:", plan["plan_id"], "| Steps:", len(plan["steps"]), "| Confidence:", plan["confidence_score"])
        assert len(plan["steps"]) == 3
        assert plan["confidence_score"] == 0.94

        # 3. PLAN VALIDATION & PREVIEW
        prev = await wf_service.validate_and_preview_plan(plan["plan_id"], org.id, user)
        print("--> [3. PLAN VALIDATION & PREVIEW PASS] Is Valid:", prev["is_valid"], "| Total Steps:", prev["preview_summary"]["total_steps"])
        assert prev["is_valid"] is True
        assert prev["preview_summary"]["total_steps"] == 3

        # 4. STEP EXECUTION & APPROVAL GATE
        step1_exec = await wf_service.execute_workflow_step(plan["plan_id"], "step-1", "START", org.id, user)
        print("--> [4. STEP 1 EXECUTION PASS] Step State:", step1_exec["step_state"], "| Plan Status:", step1_exec["plan_status"])
        assert step1_exec["step_state"] == "RUNNING"

        step3_appr = await wf_service.execute_workflow_step(plan["plan_id"], "step-3", "APPROVE", org.id, user)
        print("--> [5. STEP 3 APPROVAL PASS] Step State:", step3_appr["step_state"], "| Plan Status:", step3_appr["plan_status"])
        assert step3_appr["step_state"] == "COMPLETED"
        assert step3_appr["plan_status"] == "COMPLETED"

        # 5. EXCEPTION HANDLING & RECOVERY
        exc = await wf_service.handle_workflow_exception(plan["plan_id"], "step-2", "HTTP 503 Auth0 sandbox timeout", org.id, user)
        print("--> [6. EXCEPTION HANDLING PASS] Exception ID:", exc["exception_id"], "| Severity:", exc["severity"], "| Recovery:", exc["suggested_recovery"])
        assert exc["severity"] == "RECOVERABLE"
        assert len(exc["recovery_options"]) == 3

        # 6. DRY RUN SIMULATION TEST
        dr = await wf_service.dry_run_workflow(plan["plan_id"], org.id, user)
        print("--> [7. DRY RUN SIMULATION PASS] Mode:", dr["mode"], "| Mutation Occurred:", dr["production_mutation_occurred"])
        assert dr["mode"] == "DRY_RUN"
        assert dr["production_mutation_occurred"] is False

        # 7. PLAN VS ACTUAL EVALUATION & LESSON FEEDBACK
        ev = await wf_service.evaluate_plan_vs_actual(plan["plan_id"], org.id, user)
        print("--> [8. PLAN VS ACTUAL EVALUATION PASS] Objective:", ev["objective_achieved"], "| Candidate Lesson:", ev["candidate_lesson"])
        assert ev["objective_achieved"] == "ACHIEVED"

    print("=== MindMesh Phase 6.27 Adaptive Workflows Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_adaptive_workflow_engine_master_e2e())
