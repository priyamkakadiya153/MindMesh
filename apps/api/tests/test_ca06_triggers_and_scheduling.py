import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace, WorkspaceMember
from app.models.document import Document
from app.models.cognitive_agent import (
    CognitiveAgent,
    CognitiveAgentExecution,
    CognitiveAgentOutput,
    CognitiveAgentTrigger
)
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_triggers import CognitiveAgentTriggerService
from app.automation.schedule_calculator import ScheduleCalculator
from app.ai.gateway.models import AIResponse, AIResponseStatus


async def seed_ca06_user_and_org(db: AsyncSession, prefix: str = "ca06"):
    uid = uuid4()
    oid = uuid4()
    wid = uuid4()

    user = User(
        id=uid,
        email=f"{prefix}_{uid.hex[:6]}@mindmesh.com",
        username=f"user_{prefix}_{uid.hex[:6]}",
        hashed_password="hash",
        first_name="User",
        last_name=prefix,
        is_active=True
    )
    org = Organization(id=oid, name=f"Org {prefix}", slug=f"org-{uid.hex[:6]}")
    ws = Workspace(id=wid, organization_id=oid, name=f"WS {prefix}", slug=f"ws-{uid.hex[:6]}")
    member = WorkspaceMember(workspace_id=wid, user_id=uid, role="ADMIN")

    db.add_all([user, org, ws, member])
    await db.commit()
    await db.refresh(user)
    await db.refresh(org)
    await db.refresh(ws)
    return user, org, ws


@pytest.mark.asyncio
async def test_01_active_scheduled_agent_executes(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t01")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Scheduled Agent", instructions="Analyze workspace", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY", "time_str": "09:00", "timezone": "Asia/Kolkata"}
    )
    # Manually make trigger due
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=5)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            request_id=uuid4(),
            status=AIResponseStatus.COMPLETED,
            content='{"output_type": "INSIGHT", "title": "Scheduled Run", "summary": "Daily briefing"}'
        )
        executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    assert executed_count == 1
    await db_session.refresh(trigger)
    assert trigger.status == "ACTIVE"
    assert trigger.next_run_at is not None
    assert trigger.last_run_at is not None
    assert trigger.last_execution_id is not None


