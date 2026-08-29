import pytest
import time
import uuid
import hashlib
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
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
async def test_bug3_empty_mobile_number_registration(client: AsyncClient):
    suffix = f"optmob_{int(time.time() * 1000)}"
    user_payload = {
        "email": f"{suffix}@mindmesh.com",
        "username": suffix,
        "password": "Password123!",
        "phone_number": "   ",  # whitespace only
        "first_name": "Required",
        "last_name": "Mobile"
    }

    res = await client.post("/api/v1/auth/register", json=user_payload)
    assert res.status_code == 400
    data = res.json()
    assert data.get("detail") == "Mobile number is required." or data.get("message") == "Mobile number is required."

@pytest.mark.asyncio
async def test_bug2_organization_slug_collision_resolution(client: AsyncClient):
    ts = int(time.time() * 1000)
    suffix = f"slugcoll_{ts}"
    
    # 1. Register first user
    user_payload_1 = {
        "email": f"{suffix}_1@mindmesh.com",
        "username": f"{suffix}_user1",
        "password": "Password123!",
        "phone_number": f"+9198{ts % 100000000:08d}",
        "first_name": "Slug",
        "last_name": "One"
    }
    res1 = await register_user_in_test(client, user_payload_1)
    assert res1.status_code == 201
    user1_id = uuid.UUID(res1.json()["user"]["id"])

    # Pre-seed an organization with slug = "{suffix}_user2-personal-org" to force slug collision for user2
    async with AsyncSessionLocal() as session:
        dup_org = Organization(
            name="Colliding Org",
            slug=f"{suffix}_user2-personal-org",
            owner_id=user1_id
        )
        session.add(dup_org)
        await session.commit()

    # 2. Register second user with username "{suffix}_user2" whose base slug matches the pre-seeded org slug
    user_payload_2 = {
        "email": f"{suffix}_2@mindmesh.com",
        "username": f"{suffix}_user2",
        "password": "Password123!",
        "phone_number": f"+9198{(ts + 1) % 100000000:08d}",
        "first_name": "Slug",
        "last_name": "Two"
    }
    res2 = await register_user_in_test(client, user_payload_2)
    assert res2.status_code == 201  # Must succeed automatically without crash!

    # Verify that user2's personal organization has a unique deduplicated slug
    async with AsyncSessionLocal() as session:
        stmt = select(Organization).where(Organization.owner_id == uuid.UUID(res2.json()["user"]["id"]))
        res = await session.execute(stmt)
        user2_org = res.scalar_one_or_none()
        assert user2_org is not None
        assert user2_org.slug != f"{suffix}_user2-personal-org"
        assert user2_org.slug.startswith(f"{suffix}_user2-personal-org")

@pytest.mark.asyncio
async def test_bug1_clean_error_messages_no_sql_leak(client: AsyncClient):
    ts = int(time.time() * 1000)
    suffix = f"cleanerr_{ts}"
    user_payload = {
        "email": f"{suffix}@mindmesh.com",
        "username": suffix,
        "password": "Password123!",
        "phone_number": f"+9197{ts % 100000000:08d}",
        "first_name": "Clean",
        "last_name": "Error"
    }

    # Register initial user
    res1 = await register_user_in_test(client, user_payload)
    assert res1.status_code == 201

    # Try duplicate email
    dup_email_payload = dict(user_payload)
    dup_email_payload["username"] = f"{suffix}_unique"
    dup_email_payload["phone_number"] = f"+9197{(ts + 10) % 100000000:08d}"
    res2 = await register_user_in_test(client, dup_email_payload)
    assert res2.status_code == 400
    err_text = res2.text
    # Verify no raw SQL or DB traceback leak
    assert "sqlalchemy" not in err_text.lower()
    assert "postgresql" not in err_text.lower()
    assert "sqlite" not in err_text.lower()
    assert "unique constraint" not in err_text.lower()
    assert res2.json()["detail"] == "This email address is already registered."

    # Try duplicate username
    dup_uname_payload = dict(user_payload)
    dup_uname_payload["email"] = f"{suffix}_unique@mindmesh.com"
    dup_uname_payload["phone_number"] = f"+9197{(ts + 20) % 100000000:08d}"
    res3 = await register_user_in_test(client, dup_uname_payload)
    assert res3.status_code == 400
    err_text3 = res3.text
    assert "sqlalchemy" not in err_text3.lower()
    assert "postgresql" not in err_text3.lower()
    assert "sqlite" not in err_text3.lower()
    assert res3.json()["detail"] == "This username is already taken."
