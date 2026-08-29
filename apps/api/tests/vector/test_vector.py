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
from app.vector.models import VectorIndex, EmbeddingJob
from app.vector.similarity import (
    cosine_similarity,
    inner_product,
    euclidean_distance,
    rank_results,
    normalize_scores
)
from app.vector.service import VectorService
from app.core.security import create_access_token

@pytest.fixture
async def seeded_vector_data(db_session: AsyncSession):
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = bcrypt.hash("password123")
    user = User(username="vectoruser", email="vector@example.com", hashed_password=hashed_pwd)
    db_session.add(user)
    await db_session.flush()

    # 1. Organization 1 setup
    org1 = Organization(name="Org One", slug="org-one", owner_id=user.id)
    db_session.add(org1)
    await db_session.flush()

    member1 = OrganizationMember(organization_id=org1.id, user_id=user.id, role_id=role.id)
    db_session.add(member1)
    await db_session.flush()

    ws1 = Workspace(name="WS One", slug="ws-one", organization_id=org1.id)
    db_session.add(ws1)
    await db_session.flush()

    proj1 = Project(name="Proj One", slug="proj-one", workspace_id=ws1.id, organization_id=org1.id)
    db_session.add(proj1)
    await db_session.flush()

    doc1 = Document(
        organization_id=org1.id,
        workspace_id=ws1.id,
        project_id=proj1.id,
        uploaded_by=user.id,
        filename="doc_one.md",
        original_filename="doc_one.md",
        mime_type="text/markdown",
        extension="md",
        size=512,
        checksum_sha256="checksum111",
        storage_path="orgs/org-one/doc_one.md",
        processing_status="READY",
        visibility="private"
    )
    db_session.add(doc1)
    await db_session.flush()

    chunk1 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=1,
        content="This is the content of chunk 1 in Org One.",
        token_count=10,
        metadata_json={
            "organization_id": str(org1.id),
            "workspace_id": str(ws1.id),
            "project_id": str(proj1.id),
            "document_id": str(doc1.id)
        }
    )
    db_session.add(chunk1)
    await db_session.flush()

    # Set mock 1536-dimensional vector for chunk 1: mostly positive values
    emb1 = DocumentEmbedding(
        chunk_id=chunk1.id,
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        embedding=[0.05] * 1536,
        checksum="checksum_1"
    )
    db_session.add(emb1)
    await db_session.flush()

    # 2. Organization 2 setup (for tenant isolation test)
    org2 = Organization(name="Org Two", slug="org-two", owner_id=user.id)
    db_session.add(org2)
    await db_session.flush()

    ws2 = Workspace(name="WS Two", slug="ws-two", organization_id=org2.id)
    db_session.add(ws2)
    await db_session.flush()

    proj2 = Project(name="Proj Two", slug="proj-two", workspace_id=ws2.id, organization_id=org2.id)
    db_session.add(proj2)
    await db_session.flush()

    doc2 = Document(
        organization_id=org2.id,
        workspace_id=ws2.id,
        project_id=proj2.id,
        uploaded_by=user.id,
        filename="doc_two.md",
        original_filename="doc_two.md",
        mime_type="text/markdown",
        extension="md",
        size=512,
        checksum_sha256="checksum222",
        storage_path="orgs/org-two/doc_two.md",
        processing_status="READY",
        visibility="private"
    )
    db_session.add(doc2)
    await db_session.flush()

    chunk2 = DocumentChunk(
        document_id=doc2.id,
        chunk_index=1,
        content="This is the content of chunk 2 in Org Two.",
        token_count=10,
        metadata_json={
            "organization_id": str(org2.id),
            "workspace_id": str(ws2.id),
            "project_id": str(proj2.id),
            "document_id": str(doc2.id)
        }
    )
    db_session.add(chunk2)
    await db_session.flush()

    # Set mock 1536-dimensional vector for chunk 2: identical vector to challenge boundaries
    emb2 = DocumentEmbedding(
        chunk_id=chunk2.id,
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        embedding=[0.05] * 1536,
        checksum="checksum_2"
    )
    db_session.add(emb2)
    await db_session.commit()

    return {
        "user": user,
        "org1": org1,
        "org2": org2,
        "workspace1": ws1,
        "project1": proj1,
        "document1": doc1,
        "chunk1": chunk1,
        "document2": doc2,
        "chunk2": chunk2
    }

# 1. Similarity Engine Unit Tests
def test_similarity_cosine():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-6
    
    v3 = [0.0, 1.0, 0.0]
    assert abs(cosine_similarity(v1, v3) - 0.0) < 1e-6

def test_similarity_inner_product():
    v1 = [2.0, 3.0]
    v2 = [4.0, 5.0]
    assert inner_product(v1, v2) == 23.0

def test_similarity_euclidean():
    v1 = [1.0, 2.0]
    v2 = [4.0, 6.0]
    assert euclidean_distance(v1, v2) == 5.0

def test_similarity_ranking_and_normalization():
    query = [1.0, 0.0]
    candidates = [
        {"embedding": [0.8, 0.6]}, # cosine sim = 0.8
        {"embedding": [0.5, 0.866]} # cosine sim = 0.5
    ]
    ranked = rank_results(candidates, query, "COSINE")
    assert ranked[0]["score"] > ranked[1]["score"]
    
    normalized = normalize_scores(ranked, "COSINE")
    assert 0.0 <= normalized[0]["normalized_score"] <= 1.0

