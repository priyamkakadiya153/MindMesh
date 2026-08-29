import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.ai.llm.base import LLMSettings, UnifiedLLMResponse
from app.ai.llm.adapters import GeminiLLMAdapter, OpenAILLMAdapter, ClaudeLLMAdapter, OllamaLLMAdapter, MockLLMAdapter
from app.ai.llm.factory import LLMProviderFactory
from app.ai.llm.registry import LLMModelRegistry, LLMUsageTracker
from app.ai.llm.models import WorkspaceAISetting
from sqlalchemy import select

async def test_llm_abstraction():
    print("--- Starting MindMesh Phase 3.6 Multi-LLM Provider Abstraction Test ---")

    # 1. Test Model Registry & Cost Tracking
    info = LLMModelRegistry.get_model_info("gemini-2.5-flash")
    assert info["provider"] == "gemini"
    assert info["context_window"] == 1000000

    cost = LLMUsageTracker.calculate_cost_usd("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0
    print("--> Verified LLMModelRegistry & Cost Calculation Engine.")

    # 2. Test Provider Factory & Adapters
    gemini_ad = LLMProviderFactory.get_provider("gemini", "gemini-2.5-flash")
    assert gemini_ad.provider_name == "gemini"

    openai_ad = LLMProviderFactory.get_provider("openai", "gpt-4o-mini")
    assert openai_ad.provider_name == "openai"

    claude_ad = LLMProviderFactory.get_provider("claude", "claude-3-5-sonnet")
    assert claude_ad.provider_name == "claude"

    ollama_ad = LLMProviderFactory.get_provider("ollama", "llama3")
    assert ollama_ad.provider_name == "ollama"

    mock_ad = LLMProviderFactory.get_provider("mock")
    assert mock_ad.provider_name == "mock"

    print("--> Verified Provider Factory Adapter Instantiation (Gemini, OpenAI, Claude, Ollama, Mock).")

    # 3. Test Response Normalization via Mock Adapter
    prompt_text = "What is the primary product of MindMesh?"
    resp = await mock_ad.generate(prompt_text, system_prompt="You are MindMesh assistant.")

    assert isinstance(resp, UnifiedLLMResponse)
    assert resp.content != ""
    assert resp.provider == "mock"
    assert resp.prompt_tokens > 0
    assert resp.completion_tokens > 0
    assert resp.total_tokens == (resp.prompt_tokens + resp.completion_tokens)
    assert resp.latency_ms >= 0
    print(f"--> Verified UnifiedLLMResponse Normalization ({resp.total_tokens} tokens, {resp.latency_ms}ms latency).")

    # 4. Test Failover Generation Chain
    settings = LLMSettings(provider="gemini", model="gemini-2.5-flash", fallback_provider="openai")
    failover_resp = await LLMProviderFactory.generate_with_failover("Test prompt", settings=settings)

    assert failover_resp.content != ""
    assert failover_resp.provider in ["gemini", "openai", "mock"]
    print(f"--> Verified LLMProviderFactory Failover Chain (Provider used: {failover_resp.provider}).")

    # 5. Test Workspace AI Settings DB Persistence
    async with AsyncSessionLocal() as session:
        org = Organization(name="LLM Test Org", slug=f"llm-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="LLM Test Workspace", slug=f"llm-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        ai_setting = WorkspaceAISetting(
            workspace_id=ws.id,
            organization_id=org.id,
            provider="gemini",
            model="gemini-2.5-pro",
            temperature=0.4,
            top_p=0.9,
            max_tokens=4096,
            fallback_provider="openai"
        )
        session.add(ai_setting)
        await session.commit()

        # Query back
        stmt = select(WorkspaceAISetting).where(WorkspaceAISetting.workspace_id == ws.id)
        persisted = (await session.execute(stmt)).scalar_one()

        assert persisted.provider == "gemini"
        assert persisted.model == "gemini-2.5-pro"
        assert persisted.temperature == 0.4
        assert persisted.max_tokens == 4096

        print("--> Verified WorkspaceAISetting Database Persistence.")

    print("=== MindMesh Phase 3.6 Multi-LLM Provider Abstraction Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_llm_abstraction())
