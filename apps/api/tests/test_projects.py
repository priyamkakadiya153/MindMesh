import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.workspace.models import Workspace
from app.projects.models import Project, ProjectMember
from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.core.security import create_access_token
from passlib.hash import bcrypt

@pytest_asyncio.fixture
async def seeded_data(db_session: AsyncSession):
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = bcrypt.hash("password123")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_pwd)
    db_session.add(user)
    
    other_user = User(username="otheruser", email="other@example.com", hashed_password=hashed_pwd)
    db_session.add(other_user)
    await db_session.flush()

    org = Organization(name="Test Org", slug="test-org", owner_id=user.id)
    db_session.add(org)
    
    other_org = Organization(name="Other Org", slug="other-org", owner_id=other_user.id)
    db_session.add(other_org)
    await db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(member)
    
    other_member = OrganizationMember(organization_id=other_org.id, user_id=other_user.id, role_id=role.id)
    db_session.add(other_member)
    await db_session.flush()

    ws = Workspace(name="WS 1", slug="ws-1", organization_id=org.id)
    db_session.add(ws)
    
    other_ws = Workspace(name="WS 2", slug="ws-2", organization_id=other_org.id)
    db_session.add(other_ws)
    await db_session.flush()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="proj_hash_1", expires_at=datetime.utcnow() + timedelta(days=1))
    other_sess = UserSession(id=uuid4(), user_id=other_user.id, refresh_token_hash="proj_hash_2", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess, other_sess])

    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "org": org,
        "other_org": other_org,
        "workspace": ws,
        "other_workspace": other_ws,
        "sess": sess,
        "other_sess": other_sess
    }

@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "workspace_id": str(ws.id),
        "name": "MindMesh Platform",
        "description": "Enterprise AI Platform",
        "icon": "brain",
        "color": "#4F46E5",
        "visibility": "private"
    }
    response = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "MindMesh Platform"
    assert res_data["slug"] == "mindmesh-platform"
    assert res_data["visibility"] == "private"
    assert res_data["status"] == "active"

    stmt = select(Project).where(Project.id == UUID(res_data["id"]))
    db_proj = (await db_session.execute(stmt)).scalar_one()
    assert db_proj.name == "MindMesh Platform"

    stmt = select(ProjectMember).where(ProjectMember.project_id == db_proj.id)
    proj_mem = (await db_session.execute(stmt)).scalar_one()
    assert proj_mem.user_id == user.id
    assert proj_mem.role.lower() == "owner"

@pytest.mark.asyncio
async def test_create_duplicate_project(client: AsyncClient, seeded_data: dict):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "workspace_id": str(ws.id),
        "name": "Duplicates",
        "description": "First"
    }
    response = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201

    response2 = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    proj = Project(name="Old Project", slug="old-project", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.commit()

    payload = {
        "name": "New Project",
        "description": "Updated Project description"
    }
    response = await client.patch(f"/api/v1/projects/{proj.id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New Project"
    assert response.json()["description"] == "Updated Project description"

@pytest.mark.asyncio
async def test_archive_and_restore_project(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    proj = Project(name="Lifecycle Project", slug="lifecycle-project", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.commit()

    response = await client.post(f"/api/v1/projects/{proj.id}/archive", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_archived"] is True
    assert response.json()["status"] == "archived"

    response2 = await client.post(f"/api/v1/projects/{proj.id}/restore", headers=headers)
    assert response2.status_code == 200
    assert response2.json()["is_archived"] is False
    assert response2.json()["status"] == "active"

@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    proj = Project(name="Delete Proj", slug="delete-proj", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.commit()

    response = await client.delete(f"/api/v1/projects/{proj.id}", headers=headers)
    assert response.status_code == 204

    stmt = select(Project).where(Project.id == proj.id)
    db_proj = (await db_session.execute(stmt)).scalar_one()
    assert db_proj.is_active is False
    assert db_proj.deleted_at is not None

@pytest.mark.asyncio
async def test_workspace_isolation(client: AsyncClient, seeded_data: dict):
    user = seeded_data["user"]
    org = seeded_data["org"]
    other_ws = seeded_data["other_workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "workspace_id": str(other_ws.id),
        "name": "Isolated Project"
    }
    response = await client.post("/api/v1/projects/", json=payload, headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_member_management(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    other_user = seeded_data["other_user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    proj = Project(name="Member Project", slug="member-project", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.commit()

    payload = {
        "email": other_user.email,
        "role": "CONTRIBUTOR"
    }
    response = await client.post(f"/api/v1/projects/{proj.id}/members", json=payload, headers=headers)
    assert response.status_code == 201
    member_data = response.json()
    assert member_data["user_id"] == str(other_user.id)
    assert member_data["role"].lower() == "contributor"

    res_list = await client.get(f"/api/v1/projects/{proj.id}/members", headers=headers)
    assert res_list.status_code == 200

    payload_update = {"role": "ADMIN"}
    res_upd = await client.patch(f"/api/v1/projects/{proj.id}/members/{member_data['user_id']}", json=payload_update, headers=headers)
    assert res_upd.status_code == 200
    assert res_upd.json()["role"].lower() == "admin"

    res_del = await client.delete(f"/api/v1/projects/{proj.id}/members/{member_data['user_id']}", headers=headers)
    assert res_del.status_code == 204

@pytest.mark.asyncio
async def test_project_statistics(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    ws = seeded_data["workspace"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    proj = Project(name="Stats Project", slug="stats-project", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{proj.id}/statistics", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert "member_count" in res_data
    assert "document_count" in res_data
    assert "chat_count" in res_data
    assert "storage_used" in res_data
