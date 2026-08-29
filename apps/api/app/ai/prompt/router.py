import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.workspace.models import Workspace
from app.ai.retrieval.retriever import HybridRetriever
from app.models.message import Message
from .builder import PromptBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompt", tags=["AI Prompt & Context Assembly"])

# ---------------- PYDANTIC SCHEMAS ----------------

class BuildPromptRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or prompt input")
    conversation_id: Optional[UUID] = Field(None, description="Optional conversation ID to include message history")
    workspace_id: Optional[UUID] = Field(None, description="Optional workspace ID to scope retrieval")
    template_name: str = Field("GeneralQA", description="Prompt template e.g. GeneralQA, DocumentAnalysis, Summarization, CodeReview")
    top_k: int = Field(10, ge=1, le=50, description="Top-K retrieved knowledge chunks limit")
    max_tokens: int = Field(8000, ge=1000, le=32000, description="Maximum total prompt token budget")

class CitationSourceResponse(BaseModel):
    citation_index: int
    citation_tag: str
    chunk_id: str
    document_id: str
    title: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    score: float

class BuildPromptResponse(BaseModel):
    prompt: str
    system_prompt: str
    user_query: str
    template_name: str
    token_count: int
    sources: List[CitationSourceResponse]
    budget_summary: Dict[str, Any]

# ---------------- ENDPOINTS ----------------

@router.post("/build", response_model=BuildPromptResponse, status_code=status.HTTP_200_OK)
async def build_prompt_endpoint(
    request: BuildPromptRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Assembles a token-budgeted, validated prompt with citation sources for LLM consumption."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    # 1. Fetch Workspace Name if workspace_id provided
    ws_name = None
    if request.workspace_id:
        ws_stmt = select(Workspace).where(Workspace.id == request.workspace_id)
        ws_obj = (await db.execute(ws_stmt)).scalar_one_or_none()
        if ws_obj:
            ws_name = ws_obj.name

    # 2. Execute Hybrid Retrieval (Phase 3.4)
    retriever = HybridRetriever(db)
    retrieval_res = await retriever.hybrid_search(
        query_text=request.query,
        organization_id=org_uuid,
        workspace_id=request.workspace_id,
        top_k=request.top_k
    )
    retrieved_chunks = retrieval_res.get("chunks", [])

    # 3. Fetch Conversation History (Phase 3.1)
    conversation_history = []
    if request.conversation_id:
        msg_stmt = select(Message).where(
            Message.chat_id == request.conversation_id,
            Message.deleted_at.is_(None)
        ).order_by(Message.created_at.asc())
        msg_rows = (await db.execute(msg_stmt)).scalars().all()
        conversation_history = [{"role": m.role, "content": m.content} for m in msg_rows]

    # 4. Assemble & Budget Prompt
    builder = PromptBuilder(max_tokens=request.max_tokens)
    built_result = builder.build_prompt(
        query=request.query,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
        workspace_name=ws_name,
        template_name=request.template_name
    )

    return BuildPromptResponse(
        prompt=built_result["prompt"],
        system_prompt=built_result["system_prompt"],
        user_query=built_result["user_query"],
        template_name=built_result["template_name"],
        token_count=built_result["token_count"],
        sources=[CitationSourceResponse(**s) for s in built_result["sources"]],
        budget_summary=built_result["budget_summary"]
    )
