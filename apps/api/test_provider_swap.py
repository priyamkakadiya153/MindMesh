import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.ai.llm.base import BaseLLMAdapter, UnifiedLLMResponse, LLMSettings
from app.ai.llm.factory import LLMProviderFactory
from typing import Optional, AsyncGenerator, Dict, Any

class CustomTestProvider(BaseLLMAdapter):
    """Custom Test Provider for Architectural Swap Verification."""
    def __init__(self, default_model: str = "test-model-v1"):
        super().__init__(provider_name="test_provider", default_model=default_model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> UnifiedLLMResponse:
        return UnifiedLLMResponse(
            content="TEST PROVIDER RESPONSE — SWAP VERIFIED SUCCESSFULLY",
            model="test-model-v1",
            provider="test_provider",
            prompt_tokens=25,
            completion_tokens=10,
            total_tokens=35,
            estimated_cost_usd=0.0,
            latency_ms=10,
            finish_reason="stop"
        )

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        settings: Optional[LLMSettings] = None
    ) -> AsyncGenerator[str, None]:
        yield "TEST "
        yield "PROVIDER "
        yield "STREAM "
        yield "RESPONSE"

    async def health_check(self) -> Dict[str, Any]:
        return {"provider": "test_provider", "status": "healthy"}

async def test_provider_swap():
    print("=== Starting MindMesh Phase 2.1 Provider Swap Architectural Test ===")

    # 1. Dynamically Register Custom Test Provider in Factory
    original_get_provider = LLMProviderFactory.get_provider

    def mock_get_provider(provider_name: str = "gemini", model_name: Optional[str] = None):
        if provider_name in ["test_provider", "swapped_provider"]:
            return CustomTestProvider(default_model=model_name or "test-model-v1")
        return original_get_provider(provider_name, model_name)

    LLMProviderFactory.get_provider = mock_get_provider

    async with AsyncSessionLocal() as session:
        # Create test DB records
        org = Organization(name="Swap Test Org", slug=f"swap-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Swap Workspace", slug=f"swap-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"swap_user_{u_id}@mindmesh.com",
            username=f"swap_user_{u_id}",
            first_name="Swap",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        # 2. Execute Orchestrator using Swapped Test Provider (Zero Code Changes in Orchestrator!)
        orchestrator = MindMeshAIOrchestrator(session)
        res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is the architecture status?",
            workspace_id=ws.id,
            provider="swapped_provider",
            model="test-model-v1"
        )

        assert "answer" in res
        assert "TEST PROVIDER RESPONSE" in res["answer"]
        print(f"--> [SUCCESS] Orchestrator executed with swapped provider without any core logic change!")
        print(f"    Answer received: '{res['answer']}'")

    print("=== Provider Swap Test Passed 100%! Provider Abstraction Architecture Verified. ===")

if __name__ == "__main__":
    asyncio.run(test_provider_swap())
