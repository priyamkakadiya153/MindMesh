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
from app.governance.knowledge_governance_service import KnowledgeGovernanceService

async def test_knowledge_governance_master_e2e():
    print("=== Starting MindMesh Phase 6.0 Knowledge Governance Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Governance Org A", slug=f"gov-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Governance Workspace", slug=f"gov-wsa-{uuid.uuid4().hex[:6]}")
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
        # Section 161 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-gov-{uuid.uuid4().hex[:6]}",
            description="Knowledge governance test project"
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
            checksum_sha256="checksum_gov_1",
            storage_path="/path/gov1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        gov_service = KnowledgeGovernanceService(session)
        doc_id = str(doc1.id)

        # -------------------------------------------------------------
        # Section 161 Verification Checks
        # -------------------------------------------------------------

        # 1. SUBMIT FOR REVIEW TEST
        sub_res = await gov_service.submit_for_review(doc_id, "DOCUMENT", reviewer_id="reviewer-admin", user=userA)
        print("--> [1. SUBMIT FOR REVIEW PASS] Status:", sub_res["entity"]["status"], "| Trust Label:", sub_res["entity"]["trust_label"])
        assert sub_res["entity"]["status"] == "UNDER_REVIEW"
        assert sub_res["entity"]["trust_label"] == "Needs Review"

        # 2. APPROVAL & IMMUTABLE AUDIT LOGGING TEST
        app_res = await gov_service.approve_version(doc_id, "v1", userA)
        print("--> [2. APPROVAL PASS] Status:", app_res["entity"]["status"], "| Version:", app_res["entity"]["version"])
        assert app_res["entity"]["status"] == "APPROVED"
        assert app_res["entity"]["trust_label"] == "Approved"

        audit_logs = await gov_service.get_audit_log(doc_id)
        print("--> [2b. IMMUTABLE AUDIT PASS] Audit Entries Count:", len(audit_logs), "| Last Action:", audit_logs[-1]["action"])
        assert len(audit_logs) >= 2
        assert audit_logs[-1]["action"] == "APPROVE_VERSION"

        # 3. REQUEST CHANGES & REJECTION TEST
        req_res = await gov_service.request_changes(doc_id, "Update JWT section to specify 30m expiry", userA)
        print("--> [3a. REQUEST CHANGES PASS] Status:", req_res["entity"]["status"])
        assert req_res["entity"]["status"] == "CHANGES_REQUESTED"

        rej_res = await gov_service.reject_version(doc_id, "Outdated JWT expiry specs", userA)
        print("--> [3b. REJECTION PASS] Status:", rej_res["entity"]["status"], "| Reason:", rej_res["entity"]["rejection_reason"])
        assert rej_res["entity"]["status"] == "REJECTED"

        # 4. CONFLICT DETECTION & HUMAN RESOLUTION TEST
        conf_res = await gov_service.resolve_conflict("conflict-101", "CURRENT_DECISION_OVERRIDE", "dec-jwt-30m", "doc-auth-v1", userA)
        print("--> [4. CONFLICT RESOLUTION PASS] Message:", conf_res["message"], "| Strategy:", conf_res["resolution"]["resolution_strategy"])
        assert conf_res["success"] is True

        # 5. ARCHIVING & VERSION RESTORATION TEST
        arch_res = await gov_service.archive_entity(doc_id, userA)
        print("--> [5a. ARCHIVE PASS] Status:", arch_res["entity"]["status"])
        assert arch_res["entity"]["status"] == "ARCHIVED"

        rest_res = await gov_service.restore_version(doc_id, "v1", userA)
        print("--> [5b. RESTORE PASS] Status:", rest_res["entity"]["status"], "| New Version:", rest_res["entity"]["version"])
        assert rest_res["entity"]["status"] == "DRAFT"
        assert "v" in rest_res["entity"]["version"]

        # 6. GOVERNANCE REVIEW QUEUE RETRIEVAL TEST
        queue_res = await gov_service.get_review_queue(orgA.id, "ALL")
        print("--> [6. GOVERNANCE QUEUE PASS] Active Queue Items Count:", len(queue_res))
        assert len(queue_res) >= 3

    print("=== MindMesh Phase 6.0 Knowledge Governance Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_governance_master_e2e())
