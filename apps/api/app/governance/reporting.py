import logging
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AuditDecisionLog
from app.governance.compliance import ComplianceEngine

logger = logging.getLogger(__name__)

class ComplianceReporter:
    @staticmethod
    async def generate_audit_export(db: AsyncSession, organization_id: UUID) -> Dict[str, Any]:
        """Compiles a complete audit trace logs package for external auditors."""
        # 1. Gather compliance stats
        stats = await ComplianceEngine.get_compliance_stats(db, organization_id)

        # 2. Fetch last 50 audit traces
        stmt = select(AuditDecisionLog).where(
            AuditDecisionLog.organization_id == organization_id
        ).order_by(AuditDecisionLog.id.desc()).limit(50)
        res = await db.execute(stmt)
        audits = res.scalars().all()

        audit_list = []
        for a in audits:
            audit_list.append({
                "id": str(a.id),
                "execution_id": str(a.execution_id),
                "agent_name": a.agent_name,
                "trust_score": a.trust_score,
                "risk_score": a.risk_score,
                "confidence_score": a.confidence_score,
                "created_at": a.created_at.isoformat() if hasattr(a, "created_at") and a.created_at else None
            })

        return {
            "organization_id": str(organization_id),
            "report_timestamp": datetime.utcnow().isoformat(),
            "compliance_summary": stats,
            "recent_decision_audits": audit_list
        }
