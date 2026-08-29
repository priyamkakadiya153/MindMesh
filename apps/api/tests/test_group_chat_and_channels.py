import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_group_chat_and_channels_lifecycle(client, db_session: AsyncSession):
    # Setup test users
    user_owner = User(id=uuid4(), email=f"owner_{uuid4().hex[:6]}@example.com", username=f"owner_{uuid4().hex[:6]}", hashed_password="h", first_name="Group", last_name="Owner")
    user_member = User(id=uuid4(), email=f"member_{uuid4().hex[:6]}@example.com", username=f"member_{uuid4().hex[:6]}", hashed_password="h", first_name="Group", last_name="Member")
    db_session.add_all([user_owner, user_member])
    await db_session.commit()

    # Create Organization & Memberships
    org_id = uuid4()
    org = Organization(id=org_id, name="Group Org", slug=f"group-org-{uuid4().hex[:6]}", owner_id=user_owner.id)
    m1 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_owner.id, role="owner")
    m2 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_member.id, role="member")
    db_session.add_all([org, m1, m2])
    await db_session.commit()

    # Create Sessions & Tokens
    sess_owner = UserSession(id=uuid4(), user_id=user_owner.id, refresh_token_hash="tok_o", expires_at=datetime.utcnow() + timedelta(days=1))
    sess_member = UserSession(id=uuid4(), user_id=user_member.id, refresh_token_hash="tok_m", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess_owner, sess_member])
    await db_session.commit()

    token_owner = create_access_token(subject=user_owner.id, session_id=sess_owner.id)
    token_member = create_access_token(subject=user_member.id, session_id=sess_member.id)

    headers_owner = {"Authorization": f"Bearer {token_owner}"}
    headers_member = {"Authorization": f"Bearer {token_member}"}

    # 1. Owner creates a Group Chat
    group_res = await client.post(
        "/api/v1/groups",
        json={
            "name": "Engineering Leadership",
            "description": "Cross-functional tech discussions",
            "organization_id": str(org_id),
            "visibility": "private",
            "member_user_ids": [str(user_member.id)]
        },
        headers=headers_owner
    )
    assert group_res.status_code == 201, group_res.text
    group_data = group_res.json()
    group_id = group_data["id"]
    assert group_data["name"] == "Engineering Leadership"
    assert group_data["member_count"] == 2

    # 2. List Groups for Member
    list_res = await client.get(f"/api/v1/groups?organization_id={org_id}", headers=headers_member)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["id"] == group_id

    # 3. Owner creates a Project Channel
    channel_res = await client.post(
        "/api/v1/channels",
        json={
            "name": "#architecture-discussions",
            "description": "Technical design & system specs",
            "organization_id": str(org_id),
            "type": "project_channel",
            "visibility": "public"
        },
        headers=headers_owner
    )
    assert channel_res.status_code == 201, channel_res.text
    channel_id = channel_res.json()["id"]

    # 4. Member lists Project Channels
    chan_list_res = await client.get(f"/api/v1/channels?organization_id={org_id}", headers=headers_member)
    assert chan_list_res.status_code == 200
    assert len(chan_list_res.json()) == 1

    # 5. Member sends a message in the Group Chat
    msg_res = await client.post(
        "/api/v1/messages",
        json={
            "conversation_id": group_id,
            "content": "Hello team, welcome to the group!",
            "message_type": "text"
        },
        headers=headers_member
    )
    assert msg_res.status_code == 201, msg_res.text
    msg_id = msg_res.json()["id"]

    # 6. Owner pins the group conversation
    pin_res = await client.post(f"/api/v1/conversations/{group_id}/pin", headers=headers_owner)
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    # 7. Owner updates member role to admin
    role_res = await client.patch(
        f"/api/v1/groups/{group_id}/members/{user_member.id}/role",
        json={"role": "admin"},
        headers=headers_owner
    )
    assert role_res.status_code == 200

    # 8. Owner archives the Group
    arch_res = await client.post(f"/api/v1/groups/{group_id}/archive", headers=headers_owner)
    assert arch_res.status_code == 200
    assert arch_res.json()["is_archived"] is True

@pytest.mark.asyncio
async def test_group_rbac_permissions_security(client, db_session: AsyncSession):
    user_a = User(id=uuid4(), email=f"usera_{uuid4().hex[:6]}@example.com", username=f"usera_{uuid4().hex[:6]}", hashed_password="h")
    user_b = User(id=uuid4(), email=f"userb_{uuid4().hex[:6]}@example.com", username=f"userb_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Security Org", slug=f"sec-org-{uuid4().hex[:6]}", owner_id=user_a.id)
    m1 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_a.id, role="owner")
    m2 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_b.id, role="member")
    db_session.add_all([org, m1, m2])
    await db_session.commit()

    sess_a = UserSession(id=uuid4(), user_id=user_a.id, refresh_token_hash="s_a", expires_at=datetime.utcnow() + timedelta(days=1))
    sess_b = UserSession(id=uuid4(), user_id=user_b.id, refresh_token_hash="s_b", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess_a, sess_b])
    await db_session.commit()

    token_a = create_access_token(subject=user_a.id, session_id=sess_a.id)
    token_b = create_access_token(subject=user_b.id, session_id=sess_b.id)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Group
    group_res = await client.post(
        "/api/v1/groups",
        json={"name": "Restricted Group", "organization_id": str(org_id), "member_user_ids": [str(user_b.id)]},
        headers=headers_a
    )
    group_id = group_res.json()["id"]

    # User B (regular member) attempts to rename the Group (Should fail 403)
    edit_res = await client.patch(
        f"/api/v1/groups/{group_id}",
        json={"name": "Hacked Group Name"},
        headers=headers_b
    )
    assert edit_res.status_code == 403

    # User B attempts to archive the Group (Should fail 403)
    arch_res = await client.post(f"/api/v1/groups/{group_id}/archive", headers=headers_b)
    assert arch_res.status_code == 403
