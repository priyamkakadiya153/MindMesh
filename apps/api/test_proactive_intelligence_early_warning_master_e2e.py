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
from app.analytics.proactive_intelligence_early_warning_service import ProactiveIntelligenceEarlyWarningService

async def test_proactive_intelligence_early_warning_master_e2e():
    print("=== Starting MindMesh Phase 6.23 Proactive Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Proactive Org", slug=f"pro-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Proactive Workspace", slug=f"pro-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"pro_user_{u_id}@mindmesh.com",
            username=f"pro_user_{u_id}",
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
        pro_service = ProactiveIntelligenceEarlyWarningService(session)

        # -------------------------------------------------------------
        # Section 201 Verification Checks
        # -------------------------------------------------------------

        # 1. SIGNAL DETECTION & CORRELATION TEST
        signals = await pro_service.detect_and_correlate_proactive_signals(proj_id, org.id, user)
        print("--> [1. SIGNAL DETECTION PASS] Total Active Signals:", signals["total_active_signals"], "| Types:", [s["signal_type"] for s in signals["detected_signals"]])
        assert signals["total_active_signals"] == 3
        assert signals["detected_signals"][0]["signal_type"] == "DEADLINE_RISK"

        # 2. EARLY WARNING RISK EVALUATION TEST
        risks = await pro_service.evaluate_early_warning_risks(org.id, user)
        print("--> [2. EARLY WARNING RISKS PASS] Org Risk Score:", risks["overall_organization_risk_score"], "| Trajectory:", risks["risk_trajectory"])
        assert risks["overall_organization_risk_score"] == 68

        # 3. WHAT-IF SCENARIO SIMULATION TEST
        what_if = await pro_service.run_what_if_scenario("Dependency Delay Analysis", {"delay_days": 3}, org.id, user)
        print("--> [3. WHAT-IF SIMULATION PASS] Mode:", what_if["mode"], "| Projected Delay:", what_if["simulated_outcomes"]["projected_milestone_delay_days"], "days")
        assert what_if["mode"] == "WHAT_IF_SIMULATION"
        assert what_if["side_effect_guarantee"] == "Zero production state mutations."

        # 4. SIGNAL LIFECYCLE (SNOOZE, DISMISS, RESOLVE) TEST
        sig_id = signals["detected_signals"][0]["signal_id"]
        mg_res = await pro_service.manage_signal_status(sig_id, "SNOOZE", "Reviewing tomorrow", user)
        print("--> [4. SIGNAL LIFECYCLE PASS] Signal ID:", mg_res["signal_id"], "| Status:", mg_res["updated_status"], "| Learning Recorded:", mg_res["feedback_recorded_for_phase_620_learning"])
        assert mg_res["updated_status"] == "SNOOZED"
        assert mg_res["feedback_recorded_for_phase_620_learning"] is True

        # 5. PROACTIVE BRIEFING & PHASE 6.21 HANDOFF TEST
        briefing = await pro_service.generate_proactive_briefing("MORNING", org.id, user)
        print("--> [5. PROACTIVE BRIEFING PASS] Type:", briefing["briefing_type"], "| Bullets:", len(briefing["summary_bullet_points"]), "| Recommended Action:", briefing["recommended_next_actions"][0]["action_name"])
        assert briefing["briefing_type"] == "MORNING"
        assert briefing["recommended_next_actions"][0]["phase_621_plan_prepared"] is True

        # 6. PROACTIVE DIGEST TEST
        digest = await pro_service.generate_proactive_digest("DAILY", org.id, user)
        print("--> [6. PROACTIVE DIGEST PASS] Frequency:", digest["digest_frequency"], "| Health:", digest["trends"]["project_health"])
        assert digest["digest_frequency"] == "DAILY"

    print("=== MindMesh Phase 6.23 Proactive Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_proactive_intelligence_early_warning_master_e2e())
