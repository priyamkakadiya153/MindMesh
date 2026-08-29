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
from app.workspace.knowledge_workspace_service import KnowledgeWorkspaceService

async def test_knowledge_workspace_experience_e2e():
    print("=== Starting MindMesh Phase 6.2 Knowledge Workspace Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Workspace Org A", slug=f"wsp-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Workspace Experience", slug=f"wsp-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"wsp_usera_{uA_id}@mindmesh.com",
            username=f"wsp_usera_{uA_id}",
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
            slug=f"auth-wsp-{uuid.uuid4().hex[:6]}",
            description="Knowledge workspace experience test project"
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
            checksum_sha256="checksum_wsp_1",
            storage_path="/path/wsp1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        wsp_service = KnowledgeWorkspaceService(session)

        # -------------------------------------------------------------
        # Section 161 Verification Checks
        # -------------------------------------------------------------

        # 1. KNOWLEDGE HOME RETRIEVAL TEST
        home_res = await wsp_service.get_knowledge_home(userA, orgA.id, project.id)
        print("--> [1. KNOWLEDGE HOME PASS] Continue Items Count:", len(home_res["continue_where_you_left_off"]), "| Needs Attention Count:", len(home_res["needs_attention"]))
        assert len(home_res["continue_where_you_left_off"]) >= 2
        assert len(home_res["needs_attention"]) >= 2

        # 2. PERSONAL SAVED SPACE TEST
        save_res = await wsp_service.save_knowledge_item("dec-jwt-30m", "DECISION", "Decision #D-102: JWT Expiry = 30m", userA)
        print("--> [2. SAVE ITEM PASS] Message:", save_res["message"])
        assert save_res["success"] is True

        my_res = await wsp_service.get_my_knowledge(userA)
        print("--> [2b. MY KNOWLEDGE PASS] Saved Items Count:", len(my_res["saved_items"]))
        assert len(my_res["saved_items"]) >= 1

        # 3. KNOWLEDGE COLLECTIONS & SMART RULE CREATION TEST
        col_res = await wsp_service.create_collection("Authentication Resources", "PROJECT", "All project auth docs", "All Authentication Decisions", userA)
        print("--> [3. COLLECTION CREATION PASS] Collection ID:", col_res["collection_id"], "| Item References:", len(col_res["item_references"]))
        assert len(col_res["item_references"]) >= 2

        # 4. PROJECT KNOWLEDGE HUB & MAP RETRIEVAL TEST
        hub_res = await wsp_service.get_project_knowledge_hub(project.id, userA)
        print("--> [4. PROJECT HUB PASS] Documents Count:", len(hub_res["documents"]), "| Map Nodes Count:", len(hub_res["knowledge_map_nodes"]))
        assert len(hub_res["documents"]) >= 2
        assert len(hub_res["knowledge_map_nodes"]) >= 4

        # 5. KNOWLEDGE ATTACHMENT & REUSE TEST
        att_res = await wsp_service.attach_knowledge_reference("TASK", "task-deploy-cfg", "dec-jwt-30m", "DECISION", "SUPPORTS", userA)
        print("--> [5. KNOWLEDGE ATTACH PASS] Message:", att_res["message"], "| Attachment ID:", att_res["attachment"]["attachment_id"])
        assert att_res["success"] is True

    print("=== MindMesh Phase 6.2 Knowledge Workspace Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_workspace_experience_e2e())
