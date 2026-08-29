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
from app.search.universal_search_service import UniversalSearchService

async def test_universal_knowledge_search_e2e():
    print("=== Starting MindMesh Phase 5.7 Universal Search Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Search Org A", slug=f"sch-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Search Workspace", slug=f"sch-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"sch_usera_{uA_id}@mindmesh.com",
            username=f"sch_usera_{uA_id}",
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
        # Section 141 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sch-{uuid.uuid4().hex[:6]}",
            description="Universal search test project"
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
            checksum_sha256="checksum_sch_1",
            storage_path="/path/sch1.md",
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
            checksum_sha256="checksum_sch_2",
            storage_path="/path/sch2.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2])
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task)
        await session.commit()

        search_service = UniversalSearchService(session)

        # -------------------------------------------------------------
        # Section 141 Verification Checks
        # -------------------------------------------------------------

        # 1. HYBRID RETRIEVAL & FUSION TEST
        s_res = await search_service.search("JWT Expiry", "HYBRID", project.id, None, userA, orgA.id)
        print("--> [1. HYBRID RETRIEVAL PASS] Total Results:", s_res["total_results"], "| Entity Types Count:", len(s_res["grouped_results"]))
        assert s_res["total_results"] >= 5
        assert len(s_res["grouped_results"]) >= 4

        # 2. AUTHORITY SIGNAL & CURRENT KNOWLEDGE RANKING TEST
        top_item = s_res["results"][0]
        print("--> [2. AUTHORITY RANKING PASS] Top Ranked Item Title:", top_item["title"], "| Authority Status:", top_item["authority_status"])
        assert top_item["authority_status"] == "CURRENT_GOVERNED"
        assert top_item["entity_type"] == "DECISION"

        # 3. CONTRADICTION DETECTION TEST
        print("--> [3. CONTRADICTION DETECTION PASS] Contradictions Found:", s_res["has_contradictions"], "| Summary:", s_res["contradiction_summary"])
        assert s_res["has_contradictions"] is True

        # 4. RESULT ITEM COMPARISON TEST
        cmp_res = await search_service.compare_results("doc-auth-v1", "doc-auth-v2")
        print("--> [4. RESULT COMPARISON PASS] Summary:", cmp_res["comparison_summary"])
        assert "15 minutes to 30 minutes" in cmp_res["comparison_summary"]

        # 5. AUTOCOMPLETE SUGGESTIONS TEST
        auto_res = await search_service.autocomplete("auth", userA, orgA.id)
        print("--> [5. AUTOCOMPLETE PASS] Suggestions Count:", len(auto_res), "| Top Suggestion:", auto_res[0]["label"])
        assert len(auto_res) >= 3

        # 6. IDEMPOTENT INDEX REBUILD TEST
        rebuild_res = await search_service.rebuild_search_index(orgA.id)
        print("--> [6. INDEX REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 5.7 Universal Search Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_universal_knowledge_search_e2e())
