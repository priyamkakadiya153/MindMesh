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
from app.analytics.knowledge_automation_adaptive_learning_service import KnowledgeAutomationAdaptiveLearningService

async def test_knowledge_automation_adaptive_learning_master_e2e():
    print("=== Starting MindMesh Phase 6.20 Adaptive Learning Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Adaptive Org", slug=f"adaptive-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Adaptive Workspace", slug=f"adaptive-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"adaptive_user_{u_id}@mindmesh.com",
            username=f"adaptive_user_{u_id}",
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

        adaptive_service = KnowledgeAutomationAdaptiveLearningService(session)

        # -------------------------------------------------------------
        # Section 182 Verification Checks
        # -------------------------------------------------------------

        # 1. RECORD LEARNING EVENT TEST
        evt = await adaptive_service.record_learning_event(
            event_type="HUMAN_CORRECTION",
            scope="PROJECT",
            payload={"correction": "Auth Gateway -> OAuth Security Gateway"},
            user=user,
            organization_id=org.id
        )
        print("--> [1. RECORD LEARNING EVENT PASS] Event ID:", evt["event_id"], "| Signal Strength:", evt["signal_strength"], "| Validation State:", evt["validation_state"])
        assert evt["signal_strength"] == "STRONG"
        assert evt["validation_state"] == "VALIDATED"

        # 2. HUMAN REVIEW QUEUE TEST
        queue = await adaptive_service.get_learning_review_queue(org.id, user)
        print("--> [2. HUMAN REVIEW QUEUE PASS] Pending Items:", len(queue["pending_items"]), "| First Item Title:", queue["pending_items"][0]["title"])
        assert len(queue["pending_items"]) >= 2
        assert queue["pending_items"][0]["status"] == "PENDING_REVIEW"

        # 3. REVIEW ACTION & PROMOTION TEST
        review_act = await adaptive_service.validate_learning_signal("rev-101", "ACCEPT", user)
        print("--> [3. REVIEW ACTION & PROMOTION PASS] Action:", review_act["action"], "| New Status:", review_act["new_status"])
        assert review_act["new_status"] == "PROMOTED_ACCEPT"

        # 4. SOURCE DOCUMENT CHANGE & KNOWLEDGE REVALIDATION TEST
        reval = await adaptive_service.revalidate_knowledge_on_source_change("doc-501", org.id)
        print("--> [4. KNOWLEDGE REVALIDATION PASS] Status:", reval["revalidation_status"], "| Downstream Objects:", len(reval["downstream_objects"]))
        assert reval["revalidation_status"] == "POTENTIALLY_OUTDATED_MARKED"
        assert len(reval["downstream_objects"]) == 2

        # 5. DOWNSTREAM IMPACT GRAPH PREVIEW TEST
        impact = await adaptive_service.evaluate_downstream_impact("kn-301", user)
        print("--> [5. DOWNSTREAM IMPACT GRAPH PASS] Graph Nodes:", len(impact["impact_graph"]["nodes"]), "| Preview Summary:", impact["preview_summary"])
        assert len(impact["impact_graph"]["nodes"]) == 4

        # 6. SHADOW MODE AUTOMATION & PROMOTION TEST
        shadow = await adaptive_service.evaluate_shadow_automation("Auto-Tag OAuth Security Tasks", org.id)
        print("--> [6. SHADOW MODE AUTOMATION PASS] Alignment Rate:", shadow["human_alignment_rate"], "| Status:", shadow["status"])
        assert shadow["human_alignment_rate"] == "95.2%"

        promote = await adaptive_service.promote_automation_rule("Auto-Tag OAuth Security Tasks", user)
        print("--> [6b. AUTOMATION PROMOTION PASS] New Mode:", promote["new_mode"], "| Rollback Token:", promote["rollback_token"])
        assert promote["new_mode"] == "ACTIVE_AUTOMATION"

        # 7. ADAPTIVE INTELLIGENCE TELEMETRY DASHBOARD TEST
        dash = await adaptive_service.get_adaptive_intelligence_dashboard(org.id, user)
        print("--> [7. ADAPTIVE TELEMETRY DASHBOARD PASS] Signal Accuracy:", dash["signal_quality_metrics"]["signal_accuracy"], "| Detected Drift:", dash["drift_detection"]["detected_drift"])
        assert dash["signal_quality_metrics"]["signal_accuracy"] == "95.1%"

    print("=== MindMesh Phase 6.20 Adaptive Learning Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_automation_adaptive_learning_master_e2e())
