from typing import Dict, List
from app.agents.planning.graph import ExecutionGraph, ExecutionNode
from app.agents.exceptions import AgentException

class PlanOptimizer:
    @staticmethod
    def optimize_and_validate(graph: ExecutionGraph) -> ExecutionGraph:
        """Validates graph for loops (DFS cycle detection) and optimizes scheduling."""
        # Cycle detection
        visited = {}  # None = unvisited, 0 = visiting, 1 = visited
        
        def has_cycle(node_id: str) -> bool:
            visited[node_id] = 0  # visiting
            node = graph.nodes.get(node_id)
            if node:
                for dep_id in node.dependencies:
                    state = visited.get(dep_id)
                    if state == 0:
                        return True  # cycle detected
                    elif state is None:
                        if has_cycle(dep_id):
                            return True
            visited[node_id] = 1  # visited
            return False

        for node_id in graph.nodes.keys():
            if node_id not in visited:
                if has_cycle(node_id):
                    raise AgentException(f"Circular dependency detected in execution plan involving node '{node_id}'.")
                    
        return graph
