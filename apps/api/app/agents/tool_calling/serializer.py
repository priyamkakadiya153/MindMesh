import json
from typing import Any

class ToolSerializer:
    @staticmethod
    def serialize_output(output: Any) -> str:
        """Serializes tool output results to clean string representations."""
        if output is None:
            return ""
        if isinstance(output, str):
            return output
        if isinstance(output, (int, float, bool)):
            return str(output)
        
        try:
            return json.dumps(output, ensure_ascii=False)
        except Exception:
            return str(output)
