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
from app.models.search import SearchIndex

async def test_multi_workspace_security():
    print("=== Starting MindMesh Phase 2.2 Multi-Workspace Security Isolation Test ===")

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A (Org A, Workspace A, User A)
        org_a = Organization(name="Tenant Org A", slug=f"org-a-{uuid.uuid4().hex[:6]}")
        session.add(org_a)
        await session.commit()

        ws_a = Workspace(organization_id=org_a.id, name="Workspace A", slug=f"ws-a-{uuid.uuid4().hex[:6]}")
        session.add(ws_a)
        await session.commit()

        u_a_id = uuid.uuid4().hex[:6]
        user_a = User(
            email=f"user_a_{u_a_id}@mindmesh.com",
            username=f"user_a_{u_a_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_a_id}"
        )
        session.add(user_a)
        await session.commit()

        session.add(OrganizationMember(organization_id=org_a.id, user_id=user_a.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws_a.id, user_id=user_a.id, role="admin"))
        await session.commit()

        # Add Secret Document A in Workspace A
        doc_a = Document(
            organization_id=org_a.id,
            workspace_id=ws_a.id,
            title="Secret Financial Strategy A",
            filename="secret_a.pdf",
            original_filename="secret_a.pdf",
            stored_filename="secret_a_123.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="hash_a",
            storage_provider="local",
            storage_path="/uploads/secret_a.pdf"
        )
        session.add(doc_a)
        await session.commit()

        chunk_a = DocumentChunk(
            document_id=doc_a.id,
            organization_id=org_a.id,
            workspace_id=ws_a.id,
            chunk_index=1,
            content="Projected Revenue for Org A in 2027 is $500 Million USD.",
            metadata_json={}
        )
        session.add(chunk_a)
        session.add(SearchIndex(organization_id=org_a.id, workspace_id=ws_a.id, entity_type="document", entity_id=doc_a.id, title=doc_a.title, content=chunk_a.content))
        await session.commit()

        # 2. Setup Tenant B (Org B, Workspace B, User B)
        org_b = Organization(name="Tenant Org B", slug=f"org-b-{uuid.uuid4().hex[:6]}")
        session.add(org_b)
        await session.commit()

        ws_b = Workspace(organization_id=org_b.id, name="Workspace B", slug=f"ws-b-{uuid.uuid4().hex[:6]}")
        session.add(ws_b)
        await session.commit()

        u_b_id = uuid.uuid4().hex[:6]
        user_b = User(
            email=f"user_b_{u_b_id}@mindmesh.com",
            username=f"user_b_{u_b_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_b_id}"
        )
        session.add(user_b)
        await session.commit()

        session.add(OrganizationMember(organization_id=org_b.id, user_id=user_b.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws_b.id, user_id=user_b.id, role="admin"))
        await session.commit()

        # Add Document B in Workspace B
        doc_b = Document(
            organization_id=org_b.id,
            workspace_id=ws_b.id,
            title="Public Specs B",
            filename="specs_b.pdf",
            original_filename="specs_b.pdf",
            stored_filename="specs_b_123.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="hash_b",
            storage_provider="local",
            storage_path="/uploads/specs_b.pdf"
        )
        session.add(doc_b)
        await session.commit()

        chunk_b = DocumentChunk(
            document_id=doc_b.id,
            organization_id=org_b.id,
            workspace_id=ws_b.id,
            chunk_index=1,
            content="Workspace B standard API response threshold is set to 200ms.",
            metadata_json={}
        )
        session.add(chunk_b)
        session.add(SearchIndex(organization_id=org_b.id, workspace_id=ws_b.id, entity_type="document", entity_id=doc_b.id, title=doc_b.title, content=chunk_b.content))
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        # 3. User B attempts to query secrets from Workspace A
        res_unauthorized = await orchestrator.execute(
            user_id=user_b.id,
            org_id=org_b.id,
            query="What is the Projected Revenue for Org A?",
            workspace_id=ws_b.id
        )

        assert "$500 Million" not in res_unauthorized["answer"]
        assert len(res_unauthorized["sources"]) == 0 or res_unauthorized["grounded"] == False
        print("--> [SECURITY PASS] User B in Workspace B CANNOT retrieve secret Document A from Workspace A!")

        # 4. User A queries Workspace A
        res_authorized = await orchestrator.execute(
            user_id=user_a.id,
            org_id=org_a.id,
            query="What is the Projected Revenue for Org A?",
            workspace_id=ws_a.id
        )
        assert res_authorized["grounded"] == True
        assert len(res_authorized["sources"]) > 0
        print("--> [SECURITY PASS] User A in Workspace A successfully retrieved authorized Document A!")

    print("=== Multi-Workspace Security Isolation Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_multi_workspace_security())
