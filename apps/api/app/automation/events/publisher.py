import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.events.bus import event_bus
from app.automation.events.registry import event_registry
from app.automation.approval.models import AutomationEventLog

logger = logging.getLogger(__name__)

class EventPublisher:
    @staticmethod
    async def publish_event(
        event_type: str,
        payload: Dict[str, Any],
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None
    ) -> Optional[AutomationEventLog]:
        """Publishes a business event after persisting the log entry to the database."""
        if not event_registry.is_valid_event(event_type):
            logger.warning(f"EventPublisher: Event '{event_type}' is not recognized in standard catalog.")

        enriched_payload = {
            **payload,
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "event_type": event_type
        }

        log = None
        if db:
            try:
                log = AutomationEventLog(
                    event_type=event_type,
                    payload=enriched_payload,
                    processed=False,
                    organization_id=organization_id,
                    workspace_id=workspace_id
                )
                db.add(log)
                await db.commit()
                await db.refresh(log)
            except Exception as e:
                logger.error(f"EventPublisher: Failed to persist event log: {str(e)}")
                await db.rollback()

        # Publish to in-memory bus AFTER database commit completes
        await event_bus.publish(event_type, enriched_payload)

        return log
