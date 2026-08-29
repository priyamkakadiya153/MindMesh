import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.models.chat import Chat
from app.models.message import Message
from app.ai.chat.session import ChatSessionManager

async def test_conversation_management_system():
    print("--- Starting MindMesh Phase 3.1 Conversation Management Test ---")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Test Organization, User, Workspace
        org = Organization(name="Conversation Org", slug=f"conv-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()
        await session.refresh(org)

        user = User(email=f"conv-user-{uuid.uuid4().hex[:6]}@acme.com", username=f"conv-user-{uuid.uuid4().hex[:6]}", hashed_password="hash")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        ws = Workspace(organization_id=org.id, name="AI Workspace", slug=f"ai-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        print("--> Created test Org, User, and Workspace.")

        # 2. Test Create Conversation
        conv1 = await ChatSessionManager.create_conversation(
            db=session,
            organization_id=org.id,
            user_id=user.id,
            workspace_id=ws.id,
            title="Q3 Strategy Discussion",
            description="Discussion on Q3 goals"
        )
        await session.commit()
        await session.refresh(conv1)
        assert conv1.id is not None
        assert conv1.title == "Q3 Strategy Discussion"
        print(f"--> Created Conversation 1 (ID: {conv1.id}, Title: {conv1.title}).")

        # Create Conversation 2
        conv2 = await ChatSessionManager.create_conversation(
            db=session,
            organization_id=org.id,
            user_id=user.id,
            workspace_id=ws.id,
            title="Architecture Review",
            description="System architecture notes"
        )
        await session.commit()
        await session.refresh(conv2)

        # 3. Test Add Messages
        msg1 = await ChatSessionManager.add_message(
            db=session,
            conversation_id=conv1.id,
            sender_id=user.id,
            organization_id=org.id,
            content="What are our primary infrastructure targets?",
            role="user"
        )
        await session.commit()
        print(f"--> Added User Message 1 (ID: {msg1.id}).")

        msg2 = await ChatSessionManager.add_message(
            db=session,
            conversation_id=conv1.id,
            sender_id=user.id,
            organization_id=org.id,
            content="Our target is 99.99% availability and hybrid RAG search.",
            role="assistant",
            model="gemini-2.0-flash"
        )
        await session.commit()
        print(f"--> Added Assistant Message 2 (ID: {msg2.id}).")

        # 4. Test List Messages
        messages = await ChatSessionManager.list_messages(session, conv1.id, org.id)
        assert len(messages) == 2
        assert messages[0].content == "What are our primary infrastructure targets?"
        assert messages[1].role == "assistant"
        print(f"--> Verified Message History Retrieval ({len(messages)} messages).")

        # 5. Test Pin Conversation
        pinned_conv = await ChatSessionManager.toggle_pin_conversation(session, conv1.id, org.id, user.id, is_pinned=True)
        await session.commit()
        assert pinned_conv.is_pinned is True
        print("--> Verified Conversation Pinning.")

        # 6. Test Rename Conversation
        renamed_conv = await ChatSessionManager.update_conversation(session, conv1.id, org.id, user.id, title="Q3 Architecture & Strategy")
        await session.commit()
        assert renamed_conv.title == "Q3 Architecture & Strategy"
        print("--> Verified Conversation Rename.")

        # 7. Test List & Pagination
        convs, total = await ChatSessionManager.list_conversations(
            db=session,
            organization_id=org.id,
            user_id=user.id,
            workspace_id=ws.id,
            page=1,
            limit=10
        )
        assert total == 2
        assert len(convs) == 2
        print(f"--> Verified Paginated List ({total} total conversations).")

        # 8. Test Search
        search_hits = await ChatSessionManager.search_conversations(
            db=session,
            organization_id=org.id,
            user_id=user.id,
            query="Architecture",
            workspace_id=ws.id
        )
        assert len(search_hits) >= 1
        print(f"--> Verified Title Search (Found {len(search_hits)} matching conversation).")

        # 9. Test Soft Delete
        deleted = await ChatSessionManager.soft_delete_conversation(session, conv2.id, org.id, user.id)
        await session.commit()
        assert deleted is True

        convs_after, total_after = await ChatSessionManager.list_conversations(
            db=session,
            organization_id=org.id,
            user_id=user.id,
            workspace_id=ws.id,
            page=1,
            limit=10
        )
        assert total_after == 1
        assert convs_after[0].id == conv1.id
        print("--> Verified Soft Delete (deleted_at set, excluded from active list).")

        print("=== MindMesh Phase 3.1 Conversation Management Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_conversation_management_system())
