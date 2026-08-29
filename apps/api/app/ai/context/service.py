import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .builder import ContextBuilder
from .compressor import ContextCompressor
from .formatter import ContextFormatter
from .tokenizer import TokenBudgetManager

logger = logging.getLogger(__name__)

class ContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_context(
        self,
        user_id: UUID,
        org_id: UUID,
        chunks: List[Dict[str, Any]],
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        model_name: str = "default",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validates permissions, merges, ranks, compresses, and returns the formatted context."""
        return await ContextBuilder.build_context(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            chunks=chunks,
            workspace_id=workspace_id,
            project_id=project_id,
            model_name=model_name,
            options=options
        )

    def compress_context(
        self,
        context_chunks: List[Dict[str, Any]],
        token_limit: int,
        query: str = ""
    ) -> Dict[str, Any]:
        """Compresses context chunks directly to fit within a specific token limit."""
        compressed = ContextCompressor.compress_chunks(
            chunks=context_chunks,
            token_limit=token_limit,
            query=query
        )
        
        orig_tokens = sum(TokenBudgetManager.count_tokens(c["content"]) for c in context_chunks)
        comp_tokens = sum(TokenBudgetManager.count_tokens(c["content"]) for c in compressed)
        
        context_string = ContextFormatter.format_context_for_prompt(compressed)
        
        return {
            "context_string": context_string,
            "original_token_count": orig_tokens,
            "token_count": comp_tokens,
            "compression_ratio": round(comp_tokens / max(1, orig_tokens), 4),
            "chunks": compressed
        }
