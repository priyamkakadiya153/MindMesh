import logging
from typing import Dict, Any, List
from app.agents.execution.graph import AgentExecutionGraph, AgentExecutionNode

logger = logging.getLogger(__name__)

class BranchingManager:
    @staticmethod
    def evaluate_branches(node: AgentExecutionNode, graph: AgentExecutionGraph):
        """Evaluates conditional paths and marks skipped branches in the graph."""
        if not node.condition_path:
            return

        # Check path: e.g. "status == APPROVED"
        # We can support simple boolean checking or status matching
        result_payload = node.result or {}
        val = result_payload.get(node.condition_path)

        # If condition evaluates to False or None, skip all downstream branches
        if not val or val == "REJECTED" or val == "FAILED":
            logger.warning(
                f"BranchingManager: Condition '{node.condition_path}' failed (value: {val}) at node '{node.id}'."
                " Skipping dependent downstream branches."
            )
            
            # Find and mark all recursive dependencies as SKIPPED
            def skip_downstream(parent_id: str):
                for child in graph.nodes.values():
                    if parent_id in child.dependencies and child.status == "PENDING":
                        child.status = "SKIPPED"
                        logger.info(f"BranchingManager: Marked dependent node '{child.id}' as SKIPPED.")
                        skip_downstream(child.id)

            skip_downstream(node.id)
