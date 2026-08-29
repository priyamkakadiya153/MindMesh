import pytest
import json
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.projects.models import Project, ProjectMember
from app.workspace.models import Workspace, WorkspaceMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.models.conversations import Conversation, DirectMessage
from app.models.task import Task
from app.models.chat import Chat
from app.models.message import Message

from app.ai.orchestrator import MindMeshAIOrchestrator
from app.ai.understanding.engine import SemanticUnderstandingEngine
from app.ai.understanding.models import CapabilityType, RequestIntent
from app.ai.intent.engine import IntentEngine
from app.ai.intent.models import IntentType

async def seed_env(db: AsyncSession, username_prefix: str = "user"):
    """Helper to create authenticated User, Org, Workspace and Memberships."""
    role = Role(name="MEMBER", description="Standard Member Role")
    db.add(role)
    await db.flush()

    user = User(username=f"{username_prefix}_{uuid4().hex[:4]}", email=f"{username_prefix}_{uuid4().hex[:4]}@example.com", hashed_password="pwd")
    db.add(user)
    await db.flush()

    org = Organization(name=f"{username_prefix} Org", slug=f"org-{uuid4().hex[:6]}", owner_id=user.id)
    db.add(org)
    await db.flush()

    org_member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db.add(org_member)
    await db.flush()

    ws = Workspace(name=f"{username_prefix} WS", slug=f"ws-{uuid4().hex[:6]}", organization_id=org.id)
    db.add(ws)
    await db.flush()

    ws_member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="MEMBER")
    db.add(ws_member)
    await db.flush()

    return user, org, ws, role

@pytest.mark.asyncio
async def test_intent_understanding_routing():
    """Test 1: Verify semantic intent routing for knowledge, extraction, summaries, and explicit searches."""
    
    # 1. Architectural Knowledge Question
    res1 = SemanticUnderstandingEngine.parse_request("What are the main architectural decisions made in this project?")
    assert res1.required_capability in [CapabilityType.KNOWLEDGE_SYNTHESIS, CapabilityType.DOCUMENT_RAG]
    assert res1.required_capability != CapabilityType.CONVERSATION_SEARCH_SERVICE

    # 2. Task and Decision Extraction
    res2 = SemanticUnderstandingEngine.parse_request("Extract all tasks, responsibilities, deadlines, and decisions from this project discussion.")
    assert res2.required_capability == CapabilityType.TASK_EXTRACTION
    assert res2.intent == RequestIntent.EXTRACTION_REQUEST
    assert res2.required_capability != CapabilityType.CONVERSATION_SEARCH_SERVICE

    # 3. Discussion Summary
    res3 = SemanticUnderstandingEngine.parse_request("Summarize this project discussion")
    assert res3.required_capability == CapabilityType.DISCUSSION_SUMMARY
    assert res3.intent == RequestIntent.SUMMARY_REQUEST
    assert res3.required_capability != CapabilityType.CONVERSATION_SEARCH_SERVICE

    # 4. Explicit Search Request
    res4 = SemanticUnderstandingEngine.parse_request("Find conversations about API gateway")
    assert res4.required_capability == CapabilityType.CONVERSATION_SEARCH_SERVICE

    # 5. Document Specific Question
    res5 = SemanticUnderstandingEngine.parse_request("What does the Architecture.pdf say about the API gateway?")
    assert res5.required_capability in [CapabilityType.DOCUMENT_RAG, CapabilityType.KNOWLEDGE_SYNTHESIS]

    # 6. Decision Query
    res6 = SemanticUnderstandingEngine.parse_request("What decisions have we made about authentication?")
    assert res6.required_capability in [CapabilityType.KNOWLEDGE_SYNTHESIS, CapabilityType.DOCUMENT_RAG]
    assert res6.required_capability != CapabilityType.CONVERSATION_SEARCH_SERVICE

