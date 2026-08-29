import pytest
import asyncio
from uuid import uuid4

from app.core.database import AsyncSessionLocal, engine
from app.ai.llm.gemini import GeminiProvider
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from sqlalchemy import delete

@pytest.mark.asyncio
async def test_minimal_non_streaming_gemini_hi():
    """Test A: Minimal non-streaming Gemini call for 'hi'."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    from app.ai.gateway.models import AIRequest
    req = AIRequest(user_id=uuid4(), message="hi", model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"})
    res = await provider.generate_response(req)
    
    assert res.status.value == "COMPLETED"
    assert res.provider == "gemini"
    assert len(res.content) > 0
    assert "Here is the synthesized" not in res.content
    print(f"\n[REAL GEMINI NON-STREAMING HI ANSWER]: {res.content}")

@pytest.mark.asyncio
async def test_minimal_non_streaming_gemini_math():
    """Test B: Minimal non-streaming Gemini call for 'What is 2 + 2?'."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    from app.ai.gateway.models import AIRequest
    req = AIRequest(user_id=uuid4(), message="What is 2 + 2?", model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"})
    res = await provider.generate_response(req)
    
    assert res.status.value == "COMPLETED"
    assert "4" in res.content
    assert "Here is the synthesized" not in res.content
    print(f"\n[REAL GEMINI NON-STREAMING MATH ANSWER]: {res.content}")

@pytest.mark.asyncio
async def test_minimal_non_streaming_gemini_recursion():
    """Test C: Minimal non-streaming Gemini call for 'Explain recursion in one sentence.'."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    from app.ai.gateway.models import AIRequest
    req = AIRequest(user_id=uuid4(), message="Explain recursion in one sentence.", model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"})
    res = await provider.generate_response(req)
    
    assert res.status.value == "COMPLETED"
    assert len(res.content) > 0
    assert "Here is the synthesized" not in res.content
    print(f"\n[REAL GEMINI NON-STREAMING RECURSION ANSWER]: {res.content}")

@pytest.mark.asyncio
async def test_minimal_streaming_gemini_hi():
    """Test streaming Gemini call for 'hi'."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    from app.ai.gateway.models import AIRequest
    req = AIRequest(user_id=uuid4(), message="hi", model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"})
    
    events = []
    async for evt in provider.stream_response(req):
        events.append(evt)
        
    tokens = [e.content for e in events if e.type == "TOKEN"]
    full_text = "".join(tokens)
    assert len(full_text) > 0
    assert "Here is the synthesized" not in full_text
    print(f"\n[REAL GEMINI STREAMING HI ANSWER]: {full_text}")

@pytest.mark.asyncio
async def test_end_to_end_orchestrator_real_gemini():
    """Test complete MindMesh AI Orchestrator with real Gemini provider."""
    await engine.dispose()
    async with AsyncSessionLocal() as db_session:
        org_id = uuid4()
        ws_id = uuid4()
        user_id = uuid4()

        org = Organization(id=org_id, name="Real Gemini Org", slug=f"real-gem-{uuid4().hex[:6]}")
        db_session.add(org)
        await db_session.commit()

        ws = Workspace(id=ws_id, organization_id=org_id, name="Real Gemini WS", slug=f"real-gem-ws-{uuid4().hex[:6]}")
        db_session.add(ws)
        await db_session.commit()

        user = User(
            id=user_id,
            email=f"realgem_{uuid4().hex[:6]}@test.com",
            username=f"realgem_{uuid4().hex[:6]}",
            hashed_password="hash",
            current_organization_id=org_id,
            current_workspace_id=ws_id
        )
        db_session.add(user)
        await db_session.commit()

        orchestrator = MindMeshAIOrchestrator(db_session)
        events = []
        async for event in orchestrator.stream_execute(
            user_id=user_id,
            org_id=org_id,
            query="What is 2 + 2?",
            workspace_id=ws_id,
            provider="gemini",
            model="gemini-2.5-flash"
        ):
            events.append(event)

        tokens = [e["content"] for e in events if e.get("type") == "token"]
        full_text = "".join(tokens)
        assert "4" in full_text
        assert "Here is the synthesized" not in full_text
        print(f"\n[REAL ORCHESTRATOR STREAMING MATH ANSWER]: {full_text}")

        # Cleanup
        await db_session.execute(delete(Message).where(Message.organization_id == org_id))
        await db_session.execute(delete(Chat).where(Chat.organization_id == org_id))
        await db_session.execute(delete(User).where(User.id == user_id))
        await db_session.execute(delete(Workspace).where(Workspace.id == ws_id))
        await db_session.execute(delete(Organization).where(Organization.id == org_id))
        await db_session.commit()
    await engine.dispose()