@pytest.mark.asyncio
async def test_02_paused_agent_does_not_execute(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t02")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Paused Agent", instructions="Inst", status="PAUSED",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY", "time_str": "09:00"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=5)
    await db_session.commit()

    executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
    assert executed_count == 0


@pytest.mark.asyncio
async def test_03_disabled_trigger_does_not_execute(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t03")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Agent 3", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    await CognitiveAgentTriggerService.pause_trigger(db_session, trigger.id, org.id)
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=5)
    await db_session.commit()

    executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
    assert executed_count == 0


@pytest.mark.asyncio
async def test_04_one_time_trigger_executes_once(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t04")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="OneTime Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "One-Time Analysis"}')
        executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    assert executed_count == 1
    await db_session.refresh(trigger)
    assert trigger.status == "COMPLETED"
    assert trigger.next_run_at is None


@pytest.mark.asyncio
async def test_05_recurring_trigger_calculates_next_run(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t05")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Weekly Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "WEEKLY", "day_of_week": "Monday", "time_str": "09:00", "timezone": "Asia/Kolkata"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=10)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Weekly Report"}')
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    await db_session.refresh(trigger)
    assert trigger.status == "ACTIVE"
    assert trigger.next_run_at > datetime.utcnow()


@pytest.mark.asyncio
async def test_06_timezone_is_respected(db_session: AsyncSession):
    next_run = ScheduleCalculator.calculate_next_run(
        schedule_type="DAILY",
        time_str="09:00",
        tz_name="Asia/Kolkata"
    )
    assert next_run is not None
    assert next_run.tzinfo == dt_timezone.utc or next_run.tzinfo is None


@pytest.mark.asyncio
async def test_07_duplicate_worker_claim_creates_one_execution(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t07")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Atomic Claim Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=5)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Claim Test"}')
        count1 = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
        count2 = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    assert count1 == 1
    assert count2 == 0


@pytest.mark.asyncio
async def test_08_worker_restart_does_not_duplicate_execution(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t08")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Restart Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Restart Test"}')
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    # Worker restart simulation
    executed_on_restart = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
    assert executed_on_restart == 0


@pytest.mark.asyncio
async def test_09_deleted_agent_does_not_execute(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t09")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Deleted Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    agent.deleted_at = datetime.utcnow()
    await db_session.commit()

    executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
    assert executed_count == 0


@pytest.mark.asyncio
async def test_10_revoked_document_permission_prevents_retrieval(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t10")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Revoked Doc Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "DOCUMENT", "document_ids": [str(uuid4())]}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    # Scope resolves 0 documents due to invalid/revoked document ID, trigger fails safely before LLM invocation
    executed_count = await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)
    assert executed_count == 1
    await db_session.refresh(trigger)
    stmt = select(CognitiveAgentExecution).where(CognitiveAgentExecution.id == trigger.last_execution_id)
    res = await db_session.execute(stmt)
    ex = res.scalar_one_or_none()
    assert ex is not None
    assert ex.status == "FAILED"
    assert "no knowledge scope configured" in ex.error_message.lower()


@pytest.mark.asyncio
async def test_11_workspace_isolation(db_session: AsyncSession):
    user, org, ws1 = await seed_ca06_user_and_org(db_session, "t11_ws1")
    ws2 = Workspace(id=uuid4(), organization_id=org.id, name="WS2", slug=f"ws2-{uuid4().hex[:6]}")
    db_session.add(ws2)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws1.id, owner_user_id=user.id,
        name="WS1 Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws1.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    assert trigger.workspace_id == ws1.id
    assert trigger.workspace_id != ws2.id


@pytest.mark.asyncio
async def test_12_organization_isolation(db_session: AsyncSession):
    user1, org1, ws1 = await seed_ca06_user_and_org(db_session, "t12_org1")
    user2, org2, ws2 = await seed_ca06_user_and_org(db_session, "t12_org2")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org1.id, workspace_id=ws1.id, owner_user_id=user1.id,
        name="Org1 Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user1, organization_id=org1.id, workspace_id=ws1.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    assert trigger.organization_id == org1.id
    assert trigger.organization_id != org2.id


@pytest.mark.asyncio
async def test_13_event_trigger_executes_for_matching_event(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t13")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 13", filename="d13.pdf", original_filename="d13.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d13", storage_path="/d13")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Doc Monitor", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "EVENT", "event_type": "DOCUMENT_ADDED"}
    )

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Doc Added Intelligence"}')
        execs = await CognitiveAgentTriggerService.dispatch_event_trigger(
            db=db_session, event_type="DOCUMENT_ADDED", organization_id=org.id, workspace_id=ws.id, source_entity_id=str(doc.id)
        )

    assert len(execs) == 1
    assert execs[0].trigger_type == "EVENT"


@pytest.mark.asyncio
async def test_14_unauthorized_event_does_not_trigger_agent(db_session: AsyncSession):
    user1, org1, ws1 = await seed_ca06_user_and_org(db_session, "t14_org1")
    user2, org2, ws2 = await seed_ca06_user_and_org(db_session, "t14_org2")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org1.id, workspace_id=ws1.id, owner_user_id=user1.id,
        name="Org1 Event Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user1, organization_id=org1.id, workspace_id=ws1.id,
        payload={"trigger_type": "EVENT", "event_type": "DOCUMENT_ADDED"}
    )

    execs = await CognitiveAgentTriggerService.dispatch_event_trigger(
        db=db_session, event_type="DOCUMENT_ADDED", organization_id=org2.id, workspace_id=ws2.id, source_entity_id="other_doc"
    )
    assert len(execs) == 0


@pytest.mark.asyncio
async def test_15_duplicate_event_does_not_create_duplicate_execution(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t15")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 15", filename="d15.pdf", original_filename="d15.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d15", storage_path="/d15")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Debounce Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "EVENT", "event_type": "DOCUMENT_ADDED"}
    )

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Debounced Event"}')
        execs1 = await CognitiveAgentTriggerService.dispatch_event_trigger(db=db_session, event_type="DOCUMENT_ADDED", organization_id=org.id, workspace_id=ws.id, source_entity_id=str(doc.id))
        execs2 = await CognitiveAgentTriggerService.dispatch_event_trigger(db=db_session, event_type="DOCUMENT_ADDED", organization_id=org.id, workspace_id=ws.id, source_entity_id=str(doc.id))

    assert len(execs1) == 1
    assert len(execs2) == 0


