import pytest
from app.agents.tools.registry import register_built_in_tools
from app.agents.planning.planner import PlanningEngine
from app.agents.planning.graph import ExecutionGraph
from app.agents.exceptions import AgentException
from app.agents.planning.optimizer import PlanOptimizer

@pytest.mark.asyncio
async def test_rule_based_decomposition_create_project_and_tasks():
    register_built_in_tools()
    
    goal = "Create project 'Design Sprint' and add task 'Draw wireframes'"
    graph = await PlanningEngine.create_plan(goal, use_llm=False)
    
    assert isinstance(graph, ExecutionGraph)
    assert len(graph.nodes) == 2
    
    # Verify project node
    assert "step_1" in graph.nodes
    assert graph.nodes["step_1"].tool == "create_project"
    assert graph.nodes["step_1"].input["name"] == "Design Sprint"

    # Verify task node
    assert "step_task_1" in graph.nodes
    assert graph.nodes["step_task_1"].tool == "create_task"
    assert graph.nodes["step_task_1"].input["description"] == "Draw wireframes"
    
    # Check project reference injection
    assert graph.nodes["step_task_1"].input["project_id"] == "${step_1.result.id}"
    assert "step_1" in graph.nodes["step_task_1"].dependencies

@pytest.mark.asyncio
async def test_circular_dependency_detection():
    graph = ExecutionGraph()
    # Create steps with a loop: step_1 -> step_2 -> step_1
    from app.agents.planning.graph import ExecutionNode
    graph.add_node(ExecutionNode(id="step_1", tool="create_project", dependencies=["step_2"]))
    graph.add_node(ExecutionNode(id="step_2", tool="create_task", dependencies=["step_1"]))

    with pytest.raises(AgentException) as exc_info:
        PlanOptimizer.optimize_and_validate(graph)
        
    assert "Circular dependency detected" in str(exc_info.value)
