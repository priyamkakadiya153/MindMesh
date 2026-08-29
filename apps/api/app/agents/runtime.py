import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.registry import register_built_in_tools, tool_registry
from app.agents.registry import agent_registry
from app.agents.executor import AgentExecutionEngine
from app.agents.health import AgentHealthCheck

logger = logging.getLogger(__name__)

class AgentRuntime:
    def __init__(self):
        self.is_initialized = False

    async def initialize(self):
        """Initializes the Agent system, registering tools and example agents."""
        if self.is_initialized:
            return

        # 1. Register built-in tools
        register_built_in_tools()

        # 2. Import examples to trigger decorators and register example agents
        import importlib
        import app.agents.examples
        importlib.reload(app.agents.examples)

        self.is_initialized = True
        logger.info("AgentRuntime initialized successfully.")

    async def execute(
        self,
        agent_id: str,
        context: SessionContext,
        input_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Main execution entrypoint for running an agent."""
        if not self.is_initialized:
            await self.initialize()
        return await AgentExecutionEngine.run(agent_id, context, input_data, db)

    async def shutdown(self):
        """Clean up and clear registries."""
        tool_registry.clear()
        agent_registry.clear()
        self.is_initialized = False
        logger.info("AgentRuntime shut down.")

    async def reload(self):
        """Reload the runtime registries."""
        await self.shutdown()
        await self.initialize()

    async def health_check(self) -> Dict[str, Any]:
        """Runs diagnostics on registries and engine state."""
        return await AgentHealthCheck.perform_health_check()

# Global runtime instance
agent_runtime = AgentRuntime()
