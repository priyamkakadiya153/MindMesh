from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import math
import re

from sqlalchemy import select, or_, and_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.search import SearchIndex
from ..models.user import User
from ..workspace.models import WorkspaceMember, Workspace

class SearchParams:
    def __init__(
        self,
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
    ):
        self.query = query.strip()
        self.entity_type = entity_type.lower() if entity_type else "all"
        self.workspace_id = workspace_id
        self.organization_id = organization_id
        self.owner_id = owner_id
        self.page = max(1, page)
        self.limit = max(1, min(100, limit))
        self.sort = sort.lower() if sort else "most_relevant"
        self.status = status
        self.file_type = file_type
        self.tags = tags or []
        self.date_from = date_from
        self.date_to = date_to

class BaseSearchEngine(ABC):
    @abstractmethod
    async def search(
        self,
        db: AsyncSession,
        params: SearchParams,
        user: User,
        user_workspace_ids: List[UUID]
    ) -> Dict[str, Any]:
        """Executes universal search across entities."""
        pass

    @abstractmethod
    async def autocomplete(
        self,
        db: AsyncSession,
        query: str,
        organization_id: Optional[UUID],
        user: User,
        user_workspace_ids: List[UUID],
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """Returns autocomplete suggestions for prefix query."""
        pass

class DatabaseSearchEngine(BaseSearchEngine):
    """Production-grade relational search engine with exact match boosting,

    keyword relevance scoring, recency decay, permission filtering, and faceting.

    Future-proof: Ready to be blended or wrapped by HybridSearchEngine / VectorSearchEngine.

    """

    async def search(
        self,
        db: AsyncSession,
        params: SearchParams,
        user: User,
        user_workspace_ids: List[UUID]
    ) -> Dict[str, Any]:
        # Build base filter conditions
        conditions = [SearchIndex.is_active == True]

        # 1. Permission & Organization Scope
        if params.organization_id:
            conditions.append(SearchIndex.organization_id == params.organization_id)
        
        # Workspace RBAC Isolation: User can see entries with no workspace (org-wide)
        # OR entries in workspaces where they are a member.
        if params.workspace_id:
            # Check if user has access to requested workspace
            if params.workspace_id in user_workspace_ids:
                conditions.append(SearchIndex.workspace_id == params.workspace_id)
            else:
                # User requested a workspace they don't belong to -> return empty result
                return {
                    "results": [],
                    "total_hits": 0,
                    "page": params.page,
                    "limit": params.limit,
                    "total_pages": 0,
                    "facets": {}
                }
        else:
            # Allow items with NULL workspace or items in authorized workspace IDs
            if user_workspace_ids:
                conditions.append(
                    or_(
                        SearchIndex.workspace_id == None,
                        SearchIndex.workspace_id.in_(user_workspace_ids)
                    )
                )
            else:
                conditions.append(SearchIndex.workspace_id == None)

        # 2. Entity Type Filter
        if params.entity_type and params.entity_type != "all":
            conditions.append(SearchIndex.entity_type == params.entity_type)

        # 3. Owner Filter
        if params.owner_id:
            conditions.append(SearchIndex.owner_id == params.owner_id)

        # 4. Date Range Filters
        if params.date_from:
            conditions.append(SearchIndex.updated_at >= params.date_from)
        if params.date_to:
            conditions.append(SearchIndex.updated_at <= params.date_to)

        # 5. Query matching (Title, Content, Tags)
        keywords = [k.lower() for k in re.split(r'\s+', params.query) if k.strip()] if params.query else []

        if keywords:
            kw_clauses = []
            for kw in keywords:
                pattern = f"%{kw}%"
                kw_clauses.append(SearchIndex.title.ilike(pattern))
                kw_clauses.append(SearchIndex.content.ilike(pattern))
            conditions.append(or_(*kw_clauses))

        # Query main dataset
        stmt = select(SearchIndex).where(and_(*conditions))
        
        # Execute query to get raw candidates
        res = await db.execute(stmt)
        candidates = res.scalars().all()

        # Compute relevance scores & filter metadata in python memory for hybrid ranking
        scored_items = []
        now = datetime.utcnow()
        query_lower = params.query.lower() if params.query else ""

        for item in candidates:
            # Metadata filter checks
            meta = item.metadata_json or {}
            if params.status and meta.get("status") != params.status:
                continue
            if params.file_type and meta.get("file_type") != params.file_type:
                continue
            if params.tags:
                item_tags = [str(t).lower() for t in (item.tags or [])]
                if not any(t.lower() in item_tags for t in params.tags):
                    continue

            # Calculate Ranking Score
            score = 1.0
            title_lower = item.title.lower() if item.title else ""
            content_lower = item.content.lower() if item.content else ""

            if query_lower:
                # Exact title match boost
                if query_lower == title_lower:
                    score += 100.0
                elif title_lower.startswith(query_lower):
                    score += 50.0
                elif query_lower in title_lower:
                    score += 25.0

                # Keyword occurrence count
                for kw in keywords:
                    if kw in title_lower:
                        score += 15.0
                    if kw in content_lower:
                        # count matches up to 10
                        occurrences = min(10, content_lower.count(kw))
                        score += 3.0 * occurrences

                # Tag match boost
                item_tags_str = " ".join([str(t).lower() for t in (item.tags or [])])
                for kw in keywords:
                    if kw in item_tags_str:
                        score += 10.0

            # Recency boost (exponential decay up to +10 points)
            if item.updated_at:
                days_old = (now - item.updated_at).total_seconds() / 86400.0
                recency_boost = 10.0 * math.exp(-days_old / 30.0)  # half-life of ~30 days
                score += recency_boost

            snippet = self._generate_snippet(item.content or item.title, keywords)

            scored_items.append({
                "id": str(item.id),
                "entity_type": item.entity_type,
                "entity_id": str(item.entity_id),
                "workspace_id": str(item.workspace_id) if item.workspace_id else None,
                "organization_id": str(item.organization_id) if item.organization_id else None,
                "owner_id": str(item.owner_id) if item.owner_id else None,
                "title": item.title,
                "snippet": snippet,
                "tags": item.tags or [],
                "metadata": meta,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "score": round(score, 2),
            })

        # Calculate Facets (counts by entity_type)
        facets = {}
        for item in scored_items:
            etype = item["entity_type"]
            facets[etype] = facets.get(etype, 0) + 1
        facets["all"] = len(scored_items)

        # Sorting
        if params.sort == "newest":
            scored_items.sort(key=lambda x: x["updated_at"] or "", reverse=True)
        elif params.sort == "oldest":
            scored_items.sort(key=lambda x: x["created_at"] or "")
        elif params.sort == "alphabetical":
            scored_items.sort(key=lambda x: x["title"].lower())
        else:
            # most_relevant
            scored_items.sort(key=lambda x: x["score"], reverse=True)

        # Pagination
        total_hits = len(scored_items)
        offset = (params.page - 1) * params.limit
        paginated_results = scored_items[offset : offset + params.limit]
        total_pages = math.ceil(total_hits / params.limit) if total_hits > 0 else 0

        return {
            "results": paginated_results,
            "total_hits": total_hits,
            "page": params.page,
            "limit": params.limit,
            "total_pages": total_pages,
            "facets": facets
        }

    async def autocomplete(
        self,
        db: AsyncSession,
        query: str,
        organization_id: Optional[UUID],
        user: User,
        user_workspace_ids: List[UUID],
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        clean_q = query.strip()
        if not clean_q:
            return []

        conditions = [SearchIndex.is_active == True]
        if organization_id:
            conditions.append(SearchIndex.organization_id == organization_id)

        if user_workspace_ids:
            conditions.append(
                or_(
                    SearchIndex.workspace_id == None,
                    SearchIndex.workspace_id.in_(user_workspace_ids)
                )
            )
        else:
            conditions.append(SearchIndex.workspace_id == None)

        pattern = f"%{clean_q.lower()}%"
        conditions.append(SearchIndex.title.ilike(pattern))

        stmt = select(SearchIndex).where(and_(*conditions)).limit(limit * 2)
        res = await db.execute(stmt)
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

    def _generate_snippet(self, content: str, keywords: List[str], max_len: int = 160) -> str:
        if not content:
            return ""
        clean_text = re.sub(r'\s+', ' ', content).strip()
        if not keywords:
            return clean_text[:max_len] + ("..." if len(clean_text) > max_len else "")

        # Find first keyword match location
        text_lower = clean_text.lower()
        first_pos = len(text_lower)
        for kw in keywords:
            pos = text_lower.find(kw)
            if pos != -1 and pos < first_pos:
                first_pos = pos

        if first_pos == len(text_lower):
            return clean_text[:max_len] + ("..." if len(clean_text) > max_len else "")

        start = max(0, first_pos - 40)
        end = min(len(clean_text), first_pos + 120)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(clean_text) else ""

        return prefix + clean_text[start:end] + suffix
