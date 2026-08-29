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
from app.analytics.advanced_data_intelligence_analytics_service import AdvancedDataIntelligenceAnalyticsService

async def test_advanced_data_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.19 Advanced Data Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Analytics Org", slug=f"analytics-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Analytics Workspace", slug=f"analytics-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"analytics_user_{u_id}@mindmesh.com",
            username=f"analytics_user_{u_id}",
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
        analytics_service = AdvancedDataIntelligenceAnalyticsService(session)

        # -------------------------------------------------------------
        # Section 161 Verification Checks
        # -------------------------------------------------------------

        # 1. PROJECT HEALTH & RISK SIGNALS TEST
        proj_intel = await analytics_service.get_project_intelligence(proj_id, org.id, user)
        print("--> [1. PROJECT HEALTH PASS] Score:", proj_intel["health_assessment"]["health_score"], "| Trend:", proj_intel["trend"]["direction"], "| What Changed:", proj_intel["trend"]["what_changed"])
        assert proj_intel["health_assessment"]["overall_status"] == "POTENTIAL_RISK"
        assert proj_intel["trend"]["direction"] == "WORSENING"

        # 2. KNOWLEDGE HEALTH & ZERO-RESULT SEARCH GAP TEST
        know_health = await analytics_service.get_knowledge_health_analytics(org.id, user)
        print("--> [2. KNOWLEDGE HEALTH & GAP PASS] Freshness:", know_health["health_summary"]["freshness_score"], "| Zero-Result Searches:", len(know_health["zero_result_searches"]))
        assert len(know_health["zero_result_searches"]) > 0
        assert know_health["zero_result_searches"][0]["query"] == "OAuth 2.0 Token Refresh Policy"

        # 3. BOTTLENECKS & DEPENDENCY RISKS TEST
        bots = await analytics_service.detect_bottlenecks_and_dependencies(org.id, user)
        print("--> [3. BOTTLENECK & DEPENDENCY PASS] Active Bottlenecks:", len(bots["bottlenecks"]), "| Target:", bots["bottlenecks"][0]["target"])
        assert len(bots["bottlenecks"]) >= 2
        assert bots["bottlenecks"][0]["type"] == "DEPENDENCY_BOTTLENECK"

        # 4. TRENDS & ANOMALIES DETECTION TEST
        trends_anom = await analytics_service.detect_trends_anomalies_patterns(org.id, user)
        print("--> [4. TRENDS & ANOMALIES PASS] Trends Detected:", len(trends_anom["trends"]), "| Anomaly:", trends_anom["anomalies"][0]["observed_anomaly"])
        assert len(trends_anom["trends"]) > 0
        assert trends_anom["anomalies"][0]["confidence"] == "HIGH_CONFIDENCE"

        # 5. PORTFOLIO EXECUTIVE VIEW TEST
        portfolio = await analytics_service.get_portfolio_analytics(org.id, user)
        print("--> [5. PORTFOLIO EXECUTIVE VIEW PASS] Portfolio Health:", portfolio["portfolio_summary"]["overall_portfolio_health"], "| Projects Matrix Count:", len(portfolio["projects_matrix"]))
        assert portfolio["portfolio_summary"]["overall_portfolio_health"] == "82/100"

        # 6. DRILL-DOWN EVIDENCE CHAIN TEST
        drilldown = await analytics_service.get_drilldown_evidence("bot-1", user)
        print("--> [6. DRILL-DOWN EVIDENCE PASS] WHAT:", drilldown["explanation"]["what"], "| RBAC Authorized:", drilldown["rbac_authorized"])
        assert drilldown["rbac_authorized"] is True
        assert len(drilldown["evidence_chain"]) == 3

    print("=== MindMesh Phase 6.19 Advanced Data Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_advanced_data_intelligence_master_e2e())
