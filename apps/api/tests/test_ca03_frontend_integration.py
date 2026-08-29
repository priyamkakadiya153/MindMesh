import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace
from app.models.role import Role
from app.models.session import UserSession
from app.models.task import Task
from app.actions.candidate import ActionCandidate
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.models.cognitive_agent import CognitiveAgent, CognitiveAgentExecution
from app.core.security import create_access_token
from datetime import datetime, timedelta

async def seed_ca03_user_and_org(db: AsyncSession, name_prefix: str = "ca03"):
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


# ---------------- TEST 1: EMPTY STATE ----------------
@pytest.mark.asyncio
async def test_1_empty_state_returns_empty_list(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t1")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    res = await client.get(f"/api/v1/cognitive-agents?workspace_id={ws.id}", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


# ---------------- TEST 2: REAL AGENTS RETURNED ----------------
@pytest.mark.asyncio
async def test_2_real_agents_returned_in_list(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t2")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Real Agent", instructions="Analyze chats"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    res = await client.get(f"/api/v1/cognitive-agents?workspace_id={ws.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == str(agent.id)
    assert data[0]["name"] == "Real Agent"


# ---------------- TEST 3: CREATE AGENT VIA API ----------------
@pytest.mark.asyncio
async def test_3_create_agent_persists_record(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t3")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    payload = {
        "name": "Project Monitor",
        "description": "Monitors project tasks and deadlines",
        "agent_type": "PROJECT_MONITOR",
        "instructions": "Identify blockers and deadlines",
        "status": "ACTIVE",
        "workspace_id": str(ws.id)
    }

    res = await client.post("/api/v1/cognitive-agents", json=payload, headers=headers)
    assert res.status_code == 201
    created_data = res.json()
    assert created_data["name"] == "Project Monitor"
    assert created_data["status"] == "ACTIVE"

    # Verify directly in DB
    db_agent = await CognitiveAgentRepository.get_agent_by_id(db_session, uuid.UUID(created_data["id"]), org.id)
    assert db_agent is not None
    assert db_agent.name == "Project Monitor"


# ---------------- TEST 4: VALIDATION FAILURE ----------------
@pytest.mark.asyncio
async def test_4_create_agent_validation_failure(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t4")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    # Invalid payload: missing instructions
    invalid_payload = {
        "name": "Invalid Agent",
        "workspace_id": str(ws.id)
    }

    res = await client.post("/api/v1/cognitive-agents", json=invalid_payload, headers=headers)
    assert res.status_code == 422  # Unprocessable Entity


# ---------------- TEST 5: EDIT AGENT ----------------
@pytest.mark.asyncio
async def test_5_edit_agent_persists_changes(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t5")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Initial Name", instructions="Initial Instructions"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    patch_payload = {
        "name": "Updated Agent Name",
        "description": "Updated Description",
        "instructions": "Updated Instructions"
    }

    res = await client.patch(f"/api/v1/cognitive-agents/{agent.id}", json=patch_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Agent Name"
    assert res.json()["instructions"] == "Updated Instructions"


# ---------------- TEST 6 & 7: PAUSE AND RESUME AGENT ----------------
@pytest.mark.asyncio
async def test_6_7_pause_and_resume_agent_lifecycle(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t6")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Lifecycle Agent", instructions="Instructions", status="ACTIVE"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    # Pause
    res_pause = await client.patch(f"/api/v1/cognitive-agents/{agent.id}", json={"status": "PAUSED"}, headers=headers)
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "PAUSED"

    # Resume
    res_resume = await client.patch(f"/api/v1/cognitive-agents/{agent.id}", json={"status": "ACTIVE"}, headers=headers)
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "ACTIVE"


# ---------------- TEST 8: ARCHIVE AGENT ----------------
@pytest.mark.asyncio
async def test_8_archive_agent_removes_from_active_list(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t8")
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Archivable Agent", instructions="Instructions"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    res_archive = await client.delete(f"/api/v1/cognitive-agents/{agent.id}", headers=headers)
    assert res_archive.status_code == 204

    # List active agents
    res_list = await client.get(f"/api/v1/cognitive-agents?workspace_id={ws.id}", headers=headers)
    assert res_list.status_code == 200
    agent_ids = [a["id"] for a in res_list.json()]
    assert str(agent.id) not in agent_ids


# ---------------- TEST 9: WORKSPACE ISOLATION ----------------
@pytest.mark.asyncio
async def test_9_workspace_isolation_in_api(client: AsyncClient, db_session: AsyncSession):
    user, org, ws1, sess = await seed_ca03_user_and_org(db_session, "t9_ws1")
    ws2 = Workspace(name="Workspace 2", slug=f"ws2-{uuid.uuid4().hex[:6]}", organization_id=org.id, created_by=user.id)
    db_session.add(ws2)
    await db_session.commit()

    agent_ws1 = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws1.id, owner_user_id=user.id,
        name="WS1 Agent", instructions="Inst WS1"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    res_ws2 = await client.get(f"/api/v1/cognitive-agents?workspace_id={ws2.id}", headers=headers)
    assert res_ws2.status_code == 200
    agent_ids = [a["id"] for a in res_ws2.json()]
    assert str(agent_ws1.id) not in agent_ids


# ---------------- TEST 10: UNAUTHORIZED ACCESS ----------------
@pytest.mark.asyncio
async def test_10_unauthorized_access_prevented(client: AsyncClient, db_session: AsyncSession):
    user_a, org_a, ws_a, sess_a = await seed_ca03_user_and_org(db_session, "t10_a")
    user_b, org_b, ws_b, sess_b = await seed_ca03_user_and_org(db_session, "t10_b")

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org_a.id, workspace_id=ws_a.id, owner_user_id=user_a.id,
        name="User A Agent", instructions="Inst A"
    )

    token_b = create_access_token(subject=str(user_b.id), session_id=str(sess_b.id))
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": str(org_b.id)}

    res = await client.get(f"/api/v1/cognitive-agents/{agent_a.id}", headers=headers_b)
    assert res.status_code == 404


# ---------------- TEST 11: ZERO EXECUTION SIDE EFFECTS ----------------
@pytest.mark.asyncio
async def test_11_zero_execution_side_effects(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t11")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    tasks_count_before = (await db_session.execute(select(func.count(Task.id)))).scalar() or 0
    exec_count_before = (await db_session.execute(select(func.count(CognitiveAgentExecution.id)))).scalar() or 0

    # Create agent
    res_create = await client.post("/api/v1/cognitive-agents", json={
        "name": "SideEffect Free Agent",
        "instructions": "Do nothing autonomous",
        "workspace_id": str(ws.id)
    }, headers=headers)
    assert res_create.status_code == 201
    agent_id = res_create.json()["id"]

    # Edit agent
    await client.patch(f"/api/v1/cognitive-agents/{agent_id}", json={"status": "PAUSED"}, headers=headers)

    tasks_count_after = (await db_session.execute(select(func.count(Task.id)))).scalar() or 0
    exec_count_after = (await db_session.execute(select(func.count(CognitiveAgentExecution.id)))).scalar() or 0

    # Assert exactly zero side effects occurred
    assert tasks_count_after == tasks_count_before
    assert exec_count_after == exec_count_before


# ---------------- TEST 12: REFRESH PERSISTENCE ----------------
@pytest.mark.asyncio
async def test_12_refresh_persistence_verification(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t12")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    res_create = await client.post("/api/v1/cognitive-agents", json={
        "name": "Persistent Refresh Agent",
        "instructions": "Persistent instructions",
        "workspace_id": str(ws.id)
    }, headers=headers)
    agent_id = res_create.json()["id"]

    # Subsequent GET simulates page refresh
    res_refresh = await client.get(f"/api/v1/cognitive-agents/{agent_id}", headers=headers)
    assert res_refresh.status_code == 200
    assert res_refresh.json()["name"] == "Persistent Refresh Agent"


# ---------------- TEST 13: LOGOUT / SESSION SCOPING ----------------
@pytest.mark.asyncio
async def test_13_logout_session_scoping(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca03_user_and_org(db_session, "t13")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))

    # Revoke session in DB
    sess.revoked = True
    await db_session.commit()

    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}
    res = await client.get(f"/api/v1/cognitive-agents?workspace_id={ws.id}", headers=headers)
    assert res.status_code == 401
