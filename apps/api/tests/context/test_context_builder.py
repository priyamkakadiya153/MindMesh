import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.projects.models import Project, ProjectMember
from app.workspace.models import Workspace, WorkspaceMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.core.security import create_access_token

# Import our implementations
from app.ai.context.builder import ContextBuilder
from app.ai.context.merger import ChunkMerger
from app.ai.context.ranking import ContextRanker
from app.ai.context.compressor import ContextCompressor
from app.ai.context.tokenizer import TokenBudgetManager, MODEL_BUDGETS
from app.ai.prompt.builder import PromptBuilder
from app.ai.citations.engine import CitationEngine
from app.ai.conversation.memory import ConversationMemoryManager
from app.ai.conversation.history import ConversationHistoryManager
from app.ai.conversation.summarizer import ConversationSummarizer
from app.models.chat import Chat
from app.models.message import Message

async def seed_ai_data(db_session: AsyncSession) -> dict:
    """Helper function to seed mock database records in an active session."""
    # Setup roles and user
    role = Role(name="MEMBER", description="Standard Member Role")
    db_session.add(role)
    await db_session.flush()
    
    user = User(username="aiuser", email="ai@example.com", hashed_password="hashed_password_123")
    db_session.add(user)
    
    other_user = User(username="other_aiuser", email="other_ai@example.com", hashed_password="hashed_password_123")
    db_session.add(other_user)
    await db_session.flush()

    # Orgs
    org = Organization(name="AI Org", slug="ai-org", owner_id=user.id)
    db_session.add(org)
    other_org = Organization(name="Other AI Org", slug="other-ai-org", owner_id=other_user.id)
    db_session.add(other_org)
    await db_session.flush()

    # Memberships
    org_member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(org_member)
    other_org_member = OrganizationMember(organization_id=other_org.id, user_id=other_user.id, role_id=role.id)
    db_session.add(other_org_member)
    await db_session.flush()

    # Workspace
    ws = Workspace(name="AI WS", slug="ai-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()
    
    ws_member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="MEMBER")
    db_session.add(ws_member)
    await db_session.flush()

    # Projects
    proj = Project(name="AI Project", slug="ai-project", workspace_id=ws.id, organization_id=org.id, visibility="public")
    db_session.add(proj)
    
    private_proj = Project(name="Private Project", slug="private-proj", workspace_id=ws.id, organization_id=org.id, visibility="private")
    db_session.add(private_proj)
    await db_session.flush()

    # Add user to public project
    pm = ProjectMember(project_id=proj.id, user_id=user.id, role="VIEWER")
    db_session.add(pm)
    await db_session.flush()

    # Document 1 (in public project)
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
    
    # Document 2 (in private project)
    doc2 = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=private_proj.id,
        filename="Confidential.pdf",
        original_filename="Confidential.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=2048,
        checksum_sha256="xyz789sha",
        storage_provider="local",
        storage_path="/path/confidential.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc2)
    
    # Document 3 (in other organization)
    other_ws = Workspace(name="Other WS", slug="other-ws", organization_id=other_org.id)
    db_session.add(other_ws)
    await db_session.flush()
    
    other_proj = Project(name="Other Proj", slug="other-proj", workspace_id=other_ws.id, organization_id=other_org.id)
    db_session.add(other_proj)
    await db_session.flush()

    doc3 = Document(
        organization_id=other_org.id,
        workspace_id=other_ws.id,
        project_id=other_proj.id,
        filename="OtherManual.pdf",
        original_filename="OtherManual.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=512,
        checksum_sha256="def456sha",
        storage_provider="local",
        storage_path="/path/other.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc3)
    await db_session.flush()

    # Add Chunks
    chunk1 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=0,
        content="This is paragraph one of the user manual detailing installation instructions.",
        token_count=15,
        metadata_json={"page": 1, "heading": "Installation"}
    )
    chunk2 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=1,
        content="This is paragraph two of the manual detailing setup and initialization rules.",
        token_count=15,
        metadata_json={"page": 1, "heading": "Installation"}
    )
    chunk3 = DocumentChunk(
        document_id=doc2.id,
        chunk_index=0,
        content="This is highly confidential code to authenticate access tokens inside the enterprise.",
        token_count=15,
        metadata_json={"page": 1, "heading": "Security"}
    )
    db_session.add_all([chunk1, chunk2, chunk3])
    await db_session.commit()

    return {
        "user": user,
        "org": org,
        "other_user": other_user,
        "other_org": other_org,
        "workspace": ws,
        "project": proj,
        "private_project": private_proj,
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3,
        "chunk1": chunk1,
        "chunk2": chunk2,
        "chunk3": chunk3
    }

