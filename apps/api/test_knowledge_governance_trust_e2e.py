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
from app.governance.trust_service import KnowledgeGovernanceTrustService

async def test_knowledge_governance_trust_e2e():
    print("=== Starting MindMesh Phase 4.6 Knowledge Governance & Trust E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Gov Org A", slug=f"gov-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Gov Workspace", slug=f"gov-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"gov_usera_{uA_id}@mindmesh.com",
            username=f"gov_usera_{uA_id}",
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
        # Section 122 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-gov-{uuid.uuid4().hex[:6]}",
            description="Governance test project"
        )
        session.add(project)
        await session.commit()

        docA = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v1",
            filename="auth_arch_v1.md",
            original_filename="auth_arch_v1.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_v1",
            storage_path="/path/v1.md",
            uploaded_by=userA.id
        )
        docB = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch_v2.md",
            original_filename="auth_arch_v2.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_v2",
            storage_path="/path/v2.md",
            uploaded_by=userA.id
        )
        session.add_all([docA, docB])
        await session.commit()

        gov_service = KnowledgeGovernanceTrustService(session)

        # -------------------------------------------------------------
        # Section 122 Verification Checks
        # -------------------------------------------------------------

        # 1. AI EXTRACTION & REVIEW QUEUE TEST
        item = await gov_service.add_to_review_queue(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            entity_type="DECISION",
            entity_id=uuid.uuid4(),
            title="JWT expiry set to 30 minutes",
            description="Extracted from group conversation.",
            source_type="conversation",
            source_id=uuid.uuid4()
        )
        print("--> [1. AI EXTRACTION PASS] Review Queue Item Status:", item["status"], "| Title:", item["title"])
        assert item["status"] == "NEEDS_REVIEW"

        # 2. CONFIRM AI EXTRACTION TEST
        conf_res = await gov_service.confirm_ai_extraction(
            user=userA,
            organization_id=orgA.id,
            review_item_id=item["id"],
            edited_title="Confirmed: JWT expiry set to 30 minutes"
        )
        print("--> [2. CONFIRM EXTRACTION PASS] Updated Title:", conf_res["item"]["title"], "| New Status:", conf_res["item"]["status"])
        assert conf_res["item"]["status"] == "VERIFIED"

        # 3. CONFLICT DETECTION TEST
        conflict = await gov_service.detect_and_flag_conflict(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            source_a_title=docA.title,
            source_a_content="JWT expires after 15 minutes.",
            source_a_id=docA.id,
            source_b_title=docB.title,
            source_b_content="JWT expires after 30 minutes.",
            source_b_id=docB.id,
            topic="JWT Expiry Duration"
        )
        print("--> [3. CONFLICT DETECTION PASS] Topic:", conflict["topic"], "| Severity:", conflict["severity"])
        assert conflict["severity"] == "POTENTIAL_CONFLICT"

        # 4. CONFLICT RESOLUTION TEST
        res_conflict = await gov_service.resolve_conflict(
            user=userA,
            organization_id=orgA.id,
            conflict_id=conflict["id"],
            winning_source_id=str(docB.id),
            resolution_notes="Document B (30 minutes) is current for production."
        )
        print("--> [4. CONFLICT RESOLUTION PASS] Conflict Status:", res_conflict["conflict"]["status"], "| Winning Source:", res_conflict["conflict"]["winning_source_id"])
        assert res_conflict["conflict"]["status"] == "RESOLVED"

        # 5. SOURCE OF TRUTH MARKING TEST
        sot_res = await gov_service.set_source_of_truth(
            user=userA,
            organization_id=orgA.id,
            project_id=project.id,
            entity_id=docB.id,
            entity_title=docB.title
        )
        print("--> [5. SOURCE OF TRUTH PASS] Project SOT ID:", sot_res["source_of_truth_id"])
        assert sot_res["source_of_truth_id"] == str(docB.id)

        # 6. GOVERNANCE AUDIT TRAIL LOG TEST
        audit_log = await gov_service.get_governance_audit_log(orgA.id)
        print("--> [6. AUDIT TRAIL PASS] Total Governance Log Entries:", len(audit_log), "| Latest Action:", audit_log[-1]["action"])
        assert len(audit_log) >= 3

    print("=== MindMesh Phase 4.6 Knowledge Governance & Trust E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_governance_trust_e2e())
