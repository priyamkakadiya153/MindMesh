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
from app.decisions.decision_intelligence_service import DecisionIntelligenceService

async def test_decision_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.5 Decision Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Decision Org A", slug=f"dec-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Decision Workspace", slug=f"dec-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"dec_usera_{uA_id}@mindmesh.com",
            username=f"dec_usera_{uA_id}",
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
            slug=f"auth-dec-{uuid.uuid4().hex[:6]}",
            description="Decision intelligence test project"
        )
        session.add(project)
        await session.commit()

        doc1 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_dec_1",
            storage_path="/path/dec1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        dec_service = DecisionIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 173 Verification Checks
        # -------------------------------------------------------------

        # 1. DECISION WORKSPACE CREATION TEST
        ws_res = await dec_service.create_decision_workspace("Should we migrate API authentication system?", project.id, "API Auth Subsystem", ["Security", "2-Week Deadline"], userA)
        ws_id = ws_res["workspace_id"]
        print("--> [1. WORKSPACE CREATED PASS] Workspace ID:", ws_id, "| Question:", ws_res["question"])
        assert ws_res["readiness_state"] == "NEEDS_EVIDENCE"

        # 2. EVIDENCE SYNTHESIS & CONFLICT DETECTION TEST
        ev1 = await dec_service.add_evidence(ws_id, str(doc1.id), "DOCUMENT", "Auth Arch v2", "CURRENT", "APPROVED", "Specifies 30m timeout.", userA)
        ev2 = await dec_service.add_evidence(ws_id, "doc-legacy-v1", "DOCUMENT", "Auth Arch v1 (15m)", "HISTORICAL", "SUPERSEDED", "Legacy 15m timeout.", userA)
        print("--> [2. EVIDENCE & CONFLICT PASS] Total Evidence:", len(ev2["workspace"]["evidence_list"]), "| Conflicts Detected:", len(ev2["workspace"]["evidence_conflicts"]))
        assert len(ev2["workspace"]["evidence_list"]) == 2
        assert len(ev2["workspace"]["evidence_conflicts"]) >= 1
        assert ev2["workspace"]["readiness_state"] == "READY_FOR_DECISION"

        # 3. ALTERNATIVES & COMPARISON MATRIX TEST
        alt_res = await dec_service.add_alternative(ws_id, "Option C: Build Hybrid API Gateway", "HIGH", "MEDIUM", "HIGH", "3 Weeks", userA)
        print("--> [3. ALTERNATIVES MATRIX PASS] Alternatives Count:", len(alt_res["workspace"]["alternatives"]))
        assert len(alt_res["workspace"]["alternatives"]) >= 3

        # 4. GROUNDED RECOMMENDATION & COUNTER-EVIDENCE TEST
        rec_res = await dec_service.generate_recommendation(ws_id, userA)
        print("--> [4. GROUNDED RECOMMENDATION PASS] Option:", rec_res["recommended_option_title"], "| Confidence:", rec_res["confidence"], "| Counter-Evidence:", len(rec_res["counter_evidence"]))
        assert rec_res["confidence"] == "STRONG_EVIDENCE"
        assert len(rec_res["counter_evidence"]) >= 1

        # 5. HUMAN FINALIZE DECISION & OVERRIDE RATIONALE TEST
        fin_res = await dec_service.finalize_decision(ws_id, "opt-a", "Option A: Keep Current JWT 30m Spec", "Operational simplicity", "Team experience preference", userA)
        print("--> [5. HUMAN FINALIZE PASS] State:", fin_res["workspace"]["readiness_state"], "| Published Version:", fin_res["workspace"]["final_decision"]["published_version"])
        assert fin_res["success"] is True
        assert fin_res["workspace"]["readiness_state"] == "DECIDED"

        # 6. RETROSPECTIVE & LESSON EXTRACTION TEST
        ret_res = await dec_service.create_retrospective(ws_id, "Zero downtime migration", "Zero downtime achieved with 30m JWT", "SUCCESSFUL", ["30m timeout is optimal for mobile sync."], userA)
        print("--> [6. RETROSPECTIVE PASS] Message:", ret_res["message"])
        assert ret_res["success"] is True

    print("=== MindMesh Phase 6.5 Decision Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_decision_intelligence_master_e2e())
