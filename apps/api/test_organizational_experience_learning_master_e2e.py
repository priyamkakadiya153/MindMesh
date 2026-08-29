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
from app.analytics.organizational_experience_learning_service import OrganizationalExperienceLearningService

async def test_organizational_experience_learning_master_e2e():
    print("=== Starting MindMesh Phase 6.26 Organizational Memory Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Experience Org", slug=f"exp-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Experience Workspace", slug=f"exp-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"exp_user_{u_id}@mindmesh.com",
            username=f"exp_user_{u_id}",
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
        exp_service = OrganizationalExperienceLearningService(session)

        # -------------------------------------------------------------
        # Section 201 Verification Checks
        # -------------------------------------------------------------

        # 1. EXPERIENCE RECORD CAPTURE TEST
        rec = await exp_service.capture_experience_record(
            title="Auth0 Identity Provider Rollout",
            situation="Legacy custom token service had 14-day decision block.",
            action="Adopted Auth0 SaaS SDK and configured 15-min refresh rotation.",
            outcome="Achieved SOC2 compliance with 0 milestone delay.",
            project_id=proj_id,
            organization_id=org.id,
            user=user
        )
        print("--> [1. EXPERIENCE CAPTURE PASS] Record ID:", rec["record_id"], "| Status:", rec["validation_status"], "| Lessons Extracted:", len(rec["lessons_extracted"]))
        assert rec["validation_status"] == "VALIDATED"
        assert len(rec["lessons_extracted"]) == 1

        # 2. EXPECTED VS ACTUAL OUTCOME ATTRIBUTION TEST
        out = await exp_service.analyze_outcome_attribution(
            project_id=proj_id,
            expected_outcome="SOC2 compliance with 0 delay",
            actual_outcome="SOC2 compliance achieved with 0 delay",
            organization_id=org.id,
            user=user
        )
        print("--> [2. OUTCOME ATTRIBUTION PASS] Classification:", out["outcome_classification"], "| Contributing Factors:", len(out["contributing_factors"]))
        assert out["outcome_classification"] == "SUCCESSFUL"
        assert len(out["contributing_factors"]) == 2

        # 3. LESSON EXTRACTION & CROSS-PROJECT PATTERN DISCOVERY TEST
        lp = await exp_service.extract_lessons_and_patterns(org.id, user)
        print("--> [3. LESSONS & PATTERNS PASS] Lessons Count:", len(lp["extracted_lessons"]), "| Patterns Count:", len(lp["detected_patterns"]), "| Pattern Title:", lp["detected_patterns"][0]["title"])
        assert len(lp["extracted_lessons"]) == 1
        assert lp["detected_patterns"][0]["pattern_type"] == "SUCCESS_PATTERN"

        # 4. RETROSPECTIVE DRAFT & FACT/OPINION SEPARATION TEST
        pr = await exp_service.generate_playbook_and_retrospective(proj_id, org.id, user)
        retro = pr["retrospective_draft"]
        print("--> [4. RETROSPECTIVE DRAFT PASS] Events:", len(retro["observed_events"]), "| Interpretations:", len(retro["interpretations"]), "| Opinions:", len(retro["opinions"]))
        assert len(retro["observed_events"]) == 2
        assert len(retro["opinions"]) == 1

        # 5. REUSABLE PLAYBOOK & DRIFT STATUS TEST
        pb = pr["playbook_candidate"]
        print("--> [5. REUSABLE PLAYBOOK PASS] Playbook Title:", pb["title"], "| Status:", pb["status"], "| Drift Status:", pb["drift_status"])
        assert pb["status"] == "VALIDATED"
        assert pb["drift_status"] == "STABLE"

        # 6. CONTINUOUS IMPROVEMENT BACKLOG & BENEFIT MEASUREMENT TEST
        imp = await exp_service.manage_continuous_improvement(
            problem_description="Manual microservice Auth setup takes 4 hours.",
            proposal="Automate OAuth setup via standardized Playbook CLI script.",
            organization_id=org.id,
            user=user
        )
        print("--> [6. CONTINUOUS IMPROVEMENT PASS] Opportunity ID:", imp["opportunity_id"], "| Status:", imp["status"], "| Measured Actual:", imp["metrics"]["actual"])
        assert imp["classification"] == "QUICK_WIN"
        assert imp["phase_621_execution_plan_prepared"] is True

    print("=== MindMesh Phase 6.26 Organizational Memory Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_experience_learning_master_e2e())
