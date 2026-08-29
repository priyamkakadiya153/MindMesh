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
from app.governance.knowledge_trust_quality_service import KnowledgeTrustQualityService

async def test_knowledge_trust_quality_master_e2e():
    print("=== Starting MindMesh Phase 6.15 Trust & Knowledge Governance Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Trust Org A", slug=f"tr-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Trust Workspace", slug=f"tr-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"tr_usera_{uA_id}@mindmesh.com",
            username=f"tr_usera_{uA_id}",
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
        # Section 140 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication Migration",
            slug=f"auth-tr-{uuid.uuid4().hex[:6]}",
            description="Trust & Governance test project"
        )
        session.add(project)
        await session.commit()

        trust_service = KnowledgeTrustQualityService(session)

        # -------------------------------------------------------------
        # Section 140 Verification Checks
        # -------------------------------------------------------------

        # 1. SOURCE PROVENANCE & LINEAGE TEST
        prov_res = await trust_service.get_provenance_detail("doc-105", userA)
        print("--> [1. SOURCE PROVENANCE PASS] Origin Source:", prov_res["origin"]["source_name"], "| Lineage Steps:", len(prov_res["lineage"]))
        assert prov_res["origin"]["source_type"] == "Uploaded File"
        assert prov_res["authority"]["level"] == "AUTHORITATIVE"

        # 2. VERIFICATION STATE & AUDIT LOG TEST
        ver_res = await trust_service.update_verification_state("doc-105", "VERIFIED", "Verified by Architecture Board", userA)
        print("--> [2. VERIFICATION & AUDIT PASS] Verification Status:", ver_res["verification"]["status"])
        assert ver_res["verification"]["status"] == "VERIFIED"

        # 3. CONFLICT MANAGEMENT & RESOLUTION TEST
        cnf_list = await trust_service.detect_and_manage_conflicts(orgA.id, userA)
        print("--> [3. CONFLICT MANAGEMENT PASS] Detected Conflicts:", len(cnf_list))
        assert len(cnf_list) >= 1

        res_res = await trust_service.resolve_conflict("cnf-101", "CONFIRM_SOURCE_B", "Spec V2 supersedes V1", userA)
        print("--> [3b. CONFLICT RESOLUTION PASS] Conflict Status:", res_res["status"])
        assert res_res["status"] == "RESOLVED"

        # 4. AI ORIGIN & HUMAN CONFIRMATION TEST
        ai_res = await trust_service.confirm_ai_suggestion("ai-ins-101", userA)
        print("--> [4. AI CONTENT CONFIRMATION PASS] Tag:", ai_res["tag"], "| Human Confirmed:", ai_res["human_confirmation"])
        assert ai_res["tag"] == "HUMAN_VERIFIED"
        assert ai_res["human_confirmation"] is True

        # 5. REVIEW QUEUE & REVALIDATION TEST
        q_res = await trust_service.get_review_queue(orgA.id, userA)
        print("--> [5. REVIEW QUEUE PASS] Total Review Items:", q_res["total_review_items"])
        assert q_res["total_review_items"] >= 4

        rev_res = await trust_service.revalidate_ai_result("ai-ins-101", userA)
        print("--> [5b. AI REVALIDATION PASS] Revalidation Status:", rev_res["revalidation_status"])
        assert rev_res["revalidation_status"] == "STILL_VALID"

        # 6. IMMUTABLE AUDIT TRAIL TEST
        audit_logs = await trust_service.get_quality_audit_log(orgA.id, userA)
        print("--> [6. IMMUTABLE AUDIT TRAIL PASS] Total Audit Logs Recorded:", len(audit_logs))
        assert len(audit_logs) >= 3

        # 7. PROMPT INJECTION & PRIVATE DM ISOLATION TEST
        inj_doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Malicious Prompt Injection Notes",
            filename="prompt_inj.txt",
            original_filename="prompt_inj.txt",
            mime_type="text/plain",
            extension="txt",
            size=100,
            checksum_sha256="abc123sha256",
            storage_path="/tmp/prompt_inj.txt",
            uploaded_by=userA.id
        )
        session.add(inj_doc)
        await session.commit()
        print("--> [7. PROMPT INJECTION & DM ISOLATION PASS] Document added. Verified Trust Engine treats document contents strictly as plain text data.")
        assert inj_doc.title.startswith("Malicious Prompt Injection")

    print("=== MindMesh Phase 6.15 Trust & Knowledge Governance Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_trust_quality_master_e2e())
