import re
import logging
from uuid import UUID
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document, FileIntelligence
from app.ai.embeddings.models import DocumentChunk
from app.search.service import SearchService
from app.ai.context.validator import ContextSecurityValidator

logger = logging.getLogger(__name__)

DOC_EXTENSIONS = r"(?:pdf|docx|doc|txt|md|csv|xlsx|json|yaml|yml)"

class RAGRetrieval:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_service = SearchService(db)

    @classmethod
    def extract_document_reference(cls, query: str, history: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[str], bool]:
        """
        Extracts explicit document filename or title mentioned in the query.
        Returns (doc_name, is_from_current_query).
        """
        q = query.strip()

        # 1. Exact match with extension: e.g. Architecture-Test.pdf, auth_arch.md, Unknown-Document.pdf
        ext_pattern = re.compile(rf"\b([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)*\.(?:{DOC_EXTENSIONS}))\b", re.IGNORECASE)
        ext_matches = ext_pattern.findall(q)
        if ext_matches:
            return ext_matches[0].strip(), True

        # 2. Match phrases like 'document "XYZ"' or 'in the "XYZ" document'
        phrase_pattern = re.compile(r"""(?:in|from|about|regarding|according to)\s+(?:the\s+)?(?:document|file|report|spec|pdf)\s+["']?([^"'\?]+)["']?""", re.IGNORECASE)
        phrase_match = phrase_pattern.search(q)
        if phrase_match:
            cand = phrase_match.group(1).strip()
            if cand.lower() not in {"this", "that", "it", "the", "a", "our", "my"}:
                return cand, True

        # 3. Check for quotes around potential document titles: e.g. What does "Architecture-Test" say?
        quote_pattern = re.compile(r"""["']([a-zA-Z0-9_\-\s]+\.(?:pdf|docx|doc|txt|md|csv|xlsx|json))["']""", re.IGNORECASE)
        quote_match = quote_pattern.search(q)
        if quote_match:
            return quote_match.group(1).strip(), True

        # 4. Check conversation history if current query is a short follow-up (e.g. "What about PostgreSQL?", "What about rate limits?")
        if history:
            q_lower = q.lower()
            is_followup = any(q_lower.startswith(prefix) for prefix in [
                "what about", "how about", "what does it say", "what does that say",
                "and what about", "tell me more", "explain the", "what are the", "is there any"
            ]) or len(q.split()) <= 6

            if is_followup:
                for msg in reversed(history):
                    content = msg.get("content") or ""
                    prev_matches = ext_pattern.findall(content)
                    if prev_matches:
                        return prev_matches[0].strip(), False
                    prev_phrase = phrase_pattern.search(content)
                    if prev_phrase:
                        cand = prev_phrase.group(1).strip()
                        if cand.lower() not in {"this", "that", "it", "the", "a", "our", "my"}:
                            return cand, False

        return None, False

    async def retrieve_grounded_chunks(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        limit: int = 10,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves and security-validates chunks for the RAG pipeline."""
        doc_name, is_explicit_current = self.extract_document_reference(query, history)

        # -------------------------------------------------------------
        # PATH 1: Explicit Document Named or Follow-up Context
        # -------------------------------------------------------------
        if doc_name:
            # Query Document within current organization and workspace
            doc_stmt = select(Document).where(
                Document.organization_id == org_id,
                Document.deleted_at.is_(None),
                or_(
                    Document.title.ilike(doc_name),
                    Document.filename.ilike(doc_name),
                    Document.original_filename.ilike(doc_name),
                    Document.title.ilike(f"%{doc_name}%"),
                    Document.filename.ilike(f"%{doc_name}%")
                )
            )
            if workspace_id:
                doc_stmt = doc_stmt.where(Document.workspace_id == workspace_id)

            matched_doc = (await self.db.execute(doc_stmt)).scalars().first()

            # If explicitly named in the current query and not found, signal NOT FOUND
            if not matched_doc and is_explicit_current:
                logger.info(f"Explicit document reference '{doc_name}' not found in workspace {workspace_id}")
                return [{"not_found": True, "document_name": doc_name}]

            if matched_doc:
                # Retrieve actual document chunks
                chunk_stmt = select(DocumentChunk).where(
                    DocumentChunk.document_id == matched_doc.id,
                    DocumentChunk.deleted_at.is_(None)
                ).order_by(DocumentChunk.chunk_index)
                doc_chunks = (await self.db.execute(chunk_stmt)).scalars().all()

                if doc_chunks:
                    # Tokenize query to score chunks by keyword presence
                    stop_words = {"what", "does", "say", "about", "the", "in", "to", "of", "and", "is", "are", "tell", "me", "how", "according", "mentioned", "document", "file", "pdf"}
                    q_tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9_\-]+\b", query) if t.lower() not in stop_words and len(t) > 2 and t.lower() not in doc_name.lower()]

                    scored_chunks = []
                    for c in doc_chunks:
                        c_lower = c.content.lower()
                        s_lower = (c.section_title or "").lower()
                        match_count = sum(c_lower.count(t) + s_lower.count(t) for t in q_tokens)
                        score = min(0.98, 0.75 + (match_count * 0.08)) if q_tokens else 0.90
                        scored_chunks.append((score, c))

                    scored_chunks.sort(key=lambda x: x[0], reverse=True)

                    raw_hits = []
                    for score, c in scored_chunks[:limit]:
                        raw_hits.append({
                            "chunk_id": c.id,
                            "content": c.content,
                            "page": c.page_number or 1,
                            "document_id": str(matched_doc.id),
                            "title": matched_doc.title or matched_doc.original_filename or doc_name,
                            "score": round(score, 4),
                            "workspace": str(workspace_id) if workspace_id else None,
                            "project": str(project_id) if project_id else None,
                            "version": matched_doc.version or 1
                        })

                    # Check security permissions
                    is_authorized = await ContextSecurityValidator.validate_context_permissions(
                        db=self.db,
                        user_id=user_id,
                        org_id=org_id,
                        document_ids={matched_doc.id}
                    )
                    if is_authorized:
                        return raw_hits

        # -------------------------------------------------------------
        # PATH 2: General / Non-Document-Specific Knowledge Retrieval
        # -------------------------------------------------------------
        filters = {}
        if workspace_id:
            filters["workspace_id"] = str(workspace_id)
        if project_id:
            filters["project_id"] = str(project_id)

        from app.ai.retrieval.domain_retriever import MultiDomainRetriever
        multi_retriever = MultiDomainRetriever(self.db)
        multi_hits = await multi_retriever.search_all_domains(
            user_id=user_id,
            organization_id=org_id,
            query_text=query,
            workspace_id=workspace_id,
            project_id=project_id,
            limit=limit
        )

        raw_hits = []
        doc_ids = set()

        for m_hit in multi_hits:
            doc_id = m_hit.get("document_id")
            if doc_id:
                try:
                    doc_ids.add(UUID(str(doc_id)))
                except ValueError:
                    pass

            raw_hits.append({
                "chunk_id": m_hit.get("chunk_id"),
                "content": m_hit.get("content"),
                "page": m_hit.get("page", 1),
                "document_id": str(doc_id) if doc_id else None,
                "title": m_hit.get("title"),
                "score": m_hit.get("score", 0.75),
                "workspace": str(workspace_id) if workspace_id else None,
                "project": str(project_id) if project_id else None,
                "version": 1
            })

        # Also blend search service hybrid results if multi_hits are low
        if len(raw_hits) < limit:
            search_res = await self.search_service.execute_hybrid_search(
                org_id=org_id,
                query=query,
                limit=limit,
                filters=filters,
                user_id=user_id,
                workspace_id=workspace_id
            )
            for res_item in search_res.get("results", []):
                d_id = res_item.get("document_id")
                if d_id:
                    try:
                        doc_ids.add(UUID(str(d_id)))
                    except ValueError:
                        pass
                for mc in res_item.get("matched_chunks", []):
                    raw_hits.append({
                        "chunk_id": mc.get("chunk_id"),
                        "content": mc.get("content"),
                        "page": mc.get("page", 1),
                        "document_id": str(d_id) if d_id else None,
                        "title": res_item.get("title"),
                        "score": res_item.get("score", 0.0),
                        "workspace": res_item.get("workspace"),
                        "project": res_item.get("project"),
                        "version": res_item.get("version", 1)
                    })

        # Security permissions validation
        if not raw_hits:
            return []

        if not doc_ids:
            return raw_hits[:limit]

        is_authorized = await ContextSecurityValidator.validate_context_permissions(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            document_ids=doc_ids
        )

        if is_authorized:
            return raw_hits[:limit]

        # Fallback: filter authorized chunks individually
        authorized_hits = []
        for hit in raw_hits:
            if not hit.get("document_id"):
                authorized_hits.append(hit)
                continue
            try:
                doc_uuid = UUID(str(hit["document_id"]))
                auth = await ContextSecurityValidator.validate_context_permissions(
                    db=self.db,
                    user_id=user_id,
                    org_id=org_id,
                    document_ids={doc_uuid}
                )
                if auth:
                    authorized_hits.append(hit)
            except Exception:
                authorized_hits.append(hit)

        return authorized_hits[:limit]
