import asyncio
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

import app.models
from app.documents.models import Document # Register Document model
from app.actions.classifier import ActionClassifier
from app.actions.types import ActionIntentType, ActionResultStatus
from app.automation.scheduled_automation_model import ScheduledAutomation
from app.actions.executors.automation_management_executors import (
    PauseAutomationActionExecutor,
    ResumeAutomationActionExecutor,
    CancelAutomationActionExecutor
)

def test_management_classification():
    # 1. Pause intent
    prop_p = ActionClassifier.classify("Pause my weekly task review.")
    assert prop_p is not None
    assert prop_p.intent_type == ActionIntentType.CREATE_AUTOMATION
    assert prop_p.parameters.get("management_action") == "PAUSE"
    print("[PASS] Management Classification test ('Pause my weekly task review.')")

    # 2. Resume intent
    prop_r = ActionClassifier.classify("Resume my weekly task review.")
    assert prop_r is not None
    assert prop_r.parameters.get("management_action") == "RESUME"
    print("[PASS] Management Classification test ('Resume my weekly task review.')")

    # 3. Cancel intent
    prop_c = ActionClassifier.classify("Cancel my Friday deployment reminder.")
    assert prop_c is not None
    assert prop_c.parameters.get("management_action") == "CANCEL"
    print("[PASS] Management Classification test ('Cancel my Friday deployment reminder.')")

def test_management_executor_flow():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()

    dummy_auto = ScheduledAutomation(
        id=uuid4(),
        user_id=DummyUser.id,
        organization_id=DummyUser.organization_id,
        name="Weekly Task Review",
        action_type="CREATE_REMINDER",
        action_payload={"reminder_text": "Review tasks"},
        schedule_type="WEEKLY",
        timezone="Asia/Kolkata",
        status="ACTIVE"
    )

    class DummyScalars:
        def all(self): return [dummy_auto]
        def first(self): return dummy_auto

    class DummyDB:
        async def execute(self, stmt):
            class DummyResult:
                def scalars(self): return DummyScalars()
            return DummyResult()
        async def commit(self): pass
        async def rollback(self): pass

    executor = PauseAutomationActionExecutor()
    prop = ActionClassifier.classify("Pause my weekly task review.")
    res = asyncio.run(executor.execute(prop, DummyUser(), DummyDB()))
    assert res.status == ActionResultStatus.SUCCESS
    assert dummy_auto.status == "PAUSED"
    print("[PASS] Pause Automation Executor Flow test")

if __name__ == "__main__":
    print("Running AUTO-05 Conversational Automation Management Test Suite...")
    test_management_classification()
    test_management_executor_flow()
    print("ALL AUTO-05 BACKEND TESTS PASSED SUCCESSFULLY!")