# ----------------- UNIT TESTS -----------------

def test_chunk_merger():
    chunks = [
        {"document_id": "doc1", "content": "Hello page 1", "score": 0.9, "page": 1, "chunk_index": 0},
        {"document_id": "doc1", "content": "page 1 cont", "score": 0.8, "page": 1, "chunk_index": 1},
        {"document_id": "doc1", "content": "Hello page 1", "score": 0.7, "page": 1, "chunk_index": 0}, # duplicate
        {"document_id": "doc2", "content": "Another doc contents", "score": 0.55, "page": 1, "chunk_index": 0}
    ]
    merged = ChunkMerger.merge_chunks(chunks)
    assert len(merged) == 2
    doc1_merged = [c for c in merged if c["document_id"] == "doc1"][0]
    assert "Hello page 1" in doc1_merged["content"]
    assert "page 1 cont" in doc1_merged["content"]
    assert doc1_merged["score"] == 0.9

def test_context_ranking():
    chunks = [
        {"document_id": "doc1", "score": 0.5, "workspace_id": "ws1", "project_id": "proj1"},
        {"document_id": "doc2", "score": 0.6, "workspace_id": "ws2", "project_id": "proj2"},
        {"document_id": "doc3", "score": 0.7, "workspace_id": "ws1", "project_id": "proj3"}
    ]
    ranked = ContextRanker.rank_chunks(chunks, active_workspace_id="ws1", active_project_id="proj1")
    assert ranked[0]["document_id"] == "doc1"
    assert ranked[1]["document_id"] == "doc3"
    assert ranked[2]["document_id"] == "doc2"

def test_context_compressor():
    chunks = [
        {"content": "This is a long sentence discussing installation. It contains helper tips.", "token_count": 20, "score": 0.9}
    ]
    # Set limit to 15 to allow sentence 1 to fit under target_tokens check
    compressed = ContextCompressor.compress_chunks(chunks, token_limit=15, query="installation")
    assert len(compressed) == 1
    assert "installation" in compressed[0]["content"]

def test_token_budget_manager():
    budget = TokenBudgetManager.allocate_budget("gemini-2.0-flash", query="test query")
    assert budget["total_limit"] == 1048576
    assert budget["context_limit"] > 500000

# ----------------- INTEGRATION TESTS -----------------

