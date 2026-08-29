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
from app.models.chat import Chat
from app.models.message import Message
from app.projects.models import Project
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.conversation_intelligence.service import ConversationIntelligenceService

async def test_conversation_intelligence_e2e():
    print("=== Starting MindMesh Phase 4.1 Conversation Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="CI Org A", slug=f"ci-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="CI Workspace", slug=f"ci-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"ci_usera_{uA_id}@mindmesh.com",
            username=f"ci_usera_{uA_id}",
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
        # Section 116 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-ci-{uuid.uuid4().hex[:6]}",
            description="Core authentication CI project"
        )
        session.add(project)
        await session.commit()

        chat = Chat(organization_id=orgA.id, workspace_id=wsA.id, user_id=userA.id, title="Authentication Deployment")
        session.add(chat)
        await session.commit()

        messages_text = [
            "We need to finalize authentication deployment.",
            "JWT expiry should be 30 minutes.",
            "Agreed, we'll use 30 minutes.",
            "Priyam will update the deployment configuration by Friday.",
            "Do we have a rollback procedure?",
            "Not yet. We should document it."
        ]

        msg_entities = []
        for text in messages_text:
            msg = Message(
                chat_id=chat.id,
                organization_id=orgA.id,
                sender_id=userA.id,
                content=text
            )
            session.add(msg)
            msg_entities.append(msg)
        await session.commit()

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=b"Deployment Guide PDF Content.",
            filename="deployment-guide.pdf",
            content_type="application/pdf",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="deployment-guide.pdf",
            visibility="private"
        )
        doc.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc.id)

        ci_service = ConversationIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 116 Verification Checks
        # -------------------------------------------------------------

        # 1. SUMMARY & TOPIC TIMELINE TEST
        summary = await ci_service.summarize_conversation(chat.id, "QUICK", userA, orgA.id)
        print("--> [1. SUMMARY PASS] Topics:", len(summary["topics"]), "| Timeline Milestones:", len(summary["timeline"]))
        assert len(summary["topics"]) >= 3
        assert len(summary["timeline"]) >= 3

        # 2. SOURCE-GROUNDED EXTRACTION TEST
        items = await ci_service.extract_conversation_knowledge(chat.id, userA, orgA.id)
        print("--> [2. KNOWLEDGE EXTRACTION PASS] Extracted Items Count:", len(items))
        assert len(items) >= 3

        dec_item = next(i for i in items if i["item_type"] == "DECISION")
        task_item = next(i for i in items if i["item_type"] == "TASK")

        # 3. MEETING NOTES GENERATOR TEST
        notes = await ci_service.generate_meeting_notes(chat.id)
        print("--> [3. MEETING NOTES PASS] Notes Title:", notes["title"], "| Length:", len(notes["notes_markdown"]))
        assert "JWT" in notes["notes_markdown"]

        # 4. KNOWLEDGE PROMOTION TEST (Private DM -> Shared Project)
        prom_res = await ci_service.promote_item_to_project(uuid.UUID(task_item["id"]), project.id, userA, orgA.id)
        print("--> [4. KNOWLEDGE PROMOTION PASS] Success:", prom_res["success"], "| Promoted Entity ID:", prom_res.get("promoted_entity_id"))
        assert prom_res["success"] is True

        # 5. DUPLICATE EXTRACTION PREVENTION TEST
        dup_items = await ci_service.extract_conversation_knowledge(chat.id, userA, orgA.id)
        print("--> [5. DUPLICATE EXTRACTION PREVENTION PASS] Extracted Count Remains Constant:", len(dup_items))
        assert len(dup_items) == len(items)

    print("=== MindMesh Phase 4.1 Conversation Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_intelligence_e2e())
