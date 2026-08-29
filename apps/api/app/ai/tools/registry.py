import logging
from typing import Dict, Any, List, Optional, Tuple
from app.ai.tools.models import (
    ToolDefinition,
    RiskLevel,
    ToolCapability,
    SideEffect
)

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Central Tool Registry managing schema registration, lookup, and validation."""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._init_native_tools()

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: ToolDefinition) -> ToolDefinition:
        self._tools[tool.tool_id] = tool
        logger.info(f"[ToolRegistry] Registered tool '{tool.tool_id}' ({tool.risk_level.value})")
        return tool

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def list_tools(self, risk_filter: Optional[RiskLevel] = None) -> List[ToolDefinition]:
        if risk_filter:
            return [t for t in self._tools.values() if t.risk_level == risk_filter]
        return list(self._tools.values())

    def validate_input(self, tool_id: str, parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        tool = self.get_tool(tool_id)
        if not tool:
            return False, f"Tool '{tool_id}' is not registered."

        schema = tool.input_schema
        for param_name, param_spec in schema.items():
            is_req = param_spec.get("required", False)
            if is_req and param_name not in parameters:
                return False, f"Missing required parameter '{param_name}' for tool '{tool_id}'."

            if param_name in parameters:
                val = parameters[param_name]
                expected_type = param_spec.get("type")
                if expected_type == "str" and not isinstance(val, str):
                    return False, f"Parameter '{param_name}' must be a string."
                elif expected_type == "int" and not isinstance(val, int):
                    return False, f"Parameter '{param_name}' must be an integer."
                elif expected_type == "bool" and not isinstance(val, bool):
                    return False, f"Parameter '{param_name}' must be a boolean."

                enum_vals = param_spec.get("enum")
                if enum_vals and val not in enum_vals:
                    return False, f"Parameter '{param_name}' value '{val}' not in allowed values: {enum_vals}."

        return True, None

    def _init_native_tools(self):
        """Pre-register native application tools."""
        # 1. SEARCH_PROJECTS
        self.register(ToolDefinition(
            tool_id="SEARCH_PROJECTS",
            name="Search Projects",
            description="Search projects in workspace",
            input_schema={"query": {"type": "str", "required": True}},
            output_schema={"projects": {"type": "list"}},
            risk_level=RiskLevel.LOW,
            permissions=["projects:read"],
            side_effects=SideEffect.READ_ONLY
        ))

        # 2. CREATE_TASK
        self.register(ToolDefinition(
            tool_id="CREATE_TASK",
            name="Create Task",
            description="Create a new task in project",
            input_schema={
                "title": {"type": "str", "required": True},
                "project_id": {"type": "str", "required": False},
                "priority": {"type": "str", "required": False, "enum": ["LOW", "MEDIUM", "HIGH", "URGENT"]},
                "assignee_id": {"type": "str", "required": False}
            },
            risk_level=RiskLevel.MEDIUM,
            permissions=["tasks:create"],
            side_effects=SideEffect.LOW_IMPACT_WRITE
        ))

        # 3. UPDATE_TASK
        self.register(ToolDefinition(
            tool_id="UPDATE_TASK",
            name="Update Task",
            description="Update an existing task",
            input_schema={
                "task_id": {"type": "str", "required": True},
                "title": {"type": "str", "required": False},
                "status": {"type": "str", "required": False},
                "assignee_id": {"type": "str", "required": False}
            },
            risk_level=RiskLevel.MEDIUM,
            permissions=["tasks:update"],
            side_effects=SideEffect.LOW_IMPACT_WRITE
        ))

        # 4. DELETE_PROJECT
        self.register(ToolDefinition(
            tool_id="DELETE_PROJECT",
            name="Delete Project",
            description="Permanently delete a project and all its data",
            input_schema={"project_id": {"type": "str", "required": True}},
            risk_level=RiskLevel.CRITICAL,
            permissions=["projects:delete"],
            side_effects=SideEffect.DESTRUCTIVE
        ))
