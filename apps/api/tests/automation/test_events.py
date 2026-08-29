import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.events.bus import event_bus
from app.automation.events.publisher import EventPublisher
from app.automation.events.dispatcher import EventDispatcher
from app.automation.events.router import EventRouter
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution, AutomationEventLog
from tests.agents.test_sdk import seed_agent_test_data

def test_event_topic_router():
    assert EventRouter.match_topic("document.*", "document_uploaded") is True
    assert EventRouter.match_topic("document.*", "project_created") is False

class MockSessionContext:
    def __init__(self, session):
        self.session = session
    async def __aenter__(self):
        return self.session
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_event_pubsub_triggers_workflow(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    
    # Patch dispatcher Session constructor to share the test session
    import app.automation.events.dispatcher
    original_session_local = app.automation.events.dispatcher.AsyncSessionLocal
    app.automation.events.dispatcher.AsyncSessionLocal = lambda: MockSessionContext(db_session)

    # Enable dispatcher listener
    EventDispatcher.start_listening()

    # Create workflow subscribed to trigger: event "document_uploaded"
    definition = {
        "trigger": {"type": "event", "event_type": "document_uploaded"},
        "steps": [
            {"name": "step_1", "type": "sequential"}
        ]
    }

    wdef = WorkflowDefinition(
        name="Event Triggered Workflow",
        definition=definition,
        organization_id=org.id,
        is_active=True
    )
    db_session.add(wdef)
    await db_session.commit()

    # Publish document upload event to bus
    payload = {"document_id": "doc-uuid-123"}
    
    log = await EventPublisher.publish_event(
        event_type="document_uploaded",
        payload=payload,
        organization_id=org.id,
        db=db_session
    )
    
    assert log is not None
    assert log.event_type == "document_uploaded"

    # Query spawned execution
    stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_id == wdef.id)
    res = await db_session.execute(stmt)
    execution = res.scalar_one_or_none()

    assert execution is not None
    assert execution.status == "Completed"
    assert execution.context["document_id"] == "doc-uuid-123"

    # Restore session patch
    app.automation.events.dispatcher.AsyncSessionLocal = original_session_local
