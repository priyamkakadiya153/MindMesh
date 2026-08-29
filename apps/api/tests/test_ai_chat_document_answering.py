import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.workspace.models import WorkspaceMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.ai.rag.retrieval import RAGRetrieval

@pytest.mark.asyncio
async def test_explicit_document_reference_extraction():
    # 1. Direct document names
    doc, is_explicit = RAGRetrieval.extract_document_reference("What technologies are mentioned in Architecture-Test.pdf?")
    assert doc == "Architecture-Test.pdf"
    assert is_explicit is True

    doc, is_explicit = RAGRetrieval.extract_document_reference("What does Architecture-Test.pdf say about the API Gateway?")
    assert doc == "Architecture-Test.pdf"
    assert is_explicit is True

    doc, is_explicit = RAGRetrieval.extract_document_reference("What does Unknown-Document.pdf say about authentication?")
    assert doc == "Unknown-Document.pdf"
    assert is_explicit is True

    # 2. General queries without document names
    doc, is_explicit = RAGRetrieval.extract_document_reference("What components are used in our architecture?")
    assert doc is None
    assert is_explicit is False

    doc, is_explicit = RAGRetrieval.extract_document_reference("Find conversations about API Gateway.")
    assert doc is None
    assert is_explicit is False

    # 3. Follow-up inheritance from history
    history = [{"role": "user", "content": "What does Architecture-Test.pdf say about the API Gateway?"}]
    doc, is_explicit = RAGRetrieval.extract_document_reference("What about PostgreSQL?", history=history)
    assert doc == "Architecture-Test.pdf"
    assert is_explicit is False

@pytest.mark.asyncio
async def test_document_not_found_handling(db_session):
    # Setup test org and workspace
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:6]}@test.com",
        username=f"user_{uuid4().hex[:6]}",
        hashed_password="hashed_password",
        is_active=True
    )
    org = Organization(id=uuid4(), name="Test Org", slug=f"test-org-{uuid4().hex[:6]}", owner_id=user.id, is_active=True)
    ws = Workspace(id=uuid4(), name="Test WS", slug=f"test-ws-{uuid4().hex[:6]}", organization_id=org.id, owner_id=user.id, is_active=True)
    org_member = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role="owner", is_active=True)
    ws_member = WorkspaceMember(id=uuid4(), workspace_id=ws.id, user_id=user.id, role="admin", is_active=True)

    db_session.add_all([user, org, ws, org_member, ws_member])
    await db_session.commit()

    retrieval = RAGRetrieval(db_session)
    chunks = await retrieval.retrieve_grounded_chunks(
        user_id=user.id,
        org_id=org.id,
        workspace_id=ws.id,
        query="What does Unknown-Document.pdf say about authentication?"
    )

    assert len(chunks) == 1
    assert chunks[0].get("not_found") is True
    assert chunks[0].get("document_name") == "Unknown-Document.pdf"

@pytest.mark.asyncio
async def test_architecture_test_pdf_retrieval(db_session):
    # Setup test org, workspace, and document
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:6]}@test.com",
        username=f"user_{uuid4().hex[:6]}",
        hashed_password="hashed_password",
        is_active=True
    )
    org = Organization(id=uuid4(), name="Test Org", slug=f"test-org-{uuid4().hex[:6]}", owner_id=user.id, is_active=True)
    ws = Workspace(id=uuid4(), name="Test WS", slug=f"test-ws-{uuid4().hex[:6]}", organization_id=org.id, owner_id=user.id, is_active=True)
    org_member = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role="owner", is_active=True)
    ws_member = WorkspaceMember(id=uuid4(), workspace_id=ws.id, user_id=user.id, role="admin", is_active=True)

    doc = Document(
        id=uuid4(),
        organization_id=org.id,
        workspace_id=ws.id,
        uploaded_by=user.id,
        title="Architecture-Test.pdf",
        filename="Architecture-Test.pdf",
        original_filename="Architecture-Test.pdf",
        stored_filename="arch_test.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=1024,
        checksum_sha256="sha256_mock",
        storage_provider="local",
        storage_path="/storage/arch.pdf",
        processing_status="COMPLETED",
        visibility="workspace",
        version=1,
        is_active=True
    )

    chunk1 = DocumentChunk(
        id=uuid4(),
        document_id=doc.id,
        organization_id=org.id,
        workspace_id=ws.id,
        chunk_index=0,
        page_number=1,
        section_title="Architecture Overview",
        content="The architecture uses API Gateway, Authentication Service, Backend API, and PostgreSQL. Flow: Client -> API Gateway -> Auth/Backend -> PostgreSQL.",
        token_count=30,
        character_count=150,
        checksum="chk1",
        metadata_json={},
        is_active=True
    )

    chunk2 = DocumentChunk(
        id=uuid4(),
        document_id=doc.id,
        organization_id=org.id,
        workspace_id=ws.id,
        chunk_index=1,
        page_number=1,
        section_title="API Gateway Details",
        content="API Gateway responsibilities: routing, validation, authorization, rate limits, status codes, timeout behavior. Test cases TC-06 to TC-08.",
        token_count=25,
        character_count=140,
        checksum="chk2",
        metadata_json={},
        is_active=True
    )

    db_session.add_all([user, org, ws, org_member, ws_member, doc, chunk1, chunk2])
    await db_session.commit()

    retrieval = RAGRetrieval(db_session)

    # 1. Query technologies
    chunks_tech = await retrieval.retrieve_grounded_chunks(
        user_id=user.id,
        org_id=org.id,
        workspace_id=ws.id,
        query="What technologies are mentioned in Architecture-Test.pdf?"
    )
    assert len(chunks_tech) > 0
    assert chunks_tech[0].get("not_found") is not True
    assert chunks_tech[0]["title"] == "Architecture-Test.pdf"
    assert "API Gateway" in chunks_tech[0]["content"]

    # 2. Query API Gateway details
    chunks_gateway = await retrieval.retrieve_grounded_chunks(
        user_id=user.id,
        org_id=org.id,
        workspace_id=ws.id,
        query="What does Architecture-Test.pdf say about the API Gateway?"
    )
    assert len(chunks_gateway) > 0
    assert any("validation" in c["content"] or "routing" in c["content"] for c in chunks_gateway)

