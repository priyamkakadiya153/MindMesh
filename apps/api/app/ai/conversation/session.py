from typing import Dict, Any, Optional
from uuid import UUID

class SessionStateManager:
    @staticmethod
    def initialize_session(
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Creates a standard session state dictionary."""
        return {
            "active_workspace_id": str(workspace_id) if workspace_id else None,
            "active_project_id": str(project_id) if project_id else None,
            "preferences": preferences or {
                "temperature": 0.2,
                "max_tokens": 1000,
                "system_role": "default"
            }
        }
