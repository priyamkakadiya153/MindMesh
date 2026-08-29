import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.registry import register_built_in_tools
from app.agents.orchestrator.supervisor import SupervisorAgent
from app.agents.execution.graph import AgentExecutionGraph, AgentExecutionNode
from app.agents.execution.branching import BranchingManager
from app.agents.execution.recovery import MultiAgentRecoveryLoop
from app.agents.runtime import agent_runtime
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_supervisor_workflow_execution(db_session: AsyncSession):
    register_built_in_tools()
    await agent_runtime.initialize()
    user, org = await seed_agent_test_data(db_session)

    context = SessionContext(
        user_id=user.id,
        organization_id=org.id,
        permissions=["*"],
        request_id=str(uuid.uuid4())
    )

    supervisor = SupervisorAgent()
    # Runs QAAgent and ComplianceAgent in parallel and merges outputs using consensus checks
    res = await supervisor.run_workflow(
        goal="Run consensus validation tests and verify compliance status",
        context=context,
        db=db_session
    )
    
    assert res["status"] == "COMPLETED"
    assert "consensus_merge" in supervisor.results
    assert supervisor.results["consensus_merge"]["result"]["status"] == "APPROVED"
    assert res["metrics"]["consensus_verifications"] == 1

def test_branching_rejection_marks_downstream_skipped():
    graph = AgentExecutionGraph()
    # step_1 (rejection condition) -> step_2 (dependent task)
    graph.add_node(AgentExecutionNode(
        id="step_1",
        agent_name="ComplianceAgent",
        result={"status": "REJECTED"},
        condition_path="status"
    ))
    graph.add_node(AgentExecutionNode(
        id="step_2",
        agent_name="ReportingAgent",
        dependencies=["step_1"]
    ))
    
    BranchingManager.evaluate_branches(graph.nodes["step_1"], graph)
    
    assert graph.nodes["step_2"].status == "SKIPPED"

def test_recovery_loop_redelegation():
    node = AgentExecutionNode(
        id="step_fail",
        agent_name="ComplianceAgent",
        error="Connection Timeout",
        status="FAILED"
    )
    
    # 1. First failure recommendation is RETRY
    strategy = MultiAgentRecoveryLoop.determine_recovery(node, max_retries=1)
    assert strategy == "RETRY"
    
    # 2. Second failure recommendation triggers RE_DELEGATE
    strategy_exhausted = MultiAgentRecoveryLoop.determine_recovery(node, max_retries=1)
    assert strategy_exhausted == "RE_DELEGATE"
    assert node.agent_name == "QAAgent"
