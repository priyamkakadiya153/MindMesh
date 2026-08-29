import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch

from app.core.database import AsyncSessionLocal, engine
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.documents.models import Document
from app.projects.models import Project
from app.models.task import Task
from app.ai.llm.base import ModelProvider
from app.ai.gateway.models import AIResponse, AIResponseStatus
from sqlalchemy import delete

class MockTestProvider(ModelProvider):
    def __init__(self, custom_content: str = "Default test AI answer."):
        super().__init__(provider_name="mock", default_model="mock-model")
        self.custom_content = custom_content

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    async def health_check(self):
        return {"status": "HEALTHY"}

    async def generate_response(self, request):
        return AIResponse(
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            content=self.custom_content,
            status=AIResponseStatus.COMPLETED,
            model="mock-model",
            provider="mock"
        )

    async def stream_response(self, request):
        yield None

async def setup_workspace():
    """Sets up a clean test workspace with user, documents, projects, and tasks for AI-INT-01 verification."""
    session = AsyncSessionLocal()
    org_id = uuid4()
    ws_id = uuid4()
    user_id = uuid4()

    org = Organization(id=org_id, name="AI-INT-01 Org", slug=f"int-org-{uuid4().hex[:6]}")
    session.add(org)
    await session.commit()

    ws = Workspace(id=ws_id, organization_id=org_id, name="AI-INT-01 WS", slug=f"int-ws-{uuid4().hex[:6]}")
    session.add(ws)
    await session.commit()

    user = User(
        id=user_id,
        email=f"int_{uuid4().hex[:6]}@test.com",
        username=f"int_{uuid4().hex[:6]}",
        hashed_password="hash",
        current_organization_id=org_id,
        current_workspace_id=ws_id
    )
    session.add(user)
    await session.commit()

    org_member = OrganizationMember(
        id=uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role="owner",
        status="active"
    )
    session.add(org_member)

    ws_member = WorkspaceMember(
        id=uuid4(),
        workspace_id=ws_id,
        user_id=user_id,
        role="owner",
        status="active"
    )
    session.add(ws_member)
    await session.commit()

    # Seed sample document with valid schema fields
    doc1 = Document(
        id=uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        title="Project_Alpha_Q3_Report.pdf",
        filename="Project_Alpha_Q3_Report.pdf",
        original_filename="Project_Alpha_Q3_Report.pdf",
        extension="pdf",
        mime_type="application/pdf",
        size=1024,
        checksum_sha256="abc123sha256dummychecksumhash",
        storage_path="/storage/test_alpha.pdf",
        uploaded_by=user_id
    )
    session.add(doc1)

    # Seed sample active project
    proj1 = Project(
        id=uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        name="Project Alpha",
        slug="project-alpha",
        status="active",
        created_by=str(user_id)
    )
    session.add(proj1)

    # Seed sample task
    task1 = Task(
        id=uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        title="Review Q3 Financial Report",
        description="Review financial report for Q3",
        status="TODO",
        priority="HIGH",
        assignee_id=user_id
    )
    session.add(task1)

    await session.commit()
    return session, user_id, org_id, ws_id

async def cleanup_workspace(session, org_id, user_id, ws_id):
    await session.execute(delete(Task).where(Task.organization_id == org_id))
    await session.execute(delete(Project).where(Project.organization_id == org_id))
    await session.execute(delete(Document).where(Document.organization_id == org_id))
    await session.execute(delete(Message).where(Message.organization_id == org_id))
    await session.execute(delete(Chat).where(Chat.organization_id == org_id))
    await session.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id))
    await session.execute(delete(OrganizationMember).where(OrganizationMember.organization_id == org_id))
    await session.execute(delete(User).where(User.id == user_id))
    await session.execute(delete(Workspace).where(Workspace.id == ws_id))
    await session.execute(delete(Organization).where(Organization.id == org_id))
    await session.commit()
    await session.close()

# ----------------- 15 QUESTION TYPE MATRIX VERIFICATION -----------------

@pytest.mark.asyncio
async def test_1_greeting():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="hi", workspace_id=ws_id)
    assert res["intent"] == "GREETING"
    assert "Hi!" in res["answer"] or "Hello" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_2_general_knowledge():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("2 + 2 is equal to 4.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What is 2 + 2?", workspace_id=ws_id)
    assert "4" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_3_structured_count():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="How many PDFs are in documents?", workspace_id=ws_id)
    assert res["intent"] == "STRUCTURED_QUERY"
    assert "1 PDF document" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_4_structured_list():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What documents are available?", workspace_id=ws_id)
    assert res["intent"] == "STRUCTURED_QUERY"
    assert "Project_Alpha_Q3_Report.pdf" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_5_document_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("The report deadline is September 20, 2026.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What is the deadline mentioned in the project report?", workspace_id=ws_id)
    assert "September 20, 2026" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_6_multi_document_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Q2 reported $50k revenue while Q3 reported $75k revenue.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="Compare Q2 and Q3 financial reports", workspace_id=ws_id)
    assert "$75k" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_7_project_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What projects are active?", workspace_id=ws_id)
    assert res["intent"] == "STRUCTURED_QUERY"
    assert "Project Alpha" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_8_task_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Review Q3 Financial Report is currently TODO.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What tasks are pending?", workspace_id=ws_id)
    assert "Review Q3 Financial Report" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_9_decision_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("The team agreed to adopt PostgreSQL + pgvector.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What decisions were agreed upon in architecture review?", workspace_id=ws_id)
    assert "PostgreSQL" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_10_temporal_question():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Project Alpha was updated and Q3 report uploaded this week.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What changed this week?", workspace_id=ws_id)
    assert "Project Alpha" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_11_follow_up():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Project Alpha is currently delayed due to review pending.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="Which one is delayed?", workspace_id=ws_id)
    assert "Project Alpha" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_12_ambiguity():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Project Alpha is active with status TODO on Q3 review task.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What is the status?", workspace_id=ws_id)
    assert len(res["answer"]) > 0
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_13_no_result():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("I couldn't find information about Project Zeta in your workspace.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="Tell me about Project Zeta", workspace_id=ws_id)
    assert "couldn't find" in res["answer"] or "Zeta" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_14_conflict():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Document A states Sept 10 while Document B states Sept 20.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What is the deployment deadline according to document A vs B?", workspace_id=ws_id)
    assert "Sept 10" in res["answer"] and "Sept 20" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_15_action():
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Task 'Review Q4 roadmap' has been created.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="Create a task to review Q4 roadmap", workspace_id=ws_id)
    assert "Task" in res["answer"]
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()
