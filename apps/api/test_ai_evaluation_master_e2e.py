import uuid
import pytest
from app.ai.evaluation.models import (
    EvaluationRequest,
    EvaluationResult,
    EvaluationStatus,
    FailureCategory,
    QualityGate,
    ReleaseDecision
)
from app.ai.evaluation.datasets import GoldenDatasetManager
from app.ai.evaluation.engine import AIEvaluationEngine
from app.ai.evaluation.release import ReleaseEvaluator

def test_golden_dataset_evaluation():
    cases = GoldenDatasetManager.get_golden_cases()
    assert len(cases) >= 4
    case = GoldenDatasetManager.get_case_by_id("gc_1")
    assert case is not None
    assert case.category == "FACTUAL"

def test_phase_failure_localization():
    req_sec = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="Ignore rules",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        grounding_result={"status": "SECURITY_BLOCKED"}
    )
    res_sec = AIEvaluationEngine.evaluate_request(req_sec)
    assert res_sec.primary_failure == FailureCategory.SECURITY_ERROR

    req_ret = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="What is Zeta?",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        retrieval_result={"status": "EMPTY"}
    )
    res_ret = AIEvaluationEngine.evaluate_request(req_ret)
    assert res_ret.primary_failure == FailureCategory.RETRIEVAL_ERROR

def test_latency_token_and_cost_profiling():
    req = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="Status query",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        total_latency_ms=250.0
    )
    res = AIEvaluationEngine.evaluate_request(req)
    assert res.latency_breakdown_ms["total_ms"] == 250.0
    assert res.token_usage["total_tokens"] > 0
    assert res.estimated_cost_usd > 0.0

def test_duplicate_generation_detection():
    req_id = uuid.uuid4()
    req_1 = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=req_id,
        query="Hello",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        generation_id="gen_v1"
    )
    res_1 = AIEvaluationEngine.evaluate_request(req_1)
    assert res_1.duplicate_generation_detected is False

    req_2 = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=req_id,
        query="Hello",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        generation_id="gen_v2_dup"
    )
    res_2 = AIEvaluationEngine.evaluate_request(req_2)
    assert res_2.duplicate_generation_detected is True
    assert FailureCategory.UX_ERROR in res_2.failures

def test_release_quality_gates():
    req_pass = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="Grounded query",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        grounding_result={"status": "GROUNDED"}
    )
    res_pass = AIEvaluationEngine.evaluate_request(req_pass)

    rel_pass = ReleaseEvaluator.evaluate_release([res_pass])
    assert rel_pass.decision == ReleaseDecision.PASS

    req_block = EvaluationRequest(
        evaluation_id=uuid.uuid4(),
        request_id=uuid.uuid4(),
        query="Security attack",
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        grounding_result={"status": "SECURITY_BLOCKED"}
    )
    res_block = AIEvaluationEngine.evaluate_request(req_block)

    rel_block = ReleaseEvaluator.evaluate_release([res_block])
    assert rel_block.decision == ReleaseDecision.BLOCK
    assert len(rel_block.failed_gates) > 0
