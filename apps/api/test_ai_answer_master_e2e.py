import uuid
import pytest
from app.ai.answer.models import (
    AnswerRequest,
    AnswerResult,
    AnswerType,
    CitationItem,
    SourceType
)
from app.ai.answer.planner import AnswerPlanner
from app.ai.answer.validator import AnswerValidator
from app.ai.answer.engine import AnswerGenerationEngine

def test_direct_and_explanation_answer_generation():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    ev_set = {
        "items": [
            {"source_id": "doc_101", "source_type": "DOCUMENT", "title": "Project Alpha Status", "content": "Project Alpha is active."}
        ]
    }
    reasoning = {
        "conclusion": "Project Alpha is active.",
        "answer_readiness": "READY"
    }

    req = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="What is the status of Project Alpha?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set=ev_set,
        reasoning_result=reasoning
    )

    res = AnswerGenerationEngine.generate_answer(req)
    assert res.answer_type in [AnswerType.DIRECT, AnswerType.EXPLANATION]
    assert len(res.citations) == 1
    assert "Project Alpha Status" in res.content

def test_action_result_answer_generation():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    # Successful action
    req_suc = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="Create task Fix Login",
        user_id=u_id,
        workspace_id=w_id,
        action_results=[{"tool_id": "CREATE_TASK", "status": "SUCCEEDED"}]
    )
    res_suc = AnswerGenerationEngine.generate_answer(req_suc)
    assert res_suc.answer_type == AnswerType.ACTION_RESULT
    assert "Done" in res_suc.content

    # Failed action
    req_fail = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="Delete project",
        user_id=u_id,
        workspace_id=w_id,
        action_results=[{"tool_id": "DELETE_PROJECT", "status": "FAILED"}]
    )
    res_fail = AnswerGenerationEngine.generate_answer(req_fail)
    assert res_fail.answer_type == AnswerType.ACTION_RESULT
    assert "Done" not in res_fail.content
    assert "unable" in res_fail.content.lower()

def test_conflict_and_uncertainty_answer_display():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    reasoning = {
        "conclusion": "Conflicting deadlines found.",
        "answer_readiness": "CONFLICTING_EVIDENCE",
        "conflicting_evidence": [{"field": "deadline", "values": ["Sept 20", "Sept 25"]}]
    }

    req = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="What is the deadline?",
        user_id=u_id,
        workspace_id=w_id,
        reasoning_result=reasoning
    )

    res = AnswerGenerationEngine.generate_answer(req)
    assert res.answer_type == AnswerType.CONFLICT
    assert "conflicting information" in res.content.lower()

def test_no_result_answer_generation():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    reasoning = {
        "conclusion": "No evidence found.",
        "answer_readiness": "INSUFFICIENT_EVIDENCE"
    }

    req = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="What is Project Zeta?",
        user_id=u_id,
        workspace_id=w_id,
        evidence_set={"items": []},
        reasoning_result=reasoning
    )

    res = AnswerGenerationEngine.generate_answer(req)
    assert res.answer_type == AnswerType.NO_RESULT
    assert "couldn't find" in res.content.lower()

def test_citation_validation_and_fake_citation_rejection():
    fake_cit = CitationItem(
        citation_id="fake_1",
        source_id="non_existent_id",
        label="Fake Source"
    )
    ev_items = [{"source_id": "real_id_101", "title": "Real Doc"}]

    valid, err = AnswerValidator.validate(
        content="Testing answer",
        citations=[fake_cit],
        evidence_items=ev_items
    )

    assert valid is False
    assert "unverified source_id" in err

def test_unsupported_claim_rejection():
    # Attempting to claim action success when action failed
    valid, err = AnswerValidator.validate(
        content="Done — I created task successfully.",
        citations=[],
        evidence_items=[],
        action_results=[{"status": "FAILED"}]
    )

    assert valid is False
    assert "action failure" in err.lower()

def test_comparison_answer_generation():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    reasoning = {
        "conclusion": "Project Beta is ahead.",
        "answer_readiness": "READY",
        "calculations": {"total_tasks": 8, "overdue_tasks": 3, "percentage_overdue": 37.5}
    }

    req = AnswerRequest(
        request_id=uuid.uuid4(),
        original_query="Which project is ahead vs Alpha?",
        user_id=u_id,
        workspace_id=w_id,
        reasoning_result=reasoning
    )

    res = AnswerGenerationEngine.generate_answer(req)
    assert res.answer_type == AnswerType.COMPARISON
    assert "37.5%" in res.content
