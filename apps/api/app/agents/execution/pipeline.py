from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tool_calling.dispatcher import ToolDispatcher
from app.agents.reasoning.reflection import ReflectionEngine

class ToolCallPipeline:
    @staticmethod
    async def run_single_tool(
        tool_name: str,
        input_data: Dict[str, Any],
        context: SessionContext,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Runs a single tool execution with reflection evaluation."""
        try:
            res = await ToolDispatcher.dispatch(tool_name, input_data, context, db)
            reflection = ReflectionEngine.evaluate(tool_name, res)
            return {
                "tool": tool_name,
                "result": res,
                "reflection": reflection
            }
        except Exception as e:
            reflection = ReflectionEngine.evaluate(tool_name, None, error=str(e))
            return {
                "tool": tool_name,
                "result": None,
                "reflection": reflection
            }
        
