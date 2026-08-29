import logging
import asyncio
from uuid import UUID
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from .retrieval import RAGRetrieval
from .generation import RAGGeneration
from .citations import RAGCitations
from .formatter import RAGFormatter
from .evaluation import RAGEvaluator
from ..context.builder import ContextBuilder
from ..prompt.builder import PromptBuilder
from ..llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retrieval = RAGRetrieval(db)

    async def query(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider_name: str = "gemini",
        model_name: str = "gemini-2.0-flash",
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Runs the complete blocking RAG cycle and returns grounded response with analytics."""
        start_time = asyncio.get_event_loop().time()
        
        # 1. Access-checked semantic retrieval
        retrieved_chunks = await self.retrieval.retrieve_grounded_chunks(
            user_id=user_id,
            org_id=org_id,
            query=query,
            workspace_id=workspace_id,
            project_id=project_id,
            limit=10
        )
        
        # Format retrieval hits into builder schema
        builder_chunks = []
        for c in retrieved_chunks:
            builder_chunks.append({
                "document_id": str(c["document_id"]),
                "content": c["content"],
                "page": c["page"],
                "score": c["score"],
                "workspace_id": str(workspace_id) if workspace_id else None,
                "project_id": str(project_id) if project_id else None
            })

        # 2. Consolidate context (ranking, merging, formatting)
        context_res = await ContextBuilder.build_context(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            chunks=builder_chunks,
            workspace_id=workspace_id,
            project_id=project_id
        )
        
        # 3. Assemble prompt messages
        prompt_res = PromptBuilder.build_prompt(
            query=query,
            context_string=context_res["context_string"],
            history=history or []
        )
        
        # 4. Generate response via interchangeable provider
        gen_res = await RAGGeneration.generate_response(
            messages=prompt_res["messages"],
            provider_name=provider_name,
            model_name=model_name,
            **kwargs
        )
        
        # 5. Extract citations matching generated text with chunks
        citations = await RAGCitations.extract_citations(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            answer_text=gen_res["text"],
            retrieved_chunks=retrieved_chunks
        )
        
        # 6. Heuristic groundedness score
        eval_res = RAGEvaluator.evaluate_groundedness(gen_res["text"], retrieved_chunks)
        
        # Suggestions
        suggestions = RAGFormatter.generate_suggested_questions(query, gen_res["text"])
        
        latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000.0)
        
        # Compile response
        return {
            "answer": gen_res["text"],
            "citations": [c.model_dump() for c in citations],
            "confidence": eval_res["score"],
            "sources": [
                {
                    "title": c.get("title"),
                    "page": c.get("page"),
                    "version": c.get("version"),
                    "score": c.get("score")
                } for c in retrieved_chunks[:3]
            ],
            "tokens": {
                "prompt": gen_res["prompt_tokens"],
                "completion": gen_res["completion_tokens"]
            },
            "cost": gen_res["cost"],
            "latency_ms": latency_ms,
            "suggestions": suggestions
        }

    async def stream_query(
        self,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider_name: str = "gemini",
        model_name: str = "gemini-2.0-flash",
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams the RAG answer tokens, yielding incremental texts and returning final citations."""
        # 1. Semantic retrieval & permissions check
        retrieved_chunks = await self.retrieval.retrieve_grounded_chunks(
            user_id=user_id,
            org_id=org_id,
            query=query,
            workspace_id=workspace_id,
            project_id=project_id,
            limit=10
        )
        
        builder_chunks = []
        for c in retrieved_chunks:
            builder_chunks.append({
                "document_id": str(c["document_id"]),
                "content": c["content"],
                "page": c["page"],
                "score": c["score"],
                "workspace_id": str(workspace_id) if workspace_id else None,
                "project_id": str(project_id) if project_id else None
            })

        # 2. Build context
        context_res = await ContextBuilder.build_context(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            chunks=builder_chunks,
            workspace_id=workspace_id,
            project_id=project_id
        )
        
        # 3. Prompt building
        prompt_res = PromptBuilder.build_prompt(
            query=query,
            context_string=context_res["context_string"],
            history=history or []
        )
        
        # 4. Stream response from LLM
        full_text = ""
        provider = LLMProviderFactory.get_provider(provider_name, model_name)
        
        async for token in provider.stream(prompt_res["messages"], **kwargs):
            full_text += token
            yield {"type": "token", "content": token}
            
        # 5. Extraction of Citations on final stream completion
        citations = await RAGCitations.extract_citations(
            db=self.db,
            user_id=user_id,
            org_id=org_id,
            answer_text=full_text,
            retrieved_chunks=retrieved_chunks
        )
        
        eval_res = RAGEvaluator.evaluate_groundedness(full_text, retrieved_chunks)
        suggestions = RAGFormatter.generate_suggested_questions(query, full_text)
        
        # Estimate usage metrics for streaming session
        prompt_tokens = provider.count_tokens(" ".join(m["content"] for m in prompt_res["messages"]))
        comp_tokens = provider.count_tokens(full_text)
        cost = provider.estimate_cost(prompt_tokens, comp_tokens)
        
        yield {
            "type": "final",
            "citations": [c.model_dump() for c in citations],
            "confidence": eval_res["score"],
            "suggestions": suggestions,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": comp_tokens
            },
            "cost": cost
        }
