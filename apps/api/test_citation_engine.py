import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.models.document import Document
from app.ai.embeddings.models import DocumentChunk
from app.models.user import User
from app.models.message import Message
from app.models.chat import Chat
from app.ai.citation.models import Citation
from app.ai.citation.generator import CitationGenerator, CitationValidator
from sqlalchemy import select

async def test_citation_engine():
    print("--- Starting MindMesh Phase 3.8 Citation Rendering & Source Attribution Test ---")

    message_id = uuid.uuid4()
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    chunk_1 = uuid.uuid4()
    chunk_2 = uuid.uuid4()

    # 1. Test CitationGenerator Deduplication & Confidence Categorization
    raw_chunks = [
        {
            "id": chunk_1,
            "document_id": doc_id,
            "page_number": 12,
            "section_title": "Database Setup",
            "score": 0.92
        },
        {
            "id": chunk_1,  # Duplicate chunk ID
            "document_id": doc_id,
            "page_number": 12,
            "section_title": "Database Setup",
            "score": 0.92
        },
        {
            "id": chunk_2,
            "document_id": doc_id,
            "page_number": 15,
            "section_title": "Kubernetes Deployment",
            "score": 0.74
        }
    ]

    cits, has_evidence = CitationGenerator.generate_citations(
        message_id=message_id,
        conversation_id=None,
        organization_id=org_id,
        workspace_id=ws_id,
        retrieved_chunks=raw_chunks
    )

    assert has_evidence is True
    assert len(cits) == 2  # Deduplicated from 3 to 2
    assert cits[0].citation_tag == "[1]"
    assert cits[0].confidence_score == "High"
    assert cits[1].citation_tag == "[2]"
    assert cits[1].confidence_score == "Medium"
    print("--> Verified CitationGenerator Deduplication & Confidence Score Categorization (High/Medium/Low).")

    # 2. Test Hallucination Protection (Ungrounded Message)
    empty_cits, has_evidence_empty = CitationGenerator.generate_citations(
        message_id=message_id,
        conversation_id=None,
        organization_id=org_id,
        workspace_id=ws_id,
        retrieved_chunks=[]
    )
    assert has_evidence_empty is False
    assert len(empty_cits) == 0
    print("--> Verified Hallucination Protection (Ungrounded Message Detection).")

    # 3. Test Database Persistence & Validation
    async with AsyncSessionLocal() as session:
        org = Organization(name="Citation Org", slug=f"cit-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Citation Workspace", slug=f"cit-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            filename="Architecture.pdf",
            original_filename="Architecture.pdf",
            title="Architecture Overview",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            storage_path="/tmp/doc.pdf"
        )
        session.add(doc)
        await session.commit()

        chunk = DocumentChunk(document_id=doc.id, organization_id=org.id, workspace_id=ws.id, content="PostgreSQL database.", chunk_index=0, metadata_json={})
        session.add(chunk)
        await session.commit()

        chat = Chat(organization_id=org.id, workspace_id=ws.id, title="Citation Chat")
        session.add(chat)
        await session.commit()

        email_str = f"test-{uuid.uuid4().hex[:6]}@mindmesh.ai"
        user = User(username=email_str, email=email_str, hashed_password="pw", current_organization_id=org.id, current_workspace_id=ws.id)
        session.add(user)
        await session.commit()

        msg = Message(chat_id=chat.id, sender_id=user.id, organization_id=org.id, role="assistant", content="MindMesh uses PostgreSQL.")
        session.add(msg)
        await session.commit()

        # Generate & Persist Citation
        db_cits, _ = CitationGenerator.generate_citations(
            message_id=msg.id,
            conversation_id=chat.id,
            organization_id=org.id,
            workspace_id=ws.id,
            retrieved_chunks=[{"id": chunk.id, "document_id": doc.id, "score": 0.95, "page_number": 3}]
        )

        session.add_all(db_cits)
        await session.commit()

        # Validate
        valid_cits = await CitationValidator.validate_citations(session, db_cits, org.id, ws.id)
        assert len(valid_cits) == 1
        assert valid_cits[0].citation_tag == "[1]"

        print("--> Verified Citation DB Persistence & RBAC Security Validation.")

    print("=== MindMesh Phase 3.8 Citation Rendering & Source Attribution Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_citation_engine())
