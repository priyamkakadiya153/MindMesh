from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from .aggregator import DashboardAggregator
from .cache import export_cache as cache
from ..organizations.repository import OrganizationRepository
from ..workspace.repository import WorkspaceRepository
from ..projects.repository import ProjectRepository
from ..notifications.service import NotificationService
from ..activity.service import ActivityService
from ..favorites.service import FavoriteService
from ..recent.service import RecentItemService
from ..models.document import Document
from ..models.chat import Chat
from sqlalchemy import select, desc

import asyncio

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.aggregator = DashboardAggregator(db)
        self.org_repo = OrganizationRepository()
        self.ws_repo = WorkspaceRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.notif_service = NotificationService(db)
        self.act_service = ActivityService(db)
        self.fav_service = FavoriteService(db)
        self.recent_service = RecentItemService(db)

    async def _fetch_docs(self, org_id: UUID, workspace_id: Optional[UUID]):
        stmt_doc = (
            select(Document)
            .where(Document.organization_id == org_id, Document.is_active == True)
        )
        if workspace_id:
            stmt_doc = stmt_doc.where(Document.workspace_id == workspace_id)
        stmt_doc = stmt_doc.order_by(desc(Document.created_at)).limit(5)
        return (await self.db.execute(stmt_doc)).scalars().all()

    async def _fetch_chats(self, org_id: UUID, workspace_id: Optional[UUID]):
        stmt_chat = (
            select(Chat)
            .where(Chat.organization_id == org_id, Chat.is_active == True)
        )
        if workspace_id:
            stmt_chat = stmt_chat.where(Chat.workspace_id == workspace_id)
        stmt_chat = stmt_chat.order_by(desc(Chat.created_at)).limit(5)
        return (await self.db.execute(stmt_chat)).scalars().all()

    async def get_dashboard(self, user_id: UUID, org_id: UUID, workspace_id: Optional[UUID] = None) -> dict:
        cache_key = f"dashboard:{org_id}:{user_id}:{workspace_id}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        org = await self.org_repo.get_organization(self.db, org_id)
        org_data = {"id": str(org.id), "name": org.name, "slug": org.slug} if org else {}

        ws_data = None
        if workspace_id:
            try:
                ws = await self.ws_repo.get(workspace_id, org_id)
                if ws:
                    ws_data = {"id": str(ws.id), "name": ws.name, "slug": ws.slug}
            except Exception:
                pass

        try:
            stats = await self.aggregator.aggregate_stats(org_id, workspace_id)
        except Exception:
            stats = {
                "workspaces_count": 0, "projects_count": 0, "projects_indexed_count": 0,
                "projects_pending_count": 0, "documents_count": 0, "documents_indexed_count": 0,
                "chunks_count": 0, "chats_count": 0, "messages_today_count": 0, "storage_used": 0,
                "members_count": 0, "indexing_status": "EMPTY"
            }

        try:
            recent_projs = await self.proj_repo.list(org_id, workspace_id)
        except Exception:
            recent_projs = []

        try:
            docs = await self._fetch_docs(org_id, workspace_id)
        except Exception:
            docs = []

        try:
            chats = await self._fetch_chats(org_id, workspace_id)
        except Exception:
            chats = []

        try:
            notifs = await self.notif_service.list_notifications(user_id, limit=5, only_unread=True)
        except Exception:
            notifs = []

        try:
            acts = await self.act_service.list_timeline(org_id, limit=10)
        except Exception:
            acts = []

        try:
            favs = await self.fav_service.list_favorites(user_id)
        except Exception:
            favs = []

        recent_projs_data = [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "created_at": p.created_at.isoformat(),
                "updated_at": getattr(p, 'updated_at', p.created_at).isoformat() if getattr(p, 'updated_at', None) else p.created_at.isoformat(),
                "status": "Active" if getattr(p, 'is_active', True) else "Archived"
            }
            for p in (recent_projs or [])[:5]
        ]

        recent_docs_data = []
        for d in (docs or []):
            recent_docs_data.append(await self._format_doc(d))

        recent_chats_data = [
            {
                "id": str(c.id),
                "name": getattr(c, 'title', getattr(c, 'name', 'AI Conversation')),
                "created_at": c.created_at.isoformat(),
                "updated_at": getattr(c, 'updated_at', c.created_at).isoformat() if getattr(c, 'updated_at', None) else c.created_at.isoformat(),
                "status": "Active" if getattr(c, 'is_active', True) else "Idle"
            }
            for c in (chats or [])
        ]

        notifs_data = [
            {"id": str(n.id), "title": n.title, "message": n.message, "priority": n.priority, "created_at": n.created_at.isoformat()}
            for n in (notifs or [])
        ]

        activities_data = [
            {"id": str(a.id), "event_type": a.event_type, "user_id": str(a.user_id), "created_at": a.created_at.isoformat(), "metadata": a.metadata}
            for a in (acts or [])
        ]

        favs_data = [
            {"id": str(f.id), "item_type": f.item_type, "item_id": f.item_id, "name": f.name, "slug": f.slug}
            for f in (favs or [])
        ]

        if stats["documents_count"] > 0 or stats["chats_count"] > 0:
            insights_text = f"{stats['documents_count']} documents and {stats['chats_count']} conversation sessions active in knowledge base."
            ai_status = "active"
        else:
            insights_text = "No documents or conversations indexed in workspace knowledge base yet."
            ai_status = "idle"

        ai_summary = {
            "insights": insights_text,
            "last_generation": datetime.utcnow().isoformat(),
            "status": ai_status
        }

        dashboard_data = {
            "organization": org_data,
            "workspace": ws_data,
            "statistics": stats,
            "recent_projects": recent_projs_data,
            "recent_documents": recent_docs_data,
            "recent_chats": recent_chats_data,
            "notifications": notifs_data,
            "activity": activities_data,
            "favorites": favs_data,
            "ai_summary": ai_summary
        }

        await cache.set(cache_key, dashboard_data, ttl=60)
        return dashboard_data

    async def get_recent_projects(self, org_id: UUID, workspace_id: Optional[UUID] = None) -> list:
        recent_projs = await self.proj_repo.list(org_id, workspace_id)
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "created_at": p.created_at.isoformat(),
                "updated_at": getattr(p, 'updated_at', p.created_at).isoformat() if getattr(p, 'updated_at', None) else p.created_at.isoformat(),
                "status": "Active" if getattr(p, 'is_active', True) else "Archived"
            }
            for p in (recent_projs or [])[:5]
        ]

    async def _format_doc(self, d: Document) -> dict:
        uploader_name = "Team Member"
        if getattr(d, 'uploaded_by', None):
            try:
                from ..models.user import User
                user = await self.db.get(User, d.uploaded_by)
                if user:
                    uploader_name = getattr(user, 'username', None) or (user.email.split('@')[0] if getattr(user, 'email', None) else "Member")
            except Exception:
                pass

        return {
            "id": str(d.id),
            "name": getattr(d, 'filename', getattr(d, 'title', 'Document')),
            "mime_type": d.mime_type,
            "size": d.size,
            "created_at": d.created_at.isoformat() if getattr(d, 'created_at', None) else datetime.utcnow().isoformat(),
            "processing_status": getattr(d, 'processing_status', 'COMPLETED'),
            "uploader_name": uploader_name,
            "storage_path": getattr(d, 'storage_path', ''),
            "checksum_sha256": getattr(d, 'checksum_sha256', '')
        }

    async def get_recent_documents(self, org_id: UUID, workspace_id: Optional[UUID] = None) -> list:
        docs = await self._fetch_docs(org_id, workspace_id)
        res = []
        for d in (docs or []):
            res.append(await self._format_doc(d))
        return res

    async def get_recent_chats(self, org_id: UUID, workspace_id: Optional[UUID] = None) -> list:
        chats = await self._fetch_chats(org_id, workspace_id)
        return [
            {
                "id": str(c.id),
                "name": getattr(c, 'title', getattr(c, 'name', 'AI Conversation')),
                "created_at": c.created_at.isoformat(),
                "updated_at": getattr(c, 'updated_at', c.created_at).isoformat() if getattr(c, 'updated_at', None) else c.created_at.isoformat(),
                "status": "Active" if getattr(c, 'is_active', True) else "Idle"
            }
            for c in (chats or [])
        ]

    async def get_ai_summary(self, org_id: UUID, workspace_id: Optional[UUID] = None) -> dict:
        stats = await self.aggregator.aggregate_stats(org_id, workspace_id)
        if stats["documents_count"] > 0 or stats["chats_count"] > 0:
            insights_text = f"{stats['documents_count']} documents and {stats['chats_count']} conversation sessions active in knowledge base."
            ai_status = "active"
        else:
            insights_text = "No documents or conversations indexed in workspace knowledge base yet."
            ai_status = "idle"

        return {
            "insights": insights_text,
            "last_generation": datetime.utcnow().isoformat(),
            "status": ai_status
        }

    async def refresh_dashboard(self, user_id: UUID, org_id: UUID) -> None:
        pattern = f"dashboard:{org_id}:{user_id}:*"
        await cache.invalidate(pattern)
