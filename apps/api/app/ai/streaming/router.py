import time
import uuid
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session, AsyncSessionLocal
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.models.message import Message
from app.ai.llm.base import LLMSettings
from app.ai.llm.factory import LLMProviderFactory
from app.ai.llm.models import WorkspaceAISetting
from app.ai.prompt.builder import PromptBuilder
from app.ai.retrieval.retriever import HybridRetriever
from .transport import SSETransport, WebSocketTransport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["AI Streaming Response Engine"])

# ---------------- PYDANTIC SCHEMAS ----------------

class StreamChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User prompt or question")
    conversation_id: Optional[UUID] = Field(None, description="Chat conversation ID")
    workspace_id: Optional[UUID] = Field(None, description="Workspace ID scope")
    template_name: str = Field("GeneralQA", description="Prompt template")
    provider: Optional[str] = Field(None, description="e.g. gemini, openai, claude, ollama")
    model: Optional[str] = Field(None, description="e.g. gemini-2.5-flash")

# ---------------- SSE STREAMING ENDPOINT ----------------

@router.post("/stream", status_code=status.HTTP_200_OK)
async def stream_chat_response_endpoint(
    request: StreamChatRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Real-time SSE token streaming endpoint delivering responses via MindMesh AI Orchestrator."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    from app.ai.gateway.models import AIRequest
    from app.ai.gateway.service import AIService
    import json

    ai_req = AIRequest(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=request.workspace_id,
        conversation_id=request.conversation_id,
        message=request.query,
        model_preferences={"provider": request.provider or "gemini", "model": request.model or "gemini-2.5-flash"}
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
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# ---------------- WEBSOCKET STREAMING ENDPOINT ----------------

@router.websocket("/ws")
async def websocket_chat_stream(websocket: WebSocket):
    """Real-time WebSocket streaming endpoint."""
    await websocket.accept()
    ws_transport = WebSocketTransport()

    try:
        data = await websocket.receive_json()
        query = data.get("query", "")
        provider = data.get("provider", "gemini")
        model = data.get("model", "gemini-2.5-flash")

        await websocket.send_json(ws_transport.format_event("connected", {"provider": provider, "model": model}))

        adapter = LLMProviderFactory.get_provider(provider, model)
        accumulated = ""

        async for delta in adapter.stream_generate(query):
            accumulated += delta
            await websocket.send_json(ws_transport.format_event("token", {"delta": delta, "accumulated": accumulated}))

        await websocket.send_json(ws_transport.format_event("completed", {"content": accumulated}))
        await websocket.close()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected cleanly.")
    except Exception as err:
        logger.error(f"WebSocket streaming error: {err}")
        await websocket.send_json(ws_transport.format_event("error", {"message": str(err)}))
        await websocket.close()