@pytest.mark.asyncio
async def test_followup_and_workspace_isolation(db_session):
    # Setup WS A and WS B
    user = User(
        id=uuid4(),
        email=f"user_{uuid4().hex[:6]}@test.com",
        username=f"user_{uuid4().hex[:6]}",
        hashed_password="hashed_password",
        is_active=True
    )
    org = Organization(id=uuid4(), name="Test Org", slug=f"test-org-{uuid4().hex[:6]}", owner_id=user.id, is_active=True)
    ws_a = Workspace(id=uuid4(), name="Workspace A", slug=f"ws-a-{uuid4().hex[:6]}", organization_id=org.id, owner_id=user.id, is_active=True)
    ws_b = Workspace(id=uuid4(), name="Workspace B", slug=f"ws-b-{uuid4().hex[:6]}", organization_id=org.id, owner_id=user.id, is_active=True)

    org_member = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role="owner", is_active=True)
    ws_member_a = WorkspaceMember(id=uuid4(), workspace_id=ws_a.id, user_id=user.id, role="admin", is_active=True)
    ws_member_b = WorkspaceMember(id=uuid4(), workspace_id=ws_b.id, user_id=user.id, role="admin", is_active=True)

    # Document only in WS A
    doc_a = Document(
        id=uuid4(),
        organization_id=org.id,
        workspace_id=ws_a.id,
        uploaded_by=user.id,
        title="Architecture-Test.pdf",
        filename="Architecture-Test.pdf",
        original_filename="Architecture-Test.pdf",
        stored_filename="arch_a.pdf",
        mime_type="application/pdf",
        extension="pdf",
        size=1024,
        checksum_sha256="sha256_mock_a",
        storage_provider="local",
        storage_path="/storage/arch_a.pdf",
        processing_status="COMPLETED",
        visibility="workspace",
        version=1,
        is_active=True
    )

    chunk_a = DocumentChunk(
        id=uuid4(),
        document_id=doc_a.id,
        organization_id=org.id,
        workspace_id=ws_a.id,
        chunk_index=0,
        page_number=1,
        section_title="PostgreSQL Details",
        content="PostgreSQL persists user records and application data with ACID transactions.",
        token_count=15,
        character_count=80,
        checksum="chk_a",
        metadata_json={},
        is_active=True
    )

    db_session.add_all([user, org, ws_a, ws_b, org_member, ws_member_a, ws_member_b, doc_a, chunk_a])
    await db_session.commit()

    retrieval = RAGRetrieval(db_session)

    # 1. Follow-up query in WS A inherits doc reference from history
    history = [{"role": "user", "content": "What does Architecture-Test.pdf say about the API Gateway?"}]
    chunks_followup = await retrieval.retrieve_grounded_chunks(
        user_id=user.id,
        org_id=org.id,
        workspace_id=ws_a.id,
        query="What about PostgreSQL?",
        history=history
    )
    assert len(chunks_followup) > 0
    assert chunks_followup[0]["title"] == "Architecture-Test.pdf"
    assert "PostgreSQL" in chunks_followup[0]["content"]

    # 2. Querying Architecture-Test.pdf in WS B must return NOT FOUND (workspace isolation)
    chunks_ws_b = await retrieval.retrieve_grounded_chunks(
        user_id=user.id,
        org_id=org.id,
        workspace_id=ws_b.id,
        query="What technologies are mentioned in Architecture-Test.pdf?"
    )
    assert len(chunks_ws_b) == 1
    assert chunks_ws_b[0].get("not_found") is True

@pytest.mark.asyncio
async def test_response_sanitization_removes_internal_markers():
    from app.ai.rag.formatter import RAGFormatter
    from app.ai.capabilities.domain_executors import DomainExecutors

    raw_leaked_response = """
<source index="2">
<document_id>None</document_id>
<title>Architecture-Test.pdf</title>
[Workspace Evidence #1]
[Workspace Evidence #2]
• Workspace Evidence #1: The API Gateway handles routing and rate limiting.
• Workspace Evidence #2: PostgreSQL is used for relational persistence.
"""

    cleaned, sources = RAGFormatter.format_response(raw_leaked_response, citations=[{"document_id": "doc123", "title": "Architecture-Test.pdf", "page": 1}])
    
    assert "<source" not in cleaned
    assert "</source>" not in cleaned
    assert "<document_id>" not in cleaned
    assert "Workspace Evidence" not in cleaned
    assert "[Workspace Evidence" not in cleaned
    assert "The API Gateway handles routing and rate limiting." in cleaned
    assert "PostgreSQL is used for relational persistence." in cleaned

    # Also test DomainExecutors.sanitize_answer
    sanitized = DomainExecutors.sanitize_answer(raw_leaked_response)
    assert "<source" not in sanitized
    assert "Workspace Evidence" not in sanitized
    assert "The API Gateway handles routing" in sanitized
