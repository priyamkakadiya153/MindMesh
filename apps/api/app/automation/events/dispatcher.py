import logging
from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.automation.events.bus import event_bus
from app.automation.approval.models import WorkflowDefinition
from app.automation.events.router import EventRouter

logger = logging.getLogger(__name__)

class EventDispatcher:
    _is_listening = False

    @classmethod
    def start_listening(cls):
        """Subscribes the dispatcher to the event bus."""
        if cls._is_listening:
            return
        event_bus.subscribe("*", cls.on_event_received)
        cls._is_listening = True
        logger.info("EventDispatcher: Started listening to event bus wildcard hooks.")

    @classmethod
    async def on_event_received(cls, event_type: str, payload: Dict[str, Any]):
        """Callback triggered for any published event."""
        # Prevent infinite event loops
        if event_type == "workflow_completed":
            return

        org_id_str = payload.get("organization_id")
        if not org_id_str:
            logger.warning(f"EventDispatcher: Event '{event_type}' missing 'organization_id'. Cannot match workflow.")
            return

        try:
            org_id = UUID(org_id_str)
        except ValueError:
            logger.error(f"EventDispatcher: Invalid organization UUID in payload: {org_id_str}")
            return

        workspace_id = None
        ws_id_str = payload.get("workspace_id")
        if ws_id_str:
            try:
                workspace_id = UUID(ws_id_str)
            except ValueError:
                pass

        # Query active workflows for this organization
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(WorkflowDefinition).where(
                    WorkflowDefinition.organization_id == org_id,
                    WorkflowDefinition.is_active == True
                )
                res = await db.execute(stmt)
                definitions = res.scalars().all()

                from app.automation.workflow.orchestrator import WorkflowOrchestrator

                for wdef in definitions:
                    trigger = wdef.definition.get("trigger", {})
                    trigger_type = trigger.get("type")
                    trigger_event = trigger.get("event_type")

                    if trigger_type == "event" and trigger_event:
                        # Match exact event or using topic router
                        if EventRouter.match_topic(trigger_event, event_type):
                            logger.info(f"EventDispatcher: Event '{event_type}' matched trigger in workflow '{wdef.name}' (ID: {wdef.id})")
                            
                            # Trigger execution
                            await WorkflowOrchestrator.start_execution(
                                db=db,
                                workflow_id=wdef.id,
                                initial_context=payload,
                                organization_id=org_id,
                                workspace_id=workspace_id
                            )
                            await db.commit()
            except Exception as e:
                logger.error(f"EventDispatcher: Error dispatching event to workflows: {str(e)}", exc_info=True)
