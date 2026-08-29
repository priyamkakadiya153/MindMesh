import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.user import User
from app.core.dependencies import get_current_user
from app.actions.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actions", tags=["Action Audit Trail"])

@router.get("/history")
async def get_action_history(
    days: int = Query(default=7, ge=1, le=30),
    source_type: Optional[str] = Query(default=None),
    action_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches human-readable action history for current user and workspace."""
    events = await AuditService.get_user_action_history(
        user=user,
        db=db,
        days=days,
        source_type=source_type,
        action_type=action_type,
        limit=limit
    )

    formatted = []
    for ev in events:
        formatted.append({
            "id": str(ev.id),
            "action_type": ev.action_type,
            "status": ev.status,
            "source_type": ev.source_type,
            "target_type": ev.target_type,
            "target_id": ev.target_id,
            "before_state": ev.before_state,
            "after_state": ev.after_state,
            "reason": ev.reason,
            "created_at": ev.created_at.isoformat() if ev.created_at else None
        })

    return {"events": formatted, "total": len(formatted)}