@pytest.mark.asyncio
async def test_explicit_conversation_search_excludes_ai_chats(db_session: AsyncSession):
    """Test 2: Explicit conversation search returns real workspace conversations and excludes AI Chat threads."""
    
    user, org, ws, role = await seed_env(db_session, "expsearch")

    # 1. Seed genuine team conversation in Conversation and DirectMessage
    conv = Conversation(name="Project Discussion", organization_id=org.id, workspace_id=ws.id, type="group")
    db_session.add(conv)
    await db_session.flush()

    dm1 = DirectMessage(
        conversation_id=conv.id,
        sender_id=user.id,
        organization_id=org.id,
        workspace_id=ws.id,
        content="Please complete the API gateway documentation by tomorrow.",
        message_type="TEXT"
    )
    db_session.add(dm1)
    await db_session.flush()

    # 2. Seed an AI Chat session with matching name and assistant responses (which MUST be excluded)
    ai_chat = Chat(
        name="New Conversation — API Gateway AI Research",
        organization_id=org.id,
        workspace_id=ws.id,
        user_id=user.id
    )
    db_session.add(ai_chat)
    await db_session.flush()

    ai_msg = Message(
        chat_id=ai_chat.id,
        sender_id=user.id,
        organization_id=org.id,
        role="assistant",
        content="Found 4 matching conversations about API gateway..."
    )
    db_session.add(ai_msg)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="Find conversations about API gateway",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    assert response["capability"] == "CONVERSATION_SEARCH_SERVICE"
    
    # Must contain the real team discussion
    assert "Project Discussion" in content
    assert "Please complete the API gateway documentation" in content

    # Must NOT contain AI Chat's own session or assistant responses
    assert "New Conversation" not in content
    assert "Found 4 matching conversations" not in content
    assert "Find conversations about API gateway" not in content

@pytest.mark.asyncio
async def test_ai_chat_generated_conversation_not_in_workspace_knowledge(db_session: AsyncSession):
    """Test 3: AI Chat generated conversation sessions are NOT returned as workspace knowledge."""
    
    user, org, ws, role = await seed_env(db_session, "noknowleak")

    # Seed an AI Chat thread mentioning architecture
    ai_chat = Chat(
        name="Architecture Chat Session",
        organization_id=org.id,
        workspace_id=ws.id,
        user_id=user.id
    )
    db_session.add(ai_chat)
    await db_session.flush()

    ai_msg = Message(
        chat_id=ai_chat.id,
        sender_id=user.id,
        organization_id=org.id,
        role="assistant",
        content="Previously generated AI thoughts on architecture and services."
    )
    db_session.add(ai_msg)
    await db_session.commit()

    # Query for a project that has no real documents
    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="What are the main architectural decisions in the secret project zeta?",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    # Should safely fallback and NOT retrieve the AI Chat session
    assert "couldn't find enough information" in content.lower() or "not enough information" in content.lower()
    assert "Previously generated AI thoughts" not in content

@pytest.mark.asyncio
async def test_ai_chat_generated_answer_not_in_search_results(db_session: AsyncSession):
    """Test 4: AI Chat generated answers are NOT returned in explicit conversation search."""
    
    user, org, ws, role = await seed_env(db_session, "noanssearch")

    # Only an AI Chat message exists with the term "Redis clustering"
    ai_chat = Chat(
        name="Redis Chat",
        organization_id=org.id,
        workspace_id=ws.id,
        user_id=user.id
    )
    db_session.add(ai_chat)
    await db_session.flush()

    ai_msg = Message(
        chat_id=ai_chat.id,
        sender_id=user.id,
        organization_id=org.id,
        role="assistant",
        content="AI generated analysis: Redis clustering is active."
    )
    db_session.add(ai_msg)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="Find conversations about Redis clustering",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    assert "couldn't find any conversations" in content.lower()
    assert "AI generated analysis" not in content