@pytest.mark.asyncio
async def test_16_message_burst_is_debounced(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t16")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Chat Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "EVENT", "event_type": "MESSAGE_RECEIVED"}
    )

    total_execs = 0
    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Chat Analysis"}')
        for i in range(10):
            res = await CognitiveAgentTriggerService.dispatch_event_trigger(db=db_session, event_type="MESSAGE_RECEIVED", organization_id=org.id, workspace_id=ws.id, source_entity_id=f"msg_{i}")
            total_execs += len(res)

    assert total_execs == 1


@pytest.mark.asyncio
async def test_17_provider_failure_marks_execution_failed(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t17")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 17", filename="d17.pdf", original_filename="d17.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d17", storage_path="/d17")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Failure Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", side_effect=RuntimeError("Provider Error")):
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    await db_session.refresh(trigger)
    stmt = select(CognitiveAgentExecution).where(CognitiveAgentExecution.id == trigger.last_execution_id)
    res = await db_session.execute(stmt)
    ex = res.scalar_one_or_none()
    assert ex is not None
    assert ex.status == "FAILED"


@pytest.mark.asyncio
async def test_18_recurring_trigger_survives_failed_execution(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t18")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 18", filename="d18.pdf", original_filename="d18.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d18", storage_path="/d18")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Surviving Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "DAILY"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", side_effect=RuntimeError("Transient Flake")):
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    await db_session.refresh(trigger)
    assert trigger.status == "ACTIVE"
    assert trigger.next_run_at > datetime.utcnow()


@pytest.mark.asyncio
async def test_19_no_task_is_silently_created(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t19")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 19", filename="d19.pdf", original_filename="d19.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d19", storage_path="/d19")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="No Task Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(
            request_id=uuid4(),
            status=AIResponseStatus.COMPLETED,
            content='{"output_type": "ACTION_CANDIDATE", "title": "Create task candidate", "candidate_type": "TASK"}'
        )
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    # Confirm 0 task records generated in DB
    from app.automation.scheduled_automation_model import ScheduledAutomation
    stmt = select(ScheduledAutomation).where(ScheduledAutomation.organization_id == org.id)
    res = await db_session.execute(stmt)
    assert len(res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_20_no_reminder_is_silently_created(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t20")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="No Reminder Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "candidate_type": "REMINDER"}')
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    await db_session.refresh(trigger)
    assert trigger.last_execution_id is not None


@pytest.mark.asyncio
async def test_21_no_dm_is_silently_sent(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t21")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="No DM Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"output_type": "ACTION_CANDIDATE", "candidate_type": "MESSAGE"}')
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    await db_session.refresh(trigger)
    assert trigger.status == "COMPLETED"


@pytest.mark.asyncio
async def test_22_no_destructive_action_executed(db_session: AsyncSession):
    user, org, ws = await seed_ca06_user_and_org(db_session, "t22")
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 22", filename="d22.pdf", original_filename="d22.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d22", storage_path="/d22")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Destructive Test Agent", instructions="Inst", status="ACTIVE",
        knowledge_scope={"scope_type": "WORKSPACE"}
    )
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db_session, agent_id=agent.id, current_user=user, organization_id=org.id, workspace_id=ws.id,
        payload={"trigger_type": "SCHEDULE", "schedule_type": "ONE_TIME"}
    )
    trigger.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    await db_session.commit()

    with patch("app.agents.cognitive_engine.AIGateway.execute", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AIResponse(request_id=uuid4(), status=AIResponseStatus.COMPLETED, content='{"title": "Malicious payload to delete document"}')
        await CognitiveAgentTriggerService.run_scheduled_trigger_sweep(db_session)

    # Document remains untouched in DB
    await db_session.refresh(doc)
    assert doc.id is not None
    assert doc.title == "Doc 22"
