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
from app.memory.organizational_memory_fabric_service import OrganizationalMemoryFabricService

async def test_org_memory_fabric_master_e2e():
    print("=== Starting MindMesh Phase 6.10 Organizational Memory Fabric Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Memory Fabric Org A", slug=f"fab-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Memory Fabric Workspace", slug=f"fab-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"fab_usera_{uA_id}@mindmesh.com",
            username=f"fab_usera_{uA_id}",
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
        # Section 181 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication Migration",
            slug=f"auth-fab-{uuid.uuid4().hex[:6]}",
            description="Memory fabric test project"
        )
        session.add(project)
        await session.commit()

        mem_service = OrganizationalMemoryFabricService(session)

        # -------------------------------------------------------------
        # Section 181 Verification Checks
        # -------------------------------------------------------------

        # 1. PROJECT MEMORY RETRIEVAL TEST
        pm_res = await mem_service.get_project_memory(project.id, userA)
        print("--> [1. PROJECT MEMORY PASS] Project:", pm_res["project_name"], "| Purpose:", pm_res["purpose"][:50])
        assert pm_res["project_name"] == "Authentication Migration"
        assert len(pm_res["decisions"]) >= 2
        assert len(pm_res["lessons"]) >= 1

        # 2. DECISION MEMORY RATIONALE TEST
        dm_res = await mem_service.get_decision_memory("dec-102", userA)
        print("--> [2. DECISION MEMORY PASS] Chosen Option:", dm_res["chosen_option"], "| Outcome:", dm_res["outcome"])
        assert "OAuth 2.0" in dm_res["chosen_option"]

        # 3. DYNAMIC CONTEXT PACK TEST
        cp_res = await mem_service.generate_context_pack("TASK", "task-deploy-101", userA)
        print("--> [3. DYNAMIC CONTEXT PACK PASS] Title:", cp_res["title"], "| Knowledge Items:", len(cp_res["relevant_knowledge"]))
        assert len(cp_res["relevant_knowledge"]) >= 2
        assert len(cp_res["known_risks"]) >= 1

        # 4. KNOWLEDGE HANDOFF TEST
        hnd_res = await mem_service.create_knowledge_handoff(project.id, "user-recipient-404", userA)
        print("--> [4. KNOWLEDGE HANDOFF PASS] Handoff ID:", hnd_res["handoff_id"], "| Status:", hnd_res["status"])
        assert hnd_res["status"] == "DELIVERED"
        assert len(hnd_res["key_decisions"]) >= 1

        # 5. KNOWLEDGE BRIEF SYNTHESIS TEST
        brief_res = await mem_service.synthesize_knowledge_brief(project.id, userA)
        print("--> [5. KNOWLEDGE BRIEF PASS] Title:", brief_res["brief_title"], "| Sections:", len(brief_res["sections"]))
        assert brief_res["provenance_label"] == "GROUNDED_DERIVED_MEMORY"
        assert len(brief_res["sections"]) >= 2

        # 6. MEMORY HEALTH GAP TEST
        health_res = await mem_service.get_memory_health(orgA.id, userA)
        print("--> [6. MEMORY HEALTH PASS] Coverage:", health_res["memory_coverage"], "| Memory Gaps:", len(health_res["memory_gaps"]))
        assert health_res["memory_gaps"][0]["title"] == "Missing Decision Rationale"

        # 7. MEMORY DIGEST TEST
        dig_res = await mem_service.get_memory_digest(orgA.id, userA)
        print("--> [7. MEMORY DIGEST PASS] Total Objects:", dig_res["total_memory_objects"], "| Handoffs Completed:", dig_res["knowledge_handoffs_completed"])
        assert dig_res["total_memory_objects"] >= 150

    print("=== MindMesh Phase 6.10 Organizational Memory Fabric Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_org_memory_fabric_master_e2e())
