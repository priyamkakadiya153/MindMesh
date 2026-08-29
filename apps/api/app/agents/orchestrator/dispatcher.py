import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.runtime import agent_runtime
from app.agents.execution.graph import AgentExecutionNode

logger = logging.getLogger(__name__)

class MultiAgentDispatcher:
    @staticmethod
    async def dispatch_to_agent(
        node: AgentExecutionNode,
        context: SessionContext,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Dispatches an execution node to the central agent runtime coordinator."""
        logger.info(f"MultiAgentDispatcher: Dispatching step '{node.id}' to agent '{node.agent_name}'")
        
        # Executes using the existing runtime engine loader
        return await agent_runtime.execute(
            agent_id=node.agent_name,
            context=context,
            input_data=node.input_data,
            db=db
        )
