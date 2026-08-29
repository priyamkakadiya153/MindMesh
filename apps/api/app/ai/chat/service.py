import logging
from uuid import UUID
from typing import Dict, Any, Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def execute_chat(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        chat_id: Optional[UUID] = None,
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 1024
    ) -> Dict[str, Any]:
        """Runs blocking multi-turn chat session via MindMeshAIOrchestrator."""
        from app.ai.orchestrator import MindMeshAIOrchestrator
        orchestrator = MindMeshAIOrchestrator(db)
        return await orchestrator.execute(
            user_id=user_id,
            org_id=org_id,
            query=query,
            conversation_id=chat_id,
            workspace_id=workspace_id,
            project_id=project_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    @classmethod
    async def execute_chat_stream(
        cls,
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        provider: str = "gemini",
        model: str = "gemini-1.5-flash",
        chat_id: Optional[UUID] = None,
        temperature: Optional[float] = 0.2,
        max_tokens: Optional[int] = 1024
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams multi-turn chat response tokens via MindMeshAIOrchestrator."""
        from app.ai.orchestrator import MindMeshAIOrchestrator
        orchestrator = MindMeshAIOrchestrator(db)
        async for chunk in orchestrator.stream_execute(
            user_id=user_id,
            org_id=org_id,
            query=query,
            conversation_id=chat_id,
            workspace_id=workspace_id,
            project_id=project_id,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk

