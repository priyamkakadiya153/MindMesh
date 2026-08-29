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
from app.quality.knowledge_quality_service import KnowledgeQualityService

async def test_knowledge_quality_master_e2e():
    print("=== Starting MindMesh Phase 6.1 Knowledge Quality Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Quality Org A", slug=f"qlt-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Quality Workspace", slug=f"qlt-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"qlt_usera_{uA_id}@mindmesh.com",
            username=f"qlt_usera_{uA_id}",
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
        # Section 147 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-qlt-{uuid.uuid4().hex[:6]}",
            description="Knowledge quality test project"
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
            checksum_sha256="checksum_qlt_1",
            storage_path="/path/qlt1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        quality_service = KnowledgeQualityService(session)

        # -------------------------------------------------------------
        # Section 147 Verification Checks
        # -------------------------------------------------------------

        # 1. READ-ONLY INITIAL QUALITY SCAN TEST
        scan_res = await quality_service.run_quality_scan(orgA.id, project.id, userA)
        print("--> [1. QUALITY SCAN PASS] Checked:", scan_res["items_checked"], "| Issues Found:", scan_res["issues_found"])
        assert scan_res["items_checked"] >= 10
        assert scan_res["issues_found"] >= 4

        # 2. STALE KNOWLEDGE EXPLANATION TEST
        issues = await quality_service.get_quality_issues(orgA.id, "STALE")
        stale_iss = issues[0]
        print("--> [2. STALE KNOWLEDGE PASS] Title:", stale_iss["title"], "| Reason:", stale_iss["reason"][:60], "...")
        assert stale_iss["severity"] in ["IMPORTANT", "CRITICAL"]
        assert len(stale_iss["evidence"]) >= 2

        # 3. MISSING OWNER ASSIGNMENT TEST
        assign_res = await quality_service.assign_owner("doc-draft-policy", str(userA.id), userA)
        print("--> [3. MISSING OWNER ASSIGN PASS] Message:", assign_res["message"])
        assert assign_res["success"] is True

        # 4. DUPLICATE KEEP SEPARATE TEST
        sep_res = await quality_service.keep_separate("iss-dupl-103", userA)
        print("--> [4. KEEP SEPARATE PASS] Resolution Note:", sep_res["issue"]["resolution_note"])
        assert sep_res["success"] is True
        assert sep_res["issue"]["status"] == "RESOLVED"

        # 5. SAFE MERGE WORKFLOW TEST
        merge_res = await quality_service.merge_duplicates("doc-auth-v2", "doc-auth-design", userA)
        print("--> [5. SAFE MERGE PASS] Message:", merge_res["message"])
        assert merge_res["success"] is True

        # 6. AGGREGATE HEALTH METRICS RETRIEVAL TEST
        health_res = await quality_service.get_knowledge_health(orgA.id)
        print("--> [6. KNOWLEDGE HEALTH PASS] Needs Attention:", health_res["needs_attention_count"], "| Issues Total:", len(health_res["issues"]))
        assert len(health_res["issues"]) >= 4

    print("=== MindMesh Phase 6.1 Knowledge Quality Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_quality_master_e2e())
