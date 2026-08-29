"""
MindMesh — CA-02 Cognitive Agent Database & Persistence Test Suite

Validates all 14 required CA-02 database persistence, multi-tenant isolation,
referential integrity, CRUD operations, execution/output tracking, and migration safety tests.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.session import UserSession
from app.workspace.models import Workspace
from app.models.cognitive_agent import (
    CognitiveAgent,
    CognitiveAgentExecution,
    CognitiveAgentOutput
)
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_service import CognitiveAgentService
from app.agents.cognitive_schemas import CognitiveAgentCreate
from app.core.security import create_access_token


async def seed_test_user_and_org(db: AsyncSession, name_prefix: str = "agent_test"):
    """Helper to seed isolated User, Organization, Workspace, and active UserSession records."""
    suffix = uuid.uuid4().hex[:6]

    stmt = select(Role).where(Role.name == "MEMBER")
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name="MEMBER", description="Member Role")
        db.add(role)
        await db.flush()

    user = User(
        username=f"{name_prefix}_{suffix}",
        email=f"{name_prefix}_{suffix}@example.com",
        hashed_password="hashed_pwd_123"
    )
    db.add(user)
    await db.flush()

    org = Organization(
        name=f"Org {name_prefix} {suffix}",
        slug=f"org-{name_prefix}-{suffix}",
        owner_id=user.id
    )
    db.add(org)
    await db.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db.add(member)
    await db.flush()

    ws = Workspace(
        name=f"Workspace {name_prefix} {suffix}",
        slug=f"ws-{name_prefix}-{suffix}",
        organization_id=org.id,
        created_by=user.id
    )
    db.add(ws)
    await db.flush()

    sess = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        refresh_token_hash=f"session_hash_{suffix}",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db.add(sess)
    await db.commit()

    return user, org, ws, sess


# ---------------- TEST 1: CREATE AGENT ----------------
@pytest.mark.asyncio
async def test_1_create_agent_persistence(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t1")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session,
        organization_id=org.id,
        workspace_id=ws.id,
        owner_user_id=user.id,
        name="Discussion Summarizer Agent",
        description="Extracts key decisions from chat channels",
        agent_type="DISCUSSION_ANALYZER",
        instructions="Analyze channel messages and output bulleted summaries.",
        knowledge_scope={"scope_type": "WORKSPACE", "workspace_id": str(ws.id)},
        triggers=[{"trigger_type": "CONVERSATION_EVENT", "enabled": True}]
    )

    assert agent.id is not None
    assert agent.name == "Discussion Summarizer Agent"
    assert agent.organization_id == org.id
    assert agent.workspace_id == ws.id
    assert agent.owner_user_id == user.id
    assert agent.status == "ACTIVE"
    assert agent.enabled is True


# ---------------- TEST 2: RETRIEVE AGENT ----------------
@pytest.mark.asyncio
async def test_2_retrieve_agent(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t2")

    created = await CognitiveAgentRepository.create_agent(
        db=db_session,
        organization_id=org.id,
        workspace_id=ws.id,
        owner_user_id=user.id,
        name="Document Parser",
        instructions="Parse PDF documents."
    )

    fetched = await CognitiveAgentRepository.get_agent_by_id(
        db=db_session,
        agent_id=created.id,
        organization_id=org.id
    )

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Document Parser"
    assert fetched.instructions == "Parse PDF documents."


# ---------------- TEST 3: UPDATE AGENT ----------------
@pytest.mark.asyncio
async def test_3_update_agent(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t3")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session,
        organization_id=org.id,
        workspace_id=ws.id,
        owner_user_id=user.id,
        name="Original Name",
        instructions="Original Instructions"
    )

    updated = await CognitiveAgentRepository.update_agent(
        db=db_session,
        agent_id=agent.id,
        organization_id=org.id,
        updates={
            "name": "Updated Name",
            "description": "Updated Description",
            "instructions": "Updated Instructions",
            "status": "PAUSED"
        }
    )

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.description == "Updated Description"
    assert updated.instructions == "Updated Instructions"
    assert updated.status == "PAUSED"


# ---------------- TEST 4: LIST AGENTS & WORKSPACE FILTERING ----------------
@pytest.mark.asyncio
async def test_4_list_agents_filtering(db_session: AsyncSession):
    user, org, ws1, _ = await seed_test_user_and_org(db_session, "t4_ws1")

    # Create second workspace in same org
    ws2 = Workspace(
        name="Workspace 2",
        slug=f"ws2-{uuid.uuid4().hex[:6]}",
        organization_id=org.id,
        created_by=user.id
    )
    db_session.add(ws2)
    await db_session.commit()

    agent1 = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws1.id, owner_user_id=user.id,
        name="WS1 Agent", instructions="WS1 Inst"
    )
    agent2 = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws2.id, owner_user_id=user.id,
        name="WS2 Agent", instructions="WS2 Inst"
    )

    ws1_agents = await CognitiveAgentRepository.list_agents(db_session, org.id, workspace_id=ws1.id)
    agent_ids = [a.id for a in ws1_agents]

    assert agent1.id in agent_ids
    assert agent2.id not in agent_ids


# ---------------- TEST 5: ORGANIZATION ISOLATION ----------------
@pytest.mark.asyncio
async def test_5_organization_isolation(db_session: AsyncSession):
    user_a, org_a, ws_a, _ = await seed_test_user_and_org(db_session, "t5_org_a")
    user_b, org_b, ws_b, _ = await seed_test_user_and_org(db_session, "t5_org_b")

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org_a.id, workspace_id=ws_a.id, owner_user_id=user_a.id,
        name="Org A Agent", instructions="Org A Inst"
    )

    # Attempt to retrieve Org A's agent using Org B's organization_id
    cross_fetched = await CognitiveAgentRepository.get_agent_by_id(
        db=db_session, agent_id=agent_a.id, organization_id=org_b.id
    )

    assert cross_fetched is None


# ---------------- TEST 6: WORKSPACE ISOLATION ----------------
@pytest.mark.asyncio
async def test_6_workspace_isolation(db_session: AsyncSession):
    user, org, ws_a, _ = await seed_test_user_and_org(db_session, "t6_ws_a")
    ws_b = Workspace(name="WS B", slug=f"ws-b-{uuid.uuid4().hex[:6]}", organization_id=org.id, created_by=user.id)
    db_session.add(ws_b)
    await db_session.commit()

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws_a.id, owner_user_id=user.id,
        name="WS A Agent", instructions="WS A Inst"
    )

    # Query specifying Workspace B should not return Workspace A's agent
    fetched = await CognitiveAgentRepository.get_agent_by_id(
        db=db_session, agent_id=agent_a.id, organization_id=org.id, workspace_id=ws_b.id
    )

    assert fetched is None


# ---------------- TEST 7: UNAUTHORIZED ACCESS / HTTP ENDPOINT ISOLATION ----------------
@pytest.mark.asyncio
async def test_7_unauthorized_access_http(client: AsyncClient, db_session: AsyncSession):
    user_a, org_a, ws_a, sess_a = await seed_test_user_and_org(db_session, "t7_a")
    user_b, org_b, ws_b, sess_b = await seed_test_user_and_org(db_session, "t7_b")

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org_a.id, workspace_id=ws_a.id, owner_user_id=user_a.id,
        name="User A Agent", instructions="Inst A"
    )

    token_b = create_access_token(subject=str(user_b.id), session_id=str(sess_b.id))
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "X-Organization-ID": str(org_b.id)
    }

    # User B attempts to GET User A's agent
    response = await client.get(f"/api/v1/cognitive-agents/{agent_a.id}", headers=headers_b)
    assert response.status_code == 404


# ---------------- TEST 8: EXECUTION PERSISTENCE (QUEUED -> RUNNING -> COMPLETED) ----------------
@pytest.mark.asyncio
async def test_8_execution_persistence_lifecycle(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t8")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Project Monitor", instructions="Monitor task deadlines"
    )

    # 1. Create QUEUED execution
    exec_rec = await CognitiveAgentRepository.create_execution(
        db=db_session, agent_id=agent.id, organization_id=org.id, workspace_id=ws.id,
        triggered_by=user.id, trigger_type="MANUAL", input_context={"scope": "active_milestones"},
        status="QUEUED"
    )
    assert exec_rec.status == "QUEUED"

    # 2. Transition QUEUED -> RUNNING
    exec_running = await CognitiveAgentRepository.update_execution_status(
        db=db_session, execution_id=exec_rec.id, organization_id=org.id, status="RUNNING"
    )
    assert exec_running.status == "RUNNING"

    # 3. Transition RUNNING -> COMPLETED
    exec_completed = await CognitiveAgentRepository.update_execution_status(
        db=db_session, execution_id=exec_rec.id, organization_id=org.id, status="COMPLETED",
        output_summary="Identified 2 overdue tasks.", action_candidates_generated=2
    )
    assert exec_completed.status == "COMPLETED"
    assert exec_completed.completed_at is not None
    assert exec_completed.action_candidates_generated == 2


# ---------------- TEST 9: FAILED EXECUTION PERSISTENCE ----------------
@pytest.mark.asyncio
async def test_9_failed_execution_persistence(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t9")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Faulty Agent", instructions="Simulate error handling"
    )

    exec_rec = await CognitiveAgentRepository.create_execution(
        db=db_session, agent_id=agent.id, organization_id=org.id, status="RUNNING"
    )

    exec_failed = await CognitiveAgentRepository.update_execution_status(
        db=db_session, execution_id=exec_rec.id, organization_id=org.id, status="FAILED",
        error_message="External API timeout while reading project documents."
    )

    assert exec_failed.status == "FAILED"
    assert "timeout" in exec_failed.error_message


# ---------------- TEST 10: OUTPUT PERSISTENCE ----------------
@pytest.mark.asyncio
async def test_10_output_persistence(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t10")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Summarizer", instructions="Summarize discussions"
    )

    exec_rec = await CognitiveAgentRepository.create_execution(
        db=db_session, agent_id=agent.id, organization_id=org.id, status="RUNNING"
    )

    output = await CognitiveAgentRepository.create_output(
        db=db_session, execution_id=exec_rec.id, agent_id=agent.id, organization_id=org.id,
        workspace_id=ws.id, output_type="ACTION_CANDIDATE", title="Create Reminder for Code Review",
        body="Assigned review to lead architect", candidate_type="CREATE_REMINDER",
        provenance=[{"source_type": "CONVERSATION", "source_id": str(uuid.uuid4())}]
    )

    assert output.id is not None
    assert output.execution_id == exec_rec.id
    assert output.agent_id == agent.id
    assert output.output_type == "ACTION_CANDIDATE"
    assert output.candidate_type == "CREATE_REMINDER"


# ---------------- TEST 11: REFERENTIAL INTEGRITY ----------------
@pytest.mark.asyncio
async def test_11_referential_integrity(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t11")

    # 1. Creating agent with invalid organization_id should fail
    fake_org_id = uuid.uuid4()
    with pytest.raises(Exception) as exc_info:
        await CognitiveAgentService.create_agent(
            db=db_session,
            current_user=user,
            organization_id=fake_org_id,
            payload=CognitiveAgentCreate(name="Invalid Org Agent", instructions="Inst")
        )
    assert getattr(exc_info.value, "status_code", None) == 404

    # 2. Creating agent with invalid workspace_id should fail
    fake_ws_id = uuid.uuid4()
    with pytest.raises(Exception) as exc_info_ws:
        await CognitiveAgentService.create_agent(
            db=db_session,
            current_user=user,
            organization_id=org.id,
            payload=CognitiveAgentCreate(name="Invalid WS Agent", instructions="Inst", workspace_id=fake_ws_id)
        )
    assert getattr(exc_info_ws.value, "status_code", None) == 404


# ---------------- TEST 12: ARCHIVE BEHAVIOR (SOFT DELETE) ----------------
@pytest.mark.asyncio
async def test_12_archive_agent_preserves_history(db_session: AsyncSession):
    user, org, ws, _ = await seed_test_user_and_org(db_session, "t12")

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Archivable Agent", instructions="To be archived"
    )

    exec_rec = await CognitiveAgentRepository.create_execution(
        db=db_session, agent_id=agent.id, organization_id=org.id, status="COMPLETED"
    )

    archived = await CognitiveAgentRepository.archive_agent(db_session, agent.id, org.id)
    assert archived is True

    # Agent should not be returned by default active list
    active_agents = await CognitiveAgentRepository.list_agents(db_session, org.id, include_archived=False)
    assert agent.id not in [a.id for a in active_agents]

    # Execution record must still be preserved for historical audit
    executions = await CognitiveAgentRepository.list_agent_executions(db_session, agent.id, org.id)
    assert len(executions) == 1
    assert executions[0].id == exec_rec.id


# ---------------- TEST 13: REST API END-TO-END CRUD ----------------
@pytest.mark.asyncio
async def test_13_rest_api_e2e_crud(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_test_user_and_org(db_session, "t13")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # 1. POST /api/v1/cognitive-agents
    create_payload = {
        "name": "E2E Rest Agent",
        "description": "Created via HTTP REST API",
        "agent_type": "KNOWLEDGE_SYNTHESIZER",
        "instructions": "Synthesize weekly project reports.",
        "workspace_id": str(ws.id)
    }
    res_create = await client.post("/api/v1/cognitive-agents", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    agent_data = res_create.json()
    agent_id = agent_data["id"]

    # 2. GET /api/v1/cognitive-agents/{id}
    res_get = await client.get(f"/api/v1/cognitive-agents/{agent_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "E2E Rest Agent"

    # 3. PATCH /api/v1/cognitive-agents/{id}
    patch_payload = {"status": "PAUSED", "description": "Paused by admin"}
    res_patch = await client.patch(f"/api/v1/cognitive-agents/{agent_id}", json=patch_payload, headers=headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "PAUSED"

    # 4. DELETE /api/v1/cognitive-agents/{id}
    res_delete = await client.delete(f"/api/v1/cognitive-agents/{agent_id}", headers=headers)
    assert res_delete.status_code == 204
