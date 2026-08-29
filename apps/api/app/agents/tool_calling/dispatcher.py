import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.executor import ToolExecutor
from app.agents.metrics import metrics_tracker

logger = logging.getLogger(__name__)

class ToolDispatcher:
    @staticmethod
    async def dispatch(
        tool_name: str,
        input_data: Dict[str, Any],
        context: SessionContext,
        db: AsyncSession
    ) -> Any:
        """Dispatches execution request to the ToolExecutor engine."""
        logger.info(f"ToolDispatcher: Dispatching tool '{tool_name}' for request {context.request_id}")
        
        # Record metric tool invocation
        metrics_tracker.record_tool_call(tool_name)
        
        # Execute tool
        return await ToolExecutor.execute(
            tool_name=tool_name,
            input_data=input_data,
            context=context,
            db=db
        )
