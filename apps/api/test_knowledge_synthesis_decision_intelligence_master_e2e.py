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
from app.analytics.knowledge_synthesis_decision_intelligence_service import KnowledgeSynthesisDecisionIntelligenceService

async def test_knowledge_synthesis_decision_intelligence_master_e2e():
    print("=== Starting MindMesh Phase 6.25 Knowledge Synthesis & Decision Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Decision Org", slug=f"dec-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Decision Workspace", slug=f"dec-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"dec_user_{u_id}@mindmesh.com",
            username=f"dec_user_{u_id}",
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
        dec_service = KnowledgeSynthesisDecisionIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 203 Verification Checks
        # -------------------------------------------------------------

        # 1. MULTI-SOURCE KNOWLEDGE SYNTHESIS & CONFLICT TEST
        syn = await dec_service.synthesize_knowledge_and_evidence(proj_id, org.id, user)
        print("--> [1. KNOWLEDGE SYNTHESIS PASS] Claims Count:", syn["total_claims"], "| Conflicts Surfaced:", syn["conflicts_surfaced"])
        assert syn["total_claims"] == 2
        assert syn["conflicts_surfaced"] == 1
        assert syn["evidence_bundle"][1]["claim_type"] == "INFERENCE"

        # 2. DECISION CANDIDATE & READINESS TEST
        cand = await dec_service.evaluate_decision_candidate(proj_id, "OAuth 2.0 Migration Strategy", org.id, user)
        print("--> [2. DECISION CANDIDATE PASS] Question:", cand["decision_question"], "| Status:", cand["readiness_status"], "| Missing Gaps:", len(cand["evidence_gaps"]))
        assert cand["readiness_status"] == "NEEDS_EVIDENCE"
        assert len(cand["evidence_gaps"]) == 1

        # 3. OPTION COMPARISON & FEASIBILITY & SENSITIVITY TEST
        comp = await dec_service.compare_decision_options_and_tradeoffs(cand["candidate_id"], [], org.id, user)
        print("--> [3. OPTION COMPARISON PASS] Recommended:", comp["recommended_option"], "| Options Count:", len(comp["evaluated_options"]), "| Sensitivity Stability:", comp["sensitivity_analysis"]["stability"])
        assert comp["recommended_option"] == "opt-A"
        assert comp["evaluated_options"][2]["feasibility"] == "INFEASIBLE"
        assert comp["sensitivity_analysis"]["stability"] == "STABLE"

        # 4. DECISION RECORDING & IMMUTABLE RATIONALE & BRIEF TEST
        rec = await dec_service.record_and_version_decision(
            decision_question=cand["decision_question"],
            chosen_option_id=comp["recommended_option"],
            rationale="Approved Option A to ensure SOC2 compliance without delaying release.",
            supersedes_decision_id=None,
            organization_id=org.id,
            user=user
        )
        print("--> [4. RECORD DECISION PASS] Decision ID:", rec["decision_id"], "| Version:", rec["version"], "| Exec Brief:", rec["decision_brief_drafts"]["executive_brief"][:50] + "...")
        assert rec["version"] == 1
        assert rec["status"] == "RECORDED"

        # 5. DECISION SUPERSESSION VERSIONING TEST
        rec2 = await dec_service.record_and_version_decision(
            decision_question=cand["decision_question"],
            chosen_option_id="opt-A",
            rationale="Updated decision rationale for v2.",
            supersedes_decision_id=rec["decision_id"],
            organization_id=org.id,
            user=user
        )
        print("--> [5. DECISION SUPERSESSION PASS] Version:", rec2["version"], "| Supersedes:", rec2["supersedes_decision_id"])
        assert rec2["version"] == 2
        assert rec2["supersedes_decision_id"] == rec["decision_id"]

        # 6. CLOSED-LOOP OUTCOME & EFFECTIVENESS MONITOR TEST
        out = await dec_service.evaluate_decision_outcome_and_effectiveness(rec["decision_id"], "SOC2 compliance achieved successfully", org.id, user)
        print("--> [6. OUTCOME MONITOR PASS] Matching Status:", out["outcome_matching_status"], "| Effectiveness Score:", out["effectiveness_score"], "| Learning Recorded:", out["learning_signal_recorded_for_phase_620"])
        assert out["outcome_matching_status"] == "MATCHED"
        assert out["effectiveness_score"] == 90
        assert out["learning_signal_recorded_for_phase_620"] is True

    print("=== MindMesh Phase 6.25 Knowledge Synthesis & Decision Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_synthesis_decision_intelligence_master_e2e())
