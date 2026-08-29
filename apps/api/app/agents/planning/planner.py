import time
from typing import Optional
from app.agents.tools.registry import tool_registry
from app.agents.planning.graph import ExecutionGraph
from app.agents.planning.decomposition import TaskDecomposer
from app.agents.planning.dependency import DependencyResolver
from app.agents.planning.optimizer import PlanOptimizer
from app.agents.planning.validator import PlanValidator
from app.agents.planning.metrics import planning_metrics

class PlanningEngine:
    @staticmethod
    async def create_plan(goal: str, use_llm: bool = True) -> ExecutionGraph:
        """Decomposes goal and constructs a validated DAG ExecutionGraph."""
        start_time = time.time()

        # 1. Retrieve available tools
        tools = tool_registry.list_tools()
        tools_meta = [t.model_dump() for t in tools]

        # 2. Decompose into tasks
        tasks_data = await TaskDecomposer.decompose(goal, tools_meta, use_llm=use_llm)

        # 3. Resolve dependency mappings
        nodes = DependencyResolver.resolve_dependencies(tasks_data)

        # 4. Construct graph
        graph = ExecutionGraph()
        for node in nodes:
            graph.add_node(node)

        # 5. Run loop/cycle checks and scheduling optimizations
        PlanOptimizer.optimize_and_validate(graph)

        # 6. Pre-validate static input schemas
        PlanValidator.validate_plan_schemas(graph)

        # Record metrics
        duration_ms = (time.time() - start_time) * 1000.0
        planning_metrics.record_plan(len(graph.nodes), duration_ms)

        return graph
