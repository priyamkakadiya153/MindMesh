import logging
from typing import List, Dict, Any, Optional
from app.agents.registry import agent_registry
from app.agents.exceptions import AgentException

logger = logging.getLogger(__name__)

class DelegationEngine:
    @staticmethod
    def delegate_task(
        task_description: str,
        active_loads: Optional[Dict[str, int]] = None
    ) -> str:
        """Determines the most appropriate specialized agent class name for a task."""
        desc_lower = task_description.lower()
        active_loads = active_loads or {}

        # 1. Direct keyword capabilities mapping
        capabilities = {
            "PlannerAgent": ["plan", "schedule", "decompose", "sequence", "dependency"],
            "ResearchAgent": ["research", "retrieve", "synthesis", "find", "document"],
            "KnowledgeAgent": ["knowledge", "rag", "embedding", "semantic", "index"],
            "WorkflowAgent": ["workflow", "pipeline", "process", "orchestrate"],
            "ReportingAgent": ["report", "analytics", "dashboard", "metric", "chart"],
            "CodingAgent": ["code", "programming", "script", "develop", "review"],
            "ComplianceAgent": ["comply", "compliance", "policy", "legal", "regulation"],
            "QAAgent": ["qa", "testing", "validation", "verify", "quality"]
        }

        best_agent = None
        max_matches = 0

        for agent_name, kw_list in capabilities.items():
            matches = sum(1 for kw in kw_list if kw in desc_lower)
            if matches > max_matches:
                max_matches = matches
                best_agent = agent_name

        if best_agent:
            logger.info(f"DelegationEngine: Mapped task '{task_description}' to agent '{best_agent}' (score: {max_matches})")
            return best_agent

        # 2. Least-loaded agent policy if no clear capability match
        # Fallback to least loaded from registered agent list
        registered_agents = ["ResearchAgent", "KnowledgeAgent", "WorkflowAgent", "ReportingAgent", "CodingAgent"]
        
        # Sort registered agents by active loads
        sorted_by_load = sorted(registered_agents, key=lambda a: active_loads.get(a, 0))
        fallback_agent = sorted_by_load[0]
        
        logger.warning(
            f"DelegationEngine: No capability match for '{task_description}'. "
            f"Falling back to least-loaded agent: '{fallback_agent}'"
        )
        return fallback_agent
