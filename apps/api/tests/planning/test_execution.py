import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.registry import register_built_in_tools
from app.agents.planning.graph import ExecutionGraph, ExecutionNode
from app.agents.execution.orchestrator import GraphOrchestrator
from app.agents.execution.rollback import RollbackManager
from tests.agents.test_sdk import seed_agent_test_data
from app.workspace.models import Workspace, WorkspaceMember

async def seed_workspace_test_data(db: AsyncSession):
    user, org = await seed_agent_test_data(db)
    ws = Workspace(
        organization_id=org.id,
        name="Planning Workspace",
        slug="planning-workspace",
        is_default=True
    )
    db.add(ws)
    await db.flush()
    
    wsm = WorkspaceMember(
        workspace_id=ws.id,
        user_id=user.id,
        role="MEMBER"
    )
    db.add(wsm)
    await db.commit()
    return user, org, ws

@pytest.mark.asyncio
async def test_dynamic_variable_injection_in_orchestrator(db_session: AsyncSession):
    register_built_in_tools()
    user, org, ws = await seed_workspace_test_data(db_session)
    
    # 1. Create a dummy graph: step_1 (create_project) -> step_2 (create_task)
    graph = ExecutionGraph()
    graph.add_node(ExecutionNode(
        id="step_1",
        tool="create_project",
        input={"name": "Sprint 5 Execution"},
        dependencies=[]
    ))
    graph.add_node(ExecutionNode(
        id="step_2",
        tool="create_task",
        input={
            "description": "Code Agent Engine",
            "project_id": "${step_1.result.id}"
        },
        dependencies=["step_1"]
    ))

    context = SessionContext(
        user_id=user.id,
        organization_id=org.id,
        workspace_id=ws.id,
        permissions=["*"],
        request_id=str(uuid.uuid4())
    )

    orchestrator = GraphOrchestrator(graph)
    results = await orchestrator.execute(context, db_session)
    
    # Verify both steps succeeded
    assert graph.nodes["step_1"].status == "COMPLETED"
    assert graph.nodes["step_2"].status == "COMPLETED"

    project_id = results["step_1"]["id"]
    task_project_id = results["step_2"]["project_id"]
    
    # Verify step_2 task_project_id was correctly substituted with the step_1 project ID
    assert task_project_id == project_id
    assert task_project_id is not None

@pytest.mark.asyncio
async def test_rollback_compensation_on_failure(db_session: AsyncSession):
    register_built_in_tools()
    user, org = await seed_agent_test_data(db_session)
    
    # Register compensation mock
    rollback_ran = False
    async def mock_rollback_func(arg_id):
        nonlocal rollback_ran
        rollback_ran = True
        
    rm = RollbackManager()
    rm.register_rollback("test_step", mock_rollback_func, 42)
    
    await rm.rollback()
    assert rollback_ran is True
