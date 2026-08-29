import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:4000/api/v1"

def http_post(url, data, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {})
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {e.code}: {e.read().decode('utf-8')}")
        raise e

def http_get(url, token=None):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"} if token else {},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {e.code}: {e.read().decode('utf-8')}")
        raise e

import asyncio
import os
sys.path.insert(0, os.path.abspath("."))

from app.database.session import AsyncSessionLocal
from app.auth.service import AuthService
from app.auth.schemas import UserRegister

from uuid import uuid4
from datetime import datetime, timedelta
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.core.security import create_access_token

async def async_http_verification():
    print("==================================================")
    print("  HTTP API 2-USER REAL SERVER VERIFICATION")
    print("==================================================")

    now = datetime.utcnow()
    org_id = uuid4()
    ws_id = uuid4()
    user_a_id = uuid4()
    user_b_id = uuid4()

    async with AsyncSessionLocal() as db:
        # 1. Create Users
        user_a = User(
            id=user_a_id,
            email=f"usera_{uuid4().hex[:6]}@mindmesh.io",
            username=f"usera_{uuid4().hex[:6]}",
            first_name="Alice",
            last_name="HTTP",
            hashed_password="hashed_pass",
            phone_number=f"+1415{uuid4().int % 10000000:07d}",
            is_active=True,
            created_at=now,
            updated_at=now
        )
        db.add(user_a)

        user_b = User(
            id=user_b_id,
            email=f"userb_{uuid4().hex[:6]}@mindmesh.io",
            username=f"userb_{uuid4().hex[:6]}",
            first_name="Bob",
            last_name="HTTP",
            hashed_password="hashed_pass",
            phone_number=f"+1415{uuid4().int % 10000000:07d}",
            is_active=True,
            created_at=now,
            updated_at=now
        )
        db.add(user_b)
        await db.flush()

        # 2. Create Organization
        org = Organization(
            id=org_id,
            name="Live Test Org",
            slug=f"test-org-{uuid4().hex[:6]}",
            owner_id=user_a_id,
            created_at=now,
            updated_at=now
        )
        db.add(org)
        await db.flush()

        user_a.current_organization_id = org_id
        user_b.current_organization_id = org_id

        # 3. Create Workspace
        ws = Workspace(
            id=ws_id,
            organization_id=org_id,
            name="Live Test Workspace",
            slug=f"test-ws-{uuid4().hex[:6]}",
            owner_id=user_a_id,
            created_at=now,
            updated_at=now
        )
        db.add(ws)
        await db.flush()

        user_a.current_workspace_id = ws_id
        user_b.current_workspace_id = ws_id

        # 4. Organization Members
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_a_id, role="owner", is_active=True, joined_at=now))
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_b_id, role="member", is_active=True, joined_at=now))

        # 5. User Sessions
        sess_a_id = uuid4()
        sess_b_id = uuid4()
        from app.models.session import UserSession
        db.add(UserSession(id=sess_a_id, user_id=user_a_id, refresh_token_hash=f"hash_{uuid4().hex}", expires_at=datetime.utcnow() + timedelta(days=7), revoked=False, created_at=now, updated_at=now))
        db.add(UserSession(id=sess_b_id, user_id=user_b_id, refresh_token_hash=f"hash_{uuid4().hex}", expires_at=datetime.utcnow() + timedelta(days=7), revoked=False, created_at=now, updated_at=now))

        await db.commit()

    token_a = create_access_token(subject=str(user_a_id), org_id=str(org_id), workspace_id=str(ws_id), session_id=str(sess_a_id))
    token_b = create_access_token(subject=str(user_b_id), org_id=str(org_id), workspace_id=str(ws_id), session_id=str(sess_b_id))

    print(f"Provisioned DB Users A ({user_a_id}) and B ({user_b_id}) in Org ({org_id})")

    # Create Group by User A with User B included
    create_payload = {
        "name": "HTTP Live Test Group",
        "description": "Testing live HTTP server group creation",
        "organization_id": str(org_id),
        "workspace_id": str(ws_id),
        "visibility": "private",
        "member_user_ids": [str(user_b_id)]
    }
    group = http_post(f"{BASE_URL}/groups", create_payload, token=token_a)
    group_id = group["id"]
    print(f"[PASS] User A created group via HTTP API: '{group['name']}' ({group_id})")

    # User B queries list_groups for Org A
    groups_b = http_get(f"{BASE_URL}/groups?organization_id={org_id}", token=token_b)
    group_names_b = [g["name"] for g in groups_b]
    print(f"[PASS] User B list_groups response via HTTP API: {group_names_b}")

    assert "HTTP Live Test Group" in group_names_b, "User B did not see group via HTTP API"

    # User B sends message
    msg_b = http_post(f"{BASE_URL}/messages", {
        "conversation_id": group_id,
        "content": "Hello User A from live HTTP API",
        "message_type": "text"
    }, token=token_b)
    print(f"[PASS] User B sent group message via HTTP API: '{msg_b['content']}'")

    # User A gets message history
    history_a = http_get(f"{BASE_URL}/messages/{group_id}", token=token_a)
    print(f"[PASS] User A fetched message history via HTTP API: {len(history_a)} messages")
    assert len(history_a) == 1
    assert history_a[0]["content"] == "Hello User A from live HTTP API"

    print("==================================================")
    print("  [SUCCESS] 2-USER REAL HTTP API TEST PASSED 100%!")
    print("==================================================")

def run_http_verification():
    asyncio.run(async_http_verification())

if __name__ == "__main__":
    run_http_verification()
