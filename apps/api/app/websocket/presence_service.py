from typing import Dict, Optional
from datetime import datetime
import json
import logging
from uuid import UUID

logger = logging.getLogger("mindmesh.presence")

class PresenceService:
    def __init__(self):
        # Cache user_id -> {"status": "online"|"away"|"busy"|"offline", "custom_status": str, "last_seen": ISOString}
        self.presence_map: Dict[str, dict] = {}

    def set_user_presence(self, user_id: str, status: str, custom_status: Optional[str] = None) -> dict:
        now_iso = datetime.utcnow().isoformat()
        info = {
            "user_id": user_id,
            "status": status,
            "custom_status": custom_status,
            "last_seen": now_iso
        }
        self.presence_map[user_id] = info
        return info

    def get_user_presence(self, user_id: str) -> dict:
        return self.presence_map.get(user_id, {
            "user_id": user_id,
            "status": "offline",
            "custom_status": None,
            "last_seen": datetime.utcnow().isoformat()
        })

    def mark_user_offline(self, user_id: str) -> dict:
        return self.set_user_presence(user_id, "offline")

presence_service = PresenceService()
