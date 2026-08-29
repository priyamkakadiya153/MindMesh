import pytest
from app.agents.planning.graph import ExecutionNode
from app.agents.reasoning.recovery import RecoveryEngine
from app.agents.execution.retries import RetryPolicy

@pytest.mark.asyncio
async def test_recovery_strategy_selection():
    # 1. RETRY recommended if retries are below limit
    node_retry = ExecutionNode(id="step_1", tool="create_task", retries=0)
    strategy = RecoveryEngine.determine_strategy(node_retry, max_retries=2)
    assert strategy == "RETRY"

    # 2. ALTERNATIVE tool recommended if retries are exhausted and alternative maps
    node_alt = ExecutionNode(id="step_2", tool="search_documents", retries=2)
    strategy = RecoveryEngine.determine_strategy(node_alt, max_retries=2)
    assert strategy == "ALTERNATIVE"

    # 3. ABORT recommended if retries are exhausted and no alternative maps
    node_abort = ExecutionNode(id="step_3", tool="send_notification", retries=2)
    strategy = RecoveryEngine.determine_strategy(node_abort, max_retries=2)
    assert strategy == "ABORT"

@pytest.mark.asyncio
async def test_retry_policy_execution():
    call_count = 0
    
    async def mock_fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Temporary mock connection failure")
        return "Success"

    # Verify RetryPolicy intercepts error, waits, and succeeds on second attempt
    res = await RetryPolicy.execute_with_retry(
        mock_fail_then_succeed,
        retries=2,
        initial_delay=0.01
    )
    assert res == "Success"
    assert call_count == 2
