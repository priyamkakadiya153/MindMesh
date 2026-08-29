import logging
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AuditDecisionLog

logger = logging.getLogger(__name__)

class ExplainabilityTrace:
    @staticmethod
    async def generate_explainability_report(db: AsyncSession, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieves and compiles a secure decision explainability trace for audit review."""
        stmt = select(AuditDecisionLog).where(AuditDecisionLog.execution_id == execution_id)
        res = await db.execute(stmt)
        log = res.scalar_one_or_none()

        if not log:
            return None

        # Format trace cleanly - hiding raw LLM chain-of-thought strings to protect security/privacy
        return {
            "execution_id": str(log.execution_id),
            "agent_name": log.agent_name,
            "selected_tools": log.selected_tools.get("tools", []),
            "retrieved_documents": log.retrieved_documents.get("documents", []),
            "applied_policies": log.applied_policies.get("policies", []),
            "confidence_score": log.confidence_score,
            "risk_score": log.risk_score,
            "trust_score": log.trust_score,
            "execution_summary": log.execution_summary or "Execution completed successfully."
        }
