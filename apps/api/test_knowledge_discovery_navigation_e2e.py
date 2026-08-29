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
from app.knowledge.discovery_service import KnowledgeDiscoveryNavigationService

async def test_knowledge_discovery_navigation_e2e():
    print("=== Starting MindMesh Phase 4.8 Knowledge Discovery & Intelligent Navigation E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Disc Org A", slug=f"dsc-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Disc Workspace", slug=f"dsc-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"dsc_usera_{uA_id}@mindmesh.com",
            username=f"dsc_usera_{uA_id}",
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
        # Section 133 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-dsc-{uuid.uuid4().hex[:6]}",
            description="Discovery test project"
        )
        session.add(project)
        await session.commit()

        doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_dsc_1",
            storage_path="/path/dsc1.md",
            uploaded_by=userA.id
        )
        dst_file = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="authentication-design.dst",
            filename="authentication-design.dst",
            original_filename="authentication-design.dst",
            mime_type="application/octet-stream",
            extension="dst",
            size=4096,
            checksum_sha256="checksum_dst_dsc_1",
            storage_path="/path/design_dsc.dst",
            uploaded_by=userA.id
        )
        session.add_all([doc, dst_file])
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

        disc_service = KnowledgeDiscoveryNavigationService(session)

        # -------------------------------------------------------------
        # Section 133 Verification Checks
        # -------------------------------------------------------------

        # 1. CATEGORIZED RELATED KNOWLEDGE RETRIEVAL TEST
        rel_res = await disc_service.get_related_knowledge(userA, orgA.id, "DOCUMENT", doc.id)
        print("--> [1. RELATED KNOWLEDGE PASS] Entity ID:", rel_res["entity_id"], "| Directly Related Items:", len(rel_res["categories"]["directly_related"]))
        assert len(rel_res["categories"]["directly_related"]) >= 1
        assert len(rel_res["categories"]["historical"]) >= 1

        # 2. KNOWLEDGE PATH & BREADCRUMBS TEST
        path_res = await disc_service.get_knowledge_path(userA, orgA.id, project.id, task.id)
        print("--> [2. KNOWLEDGE PATH PASS] Project Name:", path_res["project_name"], "| Breadcrumbs Count:", len(path_res["breadcrumbs"]))
        assert len(path_res["breadcrumbs"]) == 3

        # 3. BOOKMARK KNOWLEDGE TEST
        bm_res = await disc_service.bookmark_knowledge(
            user_id=userA.id,
            entity_id=doc.id,
            entity_type="DOCUMENT",
            title=doc.title,
            governance_status="CURRENT"
        )
        print("--> [3. BOOKMARK KNOWLEDGE PASS] Saved Count:", len(bm_res["bookmarks"]), "| Saved Title:", bm_res["bookmarks"][0]["title"])
        assert len(bm_res["bookmarks"]) >= 1

        # 4. FOLLOW ENTITY TEST
        fol_res = await disc_service.follow_entity(user_id=userA.id, entity_id=project.id)
        print("--> [4. FOLLOW ENTITY PASS] Followed Entity IDs Count:", len(fol_res["followed_entity_ids"]))
        assert len(fol_res["followed_entity_ids"]) >= 1

        # 5. SAVED KNOWLEDGE COLLECTION RETRIEVAL TEST
        saved_items = await disc_service.get_saved_knowledge(userA.id)
        print("--> [5. SAVED KNOWLEDGE COLLECTION PASS] User Saved Collection Count:", len(saved_items))
        assert len(saved_items) >= 1

    print("=== MindMesh Phase 4.8 Knowledge Discovery & Intelligent Navigation E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_discovery_navigation_e2e())
