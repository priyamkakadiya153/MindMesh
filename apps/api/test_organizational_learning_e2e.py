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
from app.learning.learning_service import OrganizationalLearningService

async def test_organizational_learning_e2e():
    print("=== Starting MindMesh Phase 5.4 Organizational Learning Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Learn Org A", slug=f"lrn-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Learn Workspace", slug=f"lrn-wsa-{uuid.uuid4().hex[:6]}")
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
        # Section 141 Master E2E Seeding
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
            title="Authentication Architecture v1",
            filename="auth_arch_v1.md",
            original_filename="auth_arch_v1.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_lrn_1",
            storage_path="/path/lrn1.md",
            uploaded_by=userA.id
        )
        doc2 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch_v2.md",
            original_filename="auth_arch_v2.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_lrn_2",
            storage_path="/path/lrn2.md",
            uploaded_by=userA.id
        )
        doc3 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v3",
            filename="auth_arch_v3.md",
            original_filename="auth_arch_v3.md",
            mime_type="text/markdown",
            extension="md",
            size=3072,
            checksum_sha256="checksum_lrn_3",
            storage_path="/path/lrn3.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2, doc3])
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task)
        await session.commit()

        learn_service = OrganizationalLearningService(session)

        # -------------------------------------------------------------
        # Section 141 Verification Checks
        # -------------------------------------------------------------

        # 1. KNOWLEDGE & DECISION EVOLUTION TRACING TEST
        dec_id = uuid.uuid4()
        evo_res = await learn_service.get_knowledge_evolution("DECISION", dec_id)
        print("--> [1. KNOWLEDGE EVOLUTION PASS] Total Revisions:", evo_res["total_revisions"], "| Evolution History:", [h["value"] for h in evo_res["history"]])
        assert evo_res["total_revisions"] == 3
        assert evo_res["history"][0]["value"] == "JWT Expiry = 15 minutes"
        assert evo_res["history"][1]["value"] == "JWT Expiry = 30 minutes"
        assert evo_res["history"][2]["value"] == "JWT Expiry = 20 minutes"

        # 2. PATTERN & DERIVED INSIGHT DETECTION TEST
        insights = await learn_service.detect_insights(userA, orgA.id, project.id)
        print("--> [2. INSIGHT DETECTION PASS] Total Insights Detected:", len(insights))
        assert len(insights) == 4

        ins_vol = insights[0]
        ins_q = insights[1]

        # 3. INSIGHT CONFIRMATION & DISMISSAL LIFECYCLE TEST
        conf_res = await learn_service.confirm_insight(ins_vol["insight_id"], userA)
        print("--> [3. INSIGHT CONFIRMATION PASS] Title:", conf_res["insight"]["title"], "| Confirmed Status:", conf_res["insight"]["status"])
        assert conf_res["success"] is True
        assert conf_res["insight"]["status"] == "CONFIRMED"

        dism_res = await learn_service.dismiss_insight(ins_q["insight_id"], userA)
        print("--> [4. INSIGHT DISMISSAL PASS] Dismissed Status:", dism_res["insight"]["status"])
        assert dism_res["success"] is True
        assert dism_res["insight"]["status"] == "DISMISSED"

        # 4. KNOWLEDGE REUSE & HISTORICAL DISCOVERY TEST
        reuse_res = await learn_service.get_knowledge_reuse_suggestions(userA, orgA.id, "Authentication")
        print("--> [5. KNOWLEDGE REUSE PASS] Total Suggestions:", len(reuse_res), "| Label:", reuse_res[0]["label"])
        assert len(reuse_res) >= 1
        assert reuse_res[0]["label"] == "Historical Reference"

        # 5. IDEMPOTENT INSIGHT REBUILD TEST
        rebuild_res = await learn_service.rebuild_insights(orgA.id)
        print("--> [6. INSIGHT REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 5.4 Organizational Learning Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_learning_e2e())
