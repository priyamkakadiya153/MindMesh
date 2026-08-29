import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from .service import ContextService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context", tags=["AI Context"])

class BuildContextRequest(BaseModel):
    chunks: List[Dict[str, Any]] = Field(..., description="List of raw search hits/chunks to assemble.")
    workspace_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    model_name: Optional[str] = "default"
    options: Optional[Dict[str, Any]] = None

class CompressContextRequest(BaseModel):
    chunks: List[Dict[str, Any]] = Field(..., description="List of retrieved chunks/context parts.")
    token_limit: int = Field(..., ge=1, description="Target token capacity limit.")
    query: Optional[str] = ""

class BuildContextResponse(BaseModel):
    context_string: str
    original_token_count: int
    token_count: int
    compression_ratio: float
    chunks: List[Dict[str, Any]]

@router.post("/build", response_model=BuildContextResponse, status_code=status.HTTP_200_OK)
async def build_context_endpoint(
    request: BuildContextRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Secures, merges, filters, and structures retrieved documents/chunks into contextual prompt blocks."""
    service = ContextService(db)
    try:
        # Convert org_id to UUID if string
        org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
        res = await service.build_context(
            user_id=current_user.id,
            org_id=org_uuid,
            chunks=request.chunks,
            workspace_id=request.workspace_id,
            project_id=request.project_id,
            model_name=request.model_name,
            options=request.options
        )
        return res
    except Exception as e:
        logger.error(f"Failed to build context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build context: {str(e)}"
        )

@router.post("/compress", response_model=BuildContextResponse, status_code=status.HTTP_200_OK)
async def compress_context_endpoint(
    request: CompressContextRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Compresses context chunks down to a specific token limit using relevance heuristics."""
    service = ContextService(db)
    try:
        res = service.compress_context(
            context_chunks=request.chunks,
            token_limit=request.token_limit,
            query=request.query
        )
        return res
    except Exception as e:
        logger.error(f"Failed to compress context: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compress context: {str(e)}"
        )
