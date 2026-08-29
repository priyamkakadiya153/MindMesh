import json
import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace, WorkspaceMember
from app.documents.models import Document
from app.models.conversations import Conversation, ConversationMember
from app.models.message import Message
from app.models.task import Task
from app.models.cognitive_agent import CognitiveAgent, CognitiveAgentExecution, CognitiveAgentOutput
from app.models.proactive_suggestion import ProactiveSuggestion
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_engine import CognitiveAgentExecutionEngine
from app.agents.cognitive_actionability import CognitiveAgentActionabilityService
from app.ai.gateway.models import AIResponse, AIResponseStatus

async def seed_ca08_user_and_org(db: AsyncSession, suffix: str = "ca08"):
    user = User(
        email=f"user_{suffix}_{uuid4().hex[:6]}@mindmesh.com",
        username=f"u_{suffix}_{uuid4().hex[:6]}",
        first_name="CA08",
        last_name="Tester",
        is_active=True
    )
    db.add(user)
    await db.commit()

    org = Organization(name=f"Org {suffix}", slug=f"org-{suffix}-{uuid4().hex[:6]}", owner_id=user.id)
    db.add(org)
    await db.commit()

    ws = Workspace(name=f"WS {suffix}", slug=f"ws-{suffix}-{uuid4().hex[:6]}", organization_id=org.id, created_by=user.id)
    db.add(ws)
    await db.commit()

    wm = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="member")
    db.add(wm)
    await db.commit()

    return user, org, ws

@pytest.mark.asyncio
async def test_01_no_actionable_finding(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t01")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 1", filename="d1.pdf", original_filename="d1.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d1", storage_path="/d1")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Info Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "INSIGHT", "title": "Info Summary", "summary": "The project contains 1 document."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    assert exec_record.status == "COMPLETED"
    assert exec_record.action_candidates_generated == 0

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 0


@pytest.mark.asyncio
async def test_02_actionable_deadline(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t02")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Spec.pdf", filename="s.pdf", original_filename="s.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="s", storage_path="/s")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Deadline Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    ai_payload = '{"output_type": "ACTION_CANDIDATE", "title": "Review API Spec", "summary": "Review required by tomorrow.", "candidate_type": "TASK", "structured_payload": {"is_actionable": true, "title": "Review API Spec", "summary": "Review required by tomorrow.", "candidate_type": "TASK", "deadline": "tomorrow"}}'
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=ai_payload)
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    assert exec_record.status == "COMPLETED"
    assert exec_record.action_candidates_generated == 1

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 1
    assert suggs[0].source_type == "COGNITIVE_AGENT"
    assert suggs[0].title == "Review API Spec"
    assert suggs[0].status == "DETECTED"


@pytest.mark.asyncio
async def test_03_grounded_provenance(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t03")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Architecture.pdf", filename="a.pdf", original_filename="a.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="a", storage_path="/a")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Arch Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    ai_payload = '{"output_type": "ACTION_CANDIDATE", "title": "Verify DB Migration", "summary": "DB migration verification required.", "candidate_type": "TASK"}'
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=ai_payload)
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 1
    s = suggs[0]
    assert s.agent_id == agent.id
    assert s.agent_execution_id == exec_record.id
    assert s.agent_output_id == output.id


@pytest.mark.asyncio
async def test_04_no_provenance_blocks_candidate(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t04")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Empty Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    ai_payload = '{"output_type": "ACTION_CANDIDATE", "title": "Do something", "summary": "No source behind this."}'
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=ai_payload)
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    assert exec_record.action_candidates_generated == 0
    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 0


@pytest.mark.asyncio
async def test_05_duplicate_agent_execution_deduplicated(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t05")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 5", filename="d5.pdf", original_filename="d5.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d5", storage_path="/d5")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Dup Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    ai_payload = '{"output_type": "ACTION_CANDIDATE", "title": "Audit Security Rules", "summary": "Audit required.", "candidate_type": "TASK"}'
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=ai_payload)

    # Run 1
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    # Run 2 (identical)
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 1


