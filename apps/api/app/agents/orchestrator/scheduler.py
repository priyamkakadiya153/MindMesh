import logging
from typing import List, Dict, Optional

from app.agents.execution.graph import AgentExecutionNode

logger = logging.getLogger(__name__)

class MultiAgentScheduler:
    @staticmethod
    def schedule_nodes(
        nodes: List[AgentExecutionNode],
        policy: str = "capability-first",
        active_loads: Optional[Dict[str, int]] = None
    ) -> List[AgentExecutionNode]:
        """Schedules and sorts execution nodes based on policy configurations."""
        active_loads = active_loads or {}

        if policy == "priority-based":
            # Assume priority is in input_data or context, sort by description importance
            def get_priority_weight(node: AgentExecutionNode) -> int:
                priority = node.input_data.get("priority", "MEDIUM").upper()
                weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
                return weights.get(priority, 2)
            
            logger.info("MultiAgentScheduler: Sorting nodes by priority-based policy.")
            return sorted(nodes, key=get_priority_weight, reverse=True)

        elif policy == "least-loaded":
            # Sort nodes based on how many tasks the target agent is currently executing
            logger.info("MultiAgentScheduler: Sorting nodes by least-loaded policy.")
            return sorted(nodes, key=lambda n: active_loads.get(n.agent_name, 0))

        # Default capability-first / round-robin order
        return nodes
