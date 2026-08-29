import time
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .engine import SearchParams
from .hybrid_engine import HybridSearchEngine
from .indexer import SearchIndexer
from .analytics import analytics_tracker
from ..models.search import SearchHistory, SearchIndex
from ..models.user import User
from ..workspace.models import WorkspaceMember, Workspace
from ..models.organization import Organization
from ..models.conversations import Conversation, ConversationMember
from ..models.chat import Chat

logger = logging.getLogger(__name__)

class SearchService:
    """Central service orchestrating Universal Semantic & Keyword Hybrid Search,

    RBAC security filtering, search suggestions, and search history tracking.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.hybrid_engine = HybridSearchEngine(db)

    async def universal_search(
        self,
        user: User,
        query: str = "",
        entity_type: str = "all",
        workspace_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        owner_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
        sort: str = "most_relevant",
        status: Optional[str] = None,
        file_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()

        # Ensure index is seeded if empty
        idx_check = await self.db.execute(select(SearchIndex.id).limit(1))
        if not idx_check.scalar_one_or_none():
            logger.info("SearchIndex is empty. Performing initial auto-seed...")
            await SearchIndexer.auto_seed_index(self.db)

        # 1. Enforce Organization Membership RBAC
        if organization_id:
            from ..models.organization_member import OrganizationMember
            org_member_stmt = select(OrganizationMember.id).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user.id
            )
            is_org_member = (await self.db.execute(org_member_stmt)).scalar_one_or_none()
            if not is_org_member:
                logger.warning(f"User {user.id} attempted to search Organization {organization_id} without membership.")
                return {
                    "query": query,
                    "results": [],
                    "total_hits": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "facets": {},
                    "query_time_ms": 0.0
                }

        # 2. Resolve user's accessible workspace IDs
        ws_stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None)
        )
        ws_res = await self.db.execute(ws_stmt)
        user_workspace_ids = [row[0] for row in ws_res.all()]

        # 3. Resolve user's authorized chat / conversation IDs (Private DM & Group RBAC)
        authorized_chat_ids = await self._get_authorized_chat_ids(user.id)

        params = SearchParams(
            query=query,
            entity_type=entity_type,
            workspace_id=workspace_id,
            organization_id=organization_id,
            owner_id=owner_id,
            page=page,
            limit=limit,
            sort=sort,
            status=status,
            file_type=file_type,
            tags=tags,
            date_from=date_from,
            date_to=date_to,
        )

        search_res = await self.hybrid_engine.search(
            params=params,
            user=user,
            user_workspace_ids=user_workspace_ids,
            authorized_chat_ids=authorized_chat_ids
        )

        # Enrich workspace and organization display names for search result cards
        ws_names_cache = {}
        org_names_cache = {}

        for item in search_res["results"]:
            ws_id_str = item.get("workspace_id")
            if ws_id_str:
                if ws_id_str not in ws_names_cache:
                    ws_row = (await self.db.execute(select(Workspace.name).where(Workspace.id == UUID(ws_id_str)))).scalar_one_or_none()
                    ws_names_cache[ws_id_str] = ws_row or "Workspace"
                item["workspace_name"] = ws_names_cache[ws_id_str]

            org_id_str = item.get("organization_id")
            if org_id_str:
                if org_id_str not in org_names_cache:
                    org_row = (await self.db.execute(select(Organization.name).where(Organization.id == UUID(org_id_str)))).scalar_one_or_none()
                    org_names_cache[org_id_str] = org_row or "Organization"
                item["organization_name"] = org_names_cache[org_id_str]

        duration_ms = (time.time() - start_time) * 1000.0
        search_res["query_time_ms"] = round(duration_ms, 2)

        # Save query to user search history if query is provided
        if query and len(query.strip()) >= 2:
            await self._record_history(user.id, query.strip())
            analytics_tracker.record_search(
                query=query,
                duration_ms=duration_ms,
                result_count=search_res["total_hits"],
                user_id=str(user.id),
                workspace_id=str(workspace_id) if workspace_id else None
            )

        return search_res

    async def get_suggestions(
        self,
        user: User,
        query_prefix: str,
        organization_id: Optional[UUID] = None,
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        clean_prefix = (query_prefix or "").strip().lower()
        if not clean_prefix:
            return []

        if organization_id:
            from ..models.organization_member import OrganizationMember
            org_member_stmt = select(OrganizationMember.id).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user.id
            )
            is_org_member = (await self.db.execute(org_member_stmt)).scalar_one_or_none()
            if not is_org_member:
                return []

        # Resolve user's accessible workspace IDs
        ws_stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None)
        )
        ws_res = await self.db.execute(ws_stmt)
        user_workspace_ids = [row[0] for row in ws_res.all()]

        pattern = f"%{clean_prefix}%"
        stmt = (
            select(SearchIndex)
            .where(
                SearchIndex.is_active == True,
                SearchIndex.title.ilike(pattern),
                or_(
                    SearchIndex.workspace_id == None,
                    SearchIndex.workspace_id.in_(user_workspace_ids)
                ) if user_workspace_ids else SearchIndex.workspace_id == None
            )
            .limit(limit * 2)
        )

        res = await self.db.execute(stmt)
        items = res.scalars().all()

        suggestions = []
        seen_titles = set()

        for item in items:
            t = item.title
            if t.lower() not in seen_titles:
                seen_titles.add(t.lower())
                suggestions.append({
                    "id": str(item.entity_id),
                    "title": item.title,
                    "type": item.entity_type,
                    "workspace_id": str(item.workspace_id) if item.workspace_id else None,
                })
                if len(suggestions) >= limit:
                    break

        return suggestions

    async def get_user_search_history(self, user_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.created_at))
        )
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        seen = set()
        history_items = []
        for r in records:
            q_clean = r.query.strip()
            if q_clean.lower() not in seen:
                seen.add(q_clean.lower())
                history_items.append({
                    "id": str(r.id),
                    "query": q_clean,
                    "created_at": r.created_at.isoformat() if r.created_at else datetime.utcnow().isoformat()
                })
                if len(history_items) >= limit:
                    break

        return history_items

    async def clear_user_search_history(self, user_id: UUID) -> bool:
        stmt = delete(SearchHistory).where(SearchHistory.user_id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def _get_authorized_chat_ids(self, user_id: UUID) -> List[UUID]:
        chat_ids = set()

        # 1. Standard Chat table
        stmt1 = select(Chat.id).where(Chat.user_id == user_id, Chat.deleted_at.is_(None))
        res1 = await self.db.execute(stmt1)
        for r in res1.scalars().all():
            chat_ids.add(r)

        # 2. Conversation & Members
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

    async def _record_history(self, user_id: UUID, query: str):
        try:
            entry = SearchHistory(user_id=user_id, query=query.strip())
            self.db.add(entry)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to save search history for user {user_id}: {e}")

    # Legacy compatibility methods
    async def execute_semantic_search(self, org_id: UUID, query: str, limit: int = 10, filters: dict = None, user_id: UUID = None, workspace_id: UUID = None) -> dict:
        dummy_user = User(id=user_id or UUID("00000000-0000-0000-0000-000000000000"), email="legacy@mindmesh.internal")
        res = await self.universal_search(
            user=dummy_user,
            query=query,
            organization_id=org_id,
            workspace_id=workspace_id,
            limit=limit
        )
        return {
            "results": [
                {
                    "document_id": item["source_id"],
                    "title": item["title"],
                    "score": item["score"],
                    "snippet": item["snippet"],
                    "page": 1,
                    "workspace": item.get("workspace_name", "Workspace"),
                    "project": "Project",
                    "tags": item.get("tags", []),
                    "matched_chunks": [{"chunk_id": item["id"], "content": item["snippet"], "page": 1}]
                }
                for item in res["results"]
            ],
            "query_time_ms": res["query_time_ms"],
            "total_hits": res["total_hits"]
        }

    async def execute_hybrid_search(self, org_id: UUID, query: str, limit: int = 10, filters: dict = None, user_id: UUID = None, workspace_id: UUID = None) -> dict:
        return await self.execute_semantic_search(org_id, query, limit, filters, user_id, workspace_id)
