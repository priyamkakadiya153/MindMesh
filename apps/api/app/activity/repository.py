from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc, and_
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from .models import ActivityLog

class ActivityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self, org_id: UUID, user_id: UUID, event_type: str,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None,
        entity_type: Optional[str] = None, entity_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> ActivityLog:
        log = ActivityLog(
            organization_id=org_id,
            user_id=user_id,
            event_type=event_type,
            workspace_id=workspace_id,
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action_metadata=metadata
        )

        self.session.add(log)
        await self.session.flush()
        return log

    async def list_timeline(
        self, org_id: UUID, limit: int = 50, offset: int = 0,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None,
        event_type: Optional[str] = None
    ) -> List[ActivityLog]:
        cond = [
            ActivityLog.organization_id == org_id,
            ActivityLog.is_active == True
        ]
        if workspace_id:
            cond.append(ActivityLog.workspace_id == workspace_id)
        if project_id:
            cond.append(ActivityLog.project_id == project_id)
        if event_type:
            cond.append(ActivityLog.event_type == event_type)

        stmt = (
            select(ActivityLog)
            .where(and_(*cond))
            .order_by(desc(ActivityLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def delete_older_than(self, days: int) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = delete(ActivityLog).where(ActivityLog.created_at < cutoff)
        res = await self.session.execute(stmt)
        return res.rowcount or 0
