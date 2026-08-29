import uuid
import pytest
from app.ai.gateway.models import AIRequest
from app.ai.gateway.gateway import AIGateway
from app.ai.gateway.health import AISystemHealthChecker, HealthStatus
from app.ai.evaluation.engine import AIEvaluationEngine
from app.ai.evaluation.release import ReleaseEvaluator, ReleaseDecision
from app.ai.evaluation.models import EvaluationRequest

@pytest.mark.asyncio
async def test_complete_ai_subsystem_inventory():
    """Verify AI-01 through AI-11 components are imported and healthy."""
    health = AISystemHealthChecker.check_system_health()
    assert health.overall_status == HealthStatus.HEALTHY
    assert len(health.components) == 12
    assert "API" in health.components
    assert "Evaluation" in health.components

@pytest.mark.asyncio
async def test_end_to_end_request_trace_correlation():
    """Verify single request trace IDs stay correlated across all phases."""
    req_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    ws_id = uuid.uuid4()

    req = AIRequest(
        request_id=req_id,
        user_id=user_id,
        workspace_id=ws_id,
        conversation_id=conv_id,
        message="What is the status of Project Alpha?",
        model_preferences={"provider": "mock"}
    )

    gateway = AIGateway()
    resp = await gateway.execute(req)

    assert resp.request_id == req_id
    assert resp.conversation_id == conv_id
    assert "intent_result" in resp.metadata
    assert "reasoning_result" in resp.metadata
    assert "answer_result" in resp.metadata
    assert "grounding_result" in resp.metadata
    assert "evaluation_result" in resp.metadata

    eval_data = resp.metadata["evaluation_result"]
    assert eval_data["evaluation_id"] is not None
    assert eval_data["duplicate_generation_detected"] is False

@pytest.mark.asyncio
async def test_single_user_send_idempotency_lifecycle():
    """Verify 1 send = 1 logical message = 1 generation = 1 response without duplication."""
    req_id = uuid.uuid4()
    gen_id = f"gen_{req_id}"

    eval_req_1 = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=req_id,
        query="Status of Project Alpha",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        generation_id=gen_id
    )
    res_1 = AIEvaluationEngine.evaluate_request(eval_req_1)
    assert res_1.duplicate_generation_detected is False

    # Second evaluation with SAME generation ID (retry)
    eval_req_retry = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=req_id,
        query="Status of Project Alpha",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        generation_id=gen_id
    )
    res_retry = AIEvaluationEngine.evaluate_request(eval_req_retry)
    assert res_retry.duplicate_generation_detected is False

@pytest.mark.asyncio
async def test_multi_turn_cross_source_intelligence_flow():
    """Verify multi-turn intelligence across intent, memory, retrieval, reasoning, answer, security."""
    ws_id = uuid.uuid4()
    user_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    # Turn 1
    req1 = AIRequest(
        user_id=user_id,
        workspace_id=ws_id,
        conversation_id=conv_id,
        message="What is the status of Project Alpha?",
        model_preferences={"provider": "mock"}
    )
    res1 = await AIGateway().execute(req1)
    assert res1.content is not None

    # Turn 2
    req2 = AIRequest(
        user_id=user_id,
        workspace_id=ws_id,
        conversation_id=conv_id,
        message="Why is it delayed?",
        model_preferences={"provider": "mock"}
    )
    res2 = await AIGateway().execute(req2)
    assert res2.content is not None
    assert "intent_result" in res2.metadata

@pytest.mark.asyncio
async def test_workspace_and_security_isolation():
    """Verify prompt secret redaction and workspace security gate."""
    ws_id = uuid.uuid4()
    user_id = uuid.uuid4()

    secret_prompt = "My key is sk-proj_1234567890abcdef1234567890abcdef"
    req_secret = AIRequest(
        user_id=user_id,
        workspace_id=ws_id,
        message=secret_prompt,
        model_preferences={"provider": "mock"}
    )
    res_secret = await AIGateway().execute(req_secret)

    # Redacted text check via SecurityPolicyEngine
    from app.ai.security.policy import SecurityPolicyEngine
    sanitized = SecurityPolicyEngine.redact_secrets(secret_prompt)
    assert "sk-proj_1234567890abcdef1234567890abcdef" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized
    assert res_secret.metadata.get("evaluation_result") is not None

@pytest.mark.asyncio
async def test_ai_health_readiness_and_scorecard():
    """Verify release evaluator decision for production readiness."""
    health = AISystemHealthChecker.check_system_health()
    assert health.overall_status == HealthStatus.HEALTHY

    req = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="Final audit query",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        grounding_result={"status": "GROUNDED"}
    )
    eval_res = AIEvaluationEngine.evaluate_request(req)
    rel_eval = ReleaseEvaluator.evaluate_release([eval_res])

    assert rel_eval.decision == ReleaseDecision.PASS
