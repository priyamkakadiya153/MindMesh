import logging
from datetime import datetime
from typing import Dict, Any
from app.automation.approval.models import WorkflowExecution

logger = logging.getLogger(__name__)

class WorkflowMetrics:
    @staticmethod
    def calculate_duration_ms(started_at: datetime, completed_at: datetime) -> float:
        """Returns duration of run in milliseconds."""
        return (completed_at - started_at).total_seconds() * 1000.0

    @staticmethod
    def check_sla_breach(execution: WorkflowExecution, max_sla_seconds: int) -> bool:
        """Determines if the total run duration exceeded the SLA threshold."""
        if not execution.started_at:
            return False
        
        end_time = execution.completed_at or datetime.utcnow()
        duration_sec = (end_time - execution.started_at).total_seconds()
        
        breached = duration_sec > max_sla_seconds
        if breached:
            logger.warning(
                f"WorkflowMetrics: SLA breach detected for execution '{execution.id}'. "
                f"Limit: {max_sla_seconds}s, Elapsed: {duration_sec:.2f}s"
            )
        return breached
