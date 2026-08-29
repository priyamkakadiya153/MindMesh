import asyncio
import os
import sys
import uuid
import math
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.ai.embeddings.providers import EmbeddingProviderFactory, GeminiEmbeddingProvider, OpenAIEmbeddingProvider, OllamaEmbeddingProvider
from app.ai.embeddings.service import EmbeddingService
from app.processing.pipeline import ProcessingPipeline

def cosine_similarity(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if (norm1 > 0 and norm2 > 0) else 0.0

async def test_embedding_pipeline():
    print("--- Starting MindMesh Phase 3.3 Enterprise Embedding Generation & pgvector Test ---")

    # 1. Test Embedding Provider Factory & Unit Vectors
    gemini_p = EmbeddingProviderFactory.get_provider("gemini")
    assert gemini_p.dimension == 768
    assert gemini_p.model_name == "text-embedding-004"

    openai_p = EmbeddingProviderFactory.get_provider("openai")
    assert openai_p.dimension == 1536
    assert openai_p.model_name == "text-embedding-3-small"

    ollama_p = EmbeddingProviderFactory.get_provider("ollama")
    assert ollama_p.dimension == 768
    assert ollama_p.model_name == "nomic-embed-text"

    sample_texts = [
        "MindMesh is an AI-powered Knowledge Intelligence System.",
        "Retrieval-Augmented Generation relies on high quality vector embeddings."
    ]
    vectors = await gemini_p.embed_texts(sample_texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768
    print("--> Verified Embedding Provider Abstraction (Gemini 768d, OpenAI 1536d, Ollama 768d).")

    # 2. Test End-to-End Ingestion & Vector Persistence in DB
    async with AsyncSessionLocal() as session:
        # Create test org, user, workspace
        org = Organization(name="Vector Org", slug=f"vec-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        user = User(email=f"vec-user-{uuid.uuid4().hex[:6]}@acme.com", username=f"vec-user-{uuid.uuid4().hex[:6]}", hashed_password="hash")
        session.add(user)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Vector Workspace", slug=f"vec-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        # Create temporary file for document chunking & embedding
        test_file_dir = os.path.join(os.getcwd(), "uploads", "test")
        os.makedirs(test_file_dir, exist_ok=True)
        test_file_path = os.path.join(test_file_dir, f"vec_sample_{uuid.uuid4().hex[:6]}.txt")

        content = """
# MindMesh Architecture Overview
MindMesh transforms organizational discussions and files into structured searchable knowledge.

## Vector Search & pgvector
Document chunks are converted into float vectors stored in PostgreSQL using pgvector with HNSW indexes.
        """.strip()

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(content)

        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            uploaded_by=user.id,
            filename=os.path.basename(test_file_path),
            original_filename="vector_doc.txt",
            stored_filename=os.path.basename(test_file_path),
            mime_type="text/plain",
            extension="txt",
            size=len(content),
            checksum_sha256="hash123",
            storage_provider="local",
            storage_path=test_file_path,
            processing_status="QUEUED"
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

        # Run Stage 1-5 Chunking + Automatic Phase 3.3 Vector Embedding
        pipeline = ProcessingPipeline(session)
        job = await pipeline.process_document(doc.id)
        assert job.status == "COMPLETED"

        # Check stored embeddings in DB
        emb_service = EmbeddingService(session)
        emb_status = await emb_service.get_document_embedding_status(doc.id)
        
        assert emb_status["total_chunks"] >= 1
        assert emb_status["embedded_vectors"] == emb_status["total_chunks"]
        assert emb_status["embedding_model"] == "text-embedding-004"
        assert emb_status["dimension"] == 768
        print(f"--> Verified Auto Embedding Pipeline ({emb_status['embedded_vectors']} vectors generated & stored).")

        # 3. Test Cosine Similarity Query & Workspace Isolation
        query_text = "How does vector search work in MindMesh?"
        query_vec = await gemini_p.embed_query(query_text)
        assert len(query_vec) == 768

        emb_records = (await session.execute(
            DocumentEmbedding.__table__.select().where(
                DocumentEmbedding.organization_id == org.id,
                DocumentEmbedding.workspace_id == ws.id
            )
        )).fetchall()

        scores = []
        for r in emb_records:
            sim = cosine_similarity(query_vec, r.embedding)
            scores.append((sim, r.chunk_id))

        scores.sort(key=lambda x: x[0], reverse=True)
        assert len(scores) > 0
        assert scores[0][0] > 0.0
        print(f"--> Verified Cosine Similarity Vector Match (Top Score: {scores[0][0]:.4f}).")

        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

        print("=== MindMesh Phase 3.3 Embedding Generation & pgvector Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_embedding_pipeline())
