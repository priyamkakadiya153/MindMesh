import math
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.timeline import TimelineEvent, TimelineRelation
from ..models.user import User
from ..workspace.models import WorkspaceMember
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember
from ..models.chat import Chat

logger = logging.getLogger(__name__)

class TimelineService:
    """Core service for recording, querying, and establishing lineage between

    organizational timeline events.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(
        self,
        organization_id: UUID,
        source_type: str,
        source_id: UUID,
        event_type: str,
        title: str,
        occurred_at: datetime,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        description: Optional[str] = None,
        importance: str = "MEDIUM",
        metadata_json: Optional[Dict[str, Any]] = None,
        supersedes_event_id: Optional[UUID] = None
    ) -> TimelineEvent:
        """Idempotently records a timeline event without duplicating records."""

        # Check existing idempotency by source_type + source_id + event_type
        stmt = select(TimelineEvent).where(
            TimelineEvent.source_type == source_type,
            TimelineEvent.source_id == source_id,
            TimelineEvent.event_type == event_type
        )
        res = await self.db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.title = title
            existing.description = description or existing.description
            existing.importance = importance
            existing.occurred_at = occurred_at
            existing.updated_at = datetime.utcnow()
            if metadata_json:
                merged_meta = existing.metadata_json or {}
                merged_meta.update(metadata_json)
                existing.metadata_json = merged_meta
            await self.db.flush()
            event = existing
        else:
            event = TimelineEvent(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
                event_type=event_type,
                importance=importance,
                title=title,
                description=description,
                source_type=source_type,
                source_id=source_id,
                occurred_at=occurred_at,
                metadata_json=metadata_json or {}
            )
            self.db.add(event)
            await self.db.flush()

        # Handle SUPERSEDES lineage link
        if supersedes_event_id:
            await self.link_events(
                source_event_id=event.id,
                target_event_id=supersedes_event_id,
                relation_type="SUPERSEDES"
            )

        return event

    async def link_events(
        self,
        source_event_id: UUID,
        target_event_id: UUID,
        relation_type: str,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> TimelineRelation:
        stmt = select(TimelineRelation).where(
            TimelineRelation.source_event_id == source_event_id,
            TimelineRelation.target_event_id == target_event_id,
            TimelineRelation.relation_type == relation_type
        )
        res = await self.db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return existing

        rel = TimelineRelation(
            source_event_id=source_event_id,
            target_event_id=target_event_id,
            relation_type=relation_type,
            metadata_json=metadata_json or {}
        )
        self.db.add(rel)
        await self.db.flush()
        return rel

    async def get_timeline_events(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
        importance: Optional[str] = None,
        search_query: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 30
    ) -> Dict[str, Any]:
        # 1. Organization Access Check
        org_member_stmt = select(OrganizationMember.id).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id
        )
        if not (await self.db.execute(org_member_stmt)).scalar_one_or_none():
            return {
                "events": [],
                "total_count": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            }

        # 2. Accessible Workspace IDs
        ws_stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None)
        )
        user_ws_ids = [r[0] for r in (await self.db.execute(ws_stmt)).all()]

        # 3. Authorized Chat / Conversation IDs
        auth_chat_ids = await self._get_authorized_chat_ids(user.id)

        # 4. Build Conditions
        conditions = [
            TimelineEvent.organization_id == organization_id,
            TimelineEvent.is_active == True,
            TimelineEvent.deleted_at.is_(None)
        ]

        if workspace_id:
            if workspace_id in user_ws_ids:
                conditions.append(TimelineEvent.workspace_id == workspace_id)
            else:
                return {"events": [], "total_count": 0, "page": page, "limit": limit, "total_pages": 0}
        else:
            if user_ws_ids:
                conditions.append(
                    or_(
                        TimelineEvent.workspace_id == None,
                        TimelineEvent.workspace_id.in_(user_ws_ids)
                    )
                )
            else:
                conditions.append(TimelineEvent.workspace_id == None)

        if project_id:
            conditions.append(TimelineEvent.project_id == project_id)

        if event_type and event_type != "all":
            conditions.append(TimelineEvent.event_type == event_type.upper())

        if importance and importance != "all":
            conditions.append(TimelineEvent.importance == importance.upper())

        if date_from:
            conditions.append(TimelineEvent.occurred_at >= date_from)
        if date_to:
            conditions.append(TimelineEvent.occurred_at <= date_to)

        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            conditions.append(
                or_(
                    TimelineEvent.title.ilike(sq),
                    TimelineEvent.description.ilike(sq)
                )
            )

        # Execute query
        stmt = (
            select(TimelineEvent)
            .where(and_(*conditions))
            .order_by(desc(TimelineEvent.occurred_at))
        )
        res = await self.db.execute(stmt)
        all_events = res.scalars().all()

        # RBAC filtering for chat/message source types
        filtered_events = []
        auth_chat_set = set(str(cid) for cid in auth_chat_ids)

        for ev in all_events:
            if ev.source_type in ["message", "conversation"]:
                meta = ev.metadata_json or {}
                chat_id = str(meta.get("chat_id") or ev.source_id)
                if chat_id not in auth_chat_set:
                    continue
            filtered_events.append(ev)

        total_count = len(filtered_events)
        total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
        offset = (page - 1) * limit
        page_events = filtered_events[offset : offset + limit]

        formatted = []
        for ev in page_events:
            meta = ev.metadata_json or {}
            deep_link = meta.get("deep_link") or self._build_deep_link(ev.source_type, str(ev.source_id), meta)

            formatted.append({
                "id": str(ev.id),
                "organization_id": str(ev.organization_id),
                "workspace_id": str(ev.workspace_id) if ev.workspace_id else None,
                "project_id": str(ev.project_id) if ev.project_id else None,
                "event_type": ev.event_type,
                "importance": ev.importance,
                "title": ev.title,
                "description": ev.description or "",
                "source_type": ev.source_type,
                "source_id": str(ev.source_id),
                "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "metadata": meta,
                "deep_link": deep_link
            })

        return {
            "events": formatted,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

    async def get_knowledge_evolution(
        self,
        organization_id: UUID,
        query: str,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """Returns chronological evolution sequence of decisions/events matching query."""
        stmt = (
            select(TimelineEvent)
            .where(
                TimelineEvent.organization_id == organization_id,
                TimelineEvent.is_active == True,
                TimelineEvent.deleted_at.is_(None),
                or_(
                    TimelineEvent.title.ilike(f"%{query}%"),
                    TimelineEvent.description.ilike(f"%{query}%")
                )
            )
            .order_by(TimelineEvent.occurred_at.asc())
        )
        res = await self.db.execute(stmt)
        events = res.scalars().all()

        evolution = []
        for ev in events:
            evolution.append({
                "id": str(ev.id),
                "title": ev.title,
                "description": ev.description,
                "event_type": ev.event_type,
                "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
                "source_type": ev.source_type,
                "source_id": str(ev.source_id)
            })

        return evolution

    async def _get_authorized_chat_ids(self, user_id: UUID) -> List[UUID]:
        chat_ids = set()
        stmt1 = select(Chat.id).where(Chat.user_id == user_id, Chat.deleted_at.is_(None))
        res1 = await self.db.execute(stmt1)
        for r in res1.scalars().all():
            chat_ids.add(r)

        stmt2 = select(Conversation.id).where(
            or_(
                Conversation.participant_one == user_id,
                Conversation.participant_two == user_id,
                Conversation.id.in_(
                    select(ConversationMember.conversation_id).where(
                        ConversationMember.user_id == user_id,
                        ConversationMember.deleted_at.is_(None)
                    )
                )
            ),
            Conversation.deleted_at.is_(None)
        )
        res2 = await self.db.execute(stmt2)
        for r in res2.scalars().all():
            chat_ids.add(r)

        return list(chat_ids)

    def _build_deep_link(self, source_type: str, source_id: str, metadata: Dict[str, Any]) -> str:
        if source_type in ["document", "file"]:
            return f"/files?preview={source_id}"
        elif source_type in ["message", "conversation"]:
            chat_id = metadata.get("chat_id") or source_id
            msg_id = metadata.get("message_id") or source_id
            return f"/direct-messages?chat={chat_id}&msg={msg_id}"
        elif source_type == "project":
            return f"/projects/{source_id}"
        elif source_type == "task":
            return f"/tasks/{source_id}"
        elif source_type == "decision":
            return f"/decisions/{source_id}"
        else:
            return "/dashboard"
