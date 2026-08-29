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
from app.compliance.compliance_intelligence_service import ComplianceIntelligenceService

async def test_compliance_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.31 Compliance Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Compliance Org", slug=f"cmp-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Compliance Workspace", slug=f"cmp-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"cmp_user_{u_id}@mindmesh.com",
            username=f"cmp_user_{u_id}",
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

        cmp_service = ComplianceIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 200 Verification Checks
        # -------------------------------------------------------------

        # 1. FRAMEWORK & CONTROL MAPPING TEST
        fws = await cmp_service.list_frameworks_and_controls(org.id, user)
        print("--> [1. FRAMEWORK & CONTROL MAPPING PASS] Framework:", fws["frameworks"][0]["name"], "| Control Count:", len(fws["controls"]))
        assert len(fws["frameworks"]) == 1
        assert len(fws["controls"]) == 2

        # 2. AUTOMATED CONTROL TESTING & FAILURE GAP DETECTION TEST
        tst_fail = await cmp_service.test_compliance_control("ctrl-sec-01", "AUTOMATED", simulate_failure=True, organization_id=org.id, user=user)
        print("--> [2. CONTROL TEST FAILURE PASS] Result:", tst_fail["result"], "| Gap Detected:", tst_fail["gap_detected"]["classification"])
        assert tst_fail["result"] == "FAIL"
        assert tst_fail["gap_detected"] is not None

        # 3. EVIDENCE COLLECTION & SHA-256 CHECKSUM INTEGRITY TEST
        evd = await cmp_service.collect_compliance_evidence("ctrl-sec-01", "LOG", "Audit Log Content Payload 12345", org.id, user)
        print("--> [3. EVIDENCE PROVENANCE & HASH PASS] Evidence ID:", evd["evidence_id"], "| Checksum:", evd["sha256_checksum"][:10], "| Freshness:", evd["freshness"])
        assert evd["freshness"] == "CURRENT"
        assert len(evd["sha256_checksum"]) == 64

        # 4. REMEDIATION & FAILED VERIFICATION REOPENING TEST
        rem_fail = await cmp_service.remediate_finding(None, "Production AI Model Authorization Bypass", "HIGH", verification_passed=False, organization_id=org.id, user=user)
        print("--> [4. FAILED VERIFICATION REOPEN PASS] Finding ID:", rem_fail["finding_id"], "| Status:", rem_fail["status"])
        assert rem_fail["status"] == "OPEN_REOPENED"

        # 5. SUCCESSFUL RE-VERIFICATION & RESOLUTION TEST
        rem_pass = await cmp_service.remediate_finding(rem_fail["finding_id"], "Production AI Model Authorization Bypass", "HIGH", verification_passed=True, organization_id=org.id, user=user)
        print("--> [5. SUCCESSFUL VERIFICATION PASS] Finding ID:", rem_pass["finding_id"], "| Status:", rem_pass["status"])
        assert rem_pass["status"] == "RESOLVED"

        # 6. ENTERPRISE RISK REGISTER & TEMPORARY RISK ACCEPTANCE TEST
        risk = await cmp_service.accept_residual_risk("External AI Access to Non-Confidential Specs", "Security", 80, 24, org.id, user)
        print("--> [6. RISK ACCEPTANCE PASS] Risk ID:", risk["risk_id"], "| Inherent:", risk["inherent_score"], "| Residual:", risk["residual_score"], "| Expires At:", risk["acceptance_record"]["expires_at"])
        assert risk["status"] == "TEMPORARILY_ACCEPTED"

        # 7. AUDIT READINESS & UNKNOWN STATE PRESERVATION TEST
        readiness_missing = await cmp_service.assess_audit_readiness(missing_evidence=True, organization_id=org.id, user=user)
        print("--> [7. UNKNOWN STATE PRESERVATION PASS] Status:", readiness_missing["overall_status"], "| Readiness Warning:", readiness_missing["readiness_warning"])
        assert readiness_missing["overall_status"] == "UNKNOWN"

        readiness_ready = await cmp_service.assess_audit_readiness(missing_evidence=False, organization_id=org.id, user=user)
        print("--> [8. AUDIT READINESS PACKAGE PASS] Status:", readiness_ready["overall_status"], "| Package SHA-256:", readiness_ready["audit_package"]["package_sha256"][:10])
        assert readiness_ready["overall_status"] == "COMPLIANT"
        assert readiness_ready["audit_package"] is not None

    print("=== MindMesh Phase 6.31 Compliance Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_compliance_intelligence_master_e2e())
