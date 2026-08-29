from app.agents.tools.registry import tool_registry
from app.agents.exceptions import ToolNotFoundException

class ToolResolver:
    @staticmethod
    def resolve(tool_name: str):
        """Resolves tool name to executable function and its metadata."""
        func = tool_registry.get_tool(tool_name)
        metadata = tool_registry.get_metadata(tool_name)
        if not func or not metadata:
            raise ToolNotFoundException(f"Tool '{tool_name}' was not found in registry.")
        return func, metadata
