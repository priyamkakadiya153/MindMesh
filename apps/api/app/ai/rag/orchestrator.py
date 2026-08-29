import logging
from uuid import UUID
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from .pipeline import RAGPipeline

logger = logging.getLogger(__name__)

class RAGOrchestrator:
    @staticmethod
    async def execute_rag_flow(
        db: AsyncSession,
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
        """Simple coordinator method to run the RAG query pipeline."""
        pipeline = RAGPipeline(db)
        return await pipeline.query(
            user_id=user_id,
            org_id=org_id,
            query=query,
            workspace_id=workspace_id,
            project_id=project_id,
            provider_name=provider_name,
            model_name=model_name,
            history=history,
            **kwargs
        )
