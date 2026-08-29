import uuid
import pytest
from app.ai.tools.models import (
    ToolDefinition,
    ActionRequest,
    ActionPlan,
    ActionStep,
    RiskLevel,
    SideEffect,
    ExecutionStatus
)
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.executor import ActionExecutionEngine
from app.ai.knowledge.graph_service import KnowledgeGraphService

def test_tool_registration_and_schema_validation():
    registry = ToolRegistry.get_instance()
    tool = registry.get_tool("CREATE_TASK")
    assert tool is not None
    assert tool.risk_level == RiskLevel.MEDIUM

    # Valid input
    valid, err = registry.validate_input("CREATE_TASK", {"title": "Fix Login"})
    assert valid is True
    assert err is None

    # Missing required field
    valid_missing, err_missing = registry.validate_input("SEARCH_PROJECTS", {})
    assert valid_missing is False
    assert "Missing required parameter" in err_missing

    # Type mismatch
    valid_type, err_type = registry.validate_input("CREATE_TASK", {"title": 12345})
    assert valid_type is False
    assert "must be a string" in err_type

def test_read_only_tool_execution():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    req = ActionRequest(
        request_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        user_id=u_id,
        workspace_id=w_id,
        intent="SEARCH",
        action_type="SEARCH_PROJECTS",
        parameters={"query": "Alpha"}
    )

    plan = ActionExecutionEngine.plan_action(req)
    assert plan.confirmation_required is False
    assert plan.status == ExecutionStatus.AUTHORIZED

    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id,
        user_permissions=["projects:read"]
    )

    assert exec_plan.status == ExecutionStatus.SUCCEEDED
    assert len(results) == 1
    assert results[0].status == ExecutionStatus.SUCCEEDED

def test_high_risk_action_confirmation_policy():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    req = ActionRequest(
        request_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        user_id=u_id,
        workspace_id=w_id,
        intent="DELETE",
        action_type="DELETE_PROJECT",
        parameters={"project_id": str(uuid.uuid4())}
    )

    plan = ActionExecutionEngine.plan_action(req)
    assert plan.confirmation_required is True
    assert plan.status == ExecutionStatus.WAITING_CONFIRMATION
    assert plan.confirmation_prompt is not None

    # Executing without confirmation fails/blocks
    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id,
        user_permissions=["projects:delete"]
    )
    assert exec_plan.status == ExecutionStatus.WAITING_CONFIRMATION

    # Executing with valid confirmation_id succeeds
    exec_plan2, results2 = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id,
        user_permissions=["projects:delete"],
        confirmation_id=plan.confirmation_id
    )
    assert exec_plan2.status == ExecutionStatus.SUCCEEDED
    assert len(results2) == 1

def test_server_side_authorization_check():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    req = ActionRequest(
        request_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        user_id=u_id,
        workspace_id=w_id,
        intent="DELETE",
        action_type="DELETE_PROJECT",
        parameters={"project_id": str(uuid.uuid4())}
    )

    plan = ActionExecutionEngine.plan_action(req)

    # User lacks "projects:delete" permission
    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id,
        user_permissions=["projects:read"],
        confirmation_id=plan.confirmation_id
    )

    assert exec_plan.status == ExecutionStatus.FAILED
    assert len(results) == 1
    assert "Permission denied" in results[0].error

def test_action_execution_idempotency_and_verification():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()
    idemp_key = f"idemp_{uuid.uuid4()}"

    req = ActionRequest(
        request_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        user_id=u_id,
        workspace_id=w_id,
        intent="CREATE",
        action_type="CREATE_TASK",
        parameters={"title": "Idempotent Task"}
    )

    plan = ActionExecutionEngine.plan_action(req)
    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id,
        idempotency_key=idemp_key
    )
    assert exec_plan.status == ExecutionStatus.SUCCEEDED

    # Re-run with same idempotency key returns cached result
    plan2 = ActionExecutionEngine.plan_action(req)
    exec_plan2, results2 = ActionExecutionEngine.execute_plan(
        plan2,
        user_id=u_id,
        workspace_id=w_id,
        idempotency_key=idemp_key
    )
    assert exec_plan2.status == ExecutionStatus.SUCCEEDED
    assert results2[0].tool_call_id == results[0].tool_call_id

def test_multi_step_action_execution():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    s1 = ActionStep(
        step_id="step_1",
        tool_id="CREATE_TASK",
        action="Create Task",
        target="Task",
        parameters={"title": "Multi Step Task"}
    )
    s2 = ActionStep(
        step_id="step_2",
        tool_id="UPDATE_TASK",
        action="Update Task",
        target="Task",
        parameters={"task_id": str(uuid.uuid4()), "status": "IN_PROGRESS"}
    )

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        steps=[s1, s2],
        status=ExecutionStatus.AUTHORIZED
    )

    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id
    )

    assert exec_plan.status == ExecutionStatus.SUCCEEDED
    assert len(results) == 2

def test_loop_detection_and_recursion_protection():
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    # Plan with duplicate tool calls
    s1 = ActionStep(step_id="step_1", tool_id="CREATE_TASK", action="Create Task", target="Task", parameters={"title": "T1"})
    s2 = ActionStep(step_id="step_2", tool_id="CREATE_TASK", action="Create Task", target="Task", parameters={"title": "T2"})

    plan = ActionPlan(
        plan_id=uuid.uuid4(),
        steps=[s1, s2],
        status=ExecutionStatus.AUTHORIZED
    )

    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id
    )

    assert exec_plan.status == ExecutionStatus.FAILED
    assert "loop detected" in results[1].error.lower()

def test_action_audit_logging():
    logs = ActionExecutionEngine.get_audit_logs()
    assert len(logs) > 0
    assert logs[0].action_type is not None

def test_action_result_graph_and_memory_update():
    graph = KnowledgeGraphService.get_instance()
    u_id = uuid.uuid4()
    w_id = uuid.uuid4()

    task_title = f"Graph Linked Task {uuid.uuid4()}"
    req = ActionRequest(
        request_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        user_id=u_id,
        workspace_id=w_id,
        intent="CREATE",
        action_type="CREATE_TASK",
        parameters={"title": task_title}
    )

    plan = ActionExecutionEngine.plan_action(req)
    exec_plan, results = ActionExecutionEngine.execute_plan(
        plan,
        user_id=u_id,
        workspace_id=w_id
    )

    assert exec_plan.status == ExecutionStatus.SUCCEEDED
    # Verify entity added to KnowledgeGraph
    nbrs = graph.get_neighbors(uuid.uuid4(), workspace_id=w_id)
    assert isinstance(nbrs, list)
