from pydantic import BaseModel
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

class DashboardResponse(BaseModel):
    organization: dict
    workspace: Optional[dict] = None
    statistics: dict
    recent_projects: List[dict]
    recent_documents: List[dict]
    recent_chats: List[dict]
    notifications: List[dict]
    activity: List[dict]
    favorites: List[dict]
    ai_summary: dict
