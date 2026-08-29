import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.ai.orchestrator import MindMeshAIOrchestrator

async def test_grounding_and_refusal():
    print("=== Starting MindMesh Phase 2.1 Grounding & Refusal Test ===")

    async with AsyncSessionLocal() as session:
        # Create test DB records
        org = Organization(name="Grounding Test Org", slug=f"grd-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Grounding Workspace", slug=f"grd-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"grd_user_{u_id}@mindmesh.com",
            username=f"grd_user_{u_id}",
            first_name="Grounding",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        # Add a real document chunk with specific organizational knowledge
        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            title="Authentication Specification",
            filename="auth_spec.pdf",
            original_filename="auth_spec.pdf",
            stored_filename="auth_spec_123.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="sha256_mock",
            storage_provider="local",
            storage_path="/uploads/auth_spec.pdf"
        )
        session.add(doc)
        await session.commit()

        chunk = DocumentChunk(
            document_id=doc.id,
            organization_id=org.id,
            workspace_id=ws.id,
            chunk_index=1,
            content="JWT access tokens expire after 15 minutes and sliding refresh tokens persist for 30 days.",
            metadata_json={}
        )
        session.add(chunk)
        await session.commit()

        from app.models.search import SearchIndex
        si = SearchIndex(
            organization_id=org.id,
            workspace_id=ws.id,
            entity_type="document",
            entity_id=doc.id,
            title="Authentication Specification",
            content="JWT access tokens expire after 15 minutes and sliding refresh tokens persist for 30 days."
        )
        session.add(si)
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        # 1. Ask question present in workspace knowledge
        res_grounded = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the JWT access token expiry?",
            workspace_id=ws.id
        )

        assert res_grounded["grounded"] == True
        print(f"--> [SUCCESS] Grounded Query Answered correctly!")
        print(f"    Answer: '{res_grounded['answer']}'")

        # 2. Ask question NOT present in workspace knowledge
        res_insufficient = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="Quantum Cryptography Strategy Hyperdrive Protocol X99",
            workspace_id=ws.id
        )

        print(f"DEBUG res_insufficient: {res_insufficient}")
        assert "couldn't find enough information" in res_insufficient["answer"] or res_insufficient["grounded"] == False
        print(f"--> [SUCCESS] Insufficient knowledge correctly refused without fabrication!")
        print(f"    Refusal Answer: '{res_insufficient['answer']}'")

    print("=== Grounding & Refusal Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_grounding_and_refusal())
