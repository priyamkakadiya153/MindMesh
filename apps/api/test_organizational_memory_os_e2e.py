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
from app.memory.os_service import OrganizationalMemoryOSService

async def test_organizational_memory_os_e2e():
    print("=== Starting MindMesh Phase 5.0 Organizational Memory OS Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Memory OS Org A", slug=f"mos-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Memory Workspace", slug=f"mos-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"mos_usera_{uA_id}@mindmesh.com",
            username=f"mos_usera_{uA_id}",
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
        # Section 121 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-mos-{uuid.uuid4().hex[:6]}",
            description="Memory OS test project"
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
            checksum_sha256="checksum_mos_1",
            storage_path="/path/mos1.md",
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
            checksum_sha256="checksum_mos_2",
            storage_path="/path/mos2.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2])
        await session.commit()

        task1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        task2 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update authentication documentation",
            description="Task to update auth docs.",
            status="IN_PROGRESS"
        )
        session.add_all([task1, task2])
        await session.commit()

        os_service = OrganizationalMemoryOSService(session)

        # -------------------------------------------------------------
        # Section 121 Verification Checks
        # -------------------------------------------------------------

        # 1. MEMORY HOME FEED TEST
        home = await os_service.get_memory_home_feed(userA, orgA.id, scope="ORGANIZATION")
        print("--> [1. MEMORY HOME FEED PASS] Active Project:", home["project_memory"]["name"], "| Knowledge Feed Groups:", len(home["knowledge_feed"]))
        assert home["project_memory"]["name"] == "Authentication System"
        assert len(home["knowledge_feed"]) >= 1

        # 2. ENTITY MEMORY CONTEXT TEST
        e_mem = await os_service.get_entity_memory(userA, orgA.id, "TASK", task1.id)
        print("--> [2. ENTITY MEMORY PASS] Entity Title:", e_mem["identity"]["title"], "| Status:", e_mem["identity"]["status"])
        assert e_mem["identity"]["status"] == "BLOCKED"

        # 3. ONBOARDING BRIEF QUERY TEST
        ob_res = await os_service.query_memory(userA, orgA.id, "I'm new to this project. What should I know?", scope="CURRENT_PROJECT")
        print("--> [3. ONBOARDING BRIEF PASS] Brief Title:", ob_res["answer"]["title"], "| Purpose:", ob_res["answer"]["purpose"])
        assert ob_res["query_type"] == "ONBOARDING_BRIEF"
        assert len(ob_res["answer"]["key_decisions"]) >= 1

        # 4. ATTENTION ITEMS QUERY TEST
        att_res = await os_service.query_memory(userA, orgA.id, "What needs attention?", scope="CURRENT_PROJECT")
        print("--> [4. ATTENTION QUERY PASS] Blocked Tasks Count:", len(att_res["answer"]["blocked_tasks"]))
        assert len(att_res["answer"]["blocked_tasks"]) >= 1

        # 5. MEMORY SYSTEM HEALTH & REINDEX TEST
        hlt = await os_service.audit_memory_health(orgA.id)
        print("--> [5. MEMORY HEALTH PASS] Overall Status:", hlt["overall_status"], "| Search Index:", hlt["search_index"])
        assert hlt["overall_status"] == "HEALTHY"

        reindex_res = await os_service.reindex_memory_system(orgA.id)
        print("--> [6. MEMORY REINDEX PASS] Message:", reindex_res["message"])
        assert reindex_res["success"] is True

    print("=== MindMesh Phase 5.0 Organizational Memory OS Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_memory_os_e2e())
