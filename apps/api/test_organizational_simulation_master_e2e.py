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
from app.simulation.organizational_simulation_service import OrganizationalSimulationService

async def test_organizational_simulation_master_e2e():
    print("=== Starting MindMesh Phase 6.32 Organizational Simulation Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Simulation Org", slug=f"sim-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Simulation Workspace", slug=f"sim-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"sim_user_{u_id}@mindmesh.com",
            username=f"sim_user_{u_id}",
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

        sim_service = OrganizationalSimulationService(session)

        # -------------------------------------------------------------
        # Section 200 Verification Checks
        # -------------------------------------------------------------

        # 1. DIGITAL TWIN SNAPSHOT TEST
        twin = await sim_service.get_digital_twin_snapshot(org.id, user)
        print("--> [1. DIGITAL TWIN SNAPSHOT PASS] Snapshot ID:", twin["snapshot_id"], "| Modeled Entities:", twin["modeled_entities"])
        assert twin["data_freshness"] == "CURRENT"

        # 2. NATURAL LANGUAGE WHAT-IF SCENARIO CREATION TEST
        nl_query = "What if we delay Project Alpha by 2 weeks, but add 1 engineer and run testing in parallel?"
        scn = await sim_service.create_scenario("Project Alpha What-If", nl_query, [], org.id, user)
        print("--> [2. SCENARIO CREATION PASS] Scenario ID:", scn["scenario_id"], "| Parsed Changes:", len(scn["changes"]))
        assert len(scn["changes"]) == 3
        assert scn["status"] == "READY"

        # 3. WHAT-IF SIMULATION & GRAPH IMPACT PROPAGATION TEST
        sim_run = await sim_service.run_simulation(scn["scenario_id"], org.id, user)
        print("--> [3. WHAT-IF SIMULATION PASS] Run ID:", sim_run["simulation_run_id"], "| Duration Delta:", sim_run["modeled_delta"]["duration_delta"])
        assert sim_run["status"] == "COMPLETED"
        assert len(sim_run["impact_propagation"]["indirect_downstream_1hop"]) > 0

        # 4. MULTI-SCENARIO SIDE-BY-SIDE COMPARISON TEST
        cmp_res = await sim_service.compare_scenarios([scn["scenario_id"], "scn-opt-b"], org.id, user)
        print("--> [4. SCENARIO COMPARISON PASS] Comparison ID:", cmp_res["comparison_id"], "| Evaluated Scenarios:", len(cmp_res["scenarios_evaluated"]))
        assert len(cmp_res["scenarios_evaluated"]) == 2

        # 5. STALE SCENARIO DETECTION & EXECUTION BLOCK TEST
        handoff_stale = await sim_service.handoff_scenario_to_workflow(scn["scenario_id"], is_stale=True, organization_id=org.id, user=user)
        print("--> [5. STALE SCENARIO EXECUTION BLOCK PASS] Handoff Status:", handoff_stale["handoff_status"], "| Reason:", handoff_stale["error_reason"])
        assert handoff_stale["handoff_status"] == "BLOCKED_STALE_SCENARIO"

        # 6. REVALIDATION & WORKFLOW HANDOFF TEST
        handoff_valid = await sim_service.handoff_scenario_to_workflow(scn["scenario_id"], is_stale=False, organization_id=org.id, user=user)
        print("--> [6. WORKFLOW HANDOFF SUCCESS PASS] Created Workflow ID:", handoff_valid["created_workflow_id"], "| Status:", handoff_valid["status"])
        assert handoff_valid["handoff_status"] == "APPROVED_HANDOFF_SUCCESSFUL"
        assert handoff_valid["created_workflow_id"] is not None

    print("=== MindMesh Phase 6.32 Organizational Simulation Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_simulation_master_e2e())
