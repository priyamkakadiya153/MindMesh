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
from app.maintenance.knowledge_maintenance_service import KnowledgeMaintenanceService

async def test_knowledge_maintenance_master_e2e():
    print("=== Starting MindMesh Phase 6.8 Autonomous Knowledge Maintenance Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Maintenance Org A", slug=f"mnt-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Maintenance Workspace", slug=f"mnt-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"mnt_usera_{uA_id}@mindmesh.com",
            username=f"mnt_usera_{uA_id}",
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
        # Section 173 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-mnt-{uuid.uuid4().hex[:6]}",
            description="Knowledge maintenance test project"
        )
        session.add(project)
        await session.commit()

        mnt_service = KnowledgeMaintenanceService(session)

        # -------------------------------------------------------------
        # Section 173 Verification Checks
        # -------------------------------------------------------------

        # 1. IMPACT-AWARE REVIEW QUEUE TEST
        rq_res = await mnt_service.get_review_queue(orgA.id, userA)
        print("--> [1. REVIEW QUEUE PASS] Total Items:", len(rq_res), "| Top Priority:", rq_res[0]["priority"])
        assert len(rq_res) >= 2
        assert rq_res[0]["priority"] == "HIGH"
        assert rq_res[1]["priority"] == "LOW"

        # 2. CANONICAL CANDIDATE & MERGE PREVIEW TEST
        can_res = await mnt_service.scan_canonical_candidates(project.id, userA)
        print("--> [2. CANONICAL CANDIDATES PASS] Candidates:", len(can_res), "| Recommended:", can_res[0]["recommended_canonical_doc"])
        assert len(can_res) >= 1

        mp_res = await mnt_service.generate_merge_preview("doc-auth-v1", "doc-auth-v2", userA)
        print("--> [2b. MERGE PREVIEW PASS] Differences Count:", len(mp_res["differences"]), "| Result:", mp_res["proposed_result"])
        assert len(mp_res["differences"]) >= 2

        # 3. CONTEXT-AWARE MEMORY RETRIEVAL TEST
        ctx_a = await mnt_service.context_aware_search("What is authentication spec?", "PROJECT_A", userA)
        ctx_b = await mnt_service.context_aware_search("What is authentication spec?", "PROJECT_B", userA)
        print("--> [3. CONTEXT MEMORY PASS] Project A Answer:", ctx_a["answer"], "| Project B Answer:", ctx_b["answer"])
        assert "OAuth" in ctx_a["answer"]
        assert "JWT" in ctx_b["answer"]

        # 4. REVALIDATION & GOVERNANCE SAFEGUARD TEST
        rev_res = await mnt_service.revalidate_knowledge("doc-auth-v2", "STILL_VALID", userA)
        print("--> [4. REVALIDATION PASS] Message:", rev_res["message"])
        assert rev_res["success"] is True

        # 5. AUTOMATIC DERIVED INDEX SELF-HEALING TEST
        heal_res = await mnt_service.self_heal_index(orgA.id, userA)
        print("--> [5. SELF-HEALING INDEX PASS] Repaired Chunks:", heal_res["repaired_chunks"], "| Source Altered:", heal_res["source_text_altered"])
        assert heal_res["success"] is True
        assert heal_res["source_text_altered"] is False

        # 6. MAINTENANCE DIGEST RETRIEVAL TEST
        dig_res = await mnt_service.get_maintenance_digest(orgA.id, userA)
        print("--> [6. DIGEST PASS] Total Review Items:", dig_res["total_review_items"], "| Self-Healed Count:", dig_res["self_healed_indices_count"])
        assert dig_res["total_review_items"] >= 2

    print("=== MindMesh Phase 6.8 Autonomous Knowledge Maintenance Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_maintenance_master_e2e())
