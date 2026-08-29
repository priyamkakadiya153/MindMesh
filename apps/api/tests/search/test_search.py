import pytest
import pytest_asyncio
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from passlib.hash import bcrypt

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.project import Project
from app.workspace.models import Workspace
from app.documents.models import Document, DocumentMetadata
from app.processing.models import DocumentContent
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.core.security import create_access_token
from app.search.query_processor import QueryProcessor
from app.search.query_rewriter import rewrite_query
from app.search.entity_extractor import extract_entities
from app.search.cache import search_cache
from app.search.analytics import analytics_tracker
from app.retrieval.bm25 import search_bm25
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import rerank_candidates
from app.retrieval.scorer import calculate_freshness_decay, compute_combined_score

@pytest_asyncio.fixture
async def seeded_search_data(db_session: AsyncSession):

    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = "mocked_hashed_password"
    user = User(username="searchuser", email="search@example.com", hashed_password=hashed_pwd)

    db_session.add(user)
    await db_session.flush()

    org = Organization(name="Search Org", slug="search-org", owner_id=user.id)
    db_session.add(org)
    await db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(member)
    await db_session.flush()

    ws = Workspace(name="Search WS", slug="search-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()

    proj = Project(name="Search Proj", slug="search-proj", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.flush()

    # Document 1 (Older, tags=[k8s])
    doc1 = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="k8s_guide.md",
        original_filename="k8s_guide.md",
        mime_type="text/markdown",
        extension="md",
        size=1024,
        checksum_sha256="checksum111",
        storage_path="orgs/search-org/k8s_guide.md",
        processing_status="READY",
        visibility="private",
        created_at=datetime.utcnow() - timedelta(days=20) # 20 days old
    )
    db_session.add(doc1)
    await db_session.flush()

    meta1 = DocumentMetadata(
        document_id=doc1.id,
        title="Kubernetes Guide",
        keywords={"tags": ["k8s", "kubernetes", "infra"]}
    )
    db_session.add(meta1)
    await db_session.flush()

    chunk1 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=1,
        content="This document describes how to deploy clusters on Kubernetes (k8s). Kubernetes orchestrates containers.",
        token_count=18,
        metadata_json={
            "organization_id": str(org.id),
            "workspace_id": str(ws.id),
            "project_id": str(proj.id),
            "document_id": str(doc1.id),
            "tags": ["k8s", "kubernetes", "infra"]
        }
    )
    db_session.add(chunk1)
    await db_session.flush()

    emb1 = DocumentEmbedding(
        chunk_id=chunk1.id,
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        embedding=[0.01] * 1536,
        checksum="checksum1"
    )
    db_session.add(emb1)
    await db_session.flush()

    # Document 2 (Newer, tags=[auth])
    doc2 = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="auth_spec.md",
        original_filename="auth_spec.md",
        mime_type="text/markdown",
        extension="md",
        size=512,
        checksum_sha256="checksum222",
        storage_path="orgs/search-org/auth_spec.md",
        processing_status="READY",
        visibility="private",
        created_at=datetime.utcnow() # fresh
    )
    db_session.add(doc2)
    await db_session.flush()

    meta2 = DocumentMetadata(
        document_id=doc2.id,
        title="Authentication Spec",
        keywords={"tags": ["auth", "security"]}
    )
    db_session.add(meta2)
    await db_session.flush()

    chunk2 = DocumentChunk(
        document_id=doc2.id,
        chunk_index=1,
        content="This specification explains the authentication (auth) and security design of MindMesh JWT system.",
        token_count=18,
        metadata_json={
            "organization_id": str(org.id),
            "workspace_id": str(ws.id),
            "project_id": str(proj.id),
            "document_id": str(doc2.id),
            "tags": ["auth", "security"]
        }
    )
    db_session.add(chunk2)
    await db_session.flush()

    emb2 = DocumentEmbedding(
        chunk_id=chunk2.id,
        embedding_model="text-embedding-3-small",
        embedding_dimension=1536,
        embedding=[0.02] * 1536,
        checksum="checksum2"
    )
    db_session.add(emb2)
    await db_session.commit()

    return {
        "user": user,
        "org": org,
        "workspace": ws,
        "project": proj,
        "doc1": doc1,
        "doc2": doc2,
        "chunk1": chunk1,
        "chunk2": chunk2
    }

# 1. Query Processing Unit Tests
def test_query_normalizer_and_lang():
    assert QueryProcessor.normalize("  Deploy k8S! ") == "deploy k8s!"
    assert QueryProcessor.detect_language("Der server ist online und bereit") == "de"
    assert QueryProcessor.detect_language("C'est le guide d'installation") == "fr"
    assert QueryProcessor.detect_language("Deploy kubernetes clusters") == "en"

def test_query_rewriter():
    assert rewrite_query("k8s clusters on pg") == "kubernetes clusters on postgresql"
    assert rewrite_query("auth design spec") == "authentication design spec"

