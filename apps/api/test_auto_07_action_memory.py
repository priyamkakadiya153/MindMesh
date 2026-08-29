import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

import app.models
from app.documents.models import Document
from app.models.task import Task
from app.actions.audit_model import ActionEvent
from app.actions.audit_service import AuditService
from app.actions.types import ActionIntentType, ActionProposal, ActionResult, ActionResultStatus

def test_audit_model_creation():
    ev = ActionEvent(
        id=uuid4(),
        organization_id=uuid4(),
        workspace_id=uuid4(),
        actor_user_id=uuid4(),
        action_type="CREATE_TASK",
        status="SUCCEEDED",
        source_type="AI_CHAT",
        target_type="TASK",
        target_id="task-12345",
        reason="Created from AI Chat prompt"
    )
    assert ev.action_type == "CREATE_TASK"
    assert ev.status == "SUCCEEDED"
    assert ev.source_type == "AI_CHAT"
    print("[PASS] ActionEvent model creation test")

def test_audit_service_recording():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()

    proposal = ActionProposal(
        proposal_id="prop-audit-test",
        intent_type=ActionIntentType.SEND_DIRECT_MESSAGE,
        title="Send Message to Dhruvil",
        description="Sending status update",
        parameters={"source_type": "AI_CHAT"}
    )

    result = ActionResult(
        status=ActionResultStatus.SUCCESS,
        action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
        entity_type="DIRECT_MESSAGE",
        entity_id=str(uuid4()),
        message="Message sent successfully."
    )

    class DummyDB:
        def __init__(self):
            self.added = []
        def add(self, obj): self.added.append(obj)
        async def commit(self): pass
        async def rollback(self): pass

    db = DummyDB()
    event = asyncio.run(AuditService.record_action_event(proposal, result, DummyUser(), db))
    assert event is not None
    assert len(db.added) == 1
    recorded = db.added[0]
    assert recorded.action_type == "SEND_DIRECT_MESSAGE"
    assert recorded.status == "SUCCESS"
    assert recorded.source_type == "AI_CHAT"
    print("[PASS] AuditService record_action_event test")

if __name__ == "__main__":
    print("Running AUTO-07 Action Memory & Audit Trail Test Suite...")
    test_audit_model_creation()
    test_audit_service_recording()
    print("ALL AUTO-07 BACKEND TESTS PASSED SUCCESSFULLY!")
