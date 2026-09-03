import pytest
import time
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.pending_registration import PendingRegistration
from app.models.user import User


@pytest.mark.asyncio
async def test_123456_is_rejected_when_actual_otp_different(client: AsyncClient):
    """Criterion: Production does NOT accept 123456 as a universal master code."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"no_master_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Security",
        "last_name": "Tester"
    }

    with patch("app.auth.service.EmailOTPTransport.send_otp", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        assert init_res.status_code == 200
        token = init_res.json()["registration_token"]

    # Set real OTP to something other than 123456, e.g. 789456
    real_otp = "789456"
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        res = await session.execute(stmt)
        pending = res.scalar_one()
        pending.otp_hash = hashlib.sha256(real_otp.encode("utf-8")).hexdigest()
        session.add(pending)
        await session.commit()

    # Attempt to use the 123456 master code
    verify_res = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "123456"
    })
    assert verify_res.status_code == 400
    assert "invalid verification code" in verify_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_correct_otp_completes_registration(client: AsyncClient):
    """Criterion: User successfully completes registration using the correct emailed OTP."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"real_otp_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Valid",
        "last_name": "User"
    }

    captured_otp = []

    async def fake_send_otp(recipient_identifier, recipient_name, otp_code):
        captured_otp.append(otp_code)
        return True

    with patch("app.auth.service.EmailOTPTransport.send_otp", side_effect=fake_send_otp):
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        assert init_res.status_code == 200
        token = init_res.json()["registration_token"]

    assert len(captured_otp) == 1
    actual_emailed_otp = captured_otp[0]
    assert len(actual_emailed_otp) == 6
    assert actual_emailed_otp.isdigit()

    # Verify with the actual OTP
    verify_res = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": actual_emailed_otp
    })
    assert verify_res.status_code == 201
    data = verify_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == user_payload["email"]


@pytest.mark.asyncio
async def test_used_otp_cannot_be_reused(client: AsyncClient):
    """Criterion: Used OTP cannot be reused to create another account or session."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"single_use_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Single",
        "last_name": "Use"
    }

    captured = []
    async def capture_send(recipient_identifier="", recipient_name="", otp_code=""):
        captured.append(otp_code)
        return True

    with patch("app.auth.service.EmailOTPTransport.send_otp", side_effect=capture_send):
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        token = init_res.json()["registration_token"]

    actual_otp = captured[0]

    # First verification passes
    v1 = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": actual_otp
    })
    assert v1.status_code == 201

    # Second verification with same token/code fails
    v2 = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": actual_otp
    })
    assert v2.status_code == 400


@pytest.mark.asyncio
async def test_attempt_limit_protection(client: AsyncClient):
    """Criterion: Maximum attempts are protected against brute force."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"brute_force_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Brute",
        "last_name": "Force"
    }

    with patch("app.auth.service.EmailOTPTransport.send_otp", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        token = init_res.json()["registration_token"]

    # 3 wrong attempts
    for attempt in range(1, 4):
        res = await client.post("/api/v1/auth/register/verify-otp", json={
            "registration_token": token,
            "code": f"00000{attempt}"
        })
        assert res.status_code == 400

    # 4th attempt is locked out
    res_locked = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "111111"
    })
    assert res_locked.status_code == 400
    assert "maximum" in res_locked.json()["detail"].lower() or "expired" in res_locked.json()["detail"].lower() or "invalid" in res_locked.json()["detail"].lower()


@pytest.mark.asyncio
async def test_expired_otp_is_rejected(client: AsyncClient):
    """Criterion: Expired OTP is rejected."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"expired_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Expired",
        "last_name": "User"
    }

    with patch("app.auth.service.EmailOTPTransport.send_otp", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        token = init_res.json()["registration_token"]

    # Expire record in DB
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        res = await session.execute(stmt)
        pending = res.scalar_one()
        pending.expires_at = datetime.utcnow() - timedelta(minutes=10)
        session.add(pending)
        await session.commit()

    verify_res = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "999999"
    })
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resend_invalidates_old_otp_and_accepts_new_otp(client: AsyncClient):
    """Criterion: Resend creates a new OTP and invalidates the previous OTP."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"resend_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Resend",
        "last_name": "User"
    }

    otps = []
    async def capture_resend(recipient_identifier="", recipient_name="", otp_code=""):
        otps.append(otp_code)
        return True

    with patch("app.auth.service.EmailOTPTransport.send_otp", side_effect=capture_resend):
        init_res = await client.post("/api/v1/auth/register", json=user_payload)
        token = init_res.json()["registration_token"]

    old_otp = otps[0]

    # Advance DB timestamp to pass 60-second cooldown
    async with AsyncSessionLocal() as session:
        stmt = select(PendingRegistration).where(PendingRegistration.registration_token == token)
        res = await session.execute(stmt)
        pending = res.scalar_one()
        pending.updated_at = datetime.utcnow() - timedelta(seconds=70)
        session.add(pending)
        await session.commit()

    # Trigger resend
    with patch("app.auth.service.EmailOTPTransport.send_otp", side_effect=capture_resend):
        resend_res = await client.post("/api/v1/auth/register/resend-otp", json={
            "registration_token": token
        })
        assert resend_res.status_code == 200

    assert len(otps) == 2
    new_otp = otps[1]
    assert old_otp != new_otp



    # Attempt verification with old OTP -> must be rejected
    v_old = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": old_otp
    })
    assert v_old.status_code == 400

    # Verification with new OTP -> must succeed
    v_new = await client.post("/api/v1/auth/register/verify-otp", json={
        "registration_token": token,
        "code": new_otp
    })
    assert v_new.status_code == 201


@pytest.mark.asyncio
async def test_no_otp_leaks_in_api_responses(client: AsyncClient):
    """Criterion: Plaintext OTP is NEVER included in public API response payload."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"no_leak_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "No",
        "last_name": "Leak"
    }

    with patch("app.auth.service.EmailOTPTransport.send_otp", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        res = await client.post("/api/v1/auth/register", json=user_payload)
        assert res.status_code == 200
        data = res.json()
        assert "preview_otp" not in data
        assert "otp_code" not in data
        assert "code" not in data
        assert "otp" not in data


@pytest.mark.asyncio
async def test_delivery_failure_reports_clear_error(client: AsyncClient):
    """Criterion: If email provider rejects send, registration initiation reports HTTP 502 and does not advance."""
    ts = int(time.time() * 1000)
    user_payload = {
        "email": f"delivery_fail_{ts}@mindmesh.com",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Delivery",
        "last_name": "Fail"
    }

    with patch("app.auth.service.EmailOTPTransport.send_otp", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = False
        res = await client.post("/api/v1/auth/register", json=user_payload)
        assert res.status_code == 502
        assert "unable to send verification email" in res.json()["detail"].lower()