# 2. Multi-tenant Vector Isolation Search Integration Test
@pytest.mark.asyncio
async def test_tenant_isolation_search(seeded_vector_data: dict, db_session: AsyncSession):
    org1 = seeded_vector_data["org1"]
    service = VectorService(db_session)
    
    query_vector = [0.05] * 1536
    # Search under org1
    results = await service.search_similarity(org_id=org1.id, query_vector=query_vector, limit=5)
    
    # Assert result matches org1 data
    assert len(results) > 0
    for r in results:
        assert r["metadata"]["organization_id"] == str(org1.id)
        # Verify Org Two chunk is NOT returned despite having the exact same vector representation
        assert r["metadata"]["document_id"] != str(seeded_vector_data["document2"].id)

# 3. Index Management Tests
@pytest.mark.asyncio
async def test_index_manager_crud(seeded_vector_data: dict, db_session: AsyncSession):
    org1 = seeded_vector_data["org1"]
    from app.vector.index_manager import IndexManager
    manager = IndexManager(db_session)
    
    # Create index
    index_rec = await manager.create_index(
        org_id=org1.id,
        name="test_hnsw_idx",
        similarity_metric="COSINE",
        index_type="HNSW"
    )
    assert index_rec.name == "test_hnsw_idx"
    assert index_rec.status in ["ACTIVE", "REBUILDING"]
    
    # List indexes
    indexes = await manager.get_indexes(org1.id)
    assert len(indexes) > 0
    assert any(idx.name == "test_hnsw_idx" for idx in indexes)
    
    # Rebuild index
    success = await manager.rebuild_index(org1.id, "test_hnsw_idx")
    assert success is True

# 4. Lifecycle Synchronization & Vector Deletes
@pytest.mark.asyncio
async def test_vector_lifecycle_synchronize_and_delete(seeded_vector_data: dict, db_session: AsyncSession):
    org1 = seeded_vector_data["org1"]
    doc1 = seeded_vector_data["document1"]
    
    service = VectorService(db_session)
    
    # Clear chunk 1's embedding first to test synchronization
    stmt_del = select(DocumentEmbedding).where(DocumentEmbedding.chunk_id == seeded_vector_data["chunk1"].id)
    res = await db_session.execute(stmt_del)
    emb = res.scalar_one()
    await db_session.delete(emb)
    await db_session.commit()
    
    # Seed DocumentContent so syncer can extract and chunk
    content_json = {
        "paragraphs": [{"text": "Synced content line paragraph."}]
    }
    doc_content = DocumentContent(
        document_id=doc1.id,
        content_json=content_json,
        extracted_text="Synced content line paragraph.",
        statistics={"word_count": 4, "character_count": 30}
    )
    db_session.add(doc_content)
    await db_session.commit()
    
    # Sync embeddings
    sync_res = await service.synchronize(org1.id)
    assert sync_res["synced_documents_count"] > 0
    
    # Verify embeddings restored
    stmt_emb = select(DocumentEmbedding).join(
        DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
    ).where(DocumentChunk.document_id == doc1.id)
    embs = (await db_session.execute(stmt_emb)).scalars().all()
    assert len(embs) > 0
    
    # Delete document vectors
    deleted_count = await service.delete_document_vectors(doc1.id)
    assert deleted_count > 0
    
    # Assert they are gone
    stmt_embs_after = select(DocumentEmbedding).join(
        DocumentChunk, DocumentChunk.id == DocumentEmbedding.chunk_id
    ).where(DocumentChunk.document_id == doc1.id)
    embs_after = (await db_session.execute(stmt_embs_after)).scalars().all()
    assert len(embs_after) == 0

# 5. Router REST Endpoints
@pytest.mark.asyncio
async def test_router_endpoints(client: AsyncClient, seeded_vector_data: dict, db_session: AsyncSession):
    user = seeded_vector_data["user"]
    org1 = seeded_vector_data["org1"]
    doc1 = seeded_vector_data["document1"]
    token = create_access_token(data={"sub": str(user.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org1.id)
    }
    
    # GET /statistics
    response = await client.get("/api/v1/vector/statistics", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    assert "total_vectors" in stats
    assert "active_indexes" in stats
    
    # POST /index (Create index)
    index_payload = {
        "name": "api_hnsw_idx",
        "index_type": "HNSW",
        "similarity_metric": "COSINE"
    }
    response = await client.post("/api/v1/vector/index", json=index_payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "api_hnsw_idx"
    
    # GET /index (List indexes)
    response = await client.get("/api/v1/vector/index", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # POST /index/rebuild
    rebuild_payload = {"index_name": "api_hnsw_idx"}
    response = await client.post("/api/v1/vector/index/rebuild", json=rebuild_payload, headers=headers)
    assert response.status_code == 200
    
    # POST /optimize
    response = await client.post("/api/v1/vector/optimize", headers=headers)
    assert response.status_code == 200
    
    # POST /cleanup
    response = await client.post("/api/v1/vector/cleanup", headers=headers)
    assert response.status_code == 200
    
    # POST /synchronize
    response = await client.post("/api/v1/vector/synchronize", headers=headers)
    assert response.status_code == 200
    
    # POST /rebuild
    response = await client.post("/api/v1/vector/rebuild", headers=headers)
    assert response.status_code == 200
    
    # DELETE /document/{id}
    response = await client.delete(f"/api/v1/vector/document/{doc1.id}", headers=headers)
    assert response.status_code == 200
