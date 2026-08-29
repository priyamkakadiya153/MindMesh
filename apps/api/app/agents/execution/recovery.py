import logging
from typing import Dict, Any, Optional
from app.agents.execution.graph import AgentExecutionNode
from app.agents.collaboration.delegation import DelegationEngine

logger = logging.getLogger(__name__)

class MultiAgentRecoveryLoop:
    @staticmethod
    def determine_recovery(node: AgentExecutionNode, max_retries: int = 2) -> str:
        """Determines recovery path: RETRY, RE_DELEGATE, or ABORT."""
        if node.error and "PermissionDenied" in node.error:
            logger.warning(f"MultiAgentRecoveryLoop: Permission issue at node '{node.id}'. Aborting immediately.")
            return "ABORT"

        current_retries = getattr(node, "_retry_count", 0)
        if current_retries < max_retries:
            node._retry_count = current_retries + 1
            logger.info(f"MultiAgentRecoveryLoop: Recommending RETRY for node '{node.id}' (retries: {node._retry_count}/{max_retries})")
            return "RETRY"

        # If retries are exhausted, try delegation to an alternative agent type
        fallback_agents = {
            "ComplianceAgent": "QAAgent",
            "ResearchAgent": "KnowledgeAgent"
        }
        if node.agent_name in fallback_agents:
            alt_agent = fallback_agents[node.agent_name]
            logger.info(f"MultiAgentRecoveryLoop: Re-delegating task from '{node.agent_name}' to '{alt_agent}' for step '{node.id}'")
            node.agent_name = alt_agent
            node._retry_count = 0  # reset retries for alternative
            return "RE_DELEGATE"

        logger.error(f"MultiAgentRecoveryLoop: All recovery options exhausted for node '{node.id}'. Aborting plan.")
        return "ABORT"
