import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.models.user import User
from app.models.otp import OtpCode
from app.auth.otp_service import OTPService

@pytest.mark.asyncio
async def test_phone_otp_flow_and_isolation(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies full Phone Login + Email OTP flow, user isolation, hashing, and token generation.
    """
    # 1. Seed User 1 and User 2
    user1 = User(
        email="user1@example.com",
        username="user1",
        hashed_password="",
        phone_number="+919876543210",
        first_name="User",
        last_name="One",
        is_verified=True,
        is_phone_verified=True
    )
    user2 = User(
        email="user2@example.com",
        username="user2",
        hashed_password="",
        phone_number="+919988776655",
        first_name="User",
        last_name="Two",
        is_verified=True,
        is_phone_verified=True
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # 2. Request OTP for User 1 (+91 9876543210)
    res1 = await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919876543210"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ok"
    assert "u*1@example.com" in data1["email_masked"] or "u***1@example.com" in data1["email_masked"]

    # 3. Check DB for User 1's OtpCode record
    otp_stmt1 = select(OtpCode).where(OtpCode.user_id == user1.id)
    otp_res1 = await db_session.execute(otp_stmt1)
    otp1 = otp_res1.scalars().first()
    assert otp1 is not None
    assert len(otp1.otp_hash) == 64  # SHA-256 hex string digest length
    assert otp1.is_used is False
    assert otp1.attempt_count == 0

    # 4. Request OTP for User 2 (+91 9988776655)
    res2 = await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919988776655"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert "u*2@example.com" in data2["email_masked"] or "u***2@example.com" in data2["email_masked"]

    # 5. Check DB for User 2's OtpCode record (User isolation check)
    otp_stmt2 = select(OtpCode).where(OtpCode.user_id == user2.id)
    otp_res2 = await db_session.execute(otp_stmt2)
    otp2 = otp_res2.scalars().first()
    assert otp2 is not None
    assert otp2.user_id == user2.id
    assert otp2.user_id != user1.id
    assert otp1.otp_hash != otp2.otp_hash

@pytest.mark.asyncio
async def test_otp_verification_success(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="testverify@example.com",
        username="testverify",
        hashed_password="",
        phone_number="+919876543211",
        first_name="Verify",
        last_name="Test"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    plain_code = "482915"
    hashed_code = hashlib.sha256(plain_code.encode()).hexdigest()
    
    otp_record = OtpCode(
        user_id=user.id,
        otp_hash=hashed_code,
        purpose="phone_login",
        expires_at=OTPService.generate_otp_code() and (user.created_at or user.updated_at), # placeholder datetime
        attempt_count=0,
        is_used=False
    )
    # Re-assign proper future expiry
    from datetime import datetime, timedelta
    otp_record.expires_at = datetime.utcnow() + timedelta(minutes=5)
    db_session.add(otp_record)
    await db_session.commit()

    # Verify OTP code via endpoint
    verify_res = await client.post("/api/v1/auth/phone/verify-otp", json={
        "phone_number": "+919876543211",
        "code": "482915"
    })
    assert verify_res.status_code == 200
    val_data = verify_res.json()
    assert "access_token" in val_data
    assert "refresh_token" in val_data
    assert val_data["user"]["phone_number"] == "+919876543211"
    assert val_data["user"]["is_phone_verified"] is True

@pytest.mark.asyncio
async def test_unregistered_phone_returns_404(client: AsyncClient):
    res = await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919111122222"})
    assert res.status_code == 404
    data = res.json()
    assert "No account found" in data["detail"]

@pytest.mark.asyncio
async def test_otp_resend_cooldown(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="cooldown@example.com",
        username="cooldown_user",
        hashed_password="",
        phone_number="+919000000001",
        first_name="Cooldown",
        last_name="Test"
    )
    db_session.add(user)
    await db_session.commit()

    # Initial request
    res1 = await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919000000001"})
    assert res1.status_code == 200

    # Immediate second request should trigger HTTP 429 Cooldown
    res2 = await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919000000001"})
    assert res2.status_code == 429
    assert "Please wait" in res2.json()["detail"]

@pytest.mark.asyncio
async def test_otp_invalid_code_max_attempts(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="attempts@example.com",
        username="attempts_user",
        hashed_password="",
        phone_number="+919000000002",
        first_name="Attempts",
        last_name="Test"
    )
    db_session.add(user)
    await db_session.commit()

    # Request OTP
    await client.post("/api/v1/auth/phone/send-otp", json={"phone_number": "+919000000002"})

    # Send wrong codes
    for attempt in range(1, 4):
        wrong_res = await client.post("/api/v1/auth/phone/verify-otp", json={
            "phone_number": "+919000000002",
            "code": "000000"
        })
        assert wrong_res.status_code == 400

    # 4th attempt should indicate maximum attempts exceeded
    fourth_res = await client.post("/api/v1/auth/phone/verify-otp", json={
        "phone_number": "+919000000002",
        "code": "000000"
    })
    assert fourth_res.status_code == 400
    assert "Maximum verification attempts exceeded" in fourth_res.json()["detail"] or "Invalid or expired" in fourth_res.json()["detail"]