def test_entity_extractor():
    filters = extract_entities("project:search-ws tag:k8s pdf document uploaded yesterday")
    assert filters.get("project") == "search-ws"
    assert filters.get("tag") == "k8s"
    assert filters.get("file_type") == "pdf"
    assert "created_after" in filters

# 2. BM25 Lexical Ranking Unit Test
@pytest.mark.asyncio
async def test_bm25_lexical_search(seeded_search_data: dict, db_session: AsyncSession):
    org = seeded_search_data["org"]
    results = await search_bm25(db_session, "kubernetes deploy", limit=5, filters={"organization_id": str(org.id)})
    assert len(results) > 0
    assert "deploy" in results[0]["content"].lower()

# 3. Reciprocal Rank Fusion & Reranking Tests
def test_reciprocal_rank_fusion():
    lexical = [{"chunk_id": "A", "score": 10.0}, {"chunk_id": "B", "score": 5.0}]
    vector = [{"chunk_id": "B", "score": 0.9}, {"chunk_id": "C", "score": 0.8}]
    
    # Fused results should prioritize B (since it appears in both lists)
    fused = reciprocal_rank_fusion(lexical, vector, k=60, limit=10)
    assert len(fused) == 3
    assert fused[0]["chunk_id"] == "B"

def test_cross_encoder_reranking():
    candidates = [
        {"content": "Authentication guide for developers", "score": 0.5},
        {"content": "Deploy containers in kubernetes clusters", "score": 0.4}
    ]
    # Reranking for "authentication" query should boost matching items
    reranked = rerank_candidates(candidates, "authentication", limit=10)
    assert len(reranked) == 2
    assert "authentication" in reranked[0]["content"].lower()
    assert reranked[0]["score"] > reranked[1]["score"]

# 4. Freshness Scoring decay Tests
def test_freshness_decay_scoring():
    fresh_date = datetime.utcnow()
    old_date = datetime.utcnow() - timedelta(days=50)
    
    fresh_decay = calculate_freshness_decay(fresh_date)
    old_decay = calculate_freshness_decay(old_date)
    
    # Fresh item decay score should be closer to 1.0 than old item
    assert fresh_decay > old_decay
    
    score_fresh = compute_combined_score(base_score=0.8, created_at=fresh_date)
    score_old = compute_combined_score(base_score=0.8, created_at=old_date)
    assert score_fresh > score_old

# 5. Cache Eviction & TTL
def test_caching_layer():
    search_cache.clear()
    search_cache.set("query:key1", {"data": "hits"})
    assert search_cache.get("query:key1") == {"data": "hits"}
    
    # Expired fetch should return None
    search_cache._cache["query:key1"] = ({"data": "hits"}, 0.0) # set expiry to epoch 0
    assert search_cache.get("query:key1") is None

# 6. Analytics Logging
def test_analytics_logging():
    analytics_tracker._logs.clear()
    analytics_tracker.record_search("k8s guide", 45.5, 10, "user_123", "ws_123")
    
    # Query history
    history = analytics_tracker.get_recent_history("user_123")
    assert len(history) == 1
    assert history[0] == "k8s guide"
    
    # Popular queries
    pop = analytics_tracker.get_popular_queries()
    assert pop[0]["query"] == "k8s guide"
    
    # Click register
    analytics_tracker.record_click("k8s guide", "doc_111")
    assert analytics_tracker._logs[-1]["clicks"] == ["doc_111"]

# 7. Router Endpoints
@pytest.mark.asyncio
async def test_search_router_apis(client: AsyncClient, seeded_search_data: dict, db_session: AsyncSession):
    user = seeded_search_data["user"]
    org = seeded_search_data["org"]
    token = create_access_token(subject=str(user.id), expires_delta=timedelta(days=1))


    headers = {

        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    
    # Seed document content so semantic search has extracted content to run properly
    doc2 = seeded_search_data["doc2"]
    content_json = {
        "paragraphs": [{"text": "This specification explains the authentication (auth) and security design of MindMesh JWT system."}]
    }
    doc_content = DocumentContent(
        document_id=doc2.id,
        content_json=content_json,
        extracted_text="This specification explains the authentication (auth) and security design of MindMesh JWT system.",
        statistics={"word_count": 13, "character_count": 80}
    )
    db_session.add(doc_content)
    await db_session.commit()

    # Seed query logs so suggestions returns values
    analytics_tracker.record_search("auth spec", 10.0, 1, str(user.id))

    # POST /semantic
    response = await client.post("/api/v1/search/semantic", json={"query": "k8s"}, headers=headers)
    assert response.status_code == 200


    assert "results" in response.json()
    
    # POST /hybrid
    response = await client.post("/api/v1/search/hybrid", json={"query": "authentication"}, headers=headers)
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0
    
    # POST /metadata
    meta_payload = {"filters": {"tag": "security"}}
    response = await client.post("/api/v1/search/metadata", json=meta_payload, headers=headers)
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0
    
    # GET /suggestions
    response = await client.get("/api/v1/search/suggestions?q=auth", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # GET /history
    response = await client.get("/api/v1/search/history", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
