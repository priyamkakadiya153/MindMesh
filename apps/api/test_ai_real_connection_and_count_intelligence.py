import pytest
import asyncio
from uuid import uuid4
from sqlalchemy import delete

from app.core.database import AsyncSessionLocal, engine
from app.ai.llm.gemini import GeminiProvider
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.documents.models import Document
from app.models.chat import Chat
from app.models.message import Message
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.user import User

@pytest.mark.asyncio
async def test_gemini_provider_real_configuration_and_no_fake_mock_strings():
    """Verify GeminiProvider defaults to gemini-1.5-flash and contains no fake mock response strings."""
    provider = GeminiProvider(model_name="gemini-1.5-flash")
    assert provider.model_name == "gemini-1.5-flash"
    assert not hasattr(provider, "_generate_mock_ai_response")
    assert not hasattr(provider, "_stream_mock_ai_response")

@pytest.mark.asyncio
async def test_document_and_pdf_count_query_intelligence():
    """Verify structured database count intelligence for document, PDF, project, and task count queries."""
    await engine.dispose()
    async with AsyncSessionLocal() as db_session:
        org_id = uuid4()
        ws_id = uuid4()
        user_id = uuid4()

        # Create dummy org, workspace, user in proper dependency order
        org = Organization(id=org_id, name="Count Test Org", slug=f"count-org-{uuid4().hex[:6]}")
        db_session.add(org)
        await db_session.commit()

        ws = Workspace(id=ws_id, organization_id=org_id, name="Count Test WS", slug=f"count-ws-{uuid4().hex[:6]}")
        db_session.add(ws)
        await db_session.commit()

        user = User(
            id=user_id,
            email=f"countuser_{uuid4().hex[:6]}@test.com",
            username=f"countuser_{uuid4().hex[:6]}",
            hashed_password="hash",
            current_organization_id=org_id,
            current_workspace_id=ws_id
        )
        db_session.add(user)
        await db_session.commit()

        orchestrator = MindMeshAIOrchestrator(db_session)

        # 1. Test count when zero documents exist
        res_zero = await orchestrator.execute(
            user_id=user_id,
            org_id=org_id,
            query="how many pdf are in documents",
            workspace_id=ws_id
        )
        assert res_zero["intent"] == "COUNT_QUERY"
        assert "0 PDF document" in res_zero["answer"]
        assert "Here is the synthesized" not in res_zero["answer"]

        # 2. Add 2 PDF documents and 1 DOCX document
        doc1 = Document(
            id=uuid4(),
            organization_id=org_id,
            workspace_id=ws_id,
            title="Report 1",
            filename="report1.pdf",
            original_filename="report1.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="abc1",
            storage_provider="local",
            storage_path="/tmp/1"
        )
        doc2 = Document(
            id=uuid4(),
            organization_id=org_id,
            workspace_id=ws_id,
            title="Report 2",
            filename="report2.pdf",
            original_filename="report2.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=2048,
            checksum_sha256="abc2",
            storage_provider="local",
            storage_path="/tmp/2"
        )
        doc3 = Document(
            id=uuid4(),
            organization_id=org_id,
            workspace_id=ws_id,
            title="Specs",
            filename="specs.docx",
            original_filename="specs.docx",
            mime_type="application/docx",
            extension="docx",
            size=4096,
            checksum_sha256="abc3",
            storage_provider="local",
            storage_path="/tmp/3"
        )
        db_session.add_all([doc1, doc2, doc3])
        await db_session.commit()

        # 3. Test PDF count query
        res_pdf = await orchestrator.execute(
            user_id=user_id,
            org_id=org_id,
            query="how many pdf are in documents",
            workspace_id=ws_id
        )
        assert res_pdf["intent"] == "COUNT_QUERY"
        assert "2 PDF documents" in res_pdf["answer"]
        assert "Here is the synthesized" not in res_pdf["answer"]

        # 4. Test total documents count query
        res_docs = await orchestrator.execute(
            user_id=user_id,
            org_id=org_id,
            query="how many documents do I have?",
            workspace_id=ws_id
        )
        assert res_docs["intent"] == "COUNT_QUERY"
        assert "3 documents" in res_docs["answer"]
        assert "Here is the synthesized" not in res_docs["answer"]

        # Cleanup
        await db_session.execute(delete(Message).where(Message.organization_id == org_id))
        await db_session.execute(delete(Chat).where(Chat.organization_id == org_id))
        await db_session.execute(delete(Document).where(Document.workspace_id == ws_id))
        await db_session.execute(delete(User).where(User.id == user_id))
        await db_session.execute(delete(Workspace).where(Workspace.id == ws_id))
        await db_session.execute(delete(Organization).where(Organization.id == org_id))
        await db_session.commit()
    await engine.dispose()

@pytest.mark.asyncio
async def test_stream_execute_count_query_events():
    """Verify stream_execute yields token events and final payload without mock strings."""
    await engine.dispose()
    async with AsyncSessionLocal() as db_session:
        org_id = uuid4()
        ws_id = uuid4()
        user_id = uuid4()

        # Create dummy org, workspace, user in proper dependency order
        org = Organization(id=org_id, name="Count Stream Org", slug=f"count-str-{uuid4().hex[:6]}")
        db_session.add(org)
        await db_session.commit()

        ws = Workspace(id=ws_id, organization_id=org_id, name="Count Stream WS", slug=f"count-str-ws-{uuid4().hex[:6]}")
        db_session.add(ws)
        await db_session.commit()

        user = User(
            id=user_id,
            email=f"countstream_{uuid4().hex[:6]}@test.com",
            username=f"countstream_{uuid4().hex[:6]}",
            hashed_password="hash",
            current_organization_id=org_id,
            current_workspace_id=ws_id
        )
        db_session.add(user)
        await db_session.commit()

        orchestrator = MindMeshAIOrchestrator(db_session)
        events = []
        async for event in orchestrator.stream_execute(
            user_id=user_id,
            org_id=org_id,
            query="how many pdf are in documents",
            workspace_id=ws_id
        ):
            events.append(event)

        assert len(events) >= 3
        assert events[0]["type"] == "session"
        
        tokens = [e["content"] for e in events if e.get("type") == "token"]
        full_text = "".join(tokens)
        assert "PDF document" in full_text
        assert "Here is the synthesized" not in full_text

        final_evt = events[-1]
        assert final_evt["type"] == "final"
        assert final_evt["intent"] == "COUNT_QUERY"

        # Cleanup
        await db_session.execute(delete(Message).where(Message.organization_id == org_id))
        await db_session.execute(delete(Chat).where(Chat.organization_id == org_id))
        await db_session.execute(delete(User).where(User.id == user_id))
        await db_session.execute(delete(Workspace).where(Workspace.id == ws_id))
        await db_session.execute(delete(Organization).where(Organization.id == org_id))
        await db_session.commit()
    await engine.dispose()
