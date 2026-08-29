from typing import Dict, Any
from app.agents.planning.graph import ExecutionGraph

class FinalEvaluator:
    @staticmethod
    def evaluate_execution(graph: ExecutionGraph) -> Dict[str, Any]:
        """Evaluates final execution results of the graph."""
        nodes_summary = {}
        total_nodes = len(graph.nodes)
        completed_nodes = 0
        failed_nodes = 0

        for nid, node in graph.nodes.items():
            nodes_summary[nid] = {
                "tool": node.tool,
                "status": node.status,
                "has_result": node.result is not None,
                "error": node.error
            }
            if node.status == "COMPLETED":
                completed_nodes += 1
            elif node.status == "FAILED":
                failed_nodes += 1

        success = (completed_nodes == total_nodes) and (failed_nodes == 0)

        # Compute completion percentage
        completion_rate = (completed_nodes / total_nodes) if total_nodes > 0 else 0.0

        return {
            "success": success,
            "completion_rate": round(completion_rate * 100.0, 1),
            "total_steps": total_nodes,
            "completed_steps": completed_nodes,
            "failed_steps": failed_nodes,
            "steps": nodes_summary
        }
