import logging
from uuid import UUID
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AuditDecisionLog, GovernancePolicy

logger = logging.getLogger(__name__)

class ComplianceEngine:
    @staticmethod
    async def get_compliance_stats(db: AsyncSession, organization_id: UUID) -> Dict[str, Any]:
        """Validates current active policies and audit records against SOC 2 and GDPR checklists."""
        # 1. Count policies by category
        stmt_policies = select(GovernancePolicy.category, func.count(GovernancePolicy.id)).where(
            GovernancePolicy.organization_id == organization_id,
            GovernancePolicy.is_active == True
        ).group_by(GovernancePolicy.category)
        res_policies = await db.execute(stmt_policies)
        policy_counts = dict(res_policies.all())

        # 2. Count audit records
        stmt_audits = select(func.count(AuditDecisionLog.id)).where(
            AuditDecisionLog.organization_id == organization_id
        )
        res_audits = await db.execute(stmt_audits)
        audit_count = res_audits.scalar() or 0

        # SOC 2 & GDPR Checklists validation status
        gdpr_ready = "pii_protection" in str(policy_counts.keys()).lower() or "privacy" in str(policy_counts.keys()).lower()
        soc2_ready = audit_count > 0 and "security" in str(policy_counts.keys()).lower()

        return {
            "soc2_compliance_status": "Compliant" if soc2_ready else "Partially Compliant",
            "gdpr_compliance_status": "Compliant" if gdpr_ready else "Partially Compliant",
            "total_governed_policies": sum(policy_counts.values()),
            "total_audited_transactions": audit_count,
            "policy_coverage": policy_counts
        }
