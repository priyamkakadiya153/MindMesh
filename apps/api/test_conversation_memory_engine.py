import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.ai.memory.models import ConversationSummary, ConversationMemory
from app.ai.memory.summarizer import SummarizationEngine
from app.ai.memory.manager import MemoryManager

async def test_memory_engine():
    print("--- Starting MindMesh Phase 3.9 Conversation Memory & AI Summarization Test ---")

    async with AsyncSessionLocal() as session:
        org = Organization(name="Memory Org", slug=f"mem-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Memory Workspace", slug=f"mem-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        email_str = f"memuser-{uuid.uuid4().hex[:6]}@mindmesh.ai"
        user = User(username=email_str, email=email_str, hashed_password="pw", current_organization_id=org.id, current_workspace_id=ws.id)
        session.add(user)
        await session.commit()

        chat = Chat(organization_id=org.id, workspace_id=ws.id, title="Memory Architecture Discussion")
        session.add(chat)
        await session.commit()

        # Add 3 conversation messages
        m1 = Message(chat_id=chat.id, sender_id=user.id, organization_id=org.id, role="user", content="We decided to use PostgreSQL for storing embeddings.")
        m2 = Message(chat_id=chat.id, sender_id=user.id, organization_id=org.id, role="assistant", content="Great choice! pgvector enables fast hybrid vector search.")
        m3 = Message(chat_id=chat.id, sender_id=user.id, organization_id=org.id, role="user", content="Next action item is deploying the API to Kubernetes.")
        session.add_all([m1, m2, m3])
        await session.commit()

        # 1. Test SummarizationEngine Generation
        summary_rec = await SummarizationEngine.generate_summary(
            db=session,
            conversation_id=chat.id,
            organization_id=org.id,
            workspace_id=ws.id,
            provider="mock"
        )

        assert summary_rec.id is not None
        assert summary_rec.conversation_id == chat.id
        assert summary_rec.summary != ""
        print("--> Verified SummarizationEngine Execution & DB Persistence.")

        # 2. Test MemoryManager Operations & Ranking
        mem1 = await MemoryManager.add_memory(
            db=session,
            workspace_id=ws.id,
            organization_id=org.id,
            content="Company policy requires MFA on all accounts.",
            importance=5,
            is_pinned=True
        )
        assert mem1.is_pinned is True

        mem2 = await MemoryManager.add_memory(
            db=session,
            workspace_id=ws.id,
            organization_id=org.id,
            content="Deploy API using kubectl apply.",
            importance=3,
            is_pinned=False
        )

        # Pin memory toggle
        updated_mem2 = await MemoryManager.pin_memory(session, mem2.id, is_pinned=True)
        assert updated_mem2.is_pinned is True

        # Memory Ranking query
        ranked_res = await MemoryManager.rank_and_select_memories(
            db=session,
            workspace_id=ws.id,
            organization_id=org.id,
            top_k=5
        )

        assert ranked_res["count"] > 0
        assert "[PINNED]" in ranked_res["memory_prompt_text"]
        print(f"--> Verified MemoryManager Ranking & Prompt Injection Context ({ranked_res['count']} memories selected).")

        # Delete memory
        del_success = await MemoryManager.delete_memory(session, mem1.id)
        assert del_success is True
        print("--> Verified Memory Deletion.")

    print("=== MindMesh Phase 3.9 Conversation Memory & AI Summarization Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_memory_engine())
