import asyncio
import pytest
import httpx
import hashlib
from uuid import uuid4
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.pending_registration import PendingRegistration
from sqlalchemy import select

async def register_user_in_test(client: httpx.AsyncClient, payload: dict):
    res = await client.post("/auth/register", json=payload)
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
    
    return await client.post("/auth/register/verify-otp", json={
        "registration_token": token,
        "code": "123456"
    })

@pytest.mark.asyncio
async def test_complete_invitation_and_notification_workflow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        pwd = "Password123!"

        # 1. Register Owner
        owner_email = f"owner_{uuid4().hex[:6]}@example.com"
        resp = await register_user_in_test(client, {
            "email": owner_email,
            "password": pwd,
            "phone_number": f"+9199{uuid4().hex[:8]}",
            "first_name": "Org",
            "last_name": "Owner"
        })
        assert resp.status_code in (200, 201), f"Register owner failed: {resp.text}"
        owner_token = resp.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        # 2. Register Target User
        target_email = f"target_{uuid4().hex[:6]}@example.com"
        resp = await register_user_in_test(client, {
            "email": target_email,
            "password": pwd,
            "phone_number": f"+9198{uuid4().hex[:8]}",
            "first_name": "Target",
            "last_name": "Recipient"
        })
        assert resp.status_code in (200, 201), f"Register target user failed: {resp.text}"
        target_token = resp.json()["access_token"]
        target_headers = {"Authorization": f"Bearer {target_token}"}

        # 3. Owner creates Organization
        org_name = f"TestOrg_{uuid4().hex[:6]}"
        org_slug = f"testorg-{uuid4().hex[:6]}"
        resp = await client.post("/organizations/", json={"name": org_name, "slug": org_slug}, headers=owner_headers)
        assert resp.status_code in (200, 201), f"Create org failed: {resp.text}"
        org_data = resp.json()
        org_id = org_data["id"]

        # 4. Target User initially has no invitations and no notifications
        resp = await client.get("/invitations/my", headers=target_headers)
        assert resp.status_code == 200, f"Get invitations failed: {resp.text}"
        assert len(resp.json()) == 0

        resp = await client.get("/notifications", headers=target_headers)
        assert resp.status_code == 200, f"Get notifications failed: {resp.text}"
        assert resp.json()["unread_count"] == 0

        # 5. Owner invites Target User
        resp = await client.post(f"/organizations/{org_id}/invitations", json={
            "email": target_email,
            "role": "admin"
        }, headers=owner_headers)
        assert resp.status_code in (200, 201), f"Invite member failed: {resp.text}"
        invite_data = resp.json()
        invite_id = invite_data["id"]

        # 6. Target User receives Notification & Invitation
        resp = await client.get("/notifications", headers=target_headers)
        assert resp.status_code == 200, f"Get notifications failed: {resp.text}"
        notif_resp = resp.json()
        assert notif_resp["unread_count"] == 1, f"Expected 1 unread notification, got {notif_resp['unread_count']}"
        notif = notif_resp["notifications"][0]
        assert notif["type"] == "invitation"
        assert notif.get("entity_type") == "organization_invitation"

        resp = await client.get("/invitations/my", headers=target_headers)
        assert resp.status_code == 200, f"Get user invitations failed: {resp.text}"
        user_invites = resp.json()
        assert len(user_invites) == 1
        assert user_invites[0]["id"] == invite_id
        assert user_invites[0]["role"] == "admin"

        # 7. Target User accepts Invitation
        resp = await client.post(f"/invitations/{invite_id}/accept", headers=target_headers)
        assert resp.status_code == 200, f"Accept invitation failed: {resp.text}"
        accept_res = resp.json()
        assert accept_res["status"] == "ok"

        # 8. Verify post-acceptance state
        resp = await client.get("/invitations/my", headers=target_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 0, "Pending invitations should be empty after acceptance"

        resp = await client.get("/notifications", headers=target_headers)
        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0, "Unread count should be 0 after invitation accepted"
