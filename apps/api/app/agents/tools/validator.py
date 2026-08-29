from typing import Dict, Any
from app.agents.exceptions import ToolException

class ToolValidator:
    @staticmethod
    def validate_input(input_data: Dict[str, Any], schema: Dict[str, Any]):
        """Validates tool input data against its JSON Schema definition."""
        if not schema:
            return

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in input_data:
                raise ToolException(f"Missing required parameter '{field}' in tool inputs.")

        # Check properties and basic types
        properties = schema.get("properties", {})
        for key, val in input_data.items():
            if key not in properties:
                # We can choose to ignore extra fields or raise an error.
                # In standard API clients, it's safer to just ignore.
                continue

            prop_schema = properties[key]
            expected_type = prop_schema.get("type")

            if expected_type == "string" and not isinstance(val, str):
                raise ToolException(f"Parameter '{key}' must be a string, got {type(val).__name__}.")
            elif expected_type == "integer" and not isinstance(val, int):
                raise ToolException(f"Parameter '{key}' must be an integer, got {type(val).__name__}.")
            elif expected_type == "boolean" and not isinstance(val, bool):
                raise ToolException(f"Parameter '{key}' must be a boolean, got {type(val).__name__}.")
            elif expected_type == "number" and not (isinstance(val, int) or isinstance(val, float)):
                raise ToolException(f"Parameter '{key}' must be a number, got {type(val).__name__}.")
            elif expected_type == "array" and not isinstance(val, list):
                raise ToolException(f"Parameter '{key}' must be an array, got {type(val).__name__}.")
            elif expected_type == "object" and not isinstance(val, dict):
                raise ToolException(f"Parameter '{key}' must be an object, got {type(val).__name__}.")
