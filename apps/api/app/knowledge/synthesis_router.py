from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .synthesis_service import KnowledgeSynthesisEngineService

router = APIRouter(prefix="/knowledge/synthesis", tags=["Knowledge Synthesis & Organizational Memory"])

class SynthesizeRequest(BaseModel):
    query: str
    mode: Optional[str] = "OVERVIEW"
    project_id: Optional[str] = None

@router.post("/synthesize", status_code=status.HTTP_200_OK)
async def synthesize_knowledge(
    req: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Execute cross-source organizational memory synthesis."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")

    p_uuid = None
    if req.project_id:
        try:
            p_uuid = UUID(req.project_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid project_id UUID format")

    service = KnowledgeSynthesisEngineService(db)
    return await service.synthesize(
        user=current_user,
        organization_id=org_id,
        query=req.query,
        mode=req.mode or "OVERVIEW",
        project_id=p_uuid
    )

@router.get("/modes", status_code=status.HTTP_200_OK)
async def get_synthesis_modes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve supported synthesis modes."""
    service = KnowledgeSynthesisEngineService(db)
    return await service.get_synthesis_modes()
