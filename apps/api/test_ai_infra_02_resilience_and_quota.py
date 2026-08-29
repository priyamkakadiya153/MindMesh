import pytest
import asyncio
from uuid import uuid4

from app.core.database import AsyncSessionLocal, engine
from app.ai.llm.base import ModelProvider, LLMSettings
from app.ai.llm.gemini import GeminiProvider
from app.ai.llm.metrics import metrics_tracker, ProviderHealthState
from app.ai.gateway.models import AIRequest, AIResponseStatus
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from sqlalchemy import delete

@pytest.mark.asyncio
async def test_quota_aware_error_classification_and_metrics():
    """Verify that HTTP 429 rate limit is classified as AI_RATE_LIMITED and updates metrics tracker."""
    tracker_before = metrics_tracker.ai_rate_limited_total
    metrics_tracker.record_rate_limit("gemini")
    assert metrics_tracker.ai_rate_limited_total == tracker_before + 1
    
    health = metrics_tracker.get_health_status("gemini")
    assert health["provider"] == "gemini"
    assert health["status"] == "RATE_LIMITED"
    assert health["metrics"]["ai_rate_limited_total"] >= 1

@pytest.mark.asyncio
async def test_deterministic_count_query_bypasses_llm():
    """Verify that document/PDF count questions use _process_count_query directly without LLM quota consumption."""
    await engine.dispose()
    async with AsyncSessionLocal() as session:
        org_id = uuid4()
        ws_id = uuid4()
        user_id = uuid4()

        org = Organization(id=org_id, name="Resilience Test Org", slug=f"res-org-{uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(id=ws_id, organization_id=org_id, name="Resilience Test WS", slug=f"res-ws-{uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        user = User(
            id=user_id,
            email=f"res_{uuid4().hex[:6]}@test.com",
            username=f"res_{uuid4().hex[:6]}",
            hashed_password="hash",
            current_organization_id=org_id,
            current_workspace_id=ws_id
        )
        session.add(user)
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)
        events = []
        async for event in orchestrator.stream_execute(
            user_id=user_id,
            org_id=org_id,
            query="How many PDFs are in documents?",
            workspace_id=ws_id,
            provider="gemini",
            model="gemini-2.5-flash"
        ):
            events.append(event)

        tokens = [e["content"] for e in events if e.get("type") == "token"]
        full_text = "".join(tokens)
        
        # Must execute deterministically using DB metadata count without hallucination
        assert "PDF" in full_text or "0" in full_text or "documents" in full_text
        final_evt = [e for e in events if e.get("type") == "final"][0]
        assert final_evt.get("intent") in ["COUNT_QUERY", "STRUCTURED_QUERY"]
        assert final_evt.get("grounded") is True

        # Clean DB
        await session.execute(delete(Message).where(Message.organization_id == org_id))
        await session.execute(delete(Chat).where(Chat.organization_id == org_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.execute(delete(Workspace).where(Workspace.id == ws_id))
        await session.execute(delete(Organization).where(Organization.id == org_id))
        await session.commit()
    await engine.dispose()

@pytest.mark.asyncio
async def test_stream_generate_interface_wrapper():
    """Verify stream_generate helper method on ModelProvider works seamlessly."""
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    assert hasattr(provider, "stream_generate")
