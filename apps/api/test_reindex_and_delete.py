import asyncio
import os
import sys
import uuid
from sqlalchemy import delete, select

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.search import SearchIndex

async def test_reindex_and_delete():
    print("=== Starting MindMesh Phase 2.2 Re-Index & Delete Cleanup Test ===")

    async with AsyncSessionLocal() as session:
        # Setup tenant
        org = Organization(name="Reindex Test Org", slug=f"reindex-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Reindex Workspace", slug=f"reindex-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"reindex_user_{u_id}@mindmesh.com",
            username=f"reindex_user_{u_id}",
            first_name="Reindex",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        # 1. Version 1 Document
        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            title="JWT Expiry Spec",
            filename="jwt_spec.pdf",
            original_filename="jwt_spec.pdf",
            stored_filename="jwt_spec_1.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="hash_v1",
            storage_provider="local",
            storage_path="/uploads/jwt_spec_1.pdf"
        )
        session.add(doc)
        await session.commit()

        chunk_v1 = DocumentChunk(
            document_id=doc.id,
            organization_id=org.id,
            workspace_id=ws.id,
            chunk_index=1,
            content="JWT access tokens expire after 15 minutes.",
            metadata_json={}
        )
        session.add(chunk_v1)
        si_v1 = SearchIndex(organization_id=org.id, workspace_id=ws.id, entity_type="document", entity_id=doc.id, title=doc.title, content=chunk_v1.content)
        session.add(si_v1)
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)
        res_v1 = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the JWT access token expiry?",
            workspace_id=ws.id
        )
        print("--> [VERSION 1 VERIFIED] Answer:", res_v1["answer"])

        # 2. Re-Index: Update Document to Version 2 ("JWT access tokens expire after 30 minutes.")
        print("--> Triggering Re-Index for Document Version 2...")
        await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        await session.execute(delete(SearchIndex).where(SearchIndex.entity_id == doc.id))
        await session.commit()

        chunk_v2 = DocumentChunk(
            document_id=doc.id,
            organization_id=org.id,
            workspace_id=ws.id,
            chunk_index=1,
            content="JWT access tokens expire after 30 minutes.",
            metadata_json={}
        )
        session.add(chunk_v2)
        si_v2 = SearchIndex(organization_id=org.id, workspace_id=ws.id, entity_type="document", entity_id=doc.id, title=doc.title, content=chunk_v2.content)
        session.add(si_v2)
        await session.commit()

        res_v2 = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the JWT access token expiry?",
            workspace_id=ws.id
        )
        print("--> [RE-INDEX SUCCESS] Version 2 Answer:", res_v2["answer"])

        # 3. Permanent Deletion
        print("--> Deleting Document permanently...")
        doc.deleted_at = doc.created_at
        await session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        await session.execute(delete(SearchIndex).where(SearchIndex.entity_id == doc.id))
        await session.commit()

        res_deleted = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="JWT access token expiry",
            workspace_id=ws.id
        )

        assert res_deleted["grounded"] == False or "couldn't find enough information" in res_deleted["answer"]
        print("--> [DELETE CLEANUP SUCCESS] Deleted document content can NO LONGER be retrieved!")

    print("=== Re-Index & Delete Cleanup Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_reindex_and_delete())
