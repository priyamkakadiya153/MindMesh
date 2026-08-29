import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.documents.models import Document, DocumentProcessingJob
from app.ai.embeddings.models import DocumentChunk
from app.processing.cleaner import TextCleaner
from app.processing.chunker import SemanticChunker
from app.processing.pipeline import ProcessingPipeline

async def test_chunking_and_extraction_pipeline():
    print("--- Starting MindMesh Phase 3.2 Document Text Extraction & Chunking Test ---")

    # 1. Test TextCleaner Unit Logic
    raw_sample = "Hello\u00A0World!\r\nCommu-\nnication is key.\n\n\n\nSection 1: Details.\x07"
    cleaned = TextCleaner.clean_text(raw_sample)
    assert "Communication is key." in cleaned
    assert "\x07" not in cleaned
    assert "\r" not in cleaned
    print("--> Verified TextCleaner (Unicode NFC, line-wrap removal, control char filtering).")

    # 2. Test SemanticChunker Unit Logic
    sample_doc_text = """
# Executive Overview
MindMesh is an AI-powered Knowledge Intelligence System designed for organizational memory and semantic document retrieval.

## System Architecture
The platform features an enterprise retrieval-augmented generation pipeline. Documents are uploaded, cleaned, and split into intelligent semantic chunks with sentence and heading boundary awareness.

## Performance Requirements
Every chunk target stays within 500 to 800 tokens with an overlap buffer of 100 to 150 tokens. Checksums are computed using SHA256 hashes to guarantee data integrity across vector databases.
    """.strip()

    dummy_doc_id = uuid.uuid4()
    dummy_org_id = uuid.uuid4()
    dummy_ws_id = uuid.uuid4()

    chunker = SemanticChunker(target_chunk_tokens=50, overlap_tokens=15)
    chunks = chunker.chunk_document(sample_doc_text, dummy_doc_id, dummy_org_id, dummy_ws_id)
    
    assert len(chunks) >= 1
    for c in chunks:
        assert c["chunk_index"] >= 0
        assert c["checksum"] != ""
        assert len(c["checksum"]) == 64
        assert c["token_count"] > 0
        assert c["character_count"] > 0
    print(f"--> Verified SemanticChunker (Generated {len(chunks)} chunks with checksums & metadata).")

    # 3. Test Full Processing Pipeline & DB Persistence
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Create test org, user, workspace, doc
        org = Organization(name="Chunking Org", slug=f"chunk-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        user = User(email=f"chunk-user-{uuid.uuid4().hex[:6]}@acme.com", username=f"chunk-user-{uuid.uuid4().hex[:6]}", hashed_password="hash")
        session.add(user)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Chunk Workspace", slug=f"chunk-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        # Create temporary file storage path for test document
        test_file_dir = os.path.join(os.getcwd(), "uploads", "test")
        os.makedirs(test_file_dir, exist_ok=True)
        test_file_path = os.path.join(test_file_dir, f"sample_{uuid.uuid4().hex[:6]}.txt")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(sample_doc_text)

        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            uploaded_by=user.id,
            filename=os.path.basename(test_file_path),
            original_filename="sample_doc.txt",
            stored_filename=os.path.basename(test_file_path),
            mime_type="text/plain",
            extension="txt",
            size=len(sample_doc_text),
            checksum_sha256="dummyhash",
            storage_provider="local",
            storage_path=test_file_path,
            processing_status="QUEUED"
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        print(f"--> Created Document Record (ID: {doc.id}).")

        # Run ProcessingPipeline
        pipeline = ProcessingPipeline(session)
        job = await pipeline.process_document(doc.id)
        
        assert job.status == "COMPLETED"
        assert job.progress == 100.0
        assert job.processing_time_ms >= 0

        # Query DocumentChunk records from database
        stored_chunks = (await session.execute(
            DocumentChunk.__table__.select().where(DocumentChunk.document_id == doc.id)
        )).fetchall()

        assert len(stored_chunks) >= 1
        print(f"--> Verified Processing Pipeline DB Persistence ({len(stored_chunks)} chunks stored in database).")

        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

        print("=== MindMesh Phase 3.2 Text Extraction & Chunking Pipeline Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_chunking_and_extraction_pipeline())
