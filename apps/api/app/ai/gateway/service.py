import logging
import uuid
from typing import Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway.models import (
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIStreamEvent,
    AIError,
    GenerationAttempt
)
from app.ai.gateway.gateway import AIGateway
from app.ai.chat.session import ChatSessionManager
from app.ai.chat.idempotency import IdempotencyManager

logger = logging.getLogger(__name__)

class AIService:
    """
    MindMesh AI Service Layer.
    
    Acts as the service boundary between API Controllers and the AIGateway.
    Manages database session persistence, idempotency checks, and generation attempt tracking.
    """

    @staticmethod
    async def in_flight_check(request: AIRequest) -> Optional[AIResponse]:
        if not request.idempotency_key:
            return None

        key = IdempotencyManager.make_key(
            user_id=str(request.user_id),
            idempotency_key=request.idempotency_key,
            conversation_id=str(request.conversation_id) if request.conversation_id else None
        )

        cached = IdempotencyManager.get_cached_response(key)
        if cached:
            return cached

        if not IdempotencyManager.register_in_flight(key):
            return AIResponse(
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                content="",
                status=AIResponseStatus.FAILED,
                error=AIError(code="DUPLICATE_SUBMISSION", message="A duplicate request is already in progress. Please wait.")
            )

        return None

    @staticmethod
    async def process_chat(
        db: AsyncSession,
        request: AIRequest
    ) -> AIResponse:
        """Processes normalized AI request through MindMesh AI Orchestrator with DB message persistence."""
        in_flight_err = await AIService.in_flight_check(request)
        if in_flight_err:
            return in_flight_err

        key = IdempotencyManager.make_key(
            user_id=str(request.user_id),
            idempotency_key=request.idempotency_key or str(request.request_id),
            conversation_id=str(request.conversation_id) if request.conversation_id else None
        )

        try:
            from app.ai.orchestrator import MindMeshAIOrchestrator
            orchestrator = MindMeshAIOrchestrator(db)
            
            res_dict = await orchestrator.execute(
                user_id=request.user_id,
                org_id=request.organization_id or uuid.uuid4(),
                query=request.message,
                conversation_id=request.conversation_id,
                workspace_id=request.workspace_id,
                provider=request.model_preferences.get("provider") or "gemini",
                model=request.model_preferences.get("model") or "gemini-2.5-flash",
                temperature=request.generation_parameters.get("temperature", 0.2),
                max_tokens=request.generation_parameters.get("max_tokens", 1024)
            )

            response = AIResponse(
                request_id=request.request_id,
                conversation_id=res_dict.get("chat_id"),
                content=res_dict.get("answer", ""),
                status=AIResponseStatus.COMPLETED,
                model=request.model_preferences.get("model") or "gemini-2.5-flash",
                provider=request.model_preferences.get("provider") or "gemini",
                sources=res_dict.get("citations", []),
                metadata=res_dict
            )

            if "action_proposal" in res_dict:
                response.metadata["action_proposal"] = res_dict["action_proposal"]

            if response.status == AIResponseStatus.COMPLETED:
                IdempotencyManager.cache_response(key, response)

            return response
        finally:
            IdempotencyManager.release_in_flight(key)

    @staticmethod
    async def process_chat_stream(
        db: AsyncSession,
        request: AIRequest
    ) -> AsyncGenerator[AIStreamEvent, None]:
        """Streams AI tokens via MindMesh AI Orchestrator and emits normalized SSE events."""
        if request.idempotency_key:
            key = IdempotencyManager.make_key(
                user_id=str(request.user_id),
                idempotency_key=request.idempotency_key,
                conversation_id=str(request.conversation_id) if request.conversation_id else None
            )
            if not IdempotencyManager.register_in_flight(key):
                yield AIStreamEvent(
                    type="ERROR",
                    content="A duplicate request is already in progress. Please wait.",
                    request_id=str(request.request_id),
                    conversation_id=str(request.conversation_id) if request.conversation_id else None,
                    metadata={"error_code": "DUPLICATE_SUBMISSION"}
                )
                return

        try:
            from app.ai.orchestrator import MindMeshAIOrchestrator
            orchestrator = MindMeshAIOrchestrator(db)
            
            async for evt in orchestrator.stream_execute(
                user_id=request.user_id,
                org_id=request.organization_id or uuid.uuid4(),
                query=request.message,
                conversation_id=request.conversation_id,
                workspace_id=request.workspace_id,
                provider=request.model_preferences.get("provider") or "gemini",
                model=request.model_preferences.get("model") or "gemini-2.5-flash",
                temperature=request.generation_parameters.get("temperature", 0.2),
                max_tokens=request.generation_parameters.get("max_tokens", 1024)
            ):
                evt_type = evt.get("type", "token")
                content = evt.get("content", "")
                
                if evt_type == "session":
                    yield AIStreamEvent(
                        type="session",
                        content="",
                        request_id=str(request.request_id),
                        conversation_id=str(evt.get("conversation_id")),
                        metadata=evt
                    )
                elif evt_type == "action_proposal":
                    yield AIStreamEvent(
                        type="action_proposal",
                        content="",
                        request_id=str(request.request_id),
                        conversation_id=str(request.conversation_id) if request.conversation_id else None,
                        metadata={"action_proposal": evt.get("action_proposal")}
                    )
                elif evt_type == "token":
                    yield AIStreamEvent(
                        type="token",
                        content=content,
                        request_id=str(request.request_id),
                        conversation_id=str(request.conversation_id) if request.conversation_id else None
                    )
                elif evt_type == "final":
                    yield AIStreamEvent(
                        type="final",
                        content=evt.get("answer", ""),
                        request_id=str(request.request_id),
                        conversation_id=str(evt.get("conversation_id")),
                        metadata=evt
                    )
            yield AIStreamEvent(
                type="done",
                content="",
                request_id=str(request.request_id),
                conversation_id=str(request.conversation_id) if request.conversation_id else None
            )
        finally:
            if request.idempotency_key:
                key = IdempotencyManager.make_key(
                    user_id=str(request.user_id),
                    idempotency_key=request.idempotency_key,
                    conversation_id=str(request.conversation_id) if request.conversation_id else None
                )
                IdempotencyManager.release_in_flight(key)

    @staticmethod
    async def retry_generation(
        db: AsyncSession,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> AIResponse:
        """Retries AI generation for a given user or assistant message ID."""
        from app.models.message import Message
        from sqlalchemy import select
        
        stmt = select(Message).where(Message.id == message_id, Message.organization_id == organization_id)
        res = await db.execute(stmt)
        target_msg = res.scalar_one_or_none()

        if not target_msg:
            return AIResponse(
                request_id=uuid.uuid4(),
                content="",
                status=AIResponseStatus.FAILED,
                error=AIError(code="MESSAGE_NOT_FOUND", message="Target message not found.")
            )

        query_text = target_msg.content if target_msg.role == "user" else "Retry response request"
        ai_req = AIRequest(
            user_id=user_id,
            organization_id=organization_id,
            conversation_id=target_msg.chat_id,
            message=query_text
        )

        resp = await AIService.process_chat(db, ai_req)
        return resp
