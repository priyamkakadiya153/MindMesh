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
from app.models.conversations import Conversation, ConversationMember
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.actions.service import ActionService

async def test_knowledge_to_action_e2e():
    print("=== Starting MindMesh Phase 3.9 Knowledge-to-Action Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Action Org A", slug=f"act-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Action Workspace", slug=f"act-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"act_usera_{uA_id}@mindmesh.com",
            username=f"act_usera_{uA_id}",
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

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Action Org B", slug=f"act-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"act-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"act_userc_{uC_id}@mindmesh.com",
            username=f"act_userc_{uC_id}",
            first_name="User",
            last_name="C",
            hashed_password="mockpassword",
            phone_number=f"+1555{uC_id}"
        )
        session.add(userC)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userC.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userC.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 101 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-act-{uuid.uuid4().hex[:6]}",
            description="Core authentication action project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Authentication Deployment Guide\n\nDeployment rollback instructions.",
            filename="auth_deploy_guide.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Deployment Guide",
            visibility="private"
        )
        doc.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc.id)

        act_service = ActionService(session)

        # -------------------------------------------------------------
        # Section 101 Verification Checks
        # -------------------------------------------------------------

        # 1. ACTION RECOMMENDATIONS TEST (What should I do next?)
        recs = await act_service.get_next_action_recommendations(userA, orgA.id, wsA.id, project.id)
        print("--> [1. ACTION RECOMMENDATIONS PASS] Recs Count:", len(recs), "| Top Action:", recs[0]["title"])
        assert len(recs) >= 1

        # 2. ACTION EXECUTION TEST (Create Task)
        exec_payload = {
            "title": "Update deployment configuration",
            "project_id": str(project.id),
            "description": "Created from engineering discussion"
        }
        res_exec = await act_service.execute_action("CREATE_TASK", exec_payload, userA, orgA.id, wsA.id)
        print("--> [2. ACTION EXECUTION PASS] Success:", res_exec["success"], "| Task ID:", res_exec.get("entity_id"))
        assert res_exec["success"] is True
        assert res_exec["is_duplicate"] is False

        # 3. DUPLICATE TASK PREVENTION TEST
        res_dup = await act_service.execute_action("CREATE_TASK", exec_payload, userA, orgA.id, wsA.id)
        print("--> [3. DUPLICATE TASK PREVENTION PASS] Is Duplicate:", res_dup["is_duplicate"], "| Message:", res_dup["message"])
        assert res_dup["is_duplicate"] is True

        # 4. KNOWLEDGE GAP TO AI DOCUMENTATION DRAFT TEST
        draft_payload = {"topic": "Deployment Rollback Guide", "project_id": str(project.id)}
        res_draft = await act_service.execute_action("CREATE_DRAFT", draft_payload, userA, orgA.id, wsA.id)
        print("--> [4. KNOWLEDGE DRAFT PASS] Success:", res_draft["success"], "| Draft Doc ID:", res_draft.get("entity_id"))
        assert res_draft["success"] is True

        # 5. PROMPT INJECTION & ACTION ALLOWLIST DEFENSE TEST
        try:
            await act_service.execute_action("DELETE_DATABASE", {"query": "DROP TABLE users;"}, userA, orgA.id, wsA.id)
            assert False, "Should have rejected invalid action type"
        except ValueError as e:
            print("--> [5. ALLOWLIST DEFENSE PASS] Successfully rejected unauthorized action:", e)

    print("=== MindMesh Phase 3.9 Knowledge-to-Action Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_to_action_e2e())
