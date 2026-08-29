import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.actions.executors.task_executor import CreateTaskActionExecutor
from app.actions.executors.reminder_create_executor import CreateReminderActionExecutor
from app.actions.classifier import ActionClassifier
from app.actions.registry import action_registry
from app.actions.types import ActionProposal, ActionIntentType, ActionStatus, ActionResultStatus

def test_task_title_cleaning():
    raw1 = "Create a task to review the deployment report tomorrow"
    clean1 = CreateTaskActionExecutor.extract_clean_task_title(raw1)
    assert clean1 == "Review the deployment report"

    raw2 = "Add a task to update API documentation by Friday"
    clean2 = CreateTaskActionExecutor.extract_clean_task_title(raw2)
    assert clean2 == "Update api documentation"

    raw3 = "Finish the deployment report"
    clean3 = CreateTaskActionExecutor.extract_clean_task_title(raw3)
    assert clean3 == "Finish the deployment report"
    print("[PASS] Test: Task title cleaning and semantic extraction")

def test_reminder_title_cleaning():
    raw1 = "Remind me tomorrow to submit the weekly status report"
    clean1 = CreateReminderActionExecutor.clean_reminder_title(raw1)
    assert "submit the weekly status report" in clean1.lower()

    raw2 = "Don't let me forget about the client presentation"
    clean2 = CreateReminderActionExecutor.clean_reminder_title(raw2)
    assert "client presentation" in clean2.lower()
    print("[PASS] Test: Reminder title cleaning")

def test_missing_title_clarification():
    proposal = ActionClassifier.classify("Create a task.")
    assert proposal is not None
    assert proposal.status == ActionStatus.NEEDS_CLARIFICATION
    assert proposal.clarification_prompt is not None and "task" in proposal.clarification_prompt.lower()
    print("[PASS] Test: Missing task title clarification")

def test_missing_reminder_schedule_clarification():
    proposal = ActionClassifier.classify("Remind me to review the deployment report.")
    assert proposal is not None
    assert proposal.status == ActionStatus.NEEDS_CLARIFICATION
    assert proposal.clarification_prompt is not None and "when" in proposal.clarification_prompt.lower()
    print("[PASS] Test: Missing reminder schedule clarification")

def test_no_invented_due_date():
    proposal = ActionClassifier.classify("Create a task to review the deployment report.")
    assert proposal is not None
    assert proposal.parameters.get("due_date_str") is None
    print("[PASS] Test: No invented due date")

def test_idempotency_guard():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()
        email = "test@mindmesh.com"

    proposal_id = f"prop-idem-{uuid4().hex[:6]}"
    proposal = ActionProposal(
        proposal_id=proposal_id,
        intent_type=ActionIntentType.CREATE_TASK,
        title="Create Task: Idempotency Test",
        parameters={"title": "Idempotency Test Task"},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )

    class DummyDB:
        def __init__(self):
            self.added_items = []

        async def execute(self, stmt):
            items = self.added_items
            class DummyResult:
                def scalar_one_or_none(self):
                    return items[0] if items else None
                def scalars(self):
                    class SubRes:
                        def first(self):
                            return items[0] if items else None
                        def all(self):
                            return items
                    return SubRes()
            return DummyResult()

        def add(self, obj):
            if not getattr(obj, "id", None):
                obj.id = uuid4()
            self.added_items.append(obj)

        async def commit(self):
            pass
        async def refresh(self, obj):
            pass
        async def rollback(self):
            pass

    db = DummyDB()
    res1 = asyncio.run(action_registry.dispatch(proposal, DummyUser(), db))
    assert res1.status == ActionResultStatus.SUCCESS

    # Dispatch second time with same proposal_id
    res2 = asyncio.run(action_registry.dispatch(proposal, DummyUser(), db))
    assert res2.status == ActionResultStatus.SUCCESS
    assert res2.metadata.get("duplicate_blocked") is True or res2 == res1
    print("[PASS] Test: Idempotency double confirmation guard")

if __name__ == "__main__":
    print("Running AUTO-02 Real Execution Layer Test Suite...")
    test_task_title_cleaning()
    test_reminder_title_cleaning()
    test_missing_title_clarification()
    test_missing_reminder_schedule_clarification()
    test_no_invented_due_date()
    test_idempotency_guard()
    print("\nALL AUTO-02 EXECUTION TESTS PASSED SUCCESSFULLY!")
