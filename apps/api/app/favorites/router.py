from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from ..core.database import get_db_session
from ..auth.dependencies import get_current_user
from ..models.user import User
from .service import FavoriteService

router = APIRouter()

class FavoriteAddRequest(BaseModel):
    item_type: str
    item_id: UUID
    name: str
    slug: Optional[str] = None

@router.get("/")
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = FavoriteService(db)
    favs = await service.list_favorites(current_user.id)
    return [
        {
            "id": f.id,
            "user_id": f.user_id,
            "item_type": f.item_type,
            "item_id": f.item_id,
            "name": f.name,
            "slug": f.slug,
            "created_at": f.created_at
        }
        for f in favs
    ]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    req: FavoriteAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = FavoriteService(db)
    fav = await service.add_favorite(
        user_id=current_user.id,
        entity_type=req.item_type,
        entity_id=req.item_id,
        name=req.name,
        slug=req.slug
    )
    await db.commit()
    return {
        "id": fav.id,
        "user_id": fav.user_id,
        "item_type": fav.item_type,
        "item_id": fav.item_id,
        "name": fav.name,
        "slug": fav.slug
    }

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    service = FavoriteService(db)
    removed = await service.remove_favorite_by_id(current_user.id, id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorite bookmark not found")
    await db.commit()
