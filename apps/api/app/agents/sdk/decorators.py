from typing import Callable, Type, List, Dict, Any
from app.agents.registry import agent_registry
from app.agents.tools.registry import tool_registry
from app.agents.tools.metadata import ToolMetadata

def agent(name: str, description: str, version: str = "1.0.0", required_permissions: List[str] = None):
    """Decorator to register an agent class in the global registry."""
    def decorator(cls: Type):
        cls._agent_meta = {
            "name": name,
            "description": description,
            "version": version,
            "required_permissions": required_permissions or []
        }
        agent_id = cls.__name__.lower().replace("agent", "")
        agent_registry.register(agent_id, cls)
        return cls
    return decorator

def tool(
    name: str,
    description: str,
    version: str = "1.0.0",
    permissions: List[str] = None,
    input_schema: Dict[str, Any] = None,
    output_schema: Dict[str, Any] = None
):
    """Decorator to register a tool function in the global registry."""
    def decorator(func: Callable):
        meta = ToolMetadata(
            name=name,
            description=description,
            version=version,
            permissions=permissions or [],
            input_schema=input_schema or {},
            output_schema=output_schema or {}
        )
        tool_registry.register(name, func, meta)
        return func
    return decorator
