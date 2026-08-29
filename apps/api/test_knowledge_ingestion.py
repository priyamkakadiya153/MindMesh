import asyncio
import os
import sys
import uuid
import time

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.ai.embeddings.service import EmbeddingService
from app.ai.knowledge.models import KnowledgeItem
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.search import SearchIndex

async def test_knowledge_ingestion():
    print("=== Starting MindMesh Phase 2.2 Knowledge Ingestion & Retrieval Test ===")
    start_time = time.time()

    async with AsyncSessionLocal() as session:
        # 1. Setup Test Tenant
        org = Organization(name="Ingestion Test Org", slug=f"ing-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Ingestion Workspace", slug=f"ing-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"ing_user_{u_id}@mindmesh.com",
            username=f"ing_user_{u_id}",
            first_name="Ingestion",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        # 2. Define Real Knowledge Representation (KnowledgeItem)
        kitem = KnowledgeItem(
            id=uuid.uuid4(),
            organization_id=org.id,
            workspace_id=ws.id,
            source_type="document",
            source_id=uuid.uuid4(),
            source_name="security_architecture.pdf",
            chunk_id=uuid.uuid4(),
            content="MindMesh implements zero-trust authorization where JWT access tokens expire after 15 minutes.",
            metadata={"page": 4, "section": "Authentication Limits"}
        )
        assert kitem.source_name == "security_architecture.pdf"
        print(f"--> [SUCCESS] KnowledgeItem representation initialized correctly.")

        # 3. Create Document Record
        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            title="Security Architecture Document",
            filename="security_architecture.pdf",
            original_filename="security_architecture.pdf",
            stored_filename="security_arch_123.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=2048,
            checksum_sha256="sha256_mock_hash",
            storage_provider="local",
            storage_path="/uploads/security_arch.pdf",
            processing_status="PROCESSING"
        )
        session.add(doc)
        await session.commit()

        # 4. Chunk & Embed Document
        chunk = DocumentChunk(
            document_id=doc.id,
            organization_id=org.id,
            workspace_id=ws.id,
            chunk_index=1,
            page_number=4,
            section_title="Authentication Limits",
            content=kitem.content,
            checksum="checksum_abc123",
            metadata_json=kitem.metadata
        )
        session.add(chunk)
        await session.commit()

        search_idx = SearchIndex(
            organization_id=org.id,
            workspace_id=ws.id,
            entity_type="document",
            entity_id=doc.id,
            title=doc.title,
            content=kitem.content
        )
        session.add(search_idx)
        await session.commit()

        # Generate Embeddings via EmbeddingService
        emb_service = EmbeddingService(session)
        count = await emb_service.generate_document_embeddings(doc.id)
        print(f"--> [SUCCESS] Generated {count} vector embeddings using EmbeddingService.")

        doc.processing_status = "INDEXED"
        await session.commit()

        # 5. Verify Status
        status_info = await emb_service.get_document_embedding_status(doc.id)
        assert status_info["status"] == "COMPLETED"
        assert status_info["embedded_vectors"] == 1
        print(f"--> [SUCCESS] Document status verified as COMPLETED with {status_info['embedded_vectors']} vector.")

        # 6. Execute MindMesh AI Orchestrator Grounded Retrieval
        orchestrator = MindMeshAIOrchestrator(session)
        res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the JWT access token expiry?",
            workspace_id=ws.id
        )

        assert res["grounded"] == True
        assert len(res["sources"]) > 0
        print(f"--> [SUCCESS] AI Orchestrator successfully retrieved knowledge and answered:")
        print(f"    '{res['answer']}'")

    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    print(f"=== MindMesh Ingestion Test Completed Successfully in {latency_ms} ms! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_ingestion())
