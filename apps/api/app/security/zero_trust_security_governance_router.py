from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .zero_trust_security_governance_service import ZeroTrustSecurityGovernanceService

router = APIRouter(prefix="/security-governance", tags=["Zero-Trust Security, Privacy & Data Governance"])

class AuthorizeRequest(BaseModel):
    target_org_id: str
    target_workspace_id: str
    required_permission: str
    resource_id: Optional[str] = None

class AIPolicyCheckRequest(BaseModel):
    provider_name: str
    context_items: List[Dict[str, Any]]

class RevokeMemberRequest(BaseModel):
    target_user_id: str
    workspace_id: str

class PromptSanitizeRequest(BaseModel):
    input_text: str

@router.post("/authorize", status_code=status.HTTP_200_OK)
async def authorize_request(
    req: AuthorizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Validates server-side permissions across User, Org, Workspace, Resource, Role, and Permission."""
    try:
        t_org = UUID(req.target_org_id)
        t_ws = UUID(req.target_workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    service = ZeroTrustSecurityGovernanceService(db)
    try:
        res = await service.authorize_request(
            user=current_user,
            target_org_id=t_org,
            target_workspace_id=t_ws,
            required_permission=req.required_permission,
            resource_id=req.resource_id
        )
        if not res["authorized"]:
            raise HTTPException(status_code=403, detail=res["reason"])
        return res
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))

@router.post("/ai-policy-check", status_code=status.HTTP_200_OK)
async def evaluate_ai_data_boundary(
    req: AIPolicyCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Enforces AI provider policies and sanitizes AI context packs."""
    service = ZeroTrustSecurityGovernanceService(db)
    return await service.evaluate_ai_data_boundary(provider_name=req.provider_name, context_items=req.context_items, user=current_user)

@router.post("/revoke-member", status_code=status.HTTP_200_OK)
async def revoke_member_access(
    req: RevokeMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes immediate member removal revocation across all surfaces."""
    try:
        t_user = UUID(req.target_user_id)
        ws_id = UUID(req.workspace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    service = ZeroTrustSecurityGovernanceService(db)
    return await service.revoke_member_access(target_user_id=t_user, workspace_id=ws_id, admin_user=current_user)

@router.post("/sanitize-prompt", status_code=status.HTTP_200_OK)
async def sanitize_prompt_injection(
    req: PromptSanitizeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Scans untrusted input for prompt injection attack patterns."""
    service = ZeroTrustSecurityGovernanceService(db)
    return await service.sanitize_prompt_injection(input_text=req.input_text)

@router.post("/scan-secrets", status_code=status.HTTP_200_OK)
async def scan_secrets(
    db: AsyncSession = Depends(get_db_session)
):
    """Scans environment and API payloads to ensure no secrets are exposed."""
    service = ZeroTrustSecurityGovernanceService(db)
    return await service.scan_secrets()

@router.get("/security-audit", status_code=status.HTTP_200_OK)
async def get_security_audit_timeline(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves immutable security audit event timeline."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ZeroTrustSecurityGovernanceService(db)
    return await service.get_security_audit_timeline(organization_id=org_id, user=current_user)

@router.get("/security-status", status_code=status.HTTP_200_OK)
async def get_security_status(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves overall zero-trust security status."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ZeroTrustSecurityGovernanceService(db)
    return await service.get_security_status(organization_id=org_id, user=current_user)
