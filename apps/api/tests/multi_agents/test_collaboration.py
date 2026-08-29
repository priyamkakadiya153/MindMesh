import pytest
import uuid
from app.agents.collaboration.context import SharedContext
from app.agents.collaboration.delegation import DelegationEngine
from app.agents.collaboration.synchronization import ContextSynchronizer
from app.agents.collaboration.consensus import ConsensusFramework
from app.agents.collaboration.conflict import ConflictResolver
from app.agents.collaboration.aggregation import ResultAggregator
from app.agents.exceptions import AgentException

def test_delegation_engine():
    # Keyword checks
    assert DelegationEngine.delegate_task("please review this code") == "CodingAgent"
    assert DelegationEngine.delegate_task("verify security compliance policies") == "ComplianceAgent"
    
    # Fallback checks (least loaded)
    active_loads = {
        "ResearchAgent": 5,
        "KnowledgeAgent": 2,
        "WorkflowAgent": 1,
        "ReportingAgent": 3,
        "CodingAgent": 4
    }
    assert DelegationEngine.delegate_task("generic instructions", active_loads) == "WorkflowAgent"

@pytest.mark.asyncio
async def test_shared_context_and_synchronizer():
    ctx = SharedContext(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4()
    )
    sync = ContextSynchronizer()
    await sync.update_memory(ctx, "agent_token", "xyz")
    await sync.append_knowledge(ctx, {"id": "doc-1", "title": "Reference Guide"})
    
    assert ctx.memory["agent_token"] == "xyz"
    assert len(ctx.retrieved_knowledge) == 1

def test_consensus_verification():
    # Majority matches
    outputs = [
        {"status": "APPROVED", "agent": "A"},
        {"status": "APPROVED", "agent": "B"},
        {"status": "REJECTED", "agent": "C"}
    ]
    res = ConsensusFramework.verify_consensus(outputs, match_key="status")
    assert res["consensus"] is True
    assert res["majority_value"] == "APPROVED"
    assert res["votes"] == 2

    # Tie/No majority
    outputs_tie = [
        {"status": "APPROVED", "agent": "A"},
        {"status": "REJECTED", "agent": "B"}
    ]
    res_tie = ConsensusFramework.verify_consensus(outputs_tie, match_key="status")
    assert res_tie["consensus"] is False

def test_conflict_resolution():
    outputs = [
        {"status": "APPROVED", "confidence": 0.95},
        {"status": "REJECTED", "confidence": 0.40}
    ]
    resolved = ConflictResolver.resolve(outputs, match_key="status")
    assert resolved["resolved"] is True
    assert resolved["output"]["status"] == "APPROVED"

    # Tie triggers escalation
    outputs_tie = [
        {"status": "APPROVED", "confidence": 0.8},
        {"status": "REJECTED", "confidence": 0.8}
    ]
    with pytest.raises(AgentException) as exc_info:
        ConflictResolver.resolve(outputs_tie, match_key="status")
    assert "Escalation to Supervisor is required" in str(exc_info.value)

def test_result_aggregator():
    results = [
        {"synthesis": "Report A", "search_results": [{"id": "doc-1", "title": "First Reference"}]},
        {"synthesis": "Report B", "search_results": [{"id": "doc-1", "title": "Duplicate Reference"}]}
    ]
    aggregated = ResultAggregator.aggregate_results(results)
    
    assert "Report A\n\nReport B" in aggregated["synthesis"]
    # De-duplicated search citation checks
    assert len(aggregated["search_results"]) == 1
    assert len(aggregated["citations"]) == 1
    assert aggregated["citations"][0]["id"] == "doc-1"
