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
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.evidence.service import EvidenceService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_evidence_verification_e2e():
    print("=== Starting MindMesh Phase 3.5 Knowledge Quality & Evidence Verification E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Evidence Org A", slug=f"ev-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"ev-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"ev_usera_{uA_id}@mindmesh.com",
            username=f"ev_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"ev_userb_{uB_id}@mindmesh.com",
            username=f"ev_userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=orgA.id, user_id=userB.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userB.id, role="member", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Evidence Org B", slug=f"ev-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"ev-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"ev_userc_{uC_id}@mindmesh.com",
            username=f"ev_userc_{uC_id}",
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
        # Section 99 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Core authentication project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        docA = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJWT access tokens expire after 15 minutes.",
            filename="auth_spec_a.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture Specification",
            visibility="private"
        )
        docA.project_id = project.id

        docB = await doc_service.upload_document(
            file_content=b"Authentication Update Specification\n\nJWT access tokens now expire after 30 minutes.",
            filename="auth_spec_b.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Update Specification",
            visibility="private"
        )
        docB.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(docA.id)
        await proc_job.process_document(docB.id)

        chat = Chat(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Architecture Discussion"
        )
        session.add(chat)
        await session.commit()

        conv_mem = ConversationMemory(
            chat_id=chat.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            memory_type="decision",
            content="PostgreSQL selected for production",
            importance=5
        )
        session.add(conv_mem)
        await session.commit()

        ev_service = EvidenceService(session)

        # -------------------------------------------------------------
        # Section 99 Verification Checks
        # -------------------------------------------------------------

        # 1. EVIDENCE VERIFICATION & CONFLICT DETECTION TEST
        raw_ev = {
            "chunks": [
                {"document_id": str(docA.id), "title": docA.title, "content": "JWT access tokens expire after 15 minutes."},
                {"document_id": str(docB.id), "title": docB.title, "content": "JWT access tokens now expire after 30 minutes."}
            ]
        }
        res = await ev_service.verify_and_build_evidence(userA, orgA.id, raw_ev)
        print("--> [1. EVIDENCE VERIFICATION PASS] Trust Rating:", res["trust_rating"], "| Verified Count:", res["evidence_count"])
        print("--> [1. CONFLICT DETECTION PASS] Conflicts:", res["conflicts"])

        assert res["evidence_count"] == 2
        assert res["trust_rating"] == "CONFLICTING_EVIDENCE"
        assert len(res["conflicts"]) >= 1

        # 2. ASK MINDSMESH REASONING TEST (Current vs Historical)
        reasoner = MindMeshReasoner(session)
        ai_res_curr = await reasoner.reason_and_answer(userA.id, orgA.id, "What is the current JWT expiry?", wsA.id)
        print("--> [2. CURRENT QUESTION PASS] Answer:", ai_res_curr["answer"])
        assert len(ai_res_curr["answer"]) > 0

        ai_res_hist = await reasoner.reason_and_answer(userA.id, orgA.id, "What was the JWT expiry before the change?", wsA.id)
        print("--> [2. HISTORICAL QUESTION PASS] Answer:", ai_res_hist["answer"])
        assert len(ai_res_hist["answer"]) > 0

        # 3. SOURCE DELETION TEST (Delete Document A)
        docA.deleted_at = datetime.utcnow()
        await session.commit()

        res_del = await ev_service.verify_and_build_evidence(userA, orgA.id, raw_ev)
        del_item = [item for item in res_del["verified_items"] if item["source_id"] == str(docA.id)][0]
        print("--> [3. SOURCE DELETE PASS] Status:", del_item["status"], "| Excerpt:", del_item["excerpt"])
        assert del_item["status"] == "DELETED"
        assert del_item["excerpt"] == "Original source is no longer available."

        # 4. SECURITY ISOLATION TEST (Org B User C)
        res_orgB = await ev_service.verify_and_build_evidence(userC, orgB.id, raw_ev)
        print("--> [4. SECURITY PASS] Org B Verified Items:", len(res_orgB["verified_items"]))
        assert len(res_orgB["verified_items"]) == 0

    print("=== MindMesh Phase 3.5 Knowledge Quality & Evidence Verification E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_evidence_verification_e2e())