@pytest.mark.asyncio
async def test_context_builder_security(db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    
    # 1. Accessing public document is allowed
    chunks = [
        {"document_id": str(data["doc1"].id), "content": "Public content", "score": 0.9, "page": 1}
    ]
    res = await ContextBuilder.build_context(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        chunks=chunks
    )
    assert len(res["chunks"]) == 1
    assert "Public content" in res["context_string"]

    # 2. Accessing document from other org is filtered out
    other_chunks = [
        {"document_id": str(data["doc3"].id), "content": "Other org content", "score": 0.9, "page": 1}
    ]
    res_other = await ContextBuilder.build_context(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        chunks=other_chunks
    )
    assert len(res_other["chunks"]) == 0

    # 3. Accessing private project document is filtered since user is not a member
    private_chunks = [
        {"document_id": str(data["doc2"].id), "content": "Confidential content", "score": 0.9, "page": 1}
    ]
    res_priv = await ContextBuilder.build_context(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        chunks=private_chunks
    )
    assert len(res_priv["chunks"]) == 0

@pytest.mark.asyncio
async def test_citation_engine(db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    ai_response = "We can proceed with paragraph one and installation instructions [1]."
    retrieved = [
        {"document_id": str(data["doc1"].id), "content": "This is paragraph one of the user manual detailing installation instructions.", "page": 1}
    ]
    citations = await CitationEngine.generate_citations(
        db=db_session,
        user_id=data["user"].id,
        org_id=data["org"].id,
        ai_response=ai_response,
        retrieved_chunks=retrieved
    )
    assert len(citations) == 1
    assert citations[0].document == "Manual.pdf"

@pytest.mark.asyncio
async def test_conversation_memory_db(db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    chat = Chat(organization_id=data["org"].id, name="Test AI Chat")
    db_session.add(chat)
    await db_session.commit()
    
    mem = await ConversationMemoryManager.save_memory(
        db=db_session,
        chat_id=chat.id,
        workspace_id=data["workspace"].id,
        project_id=data["project"].id,
        context_data={"key": "val"}
    )
    await db_session.commit()
    assert mem.chat_id == chat.id
    
    loaded = await ConversationMemoryManager.load_memory(db_session, chat.id)
    assert loaded is not None
    assert loaded.context_data["key"] == "val"
    
    cleared = await ConversationMemoryManager.clear_memory(db_session, chat.id)
    await db_session.commit()
    assert cleared is True

# ----------------- ROUTER ENDPOINTS TESTS -----------------

@pytest.mark.asyncio
async def test_context_build_api(client: AsyncClient, db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    payload = {
        "chunks": [
            {"document_id": str(data["doc1"].id), "content": "Manual installation guidelines", "score": 0.88, "page": 2}
        ],
        "workspace_id": str(data["workspace"].id),
        "project_id": str(data["project"].id)
    }
    
    res = await client.post("/api/v1/context/build", json=payload, headers=headers)
    assert res.status_code == 200
    json_data = res.json()
    assert "context_string" in json_data

@pytest.mark.asyncio
async def test_context_compress_api(client: AsyncClient, db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    payload = {
        "chunks": [
            {"document_id": str(data["doc1"].id), "content": "This is sample sentence one. This is sample sentence two.", "score": 0.9}
        ],
        "token_limit": 8,
        "query": "one"
    }
    
    res = await client.post("/api/v1/context/compress", json=payload, headers=headers)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["compression_ratio"] <= 1.0

@pytest.mark.asyncio
async def test_prompt_build_api(client: AsyncClient, db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    payload = {
        "query": "How do I install the platform?",
        "context_string": "<source index=\"1\"><content>Run manual setup</content></source>",
        "history": [
            {"role": "user", "content": "Hello AI"},
            {"role": "assistant", "content": "Hello User"}
        ]
    }
    
    res = await client.post("/api/v1/prompt/build", json=payload, headers=headers)
    assert res.status_code == 200
    json_data = res.json()
    assert "messages" in json_data
    assert json_data["is_safe"] is True

@pytest.mark.asyncio
async def test_conversations_memory_endpoints(client: AsyncClient, db_session: AsyncSession):
    data = await seed_ai_data(db_session)
    token = create_access_token(str(data["user"].id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(data["org"].id)
    }
    
    # 1. Create a Chat and Message in DB
    chat = Chat(organization_id=data["org"].id, name="Conversations API Chat")
    db_session.add(chat)
    await db_session.flush()
    
    msg = Message(
        chat_id=chat.id,
        sender_id=data["user"].id,
        organization_id=data["org"].id,
        content="Testing message retrieve"
    )
    db_session.add(msg)
    await db_session.commit()
    
    # 2. Add some memory metadata
    await ConversationMemoryManager.save_memory(
        db=db_session,
        chat_id=chat.id,
        workspace_id=data["workspace"].id,
        project_id=data["project"].id,
        context_data={"test": "ok"}
    )
    await db_session.commit()
    
    # 3. GET conversation memory
    get_res = await client.get(f"/api/v1/conversations/{chat.id}/memory", headers=headers)
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data["history"]) == 1
    assert get_data["history"][0]["content"] == "Testing message retrieve"
    assert get_data["context_data"]["test"] == "ok"
    
    # 4. DELETE conversation memory
    del_res = await client.delete(f"/api/v1/conversations/{chat.id}/memory", headers=headers)
    assert del_res.status_code == 200
