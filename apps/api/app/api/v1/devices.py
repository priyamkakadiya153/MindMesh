from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from datetime import datetime

from ...core.database import get_db_session
from ..dependencies import get_current_user
from ...models.user import User
from ...auth.service import AuthService
from ...auth.schemas import ActiveSessionResponse

router = APIRouter()
auth_service = AuthService()

@router.get("", response_model=List[ActiveSessionResponse])
@router.get("/", response_model=List[ActiveSessionResponse])
async def list_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    current_session_id = request.state.session_id if hasattr(request.state, "session_id") else None
    db_sessions = await auth_service.repo.list_active_sessions(db, current_user.id)
    
    sessions_list = []
    for s in db_sessions:
        sessions_list.append(
            ActiveSessionResponse(
                id=s.id,
                device=s.device_name or "Unknown Device",
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=s.created_at,
                last_activity=s.updated_at,
                expires_at=s.expires_at,
                is_current=(s.id == current_session_id)
            )
        )
    return sessions_list

@router.delete("/{device_id}")
async def revoke_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    db_session = await auth_service.repo.get_session_by_id(db, device_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Device session not found")
        
    db_session.revoked = True
    db_session.updated_at = datetime.utcnow()
    db.add(db_session)
    await auth_service.log_audit_event(db, current_user.id, "auth.device_revoked", details={"device_id": str(device_id)})
    await db.commit()
    return {"status": "ok", "message": "Device session revoked successfully"}
