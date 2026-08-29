import logging
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import AuditDecisionLog

logger = logging.getLogger(__name__)

class ActionAuditor:
    @staticmethod
    async def log_action_decision(
        db: AsyncSession,
        execution_id: UUID,
        organization_id: UUID,
        agent_name: str,
        selected_tools: List[str],
        retrieved_documents: List[Dict[str, Any]],
        applied_policies: List[str],
        confidence_score: float,
        risk_score: float,
        trust_score: float,
        execution_summary: Optional[str] = None
    ) -> AuditDecisionLog:
        """Persists the explainability details of an execution step."""
        log = AuditDecisionLog(
            execution_id=execution_id,
            organization_id=organization_id,
            agent_name=agent_name,
            selected_tools={"tools": selected_tools},
            retrieved_documents={"documents": retrieved_documents},
            applied_policies={"policies": applied_policies},
            confidence_score=confidence_score,
            risk_score=risk_score,
            trust_score=trust_score,
            execution_summary=execution_summary
        )
        db.add(log)
        await db.flush()
        logger.info(f"ActionAuditor: Saved audit decision log for run '{execution_id}' with trust {trust_score}")
        return log
