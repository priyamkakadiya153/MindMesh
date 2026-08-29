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
from app.governance.governance_engine_service import GovernanceEngineService

async def test_governance_engine_master_e2e():
    print("=== Starting MindMesh Phase 6.30 Governance Engine Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Governance Org", slug=f"gov-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Governance Workspace", slug=f"gov-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"gov_user_{u_id}@mindmesh.com",
            username=f"gov_user_{u_id}",
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

        gov_service = GovernanceEngineService(session)

        # -------------------------------------------------------------
        # Section 201 Verification Checks
        # -------------------------------------------------------------

        # 1. POLICY CREATION & APPROVAL TEST
        pol = await gov_service.create_or_update_policy(
            name="Confidential AI Data Processing Policy",
            description="Confidential organizational data must not be sent to external AI providers without security approval.",
            category="AI",
            scope="ORGANIZATION",
            effect="REQUIRE_APPROVAL",
            rules={"target_classification": "Confidential", "action": "EXTERNAL_AI_PROCESSING"},
            organization_id=org.id,
            user=user
        )
        print("--> [1. POLICY CREATION PASS] Policy ID:", pol["policy_id"], "| Status:", pol["status"], "| Effect:", pol["effect"])
        assert pol["status"] == "ACTIVE"

        # 2. PRE-ACTION POLICY EVALUATION TEST (Confidential -> Approval Required)
        eval_req = await gov_service.evaluate_policy(
            action="EXTERNAL_AI_PROCESSING",
            data_classification="Confidential",
            target_resource="doc-confidential-spec-99",
            context={},
            organization_id=org.id,
            user=user
        )
        print("--> [2. PRE-ACTION EVALUATION PASS] Decision:", eval_req["decision"], "| Reason:", eval_req["reason"])
        assert eval_req["decision"] == "APPROVAL_REQUIRED"

        # 3. UNAUTHORIZED BYPASS PREVENTION TEST
        eval_bypass = await gov_service.evaluate_policy(
            action="EXTERNAL_AI_PROCESSING",
            data_classification="Confidential",
            target_resource="doc-confidential-spec-99",
            context={"attempting_bypass": True},
            organization_id=org.id,
            user=user
        )
        print("--> [3. BYPASS BLOCK PASS] Decision:", eval_bypass["decision"], "| Result Code:", eval_bypass["result_code"])
        assert eval_bypass["decision"] == "DENIED"

        # 4. TEMPORARY EXCEPTION APPROVAL & EXPIRED EVALUATION TEST
        exc = await gov_service.request_policy_exception(pol["policy_id"], "SOC2 audit exception", 24, org.id, user)
        print("--> [4. TEMPORARY EXCEPTION PASS] Exception ID:", exc["exception_id"], "| Temporary:", exc["is_temporary"])
        assert exc["status"] == "APPROVED"

        eval_exc = await gov_service.evaluate_policy(
            action="EXTERNAL_AI_PROCESSING",
            data_classification="Confidential",
            target_resource="doc-confidential-spec-99",
            context={"has_active_exception": True},
            organization_id=org.id,
            user=user
        )
        print("--> [5. EXCEPTION EVALUATION PASS] Decision:", eval_exc["decision"])
        assert eval_exc["decision"] == "ALLOWED_VIA_EXCEPTION"

        # 5. POLICY SIMULATION & IMPACT ANALYSIS TEST
        sim = await gov_service.simulate_policy_impact("Prohibit external AI model processing for backend source code", org.id, user)
        print("--> [6. SIMULATION PASS] Mode:", sim["mode"], "| Impact Warning:", sim["impact_warning"])
        assert sim["mode"] == "MONITOR_ONLY_DRY_RUN"
        assert sim["affected_entities"]["active_workflows_blocked"] == 3

        # 6. GOVERNANCE AUDIT & VIOLATION TRAIL TEST
        audit = await gov_service.list_governance_audit(org.id, user)
        print("--> [7. GOVERNANCE AUDIT PASS] Compliance Status:", audit["compliance_indicators"]["compliance_status"], "| Violations Count:", len(audit["violations"]))
        assert audit["compliance_indicators"]["compliance_status"] == "COMPLIANT_WITH_GUARDRAILS"

    print("=== MindMesh Phase 6.30 Governance Engine Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_governance_engine_master_e2e())
