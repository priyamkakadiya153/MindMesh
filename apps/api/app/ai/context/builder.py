import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .validator import ContextSecurityValidator
from .ranking import ContextRanker
from .merger import ChunkMerger
from .tokenizer import TokenBudgetManager
from .compressor import ContextCompressor
from .formatter import ContextFormatter

logger = logging.getLogger(__name__)

class ContextBuilder:
    @staticmethod
    async def build_context(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        chunks: List[Dict[str, Any]],
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        model_name: str = "default",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrates security checks, ranking, merging, compression, and formatting."""
        options = options or {}
        
        # 1. Security validation: Extract unique document IDs and check permissions
        doc_ids = set()
        for chunk in chunks:
            if chunk.get("document_id"):
                try:
                    doc_ids.add(UUID(str(chunk["document_id"])))
                except ValueError:
                    pass
                    
        # Exclude chunks if security validation fails
        valid_chunks = []
        if doc_ids:
            is_authorized = await ContextSecurityValidator.validate_context_permissions(
                db=db,
                user_id=user_id,
                org_id=org_id,
                document_ids=doc_ids
            )
            if not is_authorized:
                logger.warning(f"Security validation failed for subset of docs in org {org_id} user {user_id}. Filtering valid ones...")
                # We will validate individually to keep the ones the user HAS access to,
                # filtering out unauthorized ones.
                for chunk in chunks:
                    if not chunk.get("document_id"):
                        continue
                    try:
                        chunk_doc_id = UUID(str(chunk["document_id"]))
                        chunk_auth = await ContextSecurityValidator.validate_context_permissions(
                            db=db,
                            user_id=user_id,
                            org_id=org_id,
                            document_ids={chunk_doc_id}
                        )
                        if chunk_auth:
                            valid_chunks.append(chunk)
                    except Exception:
                        pass
            else:
                valid_chunks = chunks
        else:
            valid_chunks = chunks

        # 2. Ranking by multi-criteria priority
        ranked_chunks = ContextRanker.rank_chunks(
            chunks=valid_chunks,
            active_workspace_id=workspace_id,
            active_project_id=project_id
        )

        # 3. Merger: Combine sequential/contiguous blocks
        merged_chunks = ChunkMerger.merge_chunks(ranked_chunks)

        # 4. Token allocation & compression
        budget = TokenBudgetManager.allocate_budget(model_name, query="", history_text="")
        # Allow options to override context token limits
        context_limit = options.get("context_limit") or budget["context_limit"]
        
        # Calculate original token count
        orig_tokens = sum(TokenBudgetManager.count_tokens(c["content"]) for c in merged_chunks)

        # Apply compression if needed
        compressed_chunks = ContextCompressor.compress_chunks(
            chunks=merged_chunks,
            token_limit=context_limit,
            query=options.get("query", "")
        )
        
        # Calculate compressed token count
        comp_tokens = sum(TokenBudgetManager.count_tokens(c["content"]) for c in compressed_chunks)
        compression_ratio = round(comp_tokens / max(1, orig_tokens), 4)

        # 5. Formatter
        context_string = ContextFormatter.format_context_for_prompt(compressed_chunks)

        timeline_events = options.get("timeline_events") or []
        if timeline_events:
            timeline_str = "\n\n--- ORGANIZATIONAL KNOWLEDGE TIMELINE (CHRONOLOGICAL) ---\n"
            for ev in timeline_events:
                t_str = ev.get("occurred_at") or ev.get("created_at") or "Date Unknown"
                timeline_str += f"[{t_str[:10]}] {ev.get('event_type')}: {ev.get('title')} - {ev.get('description')}\n"
            context_string = timeline_str + "\n" + context_string

        graph_context = options.get("graph_context") or {}
        graph_rels = graph_context.get("relationships") or []
        if graph_rels:
            graph_str = "\n\n--- KNOWLEDGE GRAPH RELATIONSHIPS ---\n"
            for r in graph_rels:
                graph_str += f"({r['source_type']}: \"{r['source_title']}\") --[{r['relation_type']}]--> ({r['target_type']}: \"{r['target_title']}\")\n"
            context_string = graph_str + "\n" + context_string

        return {
            "context_string": context_string,
            "original_token_count": orig_tokens,
            "token_count": comp_tokens,
            "compression_ratio": compression_ratio,
            "chunks": compressed_chunks
        }
