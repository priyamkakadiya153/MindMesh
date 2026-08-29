from typing import Dict, Any

class AgentHealthCheck:
    @staticmethod
    async def perform_health_check() -> Dict[str, Any]:
        """Runs diagnostics on the agent runtime."""
        # Check tool registry status
        from app.agents.tools.registry import tool_registry
        from app.agents.registry import agent_registry
        
        num_tools = len(tool_registry.list_tools())
        num_agents = len(agent_registry.list_agents())

        return {
            "status": "healthy" if num_tools > 0 else "degraded",
            "details": {
                "registered_agents_count": num_agents,
                "registered_tools_count": num_tools
            }
        }
