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
from app.collaboration.intelligence_service import CollaborativeIntelligenceService

async def test_collaborative_intelligence_e2e():
    print("=== Starting MindMesh Phase 5.3 Collaborative Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Collab Org A", slug=f"col-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Collab Workspace", slug=f"col-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"col_usera_{uA_id}@mindmesh.com",
            username=f"col_usera_{uA_id}",
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
        # Section 124 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-col-{uuid.uuid4().hex[:6]}",
            description="Collaborative intelligence test project"
        )
        session.add(project)
        await session.commit()

        doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch_v2.md",
            original_filename="auth_arch_v2.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_col_1",
            storage_path="/path/col1.md",
            uploaded_by=userA.id
        )
        session.add(doc)
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

        collab_service = CollaborativeIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 124 Verification Checks
        # -------------------------------------------------------------

        # 1. CONVERSATION CONTEXT ENRICHMENT TEST
        conv_id = uuid.uuid4()
        c_ctx = await collab_service.get_conversation_context(conv_id, userA)
        print("--> [1. CONVERSATION CONTEXT PASS] Project:", c_ctx["project_name"], "| Active Members:", len(c_ctx["participants"]))
        assert c_ctx["project_name"] == "Authentication System"
        assert len(c_ctx["participants"]) == 3

        # 2. SUGGESTION EXTRACTION FROM GROUP DISCUSSION TEST
        suggs_res = await collab_service.detect_suggestions_from_conversation(conv_id, [])
        print("--> [2. SUGGESTION EXTRACTION PASS] Total Suggestions:", suggs_res["total_suggestions"])
        assert suggs_res["total_suggestions"] == 3

        sugg_dec = suggs_res["suggestions"][0]
        sugg_tsk = suggs_res["suggestions"][1]

        # 3. DECISION & TASK CONFIRMATION TEST
        dec_conf = await collab_service.confirm_decision(sugg_dec["suggestion_id"], userA, orgA.id)
        print("--> [3. DECISION CONFIRMATION PASS] Title:", dec_conf["decision"]["title"], "| Confirmed By:", dec_conf["decision"]["confirmed_by"])
        assert dec_conf["success"] is True
        assert dec_conf["decision"]["status"] == "CONFIRMED"

        tsk_conf = await collab_service.confirm_task(sugg_tsk["suggestion_id"], userA, orgA.id)
        print("--> [4. TASK CONFIRMATION PASS] Message:", tsk_conf["message"])
        assert tsk_conf["success"] is True

        # 4. KNOWLEDGE REVIEW ROOM CONFLICT RESOLUTION TEST
        room = await collab_service.create_review_context("JWT Expiry Contradiction", ["Auth Arch v1 (15m)", "Decision #D-102 (30m)"])
        print("--> [5. REVIEW ROOM PASS] Room ID:", room["room_id"], "| Initial Status:", room["status"])
        assert room["status"] == "UNDER_REVIEW"

        res_room = await collab_service.resolve_review(room["room_id"], userA, "Confirmed 30 minutes expiry.")
        print("--> [6. REVIEW RESOLUTION PASS] Resolved Status:", res_room["room"]["status"])
        assert res_room["room"]["status"] == "RESOLVED"

        # 5. SPECIALIZED FILE METADATA HANDLING TEST
        spec_res = await collab_service.handle_specialized_file("authentication-design.dst", "application/x-embroidery")
        print("--> [7. SPECIALIZED FILE PASS] Format:", spec_res["metadata"]["format"], "| Relationships Preserved:", spec_res["relationships_preserved"])
        assert spec_res["preview_available"] is False
        assert spec_res["relationships_preserved"] is True

        # 6. TEAM DIGEST GENERATION TEST
        t_digest = await collab_service.get_team_digest(userA, orgA.id)
        print("--> [8. TEAM DIGEST PASS] Project:", t_digest["project_name"], "| Recent Decisions:", len(t_digest["recent_decisions"]))
        assert len(t_digest["recent_decisions"]) >= 1

    print("=== MindMesh Phase 5.3 Collaborative Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_collaborative_intelligence_e2e())
