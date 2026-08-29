import asyncio
import os
import sys
import uuid
import time

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.ai.retrieval.retriever import HybridRetriever
from app.processing.pipeline import ProcessingPipeline

async def test_hybrid_retrieval():
    print("--- Starting MindMesh Phase 3.4 Hybrid Retrieval Engine Test ---")

    async with AsyncSessionLocal() as session:
        # 1. Create test orgs & workspaces to test tenant isolation
        org_a = Organization(name="Org A Retrieval", slug=f"ret-org-a-{uuid.uuid4().hex[:6]}")
        session.add(org_a)
        await session.commit()

        user_a = User(email=f"ret-user-{uuid.uuid4().hex[:6]}@acme.com", username=f"ret-user-{uuid.uuid4().hex[:6]}", hashed_password="hash")
        session.add(user_a)
        await session.commit()

        ws_a = Workspace(organization_id=org_a.id, name="WS A Retrieval", slug=f"ret-ws-a-{uuid.uuid4().hex[:6]}")
        session.add(ws_a)
        await session.commit()

        # Org B (Isolated Tenant)
        org_b = Organization(name="Org B Tenant", slug=f"ret-org-b-{uuid.uuid4().hex[:6]}")
        session.add(org_b)
        await session.commit()

        ws_b = Workspace(organization_id=org_b.id, name="WS B Tenant", slug=f"ret-ws-b-{uuid.uuid4().hex[:6]}")
        session.add(ws_b)
        await session.commit()

        # 2. Ingest Document A into Workspace A
        file_a_path = os.path.join(os.getcwd(), "uploads", "test", f"ret_doc_a_{uuid.uuid4().hex[:6]}.txt")
        os.makedirs(os.path.dirname(file_a_path), exist_ok=True)
        content_a = """
# MindMesh Deployment Guide
To deploy MindMesh in a production Kubernetes cluster, configure environment variables for PostgreSQL, Redis, and OpenAI API keys.

## Database Migrations
Always run Alembic migrations using `alembic upgrade head` before restarting the API services.
        """.strip()

        with open(file_a_path, "w", encoding="utf-8") as f:
            f.write(content_a)

        doc_a = Document(
            organization_id=org_a.id,
            workspace_id=ws_a.id,
            uploaded_by=user_a.id,
            filename=os.path.basename(file_a_path),
            original_filename="deployment_guide.txt",
            stored_filename=os.path.basename(file_a_path),
            mime_type="text/plain",
            extension="txt",
            size=len(content_a),
            checksum_sha256="hash_a",
            storage_provider="local",
            storage_path=file_a_path,
            processing_status="QUEUED"
        )
        session.add(doc_a)
        await session.commit()

        # Run extraction & automatic vector embedding for Document A
        pipeline = ProcessingPipeline(session)
        job_a = await pipeline.process_document(doc_a.id)
        assert job_a.status == "COMPLETED"

        # 3. Ingest Document B into Workspace B (Isolated Tenant)
        file_b_path = os.path.join(os.getcwd(), "uploads", "test", f"ret_doc_b_{uuid.uuid4().hex[:6]}.txt")
        content_b = "Secret Financial Report for Organization B. Top Secret confidential."
        with open(file_b_path, "w", encoding="utf-8") as f:
            f.write(content_b)

        doc_b = Document(
            organization_id=org_b.id,
            workspace_id=ws_b.id,
            uploaded_by=user_a.id,
            filename=os.path.basename(file_b_path),
            original_filename="confidential.txt",
            stored_filename=os.path.basename(file_b_path),
            mime_type="text/plain",
            extension="txt",
            size=len(content_b),
            checksum_sha256="hash_b",
            storage_provider="local",
            storage_path=file_b_path,
            processing_status="QUEUED"
        )
        session.add(doc_b)
        await session.commit()

        await pipeline.process_document(doc_b.id)

        # 4. Test Hybrid Search for Workspace A
        retriever = HybridRetriever(session)
        query = "How do I deploy MindMesh?"

        start_t = time.time()
        res = await retriever.hybrid_search(
            query_text=query,
            organization_id=org_a.id,
            workspace_id=ws_a.id,
            top_k=5
        )
        elapsed_ms = int((time.time() - start_t) * 1000)

        assert res["total_candidates_found"] >= 1
        assert len(res["chunks"]) >= 1

        top_chunk = res["chunks"][0]
        assert top_chunk["document_id"] == doc_a.id
        assert "deploy MindMesh" in top_chunk["content"] or "MindMesh" in top_chunk["title"]
        assert top_chunk["score"] > 0.0

        print(f"--> Verified Hybrid Search Retrieval (Query: '{query}', Top Score: {top_chunk['score']}, Latency: {elapsed_ms}ms).")

        # 5. Test Tenant Isolation & Cross-Workspace Leak Verification
        leak_check = await retriever.hybrid_search(
            query_text="Secret Financial Report",
            organization_id=org_a.id,
            workspace_id=ws_a.id,
            top_k=5
        )

        for chunk in leak_check["chunks"]:
            assert chunk["document_id"] != doc_b.id
            assert "Secret Financial Report" not in chunk["content"]

        print("--> Verified Strict Tenant Isolation (Zero cross-organization/workspace data leaks).")

        # Clean up test files
        if os.path.exists(file_a_path):
            os.remove(file_a_path)
        if os.path.exists(file_b_path):
            os.remove(file_b_path)

        print("=== MindMesh Phase 3.4 Hybrid Retrieval Engine Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_hybrid_retrieval())
