import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage, MessageRead
from app.core.security import create_access_token
from app.api.dependencies import get_current_user

@pytest.mark.asyncio
async def test_one_to_one_conversation_creation_and_messaging(client, db_session: AsyncSession):
    # Setup test users
    user1 = User(
        id=uuid4(),
        email=f"user1_{uuid4().hex[:6]}@example.com",
        username=f"user1_{uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="User",
        last_name="One"
    )
    user2 = User(
        id=uuid4(),
        email=f"user2_{uuid4().hex[:6]}@example.com",
        username=f"user2_{uuid4().hex[:6]}",
        hashed_password="hash",
        first_name="User",
        last_name="Two"
    )
    db_session.add_all([user1, user2])
    await db_session.commit()

    # Create Organization & Memberships
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="Test Org",
        slug=f"test-org-{uuid4().hex[:6]}",
        owner_id=user1.id
    )
    m1 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user1.id, role="owner")
    m2 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user2.id, role="member")
    db_session.add_all([org, m1, m2])
    await db_session.commit()

    # Create User Sessions
    sess1 = UserSession(id=uuid4(), user_id=user1.id, refresh_token_hash="tok1", expires_at=datetime.utcnow() + timedelta(days=1))
    sess2 = UserSession(id=uuid4(), user_id=user2.id, refresh_token_hash="tok2", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess1, sess2])
    await db_session.commit()

    # Create tokens
    token1 = create_access_token(subject=user1.id, session_id=sess1.id)
    token2 = create_access_token(subject=user2.id, session_id=sess2.id)


    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 1. Initiate Private Conversation from User 1 to User 2
    res = await client.post(
        "/api/v1/conversations/private",
        json={"target_user_id": str(user2.id), "organization_id": str(org_id)},
        headers=headers1
    )
    assert res.status_code == 200, res.text
    conv_data = res.json()
    conv_id = conv_data["id"]
    assert conv_data["participant"]["id"] == str(user2.id)

    # 2. Initiate Private Conversation again (Deduplication check)
    res2 = await client.post(
        "/api/v1/conversations/private",
        json={"target_user_id": str(user2.id), "organization_id": str(org_id)},
        headers=headers1
    )
    assert res2.status_code == 200
    assert res2.json()["id"] == conv_id

    # 3. User 1 sends a direct message
    msg_res = await client.post(
        "/api/v1/messages",
        json={
            "conversation_id": conv_id,
            "content": "Hello User Two! Enterprise MindMesh DM test.",
            "message_type": "text"
        },
        headers=headers1
    )
    assert msg_res.status_code == 201, msg_res.text
    msg_data = msg_res.json()
    msg_id = msg_data["id"]
    assert msg_data["content"] == "Hello User Two! Enterprise MindMesh DM test."

    # 4. User 2 lists conversations and verifies unread count = 1
    c_list_res = await client.get(
        f"/api/v1/conversations?organization_id={org_id}",
        headers=headers2
    )
    assert c_list_res.status_code == 200
    c_list = c_list_res.json()
    assert len(c_list) == 1
    assert c_list[0]["unread_count"] == 1
    assert c_list[0]["last_message"]["content"] == "Hello User Two! Enterprise MindMesh DM test."

    # 5. User 2 fetches message history
    history_res = await client.get(
        f"/api/v1/messages/{conv_id}",
        headers=headers2
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 1
    assert history[0]["id"] == msg_id

    # 6. User 2 marks conversation as read
    read_res = await client.post(
        f"/api/v1/conversations/{conv_id}/read",
        headers=headers2
    )
    assert read_res.status_code == 200

    # Verify unread count is reset to 0
    c_list_res2 = await client.get(
        f"/api/v1/conversations?organization_id={org_id}",
        headers=headers2
    )
    assert c_list_res2.json()[0]["unread_count"] == 0

    # 7. User 1 edits their message
    edit_res = await client.patch(
        f"/api/v1/messages/{msg_id}",
        json={"content": "Updated message content!"},
        headers=headers1
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["edited"] is True
    assert edit_res.json()["content"] == "Updated message content!"

    # 8. Search messages
    search_res = await client.get(
        f"/api/v1/messages?query=Updated",
        headers=headers2
    )
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # 9. User 1 soft deletes their message
    del_res = await client.delete(
        f"/api/v1/messages/{msg_id}",
        headers=headers1
    )
    assert del_res.status_code == 200

    # Verify content replaced with deletion banner
    hist_after_del = await client.get(
        f"/api/v1/messages/{conv_id}",
        headers=headers2
    )
    assert hist_after_del.json()[0]["deleted"] is True
    assert hist_after_del.json()[0]["content"] == "This message was deleted"

@pytest.mark.asyncio
async def test_tenant_isolation_and_unauthorized_access(client, db_session: AsyncSession):
    user_a = User(id=uuid4(), email=f"usera_{uuid4().hex[:6]}@example.com", username=f"usera_{uuid4().hex[:6]}", hashed_password="h")
    user_b = User(id=uuid4(), email=f"userb_{uuid4().hex[:6]}@example.com", username=f"userb_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    org_a = Organization(id=uuid4(), name="Org A", slug=f"org-a-{uuid4().hex[:6]}", owner_id=user_a.id)
    org_b = Organization(id=uuid4(), name="Org B", slug=f"org-b-{uuid4().hex[:6]}", owner_id=user_b.id)
    mem_a = OrganizationMember(id=uuid4(), organization_id=org_a.id, user_id=user_a.id)
    mem_b = OrganizationMember(id=uuid4(), organization_id=org_b.id, user_id=user_b.id)
    db_session.add_all([org_a, org_b, mem_a, mem_b])
    await db_session.commit()

    sess_a = UserSession(id=uuid4(), user_id=user_a.id, refresh_token_hash="s_a", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess_a)
    await db_session.commit()

    token_a = create_access_token(subject=user_a.id, session_id=sess_a.id)

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Attempt to start DM with user_b who is not in Org A
    res = await client.post(
        "/api/v1/conversations/private",
        json={"target_user_id": str(user_b.id), "organization_id": str(org_a.id)},
        headers=headers_a
    )
    assert res.status_code == 403
