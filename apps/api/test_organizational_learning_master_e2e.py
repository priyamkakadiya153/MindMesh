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
from app.learning.organizational_learning_service import OrganizationalLearningService

async def test_organizational_learning_master_e2e():
    print("=== Starting MindMesh Phase 6.4 Organizational Learning Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Learning Org A", slug=f"lrn-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Learning Workspace", slug=f"lrn-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"lrn_usera_{uA_id}@mindmesh.com",
            username=f"lrn_usera_{uA_id}",
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
        # Section 161 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-lrn-{uuid.uuid4().hex[:6]}",
            description="Organizational learning test project"
        )
        session.add(project)
        await session.commit()

        doc1 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_lrn_1",
            storage_path="/path/lrn1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        learning_service = OrganizationalLearningService(session)

        # -------------------------------------------------------------
        # Section 161 Verification Checks
        # -------------------------------------------------------------

        # 1. EXPLICIT FEEDBACK SUBMISSION TEST
        fb_res = await learning_service.submit_feedback(str(doc1.id), "DOCUMENT", "EXPLICIT", "OUTDATED", "15m spec superseded by D-102 30m", userA)
        print("--> [1. FEEDBACK PASS] Quality Signal Created:", fb_res["quality_signal_created"], "| Message:", fb_res["message"])
        assert fb_res["success"] is True
        assert fb_res["quality_signal_created"] is True

        # 2. HUMAN-IN-THE-LOOP CORRECTION WORKFLOW TEST
        prop_res = await learning_service.propose_correction(str(doc1.id), "Auth Arch v2: JWT Expiry updated to 30m.", "Decision D-102 update", userA)
        cor_id = prop_res["correction"]["correction_id"]
        print("--> [2. PROPOSE CORRECTION PASS] Correction ID:", cor_id, "| Status:", prop_res["correction"]["status"])
        assert prop_res["correction"]["status"] == "PROPOSED"

        app_res = await learning_service.approve_correction(cor_id, userA)
        print("--> [2b. APPROVE CORRECTION PASS] Message:", app_res["message"], "| Published Version:", app_res["correction"]["published_version"])
        assert app_res["success"] is True
        assert app_res["correction"]["status"] == "APPROVED"
        assert app_res["correction"]["published_version"] == "v2"

        # 3. ZERO-RESULT SEARCH & KNOWLEDGE GAP RETRIEVAL TEST
        gaps_res = await learning_service.get_knowledge_gaps(orgA.id, userA)
        print("--> [3. KNOWLEDGE GAPS PASS] Gaps Count:", len(gaps_res), "| Top Query:", gaps_res[0]["query"])
        assert len(gaps_res) >= 1
        assert gaps_res[0]["priority"] == "HIGH"

        # 4. QUESTION CLUSTERING RETRIEVAL TEST
        qcls_res = await learning_service.get_question_clusters(orgA.id, userA)
        print("--> [4. QUESTION CLUSTER PASS] Cluster Topic:", qcls_res[0]["topic"], "| Sample Queries Count:", len(qcls_res[0]["sample_questions"]))
        assert len(qcls_res) >= 1
        assert len(qcls_res[0]["sample_questions"]) >= 3

        # 5. GOVERNED ORGANIZATIONAL PLAYBOOK CREATION TEST
        pb_res = await learning_service.create_playbook("Production Deployment Playbook", ["Verify JWT expiry = 30m", "Run master tests"], userA)
        print("--> [5. PLAYBOOK CREATION PASS] Playbook ID:", pb_res["playbook"]["playbook_id"], "| Steps Count:", len(pb_res["playbook"]["steps"]))
        assert pb_res["success"] is True
        assert len(pb_res["playbook"]["steps"]) == 2

        # 6. LEARNING ANALYTICS RETRIEVAL TEST
        ana_res = await learning_service.get_learning_analytics(orgA.id)
        print("--> [6. ANALYTICS PASS] Total Feedback Events:", ana_res["total_feedback_events"], "| Helpful Rate:", ana_res["helpful_rate"])
        assert ana_res["total_feedback_events"] >= 1

    print("=== MindMesh Phase 6.4 Organizational Learning Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_learning_master_e2e())
