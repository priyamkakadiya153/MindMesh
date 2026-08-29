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

async def test_real_file_intelligence():
    print("=== Starting MindMesh Phase 2.5 Real File Intelligence Test ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Setup tenant
        org = Organization(name="Intelligence Test Org", slug=f"intel-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Intelligence Workspace", slug=f"intel-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"intel_user_{u_id}@mindmesh.com",
            username=f"intel_user_{u_id}",
            first_name="Intel",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 60 Required End-to-End Document Intelligence Test
        # -------------------------------------------------------------
        doc_content = (
            "Authentication Service Specification\n\n"
            "Access tokens expire after 15 minutes.\n"
            "Refresh tokens remain valid for 30 days.\n\n"
            "The production database is PostgreSQL.\n"
            "The team decided to use refresh token rotation."
        ).encode("utf-8")

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=doc_content,
            filename="auth_spec.txt",
            content_type="text/plain",
            org_id=org.id,
            workspace_id=ws.id,
            user_id=user.id,
            title="Authentication Service Specification",
            visibility="private"
        )
        await session.commit()

        # Run FileIntelligenceAnalyzer
        analyzer = FileIntelligenceAnalyzer(session)
        intel = await analyzer.analyze_document(doc.id)

        print(f"--> Document Type: {intel.document_type}")
        print(f"--> Summary: {intel.summary}")
        print(f"--> Topics: {intel.topics}")
        print(f"--> Facts: {[f['fact'] for f in intel.facts]}")
        print(f"--> Decisions: {[d['decision'] for d in intel.decisions]}")

        assert intel.status == "COMPLETED"
        assert intel.document_type == "Technical Specification" or intel.document_type == "Architecture Document"
        assert len(intel.facts) >= 2
        assert len(intel.decisions) >= 1

        # -------------------------------------------------------------
        # Ask MindMesh Grounded Retrieval Verification
        # -------------------------------------------------------------
        orchestrator = MindMeshAIOrchestrator(session)

        # 1. Ask: "What did the authentication specification decide?"
        res1 = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What did the authentication specification decide?",
            workspace_id=ws.id
        )
        print("--> [QUESTION 1 PASS] Answer:", res1["answer"])
        assert res1["grounded"] == True
        assert "refresh token" in res1["answer"].lower() or "rotation" in res1["answer"].lower()

        # 2. Ask: "What database does it specify?"
        res2 = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What database does it specify?",
            workspace_id=ws.id
        )
        print("--> [QUESTION 2 PASS] Answer:", res2["answer"])
        assert res2["grounded"] == True
        assert "postgresql" in res2["answer"].lower()

        # 3. Ask: "Who approved it?" (Unspecified in document)
        res3 = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="Who approved it?",
            workspace_id=ws.id
        )
        print("--> [QUESTION 3 PASS] Answer:", res3["answer"])
        assert "couldn't find" in res3["answer"].lower() or res3["grounded"] == False or "does not specify" in res3["answer"].lower()

    print("=== Section 60 Required E2E Document Intelligence Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_real_file_intelligence())
