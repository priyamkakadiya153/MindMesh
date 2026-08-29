import pytest
import uuid
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.base import BaseEntity
import app.models  # Register all SQLAlchemy models
from app.models.organization import Organization
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message

from app.ai.gateway.models import AIRequest, AIResponseStatus
from app.ai.gateway.service import AIService
from app.ai.chat.session import ChatSessionManager
from app.ai.chat.idempotency import IdempotencyManager

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        # Seed test org and user
        org = Organization(name="Lifecycle Test Org", slug=f"org-{uuid.uuid4().hex[:6]}")
        user = User(email=f"user-{uuid.uuid4().hex[:6]}@test.com", username=f"user_{uuid.uuid4().hex[:6]}", hashed_password="test", is_active=True)
        session.add_all([org, user])
        await session.commit()
        await session.refresh(org)
        await session.refresh(user)

        yield session, org, user

    await engine.dispose()

@pytest.mark.asyncio
async def test_idempotency_key_duplicate_prevention(db_session):
    session, org, user = db_session

    chat = await ChatSessionManager.get_or_create_session(
        db=session,
        organization_id=org.id,
        user_id=user.id,
        name="Idempotency Test"
    )

    idemp_key = f"key-{uuid.uuid4().hex}"
    ai_req1 = AIRequest(
        user_id=user.id,
        organization_id=org.id,
        conversation_id=chat.id,
        message="Test idempotency message",
        idempotency_key=idemp_key
    )

    # First execution succeeds
    resp1 = await AIService.process_chat(session, ai_req1)
    assert resp1.status == AIResponseStatus.COMPLETED

    # Verify user message saved
    msgs1 = await ChatSessionManager.list_messages(session, chat.id, org.id)
    user_msgs1 = [m for m in msgs1 if m.role == "user"]
    assert len(user_msgs1) == 1

    # Second execution with SAME idempotency key (simulating rapid double-click or network retry)
    ai_req2 = AIRequest(
        user_id=user.id,
        organization_id=org.id,
        conversation_id=chat.id,
        message="Test idempotency message",
        idempotency_key=idemp_key
    )
    resp2 = await AIService.process_chat(session, ai_req2)
    assert resp2.status == AIResponseStatus.COMPLETED

    # Verify NO duplicate user message was created
    msgs2 = await ChatSessionManager.list_messages(session, chat.id, org.id)
    user_msgs2 = [m for m in msgs2 if m.role == "user"]
    assert len(user_msgs2) == 1

@pytest.mark.asyncio
async def test_legitimate_repeated_messages(db_session):
    session, org, user = db_session

    chat = await ChatSessionManager.get_or_create_session(
        db=session,
        organization_id=org.id,
        user_id=user.id,
        name="Repeated Text Test"
    )

    # Turn 1: user sends "hi"
    req1 = AIRequest(
        user_id=user.id,
        organization_id=org.id,
        conversation_id=chat.id,
        message="hi",
        idempotency_key=f"turn1-{uuid.uuid4().hex}"
    )
    await AIService.process_chat(session, req1)

    # Turn 2: user sends "hi" again in separate turn
    req2 = AIRequest(
        user_id=user.id,
        organization_id=org.id,
        conversation_id=chat.id,
        message="hi",
        idempotency_key=f"turn2-{uuid.uuid4().hex}"
    )
    await AIService.process_chat(session, req2)

    msgs = await ChatSessionManager.list_messages(session, chat.id, org.id)
    user_msgs = [m for m in msgs if m.role == "user"]
    # Two distinct user messages must exist for separate user turns!
    assert len(user_msgs) == 2
    assert user_msgs[0].id != user_msgs[1].id

@pytest.mark.asyncio
async def test_retry_generation_no_user_message_duplication(db_session):
    session, org, user = db_session

    chat = await ChatSessionManager.get_or_create_session(
        db=session,
        organization_id=org.id,
        user_id=user.id,
        name="Retry Test"
    )

    # Create initial user message
    user_msg = await ChatSessionManager.save_user_message(
        db=session,
        chat_id=chat.id,
        sender_id=user.id,
        organization_id=org.id,
        content="Original question to retry"
    )
    await session.commit()

    # Retry generation for user message
    resp = await AIService.retry_generation(session, user_msg.id, user.id, org.id)
    assert resp.status == AIResponseStatus.COMPLETED

    # Verify only ONE user message remains
    msgs = await ChatSessionManager.list_messages(session, chat.id, org.id)
    user_msgs = [m for m in msgs if m.role == "user"]
    assert len(user_msgs) == 1

@pytest.mark.asyncio
async def test_regenerate_assistant_response(db_session):
    session, org, user = db_session

    chat = await ChatSessionManager.get_or_create_session(
        db=session,
        organization_id=org.id,
        user_id=user.id,
        name="Regenerate Test"
    )

    req = AIRequest(
        user_id=user.id,
        organization_id=org.id,
        conversation_id=chat.id,
        message="What is MindMesh?",
        idempotency_key=f"reg-{uuid.uuid4().hex}"
    )
    await AIService.process_chat(session, req)

    # Regenerate assistant response
    updated_msg = await ChatSessionManager.regenerate_assistant_response(
        db=session,
        conversation_id=chat.id,
        organization_id=org.id,
        new_content="Regenerated alternative answer for MindMesh.",
        model="gemini-2.0-flash"
    )
    assert updated_msg is not None
    assert updated_msg.content == "Regenerated alternative answer for MindMesh."
    assert updated_msg.msg_metadata.get("regenerated") is True

@pytest.mark.asyncio
async def test_conversation_switching_isolation(db_session):
    session, org, user = db_session

    chat_a = await ChatSessionManager.get_or_create_session(db=session, organization_id=org.id, user_id=user.id, name="Conv A")
    chat_b = await ChatSessionManager.get_or_create_session(db=session, organization_id=org.id, user_id=user.id, name="Conv B")

    await AIService.process_chat(session, AIRequest(user_id=user.id, organization_id=org.id, conversation_id=chat_a.id, message="Message for A", idempotency_key=f"a-{uuid.uuid4().hex}"))
    await AIService.process_chat(session, AIRequest(user_id=user.id, organization_id=org.id, conversation_id=chat_b.id, message="Message for B", idempotency_key=f"b-{uuid.uuid4().hex}"))

    msgs_a = await ChatSessionManager.list_messages(session, chat_a.id, org.id)
    msgs_b = await ChatSessionManager.list_messages(session, chat_b.id, org.id)

    assert all(m.chat_id == chat_a.id for m in msgs_a)
    assert all(m.chat_id == chat_b.id for m in msgs_b)
    assert len(msgs_a) > 0
    assert len(msgs_b) > 0
