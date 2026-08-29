import pytest
import time
import hashlib
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.models.pending_registration import PendingRegistration
from sqlalchemy import select

async def register_user_in_test(client: AsyncClient, payload: dict):
    res = await client.post("/api/v1/auth/register", json=payload)
    if res.status_code != 200:
        return res
    token = res.json()["registration_token"]
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        pending_res = await session.execute(stmt)
        pending = pending_res.scalar_one()
        pending.otp_hash = hashlib.sha256("123456".encode("utf-8")).hexdigest()
        session.add(pending)
        await session.commit()
    
    return await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "123456"
    })

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    ts = int(time.time() * 1000)
    unique_suffix = f"test_{ts}"
    user_payload = {
        "email": f"{unique_suffix}@mindmesh.com",
        "username": unique_suffix,
        "password": "Password123!",
        "phone_number": f"+9195{ts % 100000000:08d}",
        "first_name": "Test",
        "last_name": "User"
    }

    # Register
    reg_res = await register_user_in_test(client, user_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data
    assert reg_data["user"]["email"] == user_payload["email"]
    assert reg_data["user"]["username"] == user_payload["username"]

    # Login
    login_res = await client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # Get Me with Token
    me_res = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == user_payload["email"]

    # Refresh Token
    refresh_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens

@pytest.mark.asyncio
async def test_firebase_login(client: AsyncClient):
    id_token = "mock_firebase_token_+19998887777"
    login_res = await client.post("/api/v1/auth/firebase-login", json={"idToken": id_token})
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["phone_number"] == "+19998887777"

@pytest.mark.asyncio
async def test_password_strength_validation(client: AsyncClient):
    user_payload = {
        "email": "weak@mindmesh.com",
        "username": "weakuser",
        "password": "123",
        "phone_number": "+919500000001",
        "first_name": "Weak",
        "last_name": "User"
    }
    reg_res = await client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 400
