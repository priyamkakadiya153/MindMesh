from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user, resolve_organization_id
from app.models.user import User
from .compliance_intelligence_service import ComplianceIntelligenceService

router = APIRouter(prefix="/compliance", tags=["Continuous Compliance, Risk Intelligence & Audit Operations"])

class TestControlRequest(BaseModel):
    control_id: str
    test_type: str = "AUTOMATED"
    simulate_failure: bool = False

class CollectEvidenceRequest(BaseModel):
    control_id: str
    evidence_type: str = "LOG"
    content_payload: str

class RemediateFindingRequest(BaseModel):
    finding_id: Optional[str] = None
    title: str
    severity: str = "HIGH"
    verification_passed: bool = True

class AcceptRiskRequest(BaseModel):
    risk_title: str
    category: str = "Security"
    inherent_score: int = 80
    duration_hours: int = 24

@router.get("/frameworks", status_code=status.HTTP_200_OK)
async def list_frameworks_and_controls(
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns compliance frameworks, requirements, and control mappings."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.list_frameworks_and_controls(organization_id=org_id, user=current_user)

@router.post("/controls/test", status_code=status.HTTP_200_OK)
async def test_compliance_control(
    req: TestControlRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Runs control test procedure, evaluates design & operating effectiveness, and detects control gaps/failures."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.test_compliance_control(
        control_id=req.control_id,
        test_type=req.test_type,
        simulate_failure=req.simulate_failure,
        organization_id=org_id,
        user=current_user
    )

@router.post("/evidence/collect", status_code=status.HTTP_200_OK)
async def collect_compliance_evidence(
    req: CollectEvidenceRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Collects evidence, attaches source provenance, computes SHA-256 hash, and tracks freshness."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.collect_compliance_evidence(
        control_id=req.control_id,
        evidence_type=req.evidence_type,
        content_payload=req.content_payload,
        organization_id=org_id,
        user=current_user
    )

@router.post("/findings/remediate", status_code=status.HTTP_200_OK)
async def remediate_finding(
    req: RemediateFindingRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates audit finding, generates remediation workflow, and performs verification (reopens if verification fails)."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.remediate_finding(
        finding_id=req.finding_id,
        title=req.title,
        severity=req.severity,
        verification_passed=req.verification_passed,
        organization_id=org_id,
        user=current_user
    )

@router.post("/risks/accept", status_code=status.HTTP_200_OK)
async def accept_residual_risk(
    req: AcceptRiskRequest,
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Registers risk in Enterprise Risk Register or grants temporary RiskAcceptance with explicit expiration date."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.accept_residual_risk(
        risk_title=req.risk_title,
        category=req.category,
        inherent_score=req.inherent_score,
        duration_hours=req.duration_hours,
        organization_id=org_id,
        user=current_user
    )

@router.get("/audit-readiness", status_code=status.HTTP_200_OK)
async def assess_audit_readiness(
    missing_evidence: bool = Query(False),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Evaluates evidence completeness, open findings, and active exceptions, and generates AuditEvidencePackage."""
    if not org_id:
        org_id = UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132")
    service = ComplianceIntelligenceService(db)
    return await service.assess_audit_readiness(missing_evidence=missing_evidence, organization_id=org_id, user=current_user)