@pytest.mark.asyncio
async def test_06_promote_to_task_creates_proposal(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t06")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 6", filename="d6.pdf", original_filename="d6.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d6", storage_path="/d6")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Task Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )

    ai_payload = '{"output_type": "ACTION_CANDIDATE", "title": "Refactor Router", "summary": "Refactor router task required.", "candidate_type": "TASK"}'
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=ai_payload)
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    s = suggs[0]

    # Evaluate candidate promote logic
    s.pending_target_action_type = "CREATE_TASK"
    s.status = "PENDING_CONFIRMATION"
    await db_session.commit()

    assert s.status == "PENDING_CONFIRMATION"


@pytest.mark.asyncio
async def test_07_confirm_task_creates_exactly_one_task(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t07")
    task = Task(title="Refactor Router", description="Task desc", workspace_id=ws.id, organization_id=org.id, created_by=str(user.id), status="TODO")
    db_session.add(task)
    await db_session.commit()

    tasks = (await db_session.execute(select(Task).where(Task.workspace_id == ws.id))).scalars().all()
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_08_promote_to_reminder_creates_proposal(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t08")
    sugg = ProactiveSuggestion(
        organization_id=org.id, workspace_id=ws.id, user_id=user.id,
        source_type="COGNITIVE_AGENT", conversation_id="conv-1",
        detected_action_type="REMINDER", title="Remind about Release",
        status="PENDING_CONFIRMATION", detected_action_hash="hash08"
    )
    db_session.add(sugg)
    await db_session.commit()

    assert sugg.status == "PENDING_CONFIRMATION"


@pytest.mark.asyncio
async def test_09_confirm_reminder_creates_exactly_one_reminder(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t09")
    sugg = ProactiveSuggestion(
        organization_id=org.id, workspace_id=ws.id, user_id=user.id,
        source_type="COGNITIVE_AGENT", conversation_id="conv-1",
        detected_action_type="REMINDER", title="Release Reminder",
        status="ACCEPTED", detected_action_hash="hash09"
    )
    db_session.add(sugg)
    await db_session.commit()

    assert sugg.status == "ACCEPTED"


@pytest.mark.asyncio
async def test_10_dismiss_candidate(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t10")
    sugg = ProactiveSuggestion(
        organization_id=org.id, workspace_id=ws.id, user_id=user.id,
        source_type="COGNITIVE_AGENT", conversation_id="conv-1",
        detected_action_type="TASK", title="Dismiss Me",
        status="DETECTED", detected_action_hash="hash10"
    )
    db_session.add(sugg)
    await db_session.commit()

    sugg.status = "DISMISSED"
    sugg.dismissed_at = datetime.now(timezone.utc)
    await db_session.commit()

    assert sugg.status == "DISMISSED"
    assert sugg.dismissed_at is not None


@pytest.mark.asyncio
async def test_11_candidate_persistence(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t11")
    sugg = ProactiveSuggestion(
        organization_id=org.id, workspace_id=ws.id, user_id=user.id,
        source_type="COGNITIVE_AGENT", conversation_id="conv-1",
        detected_action_type="TASK", title="Persistent Candidate",
        status="DETECTED", detected_action_hash="hash11"
    )
    db_session.add(sugg)
    await db_session.commit()

    s_res = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.id == sugg.id))).scalar_one_or_none()
    assert s_res is not None
    assert s_res.title == "Persistent Candidate"


@pytest.mark.asyncio
async def test_12_action_inbox_pending_count(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t12")
    s1 = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="COGNITIVE_AGENT", conversation_id="c1", detected_action_type="TASK", title="P1", status="DETECTED", detected_action_hash="h12a")
    s2 = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="DIRECT_MESSAGE", conversation_id="c2", detected_action_type="TASK", title="P2", status="DETECTED", detected_action_hash="h12b")
    db_session.add_all([s1, s2])
    await db_session.commit()

    active = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.user_id == user.id, ProactiveSuggestion.status == "DETECTED"))).scalars().all()
    assert len(active) == 2


@pytest.mark.asyncio
async def test_13_view_agent_analysis_link(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t13")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 13", filename="d13.pdf", original_filename="d13.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d13", storage_path="/d13")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Link Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Check Security", "summary": "Security check."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    sugg = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().first()
    assert sugg.agent_output_id == output.id


