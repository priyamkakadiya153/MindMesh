import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.service import DocumentService
from app.ai.extraction.file_analyzer import FileIntelligenceAnalyzer
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.documents.models import FileIntelligence
from app.search.indexer import SearchIndexer
from sqlalchemy import select

async def test_file_intelligence_negative_and_security():
    print("=== Starting MindMesh Phase 2.5 Negative & Security Test ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Tenant A
        orgA = Organization(name="Org A Security Test", slug=f"orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="WS A", slug=f"wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"usera_{uA_id}@mindmesh.com",
            username=f"usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # Tenant B
        orgB = Organization(name="Org B Security Test", slug=f"orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="WS B", slug=f"wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"userb_{uB_id}@mindmesh.com",
            username=f"userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userB.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userB.id, role="admin", is_active=True))
        await session.commit()

        # 1. Upload private doc to Org A
        doc_serviceA = DocumentService(session)
        docA = await doc_serviceA.upload_document(
            file_content=b"Confidential Project Alpha Security Protocol: API keys are rotated every 90 days. Python 3.12 is used for backend.",
            filename="confidential_alpha.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Confidential Project Alpha Security Protocol",
            visibility="private"
        )
        await session.commit()

        analyzerA = FileIntelligenceAnalyzer(session)
        intelA = await analyzerA.analyze_document(docA.id)
        await session.commit()

        print(f"--> Org A File Intelligence Created: {intelA.status} | {intelA.document_type}")

        # -------------------------------------------------------------
        # Negative Refusal Test for User A
        # -------------------------------------------------------------
        orchestrator = MindMeshAIOrchestrator(session)
        refusal_res = await orchestrator.execute(
            user_id=userA.id,
            org_id=orgA.id,
            query="What database does Project Alpha specify?",
            workspace_id=wsA.id
        )
        print("--> [NEGATIVE REFUSAL TEST PASS] Answer:", refusal_res["answer"])
        assert "couldn't find" in refusal_res["answer"].lower() or refusal_res["grounded"] == False

        # -------------------------------------------------------------
        # Multi-Tenant Security Isolation Test (User B queries Org A info)
        # -------------------------------------------------------------
        security_res = await orchestrator.execute(
            user_id=userB.id,
            org_id=orgB.id,
            query="What is the API key rotation period for Project Alpha?",
            workspace_id=wsB.id
        )
        print("--> [SECURITY ISOLATION PASS] Answer for User B:", security_res["answer"])
        assert "couldn't find" in security_res["answer"].lower() or security_res["grounded"] == False

        # -------------------------------------------------------------
        # Reprocess Verification Test
        # -------------------------------------------------------------
        reprocessed_intel = await analyzerA.analyze_document(docA.id)
        await session.commit()
        print("--> [REPROCESS TEST PASS] Reprocessed Status:", reprocessed_intel.status)
        assert reprocessed_intel.status == "COMPLETED"

        # -------------------------------------------------------------
        # Permanent Delete Propagation Test
        # -------------------------------------------------------------
        del_res = await doc_serviceA.permanent_delete_document(docA.id)
        await session.commit()
        print("--> [DELETE PROPAGATION PASS] Permanent delete result:", del_res)

        # Confirm FileIntelligence record is gone
        stmt_check = select(FileIntelligence).where(FileIntelligence.document_id == docA.id)
        check_intel = (await session.execute(stmt_check)).scalar_one_or_none()
        assert check_intel is None

    print("=== MindMesh Phase 2.5 Negative & Security Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_file_intelligence_negative_and_security())
