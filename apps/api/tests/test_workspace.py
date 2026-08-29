import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.workspace.models import Workspace, WorkspaceMember
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

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="ws_hash_1", expires_at=datetime.utcnow() + timedelta(days=1))
    other_sess = UserSession(id=uuid4(), user_id=other_user.id, refresh_token_hash="ws_hash_2", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess, other_sess])
    
    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "org": org,
        "other_org": other_org,
        "sess": sess,
        "other_sess": other_sess
    }

@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "name": "Engineering Team",
        "description": "Core dev team workspace",
        "icon": "cpu",
        "color": "#3B82F6"
    }
    response = await client.post("/api/v1/workspaces", json=payload, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["name"] == "Engineering Team"
    assert res_data["slug"] == "engineering-team"
    assert res_data["organization_id"] == str(org.id)
    assert res_data["is_archived"] is False
    assert res_data["is_default"] is False

    stmt = select(Workspace).where(Workspace.id == UUID(res_data["id"]))
    db_ws = (await db_session.execute(stmt)).scalar_one()
    assert db_ws.name == "Engineering Team"
    assert db_ws.slug == "engineering-team"

    stmt = select(WorkspaceMember).where(WorkspaceMember.workspace_id == db_ws.id)
    ws_mem = (await db_session.execute(stmt)).scalar_one()
    assert ws_mem.user_id == user.id
    assert ws_mem.role.lower() == "owner"

@pytest.mark.asyncio
async def test_create_duplicate_workspace(client: AsyncClient, seeded_data: dict):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    payload = {
        "name": "Duplicates",
        "description": "First workspace"
    }
    response = await client.post("/api/v1/workspaces", json=payload, headers=headers)
    assert response.status_code == 201

    response2 = await client.post("/api/v1/workspaces", json=payload, headers=headers)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_get_workspace_details(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    ws = Workspace(name="Detail Workspace", slug="detail-workspace", organization_id=org.id)
    db_session.add(ws)
    await db_session.commit()

    response = await client.get(f"/api/v1/workspaces/{ws.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Detail Workspace"

@pytest.mark.asyncio
async def test_update_workspace(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    ws = Workspace(name="Old Name", slug="old-name", organization_id=org.id)
    db_session.add(ws)
    await db_session.commit()

    payload = {
        "name": "New Name",
        "description": "Updated desc"
    }
    response = await client.patch(f"/api/v1/workspaces/{ws.id}", json=payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["name"] == "New Name"
    assert res_data["slug"] == "new-name"
    assert res_data["description"] == "Updated desc"

@pytest.mark.asyncio
async def test_archive_and_restore_workspace(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    ws = Workspace(name="Archive Workspace", slug="archive-workspace", organization_id=org.id)
    db_session.add(ws)
    await db_session.commit()

    response = await client.post(f"/api/v1/workspaces/{ws.id}/archive", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_archived"] is True

    response2 = await client.post(f"/api/v1/workspaces/{ws.id}/restore", headers=headers)
    assert response2.status_code == 200
    assert response2.json()["is_archived"] is False

@pytest.mark.asyncio
async def test_delete_workspace(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    ws = Workspace(name="Delete Workspace", slug="delete-workspace", organization_id=org.id)
    db_session.add(ws)
    await db_session.commit()

    response = await client.delete(f"/api/v1/workspaces/{ws.id}", headers=headers)
    assert response.status_code == 204

    stmt = select(Workspace).where(Workspace.id == ws.id)
    db_ws = (await db_session.execute(stmt)).scalar_one()
    assert db_ws.is_active is False
    assert db_ws.deleted_at is not None

@pytest.mark.asyncio
async def test_organization_isolation(client: AsyncClient, seeded_data: dict, db_session: AsyncSession):
    user = seeded_data["user"]
    org = seeded_data["org"]
    other_user = seeded_data["other_user"]
    other_org = seeded_data["other_org"]
    
    ws_org2 = Workspace(name="Org 2 Workspace", slug="org-2-workspace", organization_id=other_org.id)
    db_session.add(ws_org2)
    await db_session.commit()

    sess = seeded_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    response = await client.get(f"/api/v1/workspaces/{ws_org2.id}", headers=headers)
    assert response.status_code == 404
