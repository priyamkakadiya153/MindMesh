import pytest
import json
from uuid import uuid4, UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.projects.models import Project, ProjectMember
from app.workspace.models import Workspace, WorkspaceMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.core.security import create_access_token
from app.models.chat import Chat
from app.models.message import Message

from app.ai.llm.factory import LLMProviderFactory
from app.ai.rag.pipeline import RAGPipeline
from app.ai.chat.service import ChatService
from app.ai.chat.session import ChatSessionManager

async def seed_chat_data(db_session: AsyncSession) -> dict:
    """Helper function to seed mock database records in an active session."""
    # Setup roles and user
    role = Role(name="MEMBER", description="Standard Member Role")
    db_session.add(role)
    await db_session.flush()
    
    user = User(username="chatuser", email="chat@example.com", hashed_password="hashed_password_123")
    db_session.add(user)
    await db_session.flush()

    # Orgs
    org = Organization(name="Chat Org", slug="chat-org", owner_id=user.id)
    db_session.add(org)
    await db_session.flush()

    # Memberships
    org_member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(org_member)
    await db_session.flush()

    # Workspace
    ws = Workspace(name="Chat WS", slug="chat-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()
    
    ws_member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="MEMBER")
    db_session.add(ws_member)
    await db_session.flush()

    # Projects
    proj = Project(name="Chat Project", slug="chat-project", workspace_id=ws.id, organization_id=org.id, visibility="public")
    db_session.add(proj)
    await db_session.flush()

    # Add user to public project
    pm = ProjectMember(project_id=proj.id, user_id=user.id, role="VIEWER")
    db_session.add(pm)
    await db_session.flush()

    # Document (in public project)
    doc1 = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        filename="Manual.pdf",
        original_filename="Manual.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=1024,
        checksum_sha256="abc123sha",
        storage_provider="local",
        storage_path="/path/manual.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc1)
    await db_session.flush()

    # Add Chunks
    chunk1 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=0,
        content="This is paragraph one of the user manual detailing installation instructions.",
        token_count=15,
        metadata_json={"page": 1, "heading": "Installation"}
    )
    db_session.add(chunk1)
    await db_session.commit()

    # Mock retrieval to return seeded chunk in tests
    from unittest.mock import AsyncMock
    from app.ai.rag.retrieval import RAGRetrieval
    RAGRetrieval.retrieve_grounded_chunks = AsyncMock(return_value=[
        {
            "chunk_id": chunk1.id,
            "content": chunk1.content,
            "page": 1,
            "document_id": doc1.id,
            "title": "Manual.pdf",
            "score": 0.95,
            "workspace": "chat-ws",
            "project": "chat-project",
            "version": 1
        }
    ])

    return {
        "user": user,
        "org": org,
        "workspace": ws,
        "project": proj,
        "doc1": doc1,
        "chunk1": chunk1
    }

# ----------------- UNIT TESTS -----------------

def test_llm_factory():
    provider = LLMProviderFactory.get_provider("gemini", "gemini-2.0-flash")
    assert provider is not None
    assert provider.model_name == "gemini-2.0-flash"
    
    provider_default = LLMProviderFactory.get_provider("invalid-name")
    assert provider_default is not None
    
    providers = LLMProviderFactory.list_supported_providers()
    assert "gemini" in providers
    assert "openai" in providers

# ----------------- INTEGRATION TESTS -----------------

