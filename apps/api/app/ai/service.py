import logging
import time
from uuid import UUID
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.search.service import SearchService
from app.ai.context.service import ContextService
from app.ai.prompt.builder import PromptBuilder
from app.ai.citations.engine import CitationEngine
from app.ai.conversation.memory import ConversationMemoryManager
from app.ai.conversation.history import ConversationHistoryManager

logger = logging.getLogger(__name__)

class AIRetrievalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.search_service = SearchService(db)
        self.context_service = ContextService(db)

    async def retrieve_context(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        limit: int = 10,
        model_name: str = "default",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Runs search, validates tenant permissions, filters, merges, ranks, compresses, and builds context."""
        start_time = time.time()
        options = options or {}
        
        # 1. Run hybrid semantic search
        filters = {}
        if workspace_id:
            filters["workspace_id"] = str(workspace_id)
        if project_id:
            filters["project_id"] = str(project_id)
            
        search_res = await self.search_service.execute_hybrid_search(
            org_id=org_id,
            query=query,
            limit=limit,
            filters=filters,
            user_id=user_id,
            workspace_id=workspace_id
        )
        
        # Extract individual chunks/hits from search results
        raw_hits = []
        for res_item in search_res.get("results", []):
            for mc in res_item.get("matched_chunks", []):
                hit = {
                    "chunk_id": mc.get("chunk_id"),
                    "content": mc.get("content"),
                    "page": mc.get("page", 1),
                    "document_id": res_item.get("document_id"),
                    "title": res_item.get("title"),
                    "score": res_item.get("score", 0.0),
                    "workspace": res_item.get("workspace"),
                    "project": res_item.get("project"),
                    "version": res_item.get("version", 1),
                    "workspace_id": workspace_id,
                    "project_id": project_id
                }
                raw_hits.append(hit)

        # 2. Build Context (validates, merges, ranks, compresses, formats)
        options["query"] = query
        context_payload = await self.context_service.build_context(
            user_id=user_id,
            org_id=org_id,
            chunks=raw_hits,
            workspace_id=workspace_id,
            project_id=project_id,
            model_name=model_name,
            options=options
        )
        
        duration_ms = (time.time() - start_time) * 1000.0
        context_payload["latency_ms"] = round(duration_ms, 2)
        return context_payload

    async def build_prompt(
        self,
        query: str,
        context_string: str,
        conversation_id: Optional[UUID] = None,
        role_key: str = "default",
        org_name: str = "the Organization",
        format_type: str = "markdown",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Loads conversation history (if ID provided), and builds standardized prompt payload."""
        history_dicts = []
        if conversation_id:
            # Load messages
            from app.models.message import Message
            from sqlalchemy import select
            msg_stmt = select(Message).where(
                Message.chat_id == conversation_id,
                Message.is_active == True
            ).order_by(Message.created_at.asc())
            msg_res = await self.db.execute(msg_stmt)
            messages = msg_res.scalars().all()
            
            for msg in messages:
                # We can't determine user vs assistant dynamically easily here without sender check,
                # let's assume if it is the user who is calling, message from other senders is assistant.
                # In typical chats we can check sender_id == user_id
                role = "user" if msg.sender_id == options.get("user_id") else "assistant"
                history_dicts.append({
                    "role": role,
                    "content": msg.content
                })
                
            # Trim history to token limits
            history_dicts = ConversationHistoryManager.trim_history(history_dicts, history_token_limit=1500)
            
        return PromptBuilder.build_prompt(
            query=query,
            context_string=context_string,
            history=history_dicts,
            role_key=role_key,
            org_name=org_name,
            format_type=format_type,
            options=options
        )

    async def prepare_request(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        conversation_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        model_name: str = "default",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Entrypoint to generate final ready-to-run grounded payload for LLMs."""
        options = options or {}
        options["user_id"] = user_id
        
        # 1. Retrieve & build context
        context_res = await self.retrieve_context(
            user_id=user_id,
            org_id=org_id,
            query=query,
            workspace_id=workspace_id,
            project_id=project_id,
            limit=options.get("search_limit", 10),
            model_name=model_name,
            options=options
        )
        
        # Resolve Organization Name
        from app.models.organization import Organization
        org_stmt = select(Organization.name).where(Organization.id == org_id)
        org_name = (await self.db.execute(org_stmt)).scalar() or "the Organization"
        
        # 2. Build prompt payload
        prompt_res = await self.build_prompt(
            query=query,
            context_string=context_res["context_string"],
            conversation_id=conversation_id,
            role_key=options.get("role_key", "default"),
            org_name=org_name,
            format_type=options.get("format_type", "markdown"),
            options=options
        )
        
        # 3. Save memory state
        if conversation_id:
            await ConversationMemoryManager.save_memory(
                db=self.db,
                chat_id=conversation_id,
                workspace_id=workspace_id,
                project_id=project_id,
                context_data={
                    "last_query": query,
                    "last_context_ratio": context_res["compression_ratio"],
                    "last_context_tokens": context_res["token_count"]
                }
            )
            
        return {
            "payload": prompt_res["messages"],
            "system_prompt": prompt_res["system_prompt"],
            "user_prompt": prompt_res["user_prompt"],
            "is_safe": prompt_res["is_safe"],
            "token_usage": {
                "context_tokens": context_res["token_count"],
                "total_prompt_tokens": prompt_res["estimated_token_count"]
            },
            "citations": context_res["chunks"],
            "latency": {
                "context_build_ms": context_res["latency_ms"]
            },
            "estimated_cost_usd": prompt_res["estimated_cost_usd"]
        }
