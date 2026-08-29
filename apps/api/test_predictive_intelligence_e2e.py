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
from app.predictive.predictive_service import PredictiveIntelligenceService

async def test_predictive_intelligence_e2e():
    print("=== Starting MindMesh Phase 5.5 Predictive Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Pred Org A", slug=f"prd-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Pred Workspace", slug=f"prd-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"prd_usera_{uA_id}@mindmesh.com",
            username=f"prd_usera_{uA_id}",
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
        # Section 135 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-prd-{uuid.uuid4().hex[:6]}",
            description="Predictive intelligence test project"
        )
        session.add(project)
        await session.commit()

        doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_prd_1",
            storage_path="/path/prd1.md",
            uploaded_by=userA.id
        )
        session.add(doc)
        await session.commit()

        task1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        task2 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Release Milestone Deployment",
            description="Final release deployment task.",
            status="PENDING"
        )
        session.add_all([task1, task2])
        await session.commit()

        pred_service = PredictiveIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 135 Verification Checks
        # -------------------------------------------------------------

        # 1. EARLY WARNING SYSTEM TEST
        warnings = await pred_service.get_early_warnings(userA, orgA.id, project.id)
        print("--> [1. EARLY WARNING PASS] Total Warnings:", len(warnings), "| Title:", warnings[0]["title"])
        assert len(warnings) >= 2
        assert warnings[0]["severity"] == "CRITICAL"

        # 2. DECISION DOWNSTREAM IMPACT TRACING TEST
        dec_id = str(uuid.uuid4())
        impact = await pred_service.get_decision_impact(dec_id)
        print("--> [2. DECISION IMPACT PASS] Direct Impact Entities:", len(impact["direct_impact"]), "| Title:", impact["decision_title"])
        assert len(impact["direct_impact"]) >= 2

        # 3. WHAT-IF SCENARIO ANALYSIS TEST
        what_if = await pred_service.perform_what_if_analysis("What if deployment remains blocked?", project.id)
        print("--> [3. WHAT-IF SCENARIO PASS] Known Impacts:", len(what_if["known_impacts"]), "| Unknowns:", len(what_if["unknowns"]))
        assert len(what_if["known_impacts"]) >= 2
        assert len(what_if["unknowns"]) >= 1

        # 4. PROJECT RELEASE READINESS ASSESSMENT TEST
        readiness = await pred_service.get_project_readiness(project.id)
        print("--> [4. PROJECT READINESS PASS] Overall Readiness:", readiness["overall_readiness"], "| Blockers Count:", len(readiness["categories"]["blockers"]))
        assert readiness["overall_readiness"] == "ATTENTION_REQUIRED"
        assert len(readiness["categories"]["blockers"]) >= 1

        # 5. DECISION BRIEF GENERATION TEST
        brief = await pred_service.generate_decision_brief("Database Storage Selection")
        print("--> [5. DECISION BRIEF PASS] Options Matrix Count:", len(brief["option_matrix"]), "| Context:", brief["context"])
        assert len(brief["option_matrix"]) == 2

        # 6. IDEMPOTENT PREDICTION REBUILD TEST
        rebuild_res = await pred_service.rebuild_predictions(orgA.id)
        print("--> [6. PREDICTION REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 5.5 Predictive Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_predictive_intelligence_e2e())
