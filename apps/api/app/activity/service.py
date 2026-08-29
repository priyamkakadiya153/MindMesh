from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from .repository import ActivityRepository
from .models import ActivityLog

class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ActivityRepository(db)

    async def record_event(
        self, org_id: UUID, user_id: UUID, event_type: str,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None,
        entity_type: Optional[str] = None, entity_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> ActivityLog:
        return await self.repo.record(
            org_id=org_id,
            user_id=user_id,
            event_type=event_type,
            workspace_id=workspace_id,
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata
        )

    async def list_timeline(
        self, org_id: UUID, limit: int = 50, offset: int = 0,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None,
        event_type: Optional[str] = None
    ) -> List[ActivityLog]:
        return await self.repo.list_timeline(
            org_id=org_id,
            limit=limit,
            offset=offset,
            workspace_id=workspace_id,
            project_id=project_id,
            event_type=event_type
        )

    async def delete_old_activities(self, days: int = 30) -> int:
        return await self.repo.delete_older_than(days)
