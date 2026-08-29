import pytest
import time
import hashlib
from httpx import AsyncClient
from app.auth.utils import normalize_phone_number
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

def test_phone_normalization_utility():
    # Scenario 1: Standard number with country code and spaces
    assert normalize_phone_number("+91 9925614120") == "+919925614120"
    
    # Scenario 2: Number with country code omitted
    assert normalize_phone_number("9925614120") == "+919925614120"
    
    # Scenario 3: Number with dashes
    assert normalize_phone_number("+91-9925614120") == "+919925614120"
    
    # Scenario 4: Number with parentheses
    assert normalize_phone_number("(99256)14120") == "+919925614120"

    # Edge cases
    assert normalize_phone_number(None) is None
    assert normalize_phone_number("") is None
    assert normalize_phone_number("   ") is None
    assert normalize_phone_number("+1 4155552671") == "+14155552671"

@pytest.mark.asyncio
async def test_bug1_duplicate_mobile_registration_prevention(client: AsyncClient):
    suffix = f"mob_{int(time.time() * 1000)}"
    user_payload_1 = {
        "email": f"{suffix}_1@mindmesh.com",
        "username": f"{suffix}_1",
        "password": "Password123!",
        "phone_number": "+919925614120",
        "first_name": "Mobile",
        "last_name": "Test1"
    }

    # 1. Register with +91 9925614120
    res1 = await register_user_in_test(client, user_payload_1)
    assert res1.status_code == 201
    assert res1.json()["user"]["phone_number"] == "+919925614120"

    # 2. Try registering again with omit country code format: 9925614120
    user_payload_2 = {
        "email": f"{suffix}_2@mindmesh.com",
        "username": f"{suffix}_2",
        "password": "Password123!",
        "phone_number": "9925614120",
        "first_name": "Mobile",
        "last_name": "Test2"
    }
    res2 = await register_user_in_test(client, user_payload_2)
    assert res2.status_code == 400
    assert "This mobile number is already registered." in res2.json()["detail"]

    # 3. Try registering again with full country code format: +919925614120
    user_payload_3 = {
        "email": f"{suffix}_3@mindmesh.com",
        "username": f"{suffix}_3",
        "password": "Password123!",
        "phone_number": "+919925614120",
        "first_name": "Mobile",
        "last_name": "Test3"
    }
    res3 = await register_user_in_test(client, user_payload_3)
    assert res3.status_code == 400
    assert "This mobile number is already registered." in res3.json()["detail"]

    # 4. Try registering with invalid formatting (dashes or parentheses) -> rejected by strict validation
    user_payload_4 = {
        "email": f"{suffix}_4@mindmesh.com",
        "username": f"{suffix}_4",
        "password": "Password123!",
        "phone_number": "(99256)14120",
        "first_name": "Mobile",
        "last_name": "Test4"
    }
    res4 = await register_user_in_test(client, user_payload_4)
    assert res4.status_code == 400
    assert "Invalid mobile number. India (+91) numbers must contain exactly 10 digits." in res4.json()["detail"]

@pytest.mark.asyncio
async def test_bug2_password_reset_flow(client: AsyncClient):
    suffix = f"reset_{int(time.time() * 1000)}"
    user_email = f"{suffix}@mindmesh.com"
    user_pwd = "OriginalPassword123!"
    new_pwd = "NewPassword123!"

    # Register user
    reg_res = await register_user_in_test(client, {
        "email": user_email,
        "username": suffix,
        "password": user_pwd,
        "phone_number": f"+9196{int(time.time() * 1000) % 100000000:08d}",
        "first_name": "Reset",
        "last_name": "User"
    })
    assert reg_res.status_code == 201

    # Non-existent user should fail with 404
    bad_req = await client.post("/api/v1/auth/password/forgot", json={"email": "nonexistent_email_12345@mindmesh.com"})
    assert bad_req.status_code == 404

    # Request password reset for existing email
    forgot_res = await client.post("/api/v1/auth/password/forgot", json={"email": user_email})
    assert forgot_res.status_code == 200

    # Get verification token from DB record
    from app.models.verification import EmailVerification

    async with AsyncSessionLocal() as session:
        stmt = select(EmailVerification).where(EmailVerification.email == user_email).order_by(EmailVerification.created_at.desc())
        res = await session.execute(stmt)
        record = res.scalars().first()
        assert record is not None
        code = record.code
        token = record.token

    # Reset password using the code
    reset_res = await client.post("/api/v1/auth/password/reset", json={
        "token_or_code": code,
        "new_password": new_pwd
    })
    assert reset_res.status_code == 200

    # Login with old password should fail
    fail_login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": user_pwd})
    assert fail_login.status_code == 401

    # Login with new password should succeed
    succ_login = await client.post("/api/v1/auth/login", json={"email": user_email, "password": new_pwd})
    assert succ_login.status_code == 200
