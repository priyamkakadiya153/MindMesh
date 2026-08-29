import time
import math
import re
import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .engine import SearchParams
from .query_processor import QueryProcessor
from ..models.search import SearchIndex
from ..models.user import User
from ..ai.retrieval.domain_retriever import MultiDomainRetriever

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """Production Hybrid Search Engine executing parallel Keyword Search and

    Vector Semantic Search, combined with Reciprocal Rank Fusion (RRF) and

    exact match boosting.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = MultiDomainRetriever(db)

    async def search(
        self,
        params: SearchParams,
        user: User,
        user_workspace_ids: List[UUID],
        authorized_chat_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        qp = QueryProcessor.process(params.query)
        keywords = qp["important_keywords"]
        raw_q_lower = params.query.lower()

        # -------------------------------------------------------------
        # 1. Relational Keyword Search (SearchIndex)
        # -------------------------------------------------------------
        keyword_results = await self._execute_keyword_search(
            params=params,
            user=user,
            user_workspace_ids=user_workspace_ids,
            keywords=keywords,
            raw_q_lower=raw_q_lower
        )

        # -------------------------------------------------------------
        # 2. Vector Semantic Search (MultiDomainRetriever)
        # -------------------------------------------------------------
        semantic_results = []
        if params.query and len(params.query.strip()) >= 2:
            try:
                domain_hits = await self.retriever.search_all_domains(
                    user_id=user.id,
                    organization_id=params.organization_id or UUID("00000000-0000-0000-0000-000000000000"),
                    query_text=params.query,
                    workspace_id=params.workspace_id,
                    limit=50
                )
                semantic_results = self._normalize_domain_hits(domain_hits, authorized_chat_ids)
            except Exception as sem_err:
                logger.warning(f"Semantic search warning: {sem_err}")
                semantic_results = []

        # -------------------------------------------------------------
        # 3. Reciprocal Rank Fusion (RRF) & Scoring
        # -------------------------------------------------------------
        fused_items = self._apply_rrf_fusion(
            keyword_results=keyword_results,
            semantic_results=semantic_results,
            params=params,
            qp=qp,
            raw_q_lower=raw_q_lower
        )

        # -------------------------------------------------------------
        # 4. Filter Metadata & Status
        # -------------------------------------------------------------
        filtered_items = []
        for item in fused_items:
            meta = item.get("metadata", {})
            if params.status and meta.get("status") != params.status:
                continue
            if params.file_type and meta.get("file_type") != params.file_type and item.get("extension") != params.file_type:
                continue
            if params.tags:
                item_tags = [str(t).lower() for t in (item.get("tags") or [])]
                if not any(t.lower() in item_tags for t in params.tags):
                    continue
            filtered_items.append(item)

        # -------------------------------------------------------------
        # 5. Facets & Sorting
        # -------------------------------------------------------------
        facets: Dict[str, int] = {}
        for item in filtered_items:
            stype = item["source_type"]
            facets[stype] = facets.get(stype, 0) + 1
        facets["all"] = len(filtered_items)

        if params.sort == "newest":
            filtered_items.sort(key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)
        elif params.sort == "oldest":
            filtered_items.sort(key=lambda x: x.get("created_at") or "")
        elif params.sort == "alphabetical":
            filtered_items.sort(key=lambda x: (x.get("title") or "").lower())
        else:
            filtered_items.sort(key=lambda x: x["score"], reverse=True)

        # Pagination
        total_hits = len(filtered_items)
        offset = (params.page - 1) * params.limit
        paginated_results = filtered_items[offset : offset + params.limit]
        total_pages = math.ceil(total_hits / params.limit) if total_hits > 0 else 0

        query_time_ms = round((time.time() - start_time) * 1000.0, 2)

        return {
            "query": params.query,
            "results": paginated_results,
            "total_hits": total_hits,
            "page": params.page,
            "limit": params.limit,
            "total_pages": total_pages,
            "facets": facets,
            "query_time_ms": query_time_ms
        }

    async def _execute_keyword_search(
        self,
        params: SearchParams,
        user: User,
        user_workspace_ids: List[UUID],
        keywords: List[str],
        raw_q_lower: str
    ) -> List[Dict[str, Any]]:
        conditions = [SearchIndex.is_active == True]

        if params.organization_id:
            conditions.append(SearchIndex.organization_id == params.organization_id)

        if params.workspace_id:
            if params.workspace_id in user_workspace_ids:
                conditions.append(SearchIndex.workspace_id == params.workspace_id)
            else:
                return []
        else:
            if user_workspace_ids:
                conditions.append(
                    or_(
                        SearchIndex.workspace_id == None,
                        SearchIndex.workspace_id.in_(user_workspace_ids)
                    )
                )
            else:
                conditions.append(SearchIndex.workspace_id == None)

        if params.entity_type and params.entity_type != "all":
            conditions.append(SearchIndex.entity_type == params.entity_type)

        if params.owner_id:
            conditions.append(SearchIndex.owner_id == params.owner_id)

        if params.date_from:
            conditions.append(SearchIndex.updated_at >= params.date_from)
        if params.date_to:
            conditions.append(SearchIndex.updated_at <= params.date_to)

        if keywords:
            kw_clauses = []
            for kw in keywords:
                pattern = f"%{kw}%"
                kw_clauses.append(SearchIndex.title.ilike(pattern))
                kw_clauses.append(SearchIndex.content.ilike(pattern))
            conditions.append(or_(*kw_clauses))

        stmt = select(SearchIndex).where(and_(*conditions)).limit(200)
        res = await self.db.execute(stmt)
        candidates = res.scalars().all()

        results = []
        for item in candidates:
            stype = item.entity_type.lower()
            if stype == "document":
                source_type = "document"
            elif stype == "project":
                source_type = "project"
            elif stype == "task":
                source_type = "task"
            elif stype == "chat" or stype == "message":
                source_type = "message"
            else:
                source_type = stype

            deep_link = self._build_deep_link(source_type, str(item.entity_id), item.metadata_json or {})

            results.append({
                "id": str(item.id),
                "source_type": source_type,
                "source_id": str(item.entity_id),
                "title": item.title,
                "snippet": item.content or "",
                "workspace_id": str(item.workspace_id) if item.workspace_id else None,
                "organization_id": str(item.organization_id) if item.organization_id else None,
                "metadata": item.metadata_json or {},
                "tags": item.tags or [],
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "deep_link": deep_link
            })

        return results

    def _normalize_domain_hits(
        self,
        hits: List[Dict[str, Any]],
        authorized_chat_ids: Optional[List[UUID]] = None
    ) -> List[Dict[str, Any]]:
        normalized = []
        auth_chat_set = set(str(cid) for cid in (authorized_chat_ids or []))

        for h in hits:
            domain = h.get("domain", "").lower()
            ent_id = str(h.get("entity_id") or h.get("id") or "")
            content = h.get("content") or h.get("snippet") or ""
            meta = h.get("metadata") or {}

            if domain == "documents":
                source_type = "document"
            elif domain == "messages" or domain == "conversation_memories":
                source_type = "message"
                chat_id = str(meta.get("chat_id") or "")
                # RBAC Chat Participant Check
                if authorized_chat_ids is not None and chat_id and chat_id not in auth_chat_set:
                    continue
            elif domain == "tasks":
                source_type = "task"
            elif domain == "decisions":
                source_type = "decision"
            else:
                source_type = domain or "document"

            title = h.get("title") or meta.get("title") or (content[:60] if content else "Search Match")
            deep_link = self._build_deep_link(source_type, ent_id, meta)

            normalized.append({
                "id": f"vec-{ent_id}",
                "source_type": source_type,
                "source_id": ent_id,
                "title": title,
                "snippet": content,
                "workspace_id": str(h.get("workspace_id")) if h.get("workspace_id") else None,
                "organization_id": str(h.get("organization_id")) if h.get("organization_id") else None,
                "metadata": meta,
                "tags": h.get("tags") or [],
                "created_at": h.get("created_at"),
                "updated_at": h.get("updated_at"),
                "score": float(h.get("score") or 0.5),
                "deep_link": deep_link
            })

        return normalized

    def _apply_rrf_fusion(
        self,
        keyword_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        params: SearchParams,
        qp: Dict[str, Any],
        raw_q_lower: str,
        k: float = 60.0
    ) -> List[Dict[str, Any]]:
        combined_map: Dict[str, Dict[str, Any]] = {}

        # 1. RRF from Keyword List
        for rank, item in enumerate(keyword_results, start=1):
            key = f"{item['source_type']}:{item['source_id']}"
            if key not in combined_map:
                combined_map[key] = item.copy()
                combined_map[key]["rrf_score"] = 0.0

            combined_map[key]["rrf_score"] += (1.0 / (k + rank))

        # 2. RRF from Semantic List
        for rank, item in enumerate(semantic_results, start=1):
            key = f"{item['source_type']}:{item['source_id']}"
            if key not in combined_map:
                combined_map[key] = item.copy()
                combined_map[key]["rrf_score"] = 0.0

            combined_map[key]["rrf_score"] += (1.0 / (k + rank))

        now = datetime.utcnow()
        final_list = []

        for key, item in combined_map.items():
            base_score = item.get("rrf_score", 0.0) * 100.0
            title_lower = (item.get("title") or "").lower()
            snippet_lower = (item.get("snippet") or "").lower()

            # Exact match title boosts
            if raw_q_lower:
                if raw_q_lower == title_lower:
                    base_score += 50.0
                elif title_lower.startswith(raw_q_lower):
                    base_score += 25.0
                elif raw_q_lower in title_lower:
                    base_score += 15.0

            # Technical token boost
            for tech_tok in qp["technical_tokens"]:
                if tech_tok.lower() in title_lower or tech_tok.lower() in snippet_lower:
                    base_score += 20.0

            # Recency boost
            updated_str = item.get("updated_at") or item.get("created_at")
            if updated_str:
                try:
                    dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    days_old = (now - dt).total_seconds() / 86400.0
                    recency_boost = 10.0 * math.exp(-days_old / 30.0)
                    base_score += recency_boost
                except Exception:
                    pass

            item["score"] = round(base_score, 2)
            item["snippet"] = self._format_snippet(item.get("snippet", ""), qp["important_keywords"])
            final_list.append(item)

        final_list.sort(key=lambda x: x["score"], reverse=True)
        return final_list

    def _format_snippet(self, text: str, keywords: List[str], max_len: int = 160) -> str:
        if not text:
            return ""
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not keywords:
            return clean_text[:max_len] + ("..." if len(clean_text) > max_len else "")

        text_lower = clean_text.lower()
        first_pos = len(text_lower)
        for kw in keywords:
            pos = text_lower.find(kw)
            if pos != -1 and pos < first_pos:
                first_pos = pos

        if first_pos == len(text_lower):
            start = 0
        else:
            start = max(0, first_pos - 40)

        end = min(len(clean_text), start + max_len)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(clean_text) else ""

        snippet = clean_text[start:end]

        # Highlight keywords in markdown bold
        for kw in set(keywords):
            if len(kw) >= 3:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                snippet = pattern.sub(lambda m: f"**{m.group(0)}**", snippet)

        return prefix + snippet + suffix

    def _build_deep_link(self, source_type: str, source_id: str, metadata: Dict[str, Any]) -> str:
        if source_type == "document" or source_type == "file":
            return f"/files?preview={source_id}"
        elif source_type == "message" or source_type == "conversation":
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
            return f"/dashboard"
