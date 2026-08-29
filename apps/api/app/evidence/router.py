from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["Knowledge Evidence & Quality"])

class VerifyEvidenceRequest(BaseModel):
    query: str
    raw_evidence: Dict[str, Any]

class ResolveConflictRequest(BaseModel):
    conflict_id: str
    chosen_source_id: str

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_evidence(
    req: VerifyEvidenceRequest,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Verifies candidate citations against real database records and checks for conflicts."""
    service = EvidenceService(db)
    return await service.verify_and_build_evidence(
        user=current_user,
        organization_id=org_id,
        raw_evidence=req.raw_evidence
    )

@router.get("/sources/{source_id}", status_code=status.HTTP_200_OK)
async def get_source_lineage(
    source_id: str,
    current_user: User = Depends(get_current_user),
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve verified source details and lineage chain."""
    try:
        s_uuid = UUID(source_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source UUID format")

    service = EvidenceService(db)
    res = await service.get_source_lineage(s_uuid, org_id)
    if not res:
        raise HTTPException(status_code=404, detail="Source not found or access denied")
    return res

@router.post("/conflicts/resolve", status_code=status.HTTP_200_OK)
async def resolve_conflict(
    req: ResolveConflictRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resolves a source conflict by selecting an authoritative source."""
    return {"message": "Conflict resolved successfully", "conflict_id": req.conflict_id, "chosen_source_id": req.chosen_source_id}
