import logging
from app.memory.models import LongTermMemory

logger = logging.getLogger(__name__)

class MemoryPermissionPolicy:
    @staticmethod
    def can_access(memory: LongTermMemory, user_id: str) -> bool:
        """Enforces that User memory belongs to requesting user, while allowing shared scopes."""
        if memory.memory_type == "User":
            return memory.scope_key == user_id
        # Project, Organization, and Agent memory scopes are shareable if user is authorized in the organization context
        return True
