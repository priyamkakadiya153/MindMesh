from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import ProactiveIntelligenceService

router = APIRouter(prefix="/intelligence", tags=["Proactive Intelligence"])

class SignalItemSchema(BaseModel):
    id: str
    signal_type: str
    priority: str
    title: str
    summary: str
    status: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    created_at: str
    metadata: Dict[str, Any]

@router.get("/signals", response_model=List[SignalItemSchema], status_code=status.HTTP_200_OK)
async def list_signals(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve active proactive intelligence signals."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = ProactiveIntelligenceService(db)
    return await service.get_important_signals_for_user(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid
    )

@router.get("/important", response_model=List[SignalItemSchema], status_code=status.HTTP_200_OK)
async def get_important_feed(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve personalized 'Important for You' proactive intelligence feed."""
    ws_uuid = UUID(workspace_id) if workspace_id else None
    service = ProactiveIntelligenceService(db)
    return await service.get_important_signals_for_user(
        user=current_user,
        organization_id=org_id,
        workspace_id=ws_uuid
    )

@router.post("/signals/{signal_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_signal(
    signal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismiss a proactive intelligence signal."""
    try:
        s_uuid = UUID(signal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signal UUID")

    service = ProactiveIntelligenceService(db)
    success = await service.dismiss_signal(s_uuid, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal dismissed successfully"}
