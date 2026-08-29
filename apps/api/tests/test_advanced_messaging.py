import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.advanced_messaging import MessageReaction, PinnedMessage, FavoriteConversation, MessageDraft
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_reply_to_message_and_threads(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"thread_{uuid4().hex[:6]}@example.com", username=f"thread_{uuid4().hex[:6]}", hashed_password="h", first_name="Thread", last_name="User")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Thread Org", slug=f"thread-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    db_session.add_all([org, m])
    await db_session.commit()

    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="group", name="Thread Channel")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    db_session.add_all([conv, cm])
    await db_session.commit()

    # Parent message
    parent_msg = DirectMessage(
        id=uuid4(),
        conversation_id=conv_id,
        sender_id=user.id,
        organization_id=org_id,
        content="Parent Topic Discussion"
    )
    db_session.add(parent_msg)
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_t", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Reply to Message
    reply_res = await client.post(f"/api/v1/messages/{parent_msg.id}/reply", json={"content": "First Thread Reply"}, headers=headers)
    assert reply_res.status_code == 201, reply_res.text
    reply_data = reply_res.json()
    assert reply_data["reply_to_id"] == str(parent_msg.id)

    # 2. Verify parent message thread_count updated in DB
    p_stmt = select(DirectMessage).where(DirectMessage.id == parent_msg.id)
    p_res = await db_session.execute(p_stmt)
    updated_parent = p_res.scalar_one()
    assert updated_parent.thread_count == 1
    assert updated_parent.last_reply_at is not None

    # 3. Retrieve Thread Replies
    thread_res = await client.get(f"/api/v1/messages/{parent_msg.id}/thread", headers=headers)
    assert thread_res.status_code == 200
    assert len(thread_res.json()) == 1
    assert thread_res.json()[0]["content"] == "First Thread Reply"

@pytest.mark.asyncio
async def test_emoji_reactions_lifecycle(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"react_{uuid4().hex[:6]}@example.com", username=f"react_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="React Org", slug=f"react-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="group")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    msg = DirectMessage(id=uuid4(), conversation_id=conv_id, sender_id=user.id, organization_id=org_id, content="Awesome feature!")
    db_session.add_all([org, m, conv, cm, msg])
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_r", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Add Reaction
    react_res = await client.post(f"/api/v1/messages/{msg.id}/react", json={"emoji": "🚀"}, headers=headers)
    assert react_res.status_code == 200
    assert react_res.json()["emoji"] == "🚀"

    # Remove Reaction
    unreact_res = await client.delete(f"/api/v1/messages/{msg.id}/react?emoji=🚀", headers=headers)
    assert unreact_res.status_code == 200

@pytest.mark.asyncio
async def test_message_forwarding(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"fwd_{uuid4().hex[:6]}@example.com", username=f"fwd_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Fwd Org", slug=f"fwd-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    conv1 = Conversation(id=uuid4(), organization_id=org_id, type="group", name="Source")
    conv2 = Conversation(id=uuid4(), organization_id=org_id, type="group", name="Target 1")
    conv3 = Conversation(id=uuid4(), organization_id=org_id, type="group", name="Target 2")
    cm1 = ConversationMember(id=uuid4(), conversation_id=conv1.id, user_id=user.id, role="owner")
    cm2 = ConversationMember(id=uuid4(), conversation_id=conv2.id, user_id=user.id, role="owner")
    cm3 = ConversationMember(id=uuid4(), conversation_id=conv3.id, user_id=user.id, role="owner")
    orig_msg = DirectMessage(id=uuid4(), conversation_id=conv1.id, sender_id=user.id, organization_id=org_id, content="Important Bulletin")

    db_session.add_all([org, m, conv1, conv2, conv3, cm1, cm2, cm3, orig_msg])
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_fwd", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    fwd_res = await client.post(f"/api/v1/messages/{orig_msg.id}/forward", json={"target_conversation_ids": [str(conv2.id), str(conv3.id)]}, headers=headers)
    assert fwd_res.status_code == 201
    assert len(fwd_res.json()) == 2

@pytest.mark.asyncio
async def test_message_pinning(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"pin_{uuid4().hex[:6]}@example.com", username=f"pin_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Pin Org", slug=f"pin-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="group")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    msg = DirectMessage(id=uuid4(), conversation_id=conv_id, sender_id=user.id, organization_id=org_id, content="Pinned Announcement")
    db_session.add_all([org, m, conv, cm, msg])
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_pin", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Pin Message
    pin_res = await client.post(f"/api/v1/messages/{msg.id}/pin", headers=headers)
    assert pin_res.status_code == 200

    # Get Pinned Messages
    get_pins = await client.get(f"/api/v1/conversations/{conv_id}/pins", headers=headers)
    assert get_pins.status_code == 200
    assert len(get_pins.json()) == 1

    # Unpin Message
    unpin_res = await client.delete(f"/api/v1/messages/{msg.id}/pin", headers=headers)
    assert unpin_res.status_code == 200

@pytest.mark.asyncio
async def test_favorite_mute_and_drafts(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"fav_{uuid4().hex[:6]}@example.com", username=f"fav_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Fav Org", slug=f"fav-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="group")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    db_session.add_all([org, m, conv, cm])
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_fav", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Favorite
    fav_res = await client.post(f"/api/v1/conversations/{conv_id}/favorite", headers=headers)
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    # 2. Mute
    mute_res = await client.patch(f"/api/v1/conversations/{conv_id}/mute", json={"is_muted": True}, headers=headers)
    assert mute_res.status_code == 200
    assert mute_res.json()["is_muted"] is True

    # 3. Draft Auto-saving
    draft_res = await client.post("/api/v1/messages/drafts", json={"conversation_id": str(conv_id), "content": "Transient draft text..."}, headers=headers)
    assert draft_res.status_code == 200

    get_draft = await client.get(f"/api/v1/messages/drafts?conversation_id={conv_id}", headers=headers)
    assert get_draft.status_code == 200
    assert get_draft.json()["content"] == "Transient draft text..."
