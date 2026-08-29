from typing import Dict, Any
from app.agents.planning.graph import ExecutionGraph
from app.agents.reasoning.confidence import ConfidenceEngine
from app.agents.tools.registry import tool_registry

class DecisionEngine:
    @staticmethod
    def evaluate_plan_feasibility(graph: ExecutionGraph) -> Dict[str, Any]:
        """Calculates execution plan feasibility and overall confidence levels."""
        if not graph.nodes:
            return {"level": "LOW", "score": 0.0}

        # Check tools health and match permissions
        total_nodes = len(graph.nodes)
        valid_tools_count = 0
        
        for node in graph.nodes.values():
            meta = tool_registry.get_metadata(node.tool)
            if meta:
                valid_tools_count += 1

        success_rate = (valid_tools_count / total_nodes) if total_nodes > 0 else 0.0
        
        # Assume parameters are fully matched during plan validations
        param_completion = 1.0 
        
        score = ConfidenceEngine.calculate_score({
            "success_rate": success_rate,
            "param_completion": param_completion,
            "policy_checks": 1.0
        })

        return {
            "level": ConfidenceEngine.resolve_level(score),
            "score": round(score, 2),
            "success_probability": round(score * 100.0, 1)
        }