@pytest.mark.asyncio
async def test_same_thread_followup_context_preserved(db_session: AsyncSession):
    """Test 5: Multi-turn follow-up inside the SAME AI Chat thread uses conversation history seamlessly."""
    
    user, org, ws, role = await seed_env(db_session, "followup")

    # Seed an architecture document
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        filename="Architecture.pdf",
        original_filename="Architecture.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=2048,
        checksum_sha256="abc123sha_followup",
        storage_provider="local",
        storage_path="/path/arch.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        organization_id=org.id,
        workspace_id=ws.id,
        chunk_index=0,
        content="Core Architecture Decisions: 1. FastAPI backend. 2. PostgreSQL database. 3. Kong API Gateway.",
        token_count=20,
        metadata_json={"page": 1}
    )
    db_session.add(chunk)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    
    # Turn 1
    resp1 = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="What are the architectural decisions in this project?",
        workspace_id=ws.id,
        provider="mock"
    )
    chat_id = resp1.get("conversation_id")
    assert chat_id is not None

    # Turn 2: Follow-up question in the same chat
    resp2 = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="Which one affects the API layer?",
        conversation_id=chat_id,
        workspace_id=ws.id,
        provider="mock"
    )

    content2 = resp2.get("content") or resp2.get("answer") or ""
    assert content2 is not None
    assert len(content2) > 0
    assert resp2["conversation_id"] == chat_id

@pytest.mark.asyncio
async def test_knowledge_synthesis_uses_actual_workspace_evidence(db_session: AsyncSession):
    """Test 6: Knowledge synthesis uses actual workspace documents and project discussions as evidence."""
    
    user, org, ws, role = await seed_env(db_session, "evidencesynth")

    # Real document in workspace
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        filename="Architecture.pdf",
        original_filename="Architecture.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=2048,
        checksum_sha256="abc123sha_evid",
        storage_provider="local",
        storage_path="/path/arch.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        organization_id=org.id,
        workspace_id=ws.id,
        chunk_index=0,
        content="MindMesh Architecture: FastAPI backend, PostgreSQL database, and Redis caching.",
        token_count=20,
        metadata_json={"page": 1}
    )
    db_session.add(chunk)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="What are the main architectural decisions made in this project?",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    assert "I found these related conversation threads" not in content
    assert "Architectural Decisions" in content or "FastAPI" in content or "architecture" in content.lower()
    assert response["capability"] in ["KNOWLEDGE_SYNTHESIS", "DOCUMENT_RAG", "DECISION_SERVICE"]

@pytest.mark.asyncio
async def test_task_extraction_uses_actual_workspace_evidence(db_session: AsyncSession):
    """Test 7: Task & decision extraction extracts from authentic team discussions."""
    
    user, org, ws, role = await seed_env(db_session, "extractevid")

    conv = Conversation(name="Sprint Planning", organization_id=org.id, workspace_id=ws.id, type="group")
    db_session.add(conv)
    await db_session.flush()

    dm1 = DirectMessage(
        conversation_id=conv.id,
        sender_id=user.id,
        organization_id=org.id,
        workspace_id=ws.id,
        content="Task: Implement API gateway authentication by Friday. Decision: Agreed to use JWT Bearer tokens.",
        message_type="TEXT"
    )
    db_session.add(dm1)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="Extract all tasks, responsibilities, deadlines, and decisions from this project discussion.",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    assert "I found these related conversation threads" not in content
    assert "### Tasks" in content
    assert "### Decisions" in content
    assert response["capability"] == "TASK_EXTRACTION"

@pytest.mark.asyncio
async def test_document_qa_prioritizes_actual_document(db_session: AsyncSession):
    """Test 8: Document QA prioritizes the actual document content."""
    
    user, org, ws, role = await seed_env(db_session, "docqa")

    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        filename="Architecture.pdf",
        original_filename="Architecture.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=2048,
        checksum_sha256="abc123sha_docqa",
        storage_provider="local",
        storage_path="/path/arch.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc)
    await db_session.flush()

    chunk = DocumentChunk(
        document_id=doc.id,
        organization_id=org.id,
        workspace_id=ws.id,
        chunk_index=0,
        content="Architecture Document: We selected Kong as our API gateway with OAuth2 rate limiting.",
        token_count=20,
        metadata_json={"page": 1}
    )
    db_session.add(chunk)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)
    response = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="What does Architecture.pdf say about the API gateway?",
        workspace_id=ws.id,
        provider="mock"
    )

    content = response.get("content") or response.get("answer") or ""
    assert response["capability"] in ["DOCUMENT_RAG", "KNOWLEDGE_SYNTHESIS"]
    assert "Kong" in content or "API gateway" in content or "architecture" in content.lower() or "Architecture.pdf" in str(response.get("citations", []))

