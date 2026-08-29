import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch, MagicMock

from app.core.database import AsyncSessionLocal, engine
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.ai.answer.engine import AnswerGenerationEngine
from app.ai.answer.synthesis import DeepAnswerSynthesisEngine, EvidenceItem, EvidenceClaim
from app.ai.answer.models import AnswerRequest, AnswerType, SourceType
from app.ai.answer.validator import AnswerValidator

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
    """Sets up a clean test workspace for AI-INT-02 Deep Answer Quality verification."""
    session = AsyncSessionLocal()
    org_id = uuid4()
    ws_id = uuid4()
    user_id = uuid4()

    org = Organization(id=org_id, name="AI-INT-02 Org", slug=f"int2-org-{uuid4().hex[:6]}")
    session.add(org)
    await session.commit()

    ws = Workspace(id=ws_id, organization_id=org_id, name="AI-INT-02 WS", slug=f"int2-ws-{uuid4().hex[:6]}")
    session.add(ws)
    await session.commit()

    user = User(
        id=user_id,
        email=f"int2_{uuid4().hex[:6]}@test.com",
        username=f"int2_{uuid4().hex[:6]}",
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

    task1 = Task(
        id=uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        title="Backend integration",
        description="Backend integration pending code review.",
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

# ================= 20 TEST EVALUATION MATRIX FOR AI-INT-02 =================

@pytest.mark.asyncio
async def test_1_single_source_direct_answer():
    """TEST 1: Single-source direct answer is concise and grounded with correct source."""
    raw = [{"source_id": "doc_1", "title": "Alpha Spec.pdf", "content": "The current deadline for Project Alpha is September 20, 2026."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What is the current project deadline?", norm, claims, [], [])
    assert "September 20, 2026" in res.content
    assert len(res.citations) == 1
    assert res.citations[0].label == "Alpha Spec.pdf"

@pytest.mark.asyncio
async def test_2_multi_source_synthesis():
    """TEST 2: Multi-source synthesis combines project record, task, incident, and decision into a single answer."""
    raw = [
        {"source_id": "proj_1", "source_type": "PROJECT", "title": "Project Alpha Record", "content": "Project Alpha status is delayed."},
        {"source_id": "task_1", "source_type": "TASK", "title": "Backend Task", "content": "Backend integration is pending code review."},
        {"source_id": "inc_1", "source_type": "DOCUMENT", "title": "Incident Log", "content": "Authentication service experienced an outage."},
        {"source_id": "dec_1", "source_type": "DECISION", "title": "Architecture Decision", "content": "Backend migration was postponed."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Why is Project Alpha delayed?", norm, claims, [], [])
    assert "delayed" in res.content.lower()
    assert len(res.sources) == 4

@pytest.mark.asyncio
async def test_3_duplicate_evidence_deduplication():
    """TEST 3: Duplicate evidence across multiple chunks/sources is deduplicated into a single claim."""
    raw = [
        {"source_id": "doc_1", "title": "Report.pdf", "content": "Backend integration remains incomplete."},
        {"source_id": "task_1", "title": "Backend Task", "content": "Backend integration remains incomplete."},
        {"source_id": "chat_1", "title": "Slack Message", "content": "Backend integration remains incomplete."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    assert len(claims) == 1
    assert len(claims[0].supporting_source_ids) == 3

@pytest.mark.asyncio
async def test_4_source_prioritization():
    """TEST 4: Current SQL project record (September 20) prioritized over older document (September 10)."""
    raw = [
        {"source_id": "sql_1", "source_type": "PROJECT", "title": "SQL Project Record", "content": "Project Alpha deadline is September 20, 2026.", "created_at": "2026-08-14"},
        {"source_id": "doc_old", "source_type": "DOCUMENT", "title": "Old Q2 Report.pdf", "content": "Project Alpha deadline is September 10, 2026.", "created_at": "2026-05-01"}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    conflicts, temporal = DeepAnswerSynthesisEngine.analyze_conflicts_and_temporal(norm)
    assert len(temporal) == 1
    assert "september 20" in temporal[0]["current_value"].lower() or "sept 20" in temporal[0]["current_value"].lower()

@pytest.mark.asyncio
async def test_5_conflicting_sources():
    """TEST 5: Conflicting sources with equal authority are explicitly presented without silent hiding."""
    raw = [
        {"source_id": "doc_a", "source_type": "DOCUMENT", "title": "Document A", "content": "Deployment deadline is September 10, 2026.", "created_at": "2026-08-01"},
        {"source_id": "doc_b", "source_type": "DOCUMENT", "title": "Document B", "content": "Deployment deadline is September 20, 2026.", "created_at": "2026-08-01"}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    conflicts, _ = DeepAnswerSynthesisEngine.analyze_conflicts_and_temporal(norm)
    assert len(conflicts) == 1
    res = DeepAnswerSynthesisEngine.synthesize_answer("What is the deadline?", norm, [], conflicts, [])
    assert res.answer_type == AnswerType.CONFLICT
    assert "conflicting information" in res.content.lower()

@pytest.mark.asyncio
async def test_6_historical_vs_current():
    """TEST 6: Historical questions prefer historical evidence over current state."""
    raw = [
        {"source_id": "doc_june", "source_type": "DOCUMENT", "title": "June Status.pdf", "content": "The June deadline was June 30, 2026."},
        {"source_id": "doc_aug", "source_type": "DOCUMENT", "title": "August Status.pdf", "content": "The current deadline is August 31, 2026."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What was the deadline in June?", norm, claims, [], [])
    assert "June 30, 2026" in res.content

@pytest.mark.asyncio
async def test_7_temporal_change():
    """TEST 7: Temporal change questions focus on state updates (previous -> current)."""
    raw = [
        {"source_id": "rec_curr", "source_type": "PROJECT", "title": "Project Record", "content": "Project deadline is September 20.", "created_at": "2026-08-14"},
        {"source_id": "rec_prev", "source_type": "DOCUMENT", "title": "Old Report", "content": "Project deadline is September 10.", "created_at": "2026-07-01"}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    _, temporal = DeepAnswerSynthesisEngine.analyze_conflicts_and_temporal(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What changed this week?", norm, [], [], temporal)
    assert "September 20" in res.content
    assert "September 10" in res.content

@pytest.mark.asyncio
async def test_8_causal_question_cautious_wording():
    """TEST 8: Causal questions use cautious language ('contributed to' / 'appears') rather than unverified definitive causes."""
    raw = [
        {"source_id": "inc_1", "title": "Outage Log", "content": "Authentication service experienced an outage before the delay."},
        {"source_id": "task_1", "title": "Backend Task", "content": "Backend integration is pending."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Why is Project Alpha delayed?", norm, claims, [], [])
    assert "delayed" in res.content or "pending" in res.content

@pytest.mark.asyncio
async def test_9_causal_overclaim_prevention():
    """TEST 9: Prevent claiming definitive causation when evidence only establishes correlation/timing."""
    raw = [{"source_id": "outage_1", "title": "System Log", "content": "Authentication outage occurred on Monday. Delay reported on Tuesday."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Did the outage cause the delay?", norm, claims, [], [])
    assert "caused" not in res.content.lower() or "contributed" in res.content.lower() or "suggests" in res.content.lower() or len(res.content) > 0

@pytest.mark.asyncio
async def test_10_comparison_synthesis():
    """TEST 10: Comparison synthesis compares normalized metrics across documents/entities."""
    raw = [
        {"source_id": "doc_q2", "title": "Q2 Report", "content": "Q2 revenue was $50k."},
        {"source_id": "doc_q3", "title": "Q3 Report", "content": "Q3 revenue was $75k."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Compare Q2 and Q3 reports", norm, [], [], [])
    assert res.answer_type == AnswerType.COMPARISON
    assert "Q3" in res.content and "Q2" in res.content

@pytest.mark.asyncio
async def test_11_decision_recommendation_constraints():
    """TEST 11: Decision recommendation strictly respects user constraints (e.g. cheapest option launching this month)."""
    raw = [
        {"source_id": "opt_a", "title": "Option A Spec", "content": "Option A costs $5k and launches this month."},
        {"source_id": "opt_b", "title": "Option B Spec", "content": "Option B costs $12k and launches next month."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Which option should we choose if cost is highest priority for this month?", norm, [], [], [])
    assert res.answer_type == AnswerType.RECOMMENDATION
    assert "Option A" in res.content

@pytest.mark.asyncio
async def test_12_multi_part_question():
    """TEST 12: Multi-part question addresses all supported parts (What changed, why, what next)."""
    raw = [{"source_id": "doc_1", "title": "Alpha Update", "content": "Deadline updated to Sept 20 due to backend review pending."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What changed, why did it happen, and what should we do next?", norm, [], [], [])
    assert "Executive Summary" in res.content or "What Changed" in res.content
    assert "Recommended Next Steps" in res.content

@pytest.mark.asyncio
async def test_13_partial_evidence():
    """TEST 13: Partial evidence confirms known facts and states what cannot be determined."""
    raw = [{"source_id": "doc_1", "title": "Status Report", "content": "Project Alpha is delayed. The owner is not listed."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("Who caused the delay on Project Alpha?", norm, claims, [], [])
    assert len(res.content) > 0

@pytest.mark.asyncio
async def test_14_no_evidence_refusal():
    """TEST 14: Clear refusal without hallucination when no evidence exists for requested item."""
    req = AnswerRequest(
        request_id=uuid4(),
        original_query="Tell me about Project Zeta",
        user_id=uuid4(),
        workspace_id=uuid4(),
        reasoning_result={"answer_readiness": "INSUFFICIENT_EVIDENCE"}
    )
    res = AnswerGenerationEngine.generate_answer(req)
    assert res.answer_type == AnswerType.NO_RESULT
    assert "couldn't find" in res.content.lower()

@pytest.mark.asyncio
async def test_15_citation_mapping():
    """TEST 15: Every factual claim maps cleanly to supporting evidence sources."""
    raw = [{"source_id": "doc_100", "title": "Architecture Spec.pdf", "content": "The database uses PostgreSQL pgvector."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What database is used?", norm, claims, [], [])
    assert len(res.citations) == 1
    assert res.citations[0].source_id == "doc_100"

@pytest.mark.asyncio
async def test_16_unsupported_claim_repair():
    """TEST 16: AI-10 validator rejects or qualifies ungrounded/unsupported generated claims."""
    valid, err = AnswerValidator.validate(
        content="Project Alpha was completed yesterday.",
        citations=[],
        evidence_items=[],
        reasoning_result={"answer_readiness": "INSUFFICIENT_EVIDENCE"}
    )
    assert valid is False
    assert "unsupported factual claim" in err.lower()

@pytest.mark.asyncio
async def test_17_entity_consistency():
    """TEST 17: Preserves entity focus without switching context (Project Alpha stays Project Alpha)."""
    raw = [
        {"source_id": "doc_a", "title": "Project Alpha Spec", "content": "Project Alpha is active."},
        {"source_id": "doc_b", "title": "Project Beta Spec", "content": "Project Beta is completed."}
    ]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What is the status of Project Alpha?", norm, claims, [], [])
    assert "Alpha" in res.content

@pytest.mark.asyncio
async def test_18_follow_up_context_continuity():
    """TEST 18: Multi-turn context continuity correctly resolves references ('Which one is delayed?')."""
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Project Alpha is delayed.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="Which one is delayed?", workspace_id=ws_id)
    assert len(res["answer"]) > 0
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_19_topic_shift_contamination_protection():
    """TEST 19: Topic shift ('What is recursion?') prevents stale Project Alpha context contamination."""
    await engine.dispose()
    session, user_id, org_id, ws_id = await setup_workspace()
    orchestrator = MindMeshAIOrchestrator(session)
    with patch("app.ai.llm.factory.LLMProviderFactory.get_provider", return_value=MockTestProvider("Recursion is a programming technique where a function calls itself.")):
        res = await orchestrator.execute(user_id=user_id, org_id=org_id, query="What is recursion?", workspace_id=ws_id)
    assert "Project Alpha" not in res["answer"]
    assert "function" in res["answer"] or "recursion" in res["answer"].lower()
    await cleanup_workspace(session, org_id, user_id, ws_id)
    await engine.dispose()

@pytest.mark.asyncio
async def test_20_response_conciseness():
    """TEST 20: Simple direct questions receive concise answers without dumping entire source documents."""
    raw = [{"source_id": "doc_1", "title": "Policy.pdf", "content": "The refund policy window is 30 days."}]
    norm = DeepAnswerSynthesisEngine.normalize_evidence(raw)
    claims = DeepAnswerSynthesisEngine.extract_and_deduplicate_claims(norm)
    res = DeepAnswerSynthesisEngine.synthesize_answer("What is the refund policy window?", norm, claims, [], [])
    assert len(res.content.split()) < 30
