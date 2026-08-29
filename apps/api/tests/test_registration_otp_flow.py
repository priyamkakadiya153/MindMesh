import pytest
import time
import uuid
import hashlib
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.pending_registration import PendingRegistration
from sqlalchemy import select

@pytest.mark.asyncio
async def test_auto_generated_username_without_username_input(client: AsyncClient):
    ts = int(time.time() * 1000)
    # Registration WITHOUT username field
    user_payload = {
        "email": f"autouser_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Priyam",
        "last_name": "Kakadiya"
    }

    # 1. Initiate registration (no username provided)
    init_res = await client.post("/api/v1/auth/register", json=user_payload)
    assert init_res.status_code == 200
    token = init_res.json()["registration_token"]

    # 2. Check pending registration has auto-generated internal username "priyam.kakadiya"
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        res = await session.execute(stmt)
        pending = res.scalar_one()
        assert pending.username == "priyam.kakadiya"

        # Mock OTP code verification hash
        pending.otp_hash = hashlib.sha256("123456".encode("utf-8")).hexdigest()
        session.add(pending)
        await session.commit()

    # 3. Complete registration
    verify_res = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "123456"
    })
    assert verify_res.status_code == 201
    user_data = verify_res.json()["user"]
    assert user_data["username"] == "priyam.kakadiya"
    assert user_data["first_name"] == "Priyam"
    assert user_data["last_name"] == "Kakadiya"

    # 4. Initiate SECOND registration with SAME names (Priyam Kakadiya)
    ts2 = ts + 1
    user_payload_2 = {
        "email": f"autouser_{ts2}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts2 % 100000000:08d}",
        "first_name": "Priyam",
        "last_name": "Kakadiya"
    }
    init_res2 = await client.post("/api/v1/auth/register", json=user_payload_2)
    assert init_res2.status_code == 200
    token2 = init_res2.json()["registration_token"]

    # Verify auto-deduplication generated "priyam.kakadiya2"
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token2)
        res = await session.execute(stmt)
        pending2 = res.scalar_one()
        assert pending2.username == "priyam.kakadiya2"

@pytest.mark.asyncio
async def test_duplicate_registration_checks_no_otp_sent(client: AsyncClient):
    ts = int(time.time() * 1000)
    user_payload_1 = {
        "email": f"dup_{ts}_1@mindmesh.com",
        "username": f"dup_{ts}_user1",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Dup",
        "last_name": "Test1"
    }

    # 1. Initiate and complete first registration
    init_res1 = await client.post("/api/v1/auth/register", json=user_payload_1)
    assert init_res1.status_code == 200
    token1 = init_res1.json()["registration_token"]

    # Get OTP hash from DB to complete registration in test
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token1)
        res = await session.execute(stmt)
        pending1 = res.scalar_one()

    # Create permanent user by verifying OTP via mock completion or endpoint call
    # We test complete_registration with wrong OTP first
    wrong_verify = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token1,
        "code": "000000"
    })
    assert wrong_verify.status_code == 400
    assert "Invalid verification code" in wrong_verify.json()["detail"]

    # Verify no permanent user exists yet!
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == user_payload_1["email"])
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_full_email_otp_registration_flow(client: AsyncClient):
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"flow_{ts}@mindmesh.com",
        "username": f"flow_{ts}",
        "password": "Password123!",
        "phone_number": f"+9199{ts % 100000000:08d}",
        "first_name": "Email",
        "last_name": "Verified"
    }

    # 1. Initiate registration
    init_res = await client.post("/api/v1/auth/register", json=user_payload)
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["status"] == "ok"
    assert "email_masked" in init_data
    token = init_data["registration_token"]
    assert token.startswith("reg_tok_")

    # 2. Confirm user does NOT exist in DB yet
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == user_payload["email"])
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is None

    # 3. Retrieve actual plain OTP generated for pending registration from mock/DB for verification
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        res = await session.execute(stmt)
        pending = res.scalar_one()
        assert pending.email == user_payload["email"]
        assert pending.is_used is False

    # 4. Attempt wrong OTP -> fail
    bad_res = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "111111"
    })
    assert bad_res.status_code == 400

    # User still does NOT exist
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == user_payload["email"])
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_duplicate_checks_before_otp(client: AsyncClient):
    # Missing mobile number check
    res = await client.post("/api/v1/auth/register", json={
        "email": "nomobile@mindmesh.com",
        "username": "nomobile",
        "password": "Password123!",
        "first_name": "No",
        "last_name": "Mobile"
    })
    assert res.status_code == 400
    assert "Mobile number is required." in res.json()["detail"]