@pytest.mark.asyncio
async def test_rag_pipeline_blocking(db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    pipeline = RAGPipeline(db_session)
    
    res = await pipeline.query(
        user_id=data["user"].id,
        org_id=data["org"].id,
        query="How do I install the manual?",
        workspace_id=data["workspace"].id,
        project_id=data["project"].id,
        provider_name="gemini",
        model_name="gemini-2.0-flash"
    )
    assert res is not None
    assert "answer" in res
    assert res["confidence"] > 0.0
    assert len(res["suggestions"]) > 0

@pytest.mark.asyncio
async def test_rag_pipeline_streaming(db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    pipeline = RAGPipeline(db_session)
    
    chunks_received = []
    async for event in pipeline.stream_query(
        user_id=data["user"].id,
        org_id=data["org"].id,
        query="How do I install the manual?",
        workspace_id=data["workspace"].id,
        project_id=data["project"].id,
        provider_name="gemini",
        model_name="gemini-2.0-flash"
    ):
        chunks_received.append(event)
        
    assert len(chunks_received) >= 2
    assert chunks_received[0]["type"] == "token"
    assert chunks_received[-1]["type"] == "final"
    assert "citations" in chunks_received[-1]

@pytest.mark.asyncio
async def test_chat_service_flow(db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    
    chat_res = await ChatService.execute_chat(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        query="What is page one about?",
        workspace_id=data["workspace"].id,
        project_id=data["project"].id
    )
    assert "chat_id" in chat_res
    chat_id = chat_res["chat_id"]
    
    # Run follow-up chat
    follow_up = await ChatService.execute_chat(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        query="Tell me more",
        workspace_id=data["workspace"].id,
        project_id=data["project"].id,
        chat_id=chat_id
    )
    assert follow_up["chat_id"] == chat_id

# ----------------- ROUTER ENDPOINTS TESTS -----------------

@pytest.mark.asyncio
async def test_chat_endpoints(client: AsyncClient, db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    # 1. POST blocking chat
    payload = {
        "query": "How to setup?",
        "workspace_id": str(data["workspace"].id),
        "project_id": str(data["project"].id)
    }
    res = await client.post("/api/v1/chat", json=payload, headers=headers)
    assert res.status_code == 200
    json_data = res.json()
    assert "chat_id" in json_data
    chat_id = json_data["chat_id"]
    
    # 2. GET chat session details
    get_res = await client.get(f"/api/v1/chat/{chat_id}", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["chat_id"] == chat_id
    # Should contain 2 messages: 1 user message, 1 assistant message
    assert len(get_data["messages"]) == 2
    assert get_data["messages"][0]["role"] == "user"
    assert get_data["messages"][1]["role"] == "assistant"
    
    # 3. DELETE chat session
    del_res = await client.delete(f"/api/v1/chat/{chat_id}", headers=headers)
    assert del_res.status_code == 200

@pytest.mark.asyncio
async def test_chat_stream_endpoint(client: AsyncClient, db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    payload = {
        "query": "Streaming installation instructions",
        "workspace_id": str(data["workspace"].id)
    }
    
    res = await client.post("/api/v1/chat/stream", json=payload, headers=headers)
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    
    # Read stream chunks
    body = res.text
    assert "data:" in body

@pytest.mark.asyncio
async def test_rag_endpoints(client: AsyncClient, db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    payload = {
        "query": "Quick RAG check without saving session history",
        "workspace_id": str(data["workspace"].id)
    }
    
    # 1. RAG query
    res = await client.post("/api/v1/rag/query", json=payload, headers=headers)
    assert res.status_code == 200
    assert "answer" in res.json()
    
    # 2. RAG stream
    res_stream = await client.post("/api/v1/rag/stream", json=payload, headers=headers)
    assert res_stream.status_code == 200
    assert "text/event-stream" in res_stream.headers["content-type"]

@pytest.mark.asyncio
async def test_llm_metadata_endpoints(client: AsyncClient, db_session: AsyncSession):
    data = await seed_chat_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    # 1. GET models list
    res_models = await client.get("/api/v1/llm/models", headers=headers)
    assert res_models.status_code == 200
    assert "gemini-2.0-flash" in res_models.json()
    
    # 2. GET providers list
    res_provs = await client.get("/api/v1/llm/providers", headers=headers)
    assert res_provs.status_code == 200
    assert "gemini" in res_provs.json()
