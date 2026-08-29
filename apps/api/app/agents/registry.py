import logging
from typing import Dict, Type, List, Any, Optional
from app.agents.sdk.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}

    def register(self, agent_id: str, agent_cls: Type[BaseAgent]):
        """Registers a BaseAgent implementation class."""
        self._agents[agent_id] = agent_cls
        logger.info(f"Registered agent class '{agent_id}' ({agent_cls.__name__})")

    def get_agent(self, agent_id: str) -> Optional[Type[BaseAgent]]:
        """Retrieves an agent class by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """Lists metadata of all registered agent classes."""
        results = []
        for aid, cls in self._agents.items():
            meta = getattr(cls, "_agent_meta", {})
            results.append({
                "id": aid,
                "name": meta.get("name", cls.__name__),
                "description": meta.get("description", ""),
                "version": meta.get("version", "1.0.0"),
                "required_permissions": meta.get("required_permissions", [])
            })
        return results

    def clear(self):
        """Clears all agents in the registry."""
        self._agents.clear()

# Global registry instance
agent_registry = AgentRegistry()