@pytest.mark.asyncio
async def test_workspace_isolation_intact(db_session: AsyncSession):
    """Test 9: Knowledge in Workspace A is strictly isolated from Workspace B queries."""
    
    role = Role(name="MEMBER", description="Member Role")
    db_session.add(role)
    await db_session.flush()

    user = User(username="isouser2", email="iso2@example.com", hashed_password="pwd")
    db_session.add(user)
    await db_session.flush()

    org = Organization(name="Iso Org 2", slug=f"iso-org-{uuid4().hex[:6]}", owner_id=user.id)
    db_session.add(org)
    await db_session.flush()

    org_member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(org_member)
    await db_session.flush()

    ws_a = Workspace(name="WS A", slug=f"ws-a-{uuid4().hex[:6]}", organization_id=org.id)
    ws_b = Workspace(name="WS B", slug=f"ws-b-{uuid4().hex[:6]}", organization_id=org.id)
    db_session.add_all([ws_a, ws_b])
    await db_session.flush()

    ws_a_member = WorkspaceMember(workspace_id=ws_a.id, user_id=user.id, role="MEMBER")
    ws_b_member = WorkspaceMember(workspace_id=ws_b.id, user_id=user.id, role="MEMBER")
    db_session.add_all([ws_a_member, ws_b_member])
    await db_session.flush()

    # Document in Workspace A
    doc_a = Document(
        organization_id=org.id,
        workspace_id=ws_a.id,
        filename="SecretAlpha.pdf",
        original_filename="SecretAlpha.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=1024,
        checksum_sha256="abc123sha_secret2",
        storage_provider="local",
        storage_path="/path/secret.pdf",
        processing_status="PROCESSED"
    )
    db_session.add(doc_a)
    await db_session.flush()

    chunk_a = DocumentChunk(
        document_id=doc_a.id,
        organization_id=org.id,
        workspace_id=ws_a.id,
        chunk_index=0,
        content="Confidential Secret Alpha Code: 112233445566",
        token_count=10,
        metadata_json={"page": 1}
    )
    db_session.add(chunk_a)
    await db_session.commit()

    # Query from Workspace B
    orchestrator = MindMeshAIOrchestrator(db_session)
    response_b = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="What is the confidential Secret Alpha code in this workspace?",
        workspace_id=ws_b.id,
        provider="mock"
    )

    content_b = response_b.get("content") or response_b.get("answer") or ""
    assert "112233445566" not in content_b
    assert "couldn't find enough information" in content_b.lower() or "not enough information" in content_b.lower()

@pytest.mark.asyncio
async def test_repeated_ai_chat_usage_prevents_recursive_pollution(db_session: AsyncSession):
    """Test 10: Repeated AI Chat usage does not pollute subsequent workspace searches or knowledge synthesis."""
    
    user, org, ws, role = await seed_env(db_session, "repeatloop")

    # Real team discussion
    conv = Conversation(name="Backend Team Discussion", organization_id=org.id, workspace_id=ws.id, type="group")
    db_session.add(conv)
    await db_session.flush()

    dm1 = DirectMessage(
        conversation_id=conv.id,
        sender_id=user.id,
        organization_id=org.id,
        workspace_id=ws.id,
        content="We finalized FastAPI as the backend framework.",
        message_type="TEXT"
    )
    db_session.add(dm1)
    await db_session.commit()

    orchestrator = MindMeshAIOrchestrator(db_session)

    # Perform 3 separate AI chat queries that each get saved as Chat and Message
    for i in range(3):
        await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query=f"Query {i}: What are the main architectural decisions in this project?",
            workspace_id=ws.id,
            provider="mock"
        )

    # Now perform an explicit search
    search_resp = await orchestrator.execute(
        user_id=user.id,
        org_id=org.id,
        query="Find conversations about backend framework",
        workspace_id=ws.id,
        provider="mock"
    )

    search_content = search_resp.get("content") or search_resp.get("answer") or ""
    assert "Backend Team Discussion" in search_content
    # The 3 AI Chat query sessions must NOT appear as matching conversations
    assert "Query 0" not in search_content
    assert "Query 1" not in search_content
    assert "Query 2" not in search_content
