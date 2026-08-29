import uuid
import pytest
from app.ai.reasoner.models import (
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
    ReasoningMode,
    AnswerReadiness,
    AnswerContext
)
from app.ai.reasoner.strategy import ReasoningStrategySelector
from app.ai.reasoner.orchestrator import ContextOrchestrator
from app.ai.reasoner.engine import MindMeshReasoner

def test_strategy_selection():
    # Calculation
    s_calc = ReasoningStrategySelector.select_strategy("What percentage of tasks are overdue?")
    assert s_calc == ReasoningMode.CALCULATION

    # Temporal
    s_temp = ReasoningStrategySelector.select_strategy("What changed since last week?")
    assert s_temp == ReasoningMode.TEMPORAL

    # Causal
    s_causal = ReasoningStrategySelector.select_strategy("Why is Project Alpha delayed?")
    assert s_causal == ReasoningMode.CAUSAL

    # Comparison
    s_comp = ReasoningStrategySelector.select_strategy("Which project is further ahead?")
    assert s_comp == ReasoningMode.COMPARISON

    # Action Result
    s_act = ReasoningStrategySelector.select_strategy("Create task", action_results=[{"status": "SUCCEEDED"}])
    assert s_act == ReasoningMode.ACTION_RESULT

def test_direct_and_synthesis_reasoning():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    ev_set = {
        "items": [
            {"source_id": "101", "source_type": "DOCUMENT", "title": "Project Alpha Status", "content": "Project Alpha is active."}
        ]
    }

    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="What is the status of Project Alpha?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set=ev_set
    )

    res = ContextOrchestrator.orchestrate(req)
    assert res.reasoning_status == ReasoningStatus.READY
    assert res.answer_readiness == AnswerReadiness.READY
    assert len(res.supporting_evidence) == 1

def test_conflict_detection():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    ev_set = {
        "items": [
            {"source_id": "101", "title": "Doc A", "content": "The deadline is September 20."},
            {"source_id": "102", "title": "Doc B", "content": "The deadline is September 25."}
        ]
    }

    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="What is the project deadline?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set=ev_set
    )

    res = ContextOrchestrator.orchestrate(req)
    assert res.reasoning_status == ReasoningStatus.CONFLICTING_EVIDENCE
    assert res.answer_readiness == AnswerReadiness.CONFLICTING_EVIDENCE
    assert len(res.conflicting_evidence) > 0

def test_deterministic_calculation_reasoning():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    ev_set = {"items": [{"source_id": "1", "title": "Tasks", "content": "3 of 8 tasks are overdue."}]}
    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="What percentage of tasks are overdue?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set=ev_set
    )

    res = ContextOrchestrator.orchestrate(req)
    assert "percentage_overdue" in res.calculations
    assert res.calculations["percentage_overdue"] == 37.5

def test_insufficient_evidence_reasoning():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="Who caused the project delay?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set={"items": []}
    )

    res = ContextOrchestrator.orchestrate(req)
    assert res.reasoning_status == ReasoningStatus.INSUFFICIENT_EVIDENCE
    assert res.answer_readiness == AnswerReadiness.INSUFFICIENT_EVIDENCE

def test_action_result_reasoning_integration():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    act_results = [{"tool_call_id": "call_1", "status": "SUCCEEDED", "data": {"task_id": "t1"}}]
    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="Create task Fix Login",
        user_id=u_id,
        workspace_id=w_id,
        action_results=act_results
    )

    res = ContextOrchestrator.orchestrate(req)
    assert res.reasoning_status == ReasoningStatus.READY
    assert len(res.action_effects) == 1

def test_answer_context_handoff_contract():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    ev_set = {"items": [{"source_id": "101", "source_type": "DOCUMENT", "title": "Doc Alpha", "content": "Content"}]}
    req = ReasoningRequest(
        request_id=uuid.uuid4(),
        original_query="Tell me about Alpha",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set=ev_set
    )

    res, answer_ctx = MindMeshReasoner.orchestrate_reasoning(req)
    assert isinstance(answer_ctx, AnswerContext)
    assert answer_ctx.question == "Tell me about Alpha"
    assert len(answer_ctx.citations) == 1
    assert answer_ctx.answer_readiness == AnswerReadiness.READY
