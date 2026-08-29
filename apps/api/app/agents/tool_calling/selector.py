import logging
from typing import Optional, List, Dict, Any
from app.agents.tools.registry import tool_registry

logger = logging.getLogger(__name__)

class ToolSelector:
    @staticmethod
    def select_tool_for_task(task_description: str) -> Optional[str]:
        """Matches a task description to the most appropriate registered tool."""
        desc_lower = task_description.lower()
        tools = tool_registry.list_tools()

        # 1. Direct keyword check
        keywords = {
            "search_documents": ["search", "find", "query", "document", "retrieve"],
            "create_task": ["task", "todo", "assign", "schedule"],
            "send_notification": ["notify", "alert", "warn", "message", "send"],
            "create_project": ["project", "workspace", "folder"]
        }

        best_match = None
        max_matches = 0

        for tool_name, kw_list in keywords.items():
            matches = sum(1 for kw in kw_list if kw in desc_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = tool_name

        if best_match and max_matches > 0:
            logger.info(f"ToolSelector: Matched '{task_description}' to tool '{best_match}' (score: {max_matches})")
            return best_match

        # 2. Fallback to direct name checks
        for t in tools:
            if t.name in desc_lower:
                return t.name

        # Default to document search if description is generic
        return "search_documents"
