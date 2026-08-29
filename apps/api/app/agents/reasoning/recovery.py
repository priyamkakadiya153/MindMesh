import logging
from typing import Dict, Any, Optional
from app.agents.planning.graph import ExecutionNode

logger = logging.getLogger(__name__)

class RecoveryEngine:
    @staticmethod
    def determine_strategy(node: ExecutionNode, max_retries: int = 3) -> str:
        """Determines the recovery path when a node execution fails."""
        # 1. Check if retries are not exhausted
        if node.retries < max_retries:
            logger.info(f"RecoveryEngine: Recommending RETRY for node '{node.id}' (retries: {node.retries}/{max_retries})")
            return "RETRY"

        # 2. Check for alternative tools
        # For simplicity, map known tools to fallback options
        alternatives = {
            "search_documents": "retrieve_knowledge",
            "create_project": "request_help"
        }
        
        if node.tool in alternatives:
            alt_tool = alternatives[node.tool]
            logger.info(f"RecoveryEngine: Recommending ALTERNATIVE tool '{alt_tool}' for step '{node.id}'")
            return "ALTERNATIVE"

        # 3. Escalate / Abort
        logger.warning(f"RecoveryEngine: Retries exhausted and no alternative tool for '{node.tool}'. Recommending ABORT.")
        return "ABORT"