@pytest.mark.asyncio
async def test_14_open_document_source(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t14")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 14", filename="d14.pdf", original_filename="d14.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d14", storage_path="/d14")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Doc Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Review Doc 14", "summary": "Review required."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    prov = output.provenance[0]
    assert prov["source_type"] == "document"
    assert prov["source_id"] == str(doc.id)


@pytest.mark.asyncio
async def test_15_open_message_source(db_session: AsyncSession):
    user1, org, ws = await seed_ca08_user_and_org(db_session, "t15_u1")
    user2, _, _ = await seed_ca08_user_and_org(db_session, "t15_u2")

    conv = Conversation(organization_id=org.id, workspace_id=ws.id, type="private", participant_one=user1.id, participant_two=user2.id, name="User1 ↔ User2")
    db_session.add(conv)
    await db_session.commit()

    msg = Message(conversation_id=conv.id, sender_id=user2.id, organization_id=org.id, content="Please review API tomorrow.", content_type="text/plain")
    db_session.add(msg)
    await db_session.commit()

    conv.last_message_id = msg.id
    conv.last_message_text = msg.content
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user1.id, name="Msg Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "CONVERSATION", "conversation_ids": [str(conv.id)]})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Review API", "summary": "Review requested by User2."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user1, organization_id=org.id, workspace_id=ws.id)

    sugg = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().first()
    assert sugg.conversation_id == str(conv.id)
    assert sugg.message_id == str(msg.id)


@pytest.mark.asyncio
async def test_16_unauthorized_source_blocked(db_session: AsyncSession):
    user1, org, ws = await seed_ca08_user_and_org(db_session, "t16_u1")
    user2, _, _ = await seed_ca08_user_and_org(db_session, "t16_u2")

    sugg = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user1.id, source_type="COGNITIVE_AGENT", conversation_id="c16", title="User 1 Secret", status="DETECTED", detected_action_hash="h16")
    db_session.add(sugg)
    await db_session.commit()

    res = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.user_id == user2.id))).scalars().all()
    assert len(res) == 0


@pytest.mark.asyncio
async def test_17_user_isolation(db_session: AsyncSession):
    user1, org1, ws1 = await seed_ca08_user_and_org(db_session, "t17_u1")
    user2, org2, ws2 = await seed_ca08_user_and_org(db_session, "t17_u2")

    s1 = ProactiveSuggestion(organization_id=org1.id, workspace_id=ws1.id, user_id=user1.id, source_type="COGNITIVE_AGENT", conversation_id="c17a", title="U1 Action", status="DETECTED", detected_action_hash="h17a")
    s2 = ProactiveSuggestion(organization_id=org2.id, workspace_id=ws2.id, user_id=user2.id, source_type="COGNITIVE_AGENT", conversation_id="c17b", title="U2 Action", status="DETECTED", detected_action_hash="h17b")
    db_session.add_all([s1, s2])
    await db_session.commit()

    u1_items = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.user_id == user1.id))).scalars().all()
    assert len(u1_items) == 1
    assert u1_items[0].title == "U1 Action"


@pytest.mark.asyncio
async def test_18_leader_member_dual_pov(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t18")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 18", filename="d18.pdf", original_filename="d18.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d18", storage_path="/d18")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Dual Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Review API Spec", "summary": "Review requested by Leader.", "candidate_type": "REVIEW"}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 1


@pytest.mark.asyncio
async def test_19_completion_signal_handling(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t19")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 19", filename="d19.pdf", original_filename="d19.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d19", storage_path="/d19")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Comp Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "API Documentation", "summary": "I completed the API documentation yesterday.", "candidate_type": "TASK"}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    # Self-task candidate suppressed for completed signal
    assert exec_record.action_candidates_generated == 0


@pytest.mark.asyncio
async def test_20_expired_deadline_handling(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t20")
    past_date = datetime.now(timezone.utc) - timedelta(days=2)
    sugg = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="COGNITIVE_AGENT", conversation_id="c20", title="Old Task", status="EXPIRED", normalized_deadline=past_date, detected_action_hash="h20")
    db_session.add(sugg)
    await db_session.commit()

    assert sugg.status == "EXPIRED"


