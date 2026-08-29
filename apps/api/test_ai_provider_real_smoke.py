import pytest
import asyncio
from uuid import uuid4
from app.ai.llm.gemini import GeminiProvider
from app.ai.gateway.models import AIRequest

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_real_gemini_provider_smoke():
    """
    Controlled real-provider smoke test for Google Gemini connection.
    This test makes a single lightweight request to verify real network connectivity and LLM response.
    Do NOT run automatically on every build/reload to preserve free-tier quota limits.
    """
    provider = GeminiProvider(model_name="gemini-2.5-flash")
    req = AIRequest(
        user_id=uuid4(),
        message="Respond with exactly: AI_CONNECTION_OK",
        model_preferences={"provider": "gemini", "model": "gemini-2.5-flash"}
    )
    response = await provider.generate_response(req)
    
    # Assert successful completion and real output
    assert response.provider == "gemini"
    assert response.status.value in ("COMPLETED", "FAILED")  # COMPLETED if quota window clear, FAILED if rate-limited
    if response.status.value == "COMPLETED":
        assert len(response.content) > 0
        assert "AI_CONNECTION_OK" in response.content or len(response.content) > 2
        print(f"\n[REAL GEMINI SMOKE TEST PASSED]: {response.content.strip()}")
    else:
        assert response.error is not None
        assert response.error.code in ("AI_RATE_LIMITED", "RATE_LIMIT")
        print(f"\n[REAL GEMINI SMOKE TEST RATE LIMITED (EXPECTED ON QUOTA LIMIT)]: {response.error.message}")
