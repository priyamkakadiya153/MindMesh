import time
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.ai.config import ai_config, ModelRegistry
from app.ai.gateway.models import (
    AIRequest,
    AIResponse,
    AIResponseStatus,
    AIRequestLifecycle,
    AIUsage,
    AITiming,
    AIError,
    AIStreamEvent
)
from app.ai.llm.factory import LLMProviderFactory
from app.ai.prompt.builder import normalize_user_message, PROMPT_VERSION

logger = logging.getLogger(__name__)

class AIGateway:
    """
    Central MindMesh AI Gateway Entry Point.
    
    Responsibilities:
    - Input & payload validation
    - User identity & workspace/conversation authorization
    - Centralized AI configuration resolution
    - Provider selection & invocation
    - Controlled retry mechanism preserving request identity
    - Provider response & error normalization
    - Observability & privacy-aware telemetry logging
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def execute(self, request: AIRequest) -> AIResponse:
        """
        Executes an AI generation request deterministically through the gateway lifecycle.
        """
        start_time = time.time()
        req_id = request.request_id
        
        # 1. Lifecycle: REQUESTED -> VALIDATED
        logger.info(f"[AIGateway] Processing AIRequest {req_id} for User: {request.user_id}, Workspace: {request.workspace_id}")
        
        validation_error = await self._validate_request(request)
        if validation_error:
            logger.warning(f"[AIGateway] Validation failed for request {req_id}: {validation_error.message}")
            return AIResponse(
                request_id=req_id,
                conversation_id=request.conversation_id,
                content="",
                status=AIResponseStatus.FAILED,
                error=validation_error,
                timing=AITiming(request_start_time=start_time, completion_time=time.time(), total_latency_ms=int((time.time() - start_time) * 1000))
            )

        # 2. Authorization Verification
        auth_error = await self._verify_authorization(request)
        if auth_error:
            logger.warning(f"[AIGateway] Authorization failed for request {req_id}: {auth_error.message}")
            return AIResponse(
                request_id=req_id,
                conversation_id=request.conversation_id,
                content="",
                status=AIResponseStatus.FAILED,
                error=auth_error,
                timing=AITiming(request_start_time=start_time, completion_time=time.time(), total_latency_ms=int((time.time() - start_time) * 1000))
            )

        # 3. Universal Orchestration Execution
        from app.ai.orchestrator import MindMeshAIOrchestrator
        orchestrator = MindMeshAIOrchestrator(self.db)
        
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

        end_time = time.time()
        response = AIResponse(
            request_id=req_id,
            conversation_id=res_dict.get("chat_id"),
            content=res_dict.get("answer", ""),
            status=AIResponseStatus.COMPLETED,
            model=request.model_preferences.get("model") or "gemini-2.5-flash",
            provider=request.model_preferences.get("provider") or "gemini",
            sources=res_dict.get("citations", []),
            metadata=res_dict,
            timing=AITiming(request_start_time=start_time, completion_time=end_time, total_latency_ms=int((end_time - start_time) * 1000))
        )

        if "action_proposal" in res_dict:
            response.metadata["action_proposal"] = res_dict["action_proposal"]

        # Observability Logging (Privacy Safe)
        logger.info(
            f"[AIGateway Completed] RequestID: {req_id} | Status: {response.status.value} | "
            f"Provider: {response.provider} | Model: {response.model} | Latency: {response.timing.total_latency_ms}ms"
        )

        return response

    async def stream(self, request: AIRequest) -> AsyncGenerator[AIStreamEvent, None]:
        """
        Streams normalized AIStreamEvent objects via MindMesh AI Orchestrator.
        """
        req_id_str = str(request.request_id)
        conv_id_str = str(request.conversation_id) if request.conversation_id else None

        val_err = await self._validate_request(request)
        if val_err:
            yield AIStreamEvent(type="ERROR", content=val_err.message, request_id=req_id_str, conversation_id=conv_id_str, metadata={"code": val_err.code})
            return

        auth_err = await self._verify_authorization(request)
        if auth_err:
            yield AIStreamEvent(type="ERROR", content=auth_err.message, request_id=req_id_str, conversation_id=conv_id_str, metadata={"code": auth_err.code})
            return

        from app.ai.orchestrator import MindMeshAIOrchestrator
        orchestrator = MindMeshAIOrchestrator(self.db)

        try:
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
                    yield AIStreamEvent(type="session", content="", request_id=req_id_str, conversation_id=str(evt.get("conversation_id")), metadata=evt)
                elif evt_type == "token":
                    yield AIStreamEvent(type="token", content=content, request_id=req_id_str, conversation_id=conv_id_str)
                elif evt_type == "final":
                    yield AIStreamEvent(type="final", content=evt.get("answer", ""), request_id=req_id_str, conversation_id=str(evt.get("conversation_id")), metadata=evt)
        except Exception as e:
            logger.error(f"[AIGateway Stream Error] {str(e)}", exc_info=True)
            yield AIStreamEvent(
                type="ERROR",
                content="I'm having trouble generating a response right now. Please try again.",
                request_id=req_id_str,
                conversation_id=conv_id_str,
                metadata={"code": "STREAMING_ERROR", "details": str(e)}
            )

    # ----------------- PRIVATE VALIDATION & AUTHORIZATION -----------------

    async def _validate_request(self, request: AIRequest) -> Optional[AIError]:
        if not request.user_id:
            return AIError(code="UNAUTHORIZED", message="Authenticated user context is required for AI requests.")
            
        try:
            normalize_user_message(request.message, max_length=ai_config.max_message_length)
        except ValueError as ve:
            return AIError(code="INVALID_REQUEST", message=str(ve))

        return None

    async def _verify_authorization(self, request: AIRequest) -> Optional[AIError]:
        if not self.db:
            return None

        # Verify conversation ownership/membership if conversation_id provided
        if request.conversation_id:
            from app.models.chat import Chat
            stmt = select(Chat).where(
                Chat.id == request.conversation_id,
                Chat.user_id == request.user_id,
                Chat.deleted_at.is_(None)
            )
            res = await self.db.execute(stmt)
            chat_obj = res.scalar_one_or_none()
            if not chat_obj:
                return AIError(code="CONVERSATION_ACCESS_DENIED", message="User does not have access to the specified conversation.")

        return None