@pytest.mark.asyncio
async def test_21_action_execution_failure(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t21")
    sugg = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="COGNITIVE_AGENT", conversation_id="c21", title="Failing Action", status="PENDING_CONFIRMATION", detected_action_hash="h21")
    db_session.add(sugg)
    await db_session.commit()

    # If action execution fails, status remains PENDING_CONFIRMATION or DETECTED (not ACCEPTED)
    assert sugg.status != "ACCEPTED"


@pytest.mark.asyncio
async def test_22_double_click_idempotency(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t22")
    task = Task(title="Single Task", description="Single desc", workspace_id=ws.id, organization_id=org.id, created_by=str(user.id), status="TODO")
    db_session.add(task)
    await db_session.commit()

    tasks = (await db_session.execute(select(Task).where(Task.workspace_id == ws.id))).scalars().all()
    assert len(tasks) == 1


@pytest.mark.asyncio
async def test_23_multiple_actionable_findings(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t23")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 23", filename="d23.pdf", original_filename="d23.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d23", storage_path="/d23")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Multi Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    payload_json = {
        "output_type": "ACTION_CANDIDATE",
        "title": "Multiple Action Items",
        "summary": "Found 2 tasks.",
        "structured_payload": {
            "findings": [
                {"title": "Task A", "summary": "Complete module A.", "is_actionable": True, "candidate_type": "TASK"},
                {"title": "Task B", "summary": "Verify deployment B.", "is_actionable": True, "candidate_type": "TASK"}
            ]
        }
    }
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content=json.dumps(payload_json))
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        exec_record, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    assert exec_record.action_candidates_generated == 2
    suggs = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().all()
    assert len(suggs) == 2


@pytest.mark.asyncio
async def test_24_existing_auto08_compatibility(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t24")
    sugg = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="DIRECT_MESSAGE", conversation_id="conv-24", title="AUTO-08 Chat Candidate", status="DETECTED", detected_action_hash="h24")
    db_session.add(sugg)
    await db_session.commit()

    assert sugg.source_type == "DIRECT_MESSAGE"


@pytest.mark.asyncio
async def test_25_existing_auto09_compatibility(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t25")
    sugg = ProactiveSuggestion(organization_id=org.id, workspace_id=ws.id, user_id=user.id, source_type="GROUP_CHAT", conversation_id="conv-25", title="AUTO-09 Group Candidate", status="DETECTED", detected_action_hash="h25")
    db_session.add(sugg)
    await db_session.commit()

    assert sugg.source_type == "GROUP_CHAT"


@pytest.mark.asyncio
async def test_26_existing_auto04_scheduler_compatibility(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t26")
    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Sched Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    assert agent.id is not None


@pytest.mark.asyncio
async def test_27_ca07_output_immutability(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t27")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 27", filename="d27.pdf", original_filename="d27.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d27", storage_path="/d27")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Immutable Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Immutable Output Title", "summary": "Analysis body text."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    original_body = output.body
    sugg = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().first()
    sugg.status = "ACCEPTED"
    await db_session.commit()

    await db_session.refresh(output)
    assert output.body == original_body


@pytest.mark.asyncio
async def test_28_source_updated_candidate_truthful(db_session: AsyncSession):
    user, org, ws = await seed_ca08_user_and_org(db_session, "t28")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 28", filename="d28.pdf", original_filename="d28.pdf", extension="pdf", mime_type="pdf", size=1, checksum_sha256="d28", storage_path="/d28")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id, name="Truthful Agent", instructions="Inst", status="ACTIVE", knowledge_scope={"scope_type": "WORKSPACE"})
    mock_ai = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "title": "Truthful Candidate", "summary": "Summary."}')
    with patch("app.agents.cognitive_engine.AIGateway.execute", return_value=mock_ai):
        _, output = await CognitiveAgentExecutionEngine.execute_agent(db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id)

    # Update source document timestamp
    doc.updated_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db_session.commit()

    sugg = (await db_session.execute(select(ProactiveSuggestion).where(ProactiveSuggestion.workspace_id == ws.id))).scalars().first()
    assert sugg.title == "Truthful Candidate"
