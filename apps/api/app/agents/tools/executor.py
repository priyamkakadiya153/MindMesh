import inspect
import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.resolver import ToolResolver
from app.agents.tools.validator import ToolValidator
from app.agents.permissions import AgentPermissionValidator
from app.agents.exceptions import PermissionDeniedException

logger = logging.getLogger(__name__)

class ToolExecutor:
    @staticmethod
    async def execute(
        tool_name: str,
        input_data: Dict[str, Any],
        context: SessionContext,
        db: AsyncSession
    ) -> Any:
        """Resolves, checks permissions, validates input, and runs the tool."""
        # 1. Resolve tool
        func, metadata = ToolResolver.resolve(tool_name)

        # 2. Validate permissions
        if metadata.permissions:
            is_allowed = await AgentPermissionValidator.validate_tool_permission(db, context, metadata.permissions)
            if not is_allowed:
                raise PermissionDeniedException(f"Permission denied: Execution of tool '{tool_name}' requires permissions {metadata.permissions}")

        # 3. Validate inputs
        ToolValidator.validate_input(input_data, metadata.input_schema)

        # 4. Run execution
        logger.info(f"Executing tool '{tool_name}' for request {context.request_id}")
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(context=context, db=db, **input_data)
            else:
                result = func(context=context, db=db, **input_data)
            return result
        except Exception as e:
            logger.error(f"Execution error on tool '{tool_name}': {str(e)}", exc_info=True)
            raise
