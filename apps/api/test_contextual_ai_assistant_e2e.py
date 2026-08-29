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
from app.assistant.contextual_assistant_service import ContextualAssistantService

async def test_contextual_ai_assistant_e2e():
    print("=== Starting MindMesh Phase 5.8 Contextual AI Assistant Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Assistant Org A", slug=f"ast-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Assistant Workspace", slug=f"ast-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"ast_usera_{uA_id}@mindmesh.com",
            username=f"ast_usera_{uA_id}",
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
        # Section 136 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-ast-{uuid.uuid4().hex[:6]}",
            description="Contextual assistant test project"
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
            checksum_sha256="checksum_ast_1",
            storage_path="/path/ast1.md",
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
            checksum_sha256="checksum_ast_2",
            storage_path="/path/ast2.md",
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

        assistant_service = ContextualAssistantService(session)

        # -------------------------------------------------------------
        # Section 136 Verification Checks
        # -------------------------------------------------------------

        # 1. CONTEXT-AWARE QUESTION ANSWERING TEST
        ask_res = await assistant_service.ask("What is the current JWT expiry configuration?", str(doc2.id), "DOCUMENT", project.id, None, userA, orgA.id)
        print("--> [1. CONTEXT-AWARE ASK PASS] Answer:", ask_res["answer"][:60], "... | Sources Count:", len(ask_res["sources"]))
        assert "30 minutes" in ask_res["answer"]
        assert len(ask_res["sources"]) >= 3

        # 2. CURRENT TRUTH & CONTRADICTION HANDLING TEST
        print("--> [2. CURRENT TRUTH & CONFLICT PASS] Has Conflict:", ask_res["has_conflict"], "| Conflict Summary:", ask_res["conflict_summary"])
        assert ask_res["has_conflict"] is True
        assert ask_res["confidence_label"] == "Confirmed"

        # 3. TOPIC RESEARCH MODE TEST
        research_res = await assistant_service.research("Authentication Architecture", project.id, userA, orgA.id)
        print("--> [3. TOPIC RESEARCH PASS] Topic:", research_res["topic"], "| Findings Count:", len(research_res["findings"]))
        assert len(research_res["findings"]) >= 3
        assert len(research_res["sources"]) >= 3

        # 4. STRUCTURED SUMMARIZATION TEST
        summ_res = await assistant_service.summarize("PROJECT", str(project.id), userA)
        print("--> [4. STRUCTURED SUMMARIZATION PASS] Summary Title:", summ_res["summary_title"], "| Key Points:", len(summ_res["key_points"]))
        assert len(summ_res["key_points"]) >= 3

        # 5. ENTITY & OPTION COMPARISON TEST
        cmp_res = await assistant_service.compare("doc-v1", "doc-v2")
        print("--> [5. COMPARISON PASS] Recommended Choice:", cmp_res["recommended_choice"])
        assert "v2" in cmp_res["recommended_choice"]

        # 6. ACTION PREVIEW ORCHESTRATION TEST
        act_res = await assistant_service.preview_action("CREATE_TASK", "Update deployment env var checklist", project.id, userA)
        print("--> [6. ACTION PREVIEW PASS] Risk Level:", act_res["risk_level"], "| Status:", act_res["approval_status"])
        assert act_res["requires_user_approval"] is True
        assert act_res["approval_status"] == "AWAITING_APPROVAL"

    print("=== MindMesh Phase 5.8 Contextual AI Assistant Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_contextual_ai_assistant_e2e())
