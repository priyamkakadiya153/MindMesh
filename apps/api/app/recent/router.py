from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .service import RecentItemService

router = APIRouter()

@router.get("/")
async def list_recents(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = RecentItemService(db)
    recents = await service.list_recent(current_user.id, limit)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "item_type": r.item_type,
            "item_id": r.item_id,
            "name": r.name,
            "slug": r.slug,
            "opened_at": r.opened_at
        }
        for r in recents
    ]

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_recents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = RecentItemService(db)
    await service.clear_recent(current_user.id)
