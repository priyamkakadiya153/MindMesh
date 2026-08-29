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
from app.proactive.proactive_intelligence_service import ProactiveIntelligenceService

async def test_proactive_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.7 Proactive Intelligence Master E2E Test Suite ===")

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
        # Section 173 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-pro-{uuid.uuid4().hex[:6]}",
            description="Proactive intelligence test project"
        )
        session.add(project)
        await session.commit()

        pro_service = ProactiveIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 173 Verification Checks
        # -------------------------------------------------------------

        # 1. KNOWLEDGE & DECISION DRIFT DETECTION TEST
        drift_res = await pro_service.scan_knowledge_drift(project.id, userA)
        print("--> [1. KNOWLEDGE DRIFT SCAN PASS] Total Insights:", len(drift_res), "| First Type:", drift_res[0]["insight_type"])
        assert len(drift_res) >= 2
        assert drift_res[0]["insight_type"] == "KNOWLEDGE_DRIFT"
        assert drift_res[1]["insight_type"] == "DECISION_DRIFT"

        # 2. DEADLINE & EXECUTION RISK TEST
        risk_res = await pro_service.detect_deadline_and_execution_risks(project.id, userA)
        print("--> [2. DEADLINE RISK PASS] Insight Type:", risk_res[0]["insight_type"], "| Priority:", risk_res[0]["priority"])
        assert risk_res[0]["insight_type"] == "DEADLINE_RISK"
        assert risk_res[0]["priority"] == "CRITICAL"

        # 3. EMERGING PATTERN & ANOMALY DETECTION TEST
        pat_res = await pro_service.detect_emerging_patterns(orgA.id, userA)
        print("--> [3. EMERGING PATTERNS PASS] Patterns Count:", len(pat_res), "| Maturity:", pat_res[0]["maturity"])
        assert len(pat_res) >= 1
        assert pat_res[0]["maturity"] == "EMERGING"

        # 4. PROACTIVE INSIGHTS FEED & LIFECYCLE TEST
        feed = await pro_service.get_proactive_insights("PROJECT", str(project.id), userA)
        ins_id = feed[0]["insight_id"]
        ack_res = await pro_service.acknowledge_insight(ins_id, userA)
        print("--> [4. LIFECYCLE ACKNOWLEDGE PASS] Message:", ack_res["message"], "| State:", ack_res["insight"]["lifecycle_state"])
        assert ack_res["insight"]["lifecycle_state"] == "ACKNOWLEDGED"

        dsm_res = await pro_service.dismiss_insight(ins_id, "User verified", userA)
        print("--> [4b. LIFECYCLE DISMISS PASS] Message:", dsm_res["message"], "| State:", dsm_res["insight"]["lifecycle_state"])
        assert dsm_res["insight"]["lifecycle_state"] == "DISMISSED"

        # 5. MISSED INSIGHT FEEDBACK TEST
        miss_res = await pro_service.report_missed_insight("MindMesh missed database failover timeout risk", project.id, userA)
        print("--> [5. MISSED INSIGHT REPORT PASS] Message:", miss_res["message"])
        assert miss_res["success"] is True

        # 6. PROJECT HEALTH RETRIEVAL TEST
        health_res = await pro_service.get_project_health(project.id, userA)
        print("--> [6. PROJECT HEALTH PASS] Health State:", health_res["health_state"], "| Active Insights:", health_res["active_insights_count"])
        assert health_res["health_state"] == "AT_RISK"

    print("=== MindMesh Phase 6.7 Proactive Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_proactive_intelligence_master_e2e())
