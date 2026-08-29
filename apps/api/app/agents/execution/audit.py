import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.agents.context import SessionContext

logger = logging.getLogger(__name__)

class ExecutionAuditLogger:
    @staticmethod
    async def log_step(
        db: AsyncSession,
        context: SessionContext,
        step_id: str,
        tool: str,
        status: str,
        details: dict
    ):
        """Creates an AuditLog record in the database for the executed step."""
        try:
            log = AuditLog(
                action=f"agent_tool_call:{tool}",
                user_id=context.user_id,
                organization_id=context.organization_id,
                details={
                    "request_id": context.request_id,
                    "step_id": step_id,
                    "status": status,
                    **details
                }
            )
            db.add(log)
            await db.commit()
        except Exception as e:
            logger.error(f"ExecutionAuditLogger: Failed to save audit log for tool '{tool}': {str(e)}", exc_info=True)
