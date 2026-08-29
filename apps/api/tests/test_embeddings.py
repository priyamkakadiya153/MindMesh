import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from passlib.hash import bcrypt

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.project import Project
from app.workspace.models import Workspace
from app.documents.models import Document
from app.processing.models import DocumentContent
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.ai.embeddings.service import EmbeddingService
from app.ai.vector.factory import VectorStoreFactory
from app.core.security import create_access_token

@pytest.fixture
async def seeded_doc_data(db_session: AsyncSession):
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = bcrypt.hash("password123")
    user = User(username="docuser", email="doc@example.com", hashed_password=hashed_pwd)
    db_session.add(user)
    
    await db_session.flush()

    org = Organization(name="Doc Org", slug="doc-org", owner_id=user.id)
    db_session.add(org)
    
    await db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(member)
    
    await db_session.flush()

    ws = Workspace(name="Doc WS", slug="doc-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()

    proj = Project(name="Doc Proj", slug="doc-proj", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.flush()

    # Create a document
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="test_doc.md",
        original_filename="test_doc.md",
        mime_type="text/markdown",
        extension="md",
        size=1024,
        checksum_sha256="checksum123",
        storage_provider="local",
        storage_path="orgs/doc-org/test_doc.md",
        processing_status="READY",
        visibility="private",
        version=1
    )
    db_session.add(doc)
    await db_session.flush()

    # Create DocumentContent
    content_json = {
        "sections": [
            {"title": "Section 1", "level": 1},
            {"title": "Section 2", "level": 2}
        ],
        "paragraphs": [
            {"text": "This is paragraph 1 under Section 1."},
            {"text": "This is paragraph 2 under Section 2."}
        ],
        "tables": [
            {
                "data": [
                    ["Header A", "Header B"],
                    ["Row 1 Col A", "Row 1 Col B"]
                ],
                "metadata": {"caption": "Table 1"}
            }
        ],
        "images": []
    }
    doc_content = DocumentContent(
        document_id=doc.id,
        content_json=content_json,
        extracted_text="Section 1\nThis is paragraph 1\nSection 2\nThis is paragraph 2",
        statistics={"word_count": 12, "character_count": 80}
    )
    db_session.add(doc_content)
    await db_session.commit()

    return {
        "user": user,
        "org": org,
        "workspace": ws,
        "project": proj,
        "document": doc,
        "content": doc_content
    }

@pytest.mark.asyncio
async def test_embedding_service_processing(seeded_doc_data: dict, db_session: AsyncSession):
    doc = seeded_doc_data["document"]
    service = EmbeddingService(db_session)
    chunks_count = await service.generate_document_embeddings(doc.id)
    assert chunks_count > 0
    
    # Verify chunks are saved
    stmt_chunks = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    chunks = (await db_session.execute(stmt_chunks)).scalars().all()
    assert len(chunks) == chunks_count
    
    # Verify embeddings are saved
    stmt_embs = select(DocumentEmbedding).join(
        DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
    ).where(DocumentChunk.document_id == doc.id)
    embs = (await db_session.execute(stmt_embs)).scalars().all()
    assert len(embs) == chunks_count
    for emb in embs:
        assert emb.embedding_dimension == 1536
        assert len(emb.embedding) == 1536

@pytest.mark.asyncio
async def test_vector_store_search(seeded_doc_data: dict, db_session: AsyncSession):
    doc = seeded_doc_data["document"]
    service = EmbeddingService(db_session)
    await service.generate_document_embeddings(doc.id)
    
    # Search
    vector_store = VectorStoreFactory.get_vector_store(db_session)
    query_vector = [0.1] * 1536
    results = await vector_store.search(query_vector, limit=5, filters={"project_id": str(doc.project_id)})
    assert len(results) > 0
    assert "similarity" in results[0]
    assert results[0]["document_id"] == doc.id
    
    # Search with wrong filters
    results_empty = await vector_store.search(query_vector, limit=5, filters={"project_id": str(uuid4())})
    assert len(results_empty) == 0

@pytest.mark.asyncio
async def test_cascade_delete_chunks_and_embeddings(seeded_doc_data: dict, db_session: AsyncSession):
    doc = seeded_doc_data["document"]
    service = EmbeddingService(db_session)
    await service.generate_document_embeddings(doc.id)
    
    # Delete document
    from sqlalchemy import delete
    await db_session.execute(delete(Document).where(Document.id == doc.id))
    await db_session.commit()
    
    # Assert chunks and embeddings are gone
    stmt_chunks = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    chunks = (await db_session.execute(stmt_chunks)).scalars().all()
    assert len(chunks) == 0
    
    stmt_embs = select(DocumentEmbedding).join(
        DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
    ).where(DocumentChunk.document_id == doc.id)
    embs = (await db_session.execute(stmt_embs)).scalars().all()
    assert len(embs) == 0

@pytest.mark.asyncio
async def test_router_generate_embeddings_sync(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    doc = seeded_doc_data["document"]
    token = create_access_token(data={"sub": str(user.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    
    payload = {
        "document_id": str(doc.id)
    }
    
    response = await client.post("/api/v1/embeddings/generate?background=false", json=payload, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["chunks_count"] > 0
    
    # Verify DB populated
    stmt = select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    chunks = (await db_session.execute(stmt)).scalars().all()
    assert len(chunks) == data["chunks_count"]

@pytest.mark.asyncio
async def test_router_generate_embeddings_async(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    doc = seeded_doc_data["document"]
    token = create_access_token(data={"sub": str(user.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    
    payload = {
        "document_id": str(doc.id)
    }
    
    response = await client.post("/api/v1/embeddings/generate?background=true", json=payload, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "QUEUED"

@pytest.mark.asyncio
async def test_router_rebuild_embeddings_sync(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    doc = seeded_doc_data["document"]
    token = create_access_token(data={"sub": str(user.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    
    # Generate first
    service = EmbeddingService(db_session)
    await service.generate_document_embeddings(doc.id)
    
    payload = {
        "document_id": str(doc.id)
    }
    
    response = await client.post("/api/v1/embeddings/rebuild?background=false", json=payload, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["chunks_count"] > 0

@pytest.mark.asyncio
async def test_router_status_endpoint(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    doc = seeded_doc_data["document"]
    token = create_access_token(data={"sub": str(user.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    
    # Initially status should be NOT_STARTED
    response = await client.get(f"/api/v1/embeddings/status/{doc.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NOT_STARTED"
    assert data["chunks_count"] == 0
    assert data["embeddings_count"] == 0
    
    # Generate and check status
    service = EmbeddingService(db_session)
    await service.generate_document_embeddings(doc.id)
    
    response = await client.get(f"/api/v1/embeddings/status/{doc.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["chunks_count"] > 0
    assert data["embeddings_count"] == data["chunks_count"]
