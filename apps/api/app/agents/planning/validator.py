import re
from typing import Dict, Any
from app.agents.planning.graph import ExecutionGraph
from app.agents.tools.registry import tool_registry
from app.agents.tools.validator import ToolValidator
from app.agents.exceptions import AgentException

class PlanValidator:
    @staticmethod
    def validate_plan_schemas(graph: ExecutionGraph):
        """Pre-validates that all tools exist and static inputs conform to schemas."""
        dep_pattern = re.compile(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\.[a-zA-Z0-9_-]+\s*\}")

        for node in graph.nodes.values():
            metadata = tool_registry.get_metadata(node.tool)
            if not metadata:
                raise AgentException(f"Validation failure: Proposed tool '{node.tool}' in plan step '{node.id}' not found in registry.")

            # Filter out dynamic variables before schema validation
            static_inputs = {}
            for k, val in node.input.items():
                if isinstance(val, str) and dep_pattern.search(val):
                    # Skip check since this will be resolved dynamically at execution time
                    continue
                static_inputs[k] = val

            # Validate static params
            try:
                ToolValidator.validate_input(static_inputs, metadata.input_schema)
            except Exception as e:
                raise AgentException(f"Validation failure in plan step '{node.id}' for tool '{node.tool}': {str(e)}")
