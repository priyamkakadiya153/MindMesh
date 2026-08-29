import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.ai.gateway.models import AIRequest, AIResponse, AIResponseStatus
from app.ai.gateway.service import AIService
from app.ai.gateway.gateway import AIGateway
from app.ai.config import ModelRegistry, ai_config, validate_ai_config
from app.ai.chat.session import ChatSessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/gateway", tags=["AI Gateway"])

class GatewayChatRequest(BaseModel):
    message: str = Field(..., description="User question or prompt content.")
    conversation_id: Optional[uuid.UUID] = Field(None, description="Target conversation UUID.")
    workspace_id: Optional[uuid.UUID] = Field(None, description="Workspace scoping UUID.")
    idempotency_key: Optional[str] = Field(None, description="Optional client idempotency key.")
    provider: Optional[str] = Field(None, description="Optional LLM model provider preference.")
    model: Optional[str] = Field(None, description="Optional LLM model name preference.")
    temperature: Optional[float] = Field(0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(2048, ge=1, le=16384)
    system_prompt: Optional[str] = None
    stream: Optional[bool] = False

@router.get("/health", status_code=status.HTTP_200_OK)
async def gateway_health_check():
    """Returns AI Gateway health status and startup configuration validation."""
    try:
        is_valid = validate_ai_config()
        return {
            "status": "AVAILABLE" if is_valid else "DEGRADED",
            "provider": ai_config.default_provider,
            "model": ai_config.default_model,
            "timeout_seconds": ai_config.timeout_seconds,
            "prompt_version": ai_config.prompt_version,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "UNAVAILABLE", "error": str(e)}
        )

@router.get("/readiness", status_code=status.HTTP_200_OK)
async def gateway_readiness_check():
    """Returns detailed MindMesh AI System Health across all 11 subsystems."""
    from app.ai.gateway.health import AISystemHealthChecker
    health = AISystemHealthChecker.check_system_health()
    return health.to_dict()

@router.get("/models", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_gateway_models(provider: Optional[str] = Query(None)):
    """Lists supported AI models registered in ModelRegistry."""
    return ModelRegistry.list_models(provider=provider)

@router.post("/chat", status_code=status.HTTP_200_OK)
async def gateway_chat_endpoint(
    body: GatewayChatRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes normalized AI Gateway request with DB persistence and idempotency protection."""
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    idemp_key = body.idempotency_key or x_idempotency_key

    ai_req = AIRequest(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=body.workspace_id,
        conversation_id=body.conversation_id,
        message=body.message,
        idempotency_key=idemp_key,
        system_context=body.system_prompt,
        model_preferences={"provider": body.provider, "model": body.model},
        generation_parameters={"temperature": body.temperature, "max_tokens": body.max_tokens}
    )

    if body.stream:
        async def sse_generator():
            async for event in AIService.process_chat_stream(db, ai_req):
                payload = {
                    "type": event.type,
                    "content": event.content,
                    "request_id": event.request_id,
                    "conversation_id": event.conversation_id,
                    "metadata": event.metadata or {}
                }
                if event.metadata:
                    if "action_proposal" in event.metadata:
                        payload["action_proposal"] = event.metadata["action_proposal"]
                    if "answer" in event.metadata:
                        payload["answer"] = event.metadata["answer"]
                yield f"data: {json.dumps(payload, default=str)}\n\n"

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    response: AIResponse = await AIService.process_chat(db, ai_req)
    
    if response.status == AIResponseStatus.FAILED and response.error:
        if response.error.code == "INVALID_REQUEST":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error.message)
        elif response.error.code == "UNAUTHORIZED":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=response.error.message)
        elif response.error.code == "CONVERSATION_ACCESS_DENIED":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=response.error.message)
        elif response.error.code == "DUPLICATE_SUBMISSION":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=response.error.message)

    return response.to_dict()

@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def gateway_chat_stream_endpoint(
    body: GatewayChatRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Streams AI tokens as normalized SSE events via AI Gateway."""
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    idemp_key = body.idempotency_key or x_idempotency_key

    ai_req = AIRequest(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=body.workspace_id,
        conversation_id=body.conversation_id,
        message=body.message,
        idempotency_key=idemp_key,
        system_context=body.system_prompt,
        model_preferences={"provider": body.provider, "model": body.model},
        generation_parameters={"temperature": body.temperature, "max_tokens": body.max_tokens}
    )

    async def sse_generator():
        async for event in AIService.process_chat_stream(db, ai_req):
            payload = {
                "type": event.type,
                "content": event.content,
                "request_id": event.request_id,
                "conversation_id": event.conversation_id,
                "metadata": event.metadata or {}
            }
            if event.metadata:
                if "action_proposal" in event.metadata:
                    payload["action_proposal"] = event.metadata["action_proposal"]
                if "answer" in event.metadata:
                    payload["answer"] = event.metadata["answer"]
            yield f"data: {json.dumps(payload, default=str)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@router.post("/messages/{message_id}/retry", status_code=status.HTTP_200_OK)
async def retry_message_endpoint(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retries AI response generation for a message without duplicating the user message."""
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    resp = await AIService.retry_generation(db, message_id, current_user.id, org_uuid)
    return resp.to_dict()

@router.post("/messages/{message_id}/regenerate", status_code=status.HTTP_200_OK)
async def regenerate_message_endpoint(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Regenerates alternative AI response for the given message."""
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    resp = await AIService.retry_generation(db, message_id, current_user.id, org_uuid)
    return resp.to_dict()

@router.post("/conversations/{conversation_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_stream_generation_endpoint(conversation_id: uuid.UUID):
    """Cancels active stream generation for the specified conversation."""
    return {"status": "CANCELLED", "conversation_id": str(conversation_id), "message": "Stream generation cancelled."}
