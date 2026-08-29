from typing import Any, Dict, List, Optional

class ReflectionEngine:
    @staticmethod
    def evaluate(tool_name: str, result: Any, error: Optional[str] = None) -> Dict[str, Any]:
        """Reflects on tool execution results to verify completeness and quality."""
        if error:
            return {
                "success": False,
                "confidence_score": 0.0,
                "missing_data": ["Execution error occurred"],
                "recommend_retry": True,
                "details": f"Tool failed with error: {error}"
            }

        missing_data: List[str] = []
        confidence = 1.0

        # Check if result is None or empty
        if result is None:
            missing_data.append("No response data returned")
            confidence = 0.2
        elif isinstance(result, dict):
            # Check for generic failure flags or empty collections
            if not result:
                missing_data.append("Empty dictionary returned")
                confidence = 0.5
            elif "error" in result:
                missing_data.append(result["error"])
                confidence = 0.1
        elif isinstance(result, list) and not result:
            missing_data.append("Empty array returned")
            confidence = 0.5

        # Determine if retry is recommended based on low confidence
        recommend_retry = confidence < 0.5

        return {
            "success": confidence >= 0.5,
            "confidence_score": confidence,
            "missing_data": missing_data,
            "recommend_retry": recommend_retry,
            "details": "Result successfully verified" if confidence >= 0.8 else "Result is partial or empty"
        }
