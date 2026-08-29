import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.role import Role
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace, WorkspaceMember
from app.models.session import UserSession
from app.core.security import decode_token

@pytest_asyncio.fixture(autouse=True)
async def seed_roles(db_session: AsyncSession):
    # Seed the SUPER_ADMIN role as required by the registration flow
    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    await db_session.commit()

@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    # Weak password test - should fail strength check
    payload = {
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "123",  # Less than 8 chars, no uppercase/lowercase/digits/special
        "phone_number": "+14155552670",
        "first_name": "Weak",
        "last_name": "User"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Password must be at least 8 characters long" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_missing_fields(client: AsyncClient):
    # Missing required email field - should fail Pydantic validation
    payload = {
        "username": "missinguser"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_success_and_login(client: AsyncClient, db_session: AsyncSession):
    # Success registration
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!",  # strong password
        "phone_number": "+14155552671",
        "first_name": "Test",
        "last_name": "User"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    # Assert tokens and user details returned
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["first_name"] == "Test"
    assert data["user"]["last_name"] == "User"

    user_id = data["user"]["id"]

    # Verify database inserts
    # 1. User is created and password is hashed using bcrypt 10 rounds ($2b$10$)
    stmt = select(User).where(User.id == uuid.UUID(user_id))
    res = await db_session.execute(stmt)
    db_user = res.scalar_one()
    assert db_user.email == "test@example.com"
    assert db_user.hashed_password.startswith(("$2b$", "$2a$"))

    # 2. Personal organization is created
    stmt_org = select(Organization).where(Organization.owner_id == db_user.id)
    res_org = await db_session.execute(stmt_org)
    db_org = res_org.scalar_one()
    assert db_org.slug == "testuser-personal-org"

    # 3. Organization membership is created as SUPER_ADMIN
    stmt_org_mem = select(OrganizationMember).where(
        OrganizationMember.user_id == db_user.id,
        OrganizationMember.organization_id == db_org.id
    )
    res_org_mem = await db_session.execute(stmt_org_mem)
    db_org_mem = res_org_mem.scalar_one()
    # verify role
    stmt_role = select(Role).where(Role.id == db_org_mem.role_id)
    res_role = await db_session.execute(stmt_role)
    assert res_role.scalar_one().name == "SUPER_ADMIN"

    # 4. Workspace is created
    stmt_ws = select(Workspace).where(Workspace.organization_id == db_org.id)
    res_ws = await db_session.execute(stmt_ws)
    db_ws = res_ws.scalar_one()
    assert db_ws.name == "Primary Workspace"
    assert db_ws.slug == "primary-workspace"

    # 5. Workspace membership is created as OWNER
    stmt_ws_mem = select(WorkspaceMember).where(
        WorkspaceMember.user_id == db_user.id,
        WorkspaceMember.workspace_id == db_ws.id
    )
    res_ws_mem = await db_session.execute(stmt_ws_mem)
    db_ws_mem = res_ws_mem.scalar_one()
    assert db_ws_mem.role.lower() == "owner"

    # Now let's try to Login with correct credentials
    login_payload = {
        "email": "test@example.com",
        "password": "Password123!"
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["user"]["email"] == "test@example.com"

    # Login with incorrect password
    bad_login_payload = {
        "email": "test@example.com",
        "password": "WrongPassword!"
    }
    bad_resp = await client.post("/api/v1/auth/login", json=bad_login_payload)
    assert bad_resp.status_code == 401
    assert "email or password" in bad_resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_and_logout(client: AsyncClient, db_session: AsyncSession):
    # Register user first
    payload = {
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "Password123!",
        "phone_number": "+14155552672",
        "first_name": "Refresh",
        "last_name": "User"
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    refresh_token = reg_data["refresh_token"]

    # Call Refresh endpoint
    refresh_payload = {
        "refresh_token": refresh_token
    }
    ref_resp = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert ref_resp.status_code == 200
    ref_data = ref_resp.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data
    new_refresh_token = ref_data["refresh_token"]

    import hashlib
    # Verify that the old refresh token is revoked in db
    old_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    stmt = select(UserSession).where(UserSession.refresh_token_hash == old_hash)
    res = await db_session.execute(stmt)
    old_db_token = res.scalar_one_or_none()
    assert old_db_token is not None
    assert old_db_token.revoked is True

    # Verify that the new refresh token is active in db
    new_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    stmt = select(UserSession).where(UserSession.refresh_token_hash == new_hash)
    res = await db_session.execute(stmt)
    new_db_token = res.scalar_one_or_none()
    assert new_db_token is not None
    assert new_db_token.revoked is False

    # Logout
    logout_payload = {
        "refresh_token": new_refresh_token
    }
    logout_resp = await client.post("/api/v1/auth/logout", json=logout_payload)
    assert logout_resp.status_code == 200
    
    # Verify that the new refresh token is now revoked
    stmt = select(UserSession).where(UserSession.refresh_token_hash == new_hash)
    res = await db_session.execute(stmt)
    revoked_db_token = res.scalar_one()
    assert revoked_db_token.revoked is True

@pytest.mark.asyncio
async def test_protected_routes(client: AsyncClient):
    # Verify that protected endpoints return 401 Unauthorized without token
    protected_paths = [
        "/api/v1/dashboard",
        "/api/v1/projects",
        "/api/v1/workspaces",
        "/api/v1/documents",
        "/api/v1/chat"
    ]
    for path in protected_paths:
        # GET request
        response_get = await client.get(path)
        assert response_get.status_code == 401
        
        # POST request
        response_post = await client.post(path, json={})
        assert response_post.status_code == 401

@pytest.mark.asyncio
async def test_multi_device_sessions_and_revoke(client: AsyncClient, db_session: AsyncSession):
    # Register user
    payload = {
        "email": "multidevice@example.com",
        "username": "multidevice",
        "password": "Password123!",
        "phone_number": "+14155552673",
        "first_name": "Multi",
        "last_name": "Device"
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload, headers={"User-Agent": "DeviceA"})
    assert reg_resp.status_code == 201
    token_a = reg_resp.json()["access_token"]

    # Login from second device
    login_payload = {
        "email": "multidevice@example.com",
        "password": "Password123!"
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload, headers={"User-Agent": "DeviceB"})
    assert login_resp.status_code == 200
    token_b = login_resp.json()["access_token"]

    # List active sessions from Device A
    sessions_resp = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_a}"})
    assert sessions_resp.status_code == 200
    sessions_data = sessions_resp.json()
    assert len(sessions_data) == 2

    # Find the session ID for Device B
    session_b_id = next(s["id"] for s in sessions_data if "DeviceB" in s["user_agent"])
    
    # Revoke Device B from Device A
    revoke_resp = await client.delete(f"/api/v1/auth/sessions/{session_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert revoke_resp.status_code == 200

    # Verify that Device B is now unauthorized
    protected_resp = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_b}"})
    assert protected_resp.status_code == 401

    # Verify that Device A is still authorized
    active_resp = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_a}"})
    assert active_resp.status_code == 200

@pytest.mark.asyncio
async def test_logout_all(client: AsyncClient, db_session: AsyncSession):
    # Register user
    payload = {
        "email": "logoutall@example.com",
        "username": "logoutall",
        "password": "Password123!",
        "phone_number": "+14155552674",
        "first_name": "Logout",
        "last_name": "All"
    }
    reg_resp = await client.post("/api/v1/auth/register", json=payload, headers={"User-Agent": "DeviceA"})
    assert reg_resp.status_code == 201
    token_a = reg_resp.json()["access_token"]

    # Login from second device
    login_payload = {
        "email": "logoutall@example.com",
        "password": "Password123!"
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload, headers={"User-Agent": "DeviceB"})
    assert login_resp.status_code == 200
    token_b = login_resp.json()["access_token"]

    # Trigger logout-all from Device A
    logout_all_resp = await client.post("/api/v1/auth/logout-all", headers={"Authorization": f"Bearer {token_a}"})
    assert logout_all_resp.status_code == 200

    # Verify both Device A and Device B are logged out
    resp_a = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 401

    # Verify Device B is logged out
    resp_b = await client.get("/api/v1/auth/sessions", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 401

